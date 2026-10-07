// listenStart's node graph, rendered offline: does ChannelMerger(2) -> ScriptProcessor(1024, 2, 1) hand merger input 0
// to inputBuffer channel 0 and input 1 to channel 1? What gain does the voiceIR convolver (normalize=false) give at 1 kHz?
// Where does the first onaudioprocess playbackTime sit (listen.t0 in browser mode)?
var sr = 48000, ac = new OfflineAudioContext(1, sr * 0.5, sr);
var a = ac.createConstantSource(); a.offset.value = 0.25;
var b = ac.createConstantSource(); b.offset.value = 0.75;
var mix = ac.createChannelMerger(2), sp = ac.createScriptProcessor(1024, 2, 1), mute = ac.createGain(); mute.gain.value = 0;
var seen = [];
sp.onaudioprocess = function (e) { var ib = e.inputBuffer; seen.push([ib.numberOfChannels, +ib.getChannelData(0)[600].toFixed(3), +(ib.numberOfChannels > 1 ? ib.getChannelData(1)[600] : NaN).toFixed(3), +e.playbackTime.toFixed(4)]); };
a.connect(mix, 0, 0); b.connect(mix, 0, 1); mix.connect(sp); sp.connect(mute); mute.connect(ac.destination);
a.start(); b.start();
function voiceIR(ctx) {
  var sr = ctx.sampleRate, nh = Math.max(1, Math.round(sr / 3500)), nl = Math.max(1, Math.round(sr / 250)), off = (nl - nh) >> 1, i;
  var ir = ctx.createBuffer(1, nl, sr), d = ir.getChannelData(0);
  for (i = 0; i < nl; i++) d[i] = -1 / nl;
  for (i = 0; i < nh; i++) d[off + i] += 1 / nh;
  return ir;
}
function rms(x, from) { var t = 0, n = 0; for (var i = from; i < x.length; i++) { t += x[i] * x[i]; n++; } return Math.sqrt(t / n); }
function convGain(freq) {
  var c = new OfflineAudioContext(1, sr * 0.3, sr), o = c.createOscillator(), conv = c.createConvolver();
  o.frequency.value = freq; conv.channelCount = 1; conv.channelCountMode = 'explicit'; conv.normalize = false; conv.buffer = voiceIR(c);
  o.connect(conv); conv.connect(c.destination); o.start();
  return c.startRendering().then(function (buf) { return rms(buf.getChannelData(0), sr * 0.1) / (1 / Math.sqrt(2)); });
}
ac.startRendering().then(function () {
  var n = seen.length, ok = n > 0 && seen.every(function (r) { return r[0] === 2 && Math.abs(r[1] - 0.25) < 1e-3 && Math.abs(r[2] - 0.75) < 1e-3; });
  console.log((ok ? 'PASS' : 'FAIL') + ' merger->ScriptProcessor(1024,2,1): ' + n + ' blocks, channel0=' + (seen[0] && seen[0][1]) + ' (input 0 = 0.25) channel1=' + (seen[0] && seen[0][2]) + ' (input 1 = 0.75)');
  console.log('first playbackTime ' + (seen[0] && seen[0][3]) + ' s (= ' + (seen[0] && Math.round(seen[0][3] * sr)) + ' samples; the samples in that first block were captured from 0)');
  return convGain(1000);
}).then(function (g1k) {
  console.log('voiceIR gain at 1 kHz: ' + g1k.toFixed(3) + ' (box-difference theory 0.866)');
  return convGain(100);
}).then(function (g100) {
  console.log('voiceIR gain at 100 Hz: ' + g100.toFixed(3) + ' (theory 0.243)');
  return convGain(5000);
}).then(function (g5k) {
  console.log('voiceIR gain at 5 kHz: ' + g5k.toFixed(3) + ' (theory 0.221)');
  document.getElementById('out').textContent = __lines.join('\n');
}).catch(function (e) { console.log('FAIL ' + (e && e.stack || e)); document.getElementById('out').textContent = __lines.join('\n'); });
