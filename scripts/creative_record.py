"""The Creative tab's record of where a piece went (2026-10-05).

projects/crm/creative.json, "published": {"file:media/<path>": {"on": day or None, "posts": [...]}}. "on" is the day
it counts as published (his hand mark on the tab, or the day a post went public). Each post: platform, id, url, on,
state ("private", "unlisted", "public"). youtube_api.py writes here; the CRM reads it. Kept apart from crm_server.py
so a script never imports the server.

  python scripts/creative_record.py show
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREATIVE = ROOT / "projects" / "crm" / "creative.json"


def media_key(path):
    """'file:media/looms/<set>/<name>.mp4' for a video under media/, the key the Creative tab uses."""
    p = Path(path).resolve()
    rel = p.relative_to(ROOT.resolve()).as_posix()
    if not rel.startswith("media/"):
        raise ValueError(f"{path} is not under media/")
    return "file:" + rel


def load():
    try:
        cfg = json.loads(CREATIVE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    cfg.setdefault("opusclip_projects", [])
    cfg.setdefault("published", {})
    for k, v in list(cfg["published"].items()):
        if isinstance(v, str):
            cfg["published"][k] = {"on": v, "posts": []}
    return cfg


def save(cfg):
    CREATIVE.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def record(path, platform, post_id, url, state, on=None):
    """Add or update one post on a piece. A public post also sets the piece's published day when it has none."""
    cfg = load()
    key = media_key(path)
    rec = cfg["published"].setdefault(key, {"on": None, "posts": []})
    on = on or date.today().isoformat()
    post = next((p for p in rec["posts"] if p.get("platform") == platform and p.get("id") == post_id), None)
    if post is None:
        post = {"platform": platform, "id": post_id}
        rec["posts"].append(post)
    post.update({"url": url, "state": state, "on": on})
    if state == "public" and not rec.get("on"):
        rec["on"] = on
    save(cfg)
    return rec


if __name__ == "__main__":
    if sys.argv[1:] == ["show"]:
        for k, v in load()["published"].items():
            print(k, json.dumps(v))
    else:
        print(__doc__)
