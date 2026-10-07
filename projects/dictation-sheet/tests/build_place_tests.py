"""Inject the real Blurry timed lyrics (blurry.lrc.json) into the place-test*.src.js files -> place-test*.js."""
import glob
import json
import os

SP = os.path.dirname(os.path.abspath(__file__))
lrc = json.load(open(os.path.join(SP, "blurry.lrc.json"), encoding="utf-8"))["synced"]
snippet = "var BLURRY_LRC = " + json.dumps(lrc) + ";"
for src in glob.glob(os.path.join(SP, "place-test*.src.js")):
    js = open(src, encoding="utf-8").read().replace("/*BLURRY_LRC*/", snippet)
    dst = src.replace(".src.js", ".js")
    open(dst, "w", encoding="utf-8").write(js)
    print("wrote", dst, len(js), "bytes")
