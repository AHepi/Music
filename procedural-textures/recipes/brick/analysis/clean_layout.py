# What this does (plain words): takes layout_found.json (the raw joint pairs the line detector found) and cleans it: drops joint pairs
# that are too close to the next one (spurious dark lines inside a spalled brick), then writes layout_clean.json (courses and bricks)
# and draws the rectangles over the reference so a person can check them by eye (layout_overlay.png). Analysis only.
import sys; sys.path.insert(0, ".")
import json, cv2, numpy as np
W = 1254
lay = json.load(open('layout_found.json'))
th_v = np.load('th_v.npy')
rows = []
for r in lay['rows']:
    top, bottom = r['top'], r['bottom']
    ys = np.arange(top + 9, bottom - 8) % W
    prof = th_v[ys].mean(0)
    joints = [list(j) for j in r['joints']]
    # strength of each joint = profile value at both lines
    def strength(j):
        return float(prof[j[0] % W] + prof[j[1] % W])
    changed = True
    while changed and len(joints) > 2:
        changed = False
        for i in range(len(joints)):
            a, b = joints[i], joints[(i + 1) % len(joints)]
            gap = (b[0] - a[1]) % W
            if gap < 180:
                drop = i if strength(a) < strength(b) else (i + 1) % len(joints)
                joints.pop(drop)
                changed = True
                break
    joints.sort()
    bricks = []
    for i, j in enumerate(joints):
        nxt = joints[(i + 1) % len(joints)]
        left = j[1]
        right = nxt[0] if nxt[0] > j[1] else nxt[0] + W
        bricks.append([int(left), int(right)])
    rows.append({'top': top, 'bottom': bottom, 'joints': joints, 'bricks': bricks})
out = {'rows': rows}
json.dump(out, open('layout_clean.json', 'w'))
c = cv2.imread('../../../reference/brick/colour.png')
big = np.tile(c, (3, 3, 1))     # wrap copies so wrapped bricks draw
ov = big.copy()
for r in rows:
    for (l, rt) in r['bricks']:
        for dy in (-W, 0, W):
            for dx in (-W, 0, W):
                cv2.rectangle(ov, (l + dx + W, r['top'] + dy + W), (rt + dx + W, r['bottom'] + dy + W), (0, 255, 255), 1)
cv2.imwrite('layout_overlay.png', ov[W:2 * W, W:2 * W])
for r in rows:
    print(r['top'], r['bottom'], len(r['bricks']), [b[1] - b[0] for b in r['bricks']])
