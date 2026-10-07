import { test, wait, until } from "./harness.js";

// Make trailer (Jonathan 2026-09-30, T1-T4): the peak (I to O) goes first, the call reaches back to its last ring,
// the Riser lands at the hard cut, and a black-on-white headline sits in the top third through the peak, fading in over
// 6 frames and never moving. The tests pass the headline and the ring in, so nothing calls Claude.
test("trailer", async (t, st) => {
  await t.fresh();                                      // m01: source frames 30-210 on the timeline at 0-180
  const len0 = st.doc.seqEnd(st.S.doc);
  const v0 = t.clip("V1")[0];
  t.ok("Make trailer waits for the marks", !st.actions.get("makeTrailer").enabled());
  st.history.commit("marks", (d) => { d.range = { in: 60, out: 120 }; });
  t.ok("with I and O set it's on", st.actions.get("makeTrailer").enabled());
  const res = await st.actions.run("makeTrailer", { options: ["She said no four times"], pick: "She said no four times, then this happened", ring: null });
  await wait(30);
  t.ok("the trailer is made", res && res.ok, JSON.stringify(res));
  const v = t.clip("V1");
  t.eq("the peak opens the short: source 90-150 at 0-60", [v[0].start, v[0].in, v[0].out], [0, 90, 150]);
  t.eq("then the call, moved right by the peak", [v[1].start, v[1].in], [60, 30]);
  t.ok("the peak's pieces are linked to each other, not to the call", v[0].link && v[0].link !== v[1].link
    && t.clip("A1")[0].link === v[0].link && t.clip("A2")[0].link === v[0].link);
  t.ok("the voice tracks come along (You and Them)", t.clip("A1")[0].voice === "me" && t.clip("A2")[0].voice === "them");
  t.eq("the short grew by the peak", st.doc.seqEnd(st.S.doc), len0 + 60);
  const h = st.S.doc.clips.find((c) => c.type === "text");
  t.ok("a headline through the peak", h && h.start === 0 && h.out - h.in === 60, JSON.stringify(h));
  t.ok("black words on a white box", h.text.color === "#000000" && h.text.bg === "#FFFFFF" && !h.text.strokeW);
  t.ok("in the top third, and it never moves", h.fx.posY.v === 480 && h.fx.posX.v === 540 && !h.fx.posY.k && !h.fx.posX.k);
  t.eq("it fades in over 6 frames", h.fx.opacity.k.map((k) => [k.t, k.v]), [[0, 0], [6, 100]]);
  t.ok("long headlines wrap to fit", h.text.str.includes("\n"), JSON.stringify(h.text.str));
  const m = (s) => s.length * 40;
  t.eq("wrapped lines come out even, no word alone at the end", st.trailer.wrapHeadline("She said no four times", m, 700), "She said no\nfour times");
  const riser = t.clip("A3").find((c) => st.lib.asset(c.asset).name === "Riser.wav");
  t.ok("the Riser starts at the hard cut, on Sounds", riser && riser.start === 60, JSON.stringify(t.clip("A3")));
  t.eq("the marks are cleared", [st.S.doc.range.in, st.S.doc.range.out], [null, null]);
  // the monitor draws the headline box
  st.pb.seek(20); await t.settle();
  const cv = document.querySelector(".mon-program");
  const k = cv.width / 1080;
  const box = cv.getContext("2d").getImageData(Math.round(120 * k), Math.round(420 * k), Math.round(840 * k), Math.round(120 * k)).data;
  let white = 0, black = 0;
  for (let i = 0; i < box.length; i += 4) { if (box[i] > 245 && box[i + 1] > 245 && box[i + 2] > 245) white += 1; if (box[i] < 30 && box[i + 1] < 30 && box[i + 2] < 30) black += 1; }
  t.ok("the monitor shows a white box with black words in the top third", white > box.length / 4 / 3 && black > 200, `${white} white, ${black} black`);
  // the export draws the same box (the still of that frame)
  await st.save.flush(true);
  const img = new Image();
  img.src = `/api/projects/${encodeURIComponent(st.S.doc.id)}/still?f=20&t=${Date.now()}`;
  await img.decode();
  const c2 = document.createElement("canvas"); c2.width = 1080; c2.height = 1920;
  const g2 = c2.getContext("2d"); g2.drawImage(img, 0, 0);
  const sbox = g2.getImageData(120, 420, 840, 120).data;
  let sw = 0;
  for (let i = 0; i < sbox.length; i += 4) if (sbox[i] > 245 && sbox[i + 1] > 245 && sbox[i + 2] > 245) sw += 1;
  const mw = white / (k * k);
  t.ok("the export draws the same white box", sw > 0 && Math.abs(sw - mw) / Math.max(sw, mw) < 0.15, `${sw} vs ${Math.round(mw)}`);
  st.history.undo(); await wait(30);
  t.eq("one undo takes the whole trailer back", st.doc.seqEnd(st.S.doc), len0);
  // with a ring found before the call: the call reaches back to just before the ring
  st.history.commit("marks", (d) => { d.range = { in: 60, out: 120 }; });
  const res2 = await st.actions.run("makeTrailer", { options: ["x"], pick: "Short one", ring: 0 });
  await wait(30);
  const w = t.clip("V1");
  t.eq("the call now starts at the ring (source 0), right after the peak", [w[1].start, w[1].in], [60, 0]);
  t.ok("its audio reaches back with it", t.clip("A1").some((c) => c.start === 60 && c.in === 0) && t.clip("A2").some((c) => c.start === 60 && c.in === 0));
  t.ok("the toast says what was done", /Trailer made/.test(document.getElementById("toast").textContent));
  st.history.undo();
});
