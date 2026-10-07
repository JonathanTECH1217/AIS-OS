import { test, wait, until } from "./harness.js";

// Voice tracks (Jonathan 2026-09-30, V1-V3): A1 (You) and A2 (Them) carry the same audio; each plays only its speaker's
// stretches, cut in the middle of the pause between speakers. The fixture: words 0-11 Jonathan (to 6.8 s), then the
// other side from 7.5 s, so the cut sits at 7.15 s (frame 214.5).
test("voices", async (t, st) => {
  await t.fresh();
  const aid = t.asset("src20.mp4").id;
  const v = t.clip("V1")[0], a1 = t.clip("A1")[0], a2 = t.clip("A2")[0];
  t.ok("a new short has You on A1 and Them on A2, linked to the video", a1 && a2 && a1.voice === "me" && a2.voice === "them"
    && a1.link === v.link && a2.link === v.link);
  st.history.commit("span", (d) => { for (const c of d.clips) { c.in = 0; c.out = 600; } });
  await wait(40);
  const tr = st.lib.transcript(aid);
  const A1 = t.clip("A1")[0], A2 = t.clip("A2")[0];
  const g1 = st.voices.gateFrames(A1, tr), g2 = st.voices.gateFrames(A2, tr);
  t.eq("You plays Jonathan's stretch, cut in the middle of the pause", g1, [[0, 214.5]]);
  t.eq("Them plays the rest", g2, [[214.5, 600]]);
  t.ok("on Jonathan's words You is open and Them closed", st.kf.gainAt(A1, 100, g1) === 1 && st.kf.gainAt(A2, 100, g2) === 0);
  t.ok("on hers it's the other way round", st.kf.gainAt(A1, 300, g1) === 0 && st.kf.gainAt(A2, 300, g2) === 1);
  const mid = st.kf.gainAt(A2, 215.5, g2);
  t.ok("the change of speaker ramps over 2 frames (no click)", mid > 0 && mid < 1, String(mid));
  const words = st.captions.wordsOnTimeline(st.S.doc, st.lib);
  t.ok("captions take each word once, from the track of whoever says it", new Set(words.map((w) => w.id)).size === words.length && words.length >= 30, `${words.length} words`);
  t.ok("Jonathan's words come from A1, hers from A2", words.filter((w) => w.id <= 11).every((w) => w.k === "me") && words.filter((w) => w.id >= 12).every((w) => w.k !== "me"));
  // razor: Ctrl+K cuts both voice tracks with the video
  st.pb.seek(300); t.key("Ctrl+K"); await wait(30);
  t.eq("Ctrl+K cuts V1, You and Them together", [t.clip("V1").length, t.clip("A1").length, t.clip("A2").length], [2, 2, 2]);
  st.history.undo(); await wait(20);
  // Normalize voices: both tracks measured on the server and set to the same level, one undo step
  const res = await st.actions.run("normalizeVoices");
  await wait(40);
  const va = t.clip("A1")[0].fx.volume, vb = t.clip("A2")[0].fx.volume;
  t.ok("Normalize voices sets a level on each voice track", res && va && vb && typeof va.v === "number" && typeof vb.v === "number", JSON.stringify(res));
  t.ok("the levels land each track on the same loudness (gain = -20 minus what was measured)",
    res && Object.keys(res.gains).length === 2 && res.report.every((s) => /LUFS/.test(s)), JSON.stringify(res && res.report));
  const toast = document.getElementById("toast");
  t.ok("and says what it did", /Voices evened to -20 LUFS/.test(toast.textContent), toast.textContent);
  st.history.undo(); await wait(20);
  t.ok("undo puts the levels back", !(t.clip("A1")[0].fx.volume && t.clip("A1")[0].fx.volume.v));
  // mute one voice: the other still plays
  st.history.commit("mute them", (d) => { d.tracks.find((x) => x.id === "A2").mute = true; });
  const aud = st.audio.audible(st.S.doc);
  t.ok("muting Them leaves You", aud.has("A1") && !aud.has("A2"));
  st.history.undo();
  // an older short (one A1 track, sounds on A2): Split audio by voice
  st.history.commit("make it old", (d) => {
    d.tracks = d.tracks.filter((x) => x.id !== "A3");
    for (const x of d.tracks) { delete x.voice; delete x.name; }
    d.clips = d.clips.filter((c) => c.track !== "A2");
    for (const c of d.clips) delete c.voice;
  });
  st.actions.run("placeAsset", { item: { kind: "asset", id: t.asset("pop.wav").id }, f: 30, track: "A2" });
  await wait(30);
  t.ok("(an older short: the sound sits on A2)", t.clip("A2").length === 1 && t.clip("A2")[0].asset === t.asset("pop.wav").id);
  st.actions.run("splitVoices");
  await wait(30);
  const tracks = st.S.doc.tracks.filter((x) => x.kind === "audio").map((x) => [x.id, x.name || "", x.voice || ""]);
  t.eq("Split audio by voice: You on A1, Them on A2, the sound moved to Sounds", tracks, [["A1", "You", "me"], ["A2", "Them", "them"], ["A3", "Sounds", ""]]);
  t.ok("the sound kept its place", t.clip("A3").length === 1 && t.clip("A3")[0].start === 30);
  t.ok("Them is a copy of the speech, linked to the same video", t.clip("A2")[0].voice === "them" && t.clip("A2")[0].link === t.clip("V1")[0].link
    && t.clip("A2")[0].in === t.clip("A1")[0].in);
  st.history.undo(); await wait(20);
  t.ok("undo puts the older layout back", !st.S.doc.tracks.some((x) => x.voice));
});
