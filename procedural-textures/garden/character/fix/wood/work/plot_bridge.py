# local top-view plot of the bridge geometry (numpy + PIL only). usage: python3 -I plot_bridge.py OUT.png [cx cy halfwidth]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image, ImageDraw
import wood_bridge as wb

def render(out, centre=(-3.3, 0.5), half=3.6, px=1600):
    L = wb.layout(7, bed_fn=lambda x, y: -0.44 if y < 1.9 else 0.08, rocks=[])
    meshes, parts = wb.build_meshes(L)
    S = px / (2 * half)
    def P(x, y):
        return ((x - centre[0] + half) * S, (centre[1] + half * 0.75 - y) * S)
    img = Image.new('RGB', (px, int(px * 0.75)), (24, 40, 50))
    d = ImageDraw.Draw(img)
    cols = {'footings': (70, 90, 110), 'footing_n1': (70, 90, 110), 'footing_n2': (70, 90, 110), 'sill0': (90, 90, 90), 'sill3': (90, 90, 90),
            'bearers': (190, 70, 60), 'stringers': (70, 130, 200), 'posts': (230, 170, 40), 'cramps': (20, 20, 20), 'pegs': (255, 255, 255)}
    for k in ('footings', 'footing_n1', 'footing_n2', 'sill0', 'sill3', 'stringers', 'bearers'):
        md = meshes[k]
        V = np.array(md.V)
        for f in md.F:
            pts = [P(*V[i][:2]) for i in f]
            zs = [V[i][2] for i in f]
            d.polygon(pts, fill=cols[k], outline=None)
    keys = [k for k in meshes if k.startswith('planks')]
    for k in keys:
        md = meshes[k]
        V = np.array(md.V)
        for f, m in zip(md.F, md.mat):
            if m != 0:
                continue
            pts = [P(*V[i][:2]) for i in f]
            zm = np.mean([V[i][2] for i in f])
            c = (210, 190, 150) if k.startswith('planks_n') else (190, 165, 125)
            d.polygon(pts, fill=c)
    for k in ('posts', 'cramps'):
        md = meshes[k]
        V = np.array(md.V)
        for f in md.F:
            zs = [V[i][2] for i in f]
            if k == 'posts' and not all(abs(z - max(V[:, 2])) < 1e-9 for z in zs):
                pass
            pts = [P(*V[i][:2]) for i in f]
            d.polygon(pts, fill=cols[k])
    img.save(out)
    return L

if __name__ == '__main__':
    out = sys.argv[1]
    if len(sys.argv) > 4:
        render(out, (float(sys.argv[2]), float(sys.argv[3])), float(sys.argv[4]))
    else:
        render(out)
