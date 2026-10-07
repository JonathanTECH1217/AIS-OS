// The keyboard focus: a new sheet, a click on a tool, Start a line, a click on the sheet and a closed word box all hand
// the keys to the sheet, so the arrows and n work at once; while typing in the words box they stay there.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function keyOn(el, k) { el.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function active() { var a = document.activeElement; return a ? (a.id || a.tagName) : 'none'; }
s.time = '4/4'; s.bpm = 100; s.lines = [{ kind: 'line', bars: 4, syllables: [] }]; d.cur().audio = null; d.state.audioOn = false; d.renderAll(); d.player.startSlot = -1;
// 1. typing in the words box never moves the cursor or adds notes
var ta = document.getElementById('lyrics'); ta.focus();
keyOn(ta, 'ArrowRight'); keyOn(ta, 'n');
check('with the focus in the words box the arrow and n do nothing to the sheet', d.player.startSlot === -1 && s.lines[0].syllables.length === 0, 'cursor ' + d.player.startSlot + ' notes ' + s.lines[0].syllables.length + ' active ' + active());
// 2. clicking the Add tool takes the keys to the sheet
document.querySelector('#toolSeg button[data-tool="add"]').click();
check('after clicking Add the sheet holds the focus', active() === 'work', active());
keyOn(document.activeElement, 'ArrowRight');
check('and the arrow moves the cursor', d.player.startSlot === 2, d.player.startSlot);
// 3. back in the words box, then a click on the sheet
ta.focus(); keyOn(ta, 'ArrowRight');
check('the words box keeps the keys again', d.player.startSlot === 2, d.player.startSlot);
document.getElementById('sheet').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, pointerId: 1 }));
check('a click on the sheet hands the keys back', active() === 'work', active());
keyOn(document.activeElement, 'n');
check('n adds a note at the cursor', s.lines[0].syllables.length === 1 && s.lines[0].syllables[0].pos === 2, s.lines[0].syllables.length + ' notes');
var ch = document.querySelector('.syl-chip.editing'); check('its box is open and holds the focus', !!ch && document.activeElement === ch, active());
ch.textContent = 'one'; keyOn(ch, 'Escape');
check('after the box closes the sheet has the keys', active() === 'work', active());
keyOn(document.activeElement, 'ArrowRight');
check('and the arrow moves on from after the note (6 -> 8)', d.player.startSlot === 8, d.player.startSlot);
// 4. the W key too, and a new sheet
ta.focus(); keyOn(ta, 'w'); check('W typed in the words box stays there', active() === 'lyrics' && d.state.tool === 'add', active());
document.getElementById('work').focus(); keyOn(document.activeElement, 'm'); keyOn(document.activeElement, 'w');
check('W on the sheet picks Add and keeps the focus on the sheet', d.state.tool === 'add' && active() === 'work', d.state.tool + ' ' + active());
say('LOG done');
