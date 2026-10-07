import { test, until, wait } from "./harness.js";

// An open window follows changes to a recording's words made elsewhere (another window, or words filled in on the
// server, 2026-09-30): the bin feed carries a transcript revision and the page fetches the words again, voices
// included, so words and voices never come from two different versions.
test("refresh", async (t, st) => {
  await t.fresh();
  const aid = t.asset("src20.mp4").id;
  const before = st.lib.transcript(aid);
  t.ok("the transcript arrives with its revision", !!before && !!before.trev);
  const patch = (edits) => fetch(`/api/asset/${aid}/transcript`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ edits }) });
  await patch({ 4: "ELSEWHERE" });           // "another window" (not through this page's own fix, which updates it at once)
  const got = await until(() => { const tr = st.lib.transcript(aid); return tr && tr.words[4][2] === "ELSEWHERE"; }, 10000);
  t.ok("a spelling fix made elsewhere reaches this window without a reload", !!got);
  const cap = await until(() => st.S.doc.captions.events.some((e) => e.words.some((w) => w.w === "ELSEWHERE")), 4000);
  t.ok("and its captions", !!cap);
  const tr = st.lib.transcript(aid);
  t.ok("words and voices come from the same version", tr.voices && tr.voices.spk && tr.voices.spk.length === tr.words.length);
  await patch({ 4: null });
  await until(() => { const x = st.lib.transcript(aid); return x && x.words[4][2] !== "ELSEWHERE"; }, 10000);
  // Studio updated while the window was open: the top bar offers a reload (2026-09-30)
  const chip = document.querySelector(".tb-update");
  t.ok("no update notice while nothing changed", chip && chip.hidden);
  st.S.version = "an-older-version";
  await patch({ 5: "PING" });                       // anything that wakes the bin feed
  const shown = await until(() => !document.querySelector(".tb-update").hidden, 10000);
  t.ok("a newer server version shows 'Update ready · Reload'", !!shown);
  await patch({ 5: null });
  // a short made before the voice tracks splits itself the first time it opens
  const legacy = JSON.parse(JSON.stringify(st.S.doc));
  legacy.tracks = legacy.tracks.filter((x) => x.id !== "A3").map((x) => { const y = Object.assign({}, x); delete y.voice; delete y.name; return y; });
  legacy.clips = legacy.clips.filter((c) => c.track !== "A2").map((c) => { const y = Object.assign({}, c); delete y.voice; return y; });
  legacy.id = "older-short-test"; legacy.name = "Older short";
  await st.api.saveProject("older-short-test", legacy, null);
  await st.openShort("older-short-test");
  await until(() => st.S.doc && st.S.doc.id === "older-short-test" && st.S.doc.tracks.some((x) => x.voice), 4000);
  t.ok("an older short opens split: You on A1, Them on A2", st.S.doc.tracks.find((x) => x.id === "A1").voice === "me"
    && st.S.doc.tracks.find((x) => x.id === "A2").voice === "them" && st.S.doc.clips.some((c) => c.track === "A2" && c.voice === "them"));
  st.history.undo(); await wait(20);
  t.ok("and Ctrl+Z puts the old layout back", !st.S.doc.tracks.some((x) => x.voice));
});
