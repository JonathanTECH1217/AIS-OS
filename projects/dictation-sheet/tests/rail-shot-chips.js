// hyphenated words on the strip: one chip per syllable, chained
var d = window.__ds, s = d.S();
d.state.prefs.tools = true; d.state.prefs.side = true; d.setRibbon('edit');
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.key = { tonic: 'C', mode: 'major', laMinor: true };
d.wordsToNotes('Ev-ery-thing so blur-ry\nAnd ev-ery-one so fake', 'Chips', { noUndo: true, quiet: true });
d.state.tool = 'move'; d.syncTools(); d.renderAll();
