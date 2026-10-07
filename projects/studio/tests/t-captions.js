import { test, wait, until } from "./harness.js";

// The fixture's voices (tests/fixtures/make.py): words 0-11 Jonathan (split groups S1 and S4), 12-23 Dana (a woman,
// S2), 24-35 a man with no name ("Owner", S3). Colors from the palette every short uses (grill C1-C11, 2026-09-30).
const COLORS = {
  blue: (p) => p[0] > 40 && p[0] < 120 && p[1] > 95 && p[1] < 170 && p[2] > 200,
  white: (p) => p[0] > 225 && p[1] > 225 && p[2] > 225,
  pink: (p) => p[0] > 220 && p[1] > 60 && p[1] < 135 && p[2] > 125 && p[2] < 210,
  red: (p) => p[0] > 215 && p[1] < 95 && p[2] < 85,
  yellow: (p) => p[0] > 215 && p[1] > 175 && p[2] < 90,
  green: (p) => p[0] < 90 && p[1] > 200 && p[2] < 90,
};

test("captions", async (t, st) => {
  await t.fresh();
  const aid = t.asset("src20.mp4").id;
  // the whole 20 s clip, so all three voices are on the timeline
  st.history.commit("Test span", (d) => { for (const c of d.clips) { c.in = 0; c.out = 600; } });
  await until(() => st.S.doc.captions.events.some((e) => e.words.some((w) => w.id === 30)), 4000);
  const ev = st.S.doc.captions.events;
  t.ok("captions are built from the transcript under A1 (G21)", ev.length > 0);
  t.ok("every group has 1 to 4 words", ev.every((e) => e.words.length >= 1 && e.words.length <= 4));
  t.ok("most groups have 2+ words (G18)", ev.filter((e) => e.words.length >= 2).length >= ev.length * 0.6);
  t.ok("UPPERCASE by default", ev.every((e) => e.words.every((w) => w.w === w.w.toUpperCase())));
  t.ok("each group fits in 900 px", ev.every((e) => { const xs = e.words.map((w) => w.x); return Math.max(...xs) - Math.min(...xs) < 900; }));
  t.ok("groups are centered on the frame", ev.every((e) => { const xs = e.words.map((w) => w.x); return Math.abs((Math.max(...xs) + Math.min(...xs)) / 2 - 540) < 200; }));
  const cfg = st.S.doc.captions;
  t.ok("default height is inside the safe zone (G40)", cfg.y - cfg.size / 2 > 220 && cfg.y + cfg.size / 2 < 1920 - 480, String(cfg.y));

  // voices
  const k = (id) => { for (const e of st.S.doc.captions.events) for (const w of e.words) if (w.id === id) return w.k; return null; };
  const groupOf = (id) => st.S.doc.captions.events.find((e) => e.words.some((w) => w.id === id));
  t.eq("each word carries its voice: Jonathan, Dana, the owner", [k(1), k(11), k(12), k(23), k(24), k(30)], ["me", "me", "f", "f", "m", "m"]);
  t.ok("no caption group mixes two voices", st.S.doc.captions.events.every((e) => e.words.every((w) => w.k === e.words[0].k)));
  t.ok("a group breaks where the voice changes", !groupOf(23).words.some((w) => w.id === 24) && !groupOf(11).words.some((w) => w.id === 12));
  t.ok("Jonathan's two split groups read as one voice (no break between them)", groupOf(3).words.some((w) => w.id === 2), JSON.stringify(groupOf(3).words.map((w) => w.id)));

  // the monitor draws each voice in its colors
  const box = (w) => {
    const cv = document.querySelector(".mon-program");
    const s = cv.width / 1080;
    return cv.getContext("2d").getImageData(Math.round((w.x - 22) * s), Math.round((cfg.y - 28) * s), Math.round(44 * s), Math.round(56 * s)).data;
  };
  const count = (data, test) => { let n = 0; for (let i = 0; i < data.length; i += 4) if (test([data[i], data[i + 1], data[i + 2]])) n += 1; return n; };
  const litCheck = async (litId, _unused, litColor, otherColor, who) => {
    const g = groupOf(litId);
    const lit = g.words.find((w) => w.id === litId), other = g.words.find((w) => w.id !== litId);
    st.pb.seek(lit.s + 2); await t.settle();
    const a = count(box(lit), COLORS[litColor]), b = count(box(other), COLORS[otherColor]);
    t.ok(`${who}: the spoken word is ${litColor}`, a > 15, `${a} px`);
    t.ok(`${who}: the other words are ${otherColor}`, b > 15, `${b} px`);
  };
  await litCheck(1, 2, "white", "blue", "Jonathan");
  // their spoken word is white too since 2026-09-30 ("It looks better"); it was yellow
  await litCheck(13, 14, "white", "pink", "Dana");
  await litCheck(25, 26, "white", "red", "the owner");

  // the Captions tab: palette, voices, words
  document.querySelectorAll(".tab")[1].click();
  await wait(40);
  t.eq("the old per-short highlight picker is gone", document.querySelectorAll(".cap-controls .swatch").length, 0);
  t.eq("five palette colors (every short)", document.querySelectorAll(".cap-color-grid input[type=color]").length, 5);
  const names = () => [...document.querySelectorAll(".voice-row .voice-name")].map((x) => x.textContent);
  t.eq("voices in this short: You, then Dana, then the owner by role", names(), ["You", "Dana", "Owner"]);
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
  const rowBtn = (name) => [...document.querySelectorAll(".voice-row")].find((r) => r.querySelector(".voice-name").textContent === name).querySelector("button");

  // flip Dana to a man, then back
  rowBtn("Dana").click(); await wait(30);
  t.ok("a voice's menu offers me / woman / man / same person / reset", ["This is me", "Woman", "Man", "Same person as", "Reset to automatic"].every((l) => menuItem(l)));
  await pick(["Man"]);
  await until(() => k(14) === "m", 4000);
  t.eq("Dana flipped to a man: her words turn red", k(14), "m");
  const g14 = groupOf(14);
  st.pb.seek(g14.words[0].s + 2); await t.settle();
  t.ok("and the monitor draws them red", count(box(g14.words[1]), COLORS.red) > 15);
  const ed = await st.api.get(`/api/asset/${aid}/voices`);
  t.eq("the fix is saved on the recording (every short from it follows)", ed.speakers.find((v) => v.name === "Dana").source, "you");
  rowBtn("Dana").click(); await wait(30);
  await pick(["Reset to automatic"]);
  await until(() => k(14) === "f", 4000);
  t.eq("reset to automatic: Claude's label again", k(14), "f");

  // the owner is the same person as Dana
  rowBtn("Owner").click(); await wait(30);
  await pick(["Same person as", "Dana"]);
  await until(() => k(26) === "f", 4000);
  t.eq("'same person as' joins the owner to Dana (her color)", k(26), "f");
  t.ok("and the two become one row", !names().includes("Owner"), names().join(","));
  rowBtn("Dana").click(); await wait(30);
  await pick(["Reset to automatic"]);
  // the owner's own merge sits on the owner's group: reset it from one of its words
  let spanOf = (id) => [...document.querySelectorAll(".cap-word")].find((s) => s._w.id === id);
  const ctx = (span) => { const r = span.getBoundingClientRect(); span.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: r.left + 4, clientY: r.top + 4 })); };
  ctx(spanOf(26)); await wait(30);
  await pick(["This whole voice is", "A man"]);
  await until(() => k(26) === "m", 4000);
  t.eq("'this whole voice is a man' from a word splits the owner back out", k(26), "m");

  // words: select two, say who said them
  spanOf = (id) => [...document.querySelectorAll(".cap-word")].find((s) => s._w.id === id);
  spanOf(12).click(); await wait(20);
  spanOf(13).dispatchEvent(new MouseEvent("click", { bubbles: true, shiftKey: true })); await wait(20);
  t.eq("Shift+click selects a run of words", document.querySelectorAll(".cap-word.is-sel").length, 2);
  ctx(spanOf(13)); await wait(30);
  const said = menuItem("Said by");
  said.dispatchEvent(new MouseEvent("mouseenter")); await wait(30);
  const sub = document.querySelector(".menu.sub");
  t.ok("the sub-menu stays inside the window (the tab is the rightmost column)", sub && sub.getBoundingClientRect().right <= innerWidth + 1 && sub.getBoundingClientRect().left >= 0,
    sub ? JSON.stringify(sub.getBoundingClientRect()) : "no sub");
  await pick(["Said by", "You"]);
  await until(() => k(12) === "me" && k(13) === "me", 4000);
  t.eq("'said by You' moves the selected words to Jonathan", [k(12), k(13), k(14)], ["me", "me", "f"]);
  t.ok("and the caption group breaks at the new edge", !groupOf(13).words.some((w) => w.id === 14));
  ctx(spanOf(12)); await wait(30);
  await pick(["Said by", "New voice (man)"]);
  await until(() => k(12) === "m" && k(13) === "m", 4000);
  t.ok("a new voice (man) takes the selected words", names().includes("New voice 1"), names().join(","));
  ctx(spanOf(12)); await wait(30);
  await pick(["Said by", "Reset to automatic"]);
  await until(() => k(12) === "f" && k(13) === "f", 4000);
  t.eq("reset to automatic puts the words back with Dana", [k(12), k(13)], ["f", "f"]);

  // the palette: every short, saved on the server, repaints at once
  const manInput = document.querySelector('.cap-color-grid input[data-key="man"]');
  manInput.value = "#00ff00";
  manInput.dispatchEvent(new Event("input", { bubbles: true }));
  manInput.dispatchEvent(new Event("change", { bubbles: true }));
  await until(async () => (await st.api.get("/api/config")).captionColors.man === "#00FF00", 4000);
  t.eq("a palette color is saved for every short", (await st.api.get("/api/config")).captionColors.man, "#00FF00");
  const g26 = groupOf(26);
  st.pb.seek(g26.words[0].s + 2); await t.settle();
  t.ok("the monitor repaints men's words in the new color", count(box(g26.words[1]), COLORS.green) > 15);
  [...document.querySelectorAll(".cap-colors .link")].find((b) => b.textContent === "Reset colors").click();
  await until(async () => (await st.api.get("/api/config")).captionColors.man === "#FF3B30", 4000);
  t.eq("Reset colors: back to red", (await st.api.get("/api/config")).captionColors.man, "#FF3B30");

  // the word list: click jumps, the playing word lights up, spelling fixes
  const spans = [...document.querySelectorAll(".cap-word")];
  t.ok("the Captions tab lists the words", spans.length >= 10);
  t.ok("each word is listed in its voice's color", spans[1].style.color && spans[20].style.color && spans[1].style.color !== spans[20].style.color);
  spans[5].click(); await wait(30);
  t.eq("clicking a word jumps to it", Math.round(st.S.playhead), spans[5]._w.s);
  t.ok("the playing word is lit", spans[5].classList.contains("is-active"));
  spans[2].dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
  await wait(20);
  const edt = document.querySelector(".cap-word[contenteditable='true']");
  edt.textContent = "LEADS";
  edt.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await until(() => st.S.doc.captions.events.some((e) => e.words.some((w) => w.w === "LEADS")), 4000);
  t.ok("a fixed word shows in the captions", st.S.doc.captions.events.some((e) => e.words.some((w) => w.w === "LEADS")));
  const tr = await st.api.transcript(aid);
  t.ok("and is saved on the recording's transcript", Object.values(tr.edits || {}).includes("LEADS"));
  const up = [...document.querySelectorAll(".cap-controls .switch input")][1];
  up.click(); await wait(40);
  t.ok("UPPERCASE can be turned off", !st.S.doc.captions.upper);
  up.click(); await wait(40);

  // captions follow a cut: ripple-delete the first second, the words in it go and the rest move left
  const nBefore = st.captions.wordsOnTimeline(st.S.doc, st.lib).length;
  const firstWord = st.captions.wordsOnTimeline(st.S.doc, st.lib)[0];
  st.pb.seek(30); t.key("Ctrl+K"); await wait(20);
  st.selectOnly(st.doc.withLinked(st.S.doc, [t.clip("V1")[0].id]));
  t.key("Shift+Delete"); await wait(40);
  const after = st.captions.wordsOnTimeline(st.S.doc, st.lib);
  t.ok("words under a deleted stretch drop out (G21)", after.length < nBefore, `${nBefore} -> ${after.length}`);
  t.ok("the rest slide left with the video", after[0].s < 30 && after[0].id !== firstWord.id, JSON.stringify(after[0]));
  t.ok("and keep their voices", after.every((w) => w.k === (w.id <= 11 ? "me" : w.id <= 23 ? "f" : "m")));
  document.querySelector(".cap-controls .switch input").click(); await wait(30);
  t.eq("captions can be switched off", st.S.doc.captions.on, false);

  // leave the recording as the other tests expect it
  await st.api.patch(`/api/asset/${aid}/speakers`, { groups: { S2: null, S3: null }, merge: { S2: null, S3: null } });
});
