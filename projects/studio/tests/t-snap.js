import { test, wait } from "./harness.js";

test("snap", async (t, st) => {
  await t.fresh();
  st.S.snap = true;
  t.key("S"); await wait(10);
  t.eq("S turns snapping off", st.S.snap, false);
  t.key("S"); await wait(10);
  t.eq("S turns it back on", st.S.snap, true);
  t.ok("the snap button shows the state", document.getElementById("tl-snap").classList.contains("is-on"));
  // a text clip dragged near the playhead snaps its start to it
  st.actions.run("newText", { f: 250, track: "V2" });
  await wait(20);
  st.pb.seek(100);
  const txt = t.clip("V2")[0];
  const px = 4 / st.tl.view.ppf;          // 4 px off the playhead
  await t.tlDrag({ f: 260, track: "V2" }, { f: 260 - (250 - 100) + px, track: "V2" });
  t.eq("a clip start snaps to the playhead", t.clip("V2")[0].start, 100);
  // snaps to a marker
  st.actions.run("addMarker");
  st.pb.seek(0);
  st.history.commit("marker", (d) => { d.markers = [{ id: "m1", t: 140, color: "red", note: "" }]; });
  await wait(20);
  await t.tlDrag({ f: 110, track: "V2" }, { f: 150 + px, track: "V2" });
  t.eq("a clip start snaps to a marker", t.clip("V2")[0].start, 140);
  // snaps to a clip edge (the video's end at 180)
  await t.tlDrag({ f: 150, track: "V2" }, { f: 190 - px, track: "V2" });
  t.eq("a clip start snaps to another clip's end", t.clip("V2")[0].start, 180);
  // off: lands where dropped
  st.S.snap = false;
  await t.tlDrag({ f: 190, track: "V2" }, { f: 150 + 0.4, track: "V2" });
  t.eq("with snapping off it lands where dropped", t.clip("V2")[0].start, 140);
  t.eq("no snap line left behind", st.tl.view.ppf > 0, true);
});
