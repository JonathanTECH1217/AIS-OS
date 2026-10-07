var d = window.__ds, s = d.S();
s.time = '4/4'; s.view = 'vocals'; s.title = 'gap check'; d.cur().sel = null;
s.lines = d.normalize({ lines: [{ kind: 'line', bars: 2, syllables: [{ text: 'one', pos: 0 }, { text: 'two', pos: 4 }, { text: 'three', pos: 15 }, { text: 'four', pos: 16 }, { text: 'five', pos: 28 }] }, { kind: 'line', bars: 2, syllables: [] }] }).lines;
d.state.prefs.side = false; d.state.prefs.tools = false; d.state.prefs.zoom = 200; d.renderAll();
document.body.classList.remove('drawers-open', 'both-open', 'side-open', 'tools-open'); ['.tools', '.side', '.rail'].forEach(function (q) { var e = document.querySelector(q); if (e) e.hidden = true; });
d.drawSystems(); d.player.relayout(); d.player.showAt(31.5); window.scrollTo(0, 0);
