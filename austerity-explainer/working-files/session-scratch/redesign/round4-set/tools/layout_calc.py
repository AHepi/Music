# What this does: quick screen boxes (as fractions of the 1080 x 1920 film frame) of No. 1's gate group and queue from
# W1 (composed and plate) and W3, each thing as an upright cylinder, and the pixel gaps (+) or overlaps (-) between
# neighbours, to try layouts before a Blender run. Scratch tool for round 4.
import math, sys, json
T = math.tan(math.radians(60.4 / 2)); A = 1080 / 1920
PT = math.tan(math.radians(64.4 / 2))
GROUND = 0.155
def screen(cam, p, r, h, tan=T):
    cx, cy, cz = cam; x, y = p
    d = y - cy
    sx = lambda xx: 0.5 + 0.5 * (xx - cx) / (d * tan * A)
    fy = lambda zz: 0.5 - 0.5 * (zz - cz) / (d * tan)
    return [sx(x - r), fy(GROUND + h), sx(x + r), fy(GROUND)], d
things = json.loads(sys.argv[1])
cams = {'W1': (-4.1, 10.2, 1.841), 'W1 plate': (-4.1, 9.0, 1.841), 'W3': (0.0, -7.95, 5.74)}
for cname, cam in cams.items():
    rows = []
    for name, (x, y, r, h) in things.items():
        box, d = screen(cam, (x, y), r, h, PT if 'plate' in cname else T)
        rows.append((d, name, box))
    rows.sort()
    print('==', cname)
    for d, name, box in rows:
        print(f'  {name:10s} d {d:5.2f}  x {box[0]:.3f}-{box[2]:.3f}  y {box[1]:.3f}-{box[3]:.3f}')
    # pairwise: horizontal gap in px if their vertical ranges overlap
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i][2], rows[j][2]
            if min(a[3], b[3]) - max(a[1], b[1]) <= 0: continue
            gap = max(a[0], b[0]) - min(a[2], b[2])
            px = gap * 1080
            if -40 < px < 30:
                print(f'    {rows[i][1]} / {rows[j][1]}: {"gap" if px > 0 else "overlap"} {abs(px):.0f} px')
