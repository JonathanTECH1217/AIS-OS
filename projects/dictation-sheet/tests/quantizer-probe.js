// quantizer-probe.js: why did scenario L (a hold 10.0-18.2 with the next line stamped 18.45) fall back to evenSpans while K (hold to 18.0) did not?
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var fps = 100, N = fps * 60;
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
function mkVoice(spans) { var v = new Float32Array(N), i; for (i = 0; i < N; i++) v[i] = 0.4; spans.forEach(function (p) { sing(v, p[0], p[1]); }); return v; }
[18.0, 18.1, 18.2, 18.3].forEach(function (holdEnd) {
  var env = mkVoice([[10.0, holdEnd], [18.5, 18.8], [19.0, 19.3]]), vc = { env: env, fps: fps, start: 0, rises: d.risesOf(env) };
  var t0 = 9.95 - 0.12, t1 = 18.45 - 0.05, lv = d.lineLevels(vc, t0, t1), on = d.onsetCandidatesIn(vc, t0, t1, 1), sp = d.sungSpansIn(vc, t0, t1, 1, [false]);
  say('LOG hold to ' + holdEnd + ': lineLevels ' + JSON.stringify(lv) + ' onsets ' + JSON.stringify(on) + ' spans ' + JSON.stringify(sp));
});
var env2 = mkVoice([[10.0, 18.2], [18.5, 18.8], [19.0, 19.3]]);
say('LOG env around 10.0: ' + Array.prototype.slice.call(env2, 996, 1006).map(function (v) { return v.toFixed(2); }).join(' '));
var r2 = d.risesOf(env2); say('LOG rises around 10.0: ' + Array.prototype.slice.call(r2, 996, 1006).map(function (v) { return v.toFixed(3); }).join(' '));
say('LOG env 18.15-18.30: ' + Array.prototype.slice.call(env2, 1815, 1831).map(function (v) { return v.toFixed(2); }).join(' '));
