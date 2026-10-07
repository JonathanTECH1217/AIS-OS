import { test, wait } from "./harness.js";

test("undo", async (t, st) => {
  await t.fresh();
  st.S.snap = false;
  const snap = () => JSON.stringify(st.S.doc.clips.map((c) => [c.id, c.track, c.start, c.in, c.out]).sort()) + JSON.stringify(st.S.doc.markers) + JSON.stringify(st.S.doc.transitions);
  const states = [snap()];
  const steps = [
    ["split", () => { st.pb.seek(60); t.key("Ctrl+K"); }],
    ["marker", () => t.key("M")],
    ["dissolve", () => t.key("Ctrl+D")],
    ["text", () => st.actions.run("newText", { f: 20, track: "V2" })],
    ["trim", () => st.history.commit("Trim", (d) => st.ops.trim(d, { lib: st.lib }, [d.clips.find((c) => c.type === "text").id], "out", -30))],
    ["delete", () => { st.selectOnly([st.S.doc.clips.find((c) => c.type === "text").id]); t.key("Delete"); }],
    ["join", () => st.actions.run("join", t.clip("V1")[0].id)],
  ];
  for (const [name, fn] of steps) {
    fn();
    await wait(30);
    states.push(snap());
    t.ok(`${name} changed the short`, states[states.length - 1] !== states[states.length - 2]);
  }
  // undo walks back through every state, redo walks forward
  for (let i = states.length - 2; i >= 0; i -= 1) {
    t.key("Ctrl+Z"); await wait(15);
    t.eq(`undo back to step ${i}`, snap(), states[i]);
  }
  for (let i = 1; i < states.length; i += 1) {
    t.key("Ctrl+Shift+Z"); await wait(15);
    t.eq(`redo to step ${i}`, snap(), states[i]);
  }
  t.key("Ctrl+Z"); await wait(15);
  t.key("Ctrl+Y"); await wait(15);
  t.eq("Ctrl+Y redoes too", snap(), states[states.length - 1]);
  // the Edit menu names the step
  t.ok("the undo label names the last edit", /Join Through Edit/.test(st.history.undoLabel()), st.history.undoLabel());
  // quick edits of the same kind merge into one step
  const d0 = st.history.depth().undo;
  for (let i = 0; i < 5; i += 1) st.history.commit("Nudge", (d) => { d.markers.push({ id: "n" + i, t: i, color: "blue", note: "" }); }, { key: "nudge" });
  t.eq("five quick nudges are one undo step", st.history.depth().undo, d0 + 1);
  // a drag is one step
  const d1 = st.history.depth().undo;
  await t.tlDrag({ f: 100, track: "V1" }, { f: 130, track: "V1" });
  t.eq("a whole drag is one undo step", st.history.depth().undo, d1 + 1);
  // the cap: 100 steps
  for (let i = 0; i < 130; i += 1) st.history.commit("m" + i, (d) => { d.markers = [{ id: "c", t: i, color: "green", note: "" }]; });
  t.eq("undo keeps the last 100 steps", st.history.depth().undo, 100);
  // Escape cancels a drag
  const before = snap();
  const wrap = document.querySelector(".tl-wrap");
  const p = t.tlPoint(100, "V1");
  wrap.dispatchEvent(t.pe("pointerdown", p));
  wrap.dispatchEvent(t.pe("pointermove", { x: p.x + 80, y: p.y }));
  await wait(10);
  document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  wrap.dispatchEvent(t.pe("pointerup", { x: p.x + 80, y: p.y }));
  await wait(20);
  t.eq("Esc during a drag puts everything back", snap(), before);
});
