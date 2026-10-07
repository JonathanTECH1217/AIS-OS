"""YouTube as the Monarc Build channel: upload a lead review private, publish it on his second go (2026-10-05).

Jonathan, 2026-10-05: "export those videos as long form for YouTube" and, on who presses the buttons, "I approve for
upload and publish." Two gos a video: one to upload (private), one to publish (public). The clone runs neither alone.

Usage:
  python scripts/youtube_api.py --login                 one time: Google's consent screen as jonathan@monarcbuild.com;
                                                        saves YOUTUBE_REFRESH_TOKEN to ~/.monarc/secrets.env. Refused
                                                        for any other account. Prints the channel's name as the check.
  python scripts/youtube_api.py status [video-id]       the channel; a video's privacy, upload and processing state
  python scripts/youtube_api.py upload <video.mp4> --meta <name>.youtube.json [--unlisted] [--again]
                                                        resumable upload, private unless --unlisted; writes video_id,
                                                        url, uploaded_on back into the json and a post record into
                                                        projects/crm/creative.json (the Creative tab's tag)
  python scripts/youtube_api.py publish <video-id>      sets the video public once YouTube has finished processing it;
                                                        writes published_on into the json beside the video
  python scripts/youtube_api.py check-meta <name>.youtube.json   the metadata checks only, no network

Keys: the OAuth client of the Google Ads setup (GOOGLE_ADS_API_KEY or GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET)
and YOUTUBE_REFRESH_TOKEN (written by --login). Scopes: youtube.upload (the upload) and youtube (videos.list and
videos.update, which the publish needs), plus the sign-in email. Setup and the caveats (the API Services audit, the
consent screen in Testing): references/youtube-api.md.
Quota: an upload costs 1,600 of the project's 10,000 units a day: six uploads a day at most.
"""
import argparse
import base64
import json
import secrets
import sys
import threading
import time
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import SECRETS_ENV, get_secret  # noqa: E402
from google_ads_api import AUTH_URL, TOKEN_URL, _save_secret, oauth_client_id  # noqa: E402

API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
SCOPE = "openid email https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"
ACCOUNT = "jonathan@monarcbuild.com"
TOKEN_NAME = "YOUTUBE_REFRESH_TOKEN"
CHUNK = 8 * 1024 * 1024          # a multiple of 256 KB, as the resumable upload asks
TITLE_MAX, DESC_MAX, TAGS_MAX = 100, 5000, 500
ROOT = Path(__file__).resolve().parent.parent


class YouTubeError(Exception):
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
            self.wfile.write(("<p style='font:16px sans-serif'>" + ("YouTube connected for Monarc Build. You can close this tab."
                              if ok else "Sign-in did not finish. Close this tab; the AIOS will start it again.") + "</p>").encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Catch)
    redirect = f"http://127.0.0.1:{srv.server_address[1]}"
    url = AUTH_URL + "?" + urlencode({"client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
                                      "access_type": "offline", "prompt": "consent select_account", "state": state,
                                      "login_hint": ACCOUNT})
    print(f"Opening Google sign-in. Pick {ACCOUNT} (not sumreat17). If Google asks which channel, pick Monarc Build's. Then Allow.")
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
    try:
        ch = YouTube().channel()
        print(f"Channel: {ch['title']} ({ch['id']}). If that is not Monarc Build's channel, run --login again and pick it.")
    except YouTubeError as e:
        print(f"Signed in, but the channel read failed: {e}")


class YouTube:
    def __init__(self):
        self.client_id, self.secret = oauth_client_id(), get_secret("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh = get_secret(TOKEN_NAME)
        if not (self.client_id and self.secret and self.refresh):
            raise YouTubeError(f"Not connected: run python scripts/youtube_api.py --login ({TOKEN_NAME} missing).")
        self._token, self._exp = None, 0

    def token(self):
        if not self._token or time.time() > self._exp - 60:
            r = requests.post(TOKEN_URL, data={"grant_type": "refresh_token", "refresh_token": self.refresh,
                                               "client_id": self.client_id, "client_secret": self.secret}, timeout=30)
            j = r.json()
            if r.status_code != 200:
                raise YouTubeError(f"Token refresh refused: {j.get('error_description') or j.get('error')}. "
                                   "A consent screen left in Testing expires the token after 7 days: run --login again.")
            self._token, self._exp = j["access_token"], time.time() + int(j.get("expires_in", 3600))
        return self._token

    def call(self, method, path, **kw):
        r = requests.request(method, API + path, headers={"Authorization": f"Bearer {self.token()}"}, timeout=60, **kw)
        if r.status_code >= 300:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:300])
            except ValueError:
                msg = r.text[:300]
            raise YouTubeError(f"YouTube refused ({r.status_code}): {msg}")
        return r.json() if r.text else {}

    def channel(self):
        j = self.call("GET", "/channels", params={"part": "snippet", "mine": "true"})
        items = j.get("items") or []
        if not items:
            raise YouTubeError("This account has no YouTube channel. Make one in YouTube Studio first.")
        return {"id": items[0]["id"], "title": items[0]["snippet"]["title"]}

    def video(self, vid):
        j = self.call("GET", "/videos", params={"part": "status,snippet,processingDetails", "id": vid})
        items = j.get("items") or []
        if not items:
            raise YouTubeError(f"No video {vid} on this channel.")
        it = items[0]
        return {"id": vid, "title": it["snippet"]["title"], "privacy": it["status"].get("privacyStatus"),
                "upload": it["status"].get("uploadStatus"), "processing": (it.get("processingDetails") or {}).get("processingStatus"),
                "url": f"https://youtu.be/{vid}"}

    def upload(self, path, meta, privacy="private"):
        path = Path(path)
        size = path.stat().st_size
        body = {"snippet": {"title": meta["title"], "description": meta.get("description", ""), "tags": meta.get("tags", []),
                            "categoryId": str(meta.get("category", 27))},
                "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": bool(meta.get("made_for_kids", False))}}
        r = requests.post(UPLOAD, params={"uploadType": "resumable", "part": "snippet,status"},
                          headers={"Authorization": f"Bearer {self.token()}", "Content-Type": "application/json; charset=UTF-8",
                                   "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                          data=json.dumps(body), timeout=60)
        if r.status_code != 200 or not r.headers.get("Location"):
            try:
                msg = r.json().get("error", {}).get("message", r.text[:300])
            except ValueError:
                msg = r.text[:300]
            raise YouTubeError(f"YouTube refused the upload ({r.status_code}): {msg}")
        session = r.headers["Location"]
        sent = 0
        with path.open("rb") as fh:
            while sent < size:
                fh.seek(sent)
                chunk = fh.read(CHUNK)
                end = sent + len(chunk) - 1
                pr = requests.put(session, headers={"Authorization": f"Bearer {self.token()}", "Content-Type": "video/mp4",
                                                    "Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{end}/{size}"},
                                  data=chunk, timeout=600)
                if pr.status_code == 308:
                    rng = pr.headers.get("Range")
                    sent = int(rng.split("-")[1]) + 1 if rng else end + 1
                    print(f"  sent {sent / 1048576:.1f} of {size / 1048576:.1f} MB", flush=True)
                    continue
                if pr.status_code in (200, 201):
                    return pr.json()["id"]
                if pr.status_code in (500, 502, 503, 504):
                    time.sleep(3)      # ask where it got to, then go on from there
                    q = requests.put(session, headers={"Authorization": f"Bearer {self.token()}", "Content-Length": "0",
                                                       "Content-Range": f"bytes */{size}"}, timeout=60)
                    rng = q.headers.get("Range")
                    sent = int(rng.split("-")[1]) + 1 if rng else 0
                    continue
                raise YouTubeError(f"Upload stopped ({pr.status_code}): {pr.text[:300]}")
        raise YouTubeError("Upload ended without a video id.")

    def publish(self, vid):
        v = self.video(vid)
        if v["processing"] != "succeeded":
            raise YouTubeError(f"YouTube is still processing {vid} ({v['processing'] or v['upload']}). Try again in a few minutes.")
        it = self.call("PUT", "/videos", params={"part": "status"},
                       json={"id": vid, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}})
        return it.get("status", {}).get("privacyStatus")


# ---------------------------------------------------------------- the metadata checks

def check_meta(meta):
    """What is wrong with a .youtube.json before any upload. Returns a list of problems; empty means fine."""
    bad = []
    t = meta.get("title") or ""
    if not t.strip():
        bad.append("no title")
    if len(t) > TITLE_MAX:
        bad.append(f"title is {len(t)} characters; {TITLE_MAX} is the most")
    if "<" in t or ">" in t:
        bad.append("title has < or >, which YouTube refuses")
    d = meta.get("description") or ""
    if len(d) > DESC_MAX:
        bad.append(f"description is {len(d)} characters; {DESC_MAX} is the most")
    if not d.strip():
        bad.append("no description (the first line says who it is for)")
    tags = meta.get("tags") or []
    if sum(len(x) + 2 for x in tags) > TAGS_MAX:
        bad.append("tags run past 500 characters in all")
    key = (meta.get("company_key") or "").lower()
    if key:
        stem = key.split(".")[0].replace("-", " ")
        for piece in {stem} | set(stem.split()):
            if len(piece) >= 5 and piece in (t + " " + d).lower():
                bad.append(f"the prospect's name ('{piece}') is in the title or description; a named company is never public before its deal closes")
                break
    if meta.get("privacy", "private") not in ("private", "unlisted", "public"):
        bad.append("privacy must be private, unlisted, or public")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--login", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("status")
    s.add_argument("video_id", nargs="?")
    u = sub.add_parser("upload")
    u.add_argument("video")
    u.add_argument("--meta", required=True)
    u.add_argument("--unlisted", action="store_true")
    u.add_argument("--again", action="store_true", help="upload even though the json already has a video_id")
    p = sub.add_parser("publish")
    p.add_argument("video_id")
    c = sub.add_parser("check-meta")
    c.add_argument("meta")
    a = ap.parse_args(argv)

    if a.login:
        login()
        return 0
    if a.cmd == "check-meta":
        bad = check_meta(json.loads(Path(a.meta).read_text(encoding="utf-8")))
        print("\n".join(bad) if bad else "metadata fine")
        return 1 if bad else 0
    if not a.cmd:
        ap.print_help()
        return 0
    try:
        yt = YouTube()
        if a.cmd == "status":
            ch = yt.channel()
            print(f"channel: {ch['title']} ({ch['id']})")
            if a.video_id:
                print(json.dumps(yt.video(a.video_id), indent=1))
        elif a.cmd == "upload":
            meta_path = Path(a.meta)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            bad = check_meta(meta)
            if bad:
                sys.exit("Not uploaded:\n" + "\n".join("  " + b for b in bad))
            if meta.get("video_id") and not a.again:
                sys.exit(f"Already uploaded as {meta['video_id']} ({meta.get('url')}). Pass --again to upload a second copy.")
            privacy = "unlisted" if a.unlisted else "private"
            print(f"Uploading {a.video} as {privacy} to {yt.channel()['title']}...", flush=True)
            vid = yt.upload(a.video, meta, privacy)
            today = date.today().isoformat()
            meta.update({"video_id": vid, "url": f"https://youtu.be/{vid}", "uploaded_on": today, "privacy": privacy})
            meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
            from creative_record import record
            record(a.video, "youtube", vid, meta["url"], privacy, today)
            print(f"Uploaded as {privacy}: {meta['url']}. YouTube is processing it; `status {vid}` shows when. "
                  "His second go publishes it (`publish`), or he sets Public in YouTube Studio.")
        elif a.cmd == "publish":
            state = yt.publish(a.video_id)
            today = date.today().isoformat()
            hit = None
            for jp in (ROOT / "media" / "looms").glob("*/*.youtube.json"):
                m = json.loads(jp.read_text(encoding="utf-8"))
                if m.get("video_id") == a.video_id:
                    m.update({"privacy": state, "published_on": today if state == "public" else m.get("published_on")})
                    jp.write_text(json.dumps(m, indent=1), encoding="utf-8")
                    hit = jp
                    from creative_record import record
                    record(jp.with_name(m.get("video", jp.stem.replace(".youtube", "") + ".mp4")), "youtube", a.video_id,
                           f"https://youtu.be/{a.video_id}", state, today)
            print(f"{a.video_id} is now {state}" + (f" (recorded in {hit.name})" if hit else "") +
                  (". If it still reads private, the project has not passed YouTube's API audit yet: set Public in YouTube Studio." if state != "public" else "."))
    except YouTubeError as e:
        sys.exit(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
