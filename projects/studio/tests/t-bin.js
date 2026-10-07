import { test, wait, until } from "./harness.js";

test("bin", async (t, st) => {
  const heads = [...document.querySelectorAll(".bin-sec-title")].map((x) => x.textContent);
  t.eq("the bin mirrors media/ (G24)", heads, ["Shorts", "Recordings", "Sounds", "Assets", "Ready to post"]);
  const names = [...document.querySelectorAll(".bin-name")].map((x) => x.textContent);
  t.ok("recording, sound and assets listed", !!document.querySelector('.bin-item.rec[title*="src20.mp4"]') && names.includes("pop.wav"));
  // a recording's title is the date it was recorded (2026-10-01); src20.mp4's name has none, so its file time stands in
  const recTitle = document.querySelector('.bin-item.rec[title*="src20.mp4"] .bin-name').textContent;
  t.ok("a recording is titled by the date it was recorded", /^(Sun|Mon|Tue|Wed|Thu|Fri|Sat) [A-Z][a-z]{2} \d{1,2}, \d{1,2}:\d{2} (AM|PM)$/.test(recTitle), recTitle);
  // drag-in: a file dropped onto the bin is copied into the right folder (images to assets)
  const png = await (await fetch("/fonts/../favicon.png")).blob();
  const file = new File([png], "badge.png", { type: "image/png" });
  const dt = new DataTransfer();
  dt.items.add(file);
  const bin = document.getElementById("bin");
  bin.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer: dt }));
  await until(() => st.lib.all().some((a) => a.name === "badge.png"), 8000);
  const badge = st.lib.all().find((a) => a.name === "badge.png");
  t.ok("a dropped image lands in media/assets", badge && badge.rel === "assets/badge.png", badge && badge.rel);
  // the recording row (B15): its calls; a click opens its calls view (2026-10-01; t-browse covers the view itself)
  const src = t.asset("src20.mp4");
  const rec = [...document.querySelectorAll(".bin-item.rec")].find((r) => r.title.includes("src20.mp4"));
  t.ok("the recording row shows its calls", rec && /2 calls · 1 booked/.test(rec.textContent), rec && rec.textContent);
  t.ok("with calls found, Find calls moves to the row's menu", !/Find calls/.test(rec.textContent));
  rec.click();
  await until(() => st.browse.isOpen() && document.querySelectorAll(".br-row").length === 4, 4000);
  t.ok("clicking a recording opens its calls", st.browse.isOpen());
  st.browse.close();
  await wait(40);
  t.ok("and the back arrow's close brings the sections back", [...document.querySelectorAll(".bin-sec-title")].length === 5);
  // a second, older recording (2026-10-01): titled by the date it was recorded, folded under "Previous recordings"
  const inbox = () => st.S.bin.folders.find((x) => x.dir === "inbox");
  const old = { id: "a_olderone", name: "2020-01-01 09-00-00.mkv", rel: "inbox/2020-01-01 09-00-00.mkv", kind: "video", duration: 10918,
    stages: {}, urls: {}, recorded: "2020-01-01T09:00:00", recordedFrom: "name", calls: { n: 18, booked: 0 }, moments: true };
  const put = () => { const f = inbox(); if (!f.items.some((a) => a.id === old.id)) f.items.push(old); st.emit("bin"); };
  const fold = await until(() => { put(); return document.querySelector(".bin-sub-head"); }, 4000, 100);
  t.ok("earlier recordings fold under Previous recordings, closed at first", fold && /Previous recordings/.test(fold.textContent) && /1/.test(fold.textContent)
    && !document.querySelector('.bin-item.rec[data-id="a_olderone"]'), fold && fold.textContent);
  t.ok("the newest recording stays in view", !!document.querySelector(`.bin-item.rec[data-id="${src.id}"]`));
  fold.click();
  const opened = await until(() => { put(); return document.querySelector('.bin-item.rec[data-id="a_olderone"]'); }, 4000, 100);
  t.ok("opening the fold shows them, titled by the date recorded", opened && /Wed Jan 1, 9:00 AM/.test(opened.textContent), opened && opened.textContent);
  document.querySelector(".bin-sub-head").click();
  const closed = await until(() => { put(); return !document.querySelector('.bin-item.rec[data-id="a_olderone"]'); }, 4000, 100);
  t.ok("and it folds away again", closed);
  inbox().items = inbox().items.filter((a) => a.id !== old.id); st.emit("bin");
  // a short from moment m01 (G7), with V1 and A1 linked
  await t.fresh();
  t.ok("a short from a moment opens", st.S.doc && st.S.doc.moment && st.S.doc.moment.mid === "m01");
  const v = st.S.doc.clips.find((c) => c.track === "V1"), a = st.S.doc.clips.find((c) => c.track === "A1");
  t.ok("with linked video and audio", v && a && v.link && v.link === a.link);
  t.eq("covering the moment (1.0 s to 7.0 s)", [v.in, v.out], [30, 210]);
  await until(() => document.querySelector(".bin-item.short.is-sel"), 6000);
  // status chips (G38): Draft; mark done; Export all queues only Done shorts
  let row = document.querySelector(".bin-item.short.is-sel");
  t.ok("the open short shows a Draft chip", row && /Draft/.test(row.textContent));
  st.actions.run("markDone");
  await st.save.flush(true);
  await until(() => [...document.querySelectorAll(".bin-item.short.is-sel .chip-status")].some((c) => c.textContent === "Done"), 4000);
  row = [...document.querySelectorAll(".bin-item.short")].find((r) => r.classList.contains("is-sel"));
  t.ok("Mark done shows a Done chip", row && /Done/.test(row.textContent));
  const r = await st.api.exportAll();
  t.eq("Export all queues just the Done short", r.queued, 1);
  const jobs = await st.api.get("/api/exports");
  const j = jobs.find((x) => x.project === st.S.doc.id && (x.state === "queued" || x.state === "running"));
  if (j) await st.api.post("/api/export/cancel", { id: j.id });
  t.ok("prep stages done for the fixture", Object.values(src.stages).every((s) => s.state === "done"));
});
