import { test, wait } from "./harness.js";

test("join", async (t, st) => {
  await t.fresh();
  const strip = (d) => JSON.stringify(d.clips.map((c) => [c.track, c.start, c.in, c.out, c.type]).sort());
  const orig = strip(st.S.doc);
  st.pb.seek(80); t.key("Ctrl+K"); await wait(20);
  t.eq("split made two pieces", t.clip("V1").length, 2);
  t.ok("the cut shows as a through edit on V1, You and Them", st.ops.throughEditsAt(st.S.doc).length === 3);
  // join from the right-click menu on the cut (G30)
  const items = await t.tlContext(80, "V1");
  t.ok("right-click on the cut offers Join through edit", items.includes("Join through edit"));
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Join through edit")).click();
  await wait(20);
  t.eq("join heals the cut on video and audio", strip(st.S.doc), orig);
  // keyframes on both halves survive the join
  st.pb.seek(80); t.key("Ctrl+K"); await wait(20);
  const [l, r] = t.clip("V1");
  st.actions.kfCommit ? null : null;
  st.history.commit("k", (d) => { st.kf.addKey(d.clips.find((c) => c.id === l.id), "scale", l.in + 10, 120); st.kf.addKey(d.clips.find((c) => c.id === r.id), "scale", r.in + 10, 90); });
  st.actions.run("join", l.id);
  await wait(20);
  const joined = t.clip("V1")[0];
  t.eq("joined clip keeps both keyframes", (joined.fx.scale.k || []).map((k) => k.v), [120, 90]);
  // not a through edit: two different clips side by side can't be joined
  st.actions.run("newText", { f: st.doc.clipEnd(joined), track: "V1" });
  await wait(20);
  const before = strip(st.S.doc);
  st.actions.run("join", joined.id);
  await wait(30);
  t.eq("clips from different sources are not joined", strip(st.S.doc), before);
  const items2 = await t.tlContext(st.doc.clipEnd(joined), "V1");
  const row = [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Join through edit"));
  t.ok("Join is greyed out on that cut", row && row.classList.contains("is-disabled"), items2.join("|"));
  t.closeMenus();
});
