// is the syllable splitter's dictionary (Hyphenator) alive in the built page?
var d = window.__ds;
console.log('Hyphenator:', typeof window.Hyphenator, 'languages:', window.Hyphenator && window.Hyphenator.languages ? Object.keys(window.Hyphenator.languages).join(',') : 'none');
try { console.log('direct hyphenate(silent):', JSON.stringify(String(window.Hyphenator.hyphenate('silent', 'en-us')).split('­'))); } catch (e) { console.log('direct hyphenate threw:', e && e.message); }
try { window.Hyphenator.config({ minwordlength: 3, hyphenchar: '­', displaytogglebox: false, safecopy: false, storagetype: 'none' }); var lo = window.Hyphenator.languages['en-us']; lo.leftmin = 1; lo.rightmin = 1; console.log('after config, hyphenate(silent):', JSON.stringify(String(window.Hyphenator.hyphenate('silent', 'en-us')).split('­')), 'prepared:', lo.prepared); } catch (e) { console.log('config path threw:', e && e.message); }
console.log('syllableTexts:', JSON.stringify(d.syllableTexts('Silent night holy night All is calm wonderful beautiful').map(function (x) { return x.text + (x.hy ? '-' : ''); })));
