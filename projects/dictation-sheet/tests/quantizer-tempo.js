// quantizer-tempo.js: collisions and placement error of quantizeSpans at 76/100/120/160 bpm with syllables at 3-6 a second,
// against alternatives: plain rounding (the floor of any 16th grid), an optimal monotone assignment (DP), a 1-step
// backtrack, and a 32nd grid. Run: PROFILE=prof-quantizer python pagecheck.py stage.html quantizer-tempo.js
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var seed = 777; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var OFF = 10;
function setGrid(bpm) { s.bpm = bpm; s.time = '4/4'; s.audio = { offsetSec: OFF, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null }; }
// optimal: strictly increasing integer slots >= floor minimising the sum of |slot - g|
function dpAssign(g, floor) {
  var K = g.length, lo = [], hi = [], best = [], from = [], i, v, u;
  for (i = 0; i < K; i++) { lo.push(Math.max(floor + i, Math.floor(g[i]) - K)); hi.push(Math.ceil(g[i]) + K + i); }
  for (i = 0; i < K; i++) {
    best.push({}); from.push({});
    for (v = lo[i]; v <= hi[i]; v++) {
      var cost = Math.abs(v - g[i]);
      if (i === 0) { best[i][v] = cost; continue; }
      var m = Infinity, mu = null;
      for (u = lo[i - 1]; u <= Math.min(hi[i - 1], v - 1); u++) if (best[i - 1][u] !== undefined && best[i - 1][u] < m) { m = best[i - 1][u]; mu = u; }
      if (mu !== null) { best[i][v] = m + cost; from[i][v] = mu; }
    }
  }
  var mv = null, mm = Infinity; for (v = lo[K - 1]; v <= hi[K - 1]; v++) if (best[K - 1][v] !== undefined && best[K - 1][v] < mm) { mm = best[K - 1][v]; mv = v; }
  var out = new Array(K); for (i = K - 1; i >= 0; i--) { out[i] = mv; mv = from[i][mv]; }
  return out;
}
// the current rule: round, push forward on a collision (a copy of step 1 of quantizeSpans)
function curAssign(g, floor) { var out = [], minSlot = floor, i; for (i = 0; i < g.length; i++) { var on = Math.max(0, Math.round(g[i])); if (on < minSlot) on = minSlot; out.push(on); minSlot = on + 1; } return out; }
// smarter rounding: on a collision, pull the previous note back one slot when that costs less than pushing this one forward
function backAssign(g, floor) {
  var out = [], minSlot = floor, i;
  for (i = 0; i < g.length; i++) {
    var r = Math.max(0, Math.round(g[i]));
    if (r >= minSlot) { out.push(r); minSlot = r + 1; continue; }
    var push = Math.abs(minSlot - g[i]), pull = Infinity;
    if (i > 0 && out[i - 1] - 1 >= (i > 1 ? out[i - 2] + 1 : floor)) pull = Math.abs(out[i - 1] - 1 - g[i - 1]) - Math.abs(out[i - 1] - g[i - 1]) + Math.abs(minSlot - 1 - g[i]);
    if (pull < push) { out[i - 1]--; out.push(minSlot - 1); } else { out.push(minSlot); minSlot++; }
  }
  return out;
}
function stat() { return { n: 0, lines: 0, coll: 0, linesColl: 0, cur: 0, round: 0, dp: 0, back: 0, g32: 0, lateCur: 0, lateDp: 0, lateBack: 0, maxCur: 0, maxDp: 0, worst: null }; }
function run(bpm, rate, K, lines, st, slotSec) {
  for (var c = 0; c < lines; c++) {
    var t = OFF + rnd() * slotSec, spans = [], g = [], i;
    for (i = 0; i < K; i++) { var ioi = (1 / rate) * (0.8 + 0.4 * rnd()); spans.push({ y: { hy: false }, on: t, off: t + 0.6 * ioi }); g.push((t - OFF) / slotSec); t += ioi; }
    var q = d.quantizeSpans(spans, null, 0), cur = q.map(function (e) { return e.slot; }), mine = curAssign(g, 0);
    if (JSON.stringify(cur) !== JSON.stringify(mine)) say('FAIL my copy of step 1 differs from quantizeSpans: ' + JSON.stringify([g, cur, mine]));
    var dp = dpAssign(g, 0), bk = backAssign(g, 0), lineColl = false, ms = slotSec * 1000;
    for (i = 0; i < K; i++) {
      if (i > 0 && Math.round(g[i]) <= cur[i - 1]) { st.coll++; lineColl = true; }
      var ec = (cur[i] - g[i]) * ms, ed = (dp[i] - g[i]) * ms, eb = (bk[i] - g[i]) * ms;
      st.cur += Math.abs(ec); st.dp += Math.abs(ed); st.back += Math.abs(eb);
      st.round += Math.abs(Math.round(g[i]) - g[i]) * ms; st.g32 += Math.abs(Math.round(g[i] * 2) / 2 - g[i]) * ms;
      if (ec >= ms - 1e-6) st.lateCur++; if (Math.abs(ed) >= ms - 1e-6) st.lateDp++; if (Math.abs(eb) >= ms - 1e-6) st.lateBack++;
      if (Math.abs(ec) > st.maxCur) { st.maxCur = Math.abs(ec); st.worst = { g: g.map(function (x) { return +x.toFixed(2); }), cur: cur, dp: dp, back: bk, errMs: cur.map(function (v, k) { return Math.round((v - g[k]) * ms); }), dpErrMs: dp.map(function (v, k) { return Math.round((v - g[k]) * ms); }) }; }
      if (Math.abs(ed) > st.maxDp) st.maxDp = Math.abs(ed);
    }
    st.n += K; st.lines++; if (lineColl) st.linesColl++;
  }
}
say('LOG mean |error| in ms per syllable (8 syllables a line, 200 lines, onset jitter +-20%): current = round + push; round = plain rounding with no collision handling (not valid, a floor); dp = optimal monotone assignment; back = 1-step backtrack; g32 = 32nd grid plain rounding');
[76, 100, 120, 160].forEach(function (bpm) {
  setGrid(bpm); var slotSec = d.audioNominalSlotSec();
  [3, 4, 5, 6].forEach(function (rate) {
    var st = stat(); seed = 1000 + bpm + rate; run(bpm, rate, 8, 200, st, slotSec);
    say('LOG ' + bpm + ' bpm (16th ' + Math.round(slotSec * 1000) + ' ms) ' + rate + ' syl/s: collisions ' + st.coll + '/' + st.n + ' syllables (' + (100 * st.coll / st.n).toFixed(1) + '%), lines with a collision ' + st.linesColl + '/' + st.lines + '; mean|err| current ' + (st.cur / st.n).toFixed(1) + ' round ' + (st.round / st.n).toFixed(1) + ' dp ' + (st.dp / st.n).toFixed(1) + ' back ' + (st.back / st.n).toFixed(1) + ' g32 ' + (st.g32 / st.n).toFixed(1) + '; a full slot or more late: current ' + st.lateCur + ' dp ' + st.lateDp + ' back ' + st.lateBack + '; max|err| current ' + st.maxCur.toFixed(0) + ' dp ' + st.maxDp.toFixed(0));
    if (bpm === 76 && (rate === 5 || rate === 6) && st.worst) say('LOG   worst line at ' + bpm + ' bpm ' + rate + '/s: sung slots ' + JSON.stringify(st.worst.g) + ' -> current ' + JSON.stringify(st.worst.cur) + ' err ms ' + JSON.stringify(st.worst.errMs) + ' | dp ' + JSON.stringify(st.worst.dp) + ' err ms ' + JSON.stringify(st.worst.dpErrMs) + ' | back ' + JSON.stringify(st.worst.back));
  });
});
// the same on the random spans of the property test (gaps 0.05-2 s, 2-12 syllables)
say('LOG random spans (gaps 0.05-2 s, 2-12 syllables, 500 lines) mean |error| ms:');
[76, 100, 120, 160].forEach(function (bpm) {
  setGrid(bpm); var slotSec = d.audioNominalSlotSec(), ms = slotSec * 1000, st = stat(); seed = 4242;
  for (var c = 0; c < 500; c++) {
    var K = 2 + Math.floor(rnd() * 11), t = OFF + rnd() * 3, spans = [], g = [], i;
    for (i = 0; i < K; i++) { var gap = 0.05 + rnd() * 1.95; spans.push({ y: { hy: false }, on: t, off: t + rnd() * gap }); g.push((t - OFF) / slotSec); t += gap; }
    var cur = d.quantizeSpans(spans, null, 0).map(function (e) { return e.slot; }), dp = dpAssign(g, 0), bk = backAssign(g, 0);
    for (i = 0; i < K; i++) { if (i > 0 && Math.round(g[i]) <= cur[i - 1]) st.coll++; var ec = (cur[i] - g[i]) * ms; st.cur += Math.abs(ec); st.dp += Math.abs(dp[i] - g[i]) * ms; st.back += Math.abs(bk[i] - g[i]) * ms; st.round += Math.abs(Math.round(g[i]) - g[i]) * ms; st.g32 += Math.abs(Math.round(g[i] * 2) / 2 - g[i]) * ms; if (ec >= ms - 1e-6) st.lateCur++; if (Math.abs(ec) > st.maxCur) st.maxCur = Math.abs(ec); }
    st.n += K;
  }
  say('LOG ' + bpm + ' bpm: collisions ' + st.coll + '/' + st.n + ' (' + (100 * st.coll / st.n).toFixed(1) + '%); mean|err| current ' + (st.cur / st.n).toFixed(1) + ' round ' + (st.round / st.n).toFixed(1) + ' dp ' + (st.dp / st.n).toFixed(1) + ' back ' + (st.back / st.n).toFixed(1) + ' g32 ' + (st.g32 / st.n).toFixed(1) + '; a full slot late ' + st.lateCur + '; max ' + st.maxCur.toFixed(0) + ' ms');
});
// a hand-made example at 76 bpm: six syllables at 6 a second (167 ms apart), the sixteenth is 197 ms
setGrid(76); var sl = d.audioNominalSlotSec(), ex = [], gx = [], k;
for (k = 0; k < 8; k++) { var on = OFF + 0.05 + k / 6; ex.push({ y: { hy: false }, on: on, off: on + 0.1 }); gx.push(+((on - OFF) / sl).toFixed(2)); }
var qx = d.quantizeSpans(ex, null, 0);
say('LOG example 76 bpm, 8 syllables 167 ms apart: sung slots ' + JSON.stringify(gx) + ' -> slots ' + JSON.stringify(qx.map(function (e) { return e.slot; })) + ' lens ' + JSON.stringify(qx.map(function (e) { return e.lenSlots; })) + ' error ms ' + JSON.stringify(qx.map(function (e, i) { return Math.round((e.slot - gx[i]) * sl * 1000); })) + ' | dp ' + JSON.stringify(dpAssign(gx, 0)) + ' err ms ' + JSON.stringify(dpAssign(gx, 0).map(function (v, i) { return Math.round((v - gx[i]) * sl * 1000); })));
// the .5 tie: two syllables at 0.5 and 1.3 slots, rounding up the first pushes the second a slot late
var ex2 = [{ y: { hy: false }, on: OFF + 0.5 * sl, off: OFF + 0.7 * sl }, { y: { hy: false }, on: OFF + 1.3 * sl, off: OFF + 1.9 * sl }, { y: { hy: false }, on: OFF + 2.2 * sl, off: OFF + 2.8 * sl }];
var q2 = d.quantizeSpans(ex2, null, 0);
say('LOG example 76 bpm, sung slots [0.5, 1.3, 2.2] -> ' + JSON.stringify(q2.map(function (e) { return e.slot; })) + ' error ms ' + JSON.stringify(q2.map(function (e, i) { return Math.round((e.slot - [0.5, 1.3, 2.2][i]) * sl * 1000); })) + ' (dp ' + JSON.stringify(dpAssign([0.5, 1.3, 2.2], 0)) + ', back ' + JSON.stringify(backAssign([0.5, 1.3, 2.2], 0)) + ')');
