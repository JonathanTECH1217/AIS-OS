// Undo: one pushUndo() over wordsToNotes + applyTime + lockToSong(quiet, final, noUndo) + Place-words-style writes;
// one undo() restores everything, redo() brings it back; pushUndo('lock') merge window; the stack cap.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function diff(a, b, path, out) {
  path = path || '$'; out = out || [];
  if (a === b) return out;
  var ta = a === null ? 'null' : Array.isArray(a) ? 'array' : typeof a, tb = b === null ? 'null' : Array.isArray(b) ? 'array' : typeof b;
  if (ta !== tb) { out.push(path + ': ' + JSON.stringify(a) + ' -> ' + JSON.stringify(b)); return out; }
  if (ta === 'array') { var n = Math.max(a.length, b.length); for (var i = 0; i < n; i++) diff(a[i], b[i], path + '[' + i + ']', out); return out; }
  if (ta === 'object') { var keys = {}; Object.keys(a).forEach(function (k) { keys[k] = 1; }); Object.keys(b).forEach(function (k) { keys[k] = 1; }); Object.keys(keys).forEach(function (k) { if (!(k in a)) out.push(path + '.' + k + ': (absent) -> ' + JSON.stringify(b[k])); else if (!(k in b)) out.push(path + '.' + k + ': ' + JSON.stringify(a[k]) + ' -> (absent)'); else diff(a[k], b[k], path + '.' + k, out); }); return out; }
  out.push(path + ': ' + JSON.stringify(a) + ' -> ' + JSON.stringify(b)); return out;
}
function snap() { var p = d.plain(d.S()); delete p.updatedAt; return p; }
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
try { localStorage.clear(); } catch (e) { /* ignore */ }
function setup(trackId, per) {
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
  s.spotify = { trackId: trackId, name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
  var song = makeSong(per);
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(song.full), voice: song.voice, low: song.low, blob: false };
  return s;
}
setup('fake-44', 4); d.renderAll();
var t = d.cur(), depth0 = t.undo.length, redo0 = t.redo.length;
var before = snap();

// ---- one step for a composite edit
d.pushUndo();
d.wordsToNotes('Silent night, holy night\nAll is calm', 'Tester - Test Song', { noUndo: true, quiet: true });
d.applyTime('3/4');
var sa = d.sheetAudio(); sa.offsetSec = 1.0; sa.lined = true;
d.lockToSong(true, true, true);
var s1 = d.S();
s1.filled = { key: 'spotify:fake-44', title: 'Test Song' };
var y0 = s1.lines[0].syllables[0]; y0.pos = 9; d.setSlotsRaw(y0, 6); s1.lines[0].bars = 3; y0.note = 'E'; y0.oct = 4;
d.touch(); d.renderAll();
check('composite edit is one undo step', t.undo.length === depth0 + 1, 'depth ' + depth0 + ' -> ' + t.undo.length);
check('lock took: locked, beats, bpm 120, bar 1 at 1.0 s', !!(s1.audio && s1.audio.locked && s1.audio.beats && s1.audio.beats.length > 50) && Math.abs(s1.bpm - 120) < 1 && Math.abs(s1.audio.offsetSec - 1.0) < 0.03, JSON.stringify({ locked: s1.audio && s1.audio.locked, beats: s1.audio && s1.audio.beats && s1.audio.beats.length, bpm: s1.bpm, off: s1.audio && s1.audio.offsetSec, fit: s1.audio && s1.audio.lockFit }));
check('the sheet is changed (title, lyrics, time, lines, filled)', s1.title === 'Tester - Test Song' && s1.time === '3/4' && s1.lines.length === 2 && !!s1.filled);
var mid = snap();
d.undo();
var s2 = d.S(), df = diff(before, snap());
check('one undo restores bpm, time, audio, lines, lyrics, title, filled', df.length === 0, df.join(' | '));
check('UI after undo: time 4/4, bpm 100, title and lyrics empty', document.getElementById('time').value === '4/4' && document.getElementById('bpm').value === '100' && document.getElementById('title').value === '' && document.getElementById('lyrics').value === '', [document.getElementById('time').value, document.getElementById('bpm').value, JSON.stringify(document.getElementById('title').value)].join(' '));
check('songGrid gone after undo', !d.songGrid());
check('undo moved one step to redo', t.undo.length === depth0 && t.redo.length === redo0 + 1, t.undo.length + '/' + t.redo.length);
d.redo();
var s3 = d.S(), df2 = diff(mid, snap());
check('redo brings everything back', df2.length === 0, df2.join(' | '));
check('UI after redo: time 3/4, bpm 120', document.getElementById('time').value === '3/4' && document.getElementById('bpm').value === '120', document.getElementById('time').value + ' ' + document.getElementById('bpm').value);
check('songGrid live again after redo', !!d.songGrid() && d.songGrid().length === s3.audio.beats.length);
check('redo/undo buttons follow the stacks', document.getElementById('undoBtn').disabled === false && document.getElementById('redoBtn').disabled === true);

// ---- the lined flag through an undo (song switched: lined false, offset kept)
d.pushUndo(); var sx = d.S(); sx.audio.locked = false; sx.audio.beats = null; sx.audio.lockFit = null; sx.audio.lined = false; sx.title = 'switched'; d.touch();
d.pushUndo(); d.S().title = 'switched 2'; d.touch();
d.undo();
check('undo keeps lined:false when the offset is > 0 (song was switched)', d.S().audio.lined === false && d.S().title === 'switched', 'lined ' + d.S().audio.lined + ' offset ' + d.S().audio.offsetSec + ' title ' + d.S().title);
d.undo(); d.redo(); d.redo();

// ---- merge window
var n0 = t.undo.length, t0 = Date.now();
d.pushUndo('lock'); var n1 = t.undo.length;
d.pushUndo('lock'); d.pushUndo('lock'); var n2 = t.undo.length;
check('pushUndo(lock) x3 within 1.2 s is one step', n1 === n0 + 1 && n2 === n1, n0 + ' ' + n1 + ' ' + n2);
d.pushUndo('other'); var n3 = t.undo.length; check('a different key is a new step', n3 === n2 + 1);
d.pushUndo(); var n4 = t.undo.length; check('no key never merges', n4 === n3 + 1);
d.pushUndo(); var n5 = t.undo.length; check('no key twice = two steps', n5 === n4 + 1);
check('pushUndo clears redo', t.redo.length === 0);
setTimeout(function () {
  var dt = Date.now() - t0; d.pushUndo('lock'); var n6 = t.undo.length;
  check('pushUndo(lock) after ' + dt + ' ms (>1200) starts a new step', n6 === n5 + 1, n5 + ' -> ' + n6);
  d.pushUndo('lock'); var n7 = t.undo.length; check('and merges again right after', n7 === n6);
  setTimeout(function () {
    d.pushUndo('lock'); var n8 = t.undo.length;
    setTimeout(function () {
      d.pushUndo('lock'); var n9 = t.undo.length;
      say('LOG a quiet lock every 1.0 s: depth ' + n7 + ' -> ' + n8 + ' -> ' + n9 + ' (the window slides: a re-lock every second never makes a new step)');
      // undo mid-merge: a lock, then undo, then a lock again within 1.2 s
      d.pushUndo('lock'); d.undo(); var nA = t.undo.length; d.pushUndo('lock'); var nB = t.undo.length;
      check('after an undo the next pushUndo(lock) is a new step (undoKey cleared)', nB === nA + 1, nA + ' -> ' + nB);
      // cap
      for (var i = 0; i < 130; i++) d.pushUndo();
      check('undo stack capped at 100 (UNDO_CAP)', t.undo.length === 100, 'depth ' + t.undo.length);
      var k = 0, tt0 = performance.now(); while (t.undo.length) { d.undo(); k++; if (k > 200) break; }
      check('undo all the way down (' + k + ' steps, ' + Math.round(performance.now() - tt0) + ' ms)', k === 100 && t.redo.length === 100);
      d.undo(); check('extra undo is a no-op', t.redo.length === 100 && t.undo.length === 0);
      var kk = 0; while (t.redo.length) { d.redo(); kk++; if (kk > 200) break; }
      check('redo all the way up (' + kk + ')', kk === 100 && t.undo.length === 100);
      // memory: what an undo step costs on this 2-line sheet
      say('LOG one undo snapshot of this sheet: ' + JSON.stringify(t.undo[0]).length + ' chars (x100 max = ' + Math.round(JSON.stringify(t.undo[0]).length * 100 / 1024) + ' KB)');
      try { localStorage.clear(); } catch (e) { /* ignore */ }
      say('LOG done');
    }, 1000);
  }, 1000);
}, 1300);
