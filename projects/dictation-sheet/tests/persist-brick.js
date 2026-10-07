// Writes a ds-tabs whose one sheet has a null line (one corrupt entry), so persist-boot2.js can show what boot does.
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
try { localStorage.clear(); } catch (e) { /* ignore */ }
var good = { title: 'Good sheet', lyrics: 'a', bpm: 100, time: '4/4', lines: [{ kind: 'line', bars: 1, syllables: [{ text: 'a', pos: 0 }] }] };
var bad = { title: 'Bad sheet', lyrics: 'a', bpm: 100, time: '4/4', lines: [{ kind: 'line', bars: 1, syllables: [{ text: 'a', pos: 0 }] }, null] };
localStorage.setItem('ds-tabs', JSON.stringify({ tabs: [{ id: 'good1', sheet: good }, { id: 'bad1', sheet: bad }], active: 0 }));
localStorage.setItem('ds-store', JSON.stringify({ good1: good, bad1: bad }));
say('LOG wrote ds-tabs with a good sheet and a sheet holding one null line');
