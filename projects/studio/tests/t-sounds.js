import { test, wait, until } from "./harness.js";

test("sounds", async (t, st) => {
  await t.fresh();
  const pop = t.asset("pop.wav");
  const row = [...document.querySelectorAll(".bin-item")].find((r) => r.textContent.includes("pop.wav"));
  row.querySelector(".icon-btn").click();
  await until(() => st.audio.audition, 3000);
  t.ok("clicking a sound plays it (G17)", !!st.audio.audition);
  // drag it from the bin onto A3 (Sounds) at frame 60
  const dt = new DataTransfer();
  row.dispatchEvent(new DragEvent("dragstart", { bubbles: true, dataTransfer: dt }));
  t.ok("a sound carries a drag payload", dt.getData("application/x-studio").includes(pop.id));
  const wrap = document.querySelector(".tl-wrap");
  const p = t.tlPoint(60, "A3");
  st.S.snap = false;
  wrap.dispatchEvent(new DragEvent("dragover", { bubbles: true, cancelable: true, dataTransfer: dt, clientX: p.x, clientY: p.y }));
  wrap.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer: dt, clientX: p.x, clientY: p.y }));
  await wait(40);
  const c = t.clip("A3")[0];
  t.ok("dropping it on A3 (Sounds) places it there", c && c.asset === pop.id, JSON.stringify(t.clip("A3")));
  t.near("at the drop point", c.start, 60, 1);
  t.eq("as long as the sound (0.25 s)", c.out - c.in, Math.floor(0.25 * 30));
  // a sound dropped on a video track goes to the sounds track anyway
  wrap.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer: dt, clientX: t.tlPoint(120, "V2").x, clientY: t.tlPoint(120, "V2").y }));
  await wait(40);
  t.eq("a sound dropped on V2 still lands on the sounds track", t.clip("A3").length, 2);
  // dropped on a voice track it would cut a hole in that voice: it goes on Sounds instead (2026-09-30)
  const themBefore = JSON.stringify(t.clip("A2"));
  wrap.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer: dt, clientX: t.tlPoint(150, "A2").x, clientY: t.tlPoint(150, "A2").y }));
  await wait(40);
  t.ok("a sound dropped on Them lands on Sounds and leaves her voice whole", t.clip("A3").length === 3 && JSON.stringify(t.clip("A2")) === themBefore);
});
