"""Listener with the audio engine kept active (a looped near-silent WAV): do frames flow, how fast does stop act, race."""
import io, random, struct, time, wave, winsound, requests
B = 'http://127.0.0.1:8765'
def status(): return requests.get(B + '/listen/status', timeout=5).json()
def frames(since=0): return requests.get(B + '/listen/frames', params={'since': since}, timeout=5).json()
buf = io.BytesIO(); w = wave.open(buf, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
w.writeframes(b''.join(struct.pack('<h', random.randint(-16, 16)) for _ in range(48000))); w.close(); wav = buf.getvalue()
print('before:', {k: status()[k] for k in ('running', 'count', 't0')})
try:
    import os
    wavp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server-quiet.wav'); open(wavp, 'wb').write(wav)
    winsound.PlaySound(wavp, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
    time.sleep(0.5)
    t_start = time.time(); r = requests.post(B + '/listen/start', timeout=5).json(); print('start:', {k: r[k] for k in ('running', 'count', 't0', 'err')})
    time.sleep(1.5)
    f = frames(0); n = len(f['frames']); now = time.time()
    print(f"after 1.5 s: running={f['running']} frames={n} mid={len(f['mid'])} t0-start={(f['t0'] - t_start) if f['t0'] else None}")
    if f['t0']: print(f"   wall since t0 {now - f['t0']:.3f} s -> expect {(now - f['t0']) * 100:.0f} frames, got {n}; low max {max(f['frames']):.3f} mid max {max(f['mid']):.3f}")
    t = time.time(); requests.post(B + '/listen/stop', timeout=5)
    for i in range(40):
        if not status()['running']: break
        time.sleep(0.05)
    print(f"stop took effect after {(time.time() - t) * 1000:.0f} ms (running={status()['running']})")
    requests.post(B + '/listen/start', timeout=5); time.sleep(0.5)
    requests.post(B + '/listen/stop', timeout=5)
    r = requests.post(B + '/listen/start', timeout=5).json(); print('stop then start at once -> start answers running', r['running'], 'count', r['count'])
    time.sleep(0.6); s = status(); print('0.6 s later: running', s['running'], 'count', s['count'])
    if s['running']:
        requests.post(B + '/listen/stop', timeout=5); time.sleep(0.5)
    print('cleanup:', {k: status()[k] for k in ('running', 'count')})
finally:
    winsound.PlaySound(None, 0)
time.sleep(0.5); print('end:', {k: status()[k] for k in ('running', 'count')})
