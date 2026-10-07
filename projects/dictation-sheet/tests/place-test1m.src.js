// place-test1m: test 1's Blurry flow, syllable errors measured over all syllables in sheet order (so a page that merges
// lines can be compared with the original). Same synthetic 76 bpm track and voice as place-test1.
/*BLURRY_LRC*/
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function r2(x) { return Math.round(x * 100) / 100; }
function r3(x) { return Math.round(x * 1000) / 1000; }
var fps = 100, DUR = 304, N = fps * DUR, BPM = 76, BEAT = 60 / BPM, T0 = 1.0, SIXTEENTH = BEAT / 4;
var toasts = []; (function () { var t = document.getElementById('toast'); new MutationObserver(function () { toasts.push(t.textContent); }).observe(t, { childList: true, characterData: true, subtree: true }); })();
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), f; if (k0 < env.length && env[k0] < 1.4) env[k0] = 1.4; for (f = k0 + 1; f < k1 && f < env.length; f++) if (env[f] < 2.3) env[f] = 2.3; }
var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i, k = 0, t;
for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
for (t = T0; t < DUR - 1; t += BEAT, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } bump(full, t + BEAT / 2, 1.0, 4); }
var lrc = d.parseLrc(BLURRY_LRC), ons = [], offs = [], firstIdx = [], lineText = [];
lrc.forEach(function (l) { if (!l.text) return; var K = d.syllableTexts(l.text).length, q; firstIdx.push(ons.length); lineText.push(l.text); for (q = 0; q < K; q++) { var on = l.t + 0.2 + q * 0.25; ons.push(on); offs.push(on + 0.2); sing(voice, on, on + 0.2); } });
var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.spotify = null; d.cur().undo = []; d.cur().redo = [];
d.cur().audio = { el: { paused: true, currentTime: 0, duration: DUR, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'Puddle of Mudd - Blurry.wav', peaks: null, duration: DUR, onset: d.risesOf(full), voice: voice, low: low, blob: false };
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, status: 200, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: BLURRY_LRC, plain: '', duration: DUR, track: 'Blurry', artist: 'Puddle of Mudd' }); } }); return realFetch(url, opts); };
d.autoPlaceWords().then(function () {
  var s1 = d.S(), sa = d.sheetAudio(), spb = d.slotsPerBar(s1.time), lines = [], all = [];
  s1.lines.forEach(function (l, li) { if (l.kind !== 'line') return; lines.push(l); var base = d.barOrdinal(s1, li, 0) * spb; d.sortedSyls(l).forEach(function (y) { if (!y.rest) all.push({ y: y, g: base + y.pos, li: li, bars: l.bars, base: base }); }); });
  say('LOG page ' + location.pathname.split('/').pop() + ': bpm ' + s1.bpm + ' time ' + s1.time + ' offsetSec ' + sa.offsetSec + ' locked ' + sa.locked + ' fit ' + JSON.stringify(sa.lockFit) + '; sheet lines ' + lines.length + ' (timed lines with words 55), syllables ' + all.length + ' of ' + ons.length + ' sung, total bars ' + d.player.bars.length);
  check('all 480 syllables on the sheet, in order', all.length === ons.length);
  var errs = [], off1 = 0, offHalf = 0, maxE = 0, sum = 0, packed = 0;
  all.forEach(function (a, q) { if (q >= ons.length) return; var e = d.songOfSlot(a.g) - ons[q]; errs.push(e); sum += e; if (Math.abs(e) > maxE) maxE = Math.abs(e); if (Math.abs(e) > SIXTEENTH) off1++; if (Math.abs(e) > SIXTEENTH / 2) offHalf++; if (q > 0 && a.g === all[q - 1].g + 1 && d.lenSlots(all[q - 1].y) === 1 && ons[q] - ons[q - 1] > 1.5 * SIXTEENTH) packed++; });
  check('every syllable within one sixteenth (' + r3(SIXTEENTH) + ' s) of where it was sung', off1 === 0, off1 + ' of ' + errs.length + ' off by more than a sixteenth, ' + offHalf + ' by more than half; max |err| ' + r3(maxE) + ' s, mean ' + r3(sum / errs.length) + ' s, packed-as-sixteenths pairs ' + packed);
  say('LOG first-syllable error per timed line (s): ' + firstIdx.map(function (q) { return r2(errs[q]); }).join(' '));
  var chorus = firstIdx.slice(8, 15).map(function (q) { return r2(errs[q]); }), bridge = firstIdx.slice(32, 47).map(function (q) { return r2(errs[q]); });
  say('LOG chorus 1 (lines 9-15) first-syllable errors: ' + chorus.join(' ') + '; bridge (lines 33-47): ' + bridge.join(' '));
  var last = toasts[toasts.length - 1] || '', sq = /(\d+) lines? starts?/.exec(last);
  say('LOG toast: ' + last);
  say('LOG lines with bars: ' + lines.map(function (l) { return l.bars; }).join(' '));
  // the chorus on the sheet: which sheet line holds "Can you take it all away?" lines 9-15 and where they sit
  var l9 = all[firstIdx[8]], l10 = all[firstIdx[9]]; say('LOG line 9 "Can you take it all away?" at slot ' + l9.g + ' (bar ' + (Math.floor(l9.g / spb) + 1) + ', sheet line starting bar ' + (l9.base / spb + 1) + ') placed ' + r2(d.songOfSlot(l9.g)) + ' s, sung ' + r2(ons[firstIdx[8]]) + '; line 10 at slot ' + l10.g + ' placed ' + r2(d.songOfSlot(l10.g)) + ' s, sung ' + r2(ons[firstIdx[9]]));
  check('no NaN styles', document.querySelectorAll('[style*="NaN"]').length === 0);
  check('player.bars relaid', d.player.bars.length === lines.reduce(function (a, l) { return a + d.lineBars(l, spb); }, 0), d.player.bars.length);
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
