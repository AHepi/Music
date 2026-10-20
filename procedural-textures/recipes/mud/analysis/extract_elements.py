# What this does (plain words): runs the element finder (element_tools.py) on a mud colour picture and writes analysis/elements_<name>.json: palette, puddles
# (outline + flat water tones) and stones (outline + flat faces). It also draws a quick numpy preview of just those things over a flat brown ground so I can look
# at what was found. Analysis only (it reads the reference). Use: python3 -I extract_elements.py [mud|mud_golden]
import json, os, sys, time
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import trace_tools as tt
import element_tools as et
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
name = sys.argv[1] if len(sys.argv) > 1 else 'mud'
K = 16
THRESHOLD = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0       # Lab b* below this = grey / blue / black (stones and water); calibrated so about a third of the picture is non-earth
img = cv2.imread(f'{PROC}/reference/{name}/colour.png')
h, w = img.shape[:2]
t0 = time.time()
centres = tt.make_palette(img, K, seed=1)
labels = tt.assign_labels(img, centres)
palette_bgr = tt.palette_to_bgr(centres)
kinds = et.classify_palette(palette_bgr)
for i, (c, k) in enumerate(zip(palette_bgr, kinds)):
    print(i, 'rgb', c[::-1].tolist(), k, '%.1f%%' % (100 * (labels == i).mean()))
puddles = et.find_puddles(img, labels, kinds, threshold=THRESHOLD)
print('puddles found', len(puddles), 'areas', sorted(int(p['area']) for p in puddles)[::-1])
stones_raw = et.find_stones(img, labels, threshold=THRESHOLD)
print('stones found', len(stones_raw), 'in', round(time.time() - t0, 1), 's')
pad = et.PAD_WRAP
stones = []
for s in stones_raw:
    d = et.stone_description(s)
    if d is None:
        continue
    d['outline'] = (d['outline'] - pad)
    d['faces'] = [(k, p - pad, a) for k, p, a in d['faces']]
    stones.append(d)
print('stone descriptions', len(stones))
np.save(f'/tmp/mudscratch/labels_{name}.npy', labels)
json.dump({'palette_bgr': palette_bgr.tolist(), 'kinds': kinds}, open(f'/tmp/mudscratch/palette_{name}.json', 'w'))

# --- numpy preview of the found things over flat earth (scale 3 anti-aliasing)
S = 3
earth_ids = [i for i, k in enumerate(kinds) if k == 'earth']
earth_mean = tuple(int(v) for v in palette_bgr[earth_ids[int(np.argmax([ (labels == i).sum() for i in earth_ids ]))]])
canvas = np.zeros((h * S, w * S, 3), np.uint8); canvas[:] = earth_mean
def poly(canvas, pts, colour, grow=0.0):
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            p = ((np.asarray(pts, np.float64) + 0.5 + [ox, oy]) * S).round().astype(np.int32)
            if p[:, 0].max() < 0 or p[:, 0].min() > w * S or p[:, 1].max() < 0 or p[:, 1].min() > h * S:
                continue
            cv2.fillPoly(canvas, [p], colour, lineType=cv2.LINE_8)
water_ids = [i for i, k in enumerate(kinds) if k == 'water']
for p in puddles:
    base = max(water_ids, key=lambda i: sum(t['a'] for t in p['tones'] if t['c'] == i)) if p['tones'] else water_ids[0]
    poly(canvas, p['p'], tuple(int(v) for v in palette_bgr[base]))
    for t in sorted(p['tones'], key=lambda t: -t['a']):
        poly(canvas, t['p'], tuple(int(v) for v in palette_bgr[t['c']]))
for s in sorted(stones, key=lambda s: -s['area']):
    poly(canvas, s['outline'], tuple(int(v) for v in palette_bgr[s['base']]))
    for k, p, a in s['faces']:
        poly(canvas, p, tuple(int(v) for v in palette_bgr[k]))
preview = cv2.resize(canvas, (w, h), interpolation=cv2.INTER_AREA)
cv2.imwrite(f'/tmp/mudscratch/elements_preview_{name}.png', preview)
import pickle
pickle.dump({'puddles': puddles, 'stones': stones, 'palette_bgr': palette_bgr, 'kinds': kinds}, open(f'/tmp/mudscratch/elements_{name}.pkl', 'wb'))
def enc(points):
    pts = np.asarray(points, np.int64); return np.diff(pts, axis=0, prepend=np.zeros((1, 2), np.int64)).reshape(-1).tolist()
size = len(json.dumps({'p': [enc(p['p']) for p in puddles], 's': [[s['base'], enc(s['outline']), [[k, enc(pp)] for k, pp, a in s['faces']]] for s in stones]}, separators=(',', ':')))
print('approximate description size of puddles+stones (bytes):', size)
