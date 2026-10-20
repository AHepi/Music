# What this does (plain words): the MUD GENERATOR. It reads a "description" file (a palette of flat colours plus back-to-front lists of puddles, stones, wheel ruts,
# ground patches and traced patches), builds that as real flat Blender geometry (every shape is a flat piece of mesh floating a tiny bit above the one before),
# photographs it from straight above with Blender's Cycles renderer, and writes the full set of texture pictures for one seamless tile:
# colour.png, height.png (16-bit), normal.png (OpenGL: green points up), roughness.png, metallic.png and ao.png.
# It NEVER reads the reference pictures; everything it knows is in the description file.
# How the maps are made (the "derivation" the reference maps were made with, proved in analysis/derivation_ceiling.py):
#   height = a straight-line stretch of the colour's brightness (grey = 0.299 R + 0.587 G + 0.114 B of the sRGB numbers), blurred about 0.5 dots;
#   normal = the slope of the 8-bit height, strength 9.
# Use (from the command line):
#   blender -b --disable-autoexec -t 2 --python mud_generator.py -- DESCRIPTION.json OUT_FOLDER [--size 1254] [--shift 0.5 0.5] [--samples 8]
# The same file can be imported (import mud_generator as mg) to call bake_description(description, out_folder, size).
# (The structure follows the wood generator of this project: flat shapes photographed from above. The mud-specific part is in mud_layers.py and the sampler.)
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib'))
sys.path.insert(0, HERE)

import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402
import mud_layers as layers  # noqa: E402

Z_STEP = 2.0e-5          # how far each next shape floats above the one before (the tile is 1 wide)


def srgb_to_linear(value):
    value = np.asarray(value, np.float64)
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def palette_attributes(description):
    palette = np.array(description['palette'], np.float64) / 255.0
    grey = palette @ np.array([0.299, 0.587, 0.114])
    roughness = description.get('roughness') or list(np.clip(0.97 - 0.55 * grey, 0.35, 0.98))
    metallic = description.get('metallic') or [0.0] * len(palette)
    return srgb_to_linear(palette), grey, np.asarray(roughness, np.float64), np.asarray(metallic, np.float64)


def build_tile_mesh(shape_list, description, shift=(0.0, 0.0)):
    """One Blender mesh holding every flat shape. shape_list: [(list of polygons (n x 2 tile dots, y down), palette index), ...] back to front.
    A polygon is drawn again shifted by -1 / +1 tile wherever it touches the tile edge, so the tile repeats exactly."""
    tile = float(description['tile'])
    linear, grey, roughness, metallic = palette_attributes(description)
    vertices, faces, face_colour, face_grey, face_rough, face_metal = [], [], [], [], [], []
    count = 0
    sx, sy = shift
    for polygons, index in shape_list:
        z = (count + 1) * Z_STEP
        for points in polygons:
            pts = np.asarray(points, np.float64)
            if len(pts) < 3:
                continue
            pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
            pts = pts + [sx * tile, sy * tile]
            pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
            for ox, oy in layers.wrap_copy_count(pts, tile):
                u = (pts[:, 0] + ox * tile) / tile
                v = 1.0 - (pts[:, 1] + oy * tile) / tile
                start = len(vertices)
                vertices.extend((float(a), float(b), z) for a, b in zip(u, v))
                faces.append(tuple(range(start, start + len(pts))))
                face_colour.append(linear[index])
                face_grey.append(grey[index])
                face_rough.append(roughness[index])
                face_metal.append(metallic[index])
        count += 1
    mesh = bpy.data.meshes.new('mud shapes')
    mesh.from_pydata(vertices, [], faces)
    colour = np.ones((len(faces), 4), np.float32)
    colour[:, :3] = np.array(face_colour, np.float32).reshape(-1, 3)
    for name, kind, values in (('piece_colour', 'FLOAT_COLOR', colour.ravel()), ('piece_grey', 'FLOAT', np.array(face_grey, np.float32)),
                               ('piece_rough', 'FLOAT', np.array(face_rough, np.float32)), ('piece_metal', 'FLOAT', np.array(face_metal, np.float32))):
        attribute = mesh.attributes.new(name, kind, 'FACE')
        attribute.data.foreach_set('color' if kind == 'FLOAT_COLOR' else 'value', values)
    return mesh, count, len(faces)


def channel_material(channel):
    """An emission material that shows ONE map: 'Colour', 'Roughness' or 'Metallic' (read from the attributes on the faces)."""
    material = bpy.data.materials.new('show ' + channel)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeEmission', 'emit', x=5, Strength=1.0)
    w.add('ShaderNodeOutputMaterial', 'output', x=6)
    w.link('emit', 'Emission', 'output', 'Surface')
    name = {'Colour': 'piece_colour', 'Roughness': 'piece_rough', 'Metallic': 'piece_metal'}[channel]
    if channel == 'Colour':
        w.add('ShaderNodeAttribute', 'attr', x=0, attribute_name=name, attribute_type='GEOMETRY')
        w.link('attr', 'Color', 'emit', 'Color')
    else:
        w.add('ShaderNodeAttribute', 'attr', x=0, attribute_name=name, attribute_type='GEOMETRY')
        w.add('ShaderNodeCombineColor', 'grey', x=3)
        for socket in ('Red', 'Green', 'Blue'):
            w.link('attr', 'Fac', 'grey', socket)
        w.link('grey', 'Color', 'emit', 'Color')
    return material


def photograph(scene, tile_object, material, path, linear_data, sixteen_bit, samples, box_width=1.0):
    tile_object.data.materials.clear()
    tile_object.data.materials.append(material)
    scene.cycles.samples = samples
    scene.cycles.pixel_filter_type = 'BOX'
    scene.cycles.filter_width = box_width
    bh.render_to(scene, path, linear_data, sixteen_bit)


def derive_normal_from_height(height16, strength, kernel='central'):
    """Normal map (OpenGL, green up) from the height rounded to 8 bits, the way the reference maps were made (slope across 2 dots x strength)."""
    h = np.round(height16 * 255.0)
    hx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
    hy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def gaussian_blur_wrap(image, sigma):
    radius = int(math.ceil(3 * sigma))
    kernel = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma) ** 2)
    kernel /= kernel.sum()
    out = image
    for axis in (0, 1):
        padded = np.concatenate([np.take(out, range(-radius, 0), axis=axis, mode='wrap'), out, np.take(out, range(0, radius), axis=axis, mode='wrap')], axis=axis)
        result = np.zeros_like(out)
        for offset, weight in enumerate(kernel):
            result += weight * np.take(padded, range(offset, offset + out.shape[axis]), axis=axis)
        out = result
    return out


def derive_ambient_occlusion(height16, strength=2.5, radius=6.0):
    """A cheap cavity map: how much lower than its surroundings (blurred over `radius` dots) each dot is: white = open, dark = hemmed in."""
    blurred = gaussian_blur_wrap(height16, radius)
    return np.clip(1.0 - strength * np.clip(blurred - height16, 0, None), 0, 1)


def bake_description(description, out_folder, size=1254, shift=(0.0, 0.0), samples=8, quiet=False, with_ao=True, shape_list=None):
    os.makedirs(out_folder, exist_ok=True)
    timings = {}
    started = time.time()
    shape_list = shape_list if shape_list is not None else layers.make_shape_list(description)
    timings['shapes_s'] = round(time.time() - started, 2)
    started = time.time()
    scene, tile = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile)
    mesh, shape_count, face_count = build_tile_mesh(shape_list, description, shift)
    obj = bpy.data.objects.new('mud shapes', mesh)
    scene.collection.objects.link(obj)
    scene.camera.location.z = shape_count * Z_STEP + 2.0                 # camera above the highest shape
    scene.camera.data.clip_end = shape_count * Z_STEP + 10.0
    scene.camera.location.x = scene.camera.location.y = 0.5
    timings['mesh_s'] = round(time.time() - started, 2)
    timings['shapes'] = shape_count
    timings['mesh_faces'] = face_count
    h = description['maps']['height']
    for channel, name, linear, sixteen in (('Colour', 'colour', False, False), ('Roughness', 'roughness', True, False), ('Metallic', 'metallic', True, False)):
        started = time.time()
        photograph(scene, obj, channel_material(channel), os.path.join(out_folder, name + '.png'), linear, sixteen, samples if channel == 'Colour' else 4)
        timings[name + '_render_s'] = round(time.time() - started, 2)
    started = time.time()
    colour = bh.load_png_as_array(os.path.join(out_folder, 'colour.png'))
    grey = (colour @ np.array([0.299, 0.587, 0.114])) * 255.0                      # brightness of the sRGB numbers of the finished colour picture
    stretched = np.clip((grey - h['grey_low']) / (h['grey_high'] - h['grey_low']), 0, 1)
    if h.get('blur', 0) > 0:
        stretched = gaussian_blur_wrap(stretched, h['blur'])
    bh.save_array_png(stretched, os.path.join(out_folder, 'height.png'), sixteen_bit=True)
    height = bh.load_png_as_array(os.path.join(out_folder, 'height.png'))[..., 0]
    bh.save_array_png(derive_normal_from_height(height, description['maps']['normal']['strength']) * 0.5 + 0.5, os.path.join(out_folder, 'normal.png'))
    if with_ao:
        bh.save_array_png(derive_ambient_occlusion(height), os.path.join(out_folder, 'ao.png'))
    timings['derive_s'] = round(time.time() - started, 2)
    timings['size'] = size
    timings['shift'] = list(shift)
    timings['total_s'] = round(sum(v for k, v in timings.items() if k.endswith('_s')), 1)
    with open(os.path.join(out_folder, 'bake.json'), 'w') as handle:
        json.dump(timings, handle, indent=1)
    if not quiet:
        print('[bake]', json.dumps(timings))
    return timings


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    shift = (float(arguments[arguments.index('--shift') + 1]), float(arguments[arguments.index('--shift') + 2])) if '--shift' in arguments else (0.0, 0.0)
    samples = int(option('--samples', 8))
    if arguments[0] == '--batch':
        for description_path, out_folder, size in json.load(open(arguments[1])):
            bake_description(json.load(open(description_path)), out_folder, size=int(size), shift=shift, samples=samples)
        return
    bake_description(json.load(open(arguments[0])), arguments[1], size=int(option('--size', 1254)), shift=shift, samples=samples)


if __name__ == '__main__':
    main()
