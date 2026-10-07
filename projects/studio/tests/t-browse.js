import { test, wait, until } from "./harness.js";

// The calls view (2026-10-01, brainstorms/2026-10-01-clip-browser.md), at 1536x780 (run.py). The fixture recording
// src20.mp4 has a gatekeeper call c01 (0-7.2 s, best bit m01), a booking c02 (7.2-16.5 s, m02, Dana speaks from 7.5 s),
// a stretch that isn't a call c03 (hidden) and one between calls with a best bit, c04 (18-20 s, m03).
test("browse", async (t, st) => {
  const br = st.browse;
  t.eq("a recording's date comes from the OBS name", br.recordingTitle({ name: "2026-09-28 10-38-17.mkv" }), "Mon Sep 28, 10:38 AM");
  t.eq("lengths read in hours and minutes", br.fmtHours(14594), "4 h 03 m");
  const rec = await until(() => [...document.querySelectorAll(".bin-item.rec")].find((r) => r.title.includes("src20.mp4")));
  t.ok("the recording row says its calls", rec && /2 calls · 1 booked/.test(rec.textContent), rec && rec.textContent);
  rec.click();
  await until(() => br.isOpen() && document.querySelectorAll(".br-row").length === 4);
  const app = document.getElementById("app");
  const root = br.root();
  const vis = () => [...document.querySelectorAll(".br-row")].filter((r) => !r.hidden).map((r) => r.dataset.id);
  // the layout (B13): full height beside the timeline, wider
  const bin = document.getElementById("bin").getBoundingClientRect();
  const tl = document.getElementById("timeline").getBoundingClientRect();
  const mon = document.getElementById("monitor").getBoundingClientRect();
  t.ok("opening a recording gives the browsing layout", app.classList.contains("browsing"));
  t.near("the Media panel runs down beside the timeline", bin.bottom, tl.bottom, 2);
  t.near("and widens to 800 px", bin.width, 800, 2);
  t.near("the timeline starts at the viewer's column", tl.left, mon.left, 2);
  t.eq("only one video in the Media panel", document.querySelectorAll("#bin video").length, 1);
  // rows (B7, B8, B22)
  t.eq("calls and the between-calls stretch with a best bit show; the plain stretch is hidden", vis(), ["c01", "c02", "c04"]);
  const row = (id) => document.querySelector(`.br-row[data-id="${id}"]`);
  t.ok("a row: time, title, length, how it ended", /0:07/.test(row("c02").textContent) && /Dana, Fixture Electric/.test(row("c02").textContent)
    && /0:09/.test(row("c02").textContent) && /Booked/.test(row("c02").textContent), row("c02").textContent);
  t.ok("a stretch with a best bit is tagged Between calls", /Between calls/.test(row("c04").textContent));
  // viral potential (2026-10-02): the strongest best bit's stars and why it would work, on rows that have one
  const stars = (id) => row(id).querySelector(".br-stars").textContent, why = (id) => row(id).querySelector(".br-why");
  t.ok("a call with a best bit shows its stars (m01: 5)", stars("c01") === "★★★★★" && stars("c02") === "★★★" && stars("c04") === "★★★★",
    `${stars("c01")} ${stars("c02")} ${stars("c04")}`);
  t.ok("and why it would work as a short, on a second line", why("c01") && why("c01").textContent === "Fixture");
  const showHidden = () => [...document.querySelectorAll(".br-foot .link")][0];
  t.ok("the hidden one is offered", showHidden() && /Show 1 hidden/.test(showHidden().textContent));
  showHidden().click(); await wait(30);
  t.ok("Show hidden brings it back, dimmed", vis().includes("c03") && row("c03").classList.contains("is-hidden"));
  t.ok("a stretch with no best bit stays one line, no stars", !why("c03") && stars("c03") === "");
  showHidden().click(); await wait(30);
  t.eq("and hides it again", vis(), ["c01", "c02", "c04"]);
  // tags (B14)
  const chip = (label) => [...document.querySelectorAll(".br-tags .chip")].find((c) => c.textContent.startsWith(label));
  t.ok("tags with counts", chip("All") && /3/.test(chip("All").textContent) && chip("Booked") && chip("Gatekeeper") && chip("Between calls"));
  chip("Booked").click(); await wait(30);
  t.eq("a tag narrows the list", vis(), ["c02"]);
  chip("All").click(); await wait(30);
  // playing (B9): a click plays the call from its start
  const v = br.video();
  row("c02").click();
  await until(() => !v.paused && v.currentTime > 7.25, 5000);
  t.ok("a click plays the call from its start", !v.paused && v.currentTime >= 7.2 && v.currentTime < 9.5, `${v.paused} ${v.currentTime}`);
  t.ok("from the preview copy", (v.getAttribute("src") || "").endsWith("proxy.mp4"), v.getAttribute("src"));
  // the bin feed redraws often (prep, saves): the player must play on
  for (let i = 0; i < 4; i += 1) { st.emit("bin"); await wait(60); }
  t.ok("bin feed redraws don't stop the player or swap it", !v.paused && document.querySelectorAll("#bin video").length === 1 && br.video() === v);
  // captions on the picture (B17): Dana is a woman, so pink letters in the caption band
  await until(() => v.currentTime > 8.6, 4000);
  const cv = br.caps();
  const g = cv.getContext("2d");
  const band = g.getImageData(0, Math.round(cv.height * 0.62), cv.width, Math.round(cv.height * 0.14)).data;
  let ink = 0, pink = 0;
  for (let i = 0; i < band.length; i += 4) {
    if (band[i + 3] > 200) { ink += 1; if (band[i] > 200 && band[i + 1] < 140 && band[i + 2] > 110) pink += 1; }
  }
  t.ok("captions show on the player, in her color", ink > 200 && pink > 50, `ink ${ink} pink ${pink}`);
  // watched (B19) after about 3 s of play
  await until(() => row("c02").classList.contains("watched"), 5000);
  t.ok("a call counts as watched after a few seconds", row("c02").classList.contains("watched"));
  const sv = await st.api.get(`/api/asset/${t.asset("src20.mp4").id}/calls`);
  t.ok("and the server keeps it", sv.calls.find((r) => r.id === "c02").watched);
  t.ok("a call not played keeps its dot", !row("c01").classList.contains("watched"));
  // best-bit marks (B6)
  const mark = document.querySelector(".br-mark");
  t.eq("one best bit on this call's bar", document.querySelectorAll(".br-mark").length, 1);
  t.near("at its place on the bar", parseFloat(mark.style.left), ((8.0 - 7.2) / (16.5 - 7.2)) * 100, 0.2);
  mark.click(); await wait(40);
  t.ok("clicking it marks the bit (I and O)", br.state().inMark === 8 && br.state().outMark === 16, `${br.state().inMark} ${br.state().outMark}`);
  // keys (B9, B11, B12): sent to the calls view
  t.key("Space", root); await wait(80);
  t.ok("Space pauses", v.paused);
  t.key("Down", root);
  await until(() => br.state().cur && br.state().cur.id === "c04", 2000);
  t.ok("Down plays the next call shown", br.state().cur.id === "c04" && !v.paused);
  t.key("Up", root);
  await until(() => br.state().cur && br.state().cur.id === "c02", 2000);
  t.ok("Up goes back", br.state().cur.id === "c02");
  t.key("Space", root); await wait(60);
  v.currentTime = 9.0; await until(() => Math.abs(v.currentTime - 9.0) < 0.05 && !v.seeking, 2000);
  t.key("I", root);
  v.currentTime = 12.0; await until(() => Math.abs(v.currentTime - 12.0) < 0.05 && !v.seeking, 2000);
  t.key("O", root);
  t.ok("I and O mark a part", Math.abs(br.state().inMark - 9) < 0.05 && Math.abs(br.state().outMark - 12) < 0.05, `${br.state().inMark} ${br.state().outMark}`);
  t.ok("the timeline's marks are left alone", !st.S.doc || !st.S.doc.range || st.S.doc.range.in === null || st.S.doc.range.in === undefined);
  // it stops at the hang-up (B10)
  br.select("c01", { play: false });
  await wait(80);
  v.currentTime = 6.4; await until(() => !v.seeking, 2000);
  t.key("Space", root);
  await until(() => v.paused && v.currentTime > 7.0, 4000);
  t.ok("a call stops at its hang-up", v.paused && Math.abs(v.currentTime - 7.2) < 0.12, `${v.paused} ${v.currentTime}`);
  // speed (B18), remembered
  const speed = document.querySelector(".br-speed");
  speed.click(); await wait(20);
  t.ok("speed 1.5x", speed.textContent === "1.5x" && v.playbackRate === 1.5);
  // search (B14): "first call" is said in c02 and c04
  const box = document.querySelector(".br-search");
  box.value = "first call"; box.dispatchEvent(new Event("input", { bubbles: true }));
  await until(() => vis().length === 2, 3000);
  t.eq("search narrows to the calls where it was said", vis(), ["c02", "c04"]);
  t.ok("with a hit count", /1 hit/.test(row("c02").textContent));
  box.value = ""; box.dispatchEvent(new Event("input", { bubbles: true }));
  await until(() => vis().length === 3, 3000);
  // Make short (B12) from the part marked in c02
  br.select("c02", { play: false });
  await wait(60);
  v.currentTime = 9.0; await until(() => !v.seeking, 2000);
  t.key("I", root);
  v.currentTime = 12.0; await until(() => !v.seeking, 2000);
  t.key("O", root);
  document.querySelector(".br-make").click();
  await until(() => st.S.doc && st.S.doc.moment && st.S.doc.moment.call === "c02", 6000);
  const d = st.S.doc;
  const v1 = d && d.clips.find((c) => c.track === "V1");
  t.ok("Make short opens a short of the marked part", v1 && v1.in === 270 && v1.out === 360 && d.name === "Dana, Fixture Electric", JSON.stringify(v1));
  t.ok("the layout goes back to normal", !app.classList.contains("browsing") && !br.isOpen());
  t.ok("leaving empties the player", !v.getAttribute("src"));
  // back to the recording: the same call, now with its Short tag; speed remembered
  await until(() => [...document.querySelectorAll(".bin-item.short")].some((r) => /Dana/.test(r.textContent)), 5000);
  [...document.querySelectorAll(".bin-item.rec")].find((r) => r.title.includes("src20.mp4")).click();
  await until(() => br.isOpen() && row("c02"), 3000);
  await until(() => /Short/.test(row("c02").textContent), 3000);
  t.ok("the call shows a Short tag", /Short/.test(row("c02").textContent));
  t.ok("opening again comes back to that call", br.state().cur && br.state().cur.id === "c02");
  t.ok("speed remembered", document.querySelector(".br-speed").textContent === "1.5x");
  document.querySelector(".br-speed").click(); document.querySelector(".br-speed").click();
  // the back arrow
  document.querySelector(".br-head .icon-btn").click();
  await wait(60);
  t.ok("the back arrow puts the recordings back", !app.classList.contains("browsing") && document.querySelector(".bin-list") && !document.querySelector(".bin-list").hidden);
  t.ok("and empties the player", !br.video().getAttribute("src"));
  // low disk (B20): a note under 15 GB
  // (the bin feed can replace S.bin between the change and the redraw, so set it until the note shows)
  const note = await until(() => { st.S.bin.diskFreeGb = 9.5; st.emit("bin"); return document.querySelector(".bin-note"); }, 4000, 100);
  t.ok("a note when space runs low", note && /9.5 GB free/.test(note.textContent), note && note.textContent);
  const gone = await until(() => { st.S.bin.diskFreeGb = 40; st.emit("bin"); return !document.querySelector(".bin-note"); }, 4000, 100);
  t.ok("gone when there's room", gone);
});
