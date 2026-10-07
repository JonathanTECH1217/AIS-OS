// Boot: load config and health, mount the router, keep the status light honest.
import { loadCore, subscribe, verticals, vertical, setVertical } from "./js/state.js";
import { route, start } from "./js/router.js";
import { renderToday } from "./js/views/today.js";
import { renderPipeline } from "./js/views/pipeline.js";
import { renderChannels } from "./js/views/channels.js";
import { renderChannel } from "./js/views/channel.js";
import { renderMoney } from "./js/views/money.js";
import { renderCompanies } from "./js/views/companies.js";
import { renderActivity } from "./js/views/activity.js";
import { renderReports } from "./js/views/reports.js";
import { renderSettings } from "./js/views/settings.js";

route("today", renderToday);
route("home", renderToday);          // old links; Home merged into Today 2026-09-23
route("pipeline", renderPipeline);
route("leads", renderPipeline);       // Leads view removed 2026-09-23; a lead is a deal on the board
route("channels", renderChannels);
route("channel", renderChannel);
route("companies", renderCompanies);
route("activity", renderActivity);
route("reports", renderReports);
route("money", renderMoney);
route("settings", renderSettings);

function paintStatus(state) {
  const box = document.getElementById("status");
  const text = document.getElementById("status-text");
  const h = state.health;
  if (!h) return;
  box.className = "status " + (h.airtable_ready ? "ok" : "off");
  text.replaceChildren();
  if (h.airtable_ready) {
    text.append(`${h.instance} · ${h.records} of ${h.record_cap} records`);
  } else {
    text.append(`${h.instance} · offline: dials log locally. `);
    const a = document.createElement("a");
    a.href = "#/settings";
    a.textContent = "Connect Airtable";
    text.append(a);
  }
}

// The vertical switch under the brand: one call list per trade. A pick re-renders the current screen.
function paintVerticals() {
  const box = document.getElementById("vert");
  const list = verticals();
  if (list.length < 2) { box.replaceChildren(); return; }
  const cur = vertical();
  box.replaceChildren(...list.map((v) => {
    const b = document.createElement("button");
    b.type = "button";
    b.role = "radio";
    b.setAttribute("aria-checked", String(v.key === cur));
    b.textContent = v.label;
    b.addEventListener("click", () => {
      if (vertical() === v.key) return;
      setVertical(v.key);
      paintVerticals();
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    return b;
  }));
}

subscribe(paintStatus);
subscribe(paintVerticals);
const view = document.getElementById("view");
loadCore()
  .then(() => start(view))
  .catch((e) => {
    view.replaceChildren();
    const p = document.createElement("div");
    p.className = "empty";
    p.textContent = "The local server is not answering. Run: python scripts/crm_server.py";
    view.append(p);
    console.error(e);
  });
