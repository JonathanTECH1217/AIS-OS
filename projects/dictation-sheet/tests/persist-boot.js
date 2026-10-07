// Boot check: persist-rt.js left a raw OLD sheet in ds-tabs. Did the page boot from it without errors?
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var t = d.cur(), s = d.S();
if (!t) { say('FAIL boot is dead: cur() is null, tabs ' + d.state.tabs.length + ', #sheet children ' + document.getElementById('sheet').children.length + ', tabbar "' + document.getElementById('tabbar').textContent + '", status "' + document.getElementById('stSave').textContent + '"'); try { localStorage.clear(); } catch (e) { /* ignore */ } throw new Error('boot dead'); }
say('LOG booted tab id ' + t.id + ' title "' + s.title + '" tabs ' + d.state.tabs.length + ' active ' + d.state.active);
check('old sheet from ds-tabs boots (title Old)', s.title === 'Old');
check('boot used the raw ds-tabs entry (id oldsheet1)', t.id === 'oldsheet1', 'id ' + t.id);
check('old sheet has 7 syllables on line 0, all with numeric pos', s.lines[0] && s.lines[0].syllables.length === 7 && s.lines[0].syllables.every(function (y) { return typeof y.pos === 'number' && isFinite(y.pos); }));
check('filled is null, audio lined from offsetSec, spotify null', s.filled === null && s.audio && s.audio.lined === true && s.spotify === null, JSON.stringify({ filled: s.filled, audio: s.audio, spotify: s.spotify }));
check('no NaN in the rendered page', document.querySelectorAll('[style*="NaN"]').length === 0);
check('no draw errors', !document.querySelector('.noteshint'), (document.querySelector('.noteshint') || {}).textContent);
say('LOG save status: "' + document.getElementById('stSave').textContent + '"');
say('LOG time box ' + document.getElementById('time').value + ' bpm box ' + document.getElementById('bpm').value);
try { localStorage.clear(); } catch (e) { /* ignore */ }
