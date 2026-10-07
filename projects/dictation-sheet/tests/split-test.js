// the syllable splitter on words the lookup will hand it without hyphens
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var cases = { 'Silent': 'Si-lent', 'night,': 'night,', 'holy': 'ho-ly', 'All': 'All', 'you': 'you', 'yes': 'yes', 'are.': 'are.', 'what': 'what', 'baby': 'ba-by', 'very': 've-ry', 'away': 'a-way', 'little': 'lit-tle', 'people': 'peo-ple', 'wonderful': 'won-der-ful', 'I': 'I', 'love': 'love', 'fire': 'fire', 'the': 'the', 'yellow': 'yel-low', 'every': 'e-ve-ry', 'heaven': 'hea-ven', 'star': 'star', "you're": "you're", 'Together': 'To-gether' };
var fails = 0;
Object.keys(cases).forEach(function (w) { var got = d.syllableTexts(w).map(function (x) { return x.text + (x.hy ? '-' : ''); }).join(''), want = cases[w]; if (got !== want) { fails++; say('FAIL ' + w + ' -> ' + got + ' (want ' + want + ')'); } else say('PASS ' + w + ' -> ' + got); });
say((fails ? 'FAIL ' : 'PASS ') + 'splitter: ' + fails + ' of ' + Object.keys(cases).length + ' wrong');
