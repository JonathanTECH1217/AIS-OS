// After persist-brick.js: does the page boot at all? (pagecheck prints the REJECTED boot error above this.)
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var d = window.__ds, t = d.cur();
check('page boots with one corrupt sheet in ds-tabs (the good sheet should still open)', !!t, 'cur() ' + (t ? 'ok, title "' + t.sheet.title + '"' : 'null') + '; tabs ' + d.state.tabs.length + '; #sheet children ' + document.getElementById('sheet').children.length + '; tabbar "' + document.getElementById('tabbar').textContent + '"; status "' + document.getElementById('stSave').textContent + '"; File menu enabled ' + !document.getElementById('mFile').disabled);
check('the bad ds-tabs is dropped or repaired so the next boot works', !/Bad sheet/.test(localStorage.getItem('ds-tabs') || '') || !!t, 'ds-tabs still holds the bad sheet: ' + /Bad sheet/.test(localStorage.getItem('ds-tabs') || ''));
say('LOG keys after boot: ' + Object.keys(localStorage).join(','));
try { localStorage.clear(); } catch (e) { /* ignore */ }
