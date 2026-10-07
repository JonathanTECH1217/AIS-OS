var d = window.__ds, s = d.S(); d.state.prefs.side = false; d.state.prefs.pad = false; d.state.prefs.tools = true;
d.wordsToNotes('Ev-ery-thing so blur-ry and ev-ery-one so fake\nAnd ev-ery-bo-dy emp-ty and ev-ery-thing is so messed up', 'Narrow', { noUndo: true, quiet: true }); d.renderAll();
var w = document.getElementById('work'), sys = document.querySelector('.systems'), svg = document.querySelector('.system svg');
document.title = 'work ' + w.clientWidth + '/' + w.scrollWidth + ' systems ' + (sys && sys.clientWidth) + '/' + (sys && sys.scrollWidth) + ' svg ' + (svg && svg.getAttribute('width')) + ' zoom ' + d.state.prefs.zoom;
var p = document.createElement('div'); p.id = 'dbg'; p.textContent = document.title; p.style.cssText = 'position:fixed;top:0;left:200px;background:yellow;z-index:99;font:12px monospace'; document.body.appendChild(p);
