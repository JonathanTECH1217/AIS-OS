import { test, wait } from "./harness.js";

test("pen", async (t, st) => {
  await t.fresh();
  const wrap = document.querySelector(".tl-wrap");
  const r = wrap.getBoundingClientRect();
  t.key("P");
  let [v] = t.clip("V1");
  // click on the clip's lower half with the pen: a keyframe (opacity, the default band for video)
  const row = st.tl.rows().find((x) => x.id === "V1");
  const y = row.y + row.h - 12;
  const p = { x: r.left + st.tl.xOf(60), y: r.top + y };
  wrap.dispatchEvent(t.pe("pointerdown", p)); wrap.dispatchEvent(t.pe("pointerup", p));
  await wait(30);
  [v] = t.clip("V1");
  const keys = st.kf.keysOf(v, "opacity");
  t.ok("pen click adds a keyframe", keys && keys.length === 1, JSON.stringify(v.fx));
  t.eq("at the clicked frame", keys[0].t, v.in + 60);
  t.ok("value from the height clicked (low = low opacity)", keys[0].v < 40, String(keys[0].v));
  // second key
  const p2 = { x: r.left + st.tl.xOf(120), y: r.top + row.y + 22 };
  wrap.dispatchEvent(t.pe("pointerdown", p2)); wrap.dispatchEvent(t.pe("pointerup", p2));
  await wait(30);
  [v] = t.clip("V1");
  t.eq("second pen click adds a second keyframe", st.kf.keysOf(v, "opacity").length, 2);
  // drag the first diamond right by 10 frames (Shift keeps its value)
  const kp = st.tl.keyPoint(v, "opacity", v.in + 60);
  const a = { x: r.left + kp.x, y: r.top + kp.y };
  wrap.dispatchEvent(t.pe("pointerdown", a));
  for (let i = 1; i <= 5; i += 1) wrap.dispatchEvent(t.pe("pointermove", { x: a.x + (10 * st.tl.view.ppf * i) / 5, y: a.y }, { shift: true }));
  wrap.dispatchEvent(t.pe("pointerup", { x: a.x + 10 * st.tl.view.ppf, y: a.y }, { shift: true }));
  await wait(30);
  [v] = t.clip("V1");
  t.eq("dragging a diamond moves the keyframe in time", st.kf.keysOf(v, "opacity")[0].t, v.in + 70);
  // right-click the diamond: easing menu
  const kp2 = st.tl.keyPoint(v, "opacity", v.in + 70);
  wrap.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: r.left + kp2.x, clientY: r.top + kp2.y }));
  await wait(30);
  const labels = [...document.querySelectorAll(".menu .menu-label")].map((x) => x.textContent);
  t.eq("right-click a diamond: Linear, Ease In, Ease Out, Ease In & Out, Hold, Delete",
    labels, ["Linear", "Ease In", "Ease Out", "Ease In & Out", "Hold", "Delete keyframe"]);
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Ease Out")).click();
  await wait(30);
  [v] = t.clip("V1");
  t.eq("choosing Ease Out sets it", st.kf.keysOf(v, "opacity")[0].e, "out");
  wrap.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: r.left + kp2.x, clientY: r.top + kp2.y }));
  await wait(30);
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Delete keyframe")).click();
  await wait(30);
  [v] = t.clip("V1");
  t.eq("Delete keyframe removes it", st.kf.keysOf(v, "opacity").length, 1);
  t.key("V");
});
