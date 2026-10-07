// Test 6 (playhead part): the auto-scroll in frame(): work.scrollTop += (mid - center) * 0.15 when the red line is
// below the middle. A long sheet in a short #work: does it converge without oscillating at a system change, does it
// ever scroll up (loop wrap), does it fight a scrollbar drag (no wheel event), and are fractional scrollTop kept.
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
var work = document.getElementById('work');
function phRect() { var g = player.position(), bi = Math.floor(g / player.spb), bar = player.bars[bi], sy = editor.systems[bar.sys]; return { r: sy.ph.getBoundingClientRect(), sys: bar.sys }; }
function run(ms, each) {
  var recs = [], end = fakeNow + ms;
  while (fakeNow < end && player.on) {
    fakeNow += 16; if (each) each(); player.frame(); if (!player.on) break;
    var p = phRect(), wr = work.getBoundingClientRect();
    recs.push({ t: fakeNow, sys: p.sys, st: work.scrollTop, mid: p.r.top + p.r.height / 2 - (wr.top + wr.height / 2), vis: p.r.top >= wr.top && p.r.bottom <= wr.bottom });
  }
  return recs;
}
try {
  mkSheet([8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]); var s = d.S(); s.bpm = 240; state.audioOn = false; s.spotify = null; s.audio = null;
  work.style.height = '420px'; work.style.maxHeight = '420px'; work.style.flex = 'none';
  say('LOG sheet: ' + editor.systems.length + ' systems, ' + player.bars.length + ' bars; #work ' + work.clientHeight + ' px tall, scrollHeight ' + work.scrollHeight + ', system height ' + document.querySelector('.system').getBoundingClientRect().height.toFixed(0) + ' px');
  check('#work scrolls', work.scrollHeight > work.clientHeight + 200);
  work.scrollTop = 100.4; say('LOG fractional scrollTop: set 100.4, read back ' + work.scrollTop); work.scrollTop = 0;
  // A: play through, watch the scroll at each system change
  player.startSlot = 0; player.start(); clearInterval(player.timer);
  var recs = run(26000), signFlips = 0, prevD = 0, invisible = 0, changes = [], maxStep = 0;
  for (var i = 1; i < recs.length; i++) {
    var dS = recs[i].st - recs[i - 1].st; if (dS !== 0 && prevD !== 0 && Math.sign(dS) !== Math.sign(prevD)) signFlips++; if (dS !== 0) prevD = dS; if (Math.abs(dS) > maxStep) maxStep = Math.abs(dS);
    if (!recs[i].vis) invisible++;
    if (recs[i].sys !== recs[i - 1].sys) { var traj = []; for (var k = i; k < Math.min(recs.length, i + 40); k += 4) traj.push(Math.round(recs[k].mid)); var settled = -1; for (k = i; k < recs.length; k++) { if (recs[k].mid <= 4) { settled = k - i; break; } } changes.push('sys ' + recs[i].sys + ': mid-center ' + traj.join('>') + ' settled in ' + settled + ' frames'); }
  }
  say('LOG A: ' + recs.length + ' frames, scrollTop ended at ' + recs[recs.length - 1].st + ', largest scroll step ' + maxStep.toFixed(1) + ' px, direction flips ' + signFlips + ', frames with the red line outside #work ' + invisible);
  say('LOG   ' + changes.join(' | '));
  check('no oscillation (no direction flips)', signFlips === 0, signFlips + ' flips');
  check('the red line stays inside #work while playing forward', invisible === 0, invisible + ' frames out of ' + recs.length);
  // B: the loop wrap upward: loop bars 9-17 (systems 3-5); after the wrap the line is two systems up
  d.cur().loop = { a: 9, b: 17 }; d.cur().loopOn = true; work.scrollTop = 0; player.startSlot = 0; player.start(); clearInterval(player.timer);
  recs = run(16000); var wrapAt = -1; for (i = 1; i < recs.length; i++) if (recs[i].sys < recs[i - 1].sys) { wrapAt = i; break; }
  if (wrapAt > 0) { var hidden = 0; for (k = wrapAt; k < recs.length && !recs[k].vis; k++) hidden++; var toVisible = -1; for (k = wrapAt; k < recs.length; k++) if (recs[k].vis) { toVisible = k - wrapAt; break; } say('LOG B loop wrap from system ' + recs[wrapAt - 1].sys + ' to ' + recs[wrapAt].sys + ': red line mid-center ' + Math.round(recs[wrapAt].mid) + ' px (negative = above), scrollTop ' + recs[wrapAt - 1].st + ' > ' + recs[wrapAt].st + ', line invisible for ' + hidden + ' frames (' + (hidden * 16 / 1000).toFixed(1) + ' s) until frame ' + toVisible); check('after the loop wrap the sheet scrolls back up to the line', recs[wrapAt].vis || (toVisible >= 0 && toVisible < 30), 'the scroll only ever moves down (mid > center + 4)'); }
  else say('LOG B no wrap seen');
  player.stop(); d.cur().loop = null; d.cur().loopOn = false;
  // C: a scrollbar drag (no wheel event) while the band plays low on the page
  work.scrollTop = 0; player.startSlot = 15 * 16; player.start(); clearInterval(player.timer); run(300);
  var pulled = [], sample = 0; run(1000, function () { work.scrollTop = 0; }); recs = run(600, function () { work.scrollTop = 0; if (sample++ % 6 === 0) pulled.push(Math.round(work.scrollTop)); });
  say('LOG C scrollbar drag to the top (no wheel/touch/key event) while playing at system ' + recs[0].sys + ': after each frame scrollTop is ' + recs.slice(0, 6).map(function (r) { return Math.round(r.st); }).join(',') + ' (the drag sets 0 every frame)');
  check('the auto-scroll yields to a scrollbar drag', recs.every(function (r) { return r.st < 5; }), 'it pulls ' + Math.round(recs[0].st) + ' px back every frame; lastUserScroll is only set by wheel, touchmove and keydown (line 4221), never by a scroll event');
  work.dispatchEvent(new WheelEvent('wheel', { bubbles: true })); work.scrollTop = 0; recs = run(600);
  check('after a wheel event the auto-scroll pauses 2 s', recs.every(function (r) { return r.st < 5; }), 'scrollTop after 0.6 s: ' + Math.round(recs[recs.length - 1].st));
  player.stop();
  say('DONE');
} catch (e) { say('FAIL ' + (e && e.stack || e)); }
