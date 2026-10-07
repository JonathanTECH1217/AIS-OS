import { test, wait } from "./harness.js";

test("context", async (t, st) => {
  await t.fresh();
  const has = (items, list) => list.every((x) => items.includes(x));
  let items = await t.tlContext(90, "V1");
  t.ok("clip menu", has(items, ["Split here", "Ripple delete", "Delete", "Unlink", "Enable", "Join through edit", "Show keyframes", "Reveal in bin"]), items.join("|"));
  t.closeMenus();
  st.pb.seek(90); t.key("Ctrl+K"); await wait(20);
  items = await t.tlContext(90, "V1");
  t.ok("cut (edit point) menu", has(items, ["Join through edit", "Cross dissolve", "Dip to black"]), items.join("|"));
  t.closeMenus();
  t.key("Ctrl+D"); await wait(20);
  items = await t.tlContext(90, "V1", 16);
  t.ok("transition menu", has(items, ["Cross dissolve", "Dip to black", "Delete transition"]), items.join("|"));
  t.closeMenus();
  items = await t.tlContext(400, "V1");
  t.ok("gap menu", has(items, ["Ripple delete gap"]), items.join("|"));
  t.closeMenus();
  st.pb.seek(40); t.key("M"); await wait(20);
  items = await t.tlContext(40, "ruler");
  t.ok("marker menu", has(items, ["Edit marker…", "Delete marker"]), items.join("|"));
  t.closeMenus();
  // keyframe menu
  const v = t.clip("V1")[0];
  st.history.commit("k", (d) => { st.kf.addKey(d.clips.find((c) => c.id === v.id), "opacity", v.in + 20, 80); });
  st.selectOnly([v.id]); await wait(20);
  const kp = st.tl.keyPoint(t.clip("V1")[0], "opacity", v.in + 20);
  const r = document.querySelector(".tl-wrap").getBoundingClientRect();
  document.querySelector(".tl-wrap").dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: r.left + kp.x, clientY: r.top + kp.y }));
  await wait(30);
  items = [...document.querySelectorAll(".menu .menu-label")].map((x) => x.textContent);
  t.ok("keyframe menu", has(items, ["Linear", "Ease In", "Ease Out", "Hold", "Delete keyframe"]), items.join("|"));
  t.closeMenus();
  // track header menu
  const h = document.querySelector(".tl-head.kind-video");
  h.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: 60, clientY: h.getBoundingClientRect().top + 5 }));
  await wait(20);
  items = [...document.querySelectorAll(".menu .menu-label")].map((x) => x.textContent);
  t.ok("track header menu", has(items, ["Add video track", "Add audio track"]), items.join("|"));
  t.closeMenus();
  // bin item menus
  const more = [...document.querySelectorAll(".bin-item")].find((r2) => (r2.title || "").includes("src20.mp4")).querySelector(".icon-btn[title='More']");
  more.dispatchEvent(new MouseEvent("click", { bubbles: true, clientX: 200, clientY: 200 }));
  await wait(20);
  items = [...document.querySelectorAll(".menu .menu-label")].map((x) => x.textContent);
  t.ok("recording menu", has(items, ["Open its calls", "Add to timeline at playhead", "Find calls again…", "Prepare again"]), items.join("|"));
  t.closeMenus();
  const smore = document.querySelector(".bin-item.short .icon-btn[title='More']");
  smore.dispatchEvent(new MouseEvent("click", { bubbles: true, clientX: 200, clientY: 200 }));
  await wait(20);
  items = [...document.querySelectorAll(".menu .menu-label")].map((x) => x.textContent);
  t.ok("short menu", has(items, ["Open", "Mark done", "Export"]), items.join("|"));
  t.closeMenus();
});
