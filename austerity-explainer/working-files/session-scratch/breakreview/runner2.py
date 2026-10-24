# Second pass: (1) if composed-end were painted instead of the start plate, how much of the start frame
# has no painting; (2) the fire light's shadow disk on the road for several light heights; (3) lantern vs
# notice gap and board/handcart edges at start and end; (4) what the start plate sees behind the board
# and the lamp post with the near props removed. Writes only into this folder.
import bpy, os, sys, math, json
from mathutils import Vector
BR = os.path.dirname(os.path.abspath(__file__))
head = open(os.path.join(BR, 'runner.py')).read().split("if 'render' in mode:")[0]
g = {'__file__': os.path.join(BR, 'runner.py'), '__name__': '__main__'}
exec(compile(head, 'runner_head', 'exec'), g)
scene, END, START, F, R, U, FILM, PLATE = (g[k] for k in ('scene', 'END', 'START', 'F', 'R', 'U', 'FILM', 'PLATE'))
group_of, project = g['group_of'], g['project']
out = {}
dg = bpy.context.evaluated_depsgraph_get()

def cast(C, d, dist=1e4):
    hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, C, d, distance=dist)
    return hit, loc, nrm, obj

# (1) start film frame vs an END-frame painting (60.4 deg, from END)
W, H = 135, 240
rows = []
miss = 0; miss_box = [1, 1, 0, 0]; bottom_rows = {}
for j in range(H):
    for i in range(W):
        d = (F + R * ((2 * (i + 0.5) / W - 1) * FILM[0]) + U * ((1 - 2 * (j + 0.5) / H) * FILM[1])).normalized()
        hit, P, n, obj = cast(START, d)
        if not hit or group_of(obj) == 'sky':
            continue
        x, y, zc = project(P, END, FILM)
        outside = zc <= 0 or not (0 <= x <= 1 and 0 <= y <= 1)
        if outside:
            miss += 1
            bottom_rows[j] = bottom_rows.get(j, 0) + 1
            miss_box = [min(miss_box[0], i / W), min(miss_box[1], j / H), max(miss_box[2], (i + 1) / W), max(miss_box[3], (j + 1) / H)]
# rows fully missing from the bottom
full = [j for j, c in bottom_rows.items() if c >= W * 0.95]
out['start frame without painting if composed-end were the plate'] = {
    'share_%': round(miss / (W * H) * 100, 1), 'box': [round(v, 3) for v in miss_box],
    'bottom rows fully unpainted from': round(min(full) / H, 3) if full else None,
    'left strip width': None}
# side strips: per row count from left and right
left_w, right_w = [], []
for j in range(int(H * 0.1), int(H * 0.7), 10):
    lw = rw = 0
    for i in range(W):
        d = (F + R * ((2 * (i + 0.5) / W - 1) * FILM[0]) + U * ((1 - 2 * (j + 0.5) / H) * FILM[1])).normalized()
        hit, P, n, obj = cast(START, d)
        if not hit or group_of(obj) == 'sky':
            continue
        x, y, zc = project(P, END, FILM)
        if x < 0: lw = max(lw, (i + 1) / W)
        if x > 1: rw = max(rw, 1 - i / W)
    left_w.append((round(j / H, 2), round(lw, 3), round(rw, 3)))
out['side strips (row, left width, right width)'] = left_w

# (2) the fire light's rim shadow on the road/pavement for light heights
light = bpy.data.objects['brazier_light']
L0 = light.matrix_world.translation.copy()
drum_c = Vector((2.81, 22.0, 0))
res = {}
for above_rim in (0.205, 0.35, 0.45, 0.55):
    Lp = Vector((L0.x, L0.y, 2.525 + above_rim))
    radii = {}
    for ang in (90, 135, 180, 225, 270):   # 180 = straight left (road), 270 = toward the camera
        a = math.radians(ang)
        last_dark = None
        for k in range(1, 60):
            r = 0.32 + k * 0.05
            Pxy = drum_c + Vector((math.cos(a) * r, math.sin(a) * r, 0))
            hit, P, n, obj = cast(Vector((Pxy.x, Pxy.y, 20)), Vector((0, 0, -1)))
            if not hit:
                continue
            dvec = Lp - P
            h2, l2, n2, o2 = cast(P + Vector((0, 0, 0.003)), dvec.normalized(), dvec.length - 0.02)
            if h2 and group_of(o2) == 'drum':
                last_dark = r
        radii[ang] = last_dark
    res[f'light {above_rim:.3f} m above rim (z {2.525 + above_rim:.2f})'] = radii
out['fire light: furthest point shaded by the drum (m from drum centre), by direction'] = res

# (3) edges at start and end, from id maps of the near props (film lens)
def bbox(C, groups, W=540, H=960, region=None):
    box = {}
    x0, y0, x1, y1 = region or (0, 0, 1, 1)
    for j in range(int(y0 * H), int(y1 * H)):
        for i in range(int(x0 * W), int(x1 * W)):
            d = (F + R * ((2 * (i + 0.5) / W - 1) * FILM[0]) + U * ((1 - 2 * (j + 0.5) / H) * FILM[1])).normalized()
            hit, P, n, obj = cast(C, d)
            gname = group_of(obj) if hit else 'sky'
            if gname in groups:
                b = box.get(gname, [1, 1, 0, 0])
                box[gname] = [min(b[0], i / W), min(b[1], j / H), max(b[2], (i + 1) / W), max(b[3], (j + 1) / H)]
    return {k: [round(v, 4) for v in b] for k, b in box.items()}
for which, C in (('start', START), ('end', END)):
    out[f'edges {which}'] = bbox(C, {'notice', 'lantern', 'board', 'board posts', 'handcart', 'lamp post', 'pail', 'chair', 'drum'}, region=(0, 0.05, 1, 1))

# (4) what the start plate sees behind the board and the lamp post with near props removed
hide = {'drum', 'chair', 'lantern', 'pail', 'board', 'notice', 'board posts', 'lamp post'}
moved = []
for o in bpy.data.objects:
    if o.parent is None and group_of(o) in hide:
        moved.append((o, o.location.copy())); o.location.z -= 1000
    elif o.parent is None and o.type == 'EMPTY':
        kids = [c for c in o.children_recursive if c.type == 'MESH']
        if kids and group_of(kids[0]) in hide:
            moved.append((o, o.location.copy())); o.location.z -= 1000
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
behind = {}
W2, H2 = 270, 480
for j in range(int(0.05 * H2), H2):
    for i in range(int(0.6 * W2), W2):
        d = (F + R * ((2 * (i + 0.5) / W2 - 1) * PLATE[0]) + U * ((1 - 2 * (j + 0.5) / H2) * PLATE[1])).normalized()
        hit, P, n, obj = scene.ray_cast(dg, START, d, distance=1e4)[:4] if False else (lambda r: (r[0], r[1], r[2], r[4]))(scene.ray_cast(dg, START, d, distance=1e4))
        gname = group_of(obj) if hit else 'sky'
        behind[gname] = behind.get(gname, 0) + 1
for o, loc in moved:
    o.location = loc
bpy.context.view_layer.update()
out['plate right part (x>0.6) with near props and lamp post removed: what is there (% of that region)'] = {k: round(v / (0.4 * W2 * 0.95 * H2) * 100, 1) for k, v in sorted(behind.items(), key=lambda kv: -kv[1]) if v / (0.4 * W2 * 0.95 * H2) > 0.005}
json.dump(out, open(os.path.join(BR, 'analysis2.json'), 'w'), indent=1)
print('ANALYSIS2 DONE')
