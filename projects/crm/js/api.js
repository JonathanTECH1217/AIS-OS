// Fetch wrapper for the local server. Every error becomes a list of messages the UI can show.

export class ApiError extends Error {
  constructor(status, body) {
    super((body && body.errors && body.errors.join(" ")) || `Request failed (${status})`);
    this.status = status;
    this.body = body || {};
    this.errors = (body && body.errors) || [this.message];
  }
}

async function call(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (e) { data = {}; }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

export const api = {
  get: (path) => call("GET", path),
  post: (path, body) => call("POST", path, body || {}),
  health: () => call("GET", "/api/health"),
  config: () => call("GET", "/api/config"),
  queue: (params = {}) => call("GET", "/api/queue?" + new URLSearchParams(params)),
  companies: (q = "", vertical = "") => call("GET", "/api/companies?" + new URLSearchParams({ q, vertical })),
  bundle: (id) => call("GET", "/api/companies/" + encodeURIComponent(id)),
  // the company file (2026-10-04): the file, its mail, a tick or a to-do, the call list by name, who is waiting on him
  companyFile: (id) => call("GET", "/api/companies/" + encodeURIComponent(id) + "/file"),
  companyMail: (id) => call("GET", "/api/companies/" + encodeURIComponent(id) + "/mail"),
  triage: (id, body) => call("POST", "/api/companies/" + encodeURIComponent(id) + "/triage", body),
  triageBoard: () => call("GET", "/api/triage"),
  loom: (id, body) => call("POST", "/api/companies/" + encodeURIComponent(id) + "/loom", body),   // a Loom brief on a file
  loomReport: () => call("GET", "/api/reports/looms"),                                             // show and close rate by variation
  prospects: (q) => call("GET", "/api/prospects?" + new URLSearchParams({ q })),
  pipeline: (vertical = "") => call("GET", "/api/pipeline" + (vertical ? "?vertical=" + encodeURIComponent(vertical) : "")),
  activity: (limit = 200) => call("GET", "/api/activity?limit=" + limit),
  weekly: (week) => call("GET", "/api/reports/weekly" + (week ? "?week=" + week : "")),
  sources: () => call("GET", "/api/reports/sources"),
  funnel: () => call("GET", "/api/reports/funnel"),
  home: () => call("GET", "/api/home"),
  money: () => call("GET", "/api/money"),
  channel: (name) => call("GET", "/api/channel/" + encodeURIComponent(name)),
  records: (table) => call("GET", "/api/records/" + encodeURIComponent(table)),
  saveRecord: (table, body) => call("POST", "/api/records/" + encodeURIComponent(table), body),
  channels: () => call("GET", "/api/channels"),
  dial: (body) => call("POST", "/api/dial", body),
  saveDeal: (body) => call("POST", "/api/deals", body),
  savePerson: (body) => call("POST", "/api/people", body),
  saveActivity: (body) => call("POST", "/api/activities", body),
  saveCompany: (body) => call("POST", "/api/companies", body),
  refresh: () => call("POST", "/api/refresh", {}),
};
