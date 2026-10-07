import { test, wait } from "./harness.js";

test("effects", async (t, st) => {
  // the shared easing vectors: the page must compute what the exporter computes
  const vec = await (await fetch("/tests/vectors.json")).json();
  let bad = 0;
  for (const c of vec) {
    const got = st.kf.valueAt({ fx: { scale: { v: 100, k: c.keys } } }, "scale", c.t);
    if (Math.abs(got - c.want) > 1e-6) { bad += 1; if (bad < 4) t.fail("vector", JSON.stringify({ c, got })); }
  }
  t.ok(`all ${vec.length} easing vectors match the exporter`, bad === 0);

  await t.fresh();
  document.querySelector(".tab").click();
  let [v] = t.clip("V1");
  st.selectOnly([v.id]);
  await wait(40);
  const labels = [...document.querySelectorAll(".fx-row .fx-label")].map((x) => x.textContent);
  for (const l of ["Position X", "Position Y", "Scale", "Rotation", "Opacity"]) t.ok(`Effect Controls shows ${l} (G14)`, labels.includes(l));
  const rowOf = (label) => [...document.querySelectorAll(".fx-row")].find((r) => r.querySelector(".fx-label").textContent === label);
  // stopwatch on Scale at frame 30
  st.pb.seek(30); await wait(20);
  rowOf("Scale").querySelector(".fx-watch").click();
  await wait(30);
  [v] = t.clip("V1");
  t.eq("stopwatch adds a keyframe at the playhead", (v.fx.scale.k || []).map((k) => k.t), [v.in + 30]);
  // move on and type a new value: a second key
  st.pb.seek(90); await wait(30);
  const nf = rowOf("Scale").querySelector(".num-field");
  nf.dispatchEvent(t.pe("pointerdown", { x: 1, y: 1 })); nf.dispatchEvent(t.pe("pointerup", { x: 1, y: 1 }));
  await wait(20);
  const inp = nf.querySelector("input");
  inp.value = "150";
  inp.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await wait(40);
  [v] = t.clip("V1");
  t.eq("typing a value while animating adds a second key", v.fx.scale.k.map((k) => [k.t, k.v]), [[v.in + 30, 100], [v.in + 90, 150]]);
  t.near("halfway the value is between (linear)", st.kf.valueAt(v, "scale", v.in + 60), 125, 1e-9);
  // keyframe navigation
  rowOf("Scale").querySelectorAll(".fx-nav")[0].click();
  await wait(20);
  t.eq("previous-keyframe arrow jumps to the first key", Math.round(st.S.playhead), 30);
  rowOf("Scale").querySelectorAll(".fx-nav")[1].click();
  await wait(20);
  t.eq("next-keyframe arrow jumps to the second key", Math.round(st.S.playhead), 90);
  // the diamond button on a key removes it
  rowOf("Scale").querySelector(".fx-diamond").click();
  await wait(30);
  [v] = t.clip("V1");
  t.eq("diamond on a key removes it", v.fx.scale.k.length, 1);
  // lane drag moves a key; lane right-click sets easing
  const lane = rowOf("Scale").querySelector(".fx-lane");
  const lr = lane.getBoundingClientRect();
  const x0 = lr.left + ((v.fx.scale.k[0].t - v.in) / (v.out - v.in)) * lr.width;
  lane.dispatchEvent(t.pe("pointerdown", { x: x0, y: lr.top + 10 }));
  lane.dispatchEvent(t.pe("pointermove", { x: x0 + lr.width * 0.25, y: lr.top + 10 }));
  lane.dispatchEvent(t.pe("pointerup", { x: x0 + lr.width * 0.25, y: lr.top + 10 }));
  await wait(30);
  [v] = t.clip("V1");
  t.ok("dragging a diamond in the lane moves the key later", v.fx.scale.k[0].t > v.in + 60, String(v.fx.scale.k[0].t));
  // stopwatch off keeps the value, drops the keys
  rowOf("Scale").querySelector(".fx-watch").click();
  await wait(30);
  [v] = t.clip("V1");
  t.ok("stopwatch off drops the keys", !v.fx.scale.k);
  // Rotation and Position are keyframeable too
  for (const lbl of ["Position X", "Rotation", "Opacity"]) {
    rowOf(lbl).querySelector(".fx-watch").click();
    await wait(20);
  }
  [v] = t.clip("V1");
  t.ok("Position X, Rotation, Opacity animate", !!(v.fx.posX.k && v.fx.rot.k && v.fx.opacity.k));
  // audio: Volume row
  const [a] = t.clip("A1");
  st.selectOnly([a.id]);
  await wait(30);
  t.ok("an audio clip shows Level (volume)", !!rowOf("Level"));
});
