// The Add tool: a click on a bar puts a note there with its word box open; Enter keeps the word and opens the next
// note right after; Enter on an empty box ends the line; the empty sheet's Start a line button; the new-line button.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function key(el, k) { el.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function editing() { return document.querySelector('.syl-chip.editing'); }
function line() { return d.S().lines[0]; }
function snap(l) { return d.sortedSyls(l).map(function (y) { return (y.text || '_') + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
function chipAt(pos) { var found = null; document.querySelectorAll('.syl-chip').forEach(function (c) { if (c.getAttribute('data-pos') === String(pos)) found = c; }); return found; }
s.time = '4/4'; s.bpm = 90; s.view = 'vocals'; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; d.cur().undo = []; d.state.tool = 'move'; d.renderAll();
// 1. the empty sheet offers Start a line
var startBtn = document.querySelector('#sheet .empty button');
check('an empty sheet shows a Start a line button', !!startBtn && startBtn.textContent === 'Start a line', startBtn ? startBtn.textContent : 'none');
startBtn.click();
check('Start a line makes an empty two-bar line and picks the Add tool', s.lines.length === 1 && s.lines[0].bars === 2 && s.lines[0].syllables.length === 0 && d.state.tool === 'add', s.lines.length + ' lines, tool ' + d.state.tool);
check('the tools row shows Add on', !!document.querySelector('#toolSeg button[data-tool="add"].on'));
// 2. a click on bar 1 near beat 2 with the Add tool
var c0 = document.querySelectorAll('.timeline .cell')[0], r = c0.getBoundingClientRect();
c0.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: r.left + r.width * 0.27, clientY: r.top + 2 }));
check('a click puts a note at the nearest snap slot (4, beat 2)', line().syllables.length === 1 && line().syllables[0].pos === 4, snap(line()));
var chip = editing();
check('its word box is open', !!chip, chip ? 'editing "' + chip.textContent + '"' : 'no box');
// 3. type the word, Enter: the word is kept and the next note opens right after
chip.textContent = 'Ev'; key(chip, 'Enter');
setTimeout(function () {
  var ch2 = editing();
  check('Enter keeps the word and opens the next note right after (slot 8), an eighth', line().syllables.length === 2 && d.sortedSyls(line())[0].text === 'Ev' && d.sortedSyls(line())[1].pos === 8 && d.lenSlots(d.sortedSyls(line())[1]) === 2 && !!ch2, snap(line()) + (ch2 ? ' box open' : ' no box'));
  ch2.textContent = 'ery'; key(ch2, 'Enter');
  setTimeout(function () {
    var ch3 = editing();
    check('the second word is kept and a third note, an eighth, is open at slot 10', d.sortedSyls(line())[1].text === 'ery' && line().syllables.length === 3 && d.sortedSyls(line())[2].pos === 10 && d.lenSlots(d.sortedSyls(line())[2]) === 2 && !!ch3, snap(line()));
    // 4. Enter on the empty box ends the line
    key(ch3, 'Enter');
    setTimeout(function () {
      check('Enter on an empty box closes it and takes the empty note away', line().syllables.length === 2 && !editing(), snap(line()));
      // 5. Tab does the same as Enter; Escape on the new empty note drops it
      chipAt(8).dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
      var ch4 = editing(); ch4.textContent = 'thing'; key(ch4, 'Tab');
      setTimeout(function () {
        var ch5 = editing();
        check('Tab keeps the word and opens the next note too', d.sortedSyls(line())[1].text === 'thing' && line().syllables.length === 3 && !!ch5, snap(line()));
        key(ch5, 'Escape');
        check('Escape drops the empty new note', line().syllables.length === 2 && !editing(), snap(line()));
        // 6. a note added past the last bar grows the line
        var last = d.sortedSyls(line())[1]; last.pos = 30; d.redrawLine(0);
        chipAt(30).dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
        var ch6 = editing(); ch6.textContent = 'thing'; key(ch6, 'Enter');
        setTimeout(function () {
          check('a note added past the last bar grows the line to three bars', line().bars === 3 && line().syllables.length === 3 && d.sortedSyls(line())[2].pos === 32, 'bars ' + line().bars + ' ' + snap(line()));
          key(editing(), 'Escape');
          // 7. the new-line button at the line's end
          var nl = null; document.querySelectorAll('.cellbtn').forEach(function (b) { if (b.textContent === '↵') nl = b; });
          check('the line end has a new-line button', !!nl);
          if (nl) nl.click();
          check('it starts an empty line under it', d.S().lines.length === 2 && d.S().lines[1].syllables.length === 0, d.S().lines.length + ' lines');
          // 8. W picks Add
          d.state.tool = 'move'; d.syncTools(); key(document, 'w');
          check('W picks the Add tool', d.state.tool === 'add', d.state.tool);
          check('undo steps were taken (one per note and line)', d.cur().undo.length >= 5, d.cur().undo.length + ' steps');
          say('LOG final: ' + snap(line()));
          say('LOG done');
        }, 50);
      }, 50);
    }, 50);
  }, 50);
}, 50);
