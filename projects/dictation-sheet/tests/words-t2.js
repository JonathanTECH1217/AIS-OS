// Part: words. Test 2: punctuation, apostrophes, capitals, typed hyphens, all caps, numbers, headers, blank lines,
// repeated stamps, LRC word tags, odd tokens.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function splitStr(text) { return d.syllableTexts(text).map(function (x) { return x.text + (x.hy ? '-' : ' '); }).join('').trim(); }
function n(text) { return d.syllableTexts(text).length; }
// word -> expected sung syllable count
var cases = [
  ["you're", 1], ["don't", 1], ["I'm", 1], ["can't", 1], ["won't", 1], ["we'll", 1], ["they've", 1], ["it's", 1], ["there's", 1], ["where's", 1], ["he's", 1], ["that's", 1], ["what's", 1], ["I'll", 1], ["'Cause", 1], ["’Cause", 1], ["you’re", 1], ["there’s", 1],
  ["Blurry", 2], ["BLURRY", 2], ["blurry", 2], ["Everything", 3], ["EVERYTHING", 3], ["SOMEONE", 2], ["YOU", 1], ["I", 1], ["A", 1],
  ["shoved", 1], ["messed", 1], ["showed", 1], ["loved", 1], ["lived", 1], ["walked", 1], ["jumped", 1], ["wanted", 2], ["needed", 2], ["takes", 1], ["makes", 1], ["faces", 2], ["places", 2], ["gave", 1], ["scene", 1], ["whole", 1], ["little", 2], ["stumble", 2],
  ["someone", 2], ["someone,", 2], ["oceans", 2], ["imagine", 3], ["nobody", 3], ["everybody's", 4], ["everyone's", 3], ["preoccupied", 4], ["obscene", 2], ["surrounds", 2], ["changing", 2], ["real", 1], ["fire", 1], ["hour", 1], ["every", 2], ["family", 3], ["different", 2],
  ["twin-kle", 2], ["some-one", 2], ["well-known", 2], ["co-operate", 4], ["twenty-one", 3], ["ex-girlfriend", 3], ["Nobo-,", 2], ["-", 0], ["--", 0], ["a-", 1], ["-a", 1],
  ["2", 1], ["4", 1], ["7", 1], ["100", 1], ["4ever", 2], ["2nite", 1], ["1st", 1], ["3rd", 1], ["24/7", 1],
  ["—", 0], ["...", 0], ["&", 0], ["(oh)", 1], ["(Oh-oh)", 2], ["oh-oh-oh", 3], ["yeah", 1], ["ooh", 1], ["mmm", 0], ["hmm", 0], ["la", 1], ["<00:12.34>", 0], ["<00:12.34>You", 1]
];
var bad = [];
cases.forEach(function (c) { var got = n(c[0]), sp = splitStr(c[0]); say('WORD|' + c[0] + '|' + got + '|' + c[1] + '|' + sp + (got === c[1] ? '' : '|WRONG')); if (got !== c[1]) bad.push(c[0] + '=' + sp + '(' + got + ' for ' + c[1] + ')'); });
say('LOG ' + bad.length + ' of ' + cases.length + ' words off: ' + bad.join('; '));
// lines through parseLyrics: headers, blank lines, whitespace, CRLF
var L = d.parseLyrics('[Chorus]\r\n\r\n   \r\nYou could be my someone\r\n[Verse 1]\r\n [Bridge] \r\n[Chorus] la la\r\n\tTab  spaced   words\t\r\n');
say('LOG parseLyrics kinds: ' + L.map(function (l) { return l.kind === 'header' ? 'H(' + l.text + ')' : 'L(' + l.syllables.length + ':' + l.syllables.map(function (y) { return y.text; }).join('|') + ')'; }).join(' '));
check('[Chorus], [Verse 1], [Bridge] are headers; blank and whitespace lines skipped; "[Chorus] la la" is a line', L.length === 6 && L[0].kind === 'header' && L[2].kind === 'header' && L[2].text === 'Verse 1' && L[3].kind === 'header' && L[4].kind === 'line' && L[5].kind === 'line' && L[5].syllables.length === 3);
// parseLrc: repeated stamps, same stamp twice, word tags, metadata, odd stamp forms, blank stamped lines
var P = d.parseLrc('[ar:Puddle of Mudd]\n[ti:Blurry]\n[offset:+300]\n[01:12.94][01:15.94] Can you take it all away?\n[01:19.01]Well, you shoved it in my face\n[01:19.01]Well, you shoved it in my face\n[00:23.09] <00:23.09> Everything\'s <00:23.60> so <00:24.10> blurry\n[00:23]No fraction\n[0:23.5]Short minute\n[00:23:50]Colon hundredths\n[00:23.090]Millis\n[02:51.16] \n[00:30.00] Well [I] know (x2)\n');
P.forEach(function (e, i) { say('LRC|' + i + '|' + e.t + '|' + e.text + '|' + n(e.text) + '|' + splitStr(e.text)); });
var wt = P.filter(function (e) { return e.text.indexOf('<') > -1; });
check('word tags <mm:ss.xx> do not leak into the text', wt.length === 0, wt.length ? 'leaked: "' + wt[0].text + '" -> ' + n(wt[0].text) + ' syllables: ' + splitStr(wt[0].text) : '');
check('a stamp used twice on one line gives two entries with the same text', P.filter(function (e) { return e.text === 'Can you take it all away?'; }).length === 2);
check('two lines with the same stamp both kept, in order', P.filter(function (e) { return e.t === 79.01; }).length === 2);
check('metadata tags [ar:] [ti:] [offset:] give no entries', !P.some(function (e) { return /Puddle|Blurry|300/.test(e.text); }));
check('[00:23] (no fraction) and [0:23.5] and [00:23.090] parse', P.some(function (e) { return e.text === 'No fraction'; }) && P.some(function (e) { return e.text === 'Short minute'; }) && P.some(function (e) { return e.text === 'Millis'; }));
check('[00:23:50] (colon hundredths) parses', P.some(function (e) { return e.text === 'Colon hundredths'; }), 'dropped');
check('blank stamped line is kept as an empty entry (an end marker for the line before)', P.some(function (e) { return e.t === 171.16 && e.text === ''; }));
check('[I] inside a lyric survives', P.some(function (e) { return e.text === 'Well [I] know (x2)'; }), P.filter(function (e) { return e.t === 30; }).map(function (e) { return '"' + e.text + '"'; }).join(','));
// a whole-line apostrophe/punctuation sweep as the panel would see it
var line = "Well, you shoved it in my face; there's no one left (that's real) — \"quoted\" 'single' ... yeah!";
say('LOG panel line: ' + n(line) + ' syllables: ' + splitStr(line));
