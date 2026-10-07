// Monarc Edge page test: the Settings tab. The Auto switch is locked while the gate fails (its title names the failing
// lights), unlocked with a passed gate, and saving env prod with dry run off shows the server's 409 message inline.
const out = document.getElementById("__out");
const log = (l) => { out.textContent += l + "\n"; };
const ok = (name, cond, detail = "") => { log(cond ? `PASS ${name}` : `FAIL ${name} ${detail}`); return !!cond; };
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const until = async (fn, ms = 3000) => { const t0 = performance.now(); for (;;) { let v = null; try { v = fn(); } catch (e) { v = null; } if (v) return v; if (performance.now() - t0 > ms) return null; await wait(30); } };
const realFetch = window.fetch.bind(window);
const json = (body, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
const clone = (o) => JSON.parse(JSON.stringify(o));
const REHEARSAL = "Prod with dry run off needs the rehearsal first. Run the seven-line checklist in the README, then set rehearsal_passed.";

try {
  const failing = await (await realFetch("tests/fixtures/state-cards.json")).json();
  const passed = clone(failing);
  passed.gate.passed = true; passed.gate.reasons = [];
  for (const k of Object.keys(passed.gate.lights)) passed.gate.lights[k].ok = true;
  let bundle = failing;
  let config = clone(failing.config);
  const puts = [];
  window.fetch = (url, opts = {}) => {
    const u = String(url), m = (opts.method || "GET").toUpperCase();
    if (u.startsWith("/api/state")) return json(bundle);
    if (u === "/api/config" && m === "GET") return json(config);
    if (u === "/api/config" && m === "PUT") {
      const body = JSON.parse(opts.body || "{}");
      puts.push(body);
      const env = body.env !== undefined ? body.env : config.env;
      const dry = body.dry_run !== undefined ? body.dry_run : config.dry_run;
      if (env === "prod" && dry === false && !config.rehearsal_passed) return json({ errors: [REHEARSAL] }, 409);
      if (body.mode === "auto" && !bundle.gate.passed) return json({ errors: ["Auto mode is locked until the gate passes."], gate: bundle.gate }, 409);
      config = { ...config, ...body, stake: { ...config.stake, ...(body.stake || {}) } };
      return json(config);
    }
    if (u === "/api/health") return json({ app: "Monarc Edge", version: "0.1.0", env: "demo", mode: "approve", dry_run: true, halted: false,
      keys: { kalshi_demo: "KALSHI_DEMO_API_KEY_ID", kalshi: null, football: "API_FOOTBALL_KEY", anthropic: "ANTHROPIC_API_KEY" }, football_remaining: 6120, busy: false, rev: 412, clock: bundle.now });
    if (u === "/api/backtest" && m === "GET") return json({ status: "idle", started: null, finished: null, report_md: null, report_path: null, metrics: null, error: null });
    return json({ errors: [`no fake for ${m} ${u}`] }, 404);
  };

  await window.__edge.boot();
  window.__edge.go("settings");
  let sw = await until(() => document.getElementById("f-mode"));
  ok("mode switch drawn", !!sw);
  ok("Auto switch disabled while the gate fails", sw && sw.disabled);
  ok("Auto switch title names the failing lights", sw && /Settled 37 of 200/.test(sw.title) && /CLV/.test(sw.title), sw && sw.title);
  ok("Auto switch is off", sw && !sw.checked);
  ok("every group drawn", ["Mode", "Exchange", "Money", "Busy market", "Window", "Auto windows", "Gate", "Witness", "Claude", "Legal watch", "Backtest"]
    .every((t) => [...document.querySelectorAll(".sgroup h3")].some((h) => h.textContent === t)));
  ok("field has a help line", /how many points better than the price/.test(document.getElementById("f-gap_floor_points").parentElement.textContent));
  ok("gap floor shows 7", document.getElementById("f-gap_floor_points").value === "7");
  ok("legal note textarea", document.getElementById("f-legal_watch-note").value.includes("Maryland v. Kalshi"));
  const keys = await until(() => /Kalshi practice from KALSHI_DEMO_API_KEY_ID/.test(document.getElementById("keys-line").textContent) && document.getElementById("keys-line"));
  ok("key sources line from health", !!keys, document.getElementById("keys-line").textContent);
  ok("missing key is called out", keys && /Kalshi live missing/.test(keys.textContent));
  ok("practice account radio is on", document.getElementById("f-env-demo").checked);
  ok("backtest seasons default", document.getElementById("bt-seasons").value === "1920,2021,2122,2223,2324,2425,2526");

  // save with nothing changed
  document.getElementById("save").click();
  ok("nothing changed message", !!(await until(() => /Nothing changed/.test(document.getElementById("sbar").textContent))));
  ok("no PUT when nothing changed", puts.length === 0);

  // a number change is sent as a partial config
  const gap = document.getElementById("f-gap_floor_points");
  gap.value = "8"; gap.dispatchEvent(new Event("input", { bubbles: true }));
  ok("bar shows unsaved changes", /Unsaved changes/.test(document.getElementById("sbar").textContent));
  document.getElementById("save").click();
  ok("saved message", !!(await until(() => /Saved at/.test(document.getElementById("sbar").textContent))));
  ok("PUT carried only the changed key", puts.length === 1 && JSON.stringify(puts[0]) === JSON.stringify({ gap_floor_points: 8 }), JSON.stringify(puts[0]));
  ok("form shows the saved value", document.getElementById("f-gap_floor_points").value === "8");

  // a passed gate unlocks the switch
  bundle = passed;
  await window.__edge.boot();
  window.__edge.go("settings");
  sw = await until(() => { const s = document.getElementById("f-mode"); return s && !s.disabled && s; });
  ok("Auto switch enabled when the gate passed", !!sw);
  ok("enabled switch title says allowed", sw && /allowed/.test(sw.title), sw && sw.title);

  // prod with dry run off: the server refuses, the message shows
  document.getElementById("f-env-prod").click();
  const dry = document.getElementById("f-dry_run");
  if (dry.checked) dry.click();
  ok("dry run unchecked", !dry.checked);
  document.getElementById("save").click();
  const err = await until(() => document.querySelector(".save-errors"));
  ok("409 message shows inline", !!err && err.textContent.includes(REHEARSAL), err && err.textContent);
  ok("PUT asked for prod with dry run off", puts.some((p) => p.env === "prod" && p.dry_run === false), JSON.stringify(puts));
  ok("draft keeps prod so he can fix it", document.getElementById("f-env-prod").checked);
  ok("no sideways scroll", document.documentElement.scrollWidth <= window.innerWidth);
} catch (e) {
  ok("exception", false, (e && (e.stack || e.message)) || String(e));
}
log("DONE");
