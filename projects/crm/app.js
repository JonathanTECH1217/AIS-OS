// Boot: load config and health, mount the router, keep the status light honest.
import { loadCore, subscribe, setPendingSearch, refreshHealth } from "./js/state.js";
import { api } from "./js/api.js";
import { toast } from "./js/components/modal.js";
import { mountButterfly } from "./js/components/butterfly.js";
import { mountChat } from "./js/components/chat.js";
import { route, start, current, navigate } from "./js/router.js";
import { renderToday } from "./js/views/today.js";
import { renderPipeline } from "./js/views/pipeline.js";
import { renderChannels } from "./js/views/channels.js";
import { renderChannel } from "./js/views/channel.js";
import { renderMoney } from "./js/views/money.js";
import { renderCompanies } from "./js/views/companies.js";
import { renderActivity } from "./js/views/activity.js";
import { renderArtifacts } from "./js/views/artifacts.js";
import { renderCreative } from "./js/views/creative.js";
import { renderReports } from "./js/views/reports.js";
import { renderSettings } from "./js/views/settings.js";
import { renderAds } from "./js/views/ads.js";
import { renderLead } from "./js/views/lead.js";

route("today", renderToday);
route("home", renderToday);          // old links; Home merged into Today 2026-09-23
route("pipeline", renderPipeline);
route("leads", renderPipeline);       // Leads view removed 2026-09-23; a lead is a deal on the board
route("channels", renderChannels);
route("channel", renderChannel);
route("lead", renderLead);             // one booker's click, pages, and booking in one view (2026-09-28)
route("ads", renderAds);               // approve and publish Monarc's own Google Ads (2026-09-28)
route("companies", renderCompanies);
route("activity", renderActivity);
route("artifacts", renderArtifacts);     // the documents the selling runs on, by use (2026-10-02)
route("creative", renderCreative);       // media made and not yet published (2026-10-05)
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

// The vertical switch that sat under the brand (Integrators or Electricians, 2026-09-24) left on 2026-10-03: every
// screen shows every trade together.

// The pill search in the top bar opens Companies with the words already typed in (2026-09-26).
document.getElementById("gsearch").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = e.currentTarget.elements.q;
  setPendingSearch(input.value.trim());
  input.value = "";
  input.blur();
  const c = current();
  if (c.name === "companies" && !c.params.length) window.dispatchEvent(new HashChangeEvent("hashchange"));
  else navigate("#/companies");
});

// The refresh button in the top bar (2026-09-29): pull the CRM base, the call sheets, and the books now, then redraw
// the screen. Without it the CRM base refreshes every 2 minutes and the call sheets every 15 (Airtable Free API limits).
const refreshBtn = document.getElementById("refresh-all");
refreshBtn.addEventListener("click", async () => {
  if (refreshBtn.classList.contains("is-busy")) return;
  refreshBtn.classList.add("is-busy");
  try {
    await api.refresh();
    await refreshHealth();
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    toast("Up to date with Airtable.");
  } catch (e) {
    toast((e.errors || [String(e)]).join(" "), true);
  } finally {
    refreshBtn.classList.remove("is-busy");
  }
});

// Butterfly (2026-10-05): the logo in the top bar is a button; run a skill, new project, work on a project.
mountButterfly();
// The chat box (2026-10-05): the clone in a panel on the right, opened from the top bar.
mountChat();

subscribe(paintStatus);
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
