import json, time, requests, sys, subprocess
B = "http://127.0.0.1:8765"
wav, txt = sys.argv[1], sys.argv[2]
st = requests.post(B + "/listen/start?record=1", timeout=30).json()
print("listen start", {k: st.get(k) for k in ("ok", "running", "record", "device", "why", "err")})
t_start = time.time()
time.sleep(0.5)
# play the spoken file through the speakers while the server records the sound card
ps = 'Add-Type -AssemblyName presentationCore; $p = New-Object System.Media.SoundPlayer "%s"; $p.PlaySync()' % wav
t_play = time.time()
subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=120)
time.sleep(0.8)
st2 = requests.get(B + "/listen/status", timeout=30).json()
print("after play: recorded %.1f s, frames %d, t0 %s (play began %.2f s after the capture's first sample)" % (st2.get("recorded", 0), st2.get("count", 0), st2.get("t0"), t_play - (st2.get("t0") or t_play)))
requests.post(B + "/listen/stop", timeout=30)
lines = [ln.strip() for ln in open(txt, encoding="utf-8-sig") if ln.strip()]
print("run", requests.post(B + "/align/run", json={"lines": lines, "source": "capture"}, timeout=60).json())
t0 = time.time()
while True:
    time.sleep(1)
    j = requests.get(B + "/align/status", timeout=30).json()["job"]
    if j["done"] or (j["error"] and not j["running"]):
        break
res = requests.get(B + "/align/result", timeout=30).json()
print("result ok", res.get("ok"), res.get("why"), "words", len(res.get("words", [])), "in %.1f s" % (time.time() - t0))
if res.get("ok"):
    lag = t_play - st2["t0"]
    print("first words (capture seconds; the play began at %.2f):" % lag)
    for w in res["words"][:8]:
        print("   %6.2f-%5.2f  %s" % (w["start"], w["end"], w["text"]))
    print("expected: the same words as the file run, shifted by about %.2f s" % lag)
