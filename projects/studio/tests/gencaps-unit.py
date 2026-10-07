"""Unit checks for Generate captions (scripts/studio_gencaps.py and studio_listen.py, 2026-10-02; grill G1-G7 in
brainstorms/2026-10-02-captions-after-trim.md): the kept parts heard as padded stretches, the two listens lined up,
Jonathan's own fixes pinned, Claude's picks applied (the second listen when nobody picks), each word's way to its
voice, what an export counts as missing, and one whole run through the child process with the fixtures' fake listen.

  python projects/studio/tests/gencaps-unit.py

Runs in a throwaway copy of the test fixtures (STUDIO_MEDIA). Claude is never called: STUDIO_NO_CLAUDE is set, and
the one check of the Claude path swaps in a stand-in for studio_moments._call.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="studio-gencaps-"))
os.environ["STUDIO_MEDIA"] = str(TMP / "media")
os.environ["STUDIO_CONFIG"] = str(TMP / "config.json")
os.environ["STUDIO_VOICEPRINT"] = str(TMP / "voiceprint.json")
os.environ["STUDIO_NO_CLAUDE"] = "1"
os.environ["STUDIO_FAKE_LISTEN"] = "1"
sys.path.insert(0, str(HERE / "fixtures"))
import make as fixtures  # noqa: E402
if not fixtures.seed_current():
    subprocess.run([sys.executable, str(HERE / "fixtures" / "make.py")], check=True)
shutil.copytree(HERE / "fixtures" / "seed", TMP / "media")
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import studio_common as sc  # noqa: E402
import studio_gencaps as gc  # noqa: E402

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


# ---- the stretches heard and kept
heard, keep = gc.plan_ranges([[10.0, 20.0], [22.0, 30.0], [100.0, 110.0]], 200.0)
check("kept parts closer than 4 s are heard as one", heard == [[8.0, 32.0], [98.0, 112.0]], str(heard))
check("the words reach 1 s past each kept part", keep == [[9.0, 31.0], [99.0, 111.0]], str(keep))
heard, keep = gc.plan_ranges([[0.5, 5.0], [195.0, 199.5]], 200.0)
check("never before 0 or past the end", heard == [[0.0, 7.0], [193.0, 200.0]] and keep == [[0.0, 6.0], [194.0, 200.0]], f"{heard} {keep}")
check("a backwards part is ignored", gc.plan_ranges([[5.0, 3.0]], 10.0) == ([], []))
check("letters and digits only when lining up", gc.norm("Most.") == "most" and gc.norm("10%") == "10" and gc.norm("C3's") == "c3s")

# ---- lining up the two listens
W = lambda s, t, i=None: [s, s + 0.4, t] + ([i] if i is not None else [])  # noqa: E731
A = [W(0.3, "so", 0), W(0.8, "here", 1), W(1.3, "is", 2), W(1.8, "the", 3), W(2.3, "things", 4), W(2.8, "most.", 5),
     W(3.9, "integrators", 6), W(4.4, "lose", 7), W(4.9, "the", 8), W(5.4, "lead", 9)]
B = [W(0.3, "so"), W(0.8, "here"), W(1.3, "was"), W(1.8, "the"), W(2.3, "ring"), W(2.8, "most."), W(3.4, "really"),
     W(3.9, "integrators"), W(4.4, "lose"), W(5.4, "lead,")]
edited = {4}                     # he fixed word 4 to "things" by hand
sp = gc.spans(A, B, edited)
check("four places differ: is/was, things/ring, really added, the missed",
      [(s["op"], s["a1"] - s["a0"], s["b1"] - s["b0"]) for s in sp] == [("replace", 1, 1), ("replace", 1, 1), ("insert", 0, 1), ("delete", 1, 0)],
      str([(s["op"], s["a0"], s["a1"], s["b0"], s["b1"]) for s in sp]))
check("the place holding his fix is pinned, the rest are asked", [s["pinned"] for s in sp] == [False, True, False, False])
words = gc.apply(A, B, edited, sp, {})
texts = [w[2] for w in words]
check("nobody picked: the second listen wins, his fix stays", texts == ["so", "here", "was", "the", "things", "most.", "really",
                                                                       "integrators", "lose", "lead,"], str(texts))
check("words where the two agree carry the second listen's punctuation", texts[-1] == "lead,")
check("his fixed word keeps its first-transcript id; second-listen words have none", words[4][3] == 4 and words[2][3] is None)
words = gc.apply(A, B, edited, sp, {1: "A", 3: "B", 4: "A"})
texts = [w[2] for w in words]
check("Claude's picks: A keeps the first listen's words, B the second's", texts == ["so", "here", "is", "the", "things", "most.", "really",
                                                                              "integrators", "lose", "the", "lead,"], str(texts))
check("an A pick keeps the first transcript's id", words[2][3] == 2 and words[9][3] == 8)
ov = gc.apply([W(1.0, "a", 0)], [[0.9, 1.5, "b"], [1.2, 1.6, "c"]], set(), gc.spans([W(1.0, "a", 0)], [[0.9, 1.5, "b"], [1.2, 1.6, "c"]], set()), {})
check("words from the two listens never overlap in time", all(ov[i][1] <= ov[i + 1][0] for i in range(len(ov) - 1)), str(ov))

# ---- each word's way to its voice
words = gc.apply(A, B, edited, sp, {})
dn = gc.donors(words, A)
check("a word heard by both takes the first-transcript word it overlaps", dn[2] == 2 and dn[0] == 0)
check("a word only the second listen heard, in a pause, has no donor", dn[6] is None)

# ---- what Claude reads
runs = [[0.0, 3.6, "me"], [3.6, 1e9, "them"]]
text = gc.prompt(A, B, sp, runs)
check("Claude sees each askable place with both readings", '[1| A: "is" | B: "was"]' in text and '[3| A: "" | B: "really"]' in text
      and '[4| A: "the" | B: ""]' in text, text)
check("a pinned place shows his reading, no number", "things" in text and "[2|" not in text, text)
check("a new line where the speaker side changes", text.splitlines()[0].startswith("Jonathan: ") and text.splitlines()[1].startswith("Other side: "), text)
import studio_moments as sm  # noqa: E402
real_call, real_client = sm._call, sm._client
seen = {}


def fake_call(client, req, schema, on_status, effort="high"):
    seen.update(req=req, effort=effort, schema=schema)

    class U:
        input_tokens, output_tokens = 900, 120

    class M:
        model, usage = "claude-opus-5", U()
    return {"picks": [{"n": 1, "pick": "A"}, {"n": 2, "pick": "B"}, {"n": 9, "pick": "A"}]}, M(), 0.0075, 1.2


sm._call, sm._client = fake_call, (lambda: None)
try:
    picks, cost, model, usage, _ = gc.ask_claude("a_x", A, B, sp, runs)
finally:
    sm._call, sm._client = real_call, real_client
check("Claude is asked at low effort with the schema", seen.get("effort") == "low" and seen["schema"] is gc.SCHEMA
      and seen["req"]["model"] == "claude-opus-5" and "never write words of your own" in seen["req"]["system"].lower())
check("only picks for places that were asked count (not the pinned one, not unknown numbers)", picks == {1: "A"}, str(picks))
check("the cost comes back", cost == 0.0075 and usage == {"input_tokens": 900, "output_tokens": 120})

# ---- what an export counts as missing (G5)
doc = {"fps": 30, "captions": {"mode": "generate", "on": True},
       "clips": [{"type": "audio", "track": "A1", "voice": "me", "asset": "a1", "in": 30, "out": 210, "on": True},
                 {"type": "audio", "track": "A2", "voice": "them", "asset": "a1", "in": 30, "out": 210, "on": True},
                 {"type": "video", "track": "V1", "asset": "a1", "in": 30, "out": 210}]}
check("Generate mode, nothing generated: none", gc.missing(doc) == "none")
doc["captions"]["gen"] = {"a1": {"ranges": [[0.0, 8.0]], "words": []}}
check("generated over what the clips keep: fine", gc.missing(doc) is None)
doc["clips"][0]["out"] = 330
check("a clip reaching 3 s past what was generated: part", gc.missing(doc) == "part")
doc["clips"][0]["out"] = 250
check("half a second past is still fine", gc.missing(doc) is None, str(gc.uncovered([[1.0, 250 / 30]], [[0.0, 8.0]])))
check("captions switched off: nothing to ask", gc.missing(dict(doc, captions={"mode": "generate", "on": False})) is None)
check("an older short (no mode) is never asked about", gc.missing(dict(doc, captions={"on": True})) is None)
check("uncovered seconds add up across ranges", abs(gc.uncovered([[0, 10], [20, 30]], [[2, 8], [25, 40]]) - 9.0) < 1e-9)

# ---- one whole run: the child process (fake listen), the fixtures' transcript, voices from the split
src = sc.MEDIA / "inbox" / "src20.mp4"
aid = sc.asset_id(src)
sc.write_json_atomic(sc.CACHE / aid / "meta.json", {"id": aid, "rel": "inbox/src20.mp4", "name": "src20.mp4", "kind": "video",
                                                    "duration": 20.0, "orig": "source", "audio": True})
sc.write_json_atomic(sc.CACHE / aid / "transcript-edits.json", {"4": "things"})
seen_status = []
r = gc.generate(aid, [[1.0, 6.0], [10.2, 13.0]], on_status=lambda m, p=None: seen_status.append(m))
texts = [w[2] for w in r["words"]]
check("a run through the child process answers words", len(texts) > 12 and r["listen"] == "fake", str(r)[:300])
check("it said what it was doing", "Listening again" in seen_status, str(seen_status))
check("kept parts more than 4 s apart stay two stretches", r["ranges"] == [[0.0, 7.0], [9.2, 14.0]], str(r["ranges"]))
check("the second listen's reading (Claude off), his fix kept, the added words in, the missed word out",
      "was" in texts and "is" not in texts[:4] and "things" in texts and "ring" not in texts and "really" in texts
      and "okay" in texts and not any(abs(w[0] - 4.9) < 0.01 for w in r["words"]), str(texts))
check("Claude off says so", "Claude is off" in r["note"] and r["cost"] == 0 and r["asked"] >= 3, str(r)[:300])
check("words carry the transcript they were made against", r["trRev"] == "fixture")
really = next(w for w in r["words"] if w[2] == "really")
okay = next(w for w in r["words"] if w[2] == "okay")
check("a word only the second listen heard gets the split's group at its time", really[3] is None and really[4] in ("S1", "S4")
      and okay[3] is None and okay[4] == "S2", f"{really} {okay}")
cls = gc.gen_classes(aid, r)
k = {}
for i, w in enumerate(r["words"]):
    k.setdefault(w[2], cls[i])         # the first time a word is said ("so" comes again in Dana's part)
check("its voice: Jonathan's group is him, Dana's group is a woman", k["really"] == "me" and k["okay"] == "f" and k["so"] == "me", str(k))
r2 = dict(r, words=[list(w) for w in r["words"]])
next(w for w in r2["words"] if w[2] == "okay").append("me")
check("a fix saved on the short wins", gc.gen_classes(aid, r2)[[w[2] for w in r2["words"]].index("okay")] == "me")
r3 = dict(r, trRev="another transcript")
check("a word heard by both keeps its voice by time even if the transcript changed", gc.gen_classes(aid, r3)[texts.index("so")] == "me")
log = [json.loads(x) for x in (sc.CACHE / aid / "moments-log.jsonl").read_text().splitlines()]
check("the run is logged with what it cost", log[-1]["kind"] == "captions" and log[-1]["cost"] == 0 and log[-1]["words"] == len(texts))
check("the second listen's file is cleaned up", not list((sc.CACHE / aid).glob("listen-1*.json")))

# ---- the exporter recolors generated words from the voices (studio_captions.refresh_classes)
import studio_captions as caps  # noqa: E402
gi = texts.index("okay")
cap = {"gen": {aid: r}, "events": [{"s": 0, "e": 10, "words": [{"w": "OKAY", "s": 0, "e": 5, "id": None, "gi": gi, "asset": aid, "k": "u"}]}]}
n = caps.refresh_classes(cap)
check("a generated word's color is looked up from the short's words", n == 1 and cap["events"][0]["words"][0]["k"] == "f", str(cap["events"]))

# ---- the second listen on its own
import studio_listen as sl  # noqa: E402
check("ranges parse from s:e,s:e", sl.parse_ranges("12.5:40,61:75.5,9:3") == [[12.5, 40.0], [61.0, 75.5]])

# ---- numbers start their own word ("get15" was 59 words in the first two recordings)
import studio_transcribe as st  # noqa: E402
tok = lambda toks: [w[2] for w in st.tokens_to_words(toks, [0.1 * i for i in range(len(toks))], None, 0.0, 9.0)]  # noqa: E731
check("get 15 minutes", tok([" get", "1", "5", " minutes"]) == ["get", "15", "minutes"], str(tok([" get", "1", "5", " minutes"])))
check("a 20%", tok([" a", "2", "0", "%"]) == ["a", "20%"], str(tok([" a", "2", "0", "%"])))
check("December 1st,", tok([" December", "1", "st", ","]) == ["December", "1st,"], str(tok([" December", "1", "st", ","])))
check("C3 stays one word (a single letter)", tok([" C", "3", " Electrical"]) == ["C3", "Electrical"])
check("Control4 stays one word", tok([" Control", "4"]) == ["Control4"])
sp_ = gc.split_numbers([[1.0, 1.6, "get15", 7], [2.0, 2.3, "C3", 8], [3.0, 3.4, "a20%", 9]])
check("an old transcript's joined words split the same way, both halves keeping the id",
      [w[2] for w in sp_] == ["get", "15", "C3", "a", "20%"] and sp_[0][3] == sp_[1][3] == 7 and sp_[0][1] == sp_[1][0], str(sp_))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
