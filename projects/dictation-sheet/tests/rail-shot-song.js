// a sheet that starts before the song: the green line at bar 2, a few notes, the Play set in the rail
var d = window.__ds, s = d.S();
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
d.state.prefs.tools = true; d.state.prefs.side = false; d.setRibbon('play');
s.time = '4/4'; s.bpm = 80; s.view = 'vocals'; s.title = 'Green line'; s.spotify = null; s.filled = null;
d.cur().audio = { el: { paused: true, currentTime: 0, duration: 120, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'song.wav', peaks: null, duration: 120, onset: null, voice: null, low: null, blob: false };
d.state.audioOn = true;
s.audio = { offsetSec: -3, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
s.lines = [{ kind: 'line', bars: 4, syllables: [mk(16, 'q', 'Ev'), mk(20, 'q', 'ery'), mk(24, 'h', 'thing'), mk(36, 'q', 'so'), mk(40, 'h', 'blur'), mk(48, 'q', 'ry')] }];
d.renderAll();
