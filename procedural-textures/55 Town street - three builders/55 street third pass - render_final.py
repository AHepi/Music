"""
The town street (third pass: the fronts finished): a tenement street in a northern British town about 1915, at dusk after rain.
First builder: the place; second builder: the near ground; third builder: the buildings' faces and the middle distance.
Draws the whole place and finishes it:  python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
"""
import sys, os, math, random, time
KIT = '/home/claude/build-55-street/kit'
WORK = '/home/claude/build-55-street/fronts'
sys.path.insert(0, KIT + '/store/tools')
import bpy
import bmesh
from mathutils import Vector, Matrix

T0 = time.time()
args = [a for a in sys.argv[1:]]
WIDTH = int(args[0]) if len(args) > 0 else 540
HEIGHT = int(args[1]) if len(args) > 1 else 960
SAMPLES = int(args[2]) if len(args) > 2 else 32
OUT = args[3] if len(args) > 3 else WORK + '/preview.png'
if not os.path.isabs(OUT):
    OUT = os.path.join(os.getcwd(), OUT)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

import store, lay_cobbles, lay_stone, lay_rubble, puddle, sky_and_haze, stain, finish  # noqa: E402

rng = random.Random(55)

def log(msg):
    print('[street %6.1fs] %s' % (time.time() - T0, msg), flush=True)

def coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

C_GROUND = coll('ground')
C_BUILD = coll('buildings')
C_DETAIL = coll('details')
C_LIGHT = coll('lights')

def plain_mat(name, color, rough=0.7, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit is not None:
        b.inputs['Emission Color'].default_value = (emit[0], emit[1], emit[2], 1.0)
        b.inputs['Emission Strength'].default_value = strength
    return m

# ------------------------------------------------------------------------------------------------ geometry helpers
class Acc:
    """Accumulates boxes and cylinders (world space) into one mesh per material."""
    def __init__(self, name, material, bevel=0.0):
        self.name, self.material, self.bevel = name, material, bevel
        self.bm = bmesh.new()

    def box(self, M, centre, size, rot_z=0.0, rot_x=0.0):
        S = Matrix.Diagonal((max(size[0], 1e-4), max(size[1], 1e-4), max(size[2], 1e-4), 1.0))
        R = Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Rotation(rot_x, 4, 'X')
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=M @ Matrix.Translation(Vector(centre)) @ R @ S)

    def cyl(self, M, p0, p1, r, segs=10, r2=None):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-5:
            return
        q = d.normalized().to_track_quat('Z', 'Y')
        T = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r, radius2=(r if r2 is None else r2),
                              depth=L, matrix=M @ T)

    def make(self, collection=C_DETAIL, ground=None):
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        collection.objects.link(obj)
        for p in mesh.polygons:
            p.use_smooth = False
        if self.bevel > 0:
            mod = obj.modifiers.new('bevel', 'BEVEL')
            mod.width = self.bevel
            mod.segments = 2
            mod.limit_method = 'ANGLE'
        if isinstance(self.material, str):
            store.use_material(obj, self.material, ground=ground)
        else:
            mesh.materials.append(self.material)
        return obj

def plane(name, x0, x1, y0, y1, z, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj

def box_object(name, w, d, h, location, turn_deg, collection):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, h / 2)) @ Matrix.Diagonal((w, d, h, 1.0)))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, math.radians(turn_deg))
    collection.objects.link(obj)
    bpy.context.view_layer.update()
    return obj

# accumulators for every made detail
WOOD = Acc('timber details', 'WOOD • peeling dark painted doors')
IRON = Acc('iron details', 'IRON • soot-black lamp posts')
STONE_D = Acc('stone dressings', 'STONE • worn honey-grey architectural dressings', bevel=0.012)
SLATE = Acc('slate roofs', 'MADE • slate roof')
STACK = Acc('chimney stacks and gables', 'SURFACE • old_stone_wall_02', bevel=0.01)
CLAY = Acc('chimney pots', plain_mat('clay pots', (0.20, 0.075, 0.035), rough=0.85))
GLOW = Acc('lit glass', 'GLASS • warm occupied interiors')

def hero_glow_mat():
    m = bpy.data.materials.new('hero shop glow')
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.6
    ramp.inputs['From Max'].default_value = 2.9
    ramp.inputs['To Min'].default_value = 1.6
    ramp.inputs['To Max'].default_value = 5.0
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Value'])
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(ramp.outputs[0], mul.inputs[0])
    nt.links.new(nz.outputs['Fac'], mul.inputs[1])
    mul2 = nt.nodes.new('ShaderNodeMath')
    mul2.operation = 'MULTIPLY'
    mul2.inputs[1].default_value = 2.0
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    em.inputs['Color'].default_value = (1.0, 0.50, 0.17, 1.0)
    nt.links.new(mul2.outputs[0], em.inputs['Strength'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m
HERO = Acc('hero shop glow', hero_glow_mat())
GOODS = Acc('shop goods', plain_mat('shop goods dark', (0.03, 0.018, 0.01), rough=0.6))
WEEDS = Acc('weeds', 'Weed • rain olive')
NAVY = Acc('dark glass', 'GLASS • sleeping navy interiors')
CURTAIN = Acc('curtains', plain_mat('curtain cloth lit through', (0.06, 0.02, 0.012), rough=0.9, emit=(0.55, 0.16, 0.06), strength=0.35))
FLOOR = Acc('close floor', 'SURFACE • cobblestone_floor_01')
DIM = Acc('dim glass', 'GLASS • dim amber rooms')
RUST = Acc('rusty iron', 'RUST • rain-aged iron')
DARK = Acc('recesses', 'RECESSES • near-black blue')
KERB = Acc('kerbstones', 'STONE • worn honey-grey architectural dressings', bevel=0.025)

LIGHTS = []
def point_light(name, loc, energy, color=(1.0, 0.62, 0.32), radius=0.12):
    L = bpy.data.lights.new(name, 'POINT')
    L.energy = energy
    L.color = color
    L.shadow_soft_size = radius
    o = bpy.data.objects.new(name, L)
    o.location = loc
    C_LIGHT.objects.link(o)
    LIGHTS.append(o)
    return o

def area_light(name, loc, rot, size, size_y, energy, color=(1.0, 0.6, 0.3)):
    L = bpy.data.lights.new(name, 'AREA')
    L.shape = 'RECTANGLE'
    L.size, L.size_y = size, size_y
    L.energy = energy
    L.color = color
    o = bpy.data.objects.new(name, L)
    o.location = loc
    o.rotation_euler = rot
    o.visible_camera = False
    C_LIGHT.objects.link(o)
    return o

# ------------------------------------------------------------------------------------------------ ground: setts, kerbs, flags
log('ground')
FRONT_X = 5.6           # building faces either side of the street
KERB_X = 3.45           # road edge
PAVE_Z = 0.13           # pavement top above the setts' tops
END_Y = 33.5            # face of the tenements closing the street
SIDE_Y0, SIDE_Y1 = 25.0, 31.35   # the side street (a wynd) going off to the right

base = plane('under ground', -40, 60, -20, 80, -0.16, C_GROUND)
store.use_material(base, 'SURFACE • mud_forest')

road = plane('road', -KERB_X, KERB_X, -9.0, SIDE_Y1, 0.0, C_GROUND)
setts = lay_cobbles.lay_setts(road, seed=3, missing=0.012)
road2 = plane('wynd road', KERB_X, 45.0, SIDE_Y0 + 2.15, SIDE_Y1, 0.0, C_GROUND)
setts2 = lay_cobbles.lay_setts(road2, seed=5, missing=0.01)
TOP = setts['top_height']
log('setts laid, top %.3f' % TOP)

def pave(name, x0, x1, y0, y1, seed):
    p = plane(name, x0, x1, y0, y1, PAVE_Z, C_GROUND)
    lay_cobbles.lay_flags(p, seed=seed)
    return p

pave('pavement right', KERB_X + 0.3, FRONT_X, -9.0, SIDE_Y0, 11)
pave('pavement wynd corner', KERB_X + 0.3, 45.0, SIDE_Y0, SIDE_Y0 + 1.85, 12)
pave('pavement left', -FRONT_X, -KERB_X - 0.3, -9.0, SIDE_Y1 + 0.3, 13)
pave('pavement end', -FRONT_X - 9, 45.0, SIDE_Y1 + 0.3, END_Y, 14)
log('flags laid')

def kerb_run(p0, p1, seed):
    r = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    t = 0.0
    while t < L - 0.05:
        seg = min(r.uniform(0.85, 1.25), L - t)
        c = p0 + d.normalized() * (t + seg / 2)
        dz = r.uniform(-0.012, 0.006)
        KERB.box(Matrix(), (c.x, c.y, PAVE_Z - 0.16 + dz), (seg - 0.012, 0.30, 0.32), rot_z=ang + r.uniform(-0.006, 0.006))
        t += seg

kerb_run((KERB_X + 0.15, -9.0), (KERB_X + 0.15, SIDE_Y0 + 2.0), 1)
kerb_run((KERB_X + 0.15, SIDE_Y0 + 2.0), (45.0, SIDE_Y0 + 2.0), 2)
kerb_run((-KERB_X - 0.15, -9.0), (-KERB_X - 0.15, SIDE_Y1 + 0.15), 3)
kerb_run((-KERB_X - 0.3, SIDE_Y1 + 0.15), (45.0, SIDE_Y1 + 0.15), 4)

# a cast-iron drain grate in the right-hand gutter, near the eye
gx, gy = KERB_X - 0.30, 3.1
RUST.box(Matrix(), (gx, gy, TOP - 0.008), (0.50, 0.74, 0.04))
for i in range(9):
    IRON.box(Matrix(), (gx, gy - 0.32 + i * 0.08, TOP + 0.016), (0.44, 0.034, 0.024))
IRON.box(Matrix(), (gx, gy, TOP + 0.016), (0.03, 0.68, 0.024))
DARK.box(Matrix(), (gx, gy, TOP - 0.03), (0.44, 0.68, 0.02))

# a cast-iron sewer cover in the road near the eye: a rim, rings and a cross of ribs, rusted, worn bright on top
mx, my = 2.0, 1.9
RUST.cyl(Matrix(), (mx, my, TOP - 0.03), (mx, my, TOP + 0.004), 0.36, segs=28)
for rr in (0.35, 0.25, 0.15):
    IRON.cyl(Matrix(), (mx, my, TOP + 0.004), (mx, my, TOP + 0.016), rr, segs=28, r2=rr)
    RUST.cyl(Matrix(), (mx, my, TOP + 0.005), (mx, my, TOP + 0.018), rr - 0.03, segs=28, r2=rr - 0.03)
for k in range(6):
    a = k * math.pi / 3
    IRON.box(Matrix(), (mx + math.cos(a) * 0.17, my + math.sin(a) * 0.17, TOP + 0.02), (0.34, 0.03, 0.016), rot_z=a)
DARK.box(Matrix(), (mx, my, TOP - 0.035), (0.8, 0.8, 0.01))

# ------------------------------------------------------------------------------------------------ buildings
log('buildings')
STOREY0, STOREY = 3.6, 3.0
DEPTH = 9.0

class Building:
    def __init__(self, name, side, a, b, storeys, ground, seed, rubble=False, lit=(), extra_sides=(), shop_glass=None,
                 attic=0.6, pitch=36, blind_sides=False):
        self.name, self.side, self.a, self.b = name, side, a, b
        self.storeys, self.ground, self.seed, self.rubble = storeys, ground, seed, rubble
        self.lit, self.extra_sides, self.shop_glass, self.pitch = lit, extra_sides, shop_glass, pitch
        self.blind_sides = blind_sides
        self.dormers = DORMERS.get(name, ())
        self.w = b - a
        self.h = STOREY0 + STOREY * (storeys - 1) + attic
        if side == 'L':
            loc, turn = (-FRONT_X - DEPTH / 2, (a + b) / 2, PAVE_Z), 90
        elif side == 'R':
            loc, turn = (FRONT_X + DEPTH / 2, (a + b) / 2, PAVE_Z), -90
        else:
            loc, turn = ((a + b) / 2, END_Y + DEPTH / 2, PAVE_Z), 0
        self.obj = box_object(name, self.w, DEPTH, self.h, loc, turn, C_BUILD)
        self.M = self.obj.matrix_world.copy()
        self.windows = []     # (floor, bay, u, z, w, h)
        self.fill = not any(item[0] == 'close' for item in ground)
        self.closes = []

    def front(self, u, out, z):
        """local point on the front: u from the left end, out from the wall face, z from the foot"""
        return (u - self.w / 2, -DEPTH / 2 - out, z)

    def world(self, u, out, z):
        return self.M @ Vector(self.front(u, out, z))

    def openings(self):
        ops = []
        bays = max(2, int(round(self.w / 2.25)))
        self.bays = bays
        step = self.w / bays
        self.step = step
        for k in range(1, self.storeys):
            z = STOREY0 + STOREY * (k - 1) + 0.85
            hh = 1.62 if k < self.storeys - 1 else 1.38
            for i in range(bays):
                u = (i + 0.5) * step
                ops.append(('front', 'window', u - 0.48, z, 0.96, hh))
                self.windows.append((k, i, u, z, 0.96, hh))
        # ground floor
        self.doors, self.shops = [], []
        for item in self.ground:
            kind = item[0]
            if kind == 'door':
                u = (item[1] + 0.5) * step
                ops.append(('front', 'door', u - 0.5, 0.0, 1.0, 2.35))
                ops.append(('front', 'window', u - 0.45, 2.78, 0.9, 0.42))     # fanlight
                self.doors.append(u)
            elif kind == 'close':
                u = (item[1] + 0.5) * step
                ops.append(('front', 'door', u - 0.65, 0.0, 1.3, 2.75))
                self.closes.append(u)
            elif kind == 'window':
                u = (item[1] + 0.5) * step
                ops.append(('front', 'window', u - 0.48, 0.95, 0.96, 1.7))
                self.windows.append((0, item[1], u, 0.95, 0.96, 1.7))
            elif kind == 'shop':
                u0, u1, door_side = item[1], item[2], item[3]    # window from u0 to u1 (metres), shop door beside it
                ops.append(('front', 'window', u0, 0.72, u1 - u0, 1.95))
                du = u1 + 0.35 if door_side == 'right' else u0 - 1.35
                ops.append(('front', 'door', du, 0.0, 1.0, 2.55))
                self.shops.append((u0, u1, du))
        return ops

    def build(self):
        ops = self.openings()
        sides = ['front'] + list(self.extra_sides)
        extra_ops = []
        for s in self.extra_sides:
            # a side face: plain windows, two per floor (a blind gable above a lower neighbour has none)
            if self.blind_sides:
                continue
            for k in range(1, self.storeys):
                z = STOREY0 + STOREY * (k - 1) + 0.85
                for u in (2.2, 5.6):
                    extra_ops.append((s, 'window', u, z, 0.96, 1.5))
        if self.rubble:
            self.stone = lay_rubble.lay(self.obj, sides=sides, openings=ops + extra_ops, seed=self.seed,
                                        collection=C_BUILD, relief=0.07,
                                        dressing_material='STONE • worn honey-grey architectural dressings')
            self.relief = 0.07
        else:
            self.stone = lay_stone.lay(self.obj, openings=ops + extra_ops, seed=self.seed, sides=sides,
                                       collection=C_BUILD, fill=self.fill)
            self.relief = 0.20
        self.details()

    def details(self):
        M, w, h, r = self.M, self.w, self.h, self.relief
        glass_out = (r - 0.10 + 0.015 + 0.006) if not self.rubble else 0.015
        # ---- roof with eaves overhanging the front, fascia, gutter, rafter feet
        ov = 0.42 + r
        p = math.radians(self.pitch)
        y_front = -DEPTH / 2 - ov
        ridge_y = 0.0
        ridge_z = h + (DEPTH / 2 + ov) * math.tan(p) * 0.92
        ends = (-w / 2 - (0.3 if self.side == 'R' and self is BLD.get('R4') else 0.0), w / 2)
        x0, x1 = ends
        bm = SLATE.bm
        vs = [bm.verts.new(M @ Vector(v)) for v in (
            (x0, y_front, h - 0.04), (x1, y_front, h - 0.04), (x1, ridge_y, ridge_z), (x0, ridge_y, ridge_z),
            (x0, DEPTH / 2 + ov, h - 0.04), (x1, DEPTH / 2 + ov, h - 0.04))]
        bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
        bm.faces.new((vs[3], vs[2], vs[5], vs[4]))
        gb = STACK.bm
        gv = [gb.verts.new(M @ Vector(v)) for v in (
            (x0, y_front, h - 0.04), (x0, ridge_y, ridge_z), (x0, DEPTH / 2 + ov, h - 0.04),
            (x1, y_front, h - 0.04), (x1, ridge_y, ridge_z), (x1, DEPTH / 2 + ov, h - 0.04))]
        gb.faces.new((gv[0], gv[1], gv[2]))
        gb.faces.new((gv[3], gv[5], gv[4]))
        # soffit under the overhang
        WOOD.box(M, ((x0 + x1) / 2, -DEPTH / 2 - ov / 2, h - 0.07), (x1 - x0, ov, 0.04))
        # fascia board at the eaves edge
        WOOD.box(M, ((x0 + x1) / 2, y_front + 0.02, h - 0.15), (x1 - x0, 0.035, 0.26))
        # rafter feet / brackets under the soffit
        n = int((x1 - x0) / 0.62)
        for i in range(n):
            xx = x0 + 0.31 + i * (x1 - x0 - 0.62) / max(1, n - 1)
            WOOD.box(M, (xx, -DEPTH / 2 - ov / 2 + 0.02, h - 0.15), (0.075, ov - 0.06, 0.13))
        # cast-iron gutter and its brackets
        IRON.cyl(M, (x0, y_front - 0.07, h - 0.17), (x1, y_front - 0.07, h - 0.17), 0.075, segs=10)
        # ---- dormers on the front slope (garret rooms), one of them lit
        for (du_, lit_d) in self.dormers:
            yf = -DEPTH / 2 + 0.35
            cx = du_ - w / 2
            STONE_D.box(M, (cx, yf + 1.3, h + 0.7), (1.45, 2.6, 1.6))
            dz = h + 1.5
            rv = [SLATE.bm.verts.new(M @ Vector(v)) for v in (
                (cx - 0.9, yf - 0.25, dz), (cx + 0.9, yf - 0.25, dz), (cx, yf - 0.25, dz + 0.75),
                (cx - 0.9, yf + 2.8, dz), (cx + 0.9, yf + 2.8, dz), (cx, yf + 2.8, dz + 0.75))]
            SLATE.bm.faces.new((rv[0], rv[2], rv[5], rv[3]))
            SLATE.bm.faces.new((rv[2], rv[1], rv[4], rv[5]))
            STACK.bm.faces.new([STACK.bm.verts.new(M @ Vector(v)) for v in ((cx - 0.75, yf - 0.02, dz), (cx + 0.75, yf - 0.02, dz), (cx, yf - 0.02, dz + 0.62))])
            WOOD.box(M, (cx, yf - 0.24, dz - 0.02), (1.85, 0.05, 0.12))
            gl = GLOW if lit_d else NAVY
            gl.box(M, (cx, yf - 0.02, h + 0.72), (0.72, 0.006, 0.95))
            for sx in (-1, 1):
                WOOD.box(M, (cx + sx * 0.39, yf - 0.05, h + 0.72), (0.07, 0.07, 1.05))
            for sz in (h + 0.22, h + 0.72, h + 1.22):
                WOOD.box(M, (cx, yf - 0.05, sz), (0.84, 0.07, 0.06))
            WOOD.box(M, (cx, yf - 0.045, h + 0.72), (0.03, 0.05, 0.95))
            STONE_D.box(M, (cx, yf - 0.1, h + 0.16), (1.0, 0.22, 0.08))
            if lit_d:
                point_light('dormer light ' + self.name, M @ Vector((cx, yf - 0.6, h + 0.7)), 20)
        # ---- chimney stack on the left party wall (and the right one for the end of a row)
        stack_x = [x0 + 0.05]
        if self.name in ('R4', 'L5', 'E2', 'E3', 'E4'):
            stack_x.append(x1 - 0.45)
        for sx in stack_x:
            top = ridge_z + 1.35 + rng.uniform(-0.2, 0.3)
            STACK.box(M, (sx + 0.2, 0.0, (ridge_z - 1.0 + top) / 2), (0.85, 2.6, top - ridge_z + 1.0))
            STONE_D.box(M, (sx + 0.2, 0.0, top + 0.06), (1.0, 2.75, 0.12))
            STONE_D.box(M, (sx + 0.2, 0.0, top - 0.35), (0.95, 2.7, 0.08))
            for j in range(5):
                hh = rng.uniform(0.45, 0.75)
                yy = -1.0 + j * 0.5
                CLAY.cyl(M, (sx + 0.2, yy, top + 0.1), (sx + 0.2 + rng.uniform(-0.04, 0.04), yy, top + 0.1 + hh), 0.14, segs=10, r2=0.11)
        # ---- downpipe at the left end of the front
        pu = 0.3
        out = r + 0.12
        IRON.cyl(M, self.front(pu, out, -0.02), self.front(pu, out, h - 0.5), 0.05, segs=8)
        IRON.cyl(M, self.front(pu, out, h - 0.5), self.front(pu, ov + 0.07, h - 0.17), 0.05, segs=8)   # swan neck
        IRON.cyl(M, self.front(pu, out, 0.25), self.front(pu, out + 0.22, 0.03), 0.055, segs=8)         # shoe
        z = 1.6
        while z < h - 0.8:
            IRON.cyl(M, self.front(pu, out, z), self.front(pu, out, z + 0.07), 0.068, segs=8)
            IRON.box(M, self.front(pu, (r + out) / 2, z + 0.035), (0.05, out - r + 0.02, 0.04))
            z += 1.85
        # ---- doorsteps
        for u in self.doors:
            STONE_D.box(M, self.front(u, 0.2 + r * 0.5, 0.04), (1.35, 0.42 + r, 0.17))
        # ---- shop fronts: fascia board (blank), pilasters, consoles, stall riser, step
        for (u0, u1, du) in self.shops:
            left = min(u0, du) - 0.3
            right = max(u1, du + 1.0) + 0.3
            WOOD.box(M, self.front((left + right) / 2, r + 0.14, 3.17), (right - left, 0.09, 0.5))
            WOOD.box(M, self.front((left + right) / 2, r + 0.19, 3.47), (right - left + 0.25, 0.2, 0.1))
            WOOD.box(M, self.front((left + right) / 2, r + 0.17, 2.89), (right - left + 0.1, 0.14, 0.07))
            for uu in (left, right):
                WOOD.box(M, self.front(uu, r + 0.1, 1.45), (0.3, 0.16, 2.9))
                WOOD.box(M, self.front(uu, r + 0.2, 3.15), (0.22, 0.2, 0.55))
            WOOD.box(M, self.front((u0 + u1) / 2, r + 0.06, 0.33), (u1 - u0 + 0.1, 0.07, 0.62))
            STONE_D.box(M, self.front(du + 0.5, 0.2 + r * 0.5, 0.04), (1.3, 0.4 + r, 0.15))
            if self.shop_glass == 'lit':
                HERO.box(M, self.front((u0 + u1) / 2, glass_out, 0.72 + 1.95 / 2), (u1 - u0 - 0.02, 0.004, 1.93))
                GLOW.box(M, self.front(du + 0.5, 0.08, 1.95), (0.5, 0.004, 0.5))
                # shelves of jars and tins, and a counter, dark against the lamp-lit back of the shop
                gr = random.Random(self.seed)
                for sz in (1.12, 1.62, 2.12):
                    GOODS.box(M, self.front((u0 + u1) / 2, glass_out + 0.006, sz), (u1 - u0 - 0.1, 0.004, 0.035))
                    uu = u0 + 0.12
                    while uu < u1 - 0.2:
                        gw = gr.uniform(0.07, 0.16)
                        gh = gr.uniform(0.12, 0.3)
                        if gr.random() < 0.8:
                            GOODS.box(M, self.front(uu + gw / 2, glass_out + 0.006, sz + 0.0175 + gh / 2), (gw, 0.004, gh))
                        uu += gw + gr.uniform(0.02, 0.09)
                GOODS.box(M, self.front((u0 + u1) / 2 - 0.3, glass_out + 0.006, 0.72 + 0.28), (1.4, 0.004, 0.56))
            elif self.shop_glass == 'dim':
                DIM.box(M, self.front((u0 + u1) / 2, glass_out, 0.72 + 1.95 / 2), (u1 - u0 - 0.02, 0.004, 1.93))
        # ---- sashes for the rubble front's windows (its openings are dark panels)
        if self.rubble:
            for (k, i, u, z, ww, hh) in self.windows:
                so = 0.035
                for sx in (-1, 1):
                    WOOD.box(M, self.front(u + sx * (ww / 2 - 0.03), so, z + hh / 2), (0.06, 0.05, hh))
                for sz in (z + 0.03, z + hh - 0.03, z + hh * 0.52):
                    WOOD.box(M, self.front(u, so + 0.005, sz), (ww, 0.05, 0.055))
                WOOD.box(M, self.front(u, so + 0.01, z + hh / 2), (0.03, 0.04, hh))
                for sz in (z + hh * 0.26, z + hh * 0.77):
                    WOOD.box(M, self.front(u, so + 0.01, sz), (ww, 0.035, 0.022))
        # ---- a front built without fill: glass and door leaves of our own, and the close cut through
        if not self.fill and not self.rubble:
            litset = set(self.lit)
            for (k, i, u, z, ww, hh) in self.windows:
                if (k, i) not in litset:
                    NAVY.box(M, self.front(u, 0.115, z + hh / 2), (ww + 0.02, 0.006, hh + 0.02))
            for u in self.doors:
                NAVY.box(M, self.front(u, 0.115, 2.78 + 0.21), (0.92, 0.006, 0.44))
            for u in list(self.doors) + [du + 0.5 for (_, _, du) in self.shops]:
                WOOD.box(M, self.front(u, 0.06, 1.18 if u in self.doors else 1.28), (1.02, 0.04, 2.36 if u in self.doors else 2.56))
                for rz in (0.2, 1.05, 2.2):
                    WOOD.box(M, self.front(u, 0.09, rz), (0.8, 0.03, 0.14))
        for u in self.closes:
            cut = box_object(self.name + ' close cutter', 1.3, 7.0, 2.75, (0, 0, 0), 0, C_DETAIL)
            cut.matrix_world = M @ Matrix.Translation(Vector(self.front(u, -3.45, -0.06)))
            cut.hide_render = True
            cut.display_type = 'WIRE'
            mod = self.obj.modifiers.new('close', 'BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = cut
            mod.solver = 'EXACT'
            FLOOR.box(M, self.front(u, -3.4, -0.01), (1.32, 7.0, 0.02))
            point_light('close lamp ' + self.name, self.world(u - 0.4, -2.4, 2.35), 70, color=(1.0, 0.6, 0.3), radius=0.08)
            point_light('close back court ' + self.name, self.world(u, -6.2, 2.0), 45, color=(0.55, 0.68, 1.0), radius=0.5)
            IRON.box(M, self.front(u - 0.55, -2.4, 2.35), (0.1, 0.12, 0.1))
        # ---- a stair lit behind its door: the fanlight glows and lights the step
        if self.name in LIT_STAIRS:
            for u in self.doors:
                GLOW.box(M, self.front(u, glass_out, 2.78 + 0.21), (0.86, 0.004, 0.40))
                point_light('stair fanlight ' + self.name, self.world(u, 0.6, 2.62), 18, color=(1.0, 0.62, 0.32), radius=0.2)
                # the door's upper panels are glazed: the stair's gas shows through and lights the step
                for sx in (-0.2, 0.2):
                    GLOW.box(M, self.front(u + sx, 0.084, 1.72), (0.3, 0.004, 0.62))
                point_light('stair door glass ' + self.name, self.world(u, 0.75, 1.45), 34, color=(1.0, 0.62, 0.32), radius=0.25)
        # ---- lit windows: glow over the glass and a small warm light outside it
        for (k, i) in self.lit:
            for (kk, ii, u, z, ww, hh) in self.windows:
                if kk == k and ii == i:
                    GLOW.box(M, self.front(u, glass_out, z + hh / 2), (ww - 0.02, 0.004, hh - 0.02))
                    # a curtain half drawn on one side, lit through from the room
                    side = 1 if (k + i + self.seed) % 2 else -1
                    CURTAIN.box(M, self.front(u + side * ww * 0.31, glass_out + 0.003, z + hh / 2 - 0.02), (ww * 0.34, 0.003, hh - 0.06))
                    point_light('window light %s %d %d' % (self.name, k, i), self.world(u, 0.55, z + hh * 0.45), 38)

LIT_STAIRS = ('R2',)
DORMERS = {'E2': ((3.3, False), (5.5, True)), 'E1': ((8.0, False),)}
BLD = {}
def building(*a, **kw):
    b = Building(*a, **kw)
    BLD[b.name] = b
    return b

building('L1', 'L', -9.0, 2.0, 4, [('door', 1), ('window', 0), ('window', 2), ('window', 3)], seed=11)
building('L2', 'L', 2.0, 9.0, 4, [('window', 0), ('door', 1), ('window', 2)], seed=12, attic=0.9)
building('L3', 'L', 9.0, 16.5, 4, [('door', 0), ('window', 1), ('window', 2)], seed=13, lit=((1, 2),))
building('L4', 'L', 16.5, 24.5, 4, [('shop', 2.6, 5.4, 'right'), ('door', 0)], seed=14, shop_glass='dim', lit=((2, 0),))
building('L5', 'L', 24.5, 33.5, 5, [('door', 3), ('window', 0), ('window', 1), ('window', 2)], seed=15, rubble=True, lit=((1, 1),),
         extra_sides=('left',), blind_sides=True)
building('R1', 'R', -9.0, 1.0, 4, [('door', 2), ('window', 0), ('window', 1), ('window', 3)], seed=21)
building('R2', 'R', 1.0, 8.5, 3, [('door', 0), ('window', 1), ('window', 2)], seed=22, attic=1.0)
building('R3', 'R', 8.5, 16.5, 4, [('door', 0), ('shop', 3.0, 5.8, 'right')], seed=23, shop_glass='dim', lit=((3, 2),))
building('R4', 'R', 16.5, 25.0, 4, [('window', 0), ('door', 1), ('window', 2), ('window', 3)], seed=24,
         extra_sides=('left',), lit=((2, 1),))
building('E1', 'E', -14.0, -2.4, 4, [('window', 1), ('door', 2), ('window', 3), ('window', 4)], seed=31, lit=((3, 3),))
building('E2', 'E', -2.4, 6.4, 4, [('close', 0), ('shop', 2.55, 5.45, 'right')], seed=32, shop_glass='lit', lit=((2, 1),))
building('E3', 'E', 6.4, 20.0, 3, [('window', 0), ('door', 1), ('window', 2), ('window', 3), ('window', 4), ('door', 5)],
         seed=33, lit=((1, 4),), attic=0.9)
building('E4', 'E', 20.0, 40.0, 4, [('window', i) for i in range(9)], seed=34, lit=((1, 3), (2, 6)))

for b in BLD.values():
    b.build()
    log('built %s' % b.name)

# ------------------------------------------------------------------------------------------------ lamps and lights
log('lamps')
def lamp(x, y, power=150, turn=0, seed=0, lit=True):
    root = store.add_part('gas_lamp', location=(x, y, PAVE_Z), turn=turn, seed=seed, lit=lit)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith('gas_lamp light') and o.get('_set') is None:
            o.data.energy = power
            o['_set'] = 1
    return root

lamp(-KERB_X - 0.55, 16.0, power=95, seed=1)
lamp(KERB_X + 0.5, 4.6, seed=6, lit=False)                # the near lamp on the right pavement: not lit yet
point_light('unseen lamp behind the frame', (-KERB_X - 0.55, 2.6, 3.08), 55, radius=0.15)
lamp(KERB_X + 0.55, 19.5, power=90, seed=2)
lamp(-KERB_X - 0.55, 27.0, power=80, seed=3)
lamp(-0.2, SIDE_Y1 + 0.85, power=140, seed=4)           # the hero lamp before the lit shop
lamp(13.0, SIDE_Y1 + 0.85, power=110, seed=5)           # down the wynd

# the hero shop window throws its light out over the pavement and the wet setts
E2 = BLD['E2']
hero_u = (2.55 + 5.45) / 2
hp = E2.world(hero_u, 0.75, 1.65)
area_light('hero shop light', hp, (math.radians(90), 0, 0), 2.8, 1.6, 220, color=(1.0, 0.58, 0.28))
dp = E2.world(5.45 + 0.35 + 0.5, 0.6, 1.4)
point_light('hero shop door light', dp, 40)
# the dairy's dim window spills a little
L4 = BLD['L4']
point_light('dairy window light', L4.world(4.0, 0.7, 1.5), 22, color=(1.0, 0.66, 0.38), radius=0.4)
R3b = BLD['R3']
point_light('grocer window light', R3b.world(4.4, 0.7, 1.5), 24, color=(1.0, 0.66, 0.38), radius=0.4)

# ------------------------------------------------------------------------------------------------ what people left
log('props')
def part(name, x, y, z=PAVE_Z, turn=0, seed=0, **kw):
    return store.add_part(name, location=(x, y, z), turn=turn, seed=seed, **kw)

# the coal merchant's cart, unhitched at the left kerb for the night, shafts on props
part('coal_cart', -KERB_X + 1.15, 17.2, z=TOP, turn=-4, seed=3)
# the grocer's barrel and crates by his door (R3, right side)
R3 = BLD['R3']
gp = R3.world(3.0 - 0.75, 0.55, 0.0)
part('barrel', gp.x, gp.y, turn=-90, seed=1)
gp = R3.world(5.8 + 0.35 + 1.0 + 0.6, 0.45, 0.0)
part('crate', gp.x, gp.y, turn=-88, seed=2)
part('crate', gp.x + 0.02, gp.y + 0.05, z=PAVE_Z + 0.38, turn=-95, seed=3)
# the stair door nearest the eye (R2): a besom and a bucket of mop water left beside the scrubbed step,
# the coal scuttle on the step, an umbrella against the wall
R2 = BLD['R2']
bp = R2.world(R2.doors[0] + 0.95, 0.47, 0.0)
part('besom_and_bucket', bp.x, bp.y, turn=-90, seed=2)
sp = R2.world(R2.doors[0] - 0.40, 0.42, 0.125)
part('coal_scuttle', sp.x, sp.y, z=PAVE_Z + 0.125, turn=-70, seed=1)
up = R2.world(0.5, 0.36, 0.0)
part('umbrella', up.x, up.y, turn=-90, seed=1)
# the dairyman's churns by his door (L4) and a crate of bottles
L4 = BLD['L4']
du = L4.shops[0][2]
cp = L4.world(du + 1.35, 0.42, 0.0)
part('milk_churn', cp.x, cp.y, turn=90, seed=1)
cp = L4.world(du + 1.9, 0.45, 0.0)
part('milk_churn', cp.x, cp.y, turn=80, seed=2, lid=False)
cp = L4.world(2.6 - 0.75, 0.45, 0.0)
part('crate', cp.x, cp.y, turn=90, seed=5, size=(0.6, 0.42, 0.32))
# ------------------------------------------------------------------------------------------------ water
log('puddles')
LEVEL = TOP + 0.002
puddle.make((1.7, 4.0, LEVEL), size=(3.3, 2.0), turn=14, level=LEVEL, seed=2)           # near: mirrors the sky and both lamps
puddle.make((0.5, 9.2, LEVEL), size=(2.6, 1.2), turn=58, level=LEVEL, seed=4)            # mirrors the far lamps
puddle.make((KERB_X - 0.27, 12.8, LEVEL), size=(4.6, 0.42), turn=90, level=LEVEL - 0.003, seed=6, raggedness=1.4)
puddle.make((1.6, 15.8, LEVEL), size=(3.4, 1.05), turn=88, level=LEVEL, seed=8)          # mirrors the lit shop
puddle.make((2.3, 23.5, LEVEL), size=(2.2, 0.8), turn=80, level=LEVEL, seed=9)
puddle.make((-KERB_X + 0.28, 20.5, LEVEL), size=(4.0, 0.4), turn=90, level=LEVEL - 0.003, seed=10, raggedness=1.4)
puddle.make((0.4, 28.7, LEVEL), size=(2.6, 0.8), turn=95, level=LEVEL, seed=12)

# weeds in the joints by the kerbs and in the gutter, near the eye
wr = random.Random(7)
def tuft(x, y, z, n=9, hgt=0.12):
    for k in range(n):
        a = wr.uniform(0, 2 * math.pi)
        lean = wr.uniform(0.1, 0.6)
        hh = hgt * wr.uniform(0.5, 1.2)
        top = (x + math.cos(a) * lean * hh, y + math.sin(a) * lean * hh, z + hh)
        WEEDS.cyl(Matrix(), (x + wr.uniform(-0.02, 0.02), y + wr.uniform(-0.02, 0.02), z - 0.01), top, 0.006, segs=4, r2=0.0005)
for (x, y) in ((KERB_X - 0.06, 2.6), (KERB_X - 0.05, 3.4), (KERB_X - 0.08, 6.4), (KERB_X - 0.04, 12.0), (-KERB_X + 0.06, 6.0),
               (-KERB_X + 0.05, 11.0), (2.75, 1.4), (-0.4, 2.2), (2.2, 7.4), (1.55, 0.9), (1.05, 2.6), (2.4, 3.6),
               (0.4, 6.8), (-1.2, 12.5)):
    tuft(x, y, TOP, n=wr.randint(9, 15), hgt=wr.uniform(0.14, 0.24))
for (x, y) in ((FRONT_X - 0.25, 10.4), (FRONT_X - 0.22, 17.2), (-FRONT_X + 0.25, 18.4), (-FRONT_X + 0.2, 23.6)):
    tuft(x, y, PAVE_Z, n=8, hgt=0.14)

# ------------------------------------------------------------------------------------------------ wear on the fronts
log('stains')
def wall_stains(b, seed):
    side = 'front'
    off = b.relief + 0.012
    stain.on_wall(b.obj, side, 0.0, b.w, b.h - 2.2, b.h, kind='soot', strong_at='top', strength=1.4, seed=seed, offset=off,
                  collection=C_DETAIL)
    stain.on_wall(b.obj, side, 0.0, b.w, 0.0, 1.3, kind='damp', strong_at='bottom', strength=1.3, seed=seed + 1, offset=off,
                  collection=C_DETAIL)
    # soot over the upper windows and a rust run under the downpipe's joints
    for (k, i, u, z, ww, hh) in b.windows:
        if k >= 1 and (i + k + seed) % 3 == 0:
            stain.on_wall(b.obj, side, u - 0.7, u + 0.7, z + hh + 0.1, z + hh + 1.1, kind='soot', strong_at='bottom',
                          strength=1.2, seed=seed + k * 7 + i, offset=off + 0.004, collection=C_DETAIL)
    stain.on_wall(b.obj, side, 0.05, 0.75, 0.0, b.h - 0.6, kind='rust', strong_at='top', strength=0.9, seed=seed + 3,
                  offset=off + 0.006, collection=C_DETAIL)

for j, b in enumerate(BLD.values()):
    try:
        wall_stains(b, 100 + j * 10)
    except Exception as e:
        log('stain failed on %s: %s' % (b.name, e))

# coal dust under the cart, mud by the kerbs
stain.on_ground((-KERB_X + 1.2, 17.4, TOP + 0.004), size=(1.4, 2.6), kind='coal dust', turn=0, strength=0.35, seed=3,
                collection=C_DETAIL)

# ------------------------------------------------------------------------------------------------ make the details
for acc in (WOOD, IRON, STONE_D, SLATE, STACK, CLAY, GLOW, DIM, RUST, DARK, KERB, HERO, GOODS, WEEDS, NAVY, FLOOR, CURTAIN):
    acc.make()

# ------------------------------------------------------------------------------------------------ the second pass: dressing
# ==================================================================================================================
# The second pass: dressing the near ground of the town street.
# Run inside render_final.py after the first builder's details are made (so BLD, TOP, PAVE_Z, KERB_X, Acc ... exist).
# Every thing here belongs to someone (see materials.md): the stair's ash bins and the road men's spare setts at the
# kerb by the near lamp post, the relaid patch round the sewer cover, the gutter's silt, straw, leaves and cinders.
# ==================================================================================================================
log('dressing: the second pass')
LANTERN_W = float(os.environ.get('LANTERN_W', '16'))
C_DRESS = coll('dressing')
dr = random.Random(5502)

def dress_obj(name, bm, material, collection=C_DRESS, smooth=False):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = smooth
    if isinstance(material, str):
        store.use_material(obj, material)
    else:
        mesh.materials.append(material)
    return obj

def node_mat(name, base, rough, metal=0.0, noise_scale=0.0, noise_amt=0.0, rough_var=0.0, bump=0.0, random_tint=0.0, island=False):
    """A plain material with optional noise in its colour and roughness, and a per-object random shade."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (base[0], base[1], base[2], 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    tc = nt.nodes.new('ShaderNodeTexCoord')
    if noise_scale > 0:
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = noise_scale
        nz.inputs['Detail'].default_value = 8.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.3
        mr.inputs['From Max'].default_value = 0.7
        mr.inputs['To Min'].default_value = 1.0 - noise_amt
        mr.inputs['To Max'].default_value = 1.0 + noise_amt
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        mix.inputs[6].default_value = (base[0], base[1], base[2], 1.0)
        nt.links.new(mr.outputs[0], mix.inputs[7])
        last = mix.outputs[2]
        if random_tint > 0:
            oi = nt.nodes.new('ShaderNodeObjectInfo')
            gi = nt.nodes.new('ShaderNodeNewGeometry')
            mr2 = nt.nodes.new('ShaderNodeMapRange')
            mr2.inputs['To Min'].default_value = 1.0 - random_tint
            mr2.inputs['To Max'].default_value = 1.0 + random_tint
            nt.links.new(gi.outputs['Random Per Island'] if island else oi.outputs['Random'], mr2.inputs['Value'])
            mix2 = nt.nodes.new('ShaderNodeMix')
            mix2.data_type = 'RGBA'
            mix2.blend_type = 'MULTIPLY'
            mix2.inputs['Factor'].default_value = 1.0
            nt.links.new(last, mix2.inputs[6])
            nt.links.new(mr2.outputs[0], mix2.inputs[7])
            last = mix2.outputs[2]
        nt.links.new(last, b.inputs['Base Color'])
        if rough_var > 0:
            mr3 = nt.nodes.new('ShaderNodeMapRange')
            mr3.inputs['To Min'].default_value = max(0.02, rough - rough_var)
            mr3.inputs['To Max'].default_value = min(1.0, rough + rough_var)
            nt.links.new(nz.outputs['Fac'], mr3.inputs['Value'])
            nt.links.new(mr3.outputs[0], b.inputs['Roughness'])
        if bump > 0:
            bp = nt.nodes.new('ShaderNodeBump')
            bp.inputs['Strength'].default_value = bump
            bp.inputs['Distance'].default_value = 0.01
            nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
            nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def ground_z(x, y, default):
    """The height of whatever is drawn at (x, y), found by a ray from above (setts, flags, kerbs)."""
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nor, idx, ob, mtx = scene.ray_cast(dg, Vector((x, y, 3.0)), Vector((0, 0, -1)))
    if hit and loc.z < 1.0:
        return loc.z
    return default

bpy.context.view_layer.update()

# ------------------------------------------------------------------------------------------------ materials of the dressing
M_GRANITE_NEW = node_mat('new granite setts', (0.068, 0.064, 0.061), 0.22, noise_scale=60.0, noise_amt=0.35, rough_var=0.12,
                         bump=0.25, random_tint=0.35, island=True)
M_PITCH = node_mat('pitch in the joints', (0.008, 0.007, 0.006), 0.04, noise_scale=12.0, noise_amt=0.3, rough_var=0.05)
M_ZINC = node_mat('galvanised iron, dull', (0.085, 0.087, 0.085), 0.66, metal=0.5, noise_scale=3.5, noise_amt=0.28,
                  rough_var=0.18, bump=0.15, random_tint=0.12)
M_ZINC_RUST = 'RUST • rain-aged iron'
M_ASH = node_mat('stove ash, wet', (0.10, 0.098, 0.092), 0.85, noise_scale=40.0, noise_amt=0.5, bump=0.4)
M_ASH_TOP = node_mat('stove ash, dry on top', (0.20, 0.195, 0.185), 0.9, noise_scale=30.0, noise_amt=0.45, bump=0.5)
M_CINDER = node_mat('clinker', (0.03, 0.028, 0.027), 0.55, noise_scale=80.0, noise_amt=0.6, bump=0.6, random_tint=0.4)
M_GRIT = node_mat('road grit, wet', (0.042, 0.035, 0.027), 0.5, noise_scale=45.0, noise_amt=0.7, rough_var=0.25, bump=0.5)
M_STRAW = node_mat('straw, trodden wet', (0.075, 0.052, 0.022), 0.45, noise_scale=30.0, noise_amt=0.5, random_tint=0.45)
M_LEAF_A = node_mat('fallen leaf, wet ochre', (0.17, 0.075, 0.022), 0.3, noise_scale=25.0, noise_amt=0.4, random_tint=0.5)
M_LEAF_B = node_mat('fallen leaf, wet brown', (0.05, 0.026, 0.012), 0.3, noise_scale=25.0, noise_amt=0.4, random_tint=0.5)
M_PAPER = node_mat('sodden newspaper', (0.085, 0.08, 0.07), 0.4, noise_scale=9.0, noise_amt=0.35, random_tint=0.1)

# ------------------------------------------------------------------------------------------------ the relaid patch round the sewer cover
# the road men lifted the setts round the cover (2.0, 1.9) and relaid them: new pale granite, black pitch in the joints
PATCH = (1.30, 2.78, 1.12, 2.72)          # x0, x1, y0, y1
COVER = (mx, my, 0.40)
setts_obj = bpy.data.objects.get('setts')
if setts_obj is not None:
    bm = bmesh.new()
    bm.from_mesh(setts_obj.data)
    kill = [v for v in bm.verts if PATCH[0] - 0.05 < v.co.x < PATCH[1] + 0.05 and PATCH[2] - 0.05 < v.co.y < PATCH[3] + 0.05]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(setts_obj.data)
    bm.free()
    setts_obj.data.update()
    log('patch: lifted %d old setts' % len(kill))

bm = bmesh.new()
y = PATCH[2]
row = 0
while y < PATCH[3] - 0.05:
    d = dr.uniform(0.13, 0.16)
    x = PATCH[0] + (0.0 if row % 2 == 0 else -0.13)
    while x < PATCH[1] - 0.04:
        w = dr.uniform(0.24, 0.31)
        x0, x1 = max(x, PATCH[0]), min(x + w, PATCH[1])
        if x1 - x0 > 0.08:
            cx, cy = (x0 + x1) / 2, y + d / 2
            if math.hypot(cx - COVER[0], cy - COVER[1]) > COVER[2] + 0.07:
                hz = dr.uniform(0.0, 0.012)          # a week old: still a little proud of the old setts
                S = Matrix.Diagonal((x1 - x0 - 0.018, d - 0.018, 0.13, 1.0))
                R = Matrix.Rotation(dr.uniform(-0.02, 0.02), 4, 'Z') @ Matrix.Rotation(dr.uniform(-0.012, 0.012), 4, 'X')
                bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx, cy, TOP + hz - 0.065)) @ R @ S)
        x += w
    y += d
    row += 1
patch_setts = dress_obj('relaid setts', bm, M_GRANITE_NEW)
bv = patch_setts.modifiers.new('arris', 'BEVEL')
bv.width = 0.009
bv.segments = 2
# each new sett its own shade: split into loose parts is costly; the noise and a world-position tint do it instead
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5,
                      matrix=Matrix.Translation(((PATCH[0] + PATCH[1]) / 2, (PATCH[2] + PATCH[3]) / 2, TOP - 0.009))
                      @ Matrix.Diagonal((PATCH[1] - PATCH[0] + 0.02, PATCH[3] - PATCH[2] + 0.02, 1.0, 1.0)))
dress_obj('pitch under the relaid setts', bm, M_PITCH)


# ------------------------------------------------------------------------------------------------ grit packed in the setts' joints
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5,
                      matrix=Matrix.Translation((0.0, 6.0, TOP - 0.034)) @ Matrix.Diagonal((2 * KERB_X, 15.0, 1.0, 1.0)))
dress_obj('grit in the joints', bm, M_GRIT)


def bin_mat(name):
    """Galvanised iron gone dull: grey zinc, streaks of rust and soot run down from the rim and the handles, rust at the foot."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (14.0, 14.0, 1.2)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    streak = nt.nodes.new('ShaderNodeTexNoise')
    streak.inputs['Scale'].default_value = 2.5
    streak.inputs['Detail'].default_value = 6.0
    nt.links.new(mp.outputs['Vector'], streak.inputs['Vector'])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    # strongest just under the rim (z near 1) and at the foot (z near 0)
    top = nt.nodes.new('ShaderNodeMapRange')
    top.inputs['From Min'].default_value = 0.35
    top.inputs['From Max'].default_value = 0.95
    nt.links.new(sep.outputs['Z'], top.inputs['Value'])
    foot = nt.nodes.new('ShaderNodeMapRange')
    foot.inputs['From Min'].default_value = 0.16
    foot.inputs['From Max'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], foot.inputs['Value'])
    sm = nt.nodes.new('ShaderNodeMapRange')
    sm.inputs['From Min'].default_value = 0.45
    sm.inputs['From Max'].default_value = 0.68
    nt.links.new(streak.outputs['Fac'], sm.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(top.outputs[0], mul.inputs[0])
    nt.links.new(sm.outputs[0], mul.inputs[1])
    mx_ = nt.nodes.new('ShaderNodeMath')
    mx_.operation = 'MAXIMUM'
    mx_.use_clamp = True
    nt.links.new(mul.outputs[0], mx_.inputs[0])
    nt.links.new(foot.outputs[0], mx_.inputs[1])
    blot = nt.nodes.new('ShaderNodeTexNoise')
    blot.inputs['Scale'].default_value = 5.0
    nt.links.new(tc.outputs['Object'], blot.inputs['Vector'])
    zinc = nt.nodes.new('ShaderNodeMix')
    zinc.data_type = 'RGBA'
    zinc.inputs['Factor'].default_value = 1.0
    nt.links.new(blot.outputs['Fac'], zinc.inputs['Factor'])
    zinc.inputs[6].default_value = (0.06, 0.062, 0.06, 1.0)
    zinc.inputs[7].default_value = (0.13, 0.135, 0.13, 1.0)
    col = nt.nodes.new('ShaderNodeMix')
    col.data_type = 'RGBA'
    nt.links.new(mx_.outputs[0], col.inputs['Factor'])
    nt.links.new(zinc.outputs[2], col.inputs[6])
    col.inputs[7].default_value = (0.075, 0.028, 0.010, 1.0)
    nt.links.new(col.outputs[2], b.inputs['Base Color'])
    met = nt.nodes.new('ShaderNodeMapRange')
    met.inputs['To Min'].default_value = 0.55
    met.inputs['To Max'].default_value = 0.0
    nt.links.new(mx_.outputs[0], met.inputs['Value'])
    nt.links.new(met.outputs[0], b.inputs['Metallic'])
    ro = nt.nodes.new('ShaderNodeMapRange')
    ro.inputs['To Min'].default_value = 0.55
    ro.inputs['To Max'].default_value = 0.85
    nt.links.new(mx_.outputs[0], ro.inputs['Value'])
    nt.links.new(ro.outputs[0], b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.2
    nt.links.new(blot.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
M_BIN = bin_mat('ash bin, galvanised, rust runs')

# ------------------------------------------------------------------------------------------------ the stair's ash bins at the kerb
def ash_bin(cx, cy, cz, turn, seed, lid_on=True, lid_tilt=0.0):
    r = random.Random(seed)
    H, R0, R1 = 0.64, 0.225, 0.245
    body = bmesh.new()
    bmesh.ops.create_cone(body, cap_ends=True, segments=36, radius1=R0, radius2=R1, depth=H,
                          matrix=Matrix.Translation((0, 0, H / 2)))
    # dents: push a few patches of the wall in
    dents = [(r.uniform(0, math.tau), r.uniform(0.12, 0.55), r.uniform(0.012, 0.03)) for _ in range(4)]
    for v in body.verts:
        a = math.atan2(v.co.y, v.co.x)
        rr = math.hypot(v.co.x, v.co.y)
        if rr < 0.1:
            continue
        push = 0.0
        for (da, dz, amt) in dents:
            dd = math.hypot((a - da + math.pi) % math.tau - math.pi, (v.co.z - dz) * 3.0)
            push += amt * math.exp(-(dd / 0.35) ** 2)
        k = (rr - push) / rr
        v.co.x *= k
        v.co.y *= k
    # the rolled ribs round the body and the rim
    for z in (0.03, 0.22, 0.42, H - 0.015):
        rz = R0 + (R1 - R0) * z / H
        bmesh.ops.create_cone(body, cap_ends=True, segments=36, radius1=rz + 0.009, radius2=rz + 0.009, depth=0.03,
                              matrix=Matrix.Translation((0, 0, z)))
    # drop handles at the sides
    for sgn in (-1, 1):
        for k in range(5):
            a0 = math.pi * k / 5
            a1 = math.pi * (k + 1) / 5
            p0 = Vector((sgn * (R1 + 0.035 * math.sin(a0) + 0.01), -0.07 * math.cos(a0), H - 0.12 - 0.03 * math.sin(a0)))
            p1 = Vector((sgn * (R1 + 0.035 * math.sin(a1) + 0.01), -0.07 * math.cos(a1), H - 0.12 - 0.03 * math.sin(a1)))
            dv = p1 - p0
            q = dv.normalized().to_track_quat('Z', 'Y')
            bmesh.ops.create_cone(body, cap_ends=True, segments=6, radius1=0.007, radius2=0.007, depth=dv.length,
                                  matrix=Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4())
        bmesh.ops.create_cube(body, size=1.0, matrix=Matrix.Translation((sgn * (R1 + 0.012), 0, H - 0.12))
                              @ Matrix.Diagonal((0.02, 0.17, 0.04, 1.0)))
    M = Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(math.radians(turn), 4, 'Z') @ \
        Matrix.Rotation(r.uniform(-0.03, 0.03), 4, 'X')
    bmesh.ops.transform(body, matrix=M, verts=body.verts)
    ob = dress_obj('ash bin %d' % seed, body, M_BIN, smooth=True)
    ob.modifiers.new('edges', 'EDGE_SPLIT').split_angle = math.radians(50)
    # rust ring at the foot where it stands in the wet
    rb = bmesh.new()
    bmesh.ops.create_cone(rb, cap_ends=False, segments=36, radius1=R0 + 0.011, radius2=R0 + 0.006, depth=0.07,
                          matrix=M @ Matrix.Translation((0, 0, 0.035)))
    dress_obj('ash bin %d rust' % seed, rb, M_ZINC_RUST)
    # the lid: a shallow dome with a bar handle
    lid = bmesh.new()
    bmesh.ops.create_cone(lid, cap_ends=True, segments=36, radius1=R1 + 0.022, radius2=R1 + 0.022, depth=0.035,
                          matrix=Matrix.Translation((0, 0, 0.0175)))
    bmesh.ops.create_cone(lid, cap_ends=True, segments=36, radius1=R1 + 0.005, radius2=0.07, depth=0.07,
                          matrix=Matrix.Translation((0, 0, 0.035 + 0.035)))
    for sgn in (-1, 1):
        bmesh.ops.create_cube(lid, size=1.0, matrix=Matrix.Translation((sgn * 0.06, 0, 0.13)) @ Matrix.Diagonal((0.018, 0.025, 0.05, 1.0)))
    bmesh.ops.create_cube(lid, size=1.0, matrix=Matrix.Translation((0, 0, 0.16)) @ Matrix.Diagonal((0.15, 0.03, 0.016, 1.0)))
    if lid_on:
        LM = M @ Matrix.Translation((0, 0, H - 0.005)) @ Matrix.Rotation(r.uniform(-0.05, 0.05), 4, 'Y')
    else:
        LM = lid_tilt
    bmesh.ops.transform(lid, matrix=LM, verts=lid.verts)
    lo = dress_obj('ash bin %d lid' % seed, lid, M_ZINC, smooth=True)
    lo.modifiers.new('edges', 'EDGE_SPLIT').split_angle = math.radians(50)
    return M, H

def heap(name, cx, cy, cz, rx, ry, h, material, seed, segs=24, rings=8):
    """A slumped heap (ash, grit) with a ragged foot."""
    r = random.Random(seed)
    bm = bmesh.new()
    phase = [r.uniform(0, math.tau) for _ in range(3)]
    rings_v = []
    for i in range(rings + 1):
        t = i / rings
        ring = []
        for j in range(segs):
            a = math.tau * j / segs
            wob = 1.0 + 0.16 * math.sin(3 * a + phase[0]) + 0.09 * math.sin(5 * a + phase[1]) + r.uniform(-0.05, 0.05)
            rad = (1.0 - t) * wob
            z = h * (1.0 - t ** 1.0) ** 0.6 if i < rings else h
            z = h * (1 - (1 - t) ** 2.2) if False else h * (1.0 - (rad / max(wob, 1e-3)) ** 1.6) + r.uniform(-0.006, 0.006)
            ring.append(bm.verts.new((cx + rx * rad * math.cos(a), cy + ry * rad * math.sin(a), cz + max(z, 0.0) - 0.01)))
        rings_v.append(ring)
    for i in range(rings):
        for j in range(segs):
            a, b2 = rings_v[i][j], rings_v[i][(j + 1) % segs]
            c, d = rings_v[i + 1][(j + 1) % segs], rings_v[i + 1][j]
            if i + 1 == rings:
                try:
                    bm.faces.new((a, b2, c)) if c is not d else None
                except Exception:
                    pass
            try:
                bm.faces.new((a, b2, c, d))
            except Exception:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    return dress_obj(name, bm, material, smooth=True)

def lumps(name, pts, material, seed, size=(0.015, 0.04)):
    r = random.Random(seed)
    bm = bmesh.new()
    for (x, y, z) in pts:
        s = r.uniform(*size)
        g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s,
                                       matrix=Matrix.Translation((x, y, z + s * 0.3)) @ Matrix.Rotation(r.uniform(0, 6), 4, 'Z')
                                       @ Matrix.Diagonal((r.uniform(0.7, 1.3), r.uniform(0.7, 1.3), r.uniform(0.45, 0.8), 1.0)))
        for v in g['verts']:
            v.co += Vector((r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25))) * s
    return dress_obj(name, bm, material)

# where the bins and the setts stand: the pavement at the kerb, either side of the near lamp post (3.95, 4.6)
LAMP_X, LAMP_Y = KERB_X + 0.5, 4.6
pz_bins = ground_z(LAMP_X + 0.25, LAMP_Y - 0.6, PAVE_Z + 0.02)
log('pavement top by the lamp: %.3f' % pz_bins)
B1 = (KERB_X + 0.54, 3.42)            # in a row along the kerb edge between the stack of setts and the lamp post,
B2 = (KERB_X + 0.55, 2.92)            # clear of the walking line by the wall
MB1, HB = ash_bin(B1[0], B1[1], pz_bins, turn=12, seed=1)
lid2 = Matrix.Translation((LAMP_X - 0.02, LAMP_Y - 0.36, pz_bins + 0.0)) @ Matrix.Rotation(math.radians(8), 4, 'Z') @ \
    Matrix.Rotation(math.radians(74), 4, 'X') @ Matrix.Translation((0, 0.27, 0))
MB2, _ = ash_bin(B2[0], B2[1], pz_bins, turn=-30, seed=2, lid_on=False, lid_tilt=lid2)
# ash spilt on the closed lid when the open bin was filled beside it
heap('ash on the closed lid', B1[0] + 0.07, B1[1] - 0.06, pz_bins + HB + 0.08, 0.10, 0.08, 0.035, M_ASH, seed=5)
# the open bin is heaped with ash over its rim
heap('ash in the open bin', B2[0], B2[1], pz_bins + HB - 0.06, 0.238, 0.238, 0.16, M_ASH_TOP, seed=3)
lumps('clinker on the ash', [(B2[0] + dr.uniform(-0.13, 0.13), B2[1] + dr.uniform(-0.13, 0.13), pz_bins + HB + 0.06) for _ in range(14)],
      M_CINDER, seed=6, size=(0.018, 0.035))
# cinders spilt from it when it was set down, on the flags and over the kerb edge into the gutter
cpts = []
for k in range(70):
    a = dr.uniform(0, math.tau)
    rr = abs(dr.gauss(0.0, 0.32))
    x = B2[0] - 0.42 + math.cos(a) * rr * 1.1
    yy = B2[1] - 0.25 + math.sin(a) * rr * 0.9
    if math.hypot(x - B1[0], yy - B1[1]) < 0.27 or math.hypot(x - B2[0], yy - B2[1]) < 0.27:
        continue                      # not under the bins
    if x < KERB_X + 0.31:
        z = ground_z(x, yy, TOP)      # over the kerb's edge into the gutter
        if z > PAVE_Z + 0.1:
            continue
    else:
        z = pz_bins
    cpts.append((x, yy, z))
lumps('cinders spilt', cpts, M_CINDER, seed=4, size=(0.012, 0.03))
stain.on_ground((B2[0] + 0.14, B2[1] - 0.30, pz_bins + 0.004), size=(0.28, 0.3), kind='ash', turn=-20, strength=0.45, seed=21,
                collection=C_DRESS)

# ------------------------------------------------------------------------------------------------ the road men's spare setts and grit
bm = bmesh.new()
sx, sy = KERB_X + 0.52, 2.25                  # at the kerb edge across from the relaid patch, where the road men worked
for layer in range(3):
    for i in range(3):
        for j in range(2):
            if layer == 2 and (i, j) in ((2, 1), (0, 0)):
                continue
            w, d, h = dr.uniform(0.25, 0.29), dr.uniform(0.13, 0.15), dr.uniform(0.12, 0.14)
            cx = sx + (j - 0.5) * 0.16 + dr.uniform(-0.01, 0.01)
            cy = sy + (i - 1) * 0.28 + dr.uniform(-0.015, 0.015)
            cz = pz_bins + h / 2 + layer * 0.135
            S = Matrix.Diagonal((d, w, h, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(dr.uniform(-0.06, 0.06), 4, 'Z') @ S)
for (x, yy, a) in ((sx + 0.30, sy - 0.30, 0.5),):
    S = Matrix.Diagonal((0.27, 0.14, 0.13, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((x, yy, pz_bins + 0.065)) @ Matrix.Rotation(a, 4, 'Z') @ S)
spare = dress_obj('spare setts', bm, M_GRANITE_NEW)
bv = spare.modifiers.new('arris', 'BEVEL')
bv.width = 0.01
bv.segments = 2

# the road men's lantern, left burning on the stack to mark it at the kerb for the night (a lantern brings its own light)
bpy.context.view_layer.update()
lz = ground_z(sx - 0.08, sy + 0.02, pz_bins + 0.41)
lantern = store.add_part('hurricane_lantern', location=(sx - 0.08, sy + 0.02, lz), turn=-35, seed=3, lit=True)
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.startswith('hurricane_lantern light'):
        o.data.energy = LANTERN_W
log('lantern on the stack at z %.3f, %.0f W' % (lz, LANTERN_W))

# ------------------------------------------------------------------------------------------------ the gutter: silt, straw, leaves, paper
GX = KERB_X - 0.16               # the channel's middle, at the kerb's foot
for (y0, ry, st, sd) in ((1.2, 1.1, 0.5, 31), (3.9, 0.9, 0.45, 32), (6.2, 1.2, 0.4, 33)):
    stain.on_ground((GX + 0.02, y0, TOP + 0.003), size=(0.17, ry), kind='mud', turn=0, strength=st, seed=sd, raggedness=1.4,
                    collection=C_DRESS)
stain.on_ground((GX - 0.05, 2.45, TOP + 0.004), size=(0.25, 0.32), kind='coal dust', turn=8, strength=0.4, seed=34,
                collection=C_DRESS)

def leaf(bm, x, y, z, size, turn, curl):
    """A fallen leaf: a pointed oval, folded a little along its rib, lying flat."""
    verts = []
    n = 6
    for i in range(n + 1):
        t = i / n
        wdt = math.sin(math.pi * t ** 0.8) ** 1.3 * 0.27 * size * (1.0 + 0.18 * math.sin(t * 19.0))
        ln = (t - 0.5) * size
        for s in (-1, 0, 1):
            zz = curl * abs(s) * size * 0.25 + 0.002
            verts.append(Vector((s * wdt, ln, zz)))
    R = Matrix.Rotation(turn, 3, 'Z')
    vs = [bm.verts.new(Vector((x, y, z)) + R @ v) for v in verts]
    st0 = Vector((x, y, z)) + R @ Vector((0, -0.5 * size, 0.002))
    st1 = Vector((x, y, z)) + R @ Vector((0.01 * size, -0.78 * size, 0.004))
    sa, sb, sc = bm.verts.new(st0 + R @ Vector((-0.003, 0, 0))), bm.verts.new(st0 + R @ Vector((0.003, 0, 0))), bm.verts.new(st1)
    bm.faces.new((sa, sb, sc))
    for i in range(n):
        for k in range(2):
            a = vs[i * 3 + k]
            b2 = vs[i * 3 + k + 1]
            c = vs[(i + 1) * 3 + k + 1]
            d = vs[(i + 1) * 3 + k]
            try:
                bm.faces.new((a, b2, c, d))
            except Exception:
                pass

bmA, bmB = bmesh.new(), bmesh.new()
leaf_spots = []
# caught against the drain grate's upstream edge (water runs towards the camera's side? the grate takes it from both)
for k in range(26):
    leaf_spots.append((gx + dr.uniform(-0.28, 0.24), gy + 0.40 + abs(dr.gauss(0, 0.10)), dr.uniform(0.07, 0.12)))
for k in range(9):
    leaf_spots.append((gx + dr.uniform(-0.25, 0.2), gy + dr.uniform(-0.35, 0.35), dr.uniform(0.06, 0.09)))
# along the kerb's foot, in the angle where the water left them
for k in range(40):
    yy = dr.uniform(0.5, 7.5)
    leaf_spots.append((KERB_X - abs(dr.gauss(0.0, 0.10)) - 0.03, yy, dr.uniform(0.07, 0.12)))
# a few blown out across the setts near the eye, none in the puddles
for k in range(34):
    leaf_spots.append((dr.uniform(0.6, 3.2), dr.uniform(0.5, 2.9), dr.uniform(0.08, 0.13)))
for (x, yy, s) in leaf_spots:
    z = ground_z(x, yy, TOP) + 0.001
    leaf(bmA if dr.random() < 0.55 else bmB, x, yy, z, s, dr.uniform(0, math.tau), dr.uniform(-0.6, 0.6))
dress_obj('fallen leaves, ochre', bmA, M_LEAF_A)
dress_obj('fallen leaves, brown', bmB, M_LEAF_B)

# leaves the wind has piled against the foot of the stack and the bins, on the flags
bmA2, bmB2 = bmesh.new(), bmesh.new()
for k in range(26):
    t = dr.random()
    if t < 0.35:
        x, yy = dr.uniform(KERB_X + 0.32, sx - 0.16), sy + dr.uniform(-0.40, 0.42)          # the strip between the kerb edge and the stack
    elif t < 0.6:
        x, yy = dr.uniform(KERB_X + 0.33, sx + 0.12), sy - 0.44 - abs(dr.gauss(0, 0.08))  # against the stack's near end
    else:
        a_ = dr.uniform(math.pi * 0.6, math.pi * 1.4)
        x, yy = B2[0] + math.cos(a_) * 0.29, B2[1] + math.sin(a_) * 0.29                  # round the open bin's foot
    if x < KERB_X + 0.315:
        x = KERB_X + 0.315 + dr.uniform(0.0, 0.03)
    leaf(bmA2 if dr.random() < 0.5 else bmB2, x, yy, pz_bins + 0.002, dr.uniform(0.08, 0.12), dr.uniform(0, math.tau), dr.uniform(-0.5, 0.5))
dress_obj('leaves against the stack, ochre', bmA2, M_LEAF_A)
dress_obj('leaves against the stack, brown', bmB2, M_LEAF_B)

# straw from the horses' feed, trodden dark, lying along the channel where the water laid it
bm = bmesh.new()
for (cx0, cy0, n, spread) in ((GX + 0.02, 0.95, 26, 0.38), (GX - 0.02, 2.0, 18, 0.3), (gx + 0.05, gy + 0.52, 22, 0.25),
                               (GX, 5.2, 20, 0.35)):
    base_ang = math.pi / 2 + dr.uniform(-0.35, 0.35)
    for k in range(n * 3):
        x = cx0 + dr.gauss(0, 0.045)
        yy = cy0 + dr.gauss(0, spread * 0.35)
        ang = base_ang + dr.gauss(0, 0.18)
        L = dr.uniform(0.10, 0.24)
        z = ground_z(x, yy, TOP) + 0.003
        p0 = Vector((x - math.cos(ang) * L / 2, yy - math.sin(ang) * L / 2, z))
        p1 = Vector((x + math.cos(ang) * L / 2, yy + math.sin(ang) * L / 2, z + dr.uniform(-0.002, 0.004)))
        dv = p1 - p0
        q = dv.normalized().to_track_quat('Z', 'Y')
        bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0024, radius2=0.0018, depth=dv.length,
                              matrix=Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((1.0, 0.55, 1.0, 1.0)))
dress_obj('straw in the gutter', bm, M_STRAW)

# a sheet of newspaper gone to pulp in the channel above the grate, folded over itself, no print showing
bm = bmesh.new()
pw, ph = 0.36, 0.28
nx, ny = 9, 7
grid = []
for i in range(nx + 1):
    col = []
    for j in range(ny + 1):
        u, v = i / nx, j / ny
        x = GX - 0.02 + (u - 0.5) * pw
        yy = gy + 0.95 + (v - 0.5) * ph
        z = ground_z(x, yy, TOP) + 0.004 + 0.012 * math.sin(u * 7.0 + v * 3.0) ** 2 * (1 if (u > 0.55) else 0.3)
        col.append(bm.verts.new((x + dr.uniform(-0.006, 0.006), yy + dr.uniform(-0.006, 0.006), z)))
    grid.append(col)
for i in range(nx):
    for j in range(ny):
        if (i == 0 and j == ny - 1) or (i == nx - 1 and j == 0) or (i == nx - 1 and j == 1):
            continue                # torn corners
        bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
paper = dress_obj('sodden newspaper', bm, M_PAPER, smooth=True)

# ------------------------------------------------------------------------------------------------ the kerbs: chipped, hand-dressed
kerb = bpy.data.objects.get('kerbstones')
if kerb is not None:
    sub = kerb.modifiers.new('fine', 'SUBSURF')
    sub.subdivision_type = 'SIMPLE'
    sub.levels = sub.render_levels = 3
    tex = bpy.data.textures.new('kerb chips', 'VORONOI')
    tex.noise_scale = 0.09
    tex.distance_metric = 'DISTANCE'
    disp = kerb.modifiers.new('chips', 'DISPLACE')
    disp.texture = tex
    disp.texture_coords = 'GLOBAL'
    disp.strength = -0.022
    disp.mid_level = 0.0
    tex2 = bpy.data.textures.new('kerb dressing', 'CLOUDS')
    tex2.noise_scale = 0.05
    disp2 = kerb.modifiers.new('dressing', 'DISPLACE')
    disp2.texture = tex2
    disp2.texture_coords = 'GLOBAL'
    disp2.strength = 0.008
    log('kerbs chipped')


# ------------------------------------------------------------------------------------------------ the near road: missing setts, gutter water, stains
log('dressing: the near road')
# two setts gone from the old road near the eye, by the gutter where wheels turn in to the kerb; water and grit in the holes
if setts_obj is not None:
    holes = [(2.95, 0.95), (3.12, 1.10), (1.05, 3.05)]
    bm = bmesh.new()
    bm.from_mesh(setts_obj.data)
    kill = []
    for (hx, hy) in holes:
        best = min(bm.verts, key=lambda v: (v.co.x - hx) ** 2 + (v.co.y - hy) ** 2)
        if best not in kill:
            kill.append(best)
    centres = [(v.co.x, v.co.y) for v in kill]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(setts_obj.data)
    bm.free()
    setts_obj.data.update()
    for k, (hx, hy) in enumerate(centres):
        puddle.make((hx, hy, TOP - 0.02), size=(0.36, 0.22), turn=dr.uniform(-8, 8), level=TOP - 0.02, seed=60 + k, raggedness=0.8)
    log('holes: %d setts gone' % len(centres))

# grit, small stones and moss packed in the old setts' joints near the eye: lumps set just under the setts' tops show only
# where there is a joint (inside a sett they are hidden), so they find the joints by themselves
M_MOSS_J = node_mat('moss in the joints', (0.022, 0.03, 0.009), 0.8, noise_scale=60.0, noise_amt=0.5, bump=0.6, random_tint=0.3)
M_PEB = node_mat('grit stones', (0.06, 0.055, 0.05), 0.35, noise_scale=120.0, noise_amt=0.5, random_tint=0.5)
gpts, mpts = [], []
for k in range(2600):
    x, yy = dr.uniform(0.2, KERB_X - 0.02), dr.uniform(0.3, 4.6)
    if PATCH[0] - 0.05 < x < PATCH[1] + 0.05 and PATCH[2] - 0.05 < yy < PATCH[3] + 0.05:
        continue
    near_kerb = (x - (KERB_X - 0.6)) / 0.6          # moss where wheels do not reach, by the kerb
    if near_kerb > 0 and dr.random() < 0.5 * near_kerb:
        mpts.append((x, yy, TOP - 0.03))
    else:
        gpts.append((x, yy, TOP - 0.028))
lumps('grit in the joints', gpts, M_PEB, seed=91, size=(0.007, 0.016))
lumps('moss in the joints', mpts, M_MOSS_J, seed=92, size=(0.010, 0.02))


# setts near the eye rocked loose by the wheels: a few sunk a little and tipped, so each catches the sky its own way
if setts_obj is not None:
    me = setts_obj.data
    rot = me.attributes['stone_rotation']
    n_rocked = 0
    for i, v in enumerate(me.vertices):
        if 0.3 < v.co.y < 4.2 and 0.2 < v.co.x < KERB_X and not (PATCH[0] - 0.1 < v.co.x < PATCH[1] + 0.1 and PATCH[2] - 0.1 < v.co.y < PATCH[3] + 0.1):
            if dr.random() < 0.16:
                v.co.z -= dr.uniform(0.004, 0.016)
                r0 = rot.data[i].vector
                rot.data[i].vector = (r0[0] + dr.uniform(-0.07, 0.07), r0[1] + dr.uniform(-0.07, 0.07), r0[2] + dr.uniform(-0.03, 0.03))
                n_rocked += 1
    me.update()
    log('rocked %d setts near the eye' % n_rocked)

# the channel by the kerb holds a thin run of water down to the grate
GL = TOP + 0.0015
puddle.make((KERB_X - 0.13, 1.55, GL), size=(2.5, 0.2), turn=90, level=GL, seed=71, raggedness=1.5)
# horses stood here while the coal went up the stair: dung and wet soaked into the joints, thin, off the water
for (x, yy, rx, ry, st, sd) in ((2.55, 0.95, 0.45, 0.32, 0.32, 81), (1.0, 1.45, 0.35, 0.5, 0.25, 82)):
    stain.on_ground((x, yy, TOP + 0.002), size=(rx, ry), kind='mud', turn=dr.uniform(0, 90), strength=st, seed=sd, raggedness=1.6,
                    collection=C_DRESS)

# ------------------------------------------------------------------------------------------------ the near pavement: flags broken, stained
log('dressing: the near pavement')
FLAG_TOP = pz_bins          # measured by a ray before anything stood on the flags
log('flag top %.3f' % FLAG_TOP)
# grit and dirt packed in the flags' joints (the bed under them was bare)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5,
                      matrix=Matrix.Translation(((KERB_X + 0.3 + FRONT_X) / 2, 8.0, FLAG_TOP - 0.03))
                      @ Matrix.Diagonal((FRONT_X - KERB_X - 0.3, 34.0, 1.0, 1.0)))
dress_obj('dirt in the flags joints', bm, M_GRIT)

# (a broken flag was tried here, by the stack of setts; the stack hides it from the eye, so it was taken out)

# mud thrown up from the wheels along the kerb edge, and damp where water stood on the flags
for (x, yy, rx, ry, kind, st, sd) in ((KERB_X + 0.42, 1.6, 0.16, 0.8, 'mud', 0.4, 51), (KERB_X + 0.45, 3.9, 0.18, 0.55, 'mud', 0.35, 52),
                                       (KERB_X + 0.85, 2.2, 0.35, 0.45, 'damp', 0.45, 53), (KERB_X + 0.7, 6.4, 0.3, 0.6, 'damp', 0.4, 54),
                                       (FRONT_X - 0.35, 6.0, 0.25, 1.5, 'damp', 0.5, 55)):
    stain.on_ground((x, yy, FLAG_TOP + 0.003), size=(rx, ry), kind=kind, turn=0, strength=st, seed=sd, raggedness=1.3,
                    collection=C_DRESS)
log('near pavement done')


# ------------------------------------------------------------------------------------------------ the old setts: not all one stone
# a street's setts come from more than one quarry and stain differently: about a third warm brown (iron in the granite, rust
# off the wheels), a few blue-black whinstone; the value of each still varies as the first builder made it
def setts_of_two_quarries(name, warm_share=0.32, warm=(1.32, 0.98, 0.72), dark_share=0.12, dark=(0.72, 0.78, 0.86)):
    m = store.material(name)
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return
    inp = bsdf.inputs['Base Color']
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    h1 = nt.nodes.new('ShaderNodeMath')
    h1.operation = 'MULTIPLY'
    h1.inputs[1].default_value = 17.31
    nt.links.new(oi.outputs['Random'], h1.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath')
    fr.operation = 'FRACT'
    nt.links.new(h1.outputs[0], fr.inputs[0])
    lt = nt.nodes.new('ShaderNodeMath')
    lt.operation = 'LESS_THAN'
    lt.inputs[1].default_value = warm_share
    nt.links.new(fr.outputs[0], lt.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath')
    gt.operation = 'GREATER_THAN'
    gt.inputs[1].default_value = 1.0 - dark_share
    nt.links.new(fr.outputs[0], gt.inputs[0])
    mw = nt.nodes.new('ShaderNodeMix')
    mw.data_type = 'RGBA'
    mw.blend_type = 'MULTIPLY'
    if inp.is_linked:
        nt.links.new(inp.links[0].from_socket, mw.inputs[6])
    else:
        mw.inputs[6].default_value = inp.default_value
    mw.inputs[7].default_value = (warm[0], warm[1], warm[2], 1.0)
    nt.links.new(lt.outputs[0], mw.inputs['Factor'])
    md = nt.nodes.new('ShaderNodeMix')
    md.data_type = 'RGBA'
    md.blend_type = 'MULTIPLY'
    nt.links.new(mw.outputs[2], md.inputs[6])
    md.inputs[7].default_value = (dark[0], dark[1], dark[2], 1.0)
    nt.links.new(gt.outputs[0], md.inputs['Factor'])
    nt.links.new(md.outputs[2], inp)

setts_of_two_quarries('COBBLES • wet basalt / broken amber-blue reflections')

log('dressing done')

# ==================================================================================================================
# The third pass: the buildings' faces and the middle distance of the town street.
# Runs inside render_final.py after the first builder's buildings and the second builder's dressing are made (so BLD,
# Acc, PAVE_Z, KERB_X, FRONT_X, store, stain ... exist). Every thing here belongs to someone (see materials.md):
# the coal fires' soot on every ledge, the rain's damp and leaks, the flats' blinds and nets, the pots put out on a sill,
# the stair window the factor boarded, the grocer's and the dairyman's signs, the grocer's sack barrow.
# ==================================================================================================================
log('fronts: the third pass')
C_FRONTS = coll('fronts')
fr = random.Random(5503)
fr2 = random.Random(5504)          # the end fronts' extra runs: their own dice, so nothing else moves
FR_STAIN = float(os.environ.get('FR_STAIN', '1.0'))     # working dial: how hard the made soot and damp are pushed

def fr_node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n

def wear_mat(name, color, rough, lo, hi, ragged, streak_scale, streak_amt, max_alpha):
    """A see-through stain read from the stain tool's 'fade' on each point: strong where fade is 0, gone at 1,
    streaked downwards and with a ragged edge, pushed much harder than the shelf's stains."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    bs.inputs['Roughness'].default_value = rough
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'fade'
    inv = fr_node(nt, 'ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(at.outputs['Fac'], inv.inputs[1])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    # streaks: a noise stretched up and down
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = streak_scale
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = fr_node(nt, 'ShaderNodeTexNoise', Scale=1.0, Detail=5.0, Roughness=0.62)
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    st = fr_node(nt, 'ShaderNodeMapRange')
    st.inputs['From Min'].default_value, st.inputs['From Max'].default_value = 0.34, 0.66
    nt.links.new(nz.outputs['Fac'], st.inputs['Value'])
    sv = fr_node(nt, 'ShaderNodeMath')
    sv.operation = 'MULTIPLY_ADD'
    sv.inputs[1].default_value = streak_amt
    sv.inputs[2].default_value = 1.0 - streak_amt
    nt.links.new(st.outputs[0], sv.inputs[0])
    # a ragged edge: a rounder noise added before the threshold
    mp2 = nt.nodes.new('ShaderNodeMapping')
    mp2.inputs['Scale'].default_value = (3.2, 3.2, 2.2)
    nt.links.new(tc.outputs['Object'], mp2.inputs['Vector'])
    nz2 = fr_node(nt, 'ShaderNodeTexNoise', Scale=1.0, Detail=6.0, Roughness=0.7)
    nt.links.new(mp2.outputs['Vector'], nz2.inputs['Vector'])
    rg = fr_node(nt, 'ShaderNodeMath')
    rg.operation = 'MULTIPLY_ADD'
    rg.inputs[1].default_value = ragged
    rg.inputs[2].default_value = -0.5 * ragged
    nt.links.new(nz2.outputs['Fac'], rg.inputs[0])
    add = fr_node(nt, 'ShaderNodeMath')
    add.operation = 'ADD'
    nt.links.new(inv.outputs[0], add.inputs[0])
    nt.links.new(rg.outputs[0], add.inputs[1])
    th = fr_node(nt, 'ShaderNodeMapRange')
    th.inputs['From Min'].default_value, th.inputs['From Max'].default_value = lo, hi
    th.inputs['To Min'].default_value, th.inputs['To Max'].default_value = 0.0, max_alpha
    nt.links.new(add.outputs[0], th.inputs['Value'])
    a = fr_node(nt, 'ShaderNodeMath')
    a.operation = 'MULTIPLY'
    a.use_clamp = True
    nt.links.new(th.outputs[0], a.inputs[0])
    nt.links.new(sv.outputs[0], a.inputs[1])
    nt.links.new(a.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bs.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m

SOOT = wear_mat('fronts soot', (0.010, 0.0085, 0.0075), 0.92, lo=0.02, hi=0.5, ragged=0.30,
                streak_scale=(6.0, 6.0, 0.42), streak_amt=0.62, max_alpha=min(1.0, 0.95 * FR_STAIN))
DAMP = wear_mat('fronts damp', (0.016, 0.021, 0.013), 0.42, lo=0.22, hi=0.40, ragged=0.42,
                streak_scale=(6.0, 6.0, 0.8), streak_amt=0.35, max_alpha=min(1.0, 0.86 * FR_STAIN))
LEAK = wear_mat('fronts leak', (0.013, 0.019, 0.011), 0.38, lo=0.05, hi=0.55, ragged=0.25,
                streak_scale=(6.0, 6.0, 0.4), streak_amt=0.6, max_alpha=min(1.0, 0.9 * FR_STAIN))

SOOT_FAR = wear_mat('fronts soot, far', (0.009, 0.008, 0.007), 0.92, lo=0.0, hi=0.38, ragged=0.30,
                    streak_scale=(3.0, 3.0, 0.38), streak_amt=0.5, max_alpha=min(1.0, 1.0 * FR_STAIN))

VISIBLE = ('R2', 'R3', 'R4', 'L4', 'L5', 'E1', 'E2', 'E3')
FAR = ('L5', 'E1', 'E2', 'E3')

def wall_stain(b, x0, x1, z0, z1, mat, strong_at, strength, seed, extra=0.0, kind='soot', taper=None):
    x0, x1 = max(0.0, x0), min(b.w, x1)
    z0, z1 = max(0.0, z0), min(b.h, z1)
    if x1 - x0 < 0.05 or z1 - z0 < 0.05:
        return None
    off = (0.236 if not b.rubble else 0.085) + extra
    o = stain.on_wall(b.obj, 'front', x0, x1, z0, z1, kind=kind, strong_at=strong_at, strength=strength, seed=seed,
                      offset=off, collection=C_FRONTS, material=mat)
    if taper is not None:
        # narrower at its weak end: a run gathers into streaks as it goes down
        zs = [v.co.z for v in o.data.vertices]
        zlo, zhi = min(zs), max(zs)
        for v in o.data.vertices:
            t = (v.co.z - zlo) / max(1e-6, zhi - zlo)
            f = (taper + (1.0 - taper) * t) if strong_at == 'top' else (1.0 - (1.0 - taper) * t)
            v.co.x *= f
            v.co.y *= f
        o.data.update()
    return o

n_stains = 0
for b in (BLD[n] for n in VISIBLE):
    far = b.name in FAR
    s = 1.25 if far else 1.0
    seed0 = 7000 + b.seed * 50
    # soot under the eaves, where the overhang keeps the rain off
    wall_stain(b, 0.0, b.w, b.h - (2.8 if far else 2.3), b.h, SOOT, 'top', 1.25, seed0)
    n_stains += 1
    # rising damp along the foot, in runs of its own height; higher by the doors
    u = 0.0
    while u < b.w - 0.1:
        run = fr.uniform(1.6, 3.2)
        top = fr.uniform(0.85, 1.35) * (1.15 if far else 1.0)
        for du_ in getattr(b, 'doors', []):
            if u - 0.6 < du_ < u + run + 0.6:
                top += 0.25
        wall_stain(b, u - 0.1, u + run + 0.1, 0.0, top, DAMP, 'bottom', 1.0, seed0 + int(u * 10) + 1)
        n_stains += 1
        u += run
    # soot runs under every sill, and a smudge over about half the window heads
    SO = SOOT_FAR if far else SOOT
    for (k, i, uu, z, ww, hh) in b.windows:
        L = fr.uniform(0.9, 1.9) * s
        sh_ = fr.uniform(-0.12, 0.12)
        wall_stain(b, uu + sh_ - ww / 2 - 0.12 * s, uu + sh_ + ww / 2 + 0.12 * s, z - 0.27 - L, z - 0.27, SO, 'top', 1.15 * s,
                   seed0 + 100 + k * 13 + i, taper=fr.uniform(0.35, 0.7))
        if far:
            # on the fronts that face the eye, two or three runs go on down past the apron, where the sill's drip fails
            for j in range(fr2.randint(2, 3)):
                cu_ = uu + fr2.uniform(-ww / 2 + 0.08, ww / 2 - 0.08)
                sw = fr2.uniform(0.12, 0.24)
                wall_stain(b, cu_ - sw / 2, cu_ + sw / 2, z - 0.27 - L - fr2.uniform(0.5, 1.3), z - 0.27 - L * 0.4, SO, 'top', 1.1,
                           seed0 + 150 + k * 13 + i * 5 + j, taper=fr2.uniform(0.3, 0.6))
                n_stains += 1
        n_stains += 1
        if k >= 1 and fr.random() < 0.55:
            wall_stain(b, uu - ww / 2 - 0.16, uu + ww / 2 + 0.16, z + hh + 0.20, z + hh + 0.20 + fr.uniform(0.6, 1.0) * s, SO,
                       'bottom', 0.95 * s, seed0 + 300 + k * 13 + i, taper=0.6)
            n_stains += 1
    # gutter leaks: green-black runs down from the eaves under the gutter's joints
    for j in range(fr.randint(2, 3)):
        uu = fr.uniform(0.8, b.w - 0.8)
        wd = fr.uniform(0.35, 0.7) * s
        wall_stain(b, uu - wd / 2, uu + wd / 2, b.h - 0.25 - fr.uniform(2.0, 3.6) * s, b.h - 0.2, LEAK, 'top', 1.2,
                   seed0 + 500 + j, taper=0.4)
        n_stains += 1
    # the downpipe at the left end: a wet stripe behind it, worse under each socket; rust under each holdfast
    pu = 0.3
    wall_stain(b, pu - 0.28, pu + 0.30, 0.0, b.h - 0.5, LEAK, 'bottom', 0.75, seed0 + 600)
    zz = 1.6
    while zz < b.h - 0.8:
        wall_stain(b, pu - 0.2, pu + 0.24, zz - fr.uniform(0.9, 1.5), zz, LEAK, 'top', 1.25, seed0 + 610 + int(zz), taper=0.45)
        stain.on_wall(b.obj, 'front', pu - 0.06, pu + 0.07, zz - 0.75, zz, kind='rust', strong_at='top', strength=1.0,
                      seed=seed0 + 650 + int(zz), offset=(0.24 if not b.rubble else 0.09), collection=C_FRONTS)
        n_stains += 2
        zz += 1.85
log('fronts: %d stains on the fronts' % n_stains)

# ------------------------------------------------------------------------------------------------ hopper heads
FIRON = Acc('fronts iron', 'IRON • soot-black lamp posts')
for b in (BLD[n] for n in VISIBLE):
    out_ = b.relief + 0.12
    M = b.M
    FIRON.box(M, b.front(0.3, out_, b.h - 0.52), (0.34, 0.26, 0.30))
    FIRON.box(M, b.front(0.3, out_, b.h - 0.36), (0.40, 0.31, 0.05))      # its lip
    stain.on_wall(b.obj, 'front', 0.12, 0.5, b.h - 1.5, b.h - 0.66, kind='rust', strong_at='top', strength=1.0,
                  seed=b.seed + 900, offset=b.relief + 0.02, collection=C_FRONTS)

# ------------------------------------------------------------------------------------------------ blinds and net curtains
def cloth_mat(name, color, rough=0.95, alpha=1.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bs = nt.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    bs.inputs['Roughness'].default_value = rough
    if alpha < 1.0:
        bs.inputs['Alpha'].default_value = alpha
    return m

BLIND_BUFF = Acc('blinds buff', cloth_mat('blind linen buff', (0.21, 0.155, 0.085)))
BLIND_GREEN = Acc('blinds green', cloth_mat('blind holland green', (0.035, 0.06, 0.04)))
NETS = Acc('net curtains', cloth_mat('net curtain', (0.30, 0.30, 0.28), rough=1.0, alpha=0.72))
HEM = Acc('blind laths', cloth_mat('blind lath', (0.05, 0.035, 0.025), rough=0.8))

def blind(b, uu, z, ww, hh, out_, frac, green):
    acc = BLIND_GREEN if green else BLIND_BUFF
    bh = hh * frac
    acc.box(b.M, b.front(uu, out_, z + hh - bh / 2 - 0.02), (ww - 0.12, 0.004, bh))
    HEM.box(b.M, b.front(uu, out_ + 0.004, z + hh - bh - 0.02), (ww - 0.12, 0.012, 0.028))
    HEM.cyl(b.M, b.front(uu - ww / 2 + 0.06, out_ - 0.01, z + hh - 0.05), b.front(uu + ww / 2 - 0.06, out_ - 0.01, z + hh - 0.05), 0.02, segs=8)

def nets(b, uu, z, ww, hh, out_, cover, side):
    """Net curtains in folds: `cover` of the width from one side (side -1 left, +1 right; 0 both halves)."""
    def panel(u0, u1):
        n = max(3, int((u1 - u0) / 0.07))
        step = (u1 - u0) / n
        for j in range(n):
            rz = 0.45 if j % 2 else -0.45
            NETS.box(b.M, b.front(u0 + (j + 0.5) * step, out_ + 0.006 + 0.004 * (j % 2), z + hh / 2), (step * 1.08, 0.003, hh - 0.08), rot_z=rz)
    if side == 0:
        panel(uu - ww / 2 + 0.05, uu - ww / 2 + 0.05 + (ww - 0.1) * cover / 2)
        panel(uu + ww / 2 - 0.05 - (ww - 0.1) * cover / 2, uu + ww / 2 - 0.05)
    elif side < 0:
        panel(uu - ww / 2 + 0.05, uu - ww / 2 + 0.05 + (ww - 0.1) * cover)
    else:
        panel(uu + ww / 2 - 0.05 - (ww - 0.1) * cover, uu + ww / 2 - 0.05)

n_bl = n_net = 0
for b in (BLD[n] for n in VISIBLE):
    litset = set(b.lit)
    out_ = (b.relief - 0.10 + 0.015 + 0.007) if not b.rubble else 0.012
    for (k, i, uu, z, ww, hh) in b.windows:
        if (k, i) in litset:
            continue
        if b.name == 'R2' and k == 1 and i == 0:
            continue          # the stair window, boarded (below)
        r = fr.random()
        if r < 0.34:
            blind(b, uu, z, ww, hh, out_, fr.choice((0.22, 0.35, 0.5, 0.62, 0.8)), fr.random() < 0.3)
            n_bl += 1
        elif r < 0.64:
            nets(b, uu, z, ww, hh, out_, fr.choice((0.5, 0.7, 1.0)), fr.choice((-1, 0, 1)))
            n_net += 1
        elif r < 0.78:
            blind(b, uu, z, ww, hh, out_, fr.choice((0.25, 0.4)), False)
            nets(b, uu, z, ww, hh, out_ + 0.004, 1.0, 0)
            n_bl += 1
            n_net += 1
log('fronts: %d blinds, %d net curtains' % (n_bl, n_net))

# ------------------------------------------------------------------------------------------------ the stair window, boarded
# R2's stair window over the lit stair door: the lower panes broken a year ago, the factor nailed boards over them
R2f = BLD['R2']
BOARDS = Acc('boards over the stair window', 'SURFACE • rough_wood')
NAILS = Acc('nail heads', 'MADE • rusty nail heads')
for (k, i, uu, z, ww, hh) in R2f.windows:
    if k == 1 and i == 0:
        bw = ww + 0.30
        for j, zz in enumerate((z + 0.10, z + 0.29, z + 0.48, z + 0.67)):
            BOARDS.box(R2f.M, R2f.front(uu + fr.uniform(-0.03, 0.03), 0.285 + 0.004 * j, zz), (bw + fr.uniform(-0.06, 0.04), 0.022, 0.175),
                       rot_x=0.0)
            for sx in (-1, 1):
                for dz in (-0.04, 0.04):
                    NAILS.box(R2f.M, R2f.front(uu + sx * (bw / 2 - 0.07), 0.30 + 0.004 * j, zz + dz), (0.014, 0.012, 0.014))
        # one board nailed across the corner, where the glass above it cracked too
        BOARDS.box(R2f.M, R2f.front(uu + 0.12, 0.31, z + 0.98), (0.75, 0.022, 0.15), rot_x=0.0)

# ------------------------------------------------------------------------------------------------ pots and a jug on the sills
CLAYP = Acc('flower pots', plain_mat('flower pot clay', (0.22, 0.07, 0.03), rough=0.85))
LEAF = Acc('geranium leaves', plain_mat('geranium leaves', (0.025, 0.06, 0.018), rough=0.7))
FLOWER = Acc('geranium flowers', plain_mat('geranium flowers', (0.55, 0.03, 0.02), rough=0.6))
JUG = Acc('milk jug', 'MADE • glazed china')

def geranium(b, uu, z_sill, out_, seed, head=0.055, heads=5, tall=1.0):
    gr = random.Random(seed)
    base = b.front(uu, out_, z_sill)
    top = b.front(uu, out_, z_sill + 0.17)
    CLAYP.cyl(b.M, base, top, 0.065, segs=12, r2=0.085)
    CLAYP.cyl(b.M, b.front(uu, out_, z_sill + 0.15), b.front(uu, out_, z_sill + 0.185), 0.092, segs=12)
    for j in range(16):
        a = gr.uniform(0, 2 * math.pi)
        rr = gr.uniform(0.02, 0.14)
        h_ = gr.uniform(0.2, 0.36) * tall
        c = b.front(uu + math.cos(a) * rr, out_ + math.sin(a) * rr * 0.8, z_sill + h_)
        LEAF.box(b.M, c, (gr.uniform(0.06, 0.09), gr.uniform(0.06, 0.09), 0.025), rot_z=gr.uniform(0, 3))
        LEAF.cyl(b.M, b.front(uu, out_, z_sill + 0.17), c, 0.005, segs=4)
    for j in range(heads):
        a = gr.uniform(0, 2 * math.pi)
        rr = gr.uniform(0.0, 0.11)
        c = b.front(uu + math.cos(a) * rr, out_ + math.sin(a) * rr * 0.8, z_sill + gr.uniform(0.36, 0.46) * tall)
        FLOWER.box(b.M, c, (head, head, head * 0.9), rot_z=gr.uniform(0, 3))
        LEAF.cyl(b.M, b.front(uu, out_, z_sill + 0.2), c, 0.004, segs=4)

def milk_jug(b, uu, z_sill, out_):
    JUG.cyl(b.M, b.front(uu, out_, z_sill), b.front(uu, out_, z_sill + 0.16), 0.06, segs=14, r2=0.075)
    JUG.cyl(b.M, b.front(uu, out_, z_sill + 0.16), b.front(uu, out_, z_sill + 0.2), 0.075, segs=14, r2=0.068)
    JUG.box(b.M, b.front(uu, out_ + 0.075, z_sill + 0.19), (0.04, 0.05, 0.03))           # the lip
    JUG.box(b.M, b.front(uu, out_ - 0.085, z_sill + 0.11), (0.02, 0.03, 0.11))           # the handle

R3f = BLD['R3']

# ------------------------------------------------------------------------------------------------ signs without words
# the grocer's teapot on its bracket over his door, where a customer coming down the street sees it
sh = R3f.shops[0]
TEA_U = sh[0] + 0.15
sp_ = R3f.world(TEA_U, 0.20, 0.0)
tea = store.add_part('teapot_sign', location=(sp_.x, sp_.y, PAVE_Z), turn=-90, height=3.0)
tea.scale = (1.4, 1.4, 1.4)                  # a tea merchant's teapot is made big enough to see from the street's end
stain.on_wall(R3f.obj, 'front', TEA_U - 0.17, TEA_U + 0.17, 2.6, 4.15, kind='rust', strong_at='top', strength=1.0, seed=4501,
              offset=0.24, collection=C_FRONTS)

# the dairyman's board on an iron bracket over his door, blank; and the close's name board, blank
SIGNP = Acc('sign boards', plain_mat('sign paint, faded cream', (0.34, 0.29, 0.19), rough=0.75))
SIGNB = Acc('sign borders', plain_mat('sign paint, dark green', (0.02, 0.04, 0.025), rough=0.7))
L4f = BLD['L4']
du4 = L4f.shops[0][2] + 1.2
bz = 4.0
FIRON.box(L4f.M, L4f.front(du4, 0.2 + 0.55, bz), (0.035, 1.1, 0.04))                       # the bracket's arm
FIRON.cyl(L4f.M, L4f.front(du4, 0.22, bz - 0.45), L4f.front(du4, 0.85, bz - 0.02), 0.015, segs=6)   # its strut
FIRON.box(L4f.M, L4f.front(du4, 0.22, bz - 0.2), (0.06, 0.04, 0.55))                      # the wall plate
SIGNB.box(L4f.M, L4f.front(du4, 0.77, bz - 0.42), (0.05, 0.95, 0.64))
SIGNP.box(L4f.M, L4f.front(du4, 0.77, bz - 0.42), (0.056, 0.85, 0.54))
for sy in (-0.35, 0.35):
    FIRON.cyl(L4f.M, L4f.front(du4, 0.77 + sy, bz - 0.02), L4f.front(du4, 0.77 + sy, bz - 0.1), 0.008, segs=5)
stain.on_wall(L4f.obj, 'front', du4 - 0.12, du4 + 0.12, bz - 1.5, bz - 0.2, kind='rust', strong_at='top', strength=1.0,
              seed=4502, offset=0.24, collection=C_FRONTS)
E2f = BLD['E2']
cu = E2f.closes[0]
SIGNB.box(E2f.M, E2f.front(cu, 0.30, 3.42), (1.5, 0.03, 0.36))
SIGNP.box(E2f.M, E2f.front(cu, 0.316, 3.42), (1.4, 0.03, 0.28))

# ------------------------------------------------------------------------------------------------ the grocer's sack barrow
# leant against his stall riser in front of the shop window, where he left it after taking the sacks in
SBW = Acc('sack barrow wood', 'SURFACE • rough_wood')
SBI = Acc('sack barrow iron', 'IRON • soot-black lamp posts')
u_sb = sh[1] - 0.55
lean = math.radians(22)
foot_out, foot_z = 0.78, 0.075
Hs = 1.28
for sx in (-0.2, 0.2):
    p0 = R3f.front(u_sb + sx, foot_out, foot_z)
    p1 = R3f.front(u_sb + sx * 0.85, foot_out - Hs * math.sin(lean), foot_z + Hs * math.cos(lean))
    SBW.cyl(R3f.M, p0, p1, 0.03, segs=6)
for t in (0.25, 0.5, 0.75):
    pa = R3f.front(u_sb - 0.2, foot_out - Hs * t * math.sin(lean), foot_z + Hs * t * math.cos(lean))
    pb = R3f.front(u_sb + 0.2, foot_out - Hs * t * math.sin(lean), foot_z + Hs * t * math.cos(lean))
    SBW.cyl(R3f.M, pa, pb, 0.02, segs=5)
SBI.box(R3f.M, R3f.front(u_sb, foot_out + 0.1, 0.012 + 0.07), (0.42, 0.24, 0.012))           # the nose plate on the flags
for sx in (-0.29, 0.29):                                                                      # the wheels
    c = R3f.front(u_sb + sx, foot_out - 0.05, 0.2)
    SBI.cyl(R3f.M, R3f.front(u_sb + sx - 0.025, foot_out - 0.05, 0.2), R3f.front(u_sb + sx + 0.025, foot_out - 0.05, 0.2), 0.13, segs=18)
SBI.cyl(R3f.M, R3f.front(u_sb - 0.3, foot_out - 0.05, 0.2), R3f.front(u_sb + 0.3, foot_out - 0.05, 0.2), 0.015, segs=6)

# ------------------------------------------------------------------------------------------------ a window box over the hero shop
# the first-floor flat over the end shop keeps geraniums in a box on its sill, facing the street
WBOX = Acc('window box', 'SURFACE • rough_wood')
for (k, i, uu, z, ww, hh) in E2f.windows:
    if k == 1 and i == 2:
        zs = z - 0.03
        WBOX.box(E2f.M, E2f.front(uu, 0.27, zs + 0.09), (ww + 0.1, 0.2, 0.18))
        for j, du_ in enumerate((-0.33, -0.11, 0.11, 0.33)):
            geranium(E2f, uu + du_, zs + 0.06, 0.27, 70 + j, head=0.12, heads=8, tall=1.25)

# ------------------------------------------------------------------------------------------------ the costermonger's barrow
# a barrow backed against R4's front beside the stair door its owner lives up, handles down on the flags, for the morning
R4f = BLD['R4']
CBW = Acc('barrow wood', 'SURFACE • rough_wood')
CBI = Acc('barrow iron', 'IRON • soot-black lamp posts')
bu = R4f.doors[0] - 1.05            # beside the door, nearer the street's end
FLAG = 0.076                        # the flags' top above the front's foot
wheel_r, axle_out, axle_z = 0.5, 0.78, 0.5 + FLAG
# two spoked wheels, the axle running along the wall
for side in (-1, 1):
    cu_ = bu + side * 0.52
    cen = R4f.front(cu_, axle_out, axle_z)
    # tyre and felloe: a ring of short pieces
    nseg = 22
    for j in range(nseg):
        a0 = 2 * math.pi * j / nseg
        a1 = 2 * math.pi * (j + 1) / nseg
        p0 = R4f.front(cu_, axle_out + math.cos(a0) * wheel_r, axle_z + math.sin(a0) * wheel_r)
        p1 = R4f.front(cu_, axle_out + math.cos(a1) * wheel_r, axle_z + math.sin(a1) * wheel_r)
        CBI.cyl(R4f.M, p0, p1, 0.022, segs=5)
    for j in range(12):
        a = 2 * math.pi * j / 12
        p1 = R4f.front(cu_, axle_out + math.cos(a) * (wheel_r - 0.02), axle_z + math.sin(a) * (wheel_r - 0.02))
        CBW.cyl(R4f.M, cen, p1, 0.012, segs=4)
    CBW.cyl(R4f.M, R4f.front(cu_ - 0.07, axle_out, axle_z), R4f.front(cu_ + 0.07, axle_out, axle_z), 0.06, segs=10)
CBI.cyl(R4f.M, R4f.front(bu - 0.55, axle_out, axle_z), R4f.front(bu + 0.55, axle_out, axle_z), 0.02, segs=6)
# the bed, tipped: its back end up against the wall, its handles down on the flags towards the kerb
tilt = math.radians(14)
bed_len, bed_w = 1.2, 0.86
def bedp(t, across, up=0.0):
    # t along the bed from the wall end (0) to the handle end (1)
    o = 0.24 + t * bed_len * math.cos(tilt)
    zz = axle_z + 0.12 + (0.5 - t) * bed_len * math.sin(tilt) + up
    return R4f.front(bu + across, o, zz)
for j in range(5):
    acr = -bed_w / 2 + (j + 0.5) * bed_w / 5
    CBW.cyl(R4f.M, bedp(0.0, acr), bedp(1.0, acr), 0.035, segs=4)
for side in (-1, 1):
    CBW.cyl(R4f.M, bedp(0.0, side * bed_w / 2, 0.12), bedp(1.0, side * bed_w / 2, 0.12), 0.03, segs=5)      # low sides
    CBW.cyl(R4f.M, bedp(0.95, side * 0.36), R4f.front(bu + side * 0.36, 1.74, FLAG + 0.03), 0.025, segs=6)          # handles to the flags
CBW.cyl(R4f.M, bedp(0.0, -bed_w / 2, 0.12), bedp(0.0, bed_w / 2, 0.12), 0.03, segs=5)
mp_ = R4f.world(bu, 1.1, 0.0)
stain.on_ground(Vector((mp_.x, mp_.y, 0.212)), size=(0.6, 0.35), kind='mud', turn=0, strength=0.3, seed=4601,
                collection=C_FRONTS)

# ------------------------------------------------------------------------------------------------ soot on the end chimney stacks
# the end tenement's stacks stand against the sky over the hero shop: blackened down from their caps where the smoke rolls
stack_obj = bpy.data.objects.get('chimney stacks and gables')
if stack_obj is not None:
    vs_ = [stack_obj.matrix_world @ v.co for v in stack_obj.data.vertices]
    for sx_ in (E2f.obj.location.x - E2f.w / 2 + 0.25, E2f.obj.location.x + E2f.w / 2 - 0.25):
        ys_ = E2f.obj.location.y
        pts = [v for v in vs_ if abs(v.x - sx_) < 0.45 and abs(v.y - ys_) < 1.35]
        if not pts:
            continue
        top_w = max(v.z for v in pts)
        foot_w = top_w - 2.6
        ghost = box_object('stack ghost', 0.85, 2.6, top_w - foot_w, (sx_, ys_, foot_w), 0, C_FRONTS)
        ghost.hide_render = True
        ghost.display_type = 'WIRE'
        stain.on_wall(ghost, 'front', 0.0, 0.85, (top_w - foot_w) - 1.7, (top_w - foot_w) - 0.02, kind='soot', strong_at='top',
                      strength=1.3, seed=4700 + int(sx_), offset=0.012, collection=C_FRONTS, material=SOOT_FAR)
        log('fronts: soot on the stack at x %.2f, top %.2f' % (sx_, top_w))

# ------------------------------------------------------------------------------------------------ paint peeling to grey timber
def peel_paint(name, amount=0.6):
    m = store.material(name)
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        return
    inp = bs.inputs['Base Color']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = fr_node(nt, 'ShaderNodeTexNoise', Scale=3.0, Detail=8.0, Roughness=0.7)
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    low = fr_node(nt, 'ShaderNodeMapRange')                          # worse near the ground: the bottom rails
    low.inputs['From Min'].default_value, low.inputs['From Max'].default_value = 1.2, 0.2
    low.inputs['To Min'].default_value, low.inputs['To Max'].default_value = 0.0, 0.08
    nt.links.new(sep.outputs['Z'], low.inputs['Value'])
    add = fr_node(nt, 'ShaderNodeMath')
    add.operation = 'ADD'
    nt.links.new(nz.outputs['Fac'], add.inputs[0])
    nt.links.new(low.outputs[0], add.inputs[1])
    th = fr_node(nt, 'ShaderNodeMapRange')
    th.inputs['From Min'].default_value, th.inputs['From Max'].default_value = 0.585, 0.615
    th.inputs['To Max'].default_value = amount
    nt.links.new(add.outputs[0], th.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[7].default_value = (0.085, 0.075, 0.062, 1.0)        # grey weathered timber under the paint
    if inp.is_linked:
        nt.links.new(inp.links[0].from_socket, mix.inputs[6])
    else:
        mix.inputs[6].default_value = inp.default_value
    nt.links.new(th.outputs[0], mix.inputs['Factor'])
    nt.links.new(mix.outputs[2], inp)

peel_paint('WOOD • peeling dark painted doors')

def weather_stone(m, dark=0.5, streak_scale=(4.0, 4.0, 0.33), blotch_scale=0.55, overall=1.0):
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        return
    inp = bs.inputs['Base Color']
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = streak_scale
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    n1 = fr_node(nt, 'ShaderNodeTexNoise', Scale=1.0, Detail=4.0, Roughness=0.6)
    nt.links.new(mp.outputs['Vector'], n1.inputs['Vector'])
    st = fr_node(nt, 'ShaderNodeMapRange')
    st.inputs['From Min'].default_value, st.inputs['From Max'].default_value = 0.43, 0.60
    nt.links.new(n1.outputs['Fac'], st.inputs['Value'])
    n2 = fr_node(nt, 'ShaderNodeTexNoise', Scale=blotch_scale, Detail=3.0, Roughness=0.55)
    nt.links.new(geo.outputs['Position'], n2.inputs['Vector'])
    bl = fr_node(nt, 'ShaderNodeMapRange')
    bl.inputs['From Min'].default_value, bl.inputs['From Max'].default_value = 0.42, 0.62
    nt.links.new(n2.outputs['Fac'], bl.inputs['Value'])
    mx = fr_node(nt, 'ShaderNodeMath')
    mx.operation = 'MAXIMUM'
    nt.links.new(st.outputs[0], mx.inputs[0])
    nt.links.new(bl.outputs[0], mx.inputs[1])
    f = fr_node(nt, 'ShaderNodeMapRange')
    f.inputs['To Min'].default_value, f.inputs['To Max'].default_value = overall, overall * (1.0 - dark)
    nt.links.new(mx.outputs[0], f.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    if inp.is_linked:
        nt.links.new(inp.links[0].from_socket, mix.inputs[6])
    else:
        mix.inputs[6].default_value = inp.default_value
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    for k in ('X', 'Y', 'Z'):
        nt.links.new(f.outputs[0], comb.inputs[k])
    nt.links.new(comb.outputs[0], mix.inputs[7])
    nt.links.new(mix.outputs[2], inp)

FR_WEATHER = float(os.environ.get('FR_WEATHER', '0.62'))
for nn in range(12):
    weather_stone(store.material('Hand-painted sandstone • shade %02d' % nn), dark=FR_WEATHER)
# the dressings on the fronts (jambs, sills, lintels, bands, quoins) get a sooted copy; the kerbs keep theirs
TRIM_NAME = 'STONE • worn honey-grey architectural dressings'
trim_w = store.material(TRIM_NAME).copy()
trim_w.name = 'fronts dressings, sooted'
weather_stone(trim_w, dark=0.45, overall=0.88)          # lighter than the walling, so each opening's dressings still read
_tb = next((n for n in trim_w.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
if _tb is not None and not _tb.inputs['Roughness'].is_linked:
    _tb.inputs['Roughness'].default_value = min(_tb.inputs['Roughness'].default_value, 0.42)
elif _tb is not None:
    _rm = trim_w.node_tree.nodes.new('ShaderNodeMath')
    _rm.operation = 'MULTIPLY'
    _rm.inputs[1].default_value = 0.6
    trim_w.node_tree.links.new(_tb.inputs['Roughness'].links[0].from_socket, _rm.inputs[0])
    trim_w.node_tree.links.new(_rm.outputs[0], _tb.inputs['Roughness'])
n_sw = 0
for o in C_BUILD.all_objects:
    if o.type == 'MESH':
        for sl in o.material_slots:
            if sl.material is not None and sl.material.name == TRIM_NAME:
                sl.material = trim_w
                n_sw += 1
log('fronts: sooted dressings on %d slots' % n_sw)
rub = store.material('SURFACE • old_stone_wall_02')
try:
    rub.node_tree.nodes['Weather'].inputs['Grime'].default_value = max(rub.node_tree.nodes['Weather'].inputs['Grime'].default_value, 0.8)
except Exception as e:
    log('rubble grime dial: %s' % e)

for acc in (FIRON, BLIND_BUFF, BLIND_GREEN, NETS, HEM, BOARDS, NAILS, CLAYP, LEAF, FLOWER, JUG, SIGNP, SIGNB, SBW, SBI, WBOX, CBW, CBI):
    acc.make(collection=C_FRONTS)
log('fronts done')



# ------------------------------------------------------------------------------------------------ sky, air, camera
log('sky')
sky_and_haze.sky(scene, clouds=0.8, strength=1.6, seed=3)
moon = bpy.data.objects.new('moon', bpy.data.lights.new('moon', 'SUN'))
moon.data.energy = 1.0
moon.data.color = (0.50, 0.66, 1.0)
moon.data.angle = math.radians(2.5)
moon.rotation_euler = Vector((0.30, 0.62, -0.72)).to_track_quat('-Z', 'Y').to_euler()
C_LIGHT.objects.link(moon)
sky_and_haze.haze(low=(-25, -9, -0.5), high=(50, 75, 30), density=0.0032)

import smoke_ribbon
E2b = BLD['E2']
smoke = smoke_ribbon.make(start=(E2b.obj.location.x - E2b.w / 2 + 0.25, END_Y + DEPTH / 2, PAVE_Z + 18.6), facing=(2.6, -1.6, 1.62),
                  drift=(1.0, 0.3), rise=13, lean=0.7, width_start=0.7, width_end=7.0, sway=1.4, seed=4)
sm = smoke.active_material.copy()
smoke.active_material = sm
for nd in sm.node_tree.nodes:
    if nd.type == 'MAP_RANGE' and abs(nd.inputs['To Max'].default_value - 0.75) < 1e-3:
        nd.inputs['To Max'].default_value = 0.32
    if nd.type == 'MATH' and nd.operation == 'MULTIPLY':
        for i in nd.inputs:
            if not i.is_linked and abs(i.default_value - 0.08) < 1e-4:
                i.default_value = 0.0
cam = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
cam.data.lens = 24
cam.data.sensor_fit = 'AUTO'
cam.data.shift_y = -0.03
cam.location = (2.6, -1.6, 1.62)
cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
scene.collection.objects.link(cam)
scene.camera = cam

# ------------------------------------------------------------------------------------------------ each stone its own shade
def vary_per_stone(name, low, high):
    m = store.material(name)
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return
    inp = bsdf.inputs['Base Color']
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = low
    mr.inputs['To Max'].default_value = high
    nt.links.new(oi.outputs['Random'], mr.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    if inp.is_linked:
        nt.links.new(inp.links[0].from_socket, mix.inputs[6])
    else:
        mix.inputs[6].default_value = inp.default_value
    nt.links.new(mr.outputs[0], mix.inputs[7])
    nt.links.new(mix.outputs[2], inp)

vary_per_stone('COBBLES • wet basalt / broken amber-blue reflections', 0.62, 1.25)
vary_per_stone('PAVEMENT • damp sandstone slabs', 0.8, 1.15)

# ------------------------------------------------------------------------------------------------ draw and finish
store.prepare_for_render(scene)
log('drawing %dx%d at %d samples' % (WIDTH, HEIGHT, SAMPLES))
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transmission_bounces = 4
scene.cycles.volume_bounces = 0
scene.cycles.sample_clamp_indirect = 6
scene.cycles.volume_step_rate = 2.0
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
scene.render.resolution_percentage = 100
CROP = os.environ.get('CROP')          # working pictures only: 'y0,y1' draws that band of the frame (0 bottom, 1 top)
if CROP:
    c0, c1 = [float(v) for v in CROP.split(',')]
    scene.render.use_border = True
    scene.render.use_crop_to_border = False
    scene.render.border_min_x, scene.render.border_max_x = 0.0, 1.0
    scene.render.border_min_y, scene.render.border_max_y = c0, c1
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
raw = os.path.splitext(OUT)[0] + '_raw.exr'
scene.render.filepath = raw
bpy.ops.render.render(write_still=True)
log('drawn')
finish.finish(raw, OUT, exposure=1.0, bloom=1.0, veil=0.25, soften=0.45)
log('finished -> %s' % OUT)
