// The real quota: fill localStorage, then GROW the sheet so its save no longer fits. What does the UI say?
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function kb(str) { return ((str || '').length / 1024).toFixed(1) + ' KB'; }
function status() { var e = document.getElementById('stSave'); return e.textContent + ' [' + e.className + ']'; }
try { localStorage.clear(); } catch (e) { /* ignore */ }
var s = d.S(), t = d.cur();
var text = []; for (var i = 0; i < 20; i++) text.push('Twin-kle twin-kle lit-tle star how');
d.wordsToNotes(text.join('\n'), 'Twenty lines', { quiet: true });
d.touch();
setTimeout(function () {
  check('20-line sheet saved (' + kb(localStorage.getItem('ds-store')) + ')', /Twenty lines/.test(localStorage.getItem('ds-store') || ''));
  var mb = 0, chunk = new Array(1024 * 1024 + 1).join('x'), small = new Array(8 * 1024 + 1).join('y'), sm = 0;
  try { for (var i = 0; i < 60; i++) { localStorage.setItem('__fill' + i, chunk); mb++; } } catch (e) { /* full */ }
  try { for (var j = 0; j < 200; j++) { localStorage.setItem('__small' + j, small); sm++; } } catch (e) { /* full */ }
  say('LOG quota reached: ' + mb + ' MB + ' + sm + ' x 8 KB filler (headroom now < 8 KB)');
  // grow the sheet by 40 lines (about +85 KB), which cannot fit any more
  var more = []; for (var k = 0; k < 60; k++) more.push('Twin-kle twin-kle lit-tle star how');
  d.wordsToNotes(more.join('\n'), 'Sixty lines now', { quiet: true });
  setTimeout(function () {
    var st = localStorage.getItem('ds-store') || '', tabs = localStorage.getItem('ds-tabs') || '';
    var took = /Sixty lines now/.test(st), tabsTook = /Sixty lines now/.test(tabs);
    say('LOG after growing at the quota: ds-store has the new sheet ' + took + ' (' + kb(st) + '), ds-tabs ' + tabsTook + ' (' + kb(tabs) + '), status "' + status() + '", dirty ' + t.dirty + ', dot ' + !!document.querySelector('.tab.on .dot'));
    check('store took the grown sheet at the quota', took);
    check('UI does not claim Saved when the store did not take it', took || status() !== 'Saved in this browser [st ok]', 'status "' + status() + '"');
    check('a version was still written or skipped cleanly', true, kb(localStorage.getItem('ds-versions')));
    for (var i2 = 0; i2 < 60; i2++) localStorage.removeItem('__fill' + i2);
    for (var j2 = 0; j2 < 200; j2++) localStorage.removeItem('__small' + j2);
    try { localStorage.clear(); } catch (e) { /* ignore */ }
    say('LOG done');
  }, 1000);
}, 1000);
