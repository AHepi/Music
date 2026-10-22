# Reads a multilayer EXR written by render_job.py (light groups) and reports: do the groups add up to Combined, share per group, and where the rim group is non-zero.
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import numpy as np
import OpenImageIO as oiio
exr = sys.argv[sys.argv.index('--') + 1]
out = sys.argv[sys.argv.index('--') + 2]
inp = oiio.ImageInput.open(exr); parts = []; i = 0
while inp.seek_subimage(i, 0):
    parts.append(inp.spec().getattribute('name') or ''); i += 1
inp.close()
print('PARTS', parts)
L = {}
for k, n in enumerate(parts):
    tail = n.split('.', 1)[-1]
    if tail == 'Combined' or tail.startswith('Combined_'):
        inp = oiio.ImageInput.open(exr); inp.seek_subimage(k, 0); sp = inp.spec()
        L[tail] = np.array(inp.read_image(k, 0, 0, 3, 'float'), dtype=np.float32).reshape(sp.height, sp.width, 3); inp.close()
C = L.pop('Combined'); groups = {g[9:]: v for g, v in L.items()}
S = sum(groups.values())
lum = lambda x: 0.2126*x[..., 0] + 0.7152*x[..., 1] + 0.0722*x[..., 2]
tot = float(lum(C).mean())
rep = dict(rel_error=float(np.abs(S - C).mean() / C.mean()), share={g: round(float(lum(v).mean())/tot, 4) for g, v in groups.items()}, size=list(C.shape[:2]))
r = lum(groups['rim']); thr = 0.002
mask = r > thr
H, W = r.shape; ys, xs = np.nonzero(mask)
rep['rim_nonzero_fraction'] = round(float(mask.mean()), 4)
if len(xs): rep['rim_bbox_xy_frac'] = [round(xs.min()/W, 3), round(ys.min()/H, 3), round(xs.max()/W, 3), round(ys.max()/H, 3)]
# save a sheet: each group tone-mapped simply (x/(1+x)) with gamma, for looking at
def tm(x): x = np.clip(x, 0, None); x = x/(1+x); return (np.clip(x, 0, 1)**(1/2.2)*255).astype(np.uint8)
import bpy
tiles = [('combined', C)] + list(groups.items())
for nme, arr in tiles:
    pass
np.savez_compressed(out + '.npz', **{n: tm(a) for n, a in tiles})
json.dump(rep, open(out + '.json', 'w'), indent=1)
print('GROUP_REPORT', json.dumps(rep))
