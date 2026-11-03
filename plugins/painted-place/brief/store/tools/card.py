"""
What this file does: draws the store's card pictures, so a builder (and the owner) can see an item before using it.

    python3 card.py material "SURFACE • brown_mud"        a sphere and a 1 m cube in the material, one amber light and a blue fill
    python3 card.py part bell_tent                        the part from three quarters and close up (and, with --views, the side and back)
    python3 card.py part field_gun --views three,close,side,back --seed 2 --option door_open=false
    python3 card.py material all                           every material's card
    python3 card.py sheet materials                        one sheet of every material card with its name
    python3 card.py sheet parts

Cards go to store/cards/materials/ and store/cards/parts/. Every card uses the same light: an amber key from the
front left, a blue fill from the right, a rim from behind, on a dark ground, so cards can be compared.
Parts face -Y (Blender's front view); "three" looks from 35 degrees to the right of front, "close" from nearer and
lower at the front, "side" from +X, "back" from +Y.
"""

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import store  # noqa: E402

CARDS = os.path.join(store.STORE, 'cards')
VIEWS = {  # azimuth from the front (-Y) towards +X, elevation, distance factor, aim lift and push (fractions of the radius)
    'three': (35.0, 18.0, 1.0, 0.0, 0.0),
    'close': (20.0, 10.0, 0.5, 0.1, -0.25),
    'side': (90.0, 8.0, 1.0, 0.0, 0.0),
    'back': (180.0, 15.0, 1.0, 0.0, 0.0),
}


def file_name(name):
    return name.replace(' • ', ' - ').replace('•', '-').replace('/', '-').strip()


def _empty_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = 'AgX'
    scene.render.film_transparent = False
    world = bpy.data.worlds.new('card world')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.018, 0.026, 0.036, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    scene.world = world
    return scene


def _light(scene, name, kind, location, target, colour, power, size):
    data = bpy.data.lights.new(name, kind)
    data.color = colour
    data.energy = power
    if kind == 'AREA':
        data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    return obj


def _stage(scene, centre, radius):
    """Ground, the three lights, scaled to the thing's size."""
    bpy.ops.mesh.primitive_plane_add(size=max(40.0, radius * 30.0), location=(centre.x, centre.y, 0.0))
    ground = bpy.context.object
    ground.name = 'card ground'
    ground_material = bpy.data.materials.new('card ground')
    ground_material.use_nodes = True
    ground_material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.045, 0.043, 0.04, 1)
    ground_material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85
    ground.data.materials.append(ground_material)
    r = max(radius, 0.3)
    power = 320.0 * r * r
    _light(scene, 'card key amber', 'AREA', centre + Vector((-2.2 * r, -2.6 * r, 2.4 * r)), centre, (1.0, 0.62, 0.32), power, 1.2 * r)
    _light(scene, 'card fill blue', 'AREA', centre + Vector((2.8 * r, -1.6 * r, 1.4 * r)), centre, (0.45, 0.62, 1.0), power * 0.35, 2.0 * r)
    _light(scene, 'card rim', 'AREA', centre + Vector((0.6 * r, 3.0 * r, 2.2 * r)), centre, (0.85, 0.85, 1.0), power * 0.45, 1.0 * r)


def _camera(scene, centre, radius, view, lens=50.0):
    azimuth, elevation, distance_factor, lift, push = VIEWS[view]
    data = bpy.data.cameras.new('card camera')
    data.lens = lens
    camera = bpy.data.objects.new('card camera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    half = math.atan(18.0 / lens)                  # half the narrower field (36 mm wide sensor, square frame)
    distance = radius / math.sin(half) * 1.08 * distance_factor
    a, e = math.radians(azimuth), math.radians(elevation)
    direction = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    aim = centre + Vector((0.0, push * radius, lift * radius))
    camera.location = aim + direction * distance
    camera.rotation_euler = (aim - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.clip_end = distance * 10 + 100
    return camera


def _bounds(objects):
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type not in ('MESH', 'CURVE'):
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            low = Vector(tuple(map(min, low, world)))
            high = Vector(tuple(map(max, high, world)))
    return low, high


def _render(scene, path, width, height, samples):
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.cycles.samples = samples
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    return path


def part_cards(name, views=('three', 'close'), size=420, samples=32, seed=0, options=None):
    scene = _empty_scene()
    root = store.add_part(name, seed=seed, **(options or {}))
    bpy.context.view_layer.update()
    objects = [o for o in scene.objects if o.type in ('MESH', 'CURVE')]
    low, high = _bounds(objects)
    centre = (low + high) / 2
    radius = max((high - low).length / 2, 0.05)
    _stage(scene, centre, radius)
    store.prepare_for_render(scene)
    written = []
    for view in views:
        camera = _camera(scene, centre, radius, view)
        written.append(_render(scene, os.path.join(CARDS, 'parts', '%s - %s.png' % (name, view)), size, size, samples))
        bpy.data.objects.remove(camera, do_unlink=True)
    size_m = tuple(round(v, 2) for v in (high - low))
    print('part %s: %d objects, size %.2f x %.2f x %.2f m, foot at z = %.3f' % (name, len(objects), *size_m, low.z))
    return written, size_m


def material_card(name, width=360, height=220, samples=24):
    scene = _empty_scene()
    material = store.material(name)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(-0.62, 0.0, 0.5), segments=48, ring_count=24)
    sphere = bpy.context.object
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.62, 0.15, 0.5), rotation=(0, 0, math.radians(28)))
    cube = bpy.context.object
    for obj in (sphere, cube):
        store.use_material(obj, material, ground=0.0)
    centre = Vector((0.0, 0.05, 0.5))
    _stage(scene, centre, 0.9)
    data = bpy.data.cameras.new('card camera')
    data.lens = 50
    camera = bpy.data.objects.new('card camera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = (0.35, -4.9, 1.75)
    camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
    path = os.path.join(CARDS, 'materials', file_name(name) + '.png')
    return _render(scene, path, width, height, samples)


def sheet(kind, columns=None):
    from PIL import Image, ImageDraw, ImageFont
    folder = os.path.join(CARDS, kind)
    files = sorted(f for f in os.listdir(folder) if f.endswith('.png'))
    if kind == 'parts':
        files = [f for f in files if f.endswith(' - three.png')]
    if not files:
        return None
    pictures = [Image.open(os.path.join(folder, f)).convert('RGB') for f in files]
    w, h = pictures[0].size
    columns = columns or (6 if kind == 'materials' else 5)
    rows = (len(files) + columns - 1) // columns
    label_h = 30
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font = ImageFont.truetype(font_path, 14) if os.path.exists(font_path) else ImageFont.load_default()
    out = Image.new('RGB', (columns * (w + 4), rows * (h + label_h + 4)), (16, 16, 18))
    draw = ImageDraw.Draw(out)
    for k, (f, picture) in enumerate(zip(files, pictures)):
        x, y = (k % columns) * (w + 4), (k // columns) * (h + label_h + 4)
        out.paste(picture.resize((w, h)), (x, y))
        label = f[:-4].replace(' - three', '')
        draw.text((x + 4, y + h + 6), label[:48], font=font, fill=(225, 225, 225))
    path = os.path.join(CARDS, '%s - all.jpg' % kind)
    out.save(path, quality=88)
    return path


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Draw the store\'s card pictures.')
    parser.add_argument('kind', choices=['part', 'material', 'sheet'])
    parser.add_argument('name', nargs='?', default='')
    parser.add_argument('--views', default='three,close')
    parser.add_argument('--size', type=int, default=420)
    parser.add_argument('--samples', type=int, default=32)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--option', action='append', default=[], help='a part option as key=value (true/false/numbers understood)')
    args = parser.parse_args(argv)
    if args.kind == 'part':
        options = {}
        for item in args.option:
            key, value = item.split('=', 1)
            lowered = value.lower()
            if lowered in ('true', 'false'):
                options[key] = lowered == 'true'
            else:
                try:
                    options[key] = float(value) if '.' in value else int(value)
                except ValueError:
                    options[key] = value
        written, size_m = part_cards(args.name, views=args.views.split(','), size=args.size, samples=args.samples, seed=args.seed, options=options)
        print('\n'.join(written))
    elif args.kind == 'material':
        wanted = store.names('materials') if args.name == 'all' else [args.name]
        for name in wanted:
            print(material_card(name, samples=min(args.samples, 24)))
    else:
        print(sheet(args.name or 'materials'))


if __name__ == '__main__':
    main()
