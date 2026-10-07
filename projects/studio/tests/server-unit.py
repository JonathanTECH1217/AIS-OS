"""Server checks: HTTP Range, the media path guard, uploads, shorts (revisions, 409, versions), exports list, the calls
view's routes and Remove full-size copy (2026-10-01). Starts its own server on port 8783 against a copy of the
fixtures, with STUDIO_NO_CLAUDE set so nothing can spend.

  python projects/studio/tests/server-unit.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PORT = 8783
URL = f"http://127.0.0.1:{PORT}"
FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


def req(method, path, body=None, headers=None, raw=False):
    data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    h = dict(headers or {})
    if isinstance(body, (dict, list)):
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(URL + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(rq, timeout=15) as r:
            b = r.read()
            return r.status, dict(r.headers), (b if raw else (json.loads(b) if b and "json" in r.headers.get("Content-Type", "") else b))
    except urllib.error.HTTPError as e:
        b = e.read()
        return e.code, dict(e.headers), b


def main():
    seed = HERE / "fixtures" / "seed"
    sys.path.insert(0, str(HERE / "fixtures"))
    import make as fixtures                       # noqa: E402  (tests/fixtures/make.py)
    if not fixtures.seed_current():
        subprocess.run([sys.executable, str(HERE / "fixtures" / "make.py")], check=True)
    media = Path(tempfile.mkdtemp(prefix="studio-srv-"))
    shutil.copytree(seed, media, dirs_exist_ok=True)
    log = open(media / "server.log", "w")
    srv = subprocess.Popen([sys.executable, "-u", str(ROOT / "scripts" / "studio_server.py"), "--port", str(PORT), "--no-open"],
                           env=dict(os.environ, STUDIO_MEDIA=str(media), STUDIO_CONFIG=str(media / "config.json"),
                                    STUDIO_VOICEPRINT=str(media / "voiceprint.json"), STUDIO_NO_CLAUDE="1",
                                    STUDIO_FAKE_LISTEN="1"),
                           stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(60):
            try:
                req("GET", "/api/health")
                break
            except OSError:
                time.sleep(0.3)
        src = media / "inbox" / "src20.mp4"
        size = src.stat().st_size
        s, h, b = req("GET", "/media/inbox/src20.mp4", headers={"Range": "bytes=0-99"}, raw=True)
        check("Range bytes=0-99 answers 206", s == 206, str(s))
        check("Content-Range names the span", h.get("Content-Range") == f"bytes 0-99/{size}", h.get("Content-Range"))
        check("exactly 100 bytes", len(b) == 100 and b == src.read_bytes()[:100])
        s, h, b = req("GET", "/media/inbox/src20.mp4", headers={"Range": "bytes=-50"}, raw=True)
        check("suffix range gives the last 50 bytes", s == 206 and b == src.read_bytes()[-50:])
        s, h, b = req("GET", "/media/inbox/src20.mp4", headers={"Range": f"bytes={size}-"}, raw=True)
        check("a range past the end is 416", s == 416 and h.get("Content-Range") == f"bytes */{size}", f"{s} {h.get('Content-Range')}")
        s, h, b = req("GET", "/media/inbox/src20.mp4", raw=True)
        check("no range: 200 with Accept-Ranges", s == 200 and h.get("Accept-Ranges") == "bytes" and len(b) == size)
        s, h, b = req("HEAD", "/media/inbox/src20.mp4", raw=True)
        check("HEAD gives the length", s == 200 and int(h.get("Content-Length", 0)) == size)
        for bad in ("/media/../scripts/studio_server.py", "/media/%2e%2e/%2e%2e/secrets.env", "/media/..%5c..%5cWindows%5cwin.ini"):
            s, _, _ = req("GET", bad, raw=True)
            check(f"path guard refuses {bad}", s in (403, 404), str(s))
        s, h, b = req("GET", "/app.js", raw=True)
        check(".js served as JavaScript (ES modules need it)", h.get("Content-Type", "").startswith("text/javascript"))
        # upload
        png = (ROOT / "projects" / "studio" / "favicon.png").read_bytes()
        s, h, b = req("PUT", "/api/upload?dir=assets&name=up%20load.png", body=png, headers={"Content-Type": "application/octet-stream"})
        check("upload lands in media/assets", s == 200 and (media / "assets" / "up load.png").exists(), f"{s} {b}")
        check("no .part left behind", not list((media / "assets").glob("*.part")))
        s, h, b = req("PUT", "/api/upload?dir=assets&name=up%20load.png", body=png)
        check("a second upload with the same name gets a new name", (media / "assets" / "up load (2).png").exists())
        s, h, b = req("PUT", "/api/upload?dir=assets&name=virus.exe", body=b"MZ")
        check("unsupported file types are refused", s == 400)
        # shorts (a freshly built seed is "new" to the scanner, which waits for files to stop changing first)
        aid = None
        for _ in range(60):
            aid = next((a["id"] for f in req("GET", "/api/bin")[2]["folders"] for a in f["items"] if a["name"] == "src20.mp4"), None)
            if aid:
                break
            time.sleep(0.5)
        s, h, doc = req("POST", "/api/projects", {"asset": aid, "moment": "m01"})
        check("a short from a moment: the video, You on A1 and Them on A2", s == 200 and [(c["track"], c.get("voice")) for c in doc["clips"]]
              == [("V1", None), ("A1", "me"), ("A2", "them")] and doc["clips"][0]["in"] == 30
              and len({c["link"] for c in doc["clips"]}) == 1, str(doc)[:300])
        check("new shorts name the audio tracks You, Them, Sounds", [(t["id"], t.get("name"), t.get("voice")) for t in doc["tracks"] if t["kind"] == "audio"]
              == [("A1", "You", "me"), ("A2", "Them", "them"), ("A3", "Sounds", None)], str(doc["tracks"]))
        check("a new short has no captions until Generate (G1)", doc["captions"].get("mode") == "generate" and doc["captions"]["events"] == [])
        s, h, ld = req("POST", "/api/loudness", {"asset": aid, "ranges": [[1.0, 3.0], [5.0, 7.0]]})
        check("loudness of stretches of a recording (Normalize voices)", s == 200 and isinstance(ld["lufs"], float) and -60 < ld["lufs"] < 0
              and ld["seconds"] == 4.0, str(ld))
        s, h, ld = req("POST", "/api/loudness", {"asset": "a_nope", "ranges": [[1, 2]]})
        check("loudness of an unknown recording is 404", s == 404)
        pid, rev = doc["id"], doc["rev"]
        doc["name"] = "Renamed"
        s, h, b = req("PUT", f"/api/projects/{pid}", {"doc": doc, "baseRev": rev})
        check("save with the current revision", s == 200 and b["rev"] == rev + 1, str(b))
        s, h, b = req("PUT", f"/api/projects/{pid}", {"doc": doc, "baseRev": rev})
        check("save with a stale revision is 409", s == 409)
        s, h, vs = req("GET", f"/api/projects/{pid}/versions")
        check("one version kept on creation, none extra within 10 minutes", s == 200 and len(vs) == 1, str(vs))
        s, h, lst = req("GET", "/api/projects")
        check("the list shows the short with its status", any(p["id"] == pid and p["status"] == "draft" and p["name"] == "Renamed" for p in lst))
        s, h, b = req("DELETE", f"/api/projects/{pid}")
        check("delete moves it to .trash", s == 200 and not (media / "projects" / f"{pid}.json").exists() and list((media / "projects" / ".trash").glob(f"{pid}-*.json")))
        s, h, b = req("GET", "/api/projects/../../secrets")
        check("project ids can't climb out", s in (400, 404, 500))
        # transcript edits overlay
        s, h, b = req("PATCH", f"/api/asset/{aid}/transcript", {"edits": {"3": "LEADS"}})
        check("a word fix is stored beside the transcript", s == 200 and json.loads((media / ".studio" / aid / "transcript-edits.json").read_text()) == {"3": "LEADS"})
        s, h, tr = req("GET", f"/api/asset/{aid}/transcript")
        check("the transcript comes back with the fix applied", tr["words"][3][2] == "LEADS")
        orig = json.loads((media / ".studio" / aid / "transcript.json").read_text())
        check("the original transcript file is untouched", orig["words"][3][2] != "LEADS")
        # Generate captions (2026-10-02): a job per press; the fixtures' fake second listen, Claude off (second wins)
        s, h, td = req("POST", "/api/projects", {"asset": aid, "moment": "m01", "captions": "transcript"})
        check('captions: "transcript" makes a short the old way', s == 200 and "mode" not in td["captions"])
        s, h, job = req("POST", f"/api/asset/{aid}/captions", {"ranges": [[1.0, 6.0], [10.2, 13.0]]})   # 4.2 s apart: two stretches
        check("Generate captions starts a job", s == 200 and job.get("state") == "running" and job.get("id", "").startswith("g"), f"{s} {job}")
        for _ in range(80):
            s, h, job = req("GET", f"/api/captions/{job['id']}")
            if job.get("state") != "running":
                break
            time.sleep(0.25)
        g = job.get("result") or {}
        texts = [w[2] for w in g.get("words", [])]
        check("the job ends with the words, the stretches and the transcript they were made against",
              job.get("state") == "done" and len(texts) > 12 and g["ranges"] == [[0.0, 7.0], [9.2, 14.0]] and g["trRev"] == "fixture",
              f"{job.get('state')} {len(texts)} {g.get('ranges')} {g.get('trRev')}")
        check("a place holding a word he fixed keeps his reading (LEADS pins 'is LEADS thing')",
              texts[2:5] == ["is", "LEADS", "thing"] and "was" not in texts and "ring" not in texts, str(texts))
        check("a word only the second listen heard goes in, with its voice group",
              any(w[2] == "really" and w[4] in ("S1", "S4") for w in g["words"]) and any(w[2] == "okay" and w[4] == "S2" for w in g["words"]))
        check("a word the second listen missed goes (Claude off: it wins)", not any(abs(w[0] - 4.9) < 0.01 for w in g["words"]))
        check("an unknown job is 404", req("GET", "/api/captions/g123")[0] == 404)
        check("ranges that aren't pairs of numbers are 400", req("POST", f"/api/asset/{aid}/captions", {"ranges": [["a", 2]]})[0] == 400)
        check("nothing kept is 400", req("POST", f"/api/asset/{aid}/captions", {"ranges": []})[0] == 400)
        broll = next(a["id"] for f in req("GET", "/api/bin")[2]["folders"] for a in f["items"] if a["name"] == "broll5.mp4")
        check("a recording with no transcript is 409", req("POST", f"/api/asset/{broll}/captions", {"ranges": [[0, 2]]})[0] == 409)
        # Export all names the shorts going out without generated captions (G5); the renders are cancelled right after
        s, h, bare = req("POST", "/api/projects", {"asset": aid, "moment": "m02", "name": "No captions yet"})
        bare["status"] = "done"
        req("PUT", f"/api/projects/{bare['id']}", {"doc": bare, "baseRev": bare["rev"]})
        s, h, ea = req("POST", "/api/export/all", {})
        check("Export all queues it anyway and names it as without captions", s == 200 and ea["queued"] >= 1
              and "No captions yet" in ea.get("noCaptions", []), str(ea))
        for j in req("GET", "/api/exports")[2]:
            if j["state"] in ("queued", "running"):
                req("POST", "/api/export/cancel", {"id": j["id"]})
        # voices (2026-09-30)
        vo = tr.get("voices") or {}
        check("the transcript carries each word's voice", vo.get("state") == "ready" and len(vo.get("spk") or []) == len(tr["words"])
              and vo["speakers"][0]["key"] == "me", json.dumps(vo)[:300])
        s, h, b = req("PATCH", f"/api/asset/{aid}/speakers", {"groups": {"S2": {"who": "other", "gender": "man"}}})
        check("a voice fix answers with the new voices", s == 200 and next(v for v in b["speakers"] if v["key"] == "S2")["cls"] == "m", f"{s} {str(b)[:200]}")
        ed = json.loads((media / ".studio" / aid / "speaker-edits.json").read_text())
        check("the fix is stored beside the transcript", ed["groups"]["S2"] == {"who": "other", "gender": "man"} and ed["rev"] == "fixture1")
        s, h, b = req("PATCH", f"/api/asset/{aid}/speakers", {"words": {"99999": "S2"}})
        check("a word id out of range is 400", s == 400, str(s))
        s, h, b = req("PATCH", f"/api/asset/{aid}/speakers", {"groups": {"S77": {"who": "me"}}})
        check("an unknown voice is 400", s == 400, str(s))
        s, h, b = req("PATCH", f"/api/asset/{aid}/speakers", {"groups": {"S2": None}})
        check("a fix can be reset", s == 200 and next(v for v in b["speakers"] if v["key"] == "S2")["cls"] == "f")
        check("the voiceprint is saved where STUDIO_VOICEPRINT points", (media / "voiceprint.json").exists())
        s, h, b = req("GET", f"/api/asset/{aid}/voices")
        s2, h2, bn = req("GET", "/api/bin")
        a20 = next(a for f in bn["folders"] for a in f["items"] if a.get("id") == aid)
        check("the voices alone, with a revision that matches the bin's", s == 200 and b["state"] == "ready" and b["vrev"] == a20.get("voicesRev"),
              f"{b.get('vrev')} vs {a20.get('voicesRev')}")
        spj = media / ".studio" / aid / "speakers.json"
        good = spj.read_text()
        spj.write_text('{"v": 1, "rev": "broken", "turns": [[0, 1, "S1"]], "groups": 5}')
        s, h, trb = req("GET", f"/api/asset/{aid}/transcript")
        check("a broken voice file still sends the words (the captions can't go empty)", s == 200 and len(trb["words"]) == 36
              and trb["voices"]["state"] == "error", f"{s} {str(trb)[:160]}")
        spj.write_text(good)
        s, h, b = req("POST", f"/api/asset/{aid}/reprep", {"stages": ["proxy"]})
        time.sleep(1)
        check("preparing a file again leaves its voice split alone", spj.exists())
        # the calls view (2026-10-01): rows, best bits by time, hidden and between-calls stretches, marks, search, words
        cv = None
        for _ in range(60):
            s, h, cv = req("GET", f"/api/asset/{aid}/calls")
            if s == 200 and not cv["bounding"]:
                break
            time.sleep(0.5)
        rows = {r["id"]: r for r in cv["calls"]}
        check("the calls come in time order, rings looked for", s == 200 and list(rows) == ["c01", "c02", "c03", "c04"]
              and not cv["bounding"] and (media / ".studio" / aid / "calls.json").exists(), str(cv)[:300])
        check("a stretch with no best bit is hidden; one with a bit shows as between calls",
              rows["c03"]["hidden"] and rows["c04"]["between"] and cv["hidden"] == 1)
        check("best bits sit on the stretch they overlap", {b["id"]: b["call"] for b in cv["bits"]} == {"m01": "c01", "m02": "c02", "m03": "c04"})
        check("play ranges: from 0, never past the next call or the end of the recording",
              rows["c01"]["play"] == [0.0, 7.2] and rows["c02"]["play"] == [7.2, 16.5] and rows["c04"]["play"] == [18.0, 20.0],
              str([r["play"] for r in cv["calls"]]))
        s, h, sr = req("GET", f"/api/asset/{aid}/calls/search?q=first%20call")
        check("search finds a phrase in what was said, per call", s == 200 and sr["hits"].get("c02") == {"n": 1, "first": 7.5}, str(sr))
        s, h, wd = req("GET", f"/api/asset/{aid}/words?s=7.2&e=16.5")
        check("one call's words come with their voices", s == 200 and wd["words"][0][0] == 7.5 and wd["voices"]["state"] == "ready"
              and len(wd["voices"]["spk"]) == len(wd["words"]) and wd["voices"]["speakers"], str(wd)[:200])
        s, h, b = req("GET", f"/api/asset/{aid}/words?s=9&e=3")
        check("words for a backwards stretch is 400", s == 400)
        s, h, b = req("PATCH", f"/api/asset/{aid}/calls/c02", {"watched": True})
        s2, h2, cv2 = req("GET", f"/api/asset/{aid}/calls")
        check("a watched mark is kept", s == 200 and next(r for r in cv2["calls"] if r["id"] == "c02")["watched"]
              and not next(r for r in cv2["calls"] if r["id"] == "c01")["watched"])
        check("marking an unknown call is 404, anything but watched is 400",
              req("PATCH", f"/api/asset/{aid}/calls/c99", {"watched": True})[0] == 404
              and req("PATCH", f"/api/asset/{aid}/calls/c02", {"watched": False})[0] == 400)
        s, h, sd = req("POST", "/api/projects", {"asset": aid, "call": "c02", "start": 7.2, "end": 16.5})
        check("Make short from a whole call", s == 200 and sd["clips"][0]["in"] == 216 and sd["clips"][0]["out"] == 495
              and sd["name"] == "Dana, Fixture Electric" and sd["moment"]["call"] == "c02" and sd["moment"]["type"] == "call"
              and sd["moment"]["start"] == 7.2, str(sd)[:300])
        s, h, sb = req("POST", "/api/projects", {"asset": aid, "call": "c04", "bit": "m03", "start": 18.2, "end": 19.8})
        mo_now = json.loads((media / ".studio" / aid / "moments.json").read_text())
        check("Make short from a best bit's marks: its title, and the bit is kept", s == 200 and sb["name"] == "To the camera"
              and next(m for m in mo_now["moments"] if m["id"] == "m03")["state"] == "kept", str(sb)[:200])
        for body, why in (({"asset": aid}, "a bare asset"), ({"asset": aid, "start": 5, "end": 3}, "a backwards stretch"),
                          ({"asset": aid, "start": 0, "end": 99}, "a stretch past the end")):
            check(f"a short from {why} is 400", req("POST", "/api/projects", body)[0] == 400)
        s, h, bn = req("GET", "/api/bin")
        a20 = next(a for f in bn["folders"] for a in f["items"] if a.get("id") == aid)
        check("the recording's row: calls, bookings, a revision, its copy", a20.get("calls") == {"n": 2, "booked": 1}
              and a20.get("callsRev") and a20.get("copy") == "source", str({k: a20.get(k) for k in ("calls", "callsRev", "copy")}))
        check("a name with no date: recorded from the file's own time", a20.get("recordedFrom") == "file time"
              and len(a20.get("recorded") or "") == 19, str({k: a20.get(k) for k in ("recorded", "recordedFrom")}))
        check("the bin feed carries the free disk space", isinstance(bn.get("diskFreeGb"), (int, float)))
        check("auto-run is off without autoFindMax", "autoFindMax" in bn["config"] and bn["config"]["autoFindMax"] is None)
        check("an MP4 that plays as it is has no copy to remove", req("POST", f"/api/asset/{aid}/orig", {"keep": False})[0] == 400)
        # Remove full-size copy (B20) on a small MKV in assets/ (assets videos get the copy, waveform and preview steps)
        import studio_common as scm                    # noqa: E402
        mkv = media / "assets" / "2026-09-30 10-27-42.mkv"           # named the way OBS names a recording
        subprocess.run([scm.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-t", "6", "-c", "copy", str(mkv)], check=True)
        mid_ = None
        for _ in range(120):
            mid_ = next((a["id"] for f in req("GET", "/api/bin")[2]["folders"] for a in f["items"] if a["name"] == mkv.name), None)
            if mid_ and (media / ".studio" / mid_ / "orig.mp4").exists() and all(
                    x.get("state") == "done" for x in json.loads((media / ".studio" / mid_ / "status.json").read_text())["stages"].values()):
                break
            time.sleep(0.5)
        cp = media / ".studio" / mid_ / "orig.mp4"
        am = lambda: next(a for f in req("GET", "/api/bin")[2]["folders"] for a in f["items"] if a.get("id") == mid_)  # noqa: E731
        check("an MKV gets a full-size copy", cp.exists() and am()["copy"] == "cache" and am()["copyBytes"] > 0 and "orig" in am()["urls"])
        check("an OBS name gives the date it was recorded", am()["recorded"] == "2026-09-30T10:27:42" and am()["recordedFrom"] == "name",
              str({k: am().get(k) for k in ("recorded", "recordedFrom")}))
        s, h, b = req("POST", f"/api/asset/{mid_}/orig", {"keep": False})
        meta_ = json.loads((media / ".studio" / mid_ / "meta.json").read_text())
        check("Remove full-size copy deletes it and says how much it freed", s == 200 and b["freed"] > 0 and not cp.exists()
              and meta_["orig"] == "removed", f"{s} {b}")
        check("the page then gets no full-size address (it plays the preview copy)", am()["copy"] == "removed" and "orig" not in am()["urls"])
        s, h, b = req("GET", f"/api/audio_block?asset={mid_}&i=0&sr=48000", raw=True)
        check("the editor's sound comes from the OBS file meanwhile", s == 200 and b[:4] == b"RIFF")
        req("POST", f"/api/asset/{mid_}/reprep", {"stages": ["remux", "peaks", "proxy"]})
        for _ in range(60):
            time.sleep(0.5)
            stj2 = json.loads((media / ".studio" / mid_ / "status.json").read_text())["stages"]
            if all(x.get("state") == "done" for x in stj2.values()):
                break
        check("preparing it again doesn't bring the copy back", not cp.exists()
              and json.loads((media / ".studio" / mid_ / "meta.json").read_text())["orig"] == "removed")
        s, h, b = req("POST", f"/api/asset/{mid_}/orig", {"keep": True})
        for _ in range(60):
            if cp.exists():
                break
            time.sleep(0.5)
        check("Restore makes the copy again", s == 200 and cp.exists() and am()["copy"] == "cache", f"{s} {b}")
        # a copy that goes missing while marked done (2026-10-02: a "Prepare again" lost to a restart left a recording
        # silent): the sound comes from the OBS file meanwhile, the page gets no broken address, and a run rebuilds it
        for _ in range(60):                     # let the restore's prep finish before pulling the file
            if all(x.get("state") == "done" for x in json.loads((media / ".studio" / mid_ / "status.json").read_text())["stages"].values()):
                break
            time.sleep(0.5)
        blocks = media / ".studio" / mid_ / "blocks"
        shutil.rmtree(blocks, ignore_errors=True)
        cp.unlink()
        check("a missing copy shows as missing, with no full-size address", am()["copy"] == "missing" and "orig" not in am()["urls"],
              str({k: am().get(k) for k in ("copy", "urls")}))
        s, h, b = req("GET", f"/api/audio_block?asset={mid_}&i=0&sr=48000", raw=True)
        check("the sound still comes, from the OBS file", s == 200 and b[:4] == b"RIFF" and len(b) > 1000, f"{s} {b[:80]}")
        s, h, b = req("POST", f"/api/asset/{mid_}/reprep", {"stages": []})
        for _ in range(60):
            if cp.exists():
                break
            time.sleep(0.5)
        check("a prep run makes the missing copy again", s == 200 and cp.exists() and am()["copy"] == "cache")
        s, h, b = req("POST", f"/api/asset/{mid_}/reprep", {"stages": ["peaks"]})
        check("Prepare again answers with what it will redo", s == 200 and b.get("redo") == ["peaks"], str(b))
        # the palette every short uses
        s, h, c = req("GET", "/api/config")
        check("config answers the default palette", s == 200 and c["captionColors"]["you"] == "#4D80E6" and c["captionColors"]["woman"] == "#FF5FA2", str(c))
        s, h, c = req("PUT", "/api/config", {"captionColors": {"man": "#aa0000"}})
        saved = json.loads((media / "config.json").read_text())
        check("a color change is saved (upper case) and the rest kept", s == 200 and c["captionColors"]["man"] == "#AA0000"
              and saved["captionColors"]["man"] == "#AA0000" and saved["captionColors"]["you"] == "#4D80E6", str(saved))
        s, h, b = req("PUT", "/api/config", {"captionColors": {"man": "red"}})
        check("a color that is not #RRGGBB is 400", s == 400)
        s, h, b = req("PUT", "/api/config", {"captionColors": {"sky": "#000000"}})
        check("an unknown color name is 400", s == 400)
        s, h, bn = req("GET", "/api/bin")
        check("the bin feed carries the palette", bn["config"]["captionColors"]["man"] == "#AA0000")
        s, h, c = req("PUT", "/api/config", {"reset": True})
        check("reset puts the defaults back", c["captionColors"]["man"] == "#FF3B30")
        # Find moments waits for the voice split
        stp = media / ".studio" / aid / "status.json"
        st0 = stp.read_text()
        stj = json.loads(st0)
        stj["stages"]["speakers"] = {"state": "running", "progress": 0.4}
        stp.write_text(json.dumps(stj))
        s, h, b = req("POST", f"/api/asset/{aid}/moments/estimate", {})
        check("Find calls is 409 while the voices are splitting", s == 409 and b"40 %" in b and b"Find calls" in b, f"{s} {b[:120]}")
        stp.write_text(st0)
        s, h, b = req("GET", f"/api/audio_block?asset={aid}&i=0&sr=48000", raw=True)
        check("audio blocks are WAV at the asked rate", s == 200 and b[:4] == b"RIFF" and int.from_bytes(b[24:28], "little") == 48000)
        s, h, b = req("GET", "/api/exports")
        check("exports list answers", s == 200 and isinstance(b, list))
        s, h, hl = req("GET", "/api/health")
        check("health names the app and the key source, never the key", hl["app"] == "Monarc Studio" and ("sk-" not in json.dumps(hl)))
    finally:
        subprocess.run(["taskkill", "/PID", str(srv.pid), "/T", "/F"], capture_output=True)
        srv.wait()
        log.close()
        shutil.rmtree(media, ignore_errors=True)
    print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
