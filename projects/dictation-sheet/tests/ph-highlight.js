// Test 4 (playhead part): highlightSlot on a sheet of 4 systems and 40 chips, one line held over a system break.
// Slots 0..end in 0.1 steps; exactly the chips whose [pos,end) hold the slot must be lit; DOM class toggles must be
// transitions only. Then followFrame and player.frame together, and all dark after player.stop.
var d = window.__ds, player = d.player, editor = d.editor, state = d.state;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fakeNow = 1000; performance.now = function () { return fakeNow; };
window.requestAnimationFrame = function () { return 0; }; window.cancelAnimationFrame = function () {};
player.ensureAudio = function () {};
function mkSheet(counts) {
  var text = counts.map(function (n) { var w = []; for (var i = 0; i < n; i++) w.push('da'); return w.join(' '); }).join('\n');
  d.wordsToNotes(text, 'Test', { noUndo: true, quiet: true });
  var W = document.getElementById('sys').clientWidth; state.prefs.zoom = Math.ceil((W - 130) / 3.5); d.renderWork();
}
var addN = 0, remN = 0, oAdd = DOMTokenList.prototype.add, oRem = DOMTokenList.prototype.remove;
DOMTokenList.prototype.add = function () { if (arguments[0] === 'playing') addN++; return oAdd.apply(this, arguments); };
DOMTokenList.prototype.remove = function () { if (arguments[0] === 'playing') remN++; return oRem.apply(this, arguments); };
try {
  // lines of 12, 20 and 8 quarter notes: 3 + 5 + 2 = 10 bars; 3 bars a system -> 4 systems, line 2 spans systems 2 and 3
  mkSheet([12, 20, 8]); var s = d.S(), spb = d.slotsPerBar(s.time);
  // a note in line 2 at bar 2 slot 12 held 8 slots: ends at 52, past the system break at 48
  var y = s.lines[1].syllables.filter(function (q) { return q.pos === 44; })[0]; d.setSlotsRaw(y, 8); d.renderWork();
  var chips = Array.prototype.map.call(document.querySelectorAll('.syl-chip'), function (c) { return { el: c, li: +c.getAttribute('data-li'), pos: +c.getAttribute('data-pos'), end: +c.getAttribute('data-end') }; });
  say('LOG sheet: ' + editor.systems.length + ' systems (' + editor.systems.map(function (sy) { return sy.bars.map(function (b) { return b.li + ':' + b.b; }).join(','); }).join(' | ') + '), ' + chips.length + ' chips, ' + player.bars.length + ' bars');
  check('4 systems and 40 chips', editor.systems.length === 4 && chips.length === 40);
  var held = chips.filter(function (c) { return c.pos === 44 && c.li === 1; })[0];
  check('the held chip is in the system before the break and runs to 52', !!held && held.end === 52 && editor.systems[1].chips.indexOf(editor.systems[1].chips.filter(function (r) { return r.el === held.el; })[0]) > -1, held ? 'end ' + held.end : 'no chip');
  var total = player.bars.length * spb, mism = 0, firstMism = null, expTrans = 0, prevSet = null, steps = 0, heldOk = 0, heldSteps = 0;
  addN = 0; remN = 0;
  for (var g = 0; g < total - 1e-9; g = Math.round((g + 0.1) * 10) / 10) {
    var bi = Math.floor(g / spb), bar = player.bars[bi], sil = bar.b * spb + (g - bi * spb);
    d.highlightSlot(bar, sil); steps++;
    var exp = chips.filter(function (c) { return c.li === bar.li && sil >= c.pos - 1e-9 && sil < c.end - 1e-9; }).map(function (c) { return c.el; });
    var lit = Array.prototype.slice.call(document.querySelectorAll('.syl-chip.playing'));
    var same = exp.length === lit.length && exp.every(function (e) { return lit.indexOf(e) > -1; });
    if (!same) { mism++; if (!firstMism) firstMism = 'slot ' + g + ' (line ' + bar.li + ' bar ' + bar.b + ' sys ' + bar.sys + '): expected ' + exp.map(function (e) { return e.getAttribute('data-pos'); }).join(',') + ' lit ' + lit.map(function (e) { return e.getAttribute('data-pos'); }).join(','); }
    if (bar.li === 1 && sil >= 48 && sil < 52) { heldSteps++; if (lit.indexOf(held.el) > -1) heldOk++; }
    if (prevSet) { exp.forEach(function (e) { if (prevSet.indexOf(e) < 0) expTrans++; }); prevSet.forEach(function (e) { if (exp.indexOf(e) < 0) expTrans++; }); } else expTrans += exp.length;
    prevSet = exp;
  }
  check('exactly the chips holding the slot are lit at every 0.1 step', mism === 0, steps + ' steps, ' + mism + ' mismatches' + (firstMism ? '; first: ' + firstMism : ''));
  check('the chip held over the system break stays lit in the next system', heldSteps > 0 && heldOk === heldSteps, heldOk + ' of ' + heldSteps + ' steps');
  check('DOM class toggles are transitions only', addN + remN === expTrans, 'add ' + addN + ' remove ' + remN + ' expected transitions ' + expTrans);
  // a chip held over TWO systems: line 2 bar 2 slot 12 stretched to 3 bars (end 92 > 80 = system 3 start)
  d.setSlotsRaw(y, 48); d.renderWork(); chips = Array.prototype.map.call(document.querySelectorAll('.syl-chip'), function (c) { return { el: c, li: +c.getAttribute('data-li'), pos: +c.getAttribute('data-pos'), end: +c.getAttribute('data-end') }; });
  held = chips.filter(function (c) { return c.pos === 44 && c.li === 1; })[0];
  say('LOG systems now: ' + editor.systems.map(function (sy) { return sy.bars.map(function (b) { return b.li + ':' + b.b; }).join(','); }).join(' | ') + '; held chip end ' + (held && held.end));
  var bi2 = 5, bar2 = player.bars[bi2]; d.highlightSlot(bar2, bar2.b * spb + 2);
  var litNow = Array.prototype.slice.call(document.querySelectorAll('.syl-chip.playing'));
  say('LOG   at line 2 bar ' + bar2.b + ' slot 2 (system ' + bar2.sys + '): held chip lit ' + (litNow.indexOf(held.el) > -1) + ' (expected ' + (bar2.b * spb + 2 < held.end) + ')');
  d.highlightClear(); d.setSlotsRaw(y, 4); d.renderWork();
  // followFrame and player.frame together
  var el = { paused: false, seeking: false, readyState: 4, duration: 300, playbackRate: 1, currentTime: 10, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
  d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: null, duration: 300, onset: null, voice: null, low: null, blob: false };
  s.bpm = 120; d.sheetAudio().offsetSec = 10; d.sheetAudio().lined = true; state.audioOn = false;
  el.currentTime = 10.7; d.followFrame(); var litF = document.querySelectorAll('.syl-chip.playing').length;
  check('followFrame lights the chip under the song while the band is off', litF === 1, litF + ' lit');
  player.startSlot = 0; player.start(); clearInterval(player.timer);
  fakeNow += 16; player.frame(); var litB = document.querySelectorAll('.syl-chip.playing').length;
  d.followFrame(); d.followSong(d.trackSrc()); var litB2 = document.querySelectorAll('.syl-chip.playing').length;
  check('with the band on, a leftover followFrame/followSong adds no second highlight', litB === 1 && litB2 === 1, 'band ' + litB + ' after follow calls ' + litB2);
  // followSong with the band on still moves the red line (showAt) to the song spot, not the band spot
  var sy0 = editor.systems[player.bars[0].sys], leftBand = sy0.ph.style.left; el.currentTime = 14.9; d.followSong(d.trackSrc()); var leftAfter = sy0.ph.style.left;
  say('LOG   red line with the band on: at ' + leftBand + ' from frame(), then followSong(file at 14.9 s) moved it to ' + leftAfter + ' (followSong is called by the strip ticker only when the band is off, by the strip drag only when the band is off)');
  player.stop();
  var dark = document.querySelectorAll('.syl-chip.playing').length, onFlags = 0; editor.systems.forEach(function (sy) { (sy.chips || []).forEach(function (r) { if (r.on) onFlags++; }); });
  check('after player.stop all chips are dark', dark === 0 && onFlags === 0, dark + ' lit, ' + onFlags + ' on flags');
  d.cur().audio = null;
  say('DONE');
} catch (e) { say('FAIL ' + (e && e.stack || e)); }
