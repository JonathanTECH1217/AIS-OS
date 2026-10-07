import { test, wait, until } from "./harness.js";

// Generate captions (2026-10-02, grill G1-G7 in brainstorms/2026-10-02-captions-after-trim.md). The fixtures' second
// listen (listen-fake.json under STUDIO_FAKE_LISTEN) hears "was" for "is" (word 2) and "ring" for "thing" (word 4),
// adds "really" (3.4 s, in Jonathan's pause) and "okay" (10.5 s, in Dana's), and misses word 8 ("the", 4.9 s). Claude
// is off in the tests, so the second listen wins where the two differ, except where a word was fixed by hand.
test("gencaptions", async (t, st) => {
  const aid = t.asset("src20.mp4").id;
  // only word 4 fixed by hand (t-captions leaves a fix of its own on word 2); the fixes as they were go back at the end
  const before = (await st.api.transcript(aid)).edits || {};
  await st.api.patch(`/api/asset/${aid}/transcript`, { edits: Object.assign(Object.fromEntries(Object.keys(before).map((k) => [k, null])), { 4: "things" }) });
  await st.lib.reloadTranscript(aid);
  const d = await t.fresh("m01", { captions: "generate" });
  t.eq("a new short starts with no captions (G1)", [d.captions.mode, st.S.doc.captions.events.length], ["generate", 0]);
  document.querySelectorAll(".tab")[1].click();
  await wait(40);
  const gen = () => document.querySelector(".cap-gen");
  t.ok("the Captions tab says there are none yet and offers Generate captions", /No captions yet/.test(gen().textContent) && !!gen().querySelector(".gen-btn"));
  t.ok("so does the Captions row on the timeline", !!document.querySelector(".tl-head .tl-tbtn.gen"));
  const item = st.actions.get("generateCaptions");
  t.ok("and the Clip menu", item && item.enabled() && item.label() === "Generate captions");
  t.ok("while trimming, the razor and trims still snap to the transcript's words",
    st.captions.wordsOnTimeline(st.S.doc, st.lib, { trim: true }).length > 5 && st.captions.wordsOnTimeline(st.S.doc, st.lib).length === 0);

  // the whole recording on the timeline, then Generate from the tab
  st.history.commit("Test span", (dd) => { for (const c of dd.clips) { c.in = 0; c.out = 600; } });
  await wait(60);
  gen().querySelector(".gen-btn").click();
  await until(() => st.S.genCaps && st.S.genCaps.state === "running", 2000);
  const busy = gen().textContent;
  t.ok("while it works, the tab says what it's doing", /Starting|Listening again|Claude/.test(busy), busy);
  await until(() => st.S.genCaps.state !== "running", 20000);
  t.eq("it finishes", st.S.genCaps.state, "done");
  await wait(60);
  const words = () => st.S.doc.captions.events.flatMap((e) => e.words);
  const has = (w) => words().some((x) => x.w === w);
  const kOf = (w) => (words().find((x) => x.w === w) || {}).k;
  t.ok("the captions come from the generated words", words().length > 30 && words().every((x) => x.gi !== undefined && x.id === null));
  t.ok("where the two listens differ, the second listen's reading (Claude off)", has("WAS") && !words().some((x) => x.w === "IS" && x.s < 60));
  t.ok("a word fixed by hand stays", has("THINGS") && !has("RING"));
  t.ok("words the first transcript missed are in", has("REALLY") && has("OKAY"));
  t.ok("a word the second listen didn't hear is out", !words().some((x) => x.s >= 146 && x.s < 160), JSON.stringify(words().filter((x) => x.s > 120 && x.s < 180).map((x) => [x.w, x.s])));
  t.eq("added words take their voice from the split: REALLY is Jonathan, OKAY is Dana", [kOf("REALLY"), kOf("OKAY")], ["me", "f"]);
  t.ok("no caption group mixes two voices", st.S.doc.captions.events.every((e) => e.words.every((w) => w.k === e.words[0].k)));
  const g = st.S.doc.captions.gen[aid];
  t.ok("the words are kept on the short, in the recording's seconds", g && g.ranges.length === 1 && g.ranges[0][0] === 0 && g.words.some((w) => w[2] === "really"));
  const tr = await st.api.transcript(aid);
  t.ok("the recording's transcript is left alone", !tr.words.some((w) => w[2] === "really"));
  t.ok("the tab says when they were made, with Generate again", /Captions made today/.test(gen().textContent) && /Generate again/.test(gen().textContent), gen().textContent);
  t.ok("the timeline's generate button goes once they're made", !document.querySelector(".tl-head .tl-tbtn.gen"));
  t.eq("the Clip menu item reads Generate captions again", item.label(), "Generate captions again");
  await until(() => st.S.saving === "saved" && !st.save.pending(), 4000);
  const disk = await st.api.project(st.S.doc.id);
  t.ok("they're saved with the short", disk.captions.mode === "generate" && disk.captions.gen && disk.captions.gen[aid].words.length === g.words.length);

  // undo and redo: one step
  st.history.undo(); await wait(60);
  t.eq("Undo takes them away again", st.S.doc.captions.events.length, 0);
  st.history.redo(); await wait(60);
  t.ok("Redo puts them back", has("REALLY"));

  // a word fix after Generate is saved on the short (G7)
  const spanOf = (w) => [...document.querySelectorAll(".cap-word")].find((s) => s._w.w === w);
  spanOf("REALLY").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
  await wait(20);
  const edt = document.querySelector(".cap-word[contenteditable='true']");
  edt.textContent = "truly";
  edt.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await until(() => has("TRULY"), 3000);
  t.ok("a word fixed after Generate shows at once", has("TRULY") && !has("REALLY"));
  const tr2 = await st.api.transcript(aid);
  t.ok("and is saved on this short, not on the recording (G7)", st.S.doc.captions.gen[aid].words.some((w) => w[2] === "truly")
    && !Object.values(tr2.edits || {}).includes("truly"));
  st.history.undo(); await wait(60);
  t.ok("Undo puts the word back", has("REALLY"));

  // who said it, on a generated word: saved on the short too
  const menuItem = (label) => [...document.querySelectorAll(".menu-item")].filter((b) => b.querySelector(".menu-label").textContent === label).pop();
  const pick = async (path) => {
    for (let i = 0; i < path.length; i += 1) {
      const it = menuItem(path[i]);
      if (!it) return false;
      if (i < path.length - 1) { it.dispatchEvent(new MouseEvent("mouseenter")); await wait(30); } else it.click();
    }
    await wait(40);
    return true;
  };
  const ctx = (span) => { const r = span.getBoundingClientRect(); span.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: r.left + 4, clientY: r.top + 4 })); };
  ctx(spanOf("OKAY")); await wait(30);
  await pick(["Said by", "You"]);
  await until(() => kOf("OKAY") === "me", 3000);
  t.eq("Said by on a generated word: blue, and kept on the short", [kOf("OKAY"), st.S.doc.captions.gen[aid].words.find((w) => w[2] === "okay")[5]], ["me", "me"]);
  ctx(spanOf("OKAY")); await wait(30);
  await pick(["Said by", "Reset to automatic"]);
  await until(() => kOf("OKAY") === "f", 3000);
  t.eq("Reset to automatic gives it Dana's voice back", kOf("OKAY"), "f");

  // the captions follow a cut (G3): ripple-delete the first second
  const n0 = words().length;
  st.pb.seek(30); t.key("Ctrl+K"); await wait(20);
  st.selectOnly(st.doc.withLinked(st.S.doc, [t.clip("V1")[0].id]));
  t.key("Shift+Delete"); await wait(60);
  const after = words();
  t.ok("captions follow a cut: the words in the deleted second go, the rest slide left (G3)", after.length < n0 && after[0].w === "HERE" && after[0].s === 0,
    JSON.stringify(after.slice(0, 3).map((x) => [x.w, x.s])));

  // footage added past what was generated: a note and Generate again
  await t.fresh("m01", { captions: "generate" });
  await wait(40);
  t.ok("Generate from the Clip menu", (await st.actions.run("generateCaptions")) === true);
  await wait(60);
  t.ok("only the kept part was heard (1 s each side)", JSON.stringify(st.S.doc.captions.gen[aid].ranges) === "[[0,8]]", JSON.stringify(st.S.doc.captions.gen[aid].ranges));
  st.history.commit("Test extend", (dd) => { for (const c of dd.clips) c.out = 450; });
  await wait(60);
  t.ok("a clip pulled past it: a note with Generate again", /added after the captions were made/.test(gen().textContent) && !!gen().querySelector(".gen-row.is-warn .gen-btn"), gen().textContent);
  t.ok("the timeline's generate button is back", !!document.querySelector(".tl-head .tl-tbtn.gen"));
  t.ok("the new footage has no captions yet", Math.max(...words().map((x) => x.s)) < 215, String(Math.max(...words().map((x) => x.s))));
  gen().querySelector(".gen-btn").click();
  await until(() => st.S.genCaps.state === "done" && st.S.doc.captions.gen[aid].ranges[0][1] >= 15, 15000);
  await wait(60);
  t.ok("Generate again captions it", has("OKAY") && !/added after/.test(gen().textContent));

  // export before Generate asks first (G5)
  const exp = async (button) => {
    const short = await t.fresh("m01", { captions: "generate" });
    st.actions.run("export");
    const dlg = await until(() => document.querySelector(".gen-ask"), 3000);
    const btns = dlg ? [...dlg.querySelectorAll(".actions .btn")].map((b) => b.textContent) : [];
    if (dlg) [...dlg.querySelectorAll(".actions .btn")].find((b) => b.textContent === button).click();
    const job = await until(() => (st.S.bin.exports || []).find((j) => j.project === short.id), 20000, 100);
    if (job && (job.state === "queued" || job.state === "running")) await st.api.post("/api/export/cancel", { id: job.id });
    return { dlg, btns, job };
  };
  let r = await exp("Generate and export");
  t.ok("Export asks first: Generate captions first? (G5)", r.dlg && /Generate captions first/.test(r.dlg.textContent));
  t.eq("with Export without captions and Generate and export", r.btns, ["Export without captions", "Generate and export"]);
  t.ok("Generate and export makes the captions, then queues the export", !!(st.S.doc.captions.gen && st.S.doc.captions.gen[aid]) && !!r.job);
  r = await exp("Export without captions");
  t.ok("Export without captions just exports", !!r.job && !st.S.doc.captions.gen);

  // an older short keeps its captions from the transcript; Generate replaces them (G4)
  await t.fresh();
  await wait(60);
  t.ok("an older short keeps its transcript captions (G4)", st.S.doc.captions.events.length > 0 && !st.S.doc.captions.mode && words().every((x) => x.gi === undefined));
  t.ok("with a quiet note and Generate captions", /straight from the first transcript/.test(gen().textContent) && !!gen().querySelector(".gen-btn"));
  st.actions.run("export");
  const j = await until(() => (st.S.bin.exports || []).find((x) => x.project === st.S.doc.id), 8000, 100);
  t.ok("its export doesn't ask", !document.querySelector(".gen-ask") && !!j);
  if (j && (j.state === "queued" || j.state === "running")) await st.api.post("/api/export/cancel", { id: j.id });
  t.ok("Generate captions on it", (await st.actions.run("generateCaptions")) === true);
  await wait(60);
  t.ok("replaces them with generated ones", st.S.doc.captions.mode === "generate" && words().length > 5 && words().every((x) => x.gi !== undefined) && has("WAS"));

  await st.api.patch(`/api/asset/${aid}/transcript`, { edits: Object.assign({ 4: null }, before) });
  await st.lib.reloadTranscript(aid);
});
