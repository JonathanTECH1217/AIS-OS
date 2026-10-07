// Monarc Edge page test: the halt banner. With tests/fixtures/state-halt.json (a state_block halt) the banner shows
// the plain words, no Approve button exists anywhere, and Resume asks inline before it POSTs /api/halt/clear.
const out = document.getElementById("__out");
const log = (l) => { out.textContent += l + "\n"; };
const ok = (name, cond, detail = "") => { log(cond ? `PASS ${name}` : `FAIL ${name} ${detail}`); return !!cond; };
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const until = async (fn, ms = 3000) => { const t0 = performance.now(); for (;;) { let v = null; try { v = fn(); } catch (e) { v = null; } if (v) return v; if (performance.now() - t0 > ms) return null; await wait(30); } };
const realFetch = window.fetch.bind(window);
const json = (body, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));

try {
  const bundle = await (await realFetch("tests/fixtures/state-halt.json")).json();
  const calls = [];
  window.fetch = (url, opts = {}) => {
    const u = String(url), m = (opts.method || "GET").toUpperCase();
    calls.push(`${m} ${u}`);
    if (u.startsWith("/api/state")) return json(bundle);
    if (u === "/api/halt/clear" && m === "POST") return json({ halted: false });
    if (u === "/api/record") return json(bundle.record);
    return json({ errors: [`no fake for ${m} ${u}`] }, 404);
  };

  await window.__edge.boot();
  window.__edge.go("today");
  const banner = document.querySelector("#banner .halt");
  ok("banner shows", !!banner);
  ok("banner has the state_block words", banner && /Kalshi refused an order for this account's location\. Check the app and Maryland v\. Kalshi\./.test(banner.textContent), banner && banner.textContent);
  ok("banner is the light red pair", banner && getComputedStyle(banner).backgroundColor === "rgb(252, 232, 230)" && getComputedStyle(banner).color === "rgb(179, 38, 30)",
    banner && getComputedStyle(banner).backgroundColor + " " + getComputedStyle(banner).color);
  ok("banner has the 1 px border", banner && getComputedStyle(banner).borderBottomColor === "rgb(242, 184, 181)");
  ok("blocked account shows no read", /Kalshi account \(PROD\)/.test(document.getElementById("side").textContent) && /no read/.test(document.getElementById("side").textContent));
  ok("banner spans the width", banner && Math.abs(banner.getBoundingClientRect().width - window.innerWidth) < 2, banner && String(banner.getBoundingClientRect().width));
  ok("detail folded at first", !document.querySelector(".halt-detail"));
  // the Details toggle
  const details = [...banner.querySelectorAll("button")].find((b) => b.textContent === "Details");
  ok("Details toggle present", !!details);
  details.click();
  const det = await until(() => document.querySelector(".halt-detail"));
  ok("Details shows the raw detail", !!det && /403/.test(det.textContent), det && det.textContent);

  ok("cards still drawn", document.querySelectorAll(".card").length === 9);
  ok("no Approve button anywhere", document.querySelectorAll(".btn-approve").length === 0, String(document.querySelectorAll(".btn-approve").length));
  ok("no Pass button either", document.querySelectorAll(".btn-pass").length === 0);
  ok("ready card still shows its chip", document.querySelector('.card[data-id="c-ars-away"] .chip-status').textContent === "Ready to bet");

  // Resume asks inline, never window.confirm
  let confirmCalled = false;
  const realConfirm = window.confirm;
  window.confirm = () => { confirmCalled = true; return true; };
  const resume = [...document.querySelectorAll("#banner button")].find((b) => b.textContent === "Resume");
  ok("Resume button present", !!resume);
  resume.click();
  const ask = await until(() => document.querySelector(".halt-ask"));
  ok("Resume asks inline", !!ask && /Resume trading\?/.test(ask.textContent), ask && ask.textContent);
  ok("nothing posted before Yes", !calls.includes("POST /api/halt/clear"));
  // No keeps the halt
  [...ask.querySelectorAll("button")].find((b) => b.textContent === "No").click();
  ok("No puts the Resume button back", !!(await until(() => [...document.querySelectorAll("#banner button")].find((b) => b.textContent === "Resume"))));
  ok("still halted after No", !!document.querySelector("#banner .halt"));
  // Yes clears it
  [...document.querySelectorAll("#banner button")].find((b) => b.textContent === "Resume").click();
  const ask2 = await until(() => document.querySelector(".halt-ask"));
  [...ask2.querySelectorAll("button")].find((b) => b.textContent === "Yes").click();
  ok("banner goes after Yes", !!(await until(() => !document.querySelector("#banner .halt") && document.getElementById("banner"))));
  ok("clear was posted", calls.includes("POST /api/halt/clear"), calls.join(" | "));
  ok("window.confirm never used", !confirmCalled);
  ok("state no longer halted", window.__edge.state.bundle.halted === false);
  window.confirm = realConfirm;
  ok("no sideways scroll", document.documentElement.scrollWidth <= window.innerWidth);
} catch (e) {
  ok("exception", false, (e && (e.stack || e.message)) || String(e));
}
log("DONE");
