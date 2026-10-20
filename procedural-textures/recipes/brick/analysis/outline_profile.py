import sys; sys.path.insert(0, ".")
# What this does (plain words): measures how the dark outline looks around a brick: for each of the four sides it takes the median grey value
# at each distance from the brick edge I found (-8 inside ... +8 outside), over all bricks. Shows the thickness and darkness of the outline
# and whether the edge positions I found are a dot or two off. Analysis only.
import json, cv2, numpy as np
W = 1254
c = cv2.imread('../../../reference/brick/colour.png')[..., ::-1].astype(float)
g = c @ np.array([.299, .587, .114])
big = np.tile(g, (3, 3))
bigc = np.tile(c, (3, 3, 1))
desc = json.load(open('../generator/descriptions/stage1_bricks_only.json'))
rows = desc['layers'][0]['rows']
prof = {s: [[] for _ in range(21)] for s in ('top', 'bottom', 'left', 'right')}
profc = {s: [[] for _ in range(21)] for s in ('top', 'bottom', 'left', 'right')}
for r in rows:
    y0, y1 = r['y0'], r['y1']
    if y1 - y0 < 60: continue
    for x0, x1, _ in r['bricks']:
        xs = np.arange(x0 + 20, x1 - 20)
        ys = np.arange(y0 + 15, y1 - 15)
        for k, d in enumerate(range(-10, 11)):          # d>0 outside the brick
            prof['top'][k].append(np.median(big[W + y0 - d, W + xs]))
            prof['bottom'][k].append(np.median(big[W + y1 + d, W + xs]))
            prof['left'][k].append(np.median(big[W + ys, W + x0 - d]))
            prof['right'][k].append(np.median(big[W + ys, W + x1 + d]))
            profc['top'][k].append(np.median(bigc[W + y0 - d, W + xs], axis=0))
            profc['bottom'][k].append(np.median(bigc[W + y1 + d, W + xs], axis=0))
for s in prof:
    print(s, [int(np.median(v)) for v in prof[s]])
print('top colour at d=-1..2', [np.median(profc['top'][k], axis=0).astype(int).tolist() for k in (9, 10, 11, 12)])
print('bottom colour at d=-1..3', [np.median(profc['bottom'][k], axis=0).astype(int).tolist() for k in (9, 10, 11, 12, 13)])
