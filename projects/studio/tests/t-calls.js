// Monarc Calls, the notes window (reworked 2026-10-03) against the stand-ins: the test microphone says lines
// (/api/session/fake {say}), Jonathan's Status in Airtable is played by /api/session/fake {status}. Start, live notes,
// a Status turning them into a card, edits, Push, a no-notes call filed by itself, a skip word, Pause, Stop.
import { testCalls, wait, until } from "./harness.js";

const fake = (body) => fetch("/api/session/fake", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then((r) => r.json());
const main = () => document.getElementById("cl-main").textContent;
const cards = () => [...document.querySelectorAll(".cl-card")];

testCalls("calls", async (t, ca) => {
  const C = ca.C;
  t.ok("the check lines say what's ready", /Test microphone/.test(main()) && /columns OK/.test(main()) && /phrases/.test(main()), main().slice(0, 300));
  const go = document.querySelector(".cl-go");
  t.ok("Start is ready", go && !go.disabled);
  go.click();
  await until(() => C.view && C.view.active && C.view.listening, 6000);
  t.ok("Start: listening, the dot on", C.view.listening && document.querySelector(".cl-dot").classList.contains("on")
    && /Listening/.test(document.getElementById("cl-bar").textContent));

  const heard = async (text) => { const k = (C.view.live || {}).heard || 0; await fake({ say: text }); await until(() => C.view.live && C.view.live.heard > k, 4000); };
  await heard("Hey, this is Mike with Acme.");
  await heard("We do mostly residential, but we're short on techs.");
  await heard("Sure, it's mike at acme a v dot com.");
  await until(() => document.querySelectorAll(".cl-live .cl-group").length >= 4, 3000);
  const kinds = [...document.querySelectorAll(".cl-live .cl-kind")].map((x) => x.textContent);
  t.eq("live notes by kind, in order", kinds, ["Offering", "Constraint", "Email", "Name"]);
  t.ok("the matched phrase is bold", [...document.querySelectorAll(".cl-live .cl-note b")].some((b) => b.textContent === "short on techs"));
  t.ok("the email is put together", /mike@acmeav\.com/.test(document.querySelector(".cl-live").textContent));

  await fake({ status: { rec: "recAcme0000001", words: "Callback." } });
  await until(() => cards().length === 1, 5000);
  const card = cards()[0];
  t.ok("typing Status makes a card named by the row", card && /Acme Audio Video/.test(card.textContent) && /MB-03501/.test(card.textContent) && /Callback\./.test(card.textContent));
  t.ok("and the live notes start over", /Key notes show here/.test(document.querySelector(".cl-live").textContent));
  const texts = [...card.querySelectorAll(".cl-row-text")];
  t.ok("every note is an editable line", texts.length >= 4, String(texts.length));
  // edit one, take one out, add one
  const off = [...card.querySelectorAll(".cl-row")].find((r) => r.querySelector(".cl-row-kind").value === "offering");
  const ta = off.querySelector(".cl-row-text");
  ta.value = "Mostly residential, some commercial."; ta.dispatchEvent(new Event("input", { bubbles: true }));
  const nameRow = [...card.querySelectorAll(".cl-row")].find((r) => r.querySelector(".cl-row-kind").value === "name");
  nameRow.querySelector(".icon-btn").click();
  [...card.querySelectorAll(".cl-card-actions .btn")].find((b) => /Add/.test(b.textContent)).click();
  const rows = [...card.querySelectorAll(".cl-row")];
  const added = rows[rows.length - 1];
  added.querySelector(".cl-row-kind").value = "objection"; added.querySelector(".cl-row-kind").dispatchEvent(new Event("change"));
  added.querySelector(".cl-row-text").value = "Wants to wait until spring."; added.querySelector(".cl-row-text").dispatchEvent(new Event("input", { bubbles: true }));
  // a new line heard meanwhile re-renders the window: the edits stay
  await heard("Okay, talk soon.");
  t.ok("edits survive the window updating", cards()[0] === card && card.querySelector(".cl-row-text").value !== "" &&
    [...card.querySelectorAll(".cl-row-text")].some((x) => x.value === "Wants to wait until spring."));
  [...card.querySelectorAll(".cl-card-actions .btn")].find((b) => /Push to file/.test(b.textContent)).click();
  await until(() => cards().length === 0, 4000);
  await until(() => /Acme Audio Video/.test(document.querySelector(".cl-filed").textContent), 3000);
  t.ok("Push files the card", cards().length === 0 && /Filed/.test(main()) && /Acme Audio Video/.test(document.querySelector(".cl-filed").textContent),
    `${cards().length} cards; filed: ${document.querySelector(".cl-filed").textContent.slice(0, 120)}`);
  await until(async () => { const d = await (await fetch("/api/session/fake")).json(); return d.contacts.records.find((r) => r.id === "recAcme0000001").fields.Email; }, 5000);
  const base = await (await fetch("/api/session/fake")).json();
  const acme = base.contacts.records.find((r) => r.id === "recAcme0000001").fields;
  t.ok("Push fills the blank Email; no name was kept, so Owner stays blank", acme.Email === "mike@acmeav.com" && !acme.Owner, JSON.stringify(acme));
  const log1 = base.log.records.find((r) => r.fields.Channel === "Cold Call" && r.fields["Company ID"] === "MB-03501");
  await until(async () => { const d = await (await fetch("/api/session/fake")).json(); return (d.log.records.find((r) => r.fields["Company ID"] === "MB-03501" && r.fields.Channel === "Cold Call") || { fields: {} }).fields.Transcript; }, 5000);
  const base2 = await (await fetch("/api/session/fake")).json();
  const t1 = (base2.log.records.find((r) => r.fields["Company ID"] === "MB-03501" && r.fields.Channel === "Cold Call") || { fields: {} }).fields.Transcript || "";
  t.ok("the dial's Outreach Log row, with the kept notes in Transcript", log1 && /Offering: Mostly residential, some commercial\./.test(t1) && /Objection: Wants to wait until spring\./.test(t1) && !/Name:/.test(t1), t1);

  await heard("Do you want to make more money?");
  await fake({ status: { rec: "recBrio0000002", words: "Wrong vertical." } });
  await wait(1200);
  t.ok("a skip word makes no card and no cut", cards().length === 0 && C.view.calls === 1, String(C.view.calls));
  await heard("Hello? Sorry, wrong number.");
  await fake({ status: { rec: "recCrest000003", words: "No answer." } });
  await until(() => C.view.calls === 2 && (C.view.filed || []).some((f) => f.name === "Crest Smart Homes"), 5000);
  await until(() => /words only/.test(document.querySelector(".cl-filed").textContent), 3000);
  t.ok("a call with no key notes files its words, no card", cards().length === 0 && /words only/.test(document.querySelector(".cl-filed").textContent),
    `${cards().length} cards; filed: ${document.querySelector(".cl-filed").textContent.slice(0, 160)}`);

  document.querySelector(".cl-bar .btn.quiet").click();      // Pause
  await until(() => C.view && !C.view.listening, 3000);
  t.ok("Pause: the dot goes amber, the button says Resume", document.querySelector(".cl-dot").classList.contains("paused") && /Resume/.test(document.getElementById("cl-bar").textContent));
  const k = C.view.live.heard;
  await fake({ say: "this is not heard" });
  await wait(700);
  t.eq("nothing is heard while paused", C.view.live.heard, k);
  document.querySelector(".cl-bar .btn.quiet").click();      // Resume
  await until(() => C.view && C.view.listening, 3000);
  t.ok("Resume", C.view.listening);

  await heard("We're all set, thanks.");
  await fake({ status: { rec: "recEcho0000005", words: "No." } });
  await until(() => cards().length === 1, 5000);
  document.querySelector(".cl-stop").click();
  const ok = await until(() => [...document.querySelectorAll(".dialog .btn")].find((b) => b.textContent === "End session"), 2000);
  t.ok("Stop asks first", !!ok);
  ok.click();
  await until(() => C.view && !C.view.active, 4000);
  t.ok("Stop: the start panel is back, the open card stays to file", !C.view.active && /Start/.test(main()) && cards().length === 1);
});
