// Monarc Calls (reworked 2026-10-03): the notes window's boot. It sits beside Airtable's grid (the "Monarc Calls"
// Desktop shortcut, or Calls in Studio's top bar). Runs a test when loaded with ?test=<name>
// (projects/studio/tests/run.py loads calls*.js tests here).
import { C, poll, loadCheck, send } from "./js/calls/state.js";
import { mountNotes, notesApi } from "./js/calls/notes.js";

async function boot() {
  mountNotes(document.getElementById("cl-bar"), document.getElementById("cl-main"), document.getElementById("cl-foot"));
  poll();
  await loadCheck();
  window.__calls = { C, send, loadCheck, notes: notesApi(), ready: true };
  const name = new URLSearchParams(location.search).get("test");
  if (name) {
    try { await import(`./tests/t-${name}.js`); }
    catch (e) { const out = document.getElementById("__out"); out.textContent += `FAIL load ${name}: ${e.message}\nDONE\n`; }
  }
}

boot();
