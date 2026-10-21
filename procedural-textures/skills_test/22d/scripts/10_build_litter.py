# What this does (plain words)
# --------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22d, step 1. Opens the COPY of the wet street (set_copy/street.blend), and with the Scenario geometry-nodes skill's builder (bx_gn):
#   1. makes small litter pieces by hand (paper scraps, a paper ball, two bottle stand-ins, leaves in three autumn colours), each lying flat with its
#      underside at height zero, in a collection called litter_sources that is switched off for drawing;
#   2. cuts a "host" strip out of the street's own gutter stones and the outer half-metre of the road next to them (a new object, gutter_litter);
#   3. builds ONE node tree, "Gutter Litter", that scatters paper, leaves and bottles on that host, thicker next to the kerb and in clumps;
#   4. puts it on the host as a modifier and saves the result as street_litter.blend (camera = the film's main camera) and street_litter_close.blend
#      (camera = a low camera looking along the right-hand gutter).
# Nothing else in the street is changed. Run:
#   xvfb-run -a blender -b --disable-autoexec --factory-startup --python-exit-code 1 set_copy/street.blend -P scripts/10_build_litter.py -- OUT_FOLDER
import json
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bx_gn as G  # noqa: E402

OUT = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath))
scene = bpy.context.scene
rng = random.Random(22)
TAN4 = math.tan(math.radians(4.0))


def ground_z(y):
    """the street's channel line: z = min(y, 76) * tan(4 degrees) (from camera.json, set_notes)"""
    return min(y, 76.0) * TAN4


# ---------------------------------------------------------------------------------------------------------------- 1. litter pieces
litter_col = bpy.data.collections.get('litter_sources') or bpy.data.collections.new('litter_sources')
if litter_col.name not in scene.collection.children:
    scene.collection.children.link(litter_col)
sub = {}
for name in ('litter_paper', 'litter_leaves', 'litter_bottles'):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in litter_col.children:
        litter_col.children.link(c)
    sub[name] = c


def mat(name, color, rough):
    return G.material(name, color, rough)


M = {
    'paper_cream': mat('litter_paper_cream', (0.62, 0.58, 0.46), 0.9),
    'paper_news': mat('litter_paper_newsprint', (0.36, 0.34, 0.29), 0.95),
    'paper_wet': mat('litter_paper_soaked', (0.20, 0.18, 0.14), 0.6),
    'bottle_brown': mat('litter_bottle_brown', (0.10, 0.045, 0.012), 0.12),
    'bottle_green': mat('litter_bottle_green', (0.03, 0.12, 0.05), 0.12),
    'leaf_rust': mat('litter_leaf_rust', (0.28, 0.095, 0.03), 0.8),
    'leaf_ochre': mat('litter_leaf_ochre', (0.40, 0.25, 0.05), 0.8),
    'leaf_dark': mat('litter_leaf_dark', (0.12, 0.07, 0.03), 0.85),
}


def add_mesh(name, verts, faces, material, collection, smooth=False):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = smooth
    o = bpy.data.objects.new(name, me)
    collection.objects.link(o)
    return o


def scrap(name, length, width, material, lift=0.0025, crumple=0.006, sides=10):
    """a torn scrap of paper: an uneven rim of `sides` points (some pulled in, some torn out) around a creased middle. Underside near z = lift.
    (Round 1 had 6-7 even points and read as a hexagon sticker in the picture: more points, rougher radius, a fold line.)"""
    verts = [(0.0, 0.0, lift + crumple * 0.6)]
    phase = rng.uniform(0, 2 * math.pi)
    for i in range(sides):
        a = phase + 2 * math.pi * i / sides + rng.uniform(-0.28, 0.28)
        r = rng.uniform(0.45, 1.0)
        x, y = math.cos(a) * r * length / 2, math.sin(a) * r * width / 2
        verts.append((x, y, lift + abs(math.sin(a * 1.5 + phase)) * crumple + rng.uniform(0.0, crumple * 0.4)))
    faces = [(0, 1 + i, 1 + (i + 1) % sides) for i in range(sides)]
    return add_mesh(name, verts, faces, material, sub['litter_paper'])


def paper_ball(name, radius, material):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
    for v in bm.verts:
        v.co *= rng.uniform(0.8, 1.15)
        v.co.z *= 0.8
    lo = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z += -lo + 0.001
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    sub['litter_paper'].objects.link(o)
    return o


def bottle(name, material):
    """a glass bottle lying on its side along x: a body, a shoulder, a neck and a lip, turned ten sides round. Underside at z = 0."""
    profile = [(-0.115, 0.0), (-0.113, 0.026), (-0.105, 0.032), (0.03, 0.032), (0.052, 0.024), (0.078, 0.0125), (0.098, 0.0115), (0.100, 0.0150),
               (0.106, 0.0150), (0.106, 0.0)]
    seg, radius = 10, 0.032
    verts, faces, rings = [], [], []
    for x, r in profile:
        if r == 0.0:
            verts.append((x, 0.0, radius))
            rings.append([len(verts) - 1])
        else:
            ring = []
            for k in range(seg):
                a = 2 * math.pi * k / seg
                verts.append((x, math.cos(a) * r, radius + math.sin(a) * r))
                ring.append(len(verts) - 1)
            rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1:
            faces += [(a[0], b[(k + 1) % seg], b[k]) for k in range(seg)]
        elif len(b) == 1:
            faces += [(a[k], a[(k + 1) % seg], b[0]) for k in range(seg)]
        else:
            faces += [(a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]) for k in range(seg)]
    return add_mesh(name, verts, faces, material, sub['litter_bottles'], smooth=True)


def leaf(name, length, width, material, lift=0.002, fold=0.005):
    """a fallen leaf: a pointed oval with a raised mid-rib and curled edges. Underside near z = lift."""
    n = 6
    verts, faces = [], []
    for i in range(n + 1):
        t = i / n
        x = (t - 0.5) * length
        w = width / 2 * math.sin(math.pi * min(max(t, 0.04), 0.96)) ** 0.8
        curl = rng.uniform(0.0, 0.0035)
        verts += [(x, 0.0, lift + fold), (x, w, lift + curl), (x, -w, lift + curl * rng.uniform(0.5, 1.5))]
    for i in range(n):
        a, b = 3 * i, 3 * (i + 1)
        faces += [(a, b, b + 1, a + 1), (a, a + 2, b + 2, b)]
    return add_mesh(name, verts, faces, material, sub['litter_leaves'])


scrap('litter_paper_a', 0.150, 0.105, M['paper_cream'])
scrap('litter_paper_b', 0.095, 0.070, M['paper_news'], sides=9)
scrap('litter_paper_c', 0.060, 0.045, M['paper_cream'], sides=8)
scrap('litter_paper_d', 0.125, 0.085, M['paper_wet'], lift=0.0015, crumple=0.0015, sides=11)
paper_ball('litter_paper_ball', 0.030, M['paper_news'])
bottle('litter_bottle_brown', M['bottle_brown'])
bottle('litter_bottle_green', M['bottle_green'])
leaf('litter_leaf_a', 0.090, 0.050, M['leaf_rust'])
leaf('litter_leaf_b', 0.075, 0.042, M['leaf_ochre'])
leaf('litter_leaf_c', 0.060, 0.032, M['leaf_dark'])
leaf('litter_leaf_d', 0.100, 0.055, M['leaf_ochre'])

# switched off for drawing (the node tree still reads them): untick the collection in the view layer
for lc in scene.view_layers[0].layer_collection.children:
    if lc.name == 'litter_sources':
        lc.exclude = True

# ---------------------------------------------------------------------------------------------------------------- 2. host strip
setts = bpy.data.objects['street_setts']
channels = bpy.data.objects['street_channels']
kerbs = bpy.data.objects['street_kerbs']
verts, faces = [], []
for src, keep in ((channels, lambda p, me: True), (setts, lambda p, me: abs(p.center.x) > 1.6)):
    me = src.data
    remap = {}
    for p in me.polygons:
        if not keep(p, me):
            continue
        face = []
        for vi in p.vertices:
            if vi not in remap:
                remap[vi] = len(verts)
                verts.append(tuple(src.matrix_world @ me.vertices[vi].co))
            face.append(remap[vi])
        faces.append(tuple(face))
host_me = bpy.data.meshes.new('gutter_litter_host')
host_me.from_pydata(verts, [], faces)
host_me.update()
old = bpy.data.objects.get('gutter_litter')
if old is not None:
    bpy.data.objects.remove(old)
host = bpy.data.objects.new('gutter_litter', host_me)
lit_col = bpy.data.collections.get('litter') or bpy.data.collections.new('litter')
if lit_col.name not in scene.collection.children:
    scene.collection.children.link(lit_col)
lit_col.objects.link(host)
print('HOST', len(host_me.vertices), 'verts', len(host_me.polygons), 'faces', round(sum(p.area for p in host_me.polygons), 2), 'm2')

# ---------------------------------------------------------------------------------------------------------------- 3. the node tree
b = G.Builder('Gutter Litter')
kerb_in = b.input('Kerb', 'OBJECT', description='the kerb: litter gathers against it (leave empty for no kerb pull)')
seed = b.input('Seed', 'INT', 0)
slope = b.input('Max Slope', 'FLOAT', math.radians(35.0), min=0.0, max=math.pi, subtype='ANGLE', description='faces steeper than this (against world up) get nothing')
smin = b.input('Scale Min', 'FLOAT', 0.8, min=0.0, panel='Size')
smax = b.input('Scale Max', 'FLOAT', 1.25, min=0.0, panel='Size')
pull = b.input('Kerb Pull', 'FLOAT', 0.75, min=0.0, max=1.0, subtype='FACTOR', panel='Where it gathers', description='0 even, 1 only right at the kerb')
reach = b.input('Kerb Reach', 'FLOAT', 0.25, min=0.001, subtype='DISTANCE', panel='Where it gathers', description='how far from the kerb the pull fades out')
clump = b.input('Clumping', 'FLOAT', 0.6, min=0.0, max=1.0, subtype='FACTOR', panel='Where it gathers', description='0 even, 1 bare stretches and heaps')
csize = b.input('Clump Size', 'FLOAT', 1.6, min=0.05, subtype='DISTANCE', panel='Where it gathers')
paper_c = b.input('Paper', 'COLLECTION', panel='Paper')
paper_d = b.input('Paper Density', 'FLOAT', 1.2, min=0.0, panel='Paper', description='pieces per square metre where the mask is 1')
leaf_c = b.input('Leaves', 'COLLECTION', panel='Leaves')
leaf_d = b.input('Leaf Density', 'FLOAT', 3.0, min=0.0, panel='Leaves')
bott_c = b.input('Bottles', 'COLLECTION', panel='Bottles')
bott_d = b.input('Bottle Density', 'FLOAT', 0.12, min=0.0, panel='Bottles')
keep_in = b.input('Keep Surface', 'BOOL', False, panel='Output', description='also output the host mesh itself')
realize = b.input('Realize', 'BOOL', False, panel='Output', description='turn instances into real mesh')

up, _, _ = G._world_up_local(b)
flat = b.node('Compare', data_type='VECTOR', mode='DIRECTION', operation='LESS_EQUAL', ins={'A': b.node('Normal'), 'B': up, 'Angle': slope})

# the mask (0 to 1) says how likely a scattered point is to stay: near the kerb and inside a clump
pos = b.node('Position')
kinfo = b.node('ObjectInfo', transform_space='RELATIVE', ins={'Object': kerb_in})
prox = b.node('Proximity', target_element='FACES', ins={'Geometry': (kinfo, 'Geometry'), 'Sample Position': pos})
near = b.node('MapRange', clamp=True, ins={'Value': (prox, 'Distance'), 'From Min': 0.0, 'From Max': reach, 'To Min': 1.0, 'To Max': 0.0})
kerb_mask = b.node('Mix', data_type='FLOAT', ins={'Factor': pull, 'A': 1.0, 'B': near})
inv_size = b.node('Math', operation='DIVIDE', ins={0: 1.0, 1: csize})
shift = b.node('CombineXYZ', ins={'X': b.node('Math', operation='MULTIPLY', ins={0: seed, 1: 13.7})})
noise_pos = b.node('VectorMath', operation='ADD', ins={0: pos, 1: shift})
noise = b.node('NoiseTexture', noise_dimensions='3D', ins={'Vector': noise_pos, 'Scale': inv_size, 'Detail': 2.0, 'Roughness': 0.5})
shaped = b.node('MapRange', clamp=True, ins={'Value': (noise, 'Factor'), 'From Min': 0.38, 'From Max': 0.62, 'To Min': 0.0, 'To Max': 1.0})
clump_mask = b.node('Mix', data_type='FLOAT', ins={'Factor': clump, 'A': 1.0, 'B': shaped})
mask = b.node('Math', operation='MULTIPLY', ins={0: kerb_mask, 1: clump_mask})


def category(label, k, coll, density, kind):
    """points on the eligible faces at the peak density, thinned by the mask, then one instance from the collection on each"""
    dist = b.node('DistributePointsOnFaces', ins={'Mesh': b.geo_in, 'Selection': flat, 'Density': density, 'Seed': G._seed_plus(b, seed, 100 * k)})
    roll = b.node('RandomValue', data_type='FLOAT', ins={'Min': 0.0, 'Max': 1.0, 'Seed': G._seed_plus(b, seed, 100 * k + 1)})
    drop = b.node('Compare', data_type='FLOAT', operation='GREATER_THAN', ins={'A': roll, 'B': mask})
    kept = b.node('DeleteGeometry', ins={'Geometry': dist, 'Selection': drop})
    two_pi = 2 * math.pi
    ang = b.node('RandomValue', data_type='FLOAT', ins={'Min': 0.0, 'Max': two_pi, 'Seed': G._seed_plus(b, seed, 100 * k + 2)})
    spin = b.node('EulerToRotation', ins={'Euler': b.node('CombineXYZ', ins={'Z': ang})})
    rot = b.node('RotateRotation', rotation_space='LOCAL', ins={'Rotation': (dist, 'Rotation'), 'Rotate By': spin})
    scl = b.node('RandomValue', data_type='FLOAT', ins={'Min': smin, 'Max': smax, 'Seed': G._seed_plus(b, seed, 100 * k + 3)})
    ci = b.node('CollectionInfo', ins={'Collection': coll, 'Separate Children': True, 'Reset Children': True})
    pick = b.node('RandomValue', data_type='INT', ins={'Min': 0, 'Max': 9999, 'Seed': G._seed_plus(b, seed, 100 * k + 4)})
    iop = b.node('InstanceOnPoints', ins={'Points': kept, 'Instance': ci, 'Pick Instance': True, 'Instance Index': pick, 'Rotation': rot, 'Scale': scl})
    return b.node('StoreNamedAttribute', data_type='INT', domain='INSTANCE', ins={'Geometry': iop, 'Name': 'litter_kind', 'Value': kind})


cats = [category('paper', 1, paper_c, paper_d, 0), category('leaves', 2, leaf_c, leaf_d, 1), category('bottles', 3, bott_c, bott_d, 2)]
pieces = b.join(cats)
real = b.node('RealizeInstances', ins={'Geometry': pieces})
placed = b.node('Switch', input_type='GEOMETRY', ins={'Switch': realize, 'False': pieces, 'True': real})
surface = b.node('Switch', input_type='GEOMETRY', ins={'Switch': keep_in, 'True': b.geo_in})
b.output_geometry(b.join([surface, placed]))
tree = b.done()
print('BUILT tree', tree.name, 'nodes', len(tree.nodes), 'links', len(tree.links))

md = G.attach(host, tree, inputs={'Kerb': kerbs, 'Seed': 7, 'Paper': sub['litter_paper'], 'Leaves': sub['litter_leaves'], 'Bottles': sub['litter_bottles']})
rep = G.check(md)
print('CHECK', json.dumps(rep))
st = G.stats(host)
print('STATS', json.dumps({k: v for k, v in st.items() if k != 'geometry_name'}, default=str))

# ---------------------------------------------------------------------------------------------------------------- 4. cameras and save
cam_main = bpy.data.objects['main_camera']
close = bpy.data.objects.get('litter_close_camera')
if close is not None:
    bpy.data.objects.remove(close)
cd = bpy.data.cameras.new('litter_close_camera')
cd.sensor_fit = 'VERTICAL'
cd.angle_y = math.radians(40.0)
cd.clip_start, cd.clip_end = 0.05, 1500.0
close = bpy.data.objects.new('litter_close_camera', cd)
scene.collection.objects.link(close)
eye = Vector((0.55, 6.0, ground_z(6.0) + 0.55))
aim = Vector((2.35, 11.5, ground_z(11.5) + 0.02))
close.location = eye
close.rotation_euler = (aim - eye).to_track_quat('-Z', 'Y').to_euler()

os.makedirs(OUT, exist_ok=True)
scene.camera = close
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'street_litter_close.blend'), copy=True)
scene.camera = cam_main
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'street_litter.blend'), copy=True)
print('SAVED', OUT)
