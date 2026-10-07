// Artifacts: a list of groups beside a read-only viewer. Shared by the journey map's channel cards (2026-10-01) and
// Records, Artifacts (2026-10-02). A group comes from the server already read (crm_server.py _resolve_group): files
// (a text file opens as text, an image as a picture, a PDF in place), ads-pages (per Google Ads campaign: the current
// copy, the page HTML, the ad brief, the earlier copies), site-pages, listings, messages (LinkedIn copy), shorts.
import { el, fmtDate } from "../util.js";
import { api } from "../api.js";

export function artifactViewer(empty = "Pick an item on the left to open it here.") {
  const viewer = el("div", { class: "jr-viewer" }, el("div", { class: "muted" }, empty));
  const head = (title, sub, link) => el("div", { class: "row" },
    el("div", { class: "grow" }, el("div", { class: "strong" }, title), sub ? el("div", { class: "muted", style: "font-size:12px" }, sub) : null),
    link ? el("a", { class: "btn quiet small", href: link, target: "_blank", rel: "noopener" }, "Open in a new tab") : null);
  async function show(item, title) {
    viewer.replaceChildren(el("div", { class: "muted" }, "Opening..."));
    try {
      const f = await api.get("/api/file?path=" + encodeURIComponent(item.path));
      const sub = `${f.path}${item.at ? ` · ${fmtDate(item.at.slice(0, 10))}` : ""}`;
      if (f.image) viewer.replaceChildren(head(title || item.name, sub), el("img", { class: "jr-img", src: f.image, alt: title || item.name }));
      else if (f.pdf) viewer.replaceChildren(head(title || item.name, sub, f.pdf), el("iframe", { class: "jr-pdf", src: f.pdf, title: title || item.name }));
      else viewer.replaceChildren(head(title || item.name, sub), el("pre", { class: "jr-code" + (f.ext === ".md" || f.ext === ".txt" ? " prose" : "") }, f.text + (f.cut ? "\n\n(cut at 400 KB)" : "")));
    } catch (e) { viewer.replaceChildren(el("div", { class: "down" }, (e.errors || [String(e)]).join(" "))); }
  }
  const showImage = (src, title) => viewer.replaceChildren(head(title), el("img", { class: "jr-img", src, alt: title }));
  const showText = (title, text) => viewer.replaceChildren(head(title), el("pre", { class: "jr-code prose" }, text || "(empty)"));
  return { viewer, show, showImage, showText };
}

const statusTag = (stt) => el("span", { class: "tag" + (stt === "Live" ? " won" : stt === "Paused" ? " lost" : " faint") }, stt || "Planned");

export function groupBox(g, v, { title = true } = {}) {
  const fileRow = (item, label) => el("button", { class: "jr-item", type: "button", onclick: () => v.show(item, label) },
    el("span", { class: "grow" }, label || item.name), el("span", { class: "muted num" }, item.at ? fmtDate(item.at.slice(0, 10)) : ""));
  const box = el("section", { class: "jr-group" }, title ? el("div", { class: "label" }, g.title) : null);
  if (g.error) box.append(el("div", { class: "down", style: "font-size:12px" }, g.error));
  // Open boxes in tasks.md that name this group's file (Records, Artifacts, 2026-10-05); a click reads the whole box.
  (g.tasks || []).forEach((t) => box.append(el("button", { class: "jr-todo", type: "button", onclick: () => v.showText(`To do · ${t.section}`, String(t.full || "").replace(/[`*]/g, "")) },
    el("span", { class: "tag" }, "To do"), el("span", { class: "grow" }, t.text))));
  if (g.kind === "files" || g.kind === "shorts") {
    const items = g.items || [];
    if (!items.length) box.append(el("div", { class: "jr-missing" }, g.missing || (g.kind === "shorts" ? "No finished shorts in media/ready yet." : "Nothing here yet.")));
    items.forEach((it) => box.append(g.kind === "shorts" ? el("div", { class: "jr-item static" }, el("span", { class: "grow" }, it.name), el("span", { class: "muted num" }, `${it.kb} KB`)) : fileRow(it)));
  } else if (g.kind === "ads-pages") {
    (g.campaigns || []).forEach((c) => {
      const earlier = el("details", { class: "jr-earlier" }, el("summary", {}, `Earlier copies (${c.earlier.length})`), ...c.earlier.map((it) => fileRow(it)));
      box.append(el("div", { class: "jr-camp" },
        el("div", { class: "row" }, el("span", { class: "strong grow" }, c.name), statusTag(c.status === "Not published" ? "Planned" : c.status)),
        c.url ? el("a", { class: "link", href: c.url, target: "_blank", rel: "noopener", style: "font-size:12px" }, c.url.replace(/^https:\/\//, "")) : null,
        ...c.current.map((it) => fileRow(it)), ...c.html.map((it) => fileRow(it)), ...c.brief.map((it) => fileRow(it)),
        c.earlier.length ? earlier : el("div", { class: "jr-missing" }, "No earlier copies yet.")));
    });
  } else if (g.kind === "site-pages") {
    (g.pages || []).forEach((p) => box.append(el("div", { class: "jr-camp" },
      el("div", { class: "row" }, el("span", { class: "strong grow" }, p.name), el("a", { class: "link", href: p.url, target: "_blank", rel: "noopener", style: "font-size:12px" }, "Live page")),
      fileRow(p.html),
      p.shot ? el("button", { class: "jr-item", type: "button", onclick: () => v.showImage(p.shot, `${p.name}, current copy`) }, el("span", { class: "grow" }, "Current copy, 1440 wide")) : null)));
  } else if (g.kind === "listings") {
    const ls = g.listings || [];
    box.append(el("div", { class: "muted", style: "font-size:12px" }, `${ls.filter((l) => l.status === "Live").length} of ${ls.length} live`),
      el("ul", { class: "jr-camps" }, ...ls.map((l) => el("li", {}, el("span", { class: "grow" }, l.url ? el("a", { class: "link", href: l.url, target: "_blank", rel: "noopener" }, l.name) : l.name), statusTag(l.status)))));
  } else if (g.kind === "messages") {
    const ms = g.messages || [];
    if (!ms.length && !g.error) box.append(el("div", { class: "jr-missing" }, "No message copy in the Messages table yet."));
    ms.forEach((m) => {
      const label = `${m.variation || "Message"}${m.framework ? ` · ${m.framework}` : ""}`;
      box.append(el("button", { class: "jr-item", type: "button", onclick: () => v.showText(`${label}${m.id ? ` · ${m.id}` : ""}`, m.copy) },
        el("span", { class: "grow" }, label), el("span", { class: "muted" }, m.id || "")));
    });
    box.append(el("div", { class: "muted", style: "font-size:12px" }, "From the Prospects base, Messages table. Edit the copy there."));
  }
  return box;
}
