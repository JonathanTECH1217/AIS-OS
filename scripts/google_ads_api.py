"""Google Ads API over REST: login once, then read (GAQL search) and change (googleAds:mutate) Monarc's own account.

Usage:
  python scripts/google_ads_api.py --login     one time: opens Google in the browser, saves the refresh token to
                                               ~/.monarc/secrets.env as GOOGLE_ADS_REFRESH_TOKEN (never printed)
  python scripts/google_ads_api.py --check     keys present, the accounts this login reaches, and the account settings
                                               the gates read (auto-tagging, final URL suffix); writes nothing
  python scripts/google_ads_api.py --query "SELECT campaign.id, campaign.name FROM campaign"

Access (2026-09-28, references/google-ads-api.md): a Google Cloud project with the Google Ads API turned on and
Explorer access or better. Explorer reaches the real account for campaigns, budgets, ad groups, keywords, negatives,
shared lists, and ads; it cannot use Keyword Planner, billing, or user management. Google dropped the developer token
and the manager-account requirement on 2026-09-09; if a call is refused for a missing developer token anyway, put it
in secrets.env as GOOGLE_ADS_DEVELOPER_TOKEN and it is sent.

Keys (scripts/outreach_common.load_env): GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET (an OAuth client of type
Desktop app in that project), GOOGLE_ADS_REFRESH_TOKEN (written by --login), GOOGLE_ADS_CUSTOMER_ID (optional; else
the customer id in projects/google-ads/account.md), GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_LOGIN_CUSTOMER_ID
(both optional).
"""
import argparse
import json
import re
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, SECRETS_ENV, get_secret, report_key_sources  # noqa: E402

VERSION = "v25"                      # current major release 2026-09 (v25.2 on 2026-09-23)
BASE = f"https://googleads.googleapis.com/{VERSION}"
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
SCOPE = "https://www.googleapis.com/auth/adwords"
ACCOUNT_MD = ROOT / "projects" / "google-ads" / "account.md"
KEYS = ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN"]
SETUP_HINT = "Setup: references/google-ads-api.md (Cloud project, Explorer access, Desktop OAuth client, --login)."
# Jonathan keeps the OAuth client ID under GOOGLE_ADS_API_KEY in secrets.env (2026-09-29); either name works.
CLIENT_ID_NAMES = ("GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_API_KEY")


def oauth_client_id():
    return next((v for v in (get_secret(n) for n in CLIENT_ID_NAMES) if v), None)


def missing_keys():
    have = {"GOOGLE_ADS_CLIENT_ID (or GOOGLE_ADS_API_KEY)": oauth_client_id(),
            "GOOGLE_ADS_CLIENT_SECRET": get_secret("GOOGLE_ADS_CLIENT_SECRET"),
            "GOOGLE_ADS_REFRESH_TOKEN": get_secret("GOOGLE_ADS_REFRESH_TOKEN")}
    return [k for k, v in have.items() if not v]


class AdsError(Exception):
    """A refusal from Google, with the reasons in plain lines."""

    def __init__(self, status, lines, raw=None):
        self.status, self.lines, self.raw = status, lines, raw
        super().__init__("; ".join(lines))


def customer_id():
    cid = get_secret("GOOGLE_ADS_CUSTOMER_ID")
    if not cid and ACCOUNT_MD.exists():
        m = re.search(r"\|\s*Customer id\s*\|\s*([\d-]{10,12})", ACCOUNT_MD.read_text(encoding="utf-8"))
        cid = m.group(1) if m else None
    if not cid:
        raise AdsError(0, ["No customer id: set GOOGLE_ADS_CUSTOMER_ID or fill projects/google-ads/account.md."])
    return cid.replace("-", "")


def _explain(resp):
    try:
        body = resp.json()
    except ValueError:
        return [f"HTTP {resp.status_code}: {resp.text[:300]}"], None
    err = body.get("error", body) if isinstance(body, dict) else {}
    lines = []
    for d in err.get("details", []) or []:
        for e in d.get("errors", []) or []:
            code = next(iter((e.get("errorCode") or {}).items()), ("", ""))
            where = ".".join(str(p.get("fieldName", "")) + (f"[{p['index']}]" if "index" in p else "")
                             for p in (e.get("location") or {}).get("fieldPathElements", []) or [])
            trig = (e.get("trigger") or {}).get("stringValue")
            lines.append(f"{code[1] or code[0]}: {e.get('message', '')}" + (f" (at {where})" if where else "")
                         + (f" [{trig}]" if trig else ""))
    if not lines:
        lines = [f"HTTP {resp.status_code} {err.get('status', '')}: {err.get('message', resp.text[:300])}"]
    return lines, body


class GoogleAds:
    def __init__(self):
        self.client_id = oauth_client_id()
        self.client_secret = get_secret("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh = get_secret("GOOGLE_ADS_REFRESH_TOKEN")
        missing = missing_keys()
        if missing:
            raise AdsError(0, [f"Missing {', '.join(missing)} in {SECRETS_ENV}. {SETUP_HINT}"])
        self.dev_token = get_secret("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.login_cid = (get_secret("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or "").replace("-", "")
        self.cid = customer_id()
        self._token, self._expires = None, 0
        self.s = requests.Session()

    def _access_token(self):
        if self._token and time.time() < self._expires - 60:
            return self._token
        r = requests.post(TOKEN_URL, data={"grant_type": "refresh_token", "client_id": self.client_id,
                                           "client_secret": self.client_secret, "refresh_token": self.refresh},
                          timeout=30)
        if r.status_code != 200:
            raise AdsError(r.status_code, [f"Google refused the login ({r.json().get('error', r.status_code)}). "
                                           "Run: python scripts/google_ads_api.py --login"])
        j = r.json()
        self._token, self._expires = j["access_token"], time.time() + int(j.get("expires_in", 3600))
        return self._token

    def _headers(self):
        h = {"Authorization": f"Bearer {self._access_token()}", "Content-Type": "application/json"}
        if self.dev_token:
            h["developer-token"] = self.dev_token
        if self.login_cid:
            h["login-customer-id"] = self.login_cid
        return h

    def _call(self, method, path, body=None):
        for attempt in range(3):
            r = self.s.request(method, f"{BASE}/{path}", headers=self._headers(),
                               data=None if body is None else json.dumps(body), timeout=(10, 120))
            if r.status_code in (429, 500, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code >= 400:
                lines, raw = _explain(r)
                raise AdsError(r.status_code, lines, raw)
            return r.json() if r.text else {}

    # ---- reads
    def accessible_customers(self):
        return self._call("GET", "customers:listAccessibleCustomers").get("resourceNames", [])

    def search(self, query):
        rows, token = [], None
        while True:
            body = {"query": query}
            if token:
                body["pageToken"] = token
            j = self._call("POST", f"customers/{self.cid}/googleAds:search", body)
            rows += j.get("results", [])
            token = j.get("nextPageToken")
            if not token:
                return rows

    def suggest_geo(self, names, country="US"):
        """Place names ('San Francisco, CA, United States') -> {name: geoTargetConstant resource name or None}."""
        out = {}
        for i in range(0, len(names), 20):
            chunk = names[i:i + 20]
            j = self._call("POST", "geoTargetConstants:suggest",
                           {"locale": "en", "countryCode": country, "locationNames": {"names": chunk}})
            best = {}
            for sug in j.get("geoTargetConstantSuggestions", []):
                term = sug.get("searchTerm")
                gtc = sug.get("geoTargetConstant") or {}
                if term and term not in best and gtc.get("status", "ENABLED") == "ENABLED":
                    best[term] = gtc.get("resourceName")
            for n in chunk:
                out[n] = best.get(n)
        return out

    # ---- changes
    def mutate(self, operations, validate_only=False):
        """One atomic googleAds:mutate. Temporary ids (negative numbers) link new objects inside the call."""
        if not operations:
            return {"mutateOperationResponses": []}
        return self._call("POST", f"customers/{self.cid}/googleAds:mutate",
                          {"mutateOperations": operations, "validateOnly": validate_only, "partialFailure": False})

    def rn(self, kind, rid):
        return f"customers/{self.cid}/{kind}/{rid}"


# ---------------------------------------------------------------- one-time login

def _save_secret(name, value):
    SECRETS_ENV.parent.mkdir(parents=True, exist_ok=True)
    lines = SECRETS_ENV.read_text(encoding="utf-8").splitlines() if SECRETS_ENV.exists() else []
    lines = [ln for ln in lines if not ln.strip().startswith(f"{name}=")] + [f"{name}={value}"]
    SECRETS_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def login():
    cid, secret = oauth_client_id(), get_secret("GOOGLE_ADS_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit(f"The client ID (GOOGLE_ADS_API_KEY or GOOGLE_ADS_CLIENT_ID) and GOOGLE_ADS_CLIENT_SECRET go in {SECRETS_ENV} first"
                 f" (missing: {', '.join(k for k, v in (('client ID', cid), ('GOOGLE_ADS_CLIENT_SECRET', secret)) if not v)}). {SETUP_HINT}")
    state, got = secrets.token_urlsafe(16), {}

    class Catch(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            ok = "code" in q and q.get("state", [""])[0] == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(("<p style='font:16px sans-serif'>" + ("Signed in. You can close this tab." if ok
                              else "Sign-in did not finish. Close this tab and run --login again.") + "</p>").encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Catch)
    redirect = f"http://127.0.0.1:{srv.server_address[1]}"
    url = AUTH_URL + "?" + urlencode({"client_id": cid, "redirect_uri": redirect, "response_type": "code",
                                      "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening Google sign-in. Sign in as the account that is admin on the Monarc Ads account.")
    print(f"If no browser opens, visit:\n{url}")
    threading.Thread(target=srv.handle_request, daemon=True).start()
    webbrowser.open(url)
    for _ in range(600):
        if got:
            break
        time.sleep(0.5)
    srv.server_close()
    if got.get("state") != state or "code" not in got:
        sys.exit(f"Sign-in did not finish ({got.get('error', 'no reply in 5 minutes')}).")
    r = requests.post(TOKEN_URL, data={"grant_type": "authorization_code", "code": got["code"], "client_id": cid,
                                       "client_secret": secret, "redirect_uri": redirect}, timeout=30)
    tok = r.json()
    if r.status_code != 200 or not tok.get("refresh_token"):
        sys.exit(f"Google did not return a refresh token ({tok.get('error_description') or tok.get('error') or r.status_code}).")
    _save_secret("GOOGLE_ADS_REFRESH_TOKEN", tok["refresh_token"])
    print(f"Saved GOOGLE_ADS_REFRESH_TOKEN to {SECRETS_ENV}. Next: python scripts/google_ads_api.py --check")


# ---------------------------------------------------------------- check

def check():
    ok = report_key_sources(["GOOGLE_ADS_API_KEY"] + KEYS + ["GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_DEVELOPER_TOKEN"])
    try:
        print(f"Customer id: {customer_id()} ({'secrets' if get_secret('GOOGLE_ADS_CUSTOMER_ID') else 'account.md, unverified'})")
    except AdsError as e:
        print(e)
    if missing_keys():
        sys.exit(f"Not connected yet; missing {', '.join(missing_keys())}. {SETUP_HINT}")
    g = GoogleAds()
    try:
        names = g.accessible_customers()
        print(f"This login reaches {len(names)} account(s): {', '.join(n.split('/')[-1] for n in names)}")
        rows = g.search("SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone, "
                        "customer.auto_tagging_enabled, customer.final_url_suffix, customer.status FROM customer")
        c = (rows[0] if rows else {}).get("customer", {})
        print(f"Account {c.get('id')} \"{c.get('descriptiveName')}\", {c.get('currencyCode')}, {c.get('timeZone')}, "
              f"status {c.get('status')}")
        print(f"Auto-tagging: {'on' if c.get('autoTaggingEnabled') else 'off'}; final URL suffix: "
              f"{c.get('finalUrlSuffix') or '(none)'}")
        camps = g.search("SELECT campaign.id, campaign.name, campaign.status FROM campaign "
                         "WHERE campaign.status != 'REMOVED'")
        print(f"Campaigns not removed: {len(camps)}")
        for r in camps:
            print(f"  {r['campaign']['id']}  {r['campaign']['status']:8}  {r['campaign']['name']}")
    except AdsError as e:
        print("Google refused:")
        for ln in e.lines:
            print(f"  {ln}")
        sys.exit(1)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--query", default="")
    a = ap.parse_args()
    if a.login:
        login()
    elif a.query:
        try:
            for r in GoogleAds().search(a.query):
                print(json.dumps(r))
        except AdsError as e:
            sys.exit("Google refused:\n  " + "\n  ".join(e.lines))
    else:
        check()


if __name__ == "__main__":
    main()
