// The tools rail: one symbol per button, top to bottom; the names in the tips; a group's fields in a flyout that
// opens from the group's last icon and closes on Escape, on a click elsewhere and on a ribbon change.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function vis(el) { var r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; }
d.state.prefs.tools = true; d.state.prefs.side = false; d.setRibbon('edit'); d.renderAll();
var tools = document.getElementById('toolsDrawer'), tr = tools.getBoundingClientRect();
check('the rail is a slim column at the left edge', tr.left === 0 && tr.width >= 40 && tr.width <= 60 && tr.height > 300, 'left ' + tr.left + ' width ' + tr.width + ' height ' + Math.round(tr.height));
var rbs = Array.prototype.slice.call(document.querySelectorAll('#rbEdit .rb'));
check('the Edit set shows its buttons as squares (36 px), none wider than the rail', rbs.length >= 8 && rbs.every(function (b) { var r = b.getBoundingClientRect(); return r.width >= 30 && r.width <= 40 && r.height >= 30 && r.height <= 40; }), rbs.map(function (b) { return Math.round(b.getBoundingClientRect().width); }).join(','));
check('the buttons run top to bottom', rbs.every(function (b, i) { return i === 0 || b.getBoundingClientRect().top > rbs[i - 1].getBoundingClientRect().top; }), rbs.map(function (b) { return Math.round(b.getBoundingClientRect().top); }).join(','));
check('the labels are hidden, the symbols shown', rbs.every(function (b) { var l = b.querySelector('.lbl'), i = b.querySelector('.ico'); return (!l || !vis(l)) && i && vis(i); }));
check('every button has its name in the tip', rbs.every(function (b) { var l = b.querySelector('.lbl'); return !l || (b.title || '').toLowerCase().indexOf(l.textContent.trim().toLowerCase()) === 0 || b.classList.contains('more'); }), rbs.map(function (b) { return b.title.split(':')[0]; }).join(' | '));
var add = document.querySelector('#toolSeg [data-tool="add"]');
check('Add says "Add: ..." in the tip and keeps aria-label', /^Add: Click/.test(add.title) && add.getAttribute('aria-label') === 'Add', add.title.slice(0, 30));
check('Undo keeps its own tip', document.getElementById('undoBtn').title === 'Undo (Ctrl+Z)', document.getElementById('undoBtn').title);
// the Snap group: its select lives in a flyout behind the last icon
var snapGrp = document.getElementById('snapSel').closest('.grp'), more = snapGrp.querySelector('.rb.more'), fly = snapGrp.querySelector('.flyout');
check('the Snap group has a more button and a flyout holding the select', !!more && !!fly && fly.contains(document.getElementById('snapSel')) && !vis(fly), 'more ' + (more && more.title));
more.click();
var fr = fly.getBoundingClientRect();
check('a click opens the flyout beside the rail', vis(fly) && fr.left >= tr.right && fr.left < tr.right + 20 && Math.abs(fr.top - more.getBoundingClientRect().top) < 40 && more.classList.contains('on'), 'left ' + Math.round(fr.left) + ' top ' + Math.round(fr.top) + ' rail right ' + Math.round(tr.right));
check('the select inside works', (function () { var s = document.getElementById('snapSel'); s.value = 'beat'; s.dispatchEvent(new Event('change', { bubbles: true })); return d.state.prefs.snap === 'beat'; })(), d.state.prefs.snap);
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
check('Escape closes it', !vis(fly) && !more.classList.contains('on'));
more.click(); check('opens again', vis(fly));
document.getElementById('work').dispatchEvent(new MouseEvent('click', { bubbles: true }));
check('a click on the sheet closes it', !vis(fly));
more.click(); more.click();
check('the more button toggles', !vis(fly));
more.click(); d.setRibbon('view');
check('a ribbon change closes it and shows the View set', !vis(fly) && document.getElementById('rbView').hidden === false && document.getElementById('rbEdit').hidden === true && document.getElementById('drawerTitle').textContent === 'View');
// Play set: the song group's fields and the loop and volume and Spotify flyouts
d.setRibbon('play');
var play = Array.prototype.slice.call(document.querySelectorAll('#rbPlay .rb')).filter(vis);
check('the Play set shows its icons in the rail (' + play.length + ')', play.length >= 14 && play.every(function (b) { return b.getBoundingClientRect().width <= 40; }), play.map(function (b) { return b.id || b.title.split(':')[0]; }).join(','));
var song = document.getElementById('audStart').closest('.flyout');
check('bar 1 at, its label and the track note live in the song flyout', !!song && song.contains(document.getElementById('audInfo')) && !vis(song));
check('the two song arrows are in the rail', vis(document.getElementById('songEarlier')) && vis(document.getElementById('songLater')));
var vol = document.getElementById('volMetro').closest('.flyout'), sp = document.getElementById('spClient').closest('.flyout'), loop = document.getElementById('loopInfo').closest('.flyout');
check('volumes, Spotify and the loop note have flyouts', !!vol && !!sp && !!loop && vol !== sp && sp !== loop);
check('renderPlayUI still writes the Connect label', (function () { d.sp.connected = false; document.getElementById('spConnect').lastChild.textContent = 'x'; d.renderAll(); return document.getElementById('spConnect').lastChild.textContent === 'Connect'; })());
check('the hide button is a small ✕ with a tip', document.getElementById('toolsClose').textContent === '✕' && /Alt/.test(document.getElementById('toolsClose').title));
// the words panel next to the rail, the handles beyond both
d.state.prefs.side = true; d.renderAll();
var side = document.getElementById('side').getBoundingClientRect(), rail = document.getElementById('rail').getBoundingClientRect();
check('with the words open the panel starts where the rail ends and the handles sit after the panel', Math.abs(side.left - tr.width) < 2 && Math.abs(rail.left - side.right) < 2, 'side left ' + Math.round(side.left) + ' rail ' + Math.round(rail.left) + ' side right ' + Math.round(side.right));
d.state.prefs.side = false; d.state.prefs.tools = false; d.renderAll();
check('tools hidden: the handles sit at the edge', document.getElementById('rail').getBoundingClientRect().left === 0 && !vis(tools));
d.state.prefs.tools = true; d.setRibbon('edit'); d.renderAll();
say('LOG done');
