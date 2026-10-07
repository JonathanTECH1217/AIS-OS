import { test, wait } from "./harness.js";

test("rollslipslide", async (t, st) => {
  await t.fresh();
  st.S.snap = false;
  st.pb.seek(60); t.key("Ctrl+K"); st.pb.seek(120); t.key("Ctrl+K"); await wait(20);
  const total = () => st.doc.seqEnd(st.S.doc);
  const len0 = total();
  // Rolling edit (N): drag the cut between piece 1 and 2
  t.key("N");
  await t.tlDrag({ f: 60, track: "V1" }, { f: 75, track: "V1" });
  let v = t.clip("V1");
  t.eq("rolling moves the cut", [v[0].out - v[0].in, v[1].start], [75, 75]);
  t.eq("rolling keeps the total length", total(), len0);
  t.eq("the source frame at the cut is continuous", v[1].in, v[0].out);
  // Slip (Y): the middle piece shows later source frames, same place and length
  t.key("Y");
  const mid0 = { ...t.clip("V1")[1] };
  await t.tlDrag({ f: 100, track: "V1" }, { f: 90, track: "V1" });
  v = t.clip("V1");
  t.eq("slip keeps position and length", [v[1].start, v[1].out - v[1].in], [mid0.start, mid0.out - mid0.in]);
  t.ok("slip changes which source frames play", v[1].in !== mid0.in, `${mid0.in} -> ${v[1].in}`);
  t.eq("slip keeps the total length", total(), len0);
  // Slide (U): the middle piece moves; neighbours give and take
  t.key("U");
  const b0 = t.clip("V1").map((c) => ({ ...c }));
  await t.tlDrag({ f: 100, track: "V1" }, { f: 110, track: "V1" });
  v = t.clip("V1");
  t.eq("slide moves the middle piece", v[1].start, b0[1].start + 10);
  t.eq("the left neighbour grows", v[0].out - v[0].in, b0[0].out - b0[0].in + 10);
  t.eq("the right neighbour shrinks from its head", [v[2].start, v[2].in], [b0[2].start + 10, b0[2].in + 10]);
  t.eq("slide keeps the total length", total(), len0);
  t.key("V");
});
