# Chapel at dusk. Usage: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
import sys, os, math, random
KIT = '/home/claude/build-51-chapel/kit'
sys.path.insert(0, KIT + '/store/tools')
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler
import store, lay_stone, lay_cobbles, puddle, sky_and_haze, finish as finisher

W = int(sys.argv[1]) if len(sys.argv) > 1 else 540
H = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 32
OUT = sys.argv[4] if len(sys.argv) > 4 else 'out.png'
HERE = os.path.dirname(os.path.abspath(OUT)) or '.'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
rng = random.Random(7)

def M(name):
    return store.material(name)

IRON = M('IRON • soot-black lamp posts')
RUST = M('RUST • rain-aged iron')
WOOD = M('WOOD • peeling dark painted doors')
DRESS = M('STONE • worn honey-grey architectural dressings')
SLATE = M('SLATE • soot-dark irregular roofs')
BRASS = M('MADE • old brass')
GL_LIT = M('GLASS • warm occupied interiors')
GL_DIM = M('GLASS • dim amber rooms')
GL_DARK = M('GLASS • sleeping navy interiors')
RECESS = M('RECESSES • near-black blue')
BOARDS = M('MADE • weathered boards, peeling paint')

def tint(mat, rgb):
    """multiply a material's base colour by rgb (darken / cool it)"""
    nt = mat.node_tree
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            inp = n.inputs['Base Color']
            mx = nt.nodes.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0
            mx.inputs['B'].default_value = (*rgb, 1)
            if inp.is_linked:
                src = inp.links[0].from_socket
                nt.links.new(src, mx.inputs['A'])
            else:
                mx.inputs['A'].default_value = inp.default_value
            nt.links.new(mx.outputs['Result'], inp)
            break

for k in range(12):
    tint(M('Hand-painted sandstone • shade %02d' % k), (0.62, 0.68, 0.78))
tint(DRESS, (0.78, 0.84, 0.92))
tint(M('PAVEMENT • damp sandstone slabs'), (0.55, 0.6, 0.66))
tint(M('COBBLES • wet basalt / broken amber-blue reflections'), (0.5, 0.54, 0.6))
store.material('SURFACE • old_stone_wall_02').node_tree.nodes['Weather'].inputs['Darken'].default_value = 0.7


def glow_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    tcn = nt.nodes.new('ShaderNodeTexCoord')
    sp = nt.nodes.new('ShaderNodeSeparateXYZ')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 5.0
    mr_ = nt.nodes.new('ShaderNodeMapRange')
    mr_.inputs['From Min'].default_value = 0.0
    mr_.inputs['From Max'].default_value = 1.0
    mr_.inputs['To Min'].default_value = 0.55
    mr_.inputs['To Max'].default_value = 1.15
    nt.links.new(tcn.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], mr_.inputs['Value'])
    mu = nt.nodes.new('ShaderNodeMath')
    mu.operation = 'MULTIPLY'
    mu.inputs[1].default_value = strength
    nt.links.new(mr_.outputs['Result'], mu.inputs[0])
    nt.links.new(mu.outputs[0], e.inputs['Strength'])
    nt.links.new(e.outputs[0], o.inputs[0])
    return m
WIN_GLOW = glow_mat('window glow', (1.0, 0.5, 0.14), 2.6)


def slate_courses():
    m = bpy.data.materials.new('slate courses')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.32
    tcn = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(90))
    nt.links.new(tcn.outputs['Object'], mp.inputs['Vector'])
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (0.035, 0.045, 0.055, 1)
    br.inputs['Color2'].default_value = (0.075, 0.085, 0.10, 1)
    br.inputs['Mortar'].default_value = (0.008, 0.01, 0.012, 1)
    br.inputs['Scale'].default_value = 1.3
    br.inputs['Mortar Size'].default_value = 0.025
    br.inputs['Mortar Smooth'].default_value = 0.1
    br.inputs['Brick Width'].default_value = 0.6
    br.inputs['Row Height'].default_value = 0.3
    br.offset = 0.5
    nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.2
    nz.inputs['Detail'].default_value = 8.0
    nt.links.new(tcn.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.blend_type = 'MULTIPLY'
    mx.inputs['Factor'].default_value = 0.9
    nt.links.new(br.outputs['Color'], mx.inputs['A'])
    nt.links.new(nz.outputs['Color'], mx.inputs['B'])
    nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.6
    bp.inputs['Distance'].default_value = 0.01
    nt.links.new(br.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
ROOF = slate_courses()

def simple_mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

ZINC = simple_mat('zinc', (0.16, 0.19, 0.21), 0.45, 0.8)
TWIG = simple_mat('birch twigs', (0.16, 0.10, 0.05), 0.9)
ASH = simple_mat('ash handle', (0.2, 0.14, 0.08), 0.7)
CLOTH = simple_mat('umbrella cloth', (0.02, 0.025, 0.03), 0.8)
TIN = simple_mat('milk can tin', (0.12, 0.13, 0.12), 0.5, 0.7)
GRASS_MAT = None

def obj_from(name, verts, faces, mat=None, smooth=False, collection=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (collection or scene.collection).objects.link(ob)
    if mat is not None:
        ob.data.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob

def box(name, c, s, mat, rot=(0, 0, 0)):
    """box centred c with full size s, rotated (euler xyz radians) about its centre"""
    sx, sy, sz = s[0] / 2, s[1] / 2, s[2] / 2
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mx = Matrix.Translation(c) @ Euler(rot).to_matrix().to_4x4()
    v = [tuple(mx @ Vector(p)) for p in v]
    return obj_from(name, v, f, mat)

def cyl(name, c, r, h, mat, seg=16, r2=None, rot=(0, 0, 0), smooth=True):
    r2 = r if r2 is None else r2
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r * math.cos(a), r * math.sin(a), -h / 2))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r2 * math.cos(a), r2 * math.sin(a), h / 2))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    f.append(tuple(reversed(range(seg))))
    f.append(tuple(range(seg, 2 * seg)))
    mx = Matrix.Translation(c) @ Euler(rot).to_matrix().to_4x4()
    v = [tuple(mx @ Vector(p)) for p in v]
    return obj_from(name, v, f, mat, smooth=smooth)

def merge(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]

def rotz(ob, deg, about=None):
    pass

# ------------------------------------------------------------------ ground
def plane(name, x0, x1, y0, y1, z, mat=None):
    return obj_from(name, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [(0, 1, 2, 3)], mat)

GARDEN_Z = -0.05
garden = plane('garden', -40, 40, 2.3, 90, GARDEN_Z)
# subdivide for bump
road = plane('road', -9, 9, -14, 2.2, 0.0)
side_ground = plane('lane edges', -40, 40, -40, 2.3, -0.3)
FLAG_X = 1.3
path = plane('forecourt path', -FLAG_X, FLAG_X, 2.4, 10.45, 0.0)

# ------------------------------------------------------------------ chapel
CH_W, CH_Y0, CH_D, CH_H, BASE = 7.0, 11.5, 12.0, 5.0, 0.45
TOP = BASE + CH_H
wall = box('chapel wall', (0, CH_Y0 + CH_D / 2, BASE + CH_H / 2), (CH_W, CH_D, CH_H), None)
found = box('foundation', (0, CH_Y0 + CH_D / 2 - 0.05, BASE / 2), (CH_W + 0.5, CH_D + 0.2, BASE), None)
store.use_material(found, 'SURFACE • old_stone_wall_02', ground=0)

front_open = [('front', 'door', 2.6, 0.0, 1.8, 2.85),
              ('front', 'window', 0.7, 1.3, 0.9, 2.4), ('front', 'window', 5.4, 1.3, 0.9, 2.4)]
stonework = lay_stone.lay(wall, openings=front_open, seed=11, sides=['front'], fill=False)

def face_y():
    return CH_Y0

def window(cx, bottom, w, h, y, lit, turn=0, name='window'):
    """joinery in the opening of a front wall (face at y)"""
    parts = []
    gz = BASE + bottom
    gm = WIN_GLOW if lit == 2 else (GL_DIM if lit == 1 else GL_DARK)
    parts.append(box(name + ' glass', (cx, y + 0.04, gz + h / 2), (w - 0.1, 0.03, h - 0.1), gm))
    fr = 0.07
    sz = 0.1
    yy = y + 0.0
    parts.append(box(name + ' top', (cx, yy, gz + h - 0.04), (w, sz, 0.08), WOOD))
    parts.append(box(name + ' bottom', (cx, yy, gz + 0.04), (w, sz, 0.08), WOOD))
    parts.append(box(name + ' left', (cx - w / 2 + 0.04, yy, gz + h / 2), (0.08, sz, h), WOOD))
    parts.append(box(name + ' right', (cx + w / 2 - 0.04, yy, gz + h / 2), (0.08, sz, h), WOOD))
    parts.append(box(name + ' mullion', (cx, yy, gz + h / 2), (0.04, 0.06, h), WOOD))
    for k in (1, 2, 3, 4):
        parts.append(box(name + ' bar', (cx, yy, gz + h * k / 5), (w, 0.06, 0.035), WOOD))
    return parts

lights_pending = []
fx = [(-2.35, 2), (2.35, 0)]
for i, (cx, lit) in enumerate(fx):
    window(cx, 1.3, 0.9, 2.4, CH_Y0 - 0.1, lit, name='front window %d' % i)

# door: opening x -0.9..0.9, height 2.85, sill at BASE. Interior glow behind.
DOOR_H = 2.85
inner = box('interior glow', (0, CH_Y0 - 0.04, BASE + DOOR_H / 2), (1.8, 0.05, DOOR_H), None)
em = bpy.data.materials.new('chapel interior glow')
em.use_nodes = True
nt = em.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
o = nt.nodes.new('ShaderNodeOutputMaterial')
e = nt.nodes.new('ShaderNodeEmission')
e.inputs['Color'].default_value = (1.0, 0.42, 0.10, 1)
e.inputs['Strength'].default_value = 3.2
# gradient so the glow isn't flat: brighter low
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
mr = nt.nodes.new('ShaderNodeMapRange')
mr.inputs['From Min'].default_value = -1.4
mr.inputs['From Max'].default_value = 1.4
mr.inputs['To Min'].default_value = 1.6
mr.inputs['To Max'].default_value = 0.25
nt.links.new(tc.outputs['Object'], sep.inputs[0])
nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
nt.links.new(mr.outputs['Result'], e.inputs['Strength'])
nt.links.new(e.outputs[0], o.inputs[0])
inner.data.materials.append(em)
# pews seen through the doorway: dark benches
for k in range(3):
    box('pew back %d' % k, (0.0, CH_Y0 + 0.75 - 0.0, BASE + 0.55), (1.5, 0.05, 0.05), WOOD) if False else None
# floor inside the doorway (a lit boarded floor glimpse) and the side wall reveal
box('interior floor', (0, CH_Y0 - 0.2, BASE + 0.01), (1.8, 0.4, 0.02), WOOD)
for k, px in enumerate((-0.5, 0.5)):
    box('pew end %d' % k, (px, CH_Y0 - 0.12, BASE + 0.4), (0.07, 0.06, 0.8), WOOD)
box('pew rail', (0, CH_Y0 - 0.12, BASE + 0.8), (1.0, 0.05, 0.05), WOOD)
# the doors: left leaf closed, right leaf swung open outwards
def leaf(name, hinge_x, width, angle_deg, side):
    # a leaf of boarded timber with iron straps; built at the hinge, then turned about the hinge
    parts = []
    h = 2.45
    parts.append(box(name + ' boards', (side * width / 2, 0, h / 2), (width, 0.06, h), WOOD))
    for k in range(5):
        parts.append(box(name + ' batten', (side * width * (k + 0.5) / 5, -0.04, h / 2), (0.012, 0.01, h), RECESS))
    for zz in (0.5, 1.2, 1.9):
        parts.append(box(name + ' strap', (side * width / 2.4, -0.04, zz), (width * 0.85, 0.015, 0.09), IRON))
    parts.append(box(name + ' handle', (side * (width - 0.12), -0.07, 1.15), (0.03, 0.05, 0.16), BRASS))
    ob = merge(parts, name)
    ob.location = (hinge_x, CH_Y0 - 0.1, BASE)
    ob.rotation_euler = (0, 0, math.radians(angle_deg))
    return ob
leaf('door left', -0.9, 0.9, 0, 1)
leaf('door right', 0.9, 0.9, -105, -1)
# transom bar and fanlight
box('transom', (0, CH_Y0 - 0.1, BASE + 2.5), (1.8, 0.1, 0.08), WOOD)
fan = box('fanlight glass', (0, CH_Y0 - 0.06, BASE + 2.68), (1.7, 0.03, 0.28), GL_LIT)
for k in range(-4, 5):
    box('fan bar', (k * 0.19, CH_Y0 - 0.1, BASE + 2.68), (0.03, 0.06, 0.3), WOOD)

# date plaque (blank) over the door, sill ledge
box('plaque', (0, CH_Y0 - 0.28, BASE + 3.75), (1.3, 0.1, 0.55), DRESS)
box('plaque ledge', (0, CH_Y0 - 0.3, BASE + 3.43), (1.5, 0.14, 0.07), DRESS)
box('plaque cap', (0, CH_Y0 - 0.3, BASE + 4.08), (1.5, 0.14, 0.07), DRESS)

# steps (stone), three treads
for k, (yy, zz, wd) in enumerate(((11.15, 0.45, 3.4), (10.8, 0.30, 3.6), (10.45, 0.15, 3.8))):
    st = box('step %d' % k, (0, yy + 0.2, zz / 2), (wd, 0.75 if k == 0 else 0.35, zz), DRESS)
    store.use_material(st, DRESS, ground=0) if False else None

# gable: triangle of stone in front of the roof end
GZ0 = TOP + 0.05
APEX_Z = GZ0 + (CH_W / 2) * math.tan(math.radians(38))
gv = [(-CH_W / 2, 11.3, GZ0), (CH_W / 2, 11.3, GZ0), (0, 11.3, APEX_Z),
      (-CH_W / 2, 11.9, GZ0), (CH_W / 2, 11.9, GZ0), (0, 11.9, APEX_Z)]
gable = obj_from('gable', gv, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)])
store.use_material(gable, 'SURFACE • old_stone_wall_02', ground=TOP)
# gable tie band
box('gable band', (0, 11.22, GZ0 + 0.03), (CH_W + 0.2, 0.2, 0.14), DRESS)
# rose window (lit, dim) and stone ring
rw_z = GZ0 + 1.45
rose = cyl('rose glass', (0, 11.22, rw_z), 0.42, 0.04, GL_DIM, seg=24, rot=(math.pi / 2, 0, 0))
ring = cyl('rose ring', (0, 11.26, rw_z), 0.58, 0.12, DRESS, seg=24, rot=(math.pi / 2, 0, 0))
ring.scale = (1, 1, 1)
for k in range(8):
    a = k * math.pi / 4
    box('rose spoke', (0.4 * math.cos(a) * 0.5 * 2 / 2, 11.19, rw_z + 0.2 * math.sin(a) * 2), (0.03, 0.03, 0.03), WOOD) if False else None
box('rose bar a', (0, 11.19, rw_z), (0.84, 0.04, 0.04), WOOD)
box('rose bar b', (0, 11.19, rw_z), (0.04, 0.04, 0.84), WOOD)
# louvred opening (gable vent) above rose
# roof: two slate slopes with overhang, deep eaves
PITCH = math.radians(38)
OVER = 0.65
roof_y0, roof_y1 = 10.85, CH_Y0 + CH_D + 0.6
rl = roof_y1 - roof_y0
slope_len = (CH_W / 2 + OVER) / math.cos(PITCH)
under_apex = GZ0 + (CH_W / 2) * math.tan(PITCH) + 0.02
eave_x = CH_W / 2 + OVER
roofs = []
for sgn in (-1, 1):
    # centre of the slope's underside
    cxm = sgn * eave_x / 2
    czm = under_apex - (eave_x / 2) * math.tan(PITCH)
    nx, nz = sgn * math.sin(PITCH), math.cos(PITCH)  # slope normal
    th = 0.16
    c = Vector((cxm + nx * th / 2, (roof_y0 + roof_y1) / 2, czm + nz * th / 2))
    r = box('roof slope', c, (slope_len, rl, th), ROOF, rot=(0, sgn * PITCH, 0))
    roofs.append(r)
    # eave fascia
    ex, ez = sgn * eave_x, under_apex - eave_x * math.tan(PITCH)
    box('fascia', (ex + nx * 0.05 * 0 , (roof_y0 + roof_y1) / 2, ez + 0.04), (0.05, rl, 0.22), BOARDS)
    # barge board along the front rake
    bc = Vector((cxm + nx * (th + 0.05), roof_y0 - 0.02, czm + nz * (th + 0.05)))
    box('barge board', bc, (slope_len + 0.1, 0.05, 0.3), BOARDS, rot=(0, sgn * PITCH, 0))
# ridge capping
box('ridge', (0, (roof_y0 + roof_y1) / 2, under_apex + 0.17), (0.28, rl + 0.05, 0.12), IRON)
# bellcote on the front apex
bz = APEX_Z + 0.08
box('bell base', (0, 11.55, bz + 0.1), (0.7, 0.5, 0.2), DRESS)
for sx in (-0.26, 0.26):
    box('bellcote post', (sx, 11.55, bz + 0.65), (0.1, 0.1, 0.9), WOOD)
box('bellcote beam', (0, 11.55, bz + 1.1), (0.7, 0.14, 0.1), WOOD)
cyl('bell', (0, 11.55, bz + 0.75), 0.17, 0.3, BRASS, seg=16, r2=0.07)
pv = [(-0.5, 11.25, bz + 1.15), (0.5, 11.25, bz + 1.15), (0.5, 11.85, bz + 1.15), (-0.5, 11.85, bz + 1.15), (0, 11.55, bz + 1.65)]
obj_from('bellcote roof', pv, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)], SLATE)

# ------------------------------------------------------------------ chimney (brick) behind the right slope
def chimney(x, y, base_z, top_z, w=0.75):
    b = box('chimney', (x, y, (base_z + top_z) / 2), (w, w, top_z - base_z), None)
    store.use_material(b, 'SURFACE • dark_brick_wall', ground=base_z)
    box('chimney cap', (x, y, top_z + 0.08), (w + 0.2, w + 0.2, 0.16), DRESS)
    for k in (-1, 1):
        for j in (-1, 1):
            cyl('pot', (x + k * 0.17, y + j * 0.17, top_z + 0.35), 0.1, 0.4, RUST, seg=10, r2=0.08)
chimney(2.0, 16.5, 6.0, 9.2)

# vestry lean-to on the right
VX0, VX1, VY0, VD, VH = 3.6, 7.3, 12.6, 5.5, 3.1
vwall = box('vestry wall', ((VX0 + VX1) / 2, VY0 + VD / 2, VH / 2), (VX1 - VX0, VD, VH), None)
lay_stone.lay(vwall, openings=[('front', 'window', 0.6, 1.0, 0.8, 1.4), ('front', 'door', 2.4, 0.0, 0.9, 2.0)],
              seed=5, sides=['front'], fill=False, quoins=True)
window(VX0 + 0.6 + 0.4, 1.0 - BASE, 0.8, 1.4, VY0 + 0.02, 2, name='vestry window') if False else None
vg = box('vestry glass', (VX0 + 1.0, VY0 - 0.05, 1.7), (0.7, 0.03, 1.3), WIN_GLOW)
for k in (-1, 0, 1):
    box('vestry bar h', (VX0 + 1.0, VY0 - 0.08, 1.7 + k * 0.3), (0.8, 0.06, 0.03), WOOD)
box('vestry bar v', (VX0 + 1.0, VY0 - 0.08, 1.7), (0.03, 0.06, 1.4), WOOD)
vd = box('vestry door', (VX0 + 2.85, VY0 - 0.08, 1.0), (0.82, 0.07, 1.95), WOOD)
for k in range(4):
    box('vestry door plank', (VX0 + 2.85 - 0.3 + k * 0.2, VY0 - 0.13, 1.0), (0.012, 0.01, 1.95), RECESS)
# vestry roof: lean-to, high at the chapel wall
vroof = box('vestry roof', ((VX0 + VX1) / 2 + 0.2, VY0 + VD / 2, VH + 0.35), (VX1 - VX0 + 0.8, VD + 1.0, 0.1), None, rot=(math.radians(-8), 0, 0))
store.use_material(vroof, 'SURFACE • worn_corrugated_iron', ground=VH)
box('vestry fascia', ((VX0 + VX1) / 2 + 0.2, VY0 - 0.5, VH + 0.2), (VX1 - VX0 + 0.8, 0.06, 0.2), BOARDS)
chimney(6.2, 17.0, 3.6, 6.3, w=0.55)

# ------------------------------------------------------------------ gate, piers, railings, low wall
def prism_post(name, x, y, z0, z1, w, mat):
    return box(name, (x, y, (z0 + z1) / 2), (w, w, z1 - z0), mat)

def railing(pts, z0, height, spacing, mat, name):
    objs = []
    v, f = [], []
    def add_bar(x, y, w=0.014):
        base = len(v)
        for dx, dy in ((-w, -w), (w, -w), (w, w), (-w, w)):
            v.append((x + dx, y + dy, z0))
        for dx, dy in ((-w, -w), (w, -w), (w, w), (-w, w)):
            v.append((x + dx, y + dy, z0 + height - 0.1))
        v.append((x, y, z0 + height))
        v.extend([])
        for i in range(4):
            j = (i + 1) % 4
            f.append((base + i, base + j, base + 4 + j, base + 4 + i))
            f.append((base + 4 + i, base + 4 + j, base + 8))
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / spacing))
        for i in range(n + 1):
            t = i / n
            add_bar(ax + (bx - ax) * t, ay + (by - ay) * t)
    bars = obj_from(name + ' bars', v, f, mat)
    rails = []
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        ang = math.atan2(by - ay, bx - ax)
        for zz in (z0 + 0.12, z0 + height - 0.2):
            rails.append(box(name + ' rail', ((ax + bx) / 2, (ay + by) / 2, zz), (L, 0.035, 0.035), mat, rot=(0, 0, ang)))
    return [bars] + rails

WALL_Y = 2.6
for xa, xb in ((-14, -1.5), (1.5, 14)):
    box('low wall', ((xa + xb) / 2, WALL_Y, 0.08), (xb - xa, 0.4, 0.16), None)
    lw = bpy.data.objects['low wall']
    store.use_material(lw, 'SURFACE • old_stone_wall_02', ground=0)
    lw.name = 'low wall seg'
    box('coping', ((xa + xb) / 2, WALL_Y, 0.19), (xb - xa, 0.46, 0.06), DRESS)
    railing([(xa, WALL_Y), (xb, WALL_Y)], 0.22, 0.95, 0.14, IRON, 'front railing')
for sx in (-1, 1):
    pier = box('gate pier', (sx * 1.75, WALL_Y, 0.85), (0.55, 0.55, 1.7), None)
    store.use_material(pier, 'SURFACE • old_stone_wall_02', ground=0)
    box('pier cap', (sx * 1.75, WALL_Y, 1.76), (0.72, 0.72, 0.12), DRESS)
    pv = [(sx * 1.75 - 0.3, WALL_Y - 0.3, 1.82), (sx * 1.75 + 0.3, WALL_Y - 0.3, 1.82), (sx * 1.75 + 0.3, WALL_Y + 0.3, 1.82), (sx * 1.75 - 0.3, WALL_Y + 0.3, 1.82), (sx * 1.75, WALL_Y, 2.15)]
    obj_from('pier top', pv, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)], DRESS)
# gate leaves swung open inwards
for sx in (-1, 1):
    hx = sx * 1.45
    gx = hx
    # leaf along +y from the hinge, a little off the straight
    ang = math.radians(78)
    L = 0.9
    ex, ey = hx, WALL_Y + 0.3
    railing([(hx, WALL_Y + 0.3), (hx + sx * 0.12, WALL_Y + 0.3 + L)], 0.2, 1.0, 0.13, IRON, 'gate leaf')

# kerbs along the path
for sx in (-1, 1):
    box('path kerb', (sx * (FLAG_X + 0.08), 6.45, 0.04), (0.16, 8.1, 0.12), DRESS)
# boot scraper beside the steps
bs = []
bs.append(box('scraper stone', (2.15, 10.2, 0.1), (0.4, 0.3, 0.2), DRESS))
for sx in (-0.15, 0.15):
    bs.append(box('scraper post', (2.15 + sx, 10.2, 0.28), (0.03, 0.04, 0.22), IRON))
bs.append(box('scraper blade', (2.15, 10.2, 0.38), (0.34, 0.02, 0.13), RUST))

# ------------------------------------------------------------------ things the people left
# besom broom leant against the wall left of the door
def besom(x, y, z, lean_deg=12, turn_deg=0):
    parts = [cyl('handle', (0, 0, 0.7), 0.014, 1.4, ASH, seg=8),
             cyl('twigs', (0, 0, 0.14), 0.07, 0.34, TWIG, seg=10, r2=0.1)]
    for k in range(5):
        a = k * 1.3
        parts.append(box('bind', (0, 0, 0.33), (0.1, 0.1, 0.02), IRON))
        break
    ob = merge(parts, 'besom broom')
    ob.rotation_euler = (math.radians(-lean_deg), 0, math.radians(turn_deg))
    ob.location = (x, y, z)
    return ob
bs_ = besom(-1.62, 11.15, BASE, 12, 0)
bs_.scale = (1.6, 1.6, 1.0)
# zinc bucket on the top step, mop-water standing in it
def bucket(x, y, z):
    b = cyl('bucket', (x, y, z + 0.14), 0.15, 0.28, ZINC, seg=20, r2=0.185)
    cyl('bucket water', (x, y, z + 0.25), 0.17, 0.01, RECESS, seg=20)
    box('bucket bail', (x, y, z + 0.34), (0.3, 0.012, 0.012), IRON)
    return b
bk = bucket(-1.1, 10.95, BASE)
# umbrella propped on the left gate pier
def umbrella(x, y, z, lean=14):
    parts = [cyl('umb cloth', (0, 0, 0.55), 0.045, 0.7, CLOTH, seg=10, r2=0.006),
             cyl('umb shaft', (0, 0, 0.12), 0.007, 0.3, ASH, seg=6)]
    parts.append(cyl('umb crook', (0, 0.04, 0.0), 0.03, 0.012, ASH, seg=8, rot=(math.pi / 2, 0, 0)))
    ob = merge(parts, 'umbrella')
    ob.rotation_euler = (math.radians(lean), 0, 0)
    ob.location = (x, y, z)
    return ob
umbrella(-1.45, WALL_Y - 0.35, 0.0, -10)
# milk can by the right pier
def milkcan(x, y, z):
    parts = [cyl('can body', (0, 0, 0.2), 0.12, 0.4, TIN, seg=16, r2=0.1),
             cyl('can neck', (0, 0, 0.46), 0.06, 0.12, TIN, seg=12),
             cyl('can lid', (0, 0, 0.54), 0.085, 0.04, TIN, seg=12)]
    ob = merge(parts, 'milk can')
    ob.location = (x, y, z)
    return ob
milkcan(1.45, WALL_Y - 0.3, 0.0)

# headstones
def headstone(x, y, h, w, lean, turn, mat):
    th = 0.12
    slab = box('hs slab', (0, 0, h / 2 - w * 0.1), (w, th, h - w / 2 - 0.0), mat)
    top = cyl('hs top', (0, 0, h - w / 2 - w * 0.1), w / 2, th - 0.012, mat, seg=14, rot=(math.pi / 2, 0, 0), smooth=False)
    base = box('hs base', (0, 0, 0.04), (w + 0.1, th + 0.1, 0.1), mat)
    ob = merge([slab, top, base], 'headstone')
    ob.rotation_euler = (math.radians(lean), math.radians(lean * 0.5), math.radians(turn))
    ob.location = (x, y, 0.0)
    return ob
HS_SLATE = simple_mat('slate headstone', (0.12, 0.13, 0.15), 0.7)
HS_PALE = simple_mat('pale headstone', (0.24, 0.26, 0.27), 0.8)
for i, (x, y, h, w, lean, turn) in enumerate([(-2.1, 5.2, 0.95, 0.55, 4, 8), (-2.9, 6.9, 1.15, 0.6, -3, -6), (-2.0, 8.0, 0.8, 0.5, 6, 3),
                                              (-3.2, 9.4, 1.0, 0.55, 2, 12), (2.1, 5.8, 1.0, 0.55, -4, -5), (2.8, 7.6, 0.85, 0.5, 5, 10),
                                              (2.0, 9.0, 1.2, 0.6, -2, 4), (3.6, 9.8, 0.9, 0.5, 3, -9), (-1.9, 3.9, 0.7, 0.45, 7, 5)]):
    headstone(x, y, h * 1.2, w * 1.2, lean, turn, HS_PALE if i % 3 else HS_SLATE)

# grass tufts in the graveyard
GR = [M('Weed • rain olive'), M('Weed • yellowed seed blades')]
grng = random.Random(33)
for mi, count in ((0, 900), (1, 450)):
    v, f = [], []
    for t in range(count):
        for _ in range(20):
            gx, gy = grng.uniform(-7.5, 8.5), grng.uniform(2.9, 14.0)
            if abs(gx) > 1.45 and not (abs(gx) < 4.2 and gy > 11.0):
                break
        else:
            continue
        for b in range(4):
            a = grng.uniform(0, 6.28)
            hh = grng.uniform(0.2, 0.55)
            lean = grng.uniform(0.04, 0.14)
            base = len(v)
            v += [(gx + math.cos(a) * 0.012, gy + math.sin(a) * 0.012, 0.0), (gx - math.cos(a) * 0.012, gy - math.sin(a) * 0.012, 0.0),
                  (gx + math.cos(a + 1.2) * lean, gy + math.sin(a + 1.2) * lean, hh)]
            f.append((base, base + 1, base + 2))
    obj_from('grass %d' % mi, v, f, GR[mi])


# a lit hurricane lantern hung on an iron bracket by the door
box('lamp bracket arm', (1.45, CH_Y0 - 0.5, BASE + 2.85), (0.05, 0.55, 0.04), IRON)
box('lamp bracket brace', (1.45, CH_Y0 - 0.3, BASE + 2.7), (0.03, 0.04, 0.38), IRON, rot=(math.radians(35), 0, 0))
box('lamp hook', (1.45, CH_Y0 - 0.7, BASE + 2.72), (0.02, 0.02, 0.2), IRON)
lant2 = store.add_part('hurricane_lantern', location=(1.45, CH_Y0 - 0.7, BASE + 2.6), turn=0, seed=2)
lant2.scale = (1.5, 1.5, 1.5)

# a flat tomb slab
box('tomb slab', (-2.7, 4.3, 0.07), (0.9, 1.9, 0.14), DRESS, rot=(0, 0, math.radians(3)))


def stain(name, x0, x1, z0, z1, y, color, strong_at, density=0.8, streak=True, alpha_max=0.85, scale=7.0, poly=None, axis='Z', rough=0.9):
    """a soot / damp / rain-streak stain on a wall plane at y between z0 and z1; strong_at 'top' or 'bottom'"""
    if poly is None:
        ob = obj_from(name, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(0, 1, 2, 3)])
    else:
        ob = obj_from(name, poly, [tuple(range(len(poly)))])
    ob.visible_shadow = False
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    df = nt.nodes.new('ShaderNodeBsdfPrincipled')
    df.inputs['Base Color'].default_value = (*color, 1)
    df.inputs['Roughness'].default_value = rough
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    grad = nt.nodes.new('ShaderNodeMapRange')
    grad.inputs['From Min'].default_value = z0 if strong_at == 'bottom' else z1
    grad.inputs['From Max'].default_value = z1 if strong_at == 'bottom' else z0
    grad.inputs['To Min'].default_value = 1.0
    grad.inputs['To Max'].default_value = 0.0
    grad.clamp = True
    nt.links.new(sep.outputs[axis], grad.inputs['Value'])
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale * (3.0 if streak else 1.0), scale, scale * (0.25 if streak else 1.0))
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1.0
    noise.inputs['Detail'].default_value = 6.0
    nt.links.new(mp.outputs['Vector'], noise.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mr2 = nt.nodes.new('ShaderNodeMapRange')
    mr2.inputs['From Min'].default_value = 0.3
    mr2.inputs['From Max'].default_value = 0.75
    mr2.inputs['To Min'].default_value = 0.1
    mr2.inputs['To Max'].default_value = 1.6
    nt.links.new(noise.outputs['Fac'], mr2.inputs['Value'])
    nt.links.new(grad.outputs['Result'], mul.inputs[0])
    nt.links.new(mr2.outputs['Result'], mul.inputs[1])
    mul2 = nt.nodes.new('ShaderNodeMath')
    mul2.operation = 'MULTIPLY'
    mul2.use_clamp = True
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    mul2.inputs[1].default_value = alpha_max * density / 0.8
    nt.links.new(mul2.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(df.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    ob.data.materials.append(m)
    return ob

SOOT = (0.012, 0.012, 0.014)
DAMP = (0.015, 0.02, 0.014)
FY = CH_Y0 - 0.33
stain('soot under cornice', -CH_W / 2 - 0.1, CH_W / 2 + 0.1, TOP - 2.6, TOP - 0.1, FY, SOOT, 'top', 1.5, False)
stain('general grime', -CH_W / 2 - 0.1, CH_W / 2 + 0.1, BASE, TOP - 0.2, FY - 0.02, (0.01, 0.014, 0.02), 'bottom', 0.55, False, scale=3.0)
stain('damp at foot', -CH_W / 2 - 0.1, CH_W / 2 + 0.1, BASE, BASE + 1.2, FY, DAMP, 'bottom', 1.0, False)
for cx in (-2.35, 2.35):
    stain('sill streak %.1f' % cx, cx - 0.55, cx + 0.55, BASE + 0.0, BASE + 1.32, FY - 0.04, SOOT, 'top', 0.9, True, scale=9.0)
stain('door streak L', -1.25, -0.95, BASE, BASE + 2.8, FY - 0.04, SOOT, 'top', 0.8, True, scale=9.0)
gi = 0.12
stain('gable soot', 0, 0, GZ0 + 0.1, APEX_Z, 11.2, SOOT, 'top', 1.3, True, scale=5.0,
      poly=[(-CH_W / 2 + gi, 11.2, GZ0 + 0.1), (CH_W / 2 - gi, 11.2, GZ0 + 0.1), (0, 11.2, APEX_Z - 0.1)])

# a notice board by the door (blank paper in a frame)
box('notice frame', (1.55, CH_Y0 - 0.33, BASE + 1.45), (0.62, 0.05, 0.82), WOOD)
box('notice paper', (1.55, CH_Y0 - 0.365, BASE + 1.45), (0.5, 0.01, 0.7), simple_mat('notice paper', (0.10, 0.085, 0.06), 0.9))
for sx in (-1, 1):
    stain('pier damp %d' % sx, sx * 1.75 - 0.3, sx * 1.75 + 0.3, 0.0, 0.9, WALL_Y - 0.3, DAMP, 'bottom', 1.2, False, scale=5.0)
    stain('pier soot %d' % sx, sx * 1.75 - 0.3, sx * 1.75 + 0.3, 1.0, 1.7, WALL_Y - 0.3, SOOT, 'top', 0.6, True, scale=7.0)

MUD = (0.016, 0.012, 0.008)
# a gutter of mud along the foot of the railing on the lane, climbing out into the setts
mudp = stain('lane mud', 0, 0, 0.3, 2.3, 0.018, MUD, 'bottom', 1.5, False, scale=2.5, axis='Y', rough=0.35,
             poly=[(-9, 0.3, 0.018), (9, 0.3, 0.018), (9, 2.25, 0.018), (-9, 2.25, 0.018)])
# downpipes down the front corners with rust at the joints
for sx in (-1, 1):
    px = sx * 3.62
    cyl('downpipe', (px, CH_Y0 - 0.34, (TOP - 0.3 + BASE) / 2), 0.045, TOP - 0.3 - BASE, IRON, seg=10)
    for zz in (BASE + 0.9, BASE + 2.2, BASE + 3.5):
        box('pipe bracket', (px, CH_Y0 - 0.34, zz), (0.13, 0.05, 0.05), RUST)
    box('hopper head', (px, CH_Y0 - 0.34, TOP - 0.15), (0.2, 0.2, 0.2), IRON)
    stain('pipe rust %d' % sx, px - 0.2, px + 0.2, BASE + 0.4, TOP - 0.3, CH_Y0 - 0.36, (0.07, 0.025, 0.008), 'top', 0.7, True, scale=14.0)

# ------------------------------------------------------------------ gas lamp (lit) and hurricane lantern
lamp = store.add_part('gas_lamp', location=(-2.3, 3.9, 0.0), turn=0)
lamp2 = store.add_part('gas_lamp', location=(3.3, 5.2, 0.0), turn=0, seed=3)
lant = store.add_part('hurricane_lantern', location=(1.15, 11.0, BASE), turn=20)
lant.scale = (2.0, 2.0, 2.0)


# far terraces behind the chapel, lost in the haze
BRICK = 'SURFACE • dark_brick_wall'
def terrace(x0, y, n, seed):
    r = random.Random(seed)
    w, d, h = 5.4, 7.0, 6.6
    for i in range(n):
        cx = x0 + i * w + w / 2
        hh = h + r.uniform(-0.3, 0.5)
        wl = box('terrace wall', (cx, y, hh / 2), (w, d, hh), None)
        store.use_material(wl, BRICK, ground=0)
        for fl in (1.6, 4.2):
            for wx in (-1.3, 1.3):
                lit = r.random() < 0.18
                box('terrace window', (cx + wx, y - d / 2 - 0.02, fl + 0.7), (0.9, 0.05, 1.3), GL_LIT if lit else GL_DIM)
        box('terrace door', (cx, y - d / 2 - 0.03, 1.0), (1.0, 0.06, 2.0), WOOD)
        # chimney stack at the party wall
        st = box('terrace stack', (cx + w / 2, y, hh + 2.2), (0.8, 1.0, 2.2), None)
        store.use_material(st, BRICK, ground=hh)
        box('terrace pots', (cx + w / 2, y, hh + 3.4), (0.7, 0.9, 0.4), RUST)
    # slate roof: a long prism along x
    xa, xb = x0 - 0.2, x0 + n * w + 0.2
    zb, zt = h + 0.2, h + 0.2 + 3.0
    v = [(xa, y - d / 2 - 0.4, zb), (xa, y + d / 2 + 0.4, zb), (xa, y, zt), (xb, y - d / 2 - 0.4, zb), (xb, y + d / 2 + 0.4, zb), (xb, y, zt)]
    obj_from('terrace roof', v, [(0, 2, 1), (3, 4, 5), (0, 3, 5, 2), (1, 2, 5, 4), (0, 1, 4, 3)], SLATE)
terrace(-38, 46, 5, 1)
terrace(14, 48, 5, 2)
terrace(-16, 70, 3, 3)

# a far mill chimney in the haze
cyl('mill chimney', (14, 105, 17), 1.5, 34, None, seg=12, r2=0.9)
mc = bpy.data.objects['mill chimney']
store.use_material(mc, 'SURFACE • dark_brick_wall', ground=0)
cyl('mill chimney rim', (14, 105, 34.2), 1.05, 0.5, IRON, seg=12)
for k in range(5):
    box('mill shed', (-6 + k * 6.2, 102, 4.0), (6.0, 14, 8.0), IRON)

# ------------------------------------------------------------------ materials on the ground
store.use_material(garden, 'SURFACE • mud_forest', ground=GARDEN_Z)
store.use_material(side_ground, 'SURFACE • mud_forest', ground=-0.3)
gm = bpy.data.materials['SURFACE • mud_forest']

# ------------------------------------------------------------------ lay the lane and path
setts = lay_cobbles.lay_setts(road, seed=3)
flags = lay_cobbles.lay_flags(path, seed=4)
TOPH = setts['top_height']


# fallen leaves (ochre and peat), on the flags and the setts
LEAF = [M('Fallen leaf • ochre'), M('Fallen leaf • peat brown')]
lrng = random.Random(21)
leaf_objs = []
for i in range(60):
    if i < 36:
        lx, ly, lz = lrng.uniform(-1.2, 1.2), lrng.uniform(3.0, 10.2), 0.012
    else:
        lx, ly, lz = lrng.uniform(-3.5, 4.0), lrng.uniform(-1.6, 1.9), TOPH + 0.012
    a = lrng.uniform(0, 6.28)
    sz = lrng.uniform(0.07, 0.12)
    pts = []
    for k in range(7):
        t = 2 * math.pi * k / 7
        r = sz * (1.0 if k % 2 == 0 else 0.7)
        pts.append((lx + math.cos(t + a) * r * 1.0, ly + math.sin(t + a) * r * 0.55, lz))
    lf = obj_from('leaf', pts, [tuple(range(7))], LEAF[i % 2])

# a drain grating in the gutter
for k in range(9):
    box('grate bar', (-0.4 + k * 0.05, 1.9, TOPH - 0.004), (0.02, 0.5, 0.02), IRON)
box('grate frame', (-0.2, 1.9, TOPH - 0.01), (0.55, 0.62, 0.012), RUST)

# puddles
puddle.make((0.3, 4.9, 0.0), size=(2.4, 0.9), turn=3, seed=3, level=0.003, raggedness=1.5)
puddle.make((-0.7, 8.4, 0.0), size=(1.5, 0.55), turn=-10, seed=5, level=0.003)
puddle.make((0.9, 3.0, 0.0), size=(1.0, 0.45), turn=8, seed=8, level=0.003)
puddle.make((-0.55, -2.7, 0.0), size=(2.6, 0.8), turn=88, seed=2, level=TOPH + 0.002, raggedness=1.4)
puddle.make((1.35, -2.2, 0.0), size=(2.4, 0.9), turn=86, seed=9, level=TOPH + 0.002, raggedness=1.0)

# ------------------------------------------------------------------ DRESSING PASS: the things the keeper, the coalman and the congregation left
dr = random.Random(51)

def surf(name, **dials):
    """a private copy of a shelf surface so one dial change does not change every user of it"""
    m = store.material(name).copy()
    nd = m.node_tree.nodes
    for k, v in dials.items():
        nd['Weather'].inputs[k.replace('_', ' ')].default_value = v
    return m

def beam(name, p0, p1, r, mat, seg=8):
    a, b = Vector(p0), Vector(p1)
    d = b - a
    q = d.to_track_quat('Z', 'Y')
    return cyl(name, tuple((a + b) / 2), r, d.length, mat, seg=seg, rot=tuple(q.to_euler()))

def blob(name, cx, cy, rx, ry, height, mat, z0, turn=0.0, seed=0, ground=None, rough=0.25, nang=28, flat=0.5):
    """a ragged heap or smear lying on the ground: a wobbly outline, a low dome, a thin edge"""
    r_ = random.Random(seed)
    ph = [r_.uniform(0, 6.28) for _ in range(4)]
    am = [r_.uniform(0.05, rough) for _ in range(4)]
    rings = (1.0, 0.72, 0.42, 0.16)
    v, f = [], []
    ct, st = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    def wob(a):
        return 1.0 + sum(am[k] * math.sin((k + 2) * a + ph[k]) for k in range(4))
    for ri, rr in enumerate(rings):
        for i in range(nang):
            a = 2 * math.pi * i / nang
            w = wob(a)
            lx, ly = math.cos(a) * rx * rr * w, math.sin(a) * ry * rr * w
            h = height * (1 - rr ** 2) ** flat + 0.003 + r_.uniform(0, height * 0.12) * (rr < 1)
            v.append((cx + lx * ct - ly * st, cy + lx * st + ly * ct, z0 + h))
    v.append((cx, cy, z0 + height * 1.05))
    for ri in range(len(rings) - 1):
        for i in range(nang):
            j = (i + 1) % nang
            f.append((ri * nang + i, ri * nang + j, (ri + 1) * nang + j, (ri + 1) * nang + i))
    last = (len(rings) - 1) * nang
    for i in range(nang):
        f.append((last + i, last + (i + 1) % nang, len(v) - 1))
    ob = obj_from(name, v, f, mat, smooth=True)
    store.mark(ob, ground if ground is not None else z0) if hasattr(store, 'mark') else None
    ob.visible_shadow = False if height < 0.02 else True
    return ob

def lump(name, c, size, mat, seed):
    """a broken lump of coal: a rough ball with flat facets"""
    r_ = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    sx, sy, sz = r_.uniform(0.7, 1.2), r_.uniform(0.7, 1.2), r_.uniform(0.5, 0.9)
    for vv in bm.verts:
        k = r_.uniform(0.7, 1.15)
        vv.co = Vector((vv.co.x * sx * k, vv.co.y * sy * k, vv.co.z * sz * k)) * size
    rot = Euler((r_.uniform(0, 6), r_.uniform(0, 6), r_.uniform(0, 6))).to_matrix().to_4x4()
    me = bpy.data.meshes.new(name)
    bm.transform(rot)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.location = c
    ob.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
    return ob


def ash_mat(name, dark, light, scale=55.0, bump=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.92
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = scale
    n1.inputs['Detail'].default_value = 10.0
    n1.inputs['Roughness'].default_value = 0.75
    nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.38
    cr.color_ramp.elements[0].color = (*dark, 1)
    cr.color_ramp.elements[1].position = 0.68
    cr.color_ramp.elements[1].color = (*light, 1)
    nt.links.new(n1.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.01
    nt.links.new(n1.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
ASHPILE = ash_mat('stove ash and clinker', (0.04,0.04,0.042), (0.30,0.285,0.26), 45.0, 1.4)
CLOTH2 = simple_mat('wet umbrella cloth', (0.07, 0.075, 0.09), 0.3)
MUDPATCH = surf('SURFACE • mud_forest', Wet=0.7, Bump=2.0, Darken=0.8)
SACKMAT = ash_mat('hessian sack', (0.05,0.04,0.028), (0.34,0.25,0.14), 9.0, 1.6)
PLANKMAT = surf('SURFACE • old_planks_02', Darken=0.6)
COALMAT = simple_mat('coal', (0.012, 0.012, 0.014), 0.3, 0.1)
DUNG = simple_mat('horse dung', (0.035, 0.022, 0.012), 0.7)
STRAW = simple_mat('oat straw', (0.20, 0.145, 0.055), 0.8)
ASHFINE = ash_mat('fine ash', (0.09,0.09,0.095), (0.30,0.30,0.30), 40.0, 0.5)
CHURN = simple_mat('churn tin', (0.17, 0.19, 0.19), 0.38, 0.85)

# ---- wheelbarrow of stove ash, left of the gate, left on the lane edge by the keeper
BARROWWOOD = BOARDS.copy()
tint(BARROWWOOD, (1.7, 0.75, 0.55))
def wheelbarrow():
    p = []
    p.append(box('bb', (0, 0, 0.38), (0.82, 0.50, 0.035), BARROWWOOD))
    for s in (-1, 1):
        p.append(box('bs', (0, s * 0.35, 0.51), (1.08, 0.035, 0.30), BARROWWOOD, rot=(-s * 0.27, 0, 0)))
    p.append(box('bf', (0.52, 0, 0.51), (0.035, 0.64, 0.30), BARROWWOOD, rot=(0, 0.3, 0)))
    p.append(box('bk', (-0.5, 0, 0.51), (0.035, 0.64, 0.30), BARROWWOOD, rot=(0, -0.3, 0)))
    for s in (-1, 1):
        p.append(box('bolt strap', (0.1, s * 0.30, 0.52), (0.04, 0.012, 0.30), RUST, rot=(-s * 0.27, 0, 0)))
        p.append(box('bolt strap', (-0.25, s * 0.30, 0.52), (0.04, 0.012, 0.30), RUST, rot=(-s * 0.27, 0, 0)))
        p.append(beam('handle', (0.35, s * 0.24, 0.40), (-1.15, s * 0.28, 0.66), 0.024, ASH))
        p.append(beam('grip', (-1.15, s * 0.28, 0.66), (-1.30, s * 0.285, 0.69), 0.03, ASH))
        p.append(beam('leg', (-0.68, s * 0.255, 0.55), (-0.74, s * 0.27, 0.0), 0.022, ASH))
        p.append(beam('fork', (0.50, s * 0.15, 0.42), (0.70, s * 0.075, 0.21), 0.018, IRON))
        p.append(box('foot', (-0.74, s * 0.27, 0.02), (0.07, 0.07, 0.04), RUST))
    p.append(cyl('wheel', (0.70, 0, 0.21), 0.21, 0.06, RUST, seg=24, rot=(math.pi / 2, 0, 0)))
    p.append(cyl('tyre', (0.70, 0, 0.21), 0.225, 0.045, IRON, seg=24, rot=(math.pi / 2, 0, 0)))
    p.append(cyl('hub', (0.70, 0, 0.21), 0.04, 0.2, IRON, seg=10, rot=(math.pi / 2, 0, 0)))
    ob = merge(p, 'wheelbarrow')
    return ob

def place(ob, x, y, z, yaw, scale=1.0):
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, math.radians(yaw))
    ob.scale = (scale, scale, scale)
    return ob

BX, BY, BYAW, BS = -0.6, -0.3, 190, 0.8
barrow = place(wheelbarrow(), BX, BY, TOPH, BYAW, BS)
def blw(lx, ly, lz=0.0):
    a = math.radians(BYAW)
    return (BX + BS * (lx * math.cos(a) - ly * math.sin(a)), BY + BS * (lx * math.sin(a) + ly * math.cos(a)), TOPH + BS * lz)
ax, ay, az = blw(0.0, 0.0, 0.42)
ash_in = blob('ash in barrow', ax, ay, 0.46 * BS, 0.27 * BS, 0.17 * BS, ASHFINE, az, turn=BYAW, seed=4, rough=0.12, ground=TOPH)
# clinker lumps in the ash
for k in range(14):
    lx, ly = dr.uniform(-0.35, 0.35), dr.uniform(-0.2, 0.2)
    wx, wy, wz = blw(lx, ly, 0.58 + 0.1 * (1 - abs(lx) / 0.4))
    lump('clinker', (wx, wy, wz), dr.uniform(0.03, 0.055), ASHPILE, 100 + k)

# the spill: ash tipped off the front, scattered across the setts, a fan towards the gutter
sx0, sy0 = -0.95, -1.0
blob('ash spill', sx0, sy0, 0.38, 0.26, 0.016, ASHPILE, TOPH + 0.005, turn=BYAW + 20, seed=11, rough=0.3, ground=TOPH)
blob('ash spill 2', sx0 + 0.5, sy0 - 0.15, 0.25, 0.17, 0.01, ASHFINE, TOPH + 0.005, turn=BYAW - 30, seed=12, rough=0.3, ground=TOPH)
for k in range(10):
    blob('ash fleck', sx0 + dr.uniform(-0.5, 1.1), sy0 + dr.uniform(-0.55, 0.45), dr.uniform(0.07, 0.15), dr.uniform(0.05, 0.1), 0.008, ASHFINE, TOPH + 0.005, turn=dr.uniform(0, 180), seed=20 + k, ground=TOPH, nang=14)

# shovel lying across the spill
def shovel(x, y, yaw):
    p = [beam('shovel handle', (0, 0, 0.035), (0.95, 0, 0.045), 0.017, ASH),
         box('shovel grip', (0.95, 0, 0.05), (0.14, 0.05, 0.035), ASH),
         box('shovel blade', (-0.17, 0, 0.026), (0.30, 0.27, 0.014), IRON, rot=(0, 0.04, 0)),
         box('shovel rim', (-0.03, 0, 0.032), (0.04, 0.16, 0.02), RUST)]
    ob = merge(p, 'shovel')
    return place(ob, x, y, TOPH, yaw)
shovel(sx0 + 0.45, sy0 - 0.3, 200)

# ---- coal sacks and spilled coal, dropped by the coalman at the right of the lane
def sack(name, c, yaw, size=(0.42, 0.22, 0.15), seed=0, slump=1.0, mouth_end=1):
    r_ = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    def pw(t, e):
        return math.copysign(abs(t) ** e, t)
    for vv in bm.verts:
        x, y, z = vv.co
        x, y, z = pw(x, 0.62), pw(y, 0.8), pw(z, 0.75)
        k = 1 + 0.05 * math.sin(x * 9 + seed) + 0.04 * math.sin(y * 7 + 2 * seed) + r_.uniform(-0.02, 0.02)
        taper = 1 - 0.35 * max(0.0, abs(x) - 0.55)
        zz = max(z, -0.25) * size[2] * k * slump
        if z > 0:
            zz *= (1 - 0.25 * abs(y))
        vv.co = Vector((x * size[0], y * size[1] * taper * k, zz))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for pp in me.polygons:
        pp.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(SACKMAT)
    ob.location = (c[0], c[1], TOPH + size[2] * 0.55)
    ob.rotation_euler = (0, 0, math.radians(yaw))
    store.use_material(ob, SACKMAT, ground=TOPH)
    # the stitched seam along the top and a rope tie round the mouth end
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    def w(lx, ly, lz):
        return (c[0] + lx * ca - ly * sa, c[1] + lx * sa + ly * ca, TOPH + size[2] * 0.55 + lz)
    seam = beam(name + ' seam', w(-size[0] * 0.8, 0.0, size[2] * 0.72), w(size[0] * 0.8, 0.0, size[2] * 0.72), 0.008, ASH, seg=5)
    tie = cyl(name + ' tie', w(mouth_end * size[0] * 0.78, 0, 0.0), size[1] * 0.78, 0.035, ASH, seg=14, rot=(0, math.pi / 2, math.radians(yaw)))
    tie.rotation_euler = Euler((0, math.pi / 2, 0)).to_matrix().to_4x4().to_euler()
    m_ = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    tie.rotation_euler = m_.to_euler()
    return ob

CX, CY = 0.2, -1.85
# loose coal from the burst sack, towards the camera and gutter
cn = 0
for k in range(34):
    a = dr.uniform(-1.0, 1.0)
    d = abs(dr.gauss(0, 0.30)) + 0.12
    wx, wy = CX + 0.3 + math.cos(a) * d * 0.9, CY - 0.55 + math.sin(a) * d * 0.7
    lump('coal', (wx, wy, TOPH + 0.03 + 0.03 * max(0, 0.3 - d) * 2), dr.uniform(0.04, 0.075) * (1.15 if d < 0.3 else 0.85), COALMAT, 300 + k)
for k in range(7):
    lump('coal strays', (CX + dr.uniform(-0.3, 0.7), CY + dr.uniform(-2.0, -0.3), TOPH + 0.03), dr.uniform(0.03, 0.05), COALMAT, 400 + k)

# ---- milk churn, stood by the right pier foot for the evening's tea
def churn(x, y):
    p = [cyl('churn body', (0, 0, 0.30), 0.19, 0.60, CHURN, seg=24),
         cyl('churn shoulder', (0, 0, 0.68), 0.19, 0.16, CHURN, seg=24, r2=0.105),
         cyl('churn neck', (0, 0, 0.82), 0.105, 0.12, CHURN, seg=20),
         cyl('churn lid', (0, 0, 0.91), 0.14, 0.06, CHURN, seg=20, r2=0.10),
         cyl('churn knob', (0, 0, 0.96), 0.03, 0.05, IRON, seg=8)]
    for z in (0.06, 0.30, 0.56):
        p.append(cyl('churn band', (0, 0, z), 0.197, 0.035, RUST if z < 0.1 else IRON, seg=24))
    p.append(cyl('churn foot', (0, 0, 0.012), 0.21, 0.024, RUST, seg=24))
    for s in (-1, 1):
        p.append(box('churn handle', (s * 0.2, 0, 0.62), (0.09, 0.03, 0.03), IRON))
        p.append(box('churn handle', (s * 0.24, 0, 0.58), (0.03, 0.03, 0.09), IRON))
    p.append(box('hasp', (0, -0.145, 0.88), (0.02, 0.02, 0.1), RUST))
    ob = merge(p, 'milk churn')
    return ob
place(churn(0, 0), 1.3, 0.55, TOPH, 0, 1.1)

# ---- two old boards laid over the gutter mud, from the lane to the flags
for k, (px, yaw) in enumerate(((0.78, 2.5), (1.05, -1.5))):
    L = 2.5
    pl = box('gutter plank %d' % k, (px, 1.3, TOPH + 0.05), (0.24, L, 0.05), None, rot=(0.012, 0, math.radians(yaw)))
    store.use_material(pl, PLANKMAT, ground=TOPH)
for cy_ in (0.35, 1.25, 2.15):
    cl = box('plank cleat', (0.915, cy_, TOPH + 0.085), (0.62, 0.07, 0.03), None, rot=(0, 0, math.radians(dr.uniform(-2, 2))))
    store.use_material(cl, PLANKMAT, ground=TOPH)
# ---- the coalman's horse: droppings and oat straw
for k, (x_, y_, r_) in enumerate(((0.5, -2.3, 0.12), (0.85, -2.1, 0.09))):
    blob('dung %d' % k, x_, y_, r_, r_ * 0.8, 0.055, DUNG, TOPH + 0.004, turn=dr.uniform(0, 90), seed=51 + k, rough=0.3, ground=TOPH, nang=16)
for k in range(12):
    ang = dr.uniform(0, math.pi)
    sx_, sy_ = 0.65 + dr.gauss(0, 0.3), -2.2 + dr.gauss(0, 0.25)
    box('straw', (sx_, sy_, TOPH + 0.02), (dr.uniform(0.10, 0.2), 0.02, 0.012), STRAW, rot=(0, 0, ang))


# ---- a wet umbrella dropped on the setts by the chapel-goers hurrying in, crook towards the camera
def beamt(name, p0, p1, r0, r1, mat, seg=12):
    a_, b_ = Vector(p0), Vector(p1)
    d = b_ - a_
    q = d.to_track_quat('Z', 'Y')
    return cyl(name, tuple((a_ + b_) / 2), r0, d.length, mat, seg=seg, r2=r1, rot=tuple(q.to_euler()))

def umbrella_lying(x, y, yaw):
    p = [beamt('umb gathered cloth', (0.02, 0, 0.04), (0.38, 0, 0.05), 0.014, 0.042, CLOTH2),
         beamt('umb cloth tip', (0.38, 0, 0.05), (0.92, 0, 0.04), 0.042, 0.006, CLOTH2),
         beam('umb ferrule', (0.9, 0, 0.04), (1.0, 0, 0.038), 0.006, IRON, seg=6),
         beam('umb shaft', (0.0, 0, 0.04), (-0.4, 0, 0.035), 0.011, ASH, seg=8)]
    cx0, cz0 = -0.4, 0.035
    prev = (cx0, 0.0, cz0)
    for k in range(1, 9):
        t = k / 8 * math.pi
        nxt = (cx0 - 0.08 * math.sin(t), 0.08 * (1 - math.cos(t)), cz0)
        p.append(beam('crook', prev, nxt, 0.014, ASH, seg=6))
        prev = nxt
    p.append(box('umb strap', (0.55, 0, 0.07), (0.03, 0.09, 0.02), IRON))
    p.append(box('umb strap', (0.30, 0, 0.065), (0.03, 0.07, 0.02), IRON))
    ob = merge(p, 'umbrella on the setts')
    return place(ob, x, y, TOPH, yaw, 1.2)
umbrella_lying(-0.1, -2.85, 5)


def smear(name, cx, cy, rx, ry, color, alpha=0.8, seed=0, turn=0.0, rough=0.35, z=None, scale=5.0, hard=0.0):
    """a soft, see-through smear lying on the setts (mud, soot, wet dark, coal dust): fades out towards its edge, broken by noise"""
    z = (TOPH + 0.006) if z is None else z
    n = 32
    v = [(0, 0, 0)] + [(math.cos(2 * math.pi * i / n) * rx * 1.15, math.sin(2 * math.pi * i / n) * ry * 1.15, 0) for i in range(n)]
    f = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    ob = obj_from(name, v, f)
    ob.location = (cx, cy, z)
    ob.rotation_euler = (0, 0, math.radians(turn))
    ob.visible_shadow = False
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    df = nt.nodes.new('ShaderNodeBsdfPrincipled')
    df.inputs['Base Color'].default_value = (*color, 1)
    df.inputs['Roughness'].default_value = rough
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0 / rx, 1.0 / ry, 0.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    ln = nt.nodes.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    nt.links.new(mp.outputs['Vector'], ln.inputs[0])
    rad = nt.nodes.new('ShaderNodeMapRange')
    rad.inputs['From Min'].default_value = 0.15
    rad.inputs['From Max'].default_value = 1.0
    rad.inputs['To Min'].default_value = 1.0
    rad.inputs['To Max'].default_value = 0.0
    rad.clamp = True
    nt.links.new(ln.outputs['Value'], rad.inputs['Value'])
    mp2 = nt.nodes.new('ShaderNodeMapping')
    mp2.inputs['Scale'].default_value = (scale / rx * 0.5, scale / ry * 0.5, 1.0)
    mp2.inputs['Location'].default_value = (seed * 3.1, seed * 1.7, 0)
    nt.links.new(tc.outputs['Object'], mp2.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 2.5
    nz.inputs['Detail'].default_value = 8.0
    nt.links.new(mp2.outputs['Vector'], nz.inputs['Vector'])
    nr = nt.nodes.new('ShaderNodeMapRange')
    nr.inputs['From Min'].default_value = 0.35
    nr.inputs['From Max'].default_value = 0.65
    nr.clamp = True
    nt.links.new(nz.outputs['Fac'], nr.inputs['Value'])
    mu = nt.nodes.new('ShaderNodeMath')
    mu.operation = 'MULTIPLY'
    nt.links.new(rad.outputs['Result'], mu.inputs[0])
    nt.links.new(nr.outputs['Result'], mu.inputs[1])
    mu2 = nt.nodes.new('ShaderNodeMath')
    mu2.operation = 'MULTIPLY'
    mu2.use_clamp = True
    mu2.inputs[1].default_value = alpha * 1.8
    nt.links.new(mu.outputs[0], mu2.inputs[0])
    nt.links.new(mu2.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(df.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    ob.data.materials.append(m)
    return ob

MUDC = (0.02, 0.014, 0.009)
WETDARK = (0.006, 0.008, 0.012)
GREENC = (0.015, 0.03, 0.01)
# boot mud dragged from the plank ends into the lane, a long wet dark rut strip each way, green damp at the rims
smear('boot mud', 0.95, 0.15, 0.9, 0.4, MUDC, 0.9, 1, 5, 0.3, scale=6)
smear('boot mud 2', 0.4, -0.35, 0.55, 0.2, MUDC, 0.8, 2, -15, 0.3, scale=6)
for k, (mx_, my_, mr_) in enumerate(((-0.3, 0.9, 0.25), (0.3, 1.5, 0.25), (1.9, 1.2, 0.3), (-1.6, 0.4, 0.3))):
    smear('green damp %d' % k, mx_, my_, mr_ * 1.4, mr_, GREENC, 0.8, 10 + k, dr.uniform(0, 180), 0.6, scale=7)

# ---- the keeper's coal scuttle, set down by the shovel with coal tipped out of it
def scuttle(x, y, yaw):
    p = [cyl('scuttle body', (0, 0, 0.17), 0.17, 0.34, IRON, seg=20, r2=0.22),
         cyl('scuttle floor', (0, 0, 0.01), 0.165, 0.02, RUST, seg=20),
         cyl('scuttle rim', (0, 0, 0.345), 0.225, 0.02, RUST, seg=20),
         cyl('scuttle coal', (0, 0, 0.33), 0.2, 0.04, COALMAT, seg=12)]
    for s_ in (-1, 1):
        p.append(box('scuttle ear', (s_ * 0.225, 0, 0.30), (0.03, 0.04, 0.05), RUST))
    # the sloped front lip
    p.append(box('scuttle lip', (0, -0.2, 0.20), (0.36, 0.07, 0.30), IRON, rot=(0.9, 0, 0)))
    # bail handle: half ring
    prev = (-0.225, 0, 0.30)
    for k in range(1, 9):
        t = k / 8 * math.pi
        nxt = (-0.225 * math.cos(t), 0, 0.30 + 0.17 * math.sin(t))
        p.append(beam('bail', prev, nxt, 0.008, IRON, seg=5))
        prev = nxt
    p.append(box('scuttle hand', (0.0, 0.01, 0.47), (0.14, 0.03, 0.03), ASH))
    ob = merge(p, 'coal scuttle')
    return place(ob, x, y, TOPH, yaw, 1.0)
scuttle(0.15, -1.2, 25)
smear('coal dust under', 0.45, -1.7, 0.7, 0.4, (0.004, 0.004, 0.005), 0.55, 6, 20, 0.35, scale=7)

# ---- wear on the forecourt path and the steps: boots polish the middle, ash and mud are carried in and out, damp lies along the kerbs
PALE = (0.075, 0.07, 0.062)
ASHTRK = (0.17, 0.165, 0.15)
smear('ash carried out', -0.25, 7.2, 0.4, 2.2, ASHTRK, 0.28, 30, 90, 0.5, z=0.1, scale=8)
smear('ash carried out 2', 0.3, 4.4, 0.35, 1.0, ASHTRK, 0.28, 31, 70, 0.5, z=0.1, scale=8)
smear('mud at the gate', 0.2, 3.4, 0.9, 0.5, MUDC, 0.5, 32, 10, 0.12, z=0.1, scale=6)
smear('mud at the steps', 0.0, 10.0, 0.9, 0.35, MUDC, 0.5, 33, 0, 0.12, z=0.1, scale=6)
for sx in (-1, 1):
    for k in range(3):
        smear('kerb damp', sx * 1.18, 3.5 + k * 2.6, 0.2, 1.5, GREENC, 0.7, 40 + k + (3 if sx > 0 else 0), 90, 0.2, z=0.1, scale=6)
# the steps: dished and pale in the middle of each tread
for k, (yy, zz, ry) in enumerate(((11.25, 0.45, 0.16), (10.9, 0.30, 0.06), (10.65, 0.15, 0.13))):
    smear('tread wear %d' % k, 0.0, yy, 0.9, ry, (0.14, 0.13, 0.115), 0.6, 50 + k, 0, 0.5, z=zz + 0.004, scale=6)

# ---- the keeper's lit hurricane lantern, set down on the setts between the barrow and the scuttle while he works at the ash
_before = set(o.name for o in bpy.data.objects)
lant3 = store.add_part('hurricane_lantern', location=(-0.2, -0.9, TOPH), turn=35, seed=5)
lant3.scale = (1.9, 1.9, 1.9)
for o in bpy.data.objects:
    if o.name not in _before and o.type == 'LIGHT':
        o.data.energy = max(o.data.energy, 25) * 1.4
        o.data.shadow_soft_size = 0.06

# ---- headstones near the gate: soot from the mill on the shoulders, green damp at the foot (stains in front of each face)
for (hx, hy, hh, hw) in ((-2.0, 8.0, 0.9, 0.7), (2.0, 9.0, 1.37, 0.82), (-3.2, 9.4, 1.14, 0.76), (2.8, 7.6, 0.96, 0.7)):
    stain('headstone soot', hx - hw / 2 - 0.02, hx + hw / 2 + 0.02, hh * 0.3, hh, hy - 0.14, (0.012, 0.012, 0.014), 'top', 0.55, True, scale=9.0)
    stain('headstone damp', hx - hw / 2 - 0.03, hx + hw / 2 + 0.03, 0.0, hh * 0.45, hy - 0.14, (0.016, 0.03, 0.012), 'bottom', 1.3, False, scale=8.0)

# ---- a hymn book dropped by someone hurrying in out of the rain, lying open face-down on the wet setts (no words on it)
BOOKCOVER = simple_mat('hymn book cloth', (0.07, 0.014, 0.012), 0.4)
BOOKPAGES = simple_mat('wet book pages', (0.26, 0.22, 0.15), 0.6)
def hymn_book(x, y, yaw):
    p = [box('book pages', (0.0, 0, 0.022), (0.145, 0.215, 0.034), BOOKPAGES),
         box('book cover top', (0.0, 0, 0.044), (0.16, 0.225, 0.011), BOOKCOVER),
         box('book cover under', (0.0, 0, 0.005), (0.16, 0.225, 0.011), BOOKCOVER),
         box('book spine', (-0.08, 0, 0.0245), (0.012, 0.225, 0.05), BOOKCOVER)]
    ob = merge(p, 'hymn book')
    return place(ob, x, y, TOPH, yaw, 1.5)
hymn_book(0.5, -2.45, 28)

# ---- grime on the bottom setts: boots and the horse bring mud and coal dust over the pale tops (soft, thin, kept glossy)
smear('lane grime A', 0.35, -2.1, 1.1, 0.7, (0.012, 0.01, 0.008), 0.14, 60, 8, 0.2, scale=6)
smear('lane grime B', 0.4, -3.1, 1.2, 0.5, (0.012, 0.01, 0.008), 0.14, 61, -6, 0.2, scale=6)

# ------------------------------------------------------------------ sky, haze, lights
sky_and_haze.sky(scene, strength=0.7, clouds=1.0, low_band=(0.22, 0.14, 0.11), high_band=(0.04, 0.095, 0.115), top=(0.008, 0.03, 0.045))
sky_and_haze.haze(low=(-70, -12, 0), high=(70, 150, 40), density=0.0034)

def point(name, loc, watts, color, radius=0.1):
    l = bpy.data.lights.new(name, 'POINT')
    l.energy = watts
    l.color = color
    l.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, l)
    scene.collection.objects.link(ob)
    ob.location = loc
    return ob
WARM = (1.0, 0.6, 0.28)
point('door spill', (0.0, 10.2, 1.3), 70, WARM, 0.3)
point('door inside', (0.0, 12.6, 1.5), 300, WARM, 0.4)
point('step spill', (0.0, 9.9, 0.8), 55, WARM, 0.2)
point('door high', (0.0, 10.8, 2.8), 60, WARM, 0.2)
point('left window light', (-2.35, 10.7, 2.5), 60, WARM, 0.2)
point('vestry light', (VX0 + 1.0, VY0 - 0.7, 1.8), 45, WARM, 0.15)
point('rose light', (0, 10.6, rw_z), 10, WARM, 0.1)

yard = bpy.data.lights.new('yard fill', 'AREA')
yard.shape = 'RECTANGLE'
yard.size, yard.size_y = 9.0, 8.0
yard.energy = 380
yard.color = (0.5, 0.65, 1.0)
yardob = bpy.data.objects.new('yard fill', yard)
scene.collection.objects.link(yardob)
yardob.location = (0.0, 7.5, 7.0)
sun = bpy.data.lights.new('moon fill', 'SUN')
sun.energy = 0.55
sun.color = (0.45, 0.6, 1.0)
sunob = bpy.data.objects.new('moon fill', sun)
scene.collection.objects.link(sunob)
sunob.rotation_euler = (math.radians(55), 0, math.radians(-30))


import smoke_ribbon
smoke_ribbon.make(start=(6.2, 17.0, 6.7), facing=(0.35, -6.0, 1.6), drift=(1.0, 0.2), rise=5.0, lean=0.7, width_start=0.35, width_end=2.4, sway=1.0, seed=3)

# ------------------------------------------------------------------ camera
cam = bpy.data.cameras.new('cam')
cam.lens = 28
cam.shift_y = -0.06
camob = bpy.data.objects.new('cam', cam)
scene.collection.objects.link(camob)
camob.location = (0.35, -6.0, 1.62)
d = Vector((0.0, 12.0, 3.0)) - camob.location
camob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = camob

# ------------------------------------------------------------------ render
store.prepare_for_render(scene)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.volume_bounces = 1
scene.cycles.sample_clamp_indirect = 8
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
exr = os.path.join(HERE, 'raw_' + os.path.basename(OUT).rsplit('.', 1)[0] + '.exr')
scene.render.filepath = exr
bpy.ops.render.render(write_still=True)
finisher.finish(exr, OUT, bloom=1.0, veil=0.3, soften=0.5)
print('done', OUT)
