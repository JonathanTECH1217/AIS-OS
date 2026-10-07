// Monarc Edge page test: the Record tab. Fakes fetch with tests/fixtures/state-record.json (count red, calibration
// green, profit red, CLV grey), opens Record, and checks the four lights, the band tables, the SVG and the ledger.
const out = document.getElementById("__out");
const log = (l) => { out.textContent += l + "\n"; };
const ok = (name, cond, detail = "") => { log(cond ? `PASS ${name}` : `FAIL ${name} ${detail}`); return !!cond; };
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const until = async (fn, ms = 3000) => { const t0 = performance.now(); for (;;) { let v = null; try { v = fn(); } catch (e) { v = null; } if (v) return v; if (performance.now() - t0 > ms) return null; await wait(30); } };
const realFetch = window.fetch.bind(window);
const json = (body, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
const cssColor = (name) => { const s = document.createElement("span"); s.style.color = `var(${name})`; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; };

try {
  const bundle = await (await realFetch("tests/fixtures/state-record.json")).json();
  const full = bundle.record;
  const summary = { ...full }; delete summary.equity; delete summary.ledger; delete summary.market_bands;
  const state = { ...bundle, record: summary };
  const calls = [];
  window.fetch = (url, opts = {}) => {
    const u = String(url), m = (opts.method || "GET").toUpperCase();
    calls.push(`${m} ${u}`);
    if (u.startsWith("/api/state")) return json(state);
    if (u === "/api/record") return json(full);
    return json({ errors: [`no fake for ${m} ${u}`] }, 404);
  };

  await window.__edge.boot();
  window.__edge.go("record");
  const ledger = await until(() => document.querySelector(".ledger-tbl tbody tr td:not(.muted)") && document.querySelector(".ledger-tbl"));
  ok("record was fetched in full", calls.includes("GET /api/record"));

  const lights = [...document.querySelectorAll(".gate-card")];
  ok("four gate cards", lights.length === 4, String(lights.length));
  const light = (k) => document.querySelector(`.gate-card[data-light="${k}"]`);
  ok("count light red", light("count").classList.contains("down"));
  ok("calibration light green", light("calibration").classList.contains("up"));
  ok("profit light red", light("profit").classList.contains("down"));
  ok("clv light grey", light("clv").classList.contains("muted"));
  ok("count light border is --down", getComputedStyle(light("count")).borderLeftColor === cssColor("--down"), getComputedStyle(light("count")).borderLeftColor);
  ok("calibration light border is --up", getComputedStyle(light("calibration")).borderLeftColor === cssColor("--up"));
  ok("clv light border is the grey outline", getComputedStyle(light("clv")).borderLeftColor === cssColor("--outline-variant"), getComputedStyle(light("clv")).borderLeftColor);
  ok("count reading", /37 settled cards\. 163 to go\./.test(light("count").textContent), light("count").textContent);
  ok("calibration reading", /Every band with 30 or more cards is within 5 points\./.test(light("calibration").textContent), light("calibration").textContent);
  ok("profit reading", /Return after fees: -\$12\.40 on \$1,240 staked \(-1\.0%\)\./.test(light("profit").textContent), light("profit").textContent);
  ok("clv reading when empty", /No closing lines yet; 5 points needed\./.test(light("clv").textContent), light("clv").textContent);

  const bandRows = document.querySelectorAll(".bands-tbl tbody tr");
  ok("our bands table rows", bandRows.length === full.bands.length, `${bandRows.length} vs ${full.bands.length}`);
  ok("band row reads 30 to 40 with 31 bets", /30 to 40/.test(bandRows[1].textContent) && /31/.test(bandRows[1].textContent), bandRows[1].textContent);
  ok("gate cards carry the plain titles", [...lights].map((x) => x.querySelector(".lbl").textContent).join("|") === "Bets settled|Our guesses match results|Money made after fees|Beat the closing price",
    [...lights].map((x) => x.querySelector(".lbl").textContent).join("|"));
  ok("table headings in plain words", /Do our guesses come true as often as we say\?/.test(document.getElementById("bands").textContent) && /Does Kalshi's price come true as often as it says\?/.test(document.body.textContent));
  ok("page is light", getComputedStyle(document.body).backgroundColor === "rgb(248, 249, 250)");
  ok("band row has a Wilson range", /24% to 56%/.test(bandRows[1].textContent), bandRows[1].textContent);
  ok("band row light dot", bandRows[1].querySelector(".dot.up") !== null);
  const mktRows = document.querySelectorAll(".market-tbl tbody tr");
  ok("market bands table rows", mktRows.length === full.market_bands.length, `${mktRows.length} vs ${full.market_bands.length}`);

  const svg = document.querySelector(".equity svg");
  ok("equity SVG exists", !!svg);
  ok("equity SVG has a line path", !!(svg && svg.querySelector("path.line")) && svg.querySelector("path.line").getAttribute("d").startsWith("M"));
  ok("equity SVG marks the best point", !!(svg && svg.querySelector("circle.peak")) && /best \$1,041\.20/.test(svg.textContent), svg && svg.textContent);

  ok("ledger rows", ledger && ledger.querySelectorAll("tbody tr").length === full.ledger.length, ledger && `${ledger.querySelectorAll("tbody tr").length} vs ${full.ledger.length}`);
  ok("ledger amount carries a sign", /^[+-]\$/.test(ledger.querySelector("tbody tr td:nth-child(4)").textContent), ledger.querySelector("tbody tr td:nth-child(4)").textContent);
  ok("by side table", document.querySelectorAll(".side-tbl tbody tr").length === 2);
  ok("by outcome table", document.querySelectorAll(".outcome-tbl tbody tr").length === 3);
  ok("guess score line with gloss", /Ours 0\.2210, Kalshi's 0\.2154/.test(document.querySelector(".brier").textContent) && /Lower is better/.test(document.querySelector(".brier").textContent), document.querySelector(".brier").textContent);
  ok("clv bars absent when no closing lines", document.querySelectorAll(".bars .bar").length === 0);
  ok("record tab is on in the top bar", document.querySelector(".tab.is-on").textContent === "Record");
  ok("no sideways scroll", document.documentElement.scrollWidth <= window.innerWidth);
} catch (e) {
  ok("exception", false, (e && (e.stack || e.message)) || String(e));
}
log("DONE");
