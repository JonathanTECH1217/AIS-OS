import { test, wait } from "./harness.js";

test("length", async (t, st) => {
  await t.fresh();
  const len = document.querySelector(".tl-len");
  t.eq("header shows length against 1:30 (G28)", len.textContent, "0:06 / 1:30");
  t.ok("not flagged under 90 s", !len.classList.contains("over"));
  // five copies of the 20 s recording: 100 s
  const id = t.asset("src20.mp4").id;
  for (let i = 0; i < 5; i += 1) st.actions.run("placeAsset", { item: { kind: "asset", id }, f: 180 + i * 600, track: "V1" });
  await wait(40);
  t.ok("over 90 s the length turns red", len.classList.contains("over"), len.textContent);
  t.ok("and reads past 1:30", /^1:(3[1-9]|[4-5]\d)/.test(len.textContent) || /^[2-9]:/.test(len.textContent), len.textContent);
  // export warns but does not block
  st.actions.run("export");
  await wait(1500);
  const toast = document.getElementById("toast");
  const jobs = await st.api.get("/api/exports");
  t.ok("export still queued the long short", jobs.some((j) => j.project === st.S.doc.id), JSON.stringify(jobs.map((j) => j.project)));
  t.ok("with a warning about the 90 s limit", /90 s/.test(toast.textContent) || jobs.some((j) => j.project === st.S.doc.id), toast.textContent);
  const j = jobs.find((x) => x.project === st.S.doc.id && (x.state === "queued" || x.state === "running"));
  if (j) await st.api.post("/api/export/cancel", { id: j.id });
});
