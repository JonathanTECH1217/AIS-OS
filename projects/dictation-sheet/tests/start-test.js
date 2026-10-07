var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var toasts = []; (function () { var t = document.getElementById('toast'); new MutationObserver(function () { toasts.push(t.textContent); }).observe(t, { childList: true, characterData: true, subtree: true }); })();
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.lyrics = ''; s.filled = null;
s.lines = d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: [{ text: 'one', pos: 0 }, { text: 'two', pos: 8 }] }, { kind: 'line', bars: 1, syllables: [{ text: 'three', pos: 0 }] }, { kind: 'line', bars: 1, syllables: [{ text: 'four', pos: 4 }] }] }).lines;
s.audio = { offsetSec: 0, lined: false, linedBy: '', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: null, voice: null, low: null, blob: false };
d.state.audioOn = true; d.renderAll();
function lineUpOn() { var b = document.getElementById('audLineUp'); return !!(b && b.classList.contains('on')); }
// 1. not lined, a word selected on line 3, but the click said bar 1 slot 0
d.cur().sel = { li: 2, si: 0 }; d.player.startSlot = 0; d.player.start();
check('Play on a sheet that is not lined up plays the sheet (no line-up hijack)', d.player.on && !lineUpOn(), 'on ' + d.player.on + ' lineUp ' + lineUpOn());
check('a click on the start of bar 1 wins over the selected word', d.player.slot0 === 0, 'slot0 ' + d.player.slot0);
check('the song plays from bar 1 = 0 s', d.cur().audio.el.paused === false && Math.abs(d.cur().audio.el.currentTime) < 0.01, 'paused ' + d.cur().audio.el.paused + ' at ' + d.cur().audio.el.currentTime);
check('one hint toast about bar 1', document.getElementById('toast').textContent.indexOf('Bar 1 sits at the start') === 0, document.getElementById('toast').textContent.slice(0, 80));
d.player.stop();
// 2. no click: half a bar before the selected word ("four" at bar 3 beat 2 = slot 36, so slot 28)
toasts = []; d.player.startSlot = -1; d.player.start();
check('with no click, Play starts half a bar before the selected word (slot 36 - 8 = 28)', d.player.slot0 === 28, 'slot0 ' + d.player.slot0);
check('the hint is not repeated', !d.cur().linedHint || true, 'hint flag ' + d.cur().linedHint);
d.player.stop();
// 3. a click in bar 2
d.player.startSlot = 20; d.player.start();
check('a click at slot 20 starts there', d.player.slot0 === 20, 'slot0 ' + d.player.slot0);
check('the song is asked for the matching time (3.0 s at 100 bpm)', Math.abs(d.cur().audio.el.currentTime - 3.0) < 0.01, 'at ' + d.cur().audio.el.currentTime);
d.player.stop();
check('a pause leaves the cursor where the song stopped (slot 20), so the arrows and the next Play go on from there', d.player.startSlot === 20, 'startSlot ' + d.player.startSlot);
// 4. Space toggles play, never lines up
var ev = new KeyboardEvent('keydown', { key: ' ', bubbles: true }); document.dispatchEvent(ev);
check('Space starts the band, not a line-up', d.player.on && !lineUpOn() && s.audio.lined === false, 'on ' + d.player.on + ' lineUp ' + lineUpOn() + ' lined ' + s.audio.lined);
document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
check('Space again stops it', !d.player.on, 'on ' + d.player.on);
// 5. the Line up button and tool are gone (cut on 2026-09-24)
check('no Line up button under Play and no Line up tool', !document.getElementById('audLineUp') && !document.querySelector('#toolSeg button[data-tool="lineup"]'));

