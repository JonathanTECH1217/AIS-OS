"""Which files under cdnjs vexflow/4.2.5 are the real 4.x build? Fetch the head/tail of the candidates."""
import re
import requests

base = 'https://cdnjs.cloudflare.com/ajax/libs/vexflow/4.2.5/'
for name in ['vexflow-min.js', 'vexflow.js', 'vexflow-debug.js', 'vexflow-bravura.js', 'vexflow-core.js']:
    try:
        r = requests.get(base + name, timeout=20)
    except Exception as e:
        print(name, 'ERROR', e)
        continue
    t = r.text
    ver = re.findall(r'VERSION:"([0-9.]+)"|VERSION\s*=\s*"([0-9.]+)"|This page uses version ([0-9.]+)|VexFlow ([0-9]\.[0-9.]+)', t)
    print(name, r.status_code, len(t), 'legacy-warning' if 'LEGACY VERSION 3.0.9' in t else '', 'buildAndAttach' if 'buildAndAttach' in t else 'no-buildAndAttach', ver[:3], t[:80].replace('\n', ' '))
