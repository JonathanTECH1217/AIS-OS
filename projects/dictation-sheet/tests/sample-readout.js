var d = window.__ds, s = d.S();
console.log('sample syllables:', JSON.stringify(s.lines.map(function (l) { return l.kind === 'line' ? l.syllables.map(function (y) { return y.text + (y.hy ? '-' : ''); }).join(' ') : '[' + l.text + ']'; })));
console.log('old splitter would give for the untyped words:', JSON.stringify(d.syllableTexts('star, How I won-der what you are.').map(function (x) { return x.text + (x.hy ? '-' : ''); })));
