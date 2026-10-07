// does runjs.py wait for async work? a 3 s timer and a tiny OfflineAudioContext render
var out = document.getElementById('out');
function say(t) { out.textContent += '\n' + t; }
var t0 = performance.now();
setTimeout(function () { say('TIMER 3 s fired at ' + Math.round(performance.now() - t0) + ' ms'); }, 3000);
try {
  var oc = new OfflineAudioContext(1, 48000, 48000), src = oc.createBufferSource(); src.buffer = oc.createBuffer(1, 48000, 48000); src.connect(oc.destination); src.start(0);
  oc.startRendering().then(function (b) { say('RENDER done at ' + Math.round(performance.now() - t0) + ' ms, ' + b.length + ' samples'); }, function (e) { say('RENDER failed ' + e); });
} catch (e) { say('RENDER threw ' + e); }
console.log('sync part done');
