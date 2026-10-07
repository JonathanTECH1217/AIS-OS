import { test, wait, until } from "./harness.js";

test("playback", async (t, st) => {
  await t.fresh();
  // paused seeks show the exact source frame (barcode); the short starts 30 frames into src20
  for (const f of [0, 45, 100, 179]) {
    st.pb.seek(f);
    await t.settle();
    t.eq(`paused at ${f}, the monitor shows source frame ${30 + f}`, t.frameShown(), 30 + f);
  }
  // arrows step exactly one frame
  st.pb.seek(60); await t.settle();
  t.key("Right"); await t.settle();
  t.eq("Right shows the next frame", t.frameShown(), 91);
  t.key("Left"); t.key("Left"); await t.settle();
  t.eq("Left twice shows two frames back", t.frameShown(), 89);
  // a cut: the frame on each side of an edit comes from the right clip
  st.pb.seek(90); t.key("Ctrl+K"); await wait(20);
  st.history.commit("slip right piece", (d) => { const r = d.clips.filter((c) => c.track === "V1").sort((a, b) => a.start - b.start)[1]; r.in += 200; r.out += 200; });
  st.pb.seek(89); await t.settle();
  t.eq("last frame before the cut", t.frameShown(), 30 + 89);
  st.pb.seek(90); await t.settle();
  t.eq("first frame after the cut (slipped 200)", t.frameShown(), 30 + 90 + 200);
  // a gap is black
  st.history.commit("gap", (d) => { const r = d.clips.filter((c) => c.track === "V1").sort((a, b) => a.start - b.start)[1]; r.start += 30; });
  st.pb.seek(100); await t.settle();
  const px = t.pixel(540, 960);
  t.ok("a gap shows black", px[0] + px[1] + px[2] < 20, String(px));
  st.history.undo(); st.history.undo();
  await wait(30);
  // play for ~1 s: the clock moves about 30 frames
  st.pb.seek(0);
  st.audio.prefetch(st.S.doc, 0, 120);
  await wait(600);
  const t0 = performance.now();
  st.pb.play(1);
  await wait(1000);
  const f1 = st.S.playhead, el = (performance.now() - t0) / 1000;
  st.pb.pause();
  t.near("the clock runs at 30 frames a second", f1 / el, 30, 3.5);
  t.ok("playing shows moving pictures (frame advanced)", t.frameShown() > 45, String(t.frameShown()));
  // J / K / L
  st.pb.seek(100);
  t.key("L"); await wait(300);
  t.ok("L plays forward", st.S.playing && st.S.playhead > 100);
  t.key("L"); await wait(300);
  t.ok("L again plays faster (2x)", st.pb.rate() === 2);
  t.key("K"); await wait(50);
  t.ok("K stops", !st.S.playing);
  const h = st.S.playhead;
  t.key("J"); await wait(300);
  t.ok("J plays backwards", st.S.playing && st.S.playhead < h);
  t.key("K"); await wait(50);
  // Space toggles
  t.key("Space"); await wait(200);
  t.ok("Space plays", st.S.playing);
  t.key("Space"); await wait(50);
  t.ok("Space pauses", !st.S.playing);
  // playback stops at the end
  st.pb.seek(170); st.pb.play(1);
  await until(() => !st.S.playing, 3000);
  t.eq("playback stops at the end of the short", Math.round(st.S.playhead), 180);
});
