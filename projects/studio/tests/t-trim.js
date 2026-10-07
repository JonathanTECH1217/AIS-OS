import { test, wait } from "./harness.js";

test("trim", async (t, st) => {
  await t.fresh();
  st.S.snap = false;
  let [v] = t.clip("V1");
  // the first clip's start pulled back past 0 (2026-09-30): it grows at the front with earlier source (the dial tone)
  // and stays at 0; its audio comes along
  await t.tlDrag({ f: 0.4, track: "V1" }, { f: -20, track: "V1" });
  [v] = t.clip("V1");
  t.eq("dragging the first clip's start back reaches earlier into the recording", [v.start, v.in, v.out], [0, 10, 210]);
  t.ok("You and Them reach back with it", t.clip("A1")[0].in === 10 && t.clip("A2")[0].in === 10 && t.clip("A2")[0].start === 0);
  st.history.undo(); await wait(20);
  [v] = t.clip("V1");
  await t.tlDrag({ f: 179.6, track: "V1" }, { f: 150, track: "V1" });
  [v] = t.clip("V1");
  t.eq("dragging the out edge shortens the clip", v.out - v.in, 150);
  t.eq("its linked audio trims with it", t.clip("A1")[0].out - t.clip("A1")[0].in, 150);
  await t.tlDrag({ f: 0.4, track: "V1" }, { f: 30, track: "V1" });
  [v] = t.clip("V1");
  t.eq("dragging the in edge trims the head", [v.start, v.in], [30, 60]);
  // media limits: the fixture is 20 s (600 frames); the out edge can't pass it
  st.tl.setPpf(1.5);
  await wait(20);
  await t.tlDrag({ f: 149.5, track: "V1" }, { f: 900, track: "V1" });
  [v] = t.clip("V1");
  t.ok("the out edge stops at the end of the source", v.out <= 600 && v.out >= 590, String(v.out));
  await t.tlDrag({ f: 30.3, track: "V1" }, { f: -200, track: "V1" });
  [v] = t.clip("V1");
  t.ok("the in edge stops at the start of the source", v.in === 0 || v.start === 0, JSON.stringify([v.start, v.in]));
  // trims stop at a neighbour
  st.history.undo(); st.history.undo(); st.history.undo(); st.history.undo();
  await wait(20);
  st.tl.zoomFit();
  st.actions.run("newText", { f: 200, track: "V1" });
  await wait(20);
  [v] = t.clip("V1");
  await t.tlDrag({ f: 179.6, track: "V1" }, { f: 260, track: "V1" });
  [v] = t.clip("V1");
  t.ok("a trim stops at the next clip", st.doc.clipEnd(v) <= 200, String(st.doc.clipEnd(v)));
  st.history.undo(); st.history.undo();
  await wait(20);
  // Q and W: ripple trim to the playhead
  st.pb.seek(40);
  t.key("Q");
  await wait(20);
  [v] = t.clip("V1");
  t.eq("Q ripple-trims the head to the playhead", [v.start, v.out - v.in], [0, 140]);
  st.pb.seek(100);
  t.key("W");
  await wait(20);
  [v] = t.clip("V1");
  t.eq("W ripple-trims the tail to the playhead", v.out - v.in, 100);
});
