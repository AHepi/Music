"""
What this does: paints brushstrokes over a finished picture of a scene, using the Blender Studio's Brushstrokes Tools
(its node groups and brush pictures, loaded as data; none of the add-on's code is run).

  1. finds the big surfaces the camera sees (walls, plaster, ground, roofs, timber), and copies the faces of each that
     face the camera, lifted to where the visible skin is (in front of the ashlar, on top of the setts);
  2. covers each copy with the add-on's fill strokes, running along walls and across the ground;
  3. gives each stroke one colour: the finished picture's colour where the stroke starts (strokes that start behind
     something else are dropped, so a lamp post's colour is never smeared over the wall behind it);
  4. draws only the strokes, each glowing in its own colour, everything else hidden but still in front of what it
     hides; then lays them over the finished picture. Lit windows, lamps and flames can be kept clear of strokes.

    python3 paint_over.py -- SCENE.blend PICTURE.png OUT.png --resources RES.blend --styles STYLES.blend [options]
"""

import argparse
import math
import os
import sys
import time

import bpy
import bmesh
import numpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from PIL import Image, ImageFilter

ADDED = ('FACADE •', 'LAID •', 'DETAIL •', 'LOOK •', 'TIMBER •', 'PAINT •')
CARRIER_ROLES = {'wall', 'plaster', 'road', 'pavement', 'earth', 'roof', 'trim', 'wood', 'rock', 'sand', 'iron'}
STYLES = {
    'fat': 'BSBST-BS.Oil Paint.Brushstrokes.Fat (Loaded)',
    'dry': 'BSBST-BS.Oil Paint.Brushstrokes.Dry (Loaded)',
    'feathery': 'BSBST-BS.Oil Paint.Brushstrokes.Feathery',
    'streaky': 'BSBST-BS.Oil Paint.Brushstrokes.Streaky Dashes',
    'scrumble': 'BSBST-BS.Oil Paint.Patches.Dry Scrumble',
    'grunge': 'BSBST-BS.Oil Paint.Patches.Grunge',
}


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('scene')
    parser.add_argument('picture')
    parser.add_argument('out')
    parser.add_argument('--resources', required=True)
    parser.add_argument('--styles', required=True)
    parser.add_argument('--style', default='fat', choices=sorted(STYLES))
    parser.add_argument('--width', type=float, default=0.25, help='stroke width in metres')
    parser.add_argument('--length', type=float, default=1.2, help='stroke length in metres')
    parser.add_argument('--density', type=float, default=3.0, help='strokes per metre each way (per square metre: this squared)')
    parser.add_argument('--grow-far', type=float, default=0.0,
                        help='make strokes wider and longer with distance, so far strokes are not tiny on the canvas (0 off, 1 even on the canvas)')
    parser.add_argument('--protect-lights', type=float, default=1.0, help='keep lit windows, lamps and flames clear of strokes (0 off, 1 fully)')
    parser.add_argument('--opacity', type=float, default=1.0, help='how much the stroke layer covers the picture')
    parser.add_argument('--flow', default='along', choices=['along', 'up the walls', 'down the street'],
                        help='which way strokes run: along walls and across the ground; up the walls; or down the street on the ground')
    parser.add_argument('--wander', type=float, default=0.25, help='how much each stroke strays from the flow (the add-on\'s random flow)')
    parser.add_argument('--colour-blur', type=float, default=2.0, help='each stroke takes the picture\'s colour averaged over this many pixels')
    parser.add_argument('--relief', type=float, default=0.5, help='how much the brush\'s own streaks show inside each stroke (0 flat colour)')
    parser.add_argument('--variation', type=float, default=0.06, help='each stroke a little lighter or darker than the picture (0 none)')
    parser.add_argument('--start-at', type=float, default=0.0, help='no strokes nearer the camera than this many metres (the foreground stays as drawn)')
    parser.add_argument('--samples', type=int, default=32)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--min-share', type=float, default=0.002, help='surfaces taking less of the picture than this get no strokes')
    return parser.parse_args(argv)


def srgb_to_linear(c):
    return numpy.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def ray_grid(scene, depsgraph, columns=90):
    camera = scene.camera
    tr, br, bl, tl = [camera.matrix_world @ c for c in camera.data.view_frame(scene=scene)]
    origin = camera.matrix_world.translation
    rows = round(columns * scene.render.resolution_y / scene.render.resolution_x)
    for i in range(columns):
        a = (i + 0.5) / columns
        top, bottom = tl.lerp(tr, a), bl.lerp(br, a)
        for j in range(rows):
            yield origin, (top.lerp(bottom, (j + 0.5) / rows) - origin).normalized(), columns * rows


def carrier_for(name, scene, roads, pavements):
    """The builder's object that carries strokes for whatever the camera hit."""
    if name.startswith('FACADE • '):
        return name[len('FACADE • '):].split(' • ')[0]
    if name.startswith('LAID • sett'):
        return roads
    if name.startswith('LAID • flag'):
        return pavements
    if name.startswith('DETAIL • puddles'):
        return roads + pavements
    if name.startswith(ADDED) or '• laid' in name:
        return None
    return name


def pick_carriers(scene, depsgraph, min_share):
    roles = {o.name: o.get('place_role') for o in scene.objects if o.type == 'MESH'}
    roads = [n for n, r in roles.items() if r == 'road' and not n.startswith(ADDED)]
    pavements = [n for n, r in roles.items() if r == 'pavement' and not n.startswith(ADDED)]
    share = {}
    for origin, direction, total in ray_grid(scene, depsgraph):
        hit, _, _, _, obj, _ = scene.ray_cast(depsgraph, origin, direction, distance=2000.0)
        if not hit:
            continue
        carriers = carrier_for(obj.name, scene, roads, pavements)
        if carriers is None:
            continue
        for name in ([carriers] if isinstance(carriers, str) else carriers):
            share[name] = share.get(name, 0.0) + 1.0 / total / (1 if isinstance(carriers, str) else len(carriers))
    chosen = []
    for name, value in share.items():
        obj = scene.objects.get(name)
        if obj is None or obj.type != 'MESH' or value < min_share or roles.get(name) not in CARRIER_ROLES:
            continue
        chosen.append(obj)
    return chosen, share


def face_frame(normal, flow):
    """Two directions in a face's plane: 'along' (the way strokes run) and 'across'."""
    if abs(normal.z) > 0.7:
        along = Vector((1, 0, 0)) if flow != 'down the street' else Vector((0, 1, 0))
        along = (along - normal * along.dot(normal)).normalized()
    else:
        along = normal.cross(Vector((0, 0, 1))).normalized()
        if flow == 'up the walls':
            along = normal.cross(along).normalized()
    across = normal.cross(along).normalized()
    return along, across


def belongs_to(hit_name, obj):
    """Whether what a probe hit is the object itself or something the dressing laid for it."""
    name, role = obj.name, obj.get('place_role')
    if hit_name == name or hit_name.startswith(('FACADE • ' + name + ' •', 'TIMBER • ' + name + ' •', name + ' • laid')):
        return True
    if role in ('road', 'pavement', 'earth') and hit_name.startswith(('LAID •', 'DETAIL • puddles')):
        return True
    return False


def points_on(face, count, rng):
    """Points spread over a face (its triangles chosen by area)."""
    corners = [v.co for v in face.verts]
    triangles = [(corners[0], corners[i], corners[i + 1]) for i in range(1, len(corners) - 1)]
    areas = numpy.array([max(1e-9, (b - a).cross(c - a).length / 2) for a, b, c in triangles])
    picks = rng.choice(len(triangles), size=count, p=areas / areas.sum())
    points = []
    for k in picks:
        a, b, c = triangles[k]
        u, v = rng.random(), rng.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        points.append(a + (b - a) * u + (c - a) * v)
    return points


def lifted_copy(obj, scene, depsgraph, camera_spot, flow, spacing=1.0):
    """
    The faces of obj that face the camera, each moved out along its normal to where the camera's visible surface is,
    with a flat map running the way the strokes should, and flow lines on each face in that direction (the add-on
    takes the strokes' direction from flow lines; without them every stroke points a random way).
    """
    source = bmesh.new()
    source.from_mesh(obj.data)
    source.transform(obj.matrix_world)
    source.normal_update()
    probe_rng = numpy.random.default_rng(len(obj.name))
    out = bmesh.new()
    uv = out.loops.layers.uv.new('pp_flow')
    lines = []
    for face in source.faces:
        centre = face.calc_center_median()
        normal = face.normal.copy()
        if (camera_spot - centre).dot(normal) <= 0 or face.calc_area() < 0.05:
            continue
        # where is this object's own visible skin? Probe from 1 m out at points spread over the face, and count only
        # what belongs to the object (itself, its ashlar, its laid setts or flags, its puddles): windows, timbers and
        # signs in front of it are other things, which hide its strokes rather than lift them
        lifts = []
        for point in points_on(face, 25, probe_rng):
            start = point + normal * 1.0
            hit, location, _, _, hit_obj, _ = scene.ray_cast(depsgraph, start, -normal, distance=1.2)
            if hit and hit_obj is not None and belongs_to(hit_obj.name, obj):
                lifts.append(max(0.0, min(0.5, 1.0 - (location - start).length)))
        lift = (float(numpy.median(lifts)) if lifts else 0.0) + 0.008
        verts = [out.verts.new(v.co + normal * lift) for v in face.verts]
        new_face = out.faces.new(verts)
        along, across = face_frame(normal, flow)
        for loop in new_face.loops:
            loop[uv].uv = (loop.vert.co.dot(along), loop.vert.co.dot(across))
        # flow lines: across the face every `spacing` metres, clipped to the face's outline
        outline = [(v.co.dot(along), v.co.dot(across)) for v in verts]
        depth = verts[0].co.dot(normal)
        low, high = min(b for a, b in outline), max(b for a, b in outline)
        level = low + spacing * 0.5
        while level < high:
            crossings = []
            for (a0, b0), (a1, b1) in zip(outline, outline[1:] + outline[:1]):
                if (b0 - level) * (b1 - level) < 0:
                    crossings.append(a0 + (a1 - a0) * (level - b0) / (b1 - b0))
            if len(crossings) >= 2:
                a_start, a_end = min(crossings) + 0.05, max(crossings) - 0.05
                if a_end - a_start > 0.3:
                    lines.append([along * a + across * level + normal * depth for a in (a_start, a_end)])
            level += spacing
    source.free()
    if not out.faces or not lines:
        out.free()
        return None, None
    mesh = bpy.data.meshes.new('PAINT • carrier ' + obj.name)
    out.to_mesh(mesh)
    out.free()
    carrier = bpy.data.objects.new(mesh.name, mesh)
    scene.collection.objects.link(carrier)
    curves = bpy.data.hair_curves.new('PAINT • flow ' + obj.name)
    curves.add_curves([2] * len(lines))
    curves.attributes['position'].data.foreach_set('vector', [c for line in lines for p in line for c in p])
    flow_object = bpy.data.objects.new(curves.name, curves)
    scene.collection.objects.link(flow_object)
    pre = flow_object.modifiers.new('Pre-Processing', 'NODES')
    pre.node_group = bpy.data.node_groups['.brushstroke_tools.pre_processing']
    pre['Socket_2'] = carrier
    pre['Socket_3'] = False
    flow_object.hide_render = True
    return carrier, flow_object


def load_add_on_data(resources, styles, style, relief=0.5):
    with bpy.data.libraries.load(resources, link=False) as (data_from, data_to):
        data_to.node_groups = ['.brushstroke_tools.geometry_input', '.brushstroke_tools.mask_surface', '.brushstroke_tools.surface_fill',
                               '.brushstroke_tools.pre_processing']
        data_to.materials = ['Brush Material']
    with bpy.data.libraries.load(styles, link=False) as (data_from, data_to):
        data_to.node_groups = [STYLES[style]]
    material = bpy.data.materials['Brush Material']
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes['Brush Style'].node_tree = bpy.data.node_groups[STYLES[style]]
    # the strokes glow in their own colour (the finished picture's colour), so the light is not added twice
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 1.0
    streaks = nodes.new('ShaderNodeMath')
    streaks.operation = 'MULTIPLY_ADD'
    links.new(nodes['Reroute'].outputs[0], streaks.inputs[0])
    streaks.inputs[1].default_value = 0.5 * relief
    streaks.inputs[2].default_value = 1.0 - 0.3 * relief
    shaded = nodes.new('ShaderNodeVectorMath')
    shaded.operation = 'SCALE'
    links.new(nodes['Color Out'].outputs[0], shaded.inputs[0])
    links.new(streaks.outputs[0], shaded.inputs['Scale'])
    links.new(shaded.outputs[0], emission.inputs['Color'])
    for link in list(links):
        if link.to_node == nodes['Paint Surface']:
            links.remove(link)
    links.new(emission.outputs[0], nodes['Paint Surface'].inputs[0])
    missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not os.path.exists(bpy.path.abspath(i.filepath))]
    return material, missing


def add_strokes(carrier, flow_object, material, args, index, camera_spot):
    strokes = bpy.data.objects.new('PAINT • strokes ' + carrier.name, bpy.data.meshes.new('PAINT • strokes ' + carrier.name))
    bpy.context.scene.collection.objects.link(strokes)
    first = strokes.modifiers.new('Surface Input', 'NODES')
    first.node_group = bpy.data.node_groups['.brushstroke_tools.geometry_input']
    first['Socket_2'] = carrier
    masking = strokes.modifiers.new('Masking', 'NODES')
    masking.node_group = bpy.data.node_groups['.brushstroke_tools.mask_surface']
    fill = strokes.modifiers.new('Brushstrokes', 'NODES')
    fill.node_group = bpy.data.node_groups['.brushstroke_tools.surface_fill']
    fill['Socket_3_use_attribute'] = True
    fill['Socket_3_attribute_name'] = 'pp_flow'
    grow = 1.0
    if args.grow_far > 0:
        # strokes on far surfaces made bigger, so they are not specks on the canvas
        distance = (camera_spot - carrier.matrix_world @ (sum((Vector(c) for c in carrier.bound_box), Vector()) / 8)).length
        grow = 1.0 + args.grow_far * max(0.0, distance / 12.0 - 1.0)
    fill['Socket_7'] = args.density / grow
    fill['Socket_11'] = args.length * grow
    fill['Socket_13'] = args.width * grow
    fill['Socket_14'] = 0.004
    fill['Socket_27'] = False
    fill['Socket_9'] = args.seed * 101 + index
    fill['Socket_12'] = material
    fill['Socket_2'] = flow_object
    fill['Socket_63'] = args.wander
    strokes.data.materials.append(material)
    return strokes


def main():
    args = parse()
    started = time.time()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.scene))
    scene = bpy.context.scene
    picture = numpy.asarray(Image.open(args.picture).convert('RGB'), dtype=numpy.float32) / 255.0
    softened = numpy.asarray(Image.open(args.picture).convert('RGB').filter(ImageFilter.GaussianBlur(args.colour_blur)), dtype=numpy.float32) / 255.0 \
        if args.colour_blur > 0 else picture
    height, width = picture.shape[:2]
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    camera = scene.camera
    camera_spot = camera.matrix_world.translation.copy()
    material, missing = load_add_on_data(args.resources, args.styles, args.style, args.relief)
    if missing:
        print('WARNING: brush pictures not found:', missing)
    chosen, share = pick_carriers(scene, depsgraph, args.min_share)
    print('surfaces with strokes:', len(chosen), ', '.join('%s %.1f%%' % (o.name, 100 * share[o.name]) for o in chosen))
    pairs = [p for p in (lifted_copy(o, scene, depsgraph, camera_spot, args.flow) for o in chosen) if p[0] is not None]
    carriers = [c for c, f in pairs] + [f for c, f in pairs]
    strokes_objects = [add_strokes(c, f, material, args, i, camera_spot) for i, (c, f) in enumerate(pairs)]
    for c in carriers:
        c.hide_render = True
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    meshes = []
    for obj in strokes_objects:
        made = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
        meshes.append(made)
    for obj in strokes_objects + carriers:
        bpy.data.objects.remove(obj, do_unlink=True)
    print('strokes made in %.1f s' % (time.time() - started))
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total = kept_total = 0
    variation_rng = numpy.random.default_rng(args.seed)
    painted = []
    for made in meshes:
        if not made.polygons:
            continue
        stroke_of_face = numpy.zeros(len(made.polygons), dtype=numpy.int64)
        made.attributes['stroke_index'].data.foreach_get('value', stroke_of_face)
        root = numpy.zeros(len(made.vertices) * 3, dtype=numpy.float32)
        made.attributes['brush_stroke.position'].data.foreach_get('vector', root)
        root = root.reshape(-1, 3)
        loop_start = numpy.zeros(len(made.polygons), dtype=numpy.int64)
        made.polygons.foreach_get('loop_start', loop_start)
        corner_vert = numpy.zeros(len(made.loops), dtype=numpy.int64)
        made.loops.foreach_get('vertex_index', corner_vert)
        first_vertex = corner_vert[loop_start]
        strokes, first_face = numpy.unique(stroke_of_face, return_index=True)
        positions = numpy.zeros(len(made.vertices) * 3, dtype=numpy.float32)
        made.vertices.foreach_get('co', positions)
        positions = positions.reshape(-1, 3)
        face_centres = positions[first_vertex]
        sums = numpy.zeros((int(stroke_of_face.max()) + 1, 3))
        counts = numpy.zeros(int(stroke_of_face.max()) + 1)
        numpy.add.at(sums, stroke_of_face, face_centres)
        numpy.add.at(counts, stroke_of_face, 1)
        middles = sums / numpy.maximum(counts, 1)[:, None]
        colour_of_stroke = {}
        keep = set()
        for stroke, face in zip(strokes, first_face):
            start_point = Vector(root[first_vertex[face]])
            point = Vector(middles[stroke])
            view = world_to_camera_view(scene, camera, point)
            total += 1
            if view.z <= 0 or not (0 <= view.x <= 1 and 0 <= view.y <= 1):
                continue
            to_point = point - camera_spot
            if to_point.length < args.start_at:
                continue
            hit, location, _, _, _, _ = scene.ray_cast(depsgraph, camera_spot, to_point.normalized(), distance=to_point.length + 1.0)
            if hit and (location - camera_spot).length < to_point.length - 0.04:
                continue                    # the stroke starts behind something: its colour in the picture is not its own
            x = min(width - 1.0, max(0.0, view.x * width - 0.5))
            y = min(height - 1.0, max(0.0, (1.0 - view.y) * height - 0.5))
            x0, y0 = int(x), int(y)
            x1, y1 = min(x0 + 1, width - 1), min(y0 + 1, height - 1)
            fx, fy = x - x0, y - y0
            colour = (softened[y0, x0] * (1 - fx) * (1 - fy) + softened[y0, x1] * fx * (1 - fy)
                      + softened[y1, x0] * (1 - fx) * fy + softened[y1, x1] * fx * fy)
            if colour[0] > colour[2] * 1.3 and float(colour @ numpy.array([0.2126, 0.7152, 0.0722])) > 0.42:
                continue                    # never paint with a lit window's or a lamp's colour: it smears light over the walls
            jitter = 1.0 + args.variation * (2.0 * variation_rng.random() - 1.0)
            colour_of_stroke[stroke] = srgb_to_linear(numpy.clip(colour * jitter, 0.0, 1.0))
            keep.add(int(stroke))
        kept_total += len(keep)
        print('   %-58s kept %5d of %5d' % (made.name[:58], len(keep), len(strokes)))
        # drop the faces of strokes that were not kept
        tool = bmesh.new()
        tool.from_mesh(made)
        layer = tool.faces.layers.int.get('stroke_index')
        doomed = [f for f in tool.faces if f[layer] not in keep]
        bmesh.ops.delete(tool, geom=doomed, context='FACES')
        tool.to_mesh(made)
        tool.free()
        if not made.polygons:
            continue
        stroke_of_face = numpy.zeros(len(made.polygons), dtype=numpy.int64)
        made.attributes['stroke_index'].data.foreach_get('value', stroke_of_face)
        loop_start = numpy.zeros(len(made.polygons), dtype=numpy.int64)
        made.polygons.foreach_get('loop_start', loop_start)
        loop_total = numpy.zeros(len(made.polygons), dtype=numpy.int64)
        made.polygons.foreach_get('loop_total', loop_total)
        corner_vert = numpy.zeros(len(made.loops), dtype=numpy.int64)
        made.loops.foreach_get('vertex_index', corner_vert)
        colours = numpy.zeros((len(made.vertices), 4), dtype=numpy.float32)
        colours[:, 3] = 1.0
        known = numpy.array(sorted(colour_of_stroke), dtype=numpy.int64)
        table = numpy.array([colour_of_stroke[k] for k in known], dtype=numpy.float32)
        face_colour = table[numpy.searchsorted(known, stroke_of_face)]
        face_of_corner = numpy.repeat(numpy.arange(len(made.polygons)), loop_total)
        colours[corner_vert, :3] = face_colour[face_of_corner]
        attribute = made.attributes.get('brush_stroke.color')
        attribute.data.foreach_set('color', colours.ravel())
        obj = bpy.data.objects.new(made.name, made)
        scene.collection.objects.link(obj)
        painted.append(obj)
    print('strokes kept %d of %d (%.1f s)' % (kept_total, total, time.time() - started))
    # draw only the strokes: everything else hidden but still in front of what it hides
    for obj in scene.objects:
        if obj in painted:
            continue
        if obj.type == 'MESH':
            role = obj.get('place_role')
            if role == 'smoke' or any(slot.material and slot.material.name.startswith('Chimney smoke') for slot in obj.material_slots):
                obj.hide_render = True
            else:
                obj.is_holdout = True
        elif obj.type in ('VOLUME', 'CURVES', 'POINTCLOUD'):
            obj.hide_render = True
    scene.world = None
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0
    scene.cycles.transparent_max_bounces = 256
    scene.render.film_transparent = True
    scene.render.use_compositing = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    layer_path = os.path.splitext(os.path.abspath(args.out))[0] + ' - strokes only.png'
    scene.render.filepath = layer_path
    drawn = time.time()
    bpy.ops.render.render(write_still=True)
    print('strokes drawn in %.1f s' % (time.time() - drawn))
    layer = numpy.asarray(Image.open(layer_path).convert('RGBA'), dtype=numpy.float32) / 255.0
    alpha = layer[:, :, 3:4] * args.opacity
    if args.protect_lights > 0:
        luminance = picture @ numpy.array([0.2126, 0.7152, 0.0722], dtype=numpy.float32)
        warm = (picture[:, :, 0] > picture[:, :, 2] * 1.3) & (luminance > 0.42)
        mask = Image.fromarray((warm * 255).astype(numpy.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))
        keep_clear = numpy.asarray(mask, dtype=numpy.float32)[:, :, None] / 255.0
        alpha = alpha * (1.0 - args.protect_lights * keep_clear)
    result = picture * (1 - alpha) + layer[:, :, :3] * alpha
    Image.fromarray((numpy.clip(result, 0, 1) * 255 + 0.5).astype(numpy.uint8)).save(args.out)
    print('wrote %s in %.1f s' % (args.out, time.time() - started))


if __name__ == '__main__':
    main()
