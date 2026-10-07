// a 20-slot note across the barline (grip result) and a 3-note word split by a drop, for the eye
var d = window.__ds;
var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'tie shot'; s.audio = null;
s.lines = d.normalize({ lines: [
  { kind: 'line', bars: 1, syllables: [{ text: 'one', pos: 0, len: 'w', xs: 4 }, { text: 'two', pos: 20 }, { text: 'three', pos: 24 }] },
  { kind: 'line', bars: 1, syllables: [{ text: 'beau', pos: 6, hy: true }, { text: 'ti', pos: 10, hy: true }, { text: 'star', pos: 12 }, { text: 'ful', pos: 16 }] }
] }).lines;
d.state.prefs.zoom = 260; d.state.tool = 'move'; d.setSel(null); d.renderAll();
window.scrollTo(0, 0);
