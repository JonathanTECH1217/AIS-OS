// Clears this profile's localStorage (a bad ds-tabs bricks every boot, see persist-boot2.js).
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var d = window.__ds;
say('LOG before clear: keys ' + Object.keys(localStorage).join(',') + '; booted tab: ' + (d && d.cur() ? 'yes' : 'NO (boot dead)') + '; #sheet children ' + document.getElementById('sheet').children.length + '; tabbar text "' + document.getElementById('tabbar').textContent + '"');
try { localStorage.clear(); } catch (e) { /* ignore */ }
say('LOG cleared');
