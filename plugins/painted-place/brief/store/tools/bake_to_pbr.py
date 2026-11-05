"""
What this file does: bakes (projects) a detailed thing onto a simple low shape with a UV map, as a set of pictures:
its colour without light, its relief as a normal picture, its shine (roughness) and its height. The shape gets a
material made from those pictures, and its height as real relief (a Subdivision and a Displace modifier, so its outline
is lumpy like the thing's, not smooth), so the thing can be drawn as a few hundred faces and four pictures instead of
its thousands of leaves, flowers or stones. The thing may be a store part (give its root) or any objects you give; the
tool makes the shape itself (a dome that hugs the thing's outline, open at the foot, or a ball closed all round), or
uses a shape you give. Your objects are left exactly as they were: hide or delete them yourself once the baked shape
reads well. Nothing here looks round the scene: it bakes only what you pass, in a scene of its own that it removes.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import store, bake_to_pbr
    bush = store.add_part('azalea', location=(2.0, 3.0, 0.0), seed=4)
    baked = bake_to_pbr.bake(bush, size=512, lit_through=0.3, folder='/my/work/baked')   # the low shape, in your scene
    for o in [bush] + list(bush.children_recursive):                                     # the built bush out of the picture
        o.hide_render = True
    copy = bake_to_pbr.bake([rock, moss_tufts], form='ball', size=1024, relief_detail=4, folder='/my/work/baked')

From the command line:

    python3 bake_to_pbr.py --help
    python3 bake_to_pbr.py --blend IN.blend --objects "azalea 1" --folder /my/work/baked --out OUT.blend

Options, with their defaults:
    objects        what to bake: a part's root (an empty stands for everything under it) or a list of objects (required)
    shape          None: the tool makes the shape; or a mesh object of yours, with a UV map
    form           'dome' (default): open at the foot, for things standing on the ground; 'ball': closed all round
                   (its underside gets the least of the pictures: they are laid from its top)
    segments       how many faces round the made shape (32); rings: how many from the foot to the top (10);
                   32 x 10 makes a dome of 320 faces
    size           the pictures' size in pixels, square (1024). Tested on the azalea: from 8 m 256 and 512 read the same
                   as 1024; at 1.8 m 2048 with relief_detail=4 is crisper than 1024 (9.4 MB of pictures, 59 s to bake)
    reach          metres in front of the shape the projection starts (0.06): leaves or flowers standing further out
                   than this past the shape are cut off flat
    depth          metres behind the shape the projection still looks (0.25): gaps deeper than this read as holes
    relief         True (default): the height as real relief (Subdivision 'SIMPLE' + Displace, both engines);
                   False: the plain shape with its normal picture only (it reads as a smooth painted dome)
    relief_detail  the Subdivision's levels for the relief (3: 64 faces for each face of the shape; 4 for close up)
    lit_through    how much light the baked surface lets through from behind, 0 to 1 (0; 0.3 for leaves and petals:
                   the azalea's petals are 35% lit through, its leaves 15%)
    bits           8 (default) or 16: the normal and height pictures' depth (the colour and roughness are always 8);
                   16 about doubles the pictures' files (6.7 against 3.0 MB at 1024) and Cycles' memory for them
                   (34 against 30 MB for the whole close picture), and read the same
    samples        Cycles samples for each bake (2)
    folder         where the pictures are written as PNG ('<name> - colour.png', '- normal', '- roughness', '- height');
                   None: written to a temporary folder and packed into the .blend
    name           the baked shape's name ('<the first object's name> • baked')
    collection     where the shape goes (the scene's own collection)

It returns the shape. Its material is 'BAKED • <name>', with the nodes 'Colour picture', 'Normal picture', 'Roughness
picture' and 'Height picture'; the colour picture's alpha is 1 where the projection found the thing and 0 where it
found nothing (those pixels are filled from their neighbours). The shape carries 'baked_from_faces' (the faces the
thing draws, its live copies counted), 'baked_height_low' and 'baked_height_high' (the metres the height picture's 0
and 1 stand for), 'baked_found' (the share of the shape where the projection found the thing), 'baked_faces_turned'
and 'baked_seconds'.

How it works: the thing's live copies (leaves, flowers on points) are made real on copies of its objects, and every
real face that faces into the shape is turned to face out (a leaf of one face seen from its back bakes as a dark dent
in the normal picture otherwise); the made shape's points are pulled in from outside along rays to the thing's middle
until they meet it, smoothed a little (a part's dome stands on the part's foot, its root, so leaves hanging below the
ground are left out; other things' on their lowest point); its UV map is one seamless island (the shape seen from its
top pole), so the relief cannot crack at seams; Cycles bakes colour, roughness and normal "selected to active" with the reach as its
extrusion, and the height from where each pixel's ray met the thing. Baking is done by Cycles in the tool's own scene;
yours is not changed.

Measured on the store's azalea (265,367 faces drawn; the baked shape 320 faces, 20,480 with its relief), Cycles, 32
samples, each bush drawn alone under the same light: baked in 21 s with 1024 pictures (8 s with 256); drawn in 8.3 s
against 13.2 s at 3 m (the card's three-quarter view), 10.3 s against 20.9 s at 1.8 m, 20 s against 21.4 s in a dusk
garden from 8 m (the rest of the garden takes most of that). Eevee, drawing through software on a machine with no
graphics card, took 11.1 s and 27.0 s at 3 m: slower than Cycles there. Files (the empty file's 0.48 MB taken off):
the azalea is stored as points carrying live copies, 0.92 MB; baked, 0.10 MB and its pictures: 3.0 MB at 1024, 0.92 MB
at 512, 0.26 MB at 256 (bits=16 about doubles them). Cycles' memory for the close picture: 20 MB built, 30 MB baked
with 1024 pictures; about the same in the garden (86 against 88 to 96 MB). How it reads: from 3 m on it reads as the
built bush (from 8 m 256 pictures read the same as 1024); at 1.8 m its flowers look flattened and soft and its top
outline smoother; without its relief it reads as a shiny painted dome.
"""

import argparse
import math
import os
import struct
import sys
import tempfile
import time
import zlib

import bpy
import bmesh  # bpy must come first
import numpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

TOOL = {
    'name': 'bake_to_pbr',
    'what': "bakes a detailed thing you give (a part's root or any objects) onto a simple low shape with a UV map, as four "
            'pictures (colour without light, a normal picture, roughness, height), and gives back the shape with a material '
            'made from them and its height as real relief, so a bush of thousands of leaves and flowers draws as a few '
            'hundred faces and four pictures; your objects are left as they were',
    'call': "baked = bake_to_pbr.bake(store.add_part('azalea'), size=512, lit_through=0.3, folder='/my/work/baked')",
    'options': {
        'objects': "a part's root (an empty stands for everything under it) or a list of objects (required)",
        'shape': 'None: the tool makes the shape; or a mesh object of yours with a UV map (refused without one) (None)',
        'form': "'dome': open at the foot, for things standing on the ground; 'ball': closed all round ('dome')",
        'segments, rings': 'faces round the made shape and from its foot to its top ((32, 10): 320 faces)',
        'size': "the pictures' size in pixels, square (1024; from 6 m on 256 to 512 read the same; 2048 at 1 to 2 m)",
        'reach': 'metres in front of the shape the projection starts; anything further out is cut off flat (0.06)',
        'depth': 'metres behind the shape the projection still looks; gaps deeper than this read as holes (0.25)',
        'relief': 'True: the height as real relief (Subdivision and Displace, both engines); False: normal picture only (True)',
        'relief_detail': 'the Subdivision levels for the relief (3; 4 close up)',
        'lit_through': 'how much light the baked surface lets through from behind, 0 to 1 (0; 0.3 for leaves and petals)',
        'bits': "the normal and height pictures' depth, 8 or 16 (8; 16 about doubles the files and reads the same)",
        'samples': 'Cycles samples for each bake (2)',
        'folder': 'where the four pictures are written as PNG; None packs them into the .blend (None)',
        'name': "the baked shape's name (\"<first object's name> • baked\")",
        'collection': "where the shape goes (the scene's own collection)",
    },
    'materials': ['makes its own: BAKED • <name> (the four baked pictures on a Principled BSDF)'],
    'source': "the owner's word (decision 87): bake the store's azalea onto a simple low shape as PBR pictures and see how it "
              'reads; tested on the azalea beside the built one, close up under the card light and from 8 m in a dusk garden '
              "(the bake helper's notes, closer58/bake/notes.md)",
    'trap': 'the baked shape is a shell: from about 3 m on it reads as the built thing, but at 1.8 m its flowers look '
            'flattened and soft (they lie on the shell instead of standing proud over the leaves) and its outline is '
            'smoother; without its relief (relief=False) it reads as a shiny painted dome. A part made of live copies (the '
            "azalea) is stored as points, so the baked one is bigger with 1024 pictures (3.1 against 0.92 MB): use 256 to 512 "
            'for things 6 m and more away. Its leaves cast no shadows of their own: bake again after changing the thing',
}

GEOMETRY_TYPES = ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT')
PASSES = ('colour', 'normal', 'roughness', 'height')


# ---------------------------------------------------------------------------------------------- what to bake

def _sources(objects):
    """The objects to bake, from what the caller passed: an empty (a part's root) stands for every object under it;
    objects hidden from the render (the shapes a part copies onto its points) are left out."""
    if isinstance(objects, bpy.types.Object):
        objects = [objects]
    found = []
    for obj in objects:
        group = [obj] + (list(obj.children_recursive) if obj.type == 'EMPTY' else [])
        for item in group:
            if item.type not in GEOMETRY_TYPES or item in found:
                continue
            if item.hide_render or any(c.hide_render for c in item.users_collection):
                continue
            found.append(item)
    if not found:
        raise ValueError('bake_to_pbr: nothing to bake in what was given (give meshes, or a part\'s root)')
    return found


def _realize_group():
    group = bpy.data.node_groups.new('bake_to_pbr • realize', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    given, out = group.nodes.new('NodeGroupInput'), group.nodes.new('NodeGroupOutput')
    real = group.nodes.new('GeometryNodeRealizeInstances')
    group.links.new(given.outputs[0], real.inputs[0])
    group.links.new(real.outputs[0], out.inputs[0])
    return group


def _all_nodes(tree):
    return list(tree.nodes) if tree is not None else []


def _high_copies(sources, scene):
    """Real meshes of the sources, as drawn (their live copies made real), in the bake's own scene. Materials that read
    a number from the copies' points ('Instancer' attributes) get copies reading it from the real mesh instead."""
    group = _realize_group()
    temporary = []
    for src in sources:
        tmp = src.copy()
        tmp.parent = None
        tmp.matrix_world = src.matrix_world.copy()
        scene.collection.objects.link(tmp)
        if tmp.type in ('MESH', 'CURVE'):
            try:
                modifier = tmp.modifiers.new('bake_to_pbr realize', 'NODES')
                modifier.node_group = group
            except (RuntimeError, TypeError):
                pass
        temporary.append((src, tmp))
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
        depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    highs, faces, made = [], 0, []
    for src, tmp in temporary:          # every mesh made first: removing an object stales the others' evaluated state
        evaluated = tmp.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
        made.append((src, mesh, tmp.matrix_world.copy()))
    for src, tmp in temporary:
        bpy.data.objects.remove(tmp, do_unlink=True)
    for src, mesh, world in made:
        if len(mesh.polygons) == 0:
            bpy.data.meshes.remove(mesh)
            continue
        mesh.name = 'bake_to_pbr high • ' + src.name
        high = bpy.data.objects.new(mesh.name, mesh)
        high.matrix_world = world
        scene.collection.objects.link(high)
        highs.append(high)
        faces += len(mesh.polygons)
    bpy.data.node_groups.remove(group)
    if not highs:
        raise ValueError('bake_to_pbr: what was given draws no faces')
    copies = {}
    for high in highs:
        for index, material in enumerate(high.data.materials):
            if material is None or not material.use_nodes:
                continue
            reads = [n for n in _all_nodes(material.node_tree) if n.type == 'ATTRIBUTE' and n.attribute_type == 'INSTANCER']
            if not reads:
                continue
            if material.name not in copies:
                copy = material.copy()
                copy.name = material.name + ' • bake_to_pbr'
                for node in _all_nodes(copy.node_tree):
                    if node.type == 'ATTRIBUTE' and node.attribute_type == 'INSTANCER':
                        node.attribute_type = 'GEOMETRY'
                copies[material.name] = copy
            high.data.materials[index] = copies[material.name]
    return highs, faces, list(copies.values())


def _world_triangles(highs):
    verts, tris, offset = [], [], 0
    for high in highs:
        mesh = high.data
        mesh.calc_loop_triangles()
        co = numpy.empty(len(mesh.vertices) * 3, dtype=numpy.float64)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        m = numpy.array(high.matrix_world)
        co = co @ m[:3, :3].T + m[:3, 3]
        t = numpy.empty(len(mesh.loop_triangles) * 3, dtype=numpy.int64)
        mesh.loop_triangles.foreach_get('vertices', t)
        verts.append(co)
        tris.append(t.reshape(-1, 3) + offset)
        offset += len(co)
    return numpy.concatenate(verts), numpy.concatenate(tris)


def _face_out(highs, shape):
    """Turns every face of the real meshes that faces into the shape (a leaf or a petal made of one face, seen from
    its back) to face out: the normal bake reads a face's own facing, so a leaf facing in bakes as a dent that draws
    dark (the first baked azalea had dark swirls where its leaves faced in). Returns how many faces were turned."""
    co = numpy.empty(len(shape.data.vertices) * 3, dtype=numpy.float64)
    shape.data.vertices.foreach_get('co', co)
    m = numpy.array(shape.matrix_world)
    co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    tree = BVHTree.FromPolygons(co.tolist(), [tuple(f.vertices) for f in shape.data.polygons])
    turned = 0
    for high in highs:
        world = high.matrix_world
        turn = world.to_3x3().inverted().transposed()
        bm = bmesh.new()
        bm.from_mesh(high.data)
        flip = []
        for face in bm.faces:
            centre = world @ face.calc_center_median()
            nearest = tree.find_nearest(centre)
            if nearest[1] is not None and (turn @ face.normal).dot(nearest[1]) < 0.0:
                flip.append(face)
        if flip:
            bmesh.ops.reverse_faces(bm, faces=flip)
            bm.to_mesh(high.data)
            turned += len(flip)
        bm.free()
    return turned


# ---------------------------------------------------------------------------------------------- the low shape

def _make_shape(verts, tris, form, segments, rings, name, collection, foot=None):
    """A dome (or ball) whose every point is pulled in from outside along a ray towards the thing's middle until it
    meets the thing: it hugs the outline, smoothed a little and kept just outside the tips the rays found."""
    low, high = verts.min(axis=0), verts.max(axis=0)
    half = numpy.maximum((high - low) / 2.0, 0.02)
    middle = (low + high) / 2.0
    foot = float(low[2]) if foot is None else float(foot)        # a part's foot is its root (leaves may hang below it)
    tree = BVHTree.FromPolygons(verts.tolist(), tris.tolist(), all_triangles=True)
    if form == 'dome':
        aim = Vector((middle[0], middle[1], foot))
        heights = [0.5 * math.pi * k / rings for k in range(rings)]              # elevations, the foot ring first
    else:
        aim = Vector(middle)
        heights = [-0.5 * math.pi + math.pi * (k + 1) / (rings + 1) for k in range(rings)]
    grid_points, grid_t = [], []
    for e in heights:
        row_p, row_t = [], []
        for s in range(segments):
            a = 2.0 * math.pi * s / segments
            reach = Vector((half[0] * math.cos(e) * math.cos(a), half[1] * math.cos(e) * math.sin(a),
                            (2.0 * half[2] if form == 'dome' else half[2]) * math.sin(e))) * 1.6
            target = aim.copy()
            if form == 'dome' and e == 0.0:
                target.z += 0.03 * 2.0 * half[2]                                  # the foot ring: just above the ground
            start = target + reach
            direction = (target - start)
            length = direction.length
            direction.normalize()
            hit = tree.ray_cast(start, direction, length)
            row_p.append((start, direction, length))
            row_t.append(hit[3] if hit[0] is not None else None)
        grid_points.append(row_p)
        grid_t.append(row_t)
    # rays that found nothing take their neighbours' depth; then smooth, keeping the shape outside the tips found
    t = numpy.array([[v if v is not None else numpy.nan for v in row] for row in grid_t])
    raw_missing = numpy.isnan(t)
    for _ in range(40):
        if not numpy.isnan(t).any():
            break
        padded = numpy.pad(t, ((1, 1), (0, 0)), mode='edge')
        near = numpy.stack([numpy.roll(t, 1, axis=1), numpy.roll(t, -1, axis=1), padded[:-2], padded[2:]])
        fill = numpy.nanmean(numpy.where(numpy.isnan(near), numpy.nan, near), axis=0)
        t = numpy.where(numpy.isnan(t) & ~numpy.isnan(fill), fill, t)
    t = numpy.where(numpy.isnan(t), numpy.nanmax(t) if not numpy.isnan(t).all() else 0.0, t)
    raw = t.copy()
    for _ in range(2):
        padded = numpy.pad(t, ((1, 1), (0, 0)), mode='edge')
        t = 0.4 * t + 0.15 * (numpy.roll(t, 1, axis=1) + numpy.roll(t, -1, axis=1) + padded[:-2] + padded[2:])
    t = numpy.minimum(t, raw + 0.01)
    points = []
    for r, row in enumerate(grid_points):
        for s, (start, direction, length) in enumerate(row):
            p = start + direction * (float(t[r, s]) - 0.01)
            if form == 'dome' and r == 0:
                p.z = foot
            points.append(p)
    # the pole(s)
    top_start = aim + Vector((0.0, 0.0, (4.0 if form == 'dome' else 2.0) * half[2] + 0.1))
    hit = tree.ray_cast(top_start, Vector((0.0, 0.0, -1.0)), (top_start - aim).length)
    top = (hit[0] + Vector((0.0, 0.0, 0.01))) if hit[0] is not None else Vector((aim.x, aim.y, float(high[2])))
    points.append(top)
    faces = []
    count = len(heights)
    for r in range(count - 1):
        for s in range(segments):
            a, b = r * segments + s, r * segments + (s + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    top_index = len(points) - 1
    last = (count - 1) * segments
    for s in range(segments):
        faces.append((last + s, last + (s + 1) % segments, top_index))
    if form == 'ball':
        bottom_start = aim - Vector((0.0, 0.0, 2.0 * half[2] + 0.1))
        hit = tree.ray_cast(bottom_start, Vector((0.0, 0.0, 1.0)), (bottom_start - aim).length)
        points.append((hit[0] - Vector((0.0, 0.0, 0.01))) if hit[0] is not None else Vector((aim.x, aim.y, float(low[2]))))
        bottom_index = len(points) - 1
        for s in range(segments):
            faces.append(((s + 1) % segments, s, bottom_index))
    # one seamless UV island: the shape seen from its top pole, each point as far from the middle of the picture as
    # it is from the pole along the shape (no seams, so the relief cannot crack and the normal picture has no edges)
    along = [[0.0] * segments for _ in range(count)]
    for s in range(segments):
        before = top
        run = 0.0
        for r in range(count - 1, -1, -1):
            run += (points[r * segments + s] - before).length
            along[r][s] = run
            before = points[r * segments + s]
    longest = max(along[0])
    if form == 'ball':
        longest = max(longest, max(along[0][s] + (points[s] - points[-1]).length for s in range(segments)))

    def spot(r, s, run=None):
        a = 2.0 * math.pi * s / segments
        k = (along[r][s] if run is None else run) / longest * 0.485
        return (0.5 + k * math.cos(a), 0.5 + k * math.sin(a))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(p) for p in points], [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    for face in mesh.polygons:
        ids = list(face.vertices)
        for vertex in ids:
            if vertex == top_index:
                place = (0.5, 0.5)
            elif form == 'ball' and vertex == len(points) - 1:
                others = [v for v in ids if v != vertex]
                s = min(v % segments for v in others) if abs(others[0] % segments - others[1] % segments) > 1 else \
                    (others[0] % segments + others[1] % segments) / 2.0
                a = 2.0 * math.pi * s / segments
                place = (0.5 + 0.485 * math.cos(a), 0.5 + 0.485 * math.sin(a))
            else:
                place = spot(vertex // segments, vertex % segments)
            uv.data[face.loop_start + ids.index(vertex)].uv = place
    mesh.shade_smooth()
    shape = bpy.data.objects.new(name, mesh)
    collection.objects.link(shape)
    shape['bake_rays_missed'] = int(raw_missing.sum())
    return shape


def _unwrap(shape):
    """The shape's UV map: the made shapes have one; a shape you give must bring its own."""
    if not shape.data.uv_layers:
        raise ValueError('bake_to_pbr: the shape %r has no UV map: unwrap it first, or let the tool make the shape' % shape.name)
    return shape.data.uv_layers.active.name


# ---------------------------------------------------------------------------------------------- baking

def _image(name, size, colour=(0.0, 0.0, 0.0, 0.0)):
    image = bpy.data.images.new(name, size, size, alpha=True, float_buffer=True)
    image.generated_color = colour
    image.colorspace_settings.name = 'Non-Color'
    return image


def _pixels(image):
    size = image.size
    data = numpy.empty(size[0] * size[1] * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    return data.reshape(size[1], size[0], 4)


def _emission_material(name, kind, low, span):
    """A material that shines its position (scaled into 0..1 over the box low..low+span) or its normal (into 0..1)."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new('ShaderNodeOutputMaterial')
    shine = nodes.new('ShaderNodeEmission')
    geometry = nodes.new('ShaderNodeNewGeometry')
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY_ADD'
    if kind == 'position':
        links.new(geometry.outputs['Position'], scale.inputs[0])
        scale.inputs[1].default_value = tuple(1.0 / s for s in span)
        scale.inputs[2].default_value = tuple(-l / s for l, s in zip(low, span))
    else:
        links.new(geometry.outputs['Normal'], scale.inputs[0])
        scale.inputs[1].default_value = (0.5, 0.5, 0.5)
        scale.inputs[2].default_value = (0.5, 0.5, 0.5)
    links.new(scale.outputs[0], shine.inputs['Color'])
    shine.inputs['Strength'].default_value = 1.0
    links.new(shine.outputs[0], out.inputs['Surface'])
    return material


def _bake(scene, shape, highs, kind, image, reach, depth, margin, pass_filter=None, from_highs=True):
    material = shape.data.materials[0]
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    for other in material.node_tree.nodes:
        other.select = False
    node.select = True
    material.node_tree.nodes.active = node
    chosen = ([shape] + list(highs)) if from_highs else [shape]
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0], active_object=shape, object=shape,
                                   selected_objects=chosen, selected_editable_objects=chosen):
        result = bpy.ops.object.bake(type=kind, pass_filter=pass_filter or set(), use_selected_to_active=from_highs,
                                     cage_extrusion=reach, max_ray_distance=reach + depth, margin=margin,
                                     margin_type='EXTEND', normal_space='TANGENT', use_clear=False,
                                     target='IMAGE_TEXTURES', save_mode='INTERNAL')
    material.node_tree.nodes.remove(node)
    if 'FINISHED' not in result:
        raise RuntimeError('bake_to_pbr: the %s bake did not finish (%s)' % (kind, result))


def _write_png(path, rgba, channels, bits):
    """Writes rows of 0..1 numbers (bottom row first, as Blender keeps them) as a PNG of 1 (grey), 3 or 4 channels."""
    data = numpy.clip(rgba[::-1, :, :channels], 0.0, 1.0)
    height, width = data.shape[:2]
    if bits == 16:
        raw = numpy.round(data * 65535.0).astype('>u2').reshape(height, width * channels)
        rows = raw.view(numpy.uint8).reshape(height, width * channels * 2)
    else:
        rows = numpy.round(data * 255.0).astype(numpy.uint8).reshape(height, width * channels)
    body = b''.join(b'\x00' + rows[y].tobytes() for y in range(height))
    kind = {1: 0, 3: 2, 4: 6}[channels]

    def chunk(tag, payload):
        return struct.pack('>I', len(payload)) + tag + payload + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff)
    with open(path, 'wb') as handle:
        handle.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, bits, kind, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(body, 9)) + chunk(b'IEND', b''))
    return path


def _to_srgb(linear):
    linear = numpy.clip(linear, 0.0, 1.0)
    return numpy.where(linear <= 0.0031308, linear * 12.92, 1.055 * numpy.power(linear, 1.0 / 2.4) - 0.055)


def _fill(values, known, inside, rounds=96):
    """Fills the pixels inside the shape's picture where the projection found nothing (`known` False) from the found
    pixels round them, ring by ring, so no black holes are left (most lie at a dome's foot, below the lowest leaves)."""
    values = numpy.where(known[..., None], values, 0.0).astype(numpy.float32)
    have = known.astype(numpy.float32)
    for _ in range(rounds):
        need = inside & (have < 0.5)
        if not need.any():
            break
        total = numpy.zeros_like(values)
        count = numpy.zeros_like(have)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                total += numpy.roll(numpy.roll(values * have[..., None], dy, axis=0), dx, axis=1)
                count += numpy.roll(numpy.roll(have, dy, axis=0), dx, axis=1)
        newly = need & (count > 0)
        values[newly] = total[newly] / count[newly][:, None]
        have[newly] = 1.0
    return values


def _baked_material(name, pictures, uv_name, lit_through=0.0):
    material = bpy.data.materials.new('BAKED • ' + name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes['Principled BSDF']
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = uv_name

    def picture(label, image, x, y):
        node = nodes.new('ShaderNodeTexImage')
        node.name = node.label = label
        node.image = image
        node.location = (x, y)
        links.new(uv.outputs['UV'], node.inputs['Vector'])
        return node
    colour = picture('Colour picture', pictures['colour'], -700, 400)
    links.new(colour.outputs['Color'], principled.inputs['Base Color'])
    rough = picture('Roughness picture', pictures['roughness'], -700, 100)
    links.new(rough.outputs['Color'], principled.inputs['Roughness'])
    normal = picture('Normal picture', pictures['normal'], -700, -200)
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.name = 'Normal map'
    normal_map.uv_map = uv_name
    links.new(normal.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    picture('Height picture', pictures['height'], -700, -500)
    principled.inputs['Specular IOR Level'].default_value = 0.25
    if lit_through > 0:
        # leaves and petals let light through: the baked colour, lit from behind too
        through = nodes.new('ShaderNodeBsdfTranslucent')
        through.name = 'Lit through'
        links.new(colour.outputs['Color'], through.inputs['Color'])
        mix = nodes.new('ShaderNodeMixShader')
        mix.name = 'Lit through mix'
        mix.inputs['Fac'].default_value = lit_through
        out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        links.new(principled.outputs['BSDF'], mix.inputs[1])
        links.new(through.outputs['BSDF'], mix.inputs[2])
        links.new(mix.outputs['Shader'], out.inputs['Surface'])
    material.diffuse_color = tuple(_pixels(pictures['colour'])[..., :3].reshape(-1, 3).mean(axis=0)) + (1.0,)
    return material


def bake(objects, shape=None, form='dome', segments=32, rings=10, size=1024, reach=0.06, depth=0.25, relief=True,
         relief_detail=3, lit_through=0.0, bits=8, samples=2, folder=None, name=None, collection=None):
    """Bakes `objects` onto a low shape and returns the shape with its baked material (see the file's head)."""
    started = time.time()
    if form not in ('dome', 'ball'):
        raise ValueError("bake_to_pbr form is 'dome' or 'ball', not %r" % (form,))
    size = int(size)
    if not 64 <= size <= 8192:
        raise ValueError('bake_to_pbr size is 64 to 8192 pixels, not %r' % (size,))
    if bits not in (8, 16):
        raise ValueError('bake_to_pbr bits is 8 or 16, not %r' % (bits,))
    segments, rings = int(segments), int(rings)
    if segments < 6 or rings < 3:
        raise ValueError('bake_to_pbr needs at least 6 segments and 3 rings')
    given_scene = bpy.context.scene
    bpy.context.view_layer.update()
    sources = _sources(objects)
    name = name or ((objects.name if isinstance(objects, bpy.types.Object) else sources[0].name) + ' • baked')
    target = collection or given_scene.collection
    work = bpy.data.scenes.new('bake_to_pbr • work')
    work.render.engine = 'CYCLES'
    work.cycles.device = 'CPU'
    work.cycles.samples = int(samples)
    work.cycles.use_denoising = False
    made_images, made_materials = [], []
    try:
        highs, faces, copies = _high_copies(sources, work)
        made_materials += copies
        verts, tris = _world_triangles(highs)
        if shape is None:
            given = [objects] if isinstance(objects, bpy.types.Object) else list(objects)
            roots = [o.matrix_world.translation.z for o in given if o.type == 'EMPTY']
            foot = min(roots) if roots else None          # a part's foot is its root; other things stand on their lowest point
            shape = _make_shape(verts, tris, form, segments, rings, name, work.collection, foot)
        else:
            if shape.type != 'MESH':
                raise ValueError('bake_to_pbr shape must be a mesh object, not %s' % shape.type)
            work.collection.objects.link(shape)
        uv_name = _unwrap(shape)
        turned = _face_out(highs, shape)
        low = verts.min(axis=0) - 0.5
        span = (verts.max(axis=0) + 0.5) - low
        holder = bpy.data.materials.new('bake_to_pbr • holder')
        holder.use_nodes = True
        made_materials.append(holder)
        shape.data.materials.clear()
        shape.data.materials.append(holder)
        margin = max(4, size // 128)
        images = {}
        # colour without light (alpha 0 where the projection finds nothing), roughness, normal
        images['colour'] = _image('bake colour', size)
        _bake(work, shape, highs, 'DIFFUSE', images['colour'], reach, depth, margin, {'COLOR'})
        images['roughness'] = _image('bake roughness', size)
        _bake(work, shape, highs, 'ROUGHNESS', images['roughness'], reach, depth, margin)
        images['normal'] = _image('bake normal', size, (0.5, 0.5, 1.0, 1.0))
        _bake(work, shape, highs, 'NORMAL', images['normal'], reach, depth, margin)
        # height: where the projection met the thing, against the shape's own place and facing, along its facing
        shine = _emission_material('bake_to_pbr • position', 'position', low, span)
        facing = _emission_material('bake_to_pbr • facing', 'normal', low, span)
        made_materials += [shine, facing]
        kept = {high.name: list(high.data.materials) for high in highs}
        for high in highs:
            for index in range(len(high.data.materials)):
                high.data.materials[index] = shine
            if not high.data.materials:
                high.data.materials.append(shine)
        met = _image('bake met', size)
        _bake(work, shape, highs, 'EMIT', met, reach, depth, margin)
        for high in highs:
            for index, material in enumerate(kept[high.name]):
                high.data.materials[index] = material
        own = _image('bake own place', size)
        shape.data.materials[0] = shine
        _bake(work, shape, highs, 'EMIT', own, reach, depth, 0, from_highs=False)
        own_facing = _image('bake own facing', size)
        shape.data.materials[0] = facing
        _bake(work, shape, highs, 'EMIT', own_facing, reach, depth, 0, from_highs=False)
        shape.data.materials[0] = holder
        made_images += [met, own, own_facing]
        met_px, own_px, facing_px = _pixels(met), _pixels(own), _pixels(own_facing)
        found = (_pixels(images['colour'])[..., 3] > 0.5) & (met_px[..., 3] > 0.5)
        inside = own_px[..., 3] > 0.5
        where_met = met_px[..., :3] * span + low
        where_own = own_px[..., :3] * span + low
        normal = facing_px[..., :3] * 2.0 - 1.0
        normal /= numpy.maximum(numpy.linalg.norm(normal, axis=2, keepdims=True), 1e-6)
        height = numpy.sum((where_met - where_own) * normal, axis=2)
        height = numpy.clip(height, -depth, reach)
        good = found & inside
        if good.any():
            low_h = float(numpy.percentile(height[good], 0.5))
            high_h = float(numpy.percentile(height[good], 99.8))
        else:
            low_h, high_h = -depth, 0.0
        height = _fill(height[..., None], good, inside)[..., 0]
        high_h = max(high_h, low_h + 1e-3)
        level = numpy.clip((height - low_h) / (high_h - low_h), 0.0, 1.0)
        # the pictures, written as PNG and loaded back as the material's pictures
        out_folder = folder or tempfile.mkdtemp(prefix='bake_to_pbr_')
        os.makedirs(out_folder, exist_ok=True)
        stem = name.replace(' • ', ' - ').replace('•', '-').replace('/', '-')
        colour_px = _pixels(images['colour'])
        colour_rgb = _fill(colour_px[..., :3], good, inside)
        colour_rgba = numpy.concatenate([_to_srgb(colour_rgb), good[..., None].astype(numpy.float32)], axis=2)
        normal_px = _fill(_pixels(images['normal'])[..., :3], good, inside)
        rough_px = _fill(_pixels(images['roughness'])[..., :1], good, inside)
        written = {
            'colour': _write_png(os.path.join(out_folder, stem + ' - colour.png'), colour_rgba, 4, 8),
            'normal': _write_png(os.path.join(out_folder, stem + ' - normal.png'), normal_px, 3, bits),
            'roughness': _write_png(os.path.join(out_folder, stem + ' - roughness.png'), rough_px, 1, 8),
            'height': _write_png(os.path.join(out_folder, stem + ' - height.png'), level[..., None], 1, bits),
        }
        made_images += list(images.values())
        pictures = {}
        for key, path in written.items():
            image = bpy.data.images.load(path, check_existing=False)
            image.name = 'BAKED • %s • %s' % (name, key)
            image.colorspace_settings.name = 'sRGB' if key == 'colour' else 'Non-Color'
            if key == 'colour':
                image.alpha_mode = 'CHANNEL_PACKED'
            if folder is None:
                image.pack()
            pictures[key] = image
        material = _baked_material(name, pictures, uv_name, float(lit_through))
        shape.data.materials.clear()
        shape.data.materials.append(material)
        if relief:
            detail = shape.modifiers.new('bake_to_pbr relief detail', 'SUBSURF')
            detail.subdivision_type = 'SIMPLE'
            detail.levels = detail.render_levels = int(relief_detail)
            texture = bpy.data.textures.new('BAKED • %s • height' % name, 'IMAGE')
            texture.image = pictures['height']
            texture.extension = 'EXTEND'
            lift = shape.modifiers.new('bake_to_pbr relief', 'DISPLACE')
            lift.texture = texture
            lift.texture_coords = 'UV'
            lift.uv_layer = uv_name
            lift.direction = 'NORMAL'
            lift.strength = high_h - low_h
            lift.mid_level = -low_h / (high_h - low_h)
        shape['baked_from_faces'] = int(faces)
        shape['baked_faces_turned'] = int(turned)
        shape['baked_height_low'] = low_h
        shape['baked_height_high'] = high_h
        shape['baked_pictures'] = [written[k] for k in PASSES] if folder else []
        shape['baked_found'] = float(good.sum() / max(1, inside.sum()))
        work.collection.objects.unlink(shape)
        if shape.name not in target.objects:
            target.objects.link(shape)
        for high in highs:
            mesh = high.data
            bpy.data.objects.remove(high, do_unlink=True)
            bpy.data.meshes.remove(mesh)
    finally:
        for image in made_images:
            if image.name in bpy.data.images:
                bpy.data.images.remove(image)
        for material in made_materials:
            if material.name in bpy.data.materials and material.users == 0:
                bpy.data.materials.remove(material)
        bpy.data.scenes.remove(work)
    shape['baked_seconds'] = round(time.time() - started, 1)
    return shape


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--blend', required=True, help='the .blend to open')
    parser.add_argument('--objects', action='append', required=True, help="an object's name (a part's root, or a mesh); repeat for more")
    parser.add_argument('--form', default='dome', choices=('dome', 'ball'))
    parser.add_argument('--size', type=int, default=1024)
    parser.add_argument('--reach', type=float, default=0.06)
    parser.add_argument('--depth', type=float, default=0.25)
    parser.add_argument('--no-relief', action='store_true', help='the plain shape with its normal picture only')
    parser.add_argument('--relief-detail', type=int, default=3)
    parser.add_argument('--lit-through', type=float, default=0.0, help='0 to 1; 0.3 for leaves and petals')
    parser.add_argument('--bits', type=int, default=8, choices=(8, 16), help="the normal and height pictures' depth")
    parser.add_argument('--folder', default=None, help='where the pictures are written (default: packed into the .blend)')
    parser.add_argument('--out', required=True, help='the .blend to save')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    chosen = []
    for typed in args.objects:
        if typed not in bpy.data.objects:
            raise SystemExit('no object called %r in %s' % (typed, args.blend))
        chosen.append(bpy.data.objects[typed])
    shape = bake(chosen, form=args.form, size=args.size, reach=args.reach, depth=args.depth, relief=not args.no_relief,
                 relief_detail=args.relief_detail, lit_through=args.lit_through, bits=args.bits, folder=args.folder)
    bpy.ops.wm.save_as_mainfile(filepath=args.out)
    print('baked %s: %d faces (from %d), %.1f s' % (shape.name, len(shape.data.polygons), shape['baked_from_faces'], shape['baked_seconds']))


if __name__ == '__main__':
    main()
