"""Unit checks for who-said-each-word (scripts/studio_speakers.py) and the voice parts of Find moments (2026-09-30).

  python projects/studio/tests/speakers-unit.py

Runs in a throwaway media folder (STUDIO_MEDIA, STUDIO_VOICEPRINT, STUDIO_CONFIG), no network, no models.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="studio-spk-"))
os.environ["STUDIO_MEDIA"] = str(TMP / "media")
os.environ["STUDIO_VOICEPRINT"] = str(TMP / "voiceprint.json")
os.environ["STUDIO_CONFIG"] = str(TMP / "config.json")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import numpy as np  # noqa: E402
import studio_common as sc  # noqa: E402
import studio_speakers as ss  # noqa: E402
import studio_moments as sm  # noqa: E402

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


# ---- pitch
t = np.arange(16000 * 3) / 16000
for f in (110, 140, 190, 230):
    x = (0.5 * np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)).astype(np.float32)
    p = ss.pitch_median(x)
    check(f"pitch of a {f} Hz voice-like tone", p is not None and abs(p - f) < 2, str(p))
check("pitch 140 Hz reads as a man, 190 Hz as a woman", ss._pitch_gender(140) == "man" and ss._pitch_gender(190) == "woman")
check("silence has no pitch", ss.pitch_median(np.zeros(16000 * 2, np.float32)) is None)
# phone audio: everything under 300 Hz is cut, so the fundamental itself is gone; the harmonics still carry the pitch
for f in (110, 220):
    x = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, 12))
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / 16000)
    X[(fr < 300) | (fr > 3400)] = 0
    p = ss.pitch_median(np.fft.irfft(X, len(x)).astype(np.float32))
    check(f"phone-band {f} Hz voice (fundamental filtered out) still reads {f} Hz", p is not None and abs(p - f) < 3, str(p))

# ---- windows
segs = [[0, 590, 0, 0], [596, 900, 1, 1], [901, 1195, 2, 2], [1203, 1500, 3, 3]]
w = ss.plan_windows(1500, segs)
check("windows cut in the longest pause near each 10-minute mark", [round(a) for a, _ in w] == [0, 593, 1199], str(w))
check("windows cover the whole file", w[0][0] == 0 and w[-1][1] == 1500 and all(w[i][1] == w[i + 1][0] for i in range(len(w) - 1)))
w2 = ss.plan_windows(1250, [])
check("a short last stretch joins the window before it", len(w2) == 2 and w2[-1] == (600.0, 1250.0), str(w2))
check("a short file is one window", ss.plan_windows(300, []) == [(0.0, 300.0)])

# ---- words to turns
turns = [[0.0, 1.0, "S1"], [1.0, 2.0, "S2"], [4.0, 5.0, "S1"], [10.0, 100.0, "S3"], [50.0, 51.0, "S4"]]
words = [[0.9, 1.3, "a"], [2.1, 2.2, "b"], [3.0, 3.1, "c"], [3.8, 3.9, "d"], [60.0, 60.5, "e"], [50.2, 50.6, "f"]]
raw = ss.raw_assign(turns, words)
check("a word across a turn edge goes to the turn it overlaps most", raw[0] == "S2", str(raw))
check("a word in a short gap takes the nearest turn (after it ends)", raw[1] == "S2", str(raw))
check("a word far from every turn has no voice", raw[2] is None, str(raw))
fill = ss.raw_assign([[0.0, 1.0, "S1"], [3.0, 4.0, "S2"]], [[0.5, 0.9, "a"], [1.4, 1.8, "b"], [2.0, 2.4, "c"], [3.2, 3.6, "d"]])
check("a word the split missed takes its neighbour's voice when no pause sits between", fill == ["S1", "S1", "S1", "S2"], str(fill))
check("a word in a short gap takes the nearest turn (before it starts)", raw[3] == "S1", str(raw))
check("a long turn that started much earlier still counts", raw[4] == "S3", str(raw))
check("overlapping speech: the turn covering more of the word wins", raw[5] == "S4", str(raw))

# ---- a recording with voices
AID = "a_test00000001"
ad = sc.CACHE / AID
ad.mkdir(parents=True)
wl = []
tt = 0.0
for i in range(40):
    wl.append([round(tt, 2), round(tt + 0.4, 2), f"w{i}"])
    tt += 0.5
(ad / "transcript.json").write_text(json.dumps({"v": 1, "words": wl, "segments": [[0, 20, 0, 39]], "duration": 20}))


def T(a, b, k):
    return [wl[a][0] - 0.05, wl[b][1] + 0.05, k]


sp = {"v": 1, "asset": AID, "rev": "r1", "model": ss.MODEL_TAG, "windows": [[0, 20]],
      "turns": [T(0, 9, "S1"), T(10, 19, "S2"), T(20, 24, "S3"), T(25, 29, "S4"), T(30, 34, "S5"), T(35, 39, "S6")],
      "groups": {"S1": {"sec": 5, "f0": 120, "emb": [1, 0, 0, 0]}, "S2": {"sec": 5, "f0": 215, "emb": [0, 1, 0, 0]},
                 "S3": {"sec": 2.5, "f0": 105, "emb": [0, 0, 1, 0]}, "S4": {"sec": 2.5, "f0": 118, "emb": [0.98, 0.2, 0, 0]},
                 "S5": {"sec": 2.5, "f0": None, "emb": [0, 0, 0, 1]}, "S6": {"sec": 2.5, "f0": 230, "emb": [0, 0.1, 0, 1]}}}
(ad / "speakers.json").write_text(json.dumps(sp))
r = ss.resolve(AID)
cls = ss.word_classes(AID)
check("no labels and no voiceprint yet: every voice unknown (today's white), so Jonathan never shows up red", set(cls) == {"u"}, str(set(cls)))
check("voice names: plain numbers in order of first word", [v["name"] for v in r["speakers"]][:3] == ["Voice 1", "Voice 2", "Voice 3"], str([v["name"] for v in r["speakers"]]))
check("the voices carry a revision the page compares", r["vrev"] == ss.voices_rev(AID) and r["vrev"].count("-") == 3)

labels = {"v": 1, "rev": "r1", "model": "test", "jonathan": ["S1"],
          "voices": {"S2": {"gender": "woman", "name": "Dana", "role": "gatekeeper", "same_as": ""},
                     "S3": {"gender": "unknown", "name": "", "role": "owner", "same_as": ""},
                     "S4": {"gender": "man", "name": "", "role": "other", "same_as": "S1"},
                     "S6": {"gender": "man", "name": "Mike", "role": "service_rep", "same_as": ""}}}
(ad / "speaker-labels.json").write_text(json.dumps(labels))
r = ss.resolve(AID)
cls = ss.word_classes(AID)
names = {v["key"]: v for v in r["speakers"]}
check("Claude's labels win over guesses", cls[0] == "me" and cls[10] == "f" and cls[35] == "m", str(cls[::5]))
check("gender unknown from Claude falls back to pitch", cls[20] == "m")
check("same_as joins a split group to Jonathan's", cls[25] == "me")
check("all of Jonathan's groups are one voice, listed first as You", r["speakers"][0]["key"] == "me" and r["speakers"][0]["name"] == "You"
      and sorted(r["speakers"][0]["groups"]) == ["S1", "S4"], str(r["speakers"][0]))
check("names: Claude's first name, else the role", names["S2"]["name"] == "Dana" and names["S3"]["name"] == "Owner", str(names))
check("Claude's gender beats pitch (230 Hz labeled a man stays a man)", names["S6"]["cls"] == "m")
check("each word points at a voice; raw keeps the split's own group", r["speakers"][r["spk"][25]]["key"] == "me"
      and r["rawKeys"][r["raw"][25]] == "S4")
check("Jonathan's voice says where it came from", r["speakers"][0]["source"] == "claude")

# ---- fixes
try:
    ss.apply_patch(AID, {"groups": {"S9": {"who": "me"}}})
    check("an unknown voice is refused", False)
except ValueError:
    check("an unknown voice is refused", True)
try:
    ss.apply_patch(AID, {"words": {"999": "S2"}})
    check("a word id out of range is refused", False)
except ValueError:
    check("a word id out of range is refused", True)
try:
    ss.apply_patch(AID, {"groups": {"S2": {"who": "other", "gender": "robot"}}})
    check("a label that is not me, woman or man is refused", False)
except ValueError:
    check("a label that is not me, woman or man is refused", True)
r = ss.apply_patch(AID, {"groups": {"S2": {"who": "other", "gender": "man"}}})
check("a fix beats Claude (Dana flipped to a man)", ss.word_classes(AID)[10] == "m"
      and next(v for v in r["speakers"] if v["key"] == "S2")["source"] == "you")
check("the flipped voice keeps Claude's name", next(v for v in r["speakers"] if v["key"] == "S2")["name"] == "Dana")
ss.apply_patch(AID, {"words": {"9": "S2", "10": "me"}})
c = ss.word_classes(AID)
check("word fixes move single words", c[9] == "m" and c[10] == "me", str(c[8:12]))
r = ss.apply_patch(AID, {"new_voice": {"gender": "woman", "words": [11, 12]}})
c = ss.word_classes(AID)
nv = next(v for v in r["speakers"] if v["key"].startswith("N"))
check("a new voice takes the chosen words", c[11] == "f" and c[12] == "f" and nv["name"] == "New voice 1", str(nv))
ss.apply_patch(AID, {"words": {"9": None, "10": None, "11": None, "12": None}})
check("resetting word fixes puts them back", ss.word_classes(AID)[9:13] == ["me", "m", "m", "m"], str(ss.word_classes(AID)[9:13]))
ss.apply_patch(AID, {"groups": {"S2": None}})
check("resetting a voice goes back to Claude's label", ss.word_classes(AID)[10] == "f")
ss.apply_patch(AID, {"merge": {"S4": "S4"}, "groups": {"S4": {"who": "other", "gender": "man"}}})
check("'this whole voice is a man' pulls a group out of Jonathan's", ss.word_classes(AID)[25] == "m")
ss.apply_patch(AID, {"merge": {"S4": None}, "groups": {"S4": None}})
check("and resetting it rejoins Jonathan by Claude's same_as", ss.word_classes(AID)[25] == "me")
ss.apply_patch(AID, {"groups": {"S4": {"who": "other", "gender": "woman"}}})
check("last action wins: labeling a merged group on its own detaches it (no merge sent)", ss.word_classes(AID)[25] == "f")
ss.apply_patch(AID, {"merge": {"S4": "S1"}})
ed = sc.read_json(ad / "speaker-edits.json")
check("last action wins: joining it to a voice drops its own label", ss.word_classes(AID)[25] == "me" and "S4" not in ed["groups"], str(ed))
ss.apply_patch(AID, {"merge": {"S4": None}})
ss.apply_patch(AID, {"merge": {"S3": "S6", "S6": "S3"}})
check("a merge loop does not hang", ss.word_classes(AID)[20] in ("m", "f", "u"))
ss.apply_patch(AID, {"merge": {"S3": None, "S6": None}})
ss.apply_patch(AID, {"merge": {"S5": "S2"}})
r = ss.resolve(AID)
check("'same person as' joins two voices into one row", ss.word_classes(AID)[30] == "f"
      and "S5" in next(v for v in r["speakers"] if v["key"] == "S2")["groups"])
ss.apply_patch(AID, {"merge": {"S5": None}})

# ---- voiceprint
vp = sc.read_json(sc.VOICEPRINT)
check("the voiceprint is built from groups Claude or Jonathan marked as him", vp and vp["groups"] == 2, str(vp and vp["groups"]))
check("the voiceprint leans on his longer group", vp and vp["emb"][0] > 0.95, str(vp and vp["emb"]))
check("the match threshold is set and sane", vp and 0.5 <= vp["thr"] <= 0.97, str(vp and vp["thr"]))
AID2 = "a_test00000002"
ad2 = sc.CACHE / AID2
ad2.mkdir(parents=True)
(ad2 / "transcript.json").write_text(json.dumps({"v": 1, "words": wl[:10], "segments": [[0, 5, 0, 9]], "duration": 5}))
(ad2 / "speakers.json").write_text(json.dumps({"v": 1, "asset": AID2, "rev": "q1", "model": ss.MODEL_TAG, "windows": [[0, 5]],
    "turns": [T(0, 4, "S1"), T(5, 9, "S2")],
    "groups": {"S1": {"sec": 2.5, "f0": 125, "emb": [0.99, 0.1, 0, 0]}, "S2": {"sec": 2.5, "f0": 120, "emb": [0, 0, 1, 0]}}}))
c2 = ss.word_classes(AID2)
check("a new recording: the voice matching his voiceprint is guessed as him", c2[0] == "me" and c2[9] == "m", str(c2))
check("a guess never feeds the voiceprint", sc.read_json(sc.VOICEPRINT)["groups"] == 2)
table = ss.voice_table(AID2)
check("the voice table shows seconds, pitch and the voiceprint match", table[0].startswith("S1: 2 s, 125 Hz, voiceprint 0.9"), str(table))

# ---- voice runs: the recording split into Jonathan's stretches and the other side's (voice tracks, 2026-09-30)
ww = [[0.0, 0.4, "a"], [0.5, 0.9, "b"], [2.0, 2.4, "c"], [2.5, 2.9, "d"], [3.0, 3.2, "e"], [5.0, 5.4, "f"]]
runs = ss.voice_runs(ww, ["me", "me", "them", "them", None, "me"])
check("runs cover the recording end to end, cut in the middle of each pause", runs == [[0.0, 1.45, "me"], [1.45, 4.1, "them"], [4.1, 1e9, "me"]], str(runs))
check("a word with no side goes with the words before it", runs[1][1] == 4.1)
check("words before any side join the first stretch", ss.voice_runs([[0, 1, "x"], [2, 3, "y"]], [None, "them"]) == [[0.0, 1e9, "them"]])
check("no sides at all: no runs", ss.voice_runs(ww, [None] * 6) == [])
check("a voice track plays only its side's stretches, clipped to the clip", ss.gate(runs, "them", 1.0, 3.0) == [[1.45, 3.0]]
      and ss.gate(runs, "me", 1.0, 5.0) == [[1.0, 1.45], [4.1, 5.0]], str(ss.gate(runs, "me", 1.0, 5.0)))
check("without voice data You plays everything and Them nothing", ss.gate(None, "me", 1, 2) == [[1, 2]] and ss.gate([], "them", 1, 2) == [])
rr = ss.resolve(AID)
check("resolve hands the runs to the page and the exporter", rr["runs"] and all(rr["runs"][i][1] == rr["runs"][i + 1][0] for i in range(len(rr["runs"]) - 1)), str(rr["runs"][:3]))

# ---- a scrap Claude left out takes the voice around it
AID4 = "a_test00000004"
ad4 = sc.CACHE / AID4
ad4.mkdir(parents=True)
(ad4 / "transcript.json").write_text(json.dumps({"v": 1, "words": wl[:12], "segments": [[0, 6, 0, 11]], "duration": 6}))
(ad4 / "speakers.json").write_text(json.dumps({"v": 1, "asset": AID4, "rev": "s1", "model": ss.MODEL_TAG, "windows": [[0, 6]],
    "turns": [T(0, 3, "S1"), T(4, 4, "S9"), T(5, 8, "S1"), T(9, 11, "S2")],
    "groups": {"S1": {"sec": 4, "f0": 120, "emb": [0, 0, 0.6, 0.8]}, "S9": {"sec": 0.5, "f0": 110, "emb": [0, 0, 1, 0]},
               "S2": {"sec": 1.5, "f0": 220, "emb": [0, 1, 0, 0]}}}))
(ad4 / "speaker-labels.json").write_text(json.dumps({"v": 1, "rev": "s1", "model": "t", "jonathan": ["S1"],
    "voices": {"S2": {"gender": "woman", "name": "", "role": "gatekeeper", "same_as": ""}}}))
c4 = ss.word_classes(AID4)
check("a one-word scrap Claude left out, between Jonathan's words, is Jonathan (not a pitch guess)", c4[4] == "me", str(c4))
check("the labeled words around it keep their voices", c4[3] == "me" and c4[5] == "me" and c4[10] == "f", str(c4))

# ---- a new split sets old labels aside
res = dict(sp, rev="r2")
ss.finalize(ad, res)
check("labels from an older split are set aside", not (ad / "speaker-labels.json").exists() and (ad / "speaker-labels.stale-r1.json").exists())
ed = sc.read_json(ad / "speaker-edits.json")
check("fixes from an older split are set aside; word fixes to a new voice are kept", ed and ed["rev"] == "r2" and not ed["groups"]
      and (ad / "speaker-edits.stale-r1.json").exists(), str(ed))
ss.finalize(ad, dict(sp, rev="r1"))
(ad / "speaker-labels.json").write_text(json.dumps(labels))
sc.write_json_atomic(ad / "speaker-edits.json", {"rev": "r1", "groups": {}, "merge": {}, "words": {}, "new": {}})

# ---- Claude's side
out = ss.write_labels(AID, ["[S1]", "S4", "S99"], [
    {"tag": "S2", "gender": "woman", "name": " Dana ", "role": "gatekeeper", "same_as": ""},
    {"tag": "S1", "gender": "man", "name": "", "role": "owner", "same_as": ""},
    {"tag": "S3", "gender": "man", "name": "", "role": "owner", "same_as": "S3"},
    {"tag": "S5", "gender": "robot", "name": "", "role": "other", "same_as": "S77"}], "claude-opus-5")
check("labels: brackets stripped, unknown tags dropped", out["jonathan"] == ["S1", "S4"], str(out["jonathan"]))
check("labels: a tag listed as Jonathan is not also a voice", "S1" not in out["voices"])
check("labels: names trimmed, same_as to itself or nowhere dropped, bad gender unknown",
      out["voices"]["S2"]["name"] == "Dana" and out["voices"]["S3"]["same_as"] == "" and out["voices"]["S5"]["same_as"] == ""
      and out["voices"]["S5"]["gender"] == "unknown", str(out["voices"]))
tr = {"words": wl, "segments": [[0, 5, 0, 9], [5, 10, 10, 19]], "duration": 20}
tags = ["S1"] * 5 + [None] * 2 + ["S1"] * 3 + ["S2"] * 4 + ["S1"] * 6
lines = sm.build_lines(tr, tags).splitlines()
check("tagged lines: a tag opens the line and marks each change", lines[0].startswith("0|00:00:00|[S1] w0 w1") and "[S2]" not in lines[0]
      and lines[1].startswith("1|00:00:05|[S2] w10 w11 w12 w13 [S1] w14"), lines[1][:60])
check("untagged lines are the old format", sm.build_lines(tr).splitlines()[0] == "0|00:00:00|" + " ".join(f"w{i}" for i in range(10)))
check("the untagged prompt is the 2026-09-29 prompt", sm.SYSTEM.startswith(sm.INTRO) and "Do two things." in sm.SYSTEM and "[S12]" not in sm.SYSTEM)
req, voices, rev = sm.request(sm.load_transcript(AID), AID)
check("with a split, Find moments sends tags, the voice table and the three-task prompt",
      voices and rev == "r1" and req["system"] == sm.SYSTEM_TAGGED and req["messages"][0]["content"].startswith("Voices (tag:")
      and "[S1]" in req["messages"][0]["content"])
check("room for moments, labels and thinking (128k)", req["max_tokens"] == 128000)
sch = sm.schema_for(True)
check("the schema asks for jonathan_tags and voices too", {"calls", "moments", "jonathan_tags", "voices"} <= set(sch["required"]))
check("without a split the schema is unchanged", sm.schema_for(False) is sm.SCHEMA)
req2, _, _ = sm.request(sm.load_transcript(AID), AID, voices_only=True)
check("labels only: its own prompt and schema", req2["system"] == sm.SYSTEM_VOICES and sm.schema_for(True, True) is sm.SCHEMA_VOICES)
try:
    ss.write_labels(AID, ["S1"], [], "claude-opus-5", rev="old-split")
    check("labels made from an older split are refused", False)
except RuntimeError:
    check("labels made from an older split are refused", True)
AID3 = "a_test00000003"
(sc.CACHE / AID3).mkdir(parents=True)
(sc.CACHE / AID3 / "transcript.json").write_text(json.dumps(tr))
req3, v3, _ = sm.request(sm.load_transcript(AID3), AID3)
check("no split: the old request exactly", not v3 and req3["system"] == sm.SYSTEM and req3["messages"][0]["content"].startswith("Transcript:\n"))
try:
    sm.request(sm.load_transcript(AID3), AID3, voices_only=True)
    check("labels only needs a split", False)
except RuntimeError:
    check("labels only needs a split", True)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
