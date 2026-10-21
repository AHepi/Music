# per-layer solo plates on the notice camera, then walls/trims mean ratio per distance band
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.dont_write_bytecode = True
from jobs import J, PL
tag = sys.argv[1]; layers = sys.argv[2].split(',')
cam = sys.argv[3] if len(sys.argv) > 3 else 'notice'
jobs = [J(f't_{l}_{cam}', f'solo:{l}', cam=cam, light='A', size=PL, keep_png=True, plate_height=2730) for l in layers]
jobs.append(J(f't_all_{cam}', 'kit:' + ','.join(layers), cam=cam, light='A', size=PL, keep_png=True, plate_height=2730))
p = os.path.join(HERE, 'jobs_bs.json'); json.dump(jobs, open(p, 'w'))
if '--nodraw' not in sys.argv:
    sub = subprocess.run(['python3', os.path.join(HERE, 'drive.py'), tag, p, 'street'], capture_output=True, text=True)
    print(sub.stdout[-200:].strip().splitlines()[-1] if sub.stdout.strip() else sub.stderr[-300:])
import mround, numpy as np, measure_common as mc
d = os.path.join(HERE, '..', 'out', tag)
import shutil
for f in os.listdir(os.path.join(HERE, '..', 'out', 'maps')): shutil.copy(os.path.join(HERE, '..', 'out', 'maps', f), d)
for l in layers + ['all']:
    res, Lk, Lb, cmap, depth = mround.mush(d, f't_{l}_{cam}', cam=cam, base=mround.BASE_PLATES + f'plate_{cam}_A_wet.png')
    out = []
    for cls in ('walls', 'trims', 'roofs'):
        cm = mc.class_mask(cmap, mc.classes(mround.settings)[cls])
        row = []
        for lo, hi in ((5, 10), (10, 20), (20, 40)):
            m = cm & (depth >= lo) & (depth < hi)
            row.append(round(float(Lk[m].mean() / Lb[m].mean()), 3) if m.sum() > 200 else None)
        out.append(f'{cls} {row}')
    print(f'{l:10s}', '  '.join(out))
