"""Instagram: Monarc's own account's numbers, and the public posts of any business account (2026-10-05).

Jonathan, 2026-10-05: "let's work on the instagram feed pull. This should give access to analytics as well", then
"I only pull analytics for my personal and I pull meta data on theirs." Meta's own route, the Instagram API with
Instagram Login: Jonathan's account signs in once and a token comes back. With it:

  his own account    the feed and the numbers (feed, insights)
  anyone else's      Business Discovery: the public profile and posts of another business or creator account, by its
                     handle, with no sign-in from them (discover). Captions, pictures, dates, links, likes, comments,
                     followers, bio. Never their numbers; Meta does not hand those out.

  python scripts/instagram_api.py check
        whose token it is, the followers, the post count. No change to anything.
  python scripts/instagram_api.py feed [--limit 12] [--save]
        Monarc's newest posts: date, kind, caption, link, likes, comments. --save also puts each picture in
        projects/research/monarc-build/instagram/ and writes instagram.json beside it.
  python scripts/instagram_api.py insights [--limit 12]
        Monarc's numbers and each post's numbers. Meta renames these often, so each one is asked for by itself and
        the ones the account does not have are listed, not fatal. Writes instagram-insights.json.
  python scripts/instagram_api.py discover <handle> [--limit 12] [--save] [--name slug]
        another business account's public profile and posts, through Monarc's token. --save puts the pictures in
        projects/research/<slug>/instagram/ and writes instagram.json. Only a business or creator account; a
        personal or private one comes back as not found.
  python scripts/instagram_api.py refresh
        a token lives 60 days; this trades it for a fresh one and saves it. Run it monthly.

Token (never in a tracked file or in chat): INSTAGRAM_TOKEN in %USERPROFILE%\\.monarc\\secrets.env, Monarc's own
account. A client that wants its numbers read connects the same way, INSTAGRAM_TOKEN_<SLUG>, and --account <slug>
picks it. Setup: references/instagram-api.md. Read only. This script never posts, comments, or messages.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, SECRETS_ENV, get_secret  # noqa: E402

API = "https://graph.instagram.com"
OUT = ROOT / "projects" / "research"
MEDIA_FIELDS = "id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count"
# Meta's names at the time of writing, newest first; each is tried alone (the old "impressions" went away in 2025).
POST_METRICS = ("reach", "views", "likes", "comments", "shares", "saved", "total_interactions", "impressions")
ACCOUNT_METRICS = ("reach", "views", "accounts_engaged", "total_interactions", "profile_views", "follower_count", "impressions")


class InstagramError(Exception):
    pass


def token_name(account):
    return "INSTAGRAM_TOKEN" + ("_" + re.sub(r"[^A-Z0-9]+", "_", account.upper()).strip("_") if account else "")


def token(account):
    name = token_name(account)
    tok = get_secret(name)
    if not tok:
        raise InstagramError(f"{name} is not in {SECRETS_ENV}. The account has to connect first: references/instagram-api.md.")
    return tok


def call(path, tok, **params):
    r = requests.get(f"{API}/{path.lstrip('/')}", params=dict(params, access_token=tok), timeout=40)
    try:
        j = r.json()
    except ValueError:
        raise InstagramError(f"Instagram answered {r.status_code} with no JSON.") from None
    if r.status_code != 200 or "error" in j:
        e = j.get("error", {})
        raise InstagramError(f"Instagram refused ({r.status_code}, code {e.get('code')}): {e.get('message', '')[:240]}")
    return j


def me(tok):
    return call("me", tok, fields="user_id,username,name,account_type,media_count,followers_count")


def media(tok, limit):
    out, after = [], None
    while len(out) < limit:
        page = call("me/media", tok, fields=MEDIA_FIELDS, limit=min(50, limit - len(out)), **({"after": after} if after else {}))
        out += page.get("data", [])
        after = page.get("paging", {}).get("cursors", {}).get("after")
        if not after or not page.get("data"):
            break
    return out[:limit]


def folder(account, who):
    d = OUT / (re.sub(r"[^a-z0-9]+", "-", (account or who.get("username") or "instagram").lower()).strip("-"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_check(a):
    who = me(token(a.account))
    print(f"@{who.get('username')} | {who.get('account_type')} | {who.get('followers_count')} followers | {who.get('media_count')} posts | token {token_name(a.account)}")


def cmd_feed(a):
    tok = token(a.account)
    who = me(tok)
    posts = media(tok, a.limit)
    d = folder(a.account, who)
    rows = []
    for i, p in enumerate(posts):
        row = {"id": p["id"], "date": (p.get("timestamp") or "")[:10], "kind": p.get("media_product_type") or p.get("media_type"),
               "caption": p.get("caption") or "", "link": p.get("permalink"), "likes": p.get("like_count"), "comments": p.get("comments_count"), "file": None}
        src = p.get("media_url") if p.get("media_type") != "VIDEO" else p.get("thumbnail_url")
        if a.save and src:  # a reel's own file is left alone; its cover picture is what a page shows
            (d / "instagram").mkdir(exist_ok=True)
            img = requests.get(src, timeout=90)
            if img.status_code == 200:
                f = d / "instagram" / f"{row['date']}-{p['id']}.jpg"
                f.write_bytes(img.content)
                row["file"] = f.relative_to(ROOT).as_posix()
        rows.append(row)
        print(f"{i:02d} {row['date']} {str(row['kind'])[:8]:8} likes {row['likes']} comments {row['comments']} | {row['caption'][:90].replace(chr(10), ' ')}")
    if a.save:
        (d / "instagram.json").write_text(json.dumps({"read": date.today().isoformat(), "account": who, "posts": rows}, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
        print(f"saved: {d.relative_to(ROOT).as_posix()}/instagram.json and {sum(1 for r in rows if r['file'])} pictures")


def one_metric(path, tok, metric, **params):
    """One number, or the reason the account does not have it. Some metrics want metric_type=total_value."""
    for extra in ({}, {"metric_type": "total_value"}):
        try:
            j = call(path, tok, metric=metric, **params, **extra)
        except InstagramError as e:
            last = str(e)
            continue
        row = (j.get("data") or [{}])[0]
        if "total_value" in row:
            return row["total_value"].get("value"), None
        vals = [v.get("value") for v in row.get("values", []) if isinstance(v.get("value"), (int, float))]
        return (sum(vals) if vals else None), None
    return None, last


def cmd_insights(a):
    tok = token(a.account)
    who = me(tok)
    d = folder(a.account, who)
    account, missing = {}, {}
    for m in ACCOUNT_METRICS:
        val, why = one_metric("me/insights", tok, m, period="day")
        if why:
            missing[m] = why[:160]
        else:
            account[m] = val
    print(f"@{who.get('username')} | {who.get('followers_count')} followers | the last day: " + (", ".join(f"{k} {v}" for k, v in account.items()) or "no numbers"))
    posts = []
    for p in media(tok, a.limit):
        nums = {}
        for m in POST_METRICS:
            val, why = one_metric(f"{p['id']}/insights", tok, m)
            if not why:
                nums[m] = val
        posts.append({"id": p["id"], "date": (p.get("timestamp") or "")[:10], "link": p.get("permalink"), "caption": (p.get("caption") or "")[:140], "numbers": nums})
        print(f"   {posts[-1]['date']} | " + (", ".join(f"{k} {v}" for k, v in nums.items()) or "no numbers") + f" | {posts[-1]['caption'][:60].replace(chr(10), ' ')}")
    if missing:
        print("not available on this account: " + ", ".join(missing))
    (d / "instagram-insights.json").write_text(json.dumps({"read": date.today().isoformat(), "account": who, "day": account, "not_available": missing,
                                                           "posts": posts}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"saved: {d.relative_to(ROOT).as_posix()}/instagram-insights.json")


def cmd_discover(a):
    """Another business account's public profile and posts, read with Monarc's own token (Meta's Business Discovery)."""
    tok = token(a.account)
    handle = a.handle.lstrip("@").strip("/").rsplit("/", 1)[-1]
    inner = f"media.limit({min(a.limit, 50)}){{{MEDIA_FIELDS}}}"
    fields = f"business_discovery.username({handle}){{username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url,{inner}}}"
    try:
        j = call("me", tok, fields=fields)
    except InstagramError as e:
        if "not found" in str(e).lower() or "code 110" in str(e) or "code 100" in str(e):
            sys.exit(f"@{handle}: Instagram has no business or creator account by that name that it will show. A personal or private account cannot be read. ({e})")
        raise
    bd = j.get("business_discovery") or {}
    posts = (bd.get("media") or {}).get("data") or []
    d = folder(a.name or handle, bd)
    print(f"@{bd.get('username')} | {bd.get('name') or ''} | {bd.get('followers_count')} followers | {bd.get('media_count')} posts | {bd.get('website') or ''}")
    if bd.get("biography"):
        print("   bio:", bd["biography"][:160].replace("\n", " "))
    rows = []
    for i, p in enumerate(posts[:a.limit]):
        row = {"id": p["id"], "date": (p.get("timestamp") or "")[:10], "kind": p.get("media_product_type") or p.get("media_type"),
               "caption": p.get("caption") or "", "link": p.get("permalink"), "likes": p.get("like_count"), "comments": p.get("comments_count"), "file": None}
        src = p.get("media_url") if p.get("media_type") != "VIDEO" else p.get("thumbnail_url")
        if a.save and src:
            (d / "instagram").mkdir(exist_ok=True)
            img = requests.get(src, timeout=90)
            if img.status_code == 200:
                f = d / "instagram" / f"{row['date']}-{p['id']}.jpg"
                f.write_bytes(img.content)
                row["file"] = f.relative_to(ROOT).as_posix()
        rows.append(row)
        print(f"{i:02d} {row['date']} {str(row['kind'])[:8]:8} likes {row['likes']} comments {row['comments']} | {row['caption'][:90].replace(chr(10), ' ')}")
    if a.save:
        profile = {k: bd.get(k) for k in ("username", "name", "biography", "website", "followers_count", "follows_count", "media_count", "profile_picture_url")}
        (d / "instagram.json").write_text(json.dumps({"read": date.today().isoformat(), "how": "business discovery through Monarc's token; their numbers are not available this way",
                                                      "account": profile, "posts": rows}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"saved: {d.relative_to(ROOT).as_posix()}/instagram.json and {sum(1 for r in rows if r['file'])} pictures")


def cmd_refresh(a):
    from google_ads_api import _save_secret
    j = call("refresh_access_token", token(a.account), grant_type="ig_refresh_token")
    _save_secret(token_name(a.account), j["access_token"])
    print(f"{token_name(a.account)} refreshed; good for about {int(j.get('expires_in', 0)) // 86400} days.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "feed", "insights", "discover", "refresh"):
        p = sub.add_parser(name)
        p.add_argument("--account", default="")
        if name == "discover":
            p.add_argument("handle")
            p.add_argument("--name", default="")
        if name in ("feed", "insights", "discover"):
            p.add_argument("--limit", type=int, default=12)
        if name in ("feed", "discover"):
            p.add_argument("--save", action="store_true")
    a = ap.parse_args()
    try:
        {"check": cmd_check, "feed": cmd_feed, "insights": cmd_insights, "discover": cmd_discover, "refresh": cmd_refresh}[a.cmd](a)
    except InstagramError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
