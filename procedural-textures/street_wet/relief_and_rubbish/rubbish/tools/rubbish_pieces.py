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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rubbish_layer as rl  # noqa: E402

COLLECTIONS = {}
PIECE_DIALS = [
    ('pieces_density', 'Pieces Density', 1.0, 0.0, 2.0, 'How many separate pieces (0 = none)'),
    ('pieces_distance', 'Pieces Distance', 45.0, 5.0, 90.0, 'Pieces only up to this many metres along the street'),
    ('piece_size', 'Piece Size', 1.0, 0.5, 2.0, 'Size of every piece'),
]
PIECE_DEFAULTS = {key: default for key, _, default, _, _, _ in PIECE_DIALS}
PIECE_SOCKETS = {key: name for key, name, _, _, _, _ in PIECE_DIALS}
# (collection, density per square metre where the mask is 1, nearest two pieces may be, smallest and biggest scale)
CLASSES = dict(
    lumps=dict(density=70.0, distance=0.05, scale=(0.7, 1.5)),
    coal=dict(density=45.0, distance=0.05, scale=(0.8, 1.5)),
    ash=dict(density=6.0, distance=0.12, scale=(0.7, 1.4)),
    paper=dict(density=16.0, distance=0.09, scale=(0.7, 1.4)),
    leaves=dict(density=16.0, distance=0.08, scale=(0.8, 1.3)),
    straw=dict(density=18.0, distance=0.12, scale=(0.8, 1.3)),
)
WET_NODES = []


# ------------------------------------------------------------------------------------------------------------------------------- the pieces
def piece_material(name, dry, wet, rough_dry, rough_wet, metallic=0.0, specular=0.5):
    """A plain material that goes from its dry colour to its wet colour with the value node WET (set for all pieces by set_wetness)."""
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
    tree.links.new(mix_colour.outputs[2], principled.inputs['Base Color'])
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


def _lump(collection, name, material, size, flat, seed, subdiv=1, weight=1, sharp=0.35):
    r = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=size)
    for v in bm.verts:
        v.co = Vector((v.co.x * r.uniform(1 - sharp, 1 + 0.2), v.co.y * r.uniform(1 - sharp, 1 + 0.2), v.co.z * flat * r.uniform(1 - sharp, 1.1)))
    low = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= low - 0.001                      # sits on the ground
    _finish(collection, name, bm, material, weight=weight)


def build_pieces():
    """Makes the six collections (not linked to the scene: only the scatter uses them). Returns the dict name -> collection."""
    if COLLECTIONS:
        return COLLECTIONS
    random.seed(7)
    cinder_m = piece_material('piece_cinder', (0.045, 0.042, 0.040), (0.016, 0.015, 0.015), 0.92, 0.55)
    clinker_m = piece_material('piece_clinker', (0.13, 0.095, 0.07), (0.05, 0.035, 0.026), 0.85, 0.5)
    coal_m = piece_material('piece_coal', (0.014, 0.014, 0.016), (0.010, 0.010, 0.012), 0.38, 0.22, specular=0.6)
    ash_m = piece_material('piece_ash', (0.23, 0.22, 0.21), (0.05, 0.048, 0.048), 0.97, 0.6)
    paper_m = piece_material('piece_paper', (0.36, 0.325, 0.27), (0.12, 0.105, 0.085), 0.8, 0.35)
    sodden_m = piece_material('piece_sodden_paper', (0.17, 0.150, 0.125), (0.075, 0.066, 0.055), 0.75, 0.3)
    leaf_brown_m = piece_material('piece_leaf_brown', (0.11, 0.055, 0.020), (0.040, 0.020, 0.008), 0.8, 0.4)
    leaf_orange_m = piece_material('piece_leaf_orange', (0.18, 0.085, 0.024), (0.065, 0.032, 0.010), 0.8, 0.4)
    straw_m = piece_material('piece_straw', (0.30, 0.22, 0.09), (0.10, 0.068, 0.028), 0.8, 0.5)
    china_m = piece_material('piece_china', (0.60, 0.60, 0.57), (0.40, 0.40, 0.38), 0.25, 0.12, specular=0.7)
    wood_m = piece_material('piece_stick', (0.10, 0.065, 0.035), (0.035, 0.022, 0.012), 0.9, 0.5)

    def collection(name):
        c = bpy.data.collections.new('rubbish_' + name)
        COLLECTIONS[name] = c
        return c

    def scrap(w, d, bend, seed, nx=5, ny=4):
        def build(bm):
            bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
            r = random.Random(seed)
            for v in bm.verts:
                edge = (abs(v.co.x) > 0.45) or (abs(v.co.y) > 0.45)
                v.co.x = v.co.x * w * (1 + r.uniform(-0.12, 0.12) * edge)
                v.co.y = v.co.y * d * (1 + r.uniform(-0.12, 0.12) * edge)
                v.co.z = 0.0015 + bend * (math.sin(v.co.x * 55 + seed) * 0.5 + r.uniform(-0.5, 0.5)) * (0.4 + 0.8 * edge)
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

    # lumps: cinders, clinker, sherd, stick
    c = collection('lumps')
    _lump(c, 'cinder_a', cinder_m, 0.011, 0.6, 1, weight=3)
    _lump(c, 'cinder_b', cinder_m, 0.018, 0.55, 2, weight=2)
    _lump(c, 'cinder_c', cinder_m, 0.026, 0.5, 8, weight=1)
    _lump(c, 'clinker_a', clinker_m, 0.016, 0.5, 3, weight=2)
    _lump(c, 'clinker_b', clinker_m, 0.024, 0.45, 9, weight=1)
    bm = bmesh.new()
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.02, radius2=0.017, depth=0.004)
    bmesh.ops.translate(bm, verts=geom['verts'], vec=(0, 0, 0.002))
    for v in bm.verts:
        v.co.x *= 1.0 + 0.4 * math.sin(v.co.y * 90)
    _finish(c, 'china_sherd', bm, china_m, weight=1)
    bm = bmesh.new()
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.005, radius2=0.0035, depth=0.14)
    bmesh.ops.rotate(bm, verts=geom['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    bmesh.ops.translate(bm, verts=geom['verts'], vec=(0, 0, 0.005))
    _finish(c, 'stick', bm, wood_m, weight=1)
    # coal
    c = collection('coal')
    _lump(c, 'coal_a', coal_m, 0.016, 0.7, 4, weight=3, sharp=0.45)
    _lump(c, 'coal_b', coal_m, 0.028, 0.65, 5, weight=2, sharp=0.45)
    _lump(c, 'coal_c', coal_m, 0.011, 0.7, 12, weight=3, sharp=0.45)
    # ash heaps: low flat mounds
    c = collection('ash')
    _lump(c, 'ash_heap_a', ash_m, 0.032, 0.35, 6, subdiv=2, weight=2, sharp=0.55)
    _lump(c, 'ash_heap_b', ash_m, 0.045, 0.28, 10, subdiv=2, weight=1, sharp=0.55)
    _lump(c, 'ash_heap_c', ash_m, 0.025, 0.40, 14, subdiv=1, weight=2, sharp=0.5)
    # paper
    c = collection('paper')
    for name, w, d, bend, seed, m, weight in (('paper_scrap_a', 0.08, 0.06, 0.004, 1, paper_m, 2), ('paper_scrap_b', 0.11, 0.075, 0.005, 5, paper_m, 1), ('paper_sodden_a', 0.10, 0.07, 0.002, 2, sodden_m, 2),
                                              ('paper_sodden_b', 0.14, 0.09, 0.0015, 7, sodden_m, 1), ('paper_sodden_c', 0.07, 0.07, 0.002, 11, sodden_m, 1),
                                              ('paper_wad', 0.20, 0.13, 0.003, 13, sodden_m, 1)):
        bm = bmesh.new()
        scrap(w, d, bend, seed)(bm)
        _finish(c, name, bm, m, weight=weight)
    # leaves
    c = collection('leaves')
    for name, length, width, seed, m, weight in (('leaf_a', 0.065, 0.022, 1, leaf_brown_m, 3), ('leaf_b', 0.05, 0.018, 2, leaf_orange_m, 2), ('leaf_c', 0.075, 0.026, 3, leaf_brown_m, 1)):
        bm = bmesh.new()
        leaf(length, width, seed)(bm)
        _finish(c, name, bm, m, weight=weight)
    # straw: bundles of a few strands
    c = collection('straw')
    for seed in (3, 4, 5):
        r = random.Random(seed)
        bm = bmesh.new()
        for k in range(r.randint(2, 4)):
            geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.0017, radius2=0.0012, depth=r.uniform(0.05, 0.12))
            bmesh.ops.rotate(bm, verts=geom['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
            bmesh.ops.rotate(bm, verts=geom['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(r.uniform(-0.9, 0.9), 3, 'Z'))
            bmesh.ops.translate(bm, verts=geom['verts'], vec=(r.uniform(-0.03, 0.03), r.uniform(-0.025, 0.025), 0.002 + 0.0015 * k))
        _finish(c, f'straw_{seed}', bm, straw_m, weight=1)
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
    densities = dict(lumps=lump_density, coal=coal_density, ash=ash_density, paper=paper_density, leaves=leaf_density, straw=straw_density)
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
        links.new(size.outputs[[o.type for o in size.outputs].index('VALUE')], scaled.inputs[0])
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
