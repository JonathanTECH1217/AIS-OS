"""Google Calendar as jonathan@monarcbuild.com: events, invites, and Google Meet links that carry the Monarc account.

Usage:
  python scripts/google_calendar_api.py --login    one time: Google's consent screen in the browser, signed in as
                                                   jonathan@monarcbuild.com; saves GOOGLE_CALENDAR_REFRESH_TOKEN to
                                                   ~/.monarc/secrets.env (never printed). Refused for any other account.
  python scripts/google_calendar_api.py --check    who the login is, and the next few events on its calendar

Why (Jonathan, 2026-10-01): an invite, email, or Meet link that shows sumreat17 "is a really, really bad look". The
claude.ai calendar connector and the booking Apps Script both run as sumreat17@gmail.com; this runs as the Monarc
account, so the organizer, the invite's sender, and the Meet link's owner are jonathan@monarcbuild.com.

Keys: the OAuth client of the Google Ads setup (GOOGLE_ADS_API_KEY or GOOGLE_ADS_CLIENT_ID, and
GOOGLE_ADS_CLIENT_SECRET, a Desktop app client in the Monarc Build Cloud project, with the Google Calendar API turned
on 2026-10-01) and GOOGLE_CALENDAR_REFRESH_TOKEN (written by --login). Scope: calendar.events only, plus the
sign-in email so the login can be checked.

Times: the event is stored in Eastern on Jonathan's calendar; the guest's own calendar shows it in their zone. The
rule (CLAUDE.md): emails and invites state the prospect's time, his calendar holds his time.
"""
import argparse
import base64
import json
import secrets
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import SECRETS_ENV, get_secret  # noqa: E402
from google_ads_api import AUTH_URL, TOKEN_URL, _save_secret, oauth_client_id  # noqa: E402

API = "https://www.googleapis.com/calendar/v3"
SCOPE = "openid email https://www.googleapis.com/auth/calendar.events"
ACCOUNT = "jonathan@monarcbuild.com"
TOKEN_NAME = "GOOGLE_CALENDAR_REFRESH_TOKEN"
HOME_TZ = "America/New_York"
# An email an hour before every meeting (Jonathan, 2026-10-05). Google sends it to the account's own address; a
# reminder belongs to the calendar's owner, so no guest sees it. The pop-up is the calendar's own default, kept.
EMAIL_AHEAD = 60
REMINDERS = [{"method": "popup", "minutes": 30}, {"method": "email", "minutes": EMAIL_AHEAD}]


class CalendarError(Exception):
    pass


def _email_from_id_token(tok):
    try:
        payload = tok.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("email", "")
    except (IndexError, ValueError):
        return ""


def login():
    cid, secret = oauth_client_id(), get_secret("GOOGLE_ADS_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit(f"The OAuth client ID and GOOGLE_ADS_CLIENT_SECRET must be in {SECRETS_ENV} (the Google Ads setup).")
    state, got = secrets.token_urlsafe(16), {}

    class Catch(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            ok = "code" in q and q.get("state", [""])[0] == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(("<p style='font:16px sans-serif'>" + ("Calendar connected for Monarc Build. You can close this tab."
                              if ok else "Sign-in did not finish. Close this tab; the AIOS will start it again.") + "</p>").encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Catch)
    redirect = f"http://127.0.0.1:{srv.server_address[1]}"
    url = AUTH_URL + "?" + urlencode({"client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
                                      "access_type": "offline", "prompt": "consent select_account", "state": state,
                                      "login_hint": ACCOUNT})
    print(f"Opening Google sign-in. Pick {ACCOUNT} (not sumreat17), then Allow.")
    print(f"If no browser opens, visit:\n{url}", flush=True)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    webbrowser.open(url)
    for _ in range(1200):
        if got:
            break
        time.sleep(0.5)
    srv.server_close()
    if got.get("state") != state or "code" not in got:
        sys.exit(f"Sign-in did not finish ({got.get('error', 'no reply in 10 minutes')}).")
    r = requests.post(TOKEN_URL, data={"grant_type": "authorization_code", "code": got["code"], "client_id": cid,
                                       "client_secret": secret, "redirect_uri": redirect}, timeout=30)
    tok = r.json()
    if r.status_code != 200 or not tok.get("refresh_token"):
        sys.exit(f"Google did not return a refresh token ({tok.get('error_description') or tok.get('error') or r.status_code}).")
    who = _email_from_id_token(tok.get("id_token", "")).lower()
    if who != ACCOUNT:
        sys.exit(f"Signed in as {who or 'an unknown account'}, not {ACCOUNT}. Nothing saved; run it again and pick {ACCOUNT}.")
    _save_secret(TOKEN_NAME, tok["refresh_token"])
    print(f"Connected as {who}. Saved {TOKEN_NAME} to {SECRETS_ENV}.")


class Calendar:
    def __init__(self):
        self.client_id, self.secret = oauth_client_id(), get_secret("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh = get_secret(TOKEN_NAME)
        if not (self.client_id and self.secret and self.refresh):
            raise CalendarError(f"Not connected: run python scripts/google_calendar_api.py --login ({TOKEN_NAME} missing).")
        self._token, self._exp = None, 0

    def token(self):
        if not self._token or time.time() > self._exp - 60:
            r = requests.post(TOKEN_URL, data={"grant_type": "refresh_token", "refresh_token": self.refresh,
                                               "client_id": self.client_id, "client_secret": self.secret}, timeout=30)
            j = r.json()
            if r.status_code != 200:
                raise CalendarError(f"Token refresh refused: {j.get('error_description') or j.get('error')}")
            self._token, self._exp = j["access_token"], time.time() + int(j.get("expires_in", 3600))
        return self._token

    def call(self, method, path, **kw):
        r = requests.request(method, API + path, headers={"Authorization": f"Bearer {self.token()}"}, timeout=30, **kw)
        if r.status_code >= 300:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:300])
            except ValueError:
                msg = r.text[:300]
            raise CalendarError(f"Google Calendar refused ({r.status_code}): {msg}")
        return r.json() if r.text else {}

    def upcoming(self, n=5):
        now = datetime.now(timezone.utc).isoformat()
        return self.call("GET", "/calendars/primary/events", params={"timeMin": now, "maxResults": n, "singleEvents": "true",
                                                                       "orderBy": "startTime"}).get("items", [])

    def create(self, summary, start, minutes=15, description="", guests=(), meet=True, send=False):
        """An event on Jonathan's primary calendar, stored in Eastern. guests: emails. send=True has Google email the
        invite from jonathan@monarcbuild.com; send=False keeps it quiet (a hold)."""
        end = start + timedelta(minutes=minutes)
        body = {"summary": summary, "description": description,
                "start": {"dateTime": start.astimezone(timezone.utc).isoformat(), "timeZone": HOME_TZ},
                "end": {"dateTime": end.astimezone(timezone.utc).isoformat(), "timeZone": HOME_TZ},
                "attendees": [{"email": g} for g in guests],
                "reminders": {"useDefault": False, "overrides": REMINDERS}, "guestsCanModify": False}
        if meet:
            body["conferenceData"] = {"createRequest": {"requestId": uuid.uuid4().hex,
                                                        "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
        return self.call("POST", "/calendars/primary/events", json=body,
                         params={"conferenceDataVersion": 1, "sendUpdates": "all" if send else "none"})

    def window(self, calendar_id, lo, hi):
        """Every event between two times on one calendar, with its guests and their answers, and the calendar's
        default reminders. The login owns its own calendar and the booking calendar, so it reads both."""
        r = self.call("GET", f"/calendars/{quote(calendar_id, safe='')}/events",
                      params={"timeMin": lo.isoformat(), "timeMax": hi.isoformat(), "singleEvents": "true",
                              "orderBy": "startTime", "maxResults": 250})
        return r.get("items", []), r.get("defaultReminders", [])

    @staticmethod
    def has_email_reminder(ev, defaults, minutes=EMAIL_AHEAD):
        rem = ev.get("reminders") or {}
        current = defaults if rem.get("useDefault") else rem.get("overrides") or []
        return any(o.get("method") == "email" and o.get("minutes") == minutes for o in current)

    def remind_by_email(self, calendar_id, ev, defaults, minutes=EMAIL_AHEAD):
        """Adds the email reminder to one event and keeps the reminders it has. No guest is told."""
        rem = ev.get("reminders") or {}
        current = list(defaults if rem.get("useDefault") else rem.get("overrides") or [])
        overrides = (current + [{"method": "email", "minutes": minutes}])[-5:]  # Google allows five
        return self.call("PATCH", f"/calendars/{quote(calendar_id, safe='')}/events/{quote(ev['id'], safe='')}",
                         json={"reminders": {"useDefault": False, "overrides": overrides}}, params={"sendUpdates": "none"})


def check():
    cal = Calendar()
    items = cal.upcoming()
    print(f"Connected ({TOKEN_NAME} present). Next {len(items)} event(s) on the Monarc calendar:")
    for e in items:
        s = e.get("start", {})
        print(f"  {s.get('dateTime') or s.get('date')}  {e.get('summary', '(no title)')}  organizer {e.get('organizer', {}).get('email')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.login:
        login()
    elif a.check:
        try:
            check()
        except CalendarError as e:
            sys.exit(str(e))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
