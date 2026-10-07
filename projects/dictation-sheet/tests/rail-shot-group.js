var d = window.__ds, s = d.S(); d.state.prefs.side = false; d.state.prefs.pad = false;
d.wordsToNotes('Ev-ery-thing so blur-ry and ev-ery-one so fake', 'Group', { noUndo: true, quiet: true }); d.state.tool = 'move'; d.syncTools(); d.renderAll();
d.setMarks([{ li: 0, si: 4 }, { li: 0, si: 5 }, { li: 0, si: 6 }]);
