"""Send one command to the running browser_driver.py and print the result as JSON.

Usage:
  python scripts/browser_cmd.py goto https://example.com
  python scripts/browser_cmd.py snapshot
  python scripts/browser_cmd.py click "Download PDF"
  python scripts/browser_cmd.py click '{"role": "button", "name": "Export"}'
  python scripts/browser_cmd.py fill "input[name=q]" "whole home audio"
  python scripts/browser_cmd.py download "Download"
  python scripts/browser_cmd.py wait 2000
  python scripts/browser_cmd.py links
  python scripts/browser_cmd.py eval "document.title"
  python scripts/browser_cmd.py quit
A JSON object as the sole argument after the op is passed through as args.
"""
import sys, json, time, uuid
from pathlib import Path

BASE = Path.home() / "AppData" / "Local" / "MonarcAIOS" / "browser"
CMD_DIR = BASE / "commands"
RES_DIR = BASE / "results"


def build_args(op, rest):
    if len(rest) == 1 and rest[0].strip().startswith("{"):
        return json.loads(rest[0])
    if op == "goto":
        return {"url": rest[0]}
    if op in ("click", "download"):
        return {"text": " ".join(rest)}
    if op == "fill":
        return {"selector": rest[0], "value": " ".join(rest[1:])}
    if op == "press":
        return {"key": rest[0]}
    if op == "wait":
        return {"ms": int(rest[0])} if rest and rest[0].isdigit() else ({"selector": rest[0]} if rest else {"ms": 1000})
    if op == "screenshot":
        return {"path": rest[0]} if rest else {}
    if op == "eval":
        return {"js": " ".join(rest)}
    if op == "switch":
        return {"index": int(rest[0])}
    if op == "newtab":
        return {"url": rest[0]} if rest else {}
    if op in ("snapshot", "text", "html", "links"):
        return {"max_chars": int(rest[0])} if rest and rest[0].isdigit() else {}
    return {}


def main(argv):
    if not argv:
        sys.exit(__doc__)
    op, rest = argv[0], argv[1:]
    timeout = 120
    if not CMD_DIR.exists():
        sys.exit("browser_driver.py is not running (no commands folder)")
    cid = f"{time.strftime('%H%M%S')}-{uuid.uuid4().hex[:6]}"
    (CMD_DIR / f"{cid}.json").write_text(json.dumps({"op": op, "args": build_args(op, rest)}), encoding="utf-8")
    res = RES_DIR / f"{cid}.json"
    t0 = time.time()
    while not res.exists():
        if time.time() - t0 > timeout:
            sys.exit(f"no result after {timeout}s. Is browser_driver.py running?")
        time.sleep(0.2)
    time.sleep(0.05)
    out = json.loads(res.read_text(encoding="utf-8"))
    res.unlink()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
