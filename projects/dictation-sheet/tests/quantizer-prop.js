// quantizer-prop.js: property tests on quantizeSpans, 500 random span lists, inside stage.html (straight-line grid).
// Run: PROFILE=prof-quantizer python pagecheck.py stage.html quantizer-prop.js
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var seed = 20260923; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var OFF = 10;
function setGrid(bpm, time) { s.bpm = bpm; s.time = time; s.audio = { offsetSec: OFF, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null }; }
setGrid(120, '4/4');
var slotSec = d.audioNominalSlotSec();
say('LOG grid: bpm ' + s.bpm + ' ' + s.time + ' slotSec ' + slotSec + ' slotOfSong(10.5) ' + d.slotOfSong(10.5) + ' songGrid ' + d.songGrid());
function slotAt(sec) { var g = d.slotOfSong(sec); return isFinite(g) ? Math.max(0, Math.round(g)) : 0; }
// one random line: 2-12 syllables, onsets increasing by 0.05-2 s, releases before the next onset or null (20%),
// hy 30%, next line onset null (30%) or after the last onset (15% of those: before it), floorSlot 0-8 or above the first onset
function gen() {
  var K = 2 + Math.floor(rnd() * 11), t = OFF + rnd() * 3 - 0.3, spans = [], i;
  for (i = 0; i < K; i++) {
    var gap = 0.05 + rnd() * 1.95, on = t, off = rnd() < 0.2 ? null : on + Math.max(0.02, rnd() * gap);
    spans.push({ y: { hy: rnd() < 0.3 }, on: on, off: off });
    t += gap;
  }
  var lastOn = spans[K - 1].on, next = null;
  if (rnd() < 0.7) next = lastOn + (rnd() < 0.15 ? -rnd() * 0.5 : 0.05 + rnd() * 2);
  var fl = rnd() < 0.2 ? slotAt(spans[0].on) + Math.floor(rnd() * 4) : Math.floor(rnd() * 9);
  return { spans: spans, next: next, floor: fl };
}
var fails = {}, rests = {}, oneRest = 0, oneRestEnd = 0, hySplit = 0, hySplitUnder = 0, hySplitUnknown = 0, hyPairs = 0, hyUnder = 0, hyDead = true, restsTotal = 0, cases = 0, syl = 0, pushed = 0, floorPushed = 0, capHits = 0, restSlots = 0;
function fail(name, detail) { fails[name] = (fails[name] || 0) + 1; if (fails[name] === 1) say('FAIL ' + name + ': ' + detail); }
for (var c = 0; c < 500; c++) {
  var g = gen(), K = g.spans.length, q = d.quantizeSpans(g.spans, g.next, g.floor), i;
  cases++; syl += K;
  var desc = (function (g, q, c) { return function () { return 'case ' + c + ' ' + JSON.stringify({ spans: g.spans.map(function (p) { return [+(p.on - OFF).toFixed(3), p.off === null ? null : +(p.off - OFF).toFixed(3), p.y.hy ? 1 : 0]; }), next: g.next === null ? null : +(g.next - OFF).toFixed(3), floor: g.floor, q: q.map(function (e) { return [e.slot, e.lenSlots]; }) }); }; })(g, q, c);
  if (q.length !== K) { fail('length', desc()); continue; }
  var hasNext = g.next !== null, lineEnd = hasNext ? Math.max(q[K - 1].slot + 1, slotAt(g.next)) : Infinity;
  for (i = 0; i < K; i++) {
    var e = q[i];
    if (!isFinite(e.slot) || !isFinite(e.lenSlots) || e.slot !== Math.round(e.slot) || e.lenSlots !== Math.round(e.lenSlots)) fail('finite-int', desc());
    if (e.lenSlots < 1) fail('len>=1', desc());
    if (e.lenSlots > d.MAX_SLOTS) fail('len<=MAX_SLOTS', desc());
    if (e.lenSlots === d.MAX_SLOTS) capHits++;
    if (i === 0 && e.slot < Math.round(g.floor)) fail('first>=floor', desc());
    if (i === 0 && e.slot > slotAt(g.spans[0].on)) floorPushed++;
    if (i > 0 && e.slot <= q[i - 1].slot) fail('strictly-increasing', desc());
    if (i > 0 && q[i - 1].slot + q[i - 1].lenSlots > e.slot) fail('no-overlap', desc());
    if (i > 0 && slotAt(g.spans[i].on) <= q[i - 1].slot) pushed++;
    if (i > 0) {
      var r = e.slot - (q[i - 1].slot + q[i - 1].lenSlots); rests[r] = (rests[r] || 0) + 1; if (r > 0) { restsTotal++; restSlots += r; }
      if (r === 1) { oneRest++; if (oneRest === 1) say('NOTE first 1-slot rest: ' + desc()); }
      var sp = g.spans[i - 1];
      if (sp.y.hy) {
        hyPairs++; var under = sp.off !== null && (g.spans[i].on - sp.off) < slotSec; if (under) hyUnder++;
        if (r > 0) { hySplit++; if (under) { hySplitUnder++; if (hySplitUnder === 1) say('NOTE first hy split with sung gap under a slot: ' + desc()); } if (sp.off === null) hySplitUnknown++; if (hySplit === 1) say('NOTE first hy split (sung gap ' + (sp.off === null ? 'unknown' : Math.round((g.spans[i].on - sp.off) * 1000) + ' ms, ' + ((g.spans[i].on - sp.off) / slotSec).toFixed(2) + ' slots') + ', rest ' + r + ' slots): ' + desc()); }
      }
    }
  }
  var lastEnd = q[K - 1].slot + q[K - 1].lenSlots;
  if (hasNext && lastEnd > lineEnd) fail('last<=lineEnd', desc());
  if (hasNext && lineEnd - lastEnd === 1) { oneRestEnd++; if (oneRestEnd === 1) say('NOTE first 1-slot gap before the next line: ' + desc()); }
  // is hy dead code? flip every hy flag and compare
  var flipped = g.spans.map(function (p) { return { y: { hy: !p.y.hy }, on: p.on, off: p.off }; });
  if (JSON.stringify(d.quantizeSpans(flipped, g.next, g.floor)) !== JSON.stringify(q)) hyDead = false;
}
var keys = Object.keys(rests).map(Number).sort(function (a, b) { return a - b; });
say('LOG cases ' + cases + ' syllables ' + syl + ' failures ' + JSON.stringify(fails));
say('LOG onsets pushed by a collision ' + pushed + ', first onsets pushed by floorSlot ' + floorPushed + ', notes at MAX_SLOTS ' + capHits);
say('LOG rest length histogram (slots: count, 0 = no rest): ' + keys.map(function (k) { return k + ':' + rests[k]; }).join(' '));
say('LOG rests > 0: ' + restsTotal + ' of ' + (syl - cases) + ' inner gaps, mean rest ' + (restsTotal ? (restSlots / restsTotal).toFixed(2) : 0) + ' slots; 1-slot rests inside a line ' + oneRest + '; 1-slot gaps before the next line ' + oneRestEnd);
say('LOG hy pairs ' + hyPairs + ' (sung gap under a slot: ' + hyUnder + '); split by a rest ' + hySplit + ' (under a slot: ' + hySplitUnder + ', release unknown: ' + hySplitUnknown + ')');
say((Object.keys(fails).length ? 'FAIL' : 'PASS') + ' invariants over 500 random lines (strictly increasing, len 1..64, no overlap, floor, last <= lineEnd)');
say((oneRest === 0 ? 'PASS' : 'FAIL') + ' no rest of exactly 1 slot survives: ' + oneRest);
say((hySplitUnder === 0 ? 'PASS' : 'FAIL') + ' no hy pair with a sung gap under a slot is split by a rest: ' + hySplitUnder);
say((hyDead ? 'FAIL' : 'PASS') + ' the hy flag changes the output of quantizeSpans on at least one of 500 lines (hy FILL is ' + (hyDead ? 'DEAD CODE' : 'live') + ')');
// the same at 76 and 160 bpm: rests and hy splits
[76, 160].forEach(function (bpm) {
  setGrid(bpm, '4/4'); slotSec = d.audioNominalSlotSec(); seed = 99;
  var one = 0, hs = 0, hsu = 0, hp = 0, n = 0, push = 0, tot = 0;
  for (var c2 = 0; c2 < 500; c2++) {
    var g2 = gen(), q2 = d.quantizeSpans(g2.spans, g2.next, g2.floor), K2 = g2.spans.length, i2;
    for (i2 = 1; i2 < K2; i2++) {
      tot++; var r2 = q2[i2].slot - (q2[i2 - 1].slot + q2[i2 - 1].lenSlots); if (r2 === 1) one++;
      if (slotAt(g2.spans[i2].on) <= q2[i2 - 1].slot) push++;
      var sp2 = g2.spans[i2 - 1]; if (sp2.y.hy) { hp++; if (r2 > 0) { hs++; if (sp2.off !== null && g2.spans[i2].on - sp2.off < slotSec) hsu++; } }
      if (q2[i2].slot <= q2[i2 - 1].slot || q2[i2 - 1].slot + q2[i2 - 1].lenSlots > q2[i2].slot || q2[i2].lenSlots < 1 || q2[i2].lenSlots > 64) n++;
    }
  }
  say('LOG ' + bpm + ' bpm (slot ' + Math.round(slotSec * 1000) + ' ms): inner gaps ' + tot + ', pushed by collision ' + push + ', 1-slot rests ' + one + ', hy pairs ' + hp + ' split ' + hs + ' (under a slot ' + hsu + '), invariant breaks ' + n);
});
