import { test, wait } from "./harness.js";

test("transitions", async (t, st) => {
  await t.fresh();
  st.pb.seek(90); t.key("Ctrl+K"); await wait(20);
  t.key("Ctrl+D"); await wait(20);
  const tr = st.S.doc.transitions[0];
  t.ok("Ctrl+D adds a cross dissolve at the nearest cut (G33)", tr && tr.kind === "dissolve" && tr.track === "V1", JSON.stringify(st.S.doc.transitions));
  t.ok("about half a second long", tr.dur >= 14 && tr.dur <= 15, String(tr.dur));
  const w = st.ops.transitionWindow(st.S.doc, tr);
  t.eq("centered on the cut", [w.cut, w.s, w.e], [90, 90 - tr.dur / 2, 90 + tr.dur / 2]);
  const mid = st.comp.layersAt(st.S.doc, 90).filter((l) => l.clip.track === "V1");
  t.eq("mid-dissolve: both clips drawn", mid.length, 2);
  t.near("each at half strength", mid[0].alpha, 0.5, 0.01);
  const early = st.comp.layersAt(st.S.doc, Math.ceil(w.s) + 1).filter((l) => l.clip.track === "V1");
  t.ok("early in the dissolve the outgoing clip dominates", early.length === 2 && early[0].alpha > 0.8);
  // right-click the transition: switch to dip to black
  const items = await t.tlContext(90, "V1", 16);
  t.ok("right-click a transition offers Dip to black", items.includes("Dip to black"), items.join("|"));
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Dip to black")).click();
  await wait(30);
  t.eq("switched to a dip", st.S.doc.transitions[0].kind, "dip");
  t.eq("mid-dip draws nothing on V1 (black)", st.comp.layersAt(st.S.doc, 90).filter((l) => l.clip.track === "V1" && l.alpha > 0.01).length, 0);
  st.pb.seek(90);
  await t.settle();
  const px = t.pixel(540, 960);
  t.ok("the monitor is black at the middle of the dip", px[0] + px[1] + px[2] < 30, String(px));
  // duration in Effect Controls
  st.S.selTransition = st.S.doc.transitions[0].id; st.emit("sel");
  await wait(30);
  t.ok("a selected transition shows its settings", /Duration/.test(document.getElementById("fx").textContent));
  // a dip at a clip's end with nothing after (fade to black)
  st.history.commit("rm", (d) => { d.transitions = []; });
  const end = st.doc.seqEnd(st.S.doc);
  st.actions.run("dipAt", { track: "V1", f: end });
  await wait(20);
  t.ok("dip to black at the very end works with one clip", st.S.doc.transitions.length === 1 && st.S.doc.transitions[0].a && !st.S.doc.transitions[0].b);
  // not enough footage: the fixture source starts at 0, a clip at in=0 can't dissolve from before it
  st.history.commit("rm", (d) => { d.transitions = []; });
  const del = st.history.commit("delete", (d) => { d.clips = d.clips.filter((c) => c.track !== "V1" || c.start !== 90); });
  t.ok("setup", del.ok !== false);
});
