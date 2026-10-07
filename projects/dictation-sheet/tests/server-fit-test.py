import json, time, requests, sys
B = "http://127.0.0.1:8765"
print("version", requests.get(B + "/version", timeout=5).json())
st = requests.get(B + "/align/status", timeout=30).json()
print("align status", {k: st[k] for k in ("available", "why")})
if not st["available"]:
    sys.exit("fit not available: " + st["why"])
wav = open(sys.argv[1], "rb").read()
print("upload", requests.post(B + "/align/audio", data=wav, timeout=60).json())
lines = [ln.strip() for ln in open(sys.argv[2], encoding="utf-8-sig") if ln.strip()]
print("run", requests.post(B + "/align/run", json={"lines": lines, "source": "upload"}, timeout=60).json())
t0 = time.time()
while True:
    time.sleep(1)
    j = requests.get(B + "/align/status", timeout=30).json()["job"]
    print("  %4.1fs %s %d%%" % (time.time() - t0, j["stage"], j["frac"] * 100))
    if j["done"] or (j["error"] and not j["running"]):
        break
    if time.time() - t0 > 600:
        sys.exit("timeout")
res = requests.get(B + "/align/result", timeout=30).json()
print("result ok", res.get("ok"), "why", res.get("why"), "words", len(res.get("words", [])), "tempo", res.get("tempo"), "beats", len(res.get("beats", [])))
print("hyphenated:", res.get("hyphenated"))
print("first word:", res["words"][0] if res.get("words") else None)
print("run again while idle:", requests.post(B + "/align/run", json={"lines": lines, "source": "capture"}, timeout=60).json())
