// The word box: Enter keeps the word and opens the next quarter note after it; Enter on an empty box ends the line;
// the arrows set the pitch while typing; Escape drops an empty new note; Enter in the middle of a line adds nothing.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function key(el, k, shift) { el.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true, shiftKey: !!shift })); }
function editing() { return document.querySelector('.syl-chip.editing'); }
function snap(l) { return d.sortedSyls(l).map(function (y) { return (y.text || '_') + '@' + y.pos + 'x' + d.lenSlots(y) + (y.sol ? '(' + y.sol + ')' : ''); }).join(' '); }
function line() { return d.S().lines[0]; }
s.time = '4/4'; s.bpm = 90; s.view = 'vocals'; s.key = { tonic: 'C', mode: 'major', laMinor: true }; s.lines = [{ kind: 'line', bars: 2, syllables: [] }]; s.lyrics = ''; s.title = ''; s.filled = null; d.cur().undo = []; d.state.tool = 'add'; d.renderAll();
// 1. click bar 1 beat 1, type, set the pitch with the arrows while the box is open, Enter
var c0 = document.querySelectorAll('.timeline .cell')[0], r = c0.getBoundingClientRect();
c0.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: r.left + 1, clientY: r.top + 2 }));
var ch = editing(); check('a click opens a box on a new note at slot 0', !!ch && line().syllables[0].pos === 0, snap(line()));
ch.textContent = 'Ev'; key(ch, 'ArrowUp');
var ch2 = editing();
check('ArrowUp keeps the box open with the text typed so far', !!ch2 && ch2.textContent === 'Ev', ch2 ? '"' + ch2.textContent + '"' : 'no box');
var y0 = line().syllables[0];
check('and moved the pitch up a step (the note now has a degree)', !!y0.sol || !!y0.note, 'sol ' + y0.sol + ' note ' + y0.note);
key(ch2, 'ArrowUp'); key(editing(), 'ArrowDown');
var solAfter = line().syllables[0].sol;
key(editing(), 'Enter');
setTimeout(function () {
  var l = line(), ch3 = editing();
  check('Enter keeps the word and opens the next note, an eighth right after (slot 4)', l.syllables.length === 2 && d.sortedSyls(l)[0].text === 'Ev' && d.sortedSyls(l)[1].pos === 4 && d.lenSlots(d.sortedSyls(l)[1]) === 2 && !!ch3, snap(l) + (ch3 ? ' box open' : ' no box'));
  check('the next note starts on the pitch just set', d.sortedSyls(l)[1].sol === solAfter, d.sortedSyls(l)[1].sol + ' vs ' + solAfter);
  ch3.textContent = 'ery'; key(ch3, 'Enter');
  setTimeout(function () {
    var l2 = line(), ch4 = editing();
    check('a third note is open at slot 6', l2.syllables.length === 3 && d.sortedSyls(l2)[2].pos === 6 && !!ch4, snap(l2));
    // 2. Enter on the empty box ends the line: the empty note goes
    key(ch4, 'Enter');
    setTimeout(function () {
      var l3 = line();
      check('Enter on an empty box closes it and takes the empty note away', l3.syllables.length === 2 && !editing(), snap(l3));
      // 3. editing a word in the middle: Enter keeps it and adds nothing
      var first = null; document.querySelectorAll('.syl-chip').forEach(function (c) { if (c.getAttribute('data-pos') === '0') first = c; });
      first.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
      var ch5 = editing(); ch5.textContent = 'Eve'; key(ch5, 'Enter');
      setTimeout(function () {
        var l4 = line();
        check('Enter on a word that is not the last keeps it and adds no note', l4.syllables.length === 2 && d.sortedSyls(l4)[0].text === 'Eve' && !editing(), snap(l4));
        // 4. Escape on a new empty note drops it
        var c1 = document.querySelectorAll('.timeline .cell')[1], r1 = c1.getBoundingClientRect();
        c1.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: r1.left + 1, clientY: r1.top + 2 }));
        var ch6 = editing(); check('a click on bar 2 opens a new note there', !!ch6 && line().syllables.length === 3);
        key(ch6, 'Escape');
        check('Escape drops the empty new note', line().syllables.length === 2 && !editing(), snap(line()));
        // 5. Shift+ArrowUp moves two steps
        var last = null; document.querySelectorAll('.syl-chip').forEach(function (c) { if (c.getAttribute('data-pos') === '4') last = c; });
        last.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
        var before = d.sortedSyls(line())[1].sol; key(editing(), 'ArrowUp', true); var after = d.sortedSyls(line())[1].sol;
        check('Shift+ArrowUp moves the pitch two steps', before !== after, before + ' -> ' + after);
        key(editing(), 'Escape');
        check('undo steps: pitch changes merge, notes and words are steps', d.cur().undo.length >= 4, d.cur().undo.length + ' steps');
        say('LOG final: ' + snap(line()));
        say('LOG done');
      }, 50);
    }, 50);
  }, 50);
}, 50);
