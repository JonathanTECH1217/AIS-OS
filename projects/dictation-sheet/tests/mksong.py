"""A synthetic song with a known downbeat, for the downbeat test: 4/4 at a given tempo, kick on 1 (heavy) and 3,
snare on 2 and 4, hats on the eighths, a bass root that changes every bar and a three-note chord pad that changes
every two bars, both on beat 1. Returns (wave at 16 kHz, downbeat times, beat times)."""
import numpy as np

SR = 16000


def song(bpm=78.0, bars=14, lead=0.9, seed=1, chords=True, heavy_one=True):
    beat = 60.0 / bpm
    n = int((lead + bars * 4 * beat + 1.0) * SR)
    band = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(seed)

    def hit(at, freq, amp, decay, noise=0.0):
        k0 = int(at * SR)
        L = int(decay * SR)
        if k0 >= n:
            return
        seg = np.arange(min(L, n - k0)) / SR
        env = np.exp(-seg / decay * 5)
        band[k0:k0 + len(seg)] += amp * env * (np.sin(2 * np.pi * freq * seg) + noise * rng.standard_normal(len(seg)))

    def tone(at, dur, freqs, amp):
        k0 = int(at * SR)
        L = int(dur * SR)
        if k0 >= n:
            return
        seg = np.arange(min(L, n - k0)) / SR
        env = np.minimum(1.0, seg / 0.02) * np.minimum(1.0, (dur - seg) / 0.05)
        for f in freqs:
            band[k0:k0 + len(seg)] += amp * env * np.sin(2 * np.pi * f * seg)

    roots = [55.0, 65.4, 49.0, 73.4]
    chord_sets = [(220.0, 277.2, 329.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7), (293.7, 370.0, 440.0)]
    downs, beats = [], []
    for k in range(bars * 4):
        t = lead + k * beat
        pos = k % 4
        bar = k // 4
        beats.append(t)
        if pos == 0:
            downs.append(t)
            hit(t, 60, 1.0 if heavy_one else 0.8, 0.28)
        if pos == 2:
            hit(t, 60, 0.75, 0.22)
        if pos in (1, 3):
            hit(t, 200, 0.6, 0.15, noise=1.5)
        hit(t, 6000, 0.3, 0.05, noise=2.0)
        hit(t + beat / 2, 6000, 0.25, 0.05, noise=2.0)
        if pos == 0:
            tone(t, 4 * beat, [roots[bar % 4]], 0.35)
            if chords:
                tone(t, 8 * beat if bar % 2 == 0 else 0.0, chord_sets[(bar // 2) % 4], 0.12)
    band += 0.01 * rng.standard_normal(n).astype(np.float32)
    band = band / (np.abs(band).max() + 1e-6) * 0.9
    return band.astype(np.float32), downs, beats
