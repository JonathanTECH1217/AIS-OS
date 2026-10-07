import { test, wait } from "./harness.js";

test("razor", async (t, st) => {
  await t.fresh();
  st.S.snap = false;
  t.key("C");
  await t.tlClick(60, "V1");
  t.eq("razor splits the video in two", t.clip("V1").length, 2);
  t.eq("and its linked audio (G31)", t.clip("A1").length, 2);
  const [l, r] = t.clip("V1");
  t.eq("cut lands on frame 60", [l.start, l.out - l.in, r.start], [0, 60, 60]);
  t.eq("right piece continues the source", r.in, l.out);
  t.ok("the two right pieces are linked to each other", t.clip("A1")[1].link === r.link && r.link !== l.link);
  // Shift+click splits every track
  st.actions.run("newText", { f: 0, track: "V2" });
  await wait(20);
  await t.tlClick(40, "V1", { shift: true });
  t.eq("shift-razor splits all tracks", [t.clip("V1").length, t.clip("A1").length, t.clip("V2").length], [3, 3, 2]);
  // Ctrl+K at the playhead
  t.key("V");
  st.selectOnly([]);
  st.pb.seek(120);
  t.key("Ctrl+K");
  await wait(20);
  t.eq("Ctrl+K adds an edit at the playhead on V1 and A1", [t.clip("V1").length, t.clip("A1").length], [4, 4]);
  // Ctrl+Shift+K on all tracks
  st.pb.seek(20);
  t.key("Ctrl+Shift+K");
  await wait(20);
  t.eq("Ctrl+Shift+K cuts every track", [t.clip("V1").length, t.clip("V2").length], [5, 3]);
  // snapping: a click near the playhead lands on it
  st.S.snap = true;
  st.pb.seek(150);
  t.key("C");
  await t.tlClick(150.6, "V1");
  t.ok("razor snaps to the playhead", t.clip("V1").some((c) => c.start === 150), JSON.stringify(t.clip("V1").map((c) => c.start)));
  // snapping to word edges (the fixture has a word starting 0.8 s into the source; the clip starts at 1.0 s)
  const words = st.captions.wordsOnTimeline(st.S.doc, st.lib).map((w) => w.s);
  const target = words.find((w) => w > 160 && w < 175);
  if (target) {
    await t.tlClick(target + 0.5, "V1");
    t.ok("razor snaps to a word edge", t.clip("V1").some((c) => c.start === target), `${target}`);
  }
  t.key("V");
});
