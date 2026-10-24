# Draw a 10 m grid with labels on an ortho top render. args: in out cx cy scale [marks.json]
import sys, json
from PIL import Image, ImageDraw
src, dst, cx, cy, scale = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
im = Image.open(src).convert('RGB'); W, H = im.size
d = ImageDraw.Draw(im)
k = W / scale
def px(x, y): return (W / 2 + (x - cx) * k, H / 2 - (y - cy) * k)
for gx in range(-100, 101, 10):
    X, _ = px(gx, 0)
    if 0 <= X < W:
        d.line([(X, 0), (X, H)], fill=(255, 255, 0) if gx == 0 else (255, 255, 255), width=1)
        d.text((X + 2, 2), str(gx), fill=(255, 255, 0))
for gy in range(-100, 101, 10):
    _, Y = px(0, gy)
    if 0 <= Y < H:
        d.line([(0, Y), (W, Y)], fill=(255, 255, 0) if gy == 0 else (255, 255, 255), width=1)
        d.text((2, Y + 2), str(gy), fill=(255, 255, 0))
if len(sys.argv) > 6:
    for m in json.load(open(sys.argv[6])):
        ex, ey = px(*m['eye']); tx, ty = px(*m['tgt'])
        d.line([(ex, ey), (tx, ty)], fill=(255, 0, 0), width=2)
        d.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=(255, 0, 0))
        d.text((ex + 6, ey - 6), m['name'][:5], fill=(255, 0, 0))
im.save(dst, quality=90)
