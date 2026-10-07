// The inbox and the drafts on Today's first screen (2026-09-29, Jonathan: Today should show "a brief on my email inbox,
// any draft emails that I need to approve for send, as well as a view of my Google Calendar"). Read from Proton through
// Bridge (GET /api/mail, read only: nothing is marked read). The brief is the latest AIOS inbox report; below it, what
// arrived since. The CRM never sends: Jonathan reads a draft here and sends or deletes it in Proton.
import { el } from "../util.js";
import { api } from "../api.js";
import { openModal, toast } from "./modal.js";
import { loomNotes } from "./loomnotes.js";

const PROTON = { INBOX: "https://mail.proton.me/u/0/inbox", Drafts: "https://mail.proton.me/u/0/drafts" };
const ET = "America/New_York";
const fTime = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: ET });
const fDate = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: ET });
const fDay = new Intl.DateTimeFormat("en-CA", { timeZone: ET });
const OLD_DAYS = 14;

function when(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return fDay.format(d) === fDay.format(new Date()) ? fTime.format(d) : `${fDate.format(d)}, ${fTime.format(d)}`;
}
const daysOld = (iso) => (iso ? (Date.now() - new Date(iso).getTime()) / 86400000 : 999);

// replaceChildren that skips empty parts (the native one prints "null")
function fill(panel, ...parts) {
  panel.replaceChildren(...parts.flat().filter((p) => p !== null && p !== undefined && p !== false));
}

function panelHead(title, ...right) {
  return el("div", { class: "row" }, el("h2", { class: "grow" }, title), ...right);
}

function protonLink(folder, label) {
  return el("a", { class: "link", href: PROTON[folder], target: "_blank", rel: "noopener", style: "font-size:13px" }, label);
}

// The finished Loom B and A cut a draft links to (2026-10-06, Jonathan: "show me final renders in the crm under the waiting
// email approvals"). Played from this laptop, so it can be watched before its monarcbuild.com page is pushed.
function draftVideo(v, { big } = {}) {
  if (!v) return null;
  if (v.missing || !v.src) return el("div", { class: "draft-video missing", style: "font-size:12px" }, `Links to ${v.link || "a video page"}, but its video is not on this laptop.`);
  const mins = v.seconds ? `${Math.floor(v.seconds / 60)}:${String(Math.round(v.seconds % 60)).padStart(2, "0")}` : "";
  const video = el("video", { class: "draft-video-player" + (big ? " big" : ""), controls: true, preload: "metadata", src: v.src + "#t=1" });
  video.addEventListener("click", (e) => e.stopPropagation());
  return el("div", { class: "draft-video", onclick: (e) => e.stopPropagation(), onkeydown: (e) => e.stopPropagation() },
    video,
    el("div", { class: "draft-video-meta" },
      el("span", { class: "tag" }, "Loom B and A"),
      mins ? el("span", { class: "num" }, mins) : null,
      el("span", { class: "muted" }, v.live ? "page live" : "page not pushed yet: the link in the email works after push")),
    big && v.slug && v.date ? loomNotes({ date: v.date, slug: v.slug }, video) : null);
}

// One message or draft in full, read only.
export async function openReader(folder, uid) {
  const body = el("div", { class: "stack" }, el("div", { class: "muted" }, "Opening..."));
  openModal(body, { wide: true });
  try {
    const m = await api.get(`/api/mail/message?folder=${encodeURIComponent(folder)}&uid=${encodeURIComponent(uid)}`);
    const line = (k, v) => (v ? el("div", { style: "font-size:13px" }, el("span", { class: "muted" }, `${k} `), v) : null);
    body.replaceChildren(
      el("div", {}, el("div", { class: "label" }, folder === "Drafts" ? "Draft" : "Inbox"), el("h2", {}, m.subject || "(no subject)")),
      el("div", {}, line("From", m.from), line("To", m.to), line("Cc", m.cc), line("Date", when(m.at)),
        m.attachments && m.attachments.length ? line("Attachments", m.attachments.join(", ")) : null),
      draftVideo(m.video, { big: true }),
      el("div", { class: "mail-body" }, m.body || "(no text)"),
      el("div", { class: "actions" },
        folder === "Drafts" ? el("span", { class: "muted grow", style: "font-size:12px" }, "Send it, change it, or delete it in Proton. The CRM never sends.") : el("span", { class: "grow" }),
        el("a", { class: "btn", href: PROTON[folder], target: "_blank", rel: "noopener" }, folder === "Drafts" ? "Open Proton drafts" : "Open Proton")));
  } catch (e) {
    body.replaceChildren(el("div", { class: "errors" }, (e.errors || [String(e)]).join(" ")));
  }
}

function mailRow(folder, r, { who, line2 }) {
  const row = el("div", { class: "mail-row" + (r.unread ? " unread" : ""), tabindex: "0", role: "button" },
    el("span", { class: "dot", "aria-label": r.unread ? "unread" : null }),
    el("div", { class: "mail-main" }, el("div", { class: "who" }, who), el("div", { class: "subj" }, r.subject || "(no subject)"),
      line2 ? el("div", { class: "snip" }, line2) : null),
    el("span", { class: "when num" }, when(r.at)));
  const open = () => openReader(folder, r.uid);
  row.addEventListener("click", open);
  row.addEventListener("keydown", (e) => { if (e.key === "Enter") open(); });
  return row;
}

function paintInbox(panel, d, reload) {
  const refresh = el("button", { class: "icon-btn", type: "button", title: "Read the inbox again", "aria-label": "Read the inbox again" },
    el("span", { class: "ms", "aria-hidden": "true" }, "refresh"));
  refresh.addEventListener("click", async () => { refresh.classList.add("is-busy"); await reload(true); });
  const head = panelHead("Inbox", d.bridge === "ok" ? el("span", { class: "tag" + (d.unread ? " solid" : " faint") }, `${d.unread} unread`) : null, refresh);
  if (d.bridge !== "ok") {
    panel.replaceChildren(head, el("div", { class: "down", style: "font-size:13px" }, d.note || "Could not read the inbox."),
      el("div", { class: "muted", style: "font-size:12px" }, "The brief and the drafts come from Proton Mail Bridge on this laptop."));
    return;
  }
  const r = d.report;
  const brief = r ? el("div", { class: "brief clamp" }, r.body) : null;
  const more = r && r.body && r.body.length > 420 ? el("button", { class: "link", type: "button", style: "font-size:12px" }, "Show the whole brief") : null;
  if (more) more.addEventListener("click", () => { brief.classList.toggle("clamp"); more.textContent = brief.classList.contains("clamp") ? "Show the whole brief" : "Show less"; });
  const since = d.review || [];
  // meeting replies first (2026-10-01): a guest accepting or declining an invite sent as jonathan@monarcbuild.com
  const replies = d.replies || [];
  const replyTag = (k) => el("span", { class: "tag " + (k === "Accepted" ? "won" : k === "Declined" ? "lost" : "") }, k);
  const replyBlock = replies.length ? [el("div", { class: "label" }, "Meeting replies"),
    ...replies.map((m) => { const row = mailRow("INBOX", m, { who: m.from, line2: m.subject.replace(/^[^:]+:\s*/, "") }); row.classList.add("reply"); row.querySelector(".when").before(replyTag(m.reply)); return row; })] : [];
  fill(panel, head, ...replyBlock,
    el("div", { class: "label" }, r ? `AIOS brief · ${when(r.at)}` : "AIOS brief"),
    r ? brief : el("div", { class: "muted", style: "font-size:13px" }, "No brief yet. It is written by the inbox pass when a Claude session starts."),
    more,
    el("div", { class: "label", style: "margin-top:6px" }, r ? `New since the brief · ${d.review_since || 0}` : "Needs a look"),
    ...(since.length ? since.map((m) => mailRow("INBOX", m, { who: m.from, line2: m.snippet }))
      : [el("div", { class: "muted", style: "font-size:13px" }, "Nothing new that needs you since the brief.")]),
    (d.review_since || 0) > since.length ? el("div", { class: "muted", style: "font-size:12px" }, `${d.review_since - since.length} more in Proton. `, protonLink("INBOX", "Open Proton")) : null,
    el("div", { class: "muted", style: "font-size:11px" }, `Left out: your own mail, Patrick, threads, and the reports. Read ${when(d.read_at)}; nothing is marked read.`));
}

function paintDrafts(panel, d) {
  if (d.bridge !== "ok") {
    panel.replaceChildren(panelHead("Drafts to approve"), el("div", { class: "muted", style: "font-size:13px" }, "Waiting on Proton Mail Bridge."));
    return;
  }
  const drafts = d.drafts || [];
  const fresh = drafts.filter((x) => daysOld(x.at) <= OLD_DAYS);
  const old = drafts.filter((x) => daysOld(x.at) > OLD_DAYS);
  const row = (x) => {
    const r = mailRow("Drafts", x, { who: `To ${x.to || "(no one yet)"}`, line2: (x.attachments ? `${x.attachments} attachment${x.attachments === 1 ? "" : "s"} · ` : "") + (x.snippet || "") });
    const v = draftVideo(x.video);
    if (v) r.querySelector(".mail-main").append(v);
    return r;
  };
  fill(panel,
    panelHead("Drafts to approve", el("span", { class: "tag" + (fresh.length ? " solid" : " faint") }, `${fresh.length} recent`), protonLink("Drafts", "Open")),
    el("div", { class: "muted", style: "font-size:12px" }, "Read one here, then send, change, or delete it in Proton. The CRM never sends."),
    ...(fresh.length ? fresh.map(row) : [el("div", { class: "muted", style: "font-size:13px" }, "No drafts from the last two weeks.")]),
    old.length ? el("details", { class: "old-drafts" }, el("summary", {}, `${old.length} older draft${old.length === 1 ? "" : "s"}, over two weeks old`), ...old.map(row)) : null);
}

// Two panels that fill themselves once the inbox is read, so the rest of Today does not wait on Bridge.
export function mailPanels() {
  const loading = () => el("div", { class: "muted", style: "font-size:13px" }, "Reading your inbox...");
  const inbox = el("section", { class: "panel top-panel", "aria-label": "Inbox" }, panelHead("Inbox"), loading());
  const drafts = el("section", { class: "panel top-panel", "aria-label": "Drafts to approve" }, panelHead("Drafts to approve"), loading());
  async function load(force) {
    try {
      const d = await api.get("/api/mail" + (force ? "?force=1" : ""));
      paintInbox(inbox, d, load);
      paintDrafts(drafts, d);
      if (force) toast("Inbox read again.");
    } catch (e) {
      const msg = el("div", { class: "down", style: "font-size:13px" }, (e.errors || [String(e)]).join(" "));
      inbox.replaceChildren(panelHead("Inbox"), msg);
      drafts.replaceChildren(panelHead("Drafts to approve"), msg.cloneNode(true));
    }
  }
  load(false);
  return { inbox, drafts };
}
