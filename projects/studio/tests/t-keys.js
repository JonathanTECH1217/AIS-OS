import { test, wait } from "./harness.js";

test("keys", async (t, st) => {
  await t.fresh();
  // tools by letter (G4, G5)
  for (const [k, tool] of [["C", "razor"], ["H", "hand"], ["Z", "zoom"], ["B", "ripple"], ["N", "rolling"], ["Y", "slip"], ["U", "slide"], ["P", "pen"], ["T", "text"], ["V", "select"]]) {
    t.key(k);
    await wait(5);
    t.eq(`${k} picks the ${tool} tool`, st.S.tool, tool);
  }
  // every bound key runs an action that exists
  for (const [combo, id] of st.keys.map()) t.ok(`binding ${combo} -> ${id}`, !!st.actions.get(id));
  // Premiere essentials are bound
  const want = { Space: "play", J: "shuttleJ", K: "shuttleK", L: "shuttleL", C: "tool.razor", "Ctrl+K": "split", Q: "rippleTrimPrev", W: "rippleTrimNext",
    "Shift+Delete": "rippleDelete", I: "markIn", O: "markOut", "=": "zoomIn", "-": "zoomOut", "Ctrl+Z": "undo", "Ctrl+Shift+Z": "redo", "Ctrl+M": "export", M: "addMarker", "Ctrl+D": "dissolve", S: "snap" };
  for (const [combo, id] of Object.entries(want)) t.eq(`${combo} is ${id}`, st.keys.map().get(combo), id);
  // arrows step one frame
  st.pb.seek(50);
  t.key("Right"); await wait(10);
  t.eq("Right steps +1 frame", Math.round(st.S.playhead), 51);
  t.key("Shift+Left"); await wait(10);
  t.eq("Shift+Left steps -5 frames", Math.round(st.S.playhead), 46);
  // typing in a field does not switch tools
  document.querySelector(".tab:nth-child(2)").click();
  await wait(30);
  const inp = document.createElement("input");
  document.body.append(inp);
  inp.focus();
  t.key("C", inp);
  t.eq("typing C in a field leaves the tool alone", st.S.tool, "select");
  inp.remove();
  // I / O mark the range
  st.pb.seek(20); t.key("I"); st.pb.seek(60); t.key("O"); await wait(10);
  t.eq("I and O mark in and out", [st.S.doc.range.in, st.S.doc.range.out], [20, 60]);
  t.key("Ctrl+Shift+X"); await wait(10);
  t.eq("Ctrl+Shift+X clears in and out", [st.S.doc.range.in, st.S.doc.range.out], [null, null]);
  t.key("?"); await wait(30);
  t.ok("? opens the shortcut sheet", !!document.querySelector(".kb-grid"));
});
