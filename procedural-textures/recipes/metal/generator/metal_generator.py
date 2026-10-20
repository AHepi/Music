# What this does (plain words): the Blender half of the rusted-metal generator. It reads a "metal plate description" file (see metal_shapes.py for the
# format), builds the painted shapes as REAL flat geometry in Blender (one little mesh piece per strap strip, rivet cell or patch of rust, stacked a
# tiny bit higher one after the other like layers of paint), adds Blender shader nodes on top (seamless rust, chips, stains and grain driven by
# numbers in the description), looks straight down with a 1 x 1 camera and writes the picture set for one tile:
#     colour.png  height.png (16-bit)  normal.png (OpenGL: green = up)  roughness.png  metallic.png  ao.png   (1254 dots square by default)
# It never opens the reference pictures: only the description.
#
# How the pictures are made:
#   colour     = what the camera sees (each shape glows with its own colour; the nearest-to-camera shape wins; procedural wear is laid over
#                the bare-steel shapes by shader nodes)
#   roughness / metallic = the same kind of picture, shapes glow with their roughness / metallic number
#   height     = made from the colour with the rule written in the description ("maps": grey -> light blur -> tone curve): the same rule that
#                made the reference height from the reference colour (analysis/derivation_ceiling.py); 'hybrid' also mixes in a height photographed
#                from real geometry (see metal_geometry_route.py)
#   normal     = slope of the height (Sobel), strength from the description
#   ao         = how hemmed-in a dot is, from the height (a cheap blur-difference, not a ray-traced one)
#
# Use (command line):
#   blender -b --disable-autoexec -t 2 --python metal_generator.py -- DESCRIPTION.json OUT_FOLDER [--size 1254] [--samples 16] [--shift 627]
#   --shift N moves the whole painting N dots right and down (wrapping round): used for the half-tile seamless test.
# Use (inside Blender):  import metal_generator as mg ;  mg.bake_description(description_dict, 'out_folder', size=1254)
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
import recipe_tools as rt  # noqa: E402  (node writer)
import derive_maps as dm  # noqa: E402
import metal_shapes as ms  # noqa: E402

try:
    import mathutils.geometry as mug
    from mathutils import Vector
except Exception:  # pragma: no cover
    mug = None


def srgb_to_linear(values255):
    v = np.asarray(values255, float) / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------------------------------------------- stack -> mesh
def triangles_of(shape):
    """Triangles (index triples into the shape's own points) that fill it. Convex shapes and 'fan' shapes (a centre point then a ring) use a fan."""
    n = len(shape['points'])
    if shape.get('fan'):
        return [(0, i, i + 1) for i in range(1, n - 1)] + [(0, n - 1, 1)]
    if shape.get('convex') or n <= 3:
        return [(0, i, i + 1) for i in range(1, n - 1)]
    return None                                       # a concave outline: filled by ms.slab_triangles (below)


MATERIAL_BY_KIND = {'plate': (0.55, 1.0), 'panel': (0.55, 1.0), 'face': (0.50, 1.0), 'edge': (0.40, 1.0), 'seam': (0.40, 1.0), 'rivet': (0.35, 1.0), 'scratch': (0.30, 1.0)}


def build_mesh(stack, description, tile, z_step=2.0e-5):
    """One mesh holding every shape; shape number i sits at height (i * z_step) so later shapes cover earlier ones."""
    patch_rough = description.get('patch_roughness')
    patch_metal = description.get('patch_metallic')
    vertex_blocks, faces, colours, roughs, metals, bases, auxs = [], [], [], [], [], [], []
    offset = 0
    for index, shape in enumerate(stack):
        pts = shape['points']
        n = len(pts)
        z = index * z_step
        vertex_blocks.append(np.column_stack([pts[:, 0] / tile, 1.0 - pts[:, 1] / tile, np.full(n, z)]))
        simple = triangles_of(shape)
        if simple is None:                            # concave outline: the shape gets its own corner points cut by horizontal slabs
            new_points, tris = ms.slab_triangles(pts)
            if len(new_points) == 0:
                vertex_blocks.pop()
                continue
            n = len(new_points)
            vertex_blocks[-1] = np.column_stack([new_points[:, 0] / tile, 1.0 - new_points[:, 1] / tile, np.full(n, z)])
            shape = dict(shape, colours=np.tile(shape['colours'][0], (n, 1)), aux=np.full(n, float(np.mean(shape.get('aux', [0.0])))))
            for t in tris:
                faces.append((offset + t[0], offset + t[1], offset + t[2]))
        else:
            for t in simple:
                faces.append((offset + t[0], offset + t[1], offset + t[2]))
        colours.append(np.hstack([srgb_to_linear(shape['colours']), np.ones((n, 1))]))
        rough, metal = MATERIAL_BY_KIND.get(shape['kind'], (0.6, 0.3))
        if shape['kind'] == 'patch' and 'material' in shape:
            rough, metal = shape['material']
        roughs.append(np.full(n, rough))
        metals.append(np.full(n, metal))
        bases.append(np.full(n, float(shape.get('base', 0))))
        auxs.append(np.asarray(shape.get('aux', np.zeros(n)), float))
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
    layer = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    layer.data.foreach_set('color', np.concatenate(colours).astype(np.float32).ravel())
    for name, values in (('rough', roughs), ('metal', metals), ('base', bases), ('aux', auxs)):
        attribute = mesh.attributes.new(name, 'FLOAT', 'POINT')
        attribute.data.foreach_set('value', np.concatenate(values).astype(np.float32))
    obj = bpy.data.objects.new('paint', mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, (len(stack) + 1) * z_step


# ---------------------------------------------------------------------------------------------------- seamless streaky noise (copied from lib/contrib/hp_tools.py)
def streaky_noise_group():
    """SEAMLESS noise that can be stretched. Inputs: Vector (tile coordinate 0..1), Scale U / Scale V (features across the tile left-right / up-down),
    Detail, Roughness, Distortion, Seed. Output: Fac. u goes round a circle of circumference Scale U and v round one of circumference Scale V; the 4D noise
    is read at (cos u, sin u, cos v, sin v), so it repeats every tile and each direction has its own feature size."""
    name = 'Metal streaky noise'
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    tree, w = rt.make_group_tree(name, [
        ('Vector', 'NodeSocketVector', (0, 0, 0)), ('Scale U', 'NodeSocketFloat', 8.0), ('Scale V', 'NodeSocketFloat', 8.0),
        ('Detail', 'NodeSocketFloat', 2.0), ('Roughness', 'NodeSocketFloat', 0.5), ('Distortion', 'NodeSocketFloat', 0.0),
        ('Seed', 'NodeSocketFloat', 0.0)], [('Fac', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'split uv', x=-3)
    w.link('in', 'Vector', 'split uv', 'Vector')
    for axis, label, scale_name in (('X', 'u', 'Scale U'), ('Y', 'v', 'Scale V')):
        row = 0 if label == 'u' else -3
        w.math(f'turns {label}', 'MULTIPLY', None, 2 * math.pi, x=-2, y=row)
        w.link('split uv', axis, f'turns {label}', 0)
        w.math(f'radius {label}', 'DIVIDE', None, 2 * math.pi, x=-2, y=row + 1)
        w.link('in', scale_name, f'radius {label}', 0)
        for trig, fn in (('cos', 'COSINE'), ('sin', 'SINE')):
            w.math(f'{trig} {label}', fn, x=-1, y=row)
            w.link(f'turns {label}', 0, f'{trig} {label}', 0)
            w.math(f'{trig} {label} r', 'MULTIPLY', x=0, y=row)
            w.link(f'{trig} {label}', 0, f'{trig} {label} r', 0)
            w.link(f'radius {label}', 0, f'{trig} {label} r', 1)
    w.add('ShaderNodeCombineXYZ', 'xyz', x=1)
    w.link('cos u r', 0, 'xyz', 'X')
    w.link('sin u r', 0, 'xyz', 'Y')
    w.link('cos v r', 0, 'xyz', 'Z')
    w.math('w seed', 'ADD', x=1, y=-3)
    w.link('sin v r', 0, 'w seed', 0)
    w.link('in', 'Seed', 'w seed', 1)
    w.add('ShaderNodeTexNoise', 'noise', x=2, noise_dimensions='4D', noise_type='FBM', normalize=True, Scale=1.0)
    w.link('xyz', 0, 'noise', 'Vector')
    w.link('w seed', 0, 'noise', 'W')
    for socket in ('Detail', 'Roughness', 'Distortion'):
        w.link('in', socket, 'noise', socket)
    w.link('noise', 'Fac', 'out', 'Fac')
    return tree


# ---------------------------------------------------------------------------------------------------- the material (colour / roughness / metallic)
def make_ramp(w, name, stops, interpolation='CONSTANT', x=None, y=0, factors=False):
    """A Color Ramp from stops [[position, [r,g,b] screen colour, alpha], ...]."""
    node = w.add('ShaderNodeValToRGB', name, x=x, y=y)
    ramp = node.color_ramp
    ramp.interpolation = interpolation
    while len(ramp.elements) > 1:
        ramp.elements.remove(ramp.elements[-1])
    first = True
    for position, colour, alpha in stops:
        element = ramp.elements[0] if first else ramp.elements.new(position)
        element.position = position
        lin = np.asarray(colour, float) / 128.0 if factors else srgb_to_linear(colour)      # 'factors': 128 = no change, 140 = 9 per cent brighter
        element.color = (lin[0], lin[1], lin[2], alpha)
        first = False
    return node


def add_noise_field(w, i, tag, spec, uv_name, scale_per_tile, x0, y):
    """One seamless streaky noise (spec: scale_u, scale_v, detail, roughness, distortion, seed) stretched to about 0..1. Returns the node name holding the result."""
    group = streaky_noise_group()
    n = w.add('ShaderNodeGroup', f'{tag}{i}', x=x0, y=y)
    n.node_tree = group
    w.link(uv_name, 'Vector', f'{tag}{i}', 'Vector')
    for socket, key, default in (('Scale U', 'scale_u', 8.0), ('Scale V', 'scale_v', 8.0)):
        n.inputs[socket].default_value = spec.get(key, default) * scale_per_tile
    for socket, key, default in (('Detail', 'detail', 3.0), ('Roughness', 'roughness', 0.55), ('Distortion', 'distortion', 0.0), ('Seed', 'seed', float(i))):
        n.inputs[socket].default_value = spec.get(key, default)
    # the noise sits in about 0.25..0.73: stretch it to 0..1
    w.add('ShaderNodeMapRange', f'stretch {tag}{i}', x=x0 + 1, y=y, clamp=True)
    w.nodes[f'stretch {tag}{i}'].inputs['From Min'].default_value = spec.get('noise_low', 0.27)
    w.nodes[f'stretch {tag}{i}'].inputs['From Max'].default_value = spec.get('noise_high', 0.71)
    w.link(f'{tag}{i}', 'Fac', f'stretch {tag}{i}', 'Value')
    return f'stretch {tag}{i}'


def add_wear_field(w, i, layer, uv_name, scale_per_tile, x0, y):
    """value = (fine noise, optionally blended with a coarse 'modulator' noise) x gain + offset + edge_gain x (edge/rivet attraction). Returns the node name."""
    fine = add_noise_field(w, i, 'fine', layer.get('fine', layer), uv_name, scale_per_tile, x0, y)
    source = fine
    if layer.get('mod'):
        mod = add_noise_field(w, i, 'mod', layer['mod'], uv_name, scale_per_tile, x0, y - 1)
        w.add('ShaderNodeMix', f'blend{i}', x=x0 + 2, y=y, data_type='FLOAT')
        w.nodes[f'blend{i}'].inputs['Factor'].default_value = layer['mod'].get('weight', 0.5)
        w.link(fine, 'Result', f'blend{i}', 'A')
        w.link(mod, 'Result', f'blend{i}', 'B')
        source = f'blend{i}'
    w.math(f'gain{i}', 'MULTIPLY_ADD', None, layer.get('gain', 1.0), layer.get('offset', 0.0), x=x0 + 2.5, y=y)
    w.link(source, 'Result', f'gain{i}', 0)
    w.math(f'edge{i}', 'MULTIPLY_ADD', None, layer.get('edge_gain', 0.0), None, x=x0 + 3, y=y)
    w.link('aux', 'Fac', f'edge{i}', 0)
    w.link(f'gain{i}', 0, f'edge{i}', 2)
    return f'edge{i}'


def build_material(description, channel, size, tile, shift_dots=(0.0, 0.0)):
    """A material that glows with one channel: 'colour', 'rough', 'metal', or for calibration 'field<i>' (the wear value of layer i) or 'basemask'.
    Procedural wear layers (description['procedural']['layers']) and grain are laid over the shapes marked 'base' (bare steel).
    tile = the description's tile size in dots; noise scales are 'features per 1254 dots' and grow with the tile."""
    proc = description.get('procedural', {})
    material = bpy.data.materials.new(f'show {channel}')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeAttribute', 'col', x=0, attribute_name='Col', attribute_type='GEOMETRY')
    w.add('ShaderNodeAttribute', 'rough', x=0, y=-1, attribute_name='rough', attribute_type='GEOMETRY')
    w.add('ShaderNodeAttribute', 'metal', x=0, y=-2, attribute_name='metal', attribute_type='GEOMETRY')
    w.add('ShaderNodeAttribute', 'base', x=0, y=-3, attribute_name='base', attribute_type='GEOMETRY')
    w.add('ShaderNodeAttribute', 'aux', x=0, y=-4, attribute_name='aux', attribute_type='GEOMETRY')
    w.add('ShaderNodeNewGeometry', 'geo', x=0, y=-5)
    w.add('ShaderNodeSeparateXYZ', 'pos split', x=1, y=-5)
    w.link('geo', 'Position', 'pos split', 'Vector')
    w.add('ShaderNodeCombineXYZ', 'uv', x=2, y=-5)
    w.math('u shifted', 'SUBTRACT', None, shift_dots[0] / tile, x=1.5, y=-6)
    w.link('pos split', 'X', 'u shifted', 0)
    w.math('v shifted', 'ADD', None, shift_dots[1] / tile, x=1.5, y=-7)     # v runs up the picture, the shift runs down it
    w.link('pos split', 'Y', 'v shifted', 0)
    w.link('u shifted', 0, 'uv', 'X')
    w.link('v shifted', 0, 'uv', 'Y')
    colour_socket = ('col', 'Color')
    rough_socket = ('rough', 'Fac')
    metal_socket = ('metal', 'Fac')
    scale_per_tile = tile / 1254.0
    field_wanted = int(channel[5:]) if channel.startswith('field') else None
    for i, layer in enumerate(proc.get('layers', [])):
        if not layer.get('enabled', True):
            continue
        x0 = 3 + 4 * i
        value = add_wear_field(w, i, layer, 'uv', scale_per_tile, x0, -6 - 3 * i)
        if field_wanted == i:
            colour_socket = (value, 0)
            break
        make_ramp(w, f'ramp{i}', layer['stops'], layer.get('interpolation', 'CONSTANT'), x=x0 + 3.5, y=-6 - 3 * i, factors=layer.get('blend') == 'MULTIPLY')
        w.link(value, 0, f'ramp{i}', 'Fac')
        if layer.get('on', 'base') == 'base':
            w.math(f'amount{i}', 'MULTIPLY', x=x0 + 3.9, y=-6 - 3 * i)
            w.link(f'ramp{i}', 'Alpha', f'amount{i}', 0)
            w.link('base', 'Fac', f'amount{i}', 1)
            amount = (f'amount{i}', 0)
        else:
            amount = (f'ramp{i}', 'Alpha')
        w.add('ShaderNodeMix', f'mix colour{i}', x=x0 + 3.9, y=-7 - 3 * i, data_type='RGBA', blend_type=layer.get('blend', 'MIX'))
        w.link(*amount, f'mix colour{i}', 'Factor')
        w.link(*colour_socket, f'mix colour{i}', 'A')
        w.link(f'ramp{i}', 'Color', f'mix colour{i}', 'B')
        colour_socket = (f'mix colour{i}', 'Result')
        for tag, key, current in (('r', 'rough', rough_socket), ('m', 'metal', metal_socket)):
            if key in layer:
                w.add('ShaderNodeMix', f'mix {tag}{i}', x=x0 + 3.9, y=-8 - 3 * i, data_type='FLOAT')
                w.link(*amount, f'mix {tag}{i}', 'Factor')
                w.link(*current, f'mix {tag}{i}', 'A')
                w.nodes[f'mix {tag}{i}'].inputs['B'].default_value = layer[key]
                if tag == 'r':
                    rough_socket = (f'mix {tag}{i}', 'Result')
                else:
                    metal_socket = (f'mix {tag}{i}', 'Result')
    grain = proc.get('grain')
    if grain and grain.get('amount', 0) > 0 and channel == 'colour':
        w.add('ShaderNodeVectorMath', 'to dots', x=40, y=-8, operation='SCALE')
        w.nodes['to dots'].inputs['Scale'].default_value = float(tile) * float(grain.get('per_dot', 1.0))
        w.link('uv', 'Vector', 'to dots', 0)          # the shifted tile coordinate, so that the grain moves with the painting in the half-tile seam test
        w.add('ShaderNodeVectorMath', 'whole', x=41, y=-8, operation='FLOOR')
        w.link('to dots', 'Vector', 'whole', 0)
        w.add('ShaderNodeVectorMath', 'seed shift', x=42, y=-8, operation='ADD')
        w.nodes['seed shift'].inputs[1].default_value = (0.0, 0.0, 17.0 * float(grain.get('seed', 3)))
        w.link('whole', 'Vector', 'seed shift', 0)
        w.add('ShaderNodeTexWhiteNoise', 'white', x=43, y=-8, noise_dimensions='3D')
        w.link('seed shift', 'Vector', 'white', 'Vector')
        w.add('ShaderNodeMapRange', 'grain range', x=44, y=-8)
        w.nodes['grain range'].inputs['To Min'].default_value = 1.0 - grain['amount'] * 0.5 / 0.2887
        w.nodes['grain range'].inputs['To Max'].default_value = 1.0 + grain['amount'] * 0.5 / 0.2887
        w.link('white', 'Value', 'grain range', 'Value')
        w.add('ShaderNodeCombineColor', 'grain colour', x=45, y=-8)
        for socket in ('Red', 'Green', 'Blue'):
            w.link('grain range', 'Result', 'grain colour', socket)
        w.add('ShaderNodeMix', 'grain mix', x=46, y=-8, data_type='RGBA', blend_type='MULTIPLY')
        w.nodes['grain mix'].inputs['Factor'].default_value = 1.0
        w.link(*colour_socket, 'grain mix', 'A')
        w.link('grain colour', 'Color', 'grain mix', 'B')
        colour_socket = ('grain mix', 'Result')
    w.add('ShaderNodeEmission', 'emit', x=48)
    if channel == 'colour':
        w.link(*colour_socket, 'emit', 'Color')
    else:
        if channel == 'rough':
            socket = rough_socket
        elif channel == 'metal':
            socket = metal_socket
        elif channel == 'basemask':
            socket = ('base', 'Fac')
        else:
            socket = colour_socket
        w.add('ShaderNodeCombineColor', 'grey', x=47)
        for s in ('Red', 'Green', 'Blue'):
            w.link(*socket, 'grey', s)
        w.link('grey', 'Color', 'emit', 'Color')
    w.add('ShaderNodeOutputMaterial', 'output', x=49)
    w.link('emit', 'Emission', 'output', 'Surface')
    return material


# ---------------------------------------------------------------------------------------------------- the whole bake
def ambient_occlusion_from_height(height, radius=6.0, strength=1.6):
    """A cheap AO picture: how much lower than its own neighbourhood a dot is (blur of height minus height), 1 = open, 0 = closed."""
    blurred = dm.gaussian_blur_wrap(height, radius)
    ao = 1.0 - np.clip((blurred - height) * strength * 4.0, 0.0, 1.0)
    return np.clip(ao, 0.0, 1.0)


def bake_description(description, out_folder, size=1254, samples=16, shift=0.0, quiet=False, height_mode='derived', channels=('colour', 'rough', 'metal')):
    """Description (a dict) -> colour, height, normal, roughness, metallic, ao pictures in out_folder. Returns a dict of timings and counts."""
    os.makedirs(out_folder, exist_ok=True)
    started = time.time()
    timings = {}
    tile = float(description.get('tile', ms.TILE))
    shift_pair = (float(shift), float(shift)) if not isinstance(shift, (tuple, list)) else tuple(shift)
    t0 = time.time()
    stack = ms.build_stack(description, wrap=True, shift=shift_pair)
    timings['stack_seconds'] = round(time.time() - t0, 2)
    scene, tile_object = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile_object)
    scene.cycles.samples = samples
    scene.cycles.filter_width = float(description.get('render', {}).get('filter_width', 1.0))      # 0.01 = hard staircase edges like the painted reference; 1.0 = smooth edges
    t0 = time.time()
    obj, top = build_mesh(stack, description, tile)
    timings['mesh_seconds'] = round(time.time() - t0, 2)
    scene.camera.location = (0.5, 0.5, top + 1.0)
    scene.camera.data.clip_start = 0.5
    scene.camera.data.clip_end = top + 5.0
    results = {'size': size, 'shapes': len(stack), 'tile': tile, 'samples': samples, 'shift': shift_pair}
    wanted = [('colour', 'colour', False), ('rough', 'roughness', True), ('metal', 'metallic', True)]
    wanted += [(c, c, True) for c in channels if c.startswith('field') or c == 'basemask']
    for channel, name, linear in wanted:
        if channel not in channels:
            continue
        t0 = time.time()
        material = build_material(description, channel, size, tile, shift_pair)
        obj.data.materials.clear()
        obj.data.materials.append(material)
        bh.render_to(scene, os.path.join(out_folder, name + '.png'), linear, channel.startswith('field'))
        timings[f'render_{name}_seconds'] = round(time.time() - t0, 2)
    if 'colour' not in channels:
        return results
    maps = description['maps']
    colour = bh.load_png_as_array(os.path.join(out_folder, 'colour.png'))      # Non-Color read: raw 0..1 screen values
    height = dm.height_from_colour(colour * 255.0, maps)
    bh.save_array_png(height, os.path.join(out_folder, 'height.png'), sixteen_bit=True)
    normal = dm.normal_from_height(height, maps['normal_strength'])
    bh.save_array_png(normal, os.path.join(out_folder, 'normal.png'))
    bh.save_array_png(ambient_occlusion_from_height(height), os.path.join(out_folder, 'ao.png'))
    timings['seconds'] = round(time.time() - started, 1)
    results['timings'] = timings
    with open(os.path.join(out_folder, 'bake.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    if not quiet:
        print('[bake]', json.dumps(results))
    return results


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    with open(arguments[0]) as handle:
        description = json.load(handle)
    if 'maps' not in description:
        description['maps'] = json.load(open(os.path.join(PROC, 'recipes', 'metal', 'description', 'maps_rule.json')))
    channels = tuple(option('--channels', 'colour,rough,metal').split(','))
    bake_description(description, arguments[1], size=int(option('--size', 1254)), samples=int(option('--samples', 16)), shift=float(option('--shift', 0.0)), channels=channels)


if __name__ == '__main__':
    main()
