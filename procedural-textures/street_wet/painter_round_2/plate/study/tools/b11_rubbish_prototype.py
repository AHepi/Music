# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A QUICK PROTOTYPE of the rubbish layer, to find out what it costs and whether it reads; not the finished tool. Two methods, switched separately:
#   method 1  "muck layer":  the rubbish mask (work/rubbish_plan_mask.png, made by b10_rubbish_plan_mask.py) is looked up by each dot's world position on the road, the
#             pavements, the gutter stones and the kerbs, and over the wet look the material is dirtied: coal dust and ash speckle (dark grit), a thin dull film (less shine),
#             damp brown mud in the gutter bottom (a little shine again).
#   method 2  "pieces":  small separate pieces (cinder lumps, coal, torn paper, a dead leaf, straw, a crock sherd, a stick) scattered with Geometry Nodes (Distribute Points on Faces,
#             Poisson disk: no two closer than 6 cm) where the mask's green channel is high, then Instance on Points with a random piece, turn and size.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 BLEND --python b11_rubbish_prototype.py -- OUT_FOLDER LIST
#   LIST = comma separated pictures: camera:light:state:muck(0/1):pieces(0/1):width:height:samples[:name]   e.g.  main:A:wet:1:1:540:960:16
#   The street file is opened and NEVER saved. The film's lockout file works too (the drum's cinders come from the mask).
# Prints: how many pieces, the build time, the render time of each picture.
import json
import math
import os
import random
import sys
import time

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))      # street_wet/tools: apply_wetness_to_set.py and wetness_layer.py
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402
import b02_lighting_and_variants as lv  # noqa: E402

WORK = os.path.abspath(os.path.join(HERE, '..', 'work'))
MASK = os.environ.get('RUBBISH_MASK', os.path.join(WORK, 'rubbish_plan_mask.png'))      # the street's mask, or rubbish_plan_mask_lockout.png for the lockout shot
X0, X1, Y0, Y1 = -4.5, 4.5, -12.0, 72.0
args = sys.argv[sys.argv.index('--') + 1:]
out_folder, picture_list = args[0], args[1].split(',')
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene


def S(node, name, kind=None):
    """An input socket by name (and by type when several share the name)."""
    for s in node.inputs:
        if s.name == name and (kind is None or s.type == kind):
            return s
    raise KeyError(name)


# ------------------------------------------------------------------------------------------------------------------------------- method 1: the muck layer
def add_muck(material_name, amount=None, mud_colour=(0.045, 0.034, 0.024), cinder_colour=(0.030, 0.028, 0.027)):
    amount = MUCK_AMOUNT if amount is None else amount
    material = bpy.data.materials[material_name]
    tree = material.node_tree
    group = aw.APPLIED[material_name][0]
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    nodes, links = tree.nodes, tree.links
    added = []
    # what feeds the Principled BSDF now (the wetness layer, or the joint picture on top of it): the rubbish goes AFTER it, so the layers chain
    source = {name: next(l for l in links if l.to_socket == principled.inputs[name]).from_socket for name in ('Base Color', 'Roughness', 'Coat Weight', 'Specular IOR Level', 'Normal')}

    def new(kind, **props):
        n = nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        added.append(n)
        return n

    def math_node(op, a, b=None, clamp=False):
        n = new('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    def smooth(value, lo, hi):
        n = new('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        links.new(value, n.inputs['Value'])
        n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = lo, hi
        return n.outputs['Result']

    geometry = new('ShaderNodeNewGeometry')
    position = geometry.outputs['Position']
    separate_position = new('ShaderNodeSeparateXYZ')
    links.new(position, separate_position.inputs[0])
    u = math_node('DIVIDE', math_node('ADD', separate_position.outputs['X'], -X0), X1 - X0)
    v = math_node('DIVIDE', math_node('ADD', separate_position.outputs['Y'], -Y0), Y1 - Y0)
    uv = new('ShaderNodeCombineXYZ')
    links.new(u, uv.inputs['X'])
    links.new(v, uv.inputs['Y'])
    picture = bpy.data.images.load(MASK, check_existing=True)
    picture.colorspace_settings.name = 'Non-Color'
    image_node = new('ShaderNodeTexImage', interpolation='Linear', extension='EXTEND')
    image_node.image = picture
    links.new(uv.outputs['Vector'], image_node.inputs['Vector'])
    split = new('ShaderNodeSeparateColor')
    links.new(image_node.outputs['Color'], split.inputs['Color'])
    dirt, mud = split.outputs['Red'], split.outputs['Blue']
    # fine patchiness and grit, by world position (size of the grit: about 5 mm)
    film_noise = new('ShaderNodeTexNoise', noise_dimensions='3D')
    film_noise.inputs['Scale'].default_value, film_noise.inputs['Detail'].default_value = 7.0, 4.0
    links.new(position, film_noise.inputs['Vector'])
    film = smooth(film_noise.outputs['Fac'], 0.3, 0.7)
    grit_noise = new('ShaderNodeTexNoise', noise_dimensions='3D')
    grit_noise.inputs['Scale'].default_value, grit_noise.inputs['Detail'].default_value = 230.0, 2.0
    links.new(position, grit_noise.inputs['Vector'])
    grit = smooth(grit_noise.outputs['Fac'], 0.50, 0.60)
    amount_dirt = math_node('MULTIPLY', math_node('MULTIPLY', dirt, math_node('ADD', 0.55, math_node('MULTIPLY', film, 0.9))), amount, clamp=True)
    amount_mud = math_node('MULTIPLY', math_node('MULTIPLY', mud, math_node('ADD', 0.5, film)), amount, clamp=True)
    # colour: darkened, grit specks of cinder colour, then mud
    dark = new('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    dark.inputs[0].default_value = 1.0
    links.new(source['Base Color'], dark.inputs[6])
    shade = math_node('SUBTRACT', 1.0, math_node('MULTIPLY', amount_dirt, 0.55))
    shade_colour = new('ShaderNodeCombineColor')
    for c in ('Red', 'Green', 'Blue'):
        links.new(shade, shade_colour.inputs[c])
    links.new(shade_colour.outputs['Color'], dark.inputs[7])
    cinders = new('ShaderNodeMix', data_type='RGBA')
    links.new(math_node('MULTIPLY', math_node('MULTIPLY', amount_dirt, grit), 0.95, clamp=True), cinders.inputs[0])
    links.new(dark.outputs[2], cinders.inputs[6])
    cinders.inputs[7].default_value = (*cinder_colour, 1.0)
    muddy = new('ShaderNodeMix', data_type='RGBA')
    links.new(math_node('MULTIPLY', amount_mud, 0.85, clamp=True), muddy.inputs[0])
    links.new(cinders.outputs[2], muddy.inputs[6])
    muddy.inputs[7].default_value = (*mud_colour, 1.0)
    links.new(muddy.outputs[2], principled.inputs['Base Color'])
    # roughness: dust is dull (0.95), mud is smooth and wet again
    rough_dull = new('ShaderNodeMix', data_type='FLOAT')
    links.new(math_node('MULTIPLY', amount_dirt, 0.75, clamp=True), rough_dull.inputs[0])
    links.new(source['Roughness'], rough_dull.inputs[2])
    rough_dull.inputs[3].default_value = 0.95
    rough_mud = new('ShaderNodeMix', data_type='FLOAT')
    links.new(math_node('MULTIPLY', amount_mud, 0.6, clamp=True), rough_mud.inputs[0])
    links.new(rough_dull.outputs[0], rough_mud.inputs[2])
    rough_mud.inputs[3].default_value = 0.4
    links.new(rough_mud.outputs[0], principled.inputs['Roughness'])
    # shine under dust: the film dulls the reflection
    dull_factor = math_node('SUBTRACT', 1.0, math_node('MULTIPLY', amount_dirt, 0.7))
    coat = math_node('MULTIPLY', source['Coat Weight'], dull_factor)
    links.new(coat, principled.inputs['Coat Weight'])
    links.new(math_node('MULTIPLY', source['Specular IOR Level'], math_node('ADD', 0.45, math_node('MULTIPLY', dull_factor, 0.55))), principled.inputs['Specular IOR Level'])
    # a little bump from the grit (the speckle stands up from the ground)
    bump = new('ShaderNodeBump')
    bump.inputs['Strength'].default_value, bump.inputs['Distance'].default_value = 0.35, 0.004
    links.new(math_node('MULTIPLY', amount_dirt, grit), bump.inputs['Height'])
    links.new(source['Normal'], bump.inputs['Normal'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    return added


# ------------------------------------------------------------------------------------------------------------------------------- method 2: the pieces
def piece_material(name, colour, roughness, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1.0)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m


def make_piece(collection, name, builder, material):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    builder(bm)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def build_pieces():
    random.seed(7)
    collection = bpy.data.collections.new('rubbish_pieces')      # not linked to the scene: only the scatter uses it
    cinder_m = piece_material('piece_cinder', (0.040, 0.037, 0.035), 0.9)
    clinker_m = piece_material('piece_clinker', (0.10, 0.075, 0.06), 0.85)
    coal_m = piece_material('piece_coal', (0.012, 0.012, 0.014), 0.35)
    paper_m = piece_material('piece_paper', (0.30, 0.27, 0.22), 0.85)
    sodden_m = piece_material('piece_sodden_paper', (0.12, 0.105, 0.085), 0.7)
    leaf_m = piece_material('piece_leaf', (0.10, 0.055, 0.02), 0.8)
    straw_m = piece_material('piece_straw', (0.32, 0.23, 0.08), 0.8)
    china_m = piece_material('piece_china', (0.55, 0.55, 0.52), 0.25)
    wood_m = piece_material('piece_stick', (0.08, 0.05, 0.03), 0.9)

    def lump(size, squash, seed):
        def build(bm):
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size)
            r = random.Random(seed)
            for v in bm.verts:
                v.co = Vector((v.co.x * r.uniform(0.7, 1.2), v.co.y * r.uniform(0.7, 1.2), v.co.z * squash * r.uniform(0.6, 1.1)))
                v.co.z += size * squash
        return build

    def scrap(w, d, bend, seed):
        def build(bm):
            bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=0.5)
            r = random.Random(seed)
            for v in bm.verts:
                v.co.x *= w
                v.co.y *= d
                v.co.z = bend * math.sin(v.co.x * 40) * 0.5 + r.uniform(0, 0.0015) + 0.0015
            for v in bm.verts:
                pass
        return build

    def leaf(length, width):
        def build(bm):
            bmesh.ops.create_grid(bm, x_segments=6, y_segments=3, size=0.5)
            for v in bm.verts:
                t = v.co.x + 0.5                       # 0..1 along the leaf
                v.co.y *= width * math.sin(math.pi * min(1, max(0, t))) * 2.0 + 0.0005
                v.co.x *= length
                v.co.z = 0.002 + 0.006 * (v.co.y / max(width, 1e-4)) ** 2 + 0.002 * t
        return build

    def straw(bm):
        r = random.Random(3)
        for k in range(4):
            geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.0016, radius2=0.0013, depth=r.uniform(0.12, 0.2))
            angle = r.uniform(-0.5, 0.5)
            bmesh.ops.rotate(bm, verts=geom['verts'], cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'Y'))
            bmesh.ops.rotate(bm, verts=geom['verts'], cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(angle, 3, 'Z'))
            bmesh.ops.translate(bm, verts=geom['verts'], vec=(r.uniform(-0.03, 0.03), r.uniform(-0.025, 0.025), 0.002 + 0.002 * k))

    def sherd(bm):
        pts = [(-0.025, -0.015), (0.03, -0.01), (0.015, 0.028), (-0.02, 0.012)]
        verts = [bm.verts.new((x, y, 0.001)) for x, y in pts]
        bm.faces.new(verts)
        for v in verts[:2]:
            v.co.z += 0.003

    def stick(bm):
        geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.005, radius2=0.004, depth=0.12)
        bmesh.ops.rotate(bm, verts=geom['verts'], cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'Y'))
        bmesh.ops.translate(bm, verts=geom['verts'], vec=(0, 0, 0.005))

    objs = [make_piece(collection, 'cinder_a', lump(0.014, 0.6, 1), cinder_m), make_piece(collection, 'cinder_b', lump(0.022, 0.55, 2), cinder_m),
            make_piece(collection, 'clinker', lump(0.02, 0.5, 3), clinker_m), make_piece(collection, 'coal_a', lump(0.018, 0.7, 4), coal_m),
            make_piece(collection, 'coal_b', lump(0.03, 0.65, 5), coal_m), make_piece(collection, 'paper_scrap', scrap(0.08, 0.06, 0.004, 1), paper_m),
            make_piece(collection, 'paper_sodden', scrap(0.10, 0.07, 0.002, 2), sodden_m), make_piece(collection, 'leaf', leaf(0.07, 0.025), leaf_m),
            make_piece(collection, 'straw', straw, straw_m), make_piece(collection, 'china_sherd', sherd, china_m), make_piece(collection, 'stick', stick, wood_m)]
    return collection, len(objs)


DENSITY = float(os.environ.get('RUBBISH_DENSITY', '140'))       # most pieces per square metre where the mask is 1 (first try 140; the second try 45)
Y_LIMIT = float(os.environ.get('RUBBISH_YMAX', '90'))           # pieces only up to this many metres along the street (the first try had no limit)
MUCK_AMOUNT = float(os.environ.get('RUBBISH_MUCK', '1.0'))      # strength of the muck layer (the first try 1.0)


def build_scatter(collection, piece_count, density_max=None, min_distance=0.06, seed=5):
    density_max = DENSITY if density_max is None else density_max
    tree = bpy.data.node_groups.new('rubbish_scatter_tree', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = tree.nodes, tree.links
    group_out = nodes.new('NodeGroupOutput')
    join = nodes.new('GeometryNodeJoinGeometry')
    for name in ('street_setts', 'street_pavements', 'street_channels', 'street_kerbs'):
        info = nodes.new('GeometryNodeObjectInfo')
        info.inputs['Object'].default_value = bpy.data.objects[name]
        info.transform_space = 'ORIGINAL'
        links.new(info.outputs['Geometry'], join.inputs['Geometry'])
    distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute.distribute_method = 'POISSON'
    links.new(join.outputs['Geometry'], distribute.inputs['Mesh'])
    S(distribute, 'Distance Min').default_value = min_distance
    S(distribute, 'Density Max').default_value = density_max
    S(distribute, 'Seed').default_value = seed
    # density factor = the mask's green channel at the point's world position
    position = nodes.new('GeometryNodeInputPosition')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position.outputs['Position'], sep.inputs[0])
    u = nodes.new('ShaderNodeMath'); u.operation = 'ADD'
    links.new(sep.outputs['X'], u.inputs[0]); u.inputs[1].default_value = -X0
    u2 = nodes.new('ShaderNodeMath'); u2.operation = 'DIVIDE'
    links.new(u.outputs[0], u2.inputs[0]); u2.inputs[1].default_value = X1 - X0
    v = nodes.new('ShaderNodeMath'); v.operation = 'ADD'
    links.new(sep.outputs['Y'], v.inputs[0]); v.inputs[1].default_value = -Y0
    v2 = nodes.new('ShaderNodeMath'); v2.operation = 'DIVIDE'
    links.new(v.outputs[0], v2.inputs[0]); v2.inputs[1].default_value = Y1 - Y0
    comb = nodes.new('ShaderNodeCombineXYZ')
    links.new(u2.outputs[0], comb.inputs['X'])
    links.new(v2.outputs[0], comb.inputs['Y'])
    picture = bpy.data.images.load(MASK, check_existing=True)
    picture.colorspace_settings.name = 'Non-Color'
    tex = nodes.new('GeometryNodeImageTexture')
    tex.inputs['Image'].default_value = picture
    tex.interpolation = 'Linear'
    tex.extension = 'EXTEND'
    links.new(comb.outputs['Vector'], tex.inputs['Vector'])
    sepc = nodes.new('FunctionNodeSeparateColor')
    links.new(tex.outputs['Color'], sepc.inputs['Color'])
    links.new(sepc.outputs['Green'], S(distribute, 'Density Factor'))
    # only the part of the street near the camera: faces whose centre is closer than Y_LIMIT metres along the street
    near = nodes.new('FunctionNodeCompare')
    near.data_type = 'FLOAT'
    near.operation = 'LESS_THAN'
    links.new(sep.outputs['Y'], near.inputs[0])
    near.inputs[1].default_value = Y_LIMIT
    links.new(near.outputs[0], S(distribute, 'Selection'))
    # which piece, which turn, which size
    coll = nodes.new('GeometryNodeCollectionInfo')
    coll.inputs['Collection'].default_value = collection
    coll.transform_space = 'ORIGINAL'
    S(coll, 'Separate Children').default_value = True
    S(coll, 'Reset Children').default_value = True
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    links.new(distribute.outputs['Points'], instance.inputs['Points'])
    links.new(coll.outputs['Instances'], instance.inputs['Instance'])
    instance.inputs['Pick Instance'].default_value = True
    pick = nodes.new('FunctionNodeRandomValue')
    pick.data_type = 'INT'
    S(pick, 'Min', 'INT').default_value = 0
    S(pick, 'Max', 'INT').default_value = piece_count - 1
    S(pick, 'Seed').default_value = 11
    links.new(pick.outputs[[o.type for o in pick.outputs].index('INT')], instance.inputs['Instance Index'])
    yaw = nodes.new('FunctionNodeRandomValue')
    yaw.data_type = 'FLOAT'
    S(yaw, 'Min', 'VALUE').default_value = 0.0
    S(yaw, 'Max', 'VALUE').default_value = 2 * math.pi
    S(yaw, 'Seed').default_value = 21
    euler = nodes.new('ShaderNodeCombineXYZ')
    links.new(yaw.outputs[[o.type for o in yaw.outputs].index('VALUE')], euler.inputs['Z'])
    to_rotation = nodes.new('FunctionNodeEulerToRotation')
    links.new(euler.outputs['Vector'], to_rotation.inputs[0])
    links.new(to_rotation.outputs[0], instance.inputs['Rotation'])
    size = nodes.new('FunctionNodeRandomValue')
    size.data_type = 'FLOAT'
    S(size, 'Min', 'VALUE').default_value = 0.7
    S(size, 'Max', 'VALUE').default_value = 1.5
    S(size, 'Seed').default_value = 31
    links.new(size.outputs[[o.type for o in size.outputs].index('VALUE')], instance.inputs['Scale'])
    links.new(instance.outputs['Instances'], group_out.inputs[0])
    mesh = bpy.data.meshes.new('rubbish_scatter_host')
    host = bpy.data.objects.new('rubbish_scatter', mesh)
    scene.collection.objects.link(host)
    modifier = host.modifiers.new('rubbish_scatter', 'NODES')
    modifier.node_group = tree
    return host


def count_instances(host):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return sum(1 for inst in depsgraph.object_instances if inst.is_instance and inst.parent and inst.parent.name == host.name)


# ------------------------------------------------------------------------------------------------------------------------------- run
cams = aw.cameras()
aw.apply(wetness=0.0, puddles=0.0)
if os.environ.get('RUBBISH_WITH_JOINT') == '1':
    # chain: the wetness layer, then the joint picture (mild1, the study's recommended first setting), then the rubbish
    lv.joint_picture(colour_mult=0.85, rough_to=0.9, spec_keep=0.65, coat_keep=0.55, picture='joint_cavity_closed.png')
    print('JOINT PICTURE ON (mild1)', flush=True)
started = time.time()
muck_on = {}
host = None
piece_total = None
for entry in picture_list:
    parts = entry.split(':')
    camera, light, state, muck, pieces, w, h, samples = parts[:8]
    name = parts[8] if len(parts) > 8 else f'{camera}_{light}_{state}_m{muck}p{pieces}'
    png = os.path.join(out_folder, name + '.png')
    if os.path.exists(png):
        continue
    if muck == '1' and 'done' not in muck_on:
        t = time.time()
        for material_name in ('street_setts', 'pavement_flags', 'channel_stones', 'kerb_stone'):
            add_muck(material_name)
        muck_on['done'] = True
        print('MUCK LAYER built in', round(time.time() - t, 1), 's', flush=True)
    if pieces == '1' and host is None:
        t = time.time()
        collection, count = build_pieces()
        host = build_scatter(collection, count)
        print('SCATTER built in', round(time.time() - t, 1), 's', flush=True)
        try:
            piece_total = count_instances(host)
            print('PIECES', piece_total, flush=True)
        except Exception as error:
            print('could not count the pieces', error, flush=True)
    if host is not None:
        host.hide_render = (pieces != '1')
    scene.camera = cams[camera]
    lv.eevee_setup(int(w), int(h), int(samples))
    lv.set_lighting(light)
    wet, pud = lv.parse_state(state)
    aw.set_state(wet, pud)
    scene.render.filepath = png
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('DRAWN', name, round(time.time() - t, 1), 's', flush=True)
print('PIECES TOTAL', piece_total, 'ALL DONE', flush=True)
