"""End to end on the real media: the running Studio server (8780), the newest recording in media/inbox.

  python projects/studio/tests/e2e-real.py [--keep]

Opens the editor headless, checks the recording is prepared and has calls, opens its calls view (2026-10-01: a call
plays from its ring, with colored captions), opens the Find calls cost dialog and cancels it (no spend), makes a short
from the strongest moment and uses the main tools on it (razor, trim, zoom keyframes, a title, a sound on A3, a
dissolve), generates its captions (2026-10-02: the second listen plus Claude's picks, about 1 to 2 cents, the one spend
in this run), closes the window mid-edit and checks autosave kept the edit, exports, and checks the MP4 (size, frame
rate, length, audio, captions burned in). The test short and its export are removed at the end unless --keep, and the
moment state and watched marks it touched are put back. Screenshots go to projects/studio/tests/shots/e2e-*.png.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import studio_common as sc  # noqa: E402

URL = "http://127.0.0.1:8780/"
FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


def api(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    rq = urllib.request.Request(URL + path.lstrip("/"), data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(rq, timeout=30) as r:
        return json.loads(r.read())


def main():
    keep = "--keep" in sys.argv
    restore = None      # making a short marks its moment kept: the test puts the moment back as it found it
    try:
        api("api/health")
    except OSError:
        subprocess.run([sys.executable.replace("python.exe", "pythonw.exe"), str(ROOT / "scripts" / "studio_boot.pyw"), "--no-open"])
        time.sleep(3)
    h = api("api/health")
    check("Studio server answers", h.get("app") == "Monarc Studio")
    from playwright.sync_api import sync_playwright
    shots = HERE / "shots"
    shots.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        ctx = b.new_context(viewport={"width": 1600, "height": 960})
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL)
        pg.wait_for_function("window.__studio && window.__studio.S.bin && window.__studio.lib.all().length", timeout=20000)
        rec = pg.evaluate("""() => { const a = window.__studio.lib.all().filter(x => x.kind === 'video' && x.rel.startsWith('inbox/'))
                               .sort((x, y) => (y.duration || 0) - (x.duration || 0))[0];
                               return a && { id: a.id, name: a.name, stages: a.stages, moments: a.moments, transcript: a.transcript, duration: a.duration }; }""")
        check("a recording is in the bin", bool(rec), str(rec))
        check("fully prepared (copy, waveform, preview copy, transcript, voices)", all(s["state"] == "done" for s in rec["stages"].values())
              and "speakers" in rec["stages"], json.dumps(rec["stages"]))
        mo = api(f"api/asset/{rec['id']}/moments")
        check("Claude's calls and best bits are there", len(mo["calls"]) >= 10 and len(mo["moments"]) >= 10,
              f"{len(mo['calls'])} calls, {len(mo['moments'])} best bits")
        # voices on the real call (2026-09-30): the C3 Electrical call at 1:31 opens "Hello, this is Jonathan." and
        # "Hey, this is Sean with C3 Electrical."
        tr = api(f"api/asset/{rec['id']}/transcript")
        vo = tr.get("voices") or {}
        check("the recording's voices are labeled", vo.get("state") == "ready" and any(v["source"] == "claude" for v in vo["speakers"]),
              json.dumps({k: vo.get(k) for k in ("state", "rev")}))
        words = [w[2].strip(".,?!").lower() for w in tr["words"]]

        def phrase(seq):
            for i in range(len(words) - len(seq)):
                if words[i:i + len(seq)] == seq:
                    return i
            return None

        def cls_at(i):
            j = vo["spk"][i] if vo.get("spk") else -1
            return vo["speakers"][j]["cls"] if j >= 0 else None

        i_j, i_s = phrase(["hello", "this", "is", "jonathan"]), phrase(["hey", "this", "is", "sean", "with"])
        check("found the C3 Electrical call's openings in the transcript", i_j is not None and i_s is not None, f"{i_j} {i_s}")
        if i_j is not None and i_s is not None:
            check("'Hello, this is Jonathan' is Jonathan (blue)", [cls_at(i_j + k) for k in range(4)] == ["me"] * 4,
                  str([cls_at(i_j + k) for k in range(4)]))
            check("'Hey, this is Sean with C3 Electrical' is a man (red)", [cls_at(i_s + k) for k in range(5)] == ["m"] * 5,
                  str([cls_at(i_s + k) for k in range(5)]))
        counts = {}
        for i in range(len(words)):
            c = cls_at(i) or "none"
            counts[c] = counts.get(c, 0) + 1
        print(f"     words by voice class: {counts}")
        # the calls view (2026-10-01): the recording opens to its calls; a call plays from its ring, with captions.
        # Playing marks calls watched, so the marks file is put back afterwards.
        marks_file = sc.CACHE / rec["id"] / "call-marks.json"
        marks_before = marks_file.read_bytes() if marks_file.exists() else None
        # its row: the newest recording stays in view, earlier ones fold under "Previous recordings" (2026-10-01)
        row_js = "id => document.querySelector(`.bin-item.rec[data-id='${id}']`)"
        if not pg.evaluate(f"({row_js})('{rec['id']}') !== null"):
            pg.click(".bin-sub-head")
            pg.wait_for_function(f"({row_js})('{rec['id']}') !== null", timeout=10000)
        try:
            pg.evaluate("id => document.querySelector(`.bin-item.rec[data-id='${id}']`).click()", rec["id"])
            pg.wait_for_function("window.__studio.browse.isOpen() && document.querySelectorAll('.br-row').length > 5", timeout=20000)
            cv = api(f"api/asset/{rec['id']}/calls")
            rung = [r for r in cv["calls"] if r.get("ring") is not None and not r["hidden"]]
            check("the calls view lists the calls, and some ring", len([r for r in cv["calls"] if not r["hidden"]]) > 10 and rung,
                  f"{len(cv['calls'])} rows, {len(rung)} with a ring")
            target = rung[0] if rung else cv["calls"][0]
            pg.evaluate("id => window.__studio.browse.select(id, { play: true })", target["id"])
            pg.wait_for_function("t => { const v = window.__studio.browse.video(); return !v.paused && v.currentTime > t; }",
                                 arg=target["play"][0] + 0.2, timeout=20000)
            check(f"a call plays from its ring ({target['label']}: ring {target['ring']:.1f} s, first word {target['start']:.1f} s)",
                  target["play"][0] == target["ring"] and target["play"][0] < target["start"])
            pg.wait_for_function("t => window.__studio.browse.video().currentTime > t", arg=target["start"] + 2.5, timeout=20000)
            ink = pg.evaluate("""() => { const c = window.__studio.browse.caps(); const d = c.getContext('2d').getImageData(0, Math.round(c.height*0.6), c.width, Math.round(c.height*0.16)).data;
                                  let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 200) n++; return n; }""")
            check("the call's captions show on the player", ink > 200, str(ink))
            pg.screenshot(path=str(shots / "e2e-calls.png"))
            pg.evaluate("window.__studio.browse.close()")
            check("leaving the calls empties the player", pg.evaluate("!window.__studio.browse.video().getAttribute('src')"))
        finally:
            if marks_before is None:
                marks_file.unlink(missing_ok=True)
            else:
                marks_file.write_bytes(marks_before)
        # Find calls shows the cost first; cancel, nothing spent
        pg.evaluate("id => document.querySelector(`.bin-item.rec[data-id='${id}']`).querySelector(\".icon-btn[title='More']\").click()", rec["id"])
        pg.click(".menu >> text=Find calls again…")
        pg.wait_for_selector(".dialog", timeout=30000)
        txt = pg.inner_text(".dialog")
        check("Find calls shows the cost before spending", "Estimated cost: $" in txt, txt[:200])
        pg.click(".dialog >> text=Cancel")
        # the strongest moment from a call with a live person on the other end (both voices on screen)
        live = {c["id"] for c in mo["calls"] if c["outcome"] not in ("voicemail", "no_answer", "not_a_call")}
        pool = [m for m in mo["moments"] if m.get("call") in live] or mo["moments"]
        best = sorted(pool, key=lambda m: (-m["strength"], m["end"] - m["start"]))[0]
        restore = (rec["id"], best["id"], best.get("state") or "new")
        pid = pg.evaluate("""async (m) => { const st = window.__studio; const d = await st.api.newProject({ asset: m.asset, moment: m.id, name: 'E2E check' });
                             await st.openShort(d.id); await new Promise(r => setTimeout(r, 1500)); return d.id; }""", {"asset": rec["id"], "id": best["id"]})
        check(f"short opened from moment \"{best['title']}\"", bool(pid))
        pg.screenshot(path=str(shots / "e2e-opened.png"))
        res = pg.evaluate("""async () => {
          const st = window.__studio, wait = (ms) => new Promise(r => setTimeout(r, ms));
          const len0 = st.doc.seqEnd(st.S.doc);
          st.S.snap = false;
          st.pb.seek(90); st.actions.run('split'); await wait(50);
          const pieces = st.S.doc.clips.filter(c => c.track === 'V1').length;
          // trim the tail to 45 s if longer
          const last = st.S.doc.clips.filter(c => c.track === 'V1').sort((a, b) => b.start - a.start)[0];
          if (st.doc.seqEnd(st.S.doc) > 1350) st.history.commit('Trim', d => st.ops.trim(d, { lib: st.lib }, st.doc.withLinked(d, [last.id]), 'out', 1350 - st.doc.clipEnd(last)));
          // zoom keyframes on the first piece
          const v = st.S.doc.clips.filter(c => c.track === 'V1').sort((a, b) => a.start - b.start)[0];
          st.history.commit('Zoom', d => { const c = d.clips.find(x => x.id === v.id); st.kf.addKey(c, 'scale', c.in + 15, 100, 'out'); st.kf.addKey(c, 'scale', c.in + 45, 112, 'in'); });
          // a title and a sound
          st.actions.run('newText', { f: 0, track: 'V2' }); await wait(30);
          const sfx = st.lib.all().find(a => a.rel && a.rel.startsWith('sfx/'));
          if (sfx) st.actions.run('placeAsset', { item: { kind: 'asset', id: sfx.id }, f: 60, track: 'A3' });
          await wait(30);
          st.actions.run('dissolveAt', { track: 'V1', f: 90 }); await wait(30);
          // voice tracks (2026-09-30): even the two voices
          const norm = await st.actions.run('normalizeVoices');
          // a new short has no captions until it's trimmed and Generate captions runs (2026-10-02, G1-G2)
          const caps0 = st.S.doc.captions.events.length, mode = st.S.doc.captions.mode;
          const t0 = performance.now();
          const made = await st.actions.run('generateCaptions');
          const g = Object.values(st.S.doc.captions.gen || {})[0] || {};
          await st.save.flush(true);
          const voiceTracks = st.S.doc.tracks.filter(t => t.voice).map(t => t.id + ':' + t.voice);
          return { len0, pieces, len: st.doc.seqEnd(st.S.doc), trans: st.S.doc.transitions.length, caps: st.S.doc.captions.events.length,
                   text: st.S.doc.clips.some(c => c.type === 'text'), sfx: !!sfx && st.S.doc.clips.some(c => c.asset === sfx.id && c.track === 'A3'),
                   voiceTracks, norm: norm && norm.report, caps0, mode, made, secs: Math.round((performance.now() - t0) / 1000),
                   gen: { words: (g.words || []).length, added: g.added, places: g.places, asked: g.asked, pickedA: g.pickedA, cost: g.cost, note: g.note,
                          status: st.captions.genStatus(st.S.doc) } };
        }""")
        check("the new short has You on A1 and Them on A2", res["voiceTracks"] == ["A1:me", "A2:them"], str(res["voiceTracks"]))
        check("Normalize voices measured both voices", res["norm"] and len(res["norm"]) == 2 and all("LUFS" in s for s in res["norm"]), str(res["norm"]))
        print(f"     normalize: {res['norm']}")
        check("razor made two pieces", res["pieces"] == 2, str(res))
        check("title and sound effect placed", res["text"] and res["sfx"], str(res))
        check("dissolve at the cut", res["trans"] == 1, str(res))
        check("a new short had no captions before Generate", res["mode"] == "generate" and res["caps0"] == 0, str(res))
        check("Generate captions made them (second listen, Claude's picks)", res["made"] is True and res["caps"] > 3
              and res["gen"]["words"] > 10 and res["gen"]["status"] == "ok" and not res["gen"]["note"], json.dumps(res["gen"]))
        print(f"     generate: {res['secs']} s, {json.dumps(res['gen'])}")
        pg.evaluate("window.__studio.pb.seek(100)")
        time.sleep(2.5)
        pg.screenshot(path=str(shots / "e2e-edited.png"))
        # close the window mid-edit: autosave must keep the edit
        pg.evaluate("() => { window.__studio.pb.seek(210); window.__studio.actions.run('addMarker'); }")
        pg.close(run_before_unload=True)         # as a person closing the window would
        time.sleep(1.5)
        doc = api(f"api/projects/{pid}")
        check("closing the window mid-edit kept the edit (autosave)", any(m["t"] == 210 for m in doc.get("markers", [])), str(doc.get("markers")))
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL + f"#short={pid}")
        pg.wait_for_function("window.__studio && window.__studio.S.doc && window.__studio.S.doc.id === '%s'" % pid, timeout=20000)
        check("reopening the page reopens the short", True)
        pg.evaluate("window.__studio.actions.run('export')")
        t0 = time.time()
        job = None
        while time.time() - t0 < 600:
            jobs = [j for j in api("api/exports") if j["project"] == pid]
            job = jobs[-1] if jobs else None
            if job and job["state"] in ("done", "error"):
                break
            time.sleep(2)
        check("export finished", job and job["state"] == "done", json.dumps(job)[:600])
        doc = api(f"api/projects/{pid}")        # what the export was made from
        check("the saved short still has its captions", len(doc["captions"]["events"]) > 3, str(len(doc["captions"]["events"])))
        if job and job["state"] == "done":
            out = Path(job["out"])
            secs = time.time() - t0
            info = subprocess.run([sc.ffmpeg_exe(), "-hide_banner", "-i", str(out)], capture_output=True, text=True).stderr
            check("1080x1920 at 30 fps", "1080x1920" in info and " 30 fps" in info)
            check("has audio (AAC 48 kHz)", "aac" in info and "48000 Hz" in info)
            dur = [l for l in info.splitlines() if "Duration:" in l][0].split("Duration:")[1].split(",")[0].strip()
            hh, mm, ss = dur.split(":")
            d = int(hh) * 3600 + int(mm) * 60 + float(ss)
            check(f"length matches the short ({d:.2f} s vs {res['len'] / 30:.2f} s)", abs(d - res["len"] / 30) < 0.1)
            from PIL import Image
            import numpy as np
            png = HERE / "out" / "e2e-frame.png"
            png.parent.mkdir(exist_ok=True)

            def band_at(f):
                subprocess.run([sc.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(out), "-vf", f"select=eq(n\\,{f})",
                                "-frames:v", "1", str(png)], check=True)
                im = Image.open(png).convert("RGB")
                return np.asarray(im.crop((40, doc["captions"]["y"] - 80, 1040, doc["captions"]["y"] + 80))).astype(int)

            # colored by voice: a group of Jonathan's words shows blue, a group of the other side's red or pink
            evs = doc["captions"]["events"]
            mine = next((e for e in evs if len(e["words"]) >= 2 and all(w.get("k") == "me" for w in e["words"])), None)
            theirs = next((e for e in evs if len(e["words"]) >= 2 and all(w.get("k") in ("m", "f") for w in e["words"])), None)
            if mine:
                bd = band_at(mine["words"][0]["s"] + 3)
                blue = int(((bd[..., 0] > 40) & (bd[..., 0] < 120) & (bd[..., 1] > 95) & (bd[..., 1] < 170) & (bd[..., 2] > 200)).sum())
                check("captions are burned in: Jonathan's words blue (#4D80E6)", blue > 150, str(blue))
            if theirs:
                bd = band_at(theirs["words"][0]["s"] + 3)
                warm = int(((bd[..., 0] > 215) & (bd[..., 1] < 135) & (bd[..., 2] < 210)).sum())
                check("captions are burned in: the other side's words red or pink", warm > 150, str(warm))
            check("the short has words from both sides to check", bool(mine) and bool(theirs), f"{bool(mine)} {bool(theirs)}")
            print(f"     export took {secs:.0f} s for {d:.1f} s of video -> {out}")
            if not keep:
                out.unlink(missing_ok=True)
        check("no page errors", not errors, "; ".join(errors[:3]))
        b.close()
    if not keep:
        try:
            urllib.request.urlopen(urllib.request.Request(URL + f"api/projects/{pid}", method="DELETE"), timeout=10)
            if restore:
                api(f"api/asset/{restore[0]}/moments/{restore[1]}", "PATCH", {"state": restore[2]})
        except Exception:  # noqa: BLE001
            pass
    print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
