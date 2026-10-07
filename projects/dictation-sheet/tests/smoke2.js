var d = window.__ds; console.log('ds keys', d ? Object.keys(d).length : 'none', 'VF', typeof Vex !== 'undefined' && Vex.Flow ? 'yes' : 'no', 'tabs', d && d.state ? d.state.tabs.length : '?');
var s = d.S(); console.log('sheet', s ? s.title + ' lines ' + s.lines.length + ' bpm ' + s.bpm + ' audio ' + JSON.stringify(s.audio) : 'none');
console.log('statusNote hint:', document.getElementById('stHint').textContent.slice(0, 60));
