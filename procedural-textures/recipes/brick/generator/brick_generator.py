# What this does (plain words): the Blender half of the brick generator. It reads a "painted tile" description file (see shape_stack.py
# for the format), builds the painted shapes as REAL flat geometry in Blender (one little mesh piece per patch of paint, stacked a tiny
# bit higher one after the other, like layers of paint), looks straight down on them with a 1 x 1 camera, and writes the picture set:
# colour.png, height.png (16-bit), normal.png (OpenGL: green = up), roughness.png, metallic.png and ao.png, all 1254 dots square by default.
# It never opens the reference pictures: only the description.
#
# How the pictures are made:
#   colour     = what the camera sees (each shape glows with its own palette colour; the nearest-to-camera shape wins)
#   roughness  = the same, but each shape glows with its palette entry's roughness number
#   height     = made from the colour with the rule written in the description ("maps": grey -> light blur -> tone curve), the same rule that
#                made the reference height from the reference colour (analysis/derivation_ceiling.py)
#   normal     = slope of the height (Sobel), strength from the description
#   ao         = how hemmed-in a dot is, from the height (a cheap blur-difference, not a ray-traced one)
#   metallic   = zero everywhere (bricks and mortar are not metal)
#
# Use (command line):
#   blender -b --disable-autoexec -t 2 --python brick_generator.py -- DESCRIPTION.json OUT_FOLDER [--size 1254] [--samples 16]
#           [--shift 627] [--height-mode derived|hybrid]
#   --shift N moves the whole painting N dots right and down (wrapping round) - used for the half-tile seamless test.
# Use (inside Blender):  import brick_generator as bg ;  bg.bake_description(description_dict, 'out_folder', size=1254)
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402  (the shared photo-booth: scene, camera, saving pictures)
import derive_maps as dm  # noqa: E402
import shape_stack as ss  # noqa: E402

try:
    import mathutils.geometry as mug
    from mathutils import Vector
except Exception:  # pragma: no cover
    mug = None


def srgb_to_linear(values01):
    v = np.asarray(values01, float)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------------------------------------------- stack -> mesh
def shape_triangles(points, convex, holes=None):
    """Triangles (index triples into this shape's own points, holes' points counted after the outer ones) that fill the shape."""
    n = len(points)
    if (convex or n <= 3) and not holes:
        return [(0, i, i + 1) for i in range(1, n - 1)]
    rings = [[Vector((x, y, 0.0)) for x, y in points]] + [[Vector((x, y, 0.0)) for x, y in h] for h in (holes or [])]
    triangles = mug.tessellate_polygon(rings)
    return [tuple(t) for t in triangles]


def build_mesh(stack, palette_rgb, palette_roughness, size, tile=None, z_step=2.0e-5):
    """One mesh holding every shape; shape number i sits at height (i * z_step) so later shapes cover earlier ones.
    Returns the object and the highest z."""
    tile = float(tile or ss.TILE)                              # the description's tile size in dots (1254 for one tile, 2508 for a 2 x 2 area)
    vertex_blocks, faces, colours, roughs = [], [], [], []
    offset = 0
    linear = srgb_to_linear(palette_rgb / 255.0)
    for index, shape in enumerate(stack):
        pts = shape['points']
        if shape.get('holes'):
            pts = np.vstack([pts] + list(shape['holes']))
        n = len(pts)
        z = index * z_step
        vertex_blocks.append(np.column_stack([pts[:, 0] / tile, 1.0 - pts[:, 1] / tile, np.full(n, z)]))
        for t in shape_triangles(shape['points'], shape['convex'], shape.get('holes')):
            faces.append((offset + t[0], offset + t[1], offset + t[2]))
        c = linear[shape['colour']]
        colours.append(np.tile(np.append(c, 1.0), (n, 1)))
        roughs.append(np.full(n, palette_roughness[shape['colour']]))
        offset += n
    vertices = np.concatenate(vertex_blocks)
    mesh = bpy.data.meshes.new('paint')
    mesh.vertices.add(len(vertices))
    mesh.vertices.foreach_set('co', vertices.astype(np.float32).ravel())
    face_array = np.array(faces, dtype=np.int32)
    mesh.loops.add(len(face_array) * 3)
    mesh.loops.foreach_set('vertex_index', face_array.ravel())
    mesh.polygons.add(len(face_array))
    mesh.polygons.foreach_set('loop_start', np.arange(0, len(face_array) * 3, 3, dtype=np.int32))
    mesh.polygons.foreach_set('loop_total', np.full(len(face_array), 3, dtype=np.int32))
    mesh.update(calc_edges=True)
    colour_layer = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    colour_layer.data.foreach_set('color', np.concatenate(colours).astype(np.float32).ravel())
    rough_layer = mesh.attributes.new('rough', 'FLOAT', 'POINT')
    rough_layer.data.foreach_set('value', np.concatenate(roughs).astype(np.float32))
    obj = bpy.data.objects.new('paint', mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, (len(stack) + 1) * z_step


def channel_material(name, attribute, is_colour, grain=None, tile_dots=1254.0):
    """A material that simply glows with the value stored on the shapes (no lighting): the colour, or the roughness number.
    grain (optional, colour only) = {'amount': 0.10, 'seed': 3}: a very fine noise that makes every dot a little lighter or darker
    (amount 0.10 = a typical change of 10 per cent of the brightness). It adds the tiny dot-to-dot
    variation of a painted surface; it does NOT help the dot-for-dot score (random grain cannot match the reference's grain), it helps the
    'same kind of surface' score."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    attr = tree.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = attribute
    attr.attribute_type = 'GEOMETRY'
    emit = tree.nodes.new('ShaderNodeEmission')
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    if is_colour and grain and grain.get('amount', 0) > 0:
        # per-dot grain: every dot of the tile gets its own random number (white noise read at the dot's whole-number position, so it
        # repeats exactly across the tile edge), turned into a brightness factor 1 + amount x (a random number with spread 1)
        position = tree.nodes.new('ShaderNodeNewGeometry')
        to_dots = tree.nodes.new('ShaderNodeVectorMath')
        to_dots.operation = 'SCALE'
        to_dots.inputs['Scale'].default_value = tile_dots
        tree.links.new(position.outputs['Position'], to_dots.inputs[0])
        whole = tree.nodes.new('ShaderNodeVectorMath')
        whole.operation = 'FLOOR'
        tree.links.new(to_dots.outputs['Vector'], whole.inputs[0])
        seed_shift = tree.nodes.new('ShaderNodeVectorMath')
        seed_shift.operation = 'ADD'
        seed_shift.inputs[1].default_value = (0.0, 0.0, 17.0 * float(grain.get('seed', 3)))
        tree.links.new(whole.outputs['Vector'], seed_shift.inputs[0])
        white = tree.nodes.new('ShaderNodeTexWhiteNoise')
        white.noise_dimensions = '3D'
        tree.links.new(seed_shift.outputs['Vector'], white.inputs['Vector'])
        stretch = tree.nodes.new('ShaderNodeMapRange')               # white noise is spread evenly over 0..1 (spread 0.2887): make the spread 'amount'
        stretch.inputs['From Min'].default_value = 0.0
        stretch.inputs['From Max'].default_value = 1.0
        stretch.inputs['To Min'].default_value = 1.0 - grain['amount'] * 0.5 / 0.2887
        stretch.inputs['To Max'].default_value = 1.0 + grain['amount'] * 0.5 / 0.2887
        tree.links.new(white.outputs['Value'], stretch.inputs['Value'])
        gain = tree.nodes.new('ShaderNodeCombineColor')
        for socket in ('Red', 'Green', 'Blue'):
            tree.links.new(stretch.outputs['Result'], gain.inputs[socket])
        mix = tree.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        tree.links.new(attr.outputs['Color'], mix.inputs['A'])
        tree.links.new(gain.outputs['Color'], mix.inputs['B'])
        tree.links.new(mix.outputs['Result'], emit.inputs['Color'])
    elif is_colour:
        tree.links.new(attr.outputs['Color'], emit.inputs['Color'])
    else:
        grey = tree.nodes.new('ShaderNodeCombineColor')
        for socket in ('Red', 'Green', 'Blue'):
            tree.links.new(attr.outputs['Fac'], grey.inputs[socket])
        tree.links.new(grey.outputs['Color'], emit.inputs['Color'])
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return material


# ---------------------------------------------------------------------------------------------------- a second, REAL-geometry height
def render_geometry_height(stack, size, scene, bevel_dots=4.0, out_path=None, tile=None):
    """The 'real geometry' route for the height picture: every brick face becomes a solid slab (Solidify modifier), its top edges are rounded (Bevel
    modifier), the mortar stays at ground level; the overhead camera then photographs the height of whatever it sees (each dot glows with its own
    height above the ground). Returns the picture as an array 0..1 (rows top to bottom)."""
    tile = float(tile or ss.TILE)
    verts, faces, offset = [], [], 0
    for shape in stack:
        if shape['kind'] != 'brick':
            continue
        pts = shape['points']
        verts.append(np.column_stack([pts[:, 0] / tile, 1.0 - pts[:, 1] / tile, np.zeros(len(pts))]))
        faces.extend((offset, offset + i, offset + i + 1) for i in range(1, len(pts) - 1))
        offset += len(pts)
    mesh = bpy.data.meshes.new('slabs')
    mesh.from_pydata(np.concatenate(verts).tolist(), [], faces)
    mesh.update()
    obj = bpy.data.objects.new('slabs', mesh)
    scene.collection.objects.link(obj)
    thickness = 0.02
    solid = obj.modifiers.new('slab', 'SOLIDIFY')
    solid.thickness = thickness             # the faces point DOWN (the picture's y runs downward, Blender's up), so a positive thickness with offset -1 grows the slab upward
    solid.offset = -1.0
    solid.use_even_offset = True
    bevel = obj.modifiers.new('round edges', 'BEVEL')
    bevel.width = bevel_dots / tile
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    material = bpy.data.materials.new('show height')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    split = tree.nodes.new('ShaderNodeSeparateXYZ')
    divide = tree.nodes.new('ShaderNodeMath')
    divide.operation = 'DIVIDE'
    divide.inputs[1].default_value = thickness
    grey = tree.nodes.new('ShaderNodeCombineColor')
    emit = tree.nodes.new('ShaderNodeEmission')
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(geometry.outputs['Position'], split.inputs['Vector'])
    tree.links.new(split.outputs['Z'], divide.inputs[0])
    for socket in ('Red', 'Green', 'Blue'):
        tree.links.new(divide.outputs['Value'], grey.inputs[socket])
    tree.links.new(grey.outputs['Color'], emit.inputs['Color'])
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    obj.data.materials.append(material)
    # the colour picture's mesh is hidden while the slabs are photographed; the ground (mortar) is simply black = 0
    for other in scene.objects:
        if other is not obj:
            other.hide_render = True
    scene.camera.location = (0.5, 0.5, 2.0)
    scene.camera.data.clip_start = 0.5
    scene.camera.data.clip_end = 5.0
    path = out_path or '/tmp/geometry_height.png'
    bh.render_to(scene, path, linear_data=True, sixteen_bit=True)
    for other in scene.objects:
        other.hide_render = False
    picture = bh.load_png_as_array(path)[..., 0]
    return picture


# ---------------------------------------------------------------------------------------------------- the whole bake
def bake_description(description, out_folder, size=1254, samples=16, shift=0.0, wrap=True, quiet=False, height_mode='derived', height_blend=0.5):
    """Description (a dict) -> colour, height, normal, roughness, metallic, ao pictures in out_folder. Returns a dict of timings and counts."""
    os.makedirs(out_folder, exist_ok=True)
    started = time.time()
    timings = {}
    palette_rgb, palette_roughness = ss.palette_info(description)
    stack = ss.build_shape_stack(description, wrap=wrap, shift=shift)
    timings['shapes_seconds'] = round(time.time() - started, 2)
    scene, tile_object = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile_object)                     # the harness's plain square is not needed: the first shape covers the tile
    scene.cycles.samples = samples
    t = time.time()
    obj, z_top = build_mesh(stack, palette_rgb, palette_roughness, size, tile=float(description.get('tile', ss.TILE)))
    timings['mesh_seconds'] = round(time.time() - t, 2)
    scene.camera.location = (0.5, 0.5, z_top + 1.0)
    scene.camera.data.clip_start = 0.5
    scene.camera.data.clip_end = z_top + 3.0
    t = time.time()
    colour_path = os.path.join(out_folder, 'colour.png')
    obj.data.materials.append(channel_material('show colour', 'Col', True, grain=description.get('grain'), tile_dots=float(description.get('tile', ss.TILE))))
    bh.render_to(scene, colour_path, linear_data=False)
    timings['colour_render_seconds'] = round(time.time() - t, 2)
    t = time.time()
    obj.data.materials.clear()
    obj.data.materials.append(channel_material('show roughness', 'rough', False))
    bh.render_to(scene, os.path.join(out_folder, 'roughness.png'), linear_data=True)
    timings['roughness_render_seconds'] = round(time.time() - t, 2)
    # derived maps (numpy): height from colour, normal from height, ao from height, metallic = 0
    t = time.time()
    colour = bh.load_png_as_array(colour_path) * 255.0            # screen values 0..255, rows top to bottom
    maps = dict(description['maps'])
    scale = size / float(description.get('tile', ss.TILE))
    maps['blur_sigma'] = maps['blur_sigma'] * scale
    height = dm.height_from_colour(colour, maps)
    if height_mode in ('hybrid', 'geometry'):
        t_geo = time.time()
        geometry_height = render_geometry_height(stack, size, scene, bevel_dots=float(description.get('bevel_dots', 4.0)) * scale, out_path=os.path.join(out_folder, 'height_geometry_only.png'), tile=float(description.get('tile', ss.TILE)))
        timings['geometry_height_seconds'] = round(time.time() - t_geo, 2)
        height = geometry_height if height_mode == 'geometry' else (1.0 - height_blend) * height + height_blend * geometry_height
    bh.save_array_png(height, os.path.join(out_folder, 'height.png'), sixteen_bit=True)
    normal = dm.normal_from_height(height, maps.get('normal_strength', 6.0) * scale)       # a dot is smaller at a bigger size, so the slope per dot is smaller: scale the strength to match
    bh.save_array_png(normal, os.path.join(out_folder, 'normal.png'))
    wide = dm.gaussian_blur_wrap(height, 6.0 * scale)
    ao = np.clip(0.5 + (height - wide) * 2.5, 0.0, 1.0)         # dots lower than their surroundings are darker
    bh.save_array_png(ao, os.path.join(out_folder, 'ao.png'))
    bh.save_array_png(np.zeros((size, size)), os.path.join(out_folder, 'metallic.png'))
    timings['derive_seconds'] = round(time.time() - t, 2)
    result = {'size': size, 'samples': samples, 'shift': shift, 'shapes': len(stack), 'triangles': len(obj.data.polygons),
              'seconds': round(time.time() - started, 2), **timings}
    with open(os.path.join(out_folder, 'bake.json'), 'w') as handle:
        json.dump(result, handle, indent=1)
    if not quiet:
        print('[bake]', json.dumps(result))
    return result


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    with open(arguments[0]) as handle:
        description = json.load(handle)
    bake_description(description, arguments[1], size=int(option('--size', 1254)), samples=int(option('--samples', 16)),
                     shift=float(option('--shift', 0.0)), height_mode=option('--height-mode', 'derived'), height_blend=float(option('--height-blend', 0.5)))


if __name__ == '__main__':
    main()
