var d = window.__ds, H = window.Hyphenator;
function hy(w) { try { return JSON.stringify(String(H.hyphenate(w, 'en-us')).split('­')); } catch (e) { return 'threw ' + e.message; } }
['silent', 'Silent', 'SILENT', 'all', 'All', 'holy', 'Holy', 'night', 'Night', 'calm', 'wonderful', 'Wonderful', 'every', 'Every', 'together', 'Together'].forEach(function (w) { console.log(w, '->', hy(w)); });
console.log('syllableTexts:', JSON.stringify(d.syllableTexts('silent Silent all All holy Holy every Every together Together').map(function (x) { return x.text + (x.hy ? '-' : ''); })));
