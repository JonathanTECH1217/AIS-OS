import { test, wait } from "./harness.js";

test("handzoom", async (t, st) => {
  await t.fresh();
  const v = st.tl.view;
  st.tl.setPpf(4);
  await wait(20);
  v.scrollF = 60;
  st.tl.redraw();
  t.key("H");
  const wrap = document.querySelector(".tl-wrap");
  const r = wrap.getBoundingClientRect();
  const a = { x: r.left + 400, y: r.top + 120 }, b = { x: r.left + 200, y: r.top + 120 };
  wrap.dispatchEvent(t.pe("pointerdown", a));
  for (let i = 1; i <= 5; i += 1) { wrap.dispatchEvent(t.pe("pointermove", { x: a.x - 40 * i, y: a.y })); await wait(5); }
  wrap.dispatchEvent(t.pe("pointerup", b));
  await wait(20);
  t.near("hand drag scrolls the timeline", v.scrollF, 60 + 200 / 4, 1);
  t.key("Z");
  const p0 = v.ppf;
  await t.tlClick(90, "V1");
  t.ok("zoom tool click zooms in", v.ppf > p0 * 1.4, `${p0} -> ${v.ppf}`);
  await t.tlClick(90, "V1", { alt: true });
  t.near("alt-click zooms back out", v.ppf, p0, 0.01);
  t.key("V");
  const p1 = v.ppf;
  t.key("="); await wait(10);
  t.ok("= zooms in", v.ppf > p1);
  t.key("-"); t.key("-"); await wait(10);
  t.ok("- zooms out", v.ppf < p1);
  t.key("\\"); await wait(10);
  const w = r.width;
  t.ok("\\ fits the short to the width", Math.abs(v.ppf * 180 - (w - 40)) < 3 && v.scrollF === 0, `${v.ppf * 180} vs ${w - 40}`);
  // touchpad and wheel (2026-09-30): a sideways swipe or Shift+wheel moves through time, a swipe up or down moves the
  // tracks, a pinch (Ctrl+wheel) zooms at the pointer
  const wheel = (o, target = wrap) => target.dispatchEvent(new WheelEvent("wheel", Object.assign({ bubbles: true, cancelable: true, clientX: r.left + 300, clientY: r.top + 100 }, o)));
  const s0 = v.scrollF;
  wheel({ deltaX: 100 });
  t.ok("a sideways swipe moves through time", v.scrollF > s0);
  const s1 = v.scrollF;
  wheel({ deltaY: 100, shiftKey: true });
  t.ok("Shift+wheel moves through time too", v.scrollF > s1);
  const f2 = v.scrollF;
  // make the tracks taller than the panel so there is something to scroll
  for (const id of ["V2", "V1", "A1", "A2"]) st.tl.view.expanded.add(id);
  st.emit("view"); await wait(30);
  wheel({ deltaY: 120 });
  await wait(20);
  t.ok("a swipe up or down moves the tracks", v.scrollY > 0 && Math.abs(v.scrollF - f2) < 0.01, `scrollY ${v.scrollY}`);
  const y1 = v.scrollY;
  wheel({ deltaY: -60 }, document.querySelector(".tl-heads"));
  await wait(20);
  t.ok("the same swipe over the track names moves them too", v.scrollY < y1, `${y1} -> ${v.scrollY}`);
  const vs = document.querySelector(".tl-vscroll");
  t.ok("a scrollbar shows when the tracks don't fit", vs && !vs.classList.contains("is-empty") && Math.abs(vs.scrollTop - v.scrollY) <= 1, `${vs && vs.scrollTop} vs ${v.scrollY}`);
  vs.scrollTop = 0; vs.dispatchEvent(new Event("scroll")); await wait(30);
  t.eq("dragging the scrollbar moves the tracks", Math.round(v.scrollY), 0);
  wheel({ deltaY: 100000 }); await wait(20);
  const last = [...document.querySelectorAll(".tl-add .chip")][1].getBoundingClientRect();
  const panel = document.querySelector(".tl-heads").getBoundingClientRect();
  t.ok("scrolled to the end, the + Video / + Audio row is in view", last.bottom <= panel.bottom + 1, `${last.bottom} vs ${panel.bottom}`);
  for (const id of ["V2", "V1", "A1", "A2"]) st.tl.view.expanded.delete(id);
  st.emit("view"); await wait(30);
  const z0 = v.ppf;
  wheel({ deltaY: -100, ctrlKey: true });
  t.ok("Ctrl+wheel (a pinch) zooms in", v.ppf > z0);
  localStorage.setItem("studio.tl.expanded", "[]");
});
