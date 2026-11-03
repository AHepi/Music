"""A 1915 army camp at dusk, tall frame. Run: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
Builds the scene in Blender (Cycles), draws it, then finishes the picture (glow, vignette, colour pull, soft paint)."""
import sys, math, random, time
import bpy
import bmesh
from mathutils import Vector, Euler, noise as mnoise
import numpy as np
from PIL import Image, ImageFilter

W = int(sys.argv[1]) if len(sys.argv) > 1 else 540
H = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 48
import os
OUT = os.path.abspath(sys.argv[4] if len(sys.argv) > 4 else 'test.png')
random.seed(7)
t0 = time.time()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt

def N(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n

def link(nt, a, ai, b, bi):
    nt.links.new(a.outputs[ai], b.inputs[bi])

def surf(name, ca, cb, scale=3.0, rough=0.7, metal=0.0, bump=0.3, bscale=40.0,
         boards=0.0, ribs=0.0, rust=0.0, emit=None, strength=0.0, wet=0.0):
    """Procedural old, used surface. ca/cb: two colours it varies between."""
    m, nt = new_mat(name)
    out = N(nt, 'ShaderNodeOutputMaterial')
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled')
    link(nt, bsdf, 'BSDF', out, 'Surface')
    tc = N(nt, 'ShaderNodeTexCoord')
    nz = N(nt, 'ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 6
    link(nt, tc, 'Object', nz, 'Vector')
    ramp = N(nt, 'ShaderNodeMixRGB')
    ramp.inputs['Color1'].default_value = (*ca, 1)
    ramp.inputs['Color2'].default_value = (*cb, 1)
    link(nt, nz, 'Fac', ramp, 'Fac')
    col = ramp
    if rust > 0:  # rust-orange blotches over the base
        n2 = N(nt, 'ShaderNodeTexNoise')
        n2.inputs['Scale'].default_value = scale * 1.7 + 2
        n2.inputs['Detail'].default_value = 8
        link(nt, tc, 'Object', n2, 'Vector')
        cr = N(nt, 'ShaderNodeValToRGB')
        cr.color_ramp.elements[0].position = 0.5
        cr.color_ramp.elements[1].position = 0.7
        cr.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr.color_ramp.elements[1].color = (rust, rust, rust, 1)
        link(nt, n2, 'Fac', cr, 'Fac')
        mx = N(nt, 'ShaderNodeMixRGB')
        mx.inputs['Color2'].default_value = (0.20, 0.075, 0.03, 1)
        link(nt, cr, 'Color', mx, 'Fac')
        link(nt, col, 'Color', mx, 'Color1')
        col = mx
    hsum = None
    bn = N(nt, 'ShaderNodeTexNoise')
    bn.inputs['Scale'].default_value = bscale
    bn.inputs['Detail'].default_value = 5
    link(nt, tc, 'Object', bn, 'Vector')
    hsrc = bn
    if boards > 0:
        wv = N(nt, 'ShaderNodeTexWave')
        wv.wave_type = 'BANDS'
        wv.bands_direction = 'Z'
        wv.inputs['Scale'].default_value = boards
        wv.inputs['Distortion'].default_value = 1.5
        wv.inputs['Detail'].default_value = 2
        link(nt, tc, 'Object', wv, 'Vector')
        # dark seams between boards
        cr2 = N(nt, 'ShaderNodeValToRGB')
        cr2.color_ramp.elements[0].position = 0.0
        cr2.color_ramp.elements[1].position = 0.18
        cr2.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
        cr2.color_ramp.elements[1].color = (1, 1, 1, 1)
        link(nt, wv, 'Fac', cr2, 'Fac')
        mm = N(nt, 'ShaderNodeMix')
        mm.data_type = 'RGBA'
        mm.blend_type = 'MULTIPLY'
        mm.inputs[0].default_value = 1.0
        link(nt, col, 'Color', mm, 6)
        link(nt, cr2, 'Color', mm, 7)
        col = mm
        col_out = 'Result'
        hsrc = wv
    elif ribs > 0:
        wv = N(nt, 'ShaderNodeTexWave')
        wv.wave_type = 'BANDS'
        wv.bands_direction = 'Y'
        wv.wave_profile = 'SIN'
        wv.inputs['Scale'].default_value = ribs
        wv.inputs['Distortion'].default_value = 0.3
        link(nt, tc, 'Object', wv, 'Vector')
        hsrc = wv
        col_out = 'Color'
    else:
        col_out = 'Color'
    if not (boards > 0):
        col_out = 'Color'
    link(nt, col, col_out, bsdf, 'Base Color')
    bp = N(nt, 'ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.05
    link(nt, hsrc, 'Fac', bp, 'Height')
    link(nt, bp, 'Normal', bsdf, 'Normal')
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    return m

def glow(name, color, strength):
    m, nt = new_mat(name)
    out = N(nt, 'ShaderNodeOutputMaterial')
    em = N(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = strength
    link(nt, em, 'Emission', out, 'Surface')
    return m

M = {}
M['ground'] = None  # made later (needs position colouring)
M['wood'] = surf('wood', (0.06, 0.055, 0.05), (0.11, 0.095, 0.075), 4, 0.8, bump=0.5, boards=5.5, rust=0.0)
M['hutwall'] = surf('hutwall', (0.06, 0.065, 0.065), (0.10, 0.10, 0.09), 3.5, 0.85, bump=0.6, boards=4.2)
M['roof'] = surf('roof', (0.07, 0.05, 0.045), (0.16, 0.09, 0.055), 2.2, 0.55, metal=0.6, bump=0.9, ribs=11, rust=0.85)
M['iron'] = surf('iron', (0.045, 0.045, 0.05), (0.13, 0.07, 0.04), 5, 0.6, metal=0.7, bump=0.3, rust=0.9)
M['canvas'] = surf('canvas', (0.16, 0.14, 0.10), (0.26, 0.22, 0.15), 6, 0.95, bump=0.15, bscale=120)
M['sand'] = surf('sand', (0.12, 0.10, 0.07), (0.21, 0.17, 0.11), 9, 0.95, bump=0.7, bscale=60)
M['crate'] = surf('crate', (0.09, 0.075, 0.06), (0.17, 0.13, 0.085), 5, 0.75, bump=0.5, boards=2.5)
M['paint'] = surf('paint', (0.10, 0.06, 0.04), (0.20, 0.17, 0.12), 3, 0.7, bump=0.4, rust=0.7)  # boom, peeling
M['olive'] = surf('olive', (0.10, 0.11, 0.08), (0.19, 0.18, 0.12), 4, 0.8, bump=0.3, rust=0.5)  # gun, carriage
M['dark'] = surf('dark', (0.02, 0.022, 0.026), (0.05, 0.045, 0.045), 4, 0.9, bump=0.2)
M['hill'] = surf('hill', (0.035, 0.06, 0.075), (0.06, 0.09, 0.10), 0.05, 1.0, bump=0.0)
M['hill2'] = surf('hill2', (0.07, 0.11, 0.13), (0.09, 0.13, 0.15), 0.05, 1.0, bump=0.0)
M['win'] = glow('win', (1.0, 0.5, 0.16), 6.0)
M['winhot'] = glow('winhot', (1.0, 0.55, 0.2), 8.0)
M['lamp'] = glow('lamp', (1.0, 0.55, 0.2), 7.0)
M['tentglow'] = surf('tentglow', (0.30, 0.17, 0.07), (0.40, 0.24, 0.09), 6, 0.95, bump=0.1, bscale=120,
                     emit=(1.0, 0.5, 0.18), strength=1.1)
M['flag'] = surf('flag', (0.05, 0.04, 0.045), (0.08, 0.06, 0.06), 3, 0.95, bump=0.2)

# water
mw, nt = new_mat('water')
o = N(nt, 'ShaderNodeOutputMaterial'); b = N(nt, 'ShaderNodeBsdfPrincipled')
b.inputs['Base Color'].default_value = (0.012, 0.022, 0.028, 1)
b.inputs['Roughness'].default_value = 0.04
b.inputs['Specular IOR Level'].default_value = 0.8
link(nt, b, 'BSDF', o, 'Surface')
M['water'] = mw

# ground: road mud (dark brown) blending to muddy olive verge, wet near ruts
mg, nt = new_mat('ground')
o = N(nt, 'ShaderNodeOutputMaterial'); b = N(nt, 'ShaderNodeBsdfPrincipled')
link(nt, b, 'BSDF', o, 'Surface')
tc = N(nt, 'ShaderNodeTexCoord')
sep = N(nt, 'ShaderNodeSeparateXYZ'); link(nt, tc, 'Object', sep, 'Vector')
n1 = N(nt, 'ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 2.5; n1.inputs['Detail'].default_value = 8
link(nt, tc, 'Object', n1, 'Vector')
n2 = N(nt, 'ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 14; n2.inputs['Detail'].default_value = 6
link(nt, tc, 'Object', n2, 'Vector')
absx = N(nt, 'ShaderNodeMath'); absx.operation = 'ABSOLUTE'; link(nt, sep, 'X', absx, 0)
vr = N(nt, 'ShaderNodeMapRange'); vr.inputs['From Min'].default_value = 2.8; vr.inputs['From Max'].default_value = 5.5
link(nt, absx, 0, vr, 'Value')
mud = N(nt, 'ShaderNodeMix'); mud.data_type = 'RGBA'
mud.inputs[6].default_value = (0.018, 0.02, 0.024, 1)
mud.inputs[7].default_value = (0.04, 0.041, 0.042, 1)
link(nt, n1, 'Fac', mud, 0)
verge = N(nt, 'ShaderNodeMix'); verge.data_type = 'RGBA'
verge.inputs[6].default_value = (0.06, 0.07, 0.04, 1)
verge.inputs[7].default_value = (0.10, 0.10, 0.06, 1)
link(nt, n1, 'Fac', verge, 0)
fin = N(nt, 'ShaderNodeMix'); fin.data_type = 'RGBA'
link(nt, vr, 0, fin, 0); link(nt, mud, 2, fin, 6); link(nt, verge, 2, fin, 7)
fin2 = N(nt, 'ShaderNodeMix'); fin2.data_type = 'RGBA'; fin2.blend_type = 'MULTIPLY'
fin2.inputs[0].default_value = 1.0
link(nt, fin, 2, fin2, 6)
dk = N(nt, 'ShaderNodeValToRGB')
dk.color_ramp.elements[0].position = 0.35; dk.color_ramp.elements[1].position = 0.65
dk.color_ramp.elements[0].color = (0.32, 0.33, 0.36, 1); dk.color_ramp.elements[1].color = (0.7, 0.7, 0.72, 1)
link(nt, n2, 'Fac', dk, 'Fac')
link(nt, dk, 'Color', fin2, 7)
link(nt, fin2, 2, b, 'Base Color')
rr = N(nt, 'ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.75; rr.inputs['To Max'].default_value = 0.95
link(nt, n2, 'Fac', rr, 'Value')
link(nt, rr, 0, b, 'Roughness')
bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.05
n3 = N(nt, 'ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = 16; n3.inputs['Detail'].default_value = 6
link(nt, tc, 'Object', n3, 'Vector')
link(nt, n3, 'Fac', bp, 'Height')
link(nt, bp, 'Normal', b, 'Normal')
M['ground'] = mg

# ---------------------------------------------------------------- geometry buckets
buckets = {}
def bm_of(key):
    if key not in buckets:
        buckets[key] = bmesh.new()
    return buckets[key]

def box(key, c, s, rot=(0, 0, 0)):
    """box centred at c, size s, rotated by euler rot (radians) about its centre."""
    bm = bm_of(key)
    r = bmesh.ops.create_cube(bm, size=1.0)
    verts = r['verts']
    e = Euler(rot, 'XYZ').to_matrix()
    for v in verts:
        p = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2]))
        p = e @ p
        v.co = p + Vector(c)

def cyl(key, c, radius, depth, rot=(0, 0, 0), seg=12):
    bm = bm_of(key)
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=depth)
    e = Euler(rot, 'XYZ').to_matrix()
    for v in r['verts']:
        v.co = e @ v.co + Vector(c)

def cone(key, c, r1, r2, depth, seg=24):
    bm = bm_of(key)
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth)
    for v in r['verts']:
        v.co = v.co + Vector(c)

def sphere(key, c, radius):
    bm = bm_of(key)
    r = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=radius)
    for v in r['verts']:
        v.co = v.co + Vector(c)

def beam(key, a, b, thick):
    """a stick from point a to point b."""
    a = Vector(a); b = Vector(b)
    d = b - a
    mid = (a + b) / 2
    L = d.length
    q = d.to_track_quat('X', 'Z')
    eu = q.to_euler()
    box(key, mid, (L, thick, thick), (eu.x, eu.y, eu.z))

# ---------------------------------------------------------------- ground
def hole(x, y, cx, cy, rx, ry, depth):
    return -depth * math.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))

def ground_h(x, y):
    h = 0.035 * mnoise.noise(Vector((x * 1.3, y * 1.3, 0))) + 0.018 * mnoise.noise(Vector((x * 6, y * 6, 3)))
    for cx, ph in ((-1.15, 1.0), (0.95, 2.0)):
        d = x - cx
        mod = 0.35 + 1.0 * (0.5 + 0.5 * mnoise.noise(Vector((y * 0.11, ph * 5, 1))))
        h += -0.12 * mod * math.exp(-(d / 0.24) ** 2)
    h += hole(x, y, -0.1, 9.0, 0.7, 2.6, 0.17)
    h += hole(x, y, 1.9, 17.0, 0.8, 3.5, 0.16)
    h += hole(x, y, -2.0, 6.0, 0.6, 1.6, 0.14)
    h += hole(x, y, 0.55, 4.3, 0.45, 1.3, 0.16)
    h += hole(x, y, -0.6, 2.6, 0.7, 0.9, 0.15)
    h += hole(x, y, 0.2, 26.0, 1.0, 5.0, 0.15)
    h += hole(x, y, -1.2, 40.0, 1.2, 6.0, 0.15)
    h += hole(x, y, 1.0, 55.0, 1.2, 7.0, 0.15)
    ax = abs(x)
    if ax > 3.0:
        h += min(1.0, (ax - 3.0) / 2) * (0.08 * mnoise.noise(Vector((x * 0.7, y * 0.7, 5))) + 0.06)
    return h

def spaced():
    xs = []
    x = -40.0
    while x < 40:
        xs.append(x)
        ax = abs(x)
        x += 0.07 if ax < 4.5 else (0.35 if ax < 10 else (1.2 if ax < 20 else 4))
    ys = []
    y = -3.0
    while y < 230:
        ys.append(y)
        y += 0.09 if y < 14 else (0.3 if y < 40 else (0.9 if y < 80 else 5))
    return xs, ys

xs, ys = spaced()
me = bpy.data.meshes.new('ground')
verts = []
for yv in ys:
    for xv in xs:
        verts.append((xv, yv, ground_h(xv, yv)))
faces = []
nx = len(xs)
for j in range(len(ys) - 1):
    for i in range(nx - 1):
        faces.append((j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i))
me.from_pydata(verts, [], faces)
me.update()
for p in me.polygons:
    p.use_smooth = True
gobj = bpy.data.objects.new('ground', me)
scene.collection.objects.link(gobj)
gobj.data.materials.append(M['ground'])

# water sheet (only visible where the ground dips under it)
wm_ = bpy.data.meshes.new('water')
wb = bmesh.new()
bmesh.ops.create_grid(wb, x_segments=2, y_segments=2, size=1.0)
for v in wb.verts:
    v.co = Vector((v.co.x * 7.0, v.co.y * 80 + 77, -0.085))
wb.to_mesh(wm_)
wobj = bpy.data.objects.new('water', wm_)
scene.collection.objects.link(wobj)
wobj.data.materials.append(M['water'])

# ---------------------------------------------------------------- huts
lamp_points = []   # (position, strength) of warm lights to add
def hut(x0, y0, y1, side, lit=(), door=0.5):
    """side=-1: hut on the left of the road, facing +x. side=+1: right, facing -x."""
    depth = 5.0
    xf = x0                         # road-facing wall plane
    xb = xf + side * depth           # back wall
    xc = (xf + xb) / 2
    yc = (y0 + y1) / 2
    L = y1 - y0
    wh = 2.4
    box('hutwall', (xc, yc, 0.5 + wh / 2), (depth, L, wh))
    # plinth piers
    box('dark', (xc, yc, 0.25), (depth - 0.1, L - 0.1, 0.5))
    # gable roof: two slabs
    half = depth / 2 + 0.35
    rise = 1.5
    ang = math.atan2(rise, depth / 2)
    slab = math.hypot(half, rise * half / (depth / 2))
    zr = 0.5 + wh + rise / 2 - 0.03
    for sgn in (-1, 1):
        box('roof', (xc + sgn * (depth / 4 + 0.08), yc, zr),
            (slab / 2 + 0.0, L + 0.7, 0.07), (0, sgn * ang, 0))
    # gable end boards (triangle approximated by stacked boxes)
    for k in range(5):
        wk = depth * (1 - (k + 0.5) / 5.0) * 0.98
        for ye in (y0, y1):
            box('hutwall', (xc, ye, 0.5 + wh + (k + 0.5) * rise / 5), (wk, 0.1, rise / 5 + 0.01))
    # ridge cap
    box('iron', (xc, yc, 0.5 + wh + rise + 0.02), (0.18, L + 0.75, 0.12))
    # stove pipe
    cyl('iron', (xc + side * 0.8, y0 + L * 0.3, 0.5 + wh + rise + 0.55), 0.09, 1.6, seg=8)
    cyl('iron', (xc + side * 0.8, y0 + L * 0.3, 0.5 + wh + rise + 1.4), 0.14, 0.15, seg=8)
    # door
    dy = y0 + L * door
    box('dark', (xf - side * 0.0 + 0.0, dy, 0.5 + 1.0), (0.12, 1.0, 2.0)) if False else None
    box('dark', (xf - side * 0.04, dy, 0.5 + 1.0), (0.1, 0.95, 2.0))
    box('wood', (xf - side * 0.5, dy, 0.25), (1.0, 1.4, 0.5))        # step
    box('wood', (xf - side * 0.05, dy, 0.5 + 2.08), (0.2, 1.2, 0.1))
    # windows
    wy = [y0 + L * f for f in (0.14, 0.31, 0.69, 0.86)]
    for i, y in enumerate(wy):
        if abs(y - dy) < 1.0:
            continue
        key = None
        if i in lit:
            key = 'winhot' if lit[i] else 'win'
        else:
            key = 'dark'
        box('wood', (xf - side * 0.02, y, 1.65), (0.14, 1.15, 0.95))      # frame
        box(key, (xf - side * 0.1, y, 1.65), (0.06, 0.95, 0.75))
        if key != 'dark':
            box('wood', (xf - side * 0.13, y, 1.65), (0.04, 0.05, 0.75))   # mullion
            box('wood', (xf - side * 0.13, y, 1.65), (0.04, 0.95, 0.05))
            # a light outside the window so the glow lands on the ground and wall
            lamp_points.append(((xf - side * 1.2, y, 1.4), 170 if lit[i] else 80))
    # rust streaks / vertical battens
    for k in range(int(L / 1.5) + 1):
        box('wood', (xf - side * 0.03, y0 + k * 1.5, 0.5 + wh / 2), (0.08, 0.1, wh))

hut(-4.2, 7, 19, -1, lit={1: True}, door=0.5)
hut(-4.2, 22, 34, -1, lit={2: False}, door=0.2)
hut(-4.2, 37, 49, -1, lit={0: False}, door=0.5)
hut(4.2, 12, 24, 1, lit={2: True}, door=0.15)
hut(4.2, 27, 39, 1, lit={1: False}, door=0.8)
hut(4.2, 42, 54, 1, lit={}, door=0.5)

# ---------------------------------------------------------------- hero: the watchtower at the end of the road
TY = 62.0
top = 10.0
for sx in (-1, 1):
    for sy in (-1, 1):
        a = (sx * 1.7, TY + sy * 1.7, 0)
        b = (sx * 1.15, TY + sy * 1.15, top)
        beam('wood', a, b, 0.24)
for z0, z1 in ((0.5, 3.6), (3.6, 6.8), (6.8, 10.0)):
    def w(z):  # half width at height z
        return 1.7 - 0.55 * z / top
    for sx, sy, dx, dy in ((1, 0, 0, 1), (-1, 0, 0, 1), (0, 1, 1, 0), (0, -1, 1, 0)):
        pass
    # front face braces (facing camera, y minus side)
    f = TY - 1
    beam('wood', (-w(z0), TY - w(z0), z0), (w(z1), TY - w(z1), z1), 0.13)
    beam('wood', (w(z0), TY - w(z0), z0), (-w(z1), TY - w(z1), z1), 0.13)
    for z in (z0, z1):
        box('wood', (0, TY - w(z), z), (2 * w(z), 0.16, 0.16))
        box('wood', (w(z), TY, z), (0.16, 2 * w(z), 0.16))
        box('wood', (-w(z), TY, z), (0.16, 2 * w(z), 0.16))
# cabin
box('hutwall', (0, TY, top + 1.15), (3.4, 3.4, 2.3))
box('dark', (0, TY, top - 0.05), (3.8, 3.8, 0.2))      # floor shelf
box('dark', (0, TY - 1.72, top + 1.35), (2.4, 0.06, 0.2))   # wide opening (dark slot)
box('winhot', (-0.55, TY - 1.72, top + 1.45), (0.75, 0.05, 0.6))
box('win', (0.6, TY - 1.72, top + 1.45), (0.55, 0.05, 0.5))
# hip roof (4-sided pyramid)
bmr = bm_of('roof')
pv = [Vector((-2.2, TY - 2.2, top + 2.3)), Vector((2.2, TY - 2.2, top + 2.3)),
      Vector((2.2, TY + 2.2, top + 2.3)), Vector((-2.2, TY + 2.2, top + 2.3))]
apex = Vector((0, TY, top + 3.8))
vs = [bmr.verts.new(p) for p in pv] + [bmr.verts.new(apex)]
for i in range(4):
    bmr.faces.new((vs[i], vs[(i + 1) % 4], vs[4]))
bmr.faces.new((vs[3], vs[2], vs[1], vs[0]))
# rail around cabin
box('wood', (0, TY - 1.95, top + 0.55), (3.8, 0.08, 0.1))
# ladder up the front
for sx in (-0.35, 0.35):
    box('wood', (sx, TY - 1.75, top / 2 + 0.3), (0.07, 0.07, top - 0.4), (0.1, 0, 0))
for k in range(18):
    box('wood', (0, TY - 1.75 - 0.0, 0.5 + k * 0.5), (0.7, 0.06, 0.06))
# searchlight-style lamp on a bracket and a hanging lamp at the tower foot
sphere('lamp', (1.9, TY - 2.1, top + 0.8), 0.12)
lamp_points.append(((1.9, TY - 2.5, top + 0.8), 400))
lamp_points.append(((0.0, TY - 2.6, top + 1.45), 900))
# tower base: sandbag nest + guard post
for k in range(6):
    for lvl in range(3):
        box('sand', (-3.6 + k * 0.62 + (lvl % 2) * 0.3, TY - 4.0, 0.15 + lvl * 0.28), (0.58, 0.34, 0.25),
            (0, 0, random.uniform(-0.05, 0.05)))
# flagpole + plain flag
cyl('iron', (4.2, TY + 1.0, 6.5), 0.06, 13.0, seg=6)
box('flag', (4.2, TY + 1.0 + 0.0, 11.7), (0.04, 2.0, 1.0), (0, 0, 0))
# gate posts + boom at the end of the camp road
for sx in (-1, 1):
    box('wood', (sx * 2.4, TY - 6.0, 0.9), (0.26, 0.26, 1.8))
# ---------------------------------------------------------------- tents
def tent(cx, cy, r, h, key='canvas'):
    cone(key, (cx, cy, h / 2), r, 0.12, h)
    cone('dark', (cx, cy, 0.05), r * 1.02, r * 1.02, 0.1)
    box('wood', (cx, cy - r + 0.1, 0.9), (0.6, 0.06, 1.7))
tent(-7.5, 56, 2.3, 3.3, 'tentglow')
tent(7.8, 60, 2.2, 3.1)
tent(-13, 52, 2.3, 3.3)
tent(-8, 62, 2.0, 3.0)
lamp_points.append(((-5.6, 53.5, 1.6), 70))

# ---------------------------------------------------------------- fences: posts and barbed wire
def fence(x, y0, y1):
    n = int((y1 - y0) / 2.4)
    pts = []
    for k in range(n + 1):
        y = y0 + k * 2.4
        zl = random.uniform(-0.04, 0.04)
        box('wood', (x, y, 0.75), (0.1, 0.1, 1.5), (zl, 0, 0))
        box('iron', (x, y, 1.5), (0.14, 0.14, 0.05))
        pts.append(y)
    for z in (0.35, 0.75, 1.15, 1.45):
        box('iron', (x, (y0 + y1) / 2, z), (0.015, y1 - y0, 0.015))
    # crossed wire X between posts (visible from the front)
    for k in range(n):
        beam('iron', (x, pts[k], 0.4), (x, pts[k + 1], 1.4), 0.012)
fence(-3.3, 3, 7)
fence(3.2, 4, 12)
fence(-3.3, 50, 66)
fence(3.2, 56, 68)
# a coil of barbed wire in the near right
for k in range(14):
    cyl('iron', (3.0, 8.0 + k * 0.45, 0.35), 0.32, 0.03, rot=(0, math.pi / 2, 0), seg=14)
    cyl('iron', (3.0, 8.2 + k * 0.45, 0.35), 0.30, 0.03, rot=(0, math.pi / 2, math.radians(15)), seg=14)

# ---------------------------------------------------------------- foreground: sandbags, crates, field gun, duckboards
# sandbag wall, near left
for lvl in range(4):
    for k in range(5):
        off = (lvl % 2) * 0.33
        box('sand', (-2.7 + 0.0, 7.5 + k * 0.68 + off, 0.15 + lvl * 0.27), (0.6, 0.64, 0.26),
            (random.uniform(-0.04, 0.04), 0, random.uniform(-0.05, 0.05)))
for lvl in range(3):
    for k in range(3):
        box('sand', (-2.15 + 0.0, 8.0 + k * 0.7 + (lvl % 2) * 0.33, 0.15 + lvl * 0.27), (0.6, 0.64, 0.26),
            (0, 0, random.uniform(-0.05, 0.05)))
# crates, near right
box('crate', (2.55, 8.2, 0.3), (0.9, 0.55, 0.6), (0, 0, 0.12))
box('crate', (2.4, 8.9, 0.3), (0.9, 0.55, 0.6), (0, 0, -0.1))
box('crate', (2.5, 8.5, 0.88), (0.8, 0.5, 0.55), (0, 0, 0.2))
box('crate', (1.7, 9.6, 0.22), (0.8, 0.5, 0.45), (0, 0, 0.35))
# shells (brass) - bright warm points that the sun glints on
M['brass'] = surf('brass', (0.22, 0.13, 0.05), (0.36, 0.22, 0.08), 8, 0.5, metal=0.8, bump=0.2)
for k in range(4):
    cyl('brass', (1.2 + k * 0.17, 7.0, 0.12), 0.07, 0.5, rot=(math.pi / 2, 0, 0), seg=10)
    cone('brass', (1.55 + k * 0.17, 4.7, 0.12), 0.04, 0.0, 0.0, 6) if False else None
_gun_marks = {k: len(bm.verts) for k, bm in buckets.items()}
# field gun (18-pounder): wheels, axle, trail, barrel, shield
gx, gy = -0.95, 8.6
for sx in (-1, 1):
    wx = gx + sx * 0.85
    # rim
    for k in range(20):
        a = 2 * math.pi * k / 20
        box('olive', (wx, gy + math.cos(a) * 0.75, 0.78 + math.sin(a) * 0.75), (0.1, 0.16, 0.08), (a, 0, 0))
    cyl('iron', (wx, gy, 0.78), 0.1, 0.18, rot=(0, math.pi / 2, 0), seg=10)
    for k in range(12):
        a = 2 * math.pi * k / 12
        beam('wood', (wx, gy, 0.78), (wx, gy + math.cos(a) * 0.72, 0.78 + math.sin(a) * 0.72), 0.07)
box('iron', (gx, gy, 0.78), (1.8, 0.1, 0.1))
box('olive', (gx, gy + 0.35, 1.25), (1.05, 0.07, 0.85))              # shield
box('olive', (gx, gy + 0.3, 1.72), (1.05, 0.06, 0.12), (0.3, 0, 0))   # folded top plate
beam('iron', (gx, gy + 0.1, 1.15), (gx, gy + 3.6, 2.0), 0.19)        # barrel, pointing up the road, raised
beam('iron', (gx, gy + 3.3, 1.93), (gx, gy + 3.7, 2.02), 0.26)       # muzzle swell
box('iron', (gx, gy + 0.15, 1.05), (0.4, 0.5, 0.35))                 # breech
beam('olive', (gx, gy - 0.1, 0.8), (gx + 0.1, gy - 3.4, 0.1), 0.16)   # trail, toward the camera
cyl('iron', (gx + 0.1, gy - 3.45, 0.1), 0.13, 0.12, seg=8)
for sx in (-0.5, 0.5):
    beam('wood', (gx + sx, gy + 0.3, 0.95), (gx + sx, gy + 0.3, 0.8), 0.02)


_yaw = Euler((0, 0, -0.62), 'XYZ').to_matrix()
for k, bm in buckets.items():
    bm.verts.ensure_lookup_table()
    for v in list(bm.verts)[_gun_marks.get(k, 0):]:
        v.co = _yaw @ (v.co - Vector((gx, gy, 0))) + Vector((gx, gy, 0))

# ---- near foreground (the frame is narrow here, so things sit close to the middle)
box('crate', (1.35, 4.9, 0.25), (0.62, 0.5, 0.5), (0, 0, 0.25))
box('crate', (1.7, 5.6, 0.25), (0.6, 0.5, 0.5), (0, 0, -0.15))
box('crate', (1.4, 5.1, 0.72), (0.55, 0.45, 0.42), (0, 0, 0.5))
# the lantern on the crates: flame outside, no glass around it
sphere('lamp', (1.55, 4.5, 0.62), 0.045)
lamp_points.append(((1.45, 4.2, 0.9), 9))
# shells standing in front of the crates
for k in range(4):
    sx_, sy_ = 0.8 + k * 0.16, 4.0 + (k % 2) * 0.12
    cyl('brass', (sx_, sy_, 0.24), 0.06, 0.48, seg=10)
    cone('brass', (sx_, sy_, 0.58), 0.06, 0.012, 0.2, seg=10)
# loose planks across the ruts and a coil of wire
for k, (px, py, ra) in enumerate(((0.0, 6.4, 0.2), (0.45, 7.2, -0.35), (-0.5, 7.9, 0.5))):
    box('wood', (px, py, -0.03), (1.3, 0.2, 0.05), (0, 0, ra))
for k in range(12):
    cyl('iron', (0.7 + 0.0, 2.6 + k * 0.0, 0.3), 0.3, 0.02, rot=(0, math.pi / 2 + 0.0, 0), seg=14) if False else None


# stones and mud lumps along the bottom edge (a squashed low ball, never a cube)
def lump(key, c, r, sq=0.6, rot=0.0):
    bm = bm_of(key)
    res = bmesh.ops.create_uvsphere(bm, u_segments=9, v_segments=6, radius=r)
    for v in res['verts']:
        p = Vector((v.co.x * 1.25, v.co.y, v.co.z * sq))
        p = Euler((0, 0, rot), 'XYZ').to_matrix() @ p
        v.co = p + Vector(c)
for k in range(95):
    x = random.uniform(-2.4, 2.4); y = random.uniform(1.2, 8.0)
    if abs(x - 0.95) < 0.3 or abs(x + 1.15) < 0.3 and False:
        continue
    r = random.choice([0.03, 0.04, 0.05, 0.07, 0.1]) * random.uniform(0.8, 1.2)
    lump('dark', (x, y, ground_h(x, y) + r * 0.2), r, 0.55, random.random() * 3)


# a coil of barbed wire lying across the bottom, and a low pile of sandbags
for k in range(9):
    cx_ = -1.2 + k * 0.15
    for m in range(16):
        a_ = 2 * math.pi * m / 16
        box('iron', (cx_ + 0.03 * math.sin(a_ * 2), 3.0 + math.cos(a_) * 0.26, 0.28 + math.sin(a_) * 0.26 + ground_h(cx_, 3.0) * 0.0),
            (0.025, 0.125, 0.022), (a_ + math.pi / 2, 0, 0))
for (bx_, by_, bz_, rr_) in ((1.15, 3.2, 0.1, 0.2), (1.5, 3.5, 0.1, -0.3), (1.3, 3.8, 0.1, 0.5), (1.3, 3.5, 0.32, 0.1)):
    box('sand', (bx_, by_, bz_), (0.55, 0.34, 0.22), (0.05, 0, rr_))

# duckboards along the left rut
for k in range(34):
    y = 1.5 + k * 0.38
    box('wood', (-1.95 + random.uniform(-0.03, 0.03), y, 0.0), (1.0, 0.26, 0.05),
        (random.uniform(-0.05, 0.05), random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04)))
for sx in (-2.4, -1.5):
    box('wood', (sx, 14.0, -0.02), (0.1, 26, 0.05))
# stones/rubble and a few planks in the mud
for k in range(60):
    x = random.uniform(-3.3, 3.3); y = random.uniform(5, 40)
    s = random.uniform(0.03, 0.07)
    box('dark', (x, y, ground_h(x, y) + s * 0.3), (s, s * 1.2, s * 0.7), (random.random(), random.random(), random.random()))
# oil drums along the right of the road (rusted)
for (x, y) in ((3.9, 10.0), (3.9, 10.8), (-3.9, 21.0), (3.6, 25.0), (-3.7, 51.0)):
    cyl('iron', (x, y, 0.45), 0.28, 0.9, seg=14)
# hanging lamp posts (post lamp: glass-free flame)
def lamp_post(x, y, h=2.6, power=130):
    box('wood', (x, y, h / 2), (0.12, 0.12, h))
    box('wood', (x - 0.2 * (1 if x < 0 else -1), y, h), (0.4, 0.07, 0.07))
    lx = x + 0.38 * (1 if x < 0 else -1)
    sphere('lamp', (lx, y, h - 0.15), 0.1)
    lamp_points.append(((lx - 0.1 * (1 if x < 0 else -1), y, h - 0.3), power))
lamp_post(-3.6, 9.0, 2.8, 600)
lamp_post(3.7, 20.0, 2.8, 800)
lamp_post(-3.7, 33.0, 2.8, 900)
lamp_post(3.7, 41.0, 2.8, 1000)


# ---------------------------------------------------------------- searchlight beam from the tower (a faint cone of lit haze)
bl_ = bmesh.new()
BL = 70.0
rr_ = bmesh.ops.create_cone(bl_, cap_ends=True, segments=32, radius1=0.0, radius2=5.0, depth=BL)
for v in rr_['verts']:
    v.co.z += BL / 2        # apex at local origin, opens along +z
bm_ = bpy.data.meshes.new('beam')
bl_.to_mesh(bm_)
bo = bpy.data.objects.new('beam', bm_)
bo.location = (-0.3, TY - 2.3, top + 1.4)
aim = Vector((-0.55, -0.62, 0.34)).normalized()
bo.rotation_euler = aim.to_track_quat('Z', 'Y').to_euler()
scene.collection.objects.link(bo)
bmt, nt = new_mat('beam')
o = N(nt, 'ShaderNodeOutputMaterial')
pvb = N(nt, 'ShaderNodeVolumePrincipled')
pvb.inputs['Color'].default_value = (1.0, 0.7, 0.4, 1)
pvb.inputs['Emission Color'].default_value = (1.0, 0.62, 0.3, 1)
link(nt, pvb, 'Volume', o, 'Volume')
tcb = N(nt, 'ShaderNodeTexCoord')
spb = N(nt, 'ShaderNodeSeparateXYZ'); link(nt, tcb, 'Object', spb, 'Vector')
rad = N(nt, 'ShaderNodeVectorMath'); rad.operation = 'LENGTH'
xy = N(nt, 'ShaderNodeCombineXYZ'); link(nt, spb, 'X', xy, 'X'); link(nt, spb, 'Y', xy, 'Y')
link(nt, xy, 0, rad, 0)
# radial fraction r / (z * 0.1): 0 at the axis, 1 at the cone wall
den = N(nt, 'ShaderNodeMath'); den.operation = 'MULTIPLY'; den.inputs[1].default_value = 0.0715
link(nt, spb, 'Z', den, 0)
den2 = N(nt, 'ShaderNodeMath'); den2.operation = 'MAXIMUM'; den2.inputs[1].default_value = 0.01
link(nt, den, 0, den2, 0)
fr = N(nt, 'ShaderNodeMath'); fr.operation = 'DIVIDE'
link(nt, rad, 'Value', fr, 0); link(nt, den2, 0, fr, 1)
inv = N(nt, 'ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
link(nt, fr, 0, inv, 1)
inv2 = N(nt, 'ShaderNodeMath'); inv2.operation = 'MAXIMUM'; inv2.inputs[1].default_value = 0.0
link(nt, inv, 0, inv2, 0)
sq2 = N(nt, 'ShaderNodeMath'); sq2.operation = 'POWER'; sq2.inputs[1].default_value = 2.0
link(nt, inv2, 0, sq2, 0)
# fades out along the length, brightest near the lamp
lf = N(nt, 'ShaderNodeMapRange'); lf.inputs['From Min'].default_value = 0.0; lf.inputs['From Max'].default_value = BL
lf.inputs['To Min'].default_value = 1.0; lf.inputs['To Max'].default_value = 0.15
link(nt, spb, 'Z', lf, 'Value')
bd = N(nt, 'ShaderNodeMath'); bd.operation = 'MULTIPLY'
link(nt, sq2, 0, bd, 0); link(nt, lf, 0, bd, 1)
dd = N(nt, 'ShaderNodeMath'); dd.operation = 'MULTIPLY'; dd.inputs[1].default_value = 0.03
link(nt, bd, 0, dd, 0)
link(nt, dd, 0, pvb, 'Density')
ee = N(nt, 'ShaderNodeMath'); ee.operation = 'MULTIPLY'; ee.inputs[1].default_value = 0.28
link(nt, bd, 0, ee, 0)
link(nt, ee, 0, pvb, 'Emission Strength')
bo.data.materials.append(bmt)
bo.visible_shadow = False

# ---------------------------------------------------------------- hills
def ridge(key, y, x0, x1, base, amp, seed, zbot=-20):
    bm = bm_of(key)
    n = 90
    top_ = []
    bot = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        h = base + amp * (0.5 + 0.5 * mnoise.noise(Vector((x * 0.012, seed, 0)))) \
            + amp * 0.35 * mnoise.noise(Vector((x * 0.04, seed + 9, 0)))
        top_.append(bm.verts.new((x, y, h)))
        bot.append(bm.verts.new((x, y, zbot)))
    for i in range(n):
        bm.faces.new((bot[i], bot[i + 1], top_[i + 1], top_[i]))
ridge('hill', 190, -300, 300, 5, 14, 1.3)
ridge('hill2', 300, -500, 500, 14, 26, 5.7)

# build objects
for key, bm in buckets.items():
    mesh = bpy.data.meshes.new(key)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(key, mesh)
    scene.collection.objects.link(ob)
    ob.data.materials.append(M[key])
    for p in mesh.polygons:
        p.use_smooth = key in ('canvas', 'tentglow', 'hill', 'hill2') and False

# ---------------------------------------------------------------- lights
sun_dir = Vector((0.12, 1.0, 0.0)).normalized()
elev = math.radians(5.5)
sd = Vector((sun_dir.x * math.cos(elev), sun_dir.y * math.cos(elev), math.sin(elev)))
sl = bpy.data.lights.new('sun', 'SUN')
sl.energy = 2.2
sl.color = (1.0, 0.66, 0.38)
sl.angle = math.radians(2.0)
so = bpy.data.objects.new('sun', sl)
scene.collection.objects.link(so)
# the light points from the sun toward the scene: -sd
so.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()

for (p, s) in lamp_points:
    l = bpy.data.lights.new('lamp', 'POINT')
    l.energy = s
    l.color = (1.0, 0.62, 0.28)
    l.shadow_soft_size = 0.06
    ob = bpy.data.objects.new('lamp', l)
    ob.location = p
    scene.collection.objects.link(ob)
# the lamp glow spheres sit beside lights, never around them
for (p, s) in lamp_points:
    pass

# ---------------------------------------------------------------- world: dusk sky with a low glow behind the tower
world = bpy.data.worlds.new('world')
scene.world = world
world.use_nodes = True
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
wo = N(nt, 'ShaderNodeOutputWorld')
bg = N(nt, 'ShaderNodeBackground')
link(nt, bg, 'Background', wo, 'Surface')
tc = N(nt, 'ShaderNodeTexCoord')
sep = N(nt, 'ShaderNodeSeparateXYZ')
link(nt, tc, 'Object', sep, 'Vector')
# generated for world = direction * 0.5 + 0.5 ; z=0.5 is the horizon
zr = N(nt, 'ShaderNodeMapRange')
zr.inputs['From Min'].default_value = -0.02
zr.inputs['From Max'].default_value = 0.75
zr.clamp = True
link(nt, sep, 'Z', zr, 'Value')
sky = N(nt, 'ShaderNodeValToRGB')
cs = sky.color_ramp
cs.elements[0].position = 0.0
cs.elements[0].color = (1.0, 0.42, 0.12, 1)
e1 = cs.elements.new(0.09); e1.color = (0.95, 0.38, 0.12, 1)
e2 = cs.elements.new(0.25); e2.color = (0.28, 0.27, 0.30, 1)
e3 = cs.elements.new(0.42); e3.color = (0.08, 0.20, 0.32, 1)
cs.elements[-1].position = 1.0
cs.elements[-1].color = (0.02, 0.055, 0.12, 1)
link(nt, zr, 0, sky, 'Fac')
# stronger toward the sun's side
yr = N(nt, 'ShaderNodeMapRange')
yr.inputs['From Min'].default_value = -0.2
yr.inputs['From Max'].default_value = 1.0
yr.inputs['To Min'].default_value = 0.35
yr.inputs['To Max'].default_value = 1.0
link(nt, sep, 'Y', yr, 'Value')
mulc = N(nt, 'ShaderNodeVectorMath')
mulc.operation = 'SCALE'
link(nt, sky, 'Color', mulc, 0)
link(nt, yr, 0, mulc, 'Scale')
bg.inputs['Strength'].default_value = 1.2
cmap = N(nt, 'ShaderNodeMapping')
cmap.inputs['Scale'].default_value = (1.6, 1.6, 9.0)
cmap.inputs['Location'].default_value = (3.0, 1.0, 0.0)
link(nt, tc, 'Object', cmap, 'Vector')
cn = N(nt, 'ShaderNodeTexNoise'); cn.inputs['Scale'].default_value = 1.4; cn.inputs['Detail'].default_value = 7
link(nt, cmap, 0, cn, 'Vector')
cm = N(nt, 'ShaderNodeMapRange'); cm.inputs['From Min'].default_value = 0.42; cm.inputs['From Max'].default_value = 0.68
cm.inputs['To Min'].default_value = 1.0; cm.inputs['To Max'].default_value = 0.28
link(nt, cn, 'Fac', cm, 'Value')
cmul = N(nt, 'ShaderNodeVectorMath'); cmul.operation = 'SCALE'
link(nt, mulc, 0, cmul, 0); link(nt, cm, 0, cmul, 'Scale')
link(nt, cmul, 0, bg, 'Color')

# haze volume: thin, thicker low and far
vb = bmesh.new()
bmesh.ops.create_cube(vb, size=2.0)
vm = bpy.data.meshes.new('haze')
vb.to_mesh(vm)
vo = bpy.data.objects.new('haze', vm)
vo.location = (0, 105, 7)
vo.scale = (60, 130, 7)
scene.collection.objects.link(vo)
hm, nt = new_mat('haze')
o = N(nt, 'ShaderNodeOutputMaterial')
pv_ = N(nt, 'ShaderNodeVolumeScatter')
pv_.inputs['Color'].default_value = (0.62, 0.74, 0.85, 1)
pv_.inputs['Anisotropy'].default_value = 0.15
link(nt, pv_, 'Volume', o, 'Volume')
tcn = N(nt, 'ShaderNodeTexCoord')
sp = N(nt, 'ShaderNodeSeparateXYZ'); link(nt, tcn, 'Object', sp, 'Vector')
hz = N(nt, 'ShaderNodeMapRange')
hz.inputs['From Min'].default_value = -1.0; hz.inputs['From Max'].default_value = 1.0
hz.inputs['To Min'].default_value = 1.0; hz.inputs['To Max'].default_value = 0.05
link(nt, sp, 'Z', hz, 'Value')
sq = N(nt, 'ShaderNodeMath'); sq.operation = 'POWER'; sq.inputs[1].default_value = 2.0
link(nt, hz, 0, sq, 0)
dn = N(nt, 'ShaderNodeTexNoise'); dn.inputs['Scale'].default_value = 1.5
link(nt, tcn, 'Object', dn, 'Vector')
dm = N(nt, 'ShaderNodeMath'); dm.operation = 'MULTIPLY'
dmap = N(nt, 'ShaderNodeMapRange'); dmap.inputs['To Min'].default_value = 0.6; dmap.inputs['To Max'].default_value = 1.3
link(nt, dn, 'Fac', dmap, 'Value')
link(nt, sq, 0, dm, 0); link(nt, dmap, 0, dm, 1)
dens = N(nt, 'ShaderNodeMath'); dens.operation = 'MULTIPLY'; dens.inputs[1].default_value = 0.005
link(nt, dm, 0, dens, 0)
link(nt, dens, 0, pv_, 'Density')
vo.data.materials.append(hm)
vo.visible_shadow = True

# ---------------------------------------------------------------- camera
cam = bpy.data.cameras.new('cam')
cam.lens = 36
cam.sensor_width = 24
cam.sensor_fit = 'HORIZONTAL'
cam.shift_y = -0.07
co = bpy.data.objects.new('cam', cam)
scene.collection.objects.link(co)
co.location = (0.35, -2.0, 1.65)
tgt = Vector((0.0, 80.0, 1.65 + 0.4))
co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = co

# ---------------------------------------------------------------- render settings
r = scene.render
r.engine = 'CYCLES'
r.resolution_x = W
r.resolution_y = H
r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'
r.filepath = OUT + '.raw.png'
cy = scene.cycles
cy.device = 'CPU'
cy.samples = SAMPLES
cy.use_denoising = True
try:
    cy.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
cy.max_bounces = 6
cy.diffuse_bounces = 3
cy.glossy_bounces = 4
cy.volume_bounces = 1
cy.transmission_bounces = 2
cy.volume_step_rate = 2.0
cy.volume_max_steps = 128
cy.sample_clamp_indirect = 8.0
cy.sample_clamp_direct = 0
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = 0.0
scene.render.threads = 2
bpy.ops.render.render(write_still=True)
t1 = time.time()
print('render seconds', round(t1 - t0, 1))

# ---------------------------------------------------------------- finishing (glow, vignette, colour pull, soft paint)
img = Image.open(OUT + '.raw.png').convert('RGB')
a = np.asarray(img).astype(np.float32) / 255.0
# glow: blur the bright parts and add them back
lum = a.max(axis=2)
bright = np.clip((lum - 0.55) / 0.45, 0, 1)[..., None] * a
bl = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(W / 60))
bl2 = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(W / 18))
a = a + 0.55 * np.asarray(bl).astype(np.float32) / 255 + 0.35 * np.asarray(bl2).astype(np.float32) / 255
# vignette
yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.52) / (H / 2)) ** 2)
vig = 1 - 0.38 * np.clip(d - 0.45, 0, 1) ** 1.4
a = a * vig[..., None]
# colour pull: shadows toward blue-black, lights toward amber
l2 = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
sh = np.clip(1 - l2 * 3.0, 0, 1)
a = a + sh * np.array([-0.012, 0.004, 0.022])
# dark and mid-dark warm tones lean toward cool slate; only the light itself stays amber
l3 = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
dm = np.clip(1 - l3 / 0.30, 0, 1) ** 0.7 * 0.55
slate = l3 * np.array([0.92, 1.0, 1.10])
a = a * (1 - dm) + slate * dm
a = np.clip(a, 0, 1)
out = Image.fromarray((a * 255).astype(np.uint8))
# a little soft paint: gentle median then blend with the original so edges stay crisp
soft = out.filter(ImageFilter.MedianFilter(3))
out = Image.blend(out, soft, 0.5)
out.save(OUT)
print('done', round(time.time() - t0, 1))
