import { test, wait, until } from "./harness.js";

test("export", async (t, st) => {
  const doc = await t.fresh();
  st.actions.run("newText", { f: 0, track: "V2" });
  await wait(30);
  t.key("Ctrl+M");
  const job = await until(async () => (await st.api.get("/api/exports")).find((j) => j.project === doc.id), 5000);
  t.ok("Ctrl+M queues an export (G27)", !!job);
  const done = await until(async () => { const j = (await st.api.get("/api/exports")).find((x) => x.project === doc.id && x.id === job.id); return j && (j.state === "done" || j.state === "error") && j; }, 80000, 500);
  t.ok("the export finishes", done && done.state === "done", JSON.stringify(done && (done.error || done.state)));
  if (!done || done.state !== "done") return;
  const res = await fetch(done.url, { method: "HEAD" });
  t.ok("the MP4 is in media/ready", res.ok && +res.headers.get("Content-Length") > 50000, String(res.status));
  await until(() => [...document.querySelectorAll(".bin-item.short.is-sel .chip-status")].some((c) => c.textContent === "Exported"), 6000);
  t.ok("the short's chip turns Exported (G38)", [...document.querySelectorAll(".bin-item.short.is-sel .chip-status")].some((c) => c.textContent === "Exported"));
  t.ok("it shows under Ready to post", st.S.bin.folders.find((f) => f.dir === "ready").items.length >= 1);
  // an edit after export puts it back to Draft/Done status (a save within 1 s of the export finishing still counts as
  // the exported version on the server, so the edit comes a moment later, as a person's would)
  await wait(1500);
  st.pb.seek(10); t.key("M");
  await st.save.flush(true);
  await until(() => ![...document.querySelectorAll(".bin-item.short.is-sel .chip-status")].some((c) => c.textContent === "Exported"), 4000);
  t.ok("editing after the export drops the Exported chip", ![...document.querySelectorAll(".bin-item.short.is-sel .chip-status")].some((c) => c.textContent === "Exported"));
});
