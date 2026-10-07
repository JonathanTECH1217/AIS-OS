// One store. Config and health are loaded once and refreshed on demand; views fetch their own rows.
import { api } from "./api.js";

export const state = {
  config: null,
  health: null,
  listeners: new Set(),
};

export function subscribe(fn) { state.listeners.add(fn); return () => state.listeners.delete(fn); }
function emit() { for (const fn of state.listeners) fn(state); }

export async function loadCore() {
  const [config, health] = await Promise.all([api.config(), api.health()]);
  state.config = config;
  state.health = health;
  emit();
  return state;
}

export async function refreshHealth() {
  state.health = await api.health();
  emit();
  return state.health;
}

export function cfg() { return state.config || {}; }
export function todayISO() { return (state.health && state.health.today) || new Date().toISOString().slice(0, 10); }
export function stages() { return cfg().stages || []; }
export function stage(name) { return stages().find((s) => s.name === name); }
export function isClosedStage(name) { const s = stage(name); return !!(s && s.closed); }
export function outcomes() { return cfg().dial_outcomes || []; }
export function outcome(name) { return outcomes().find((o) => o.name === name); }
export function sources() { return cfg().sources || []; }
export function sourceName(id) { const s = sources().find((x) => x.id === id); return s ? s.name : ""; }
export function offers() { return cfg().offers || []; }
export function numbers() { return cfg().numbers || {}; }

// Verticals (2026-09-24): the trades, each with its own call list CSV; a company carries its trade in Airtable.
// The switch in the rail that showed one trade at a time left on 2026-10-03 (Jonathan: "I don't even know what that's
// for"), so every screen shows every trade together. vertical() is now only the default trade for a new company.
export function verticals() { return cfg().verticals || [{ key: "integrator", label: "Integrators", airtable: "Integrator" }]; }
export function vertical() { return verticals()[0].key; }
// The search box in the top bar (2026-09-26): it hands its words to the Companies screen, which reads them once.
let pendingSearch = "";
export function setPendingSearch(q) { pendingSearch = q || ""; }
export function takePendingSearch() { const q = pendingSearch; pendingSearch = ""; return q; }

export function verticalLabel(key) { const v = verticals().find((x) => x.key === (key || vertical())); return v ? v.label : ""; }
export function verticalAirtable(key) { const v = verticals().find((x) => x.key === (key || vertical())); return v ? v.airtable : ""; }
