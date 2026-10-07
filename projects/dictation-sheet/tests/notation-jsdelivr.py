"""Is the jsDelivr npm build of vexflow 4.2.5 the real 4.x (BUILD.VERSION, Dot.buildAndAttach)? Also list cdnjs 4.2.5 files."""
import re
import requests

for url in ['https://cdn.jsdelivr.net/npm/vexflow@4.2.5/build/cjs/vexflow.js', 'https://cdn.jsdelivr.net/npm/vexflow@4.2.5/build/cjs/vexflow-debug.js']:
    try:
        r = requests.get(url, timeout=30)
        t = r.text
        print(url, r.status_code, len(t), 'buildAndAttach' if 'buildAndAttach' in t else 'NO buildAndAttach', 'legacy' if 'LEGACY VERSION' in t else 'not-legacy', re.findall(r'VERSION\s*[:=]\s*"([0-9.]+)"', t)[:3], re.findall(r'openGroup\(["\']stavetie', t)[:1])
    except Exception as e:
        print(url, 'ERROR', e)
try:
    r = requests.get('https://api.cdnjs.com/libraries/vexflow/4.2.5?fields=files', timeout=30)
    print('cdnjs 4.2.5 files:', r.status_code, r.json().get('files'))
except Exception as e:
    print('cdnjs api ERROR', e)
