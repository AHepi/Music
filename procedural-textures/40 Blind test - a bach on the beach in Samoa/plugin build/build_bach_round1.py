"""
Builds a bach (small simple holiday house) on a beach in Samoa, modern day, as plain named shapes.
Nothing is textured or lit here. Every object is named with role words from the painted-place plugin.
The place runs along Y (the beach), ground at Z = 0, metres. Camera: a standing person on the sand.

    python3 build_bach.py --out /home/claude/blind-test/plugin-build/bach.blend
"""
import argparse
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def emit(name, bm, xf=None, solid=None, smooth=False):
    if xf is not None:
        bmesh.ops.transform(bm, matrix=xf, verts=bm.verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    if solid:
        mod = obj.modifiers.new('thickness', 'SOLIDIFY')
        mod.thickness = solid
        mod.offset = 0
    return obj


def add_box(bm, c, size, rot=(0, 0, 0)):
    m = Matrix.Translation(c) @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X') \
        @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)


def add_cyl(bm, c, r1, r2, depth, rot=(0, 0, 0), seg=12):
    m = Matrix.Translation(c) @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth, matrix=m)


def new():
    return bmesh.new()


def box_obj(name, c, size, rot=(0, 0, 0), xf=None):
    bm = new()
    add_box(bm, c, size, rot)
    return emit(name, bm, xf)


def uv_box(obj):
    """Give an object simple box-projected UVs so materials that want UVs have some."""
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=2.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)


# --------------------------------------------------------------------------- the bach (local frame: x across, y long, z up)
BACH_CENTRE = Vector((-1.9, 9.0, 0.0))
BACH_TURN = math.radians(30)
XF = Matrix.Translation(BACH_CENTRE) @ Matrix.Rotation(BACH_TURN, 4, 'Z')

FLOOR_TOP = 0.6
WALL_TOP = 3.0
HALF_W = 1.8
FRONT_Y = -3.5
BACK_Y = 3.5


def boarded(name, along, fixed, lo, hi, openings, normal_sign, bm=None):
    """A wall of lapped weatherboards. along = 'x' or 'y' is the direction the boards run; fixed is the other coordinate.
    openings: list of (a0, a1, z0, z1) gaps in the boards."""
    bm = new()
    rows = int((WALL_TOP - FLOOR_TOP) / 0.15)
    for r in range(rows):
        z0 = FLOOR_TOP + r * 0.15
        z1 = z0 + 0.15
        cuts = [(a0, a1) for (a0, a1, oz0, oz1) in openings if z1 > oz0 and z0 < oz1]
        cuts.sort()
        segs = []
        cur = lo
        for a0, a1 in cuts:
            if a0 > cur:
                segs.append((cur, a0))
            cur = max(cur, a1)
        if cur < hi:
            segs.append((cur, hi))
        for s0, s1 in segs:
            mid = (s0 + s1) / 2
            length = s1 - s0
            out = fixed + normal_sign * (0.02 + 0.008 * (r % 2))
            zc = (z0 + z1) / 2
            tilt = normal_sign * 0.12
            if along == 'x':
                add_box(bm, (mid, out, zc), (length, 0.045, 0.145), rot=(tilt, 0, 0))
            else:
                add_box(bm, (out, mid, zc), (0.045, length, 0.145), rot=(0, -tilt, 0))
    return bm


def build_bach():
    # piles and floor
    bm = new()
    for x in (-1.7, 0, 1.7):
        for y in (-5.2, -2.0, 1.2, 3.3):
            add_cyl(bm, (x, y, 0.27), 0.09, 0.09, 0.55, seg=8)
    emit('bach pile timber', bm, XF)
    bm = new()
    add_box(bm, (0, -1.0, FLOOR_TOP - 0.05), (4.0, 9.0, 0.1))
    emit('bach floor plank', bm, XF)
    # steps down from the verandah (front)
    bm = new()
    for i in range(3):
        add_box(bm, (0, -5.85 - i * 0.3, FLOOR_TOP - 0.17 - i * 0.17), (1.2, 0.3, 0.06))
    emit('bach verandah stair plank', bm, XF)

    # walls: a dark core (the shadow in the gaps), then lapped boards
    box_obj('bach core wall inside', (0, 0, (FLOOR_TOP + WALL_TOP) / 2), (3.5, 6.9, WALL_TOP - FLOOR_TOP), xf=XF)
    front_open = [(-0.45, 0.45, FLOOR_TOP, 2.6), (0.85, 1.55, 1.4, 2.5), (-1.55, -0.85, 1.4, 2.5)]
    emit('bach front wall board timber', boarded('front', 'x', FRONT_Y, -HALF_W, HALF_W, front_open, -1), XF)
    side_open = [(-1.8 - 0.45, -1.8 + 0.45, 1.4, 2.5), (-0.45, 0.45, 1.4, 2.5), (1.8 - 0.45, 1.8 + 0.45, 1.4, 2.5)]
    emit('bach left wall board timber', boarded('left', 'y', -HALF_W, FRONT_Y, BACK_Y, side_open, -1), XF)
    emit('bach right wall board timber', boarded('right', 'y', HALF_W, FRONT_Y, BACK_Y, side_open, 1), XF)
    emit('bach back wall board timber', boarded('back', 'x', BACK_Y, -HALF_W, HALF_W, [], 1), XF)

    # window frames, louvre slats, panes
    frames = new()
    slats = new()
    panes = []  # (name, centre, size)

    def window(wall, pos, kind):
        if wall == 'front':
            c = (pos, FRONT_Y - 0.03, 1.95)
            size = (0.7, 0.05, 1.1)
            fs = [(0.84, 0.06, 0.07), (0.84, 0.06, 0.07)]
            for dz in (-0.56, 0.56):
                add_box(frames, (c[0], c[1] - 0.02, c[2] + dz), (0.86, 0.07, 0.07))
            for dx in (-0.43, 0.43):
                add_box(frames, (c[0] + dx, c[1] - 0.02, c[2]), (0.07, 0.07, 1.14))
            for k in range(7):
                add_box(slats, (c[0], c[1] - 0.05, c[2] - 0.47 + k * 0.157), (0.74, 0.07, 0.03), rot=(math.radians(-28), 0, 0))
            panes.append(('bach front louvre %s window' % kind, c, size))
        else:
            sx = -1 if wall == 'left' else 1
            c = (sx * (HALF_W + 0.03), pos, 1.95)
            size = (0.05, 0.7, 1.1)
            for dz in (-0.56, 0.56):
                add_box(frames, (c[0] + sx * 0.02, c[1], c[2] + dz), (0.07, 0.86, 0.07))
            for dy in (-0.43, 0.43):
                add_box(frames, (c[0] + sx * 0.02, c[1] + dy, c[2]), (0.07, 0.07, 1.14))
            for k in range(7):
                add_box(slats, (c[0] + sx * 0.05, c[1], c[2] - 0.47 + k * 0.157), (0.07, 0.74, 0.03), rot=(0, 0, 0) if False else (0, math.radians(28 * sx), 0))
            panes.append(('bach %s louvre %s window' % (wall, kind), c, size))

    window('front', -1.2, 'lit')
    window('front', 1.2, 'dark')
    window('left', -1.8, 'dim')
    window('left', 0.0, 'lit')
    window('left', 1.8, 'dark')
    window('right', -1.8, 'dark')
    window('right', 0.0, 'dim')
    window('right', 1.8, 'dark')
    emit('bach casing frame timber', frames, XF)
    emit('bach louvre slat timber', slats, XF)
    for i, (name, c, size) in enumerate(panes):
        # name carries "<wall> louvre <kind> window"; the role words are 'window' + 'lit'/'dim'/'dark'
        box_obj(name + ' %d' % i, c, size, xf=XF)

    # door
    box_obj('bach front door timber', (0, FRONT_Y - 0.03, (FLOOR_TOP + 2.6) / 2), (0.9, 0.05, 2.0), xf=XF)
    bm = new()
    for dx in (-0.5, 0.5):
        add_box(bm, (dx, FRONT_Y - 0.05, (FLOOR_TOP + 2.65) / 2), (0.08, 0.08, 2.1))
    add_box(bm, (0, FRONT_Y - 0.05, 2.65), (1.08, 0.08, 0.08))
    emit('bach door frame timber', bm, XF)

    # verandah columns, beam, handrail
    bm = new()
    for x in (-1.85, 1.85):
        add_box(bm, (x, -5.3, (FLOOR_TOP + 3.0) / 2), (0.12, 0.12, 3.0 - FLOOR_TOP))
    add_box(bm, (0, -5.3, 3.0), (3.9, 0.14, 0.14))
    add_box(bm, (0, -3.5, 3.0), (3.9, 0.14, 0.14))
    for x in (-1.85, 1.85):
        add_box(bm, (x, -4.4, 3.0), (0.14, 1.9, 0.14))
    for x in (-1.85, 1.85):
        add_box(bm, (x, -4.4, 1.5), (0.06, 1.8, 0.06))
        add_box(bm, (x, -4.4, 1.2), (0.05, 1.8, 0.05))
    add_box(bm, (0, -5.3, 1.5), (0.8, 0.06, 0.06))
    emit('bach verandah column timber', bm, XF)

    # gable infill at the front: a triangle of boards
    bm = new()
    ridge_z = 4.55
    verts = [bm.verts.new(v) for v in [(-2.35, -5.45, 3.0), (2.35, -5.45, 3.0), (0, -5.45, ridge_z),
                                       (-2.35, -5.38, 3.0), (2.35, -5.38, 3.0), (0, -5.38, ridge_z)]]
    bm.faces.new((verts[0], verts[1], verts[2]))
    bm.faces.new((verts[3], verts[5], verts[4]))
    bm.faces.new((verts[0], verts[3], verts[4], verts[1]))
    bm.faces.new((verts[0], verts[2], verts[5], verts[3]))
    bm.faces.new((verts[1], verts[4], verts[5], verts[2]))
    gable = emit('bach front gable board timber', bm, XF)
    uv_box(gable)
    # board lines over the gable
    bm = new()
    for i in range(8):
        z = 3.1 + i * 0.18
        half = 2.35 * (ridge_z - z) / (ridge_z - 3.0)
        if half > 0.05:
            add_box(bm, (0, -5.5, z), (half * 2, 0.04, 0.03))
    emit('bach front gable lap board timber', bm, XF)

    # roof: two corrugated iron sheets, ridge along the long axis
    for s, label in ((-1, 'left'), (1, 'right')):
        bm = new()
        nu, nv = 2, 330
        y0, y1 = -5.8, 3.8
        slope = Vector((s * 2.5, 0, -1.65))
        normal = Vector((s * 1.65, 0, 2.5)).normalized()
        grid = []
        for iu in range(nu + 1):
            u = iu / nu
            row = []
            for iv in range(nv + 1):
                y = y0 + (y1 - y0) * iv / nv
                base = Vector((0, y, ridge_z)) + slope * u
                base += normal * (0.03 * math.sin(2 * math.pi * (y - y0) / 0.22))
                row.append(bm.verts.new(base))
            grid.append(row)
        for iu in range(nu):
            for iv in range(nv):
                bm.faces.new((grid[iu][iv], grid[iu][iv + 1], grid[iu + 1][iv + 1], grid[iu + 1][iv]))
        emit('bach %s corrugated rust sheet' % label, bm, XF, solid=0.012, smooth=True)
    bm = new()
    add_box(bm, (0, -1.0, ridge_z + 0.03), (0.35, 9.8, 0.04), rot=(0, 0, 0))
    emit('bach apex flashing iron', bm, XF)
    # fascia boards on the eaves
    bm = new()
    for s in (-1, 1):
        add_box(bm, (s * 2.5, -1.0, ridge_z - 1.65 - 0.06), (0.04, 9.8, 0.2), rot=(0, s * math.radians(33), 0))
    add_box(bm, (0, -5.85, ridge_z + 0.0), (0.04, 0.04, 0.04))
    emit('bach fascia board timber', bm, XF)
    # gutter and downpipe, as steel
    bm = new()
    add_cyl(bm, (-2.52, -1.0, 2.75), 0.05, 0.05, 9.6, rot=(math.radians(90), 0, 0), seg=8)
    add_cyl(bm, (-1.84, 3.2, 1.8), 0.035, 0.035, 2.4, seg=8)
    emit('bach gutter and down pipe steel', bm, XF)

    # lamps: an LED bulkhead light over the door, one under the verandah beam
    box_obj('bach door lamp glass', (0, FRONT_Y - 0.09, 2.85), (0.26, 0.14, 0.2), xf=XF)
    box_obj('bach verandah lamp glass', (0.0, -5.2, 2.88), (0.22, 0.22, 0.14), xf=XF)

    # two plastic chairs on the verandah (named as planks: the plugin has no plastic)
    bm = new()
    for cx, cy, rz in ((-1.2, -4.5, 0.4), (-0.35, -4.7, -0.3)):
        c = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rz, 4, 'Z')
        sub = new()
        add_box(sub, (0, 0, FLOOR_TOP + 0.43), (0.46, 0.46, 0.05))
        add_box(sub, (0, 0.21, FLOOR_TOP + 0.72), (0.46, 0.05, 0.55), rot=(math.radians(-8), 0, 0))
        for dx in (-0.2, 0.2):
            for dy in (-0.2, 0.2):
                add_box(sub, (dx, dy, FLOOR_TOP + 0.2), (0.04, 0.04, 0.42))
        bmesh.ops.transform(sub, matrix=c, verts=sub.verts)
        tmp = bpy.data.meshes.new('t')
        sub.to_mesh(tmp)
        sub.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    emit('bach verandah chair plank', bm, XF)
    # a surfboard leaning on the front wall beside the right window
    bm = new()
    add_box(bm, (1.7, FRONT_Y - 0.22, FLOOR_TOP + 1.1), (0.5, 0.05, 2.1), rot=(math.radians(-8), 0, 0))
    emit('bach surfboard plank', bm, XF)


# --------------------------------------------------------------------------- ground, sea, sky edge
def build_ground():
    bm = new()
    add_box(bm, (-10, 29, -0.05), (30, 90, 0.1))
    ground = emit('beach sand ground', bm)
    bm = new()
    add_box(bm, (-33, 29, 0.0), (36, 90, 0.04))  # the village side: a lawn at the back of the beach
    emit('village lawn grass', bm)
    # the sea
    bm = new()
    add_box(bm, (4.5 + 400, 200, -0.02), (800, 800, 0.02))
    emit('sea water', bm)
    bm = new()
    add_box(bm, (4.5 + 400, 200, -0.5), (800, 800, 0.1))
    emit('sea bed shadow', bm)
    # a low reef line out in the lagoon
    bm = new()
    rng = random.Random(3)
    y = -10
    while y < 80:
        ln = rng.uniform(6, 14)
        add_box(bm, (46 + rng.uniform(-1, 1), y + ln / 2, 0.1), (rng.uniform(2, 4), ln, rng.uniform(0.3, 0.5)))
        y += ln + rng.uniform(1, 4)
    emit('reef stone', bm)
    # a headland at the far end of the beach
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=1.0)
    rr = random.Random(11)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.z *= 0.2
        v.co.x *= 30
        v.co.y *= 16
        v.co.z *= 11
        v.co.z += rr.uniform(-0.3, 0.3) * (1 if v.co.z > 0 else 0)
    emit('headland moss', bm, Matrix.Translation((-6, 80, -1.0)), smooth=True)


# --------------------------------------------------------------------------- palms
def make_palm(idx, base, height, lean_dir, lean, seed):
    rng = random.Random(seed)
    ldx, ldy = lean_dir
    n_ring, n_seg = 18, 10
    bm = new()
    rings = []
    path = []
    for i in range(n_ring):
        t = i / (n_ring - 1)
        off = lean * (t ** 1.7)
        wob = 0.12 * math.sin(t * 5 + seed)
        p = Vector((base[0] + ldx * off + wob * -ldy, base[1] + ldy * off + wob * ldx, height * t))
        path.append(p)
        r = 0.22 - 0.09 * t + 0.14 * max(0.0, 1 - t * 7) ** 2
        r *= 1 + 0.045 * math.sin(t * 90)
        ring = []
        for k in range(n_seg):
            a = 2 * math.pi * k / n_seg
            ring.append(bm.verts.new(p + Vector((r * math.cos(a), r * math.sin(a), 0))))
        rings.append(ring)
    for i in range(n_ring - 1):
        for k in range(n_seg):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % n_seg], rings[i + 1][(k + 1) % n_seg], rings[i + 1][k]))
    emit('palm %d trunk wood' % idx, bm, smooth=True)
    crown = path[-1] + Vector((0, 0, 0.05))
    # fronds
    bm = new()
    count = 15
    for f in range(count):
        az = 2 * math.pi * (f / count) + rng.uniform(-0.2, 0.2)
        e0 = math.radians(rng.choice([55, 45, 30, 15, 5, -10, -25, 20, 35, 10, -15, 25, 0, 40, 50]) + rng.uniform(-6, 6))
        L = rng.uniform(3.2, 4.3)
        k = rng.uniform(0.07, 0.15) * (1.6 if e0 < 0 else 1.0)
        n = 22
        dirh = Vector((math.cos(az), math.sin(az), 0))
        perp = Vector((-math.sin(az), math.cos(az), 0))
        prev = None
        for i in range(n + 1):
            s = i / n
            d = s * L
            h = d * math.cos(e0)
            z = d * math.sin(e0) - k * d * d
            spine = crown + dirh * h + Vector((0, 0, z))
            w = 0.42 * math.sin(math.pi * min(1.0, s ** 0.7)) * (1.0 if i % 2 == 0 else 0.5)
            left = spine + perp * w + Vector((0, 0, -0.75 * w))
            right = spine - perp * w + Vector((0, 0, -0.75 * w))
            cur = (bm.verts.new(left), bm.verts.new(spine), bm.verts.new(right))
            if prev:
                bm.faces.new((prev[0], prev[1], cur[1], cur[0]))
                bm.faces.new((prev[1], prev[2], cur[2], cur[1]))
            prev = cur
    emit('palm %d frond grass' % idx, bm)


def make_fern_clump(idx, c, seed):
    rng = random.Random(seed)
    bm = new()
    for f in range(9):
        az = 2 * math.pi * f / 9 + rng.uniform(-0.2, 0.2)
        L = rng.uniform(1.0, 1.7)
        e0 = math.radians(rng.uniform(35, 65))
        dirh = Vector((math.cos(az), math.sin(az), 0))
        perp = Vector((-math.sin(az), math.cos(az), 0))
        prev = None
        for i in range(13):
            s = i / 12
            d = s * L
            spine = Vector(c) + dirh * (d * math.cos(e0)) + Vector((0, 0, d * math.sin(e0) - 0.35 * d * d + 0.05))
            w = 0.17 * math.sin(math.pi * min(1, s ** 0.7)) * (1 if i % 2 == 0 else 0.6)
            cur = (bm.verts.new(spine + perp * w), bm.verts.new(spine), bm.verts.new(spine - perp * w))
            if prev:
                bm.faces.new((prev[0], prev[1], cur[1], cur[0]))
                bm.faces.new((prev[1], prev[2], cur[2], cur[1]))
            prev = cur
    emit('fern %d frond grass' % idx, bm)


# --------------------------------------------------------------------------- the village: a fale in the distance, a tank, a pole, a canoe, a fire
def build_fale(c):
    cx, cy = c
    bm = new()
    for k in range(10):
        a = 2 * math.pi * k / 10
        add_cyl(bm, (cx + 3.2 * math.cos(a), cy + 2.2 * math.sin(a), 1.1), 0.1, 0.1, 2.2, seg=8)
    emit('fale post timber', bm)
    bm = new()
    add_box(bm, (cx, cy, 0.2), (7.4, 5.4, 0.4))
    emit('fale foundation stone', bm)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=1.0, radius2=0.0, depth=1.0, matrix=Matrix.Diagonal((1, 1, 1, 1)))
    for v in bm.verts:
        v.co.x *= 4.4 * 1.0
        v.co.y *= 3.3
        v.co.z = (v.co.z + 0.5) * 3.2 + 2.2
        v.co.z += 0.0
    # round the shoulder of the dome a little
    for v in bm.verts:
        r = math.hypot(v.co.x / 4.4, v.co.y / 3.3)
        v.co.z = 2.2 + 3.0 * (1 - r ** 1.6) ** 0.8 if r < 1 else 2.2
    emit('fale thatch leaf', bm, Matrix.Translation((cx, cy, 0)), smooth=True)
    box_obj('fale lantern lamp glass', (cx, cy - 0.5, 1.7), (0.2, 0.2, 0.3))
    # a post above, with the lantern's hook
    box_obj('fale hook post timber', (cx, cy - 0.5, 2.0), (0.04, 0.04, 0.8))


def build_village():
    # water tank on a stand, beside the bach
    bm = new()
    for dx in (-0.6, 0.6):
        for dy in (-0.6, 0.6):
            add_box(bm, (1.9 + dx, 11.4 + dy, 0.3), (0.12, 0.12, 0.6))
    add_box(bm, (1.9, 11.4, 0.62), (1.5, 1.5, 0.08))
    emit('tank stand timber', bm)
    bm = new()
    add_cyl(bm, (1.9, 11.4, 1.7), 0.78, 0.78, 2.0, seg=24)
    add_cyl(bm, (1.9, 11.4, 2.75), 0.5, 0.45, 0.12, seg=24)
    emit('rain tank steel', bm, smooth=False)
    # a solar panel on a short post
    bm = new()
    add_box(bm, (0.2, 7.0, 0.8), (0.1, 0.1, 1.6))
    emit('solar mount timber', bm)
    box_obj('solar panel glass', (0.2, 6.85, 1.72), (1.0, 0.04, 1.5), rot=(math.radians(-32), 0, 0))
    # the power pole and its wire to the bach
    bm = new()
    add_cyl(bm, (4.0, 5.5, 3.8), 0.14, 0.11, 7.6, seg=10)
    add_box(bm, (4.0, 5.5, 7.1), (1.4, 0.08, 0.08))
    emit('power pole timber', bm)
    top = Vector((4.0, 5.5, 7.1))
    eave = XF @ Vector((1.0, -3.2, 3.0))
    mid = (top + eave) / 2
    direction = eave - top
    bm = new()
    rot = direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    m = Matrix.Translation(mid) @ rot
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.012, radius2=0.012, depth=direction.length, matrix=m)
    emit('power wire iron', bm)
    # beached outrigger canoe (paopao)
    bm = new()
    stations = 14
    rings = []
    for i in range(stations + 1):
        t = i / stations
        y = -2.3 + 4.6 * t
        w = 0.34 * (math.sin(math.pi * t) ** 0.55)
        dpt = 0.28 * (math.sin(math.pi * t) ** 0.4)
        rise = 0.2 * (abs(2 * t - 1) ** 2.2)
        ring = []
        for k in range(9):
            a = math.pi * k / 8
            ring.append(bm.verts.new((w * math.cos(a), y, 0.32 + rise - dpt * math.sin(a) - 0.0)))
        rings.append(ring)
    for i in range(stations):
        for k in range(8):
            bm.faces.new((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]))
    hull = emit('paopao hull timber', bm, Matrix.Translation((3.0, 5.0, 0.0)) @ Matrix.Rotation(math.radians(8), 4, 'Z'), solid=0.03, smooth=True)
    bm = new()
    add_cyl(bm, (1.5, 0, 0.3), 0.07, 0.07, 3.6, rot=(math.radians(90), 0, 0), seg=10)
    for dy in (-0.9, 0.9):
        add_cyl(bm, (0.75, dy, 0.36), 0.025, 0.025, 1.5, rot=(0, math.radians(90), 0), seg=6)
    emit('paopao outrigger float timber', bm, Matrix.Translation((3.0, 5.0, 0.0)) @ Matrix.Rotation(math.radians(8), 4, 'Z'))
    # a fire pit on the sand, near the camera: ring of stones, two logs, a low flame
    rng = random.Random(21)
    fx, fy = 0.35, -1.9
    bm = bmesh.new()
    for k in range(9):
        a = 2 * math.pi * k / 9
        sub = bmesh.new()
        bmesh.ops.create_icosphere(sub, subdivisions=1, radius=0.13)
        for v in sub.verts:
            v.co *= Vector((1.0, rng.uniform(0.8, 1.2), rng.uniform(0.7, 1.0)))
        bmesh.ops.transform(sub, matrix=Matrix.Translation((fx + 0.5 * math.cos(a), fy + 0.5 * math.sin(a), 0.07)), verts=sub.verts)
        tmp = bpy.data.meshes.new('t')
        sub.to_mesh(tmp)
        sub.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    emit('hearth ring stone', bm)
    bm = new()
    add_cyl(bm, (fx, fy, 0.12), 0.06, 0.06, 0.8, rot=(math.radians(90), math.radians(25), 0), seg=8)
    add_cyl(bm, (fx, fy, 0.18), 0.06, 0.06, 0.8, rot=(math.radians(90), math.radians(-35), 0), seg=8)
    emit('hearth log timber', bm)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.2, radius2=0.02, depth=0.45, matrix=Matrix.Translation((fx, fy, 0.38)))
    emit('fire flame', bm)
    # driftwood and a boulder or two along the foreground and the waterline
    bm = new()
    add_cyl(bm, (-1.3, -3.2, 0.1), 0.09, 0.07, 1.8, rot=(math.radians(90), math.radians(20), math.radians(10)), seg=8)
    add_cyl(bm, (1.1, 0.8, 0.07), 0.07, 0.06, 1.2, rot=(math.radians(90), math.radians(-60), 0), seg=8)
    add_cyl(bm, (3.4, 13.0, 0.09), 0.1, 0.08, 2.4, rot=(math.radians(90), math.radians(15), 0), seg=8)
    emit('driftwood timber', bm)
    bm = bmesh.new()
    for (x, y, s) in ((-1.8, -2.2, 0.35), (-1.55, -2.5, 0.2), (3.9, 3.0, 0.45), (4.1, 14.0, 0.55), (3.6, 20.0, 0.4), (4.2, 30.0, 0.6),
                      (-3.0, 20.0, 0.5), (4.0, 9.5, 0.3)):
        sub = bmesh.new()
        bmesh.ops.create_icosphere(sub, subdivisions=2, radius=s)
        for v in sub.verts:
            v.co *= Vector((rng.uniform(0.9, 1.4), rng.uniform(0.9, 1.4), rng.uniform(0.55, 0.8)))
            v.co += Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)))
        bmesh.ops.transform(sub, matrix=Matrix.Translation((x, y, s * 0.35)), verts=sub.verts)
        tmp = bpy.data.meshes.new('t')
        sub.to_mesh(tmp)
        sub.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    emit('shore boulder stone', bm)


def build_camera():
    data = bpy.data.cameras.new('bach camera')
    data.lens = 32
    data.sensor_width = 36
    cam = bpy.data.objects.new('bach camera', data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.0, -7.0, 1.65)
    target = Vector((0.0, 13.0, 2.3))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920


def build():
    clear()
    build_ground()
    build_bach()
    build_village()
    build_fale((-6.0, 33.0))
    # palms: around and behind the bach; they lean toward the sea (+x)
    palms = [
        (( -5.8, 16.0), 9.5, (0.6, 0.0), 1.8),
        (( -1.5, 20.0), 10.5, (0.5, 0.1), 1.4),
        ((  2.6, 17.0), 8.8, (0.9, 0.0), 2.4),
        (( 3.2, 26.0), 9.8, (0.9, 0.0), 2.2),
        ((-8.5, 24.0), 11.0, (0.5, 0.0), 1.6),
        (( -3.2, 29.0), 10.0, (0.6, 0.0), 1.9),
        ((  3.5, 38.0), 10.5, (0.9, 0.0), 2.0),
        ((-6.6, 5.0), 9.0, (0.8, 0.0), 2.4),
    ]
    for i, (base, h, ld, lean) in enumerate(palms):
        make_palm(i + 1, (base[0], base[1]), h, ld, lean, 100 + i)
    for i, c in enumerate([(-3.4, 3.0, 0), (-4.2, 12.6, 0), (2.8, 6.0, 0), (1.0, 14.5, 0), (-5.5, 8.0, 0)]):
        make_fern_clump(i + 1, c, 50 + i)
    build_camera()


if __name__ == '__main__':
    import sys
    argv = sys.argv
    argv = argv[argv.index('--') + 1:] if '--' in argv else argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    a = p.parse_args(argv)
    build()
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    print('saved', a.out, 'objects', len(bpy.data.objects))
