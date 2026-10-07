  function voiceIR(ctx) {
    var sr = ctx.sampleRate, nh = Math.max(1, Math.round(sr / 3500)), nl = Math.max(1, Math.round(sr / 250)), off = (nl - nh) >> 1, i;
    var ir = ctx.createBuffer(1, nl, sr), d = ir.getChannelData(0);
    for (i = 0; i < nl; i++) d[i] = -1 / nl;
    for (i = 0; i < nh; i++) d[off + i] += 1 / nh;
    return ir;
  }
  // Voice-band loudness of a decoded track at 100 frames a second, in the listener's units: log1p(100 * RMS) of the mono
  // mean through voiceIR, rendered off the main thread. Null when it cannot be had or the track is over 20 minutes.
  async function voiceOf(ab) {
    try {
      var OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
      if (!OAC || !ab || !ab.length || ab.duration > 20 * 60) return null;
      var sr = ab.sampleRate, hop = Math.round(sr / 100), nl = Math.max(1, Math.round(sr / 250)), skip = nl >> 1;
      var ctx = new OAC(1, ab.length + skip, sr), src = ctx.createBufferSource(), conv = ctx.createConvolver();
      conv.channelCount = 1; conv.channelCountMode = 'explicit'; conv.normalize = false; conv.buffer = voiceIR(ctx);
      src.buffer = ab; src.connect(conv); conv.connect(ctx.destination); src.start(0);
      var out = (await ctx.startRendering()).getChannelData(0), n = Math.floor((out.length - skip) / hop), env = new Float32Array(n), i, j, k, acc;
      for (i = 0; i < n; i++) { acc = 0; for (j = skip + i * hop, k = j + hop; j < k; j++) acc += out[j] * out[j]; env[i] = Math.log1p(100 * Math.sqrt(acc / hop)); }
      return env;
    } catch (e) { return null; }
  }

var out = document.getElementById('out');
function say(t) { out.textContent += '\n' + t; }
try {
  var sr = 48000, n = sr * 3, oc = new OfflineAudioContext(1, n, sr), buf = oc.createBuffer(1, n, sr), ch = buf.getChannelData(0), i;
  for (i = 0; i < n; i++) { var t = i / sr; ch[i] = 0.02 * Math.sin(2 * Math.PI * 60 * t) + (t >= 1 && t < 2 ? 0.3 * Math.sin(2 * Math.PI * 1000 * t) : 0); }
  var ir = voiceIR(oc).getChannelData(0), sum = 0; for (i = 0; i < ir.length; i++) sum += ir[i];
  say('LOG voiceIR taps ' + ir.length + ' sum ' + sum.toFixed(6) + ' (0 means DC is cancelled)');
  var t0 = performance.now();
  voiceOf(buf).then(function (env) {
    if (!env) { say('FAIL voiceOf returned null'); return; }
    var q = [env[50], env[99], env[101], env[150], env[199], env[201], env[250]].map(function (v) { return Math.round(v * 100) / 100; });
    var ok = env.length === 300 && q[0] < 0.3 && q[3] > 1.5 && q[6] < 0.3;
    say((ok ? 'PASS' : 'FAIL') + ' voiceOf: length ' + env.length + ' frames [50,99,101,150,199,201,250] = ' + JSON.stringify(q) + ' in ' + Math.round(performance.now() - t0) + ' ms');
  }, function (e) { say('FAIL voiceOf rejected ' + e); });
} catch (e) { say('FAIL threw ' + (e && e.message)); }
