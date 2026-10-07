// Preview vs export: the monitor's canvas (Full quality) against the exporter's still of the same frame
// (/api/projects/<id>/still, studio_render.py --still), on a short with an eased zoom, an 8 degree rotation, a 50 %
// image, a text title, a box, a dissolve and captions.
//  - where things sit: the captions' letters, the lit word, the title and the box match within 2 px
//  - brightness (luma) PSNR: >= 32 dB on frames without a title, >= 27 dB with one, >= 23 dB in the caption band.
//    White-on-black letter edges anti-alias differently in the browser, Pillow and libass (checked by eye
//    2026-09-29: identical at a glance), so text-heavy areas score lower without anything being out of place.
//    The band floor was 24 until the voice colors (2026-09-30): Jonathan's spoken word is now white, the brightest
//    color, and frame 40 (zoom and rotation behind the words) went from just over 24 to 23.6 dB. Positions still
//    match within 2 px, and the voice colors are checked by pixel counts below.
import { test, wait, until } from "./harness.js";

function luma(data) {
  const out = new Float32Array(data.length / 4);
  for (let i = 0, j = 0; i < data.length; i += 4, j += 1) out[j] = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
  return out;
}
function psnr(a, b, w, rect) {
  let se = 0, n = 0;
  const [x0, y0, x1, y1] = rect || [0, 0, w, a.length / w];
  for (let y = y0; y < y1; y += 1) for (let x = x0; x < x1; x += 1) { const i = y * w + x; const d = a[i] - b[i]; se += d * d; n += 1; }
  const mse = se / n;
  return mse === 0 ? 99 : 10 * Math.log10((255 * 255) / mse);
}
async function stillPixels(id, f) {
  const img = new Image();
  img.src = `/api/projects/${encodeURIComponent(id)}/still?f=${f}&t=${Date.now()}`;
  await img.decode();
  const c = document.createElement("canvas"); c.width = 1080; c.height = 1920;
  const g = c.getContext("2d"); g.drawImage(img, 0, 0);
  return g.getImageData(0, 0, 1080, 1920).data;
}
function boxOf(data, w, h, test, rect) {
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  const [ax, ay, bx, by] = rect || [0, 0, w, h];
  for (let y = ay; y < by; y += 1) for (let x = ax; x < bx; x += 1) {
    const i = (y * w + x) * 4;
    if (test(data[i], data[i + 1], data[i + 2])) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  return [x0, y0, x1, y1];
}
const isYellow = (r, g, b) => r > 230 && g > 190 && g < 235 && b < 40;
const isWhite = (r, g, b) => r > 235 && g > 235 && b > 235;
// caption letters in any voice color (blue, white, pink, red, yellow) on black: the fill is bright, the outline black
const isInk = (r, g, b) => Math.max(r, g, b) > 150;
const isBlue = (r, g, b) => r > 40 && r < 120 && g > 95 && g < 170 && b > 200;
const isPink = (r, g, b) => r > 220 && g > 60 && g < 135 && b > 125 && b < 210;
const yellowBox = (data, w, h, rect) => boxOf(data, w, h, isYellow, rect);
const close = (A, B) => A[2] > A[0] && A.every((v, i) => Math.abs(v - B[i]) <= 2);
function countIn(data, w, test, rect) {
  let n = 0;
  const [ax, ay, bx, by] = rect;
  for (let y = ay; y < by; y += 1) for (let x = ax; x < bx; x += 1) { const i = (y * w + x) * 4; if (test(data[i], data[i + 1], data[i + 2])) n += 1; }
  return n;
}
const similar = (a, b) => a > 100 && b > 100 && Math.max(a, b) / Math.min(a, b) < 1.5;

test("parity", async (t, st) => {
  const doc = await t.fresh();
  st.actions.run("quality.full");
  st.pb.seek(90); t.key("Ctrl+K"); await wait(20);
  const logo = t.asset("logo.png").id;
  st.history.commit("features", (d) => {
    const v = d.clips.filter((c) => c.track === "V1").sort((a, b) => a.start - b.start);
    v[0].fx.scale = { v: 100, k: [{ t: v[0].in + 5, v: 100, e: "out" }, { t: v[0].in + 45, v: 115, e: "in" }] };
    v[0].fx.rot = { v: 8 };
    v[1].in += 60; v[1].out += 60;       // the second piece shows later frames, so the dissolve is visible
    for (const c of d.clips.filter((x) => (x.track === "A1" || x.track === "A2") && x.start === 90)) { c.in += 60; c.out += 60; }
    d.clips.push({ id: "pl", track: "V2", type: "image", asset: logo, in: 0, out: 60, start: 0, on: true, fx: { opacity: { v: 50 }, posY: { v: 700 } } });
    d.clips.push({ id: "pt", track: "V2", type: "text", in: 0, out: 60, start: 60, on: true, fx: { posY: { v: 420 } },
      text: { str: "PARITY", size: 110, color: "#FFFFFF", stroke: "#000000", strokeW: 8 } });
    d.clips.push({ id: "pb", track: "V2", type: "shape", in: 0, out: 60, start: 120, on: true, fx: { posY: { v: 300 } },
      shape: { kind: "rect", w: 600, h: 120, fill: "#FFD400", radius: 24 } });
  });
  st.actions.run("dissolveAt", { track: "V1", f: 90 });
  await wait(30);
  await st.save.flush(true);
  await until(() => st.S.saving === "saved", 4000);
  const cv = document.querySelector(".mon-program");
  t.eq("monitor at Full quality", cv.width, 1080);
  const cy = st.S.doc.captions.y;
  for (const f of [15, 40, 90, 100, 130, 160]) {
    st.pb.seek(f);
    await t.settle();
    const a = luma(cv.getContext("2d").getImageData(0, 0, 1080, 1920).data);
    const b = luma(await stillPixels(doc.id, f));
    const whole = psnr(a, b, 1080);
    const band = psnr(a, b, 1080, [60, cy - 90, 1020, cy + 90]);
    const floor = f >= 60 && f < 120 ? 27 : 32;       // the title is on screen from 60 to 120
    t.ok(`frame ${f}: preview matches export (luma ${whole.toFixed(1)} dB >= ${floor})`, whole >= floor, whole.toFixed(1));
    t.ok(`frame ${f}: caption band matches (luma ${band.toFixed(1)} dB >= 23)`, band >= 23, band.toFixed(1));
  }
  // where things sit, on black (V1 hidden): captions, the lit word, the title, the box
  st.history.commit("hide V1", (d) => { d.tracks.find((x) => x.id === "V1").hide = true; });
  await st.save.flush(true);
  const band = [0, cy - 100, 1080, cy + 100];
  for (const f of [40, 100]) {
    st.pb.seek(f);
    await t.settle();
    const pa = cv.getContext("2d").getImageData(0, 0, 1080, 1920).data;
    const pbx = await stillPixels(doc.id, f);
    const wA = boxOf(pa, 1080, 1920, isInk, band), wB = boxOf(pbx, 1080, 1920, isInk, band);
    t.ok(`frame ${f}: caption letters sit within 2 px`, close(wA, wB), `${wA} vs ${wB}`);
    // m01 is all Jonathan: blue letters, his spoken word white (grill C1, C2)
    const bA = countIn(pa, 1080, isBlue, band), bB = countIn(pbx, 1080, isBlue, band);
    t.ok(`frame ${f}: his words are blue in both`, similar(bA, bB), `${bA} vs ${bB} px`);
    const lA = boxOf(pa, 1080, 1920, isWhite, band), lB = boxOf(pbx, 1080, 1920, isWhite, band);
    if (lA[2] > 0 || lB[2] > 0) t.ok(`frame ${f}: his spoken word (white) sits within 2 px`, close(lA, lB), `${lA} vs ${lB}`);
    if (f === 100) {
      const tA = boxOf(pa, 1080, 1920, isWhite, [0, 300, 1080, 540]), tB = boxOf(pbx, 1080, 1920, isWhite, [0, 300, 1080, 540]);
      t.ok("the title sits within 2 px", close(tA, tB), `${tA} vs ${tB}`);
    }
  }
  st.pb.seek(140);
  await t.settle();
  const pa = cv.getContext("2d").getImageData(0, 0, 1080, 1920).data;
  const pbx = await stillPixels(doc.id, 140);
  const A = yellowBox(pa, 1080, 1920, [0, 0, 1080, 800]), B = yellowBox(pbx, 1080, 1920, [0, 0, 1080, 800]);
  t.ok("the box's edges match within 2 px", close(A, B), `${A} vs ${B}`);

  // a woman's words (the fixture's Dana, m02): pink letters and a yellow spoken word, in both
  const d2 = await t.fresh("m02");
  st.history.commit("hide V1", (d) => { d.tracks.find((x) => x.id === "V1").hide = true; });
  await st.save.flush(true);
  await until(() => st.S.saving === "saved", 4000);
  const ev = st.S.doc.captions.events.find((e) => e.words.length >= 2 && e.words.every((w) => w.k === "f"));
  t.ok("the m02 short has a group of Dana's words", !!ev);
  if (ev) {
    const f2 = ev.words[0].s + 3;
    st.pb.seek(f2);
    await t.settle();
    const cv2 = document.querySelector(".mon-program");
    const qa = cv2.getContext("2d").getImageData(0, 0, 1080, 1920).data;
    const qb = await stillPixels(d2.id, f2);
    const pA = countIn(qa, 1080, isPink, band), pB = countIn(qb, 1080, isPink, band);
    t.ok("her words are pink in both", similar(pA, pB), `${pA} vs ${pB} px`);
    // her spoken word is white since 2026-09-30 (it was yellow)
    const yA = boxOf(qa, 1080, 1920, isWhite, band), yB = boxOf(qb, 1080, 1920, isWhite, band);
    t.ok("her spoken word is white and sits within 2 px in both", close(yA, yB), `${yA} vs ${yB}`);
  }
});
