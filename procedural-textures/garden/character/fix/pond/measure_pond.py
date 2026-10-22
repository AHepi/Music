# POND BUILDER: measures the pond bands in a hero or veranda picture (JPG/PNG, any size) with the sample points of work/water_samples.json
# (visible water points of the starting scene, with their depth). Prints luminance mean/std and mean colour per band, and the hue/saturation.
# usage: python3 -I measure_pond.py hero.png photo|veranda
import sys, json, colorsys
import numpy as np
from PIL import Image
D = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond/"
def bands(path, cam):
    s = json.load(open(D + "work/water_samples.json"))[cam]
    im = Image.open(path).convert('RGB')
    sx, sy = im.size[0] / 2400.0, im.size[1] / 1600.0
    a = np.asarray(im).astype(np.float32) / 255
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    pts = np.array(s)
    out = {}
    for lo, hi, name in ((0, 0.04, 'rim'), (0.04, 0.10, 'edge'), (0.10, 0.20, 'mid-edge'), (0.20, 0.30, 'slope'), (0.30, 0.5, 'middle')):
        m = (pts[:, 2] >= lo) & (pts[:, 2] < hi)
        if not m.any():
            continue
        L, C = [], []
        for x, y, d, px, py in pts[m]:
            px, py = int(px * sx), int(py * sy)
            w = max(2, int(4 * sx))
            L.append(lum[py - w:py + w + 1, px - w:px + w + 1].mean())
            C.append(a[py - w:py + w + 1, px - w:px + w + 1].reshape(-1, 3).mean(0))
        L = np.array(L); C = np.array(C)
        rgb = C.mean(0)
        h, s_, v = colorsys.rgb_to_hsv(*rgb)
        out[name] = dict(n=int(m.sum()), lum=float(L.mean()), std=float(L.std()), rgb=[round(float(v_), 3) for v_ in rgb], hue=round(h * 360, 0), sat=round(s_, 2))
    return out
if __name__ == '__main__':
    r = bands(sys.argv[1], sys.argv[2])
    for k, v in r.items():
        print("%-9s n=%3d lum %.3f std %.3f rgb %s hue %d sat %.2f" % (k, v['n'], v['lum'], v['std'], v['rgb'], v['hue'], v['sat']))
