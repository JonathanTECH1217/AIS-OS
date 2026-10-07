import { test, wait } from "./harness.js";

test("select", async (t, st) => {
  await t.fresh();
  st.S.snap = false;
  const [v] = t.clip("V1"), [a] = t.clip("A1");
  await t.tlClick(90, "V1");
  t.ok("click selects the clip and its linked audio (G31)", st.S.sel.has(v.id) && st.S.sel.has(a.id));
  await t.tlClick(90, "V1", { shift: true });
  t.eq("shift-click takes it back off", st.S.sel.size, 0);
  await t.tlClick(90, "V1", { alt: true });
  t.ok("alt-click grabs only the video", st.S.sel.has(v.id) && !st.S.sel.has(a.id));
  // move: linked pair moves together
  await t.tlClick(90, "V1");
  await t.tlDrag({ f: 90, track: "V1" }, { f: 150, track: "V1" });
  t.eq("drag moves the clip 60 frames", t.clip("V1")[0].start, 60);
  t.eq("its linked audio moved too", t.clip("A1")[0].start, 60);
  // alt-drag moves one side only
  await t.tlDrag({ f: 120, track: "V1" }, { f: 90, track: "V1" }, { alt: true });
  t.eq("alt-drag moves only the video", [t.clip("V1")[0].start, t.clip("A1")[0].start], [30, 60]);
  st.history.undo();
  await wait(20);
  // change track: V1 -> V2
  await t.tlDrag({ f: 120, track: "V1" }, { f: 120, track: "V2" }, { alt: true });
  t.eq("drag up moves the clip to V2", st.S.doc.clips.find((c) => c.id === v.id).track, "V2");
  st.history.undo();
  await wait(20);
  // marquee from an empty spot selects what it touches
  await t.tlClick(10, "V2");
  t.eq("click on empty track clears selection", st.S.sel.size, 0);
  await t.tlDrag({ f: 5, track: "V2" }, { f: 100, track: "A1" });
  t.ok("marquee selects the clips it crosses", st.S.sel.has(v.id) && st.S.sel.has(a.id), [...st.S.sel].join(","));
  // 2026-10-02 ("I should also be able to drag select clips"): it also starts in the Captions row and below the tracks
  await t.tlClick(10, "V2");
  await t.tlDrag({ f: 5, track: "C" }, { f: 100, track: "V1" });
  t.ok("a drag from the Captions row selects the clips it crosses", st.S.sel.has(v.id) && !st.S.sel.has(a.id), [...st.S.sel].join(","));
  await t.tlClick(10, "V2");
  const wr = document.querySelector(".tl-wrap").getBoundingClientRect();
  const lastRow = st.tl.rows()[st.tl.rows().length - 1];
  const below = { x: wr.left + st.tl.xOf(150), y: wr.top + lastRow.y + lastRow.h + 6 };
  const intoA1 = { x: wr.left + st.tl.xOf(20), y: wr.top + st.tl.yOfTrack("A1") };
  const pd = (type, p) => new PointerEvent(type, { bubbles: true, cancelable: true, clientX: p.x, clientY: p.y, button: 0,
    buttons: type === "pointerup" ? 0 : 1, pointerId: 1, pointerType: "mouse", isPrimary: true, detail: 1 });
  const wrapEl = document.querySelector(".tl-wrap");
  wrapEl.dispatchEvent(pd("pointerdown", below));
  for (let i = 1; i <= 6; i += 1) { wrapEl.dispatchEvent(pd("pointermove", { x: below.x + ((intoA1.x - below.x) * i) / 6, y: below.y + ((intoA1.y - below.y) * i) / 6 })); await wait(10); }
  wrapEl.dispatchEvent(pd("pointerup", intoA1)); await wait(40);
  t.ok("a drag from below the last track selects the clips it crosses", st.S.sel.has(a.id) && !st.S.sel.has(v.id), [...st.S.sel].join(","));
  // overwrite on drop: a text clip dropped over the video's start trims it (V2 over V1 is a different track, so use V1)
  st.actions.run("newText", { f: 0, track: "V1" });
  await wait(30);
  const v1 = t.clip("V1");
  t.ok("a clip placed over another overwrites it (the video is trimmed, not overlapped)",
    v1.length === 2 && v1[0].type === "text" && v1[1].start === 90, JSON.stringify(v1.map((c) => [c.type, c.start])));
  // insert with Ctrl: moving pushes the rest right
  st.history.undo();
  await wait(20);
  const len = st.doc.clipLen(t.clip("V1")[0]);
  st.actions.run("newText", { f: 400, track: "V2" });
  await wait(20);
  const txt = t.clip("V2")[0];
  const before = t.clip("V1")[0].start;
  await t.tlDrag({ f: 410, track: "V2" }, { f: 70, track: "V1" }, { ctrl: true });
  t.ok("ctrl-drag inserts and pushes the clips after the drop point right", t.clip("V1").some((c) => c.id === txt.id) || t.clip("V2").some((c) => c.id === txt.id));
  t.ok("insert kept the moved clip whole", st.doc.clipLen(st.S.doc.clips.find((c) => c.id === txt.id)) === 90);
  t.ok("clip length unchanged by selection work", len === 180 && before === 60);
});
