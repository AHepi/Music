# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The SMALL SEPARATE PIECES of rubbish (Blender code; runs only inside Blender): a handful of little 3D objects (cinder and clinker lumps, coal lumps, ash heaps, torn paper,
# sodden paper, dead leaves, straw, a broken pot, a stick, 1 to 20 cm, each in a plain colour, NOTHING printed on any of them, nothing modern) and a Geometry Nodes recipe that scatters
# them over the ground where the rubbish mask (rubbish_layer.py, the same mask nodes and the same dials as the painted muck layer) says there is rubbish.
# Why real pieces as well as paint: a real lump catches the light and throws a tiny shadow, so it reads as litter even where the painted layer is faint. They are for the plate only
# (they are not in the glb).
# SIX KINDS, each scattered separately with its own density (a "Poisson disk" scatter: no two pieces of one kind nearer than a set distance):
#     lumps (cinders, clinker, a sherd, a stick) where the muck is;  coal (black, shiny) round the sacks, the slack heap, the drum and the doorsteps;  ash heaps at the doorsteps and the drum;
#     paper (torn and sodden scraps) along walls and gutter and in corners;  leaves at the foot of rain pipes and in corners;  straw bundles at the kerb foot and the wall foot.
# THE DIALS (on top of the muck layer's dials, which also act here: Rubbish Amount, the four places, Seed, Patchiness, Dust And Cinders, Ash, Straw, Paper, Leaves):
#     Pieces Density  0..2   how many pieces (1 = normal, 0 = none, 2 = double). Default 1.
#     Pieces Distance m      pieces are laid only up to this far along the street from the street's start (y), to keep the picture fast: 45 m by default.
#     Piece Size      0.5..2 the size of every piece (1 = as built).
#     Pieces Wet      0..1   how wet the pieces look (paper dark and limp, coal shiny): set from the street's wetness by apply_rubbish_to_set.set_state.
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rubbish_layer as rl  # noqa: E402

COLLECTIONS = {}
PIECE_DIALS = [
    ('pieces_density', 'Pieces Density', 1.0, 0.0, 2.0, 'How many separate pieces (0 = none)'),
    ('pieces_distance', 'Pieces Distance', 45.0, 5.0, 90.0, 'Pieces only up to this many metres along the street'),
    ('piece_size', 'Piece Size', 1.0, 0.5, 2.0, 'Size of every piece'),
    ('pieces_gather', 'Pieces Gather', 1.0, 0.0, 1.0, 'How much the pieces gather at the kerb and the foot of the walls (0 = as in round 1, 1 = about twice as many there, a fifth as many elsewhere)'),
    ('piece_near_cap', 'Piece Near Cap', 0.7, 0.2, 3.0, 'The biggest scale a piece can have near the camera (full from the camera out to 5 m, no cap beyond 12 m)'),
]
PIECE_DEFAULTS = {key: default for key, _, default, _, _, _ in PIECE_DIALS}
PIECE_SOCKETS = {key: name for key, name, _, _, _, _ in PIECE_DIALS}
# (collection, density per square metre where the mask is 1, nearest two pieces may be, smallest and biggest scale)
CLASSES = dict(
    lumps=dict(density=70.0, distance=0.05, scale=(0.7, 1.5)),
    coal=dict(density=45.0, distance=0.05, scale=(0.7, 1.4)),
    ash=dict(density=6.0, distance=0.12, scale=(0.7, 1.4)),
    paper=dict(density=16.0, distance=0.09, scale=(0.7, 1.4)),
    leaves=dict(density=16.0, distance=0.08, scale=(0.8, 1.3)),
    straw=dict(density=18.0, distance=0.10, scale=(0.8, 1.3)),
    specks=dict(density=420.0, distance=0.014, scale=(0.7, 1.5)),      # round 2 plate: many tiny dust specks
    clumps=dict(density=7.0, distance=0.10, scale=(0.8, 1.3)),         # round 2 plate: a few wet-paper clumps, mostly in the gutters
)
WET_NODES = []
VIEW_POINT_NAME = 'rubbish_view_point'
NEAR_FULL, NEAR_END = 5.0, 12.0       # metres from the camera: the near-camera size cap is full out to 5 m and gone at 12 m


def view_point():
    """The empty that stands where the camera is (made once; set_view_point moves it)."""
    obj = bpy.data.objects.get(VIEW_POINT_NAME)
    if obj is None:
        obj = bpy.data.objects.new(VIEW_POINT_NAME, None)
        obj.empty_display_type = 'PLAIN_AXES'
        bpy.context.scene.collection.objects.link(obj)
        obj.location = (-1.0, 1.2, 1.7)
    return obj


def set_view_point(location):
    """Tells the scatter where the camera is (for the size cap near it). Call before drawing each picture."""
    view_point().location = tuple(location)


# ------------------------------------------------------------------------------------------------------------------------------- the pieces
def piece_material(name, dry, wet, rough_dry, rough_wet, metallic=0.0, specular=0.5, grain=0.35, grain_scale=400.0, bump=0.25):
    """A plain material that goes from its dry colour to its wet colour with the value node WET (set for all pieces by set_wetness).
    Round 2 plate: a little grain (colour speckle and a tiny bump from a noise picture in the piece's own coordinates), so that a lump is not one smooth flat colour with one sharp highlight."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    principled = tree.nodes['Principled BSDF']
    wet_node = tree.nodes.new('ShaderNodeValue')
    wet_node.name, wet_node.label = 'WET', 'wet look 0..1'
    wet_node.outputs[0].default_value = 0.0
    mix_colour = tree.nodes.new('ShaderNodeMix')
    mix_colour.data_type, mix_colour.blend_type = 'RGBA', 'MIX'
    mix_colour.inputs[6].default_value = (*dry, 1.0)
    mix_colour.inputs[7].default_value = (*wet, 1.0)
    tree.links.new(wet_node.outputs[0], mix_colour.inputs[0])
    colour_out = mix_colour.outputs[2]
    if grain > 0.0:
        texcoord = tree.nodes.new('ShaderNodeTexCoord')
        noise = tree.nodes.new('ShaderNodeTexNoise')
        noise.noise_dimensions = '3D'
        noise.inputs['Scale'].default_value = grain_scale
        noise.inputs['Detail'].default_value = 3.0
        noise.inputs['Roughness'].default_value = 0.6
        tree.links.new(texcoord.outputs['Object'], noise.inputs['Vector'])
        speckle = tree.nodes.new('ShaderNodeMapRange')
        speckle.inputs['From Min'].default_value, speckle.inputs['From Max'].default_value = 0.3, 0.7
        speckle.inputs['To Min'].default_value, speckle.inputs['To Max'].default_value = 1.0 - grain, 1.0 + grain
        tree.links.new(noise.outputs['Fac'], speckle.inputs['Value'])
        multiply = tree.nodes.new('ShaderNodeMix')
        multiply.data_type, multiply.blend_type = 'RGBA', 'MULTIPLY'
        multiply.inputs[0].default_value = 1.0
        tree.links.new(colour_out, multiply.inputs[6])
        tree.links.new(speckle.outputs['Result'], multiply.inputs[7])
        colour_out = multiply.outputs[2]
        if bump > 0.0:
            bump_node = tree.nodes.new('ShaderNodeBump')
            bump_node.inputs['Strength'].default_value = bump
            bump_node.inputs['Distance'].default_value = 0.002
            tree.links.new(noise.outputs['Fac'], bump_node.inputs['Height'])
            tree.links.new(bump_node.outputs['Normal'], principled.inputs['Normal'])
    tree.links.new(colour_out, principled.inputs['Base Color'])
    mix_rough = tree.nodes.new('ShaderNodeMix')
    mix_rough.data_type = 'FLOAT'
    mix_rough.inputs[2].default_value, mix_rough.inputs[3].default_value = rough_dry, rough_wet
    tree.links.new(wet_node.outputs[0], mix_rough.inputs[0])
    tree.links.new(mix_rough.outputs[0], principled.inputs['Roughness'])
    principled.inputs['Metallic'].default_value = metallic
    principled.inputs['Specular IOR Level'].default_value = specular
    WET_NODES.append(wet_node)
    return material


def _finish(collection, name, bm, material, smooth=False, weight=1):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = smooth
    mesh.materials.append(material)
    for k in range(weight):                       # weight: more copies of a piece make it more likely to be picked (the copies share the mesh)
        obj = bpy.data.objects.new(name if k == 0 else f'{name}_{k}', mesh)
        collection.objects.link(obj)


def _lump(collection, name, material, size, flat, seed, subdiv=3, weight=1, sharp=0.35, ridge=0.7, freq=1.5, stretch=1.0, underside=0.5, crease_angle=24.0, smooth=True):
    """A noise-pushed lump (round 2 plate: the old ones were 80-face balls with every corner pulled out by a random number, and read as faceted gems or dice).
    A sphere of 1,280 faces is pushed in and out along its own direction by smooth 3D noise (two sizes of bump; ridge = how much of it is 'creased' noise, which gives the angular chipped look
    of coal and cinder without sharp facets), stretched a little along one way, squashed flat (flat = height as a share of width, 0.4 to 0.7 for cinders and coal), its underside flattened, and
    shaded smooth. size = the radius in metres before the push."""
    r = random.Random(seed)
    off = Vector((r.uniform(-40, 40), r.uniform(-40, 40), r.uniform(-40, 40)))
    sx, sy = stretch * r.uniform(0.85, 1.3), r.uniform(0.8, 1.15)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        p = v.co.normalized()
        n1 = mnoise.noise(p * freq + off)
        n2 = mnoise.noise(p * freq * 2.6 + off * 1.9)
        creased = 0.5 - abs(n1) * 1.4                    # -0.9 .. 0.5: deep creases where the noise crosses zero
        n3 = mnoise.noise(p * freq * 6.0 + off * 0.7)                  # a third, fine bump
        k = 1.0 + sharp * (ridge * creased + (1.0 - ridge) * n1) + 0.5 * sharp * n2 + 0.22 * sharp * n3
        k = max(k, 0.3)
        v.co = Vector((p.x * k * sx * size, p.y * k * sy * size, p.z * k * size * flat))
    for e in bm.edges:                                   # keep the creases crisp: an edge where two faces meet at more than about 30 degrees stays sharp (the rest is smooth shaded)
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(crease_angle):
            e.smooth = False
    low = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        if v.co.z < low * underside:                      # flat underside: the lump sits on the ground instead of balancing on a point
            v.co.z = low * underside
        v.co.z -= low * underside - 0.0008
    _finish(collection, name, bm, material, smooth=smooth, weight=weight)


def _crumple(collection, name, material, size, flat, seed, weight=1):
    """A sodden paper wad: a flattened blob with deep creases, smooth shaded. size = radius in metres."""
    _lump(collection, name, material, size, flat, seed, subdiv=3, weight=weight, sharp=0.55, ridge=0.9, freq=2.2, stretch=1.2, underside=0.4)


def _straw_bundle(collection, name, material, seed):
    """Two or three thin curved wet strands, 3 to 7 cm long, 1 to 1.5 mm wide, lying on the ground (flat ribbons that bend as they go, ends touching down)."""
    r = random.Random(seed)
    bm = bmesh.new()
    for k in range(r.randint(2, 3)):
        length, width = r.uniform(0.035, 0.07), r.uniform(0.0010, 0.0016)
        turn = r.uniform(-1.6, 1.6)                        # how far the strand bends in all, radians
        angle = r.uniform(0.0, math.tau)
        x, y = r.uniform(-0.015, 0.015), r.uniform(-0.012, 0.012)
        segments = 6
        rows = []
        for i in range(segments + 1):
            lift = 0.0006 + 0.0005 * k + 0.0009 * math.sin(math.pi * i / segments)       # touches down at both ends, a hair up in the middle
            nx, ny = -math.sin(angle) * width * 0.5, math.cos(angle) * width * 0.5
            rows.append((bm.verts.new((x + nx, y + ny, lift)), bm.verts.new((x - nx, y - ny, lift))))
            angle += turn / segments
            x += math.cos(angle) * length / segments
            y += math.sin(angle) * length / segments
        for (a0, b0), (a1, b1) in zip(rows[:-1], rows[1:]):
            bm.faces.new((a0, b0, b1, a1))
    _finish(collection, name, bm, material, smooth=False)


def build_pieces():
    """Makes the collections (not linked to the scene: only the scatter uses them). Returns the dict name -> collection."""
    if COLLECTIONS:
        return COLLECTIONS
    random.seed(7)
    cinder_m = piece_material('piece_cinder', (0.045, 0.042, 0.040), (0.016, 0.015, 0.015), 0.92, 0.72, grain=0.45, bump=0.45)
    clinker_m = piece_material('piece_clinker', (0.105, 0.085, 0.07), (0.040, 0.031, 0.025), 0.88, 0.55, grain=0.45, bump=0.45)
    coal_m = piece_material('piece_coal', (0.014, 0.014, 0.016), (0.010, 0.010, 0.012), 0.65, 0.5, specular=0.3, grain=0.5, bump=0.5)
    ash_m = piece_material('piece_ash', (0.23, 0.22, 0.21), (0.05, 0.048, 0.048), 0.97, 0.6)
    paper_m = piece_material('piece_paper', (0.33, 0.30, 0.25), (0.062, 0.054, 0.044), 0.85, 0.6, specular=0.25, grain=0.25, bump=0.15)
    sodden_m = piece_material('piece_sodden_paper', (0.16, 0.14, 0.115), (0.050, 0.043, 0.035), 0.8, 0.55, specular=0.25, grain=0.25, bump=0.15)
    clump_m = piece_material('piece_wet_clump', (0.13, 0.115, 0.095), (0.034, 0.030, 0.025), 0.85, 0.5, specular=0.3, grain=0.4, bump=0.4)
    leaf_brown_m = piece_material('piece_leaf_brown', (0.11, 0.055, 0.020), (0.040, 0.020, 0.008), 0.8, 0.4, grain=0.2, bump=0.1)
    leaf_orange_m = piece_material('piece_leaf_orange', (0.18, 0.085, 0.024), (0.065, 0.032, 0.010), 0.8, 0.4, grain=0.2, bump=0.1)
    straw_m = piece_material('piece_straw', (0.28, 0.20, 0.085), (0.085, 0.058, 0.024), 0.8, 0.5, grain=0.2, bump=0.0)
    china_m = piece_material('piece_china', (0.42, 0.42, 0.40), (0.20, 0.20, 0.19), 0.45, 0.30, specular=0.4, grain=0.3, bump=0.1)
    wood_m = piece_material('piece_stick', (0.10, 0.065, 0.035), (0.035, 0.022, 0.012), 0.9, 0.5, grain=0.3)
    speck_m = piece_material('piece_speck', (0.04, 0.037, 0.035), (0.013, 0.012, 0.012), 0.9, 0.5, grain=0.0, bump=0.0)
    speck_pale_m = piece_material('piece_speck_pale', (0.17, 0.16, 0.15), (0.04, 0.038, 0.038), 0.95, 0.6, grain=0.0, bump=0.0)

    def collection(name):
        c = bpy.data.collections.new('rubbish_' + name)
        COLLECTIONS[name] = c
        return c

    def scrap(w, d, bend, seed, nx=7, ny=6):
        """A scrap of paper. Round 2 plate: limp, not stiff: it hugs the ground (about 1.5 mm up in the middle), its edge curls and wrinkles a little, and its outline is ragged."""
        def build(bm):
            bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
            r = random.Random(seed)
            for v in bm.verts:
                edge = (abs(v.co.x) > 0.42) or (abs(v.co.y) > 0.42)
                v.co.x = v.co.x * w * (1 + r.uniform(-0.16, 0.16) * edge)
                v.co.y = v.co.y * d * (1 + r.uniform(-0.16, 0.16) * edge)
                wrinkle = mnoise.noise(Vector((v.co.x * 70 + seed, v.co.y * 70, seed * 3.1)))
                v.co.z = 0.0010 + bend * (wrinkle * 0.6 + r.uniform(-0.25, 0.25)) * (0.5 + 1.0 * edge)
        return build

    def leaf(length, width, seed):
        def build(bm):
            bmesh.ops.create_grid(bm, x_segments=8, y_segments=3, size=0.5)
            r = random.Random(seed)
            for v in bm.verts:
                t = v.co.x + 0.5                       # 0..1 along the leaf
                v.co.y *= width * math.sin(math.pi * min(1, max(0, t))) * 2.0 + 0.0008
                v.co.x *= length
                v.co.z = 0.0015 + 0.007 * (v.co.y / max(width, 1e-4)) ** 2 + 0.004 * t + r.uniform(0, 0.0012)
        return build

    # lumps: cinders, clinker (noise-pushed, flat), a sherd, a twig
    c = collection('lumps')
    _lump(c, 'cinder_a', cinder_m, 0.010, 0.55, 1, weight=5, sharp=0.45, subdiv=3, smooth=False)
    _lump(c, 'cinder_b', cinder_m, 0.016, 0.50, 2, weight=4, sharp=0.5, subdiv=3, smooth=False)
    _lump(c, 'cinder_c', cinder_m, 0.024, 0.45, 8, weight=2, sharp=0.45, subdiv=3, smooth=False)
    _lump(c, 'cinder_d', cinder_m, 0.013, 0.60, 15, weight=3, ridge=0.5, sharp=0.45, subdiv=3, smooth=False)
    _lump(c, 'clinker_a', clinker_m, 0.015, 0.50, 3, weight=2, ridge=0.5, sharp=0.5)
    _lump(c, 'clinker_b', clinker_m, 0.022, 0.45, 9, weight=1, ridge=0.5, sharp=0.55)
    bm = bmesh.new()                                        # a china sherd: a thin, curved, irregular piece (a shallow dished disc with a ragged edge), grubby off-white
    bmesh.ops.create_grid(bm, x_segments=5, y_segments=5, size=0.5)
    rs = random.Random(5)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        rad = math.hypot(v.co.x, v.co.y)
        shape = 0.016 * (1 + 0.35 * math.sin(3 * a + 1.0) + 0.2 * math.sin(5 * a)) * (1 + rs.uniform(-0.08, 0.08))
        v.co.x, v.co.y = math.cos(a) * rad * 2 * shape, math.sin(a) * rad * 2 * shape * 0.75
        v.co.z = 0.0015 + 0.004 * (rad * 2) ** 2
    _finish(c, 'china_sherd', bm, china_m, smooth=False, weight=1)
    bm = bmesh.new()                                        # a short bent twig
    pts = []
    for i in range(7):
        t = i / 6.0
        pts.append((t * 0.075 - 0.0375, 0.012 * math.sin(t * 2.6), 0.003 + 0.002 * math.sin(math.pi * t)))
    rings = []
    for i, (x, y, z) in enumerate(pts):
        rad = 0.0033 - 0.0012 * i / 6.0
        rings.append([bm.verts.new((x, y + rad * math.cos(a), z + rad * 0.8 * math.sin(a))) for a in (0, 2.1, 4.2)])
    for ring_a, ring_b in zip(rings[:-1], rings[1:]):
        for j in range(3):
            bm.faces.new((ring_a[j], ring_a[(j + 1) % 3], ring_b[(j + 1) % 3], ring_b[j]))
    _finish(c, 'stick', bm, wood_m, smooth=False, weight=1)
    # coal: shiny but chunky and irregular, flat lumps (not gems)
    c = collection('coal')
    _lump(c, 'coal_a', coal_m, 0.015, 0.60, 4, weight=3, sharp=0.6, ridge=0.85, subdiv=3, smooth=False)
    _lump(c, 'coal_b', coal_m, 0.026, 0.55, 5, weight=2, sharp=0.6, ridge=0.85, subdiv=3, smooth=False)
    _lump(c, 'coal_c', coal_m, 0.010, 0.65, 12, weight=3, sharp=0.6, ridge=0.85, subdiv=3, smooth=False)
    _lump(c, 'coal_d', coal_m, 0.018, 0.50, 17, weight=2, sharp=0.55, ridge=0.9, stretch=1.3, subdiv=3, smooth=False)
    # ash heaps: low flat mounds
    c = collection('ash')
    _lump(c, 'ash_heap_a', ash_m, 0.030, 0.35, 6, subdiv=3, weight=2, sharp=0.5, ridge=0.1, underside=0.3)
    _lump(c, 'ash_heap_b', ash_m, 0.042, 0.28, 10, subdiv=3, weight=1, sharp=0.5, ridge=0.1, underside=0.3)
    _lump(c, 'ash_heap_c', ash_m, 0.024, 0.40, 14, subdiv=3, weight=2, sharp=0.45, ridge=0.1, underside=0.3)
    # paper: torn scraps and sodden ones (limp: nearly flat, wrinkled, dark when wet)
    c = collection('paper')
    for name, w, d, bend, seed, m, weight in (('paper_scrap_a', 0.07, 0.05, 0.0025, 1, paper_m, 2), ('paper_scrap_b', 0.10, 0.065, 0.003, 5, paper_m, 1), ('paper_sodden_a', 0.09, 0.06, 0.0015, 2, sodden_m, 3),
                                              ('paper_sodden_b', 0.12, 0.08, 0.0012, 7, sodden_m, 2), ('paper_sodden_c', 0.06, 0.06, 0.0015, 11, sodden_m, 2),
                                              ('paper_wad', 0.16, 0.11, 0.0020, 13, sodden_m, 1)):
        bm = bmesh.new()
        scrap(w, d, bend, seed)(bm)
        _finish(c, name, bm, m, smooth=True, weight=weight)
    # wet paper clumps (for the gutters): small sodden wads and balls of wet paper and grime
    c = collection('clumps')
    _crumple(c, 'clump_a', clump_m, 0.020, 0.45, 21, weight=3)
    _crumple(c, 'clump_b', clump_m, 0.030, 0.40, 22, weight=2)
    _crumple(c, 'clump_c', clump_m, 0.040, 0.35, 23, weight=1)
    # tiny dust specks (grit): the small stuff that makes the ground read as dirty at full size
    c = collection('specks')
    for seed in range(6):
        _lump(c, f'speck_{seed}', speck_m, 0.0022 + 0.0006 * (seed % 3), 0.6, 40 + seed, subdiv=1, weight=3, sharp=0.5, ridge=0.3, underside=0.5)
    _lump(c, 'speck_pale_0', speck_pale_m, 0.0026, 0.6, 50, subdiv=1, weight=1, sharp=0.4, ridge=0.2)
    _lump(c, 'speck_pale_1', speck_pale_m, 0.0034, 0.5, 51, subdiv=1, weight=1, sharp=0.4, ridge=0.2)
    # leaves
    c = collection('leaves')
    for name, length, width, seed, m, weight in (('leaf_a', 0.065, 0.022, 1, leaf_brown_m, 3), ('leaf_b', 0.05, 0.018, 2, leaf_orange_m, 2), ('leaf_c', 0.075, 0.026, 3, leaf_brown_m, 1)):
        bm = bmesh.new()
        leaf(length, width, seed)(bm)
        _finish(c, name, bm, m, weight=weight)
    # straw: short, thin, curved strands in twos and threes
    c = collection('straw')
    for seed in (3, 4, 5, 6):
        _straw_bundle(c, f'straw_{seed}', straw_m, seed)
    return COLLECTIONS


def set_wetness(wet):
    """How wet the pieces look (0 dry .. 1 soaked): the paper goes dark and limp, the coal and cinders glossy."""
    for node in WET_NODES:
        node.outputs[0].default_value = float(wet)


# ------------------------------------------------------------------------------------------------------------------------------- the scatter
def S(node, name, kind=None):
    for s in node.inputs:
        if s.name == name and (kind is None or s.type == kind):
            return s
    raise KeyError(name)


def build_scatter_tree():
    existing = bpy.data.node_groups.get(rl.SCATTER_TREE_NAME)
    if existing:
        return existing
    collections = build_pieces()
    tree = bpy.data.node_groups.new(rl.SCATTER_TREE_NAME, 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = tree.nodes, tree.links
    group_in, group_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    b = rl.Builder(tree, 'geometry')
    # the dials: one Value node each (named 'dial_<short name>'), so that set_dials() can move them
    value_nodes = {}
    for key, name, default, lo, hi, text in rl.DIALS + PIECE_DIALS:
        node = nodes.new('ShaderNodeValue')
        node.name, node.label = 'dial_' + key, name
        node.outputs[0].default_value = default
        value_nodes[key] = node
    dial = lambda key: value_nodes[key].outputs[0]   # noqa: E731
    position = nodes.new('GeometryNodeInputPosition')
    t = rl.build_terms(b, dial, position.outputs['Position'])
    # round 2 plate: where the camera is (an empty, VIEW_POINT_NAME, that set_view_point() moves to the camera before each picture), to cap the size of the pieces near it
    view_info = nodes.new('GeometryNodeObjectInfo')
    view_info.inputs['Object'].default_value = view_point()
    view_info.transform_space = 'ORIGINAL'
    distance_node = nodes.new('ShaderNodeVectorMath')
    distance_node.operation = 'DISTANCE'
    links.new(position.outputs['Position'], distance_node.inputs[0])
    links.new(view_info.outputs['Location'], distance_node.inputs[1])
    near_t = b.smooth(distance_node.outputs['Value'], NEAR_FULL, NEAR_END)         # 0 near the camera, 1 far from it
    scale_cap = b.add(dial('piece_near_cap'), b.mul(near_t, 4.0))
    px, py, pz, seed = t['px'], t['py'], t['pz'], t['seed']
    mask = t['mask']
    # ---- densities (0..1 of each kind's maximum), the same recipes as the painted layer's kinds
    density_dial = dial('pieces_density')
    lumpy = b.lin(b.noise_at(b.mul(px, 2.2), b.add(b.mul(py, 2.2), seed), 31.0, 1.0, detail=3.0), 0.3, 0.7)
    lump_density = b.mul(b.mul(b.power(mask, 1.1), b.add(0.25, b.mul(lumpy, 0.75))), b.mul(dial('dust'), 0.6))
    coal_density = b.mul(b.clamp01(b.add(b.add(b.mul(t['props'], 0.9), b.mul(t['door'], 0.5)), b.mul(mask, 0.12))), b.mul(dial('dust'), 0.8))
    ash_density = b.mul(b.maximum(b.maximum(b.mul(t['props'], 0.95), b.mul(t['door'], 0.8)), b.mul(t['wall'], 0.12)), dial('ash'))
    straw_density = b.mul(b.add(b.mul(t['gutter'], 0.9), b.mul(t['wall'], 0.8)), b.mul(dial('straw'), 0.5))
    paper_density = b.mul(b.add(b.add(b.mul(t['wall'], 0.7), b.mul(t['gutter'], 0.85)), b.mul(t['corner'], 0.9)), b.mul(dial('paper'), 0.5))
    leaf_density = b.mul(b.add(b.add(b.add(b.mul(t['feet'], 0.9), b.mul(t['corner_only'], 0.5)), b.mul(t['wall'], 0.28)), b.mul(t['gutter'], 0.25)), b.mul(dial('leaves'), 0.7))
    # round 2 plate: the pieces gather where the rubbish gathers. Weight (about 0.2 away from the gutter and the wall foot, 2.0 in them) from the same gutter and wall-foot terms as the painted layer
    gather_term = b.clamp01(b.maximum(t['gutter'], t['wall']))
    gather_weight = b.lerp(dial('pieces_gather'), 1.0, b.add(0.2, b.mul(b.mul(gather_term, gather_term), 1.8)))     # squared: the weight is only high right in the gutter and at the wall foot, low in between
    specks_density = b.mul(b.mul(b.power(mask, 0.9), b.add(0.3, b.mul(lumpy, 0.7))), b.mul(dial('dust'), 0.9))
    clump_density = b.mul(b.add(b.add(b.mul(t['gutter'], 0.9), b.mul(t['wall'], 0.2)), b.mul(t['corner'], 0.35)), b.mul(dial('paper'), 0.7))
    densities = dict(lumps=b.mul(lump_density, gather_weight), coal=coal_density, ash=ash_density, paper=b.mul(paper_density, gather_weight), leaves=b.mul(leaf_density, gather_weight),
                     straw=b.mul(straw_density, gather_weight), specks=b.mul(specks_density, gather_weight), clumps=b.mul(clump_density, gather_weight))
    # ---- the ground: the road, the gutter, the kerbs and the pavements
    join_ground = nodes.new('GeometryNodeJoinGeometry')
    for name in ('street_setts', 'street_pavements', 'street_channels', 'street_kerbs'):
        info = nodes.new('GeometryNodeObjectInfo')
        info.inputs['Object'].default_value = bpy.data.objects[name]
        info.transform_space = 'ORIGINAL'
        links.new(info.outputs['Geometry'], join_ground.inputs['Geometry'])
    near = nodes.new('FunctionNodeCompare')
    near.data_type, near.operation = 'FLOAT', 'LESS_THAN'
    links.new(py, near.inputs[0])
    links.new(dial('pieces_distance'), near.inputs[1])
    join_out = nodes.new('GeometryNodeJoinGeometry')
    for index, (name, spec) in enumerate(CLASSES.items()):
        distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
        distribute.distribute_method = 'POISSON'
        links.new(join_ground.outputs['Geometry'], distribute.inputs['Mesh'])
        links.new(near.outputs[0], S(distribute, 'Selection'))
        S(distribute, 'Distance Min').default_value = spec['distance']
        S(distribute, 'Density Max').default_value = spec['density']
        seeded = nodes.new('ShaderNodeMath')              # the Seed dial moves the pieces too
        seeded.operation = 'ADD'
        links.new(dial('seed'), seeded.inputs[0])
        seeded.inputs[1].default_value = 5 + index
        links.new(seeded.outputs[0], S(distribute, 'Seed'))
        links.new(b.clamp01(b.mul(densities[name], density_dial)), S(distribute, 'Density Factor'))
        info = nodes.new('GeometryNodeCollectionInfo')
        info.inputs['Collection'].default_value = collections[name]
        info.transform_space = 'ORIGINAL'
        S(info, 'Separate Children').default_value = True
        S(info, 'Reset Children').default_value = True
        instance = nodes.new('GeometryNodeInstanceOnPoints')
        links.new(distribute.outputs['Points'], instance.inputs['Points'])
        links.new(info.outputs['Instances'], instance.inputs['Instance'])
        instance.inputs['Pick Instance'].default_value = True
        count = len(collections[name].objects)
        pick = nodes.new('FunctionNodeRandomValue')
        pick.data_type = 'INT'
        S(pick, 'Min', 'INT').default_value = 0
        S(pick, 'Max', 'INT').default_value = count - 1
        pick_seed = nodes.new('ShaderNodeMath')
        pick_seed.operation = 'ADD'
        links.new(dial('seed'), pick_seed.inputs[0])
        pick_seed.inputs[1].default_value = 11 + index
        links.new(pick_seed.outputs[0], S(pick, 'Seed'))
        links.new(pick.outputs[[o.type for o in pick.outputs].index('INT')], instance.inputs['Instance Index'])
        # lie on the ground (the point's rotation aligns the piece with the ground), turned a random way round
        yaw = nodes.new('FunctionNodeRandomValue')
        yaw.data_type = 'FLOAT'
        S(yaw, 'Min', 'VALUE').default_value = 0.0
        S(yaw, 'Max', 'VALUE').default_value = 2 * math.pi
        S(yaw, 'Seed').default_value = 21 + index
        euler = nodes.new('ShaderNodeCombineXYZ')
        links.new(yaw.outputs[[o.type for o in yaw.outputs].index('VALUE')], euler.inputs['Z'])
        to_rotation = nodes.new('FunctionNodeEulerToRotation')
        links.new(euler.outputs['Vector'], to_rotation.inputs[0])
        rotate = nodes.new('FunctionNodeRotateRotation')
        rotate.rotation_space = 'LOCAL'
        links.new(distribute.outputs['Rotation'], rotate.inputs['Rotation'])
        links.new(to_rotation.outputs[0], rotate.inputs['Rotate By'])
        links.new(rotate.outputs[0], instance.inputs['Rotation'])
        size = nodes.new('FunctionNodeRandomValue')
        size.data_type = 'FLOAT'
        S(size, 'Min', 'VALUE').default_value = spec['scale'][0]
        S(size, 'Max', 'VALUE').default_value = spec['scale'][1]
        S(size, 'Seed').default_value = 31 + index
        scaled = nodes.new('ShaderNodeMath')
        scaled.operation = 'MULTIPLY'
        capped = nodes.new('ShaderNodeMath')              # round 2 plate: a piece near the camera is never bigger than the cap
        capped.operation = 'MINIMUM'
        links.new(size.outputs[[o.type for o in size.outputs].index('VALUE')], capped.inputs[0])
        links.new(scale_cap, capped.inputs[1])
        links.new(capped.outputs[0], scaled.inputs[0])
        links.new(dial('piece_size'), scaled.inputs[1])
        links.new(scaled.outputs[0], instance.inputs['Scale'])
        links.new(instance.outputs['Instances'], join_out.inputs['Geometry'])
    links.new(join_out.outputs['Geometry'], group_out.inputs[0])
    return tree


def add_scatter(scene):
    """Builds the scatter (once) and returns its host object (an empty mesh with the Geometry Nodes modifier)."""
    tree = build_scatter_tree()
    host = bpy.data.objects.get('rubbish_scatter')
    if host is None:
        mesh = bpy.data.meshes.new('rubbish_scatter_host')
        host = bpy.data.objects.new('rubbish_scatter', mesh)
        scene.collection.objects.link(host)
        modifier = host.modifiers.new('rubbish_scatter', 'NODES')
        modifier.node_group = tree
    return host


def set_scatter_dials(**dials):
    tree = bpy.data.node_groups.get(rl.SCATTER_TREE_NAME)
    if tree is None:
        return
    for key, value in dials.items():
        node = tree.nodes.get('dial_' + key)
        if node is not None:
            node.outputs[0].default_value = float(value)


def count_pieces(host):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return sum(1 for inst in depsgraph.object_instances if inst.is_instance and inst.parent and inst.parent.name == host.name)
