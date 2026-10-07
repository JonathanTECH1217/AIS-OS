// the note pad open over a sheet in G major, Vocals view
var d = window.__ds, s = d.S();
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
d.state.prefs.tools = true; d.state.prefs.side = false; d.setRibbon('edit');
s.time = '4/4'; s.bpm = 80; s.view = 'vocals'; s.title = 'Note pad'; s.key = { tonic: 'G', mode: 'major', laMinor: true };
s.lines = [{ kind: 'line', bars: 4, syllables: [mk(0, 'q', 'Ev'), mk(4, 'q', 'ery'), mk(8, 'h', 'thing'), mk(20, 'q', 'so'), mk(24, 'h', 'blur'), mk(32, 'q', 'ry')] }];
d.state.prefs.pad = true; d.renderAll();
