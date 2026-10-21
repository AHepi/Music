# What this does (plain words): plain Python (no Blender). Labels every dot of the 1200 x 800 courtyard pictures by family, using the flat family map (same camera, same size), and reports the
# average brightness of each family and the share of its dots that are very dark (under 0.13 and under 0.17), the zone the film's stage crushes. Brightness is the finished 8-bit picture's
# brightness from 0 (black) to 1 (white), as in the street study.
# Run: python3 c10_brightness_by_family.py MAP.png PICTURE.png [PICTURE2.png ...] > OUT.json
import json, sys
import numpy as np
from PIL import Image
COL = {'ground': (0.30, 0.55, 0.18), 'add-on moss and pebbles': (0.62, 0.88, 0.32), 'raked gravel': (0.88, 0.78, 0.48), 'water': (0.15, 0.40, 0.85), 'wood': (0.80, 0.40, 0.10),
       'plaster': (0.97, 0.97, 0.88), 'wall cap tiles': (0.10, 0.10, 0.55), 'roof tiles': (0.45, 0.25, 0.70), 'add-on stones': (0.62, 0.62, 0.66), 'plain stone': (0.32, 0.34, 0.45),
       'bamboo': (0.85, 0.92, 0.15), 'bark': (0.45, 0.22, 0.08), 'leaves, needles, lilies': (0.05, 0.28, 0.07), 'hills and glow (backdrop)': (0.22, 0.22, 0.26), 'sky': (0, 0, 0)}
def srgb(c):  # linear -> 8-bit sRGB
    c = np.array(c, float); return np.round(255 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055))
m = np.array(Image.open(sys.argv[1]).convert('RGB')).astype(float)
labels = np.full(m.shape[:2], -1); names = list(COL)
for i, n in enumerate(names):
    ok = (np.abs(m - srgb(COL[n])) <= 3).all(axis=2); labels[ok] = i
print('labelled share', round(float((labels >= 0).mean()), 3), file=sys.stderr)
out = {}
for path in sys.argv[2:]:
    p = np.array(Image.open(path).convert('RGB')).astype(float) / 255
    L = 0.2126 * p[..., 0] + 0.7152 * p[..., 1] + 0.0722 * p[..., 2]
    r = {}
    for i, n in enumerate(names):
        sel = labels == i
        if sel.sum() < 200: continue
        v = L[sel]; r[n] = {'dots': int(sel.sum()), 'mean': round(float(v.mean()), 3), 'p10': round(float(np.percentile(v, 10)), 3), 'p90': round(float(np.percentile(v, 90)), 3),
                            'under_0.13': round(float((v < 0.13).mean()), 3), 'under_0.17': round(float((v < 0.17).mean()), 3)}
    out[path.split('/')[-1]] = r
json.dump(out, sys.stdout, indent=1)
