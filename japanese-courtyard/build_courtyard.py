# What this does: builds a small Japanese courtyard in Blender 5.2 with the Astra Painted Workbench add-on (roof, seated
# stones, planks, moss and pebbles) plus hand-made walls, posts, paper screens, trees, bamboo, gravel and a pond, then
# lights it at golden hour and renders a photograph.
# Use: blender -b --disable-autoexec --python build_courtyard.py -- ADDON_FOLDER OUT_PREFIX [--quick] [--samples N] [--width W]
#   --quick   small, fast preview;  --samples N  Cycles samples;  --width W  picture width in pixels (3:2 picture)
# Writes OUT_PREFIX.png and OUT_PREFIX.blend. Metres; x is across, y is away from the camera, z is up.
import bpy, bmesh, math, random, sys, time
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from astra_loader import load_astra, apply_blender_52_shim

ARGS = sys.argv[sys.argv.index('--') + 1:]
ADDON_FOLDER, OUT_PREFIX = ARGS[0], ARGS[1]
QUICK = '--quick' in ARGS
def option(name, default):
    return type(default)(ARGS[ARGS.index(name) + 1]) if name in ARGS else default
SAMPLES = option('--samples', 24 if QUICK else 128)
WIDTH = option('--width', 720 if QUICK else 2400)
HEIGHT = int(WIDTH * 2 / 3)
START = time.time()
def say(text):
    print(f'[{time.time() - START:6.1f}s] {text}', flush=True)

api = load_astra(ADDON_FOLDER)
say(f'add-on loaded; Blender 5.2 shim applied: {apply_blender_52_shim(api)}')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
RNG = random.Random(2026)

# ------------------------------------------------------------------ small helpers
def smoothstep(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def collection(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
C_WORLD, C_ARCH, C_STONE, C_PLANT, C_LIGHT = (collection(n) for n in ('Ground and water', 'Hall and walls', 'Stones and bridge', 'Plants', 'Lights'))

def link(obj, col):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    col.objects.link(obj); return obj

def object_from_bmesh(name, bm, material, col):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if material is not None: me.materials.append(material)
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); return ob

def principled(name, color, rough=0.8, **inputs):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    for key, value in inputs.items():
        b.inputs[key.replace('_', ' ')].default_value = value
    return m

def noise_material(name, color_a, color_b, scale=5.0, rough=0.85, detail_scale=40.0, bump=0.25, stretch=(1, 1, 1), emission=0.0):
    """A node material whose colour wanders between two colours with noise, plus fine bump."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree; n = t.nodes; l = t.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    coord = n.new('ShaderNodeTexCoord'); mapping = n.new('ShaderNodeMapping'); mapping.inputs['Scale'].default_value = stretch
    l.new(coord.outputs['Object'], mapping.inputs['Vector'])
    big = n.new('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = scale; big.inputs['Detail'].default_value = 6
    fine = n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = detail_scale; fine.inputs['Detail'].default_value = 3
    l.new(mapping.outputs['Vector'], big.inputs['Vector']); l.new(mapping.outputs['Vector'], fine.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*color_a, 1); ramp.color_ramp.elements[1].color = (*color_b, 1)
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.65
    l.new(big.outputs['Fac'], ramp.inputs['Fac']); l.new(ramp.outputs['Color'], b.inputs['Base Color'])
    bm = n.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = bump; bm.inputs['Distance'].default_value = 0.02
    l.new(fine.outputs['Fac'], bm.inputs['Height']); l.new(bm.outputs['Normal'], b.inputs['Normal'])
    if emission:
        l.new(ramp.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emission
    return m

def vertex_color_material(name, rough=0.6, emission=0.0, layer='Col'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree; b = t.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    vc = t.nodes.new('ShaderNodeVertexColor'); vc.layer_name = layer
    t.links.new(vc.outputs['Color'], b.inputs['Base Color'])
    if emission:
        t.links.new(vc.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emission
    return m

def leaf_material(name, rough=0.55, translucency=0.5, emission=0.0):
    """Vertex-coloured leaf that lets light through (Translucent BSDF mixed in), drawn on both sides."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree; n = t.nodes; l = t.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    vc = n.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    tr = n.new('ShaderNodeBsdfTranslucent'); mix = n.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = translucency
    out = n['Material Output']
    l.new(vc.outputs['Color'], b.inputs['Base Color']); l.new(vc.outputs['Color'], tr.inputs['Color'])
    if emission:
        l.new(vc.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emission
    l.new(b.outputs['BSDF'], mix.inputs[1]); l.new(tr.outputs['BSDF'], mix.inputs[2]); l.new(mix.outputs['Shader'], out.inputs['Surface'])
    m.use_backface_culling = False
    return m

def emission_material(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree; t.nodes.clear()
    e = t.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    o = t.nodes.new('ShaderNodeOutputMaterial'); t.links.new(e.outputs['Emission'], o.inputs['Surface']); return m

def add_box(bm, center, size, matrix=None):
    sx, sy, sz = size
    ret = bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Translation(center) @ (matrix or Matrix.Identity(4)) @ Matrix.Diagonal((sx, sy, sz, 1))
    bmesh.ops.transform(bm, matrix=m, verts=ret['verts']); return ret['verts']

def add_cylinder(bm, base, top, radius, segments=8, radius_top=None):
    a, b = Vector(base), Vector(top); d = b - a
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius if radius_top is None else radius_top, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=ret['verts']); return ret['verts']

# ------------------------------------------------------------------ the ground: shape, pond and hill
POND_C, POND_A, POND_B, POND_ROT = (-3.0, 1.0), 3.3, 2.5, math.radians(10)
WATER_Z = -0.12
def pond_radius(x, y):
    """About 1.0 on the pond's edge, below 1 in the water (an organic wobbly outline)."""
    dx, dy = x - POND_C[0], y - POND_C[1]
    u = dx * math.cos(-POND_ROT) - dy * math.sin(-POND_ROT); v = dx * math.sin(-POND_ROT) + dy * math.cos(-POND_ROT)
    th = math.atan2(v / POND_B, u / POND_A)
    wobble = 1 + 0.10 * math.sin(3 * th + 0.8) + 0.06 * math.sin(5 * th + 2.1) + 0.04 * math.sin(2 * th)
    return math.hypot(u / POND_A, v / POND_B) / wobble

def ground_height(x, y):
    z = -0.58 * smoothstep((1.0 - pond_radius(x, y)) / 0.55)
    z += 0.95 * math.exp(-(((x + 8.4) / 2.7) ** 2 + ((y - 6.4) / 3.0) ** 2))     # grassy rise, back left
    z += 0.35 * math.exp(-(((x + 6.8) / 3.0) ** 2 + ((y + 2.6) / 2.2) ** 2))     # a soft swell front left
    return z

X0, X1, Y0, Y1, STEP = -11.0, 11.0, -8.5, 12.5, 0.25
nx, ny = int(round((X1 - X0) / STEP)), int(round((Y1 - Y0) / STEP))
verts = [(X0 + i * STEP, Y0 + j * STEP, 0.0) for j in range(ny + 1) for i in range(nx + 1)]
verts = [(x, y, ground_height(x, y)) for x, y, _ in verts]
faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
me = bpy.data.meshes.new('Courtyard ground source'); me.from_pydata(verts, [], faces); me.update()
ground_material = noise_material('Moss and earth', (0.07, 0.05, 0.03), (0.05, 0.15, 0.035), scale=4.0, rough=0.95, detail_scale=90, bump=0.5)
me.materials.append(ground_material)
source = bpy.data.objects.new('Courtyard ground source', me); C_WORLD.objects.link(source)
say(f'ground source: {len(verts)} vertices')

spec = api.default_spec(bounds=(X0, Y0, X1, Y1), seed=2026)
spec.update(dict(
    detail_scale=1.0,
    relief=dict(height=0.20, banks=[
        dict(id='bank-left', center=[-6.4, 1.3], radius=[1.5, 1.3], weight=1.0),
        dict(id='bank-back', center=[-3.4, 3.7], radius=[2.6, 0.8], weight=0.8),
        dict(id='bank-front', center=[-3.0, -1.7], radius=[2.8, 0.7], weight=0.7)]),
    paths=[dict(points=[[4.3, -5.6], [3.2, -3.1], [2.4, -1.0], [2.0, 0.9], [2.2, 2.8], [2.2, 4.6]], width=1.15, feather=0.5)],
    protected=[
        dict(min=[-5.3, 4.5], max=[6.4, 10.8], feather=0.3),          # hall platform
        dict(min=[0.8, -5.9], max=[9.2, 1.9], feather=0.4),           # raked gravel court
        dict(min=[-1.5, -1.2], max=[0.1, 0.1], feather=0.3),          # bridge landing, near bank
        dict(min=[-6.9, 0.8], max=[-5.4, 2.3], feather=0.3)],         # bridge landing, far bank
    water=dict(level=WATER_Z, shore_reach=0.5),
    contacts=[dict(id='contact-rocks', center=[-3.5, 3.7], radius=[2.6, 0.9], weight=0.8),
              dict(id='contact-maple', center=[-6.8, 1.6], radius=[1.6, 1.5], weight=0.7)],
    shelter=[dict(id='shelter-maple', center=[-6.2, 1.5], radius=[2.6, 2.4], weight=0.9),
             dict(id='shelter-hill', center=[-8.2, 6.0], radius=[2.6, 2.2], weight=0.7)],
    pebbles=dict(density=34.0, radius=0.07, patches=[
        dict(id='pebbles-front-shore', center=[-3.0, -1.45], radius=[3.0, 0.5], weight=1.0),
        dict(id='pebbles-back-shore', center=[-3.3, 3.45], radius=[2.6, 0.4], weight=0.8),
        dict(id='pebbles-right-shore', center=[0.25, 1.1], radius=[0.5, 1.2], weight=0.9),
        dict(id='pebbles-left-shore', center=[-6.4, 0.3], radius=[0.5, 1.1], weight=0.7)]),
    moss=dict(density=15.0, radius=0.14, body_height=0.05, contact_influence=0.65, shelter_influence=0.75, patches=[
        dict(id='moss-front-left', center=[-7.4, -3.0], radius=[2.6, 2.0], weight=0.75),
        dict(id='moss-hill', center=[-8.2, 6.0], radius=[2.6, 2.1], weight=0.95),
        dict(id='moss-maple-root', center=[-6.9, 2.0], radius=[1.7, 1.5], weight=0.95),
        dict(id='moss-rocks', center=[-3.4, 4.0], radius=[2.3, 0.7], weight=0.9),
        dict(id='moss-lantern', center=[1.0, 1.4], radius=[0.9, 0.8], weight=0.8),
        dict(id='moss-gravel-islands', center=[5.9, -2.2], radius=[1.3, 1.0], weight=0.6),
        dict(id='moss-path-edge', center=[3.9, -3.3], radius=[1.4, 1.3], weight=0.5)])))
land = api.create_landscape(source, spec, name='Courtyard')
ground = land['astra_ground']
say(f'landscape built; relief peak {land and ground and spec["relief"]["height"]}')

depsgraph = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(ground, depsgraph)
def ground_z(x, y):
    hit = bvh.ray_cast(Vector((x, y, 20.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0

# water: one plane just under the shoreline; the ground hides it everywhere but the pond
bm = bmesh.new(); add_box(bm, (POND_C[0], POND_C[1], WATER_Z - 0.01), (8.2, 6.2, 0.02))
water_material = principled('Pond water', (0.035, 0.07, 0.07), rough=0.06, IOR=1.33, Specular_IOR_Level=0.6)
t = water_material.node_tree; tc = t.nodes.new('ShaderNodeTexCoord'); wn = t.nodes.new('ShaderNodeTexNoise')
wn.inputs['Scale'].default_value = 6.0; wn.inputs['Detail'].default_value = 2; t.links.new(tc.outputs['Object'], wn.inputs['Vector'])
wb = t.nodes.new('ShaderNodeBump'); wb.inputs['Strength'].default_value = 0.035; wb.inputs['Distance'].default_value = 0.03
t.links.new(wn.outputs['Fac'], wb.inputs['Height']); t.links.new(wb.outputs['Normal'], t.nodes['Principled BSDF'].inputs['Normal'])
object_from_bmesh('Pond water', bm, water_material, C_WORLD)

# raked gravel court, with parallel rake lines and fine grain (shading only, no extra mesh)
gravel_material = bpy.data.materials.new('Raked gravel'); gravel_material.use_nodes = True
gt = gravel_material.node_tree; gb = gt.nodes['Principled BSDF']; gb.inputs['Roughness'].default_value = 0.92
gc = gt.nodes.new('ShaderNodeTexCoord'); gmap = gt.nodes.new('ShaderNodeMapping')
gwave = gt.nodes.new('ShaderNodeTexWave'); gwave.wave_type = 'BANDS'; gwave.bands_direction = 'X'; gwave.inputs['Scale'].default_value = 5.5
gwave.inputs['Distortion'].default_value = 2.2; gwave.inputs['Detail'].default_value = 1.0; gwave.inputs['Detail Scale'].default_value = 0.6
gwave.wave_profile = 'SIN'
ggrain = gt.nodes.new('ShaderNodeTexNoise'); ggrain.inputs['Scale'].default_value = 220; ggrain.inputs['Detail'].default_value = 4
gmix = gt.nodes.new('ShaderNodeMath'); gmix.operation = 'ADD'; gmix.inputs[1].default_value = 0.0
gt.links.new(gc.outputs['Object'], gmap.inputs['Vector']); gt.links.new(gmap.outputs['Vector'], gwave.inputs['Vector']); gt.links.new(gmap.outputs['Vector'], ggrain.inputs['Vector'])
gtone = gt.nodes.new('ShaderNodeTexNoise'); gtone.inputs['Scale'].default_value = 1.4; gt.links.new(gmap.outputs['Vector'], gtone.inputs['Vector'])
gramp = gt.nodes.new('ShaderNodeValToRGB'); gramp.color_ramp.elements[0].color = (0.115, 0.092, 0.068, 1); gramp.color_ramp.elements[1].color = (0.25, 0.205, 0.155, 1)
gt.links.new(ggrain.outputs['Fac'], gramp.inputs['Fac']); gt.links.new(gramp.outputs['Color'], gb.inputs['Base Color'])
gb1 = gt.nodes.new('ShaderNodeBump'); gb1.inputs['Strength'].default_value = 0.0; gb1.inputs['Distance'].default_value = 0.03
gt.links.new(gwave.outputs['Fac'], gb1.inputs['Height'])
gb2 = gt.nodes.new('ShaderNodeBump'); gb2.inputs['Strength'].default_value = 0.5; gb2.inputs['Distance'].default_value = 0.004
gt.links.new(ggrain.outputs['Fac'], gb2.inputs['Height']); gt.links.new(gb1.outputs['Normal'], gb2.inputs['Normal']); gt.links.new(gb2.outputs['Normal'], gb.inputs['Normal'])
GRAVEL_ROCKS = [(5.5, -1.9), (6.6, -2.7), (7.4, -0.8)]
STEP_PATH = [(4.3, -5.6), (3.2, -3.1), (2.4, -1.0), (2.0, 0.9), (2.2, 2.8)]
def dist_to_path(x, y):
    best = 99.0
    for (ax, ay), (bx, by) in zip(STEP_PATH, STEP_PATH[1:]):
        dx, dy = bx - ax, by - ay; t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best
def gravel_height(x, y):
    d = min(math.hypot(x - rx, y - ry) for rx, ry in GRAVEL_ROCKS)
    ring_w = 1.0 - smoothstep((d - 1.1) / 0.8)
    rings = math.sin(math.tau * d / 0.17) * ring_w
    lines = math.sin(math.tau * (x + 0.08 * math.sin(y * 0.9)) / 0.17) * (1.0 - ring_w)
    keep = smoothstep((dist_to_path(x, y) - 0.45) / 0.35)            # flat under the stepping stones
    edge = smoothstep((min(x - 0.95, 9.05 - x, y + 5.85, 1.85 - y)) / 0.25)
    return 0.016 * (rings + lines) * keep * edge
GX0, GX1, GY0, GY1, GSTEP = 0.9, 9.1, -5.9, 1.9, 0.045
gnx, gny = int(round((GX1 - GX0) / GSTEP)), int(round((GY1 - GY0) / GSTEP))
gverts = [(GX0 + i * GSTEP, GY0 + j * GSTEP, 0.02 + gravel_height(GX0 + i * GSTEP, GY0 + j * GSTEP)) for j in range(gny + 1) for i in range(gnx + 1)]
gfaces = [(j * (gnx + 1) + i, j * (gnx + 1) + i + 1, (j + 1) * (gnx + 1) + i + 1, (j + 1) * (gnx + 1) + i) for j in range(gny) for i in range(gnx)]
gme = bpy.data.meshes.new('Raked gravel court'); gme.from_pydata(gverts, [], gfaces); gme.update(); gme.materials.append(gravel_material)
for poly in gme.polygons: poly.use_smooth = True
gravel = bpy.data.objects.new('Raked gravel court', gme); C_WORLD.objects.link(gravel)

# ------------------------------------------------------------------ materials for the buildings
plaster = noise_material('Plaster wall', (0.62, 0.585, 0.52), (0.80, 0.765, 0.69), scale=3.0, rough=0.95, detail_scale=30, bump=0.15)
timber = noise_material('Dark timber', (0.055, 0.032, 0.018), (0.13, 0.078, 0.042), scale=9.0, rough=0.55, detail_scale=60, bump=0.3, stretch=(30, 30, 2.5))
beam_timber = noise_material('Beam timber', (0.05, 0.03, 0.017), (0.11, 0.068, 0.038), scale=7.0, rough=0.6, detail_scale=55, bump=0.3, stretch=(2.5, 30, 30))
stone_plinth = noise_material('Plinth stone', (0.10, 0.098, 0.092), (0.26, 0.25, 0.225), scale=6.0, rough=0.9, detail_scale=26, bump=0.6)
cap_tile = principled('Wall cap tile', (0.032, 0.034, 0.04), rough=0.38)
paper_glow = emission_material('Shoji paper glow', (1.0, 0.62, 0.30), 5.0)
paper_dim = emission_material('Shoji paper, softer', (1.0, 0.72, 0.45), 2.4)
interior_dark = emission_material('Open room, dim', (0.45, 0.25, 0.10), 0.35)
bamboo_green = noise_material('Bamboo stalk', (0.20, 0.30, 0.045), (0.38, 0.46, 0.09), scale=3.0, rough=0.4, detail_scale=18, bump=0.1, stretch=(4, 4, 0.5))
bamboo_leaf = principled('Bamboo leaf', (0.11, 0.28, 0.035), rough=0.5, Emission_Color=(0.06, 0.18, 0.02, 1), Emission_Strength=0.15)
bamboo_leaf.use_backface_culling = False
trunk_bark = noise_material('Bark', (0.055, 0.04, 0.03), (0.14, 0.11, 0.085), scale=5.0, rough=0.9, detail_scale=34, bump=0.7, stretch=(14, 14, 1.2))
maple_leaves = leaf_material('Maple leaves', rough=0.5, translucency=0.55, emission=0.06)
maple_core = vertex_color_material('Maple inner mass', rough=0.7, emission=0.03)
pine_needles = vertex_color_material('Pine needles', rough=0.7, emission=0.05)
hill_material = principled('Far hill', (0.012, 0.03, 0.022), rough=1.0)
fallen_leaf = vertex_color_material('Fallen leaves', rough=0.7, emission=0.12)

# ------------------------------------------------------------------ the hall: platform, floor, posts, screens, roof
HALL_X0, HALL_X1, PLINTH_Y0, HALL_Y0, HALL_Y1, FLOOR_Z = -5.0, 5.4, 4.7, 6.4, 10.1, 0.55
POST, BEAM_Z, EAVE_Z = 0.17, 3.0, 3.2
bm = bmesh.new()
add_box(bm, ((HALL_X0 + HALL_X1) / 2, (PLINTH_Y0 + HALL_Y1 + 0.2) / 2, FLOOR_Z / 2 - 0.02), (HALL_X1 - HALL_X0 + 0.5, HALL_Y1 + 0.2 - PLINTH_Y0, FLOOR_Z + 0.04))
object_from_bmesh('Stone plinth', bm, stone_plinth, C_ARCH)

# veranda deck: Astra planks laid across the depth; three runs side by side (the add-on limits one run to 4 m wide)
deck_runs = []
deck_x = HALL_X0 - 0.25; deck_depth = HALL_Y0 - PLINTH_Y0 + 0.1
total_w = HALL_X1 - HALL_X0 + 0.5; run_w = total_w / 3.0
for i in range(3):
    cx = deck_x + run_w * (i + 0.5)
    run = api.create_planks(length=deck_depth, width=run_w, count=14, seed=21 + i, variation=0.22, gap=0.012,
                            location=(cx, PLINTH_Y0 - 0.1 + deck_depth / 2, FLOOR_Z), rotation=(0, 0, math.pi / 2) if False else (0, 0, 0), collection=C_ARCH)
    deck_runs.append(run)
say('veranda deck built')

post_xs = [HALL_X0 + 0.15 + i * (HALL_X1 - HALL_X0 - 0.3) / 4 for i in range(5)]
bm = bmesh.new()
for px in post_xs:
    add_box(bm, (px, HALL_Y0 + 0.1, FLOOR_Z + (BEAM_Z - FLOOR_Z) / 2), (POST, POST, BEAM_Z - FLOOR_Z))
for px in (HALL_X0 + 0.15, HALL_X1 - 0.15):                                   # rear corner posts
    add_box(bm, (px, HALL_Y1 - 0.1, FLOOR_Z + (BEAM_Z - FLOOR_Z) / 2), (POST, POST, BEAM_Z - FLOOR_Z))
object_from_bmesh('Hall posts', bm, timber, C_ARCH)
bm = bmesh.new()
for z, h, d in ((BEAM_Z + 0.07, 0.17, 0.2), (2.28, 0.09, 0.13), (FLOOR_Z + 0.06, 0.09, 0.13)):   # nageshi beam, lintel, sill
    add_box(bm, ((HALL_X0 + HALL_X1) / 2, HALL_Y0 + 0.1, z), (HALL_X1 - HALL_X0 + 0.1, d, h))
add_box(bm, ((HALL_X0 + HALL_X1) / 2, HALL_Y0 - 0.55, BEAM_Z + 0.14), (HALL_X1 - HALL_X0 + 0.3, 0.2, 0.2))        # eave beam over the deck
for px in (HALL_X0 + 0.15, HALL_X1 - 0.15, (HALL_X0 + HALL_X1) / 2):                                              # deck-edge posts
    add_box(bm, (px, HALL_Y0 - 0.55, FLOOR_Z + (BEAM_Z - FLOOR_Z) / 2), (0.19, 0.19, BEAM_Z - FLOOR_Z))
object_from_bmesh('Hall beams', bm, beam_timber, C_ARCH)

# shoji: a glowing paper panel behind a lattice of thin bars, in each bay; one bay half open onto a dim room
bm_bar = bmesh.new(); bm_paper = bmesh.new(); bm_room = bmesh.new()
lo, hi = 0.67, 2.2
for b in range(4):
    x0, x1 = post_xs[b] + POST / 2, post_xs[b + 1] - POST / 2
    leaves = 2
    for k in range(leaves):
        lx0 = x0 + (x1 - x0) * k / leaves; lx1 = x0 + (x1 - x0) * (k + 1) / leaves
        if b == 2 and k == 0:                           # this leaf slid away: a dark room behind
            add_box(bm_room, ((lx0 + lx1) / 2, HALL_Y0 + 0.9, (lo + hi) / 2), (lx1 - lx0, 0.05, hi - lo))
            continue
        y = HALL_Y0 + 0.1 + (0.035 if k else -0.01)
        add_box(bm_paper, ((lx0 + lx1) / 2, y, (lo + hi) / 2), (lx1 - lx0 - 0.02, 0.012, hi - lo - 0.02))
        for i in range(5):                                                      # vertical bars
            xx = lx0 + (lx1 - lx0) * i / 4 if i else lx0 + 0.015
            xx = min(xx, lx1 - 0.015)
            add_box(bm_bar, (xx, y - 0.012, (lo + hi) / 2), (0.028, 0.028, hi - lo))
        for i in range(9):                                                      # horizontal bars
            zz = lo + (hi - lo) * i / 8 + (0.012 if i == 0 else (-0.012 if i == 8 else 0))
            add_box(bm_bar, ((lx0 + lx1) / 2, y - 0.012, zz), (lx1 - lx0, 0.028, 0.022))
object_from_bmesh('Shoji bars', bm_bar, timber, C_ARCH)
object_from_bmesh('Shoji paper', bm_paper, paper_glow, C_ARCH)
object_from_bmesh('Open room back', bm_room, interior_dark, C_ARCH)

# plaster above the lintel and the side/back walls of the hall
bm = bmesh.new()
add_box(bm, ((HALL_X0 + HALL_X1) / 2, HALL_Y0 + 0.2, (2.3 + BEAM_Z) / 2 + 0.0), (HALL_X1 - HALL_X0, 0.1, BEAM_Z - 2.3 - 0.1))
add_box(bm, ((HALL_X0 + HALL_X1) / 2, HALL_Y1, (FLOOR_Z + BEAM_Z) / 2), (HALL_X1 - HALL_X0, 0.12, BEAM_Z - FLOOR_Z))
for px in (HALL_X0 + 0.1, HALL_X1 - 0.1):
    add_box(bm, (px, (HALL_Y0 + HALL_Y1) / 2, (FLOOR_Z + BEAM_Z) / 2), (0.12, HALL_Y1 - HALL_Y0, BEAM_Z - FLOOR_Z))
object_from_bmesh('Hall plaster', bm, plaster, C_ARCH)
bm = bmesh.new()                                                    # dark soffit under the eaves, front and back
add_box(bm, ((HALL_X0 + HALL_X1) / 2, (HALL_Y0 - 0.9 + HALL_Y0 + 0.1) / 2, EAVE_Z - 0.04), (HALL_X1 - HALL_X0 + 1.2, 1.1, 0.06))
object_from_bmesh('Eave soffit', bm, beam_timber, C_ARCH)

ROOF_W, ROOF_HD, ROOF_RISE = 11.6, 2.8, 1.25
roof_y = 7.2
roof = api.create_roof('Hall roof', api.RoofSpec(width=ROOF_W, half_depth=ROOF_HD, rise=ROOF_RISE, seed=19, surface_seed=33),
                       location=((HALL_X0 + HALL_X1) / 2, roof_y, EAVE_Z), collection=C_ARCH)
say('roof built')

# ------------------------------------------------------------------ garden walls with tiled caps
def plaster_wall(name, x0, y0, x1, y1, height=2.1):
    """A plaster wall along a line from (x0,y0) to (x1,y1) with a small dark tiled cap."""
    d = Vector((x1 - x0, y1 - y0, 0)); length = d.length; yaw = math.atan2(d.y, d.x)
    rot = Matrix.Rotation(yaw, 4, 'Z'); mid = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0))
    bm = bmesh.new(); add_box(bm, mid + Vector((0, 0, height / 2)), (length, 0.3, height), rot)
    object_from_bmesh(name, bm, plaster, C_ARCH)
    bm = bmesh.new()
    add_box(bm, mid + Vector((0, 0, height + 0.12)), (length + 0.1, 0.5, 0.07), rot)                                   # cap base
    for s in (-1, 1):                                                                                                 # two sloping cap sides
        add_box(bm, mid + Vector((0, 0, height + 0.17)) + rot.to_3x3() @ Vector((0, s * 0.15, 0)), (length + 0.1, 0.30, 0.04), rot @ Matrix.Rotation(-s * 0.25, 4, 'X'))
    add_box(bm, mid + Vector((0, 0, height + 0.01)), (length, 0.34, 0.02), rot)
    object_from_bmesh(name + ' cap', bm, cap_tile, C_ARCH)

plaster_wall('Back wall, left', -10.4, 10.5, HALL_X0 - 0.2, 10.5)
plaster_wall('Back wall, right', HALL_X1 + 0.2, 10.5, 10.4, 10.5)
# (no left wall: the low sun comes in from that side)
plaster_wall('Right wall behind hall', 10.4, 1.4, 10.4, 10.5, 2.2)

# bamboo fence (takegaki) along the right edge of the gravel court
bm = bmesh.new(); fx = 9.7
for i in range(int((1.4 + 6.2) / 0.085)):
    y = -6.2 + i * 0.085; h = 1.55 + RNG.uniform(-0.02, 0.03)
    add_cylinder(bm, (fx, y, ground_z(fx, y) - 0.05), (fx, y, ground_z(fx, y) + h), 0.026, 6)
for z in (0.38, 0.82, 1.28):
    add_cylinder(bm, (fx - 0.04, -6.3, z), (fx - 0.04, 1.5, z), 0.034, 8)
for y in (-6.1, -3.5, -0.9, 1.4):
    add_cylinder(bm, (fx - 0.03, y, -0.05), (fx - 0.03, y, 1.72), 0.05, 8)
object_from_bmesh('Bamboo fence', bm, bamboo_green, C_ARCH)

# ------------------------------------------------------------------ stones (add-on seated stones)
def seat_stone(name, x, y, length, width, height, yaw=0.0, sink=0.0, tilt=(0.0, 0.0), z=None, seed=None, bevel=0.02):
    base = ground_z(x, y) - sink if z is None else z
    normal = Vector((tilt[0], tilt[1], 1.0)).normalized()
    s = api.create_stone(name, api.StoneSpec(length=length, width=width, height=height, upper_variation=0.045,
                                              seed=RNG.randrange(1, 9000) if seed is None else seed, surface_seed=RNG.randrange(1, 9000), bevel=bevel),
                         location=(x, y, base), normal=tuple(normal), yaw=yaw, collection=C_STONE)
    return s

# stepping stones (tobi-ishi) along the path to the veranda step
path = [(4.3, -5.6), (3.2, -3.1), (2.4, -1.0), (2.0, 0.9), (2.2, 2.8)]
spots = []
for (ax, ay), (bx, by) in zip(path, path[1:]):
    seg = math.hypot(bx - ax, by - ay); n = max(2, int(seg / 0.95))
    for i in range(n):
        t = (i + 0.5) / n; spots.append((ax + (bx - ax) * t, ay + (by - ay) * t))
for i, (x, y) in enumerate(spots):
    off = 0.22 * (1 if i % 2 else -1) * RNG.uniform(0.5, 1.0)
    seat_stone(f'Stepping stone {i}', x + off, y + RNG.uniform(-0.1, 0.1), RNG.uniform(0.62, 0.86), RNG.uniform(0.5, 0.7), 0.26,
               yaw=RNG.uniform(-0.5, 0.5), sink=0.17, tilt=(RNG.uniform(-0.03, 0.03), RNG.uniform(-0.03, 0.03)), bevel=0.018)
seat_stone('Veranda step', 2.2, 4.25, 1.9, 0.62, 0.34, yaw=0.0, z=FLOOR_Z - 0.34 + 0.02 - 0.0, seed=14)
seat_stone('Veranda step, lower', 2.2, 3.7, 1.35, 0.55, 0.26, yaw=0.0, sink=0.14, seed=15)

# stones around the pond (ishigumi): placed on the pond's own edge
for i in range(15):
    th = i / 15 * math.tau + RNG.uniform(-0.12, 0.12)
    r = 1.0
    ux, vy = POND_A * math.cos(th), POND_B * math.sin(th)
    x = POND_C[0] + ux * math.cos(POND_ROT) - vy * math.sin(POND_ROT); y = POND_C[1] + ux * math.sin(POND_ROT) + vy * math.cos(POND_ROT)
    # walk outward until the ground is above the waterline, so each stone sits on the bank
    for _ in range(40):
        if ground_z(x, y) > WATER_Z + 0.04: break
        x += math.cos(th) * 0.04; y += math.sin(th) * 0.04
    L = RNG.uniform(0.55, 1.25); W = RNG.uniform(0.45, 0.95); H = RNG.uniform(0.38, 0.75)
    seat_stone(f'Pond edge stone {i}', x, y, L, W, H, yaw=th + RNG.uniform(-0.6, 0.6), sink=H * 0.55, tilt=(RNG.uniform(-0.1, 0.1), RNG.uniform(-0.1, 0.1)))

# rock group (taki-ishi) on the far shore, and two standing rocks in the gravel
for i, (x, y, L, W, H, yaw) in enumerate([(-4.3, 3.75, 1.2, 0.85, 1.9, 0.4), (-2.8, 3.65, 1.6, 1.0, 1.25, -0.3), (-1.3, 3.2, 0.9, 0.7, 0.95, 0.9),
                                          (-5.6, 3.3, 1.0, 0.8, 0.9, -0.7), (-3.7, 3.35, 0.8, 0.6, 0.55, 0.2)]):
    seat_stone(f'Rock {i}', x, y, L, W, H, yaw=yaw, sink=H * 0.22, tilt=(0.08 * (i % 2 - 0.5), 0.06), seed=40 + i, bevel=0.03)
seat_stone('Gravel rock 0', GRAVEL_ROCKS[0][0], GRAVEL_ROCKS[0][1], 1.1, 0.8, 0.95, yaw=0.5, sink=0.25, tilt=(0.06, -0.05), seed=61, bevel=0.03)
seat_stone('Gravel rock 1', GRAVEL_ROCKS[1][0], GRAVEL_ROCKS[1][1], 0.8, 0.6, 0.5, yaw=-0.4, sink=0.15, tilt=(-0.05, 0.04), seed=62, bevel=0.03)
seat_stone('Gravel rock 2', GRAVEL_ROCKS[2][0], GRAVEL_ROCKS[2][1], 0.7, 0.55, 0.38, yaw=1.1, sink=0.1, seed=63, bevel=0.025)

# stone lantern (tōrō) beside the pond's right shore, stacked from add-on stones
LX, LY = 0.95, 1.1
lz = ground_z(LX, LY)
parts = [('Lantern base', 0.75, 0.75, 0.28), ('Lantern post', 0.26, 0.26, 0.78), ('Lantern gallery', 0.7, 0.7, 0.2),
         ('Lantern firebox', 0.46, 0.46, 0.42), ('Lantern cap', 0.96, 0.96, 0.3)]
z = lz - 0.04
for name, L, W, H in parts:
    s = seat_stone(name, LX, LY, L, W, H, yaw=math.radians(35), z=z, seed=70 + int(L * 10), bevel=min(0.02, H * 0.07))
    z += H - 0.015
lantern_top = z
bm = bmesh.new()                                                       # little finial and the glowing window
add_cylinder(bm, (LX, LY, lantern_top - 0.02), (LX, LY, lantern_top + 0.2), 0.07, 10, radius_top=0.01)
object_from_bmesh('Lantern finial', bm, stone_plinth, C_STONE)
fire_z = lz - 0.04 + (0.28 - 0.015) + (0.78 - 0.015) + (0.2 - 0.015) + 0.21
glow = emission_material('Lantern flame', (1.0, 0.5, 0.16), 80.0)
bm = bmesh.new(); add_box(bm, (LX, LY, fire_z), (0.30, 0.30, 0.24), Matrix.Rotation(math.radians(35), 4, 'Z'))
object_from_bmesh('Lantern window glow', bm, glow, C_STONE)

# water basin (tsukubai) beside the veranda steps
BX, BY = 4.4, 4.0
seat_stone('Water basin', BX, BY, 0.62, 0.62, 0.52, yaw=0.3, sink=0.2, seed=88, bevel=0.025)
bm = bmesh.new(); add_cylinder(bm, (BX, BY, ground_z(BX, BY) - 0.2 + 0.46), (BX, BY, ground_z(BX, BY) - 0.2 + 0.505), 0.22, 18)
object_from_bmesh('Basin water', bm, water_material, C_STONE)

# ------------------------------------------------------------------ the zigzag bridge (yatsuhashi): add-on planks on stone piers
DECK_TOP = 0.20
nodes_xy = [(-0.55, -0.6), (-2.0, 1.0), (-3.9, 0.15), (-5.95, 1.55)]
for i, ((ax, ay), (bx, by)) in enumerate(zip(nodes_xy, nodes_xy[1:])):
    d = Vector((bx - ax, by - ay)); L = d.length
    yaw = math.atan2(-d.x, d.y)
    api.create_planks(length=L + 0.55, width=1.05, count=int((L + 0.55) / 0.15), seed=90 + i, variation=0.2, gap=0.012,
                      location=((ax + bx) / 2, (ay + by) / 2, DECK_TOP + 0.012 * i), rotation=(0, 0, yaw), collection=C_STONE)
for i in range(1, 3):        # a square landing where the bridge turns, so no wedge gap shows
    (px, py), (ax, ay), (bx, by) = nodes_xy[i - 1], nodes_xy[i], nodes_xy[i + 1]
    d1 = Vector((ax - px, ay - py)).normalized(); d2 = Vector((bx - ax, by - ay)).normalized(); mid = (d1 + d2).normalized()
    api.create_planks(length=1.2, width=1.2, count=8, seed=140 + i, variation=0.18, gap=0.012,
                      location=(ax, ay, DECK_TOP + 0.03), rotation=(0, 0, math.atan2(-mid.x, mid.y)), collection=C_STONE)
for i, (x, y) in enumerate(nodes_xy):
    bed = ground_z(x, y)
    top = DECK_TOP - 0.11
    h = top - bed + 0.12
    s = seat_stone(f'Bridge pier {i}', x, y, 0.62, 0.62, max(0.3, h), yaw=0.4 * i, z=bed - 0.12, seed=120 + i, bevel=0.02)
say('stones, lantern and bridge built')

# ------------------------------------------------------------------ trees: maple, pine, bamboo, fallen leaves
import numpy as np
_ICO = {}
def ico_template(detail):
    if detail not in _ICO:
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=detail, radius=1.0)
        idx = {v: i for i, v in enumerate(bm.verts)}
        _ICO[detail] = (np.array([tuple(v.co) for v in bm.verts]), np.array([[idx[v] for v in f.verts] for f in bm.faces])); bm.free()
    return _ICO[detail]

def leaf_mass(name, clusters, material, palette, blob_r, count_per_cluster, flatten=1.0, col=C_PLANT, seed=1, detail=2):
    """Many small tinted blobs packed into ellipsoid clusters: a stylised leaf mass. clusters: (cx,cy,cz,rx,ry,rz).
    Built with numpy so thousands of blobs take well under a second."""
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    tv, tf = ico_template(detail); nv, nf = len(tv), len(tf)
    vs, fs, cs = [], [], []; offset = 0
    for cx, cy, cz, rx, ry, rz in clusters:
        for _ in range(count_per_cluster):
            while True:
                p = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
                if 0.15 < p.length <= 1.0: break
            p.normalize(); p *= rng.uniform(0.55, 1.0) ** 0.5
            pos = np.array((cx + p.x * rx, cy + p.y * ry, cz + p.z * rz)); r = rng.uniform(*blob_r)
            rot = np.array(Euler((rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))).to_matrix())
            vs.append((tv * np.array((r, r, r * flatten))) @ rot.T + pos); fs.append(tf + offset); offset += nv
            tone = np.clip(0.5 + 0.5 * p.z + nrng.uniform(-0.28, 0.28, (nf, 1)) * 0.5 + rng.uniform(-0.25, 0.25), 0, 1)
            a, b = np.array(palette[0]), np.array(palette[1]); cs.append(a + (b - a) * tone)
    V, F, Cc = np.concatenate(vs), np.concatenate(fs), np.concatenate(cs)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel())
    me.polygons.add(len(F)); me.loops.add(len(F) * 3)
    me.loops.foreach_set('vertex_index', F.astype(np.int32).ravel())
    me.polygons.foreach_set('loop_start', np.arange(0, len(F) * 3, 3, dtype=np.int32))
    me.update(calc_edges=True); me.validate()
    me.polygons.foreach_set('use_smooth', np.ones(len(F), dtype=bool))
    layer = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    layer.data.foreach_set('color', np.repeat(np.concatenate([Cc, np.ones((len(F), 1))], axis=1), 3, axis=0).astype(np.float32).ravel())
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); return ob

def leaf_cards(name, clusters, material, palette, size, count_per_cluster, seed=1, col=C_PLANT, lobes=5):
    """Thousands of flat star-shaped (maple-like) leaves in ellipsoid clusters, mostly facing outward and up."""
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    ang = np.arange(lobes * 2) * math.pi / lobes
    ring = np.stack([np.cos(ang) * np.where(np.arange(lobes * 2) % 2 == 0, 1.0, 0.42), np.sin(ang) * np.where(np.arange(lobes * 2) % 2 == 0, 1.0, 0.42), np.zeros(lobes * 2)], axis=1)
    tv = np.vstack([[0, 0, 0], ring]); tf = np.array([[0, 1 + k, 1 + (k + 1) % (lobes * 2)] for k in range(lobes * 2)])
    vs, fs, cs = [], [], []; offset = 0
    for cx, cy, cz, rx, ry, rz in clusters:
        for _ in range(count_per_cluster):
            while True:
                p = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
                if 0.2 < p.length <= 1.0: break
            p.normalize(); p *= rng.uniform(0.5, 1.0) ** 0.4
            pos = np.array((cx + p.x * rx, cy + p.y * ry, cz + p.z * rz))
            normal = Vector((p.x, p.y, p.z * 0.8 + 0.25)) + Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)))
            normal.normalize(); q = Vector((0, 0, 1)).rotation_difference(normal) @ Euler((0, 0, rng.uniform(0, math.tau))).to_quaternion()
            rot = np.array(q.to_matrix()); r = rng.uniform(*size)
            vs.append((tv * r) @ rot.T + pos); fs.append(tf + offset); offset += len(tv)
            tone = float(np.clip(0.5 + 0.5 * p.z + rng.uniform(-0.32, 0.32), 0, 1)); a, b = np.array(palette[0]), np.array(palette[1])
            cs.append(np.repeat((a + (b - a) * tone)[None, :], len(tf), axis=0))
    V, F, Cc = np.concatenate(vs), np.concatenate(fs), np.concatenate(cs)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel())
    me.polygons.add(len(F)); me.loops.add(len(F) * 3)
    me.loops.foreach_set('vertex_index', F.astype(np.int32).ravel()); me.polygons.foreach_set('loop_start', np.arange(0, len(F) * 3, 3, dtype=np.int32))
    me.update(calc_edges=True); me.validate()
    layer = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    layer.data.foreach_set('color', np.repeat(np.concatenate([Cc, np.ones((len(F), 1))], axis=1), 3, axis=0).astype(np.float32).ravel())
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); return ob

def branch(name, points, radius0, radius1, material, col=C_PLANT):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(points) - 1)
    for i, (p, pt) in enumerate(zip(points, sp.points)):
        pt.co = (*p, 1.0); pt.radius = radius0 + (radius1 - radius0) * i / (len(points) - 1)
    ob = bpy.data.objects.new(name, cu); cu.materials.append(material); col.objects.link(ob); return ob

# maple (momiji) leaning over the pond's left bank
MX, MY = -6.7, 1.3; mz = ground_z(MX, MY)
trunk = [(MX, MY, mz - 0.1), (MX + 0.05, MY - 0.1, mz + 0.9), (MX + 0.55, MY - 0.25, mz + 1.8), (MX + 1.15, MY - 0.1, mz + 2.55), (MX + 1.7, MY + 0.15, mz + 3.2)]
branch('Maple trunk', trunk, 0.2, 0.06, trunk_bark)
for pts in ([(MX + 0.5, MY - 0.2, mz + 1.7), (MX + 1.5, MY - 0.65, mz + 2.1), (MX + 2.5, MY - 0.8, mz + 2.4), (MX + 3.4, MY - 0.7, mz + 2.45)],
            [(MX + 0.9, MY - 0.15, mz + 2.3), (MX + 0.4, MY + 0.7, mz + 2.9), (MX - 0.5, MY + 1.1, mz + 3.4)],
            [(MX + 1.2, MY - 0.05, mz + 2.6), (MX + 2.0, MY + 0.7, mz + 3.0), (MX + 3.0, MY + 1.1, mz + 3.25)]):
    branch('Maple branch', pts, 0.07, 0.025, trunk_bark)
maple_clusters = [(MX + 1.7, MY - 0.3, mz + 3.15, 1.7, 1.5, 0.55), (MX + 3.0, MY - 0.7, mz + 2.55, 1.2, 1.1, 0.42), (MX + 0.0, MY + 0.9, mz + 3.4, 1.3, 1.1, 0.5),
                  (MX + 2.9, MY + 1.0, mz + 3.2, 1.0, 0.9, 0.4), (MX + 0.9, MY - 0.9, mz + 2.3, 1.1, 0.9, 0.38)]
leaf_mass('Maple inner mass', [(a, b, c, d * 0.8, e * 0.8, f * 0.75) for a, b, c, d, e, f in maple_clusters], maple_core, ((0.07, 0.008, 0.006), (0.26, 0.03, 0.015)), (0.12, 0.2), 40, flatten=0.6, seed=5, detail=1)
leaf_cards('Maple leaves', maple_clusters, maple_leaves, ((0.30, 0.018, 0.012), (0.95, 0.20, 0.03)), (0.10, 0.17), 1500, seed=6)

# pine (matsu) pruned into cloud pads, at the hall's left corner
PX, PY = 7.6, 4.6; pz = ground_z(PX, PY)
trunk = [(PX, PY, pz - 0.1), (PX - 0.15, PY + 0.05, pz + 1.0), (PX + 0.35, PY - 0.05, pz + 2.0), (PX - 0.05, PY + 0.1, pz + 3.0), (PX + 0.25, PY, pz + 3.9)]
branch('Pine trunk', trunk, 0.24, 0.07, trunk_bark)
pads = []
for (dx, dy, dz, r) in ((1.0, -0.3, 1.5, 0.95), (-1.0, 0.3, 2.3, 0.85), (1.1, 0.3, 3.0, 0.9), (-0.7, -0.2, 3.5, 0.7), (0.3, 0.0, 4.1, 0.75)):
    branch('Pine limb', [(PX + dx * 0.1, PY + dy * 0.1, pz + dz - 0.35), (PX + dx * 0.55, PY + dy * 0.55, pz + dz - 0.12), (PX + dx, PY + dy, pz + dz)], 0.05, 0.025, trunk_bark)
    pads.append((PX + dx, PY + dy, pz + dz + 0.1, r, r * 0.9, 0.3))
leaf_mass('Pine pads', pads, pine_needles, ((0.02, 0.06, 0.025), (0.12, 0.24, 0.05)), (0.07, 0.12), 140, flatten=0.5, seed=9, detail=2)

# bamboo clumps at the back left
bm = bmesh.new(); bl = bmesh.new(); leaf_layer = bl.loops.layers.float_color.new('Col')
rng = random.Random(77)
def bamboo_clump(cx, cy, count, spread):
    for _ in range(count):
        bx, by = cx + rng.uniform(-spread, spread), cy + rng.uniform(-spread, spread); bz = ground_z(bx, by)
        height = rng.uniform(5.5, 7.5); lean = Vector((rng.uniform(-0.45, 0.35), rng.uniform(-0.25, 0.3)))
        r = rng.uniform(0.035, 0.05); n = int(height / 0.45); prev = Vector((bx, by, bz - 0.1))
        for k in range(1, n + 1):
            t = k / n; p = Vector((bx + lean.x * t * t * 1.4, by + lean.y * t * t * 1.4, bz + height * t))
            add_cylinder(bm, prev, p, r * (1.05 - 0.45 * t), 8); add_cylinder(bm, prev.lerp(p, 0.97), p, r * (1.2 - 0.45 * t), 8)
            if t > 0.45 and rng.random() < 0.85:
                for _ in range(rng.randint(3, 6)):                               # a few leaves hanging from this node
                    ang = rng.uniform(0, math.tau); ln = rng.uniform(0.28, 0.5)
                    o = p; tip = o + Vector((math.cos(ang) * ln, math.sin(ang) * ln, -ln * rng.uniform(0.2, 0.6)))
                    side = Vector((-math.sin(ang), math.cos(ang), 0)) * 0.04
                    vs = [bl.verts.new(o), bl.verts.new(o + (tip - o) * 0.5 + side), bl.verts.new(tip), bl.verts.new(o + (tip - o) * 0.5 - side)]
                    f = bl.faces.new(vs)
                    tone = rng.uniform(0, 1); c = (0.06 + 0.10 * tone, 0.2 + 0.18 * tone, 0.025 + 0.02 * tone, 1.0)
                    for lp in f.loops: lp[leaf_layer] = c
            prev = p
bamboo_clump(-8.8, 8.2, 9, 0.9); bamboo_clump(-9.4, 5.2, 6, 0.7); bamboo_clump(-6.6, 9.4, 4, 0.5)
object_from_bmesh('Bamboo stalks', bm, bamboo_green, C_PLANT)
bleaf = object_from_bmesh('Bamboo leaves', bl, leaf_material('Bamboo leaf colour', rough=0.5, translucency=0.5, emission=0.03), C_PLANT)
say('trees and bamboo built')


# lily pads and a few lotus blossoms on the pond
pad_material = principled('Lily pad', (0.05, 0.2, 0.04), rough=0.45)
blossom_material = principled('Lotus blossom', (0.9, 0.45, 0.55), rough=0.5, Emission_Color=(0.9, 0.3, 0.4, 1), Emission_Strength=0.15)
rngl = random.Random(3); bm = bmesh.new(); bb = bmesh.new(); placed = []
for _ in range(400):
    x = POND_C[0] + rngl.uniform(-3.3, 3.3); y = POND_C[1] + rngl.uniform(-2.5, 2.5)
    if pond_radius(x, y) > 0.82 or any(math.hypot(x - a, y - b) < 0.7 for a, b in placed): continue
    near_bridge = any(math.hypot(x - bx, y - by) < 0.8 for bx, by in nodes_xy) or any(
        abs((bx - ax) * (ay - y) - (ax - x) * (by - ay)) / max(1e-6, math.hypot(bx - ax, by - ay)) < 0.8 and min(ax, bx) - 0.5 < x < max(ax, bx) + 0.5
        for (ax, ay), (bx, by) in zip(nodes_xy, nodes_xy[1:]))
    if near_bridge: continue
    placed.append((x, y)); r = rngl.uniform(0.11, 0.2); notch = rngl.uniform(0, math.tau)
    ctr = bm.verts.new((x, y, WATER_Z + 0.004)); ring = []
    for k in range(18):
        a = notch + 0.35 + k * (math.tau - 0.7) / 17; ring.append(bm.verts.new((x + math.cos(a) * r, y + math.sin(a) * r, WATER_Z + 0.004)))
    for k in range(17): bm.faces.new((ctr, ring[k], ring[k + 1]))
    if rngl.random() < 0.18:
        for k in range(6):
            a = k * math.tau / 6; tip = bb.verts.new((x + 0.02 + math.cos(a) * 0.06, y + math.sin(a) * 0.06, WATER_Z + 0.1))
            b0 = bb.verts.new((x + 0.02 + math.cos(a + 0.5) * 0.025, y + math.sin(a + 0.5) * 0.025, WATER_Z + 0.01)); b1 = bb.verts.new((x + 0.02 + math.cos(a - 0.5) * 0.025, y + math.sin(a - 0.5) * 0.025, WATER_Z + 0.01))
            bb.faces.new((b0, tip, b1))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
pads_obj = object_from_bmesh('Lily pads', bm, pad_material, C_PLANT); blossoms_obj = object_from_bmesh('Lotus blossoms', bb, blossom_material, C_PLANT)
blossoms_obj.data.materials[0].use_backface_culling = False

# fallen maple leaves on the gravel, path and moss
bm = bmesh.new(); layer = bm.loops.layers.float_color.new('Col')
for _ in range(190):
    x = RNG.choice([RNG.uniform(1.0, 8.5), RNG.uniform(-8.0, -1.0), RNG.uniform(-2.0, 4.0)]); y = RNG.choice([RNG.uniform(-5.5, 1.5), RNG.uniform(-3.5, 2.5)])
    if pond_radius(x, y) < 1.05 or (HALL_X0 - 1 < x < HALL_X1 + 1 and y > 4.0): continue
    z = ground_z(x, y) + 0.012; s = RNG.uniform(0.045, 0.08); a = RNG.uniform(0, math.tau)
    vs = [bm.verts.new((x + math.cos(a + k * math.tau / 5) * s * (1.0 if k % 2 == 0 else 0.55), y + math.sin(a + k * math.tau / 5) * s * (1.0 if k % 2 == 0 else 0.55), z)) for k in range(5)]
    f = bm.faces.new(vs); tone = RNG.uniform(0, 1); c = (0.5 + 0.4 * tone, 0.06 + 0.22 * tone, 0.03, 1.0)
    for lp in f.loops: lp[layer] = c
object_from_bmesh('Fallen leaves', bm, fallen_leaf, C_PLANT)

# distant hills: three hazy, unlit ridgelines (nearer = darker), so the sky never ends in an empty horizon
def ridge(name, radius, cy, base, wobble, color, seed, half_deg=95):
    rr = random.Random(seed); n = 160; bm = bmesh.new(); top = []; bot = []
    ph = [rr.uniform(0, 6.3) for _ in range(5)]
    for i in range(n + 1):
        ang = math.radians(-half_deg + 2 * half_deg * i / n); x = math.sin(ang) * radius; y = cy + math.cos(ang) * radius
        h = base + wobble * (0.5 * math.sin(ang * 5 + ph[0]) + 0.3 * math.sin(ang * 11 + ph[1]) + 0.15 * math.sin(ang * 23 + ph[2]) + 0.08 * math.sin(ang * 47 + ph[3]))
        top.append(bm.verts.new((x, y, h))); bot.append(bm.verts.new((x, y, -4)))
    for i in range(n): bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    ob = object_from_bmesh(name, bm, emission_material(name + ' haze', color, 1.0), C_WORLD)
    ob.visible_shadow = False            # a painted backdrop: it must not block the sun
    return ob
ridge('Hills, far', 120, 10, 24, 9, (0.20, 0.13, 0.115), 1)
ridge('Hills, middle', 80, 8, 17, 7, (0.085, 0.062, 0.062), 2)
ridge('Hills, near', 56, 6, 9, 4, (0.022, 0.03, 0.03), 3)
bm = bmesh.new(); add_box(bm, (0, 30, -0.6), (400, 220, 0.2)); plain = object_from_bmesh('Dark plain', bm, hill_material, C_WORLD); plain.visible_shadow = False

# ------------------------------------------------------------------ light: golden hour sky and sun, warm lights in the lantern and hall
world = bpy.data.worlds.new('Golden hour'); scene.world = world; world.use_nodes = True
wt = world.node_tree; wt.nodes.clear()
sky = wt.nodes.new('ShaderNodeTexSky')
for kind in ('MULTIPLE_SCATTERING', 'NISHITA'):
    try: sky.sky_type = kind; break
    except Exception: pass
sky.sun_disc = False; sky.sun_elevation = math.radians(9.0); sky.sun_rotation = math.radians(270.0)
sky.altitude = 40.0; sky.air_density = 1.0; sky.aerosol_density = 0.9; sky.ozone_density = 1.0
bg = wt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = option('--sky', 0.3)
out = wt.nodes.new('ShaderNodeOutputWorld')
tcoord = wt.nodes.new('ShaderNodeTexCoord'); sep = wt.nodes.new('ShaderNodeSeparateXYZ'); wt.links.new(tcoord.outputs['Generated'], sep.inputs['Vector'])
band = wt.nodes.new('ShaderNodeMapRange'); band.inputs['From Min'].default_value = 0.5; band.inputs['From Max'].default_value = 0.615
band.inputs['To Min'].default_value = 1.0; band.inputs['To Max'].default_value = 0.0; band.clamp = True
wt.links.new(sep.outputs['Z'], band.inputs['Value'])
warm = wt.nodes.new('ShaderNodeRGB'); warm.outputs[0].default_value = (3.0, 1.15, 0.38, 1)
mixw = wt.nodes.new('ShaderNodeMix'); mixw.data_type = 'RGBA'; mixw.blend_type = 'MIX'
wt.links.new(band.outputs['Result'], mixw.inputs['Factor']); wt.links.new(sky.outputs['Color'], mixw.inputs[6]); wt.links.new(warm.outputs[0], mixw.inputs[7])
band2 = wt.nodes.new('ShaderNodeMapRange'); band2.inputs['From Min'].default_value = 0.58; band2.inputs['From Max'].default_value = 0.74
band2.inputs['To Min'].default_value = 0.0; band2.inputs['To Max'].default_value = 0.85; band2.clamp = True; wt.links.new(sep.outputs['Z'], band2.inputs['Value'])
dusk = wt.nodes.new('ShaderNodeRGB'); dusk.outputs[0].default_value = (0.16, 0.24, 0.52, 1)
mix2 = wt.nodes.new('ShaderNodeMix'); mix2.data_type = 'RGBA'; mix2.blend_type = 'MIX'
wt.links.new(band2.outputs['Result'], mix2.inputs['Factor']); wt.links.new(mixw.outputs[2], mix2.inputs[6]); wt.links.new(dusk.outputs[0], mix2.inputs[7])
wt.links.new(mix2.outputs[2], bg.inputs['Color']); wt.links.new(bg.outputs['Background'], out.inputs['Surface'])

sun = bpy.data.lights.new('Golden hour sun', 'SUN'); sun.energy = option('--sun', 5.5); sun.color = (1.0, 0.52, 0.2); sun.angle = math.radians(1.2)
sun_obj = bpy.data.objects.new('Golden hour sun', sun); C_LIGHT.objects.link(sun_obj)
SUN_TRAVEL = Vector((0.93, 0.24, -0.22))          # light travels to the right and a little away: sun low on the left
sun_obj.rotation_euler = SUN_TRAVEL.normalized().to_track_quat('-Z', 'Y').to_euler()
sun.energy = option('--sun', 8.0)

def point_light(name, loc, watts, color, radius=0.1):
    l = bpy.data.lights.new(name, 'POINT'); l.energy = watts; l.color = color; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); o.location = loc; C_LIGHT.objects.link(o); return o
point_light('Lantern light', (LX, LY, fire_z), 120, (1.0, 0.58, 0.25), 0.06)
for i, bx in enumerate((-3.4, -0.8, 1.7, 4.2)):
    a = bpy.data.lights.new(f'Hall glow {i}', 'AREA'); a.shape = 'RECTANGLE'; a.size = 1.9; a.size_y = 1.5; a.energy = 90; a.color = (1.0, 0.62, 0.3)
    o = bpy.data.objects.new(f'Hall glow {i}', a); o.location = (bx, HALL_Y0 - 0.7, 1.55); o.rotation_euler = (math.radians(90) + 0.0, 0, 0)
    o.rotation_euler = (-math.radians(90), 0, 0); C_LIGHT.objects.link(o)

# weathered timber: the add-on's plank tones come out fresh orange-brown; pull them toward silvery grey-brown
for m in bpy.data.materials:
    if m.name.startswith('Astra / planks tone') and m.use_nodes:
        b = m.node_tree.nodes.get('Principled BSDF')
        if b and not b.inputs['Base Color'].is_linked:
            r, g, bl, _ = b.inputs['Base Color'].default_value
            b.inputs['Base Color'].default_value = (r * 0.62 + 0.012, g * 0.64 + 0.014, bl * 0.72 + 0.018, 1)
            b.inputs['Roughness'].default_value = 0.78

# the add-on's pebbles come out very pale in raking sun: tone them down and warm them a little
for m in bpy.data.materials:
    if m.name.startswith('Astra / pebbles tone') and m.use_nodes:
        b = m.node_tree.nodes.get('Principled BSDF')
        if b and not b.inputs['Base Color'].is_linked:
            r, g, bl, _ = b.inputs['Base Color'].default_value
            b.inputs['Base Color'].default_value = (r * 0.62, g * 0.58, bl * 0.52, 1)

# a big soft cool fill from the camera's side, so the shaded roof and stone faces keep their shape
fill = bpy.data.lights.new('Cool sky fill', 'AREA'); fill.shape = 'DISK'; fill.size = 14.0; fill.energy = option('--fill', 3500.0); fill.color = (0.72, 0.82, 1.0)
fill_obj = bpy.data.objects.new('Cool sky fill', fill); fill_obj.location = (-13.0, -11.0, 9.0); C_LIGHT.objects.link(fill_obj)
fill_obj.rotation_euler = (Vector((0.3, 3.0, 1.6)) - fill_obj.location).to_track_quat('-Z', 'Y').to_euler()

HAZE = option('--haze', 0.0)
if HAZE > 0:                                  # a thin golden haze so the low sun shows as soft beams through the maple
    vol = wt.nodes.new('ShaderNodeVolumeScatter'); vol.inputs['Density'].default_value = HAZE; vol.inputs['Anisotropy'].default_value = 0.55
    vol.inputs['Color'].default_value = (1.0, 0.86, 0.7, 1)
    wt.links.new(vol.outputs['Volume'], out.inputs['Volume']); scene.cycles.volume_bounces = 0; scene.cycles.volume_step_rate = 2.0

# ------------------------------------------------------------------ camera, render settings
cam_data = bpy.data.cameras.new('Camera'); cam_data.lens = 26; cam_data.sensor_width = 36
cam = bpy.data.objects.new('Camera', cam_data); scene.collection.objects.link(cam)
cam.location = (-5.2, -5.6, 3.0); target = Vector((1.0, 3.9, 1.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
focus = bpy.data.objects.new('Focus', None); focus.location = (-2.5, 0.6, 0.4); scene.collection.objects.link(focus)
cam_data.dof.use_dof = True; cam_data.dof.focus_object = focus; cam_data.dof.aperture_fstop = 3.2
DEBUG_CAM = [float(v) for v in ARGS[ARGS.index('--debugcam') + 1].split(',')] if '--debugcam' in ARGS else None
if DEBUG_CAM:        # a close look at one spot: x,y,z of the camera then x,y,z of the target
    cam.location = DEBUG_CAM[:3]; cam.rotation_euler = (Vector(DEBUG_CAM[3:]) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 40; cam_data.dof.use_dof = False
for prefix in (ARGS[ARGS.index('--hide') + 1].split(',') if '--hide' in ARGS else []):    # debugging: hide objects by name prefix
    for ob in bpy.data.objects:
        if ob.name.startswith(prefix): ob.hide_render = True
scene.camera = cam
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = 0.012
scene.cycles.use_denoising = True
try: scene.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
scene.cycles.max_bounces = 6; scene.cycles.diffuse_bounces = 3; scene.cycles.glossy_bounces = 3; scene.cycles.transmission_bounces = 4; scene.cycles.volume_bounces = 0
scene.cycles.sample_clamp_indirect = 8.0
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_depth = '8'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = option('--exposure', 0.5)
try: scene.view_settings.look = 'AgX - Punchy'
except Exception: pass

# a fingerprint of everything that was built (evaluated geometry included), so two runs can be compared exactly
import hashlib, json as _json
def scene_fingerprint():
    dg = bpy.context.evaluated_depsgraph_get(); parts = []; total_v = total_f = 0
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if ob.type != 'MESH': continue
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        co = np.array([tuple(v.co) for v in me.vertices], dtype=np.float64)
        m = np.array(ob.matrix_world, dtype=np.float64); world = (co @ m[:3, :3].T + m[:3, 3]) if len(co) else co
        digest = hashlib.sha256(np.round(world, 5).tobytes()).hexdigest()[:16]
        parts.append((ob.name, len(me.vertices), len(me.polygons), digest, [mt.name if mt else None for mt in ob.data.materials]))
        total_v += len(me.vertices); total_f += len(me.polygons); ev.to_mesh_clear()
    return {'objects': len(parts), 'vertices': total_v, 'faces': total_f, 'whole': hashlib.sha256(_json.dumps(parts, sort_keys=True).encode()).hexdigest()[:24], 'parts': parts}
FP = scene_fingerprint()
with open(OUT_PREFIX + '.fingerprint.json', 'w') as f: _json.dump(FP, f, indent=1)
say(f"fingerprint: {FP['objects']} meshes, {FP['vertices']} vertices, {FP['faces']} faces, whole={FP['whole']}")

bpy.ops.wm.save_as_mainfile(filepath=OUT_PREFIX + '.blend', compress=True)
say('scene saved; rendering')
scene.render.filepath = OUT_PREFIX + '.png'
bpy.ops.render.render(write_still=True)
say(f'rendered {WIDTH}x{HEIGHT} at {SAMPLES} samples -> {OUT_PREFIX}.png')
