import { test, wait } from "./harness.js";

test("ripple", async (t, st) => {
  await t.fresh();
  st.S.snap = false;
  // two pieces: cut at 60, then ripple-trim the first piece's tail with the B tool
  st.pb.seek(60); t.key("Ctrl+K"); await wait(20);
  t.key("B");
  await t.tlDrag({ f: 59.6, track: "V1" }, { f: 40, track: "V1" });
  let v = t.clip("V1");
  t.eq("B tool: shortening the first piece", v[0].out - v[0].in, 40);
  t.eq("pulls the next piece left (no gap)", v[1].start, 40);
  t.eq("on the audio too", t.clip("A1")[1].start, 40);
  t.key("V");
  // Shift+Delete: ripple delete closes the gap
  st.selectOnly(st.doc.withLinked(st.S.doc, [v[0].id]));
  t.key("Shift+Delete");
  await wait(20);
  v = t.clip("V1");
  t.eq("ripple delete removes the clip and closes the gap", [v.length, v[0].start], [1, 0]);
  // lift leaves a gap, then ripple the gap out from the right-click menu
  st.pb.seek(50); t.key("Ctrl+K"); await wait(20);
  v = t.clip("V1");
  st.selectOnly(st.doc.withLinked(st.S.doc, [v[0].id]));
  t.key("Delete"); await wait(20);
  t.eq("Delete (lift) leaves a gap", t.clip("V1")[0].start, 50);
  const items = await t.tlContext(20, "V1");
  t.ok("right-click on a gap offers Ripple delete gap", items.includes("Ripple delete gap"));
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Ripple delete gap")).click();
  await wait(20);
  t.eq("ripple delete gap closes it", t.clip("V1")[0].start, 0);
  // blocked: a clip on another track straddling the gap
  st.pb.seek(50); t.key("Ctrl+K"); await wait(20);
  v = t.clip("V1");
  st.actions.run("placeAsset", { item: { kind: "asset", id: t.asset("pop.wav").id }, f: 20, track: "A3" });
  await wait(20);
  st.selectOnly(st.doc.withLinked(st.S.doc, [v[0].id]));
  const before = JSON.stringify(st.S.doc.clips);
  t.key("Shift+Delete");
  await wait(40);
  t.eq("ripple delete is blocked by a clip in the way on another track", JSON.stringify(st.S.doc.clips), before);
  const toast = document.getElementById("toast");
  t.ok("and says which track", !toast.hidden && /A3 has a clip in the way/.test(toast.textContent), toast.textContent);
});
