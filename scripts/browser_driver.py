"""Drive a real Chrome window from the AIOS.

Launches the installed Google Chrome with its own persistent profile at
%LOCALAPPDATA%\\MonarcAIOS\\browser\\chrome-profile (logins survive restarts), then executes JSON
commands dropped into the commands folder and writes results next to them. Jonathan can click in
the same window at any time. Every download that happens in the window, whether Jonathan clicks
it or the AIOS does, is saved to the downloads folder and logged to downloads.jsonl, so one manual
download shows the pattern for a batch.

Usage:
  python scripts/browser_driver.py [--downloads DIR] [--url URL]
  python scripts/browser_cmd.py <op> [args...]     send one command and print the result

Ops (browser_cmd.py): goto URL | snapshot | text | html | links | click <text or {json}> |
  fill <selector> <value> | press <key> | wait <ms or selector> | screenshot [path] |
  download <text or {json}> | eval <js> | tabs | switch <i> | newtab [url] | quit
Locators as JSON: {"selector": css}, {"role": "button", "name": "Download"}, {"text": "..."},
  {"label": "..."}, {"placeholder": "..."}; add "exact": true for exact text.
"""
import sys, json, time, shutil, traceback, re
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path.home() / "AppData" / "Local" / "MonarcAIOS" / "browser"
PROFILE = BASE / "chrome-profile"
CMD_DIR = BASE / "commands"
RES_DIR = BASE / "results"
LOG = BASE / "events.log"
DL_LOG = BASE / "downloads.jsonl"
CHROME_DEFAULT = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default"
LOCATOR_KEYS = ("selector", "role", "text", "label", "placeholder")


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def seed_bookmarks():
    src = CHROME_DEFAULT / "Bookmarks"
    dst = PROFILE / "Default" / "Bookmarks"
    if src.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        log("copied bookmarks from the Default Chrome profile")


CHROME_USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
ONE_TIME_DIR = BASE / "one-time-copy"


def copy_session_profile(source_profile):
    """Copy one of Jonathan's real Chrome profiles into a throwaway user-data dir as 'Default',
    so a controllable Chrome opens already logged in. His real profile is never touched.
    Requires his Chrome to be fully closed first, or the cookie DB is locked and the copy is stale.
    Returns the temp user-data-dir path. Discard it after the one-time job."""
    src = CHROME_USER_DATA / source_profile
    if not src.exists():
        raise SystemExit(f"profile not found: {src}")
    if ONE_TIME_DIR.exists():
        shutil.rmtree(ONE_TIME_DIR, ignore_errors=True)
    (ONE_TIME_DIR / "Default").mkdir(parents=True, exist_ok=True)
    # Local State holds the encryption key that unwraps the cookie DB; it must travel with the copy.
    ls = CHROME_USER_DATA / "Local State"
    if ls.exists():
        shutil.copy(ls, ONE_TIME_DIR / "Local State")
    skip = {"Cache", "Code Cache", "GPUCache", "Service Worker", "DawnGraphiteCache",
            "DawnWebGPUCache", "GraphiteDawnCache", "Component Crx Cache"}
    for item in src.iterdir():
        if item.name in skip:
            continue
        dest = ONE_TIME_DIR / "Default" / item.name
        try:
            if item.is_dir():
                shutil.copytree(item, dest, ignore_errors=True)
            else:
                shutil.copy(item, dest)
        except Exception as e:  # noqa: BLE001
            log(f"skip {item.name}: {e}")
    log(f"copied session profile '{source_profile}' -> {ONE_TIME_DIR}")
    return ONE_TIME_DIR


def snapshot(page, max_chars=12000):
    try:
        aria = page.locator("body").aria_snapshot()
    except Exception as e:  # noqa: BLE001
        aria = f"(aria snapshot failed: {e})"
    return {"url": page.url, "title": page.title(), "aria": aria[:max_chars], "truncated": len(aria) > max_chars}


def resolve(page, a):
    exact = a.get("exact", False)
    if "selector" in a:
        return page.locator(a["selector"]).first
    if "role" in a:
        return page.get_by_role(a["role"], name=a.get("name"), exact=exact).first
    if "text" in a:
        return page.get_by_text(a["text"], exact=exact).first
    if "label" in a:
        return page.get_by_label(a["label"], exact=exact).first
    if "placeholder" in a:
        return page.get_by_placeholder(a["placeholder"], exact=exact).first
    raise ValueError("locator needs one of: selector, role, text, label, placeholder")


def unique_target(folder, name):
    name = re.sub(r'[\\/:*?"<>|]+', "_", name) or "download"
    target = folder / name
    i = 1
    while target.exists():
        target = folder / f"{Path(name).stem} ({i}){Path(name).suffix}"
        i += 1
    return target


def make_download_handler(state):
    def on_download(dl):
        try:
            target = unique_target(state["downloads"], dl.suggested_filename)
            dl.save_as(str(target))
            rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "page_url": dl.page.url, "download_url": dl.url,
                   "suggested": dl.suggested_filename, "saved": str(target)}
            with DL_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            state["last_download"] = rec
            log(f"download saved: {target.name}  from {dl.url[:120]}")
        except Exception as e:  # noqa: BLE001
            log(f"download failed: {e}")
    return on_download


def handle(ctx, state, cmd):
    page = state["page"]
    op = cmd["op"]
    a = cmd.get("args", {}) or {}
    if op == "goto":
        page.goto(a["url"], wait_until=a.get("wait", "load"), timeout=a.get("timeout", 60000))
        return snapshot(page)
    if op == "snapshot":
        return snapshot(page, a.get("max_chars", 12000))
    if op == "text":
        return {"url": page.url, "text": page.inner_text("body")[: a.get("max_chars", 12000)]}
    if op == "html":
        return {"url": page.url, "html": page.content()[: a.get("max_chars", 20000)]}
    if op == "links":
        links = page.eval_on_selector_all(
            "a[href]", "els => els.map(e => ({text: e.innerText.trim().slice(0, 80), href: e.href}))")
        return {"url": page.url, "count": len(links), "links": links[: a.get("max", 400)]}
    if op == "click":
        resolve(page, a).click(timeout=a.get("timeout", 10000))
        try:
            page.wait_for_load_state("load", timeout=15000)
        except Exception:  # noqa: BLE001
            pass
        return snapshot(page)
    if op == "fill":
        resolve(page, a).fill(a["value"])
        return {"ok": True}
    if op == "press":
        if any(k in a for k in LOCATOR_KEYS):
            resolve(page, a).press(a["key"])
        else:
            page.keyboard.press(a["key"])
        return snapshot(page)
    if op == "wait":
        if "selector" in a:
            page.wait_for_selector(a["selector"], timeout=a.get("timeout", 30000))
        else:
            page.wait_for_timeout(a.get("ms", 1000))
        return snapshot(page)
    if op == "screenshot":
        p = a.get("path") or str(BASE / "screenshot.png")
        page.screenshot(path=p, full_page=a.get("full", False))
        return {"path": p}
    if op == "download":
        with page.expect_download(timeout=a.get("timeout", 60000)) as d:
            resolve(page, a).click()
        dl = d.value
        dl.path()  # wait for completion; the context handler saves and logs it
        time.sleep(0.5)
        return {"download": state.get("last_download"), "url": dl.url}
    if op == "eval":
        return {"value": page.evaluate(a["js"])}
    if op == "tabs":
        return {"tabs": [{"i": i, "url": p.url, "title": p.title()} for i, p in enumerate(ctx.pages)]}
    if op == "switch":
        state["page"] = ctx.pages[a["index"]]
        state["page"].bring_to_front()
        return snapshot(state["page"])
    if op == "newtab":
        state["page"] = ctx.new_page()
        if a.get("url"):
            state["page"].goto(a["url"])
        return snapshot(state["page"])
    if op == "quit":
        state["quit"] = True
        return {"ok": True}
    raise ValueError(f"unknown op: {op}")


def main(argv):
    downloads = Path.home() / "Downloads" / "AIOS"
    url = None
    user_data_dir = PROFILE
    from_profile = None
    if "--downloads" in argv:
        downloads = Path(argv[argv.index("--downloads") + 1])
    if "--url" in argv:
        url = argv[argv.index("--url") + 1]
    if "--from-profile" in argv:
        from_profile = argv[argv.index("--from-profile") + 1]
    for d in (CMD_DIR, RES_DIR, downloads):
        d.mkdir(parents=True, exist_ok=True)
    for stale in CMD_DIR.glob("*.json"):
        stale.unlink()
    if from_profile:
        user_data_dir = copy_session_profile(from_profile)  # one-time logged-in copy
    else:
        PROFILE.mkdir(parents=True, exist_ok=True)
        seed_bookmarks()
    state = {"downloads": downloads, "quit": False, "last_download": None}
    log(f"starting Chrome. user_data_dir={user_data_dir} downloads={downloads}")
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(user_data_dir), channel="chrome", headless=False, no_viewport=True, accept_downloads=True,
            args=["--start-maximized"], ignore_default_args=["--enable-automation"])
        on_download = make_download_handler(state)

        def attach(p):
            p.on("download", on_download)
        for p in ctx.pages:
            attach(p)
        ctx.on("page", attach)
        state["page"] = ctx.pages[0] if ctx.pages else ctx.new_page()
        if url:
            state["page"].goto(url)
        log("ready. waiting for commands")
        empty_since = None
        while not state["quit"]:
            if not ctx.pages:
                empty_since = empty_since or time.time()
                if time.time() - empty_since > 3:
                    log("all tabs closed by the user. exiting")
                    break
            else:
                empty_since = None
                if state["page"].is_closed():
                    state["page"] = ctx.pages[-1]
            for f in sorted(CMD_DIR.glob("*.json")):
                try:
                    cmd = json.loads(f.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    continue
                out = {"id": f.stem, "op": cmd.get("op")}
                try:
                    out["ok"] = True
                    out["result"] = handle(ctx, state, cmd)
                except Exception as e:  # noqa: BLE001
                    out["ok"] = False
                    out["error"] = f"{type(e).__name__}: {e}"
                    out["trace"] = traceback.format_exc()[-1500:]
                (RES_DIR / f.name).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
                f.unlink()
                log(f"{cmd.get('op')} -> {'ok' if out['ok'] else out['error']}")
            time.sleep(0.25)
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass
    log("stopped")


if __name__ == "__main__":
    main(sys.argv[1:])
