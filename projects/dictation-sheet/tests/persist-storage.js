// Storage: touch() lands in ds-store within 1 s; size of a 60-line placed sheet; the three keys; a failing setItem
// (simulated quota) and the real quota.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function kb(str) { return ((str || '').length / 1024).toFixed(1) + ' KB'; }
function status() { var e = document.getElementById('stSave'); return e.textContent + ' [' + e.className + ']'; }
try { localStorage.clear(); } catch (e) { /* ignore */ }
var s = d.S(), t = d.cur();
var text = []; for (var i = 0; i < 60; i++) text.push('Twin-kle twin-kle lit-tle star how');
d.wordsToNotes(text.join('\n'), 'Sixty lines', { quiet: true });
var letters = ['C', 'D', 'E', 'F', 'G', 'A', 'B'], k = 0;
s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var p = 0; l.syllables.forEach(function (y) { y.note = letters[k % 7]; y.sol = 'do'; y.drum = ['kick', 'hh']; y.pos = p; p += 4; k++; }); l.bars = 2; });
var beats = []; for (var b = 0; b < 300; b++) beats.push(Math.round((5.0 + b * 0.5) * 1000) / 1000);
s.audio = { offsetSec: 5, lined: true, name: 'song.mp3', assetId: null, forTrack: null, beats: beats, locked: true, lockFit: { onHit: 90, avgMs: 10 } };
d.renderAll();
say('LOG sheet: ' + k + ' syllables on ' + s.lines.length + ' lines');
var sheetJson = JSON.stringify(d.plain(s)); say('LOG one 60-line placed sheet as JSON: ' + kb(sheetJson) + ' (' + Math.round(sheetJson.length / k) + ' chars per syllable)');
var tA = performance.now(); d.touch(); var tB = performance.now();
check('touch() returns fast (' + (tB - tA).toFixed(1) + ' ms) and marks the tab dirty', tB - tA < 50 && t.dirty === true);
check('status says Saving right after touch', /^Saving/.test(status()), status());
check('nothing written yet (debounced)', !localStorage.getItem('ds-store'));
setTimeout(function () {
  var st = localStorage.getItem('ds-store') || '', m = {}; try { m = JSON.parse(st); } catch (e) { /* ignore */ }
  check('ds-store holds the sheet within 1 s of touch', !!(m[t.id] && m[t.id].title === 'Sixty lines'), 'keys ' + Object.keys(m).join(',') + ' id ' + t.id);
  check('status says Saved in this browser', status() === 'Saved in this browser [st ok]', status());
  check('tab no longer dirty', t.dirty === false);
  var tabs = localStorage.getItem('ds-tabs') || '', vers = localStorage.getItem('ds-versions') || '', prefs = localStorage.getItem('ds-prefs') || '';
  say('LOG localStorage after one save: ds-store ' + kb(st) + ', ds-tabs ' + kb(tabs) + ', ds-versions ' + kb(vers) + ', ds-prefs ' + prefs.length + ' chars; total ' + kb(st + tabs + vers + prefs) + '; keys ' + Object.keys(localStorage).join(','));
  check('ds-tabs holds a second full copy of the sheet (session)', /Sixty lines/.test(tabs) && tabs.length > sheetJson.length * 0.9, kb(tabs));
  check('ds-versions holds a third copy after the first save', /Sixty lines/.test(vers), kb(vers));
  // cost of one localSave with this store: time the debounced save by touching again
  var t1 = performance.now(); d.touch();
  setTimeout(function () {
    // a failing setItem (quota, private mode, blocked storage)
    var orig = Storage.prototype.setItem, blocked = [];
    Storage.prototype.setItem = function (key, v) { blocked.push(key + ' ' + kb(v)); var e; try { e = new DOMException('Failed to execute setItem on Storage: exceeded the quota.', 'QuotaExceededError'); } catch (x) { e = new Error('QuotaExceededError'); } throw e; };
    s.title = 'Changed after quota'; d.touch();
    setTimeout(function () {
      Storage.prototype.setItem = orig;
      var m2 = {}; try { m2 = JSON.parse(localStorage.getItem('ds-store') || '{}'); } catch (e) { /* ignore */ }
      say('LOG setItem calls that threw: ' + blocked.join(' | '));
      check('store did not take the change (setItem threw)', !(m2[t.id] && m2[t.id].title === 'Changed after quota'));
      check('status must not claim "Saved in this browser" after setItem threw', status() !== 'Saved in this browser [st ok]', 'status "' + status() + '", tab dirty ' + t.dirty + ', tab dot ' + !!document.querySelector('.tab.on .dot'));
      check('ds-tabs is now stale (title still Sixty lines)', /"title":"Sixty lines"/.test(localStorage.getItem('ds-tabs') || ''));
      // the real quota: fill it, then a save that cannot fit
      var mb = 0, err = null, chunk = new Array(1024 * 1024 + 1).join('x');
      try { for (var i = 0; i < 60; i++) { localStorage.setItem('__fill' + i, chunk); mb++; } } catch (e) { err = e; }
      var small = new Array(32 * 1024 + 1).join('y'), sm = 0; try { for (var j = 0; j < 64; j++) { localStorage.setItem('__small' + j, small); sm++; } } catch (e) { /* full */ }
      say('LOG real quota on this origin: ' + mb + ' MB + ' + sm + ' x 32 KB fitted, then ' + (err ? err.name : 'no error') + ' (store keys now ' + kb(localStorage.getItem('ds-store')) + ')');
      s.title = 'Changed at real quota'; d.touch();
      setTimeout(function () {
        var m3 = {}; try { m3 = JSON.parse(localStorage.getItem('ds-store') || '{}'); } catch (e) { /* ignore */ }
        var took = !!(m3[t.id] && m3[t.id].title === 'Changed at real quota');
        say('LOG at the real quota: store took the change ' + took + ', ds-tabs has the new title ' + /Changed at real quota/.test(localStorage.getItem('ds-tabs') || '') + ', status "' + status() + '", dirty ' + t.dirty);
        check('at the real quota the UI does not claim Saved unless the store took it', took || status() !== 'Saved in this browser [st ok]', 'took ' + took + ' status "' + status() + '"');
        for (var i2 = 0; i2 < 60; i2++) localStorage.removeItem('__fill' + i2);
        for (var j2 = 0; j2 < 64; j2++) localStorage.removeItem('__small' + j2);
        // how many such sheets fit: versions keep up to 20 copies per sheet id
        say('LOG budget: one sheet ' + kb(sheetJson) + '; store + tabs + versions after 20 versions = ~' + Math.round(sheetJson.length * 22 / 1024) + ' KB per open sheet');
        try { localStorage.clear(); } catch (e) { /* ignore */ }
        say('LOG done');
      }, 1000);
    }, 1000);
  }, 1000);
}, 1000);
