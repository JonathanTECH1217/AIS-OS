"""Write voice-test.js: the page's voiceIR and voiceOf (copied from index.html as they are now) plus a synthetic check."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = Path(r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\index.html").read_text("utf-8")
m = re.search(r"^  function voiceIR\(ctx\) \{.*?^  \}\n.*?^  async function voiceOf\(ab\) \{.*?^  \}\n", src, re.S | re.M)
assert m, "voiceIR/voiceOf not found"
test = m.group(0) + r"""
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
"""
(HERE / "voice-test.js").write_text(test, "utf-8")
print("wrote voice-test.js with", m.group(0).count("\n"), "lines of page code")
