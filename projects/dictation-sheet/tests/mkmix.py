"""spoken.wav under a loud synthetic band: drums at 78 bpm with hats on the eighths, a bass line, and noise, so the fit
can be tried on something closer to a song. Writes mix.wav (16 kHz) and mix.stamps.json (line starts from spoken.json)."""
import json, numpy as np, soundfile as sf, librosa
y, sr = librosa.load("spoken.wav", sr=16000, mono=True)
n = len(y) + 16000 * 2
t = np.arange(n) / 16000
band = np.zeros(n, dtype=np.float32)
beat = 60 / 78
rng = np.random.default_rng(1)
def hit(at, freq, amp, decay, noise=0.0):
    k0 = int(at * 16000); L = int(decay * 16000)
    if k0 >= n: return
    seg = np.arange(min(L, n - k0)) / 16000
    env = np.exp(-seg / decay * 5)
    band[k0:k0 + len(seg)] += amp * env * (np.sin(2 * np.pi * freq * seg) + noise * rng.standard_normal(len(seg)))
k = 0; tt = 0.3
while tt < n / 16000:
    pos = k % 4
    if pos in (0, 2): hit(tt, 60, 0.9, 0.25)           # kick
    if pos in (1, 3): hit(tt, 200, 0.7, 0.15, noise=1.5)  # snare
    hit(tt, 6000, 0.35, 0.05, noise=2.0); hit(tt + beat / 2, 6000, 0.3, 0.05, noise=2.0)  # hats on eighths
    hit(tt, 55 if pos < 2 else 73, 0.5, 0.5)            # bass
    tt += beat; k += 1
band += 0.02 * rng.standard_normal(n).astype(np.float32)
voice = np.zeros(n, dtype=np.float32); voice[:len(y)] = y * 0.9
mix = voice + band
mix = mix / (np.abs(mix).max() + 1e-6) * 0.9
sf.write("mix.wav", mix, 16000)
res = json.load(open("spoken.json", encoding="utf-8"))
stamps = [L["start"] - 0.15 for L in res["lines"]]
json.dump({"stamps": stamps}, open("mix.stamps.json", "w"))
print("wrote mix.wav", n / 16000, "s; stamps", [round(s, 2) for s in stamps])
