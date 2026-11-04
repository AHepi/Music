"""A railway goods yard at dusk after rain. Run: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png"""
import sys, os, math, random, time
KIT = '/home/claude/build-51-goodsyard/kit'
sys.path.insert(0, KIT + '/store/tools')
import bpy
import bmesh
from mathutils import Vector, Matrix, noise
import store

W = int(sys.argv[1]) if len(sys.argv) > 1 else 270
H = int(sys.argv[2]) if len(sys.argv) > 2 else 480
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 16
OUT = sys.argv[4] if len(sys.argv) > 4 else '/home/claude/build-51-goodsyard/work/preview.png'
rng = random.Random(51)
hob_hide = [False]
HAZE = float(os.environ.get('HAZE','0.0016'))
SUN = float(os.environ.get('SUN','7'))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COLL = scene.collection

# ------------------------------------------------------------------ helpers
def mk(name, base, rough=0.7, metal=0.0, var=0.25, scale=6.0, bump=0.3, base2=None, emit=None, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale; n1.inputs['Detail'].default_value = 8
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = scale * 7; n2.inputs['Detail'].default_value = 4
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    c1 = tuple(base) + (1,)
    c2 = tuple(base2 if base2 else [min(1, v * (1 + var * 2)) for v in base]) + (1,)
    mix.inputs[6].default_value = c1
    mix.inputs[7].default_value = c2
    nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    nt.links.new(n1.outputs['Fac'], mix.inputs[0])
    nt.links.new(mix.outputs[2], bs.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.01
    nt.links.new(n2.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    if coat:
        bs.inputs['Coat Weight'].default_value = coat
    if emit:
        bs.inputs['Emission Color'].default_value = tuple(emit[:3]) + (1,)
        bs.inputs['Emission Strength'].default_value = emit[3]
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    return m

MAT = {}
def M(name):
    if name not in MAT:
        MAT[name] = MATS[name]()
    return MAT[name]

def rail_mat():
    m = bpy.data.materials.new('rail'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    tcd = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 5; nz.inputs['Detail'].default_value = 8
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.55; ramp.color_ramp.elements[0].color = (0.09, 0.04, 0.025, 1)
    ramp.color_ramp.elements[1].position = 0.9; ramp.color_ramp.elements[1].color = (0.30, 0.27, 0.25, 1)
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0.3; rr.inputs['From Max'].default_value = 0.95
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.35
    nt.links.new(geo.outputs['Normal'], sep.inputs[0])
    nt.links.new(tcd.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], mul.inputs[0])
    nt.links.new(sep.outputs['Z'], add.inputs[0]); nt.links.new(mul.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bs.inputs['Base Color'])
    rgh = nt.nodes.new('ShaderNodeMapRange'); rgh.inputs['From Min'].default_value = 0.3; rgh.inputs['From Max'].default_value = 0.9; rgh.inputs['To Min'].default_value = 0.7; rgh.inputs['To Max'].default_value = 0.22
    nt.links.new(add.outputs[0], rgh.inputs['Value']); nt.links.new(rgh.outputs['Result'], bs.inputs['Roughness'])
    bs.inputs['Metallic'].default_value = 0.8
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    return m

MATS = {
 'rail': rail_mat,
 'sleeper': lambda: mk('sleeper', (0.035, 0.030, 0.026), 0.55, var=0.5, scale=3, bump=0.6, base2=(0.09, 0.075, 0.06)),
 'iron': lambda: mk('iron', (0.04, 0.035, 0.035), 0.5, 0.7, var=0.5, scale=4, bump=0.4, base2=(0.16, 0.07, 0.035)),
 'rustiron': lambda: mk('rustiron', (0.17, 0.065, 0.028), 0.6, 0.4, var=0.6, scale=5, bump=0.5, base2=(0.05, 0.03, 0.026)),
 'coal': lambda: mk('coal', (0.010, 0.010, 0.011), 0.58, 0.0, var=1.5, scale=9, bump=0.9, base2=(0.04, 0.038, 0.04)),
 'ballast': lambda: mk('ballast', (0.03, 0.032, 0.036), 0.5, var=0.8, scale=14, bump=0.9, base2=(0.13, 0.115, 0.105)),
 'timber': lambda: mk('timber', (0.07, 0.055, 0.04), 0.7, var=0.5, scale=5, bump=0.5, base2=(0.17, 0.14, 0.11)),
 'paintred': lambda: mk('paintred', (0.16, 0.035, 0.022), 0.6, var=0.5, scale=3, bump=0.5, base2=(0.05, 0.03, 0.03)),
 'paintgrey': lambda: mk('paintgrey', (0.10, 0.11, 0.11), 0.65, var=0.4, scale=3, bump=0.5, base2=(0.035, 0.04, 0.045)),
 'weed': lambda: mk('weed', (0.10, 0.12, 0.03), 0.6, var=0.8, scale=3, bump=0.0, base2=(0.28, 0.22, 0.06)),
 'sack': lambda: mk('sack', (0.12, 0.09, 0.055), 0.95, var=0.6, scale=12, bump=0.8, base2=(0.04, 0.035, 0.035)),
 'redlamp': lambda: mk('redlamp', (0.5, 0.02, 0.01), 0.3, emit=(1, 0.05, 0.02, 3.0)),
 'darktimber': lambda: mk('darktimber', (0.025, 0.022, 0.024), 0.8, var=0.4, scale=2, bump=0.3),
 'coalsack': lambda: mk('coalsack', (0.03, 0.026, 0.024), 0.9, var=1.5, scale=16, bump=1.0, base2=(0.11, 0.08, 0.05)),
 'chalk': lambda: mk('chalk', (0.5, 0.5, 0.46), 0.9, var=0.4),
}

DIALS = {
 'SURFACE • muddy_tracks': dict(Wet=0.7, Grime=0.6, Bump=1.6, Roughness=0.3, Height=0.7),
 'SURFACE • gravel_road': dict(Wet=0.7, Grime=0.5, Bump=1.0, Darken=0.22, Roughness=0.45),
 'SURFACE • old_planks_02': dict(Wet=0.6, Grime=0.8, Bump=0.8, Darken=0.5, Roughness=0.4),
 'SURFACE • wood_planks_grey': dict(Wet=0.55, Grime=0.5, Bump=0.8, Darken=0.8),
 'SURFACE • dark_brick_wall': dict(Wet=0.3, Grime=0.8, Bump=0.8),
 'SURFACE • distressed_painted_planks': dict(Wet=0.3, Grime=0.7, Bump=0.8, Darken=0.8),
 'SURFACE • hessian_380': dict(Darken=0.55, Wet=0.5, Grime=1.0, Bump=1.0, Roughness=0.8),
 'SURFACE • rough_wood': dict(Wet=0.3, Grime=0.7, Bump=0.8, Darken=0.7),
}
DIALED = {}
def surface(name):
    if name in DIALED: return DIALED[name]
    m = store.material(name)
    if name in DIALS:
        m = m.copy(); m.name = name + ' (yard)'
        w = m.node_tree.nodes['Weather']
        for k, v in DIALS[name].items():
            w.inputs[k].default_value = v
    DIALED[name] = m
    return m

def new_obj(name, bm, mat=None, smooth=False, collection=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (collection or COLL).objects.link(ob)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if mat is not None:
        me.materials.append(mat if not isinstance(mat, str) else (M(mat) if mat in MATS else surface(mat)))
    return ob

def add_box(bm, c, s, rz=0.0, taper=None):
    """box centred c, size s, rotated rz about Z (deg)."""
    mat = Matrix.Translation(c) @ Matrix.Rotation(math.radians(rz), 4, 'Z') @ Matrix.Diagonal((s[0], s[1], s[2], 1))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)

def add_box_m(bm, matrix, s):
    bmesh.ops.create_cube(bm, size=1.0, matrix=matrix @ Matrix.Diagonal((s[0], s[1], s[2], 1)))

def box_obj(name, c, s, mat, rz=0, bevel=0.0, collection=None):
    bm = bmesh.new()
    add_box(bm, Vector(c), s, rz)
    ob = new_obj(name, bm, mat, collection=collection)
    if bevel:
        md = ob.modifiers.new('bev', 'BEVEL'); md.width = bevel; md.segments = 2
    return ob

def cyl(bm, c, r, h, axis='Z', seg=16, r2=None):
    rot = {'Z': Matrix.Identity(4), 'X': Matrix.Rotation(math.radians(90), 4, 'Y'), 'Y': Matrix.Rotation(math.radians(90), 4, 'X')}[axis]
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=(r if r2 is None else r2), depth=h,
                          matrix=Matrix.Translation(c) @ rot)

def rough_blob(bm, amp, scale, seed, sq=1.0):
    for v in bm.verts:
        p = v.co
        n = noise.noise(Vector((p.x * scale + seed, p.y * scale, p.z * scale)))
        v.co += v.normal * amp * n
        v.co.x += (rng.random() - 0.5) * amp * 0.5; v.co.y += (rng.random() - 0.5) * amp * 0.5; v.co.z += (rng.random() - 0.5) * amp * 0.5

# ------------------------------------------------------------------ geometry constants
RAIL_Z = 0.15            # sleeper top
HEAD = 0.28              # top of rail head above ground
GAUGE_C = 0.7525
PLAT_X = -2.4            # platform edge
DECK_Z = 1.0
WALL_X = -6.8            # shed front wall
TRACKS = [0.0, 5.2]
LEN_Y0, LEN_Y1 = -6.0, 140.0

# ------------------------------------------------------------------ ground
def build_ground():
    bm = bmesh.new()
    # rings of grid: fine near camera, coarse far
    xs = [-80, -40, -24, -16, -12, -9, -7, -6, -5, -4.4, -4, -3.6, -3.2, -2.8, -2.4, -2, -1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6, 2, 2.4, 2.8, 3.2, 3.6, 4, 4.4, 5, 6, 7, 9, 12, 16, 24, 40, 80]
    ys = [-8 + i * 0.45 for i in range(0, 60)] + [19 + i * 1.2 for i in range(0, 30)] + [55 + i * 5 for i in range(0, 20)] + [155, 200]
    verts = []
    for y in ys:
        row = []
        for x in xs:
            z = 0.0
            far = max(abs(x), 0) 
            z = 0.06 * noise.noise(Vector((x * 0.45, y * 0.45, 1.3))) + 0.025 * noise.noise(Vector((x * 2.2, y * 2.2, 5.1)))
            # wheel ruts alongside platform foot and yard lane between track B and beyond
            z -= 0.10 * math.exp(-((x - 2.35) / 0.16) ** 2)
            z -= 0.09 * math.exp(-((x - 3.1) / 0.16) ** 2)
            z += 0.03 * math.exp(-((x - 2.7) / 0.12) ** 2)
            row.append(bm.verts.new((x, y, z)))
        verts.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    ob = new_obj('ground', bm, 'SURFACE • muddy_tracks', smooth=True)
    return ob

# ------------------------------------------------------------------ track
def build_track(cx):
    # ballast bed
    bm = bmesh.new()
    ys = [LEN_Y0 + i * 0.5 for i in range(0, int((LEN_Y1 - LEN_Y0) / 0.5) + 1)]
    profile = [(-1.95, -0.02), (-1.45, 0.07), (-1.0, 0.10), (1.0, 0.10), (1.45, 0.07), (1.95, -0.02)]
    rows = []
    for y in ys:
        row = []
        for (px, pz) in profile:
            n = noise.noise(Vector((px * 3 + cx, y * 3, 0.5)))
            row.append(bm.verts.new((cx + px, y, pz + 0.025 * n + (0.02 * noise.noise(Vector((y * 0.8, cx, 3))) if abs(px) > 1.4 else 0))))
        rows.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(profile) - 1):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    new_obj('ballast %d' % cx, bm, 'SURFACE • gravel_road', smooth=True)
    # sleepers
    bm = bmesh.new()
    y = LEN_Y0
    while y < LEN_Y1:
        jit = rng.uniform(-0.03, 0.03)
        zlift = rng.uniform(-0.015, 0.02)
        add_box(bm, Vector((cx + rng.uniform(-0.04, 0.04), y, RAIL_Z - 0.065 + zlift)), (2.6, 0.25, 0.13), rz=jit * 20)
        y += 0.78 + rng.uniform(-0.04, 0.05)
    new_obj('sleepers %d' % cx, bm, 'SURFACE • old_planks_02')
    # rails
    prof = [(-0.07, 0), (0.07, 0), (0.07, 0.025), (0.014, 0.04), (0.014, 0.09), (0.037, 0.10), (0.037, 0.12), (0.02, 0.13), (-0.02, 0.13), (-0.037, 0.12), (-0.037, 0.10), (-0.014, 0.09), (-0.014, 0.04), (-0.07, 0.025)]
    for side in (-1, 1):
        bm = bmesh.new()
        seg = [LEN_Y0]
        while seg[-1] < LEN_Y1: seg.append(seg[-1] + 9.0)
        for a, b in zip(seg[:-1], seg[1:]):
            rows = []
            for y in (a + 0.01, b - 0.01):
                rows.append([bm.verts.new((cx + side * GAUGE_C + px, y, RAIL_Z + 0.02 + pz)) for (px, pz) in prof])
            n = len(prof)
            for i in range(n):
                bm.faces.new((rows[0][i], rows[0][(i + 1) % n], rows[1][(i + 1) % n], rows[1][i]))
        new_obj('rail %d %d' % (cx, side), bm, M('rail'), smooth=False)
    # fishplates and bolts at each joint
    bm = bmesh.new(); bb = bmesh.new()
    y = LEN_Y0 + 9.0
    while y < LEN_Y1:
        for side in (-1, 1):
            for s2 in (-1, 1):
                add_box(bm, Vector((cx + side * GAUGE_C + s2 * 0.032, y, RAIL_Z + 0.02 + 0.065)), (0.015, 0.55, 0.07))
            for k in (-0.2, -0.07, 0.07, 0.2):
                cyl(bb, Vector((cx + side * GAUGE_C + 0.045, y + k, RAIL_Z + 0.02 + 0.065)), 0.013, 0.02, 'X', 6)
        y += 9.0
    new_obj('fishplates %d' % cx, bm, M('rustiron'))
    new_obj('bolts %d' % cx, bb, M('rustiron'))
    # spikes / chair dots on sleepers: little iron plates under the rails near the camera only
    bm = bmesh.new()
    y = LEN_Y0
    while y < 40:
        for side in (-1, 1):
            add_box(bm, Vector((cx + side * GAUGE_C, y + rng.uniform(-0.02, 0.02), RAIL_Z + 0.012)), (0.2, 0.2, 0.025))
        y += 0.78
    new_obj('chairs %d' % cx, bm, M('rustiron'))

# ------------------------------------------------------------------ wagon
def ring(bm, c, ro, ri, w, seg=32):
    top = []; bot = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        top.append((bm.verts.new((c.x - w / 2, c.y + ro * ca, c.z + ro * sa)), bm.verts.new((c.x - w / 2, c.y + ri * ca, c.z + ri * sa)),
                    bm.verts.new((c.x + w / 2, c.y + ro * ca, c.z + ro * sa)), bm.verts.new((c.x + w / 2, c.y + ri * ca, c.z + ri * sa))))
    for i in range(seg):
        a = top[i]; b = top[(i + 1) % seg]
        bm.faces.new((a[0], b[0], b[2], a[2]))   # outer
        bm.faces.new((a[1], a[3], b[3], b[1]))   # inner
        bm.faces.new((a[0], a[1], b[1], b[0]))   # side -
        bm.faces.new((a[2], b[2], b[3], a[3]))   # side +

def coal_wagon(x, y, length=5.2, loaded=True, seed=0, door_open=False, name='wagon'):
    r = random.Random(seed)
    paint = ['paintred', 'paintgrey'][seed % 2]
    body = bmesh.new(); strap = bmesh.new(); under = bmesh.new(); coal = bmesh.new(); buff = bmesh.new()
    wid = 2.25
    zf = 0.95   # floor top
    plank_h = 0.2
    nplank = 6
    # floor
    add_box(body, Vector((x, y, zf - 0.07)), (wid, length, 0.14))
    dark = bmesh.new(); add_box(dark, Vector((x, y, zf + 0.04 + plank_h * nplank / 2)), (wid - 0.12, length - 0.12, plank_h * nplank))
    new_obj(name + ' inner', dark, 'RECESSES • near-black blue')
    chalk = bmesh.new()
    for k in range(3):
        add_box(chalk, Vector((x - wid / 2 - 0.045, y - 0.6 + k * 0.17 + r.uniform(-0.03, 0.03), zf + 0.6 + r.uniform(-0.05, 0.05))), (0.004, 0.02, 0.22 + r.uniform(0, 0.1)), rz=0)
    add_box(chalk, Vector((x - wid / 2 - 0.044, y + 1.2, zf + 0.45)), (0.004, 0.45, 0.2))
    new_obj(name + ' chalk', chalk, M('chalk'))
    # side and end planks with relief (each plank own box, gaps, slightly different depth)
    for side in (-1, 1):
        for k in range(nplank):
            add_box(body, Vector((x + side * (wid / 2 - 0.04 + r.uniform(0, 0.012)), y, zf + 0.04 + plank_h * (k + 0.5))), (0.07 + r.uniform(0, 0.015), length - 0.02, plank_h - 0.012))
    for end in (-1, 1):
        for k in range(nplank):
            add_box(body, Vector((x, y + end * (length / 2 - 0.04 + r.uniform(0, 0.012)), zf + 0.04 + plank_h * (k + 0.5))), (wid - 0.1, 0.07 + r.uniform(0, 0.015), plank_h - 0.012))
    top = zf + 0.04 + plank_h * nplank
    # top capping rails (edges rub bright later)
    for side in (-1, 1):
        add_box(strap, Vector((x + side * (wid / 2 + 0.005), y, top + 0.02)), (0.11, length + 0.04, 0.045))
    for end in (-1, 1):
        add_box(strap, Vector((x, y + end * (length / 2 + 0.005), top + 0.02)), (wid + 0.04, 0.11, 0.045))
    # vertical iron straps with bolt heads and diagonal bracing
    nstraps = 5
    for side in (-1, 1):
        for i in range(nstraps):
            sy = y - length / 2 + 0.2 + i * (length - 0.4) / (nstraps - 1)
            add_box(strap, Vector((x + side * (wid / 2 + 0.035), sy, zf + (top - zf) / 2 + 0.02)), (0.02, 0.1, top - zf + 0.1))
        # diagonal brace on the door panel
        mid = y
        ang = math.atan2(top - zf - 0.2, length / (nstraps - 1) * 1.9)
        mat = Matrix.Translation(Vector((x + side * (wid / 2 + 0.03), mid, zf + (top - zf) / 2))) @ Matrix.Rotation(ang, 4, 'X')
        add_box_m(strap, mat, (0.018, 0.09, math.hypot(top - zf - 0.2, length / (nstraps - 1) * 1.9)))
    # headstock, solebars, springs, axle boxes
    for side in (-1, 1):
        add_box(under, Vector((x + side * (wid / 2 - 0.15), y, zf - 0.24)), (0.12, length, 0.2))
    for end in (-1, 1):
        add_box(under, Vector((x, y + end * (length / 2 + 0.04), zf - 0.2)), (wid + 0.1, 0.16, 0.22))
        # buffers
        for bx in (-0.82, 0.82):
            cyl(buff, Vector((x + bx, y + end * (length / 2 + 0.28), zf - 0.2)), 0.16, 0.04, 'Y', 14)
            cyl(buff, Vector((x + bx, y + end * (length / 2 + 0.16), zf - 0.2)), 0.045, 0.28, 'Y', 8)
        # coupling hook chain
        cyl(buff, Vector((x, y + end * (length / 2 + 0.2), zf - 0.2)), 0.025, 0.2, 'Y', 6)
    # wheels
    wheel_y = [y - length * 0.3, y + length * 0.3]
    for wy in wheel_y:
        for side in (-1, 1):
            wx = x + side * GAUGE_C
            wc = Vector((wx, wy, 0.46))
            for k in range(10):
                ang = k * math.pi / 5
                add_box_m(under, Matrix.Translation(wc) @ Matrix.Rotation(ang, 4, 'X'), (0.05, 0.035, 0.84))
            ring(under, wc, 0.47, 0.40, 0.07)
            cyl(buff, wc + Vector((side * 0.0, 0, 0)), 0.1, 0.12, 'X', 12)
        cyl(under, Vector((x, wy, 0.46)), 0.05, 1.9, 'X', 8)   # axle
        for side in (-1, 1):
            add_box(under, Vector((x + side * (GAUGE_C + 0.12), wy, 0.5)), (0.14, 0.2, 0.2))  # axle box
            add_box(under, Vector((x + side * (wid / 2 - 0.2), wy, zf - 0.42)), (0.05, 0.8, 0.07))  # spring
    # brake lever and step
    add_box(under, Vector((x + wid / 2 + 0.1, y + length * 0.42, zf - 0.38)), (0.04, 0.5, 0.05))
    add_box(under, Vector((x + wid / 2 + 0.05, y + length * 0.42, zf + 0.1)), (0.03, 0.03, 1.1))
    # coal heap
    if loaded:
        cb = bmesh.new()
        bmesh.ops.create_icosphere(cb, subdivisions=4, radius=1.0)
        for v in cb.verts:
            v.co.x *= wid / 2 - 0.1; v.co.y *= length / 2 - 0.1; v.co.z = max(v.co.z, -0.02) * 0.62 + 0.0
        rough_blob(cb, 0.09, 6.0, seed * 3.1)
        for v in cb.verts:
            v.co.z = max(v.co.z, 0)
        bmesh.ops.translate(cb, vec=(x, y, top - 0.12), verts=cb.verts)
        new_obj('%s coal' % name, cb, M('coal'), smooth=False)
        # sack of coal slumped on the ground at the wagon's foot and spill
    new_obj('%s body' % name, body, 'SURFACE • distressed_painted_planks')
    new_obj('%s straps' % name, strap, M('iron'))
    new_obj('%s under' % name, under, M('iron'))
    new_obj('%s buffers' % name, buff, M('rustiron'))

def coal_lumps(cx, cy, w, l, n, seed):
    r = random.Random(seed)
    bm = bmesh.new()
    for i in range(n):
        s = r.uniform(0.03, 0.09)
        px = cx + r.gauss(0, w); py = cy + r.uniform(-l, l)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s, matrix=Matrix.Translation((px, py, 0.1 + r.uniform(0, 0.02))) @ Matrix.Diagonal((r.uniform(.8, 1.3), r.uniform(.8, 1.3), r.uniform(.6, 1), 1)))
    for v in bm.verts:
        v.co += Vector((rng.uniform(-.012, .012), rng.uniform(-.012, .012), rng.uniform(-.012, .012)))
    new_obj('coal lumps', bm, M('coal'))

def sack(x, y, z, rot, seed, size=1.0, standing=False):
    r = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for v in bm.verts:
        if standing:
            v.co.x *= 0.20 * size; v.co.y *= 0.14 * size; v.co.z *= 0.34 * size
            if v.co.z > 0.2 * size: v.co.x *= 0.5; v.co.y *= 0.6
        else:
            v.co.x *= 0.40 * size; v.co.y *= 0.19 * size; v.co.z *= 0.12 * size
            ex = abs(v.co.x) / (0.4 * size)
            v.co.z *= (1.1 - 0.5 * ex * ex); v.co.y *= (1.0 - 0.5 * ex ** 3)
            if v.co.x > 0.28 * size:   # the tied neck
                k = (v.co.x - 0.28 * size) / (0.12 * size)
                v.co.y *= 1.0 - 0.45 * min(1, k); v.co.z *= 1.0 - 0.35 * min(1, k)
    for v in bm.verts:   # creases and folds
        p = v.co
        n = noise.noise(Vector((p.x * 7 + seed, p.y * 16, p.z * 9)))
        v.co += v.normal * (0.030 * size) * n
        v.co.z += 0.02 * size * math.sin(p.x * 22 + seed) * (1 if p.z > 0 else 0)
    rough_blob(bm, 0.010, 40.0, seed + 3)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(rot), 3, 'Z'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(x, y, z + (0.34 if standing else 0.11) * size), verts=bm.verts)
    return new_obj('sack', bm, 'SURFACE • hessian_380', smooth=True)

def trolley(x, y, rot=0, loaded=True):
    bm = bmesh.new(); fr = bmesh.new()
    M0 = Matrix.Translation((x, y, DECK_Z)) @ Matrix.Rotation(math.radians(rot), 4, 'Z')
    # deck planks
    for i in range(6):
        add_box_m(bm, M0 @ Matrix.Translation((0, -0.5 + i * 0.2 + 0.1, 0.46)), (0.62, 0.185, 0.04))
    # frame: rails under, handles at the ends, wheels
    for sx in (-0.29, 0.29):
        add_box_m(fr, M0 @ Matrix.Translation((sx, 0, 0.42)), (0.04, 1.25, 0.05))
        add_box_m(fr, M0 @ Matrix.Translation((sx, 0.55, 0.85)), (0.025, 0.025, 0.85))
        add_box_m(fr, M0 @ Matrix.Translation((sx, -0.55, 0.85)), (0.025, 0.025, 0.85))
    add_box_m(fr, M0 @ Matrix.Translation((0, 0.55, 1.27)), (0.6, 0.025, 0.025))
    add_box_m(fr, M0 @ Matrix.Translation((0, -0.55, 1.27)), (0.6, 0.025, 0.025))
    add_box_m(fr, M0 @ Matrix.Translation((0, 0.55, 0.85)), (0.6, 0.025, 0.025))
    for sx in (-0.34, 0.34):
        for sy in (-0.45, 0.45):
            c = M0 @ Vector((sx, sy, 0.22))
            cyl(fr, c, 0.21 if sy > 0 else 0.12, 0.04, 'X', 20)
    new_obj('trolley deck', bm, 'SURFACE • old_planks_02')
    new_obj('trolley frame', fr, M('iron'))

# ------------------------------------------------------------------ platform and canopy
def deck_block(x0, x1, y0, y1, name):
    """a stretch of platform: deck planks, coping on the track edge, brick face"""
    bm = bmesh.new()
    x = x1
    while x > x0 + 0.05:
        w = min(rng.uniform(0.2, 0.26), x - x0)
        add_box(bm, Vector((x - w / 2, (y0 + y1) / 2, DECK_Z - 0.04 + rng.uniform(-0.008, 0.008))), (w - 0.012, y1 - y0, 0.07))
        x -= w
    new_obj(name + ' deck', bm, 'SURFACE • wood_planks_grey')
    bm = bmesh.new()
    add_box(bm, Vector((x1 - 0.3, (y0 + y1) / 2, DECK_Z / 2 - 0.05)), (0.6, y1 - y0, DECK_Z - 0.1))
    add_box(bm, Vector(((x0 + x1) / 2, y0 + 0.3, DECK_Z / 2 - 0.05)), (x1 - x0, 0.6, DECK_Z - 0.1))
    new_obj(name + ' face', bm, 'SURFACE • dark_brick_wall')
    bm = bmesh.new()
    y = y0
    while y < y1:
        l = min(rng.uniform(0.9, 1.6), y1 - y)
        add_box(bm, Vector((x1 + 0.0 + rng.uniform(-0.01, 0.015), y + l / 2, DECK_Z + 0.005)), (0.46, l - 0.02, 0.1 + rng.uniform(-0.01, 0.01)))
        y += l
    new_obj(name + ' coping', bm, 'STONE • worn honey-grey architectural dressings')

def build_platform():
    deck_block(-16.0, PLAT_X, 7.0, 21.0, 'forecourt')
    deck_block(-4.6, PLAT_X, 21.0, 52.0, 'strip')
    # ramp down at the near end
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(PLAT_X - 0.9, 7.0, DECK_Z), (PLAT_X - 3.5, 7.0, DECK_Z), (PLAT_X - 3.5, 2.0, 0.1), (PLAT_X - 0.9, 2.0, 0.1)]]
    bm.faces.new(v)
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=0.1)
    new_obj('ramp', bm, 'SURFACE • wood_planks_grey')

import lay_boards
SHED = dict(x0=-14.5, x1=-4.5, y0=21.0, y1=27.0, h=3.0)
def build_shed():
    sx = (SHED['x0'] + SHED['x1']) / 2; sy = (SHED['y0'] + SHED['y1']) / 2
    bm = bmesh.new()
    add_box(bm, Vector((sx, sy, DECK_Z + SHED['h'] / 2)), (SHED['x1'] - SHED['x0'], SHED['y1'] - SHED['y0'], SHED['h']))
    box = new_obj('shed box', bm, 'RECESSES • near-black blue')
    openings = [('front', 'window', 5.3, 1.05, 0.9, 1.0), ('front', 'door', 6.6, 0.0, 1.4, 2.3), ('front', 'window', 8.6, 1.05, 0.9, 1.0),
                ('right', 'window', 1.3, 1.05, 0.8, 1.0), ('right', 'window', 3.6, 1.05, 0.8, 1.0)]
    made = lay_boards.lay(box, openings=openings, eaves='pitched', overhang=0.9, pitch=24, sides=['front', 'right', 'left', 'back'], seed=4)
    return made

def glow_pane(x, y, z, w, h, facing, strength=10.0, light=True, energy=40):
    bm = bmesh.new()
    if facing == 'front':
        v = [bm.verts.new((x - w / 2, y, z - h / 2)), bm.verts.new((x + w / 2, y, z - h / 2)), bm.verts.new((x + w / 2, y, z + h / 2)), bm.verts.new((x - w / 2, y, z + h / 2))]
    else:
        v = [bm.verts.new((x, y - w / 2, z - h / 2)), bm.verts.new((x, y + w / 2, z - h / 2)), bm.verts.new((x, y + w / 2, z + h / 2)), bm.verts.new((x, y - w / 2, z + h / 2))]
    bm.faces.new(v)
    m = mk('glow pane', (0.9, 0.5, 0.2), 0.4, emit=(1.0, 0.55, 0.2, strength))
    new_obj('glow pane', bm, m)
    if light:
        L = bpy.data.lights.new('pane light', 'POINT'); L.energy = energy; L.color = (1.0, 0.6, 0.28); L.shadow_soft_size = 0.2
        o = bpy.data.objects.new('pane light', L)
        o.location = (x, y - 0.8, z) if facing == 'front' else (x + 0.8, y, z)
        COLL.objects.link(o)

# ------------------------------------------------------------------ signal, tower, poles, weeds
def signal_post(x, y, h=5.2):
    bm = bmesh.new(); arm = bmesh.new(); lamp = bmesh.new(); lad = bmesh.new()
    add_box(bm, Vector((x, y, h / 2)), (0.14, 0.14, h))
    add_box(bm, Vector((x, y, 0.2)), (0.3, 0.3, 0.4))
    add_box(bm, Vector((x - 0.35, y, h - 0.2)), (0.7, 0.04, 0.04))
    for k in range(int(h / 0.35)):
        add_box(lad, Vector((x, y - 0.1, 0.5 + k * 0.35)), (0.34, 0.03, 0.03))
    for sx in (-0.17, 0.17):
        add_box(lad, Vector((x + sx, y - 0.1, h / 2)), (0.03, 0.03, h))
    # arm: lowered 30 degrees
    mat = Matrix.Translation(Vector((x - 0.05, y - 0.1, h - 0.45))) @ Matrix.Rotation(math.radians(-8), 4, 'Y')
    add_box_m(arm, mat @ Matrix.Translation((-0.7, 0, 0)), (1.4, 0.03, 0.2))
    bmesh.ops.create_cone(lamp, cap_ends=True, segments=10, radius1=0.1, radius2=0.1, depth=0.22, matrix=Matrix.Translation((x + 0.0, y - 0.18, h - 0.1)) @ Matrix.Rotation(math.radians(90), 4, 'X'))
    new_obj('signal post', bm, 'SURFACE • rough_wood')
    new_obj('signal arm', arm, M('paintred'))
    new_obj('signal ladder', lad, M('iron'))
    new_obj('signal lamp', lamp, M('redlamp'))
    L = bpy.data.lights.new('signal glow', 'POINT'); L.energy = 15; L.color = (1, 0.1, 0.04); L.shadow_soft_size = 0.1
    o = bpy.data.objects.new('signal glow', L); o.location = (x, y - 0.5, h - 0.1); COLL.objects.link(o)

def coaling_stage(x, y):
    bm = bmesh.new()
    water_tower(bm, x + 22, y - 12)
    far_shed(bm)
    far_chimney()
    add_box(bm, Vector((x, y, 11)), (7, 5, 7))            # bunker
    for lx in (-3, 3):
        for ly in (-2, 2):
            add_box(bm, Vector((x + lx, y + ly, 3.7)), (0.5, 0.5, 7.4))
    add_box(bm, Vector((x, y, 7.3)), (7.6, 5.6, 0.5))
    add_box(bm, Vector((x - 5, y, 14.8)), (3, 3, 3))
    # chute
    mat = Matrix.Translation((x + 4.5, y, 8)) @ Matrix.Rotation(math.radians(-35), 4, 'Y')
    add_box_m(bm, mat, (0.8, 1.2, 9))
    for dz in (0, 5):
        add_box(bm, Vector((x, y - 2.6, 5 + dz)), (7, 0.2, 0.2))
    cyl(bm, Vector((x + 9, y, 6)), 2.2, 8, 'Z', 16)
    for lx in (-1.6, 1.6):
        add_box(bm, Vector((x + 9 + lx, y, 1.8)), (0.4, 0.4, 3.6))
    add_box(bm, Vector((x, y, 14.7)), (7.4, 5.4, 0.3))
    add_box_m(bm, Matrix.Translation((x - 1.9, y, 15.4)) @ Matrix.Rotation(math.radians(22), 4, 'Y'), (4.1, 5.8, 0.18))
    add_box_m(bm, Matrix.Translation((x + 1.9, y, 15.4)) @ Matrix.Rotation(math.radians(-22), 4, 'Y'), (4.1, 5.8, 0.18))
    wm = mk('far window', (0.9, 0.5, 0.2), 0.4, emit=(1.0, 0.55, 0.2, 5.0))
    wb = bmesh.new(); add_box(wb, Vector((x - 5, y - 1.52, 15.0)), (0.7, 0.05, 0.8)); add_box(wb, Vector((x + 1.0, y - 2.52, 11.0)), (0.9, 0.05, 0.9))
    new_obj('far lit windows', wb, wm)
    # roof caps
    new_obj('coaling stage', bm, M('darktimber'))

def water_tower(bm, x, y):
    cyl(bm, Vector((x, y, 11.5)), 2.6, 4.0, 'Z', 18)
    cyl(bm, Vector((x, y, 14.1)), 2.6, 1.6, 'Z', 18, r2=0.1)
    for lx in (-2, 2):
        for ly in (-2, 2):
            add_box(bm, Vector((x + lx, y + ly, 4.8)), (0.35, 0.35, 9.6))
    for z in (3, 6.5):
        add_box(bm, Vector((x, y - 2.0, z)), (4.2, 0.18, 0.18)); add_box(bm, Vector((x - 2.0, y, z)), (0.18, 4.2, 0.18))

def far_chimney():
    bm = bmesh.new()
    cyl(bm, Vector((-24, 85, 12.5)), 1.1, 25, 'Z', 14, r2=0.8)
    cyl(bm, Vector((-24, 85, 25.1)), 1.0, 0.5, 'Z', 14)
    new_obj('mill chimney', bm, mk('chimney brick', (0.02, 0.014, 0.014), 0.9, var=0.3))

def far_shed(bm):
    # a long low goods shed beyond the yard on the left, a mill chimney behind it
    add_box(bm, Vector((-17, 62, 3.0)), (12, 30, 6))
    add_box_m(bm, Matrix.Translation((-19.2, 62, 7.2)) @ Matrix.Rotation(math.radians(28), 4, 'Y'), (7.0, 31.0, 0.3))
    add_box_m(bm, Matrix.Translation((-14.8, 62, 7.2)) @ Matrix.Rotation(math.radians(-28), 4, 'Y'), (7.0, 31.0, 0.3))
    for i in range(8):
        add_box(bm, Vector((-17, 49 + i * 4, 3.0)), (12.4, 0.4, 6.2))
    add_box(bm, Vector((16, 66, 4)), (10, 24, 8))
    add_box_m(bm, Matrix.Translation((13.4, 66, 9.0)) @ Matrix.Rotation(math.radians(28), 4, 'Y'), (6.0, 25.0, 0.3))
    add_box_m(bm, Matrix.Translation((18.6, 66, 9.0)) @ Matrix.Rotation(math.radians(-28), 4, 'Y'), (6.0, 25.0, 0.3))
    for k in range(6):
        add_box(bm, Vector((16, 56 + k * 4, 4.0)), (10.3, 0.4, 8.2))


def gantry(y, x0=-3.4, x1=5.6, h=8.0):
    bm = bmesh.new(); lamps = bmesh.new(); arms = bmesh.new()
    for x in (x0, x1):
        for dx in (-0.3, 0.3):
            add_box(bm, Vector((x + dx, y, h / 2)), (0.1, 0.1, h))
        for k in range(8):
            z0 = k * h / 8
            add_box_m(bm, Matrix.Translation((x, y, z0 + h / 16)) @ Matrix.Rotation(math.radians(30 if k % 2 else -30), 4, 'Y'), (0.04, 0.04, 1.3))
    for z in (h - 0.15, h - 0.9):
        add_box(bm, Vector(((x0 + x1) / 2, y, z)), (x1 - x0, 0.1, 0.1))
    n = 18
    for k in range(n):
        xa = x0 + (x1 - x0) * k / n; xb = x0 + (x1 - x0) * (k + 1) / n
        a = Vector(((xa + xb) / 2, y, h - 0.525)); sgn = 1 if k % 2 else -1
        add_box_m(bm, Matrix.Translation(a) @ Matrix.Rotation(math.radians(sgn * 45), 4, 'Y'), (0.04, 0.04, 1.1))
    for i, xs in enumerate((0.0, 5.2)):
        add_box_m(arms, Matrix.Translation((xs, y - 0.12, h + 0.35)) @ Matrix.Rotation(math.radians(-10), 4, 'Y'), (1.2, 0.03, 0.18))
        add_box(bm, Vector((xs, y, h + 0.3)), (0.1, 0.1, 0.7))
        cyl(lamps, Vector((xs + 0.0, y - 0.2, h + 0.62)), 0.09, 0.15, 'Y', 8)
    new_obj('gantry', bm, M('iron')); new_obj('gantry arms', arms, M('paintred'))
    new_obj('gantry lamps', lamps, mk('green lamp', (0.05, 0.4, 0.15), 0.3, emit=(0.1, 1.0, 0.35, 4.0)))

def coal_heap(x, y, sx=1.0, sy=0.9, sz=0.5, seed=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy; v.co.z = max(v.co.z, -0.05) * sz
    rough_blob(bm, 0.07, 6.0, seed)
    rough_blob(bm, 0.045, 26.0, seed + 5)
    for v in bm.verts: v.co.z = max(v.co.z, 0.0)
    bmesh.ops.translate(bm, vec=(x, y, 0.06), verts=bm.verts)
    new_obj('coal heap', bm, M('coal'))

def shovel(x, y, z, tilt=25, rot=0):
    bm = bmesh.new(); bl = bmesh.new()
    M0 = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot), 4, 'Z') @ Matrix.Rotation(math.radians(tilt), 4, 'X')
    add_box_m(bm, M0 @ Matrix.Translation((0, 0, 0.55)), (0.035, 0.035, 1.1))
    add_box_m(bm, M0 @ Matrix.Translation((0, 0, 1.12)), (0.2, 0.035, 0.035))
    add_box_m(bl, M0 @ Matrix.Translation((0, 0, -0.05)), (0.26, 0.02, 0.32))
    new_obj('shovel handle', bm, M('timber')); new_obj('shovel blade', bl, M('rustiron'))

def pole(x, y, z, rot, length=3.2):
    bm = bmesh.new(); hk = bmesh.new()
    M0 = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot), 4, 'Z')
    cyl(bm, Vector((0, 0, 0)), 0.035, length, 'Y', 8)
    bm.transform(M0)
    add_box_m(hk, M0 @ Matrix.Translation((0, length / 2 + 0.05, 0.03)), (0.03, 0.14, 0.03))
    add_box_m(hk, M0 @ Matrix.Translation((0, length / 2 + 0.12, 0.07)), (0.03, 0.03, 0.12))
    new_obj('shunter pole', bm, M('timber')); new_obj('pole hook', hk, M('iron'))

def smoke_ribbon():
    bm = bmesh.new()
    n = 28; rows = []
    base = Vector((-24.0, 84.0, 24.6))
    for i in range(n + 1):
        t = i / n
        h = t * 34
        cx = base.x + 0.45 * h + 2.8 * math.sin(t * 5.0) * t + 2.0 * t * t * 10
        w = 3.0 + 15.0 * t ** 0.8
        z = base.z + h
        uu = bm.verts.new((cx - w, base.y, z)); vv = bm.verts.new((cx + w, base.y, z))
        uu.co.y -= 0.3 * math.sin(i); 
        rows.append((uu, vv))
    uvl = bm.loops.layers.uv.new('uv')
    for i in range(n):
        f = bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
        for lp, (u, v) in zip(f.loops, [(0, i / n), (1, i / n), (1, (i + 1) / n), (0, (i + 1) / n)]):
            lp[uvl].uv = (u, v)
    m = bpy.data.materials.new('smoke'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    uvn = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.65
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 2.2, 1.0)
    nt.links.new(uvn.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    nt.links.new(uvn.outputs['UV'], sep.inputs[0])
    # edge fade: 1 - |2u-1|
    e1 = nt.nodes.new('ShaderNodeMath'); e1.operation = 'MULTIPLY_ADD'; e1.inputs[1].default_value = 2.0; e1.inputs[2].default_value = -1.0
    e2 = nt.nodes.new('ShaderNodeMath'); e2.operation = 'ABSOLUTE'
    e3 = nt.nodes.new('ShaderNodeMath'); e3.operation = 'SUBTRACT'; e3.inputs[0].default_value = 1.0
    e4 = nt.nodes.new('ShaderNodeMath'); e4.operation = 'MULTIPLY'; 
    nt.links.new(sep.outputs['X'], e1.inputs[0]); nt.links.new(e1.outputs[0], e2.inputs[0]); nt.links.new(e2.outputs[0], e3.inputs[1])
    nt.links.new(e3.outputs[0], e4.inputs[0]); nt.links.new(nz.outputs['Fac'], e4.inputs[1])
    # fade along height
    h1 = nt.nodes.new('ShaderNodeMath'); h1.operation = 'SUBTRACT'; h1.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs['Y'], h1.inputs[1])
    h2 = nt.nodes.new('ShaderNodeMath'); h2.operation = 'MULTIPLY'
    nt.links.new(e4.outputs[0], h2.inputs[0]); nt.links.new(h1.outputs[0], h2.inputs[1])
    ra = nt.nodes.new('ShaderNodeMapRange'); ra.inputs['From Min'].default_value = 0.12; ra.inputs['From Max'].default_value = 0.45; ra.inputs['To Max'].default_value = 0.7
    nt.links.new(h2.outputs[0], ra.inputs['Value'])
    nt.links.new(ra.outputs['Result'], bs.inputs['Alpha'])
    bs.inputs['Base Color'].default_value = (0.05, 0.06, 0.09, 1); bs.inputs['Roughness'].default_value = 1.0
    bs.inputs['Emission Color'].default_value = (1.0, 0.5, 0.2, 1)
    em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 0.10
    nt.links.new(h1.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], bs.inputs['Emission Strength'])
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    ob = new_obj('chimney smoke', bm, m, smooth=True)
    ob.visible_shadow = False

def telegraph_poles():
    bm = bmesh.new(); xarm = bmesh.new()
    pts = []
    y = 4.0
    while y < 130:
        x = 10.0 + y * 0.015
        add_box(bm, Vector((x, y, 4.2)), (0.22, 0.22, 8.4))
        add_box(xarm, Vector((x, y, 8.0)), (1.6, 0.08, 0.1))
        pts.append((x, y))
        y += 14
    new_obj('telegraph poles', bm, M('timber'))
    new_obj('telegraph arms', xarm, M('iron'))
    for off in (-0.65, -0.2, 0.2, 0.65):
        cu = bpy.data.curves.new('wire', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006; cu.bevel_resolution = 0
        for a, b in zip(pts[:-1], pts[1:]):
            sp = cu.splines.new('POLY'); sp.points.add(8)
            for i in range(9):
                t = i / 8
                sp.points[i].co = (a[0] + (b[0] - a[0]) * t + off, a[1] + (b[1] - a[1]) * t, 8.05 - 0.45 * math.sin(math.pi * t) * 1.0, 1)
        o = bpy.data.objects.new('wire', cu); COLL.objects.link(o)
        o.data.materials.append(M('iron'))

def weeds(cx, y0, y1, n, seed, xr=1.3):
    r = random.Random(seed)
    bm = bmesh.new()
    for i in range(n):
        px = cx + r.uniform(-xr, xr); py = r.uniform(y0, y1)
        for b in range(r.randint(5, 9)):
            a = r.uniform(0, 6.28); lean = r.uniform(0.05, 0.35); h = r.uniform(0.18, 0.5)
            dx, dy = math.cos(a) * lean * h, math.sin(a) * lean * h
            base = Vector((px + r.uniform(-.04, .04), py + r.uniform(-.04, .04), 0.08))
            tip = base + Vector((dx * 2, dy * 2, h))
            mid = base + Vector((dx * 0.8, dy * 0.8, h * 0.5))
            side = Vector((-dy, dx, 0)).normalized() * 0.012
            v = [bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(mid + side * 0.7), bm.verts.new(mid - side * 0.7), bm.verts.new(tip)]
            bm.faces.new((v[0], v[1], v[2], v[3])); bm.faces.new((v[3], v[2], v[4]))
    ob = new_obj('weeds', bm, M('weed'))
    return ob

# ------------------------------------------------------------------ world, camera, lights
def world_and_light():
    w = bpy.data.worlds.new('dusk'); scene.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    # use direction: world 'Generated' is the view dir mapped 0..1
    mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.9; mr.clamp = True
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    cs = ramp.color_ramp.elements
    cs[0].position = 0.0; cs[0].color = (0.85, 0.36, 0.12, 1)
    e = cs.new(0.10); e.color = (0.30, 0.15, 0.10, 1)
    e = cs.new(0.26); e.color = (0.028, 0.085, 0.15, 1)
    cs[-1].position = 1.0; cs[-1].color = (0.003, 0.025, 0.06, 1)
    bg.inputs['Strength'].default_value = 1.1
    cl = nt.nodes.new('ShaderNodeTexNoise'); cl.inputs['Scale'].default_value = 2.2; cl.inputs['Detail'].default_value = 9; cl.inputs['Roughness'].default_value = 0.6
    cm = nt.nodes.new('ShaderNodeMapping'); cm.inputs['Scale'].default_value = (1.0, 1.0, 5.0)
    nt.links.new(tc.outputs['Object'], cm.inputs['Vector']); nt.links.new(cm.outputs['Vector'], cl.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.42; cr.inputs['From Max'].default_value = 0.68; cr.inputs['To Max'].default_value = 0.8
    nt.links.new(cl.outputs['Fac'], cr.inputs['Value'])
    cmix = nt.nodes.new('ShaderNodeMix'); cmix.data_type = 'RGBA'
    nt.links.new(cr.outputs['Result'], cmix.inputs[0]); nt.links.new(ramp.outputs['Color'], cmix.inputs[6])
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = (0.35, 0.40, 0.62)
    nt.links.new(ramp.outputs['Color'], mul.inputs[0]); nt.links.new(mul.outputs[0], cmix.inputs[7])
    nt.links.new(cmix.outputs[2], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    # thin haze: a big box of scattering air (a world volume would cover the sky)
    hz = bpy.data.materials.new('haze'); hz.use_nodes = True
    hn = hz.node_tree; hn.nodes.clear()
    ho = hn.nodes.new('ShaderNodeOutputMaterial'); hs = hn.nodes.new('ShaderNodeVolumeScatter')
    hs.inputs['Density'].default_value = HAZE; hs.inputs['Color'].default_value = (0.55, 0.68, 0.8, 1); hs.inputs['Anisotropy'].default_value = 0.35
    hn.links.new(hs.outputs['Volume'], ho.inputs['Volume'])
    bm = bmesh.new(); add_box(bm, Vector((0, 85, 14)), (500, 200, 28))
    hob = new_obj('haze box', bm, hz)
    hob.visible_shadow = False
    hob.hide_render = bool(os.environ.get('TOP'))
    # low amber sun behind the far end, a little to the right
    sun = bpy.data.lights.new('low sun', 'SUN'); sun.energy = SUN; sun.color = (1.0, 0.55, 0.25); sun.angle = math.radians(2.5)
    so = bpy.data.objects.new('low sun', sun); COLL.objects.link(so)
    d = Vector((0.0, 0.0, 0.0))
    # sun sits towards +Y,+X, elevation 4 deg: direction FROM scene TO sun
    to_sun = Vector((0.3, 1.0, 0.10)).normalized()
    so.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    # cool fill from above-left
    fill = bpy.data.lights.new('sky fill', 'AREA'); fill.energy = 2500; fill.color = (0.35, 0.55, 1.0); fill.size = 30
    fo = bpy.data.objects.new('sky fill', fill); COLL.objects.link(fo); fo.location = (-10, 10, 28); fo.rotation_euler = (0, 0, 0)
    cam = bpy.data.cameras.new('cam'); cam.lens = 24; cam.sensor_width = 36; cam.sensor_fit = 'AUTO'
    co = bpy.data.objects.new('cam', cam); COLL.objects.link(co)
    co.location = (0.95, -0.5, 1.7)
    tgt = Vector((0.95, 60, 1.7 + 60 * math.tan(math.radians(1.6))))
    co.rotation_euler = (tgt - Vector(co.location)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    if os.environ.get('TOP'):
        cam.type = 'ORTHO'; cam.ortho_scale = float(os.environ.get('TOP'))
        co.location = (-3, float(os.environ.get('TOPY', '25')), 100); co.rotation_euler = (0, 0, 0)
        hob_hide[0] = True

# ------------------------------------------------------------------ build
t0 = time.time()
world_and_light()
ground = build_ground()
for cx in TRACKS:
    build_track(cx)
build_platform()
# shed
build_shed()
bm = bmesh.new()
add_box(bm, Vector((-9.0, 24.8, DECK_Z + 4.1)), (0.55, 0.55, 1.7))
add_box(bm, Vector((-9.0, 24.8, DECK_Z + 5.02)), (0.7, 0.7, 0.14))
new_obj('chimney', bm, 'SURFACE • dark_brick_wall')
bm = bmesh.new()
cyl(bm, Vector((-6.2, 24.2, DECK_Z + 4.0)), 0.07, 1.3, 'Z', 8)
cyl(bm, Vector((-6.2, 24.2, DECK_Z + 4.75)), 0.12, 0.14, 'Z', 8)
new_obj('stove pipe', bm, M('iron'))
# lit panes (the lamp-lit office window, the door left ajar, the side window)
fx = SHED['x0']
glow_pane(fx + 8.6 + 0.45, SHED['y0'] - 0.03, DECK_Z + 1.55, 0.78, 0.85, 'front', 4.5, True, 60)
glow_pane(fx + 6.6 + 1.55, SHED['y0'] - 0.04, DECK_Z + 1.2, 0.16, 2.1, 'front', 4.0, True, 30)
glow_pane(SHED['x1'] + 0.03, SHED['y0'] + 1.3 + 0.4, DECK_Z + 1.55, 0.68, 0.85, 'side', 6, True, 40)
# yard things
coal_wagon(5.2, 11.0, 5.2, True, 1, name='wagon A')
coal_wagon(5.2, 18.5, 5.2, True, 2, name='wagon B')
coal_wagon(5.2, 27.0, 5.2, False, 3, name='wagon C')
coal_wagon(5.2, 36.0, 5.2, True, 4, name='wagon D')
coal_lumps(2.7, 11, 0.3, 3.0, 30, 1)
coal_lumps(0.05, 4.5, 0.9, 1.5, 22, 2)
lamp = store.add_part('gas_lamp', location=(PLAT_X - 0.25, 10.8, DECK_Z), turn=0, seed=2, lit=True)
signal_post(2.2, 15.0)
for ly in (30.0, 48.0):
    store.add_part('gas_lamp', location=(PLAT_X - 0.25, ly, DECK_Z), turn=0, seed=ly, lit=True)

telegraph_poles()
coaling_stage(-4, 70)
weeds(0.0, 3, 30, 60, 5, 1.7)
weeds(-2.2, 7, 40, 25, 7, 0.1)
weeds(5.2, 2, 30, 40, 9, 1.8)
# loose ballast stones and clinker, packed between the sleepers and heaped on the shoulders
bm = bmesh.new()
def stones(n, ymin, ymax, power=1.0):
    for i in range(n):
        cx = rng.choice(TRACKS)
        x = cx + rng.uniform(-1.75, 1.75) * (1.0 if rng.random() < 0.7 else 1.12)
        y = ymin + (ymax - ymin) * rng.random() ** power
        edge = abs(x - cx)
        z = 0.105 if edge < 1.0 else 0.105 - (edge - 1.0) * 0.1
        r = rng.uniform(0.022, 0.065)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, 3), 4, 'Z') @ Matrix.Diagonal((rng.uniform(.8, 1.5), rng.uniform(.8, 1.3), rng.uniform(.5, .9), 1)))
stones(4200, 0.5, 12, 1.0)
stones(2600, 12, 38, 1.2)
for v in bm.verts:
    v.co += Vector((rng.uniform(-.012, .012), rng.uniform(-.012, .012), rng.uniform(-.012, .012)))
new_obj('ballast stones', bm, M('ballast'))
coal_heap(2.7, 8.8, 0.7, 0.75, 0.42, 3)
shovel(2.55, 8.45, 0.22, 28, 20)
sack(3.3, 7.6, 0.0, 70, 8, 1.3)
sack(3.0, 7.0, 0.0, 20, 9, 1.2)
sack(2.35, 7.9, 0.0, 120, 10, 1.25)
pole(-1.7, 4.2, 0.09, 6)
gantry(32, x1=7.8)
lan2 = store.add_part('hurricane_lantern', location=(2.0, 5.7, 0.0), seed=3, lit=True)
bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.type == 'LIGHT' and 'hurricane_lantern light' in o.name:
        o.data.energy = 130
        o.data.use_shadow = True
smoke_ribbon()
# a stack of loose sleepers in the lane, and one dropped across the ruts
bm = bmesh.new()
for row in range(4):
    for col in range(3 - (row // 2)):
        add_box(bm, Vector((2.55 + (col - 1 + 0.5 * (row // 2)) * 0.27 + rng.uniform(-0.02, 0.02), 17.5 + rng.uniform(-0.1, 0.1), 0.13 + row * 0.135)), (0.25, 2.6, 0.13), rz=rng.uniform(-1.5, 1.5))
add_box(bm, Vector((2.75, 12.2, 0.12)), (0.25, 2.6, 0.13), rz=72)
new_obj('loose sleepers', bm, 'SURFACE • old_planks_02')
# platform things
for i, (cy, sd) in enumerate([(9.3, 1), (9.3, 2)]):
    pass
store.add_part('crate', location=(-9.0, 20.3, DECK_Z), turn=2, seed=1, size=(0.95, 0.55, 0.5))
store.add_part('crate', location=(-8.9, 20.35, DECK_Z + 0.5), turn=-4, seed=2, size=(0.8, 0.48, 0.42))
store.add_part('hurricane_lantern', location=(-9.15, 20.3, DECK_Z + 0.92), seed=1, lit=True)
store.add_part('crate', location=(-4.55, 12.6, DECK_Z), turn=20, seed=5, size=(0.8, 0.5, 0.45))
store.add_part('crate', location=(-5.4, 13.4, DECK_Z), turn=-10, seed=6, size=(0.7, 0.45, 0.4))
for k in range(3):
    store.add_part('barrel', location=(-4.0, 23.4 + k * 0.85, DECK_Z), seed=k)
store.add_part('barrel', location=(-3.3, 22.6, DECK_Z), seed=7, lying=True, turn=90)
trolley(-4.0, 16.0, 6)
trolley(-6.8, 17.6, 30)
sack(-4.15, 15.7, DECK_Z + 0.49, 100, 1, 1.0)
sack(-3.85, 16.3, DECK_Z + 0.49, 80, 2, 0.95)
sack(-4.0, 16.0, DECK_Z + 0.62, 90, 3, 0.9)
sack(2.0, 8.0, 0.1, 40, 4)
sack(2.3, 8.45, 0.1, -10, 5, 0.9)
store.prepare_for_render(scene)
print('built in %.1fs' % (time.time() - t0))

# puddles
import puddle
for (loc, size, turn, seed) in [((0.0, 5.4, 0.12), (5.6, 1.0), 90, 1), ((0.0, 15.5, 0.12), (6.0, 0.8), 90, 2), ((2.6, 15.0, 0.0), (11.0, 1.0), 90, 3), ((2.7, 7.4, 0.0), (1.8, 0.7), 80, 11), ((2.33, 12.0, 0.0), (14.0, 0.28), 90, 12), ((3.12, 21.0, 0.0), (14.0, 0.28), 89, 13), ((2.7, 26.0, 0.0), (8.0, 0.9), 91, 4), ((5.2, 4.0, 0.12), (4.0, 1.0), 90, 6), ((-1.55, 24.0, 0.0), (4.0, 0.4), 90, 8)]:
    w_, f_ = puddle.make(loc, size=size, turn=turn, ground=None if loc[2] > 0.1 else ground, seed=seed, raggedness=(1.9 if size[0] > 8 else 1.0))

# ------------------------------------------------------------------ render
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.volume_bounces = 1
scene.cycles.volume_step_rate = 2.0
scene.cycles.sample_clamp_indirect = 8
scene.render.resolution_x = W; scene.render.resolution_y = H; scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
raw = OUT.replace('.png', '_raw.exr')
scene.render.image_settings.file_format = 'OPEN_EXR'; scene.render.image_settings.color_depth = '32'
scene.render.filepath = raw
t1 = time.time()
bpy.ops.render.render(write_still=True)
print('rendered in %.1fs' % (time.time() - t1))
import finish
FIN = dict(bloom=1.0, soften=0.4, veil=0.0)
finish.finish(raw, OUT, **FIN)
print('done', OUT)
