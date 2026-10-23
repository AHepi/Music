"""Place buildings, props, fences and garden details in the village."""
import math, time
import numpy as np
import bpy
from common import *
import layout, materials, buildings, props, plants, stage1

def ensure_layout():
    if not layout.ROADS or layout.HOOF_KD is None:
        stage1.setup_layout()

def gz(x, y):
    return float(layout.terrain_eval(np.array([x], float), np.array([y], float), do_hoof=False)['z'][0])

def gz_arr(X, Y):
    return layout.terrain_eval(np.asarray(X, float), np.asarray(Y, float), do_hoof=False)['z']

def bmat(name, default=None):
    return bpy.data.materials.get(name)

def all_building_mats():
    names = buildings.CM_NAMES
    out = []
    for n in names:
        m = bpy.data.materials.get(n)
        if m is None:
            raise RuntimeError('missing material ' + n)
        out.append(m)
    return out

def plant_mats():
    out = []
    for n in plants.PM_NAMES:
        m = bpy.data.materials.get(n)
        if m is None:
            raise RuntimeError('missing material ' + n)
        out.append(m)
    return out

def l2w(b, lx, ly):
    c, s = math.cos(b['yaw']), math.sin(b['yaw'])
    return b['x'] + lx * c - ly * s, b['y'] + lx * s + ly * c

def link_obj(name, me, coll, loc, yaw=0.0, scale=1.0, rot=None):
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot if rot is not None else (0, 0, yaw)
    ob.scale = (scale, scale, scale) if np.isscalar(scale) else scale
    return ob

# ----------------------------------------------------------------------------- buildings
COTTAGES = {
    'Cottage1': dict(seed=21, W=7.2, D=4.8, style='timber', roof='thatch', pitch=46, door_x=-0.8, win_x=(-2.5, 1.5), chim=1, back_win=(-1.8, 1.2)),
    'Cottage2': dict(seed=33, W=6.4, D=4.6, style='stone', roof='shingle', pitch=40, door_x=0.6, win_x=(-1.9,), chim=-1, back_win=(0.0,)),
    'Cottage3': dict(seed=47, W=8.0, D=5.0, style='timber', roof='thatch', pitch=47, door_x=0.4, win_x=(-2.9, 2.5), chim=-1, back_win=(-2.0, 1.5)),
    'Cottage4': dict(seed=58, W=6.0, D=4.4, style='timber', roof='shingle', pitch=41, door_x=-0.5, win_x=(1.75,), chim=1, back_win=(-1.0,)),
    'Cottage5': dict(seed=64, W=7.0, D=4.8, style='stone', roof='thatch', pitch=46, door_x=0.0, win_x=(-2.2, 2.2), chim=1, back_win=(0.0,)),
}

def build_buildings(log=None):
    ensure_layout()
    mats = all_building_mats()
    coll = get_coll('Buildings')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    out = []
    for b in layout.BUILDINGS:
        nm = b['name']
        if nm in COTTAGES:
            p = dict(COTTAGES[nm])
            seed = p.pop('seed')
            mb, info = buildings.cottage(seed, **p)
        else:
            mb, info = buildings.stable(11)
        me = mb.build(nm + '_mesh', mats)
        z = b.get('pad_z')
        if z is None:
            z = layout.building_pad_z(b)
            b['pad_z'] = z
        ob = link_obj(nm, me, coll, (b['x'], b['y'], z), b['yaw'])
        b['info'] = info
        out.append((nm, round(b['x'], 1), round(b['y'], 1), round(z, 2), len(me.polygons)))
        if log is not None:
            log.append('building %s %d faces' % (nm, len(me.polygons)))
    return out

# ----------------------------------------------------------------------------- props
def build_props(log=None):
    ensure_layout()
    mats = all_building_mats()
    pm = plant_mats()
    rng = np.random.RandomState(404)
    coll = get_coll('Props')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    B = {b['name']: b for b in layout.BUILDINGS}
    placed = []

    def put(name, mb, x, y, yaw=0.0, scale=1.0, z=None, mesh=None, matlist=None, tilt=None):
        me = mesh if mesh is not None else mb.build(name + '_m', matlist or mats)
        zz = gz(x, y) if z is None else z
        ob = link_obj(name, me, coll, (x, y, zz), yaw, scale, rot=tilt)
        placed.append(name)
        return ob

    shared = {}
    def shared_mesh(key, fn):
        if key not in shared:
            shared[key] = fn().build('shared_' + key, mats)
        return shared[key]

    # --- village green: well, signpost, lantern post, bench
    put('Well', props.well(rng), 11.5, 1.5, 0.6)
    R1 = layout.ROADS['R1']
    s_j = R1.s_at_x(6.5)
    x, y, tx, ty = R1.point(s_j)
    put('Signpost', props.signpost(rng), x - ty * -3.2 + tx * 1.5, y + tx * -3.2 + ty * 1.5, 0.4)
    put('LanternPost1', props.lantern_post(rng), x + ty * 3.6 + tx * -2.0, y - tx * 3.6 + ty * -2.0, 2.2)
    put('Bench1', props.bench(rng), 8.0, 4.8, math.radians(-100))
    put('Boulder_green', props.boulder(rng, 0.55), 14.5, -1.0, 0.7)

    # --- cottage details (local coordinates, front faces -y)
    def cottage_set(b, ops):
        for (kind, lx, ly, ryaw) in ops:
            wx, wy = l2w(b, lx, ly)
            yaw = b['yaw'] + ryaw
            nm = '%s_%s' % (b['name'], kind)
            if kind == 'barrel':
                put(nm, None, wx, wy, yaw, mesh=shared_mesh('barrel', lambda: props.barrel(np.random.RandomState(5))))
            elif kind == 'barrel2':
                put(nm, None, wx, wy, yaw, mesh=shared_mesh('barrel2', lambda: props.barrel(np.random.RandomState(9), 0.3, 0.85)))
            elif kind == 'woodpile':
                put(nm, props.woodpile(rng), wx, wy, yaw)
            elif kind == 'chop':
                put(nm, props.chopping_block(rng), wx, wy, yaw)
            elif kind == 'bench':
                put(nm, props.bench(rng), wx, wy, yaw)
            elif kind == 'crate':
                put(nm, None, wx, wy, yaw, mesh=shared_mesh('crate', lambda: props.crate(np.random.RandomState(6))))
            elif kind == 'crate2':
                put(nm, None, wx, wy, yaw, scale=0.8, mesh=shared_mesh('crate', lambda: props.crate(np.random.RandomState(6))))
            elif kind == 'sack':
                put(nm, None, wx, wy, yaw, mesh=shared_mesh('sack', lambda: props.sack(np.random.RandomState(8))))
            elif kind == 'jug':
                put(nm, None, wx, wy, yaw, mesh=shared_mesh('jug', lambda: props.jug(np.random.RandomState(3))))
            elif kind == 'ladder':
                ob = put(nm, props.ladder(rng), wx, wy, yaw, tilt=(0, math.radians(-14), yaw))
            elif kind == 'skep':
                put(nm, None, wx, wy, yaw, mesh=shared_mesh('skep', lambda: props.skep(np.random.RandomState(4))))
            elif kind == 'bale':
                put(nm, props.hay_bale(rng), wx, wy, yaw)
            elif kind == 'haystack':
                put(nm, props.haystack(rng), wx, wy, yaw)
            elif kind == 'cart':
                put(nm, props.cart(rng), wx, wy, yaw)
            elif kind == 'trough':
                put(nm, props.trough(rng), wx, wy, yaw)
            elif kind == 'barrow':
                put(nm, props.wheelbarrow(rng), wx, wy, yaw)
            elif kind == 'boulder':
                put(nm, props.boulder(rng, rng.uniform(0.35, 0.7)), wx, wy, yaw)
            elif kind == 'muck':
                put(nm, props.muck_heap(rng), wx, wy, yaw)
            elif kind == 'fork':
                put(nm, props.pitchfork(rng), wx, wy, yaw, tilt=(math.radians(8), math.radians(-6), yaw))
            elif kind == 'broom':
                put(nm, props.broom(rng), wx, wy, yaw, tilt=(math.radians(-8), math.radians(5), yaw))
            elif kind == 'blockseat':
                put(nm, props.stone_block_seat(rng), wx, wy, yaw)
            elif kind == 'lantern':
                put(nm, props.lantern_post(rng, 2.6), wx, wy, yaw)

    cottage_set(B['Cottage1'], [('barrel', -3.0, -3.0, 0.0), ('woodpile', -4.9, 0.2, math.pi / 2), ('chop', 2.4, -4.3, 0.3), ('bench', 1.6, -2.95, 0.0),
                                ('jug', -0.1, -3.1, 0.0), ('barrel2', -3.0, 3.0, 0.5), ('ladder', -1.0, 3.3, math.pi / 2), ('crate', 3.0, -3.7, 0.4)])
    cottage_set(B['Cottage2'], [('barrel', 2.5, -3.2, 0.0), ('barrel2', 3.15, -2.75, 0.4), ('barrow', -3.0, -4.4, 0.8), ('sack', 1.8, -3.0, 0.0), ('sack', 1.4, -2.85, 1.2),
                                ('woodpile', 4.15, 0.0, math.pi / 2), ('skep', -2.6, -2.75, 0.0), ('crate', -3.8, 1.0, 0.7)])
    cottage_set(B['Cottage3'], [('barrel', 3.9, -3.3, 0.0), ('barrel2', 3.4, -3.5, 0.9), ('bench', -1.2, -3.0, 0.0), ('chop', -4.6, -3.8, 0.6), ('woodpile', 5.1, 0.5, math.pi / 2),
                                ('jug', 0.9, -3.05, 0.0), ('ladder', 2.0, 3.6, math.pi / 2), ('bale', -6.5, -1.0, 0.2), ('bale', -6.5, -1.0 + 0.55, 0.1)])
    cottage_set(B['Cottage4'], [('barrel', -2.4, -3.0, 0.0), ('crate', -2.8, 2.6, 0.2), ('crate2', -2.7, 2.6, 0.7), ('sack', 3.2, 0.5, 0.0), ('chop', 3.8, -3.2, 1.0),
                                ('lantern', 1.6, -4.4, 0.0), ('trough', -1.0, 3.9, 0.0)])
    cottage_set(B['Cottage5'], [('haystack', -7.8, 1.0, 0.4), ('bale', 4.2, -3.6, 0.2), ('bale', 4.2, -3.6 + 0.55, 0.3), ('bale', 4.2, -3.6, 0.2), ('cart', 6.5, -6.0, 2.9),
                                ('barrel', -3.4, -3.0, 0.0), ('chop', -2.5, -4.2, 0.2), ('woodpile', 4.7, 1.0, math.pi / 2), ('muck', -5.2, 5.0, 0.0)])

    # --- stable surroundings (stable local frame: front faces -y; bays along x)
    st = B['Stable']
    cottage_set(st, [('cart', -3.6, -6.9, math.radians(-155)), ('trough', 7.4, -3.4, math.radians(90)), ('muck', 8.2, 3.2, 0.0), ('barrel', -6.9, -3.6, 0.0),
                     ('barrel2', -6.9, -4.25, 0.5), ('bale', 6.9, -4.2, 0.1), ('bale', 6.9, -4.2 + 0.55, 0.2), ('bale', 7.55, -4.1, 0.3), ('fork', 5.3, -3.2, 0.0),
                     ('broom', 5.55, -3.18, 0.0), ('blockseat', 2.2, -5.2, 0.3), ('boulder', -8.0, 2.0, 0.0), ('ladder', 6.15, 3.6, math.pi / 2),
                     ('lantern', -1.6, -5.2, 0.0), ('sack', 6.6, -3.5, 0.5)])
    # --- tack left hanging on the front posts of the (empty) stable
    hxs = st['W'] / 2
    pxs = [-hxs + 0.14 + i * (st['W'] - 0.28) / 4 for i in range(5)]
    for nm_, i_, mbf in (('Collar1', 1, props.horse_collar), ('Halter1', 2, props.halter), ('Collar2', 3, props.horse_collar)):
        wx, wy = l2w(st, pxs[i_] + 0.02, -st['D'] / 2 - 0.1)
        put(nm_, mbf(rng), wx, wy, st['yaw'], z=st['pad_z'] + 1.95)
    # --- hand-placed stragglers
    put('LoosePile', props.log_pile_loose(rng), 24.5, 30.0, 0.5)
    return placed

def build_fences(log=None):
    ensure_layout()
    mats = all_building_mats()
    rng = np.random.RandomState(515)
    coll = get_coll('Fences')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    B = {b['name']: b for b in layout.BUILDINGS}
    out = []

    def run(name, b, loop, gate=None):
        pts = []
        for (lx, ly) in loop:
            wx, wy = l2w(b, lx, ly)
            pts.append((wx, wy, gz(wx, wy)))
        mb = props.fence(rng, pts, h=1.05, gap=2.35, rails=2, broken=0.16)
        me = mb.build(name + '_m', mats)
        ob = link_obj(name, me, coll, (0, 0, 0), 0.0)
        out.append(name)

    def garden_loop(b, mx=2.4, my_front=3.1, my_back=2.2, gate_x=None, gate_w=1.5):
        W, D = b['W'], b['D']
        x0, x1 = -W / 2 - mx, W / 2 + mx
        y0, y1 = -D / 2 - my_front, D / 2 + my_back
        gx = gate_x if gate_x is not None else 0.0
        front_a = [(x0, y0), (gx - gate_w / 2, y0)]
        front_b = [(gx + gate_w / 2, y0), (x1, y0)]
        return x0, x1, y0, y1, front_a, front_b

    for nm, ex in (('Cottage1', dict(gate_x=-0.8)), ('Cottage3', dict(gate_x=0.4)), ('Cottage4', dict(gate_x=-0.5, mx=2.0)), ('Cottage2', dict(gate_x=0.6, mx=2.0))):
        b = B[nm]
        x0, x1, y0, y1, fa, fb = garden_loop(b, **ex)
        # front left run, left side, back, right side, front right run (separate runs so the gate stays open)
        run(nm + '_fenceA', b, [(fa[1][0], fa[1][1]), (x0, y0), (x0, y1), (x1, y1), (x1, y0), (fb[0][0], fb[0][1])])
    # farm pen beside cottage 5
    b = B['Cottage5']
    run('Cottage5_pen', b, [(-9.5, -2.0), (-9.5, 5.5), (-3.0, 7.0), (4.5, 6.2)])
    # fence line along the lane near the stable yard
    st = B['Stable']
    run('Stable_paddock', st, [(-9.0, -2.0), (-9.0, 4.0), (-8.0, 9.5), (0.0, 10.8), (8.0, 10.2)])
    return out
