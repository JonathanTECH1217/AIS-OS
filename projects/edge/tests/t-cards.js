// Monarc Edge page test: the Today tab's cards in plain words. Fakes fetch with tests/fixtures/state-cards.json (three
// fixtures, nine cards), boots the page, and checks the bet words, the two big numbers, the gap chip words, the money
// line, the flag words, the math fold, the buttons, the Approve flow (200 and 409), folding, and the New York time.
// Writes PASS / FAIL lines and DONE into <pre id="__out"> for tests/page-check.py.
const out = document.getElementById("__out");
const log = (l) => { out.textContent += l + "\n"; };
const ok = (name, cond, detail = "") => { log(cond ? `PASS ${name}` : `FAIL ${name} ${detail}`); return !!cond; };
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const until = async (fn, ms = 3000) => { const t0 = performance.now(); for (;;) { let v = null; try { v = fn(); } catch (e) { v = null; } if (v) return v; if (performance.now() - t0 > ms) return null; await wait(30); } };
const realFetch = window.fetch.bind(window);
const json = (body, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
const clone = (o) => JSON.parse(JSON.stringify(o));
const card = (sel) => document.querySelector(`.card[data-id="${sel}"]`);
const text = (node, sel) => { const n = node && node.querySelector(sel); return n ? n.textContent : null; };
// the words only: the icon font is a ligature, so an icon's name sits in textContent ("warning", "check")
const plain = (n) => (n ? [...n.childNodes].map((x) => (x.nodeType === 3 ? x.textContent : x.classList && x.classList.contains("ms") ? "" : plain(x))).join("") : "");
const bigs = (node) => [...node.querySelectorAll(".bignum b")].map((b) => b.textContent).join(",");
const cssColor = (name) => { const s = document.createElement("span"); s.style.color = `var(${name})`; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; };

try {
  const bundle = await (await realFetch("tests/fixtures/state-cards.json")).json();
  const calls = [];
  window.fetch = (url, opts = {}) => {
    const u = String(url), m = (opts.method || "GET").toUpperCase();
    calls.push(`${m} ${u}`);
    if (u.startsWith("/api/state")) return json(bundle);
    if (u === "/api/record") return json(bundle.record);
    if (u === "/api/tick" && m === "POST") return json({ ran: true, took_ms: 12, did: [] });
    let mm = /^\/api\/cards\/([^/]+)\/approve$/.exec(u);
    if (mm && m === "POST") {
      const id = decodeURIComponent(mm[1]);
      const c = bundle.cards.find((x) => x.id === id);
      if (id === "c-ars-away") return json({ ...c, state: "placed", can_approve: false, order_id: "ord-2210", approved_at: bundle.now });
      return json({ errors: ["The gap fell to 5.1 points, under the 7.0 floor."], card: { ...c, state: "watching", can_approve: false, gap_points: 5.1, color: "amber" } }, 409);
    }
    mm = /^\/api\/cards\/([^/]+)\/(pass|cancel)$/.exec(u);
    if (mm && m === "POST") { const c = bundle.cards.find((x) => x.id === decodeURIComponent(mm[1])); return json({ ...c, state: mm[2] === "pass" ? "passed" : "unfilled", can_approve: false }); }
    return json({ errors: [`no fake for ${m} ${u}`] }, 404);
  };

  await window.__edge.boot();
  window.__edge.go("today");

  // light theme
  ok("page is light", getComputedStyle(document.body).backgroundColor === "rgb(248, 249, 250)", getComputedStyle(document.body).backgroundColor);
  ok("cards are white with a border", getComputedStyle(card("c-ars-away")).backgroundColor === "rgb(255, 255, 255)" && getComputedStyle(card("c-ars-away")).borderTopWidth === "1px");
  ok("nine cards drawn", document.querySelectorAll(".card").length === 9, String(document.querySelectorAll(".card").length));
  ok("three fixture headings", document.querySelectorAll(".fixture").length === 3);
  const ready = card("c-ars-away"), red = card("c-nfo-home"), amber = card("c-nfo-draw");

  // the bet in words
  ok("Yes on a team", text(ready, ".card-title") === "Bet: Arsenal wins", text(ready, ".card-title"));
  ok("No on the draw", text(amber, ".card-title") === "Bet: it does not end in a draw", text(amber, ".card-title"));
  ok("no side is a plain label", text(red, ".card-title") === "Nottingham Forest wins", text(red, ".card-title"));
  ok("Yes on the draw", text(card("c-bre-draw"), ".card-title") === "Bet: it ends in a draw");

  // state chips in words
  ok("ready chip", text(ready, ".chip-status") === "Ready to bet");
  ok("watching chip", text(amber, ".chip-status") === "Watching");
  ok("no edge chip", text(red, ".chip-status") === "No bet");
  ok("busy-failed chip", text(card("c-mci-away"), ".chip-status") === "No bet");
  ok("placed chip", text(card("c-bre-draw"), ".chip-status") === "Bet placed, waiting");
  ok("paper filled chip", text(card("c-bre-home"), ".chip-status") === "Paper bet on", text(card("c-bre-home"), ".chip-status"));
  ok("won chip", text(card("c-liv-away"), ".chip-status") === "Won");
  ok("lost chip", text(card("c-eve-draw"), ".chip-status") === "Lost");
  ok("won chip is green", getComputedStyle(card("c-liv-away").querySelector(".chip-status")).color === cssColor("--up"));
  ok("lost chip is red", getComputedStyle(card("c-eve-draw").querySelector(".chip-status")).color === cssColor("--down"));
  ok("expired chip", text(card("c-eve-home"), ".chip-status") === "Missed (kickoff passed)");

  // the two big numbers, out of 100
  ok("ready card numbers 38 and 26", bigs(ready) === "38,26", bigs(ready));
  ok("No-side numbers flip to the No price", bigs(amber) === "76,71", bigs(amber));
  ok("red card numbers", bigs(red) === "36,44", bigs(red));
  ok("labels say We think and Kalshi's price says", /We think/.test(ready.textContent) && /Kalshi's price says/.test(ready.textContent) && (ready.textContent.match(/out of 100/g) || []).length === 2);

  // the gap chip in words
  const gapUp = ready.querySelector(".gap");
  ok("green gap chip has the up class", gapUp.classList.contains("up"));
  ok("green gap chip is painted --up", getComputedStyle(gapUp).color === cssColor("--up"), getComputedStyle(gapUp).color);
  ok("green gap words", text(gapUp, "b") === "11 points in our favor" && /after Kalshi's fee/.test(gapUp.textContent), gapUp.textContent);
  const gapWarn = amber.querySelector(".gap");
  ok("amber gap chip has the warn class", gapWarn.classList.contains("warn"));
  ok("amber gap words", text(gapWarn, "b") === "3 points short" && /we need 7/.test(gapWarn.textContent), gapWarn.textContent);
  const gapDown = red.querySelector(".gap");
  ok("red gap chip has the down class", gapDown.classList.contains("down"));
  ok("red gap chip is painted --down", getComputedStyle(gapDown).color === cssColor("--down"));
  ok("red gap words", text(gapDown, "b") === "Not in our favor" && /Kalshi's price is better than ours/.test(gapDown.textContent), gapDown.textContent);

  // money line, Why, flags
  ok("money line", text(ready, ".money") === "Paper: risk $71 to win $188", text(ready, ".money"));
  ok("settled card shows the result", /Won \$60\.58/.test(text(card("c-liv-away"), ".money")) && /Lost \$64\.96/.test(text(card("c-eve-draw"), ".money")), text(card("c-liv-away"), ".money"));
  ok("Why label and the reasoning", text(ready, ".why .lbl") === "Why" && /Arsenal have won eight/.test(text(ready, ".reasoning")));
  const flagWords = [...ready.querySelectorAll(".flags .chip")].map((x) => plain(x).trim());
  ok("flags in plain words", flagWords.join("|") === "Polymarket agrees with Kalshi, not with us|Lineups not out yet", flagWords.join("|"));
  ok("thin market flag in words", [...card("c-mci-away").querySelectorAll(".flags .chip")].some((x) => plain(x).trim() === "Too few people trading this"));
  ok("lineups posted in words", [...card("c-liv-away").querySelectorAll(".flags .chip")].some((x) => plain(x).trim() === "Lineups are out"));
  const iconsOn = await until(() => document.documentElement.classList.contains("icons-ready"), 6000);
  ok("icons render as glyphs", !!iconsOn && ready.querySelector(".flags .ms").getBoundingClientRect().width <= 22, `ready=${!!iconsOn} width=${ready.querySelector(".flags .ms").getBoundingClientRect().width}`);
  ok("unknown flags pass through", window.__edge.fmt.flagWords("key player out: Saka", []) === "key player out: Saka" && window.__edge.fmt.flagWords("expired at kickoff", []) === null
    && window.__edge.fmt.flagWords("larger edge on Arsenal", []) === "Better bet on Arsenal in this match" && window.__edge.fmt.flagWords("reasoning failed: timeout", []) === "No note yet"
    && window.__edge.fmt.flagWords("no lineup feed", ["no lineups"]) === null && window.__edge.fmt.flagWords("no lineup feed", []) === "Lineups not out yet");

  // the math fold
  const math = ready.querySelector("details.math");
  ok("math fold closed by default", math && !math.open && /Show the math/.test(math.querySelector("summary").textContent));
  ok("math holds the trader line", /Our chance38%/.test(text(math, ".nums")) && /Break-even27\.3%/.test(text(math, ".nums")) && /Stake\$67\.40 = 259 at 0\.26/.test(text(math, ".nums")), text(math, ".nums"));
  ok("math holds the sources", /football-data\.co\.uk E0 2024\/25 to 2026\/27; Kalshi KXEPLGAME; Polymarket/.test(text(math, ".sources")));
  math.querySelector("summary").click();
  ok("math opens on click", !!(await until(() => math.open && /Hide the math/.test(math.querySelector("summary").textContent))));
  math.querySelector("summary").click();
  ok("math closes again", !!(await until(() => !math.open && /Show the math/.test(math.querySelector("summary").textContent))));

  // buttons
  ok("Approve only on the ready card", document.querySelectorAll(".btn-approve").length === 1 && !!ready.querySelector(".btn-approve"), String(document.querySelectorAll(".btn-approve").length));
  ok("Approve reads Yes, paper bet under paper money", plain(ready.querySelector(".btn-approve")).trim() === "Yes, paper bet", text(ready, ".btn-approve"));
  ok("Pass reads Skip", text(ready, ".btn-pass") === "Skip");
  ok("placed card has Cancel bet", text(card("c-bre-draw"), ".btn-cancel") === "Cancel bet");
  ok("busy-failed card has no Approve", !card("c-mci-away").querySelector(".btn-approve"));

  // folding: red and amber fold to the title, the chip, the two numbers and the gap chip
  ok("red card starts folded", !red.querySelector(".card-more") && !!red.querySelector(".fold") && bigs(red) === "36,44");
  ok("amber card starts folded", !amber.querySelector(".card-more"));
  ok("green card starts open", !!ready.querySelector(".card-more") && !ready.querySelector(".fold"));
  red.querySelector(".fold").click();
  const redOpen = await until(() => card("c-nfo-home").querySelector(".card-more"));
  ok("red card unfolds on the chevron", !!redOpen);
  ok("unfolded red card shows the no-note words", redOpen && /No note yet/.test(redOpen.textContent));
  card("c-nfo-home").querySelector(".fold").click();
  ok("red card folds again", !!(await until(() => !card("c-nfo-home").querySelector(".card-more") && card("c-nfo-home"))));

  // the fixture heading in New York time and plain words
  const head = ready.closest(".fixture").querySelector(".fx-head");
  ok("fixture heading names the match", head.querySelector("h2").textContent === "Nottingham Forest vs Arsenal");
  ok("kickoff shows as Sun 2:30 PM New York", /Sun 2:30 PM/.test(head.textContent), head.textContent);
  ok("hours-to-kickoff in words", /in 20 hours/.test(head.textContent), head.textContent);
  ok("price source in words", /Prices from Kalshi and Polymarket/.test(head.textContent));
  const overChips = [...card("c-liv-away").closest(".fixture").querySelectorAll(".fx-head .chip")].map((x) => plain(x).trim());
  ok("a finished match reads over", overChips.includes("over"), overChips.join("|"));
  ok("fixture with a ready card comes first", document.querySelector(".fixture").dataset.fixture === "fx-1");
  ok("cards sorted by gap inside the fixture", [...head.parentElement.querySelectorAll(".card")].map((x) => x.dataset.id).join(",") === "c-ars-away,c-nfo-draw,c-nfo-home");
  ok("fmtUntil words", window.__edge.fmt.fmtUntil("2026-10-16T22:30:00Z", bundle.now) === "in 6 days" && window.__edge.fmt.fmtUntil("2026-10-10T23:15:00Z", bundle.now) === "in 45 minutes" && window.__edge.fmt.fmtUntil("2026-10-10T22:00:00Z", bundle.now) === "started",
    [window.__edge.fmt.fmtUntil("2026-10-16T22:30:00Z", bundle.now), window.__edge.fmt.fmtUntil("2026-10-10T23:15:00Z", bundle.now)].join(","));

  // approve: 200 answers a placed card
  ready.querySelector(".btn-approve").click();
  const placed = await until(() => { const c = card("c-ars-away"); return c && text(c, ".chip-status") === "Bet placed, waiting" && c; });
  ok("Approve redraws the card as placed", !!placed);
  ok("placed card got a Cancel bet button", placed && text(placed, ".btn-cancel") === "Cancel bet");
  ok("placed card lost its Approve button", placed && !placed.querySelector(".btn-approve"));
  ok("approve was posted", calls.includes("POST /api/cards/c-ars-away/approve"), calls.join(" | "));

  // approve: a 409 on another card shows the errors inline and redraws from the body's card
  const st = window.__edge.state;
  const draw = st.bundle.cards.find((x) => x.id === "c-nfo-draw");
  draw.state = "ready"; draw.can_approve = true; draw.color = "green";
  window.__edge.render();
  const drawCard = card("c-nfo-draw");
  ok("second card now shows Approve", drawCard && !!drawCard.querySelector(".btn-approve"));
  drawCard.querySelector(".btn-approve").click();
  const errBox = await until(() => { const c = card("c-nfo-draw"); return c && c.querySelector(".card-errors"); });
  ok("409 shows the error inline", !!errBox && /under the 7\.0 floor/.test(errBox.textContent), errBox && errBox.textContent);
  ok("409 error is painted --warn", errBox && getComputedStyle(errBox).color === cssColor("--warn"));
  ok("409 redraws the card from the body", text(card("c-nfo-draw"), ".chip-status") === "Watching" && !card("c-nfo-draw").querySelector(".btn-approve"));
  ok("409 card gap words updated", text(card("c-nfo-draw"), ".gap b") === "2 points short", text(card("c-nfo-draw"), ".gap b"));

  // side panel in words
  const side = document.getElementById("side");
  ok("gate heading in words", /Before auto mode can turn on/.test(side.textContent));
  ok("bets settled line", /Bets settled: 37 of 200/.test(side.textContent));
  ok("guesses match line", /Our guesses match results: no, the 30 to 40 band is off/.test(side.textContent), side.textContent.slice(0, 300));
  ok("money made line", /Money made after fees: -\$12\.40/.test(side.textContent));
  ok("closing price line", /Beat the closing price: \+1\.2 points, need 5/.test(side.textContent));
  ok("lock line", /Auto mode stays off until all four are green/.test(side.textContent));
  ok("paper money panel", /Paper money/.test(side.textContent) && /\$987\.60/.test(side.textContent) && /Best so far/.test(side.textContent));
  ok("Kalshi account rows", /Kalshi account \(DEMO\)/.test(side.textContent) && /\$1,000\.00/.test(side.textContent) && /Open positions/.test(side.textContent));
  ok("checks panel", /Checks/.test(side.textContent) && /Last market check/.test(side.textContent) && /Polymarket.*working/s.test(side.textContent));
  ok("could not match lists the raw names", /Could not match/.test(side.textContent) && /Wolves \/ Brighton & Hove Albion/.test(side.textContent));
  const tb = document.getElementById("topbar").textContent;
  ok("top bar balance says Paper and counts open bets at cost (equity, not cash)", /Paper \$1,012\.30/.test(tb), tb);
  ok("top bar football calls", /Football calls left: 6,120/.test(tb));
  ok("top bar badges", /Practice account/.test(tb) && /You approve each bet/.test(tb) && /Paper money/.test(tb), tb);
  ok("no sideways scroll", document.documentElement.scrollWidth <= window.innerWidth, `${document.documentElement.scrollWidth} > ${window.innerWidth}`);

  // no account key: the paper-only line
  st.bundle.account = null;
  window.__edge.render();
  ok("no account key line", /No Kalshi account key: paper only\./.test(document.getElementById("side").textContent));

  // empty state
  st.bundle.cards = [];
  window.__edge.render();
  ok("empty state words", /No Premier League markets priced yet/.test(document.getElementById("cards").textContent));
  st.bundle.cards = clone(bundle.cards);
  window.__edge.render();
} catch (e) {
  ok("exception", false, (e && (e.stack || e.message)) || String(e));
}
log("DONE");
