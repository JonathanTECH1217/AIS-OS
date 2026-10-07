// Monarc Calls at its real size: a third of Jonathan's screen (510 x 780) beside Airtable's grid. Nothing spills
// sideways, the bar stays on top, a card's lines and buttons fit the width, and the main area scrolls on its own.
import { testCalls, until } from "./harness.js";

testCalls("calls-layout", async (t, ca) => {
  const C = ca.C;
  t.eq("the window is 510 x 780", [innerWidth, innerHeight], [510, 780]);
  t.ok("nothing spills sideways", document.documentElement.scrollWidth <= innerWidth);
  const bar = document.getElementById("cl-bar").getBoundingClientRect();
  t.ok("the bar runs across the top", bar.top === 0 && Math.round(bar.width) === innerWidth && bar.height <= 56, JSON.stringify(bar));
  // the card t-calls left to file (Echo Systems) shows before Start
  await until(() => document.querySelector(".cl-card"), 4000);
  const card = document.querySelector(".cl-card");
  t.ok("a card waiting to be filed shows before Start", !!card);
  if (card) {
    const r = card.getBoundingClientRect();
    t.ok("the card fits the width", r.left >= 0 && r.right <= innerWidth, JSON.stringify(r));
    const btns = [...card.querySelectorAll(".cl-card-actions .btn")];
    t.ok("its buttons sit inside it", btns.length === 3 && btns.every((b) => { const x = b.getBoundingClientRect(); return x.right <= r.right + 0.5 && x.left >= r.left - 0.5; }));
    const row = card.querySelector(".cl-row");
    t.ok("a note line: kind, text, take-out, in one row", row && row.children.length === 3 && Math.abs(row.children[0].getBoundingClientRect().top - row.children[1].getBoundingClientRect().top) < 2);
  }
  const mainEl = document.getElementById("cl-main");
  t.ok("the main area scrolls by itself (the page doesn't)", getComputedStyle(mainEl).overflowY === "auto" && document.documentElement.scrollHeight <= innerHeight + 1);
  // Start again: the live section fits under the bar
  document.querySelector(".cl-go").click();
  await until(() => C.view && C.view.listening, 6000);
  const live = document.querySelector(".cl-live").getBoundingClientRect();
  t.ok("the live notes sit under the bar, full width", live.top >= bar.bottom && live.right <= innerWidth, JSON.stringify(live));
  await ca.send("stop");
  await until(() => C.view && !C.view.active, 4000);
});
