// runs 1.5 s after boot inside the built page: a few readouts about what got drawn
console.log('systems drawn:', document.querySelectorAll('.system').length, 'chips:', document.querySelectorAll('.syl-chip').length, 'noteheads:', document.querySelectorAll('.vf-notehead').length);
console.log('NaN styles:', document.querySelectorAll('[style*="NaN"]').length, 'draw failures:', Array.prototype.filter.call(document.querySelectorAll('.system'), function (s) { return /Could not draw/.test(s.textContent); }).length);
console.log('hook present:', typeof window.__ds === 'object' ? Object.keys(window.__ds).join(',') : 'no');
