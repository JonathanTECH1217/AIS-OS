"""Unit checks for prep's safety rules (scripts/studio_prep.py, 2026-10-02): a missing remux never silences a recording,
the server's start-up check notices outputs that are gone, and "Prepare again" removes an old output only when its
stage runs again.

  python projects/studio/tests/prep-unit.py

Background: on 2026-10-02 the 3-hour recording's remux (orig.mp4) was missing while status.json said done. "Prepare
again" had deleted it at the click; the rebuild waited (Monarc Calls holds prep while OBS records) and a restart lost
the queue. The sound blocks read only orig.mp4, so every short from that recording played silent.
Runs in a throwaway media folder (STUDIO_MEDIA); the stages are stand-ins, nothing is encoded.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="studio-prep-"))
os.environ["STUDIO_MEDIA"] = str(TMP / "media")
os.environ["STUDIO_CONFIG"] = str(TMP / "config.json")
os.environ["STUDIO_VOICEPRINT"] = str(TMP / "voiceprint.json")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import studio_common as sc  # noqa: E402
import studio_prep as prep  # noqa: E402

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


aid = "a_prep"
d = sc.CACHE / aid
d.mkdir(parents=True, exist_ok=True)
(sc.MEDIA / "inbox").mkdir(parents=True, exist_ok=True)
(sc.MEDIA / "inbox" / "2026-09-30 10-27-42.mkv").write_bytes(b"obs file")
meta = {"id": aid, "rel": "inbox/2026-09-30 10-27-42.mkv", "name": "2026-09-30 10-27-42.mkv", "kind": "video", "orig": "cache"}
sc.write_json_atomic(d / "meta.json", meta)

# ---- the sound never depends on the remux alone
check("no remux yet: the OBS file stands in", prep.orig_path(aid, meta) == sc.MEDIA / meta["rel"], str(prep.orig_path(aid, meta)))
(d / "orig.mp4").write_bytes(b"remux")
check("with the remux there, the remux", prep.orig_path(aid, meta) == d / "orig.mp4")
check("an MP4 that plays as it is: the file itself", prep.orig_path(aid, dict(meta, orig="source")) == sc.MEDIA / meta["rel"])
check("a removed copy: the file itself", prep.orig_path(aid, dict(meta, orig="removed")) == sc.MEDIA / meta["rel"])

# ---- the start-up check looks at the outputs, not only status.json
for f in ("peaks-10.i8", "transcript.json", "speakers.json"):
    (d / f).write_text("x")
(d / "thumbs").mkdir(exist_ok=True)
(d / "thumbs" / ".done").write_text("{}")
done = {s: {"state": "done"} for s in ("remux", "peaks", "proxy", "transcript", "speakers")}
check("everything there and marked done: nothing to run", prep.missing_stages(aid, meta, done) == [])
(d / "orig.mp4").unlink()
check("marked done but the remux is gone: remux runs again", prep.missing_stages(aid, meta, done) == ["remux"],
      str(prep.missing_stages(aid, meta, done)))
check("a stage not marked done still counts", "speakers" in prep.missing_stages(aid, meta, dict(done, speakers={"state": "error"})))

# ---- "Prepare again": old outputs go only when their stage runs
ran = []


def stand_in(stage, out):
    def fn(a, m, st, cancel):
        ran.append(stage)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("new " + stage)
    return fn


real = dict(prep.STAGE_FN)
prep.STAGE_FN.update({"remux": stand_in("remux", d / "orig.mp4"), "peaks": stand_in("peaks", d / "peaks-10.i8"),
                      "proxy": stand_in("proxy", d / "thumbs" / ".done"),
                      "transcript": stand_in("transcript", d / "transcript.json"),
                      "speakers": stand_in("speakers", d / "speakers.json")})
try:
    (d / "orig.mp4").write_text("old remux")
    got = prep.request_redo(aid, ["peaks", "proxy", "nonsense"])
    check("Prepare again keeps only real stages", got == ["peaks", "proxy"], str(got))
    check("and deletes nothing at the click", (d / "peaks-10.i8").read_text() == "x" and (d / "thumbs" / ".done").exists())
    check("it waits in redo.json (a restart doesn't lose it)", prep.redo_stages(aid) == {"peaks", "proxy"})
    prep.run_asset(aid, meta)
    check("then exactly those stages run again", sorted(ran) == ["peaks", "proxy"], str(ran))
    check("their outputs are new; the rest untouched", (d / "peaks-10.i8").read_text() == "new peaks"
          and (d / "orig.mp4").read_text() == "old remux" and (d / "transcript.json").read_text() == "x")
    check("and redo.json is cleared", not prep.redo_path(aid).exists())
    st = json.loads((d / "status.json").read_text())["stages"]
    check("status says done for all", all(v["state"] == "done" for v in st.values()), str(st))
    ran.clear()
    (d / "orig.mp4").unlink()
    prep.run_asset(aid, meta)
    check("a remux that went missing is made again on the next run", ran == ["remux"] and (d / "orig.mp4").read_text() == "new remux", str(ran))
    # an output outside Studio's cache (an MP4 source's done file is the source itself) is never deleted
    ran.clear()
    prep.request_redo(aid, ["remux"])
    prep.run_asset(aid, dict(meta, orig="source"))
    check("Prepare again never deletes the recording itself", (sc.MEDIA / meta["rel"]).read_bytes() == b"obs file" and ran == [], str(ran))
finally:
    prep.STAGE_FN.clear()
    prep.STAGE_FN.update(real)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
