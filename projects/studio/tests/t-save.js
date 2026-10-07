import { test, wait, until } from "./harness.js";

test("save", async (t, st) => {
  const doc = await t.fresh();
  const rev0 = st.S.baseRev;
  st.pb.seek(33); t.key("M");
  await wait(100);
  t.eq("an edit starts a save", st.S.saving, "saving");
  const t0 = performance.now();
  await until(() => st.S.saving === "saved" && st.S.baseRev > rev0, 5000, 20);
  t.ok("autosave lands within about a second (G26)", performance.now() - t0 < 1500 && st.S.baseRev > rev0, `${Math.round(performance.now() - t0)} ms`);
  const onDisk = await st.api.project(doc.id);
  t.eq("the server has the marker", onDisk.markers.map((m) => m.t), [33]);
  t.ok("the top bar says Saved", /Saved/.test(document.querySelector(".tb-saving").textContent));
  // Ctrl+S saves at once
  st.pb.seek(44); t.key("M");
  t.key("Ctrl+S");
  await until(() => st.S.saving === "saved", 3000, 20);
  t.eq("Ctrl+S saves now", (await st.api.project(doc.id)).markers.map((m) => m.t), [33, 44]);
  // captions saved with the short, stamped for the exporter
  const disk = await st.api.project(doc.id);
  t.ok("captions are saved with the short", disk.captions.events.length > 0);
  t.eq("stamped with the revision they were built for", disk.captions.evRev, disk.rev);
  // a stale save is refused (another window)
  let status = 0;
  try { await st.api.saveProject(doc.id, disk, disk.rev - 1); } catch (e) { status = e.status; }
  t.eq("a save based on an old revision gets 409", status, 409);
  // versions: one was kept on creation
  const vs = await st.api.versions(doc.id);
  t.ok("a version is kept (every 10 minutes)", vs.length >= 1);
  st.actions.run("versions");
  await wait(200);
  t.ok("File > Versions lists them", document.querySelectorAll(".dialog .open-row").length >= 1);
  document.querySelector(".dialog .open-row").click();
  await until(() => st.S.doc.markers.length === 0, 3000);
  t.eq("restoring a version brings back that copy", st.S.doc.markers.length, 0);
  t.key("Ctrl+Z"); await wait(30);
  t.eq("and Undo puts the newer copy back", st.S.doc.markers.map((m) => m.t), [33, 44]);
  // reopening the short shows what was saved
  await st.save.flush(true);
  await st.openShort(doc.id);
  t.eq("reopened short has the saved edits", st.S.doc.markers.map((m) => m.t), [33, 44]);
});
