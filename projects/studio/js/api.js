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
    headers: body !== undefined ? { "Content-Type": "application/json" } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (e) { data = {}; }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

export const api = {
  get: (p) => call("GET", p),
  post: (p, b) => call("POST", p, b || {}),
  put: (p, b) => call("PUT", p, b || {}),
  patch: (p, b) => call("PATCH", p, b || {}),
  del: (p) => call("DELETE", p),
  health: () => call("GET", "/api/health"),
  bin: (since = 0) => call("GET", "/api/bin" + (since ? "?since=" + since : "")),
  asset: (id) => call("GET", "/api/asset/" + id),
  transcript: (id) => call("GET", "/api/asset/" + id + "/transcript"),
  moments: (id) => call("GET", "/api/asset/" + id + "/moments"),
  project: (id) => call("GET", "/api/projects/" + encodeURIComponent(id)),
  saveProject: (id, doc, baseRev) => call("PUT", "/api/projects/" + encodeURIComponent(id), { doc, baseRev }),
  newProject: (body) => call("POST", "/api/projects", body),
  versions: (id) => call("GET", "/api/projects/" + encodeURIComponent(id) + "/versions"),
  restore: (id, ts) => call("POST", "/api/projects/" + encodeURIComponent(id) + "/restore", { ts }),
  exportShort: (id) => call("POST", "/api/export", { project: id }),
  exportAll: () => call("POST", "/api/export/all", {}),
  genCaptions: (asset, ranges) => call("POST", "/api/asset/" + asset + "/captions", { ranges }),
  captionJob: (id) => call("GET", "/api/captions/" + id),
  async upload(file, dir) {
    const res = await fetch(`/api/upload?dir=${encodeURIComponent(dir || "")}&name=${encodeURIComponent(file.name)}`,
      { method: "PUT", body: file });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new ApiError(res.status, data);
    return data;
  },
};
