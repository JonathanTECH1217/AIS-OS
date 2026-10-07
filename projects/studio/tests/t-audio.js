import { test, wait, until } from "./harness.js";

test("audio", async (t, st) => {
  await t.fresh();
  let [a] = t.clip("A1");
  // fade handles: drag the fade-in handle 20 frames in
  const wrap = document.querySelector(".tl-wrap");
  const r = wrap.getBoundingClientRect();
  const row = st.tl.rows().find((x) => x.id === "A1");
  const hy = r.top + row.y + 20;
  const hx = r.left + st.tl.xOf(0) + 1;
  wrap.dispatchEvent(t.pe("pointerdown", { x: hx, y: hy }));
  for (let i = 1; i <= 5; i += 1) wrap.dispatchEvent(t.pe("pointermove", { x: hx + (20 * st.tl.view.ppf * i) / 5, y: hy }));
  wrap.dispatchEvent(t.pe("pointerup", { x: hx + 20 * st.tl.view.ppf, y: hy }));
  await wait(30);
  [a] = t.clip("A1");
  t.near("dragging the fade handle sets a fade-in (G33)", a.fadeIn, 20, 1);
  // gain: halfway through the fade the gain is half
  t.near("half way into the fade the gain is 0.5", st.kf.gainAt(a, 10), 0.5, 0.06);
  // volume keyframes in dB
  st.history.commit("vol", (d) => { const c = d.clips.find((x) => x.id === a.id); st.kf.addKey(c, "volume", c.in + 60, 0); st.kf.addKey(c, "volume", c.in + 120, -20); });
  [a] = t.clip("A1");
  t.near("-20 dB is a gain of 0.1", st.kf.gainAt(a, 150), 0.1, 1e-6);
  t.near("halfway between 0 and -20 dB (linear in dB)", st.kf.gainAt(a, 90), Math.pow(10, -10 / 20), 1e-6);
  // mute and solo decide what plays
  st.actions.run("placeAsset", { item: { kind: "asset", id: t.asset("pop.wav").id }, f: 30, track: "A3" });
  await wait(20);
  let aud = st.audio.audible(st.S.doc);
  t.ok("both audio tracks audible by default", aud.has("A1") && aud.has("A2"));
  st.history.commit("solo", (d) => { d.tracks.find((x) => x.id === "A2").solo = true; });
  aud = st.audio.audible(st.S.doc);
  t.ok("solo A2 silences A1", !aud.has("A1") && aud.has("A2"));
  st.history.commit("unsolo", (d) => { d.tracks.find((x) => x.id === "A2").solo = false; d.tracks.find((x) => x.id === "A1").mute = true; });
  aud = st.audio.audible(st.S.doc);
  t.ok("mute A1 silences it", !aud.has("A1") && aud.has("A2"));
  st.history.commit("unmute", (d) => { d.tracks.find((x) => x.id === "A1").mute = false; });
  // play one second: the scheduler starts both clips at the right source offsets
  st.pb.seek(0);
  st.audio.prefetch(st.S.doc, 0, 90);
  await wait(900);
  st.pb.play(1);
  await wait(1300);
  st.pb.pause();
  const log = st.audio.log;
  const a1 = log.find((x) => x.clip === a.id);
  t.ok("A1 was scheduled", !!a1, JSON.stringify(log.slice(0, 3)));
  if (a1) t.near("A1 starts 1.0 s into its source (moment m01 starts at 1 s)", a1.offset + a1.block * 30, 1.0 + (a1.p0 / 30), 0.05);
  const pop = t.clip("A3")[0];
  const sfx = pop && log.find((x) => x.clip === pop.id);
  t.ok("the sound effect on A3 (Sounds) was scheduled", !!sfx);
  if (sfx) t.near("at its place on the timeline (frame 30)", sfx.p0, 30, 1.5);
  t.ok("the audio clock ran", st.audio.ctx && st.audio.ctx.state === "running");
});
