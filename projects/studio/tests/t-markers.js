import { test, wait } from "./harness.js";

test("markers", async (t, st) => {
  await t.fresh();
  st.pb.seek(45);
  t.key("M"); await wait(20);
  t.eq("M adds a marker at the playhead (G33)", st.S.doc.markers.map((m) => m.t), [45]);
  t.key("M"); await wait(20);
  t.eq("a second M on the same frame doesn't duplicate it", st.S.doc.markers.length, 1);
  st.actions.run("editMarker", st.S.doc.markers[0].id);
  await wait(40);
  const dlg = document.querySelector(".dialog");
  t.ok("edit marker opens a dialog", !!dlg);
  dlg.querySelector("input").value = "hook ends";
  [...dlg.querySelectorAll(".chip")].find((c) => c.textContent === "red").click();
  dlg.querySelector(".actions .btn").click();
  await wait(30);
  t.eq("note and color saved", [st.S.doc.markers[0].note, st.S.doc.markers[0].color], ["hook ends", "red"]);
  // right-click the marker on the ruler
  const items = await t.tlContext(45, "ruler");
  t.ok("right-click a marker offers edit and delete", items.includes("Edit marker…") && items.includes("Delete marker"), items.join("|"));
  [...document.querySelectorAll(".menu-item")].find((x) => x.textContent.includes("Delete marker")).click();
  await wait(20);
  t.eq("delete marker removes it", st.S.doc.markers.length, 0);
  // markers move with a ripple
  st.pb.seek(150); t.key("M");
  st.pb.seek(60); t.key("Ctrl+K"); await wait(20);
  st.selectOnly(st.doc.withLinked(st.S.doc, [t.clip("V1")[0].id]));
  t.key("Shift+Delete"); await wait(20);
  t.eq("a ripple delete pulls later markers left", st.S.doc.markers.map((m) => m.t), [90]);
});
