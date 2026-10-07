// Exports on a placed sheet (e2e2 fill + a 40-slot note): asText columns, musicXML well-formed and measure sums,
// midiBytes parsed with a tiny MIDI reader (one on/off pair per syllable, drums on channel 10); barTokens vs the
// renderer's own piece list on random lines; score mode.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100, N = fps * 60;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function makeSong(per) {
  var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i;
  for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
  var beat = 0.5, t0 = 1.0, k = 0;
  for (var t = t0; t < 59; t += beat, k++) {
    var pos = k % per;
    if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); }
    else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); }
    else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); }
  }
  return { full: full, low: low, voice: voice };
}
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
var spans = [[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [24.60, 24.85], [24.90, 25.10], [25.35, 26.30]];
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
try { localStorage.clear(); } catch (e) { /* ignore */ }
function setup(trackId, per) {
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
  s.spotify = { trackId: trackId, name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
  var song = makeSong(per); spans.forEach(function (p) { sing(song.voice, p[0], p[1]); });
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(song.full), voice: song.voice, low: song.low, blob: false };
  return s;
}
var LENS = ['w', 'h', 'q', '8', '16'];
var NAT = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
var GM = { kick: 36, snare: 38, hh: 42, hho: 46, hhp: 44, ride: 51, crash: 49, tom1: 48, tom2: 47, ftom: 43 };
function midiOfText(note, oct) { var m = /^([A-G])([#b]*)$/.exec(note || ''); if (!m) return null; var acc = 0; for (var i = 0; i < m[2].length; i++) acc += m[2][i] === '#' ? 1 : -1; return NAT[m[1]] + acc + 12 * (oct + 1); }
function totalBars(sheet) { var spb = d.slotsPerBar(sheet.time), n = 0; sheet.lines.forEach(function (l) { if (l.kind === 'line') n += d.lineBars(l, spb); }); return n; }
function parseMidi(u8) {
  var p = 0;
  function u32() { var v = ((u8[p] << 24) >>> 0) + (u8[p + 1] << 16) + (u8[p + 2] << 8) + u8[p + 3]; p += 4; return v; }
  function u16() { var v = (u8[p] << 8) + u8[p + 1]; p += 2; return v; }
  function str4() { var v = String.fromCharCode(u8[p], u8[p + 1], u8[p + 2], u8[p + 3]); p += 4; return v; }
  function vlq() { var v = 0, b; do { b = u8[p++]; v = (v << 7) | (b & 0x7f); } while (b & 0x80); return v; }
  var hdr = str4(), hl = u32(), fmt = u16(), ntr = u16(), div = u16(); p = 8 + hl;
  var tracks = [];
  for (var k = 0; k < ntr; k++) {
    var id = str4(), len = u32(), end = p + len, t = 0, evs = [], status = 0, guard = 0;
    while (p < end && guard++ < 1e6) {
      t += vlq(); var st = u8[p];
      if (st === 0xFF) { p++; var ty = u8[p++], ml = vlq(), data = Array.prototype.slice.call(u8, p, p + ml); p += ml; evs.push({ t: t, meta: ty, data: data }); }
      else if (st === 0xF0 || st === 0xF7) { p++; var sl = vlq(); p += sl; evs.push({ t: t, sysex: true }); }
      else { if (st & 0x80) { status = st; p++; } var hi = status & 0xF0, ch = status & 0x0F, a = u8[p++], b2 = (hi === 0xC0 || hi === 0xD0) ? null : u8[p++]; evs.push({ t: t, st: hi, ch: ch, a: a, b: b2 }); }
    }
    tracks.push({ id: id, len: len, evs: evs, endOk: p === end });
  }
  return { hdr: hdr, hl: hl, fmt: fmt, ntr: ntr, div: div, tracks: tracks, consumed: p, total: u8.length };
}
function pairsOf(evs) {
  var open = {}, pairs = [], problems = [];
  evs.forEach(function (e) {
    if (e.st === undefined) return;
    var key = e.ch + ':' + e.a;
    if (e.st === 0x90 && e.b > 0) { if (open[key] !== undefined) problems.push('double note-on ch' + (e.ch + 1) + ' n' + e.a + ' at ' + e.t + ' (open since ' + open[key] + ')'); open[key] = e.t; }
    else if (e.st === 0x80 || (e.st === 0x90 && e.b === 0)) { if (open[key] === undefined) problems.push('orphan note-off ch' + (e.ch + 1) + ' n' + e.a + ' at ' + e.t); else { pairs.push({ ch: e.ch, n: e.a, on: open[key], off: e.t }); delete open[key]; } }
  });
  Object.keys(open).forEach(function (k) { problems.push('never released ' + k + ' (on at ' + open[k] + ')'); });
  return { pairs: pairs, problems: problems };
}
function expectedPitched(sheet) { var spb = d.slotsPerBar(sheet.time), out = []; sheet.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(sheet, li, 0) * spb; d.sortedSyls(l).forEach(function (y) { if (y.rest) return; var n = midiOfText(y.note, y.oct || 4); if (n === null) return; out.push({ ch: 0, n: n, on: (base + y.pos) * 120, off: (base + y.pos + d.lenSlots(y)) * 120 - 1, text: y.text }); }); }); return out; }
function expectedDrums(sheet) { var spb = d.slotsPerBar(sheet.time), out = []; sheet.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(sheet, li, 0) * spb; d.sortedSyls(l).forEach(function (y) { var seen = {}; y.drum.forEach(function (id) { if (!GM[id] || seen[GM[id]]) return; seen[GM[id]] = 1; out.push({ ch: 9, n: GM[id], on: (base + y.pos) * 120, off: (base + y.pos) * 120 + Math.min(d.lenSlots(y), 1) * 120 - 1, text: y.text + '/' + id }); }); }); }); return out; }
function matchPairs(label, expected, got) {
  var missing = [], extra = got.slice();
  expected.forEach(function (e) { var i = -1; for (var k = 0; k < extra.length; k++) if (extra[k].ch === e.ch && extra[k].n === e.n && extra[k].on === e.on && extra[k].off === e.off) { i = k; break; } if (i < 0) missing.push(e.text + ' n' + e.n + ' ' + e.on + '-' + e.off); else extra.splice(i, 1); });
  check(label + ': every syllable gives exactly one on/off pair with the right ticks (' + expected.length + ' expected, ' + got.length + ' found)', missing.length === 0 && extra.length === 0, 'missing [' + missing.join(', ') + '] extra [' + extra.map(function (p) { return 'ch' + (p.ch + 1) + ' n' + p.n + ' ' + p.on + '-' + p.off; }).join(', ') + ']');
}
function xmlDoc(x) { return new DOMParser().parseFromString(x, 'application/xml'); }
function measureSums(doc) { var out = []; Array.prototype.forEach.call(doc.getElementsByTagName('measure'), function (m) { var sum = 0; Array.prototype.forEach.call(m.getElementsByTagName('note'), function (n) { if (n.getElementsByTagName('chord').length) return; var du = n.getElementsByTagName('duration')[0]; sum += du ? +du.textContent : 0; }); out.push(sum); }); return out; }
function countTies(doc) { var st = 0, sp = 0; Array.prototype.forEach.call(doc.getElementsByTagName('tie'), function (t) { if (t.getAttribute('type') === 'start') st++; else sp++; }); return { start: st, stop: sp }; }
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function rendererPieces(line, b, spb, time) {
  // mirrors partBar() in the notation engine
  var events = d.barEvents(line, b, spb), out = [], cursor = 0;
  function pushRests(from, n) { if (n <= 0) return; var pcs = (from === 0 && n === spb) ? [{ dur: 'w', dots: 0 }] : d.restPieces(from, n, spb, time); pcs.forEach(function (p) { var sl = (from === 0 && n === spb) ? spb : d.pieceSlots(p); out.push({ rest: true, dur: p.dur, dots: p.dots || 0, slots: sl }); }); }
  events.forEach(function (ev) { if (ev.s > cursor) pushRests(cursor, ev.s - cursor); var pcs2 = d.notePiecesAt(ev.s, ev.len, spb, time); pcs2.forEach(function (p) { out.push({ rest: false, dur: p.dur, dots: p.dots || 0, slots: d.pieceSlots(p) }); }); cursor = ev.s + ev.len; });
  if (cursor < spb) pushRests(cursor, spb - cursor);
  return out;
}

setup('fake-44', 4);
d.autoPlaceWords().then(function () {
  var s = d.S(), spb = d.slotsPerBar(s.time);
  say('LOG placed: ' + s.lines.length + ' lines, time ' + s.time + ' bpm ' + s.bpm + ' locked ' + !!(s.audio && s.audio.locked));
  // pitches on every syllable, drums on all, the last note held 40 slots
  var letters = ['C', 'D', 'E', 'F', 'G', 'A', 'B'], k = 0, lastY = null, lastLi = -1;
  s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; d.sortedSyls(l).forEach(function (y) { y.note = letters[k % 7]; y.oct = 4 + (k % 3 === 0 ? 1 : 0); y.drum = k % 2 ? ['snare', 'hh'] : ['kick', 'hh']; k++; lastY = y; lastLi = li; }); });
  d.setSlotsRaw(lastY, 40); s.lines[lastLi].bars = d.minBars(s.lines[lastLi], spb);
  // one more line: a 4-hit drum, a dotted rest with extra slots (9 chars in asText), a half note
  var extra = d.parseLyrics('Ex-tra words here')[0]; extra.syllables = extra.syllables.slice(0, 3);
  var e0 = extra.syllables[0], e1 = extra.syllables[1], e2 = extra.syllables[2];
  e0.text = 'Ex'; e0.hy = false; e0.pos = 0; e0.len = 'q'; e0.note = 'C'; e0.oct = 4; e0.drum = ['kick', 'snare', 'hh', 'crash'];
  e1.text = ''; e1.hy = false; e1.rest = true; e1.pos = 4; e1.len = 'q'; e1.dot = true; e1.xs = 10; e1.note = ''; e1.drum = [];
  e2.text = 'words'; e2.hy = false; e2.pos = 20; e2.len = 'h'; e2.note = 'D'; e2.oct = 4; e2.drum = ['kick'];
  extra.bars = 2; s.lines.push(extra);
  d.touch(); d.renderAll();
  var tb = totalBars(s);
  say('LOG sheet: ' + s.lines.map(function (l, li) { return l.kind !== 'line' ? '[' + l.text + ']' : 'L' + li + ' bars ' + d.lineBars(l, spb) + ' base ' + d.barOrdinal(s, li, 0) + ': ' + d.sortedSyls(l).map(function (y) { return (y.rest ? 'rest' : y.text) + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }).join(' | ') + ' | total bars ' + tb);
  check('the 40-slot note is on the sheet', d.lenSlots(lastY) === 40 && lastY.len === 'w' && lastY.xs === 24);

  // ---- asText
  var txt = d.asText(), tl = txt.split('\n');
  say('LOG asText:\n' + txt);
  var rowIdx = 3, problems = [], labels = ['', 'at', 'len', 'drum', 'sol', 'note', 'tab'];
  s.lines.forEach(function (l, li) {
    if (l.kind === 'header') { rowIdx++; return; }
    var syls = d.sortedSyls(l), w = syls.map(function (y) { return Math.max(y.text.length, 8); }), starts = [6]; for (var i = 1; i < w.length; i++) starts.push(starts[i - 1] + w[i - 1] + 1);
    for (var r = 0; r < 7; r++) { var row = tl[rowIdx + r] || ''; for (var i2 = 1; i2 < starts.length; i2++) { if (row.length > starts[i2] - 1 && row.charAt(starts[i2] - 1) !== ' ') problems.push('line ' + li + ' row "' + labels[r] + '" col ' + i2 + ' shifted by "' + row.slice(starts[i2 - 1], starts[i2] + 2).trim() + '"'); } }
    rowIdx += 8;
  });
  check('asText columns line up (width 8)', problems.length === 0, problems.length + ' shifted: ' + problems.join('; '));
  check('len row shows +N for the 40-slot note (whol+24)', /whol\+24/.test(txt), (txt.match(/whol\+\d+/) || ['none'])[0]);
  check('len row marks the rest r and the dot', /rquar\.\+10/.test(txt), (txt.match(/rquar[^ ]*/) || ['none'])[0]);

  // ---- musicXML on the placed sheet
  var xml = d.musicXML(s), doc = xmlDoc(xml), perr = doc.getElementsByTagName('parsererror');
  check('musicXML is well-formed XML', perr.length === 0, perr.length ? perr[0].textContent.slice(0, 200) : '');
  var measures = doc.getElementsByTagName('measure'), sums = measureSums(doc), badSums = [];
  sums.forEach(function (v, i) { if (v !== spb) badSums.push((i + 1) + ':' + v); });
  check('measure count = total bars (' + tb + ')', measures.length === tb, measures.length + ' measures');
  check('divisions 4, every measure sums to ' + spb + ' slots', doc.getElementsByTagName('divisions')[0].textContent === '4' && badSums.length === 0, 'short/long measures: ' + badSums.join(' '));
  var ties = countTies(doc), tied = doc.getElementsByTagName('tied').length, rests = doc.getElementsByTagName('rest').length, notes = doc.getElementsByTagName('note').length, lyrics = doc.getElementsByTagName('lyric');
  say('LOG xml: ' + measures.length + ' measures, ' + notes + ' notes, ' + rests + ' rests, ties start ' + ties.start + ' stop ' + ties.stop + ' (' + tied + ' tied), ' + lyrics.length + ' lyrics, ' + xml.length + ' chars');
  check('tie starts == tie stops', ties.start === ties.stop && ties.start > 0, ties.start + '/' + ties.stop);
  var lyrTexts = Array.prototype.map.call(lyrics, function (l) { return l.getElementsByTagName('text')[0].textContent; });
  var sylTexts = []; s.lines.forEach(function (l) { if (l.kind === 'line') d.sortedSyls(l).forEach(function (y) { if (!y.rest && y.text) sylTexts.push(y.text); }); });
  check('each syllable text appears once as a lyric, continuations carry none', lyrTexts.join('|') === sylTexts.join('|'), 'lyrics ' + lyrTexts.join(' ') + ' vs syllables ' + sylTexts.join(' '));
  // the 40-slot note: from its first piece, follow the tie chain and add durations
  var chain = 0, inChain = false, allNotes = doc.getElementsByTagName('note');
  Array.prototype.forEach.call(allNotes, function (n) { var ly = n.getElementsByTagName('lyric')[0]; var isStart = ly && ly.getElementsByTagName('text')[0].textContent === lastY.text; if (isStart) inChain = true; if (inChain) { chain += +n.getElementsByTagName('duration')[0].textContent; var hasStart = Array.prototype.some.call(n.getElementsByTagName('tie'), function (t) { return t.getAttribute('type') === 'start'; }); if (!hasStart) inChain = false; } });
  check('the 40-slot note is a tie chain of 40 slots in the XML', chain === 40, 'chain ' + chain);
  check('tempo written as the sheet bpm', new RegExp('<per-minute>' + s.bpm + '</per-minute>').test(xml), (xml.match(/<per-minute>[^<]*/) || [''])[0]);

  // ---- MIDI on the placed sheet (guitar view: channel 1, program 24)
  var m = parseMidi(d.midiBytes(s)), evs = m.tracks[0] ? m.tracks[0].evs : [];
  check('MIDI header MThd, format 0, 1 track, 480 ppq', m.hdr === 'MThd' && m.fmt === 0 && m.ntr === 1 && m.div === 480, JSON.stringify({ hdr: m.hdr, fmt: m.fmt, ntr: m.ntr, div: m.div }));
  check('track chunk length right, every byte consumed', m.tracks[0] && m.tracks[0].id === 'MTrk' && m.tracks[0].endOk && m.consumed === m.total, m.consumed + '/' + m.total);
  var tempo = evs.filter(function (e) { return e.meta === 0x51; })[0], mpq = tempo ? (tempo.data[0] << 16) + (tempo.data[1] << 8) + tempo.data[2] : 0;
  check('tempo meta = 60e6 / bpm', Math.abs(mpq - 60000000 / s.bpm) < 1, mpq + ' vs ' + (60000000 / s.bpm).toFixed(1));
  var tsm = evs.filter(function (e) { return e.meta === 0x58; })[0], tp = d.timeParts(s.time);
  check('time signature meta ' + s.time, !!tsm && tsm.data[0] === tp.beats && tsm.data[1] === Math.round(Math.log(tp.unit) / Math.LN2), tsm && tsm.data.join(','));
  var eot = evs.filter(function (e) { return e.meta === 0x2F; })[0];
  check('end of track at total bars x spb x 120 = ' + (tb * spb * 120), !!eot && eot.t === tb * spb * 120, eot && String(eot.t));
  var prog = evs.filter(function (e) { return e.st === 0xC0; })[0];
  check('program change guitar 24 on channel 1', !!prog && prog.ch === 0 && prog.a === 24, prog && JSON.stringify(prog));
  var pr = pairsOf(evs);
  check('note-on/off pairing clean', pr.problems.length === 0, pr.problems.join('; '));
  matchPairs('pitched', expectedPitched(s), pr.pairs);
  check('pitched notes all on channel 1', pr.pairs.every(function (p) { return p.ch === 0; }));
  // drums view
  s.view = 'drums';
  var md = parseMidi(d.midiBytes(s)), devs = md.tracks[0].evs, dpr = pairsOf(devs);
  check('drum MIDI parses, no program change', md.tracks[0].endOk && !devs.some(function (e) { return e.st === 0xC0; }));
  check('drum pairing clean', dpr.problems.length === 0, dpr.problems.join('; '));
  matchPairs('drums', expectedDrums(s), dpr.pairs);
  check('drums all on channel 10', dpr.pairs.length > 0 && dpr.pairs.every(function (p) { return p.ch === 9; }));
  var dx = xmlDoc(d.musicXML(s)), dsums = measureSums(dx);
  check('drum musicXML well-formed, measures sum', dx.getElementsByTagName('parsererror').length === 0 && dsums.every(function (v) { return v === spb; }) && dx.getElementsByTagName('unpitched').length > 0, dsums.join(','));
  s.view = 'piano';
  var px = xmlDoc(d.musicXML(s)), psums = measureSums(px);
  check('piano musicXML: two parts, measures sum', px.getElementsByTagName('part').length === 2 && psums.length === 2 * tb && psums.every(function (v) { return v === spb; }), psums.length + ' measures');
  var pm = parseMidi(d.midiBytes(s)), ppr = pairsOf(pm.tracks[0].evs);
  matchPairs('piano', expectedPitched(s), ppr.pairs);
  s.view = 'guitar';

  // ---- 12/8 and 3/4 empty bars (whole-bar rest token)
  function emptyBarSheet(time) { return d.normalize({ time: time, bpm: 100, view: 'guitar', lines: [{ kind: 'line', bars: 3, syllables: [{ text: 'a', pos: 0, len: 'q', note: 'C' }, { text: 'b', pos: 4, len: 'q', note: 'D' }] }] }); }
  ['12/8', '3/4', '6/8', '2/4', '4/4'].forEach(function (time) {
    var sh = emptyBarSheet(time), sp2 = d.slotsPerBar(time), dd = xmlDoc(d.musicXML(sh)), ss = measureSums(dd), mm = parseMidi(d.midiBytes(sh)), e2 = mm.tracks[0].evs.filter(function (e) { return e.meta === 0x2F; })[0];
    check(time + ': empty bars export ' + sp2 + ' slots (xml measures ' + ss.join(',') + '; midi end ' + (e2 && e2.t) + ' of ' + 3 * sp2 * 120 + ')', ss.every(function (v) { return v === sp2; }) && e2 && e2.t === 3 * sp2 * 120);
  });

  // ---- a line whose first syllable has tie:true (only from a file), and an overlapping pair
  var sT = d.normalize({ lines: [{ kind: 'line', syllables: [{ text: 'a', pos: 0, note: 'C', tie: true }, { text: 'b', pos: 4, note: 'C' }] }] }), errT = null;
  try { d.musicXML(sT); } catch (e) { errT = e; }
  check('musicXML survives tie:true on the first syllable of a line', !errT, errT && String(errT.message));
  var sO = d.normalize({ time: '4/4', bpm: 100, lines: [{ kind: 'line', bars: 2, syllables: [{ text: 'a', pos: 12, len: 'h', note: 'C' }, { text: 'b', pos: 16, len: 'q', note: 'E' }] }] });
  var mo = pairsOf(parseMidi(d.midiBytes(sO)).tracks[0].evs), onsC = mo.pairs.filter(function (p) { return p.n === 60; }).length;
  var xo = xmlDoc(d.musicXML(sO)), m2 = xo.getElementsByTagName('measure')[1], m2lyr = Array.prototype.map.call(m2.getElementsByTagName('lyric'), function (l) { return l.getElementsByTagName('text')[0].textContent; });
  check('overlap (a: 12+8 runs over b at 16): MIDI has one note-on for a, XML bar 2 lyric is b', onsC === 1 && mo.problems.length === 0 && m2lyr.join('|') === 'b', 'note-ons for C ' + onsC + ' problems [' + mo.problems.join('; ') + '] bar-2 lyrics [' + m2lyr.join(',') + ']');

  // ---- barTokens vs the renderer's own pieces, random lines
  var rnd = mulberry32(7), times = ['4/4', '3/4', '2/4', '6/8', '12/8'], mism = [], sumBad = [], total = 0, byTime = {};
  for (var trial = 0; trial < 500; trial++) {
    var time = times[trial % 5], sp3 = d.slotsPerBar(time), n = 1 + Math.floor(rnd() * 8), syls = [], pos = Math.floor(rnd() * 4);
    for (var i = 0; i < n; i++) { var y = { text: 's' + i, pos: pos, len: LENS[Math.floor(rnd() * 5)], dot: rnd() < 0.3, xs: rnd() < 0.3 ? Math.floor(rnd() * 40) : 0, rest: rnd() < 0.15, note: 'C' }; syls.push(y); pos += (rnd() < 0.2 ? 1 : d.lenSlots(y)) + (rnd() < 0.5 ? Math.floor(rnd() * 6) : 0); }
    var line = d.normalize({ lines: [{ kind: 'line', bars: 1 + Math.floor(rnd() * 2), syllables: syls }] }).lines[0];
    var nb = d.lineBars(line, sp3);
    for (var b = 0; b < nb; b++) {
      total++; byTime[time] = (byTime[time] || 0) + 1;
      var A = rendererPieces(line, b, sp3, time), B = d.barTokens(line, b, sp3, time).map(function (t) { return { rest: t.rest, dur: t.dur, dots: t.dots || 0, slots: t.slots }; });
      var ja = JSON.stringify(A), jb = JSON.stringify(B);
      if (ja !== jb) mism.push(time + ' bar ' + b + ' of ' + nb + ' [' + syls.map(function (y) { return (y.rest ? 'r' : '') + y.pos + 'x' + d.lenSlots(y); }).join(' ') + '] renderer ' + ja + ' tokens ' + jb);
      var sumB = B.reduce(function (acc, t) { return acc + t.slots; }, 0); if (sumB !== sp3) sumBad.push(time + ' bar ' + b + ' sum ' + sumB + ' of ' + sp3);
    }
  }
  var mmTimes = {}; mism.forEach(function (x) { mmTimes[x.split(' ')[0]] = (mmTimes[x.split(' ')[0]] || 0) + 1; });
  check('barTokens == renderer pieces on ' + total + ' random bars (' + JSON.stringify(byTime) + ')', mism.length === 0, mism.length + ' mismatches by meter ' + JSON.stringify(mmTimes) + '; first: ' + mism.slice(0, 2).join(' || '));
  check('token slots sum to the bar in every bar', sumBad.length === 0, sumBad.length + ' bad, e.g. ' + sumBad.slice(0, 3).join(', '));

  // ---- score mode
  d.state.scoreMode = true; var errS = null; try { d.renderAll(); } catch (e) { errS = e; }
  var sv = document.getElementById('scoreView'), sh = document.getElementById('sheet');
  check('renderScore runs without error', !errS, errS && errS.stack);
  check('score view shown, sheet hidden', sv.hidden === false && sh.hidden === true);
  check('score has no chips, timeline, note hits, playhead, cells', sv.querySelectorAll('.timeline, .chip, .syl-chip, .notehit, .playhead, .cell, .barhit').length === 0, String(sv.querySelectorAll('.timeline, .chip, .syl-chip, .notehit, .playhead, .cell, .barhit').length));
  check('score drew ' + sv.querySelectorAll('svg').length + ' system(s) with no draw error', sv.querySelectorAll('svg').length > 0 && !sv.querySelector('.noteshint'), (sv.querySelector('.noteshint') || {}).textContent);
  check('score head shows title, key, bpm, time', /bpm/.test(sv.querySelector('.scorehead .meta').textContent) && new RegExp(s.time).test(sv.querySelector('.scorehead .meta').textContent), sv.querySelector('.scorehead .meta').textContent);
  check('status bar says Score', /Score/.test(document.getElementById('stMeta').textContent));
  var printRules = []; Array.prototype.forEach.call(document.styleSheets, function (ss) { try { Array.prototype.forEach.call(ss.cssRules, function (r) { if (r.media && /print/.test(r.media.mediaText)) Array.prototype.forEach.call(r.cssRules, function (q) { printRules.push(q.selectorText + ' {' + q.style.cssText + '}'); }); }); } catch (e) { /* cross-origin */ } });
  say('LOG @media print rules: ' + printRules.join(' || '));
  check('@media print hides timeline, playhead, notehit, chrome', printRules.some(function (t) { return /\.timeline/.test(t) && /\.playhead/.test(t) && /\.notehit/.test(t) && /\.menubar/.test(t) && /display: none/.test(t); }));
  check('@media print keeps score systems whole on a page (break-inside on .system)', printRules.some(function (t) { return /\.system\b/.test(t) && /break-inside/.test(t); }), 'only .lineblock has break-inside: avoid; the score is not inside a .lineblock');
  check('scoreView sits inside .lineblock? (for the print rule)', !!sv.closest('.lineblock'), 'no');
  d.state.scoreMode = false; d.renderAll();
  check('back to editing restores the sheet with chips', sh.hidden === false && sv.hidden === true && document.querySelectorAll('#sheet .timeline').length > 0);
  window.fetch = realFetch;
  try { localStorage.clear(); } catch (e) { /* ignore */ }
  say('LOG done');
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
