// a loop from bar 1 beat 2& to bar 3 beat 3 on a short sheet
var d = window.__ds, s = d.S();
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
d.state.prefs.tools = true; d.state.prefs.side = false; d.state.prefs.pad = false; d.setRibbon('play');
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.title = 'Loop'; d.cur().audio = null;
s.lines = [{ kind: 'line', bars: 4, syllables: [mk(0, 'q', 'Ev'), mk(4, 'q', 'ery'), mk(8, 'h', 'thing'), mk(20, 'q', 'so'), mk(24, 'h', 'blur'), mk(32, 'q', 'ry')] }];
d.cur().loop = d.makeLoop(6, 40); d.cur().loopOn = true; d.renderAll(); d.applyLoop();
