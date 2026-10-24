# Rebuilds the composed-end scene (brief's positions) from a snapshot of assemble_notice_corner.py and
# measures what the 1.5 m slide uncovers. Writes only into this folder.
import bpy, sys, os, math, json
from mathutils import Vector

BR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BR, 'assemble_snapshot.py')
mode = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
src = open(SRC).read()
repl = {
    'BOARD = Vector((3.45, 22.75))': 'BOARD = Vector((3.40, 22.25))',
    'BOARD_SCALE = 1.11': 'BOARD_SCALE = 1.0',
    'BOARD_LIFT = 0.46': 'BOARD_LIFT = 0.60',
    'DRUM = Vector((2.76, 22.0))': 'DRUM = Vector((2.81, 22.0))',
    'CHAIR = Vector((3.27, 21.75))': 'CHAIR = Vector((3.34, 21.75))',
    'CHAIR_TURN_DEGREES = -40.0': 'CHAIR_TURN_DEGREES = 140.0',
    'PAIL = Vector((3.28, 21.15))': 'PAIL = Vector((3.36, 21.15))',
    'PAIL_SCALE = 0.85': 'PAIL_SCALE = 1.0',
    'LANTERN_SCALE = 1.25': 'LANTERN_SCALE = 1.4',
    'LAMP_POST = Vector((3.50, 23.25))': 'LAMP_POST = Vector((3.25, 23.0))',
    'seat = CHAIR + Vector((-0.05, -0.07))': 'seat = CHAIR + Vector((-0.10, -0.12))',
    "place_prop('handcart.glb', -1.2, 30.5": "place_prop('handcart.glb', -2.0, 30.5",
    '((-1.2, 30.45), -75': '((-2.0, 30.45), -75',
    '    tint(chair.children_recursive, (0.62, 0.56, 0.46))': '    pass',
    'brazier_fire(DRUM.x, DRUM.y, light_above_coals=FIRE_LIGHT_ABOVE_COALS, coal_top=COAL_TOP, dark_every=1.33, glow=4.0)':
        'brazier_fire(DRUM.x, DRUM.y, light_above_coals=0.25)',
}
for a, b in repl.items():
    if a not in src:
        print('PATCH MISSING:', a)
    src = src.replace(a, b)
ns = {'__file__': SRC, '__name__': '__main__'}
exec(compile(src, SRC, 'exec'), ns)

scene = bpy.context.scene
END = ns['camera_spot']('end')
START = ns['camera_spot']('start')
YAW = math.radians(ns['CAMERA_YAW_DEGREES'])
F = Vector((-math.sin(YAW), math.cos(YAW), 0)); R = Vector((math.cos(YAW), math.sin(YAW), 0)); U = Vector((0, 0, 1))
ASPECT = 1080 / 1920
def tans(fov):
    tv = math.tan(math.radians(fov) / 2)
    return tv * ASPECT, tv
FILM = tans(60.4); PLATE = tans(64.4)
print('END', tuple(round(v, 3) for v in END), 'START', tuple(round(v, 3) for v in START))

HOLDERS = {'notice-on-board': 'board', 'brazier-drum': 'drum', 'kitchen-chair': 'chair', 'hurricane-lantern': 'lantern',
           'wooden-pail': 'pail', 'gas-lamp-post': 'lamp post', 'handcart': 'handcart', 'coal-sacks': 'sacks',
           'wooden-barrel': 'barrel', 'dustbins': 'dustbins'}
def group_of(o):
    if o is None:
        return 'sky'
    o = bpy.data.objects.get(o.name, o)
    n = o.name
    if n.startswith('brazier_coal'):
        return 'drum'
    if n.startswith('lantern_flame'):
        return 'lantern'
    if n.startswith('Cube') and any(c.name == 'signs' for c in o.users_collection):
        return 'board posts'
    p = o
    while p is not None:
        for k, g in HOLDERS.items():
            if p.name == k or p.name.startswith(k + '.'):
                if g == 'board' and o.type == 'MESH' and 'notice' in o.name.lower() and 'board' not in o.name.lower():
                    return 'notice'
                return g
        p = p.parent
    if n.startswith('sky'):
        return 'sky'
    base = ''.join(ch if not ch.isdigit() else '#' for ch in n).split('.')[0]
    return 'street:' + base

# report props' boxes, to compare with facts-end
for k in HOLDERS:
    for h in [o for o in bpy.data.objects if o.name == k or o.name.startswith(k + '.')]:
        pts = []
        for o in h.children_recursive:
            if o.type == 'MESH':
                pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
        if pts:
            lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
            print('BOX', h.name, 'centre', [round((lo[i] + hi[i]) / 2, 3) for i in range(3)], 'size', [round(hi[i] - lo[i], 3) for i in range(3)])
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        print('LIGHT', o.name, o.data.type, round(o.data.energy, 1), tuple(round(v, 2) for v in o.matrix_world.translation), 'shadow', o.data.use_shadow, 'soft', round(getattr(o.data, 'shadow_soft_size', 0), 3))

def project(P, C, t):
    Q = P - C
    zc = Q.dot(F)
    return 0.5 + 0.5 * Q.dot(R) / (zc * t[0]), 0.5 - 0.5 * Q.dot(U) / (zc * t[1]), zc

def ray(C, d, dist=1e4):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, C, d, distance=dist)
    return (hit, loc, nrm, obj)

if 'render' in mode:
    for which, fov, name in (('start', 60.4, 'start-film.png'), ('end', 60.4, 'end-film.png'), ('start', 64.4, 'start-plate.png')):
        ns['set_camera'](which, fov)
        ns['render'](os.path.join(BR, name), 540, int(540 * (1920 / 1080)) if fov == 60.4 else 960, 16)
    sys.exit(0)

# --------------------------------------------------------------- id maps from start and end (film lens)
W, H = int(mode[mode.index('--w') + 1]) if '--w' in mode else 270, 0
H = int(W * 1920 / 1080)
def idmap(C, t):
    out = []
    dg = bpy.context.evaluated_depsgraph_get()
    for j in range(H):
        row = []
        for i in range(W):
            d = (F + R * ((2 * (i + 0.5) / W - 1) * t[0]) + U * ((1 - 2 * (j + 0.5) / H) * t[1])).normalized()
            hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, C, d, distance=1e4)
            row.append((group_of(obj) if hit else 'sky', loc.copy() if hit else None, nrm.copy() if hit else None))
        out.append(row)
    return out

end_map = idmap(END, FILM)
start_map = idmap(START, FILM)

def boxes(m):
    b = {}
    for j in range(H):
        for i in range(W):
            g = m[j][i][0]
            if g.startswith('street') or g == 'sky':
                continue
            x0, y0, x1, y1, n = b.get(g, (1, 1, 0, 0, 0))
            b[g] = (min(x0, i / W), min(y0, j / H), max(x1, (i + 1) / W), max(y1, (j + 1) / H), n + 1)
    return {g: [round(v, 3) for v in bb[:4]] + [round(bb[4] / (W * H) * 100, 2)] for g, bb in b.items()}
result = {'end_boxes': boxes(end_map), 'start_boxes': boxes(start_map)}

# --------------------------------------------------------------- what the end frame sees that the plate (start, 64.4) did not
HIDE_A = {'drum', 'chair', 'lantern', 'pail', 'board', 'notice'}
HIDE_B = HIDE_A | {'board posts', 'lamp post'}
cat = [[None] * W for _ in range(H)]
need = []
dg = bpy.context.evaluated_depsgraph_get()
for j in range(H):
    for i in range(W):
        g, P, n = end_map[j][i]
        if g == 'sky':
            cat[j][i] = ('sky', None); continue
        x, y, zc = project(P, START, PLATE)
        if zc <= 0 or not (0 <= x <= 1 and 0 <= y <= 1):
            cat[j][i] = ('outside plate', None); continue
        Q = P - START
        dist = Q.length
        if n.dot(-Q) <= 0:
            cat[j][i] = ('faces away from plate', g); continue
        hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, START, Q.normalized(), distance=dist * (1 - 0.004) - 0.01)
        if not hit:
            cat[j][i] = ('painted', g); continue
        occ = group_of(obj)
        cat[j][i] = ('occluded', g, occ)
        need.append((j, i))

# move the hide-list props away and test again
def move_away(groups):
    moved = []
    for o in bpy.data.objects:
        if o.parent is None and o.type in ('MESH', 'EMPTY') and group_of(o) in groups:
            moved.append((o, o.location.copy())); o.location.z -= 1000
    # posts and coals are roots too
    bpy.context.view_layer.update()
    return moved
def restore(moved):
    for o, loc in moved:
        o.location = loc
    bpy.context.view_layer.update()

def roots_in(groups):
    out = []
    for o in bpy.data.objects:
        if o.parent is not None:
            continue
        g = group_of(o)
        if g in groups:
            out.append(o)
        elif o.type == 'EMPTY':
            # a holder: its own group via children
            kids = [c for c in o.children_recursive if c.type == 'MESH']
            if kids and group_of(kids[0]) in groups:
                out.append(o)
    return out

summary = {}
for label, hide in (('A brief hide list (drum, chair, lantern, pail, board+notice)', HIDE_A), ('B plus board posts and lamp post', HIDE_B)):
    moved = []
    for o in roots_in(hide):
        moved.append((o, o.location.copy())); o.location.z -= 1000
    bpy.context.view_layer.update()
    dg2 = bpy.context.evaluated_depsgraph_get()
    counts = {}
    mapimg = []
    for j in range(H):
        for i in range(W):
            c = cat[j][i]
            if c[0] == 'occluded':
                g, occ = c[1], c[2]
                P = end_map[j][i][1]
                if g in hide:
                    key = ('near-prop surface uncovered -> own texture', g, occ)
                else:
                    Q = P - START
                    hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg2, START, Q.normalized(), distance=Q.length * (1 - 0.004) - 0.01)
                    key = ('behind painting', g, occ) if not hit else ('own texture: hidden by a prop not painted out', g, group_of(obj))
            else:
                key = (c[0], c[1] if c[0] != 'painted' else 'any', '')
            counts[key] = counts.get(key, 0) + 1
            mapimg.append(key[0])
    for o, loc in moved:
        o.location = loc
    bpy.context.view_layer.update()
    tot = W * H
    summary[label] = sorted([[k[0], k[1], k[2], round(v / tot * 100, 3)] for k, v in counts.items()], key=lambda r: -r[3])
    # write a category image (ppm)
    colours = {'painted': (40, 40, 40), 'sky': (10, 10, 30), 'behind painting': (40, 200, 70),
               'near-prop surface uncovered -> own texture': (255, 140, 0), 'own texture: hidden by a prop not painted out': (255, 0, 0),
               'faces away from plate': (0, 120, 255), 'outside plate': (255, 0, 255)}
    with open(os.path.join(BR, 'cat-' + label[0] + '.ppm'), 'wb') as fh:
        fh.write(b'P6 %d %d 255\n' % (W, H))
        fh.write(bytes(v for k in mapimg for v in colours[k]))
result['uncovered'] = summary

# --------------------------------------------------------------- which lights reach a road point in the wedge
lights = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'POINT']
probe = {}
for name, (fx, fy) in {'wedge mid (0.35, 0.86)': (0.35, 0.86), 'wedge low (0.22, 0.95)': (0.22, 0.95), 'lit road (0.06, 0.81)': (0.06, 0.81), 'lit band (0.25, 0.69)': (0.25, 0.69)}.items():
    g, P, n = end_map[int(fy * H)][int(fx * W)]
    rows = []
    for L in lights:
        Lp = L.matrix_world.translation
        d = Lp - P
        hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, P + n * 0.002, d.normalized(), distance=d.length - 0.02)
        rows.append([L.name, round(L.data.energy, 0), round(d.length, 2), 'blocked by ' + group_of(obj) if hit else 'lit'])
    probe[name] = {'surface': g, 'point': [round(v, 2) for v in P], 'lights': rows}
result['light_probe'] = probe

# --------------------------------------------------------------- key points, start vs end (film lens)
pts = {}
def add(name, P):
    pts[name] = {'end': [round(v, 3) for v in project(P, END, FILM)[:2]], 'start': [round(v, 3) for v in project(P, START, FILM)[:2]], 'start_in_plate': [round(v, 3) for v in project(P, START, PLATE)[:2]]}
nc = ns['notice_centre']()
add('notice centre', nc)
for o in bpy.data.objects:
    if o.name in ('corner_lamp_light', 'brazier_light', 'lantern_light'):
        add(o.name, o.matrix_world.translation)
result['points'] = pts
result['cameras'] = {'end': [round(v, 3) for v in END], 'start': [round(v, 3) for v in START]}
json.dump(result, open(os.path.join(BR, 'analysis.json'), 'w'), indent=1)
print('ANALYSIS DONE')
