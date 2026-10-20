# What this does (plain python): "edge density" = share of pixels where the lightness changes by more than 8 units between the pixels on either side
# (central difference over 2 px, horizontally or vertically). A rough measure of how busy and ragged a painted picture is. Prints it for the references and for
# the picture files given on the command line (label=path).
import os, sys, json, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.abspath(os.path.join(HERE, '..')); PROC = os.path.abspath(os.path.join(BASE, '..', '..'))
def density(path, threshold=8.0):
    rgb = cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)[..., 0]
    gx = np.abs(np.roll(L, -1, axis=1) - np.roll(L, 1, axis=1)); gy = np.abs(np.roll(L, -1, axis=0) - np.roll(L, 1, axis=0))
    return float(((gx > threshold) | (gy > threshold)).mean())
out = {}
for n in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']:
    out['reference ' + n] = density(os.path.join(PROC, 'reference', n, 'colour.png'))
for item in sys.argv[1:]:
    label, path = item.split('=', 1)
    out[label] = density(path)
for k, v in out.items(): print(f'{k:40s} {v*100:5.1f}%')
json.dump(out, open(os.path.join(BASE, 'data', 'a05_edge_density.json'), 'w'), indent=1)
