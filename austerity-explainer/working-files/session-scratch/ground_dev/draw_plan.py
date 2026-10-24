import json, math
from PIL import Image, ImageDraw
d = json.load(open('plan.json'))
S = 20
X0, Y1 = -20, 14
W, H = 42 * S, 46 * S
def P(x, y): return ((x - X0) * S, (Y1 - y) * S)
im = Image.new('RGB', (W, H), (40, 36, 32)); dr = ImageDraw.Draw(im)
for gx in range(-20, 23, 5):
    dr.line([P(gx, -32), P(gx, 14)], fill=(70, 66, 60)); dr.text(P(gx + .1, 13.8), str(gx), fill=(200, 200, 200))
for gy in range(-30, 15, 5):
    dr.line([P(-20, gy), P(22, gy)], fill=(70, 66, 60)); dr.text(P(-19.8, gy + .1), str(gy), fill=(200, 200, 200))
for b in d['buildings']:
    dr.rectangle([P(b[0], b[3]), P(b[1], b[2])], outline=(220, 120, 80), width=2)
for t in d['puddles']:
    for x, y in t['pts']:
        px, py = P(x, y); dr.rectangle([px - 1, py - 1, px + 1, py + 1], fill=(90, 150, 220))
    if t['pts']:
        cx = sum(p[0] for p in t['pts']) / len(t['pts']); cy = sum(p[1] for p in t['pts']) / len(t['pts'])
        dr.text(P(cx, cy), t['name'][:12], fill=(255, 255, 255))
for r, n in zip(d['ruts'], d['rut_names']):
    dr.line([P(*p) for p in r], fill=(200, 170, 90), width=2); dr.text(P(*r[0]), n, fill=(255, 220, 120))
dr.line([P(*p) for p in d['track']], fill=(255, 255, 255), width=3)
for x, y, r, h in d['heaps']:
    dr.ellipse([P(x - r, y + r), P(x + r, y - r)], outline=(160, 160, 190), width=2); dr.text(P(x, y), 'coal', fill=(190, 190, 230))
for x, y, r, h in d['mounds']:
    dr.ellipse([P(x - r, y + r), P(x + r, y - r)], outline=(120, 100, 70), width=1)
for x, y in d['barrels']: dr.ellipse([P(x - .3, y + .3), P(x + .3, y - .3)], fill=(150, 90, 60))
x, y = d['lamp']; dr.ellipse([P(x - .3, y + .3), P(x + .3, y - .3)], fill=(255, 220, 100)); dr.text(P(x + .4, y), 'lamp', fill=(255, 220, 100))
dr.line([P(*p) for p in d['fence']], fill=(180, 130, 70), width=3); dr.text(P(*d['fence'][0]), 'fence', fill=(200, 150, 90))
k = d['rack']; dr.line([P(k['x'], k['y_from']), P(k['x'], k['y_to'])], fill=(200, 150, 70), width=4); dr.text(P(k['x'] - 2, k['y_to'] + 1), 'rack', fill=(200, 150, 70))
c = d['cart']; dr.ellipse([P(c['x'] - .6, c['y'] + .6), P(c['x'] + .6, c['y'] - .6)], fill=(180, 130, 70)); dr.text(P(c['x'], c['y'] + 1), 'cart', fill=(220, 170, 100))
s = d['sleepers']; dr.rectangle([P(s['x'] - 1.2, s['y'] + .6), P(s['x'] + 1.2, s['y'] - .6)], fill=(150, 110, 70)); dr.text(P(s['x'], s['y'] + 1), 'sleepers', fill=(220, 170, 100))
# camera and its wedge (standard view)
cam = (-9.5, -21.0)
for yaw in (24.5 - 19.7, 24.5 + 19.7, 24.5):
    a = math.radians(yaw); L = 60
    dr.line([P(*cam), P(cam[0] + L * math.sin(a), cam[1] + L * math.cos(a))], fill=(80, 255, 120) if yaw != 24.5 else (60, 160, 90), width=1)
dr.ellipse([P(cam[0] - .4, cam[1] + .4), P(cam[0] + .4, cam[1] - .4)], fill=(80, 255, 120))
im.save('plan.png')
