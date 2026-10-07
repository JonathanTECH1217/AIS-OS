import { test, wait } from "./harness.js";

test("monitor", async (t, st) => {
  await t.fresh();
  const cv = document.querySelector(".mon-program");
  for (const [q, w] of [["full", 1080], ["half", 540], ["quarter", 270]]) {
    st.actions.run("quality." + q); await wait(40);
    t.eq(`quality ${q} draws at ${w} px wide (G25)`, cv.width, w);
  }
  st.actions.run("quality.half");
  // 9:16 holds when the panel resizes
  const fr = document.querySelector(".mon-frame").getBoundingClientRect();
  t.near("monitor frame is 9:16", fr.width / fr.height, 9 / 16, 0.01);
  st.layout.reset();
  document.getElementById("app").style.setProperty("--side", "520px");
  window.dispatchEvent(new Event("resize"));
  await wait(120);
  const fr2 = document.querySelector(".mon-frame").getBoundingClientRect();
  t.near("still 9:16 after a resize", fr2.width / fr2.height, 9 / 16, 0.01);
  st.layout.reset();
  // safe zones: drawn on the guides canvas, never on the picture (G40)
  st.pb.seek(30); await t.settle();
  const before = t.pixel(540, 100);
  st.actions.run("safe"); await wait(60);
  const gd = document.querySelector(".mon-guides");
  const gp = gd.getContext("2d").getImageData(Math.round(540 * gd.width / 1080), Math.round(100 * gd.width / 1080), 1, 1).data;
  t.ok("safe zones show on the guide layer", gp[3] > 0, String([...gp]));
  t.eq("the picture underneath is unchanged", t.pixel(540, 100), before);
  st.actions.run("safe");
  // drag an overlay on the picture to move it
  st.actions.run("newText", { f: 30, track: "V2" }); await wait(40);
  const txt = t.clip("V2")[0];
  const r = gd.getBoundingClientRect();
  const k = r.width / 1080;
  const a = { x: r.left + 540 * k, y: r.top + 420 * k };
  gd.dispatchEvent(t.pe("pointerdown", a));
  gd.dispatchEvent(t.pe("pointermove", { x: a.x + 100 * k, y: a.y + 200 * k }));
  gd.dispatchEvent(t.pe("pointerup", { x: a.x + 100 * k, y: a.y + 200 * k }));
  await wait(40);
  const moved = st.S.doc.clips.find((c) => c.id === txt.id);
  t.near("dragging an overlay on the monitor moves it (x)", moved.fx.posX.v, 640, 3);
  t.near("and y", moved.fx.posY.v, 620, 3);
  // the Type tool on the monitor adds text where clicked
  t.key("T");
  const b = { x: r.left + 300 * k, y: r.top + 1500 * k };
  gd.dispatchEvent(t.pe("pointerdown", b)); gd.dispatchEvent(t.pe("pointerup", b));
  await wait(40);
  t.key("V");
  const added = st.S.doc.clips.filter((c) => c.type === "text").find((c) => c.id !== txt.id);
  t.ok("Type tool click on the monitor adds a text clip there", added && Math.abs(added.fx.posX.v - 300) < 4 && Math.abs(added.fx.posY.v - 1500) < 4, JSON.stringify(added && added.fx));
  // transport buttons
  st.pb.seek(50);
  document.querySelector(".mon-transport .icon-btn[title^='Forward one frame']").click();
  t.eq("monitor step button moves one frame", Math.round(st.S.playhead), 51);
  document.querySelector(".mon-transport .icon-btn[title^='Go to end']").click();
  t.eq("go-to-end button", Math.round(st.S.playhead), 180);
  await wait(80);
  t.eq("timecode shows the playhead", document.querySelector(".mon-tc").textContent, "0:06:00");
  // no black flashes while a video jumps or loads (2026-09-30, "on playback, sometimes the screen goes black")
  const pool = st.mon.pool();
  // 1. a video that is seeking shows the copy of its last picture
  st.pb.seek(60); await t.settle();
  const at60 = t.frameShown();
  const live = pool.live;
  pool.live = () => false;
  st.pb.seek(90); st.mon.draw(); await wait(30);
  t.eq("while its video seeks, a clip shows its last picture", t.frameShown(), at60);
  t.eq("the timecode follows the playhead", document.querySelector(".mon-tc").textContent, "0:03:00");
  pool.live = live;
  await t.settle();
  t.eq("then the new picture", t.frameShown(), at60 + 30);
  // 2. a clip with nothing to show at all yet: the whole last frame holds, for HOLD_MS at most
  st.pb.seek(60); await t.settle();
  const shown = t.pixel(270, 960);
  const picture = pool.picture;
  pool.picture = () => null;
  st.pb.seek(90); st.mon.draw(); await wait(30);
  const held = t.pixel(270, 960);
  t.ok("a clip with no picture yet: the last frame holds", held.join() === shown.join() && held[0] + held[1] + held[2] > 60, `${held} vs ${shown}`);
  t.eq("the timecode still follows the playhead", document.querySelector(".mon-tc").textContent, "0:03:00");
  await wait(1700);
  st.mon.draw(); await wait(30);
  const gone = t.pixel(270, 960);
  t.ok("a video that never comes stops being waited for (then the frame shows what it has)", gone.join() !== shown.join(), `${gone}`);
  pool.picture = picture;
  await t.settle();
  // 3. the canvas clears when it changes size: a quality change carries the picture over
  const small = t.pixel(270, 960);
  st.actions.run("quality.full"); await null; await null;
  const carried = t.pixel(270, 960);
  t.ok("a quality change doesn't flash black", cv.width === 1080 && carried.slice(0, 3).every((c, i) => Math.abs(c - small[i]) < 40) && carried[0] + carried[1] + carried[2] > 60, `${cv.width} ${carried} vs ${small}`);
  st.actions.run("quality.half"); await t.settle();
  // 4. the video pool while playing (a stand-in element, so the timing is exact)
  const Pool = pool.constructor;
  const fake = (o) => Object.assign({ readyState: 4, seeking: false, paused: false, currentTime: 0, playbackRate: 1, videoWidth: 0, videoHeight: 0, sets: [],
    play() { this.paused = false; return Promise.resolve(); }, pause() { this.paused = true; }, addEventListener() {} }, o);
  const item = (v, extra = {}) => Object.assign({ v, key: "c", url: "u", used: 0, want: null, seeking: false, seekAt: 0, target: null, snap: null, snapKey: null, picKey: "c" }, extra);
  const track = (v) => { let ct = v.currentTime; Object.defineProperty(v, "currentTime", { get: () => ct, set: (x) => { ct = x; v.sets.push(x); } }); return v; };
  const p = new Pool(document.createElement("div"), () => {});
  let v = track(fake({ currentTime: 10 })); p.items = [item(v)];
  p.seekSecs.set("u", 0.8);
  p.sync("c", "u", 12, true);
  t.ok("far behind while playing: one seek, aimed ahead by what a seek takes in that file", v.sets.length === 1 && Math.abs(v.sets[0] - 12.8) < 1e-6, JSON.stringify(v.sets));
  v.seeking = true;
  p.sync("c", "u", 12.1, true); p.sync("c", "u", 12.2, true); p.sync("c", "u", 12.3, true);
  t.eq("a seek in flight is left to finish (a slow one would never land)", v.sets.length, 1);
  v.seeking = false; v.paused = false; p.items[0].want = 11; p.items[0].seeking = true;
  p.seeked(p.items[0]);
  t.eq("a seek that lands while playing isn't pulled back to an old paused spot", v.sets.length, 1);
  v = track(fake({ currentTime: 20 })); p.items = [item(v)];
  p.sync("c", "u", 20.2, true);
  t.ok("a little behind: it speeds up instead of seeking", v.sets.length === 0 && v.playbackRate > 1.2, `${v.playbackRate} ${v.sets}`);
  p.sync("c", "u", 19.7, true);
  t.ok("a little ahead: it waits for the clock instead of seeking", v.sets.length === 0 && v.paused, `${v.paused} ${v.sets}`);
  v = track(fake({ currentTime: 30, paused: true })); p.items = [item(v, { want: 31, seeking: true })];
  p.seeked(p.items[0]);
  t.eq("paused, a seek that lands chases the newest spot asked for", v.sets[0], 31);
});
