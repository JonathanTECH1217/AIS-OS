// first call after boot, no warm-up: what does the app's own splitter do, and does Hyphenator throw on a cold call?
var d = window.__ds, H = window.Hyphenator;
console.log('cold syllableTexts:', JSON.stringify(d.syllableTexts('Silent night, holy night').map(function (x) { return x.text + (x.hy ? '-' : ''); })));
try { console.log('cold direct:', JSON.stringify(String(H.hyphenate('wonderful', 'en-us')).split('­'))); } catch (e) { console.log('cold direct threw:', e && (e.stack || e.message)); }
console.log('warm syllableTexts:', JSON.stringify(d.syllableTexts('Silent night, holy night wonderful').map(function (x) { return x.text + (x.hy ? '-' : ''); })));
