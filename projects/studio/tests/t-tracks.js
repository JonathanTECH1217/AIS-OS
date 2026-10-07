import { test, wait } from "./harness.js";

test("tracks", async (t, st) => {
  await t.fresh();
  t.eq("a new short starts with Captions, V2, V1, A1 You, A2 Them, A3 Sounds (G13, voice tracks 2026-09-30)", st.S.doc.tracks.map((x) => x.id), ["C", "V2", "V1", "A1", "A2", "A3"]);
  const heads = [...document.querySelectorAll(".tl-head .tl-head-id")].map((x) => x.textContent);
  t.eq("track headers top to bottom", heads.slice(1), ["V2", "V1", "A1", "A2", "A3"]);
  const names = [...document.querySelectorAll(".tl-head")].map((h) => (h.querySelector(".tl-head-name") || {}).textContent || "");
  t.eq("the audio tracks say whose they are", names.slice(-3), ["You", "Them", "Sounds"]);
  [...document.querySelectorAll(".tl-add .chip")][0].click();
  await wait(20);
  t.eq("+ Video adds V3 on top of the video tracks", st.S.doc.tracks.map((x) => x.id), ["C", "V3", "V2", "V1", "A1", "A2", "A3"]);
  [...document.querySelectorAll(".tl-add .chip")][1].click();
  await wait(20);
  t.eq("+ Audio adds A4 at the bottom", st.S.doc.tracks.map((x) => x.id).slice(-1), ["A4"]);
  // the "+" in the corner above the track names never scrolls away (2026-09-30)
  const plus = document.querySelector(".tl-head-ruler .tl-add-btn");
  t.ok("a + sits in the corner above the track names", !!plus);
  plus.click(); await wait(20);
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Add audio track")).click();
  await wait(20);
  t.eq("the corner + adds an audio track", st.S.doc.tracks.map((x) => x.id).slice(-1), ["A5"]);
  document.querySelector(".tl-head-ruler .tl-add-btn").click(); await wait(20);
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Add video track")).click();
  await wait(20);
  t.eq("and a video track (on top: V4, since V3 is already there)", st.S.doc.tracks.map((x) => x.id)[1], "V4");
  st.history.undo(); st.history.undo(); await wait(20);
  t.eq("undo takes both back", st.S.doc.tracks.map((x) => x.id).slice(-1), ["A4"]);
  // delete an empty track from its header menu; V1 can't be deleted
  const h = [...document.querySelectorAll(".tl-head")].find((x) => x.querySelector(".tl-head-id").textContent === "V3");
  h.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: 60, clientY: h.getBoundingClientRect().top + 10 }));
  await wait(20);
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Delete V3")).click();
  await wait(20);
  t.ok("an empty track can be deleted", !st.S.doc.tracks.some((x) => x.id === "V3"));
  const res = st.history.commit("del", (d) => st.ops.deleteTrack(d, "V1"));
  t.ok("V1 can't be deleted", res.ok === false);
  // lock: edits skip a locked track
  const lockBtn = [...document.querySelectorAll(".tl-head")].find((x) => x.querySelector(".tl-head-id").textContent === "V1").querySelector(".tl-tbtn[title='Lock']");
  lockBtn.click();
  await wait(20);
  t.ok("lock button locks V1", st.S.doc.tracks.find((x) => x.id === "V1").lock);
  st.pb.seek(60); t.key("Ctrl+Shift+K"); await wait(20);
  t.eq("a locked track isn't cut", [t.clip("V1").length, t.clip("A1").length], [1, 2]);
  // hide V1: the monitor goes black
  st.history.commit("unlock", (d) => { d.tracks.find((x) => x.id === "V1").lock = false; d.tracks.find((x) => x.id === "V1").hide = true; });
  t.eq("a hidden video track draws nothing", st.comp.layersAt(st.S.doc, 30).length, 0);
  // expand a track with a double-click on its header
  const v1 = [...document.querySelectorAll(".tl-head")].find((x) => x.querySelector(".tl-head-id").textContent === "V1");
  const hh = v1.getBoundingClientRect().height;
  v1.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
  await wait(30);
  const v1b = [...document.querySelectorAll(".tl-head")].find((x) => x.querySelector(".tl-head-id").textContent === "V1");
  t.ok("double-click a header makes the track taller", v1b.getBoundingClientRect().height > hh * 1.5);
  v1b.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
});
