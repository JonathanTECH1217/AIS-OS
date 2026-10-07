"""Part: words. Writes words-t1.js from words-t1.template.js with the real Blurry LRC (blurry.lrc.json) embedded."""
import json
import os

SP = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(SP, "blurry.lrc.json"), encoding="utf-8"))
for name in ("words-t1", "words-t5"):
    tpl = open(os.path.join(SP, name + ".template.js"), encoding="utf-8").read()
    js = tpl.replace("__LRC__", json.dumps(d["synced"]))
    open(os.path.join(SP, name + ".js"), "w", encoding="utf-8").write(js)
    print("wrote", name + ".js with", len(d["synced"].splitlines()), "LRC lines")
