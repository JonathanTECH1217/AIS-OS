var d = window.__ds;
['edit', 'view', 'play'].forEach(function (r) { try { d.setRibbon ? d.setRibbon(r) : document.querySelector('[data-ribbon="' + r + '"]').click(); console.log('ribbon ' + r + ' ok'); } catch (e) { console.log('ribbon ' + r + ' threw ' + (e && e.message)); } });
try { d.renderAll(); console.log('renderAll ok'); } catch (e) { console.log('renderAll threw ' + e.message); }
try { document.getElementById('helpBtn').click(); console.log('help ok, sections ' + document.querySelectorAll('#helpPanel h3').length + ': ' + Array.prototype.map.call(document.querySelectorAll('#helpPanel h3'), function (h) { return h.textContent; }).join(', ')); } catch (e) { console.log('help threw ' + e.message); }
console.log('play ribbon buttons: ' + Array.prototype.map.call(document.querySelectorAll('#rbPlay button'), function (b) { return b.id || b.textContent.trim(); }).join(', '));
console.log('tools: ' + Array.prototype.map.call(document.querySelectorAll('#toolSeg button'), function (b) { return b.getAttribute('data-tool'); }).join(', ') + '; menubar: ' + Array.prototype.map.call(document.querySelectorAll('.menubar button'), function (b) { return b.id; }).join(', '));
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'u', bubbles: true })); console.log('after U the tool is ' + d.state.tool);
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'v', bubbles: true })); document.dispatchEvent(new KeyboardEvent('keydown', { key: 'b', bubbles: true })); console.log('V and B did nothing bad');
