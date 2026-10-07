// File save / open through the real File menu buttons, with the file pickers stubbed to capture the bytes.
// Also Print (score mode), the XML/MIDI export buttons and Duplicate. Each step waits (polls) for its outcome,
// since openFileDialog awaits IndexedDB (startInDir) which is slow against the virtual clock.
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
function snapOf(sheet) { var p = d.plain(sheet); delete p.updatedAt; return p; }
function toastText() { return document.getElementById('toast').textContent; }
function statusText() { return document.getElementById('stSave').textContent; }
function waitFor(cond, ms) { return new Promise(function (res) { var t0 = Date.now(); var iv = setInterval(function () { var ok = false; try { ok = cond(); } catch (e) { ok = false; } if (ok || Date.now() - t0 > (ms || 5000)) { clearInterval(iv); res(ok); } }, 50); }); }
function sleep(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
try { localStorage.clear(); } catch (e) { /* ignore */ }
var s = d.S();
s.title = 'File trip'; s.lyrics = 'Twin-kle star\nHo-ly night'; s.time = '3/4'; s.bpm = 97.5; s.lines = d.parseLyrics(s.lyrics);
var a = s.lines[0].syllables[0]; d.setSlotsRaw(a, 40); s.lines[0].syllables[1].pos = 40; s.lines[0].syllables[2].pos = 44; a.note = 'C'; a.oct = 5; a.drum = ['kick'];
s.lines[0].bars = 4; s.lines[1].syllables[0].note = 'G'; s.lines[1].syllables[1].rest = true;
var beats = []; for (var i = 0; i < 300; i++) beats.push(Math.round((7 + i * 0.6) * 1000) / 1000);
s.audio = { offsetSec: 7, lined: true, name: 'song.mp3', assetId: null, forTrack: null, beats: beats, locked: true, lockFit: { onHit: 88, avgMs: 9 } };
s.spotify = { trackId: 'sp9', name: 'N', durationMs: 1000, title: 'N', artist: 'Ar', album: '' }; s.filled = { key: 'spotify:sp9', title: 'N' };
d.touch(); d.renderAll();
var original = snapOf(s), captured = null, savedName = null, blobs = [], fileText = null;
window.showDirectoryPicker = undefined;
window.showSaveFilePicker = function (opts) { savedName = opts && opts.suggestedName; return Promise.resolve({ name: savedName, createWritable: function () { return Promise.resolve({ write: function (x) { if (typeof x === 'string') captured = x; else blobs.push({ name: savedName, size: x.size, type: x.type }); return Promise.resolve(); }, close: function () { return Promise.resolve(); } }); } }); };
window.showOpenFilePicker = function () { var txt = fileText; return Promise.resolve([{ name: 'rt.json', getFile: function () { return Promise.resolve({ name: 'rt.json', text: function () { return Promise.resolve(txt); } }); } }]); };
function openWith(text) { fileText = text; document.getElementById('toast').textContent = ''; var n = d.state.tabs.length; document.getElementById('fOpenFile').click(); return waitFor(function () { return d.state.tabs.length !== n || toastText() !== ''; }, 8000); }

sleep(700).then(function () {
  // 1. Save as, after the local save has settled
  document.getElementById('fSaveAs').click();
  return waitFor(function () { return !!captured; }, 8000);
}).then(function (ok) {
  check('Save as writes a JSON file named after the title', ok && savedName === 'File trip.json', 'name ' + savedName + ' captured ' + (captured ? captured.length + ' chars' : 'nothing'));
  var data = null; try { data = JSON.parse(captured); } catch (e) { data = null; }
  check('file is JSON with format dictation-sheet/2', !!data && data.format === 'dictation-sheet/2', data && data.format);
  var dfile = data ? diff(original, snapOf(d.normalize(data))) : ['no data'];
  check('file content normalizes back to the sheet', dfile.length === 0, dfile.join(' | '));
  return sleep(300);
}).then(function () {
  check('status after Save as: Saved to File trip.json, tab clean', /Saved to File trip\.json/.test(statusText()) && d.cur().dirty === false && !!d.cur().fileHandle, statusText() + ' dirty ' + d.cur().dirty);
  // 2. the fast sequence: an edit, then Ctrl+S within 400 ms
  d.pushUndo(); d.S().title = 'File trip'; d.touch(); captured = null;
  document.getElementById('fSave').click();
  return waitFor(function () { return !!captured; }, 8000);
}).then(function (ok) {
  var st0 = statusText();
  return sleep(700).then(function () {
    check('edit then Ctrl+S within 400 ms: status stays Saved (was "' + st0 + '")', /Saved to/.test(statusText()) && d.cur().dirty === false, 'after the debounced local save fires: "' + statusText() + '", dirty ' + d.cur().dirty + ', dot ' + !!document.querySelector('.tab.on .dot'));
  });
}).then(function () {
  // 3. Open the captured file
  var tabsBefore = d.state.tabs.length;
  return openWith(captured).then(function () {
    var opened = d.S();
    check('Open adds a tab with the file', d.state.tabs.length === tabsBefore + 1 && opened.title === 'File trip', 'tabs ' + d.state.tabs.length + ' title ' + opened.title + ' toast "' + toastText() + '"');
    var dopen = diff(original, snapOf(opened));
    check('opened sheet equals the saved one', dopen.length === 0, dopen.join(' | '));
    check('status says Opened rt.json', /Opened rt\.json/.test(statusText()), statusText());
    check('opened sheet is in ds-store under a new id', Object.keys(JSON.parse(localStorage.getItem('ds-store') || '{}')).length === 2, Object.keys(JSON.parse(localStorage.getItem('ds-store') || '{}')).length + ' keys');
    return tabsBefore + 1;
  });
}).then(function (n) {
  return openWith('not json').then(function () {
    check('garbage file: refused with a toast, no new tab', d.state.tabs.length === n && /not a dictation sheet/.test(toastText()), 'tabs ' + d.state.tabs.length + ' toast "' + toastText() + '"');
    return openWith(JSON.stringify({ sheet: JSON.parse(captured) }));
  }).then(function () {
    check('a {sheet: ...} wrapper (legacy store shape) is refused', d.state.tabs.length === n && /not a dictation sheet/.test(toastText()), 'tabs ' + d.state.tabs.length + ' toast "' + toastText() + '"');
    var corrupt = JSON.parse(captured); corrupt.lines.push(null);
    return openWith(JSON.stringify(corrupt));
  }).then(function () {
    check('a file with a null line: refused with "Could not open", no new tab', d.state.tabs.length === n && /Could not open/.test(toastText()), 'tabs ' + d.state.tabs.length + ' toast "' + toastText() + '"');
    var noFormat = JSON.parse(captured); delete noFormat.format; noFormat.title = 'No format field';
    return openWith(JSON.stringify(noFormat));
  }).then(function () {
    check('a file without the format field still opens (format is not checked)', d.state.tabs.length === n + 1 && d.S().title === 'No format field', 'tabs ' + d.state.tabs.length + ' toast "' + toastText() + '"');
    // 4. exports through the buttons
    blobs = []; document.getElementById('fXml').click();
    return waitFor(function () { return blobs.length === 1; }, 8000);
  }).then(function () {
    document.getElementById('fMidi').click();
    return waitFor(function () { return blobs.length === 2; }, 8000);
  }).then(function () {
    check('XML and MIDI export buttons write named files', blobs.length === 2 && /\.musicxml$/.test(blobs[0].name) && /\.mid$/.test(blobs[1].name) && blobs[0].size > 500 && blobs[1].size > 50, JSON.stringify(blobs));
    // 5. print
    var printed = 0; window.print = function () { printed++; }; document.getElementById('fPrint').click();
    return waitFor(function () { return printed > 0; }, 3000).then(function () {
      check('Print switches to score mode and calls window.print once', d.state.scoreMode === true && printed === 1, 'scoreMode ' + d.state.scoreMode + ' printed ' + printed);
      check('score view visible while printing, sheet hidden', document.getElementById('scoreView').hidden === false && document.getElementById('sheet').hidden === true);
      d.state.scoreMode = false; d.renderAll();
    });
  }).then(function () {
    // 6. duplicate
    var n0 = d.state.tabs.length; document.getElementById('fDup').click();
    return waitFor(function () { return d.state.tabs.length === n0 + 1; }, 3000).then(function () {
      check('Duplicate opens a copy tab', d.state.tabs.length === n0 + 1 && /copy$/.test(d.S().title), d.S().title);
      var m = JSON.parse(localStorage.getItem('ds-store') || '{}');
      check('the copy is in the store (' + Object.keys(m).length + ' sheets stored)', Object.keys(m).length === n0 + 1);
      say('LOG ds-tabs now ' + ((localStorage.getItem('ds-tabs') || '').length / 1024).toFixed(1) + ' KB for ' + d.state.tabs.length + ' tabs');
    });
  });
}).then(function () {
  try { localStorage.clear(); } catch (e) { /* ignore */ }
  say('LOG done');
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); });
