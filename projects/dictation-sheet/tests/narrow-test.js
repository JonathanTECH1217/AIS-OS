// In a narrow window (run with SIZE 700,700 via pagecheck's fixed 1400 width is not enough: this test checks what it
// can at any width) the page is never wider than the window, and a sheet wider than its space can be swiped sideways.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
d.state.prefs.side = false; d.state.prefs.pad = false; d.state.prefs.tools = true;
d.wordsToNotes('Ev-ery-thing so blur-ry and ev-ery-one so fake', 'Narrow', { noUndo: true, quiet: true }); d.renderAll();
var app = document.getElementById('app'), w = document.getElementById('work'), mb = document.querySelector('.menubar');
check('the page is no wider than the window', app.getBoundingClientRect().width <= window.innerWidth + 1 && w.getBoundingClientRect().right <= window.innerWidth + 1, Math.round(app.getBoundingClientRect().width) + ' / ' + window.innerWidth);
check('the top bar scrolls sideways when its buttons do not fit (never widens the page)', getComputedStyle(mb).overflowX === 'auto' && mb.getBoundingClientRect().width <= window.innerWidth + 1, getComputedStyle(mb).overflowX + ' ' + Math.round(mb.getBoundingClientRect().width));
// zoomed right in: the sheet is wider than its space and swipes sideways
d.state.prefs.zoom = 320; d.renderAll();
var sys = document.querySelector('.systems'), wide = sys.scrollWidth > sys.clientWidth || w.scrollWidth > w.clientWidth;
var sx = sys.scrollWidth > sys.clientWidth ? sys : w; var before = sx.scrollLeft; sx.scrollLeft = 200;
check('zoomed in the sheet is swipeable sideways where it does not fit', !wide || sx.scrollLeft > before, 'wide ' + wide + ' scrolled ' + sx.scrollLeft);
d.state.prefs.zoom = 200; d.renderAll();
say('LOG done');
