// Records, Creative (Jonathan, 2026-10-05: "There should be a creative tab in the CRM that holds unpublished media").
// What is made and not yet out: the cuts joined on this laptop, the shorts Monarc Studio exported, and the clips
// OpusClip holds for the projects in projects/crm/creative.json. A click plays one on the right. "Mark published"
// moves it to the folded Published list. Nothing is posted from here.
import { el } from "../util.js";
import { api } from "../api.js";
import { toast } from "../components/modal.js";
import { rerender } from "../router.js";
import { loomNotes } from "../components/loomnotes.js";

const ET = "America/New_York";
const fDay = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: ET });
const length = (s) => (s ? `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}` : "");
const facts = (it) => [it.sub, length(it.seconds), it.mb ? `${it.mb} MB` : "", it.at ? fDay.format(new Date(it.at)) : ""].filter(Boolean).join(" · ");

let open = null;  // the key of the item playing, kept across a redraw

export async function renderCreative(root) {
  const data = await api.get("/api/creative");
  const viewer = el("div", { class: "jr-viewer cr-viewer" });
  const rows = new Map();

  async function mark(it, on) {
    try {
      await api.post("/api/creative/published", { key: it.key, published: on });
      toast(on ? "Moved to Published." : "Back in the unpublished list.");
      if (on && open === it.key) open = null;
      rerender();
    } catch (e) { toast((e.errors || [String(e)]).join(" "), true); }
  }

  function play(it) {
    open = it.key;
    rows.forEach((r, k) => r.classList.toggle("is-on", k === it.key));
    const video = el("video", { class: "cr-video", controls: true, preload: "metadata", src: it.src, poster: it.thumb || null });
    viewer.replaceChildren(
      el("div", {}, el("div", { class: "label" }, it.where), el("h2", {}, it.title),
        el("div", { class: "muted", style: "font-size:12px" }, facts(it))),
      video,
      it.notes ? loomNotes(it.notes, video) : null,
      it.note ? el("div", { class: "cr-note" }, it.note) : null,
      it.path ? el("div", { class: "muted", style: "font-size:12px" }, `On this laptop: ${it.path}`) : null,
      (it.posts || []).length ? el("div", { class: "row", style: "gap:6px;flex-wrap:wrap" },
        ...(it.posts || []).map((p) => p.url
          ? el("a", { class: "tag" + (p.state === "public" ? " won" : " wait"), href: p.url, target: "_blank", rel: "noopener" }, `${p.platform} ${p.state || ""} · ${p.on || ""}`)
          : el("span", { class: "tag" }, `${p.platform} ${p.state || ""}`))) : null,
      el("div", { class: "row", style: "gap:8px;flex-wrap:wrap" },
        el("button", { class: "btn small", type: "button", onclick: () => mark(it, !it.published) }, it.published ? "Not published after all" : "Mark published"),
        it.download ? el("a", { class: "btn quiet small", href: it.download, target: "_blank", rel: "noopener" }, "Download the file") : null));
  }

  // One small tag per place a piece went (youtube_api.py records them): "YouTube private" until he publishes it.
  const postTags = (it) => (it.posts || []).map((p) =>
    el("span", { class: "tag" + (p.state === "public" ? " won" : " wait"), title: p.url || "" },
      `${p.platform === "youtube" ? "YouTube" : p.platform} ${p.state || ""}`.trim()));

  function row(it) {
    const r = el("button", { class: "jr-item cr-item", type: "button", onclick: () => play(it) },
      el("span", { class: "grow" }, el("span", { class: "cr-title" }, it.title), el("span", { class: "muted" }, facts(it))),
      ...postTags(it),
      it.published ? el("span", { class: "tag won" }, `published ${fDay.format(new Date(it.published + "T12:00:00"))}`) : null);
    rows.set(it.key, r);
    return r;
  }

  const list = el("div", { class: "jr-alist art-list" },
    ...data.groups.map((g) => el("section", { class: "art-cat" },
      el("div", { class: "row art-cat-head" },
        el("div", { class: "grow" }, el("h2", {}, g.label), el("div", { class: "muted", style: "font-size:12px" }, g.note || "")),
        el("span", { class: "tag" + (g.items.length ? "" : " faint") }, String(g.items.length))),
      g.error ? el("div", { class: "jr-missing" }, g.error) : null,
      !g.error && !g.items.length ? el("div", { class: "muted", style: "font-size:13px" }, g.wait || "Nothing here yet.") : null,
      ...g.items.map(row))),
    data.published.length ? el("details", { class: "art-cat" },
      el("summary", { style: "cursor:pointer;font-weight:500" }, `Published · ${data.published.length}`),
      ...data.published.map(row)) : null);

  const all = [...data.groups.flatMap((g) => g.items), ...data.published];
  const first = all.find((i) => i.key === open);
  if (first) play(first);
  else viewer.replaceChildren(el("div", { class: "muted" }, "Pick a piece on the left to play it here."));

  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Records"), el("h1", {}, "Creative"),
        el("div", { class: "sub" }, `Media that is made and not yet published: ${data.total} piece${data.total === 1 ? "" : "s"}. Click one to play it. Nothing is posted from here.`))),
    el("div", { class: "jr-split art-split" }, list, viewer));
}
