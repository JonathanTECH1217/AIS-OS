"""Write tests/vectors.json: keyframe cases with the value the exporter computes (studio_render.value_at).
The page's js/model/keyframes.js must give the same numbers (t-effects.js) and so must the exporter
(render-unit.py), so preview and export can't drift apart.

  python projects/studio/tests/make_vectors.py
"""
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import studio_render as r  # noqa: E402

EASES = ["linear", "in", "out", "both", "hold"]
cases = []
for e0, e1 in itertools.product(EASES, EASES):
    keys = [{"t": 10, "v": 100, "e": e0}, {"t": 40, "v": 160, "e": e1}, {"t": 70, "v": 80, "e": "linear"}]
    clip = {"fx": {"scale": {"v": 100, "k": keys}}}
    for t in (0, 10, 13, 17.5, 25, 31, 39.9, 40, 55, 70, 90):
        cases.append({"keys": keys, "t": t, "want": round(r.value_at(clip, "scale", t), 9)})
(HERE / "vectors.json").write_text(json.dumps(cases, indent=0))
print(f"{len(cases)} cases")
