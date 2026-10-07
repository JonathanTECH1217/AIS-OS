import { test, wait } from "./harness.js";

// Dragging the volume line on the timeline (2026-10-02, "drag the volume up and down on the timeline for select media"):
// with the Selection tool, a selected audio clip's line drags up (louder) or down at 0.2 dB a pixel (Ctrl: 0.05), with
// a catch at 0 dB; every selected audio clip moves by the same amount; one undo step; double-click goes back to 0 dB.
test("volume", async (t, st) => {
  await t.fresh();                                    // m01: V1, A1 (You), A2 (Them), all linked
  st.actions.run("tool.select");
  const wrap = document.querySelector(".tl-wrap");
  const a1 = () => t.clip("A1")[0], a2 = () => t.clip("A2")[0], v1 = () => t.clip("V1")[0];
  const vol = (c) => (c.fx && c.fx.volume ? c.fx.volume.v : 0);
  const at = (clip, f) => { const r = wrap.getBoundingClientRect(); return { x: r.left + st.tl.xOf(f), y: r.top + st.tl.volY(clip, f) }; };
  const dragBy = async (p, dy, opts = {}) => {
    wrap.dispatchEvent(t.pe("pointerdown", p, opts));
    const n = 8;
    for (let i = 1; i <= n; i += 1) { wrap.dispatchEvent(t.pe("pointermove", { x: p.x, y: p.y - (dy * i) / n }, opts)); await wait(8); }
    wrap.dispatchEvent(t.pe("pointerup", { x: p.x, y: p.y - dy }, opts));
    await wait(40);
  };
  // only selected clips offer the line: an unselected clip's line spot just selects and moves as before
  st.selectOnly([]); st.emit("sel"); await wait(30);
  const r0 = wrap.getBoundingClientRect();
  const p0 = at(a1(), 60);
  t.eq("an unselected clip has no volume handle", st.tl.hitAt(p0.x - r0.left, p0.y - r0.top).kind === "volume", false);
  st.selectOnly([a1().id]); st.emit("sel"); await wait(30);
  t.eq("a selected audio clip's line is a volume handle", st.tl.hitAt(p0.x - r0.left, p0.y - r0.top).kind, "volume");
  // drag up 30 px: +6 dB on the selected clip only
  await dragBy(at(a1(), 60), 30);
  t.near("dragging the line up 30 px turns the clip up 6 dB", vol(a1()), 6, 0.21);
  t.eq("a clip not selected keeps its level", vol(a2()), 0);
  t.ok("the waveform and the playback follow (gain at the playhead)", Math.abs(st.kf.gainAt(a1(), 60) - Math.pow(10, 6 / 20)) < 0.06, String(st.kf.gainAt(a1(), 60)));
  t.ok("Effect Controls shows the new level", /6\.0/.test(document.getElementById("fx").textContent), document.getElementById("fx").textContent.slice(0, 120));
  st.actions.run("undo"); await wait(30);
  t.eq("one undo puts it back", vol(a1()), 0);
  // several selected clips move together (the video in the selection is left alone)
  st.selectOnly([a1().id, a2().id, v1().id]); st.emit("sel"); await wait(30);
  await dragBy(at(a1(), 60), -20);
  t.ok("every selected audio clip moves by the same amount", Math.abs(vol(a1()) + 4) < 0.21 && Math.abs(vol(a2()) + 4) < 0.21, `${vol(a1())} ${vol(a2())}`);
  t.ok("the video has no volume to change", !(v1().fx && v1().fx.volume));
  // the catch at 0 dB: from -4, a drag up 19 px would land at -0.2 and is caught at 0
  await dragBy(at(a1(), 60), 19);
  t.ok("a catch at 0 dB", vol(a1()) === 0 && vol(a2()) === 0, `${vol(a1())} ${vol(a2())}`);
  // Ctrl for fine steps: 20 px = 1 dB
  st.selectOnly([a1().id]); st.emit("sel"); await wait(30);
  await dragBy(at(a1(), 60), 20, { ctrl: true });
  t.near("Ctrl drags in fine steps (20 px = 1 dB)", vol(a1()), 1, 0.11);
  // the limits: never under -60 dB
  await dragBy(at(a1(), 60), -600);
  t.eq("never under -60 dB", vol(a1()), -60);
  // double-click the line: back to 0 dB
  const pd = at(a1(), 60);
  wrap.dispatchEvent(new MouseEvent("dblclick", { bubbles: true, clientX: pd.x, clientY: pd.y }));
  await wait(40);
  t.eq("double-click the line: back to 0 dB", vol(a1()), 0);
  // a clip with volume keyframes keeps its shape: every key moves by the drag
  const c = a1();
  st.history.commit("keys", (d) => { const x = d.clips.find((k) => k.id === c.id); st.kf.addKey(x, "volume", x.in + 30, 0); st.kf.addKey(x, "volume", x.in + 90, -6); });
  await wait(30);
  await dragBy(at(a1(), 20), 15);
  const keys = a1().fx.volume.k.map((k) => k.v);
  t.ok("keyframes all move by the drag, keeping the fade's shape", Math.abs(keys[0] - 3) < 0.21 && Math.abs(keys[1] + 3) < 0.21, JSON.stringify(keys));
});
