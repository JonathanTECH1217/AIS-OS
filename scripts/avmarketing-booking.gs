/**
 * Monarc Build booking backend for monarcbuild.com/av_marketing/ (live 2026-09-23) and the homepage popup.
 * Google Apps Script web app, deployed from Jonathan's Google account (the one that owns the business calendar).
 * Setup and deploy steps: references/apps-script-booking.md.
 *
 * GET  ?action=slots       -> {ok, k, slots:[ISO...]} the first weekday with open afternoon slots (homepage popup)
 * GET  ?action=calendar    -> {ok, days:{"yyyy-MM-dd":[ISO...]}} every open afternoon slot, DAYS_AHEAD days out (ad page calendar)
 * POST {token, start, name, email, phone, technicians, page, viewer_timezone, utm_*}
 *                          -> books the slot: event on BOOK_CALENDAR with a Google Meet link, invite emailed by Google Calendar,
 *                             a row in the "Monarc bookings" sheet, the details emailed to Jonathan, the confirmation emailed to
 *                             the prospect (Meet link, time, who they speak with), and reminders queued for the afternoon before
 *                             (2026-10-03) and one hour before the call (Jonathan's spec, 2026-09-23; the "Before our call" email
 *                             is in the file, switched off). A /builder-check/ booking also carries installs, last_five, ads_today
 *                             (the four tiles of the builder search check, projects/meta-ads/check.md) and fbclid.
 *                          -> {ok, eventId, meet, htmlLink} or {ok:false, error}
 *
 * The queue runs off ONE recurring trigger (installQueue, every 5 minutes) that reads the sheet and sends what is due.
 * Apps Script caps time-based triggers at 20 per script, so there is never one trigger per booking.
 *
 * Slot rules mirror Style Guide section 6 rule 10: 1:00 to 5:00 pm Eastern, 15 minute calls, one slot per hour,
 * nothing sooner than LEAD_MIN from now, weekdays only, up to DAYS_AHEAD days out.
 *
 * Run once from the editor, in this order: setup, selfTest, installQueue, dripSelfTest. Then deploy.
 */

var BOOK_CALENDAR = "74d611a15d0883e131529542f6bef46bb91bda5704d30c3cc95199be6addde5c@group.calendar.google.com"; // the "Monarc Build" calendar, connections.md row 3
var BUSY_CALENDARS = [BOOK_CALENDAR, "primary"];   // every calendar checked for conflicts; "primary" is the account's own
var TZ = "America/New_York";
var WINDOW_START = 13;   // 1:00 pm Eastern
var WINDOW_END = 17;     // last call ends by 5:00 pm Eastern
var SLOT_MIN = 15;       // call length
var STEP_MIN = 60;       // one slot per hour: 1, 2, 3, 4 pm
var LEAD_MIN = 45;       // nothing sooner than 45 minutes from now
var DAYS_AHEAD = 14;     // the calendar step shows two weeks (was 5 for the single-day list)
var MAX_SLOTS = 8;
var TOKEN = "jBNRkhGWf6qpdLCmg7Vmr4gbJikf";          // set to a random string and paste the same value into BOOKING_TOKEN on the page. Empty = no check.
var EVENT_TITLE = "Monarc Build audit: ";          // + the prospect's first name (the invite's headline). No person's name anywhere a prospect reads (Jonathan, 2026-10-01).
var ORGANIZER_NOTE = "Booked from monarcbuild.com.";

/* Emails and the drip (2026-09-23) */
var SHEET_NAME = "Monarc bookings";                 // created by setup(); id kept in script properties
var NOTIFY_TO = "jonathan@monarcbuild.com";         // where the booking details go
var REPLY_TO = "jonathan@monarcbuild.com";          // reply-to on every email to the prospect
var FROM_NAME = "Monarc Build";                     // display name on every email (was "Jonathan Beach" until 2026-10-01)
var SEND_AS = "";                                   // optional Gmail "send mail as" alias, e.g. "jonathan@monarcbuild.com". Empty = the script account's address.
/* Jonathan's spec, 2026-09-23: the prospect gets a confirmation (Meet link, time, who they speak with) and one reminder
   an hour before the call; Jonathan gets the details. The "Before our call" email stays in the file, switched off. */
var ENRICH_ENABLED = false;                         // true turns the "Before our call" email back on
var ENRICH_AFTER_MIN = 180;                         // enrichment email 3 hours after booking...
var MORNING_HOUR = 8;                               // ...or 8:00 am Eastern next morning when booked after EVENING_HOUR
var EVENING_HOUR = 17;
var REMIND_BEFORE_MIN = 60;                         // reminder one hour before the call; skipped when the call is nearer than that at booking
var DAYBEFORE_HOUR = 16;                            // the day-before reminder goes at 4:00 pm Eastern the day before the call (2026-10-03); skipped when the booking lands after that
var QUEUE_EVERY_MIN = 5;                            // the queue runs every 5 minutes, so the reminder lands 55 to 60 minutes before
var COLS = ["booked_at","name","email","phone","technicians","start_iso","start_eastern","start_local","meet","event_id","page","viewer_timezone",
            "utm_source","utm_medium","utm_campaign","utm_content","utm_id","landing_url",
            "status","confirm_sent","enrich_due","enrich_sent","remind_due","remind_sent",
            // added 2026-10-03, at the end: sheet() appends the missing header cells in this order, so appendRow stays aligned
            "daybefore_due","daybefore_sent","installs","last_five","ads_today","fbclid"];

function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || "slots";
  if (action === "slots") {
    var found = firstOpenDay();
    return out(found ? {ok: true, k: found.k, slots: found.open.map(function (s) { return new Date(s[0]).toISOString(); })} : {ok: true, k: 0, slots: []});
  }
  if (action === "calendar") {
    var days = {};
    openDays().forEach(function (d) { days[d.key] = d.open.map(function (s) { return new Date(s[0]).toISOString(); }); });
    return out({ok: true, days: days});
  }
  if (action === "agenda") return out(agenda(parseInt((e && e.parameter && e.parameter.days) || "2", 10)));
  return out({ok: false, error: "unknown action"});
}

/* GET ?action=agenda&days=N -> the next N days of events from the business calendar and the account's own calendar,
   for the CRM's Today screen (Jonathan, 2026-09-23: "Today should show me my calendar"). Read only. */
function agenda(days) {
  days = Math.min(7, Math.max(1, isNaN(days) ? 2 : days));
  var t0 = todayEastern();
  var lo = new Date(wall(t0.y, t0.m, t0.d, 0, 0)), hi = new Date(wall(t0.y, t0.m, t0.d + days, 0, 0));
  var events = [], seen = {};
  BUSY_CALENDARS.forEach(function (id) {
    var calName = id === "primary" ? "Personal" : "Monarc Build";
    try {
      var res = Calendar.Events.list(id, {timeMin: lo.toISOString(), timeMax: hi.toISOString(), singleEvents: true, orderBy: "startTime", maxResults: 50});
      (res.items || []).forEach(function (ev) {
        if (ev.status === "cancelled") return;
        var key = ev.iCalUID || ev.id;
        if (seen[key]) return;
        seen[key] = 1;
        var allDay = !!(ev.start && ev.start.date);
        events.push({
          id: ev.id, title: ev.summary || "(no title)",
          start: allDay ? ev.start.date : ev.start.dateTime, end: allDay ? ev.end.date : ev.end.dateTime, all_day: allDay,
          calendar: calName, meet: ev.hangoutLink || "", location: ev.location || "", link: ev.htmlLink || "",
          guests: (ev.attendees || []).filter(function (a) { return !a.self && !a.organizer; }).map(function (a) { return a.displayName || a.email; }).slice(0, 4)
        });
      });
    } catch (err) {
      events.push({id: "err:" + id, title: "Calendar not readable: " + calName, start: lo.toISOString(), end: lo.toISOString(), all_day: true, calendar: calName, error: String(err && err.message || err)});
    }
  });
  events.sort(function (a, b) { return String(a.start).localeCompare(String(b.start)); });
  return {ok: true, tz: TZ, days: days, events: events};
}

function doPost(e) {
  var body = {};
  try { body = JSON.parse((e && e.postData && e.postData.contents) || "{}"); } catch (err) { return out({ok: false, error: "bad json"}); }
  if (TOKEN && body.token !== TOKEN) return out({ok: false, error: "bad token"});
  if (!body.start || !body.email || !body.name) return out({ok: false, error: "missing start, name, or email"});
  var start = Date.parse(body.start);
  if (isNaN(start)) return out({ok: false, error: "bad start"});
  var end = start + SLOT_MIN * 60000;

  var lock = LockService.getScriptLock();
  try { lock.waitLock(10000); } catch (err) { return out({ok: false, error: "busy, try again"}); }
  var ev;
  try {
    if (!isOfferedSlot(start)) return out({ok: false, error: "slot not offered"});
    if (isBusy(start, end)) return out({ok: false, error: "slot just taken"});
    /* The prospect reads the title and the description in the invite, so both speak to them (Jonathan, 2026-09-23).
       The internal fields ride on the event as private extended properties, which the invite never shows. */
    var description = [
      "Fifteen minutes on Google Meet with Monarc Build.",
      "",
      "Before the call we pull your search results, your pages, and your ad account. You leave with the audit either way. Bring nothing.",
      "",
      "Questions before then: " + REPLY_TO
    ].join("\n");
    var hidden = {source: ORGANIZER_NOTE, name: body.name, email: body.email};
    ["phone","technicians","page","viewer_timezone","utm_id","utm_source","utm_medium","utm_campaign","utm_content","utm_term","li_fat_id","gclid","fbclid","installs","last_five","ads_today","landing_url","referrer"].forEach(function (k) {
      if (body[k]) hidden[k] = String(body[k]).slice(0, 1000);
    });
    ev = Calendar.Events.insert({
      summary: EVENT_TITLE + firstName(body.name),
      description: description,
      start: {dateTime: new Date(start).toISOString()},
      end: {dateTime: new Date(end).toISOString()},
      attendees: [{email: body.email, displayName: body.name}],
      conferenceData: {createRequest: {requestId: Utilities.getUuid(), conferenceSolutionKey: {type: "hangoutsMeet"}}},
      extendedProperties: {private: hidden},
      guestsCanModify: false,
      reminders: {useDefault: true}
    }, BOOK_CALENDAR, {conferenceDataVersion: 1, sendUpdates: "all"});
  } catch (err) {
    return out({ok: false, error: String(err && err.message || err)});
  } finally {
    lock.releaseLock();
  }

  /* The booking stands from here. Sheet row, the confirmation, the CRM lead, and Jonathan's email must not undo it. */
  var row = null;
  try {
    row = bookingRow(body, start, ev);
    sendMail(row.email, confirmEmail(row));
    row.confirm_sent = new Date();
    appendRow(row);
  } catch (err2) {
    console.error("post-booking step failed: " + (err2 && err2.message || err2));
  }
  if (row) {
    try { row.crm = postLead(body, start, ev); } catch (err3) { row.crm = "failed: " + (err3 && err3.message || err3); console.error("CRM post failed: " + row.crm); }
    row.journeyLine = journeyLine(body);  // after the sheet row, so the sheet's columns stay as they are
    try { sendMail(NOTIFY_TO, notifyEmail(row), row.email); } catch (err4) { console.error("notify failed: " + (err4 && err4.message || err4)); }
  }
  return out({ok: true, eventId: ev.id, meet: ev.hangoutLink || "", htmlLink: ev.htmlLink || ""});
}

/* ---------- CRM: one Leads row per booking (2026-09-23) ----------
   Posts to the Monarc CRM base (references/airtable-api.md) when AIRTABLE_TOKEN is set in Script properties
   (Project Settings, Script properties). Empty token = skipped, and the notification says so. The token needs
   data.records:read and data.records:write on the Monarc CRM base only. Links are sent by name with typecast,
   the way the dashboard's offline replay does (write rule 7): Source by channel name, Landing page by URL,
   Keyword by utm_term; Campaign by Platform id when a row matches, else by name. Company is left for the
   dashboard and the inbox pass, which know the one-company-per-Key rule (write rule 1). */
var AIRTABLE_BASE = "appgv3njf5Fk99QXo";
var SITE = "https://monarcbuild.com/";

function airtableToken() { return PropertiesService.getScriptProperties().getProperty("AIRTABLE_TOKEN") || ""; }

function at(method, path, payload) {
  var res = UrlFetchApp.fetch("https://api.airtable.com/v0/" + AIRTABLE_BASE + "/" + path, {
    method: method, contentType: "application/json",
    headers: {Authorization: "Bearer " + airtableToken()},
    payload: payload ? JSON.stringify(payload) : undefined,
    muteHttpExceptions: true
  });
  var code = res.getResponseCode(), body = {};
  try { body = JSON.parse(res.getContentText()); } catch (e) {}
  if (code >= 300) throw new Error("airtable " + code + " " + ((body.error && (body.error.message || body.error.type)) || ""));
  return body;
}

function atFind(table, field, value) {
  if (!value) return null;
  var formula = encodeURIComponent("{" + field + "}=\"" + String(value).replace(/"/g, '\\"') + "\"");
  var r = at("get", encodeURIComponent(table) + "?maxRecords=1&filterByFormula=" + formula);
  return r.records && r.records.length ? r.records[0] : null;
}

/* Channel from the UTMs, the same reading as references/attribution.md. A LinkedIn click id or a paid-social
   medium off a LinkedIn referrer still counts as LinkedIn when utm_source carries something else (an id, say).
   With no utm_source at all, the referrer decides (2026-09-28: a click on an untagged LinkedIn post came in as
   inbound): linkedin.com or lnkd.in is LinkedIn, a Google search page is Google Organic. */
function channelFor(b) {
  var s = String(b.utm_source || "").toLowerCase(), m = String(b.utm_medium || "").toLowerCase();
  var ref = String(b.referrer || "").toLowerCase();
  if ((s === "google" && m === "cpc") || b.gclid) return "google-ads";
  if (s === "google") return "google-organic";
  if (s === "facebook" || s === "instagram" || s === "meta") return "meta-ads";
  if (s === "linkedin" || b.li_fat_id || (m === "paid-social" && /linkedin/.test(ref))) return "linkedin";
  if (s === "email") return "email";
  if (!s && /(^|[\/.])(linkedin\.com|lnkd\.in)/.test(ref)) return "linkedin";
  if (!s && /(^|[\/.])google\.[a-z.]+\//.test(ref)) return "google-organic";
  return "inbound";
}

/* The visitor's journey (2026-09-28): assets/journey.js on every page keeps the click that brought someone and each
   page they viewed, in their browser for up to 30 days, and the page sends it as body.journey. When this visit carries
   no link tags, no click id, and no outside referrer (a return visit), the first click in the journey gets the credit:
   a LinkedIn ad clicked on Monday still owns the booking made on Thursday. */
var TAG_KEYS = ["utm_source","utm_medium","utm_campaign","utm_content","utm_term","utm_id","li_fat_id","gclid","fbclid"];

function journeyOf(b) {
  if (!b.journey) return null;
  try { var j = JSON.parse(String(b.journey).slice(0, 60000)); return j && j.ev ? j : null; } catch (e) { return null; }
}

function withFirstTouch(b) {
  var j = journeyOf(b);
  var ref = String(b.referrer || "");
  var outside = /^https?:\/\//.test(ref) && ref.indexOf("monarcbuild.com") === -1;
  if (b.utm_source || b.gclid || b.li_fat_id || outside || !j || !j.first) return b;
  var c = {};
  for (var k in b) c[k] = b[k];
  TAG_KEYS.forEach(function (key) { if (j.first[key]) c[key] = j.first[key]; });
  if (j.first.ref) c.referrer = j.first.ref;
  c.first_touch = true;
  return c;
}

function journeyLine(b) {
  var j = journeyOf(b);
  if (!j) return "";
  var f = j.first;
  var views = j.ev.filter(function (e) { return e.k === "page" || e.k === "arrive"; }).length;
  var from = "direct";
  if (f) from = [f.utm_source, f.utm_medium, f.utm_campaign, f.utm_content].filter(function (x) { return x; }).join(" / ") || (f.ref ? "from " + f.ref : "direct");
  return "Journey: first click " + (f ? fmtWhen(f.t * 1000, TZ) + " (" + from + ")" : "not recorded") + ", " + views + " page view" + (views === 1 ? "" : "s") + " before booking.";
}

/* The raw query string, as the CRM stores it: the landing URL's query when the page sent one, else rebuilt. */
function utmString(b) {
  var u = String(b.landing_url || ""), i = u.indexOf("?");
  if (i > -1) return u.slice(i + 1).replace(/#.*$/, "");
  return ["utm_source","utm_medium","utm_campaign","utm_term","utm_content","utm_id","li_fat_id","gclid","fbclid"]
    .filter(function (k) { return b[k]; })
    .map(function (k) { return k + "=" + encodeURIComponent(b[k]); }).join("&");
}

/* Jonathan's own bookings are tests, never leads (Jonathan, 2026-10-02: "anything that's from me or gets sent to
   jonathan@monarcbuild.com is a no-go"). The CRM ignores them too (crm_server.py is_self). */
var SELF_EMAILS = ["jonathan@monarcbuild.com", "jonathanbeach17@gmail.com", "sumreat17@gmail.com"];
var SELF_DOMAINS = ["monarcbuild.com"];
var SELF_PHONES = ["4438226004"];
function isSelf(body) {
  var email = String(body.email || "").trim().toLowerCase();
  var phone = String(body.phone || "").replace(/\D/g, "").slice(-10);
  return SELF_EMAILS.indexOf(email) > -1 || SELF_DOMAINS.indexOf(email.split("@").pop()) > -1 || (phone.length === 10 && SELF_PHONES.indexOf(phone) > -1);
}

/* The landing page's path from the popup's page label (2026-10-03). Labels carry underscores (facebook_ads) where the
   paths carry hyphens (/facebook-ads/); /av_marketing/ is the one path with an underscore; "home" is the root. */
function pagePath(label) {
  var l = String(label || "").trim().toLowerCase();
  if (!l || l === "home") return "";
  if (l === "av_marketing" || l === "avmarketing") return "av_marketing/";
  return l.replace(/_/g, "-") + "/";
}

/* The builder search check (/builder-check/, 2026-10-03): the four tiles ride on the booking as installs, technicians,
   last_five, ads_today. "None of these" installed, or 1 to 2 technicians, is not a fit (projects/meta-ads/check.md). */
function checkLine(b) {
  if (!b.installs && !b.last_five && !b.ads_today) return "";
  var fit = (/none/i.test(String(b.installs || "")) || /^1 to 2$/i.test(String(b.technicians || "")) ) ? "not a fit" : "ok";
  return "Check: installs " + (b.installs || "?") + "; last five " + (b.last_five || "?") + "; ads today " + (b.ads_today || "?") + ". Fit: " + fit + ".";
}

function postLead(raw, start, ev) {
  if (!airtableToken()) return "skipped (no AIRTABLE_TOKEN)";
  if (isSelf(raw)) return "skipped (Jonathan's own booking, a test)";
  var ext = "calendar:" + ev.id;
  if (atFind("Leads", "External id", ext)) return "already there";
  var body = withFirstTouch(raw);  // a return visit takes the tags of the first click in the journey
  var page = SITE + pagePath(body.page);
  var f = {
    "Name": body.name,
    "When": Utilities.formatDate(new Date(), TZ, "yyyy-MM-dd'T'HH:mm:ssXXX"),
    "Email": body.email,
    "Phone": body.phone || "",
    "Status": "Booked",
    "Call at": new Date(start).toISOString(),
    "Technicians": body.technicians || "",
    "Installs": body.installs || "",
    "Last five": body.last_five || "",
    "Ads today": body.ads_today || "",
    "UTM": utmString(body),
    "External id": ext,
    "Message": "Booked " + fmtWhen(start, TZ) + " from " + page + (ev.hangoutLink ? ". Meet " + ev.hangoutLink : ""),
    "Notes": [checkLine(body), body.technicians ? "Technicians " + body.technicians + "." : "", body.viewer_timezone ? "Prospect time zone " + body.viewer_timezone + "." : "", body.referrer ? "Referrer " + body.referrer + "." : ""].filter(String).join(" "),
    "Source": [channelFor(body)],
    "Landing page": [page]
  };
  if (raw.journey) f["Journey"] = String(raw.journey).slice(0, 90000);
  if (body.first_touch) f["Notes"] = (f["Notes"] ? f["Notes"] + " " : "") + "Credited to the first click in the journey (a return visit with no tags).";
  if (body.gclid) f["gclid"] = body.gclid;
  if (body.utm_campaign) { var camp = atFind("Campaigns", "Platform id", body.utm_campaign); f["Campaign"] = [camp ? camp.id : body.utm_campaign]; }
  if (body.utm_term) f["Keyword"] = [body.utm_term];
  at("post", "Leads", {records: [{fields: f}], typecast: true});
  return "posted";
}

/* Read-only check that the token reaches the base: logs the channel rows. Writes nothing. */
function crmSelfTest() {
  if (!airtableToken()) { Logger.log("AIRTABLE_TOKEN is not set in Script properties."); return; }
  var r = at("get", "Sources?pageSize=20");
  Logger.log("Sources: " + (r.records || []).map(function (x) { return x.fields.Name; }).join(", "));
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

/* Eastern wall clock helpers */
function offsetMinutes(d) {
  var z = Utilities.formatDate(d, TZ, "Z");           // e.g. -0400
  var sign = z.charAt(0) === "-" ? -1 : 1;
  return sign * (parseInt(z.substr(1, 2), 10) * 60 + parseInt(z.substr(3, 2), 10));
}
function wall(y, m, d, h, mi) {                       // Eastern wall time to a UTC ms instant
  var guess = Date.UTC(y, m - 1, d, h, mi);
  return guess - offsetMinutes(new Date(guess)) * 60000;
}
function todayEastern() {
  var s = Utilities.formatDate(new Date(), TZ, "yyyy-M-d").split("-");
  return {y: +s[0], m: +s[1], d: +s[2]};
}
function easternParts(ms) {
  var s = Utilities.formatDate(new Date(ms), TZ, "yyyy-M-d-H").split("-");
  return {y: +s[0], m: +s[1], d: +s[2], h: +s[3]};
}
function pad2(n) { return (n < 10 ? "0" : "") + n; }

function candidateDays() {
  var now = Date.now();
  var t0 = todayEastern();
  var days = [];
  for (var k = 0; k <= DAYS_AHEAD; k++) {
    var dd = new Date(Date.UTC(t0.y, t0.m - 1, t0.d + k));
    var wd = dd.getUTCDay();
    if (wd === 0 || wd === 6) continue;
    var y = dd.getUTCFullYear(), m = dd.getUTCMonth() + 1, d = dd.getUTCDate();
    var cands = [];
    for (var t = WINDOW_START * 60; t + SLOT_MIN <= WINDOW_END * 60; t += STEP_MIN) {
      var st = wall(y, m, d, Math.floor(t / 60), t % 60);
      if (st >= now + LEAD_MIN * 60000) cands.push([st, st + SLOT_MIN * 60000]);
    }
    if (cands.length) days.push({k: k, y: y, m: m, d: d, key: y + "-" + pad2(m) + "-" + pad2(d), cands: cands});
  }
  return days;
}

function busyBlocks(lo, hi) {
  var blocks = [];
  BUSY_CALENDARS.forEach(function (id) {
    var cal = id === "primary" ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(id);
    if (!cal) return;
    cal.getEvents(new Date(lo), new Date(hi)).forEach(function (ev) {
      try { if (ev.getTransparency && ev.getTransparency() === CalendarApp.EventTransparency.TRANSPARENT) return; } catch (e) {}
      try { if (ev.getMyStatus && ev.getMyStatus() === CalendarApp.GuestStatus.NO) return; } catch (e) {}
      blocks.push([ev.getStartTime().getTime(), ev.getEndTime().getTime()]);
    });
  });
  return blocks;
}

function overlaps(blocks, s, e) {
  return blocks.some(function (b) { return b[0] < e && b[1] > s; });
}

/* Every candidate day with its open slots. One calendar read covers the whole window. */
function openDays() {
  var days = candidateDays();
  if (!days.length) return [];
  var first = days[0], last = days[days.length - 1];
  var blocks = busyBlocks(wall(first.y, first.m, first.d, 0, 0), wall(last.y, last.m, last.d + 1, 0, 0));
  return days.map(function (day) {
    return {k: day.k, key: day.key, open: day.cands.filter(function (c) { return !overlaps(blocks, c[0], c[1]); }).slice(0, MAX_SLOTS)};
  }).filter(function (d) { return d.open.length; });
}

function firstOpenDay() {
  var days = openDays();
  return days.length ? {k: days[0].k, open: days[0].open} : null;
}

function isOfferedSlot(start) {
  return candidateDays().some(function (day) { return day.cands.some(function (c) { return c[0] === start; }); });
}

function isBusy(start, end) {
  return overlaps(busyBlocks(start - 3600000, end + 3600000), start, end);
}

/* ---------- Bookings sheet ---------- */

function sheet() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty("SHEET_ID");
  var ss = null;
  if (id) { try { ss = SpreadsheetApp.openById(id); } catch (e) { ss = null; } }
  if (!ss) {
    ss = SpreadsheetApp.create(SHEET_NAME);
    props.setProperty("SHEET_ID", ss.getId());
  }
  var sh = ss.getSheets()[0];
  if (sh.getName() !== "Bookings") sh.setName("Bookings");
  if (sh.getLastRow() === 0) {
    sh.appendRow(COLS);
    sh.setFrozenRows(1);
  } else {
    /* Columns added since the sheet was made (2026-10-03: the day-before reminder, the check answers, fbclid) are
       appended to the header in COLS order, so appendRow's values keep landing under the right names. */
    var head = sh.getRange(1, 1, 1, Math.max(1, sh.getLastColumn())).getValues()[0];
    while (head.length && !head[head.length - 1]) head.pop();
    var missing = COLS.filter(function (c) { return head.indexOf(c) === -1; });
    if (missing.length) sh.getRange(1, head.length + 1, 1, missing.length).setValues([missing]);
  }
  return sh;
}

function bookingRow(body, start, ev) {
  var booked = Date.now();
  var vtz = validTz(body.viewer_timezone) ? body.viewer_timezone : TZ;
  var row = {
    booked_at: new Date(booked),
    name: body.name, email: body.email, phone: body.phone || "", technicians: body.technicians || "",
    start_iso: new Date(start).toISOString(),
    start_eastern: fmtWhen(start, TZ),
    start_local: fmtWhen(start, vtz),
    meet: ev.hangoutLink || "", event_id: ev.id, page: body.page || "",
    viewer_timezone: body.viewer_timezone || "",
    utm_source: body.utm_source || "", utm_medium: body.utm_medium || "", utm_campaign: body.utm_campaign || "",
    utm_content: body.utm_content || "", utm_id: body.utm_id || "", landing_url: body.landing_url || "",
    status: "booked", confirm_sent: "", enrich_due: "", enrich_sent: "", remind_due: "", remind_sent: "",
    daybefore_due: "", daybefore_sent: "",
    installs: body.installs || "", last_five: body.last_five || "", ads_today: body.ads_today || "", fbclid: body.fbclid || ""
  };
  var due = dripDue(booked, start);
  row.enrich_due = due.enrich ? new Date(due.enrich) : "";
  row.enrich_sent = due.enrich ? "" : "skipped";
  row.daybefore_due = due.dayBefore ? new Date(due.dayBefore) : "";
  row.daybefore_sent = due.dayBefore ? "" : "skipped";
  row.remind_due = due.remind ? new Date(due.remind) : "";
  row.remind_sent = due.remind ? "" : "skipped";
  return row;
}

/* Reminder: one hour before the call; skipped when the booking lands inside that hour (the confirmation already
   carries the link). Enrichment, when ENRICH_ENABLED: 3 hours after booking, or 8:00 am Eastern next day when booked
   after 5 pm (or before 7 am), skipped when that would land inside the last hour before the call. */
function dripDue(booked, start) {
  var enrich = 0;
  if (ENRICH_ENABLED) {
    enrich = booked + ENRICH_AFTER_MIN * 60000;
    var ep = easternParts(booked);
    if (ep.h >= EVENING_HOUR) enrich = wall(ep.y, ep.m, ep.d + 1, MORNING_HOUR, 0);
    else if (ep.h < 7) enrich = wall(ep.y, ep.m, ep.d, MORNING_HOUR, 0);
    if (enrich > start - 60 * 60000) enrich = 0;
  }
  var remind = start - REMIND_BEFORE_MIN * 60000;
  if (remind < booked + 5 * 60000) remind = 0;
  /* The day-before reminder (2026-10-03): 4:00 pm Eastern on the day before the call, skipped when the booking lands
     after that (the confirmation already carries the link). A Monday call gets it on Sunday. */
  var sp = easternParts(start);
  var dayBefore = wall(sp.y, sp.m, sp.d - 1, DAYBEFORE_HOUR, 0);
  if (dayBefore < booked + 5 * 60000) dayBefore = 0;
  return {enrich: enrich, remind: remind, dayBefore: dayBefore};
}

function appendRow(row) {
  sheet().appendRow(COLS.map(function (c) { return row[c] === undefined ? "" : row[c]; }));
}

function rowsAsObjects(sh) {
  var data = sh.getDataRange().getValues();
  var head = data[0] || [];
  var idx = {};
  head.forEach(function (h, i) { idx[h] = i; });
  var rows = [];
  for (var r = 1; r < data.length; r++) {
    var o = {_row: r + 1};
    COLS.forEach(function (c) { o[c] = idx[c] === undefined ? "" : data[r][idx[c]]; });
    rows.push(o);
  }
  return {rows: rows, idx: idx};
}

function setCell(sh, idx, rowNum, col, value) {
  if (idx[col] === undefined) return;
  sh.getRange(rowNum, idx[col] + 1).setValue(value);
}

function toMs(v) {
  if (!v) return 0;
  if (v instanceof Date) return v.getTime();
  var t = Date.parse(v);
  return isNaN(t) ? 0 : t;
}

/* ---------- The queue: one trigger, every 15 minutes ---------- */

function installQueue() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === "processQueue") ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger("processQueue").timeBased().everyMinutes(QUEUE_EVERY_MIN).create();
  Logger.log("processQueue runs every " + QUEUE_EVERY_MIN + " minutes.");
}

function processQueue() {
  var sh = sheet();
  var data = rowsAsObjects(sh);
  var now = Date.now();
  data.rows.forEach(function (row) {
    if (row.status !== "booked") return;
    var start = toMs(row.start_iso);
    if (eventCancelled(row.event_id)) { setCell(sh, data.idx, row._row, "status", "cancelled"); return; }
    if (row.enrich_due && !row.enrich_sent && toMs(row.enrich_due) <= now) {
      try { sendMail(row.email, enrichEmail(row)); setCell(sh, data.idx, row._row, "enrich_sent", new Date()); }
      catch (e) { console.error("enrich failed for " + row.email + ": " + e); }
    }
    if (row.daybefore_due && !row.daybefore_sent && toMs(row.daybefore_due) <= now) {
      try { sendMail(row.email, dayBeforeEmail(row)); setCell(sh, data.idx, row._row, "daybefore_sent", new Date()); }
      catch (e) { console.error("day-before reminder failed for " + row.email + ": " + e); }
    }
    if (row.remind_due && !row.remind_sent && toMs(row.remind_due) <= now) {
      try { sendMail(row.email, remindEmail(row)); setCell(sh, data.idx, row._row, "remind_sent", new Date()); }
      catch (e) { console.error("reminder failed for " + row.email + ": " + e); }
    }
    if (start && start + 60 * 60000 < now) setCell(sh, data.idx, row._row, "status", "done");
  });
}

function eventCancelled(eventId) {
  if (!eventId) return false;
  try {
    var ev = Calendar.Events.get(BOOK_CALENDAR, eventId);
    if (!ev || ev.status === "cancelled") return true;
    var guests = (ev.attendees || []).filter(function (a) { return !a.organizer && !a.self; });
    return guests.length > 0 && guests.every(function (a) { return a.responseStatus === "declined"; });
  } catch (e) {
    return String(e && e.message || e).indexOf("Not Found") > -1;
  }
}

/* ---------- Email ---------- */

function validTz(tz) {
  if (!tz) return false;
  try { Utilities.formatDate(new Date(), tz, "H"); return true; } catch (e) { return false; }
}
function lowerAmPm(s) { return s.replace(/\bAM\b/g, "am").replace(/\bPM\b/g, "pm"); }
function fmtWhen(ms, tz) {                            // "Thursday, Sep 24, 2:00 pm EDT"
  return lowerAmPm(Utilities.formatDate(new Date(ms), tz, "EEEE, MMM d, h:mm a z"));
}
function fmtClock(ms, tz) {                           // "2:00 pm EDT"
  return lowerAmPm(Utilities.formatDate(new Date(ms), tz, "h:mm a z"));
}
function dayWord(ms, tz) {                            // "Today", "Tomorrow", or the weekday
  var a = Utilities.formatDate(new Date(), tz, "yyyy-MM-dd"), b = Utilities.formatDate(new Date(ms), tz, "yyyy-MM-dd");
  if (a === b) return "Today";
  var t = new Date(); t.setTime(t.getTime() + 86400000);
  if (Utilities.formatDate(t, tz, "yyyy-MM-dd") === b) return "Tomorrow";
  return Utilities.formatDate(new Date(ms), tz, "EEEE");
}
function firstName(name) { return String(name || "").trim().split(/\s+/)[0] || "there"; }
function when(row) {
  var start = toMs(row.start_iso);
  var vtz = validTz(row.viewer_timezone) ? row.viewer_timezone : TZ;
  var local = fmtWhen(start, vtz);
  var same = vtz === TZ || fmtClock(start, vtz) === fmtClock(start, TZ);
  return {start: start, vtz: vtz, local: local, eastern: fmtClock(start, TZ), both: same ? local : local + " (" + fmtClock(start, TZ) + " Eastern)"};
}

/* Copy lives in templates/booking-drip.md. Change both together. */
function confirmEmail(row) {
  var w = when(row);
  return {
    subject: "Booked: " + Utilities.formatDate(new Date(w.start), w.vtz, "EEEE") + " at " + fmtClock(w.start, w.vtz) + " with Monarc Build",
    body: firstName(row.name) + ",\n\n" +
      "Booked. " + w.both + ". Fifteen minutes on Google Meet: " + row.meet + "\n\n" +
      "Before the call we pull your search results, your pages, and your ad account. Reply with your site URL and the metro you sell in and the audit goes deeper.\n\n" +
      "Reminders with the same link come the afternoon before and an hour before. Bring nothing.\n\n" +
      "My Best,\nMonarc Build"
  };
}
function enrichEmail(row) {
  var w = when(row);
  return {
    subject: "Before our call",
    body: firstName(row.name) + ",\n\n" +
      "One example of what we look for. We ranked an integrator #1 for \"whole home audio in Annapolis.\" A contractor restoring a Georgian Colonial found the page: $70k of James Loudspeaker, wired from rough-in. That one contractor is now over $500k in lifetime value.\n\n" +
      "On the call we walk your search results the same way: what ranks, what the ads are buying, and what a page per service would change. You leave with the audit either way.\n\n" +
      w.both + ". Meet link: " + row.meet + "\n\n" +
      "Monarc Build"
  };
}
function remindEmail(row) {
  var w = when(row);
  return {
    subject: "In one hour: your Monarc Build call, " + fmtClock(w.start, w.vtz),
    body: firstName(row.name) + ",\n\n" +
      "Your Monarc Build call is in one hour, at " + fmtClock(w.start, w.vtz) + (w.vtz === TZ ? "" : " (" + w.eastern + " Eastern)") + ". Fifteen minutes on Google Meet: " + row.meet + "\n\n" +
      "If the time no longer works, reply with two others.\n\n" +
      "Monarc Build"
  };
}
/* The day-before reminder (2026-10-03), 4:00 pm Eastern the day before; "Tomorrow" or the weekday from dayWord. */
function dayBeforeEmail(row) {
  var w = when(row);
  var day = dayWord(w.start, w.vtz);
  return {
    subject: day + " at " + fmtClock(w.start, w.vtz) + ": your Monarc Build call",
    body: firstName(row.name) + ",\n\n" +
      day + ", " + w.both + ". Fifteen minutes on Google Meet: " + row.meet + "\n\n" +
      "Before the call we pull your search results and your pages. If the time no longer works, reply with two others.\n\n" +
      "Monarc Build"
  };
}
function notifyEmail(row) {
  var w = when(row);
  var check = checkLine(row);
  var lines = [
    row.name + " booked " + fmtWhen(w.start, TZ) + ".",
    "",
    "Email: " + row.email,
    "Phone: " + (row.phone || "none given"),
    "Technicians: " + (row.technicians || "not answered"),
    check,
    "Their time: " + w.local + (row.viewer_timezone ? " (" + row.viewer_timezone + ")" : ""),
    "Meet: " + row.meet,
    "Event: " + row.event_id,
    "Page: " + (row.page || "") + (row.utm_source ? "  Source: " + row.utm_source : "") + (row.utm_campaign ? "  Campaign: " + row.utm_campaign : "") + (row.utm_content ? "  Content: " + row.utm_content : "") + (row.utm_id ? "  Id: " + row.utm_id : ""),
    row.landing_url ? "Landing URL: " + row.landing_url : "",
    row.journeyLine || "",
    "",
    "Drip: confirmation sent now; enrichment " + (row.enrich_due ? fmtWhen(toMs(row.enrich_due), TZ) : "skipped") + "; day-before " + (row.daybefore_due ? fmtWhen(toMs(row.daybefore_due), TZ) : "skipped") + "; reminder " + (row.remind_due ? fmtWhen(toMs(row.remind_due), TZ) : "skipped") + ".",
    "CRM: " + (row.crm || "not attempted") + ".",
    "Sheet: " + SHEET_NAME + " (script properties SHEET_ID)."
  ].filter(function (l) { return l !== ""; });
  return {subject: "Booked: " + row.name + ", " + fmtWhen(w.start, TZ), body: lines.join("\n")};
}

function htmlBody(text) {
  var esc = String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  esc = esc.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1">$1</a>');
  return '<div style="font-family:\'Times New Roman\',Times,serif;font-size:12pt;white-space:pre-wrap">' + esc + "</div>";
}

/* Plain text plus a Times New Roman 12pt HTML part (references/mycopy.md rule 1). Reply-to Jonathan. */
function sendMail(to, msg, replyTo) {
  var opts = {name: FROM_NAME, replyTo: replyTo || REPLY_TO, htmlBody: htmlBody(msg.body)};
  if (SEND_AS) {
    opts.from = SEND_AS;
    GmailApp.sendEmail(to, msg.subject, msg.body, opts);
  } else {
    opts.to = to; opts.subject = msg.subject; opts.body = msg.body;
    MailApp.sendEmail(opts);
  }
}

/* ---------- Run once from the editor ---------- */

/* Creates the bookings sheet (grants the Sheets scope) and logs its URL. */
function setup() {
  var sh = sheet();
  Logger.log("Bookings sheet: " + sh.getParent().getUrl());
}

/* Grants the calendar scopes and confirms the setup. Check the log. */
function selfTest() {
  var found = firstOpenDay();
  Logger.log(found ? found.open.map(function (s) { return Utilities.formatDate(new Date(s[0]), TZ, "EEE MMM d h:mm a z"); }) : "no open slot in the window");
  Logger.log("Open days in the window: " + openDays().length);
  Logger.log("Book calendar: " + (CalendarApp.getCalendarById(BOOK_CALENDAR) ? CalendarApp.getCalendarById(BOOK_CALENDAR).getName() : "NOT FOUND"));
}

/* Sends the four emails to the script owner with a sample booking (tomorrow 2:00 pm Eastern, a Pacific prospect). Nothing is booked or logged. */
function dripSelfTest() {
  var me = Session.getEffectiveUser().getEmail();
  var t = todayEastern();
  var start = wall(t.y, t.m, t.d + 1, 14, 0);
  var row = {
    name: "Sample Prospect", email: me, phone: "555 555 0100", technicians: "3 to 5",
    installs: "Lutron or Ketra", last_five: "Referrals", ads_today: "Never",
    start_iso: new Date(start).toISOString(), start_eastern: fmtWhen(start, TZ), start_local: fmtWhen(start, "America/Los_Angeles"),
    meet: "https://meet.google.com/xxx-xxxx-xxx", event_id: "sample", page: "avmarketing", viewer_timezone: "America/Los_Angeles",
    utm_source: "linkedin", utm_medium: "paid-social", utm_campaign: "sample", utm_content: "", utm_id: "", landing_url: "https://monarcbuild.com/avmarketing/",
    status: "booked"
  };
  var due = dripDue(Date.now(), start);
  row.enrich_due = due.enrich ? new Date(due.enrich) : ""; row.remind_due = due.remind ? new Date(due.remind) : "";
  row.daybefore_due = due.dayBefore ? new Date(due.dayBefore) : "";
  row.crm = "sample, nothing posted";
  sendMail(me, confirmEmail(row));
  if (ENRICH_ENABLED) sendMail(me, enrichEmail(row));
  sendMail(me, dayBeforeEmail(row));
  sendMail(me, remindEmail(row));
  sendMail(me, notifyEmail(row), me);
  Logger.log((ENRICH_ENABLED ? "Five" : "Four") + " sample emails sent to " + me + ". Enrichment " + (row.enrich_due || "off") + ", day-before due " + (row.daybefore_due || "skipped") + ", reminder due " + (row.remind_due || "skipped") + ".");
}
