"""Which VexFlow is inlined in a built page? Prints version strings and API markers found in the file."""
import re
import sys

for path in sys.argv[1:]:
    t = open(path, encoding='utf-8', errors='replace').read()
    print('==', path, len(t), 'chars')
    for pat in [r'This page uses version [0-9.]+', r'VERSION:"[0-9.]+"', r'VERSION="[0-9.]+"', r'version:"[0-9.]+"',
                r'vexflow[^"\'<>]{0,60}', r'BUILD=\{[^}]{0,160}\}', r'buildAndAttach', r'addDotToAll', r'openGroup\("stavetie"',
                r"openGroup\('stavetie'", r'"stavetie"', r'getDefaultBeamGroups', r'Bravura', r'cdnjs\.cloudflare\.com/ajax/libs/vexflow/[0-9.]+']:
        ms = re.findall(pat, t)
        print('  %-50s -> %d %s' % (pat, len(ms), [m[:100] for m in ms[:3]]))
