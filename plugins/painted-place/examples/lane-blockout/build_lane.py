"""
What this file does:
Builds a plain grey-box lane, the way a fresh builder would before dressing: boxes and cylinders only, every
object named with role words (wall, window lit, door, kerb, lamp post, lamp glass, puddle, roof, chimney smoke),
one camera at standing height looking down the lane. Nothing is textured and nothing is lit here: that is the
job of materials/apply_by_role.py and stage/look_stage.py. Saves lane.blend next to the --out path.

    blender -b --python build_lane.py -- --out FOLDER/lane.blend
    python3 build_lane.py --out FOLDER/lane.blend        (with the bpy module installed)

The lane runs along Y (the long way), as the street bundle's materials expect.
"""

import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Vector


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def box(name, centre, size, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(scale=True)
    return obj


def cylinder(name, centre, radius, height, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=height, location=centre)
    obj = bpy.context.object
    obj.name = name
    return obj


def plane(name, centre, size):
    bpy.ops.mesh.primitive_plane_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    return obj


def build(seed=5):
    rng = random.Random(seed)
    clear()
    # ground: road, pavements, kerbs
    plane('road setts', (0, 22, 0), (7.0, 80))
    for side in (-1, 1):
        box('pavement flags %s' % ('left' if side < 0 else 'right'), (side * 4.4, 22, 0.07), (1.8, 80, 0.14))
        box('kerb stone %s' % ('left' if side < 0 else 'right'), (side * 3.6, 22, 0.08), (0.2, 80, 0.16))
    # terraces: unequal buildings along both sides
    for side in (-1, 1):
        y = -9.0 if side < 0 else -6.5
        index = 0
        while y < 52:
            width = rng.uniform(5.5, 7.6)
            height = rng.uniform(11.0, 15.0)
            mid = y + width / 2
            face_x = side * 5.3
            label = '%s terrace %02d' % ('left' if side < 0 else 'right', index)
            box(label + ' wall', (face_x + side * 2.5, mid, height / 2), (5.0, width - 0.05, height))
            # roof: two tilted slabs meeting at a ridge
            ridge = height + 1.8
            for pitch in (-1, 1):
                box(label + ' roof slate', (face_x + side * 2.5 + pitch * 1.25, mid, (height + ridge) / 2),
                    (3.1, width + 0.2, 0.12), rotation=(0, pitch * math.radians(36), 0))
            box(label + ' chimney stack wall', (face_x + side * 3.6, mid + rng.uniform(-width * 0.3, width * 0.3), ridge + 0.6), (1.1, 0.8, 2.0))
            # windows in rows, a door on the ground floor
            columns = max(2, int(width / 2.0))
            spacing = width / (columns + 0.4)
            for floor in range(1, 4 if height < 13 else 5):
                z = 1.6 + floor * 2.9
                for column in range(columns):
                    wy = mid + (column - (columns - 1) / 2) * spacing
                    roll = rng.random()
                    kind = 'window lit' if roll < 0.12 else ('window dim' if roll < 0.27 else 'window dark')
                    box(label + ' window surround stone', (face_x - side * 0.04, wy, z), (0.08, 1.3, 1.9))
                    box(label + ' ' + kind, (face_x - side * 0.08, wy, z), (0.06, 1.0, 1.6))
            door_y = mid - (columns - 1) / 2 * spacing
            box(label + ' door surround stone', (face_x - side * 0.05, door_y, 1.35), (0.10, 1.5, 2.7))
            box(label + ' door wood', (face_x - side * 0.09, door_y, 1.25), (0.06, 1.1, 2.4))
            box(label + ' door step', (face_x - side * 0.25, door_y, 0.18), (0.45, 1.4, 0.08))
            for column in range(1, columns):
                wy = mid + (column - (columns - 1) / 2) * spacing
                box(label + ' window surround stone', (face_x - side * 0.04, wy, 1.7), (0.08, 1.3, 2.1))
                box(label + ' window dim', (face_x - side * 0.08, wy, 1.7), (0.06, 1.0, 1.8))
            box(label + ' downpipe iron', (face_x - side * 0.12, y + 0.3, height / 2), (0.1, 0.1, height - 0.3))
            y += width
            index += 1
    # the far end: a building across the lane with a gap on the right, so the lines meet beside it
    box('end tenement wall', (-1.5, 55, 7.0), (10.0, 5.0, 14.0))
    box('end tenement roof slate', (-1.5, 55, 14.8), (10.4, 5.4, 1.6))
    for wy in (-4.5, -1.5, 1.5):
        for z in (4.5, 7.4, 10.3):
            box('end tenement window surround stone', (wy, 52.46, z), (1.3, 0.08, 1.9))
            box('end tenement window ' + ('lit' if (wy, z) in ((-1.5, 7.4), (1.5, 4.5)) else 'dark'), (wy, 52.42, z), (1.0, 0.06, 1.6))
    # gas lamps
    for side, y in ((-1, 2.0), (1, 14.0), (-1, 27.0), (1, 40.0)):
        x = side * 4.0
        cylinder('lamp post iron %d' % y, (x, y, 1.9), 0.06, 3.6)
        box('lamp glass %d' % y, (x, y, 3.95), (0.34, 0.34, 0.5))
        box('lamp cap iron %d' % y, (x, y, 4.28), (0.5, 0.5, 0.12))
    # puddles in the gutter and the road's low spots
    for side, y, length in ((-1, 3.5, 2.4), (1, 9.0, 3.0), (-1, 16.0, 1.8), (1, 24.0, 2.6), (-1, 31.0, 2.0), (0.3, 12.0, 1.6)):
        plane('puddle water %d' % (y * 10), (side * 3.0 if abs(side) == 1 else side, y, 0.012), (1.1, length))
    # a hand cart against the left pavement
    box('cart bed wood', (-2.6, 6.0, 0.75), (1.1, 2.0, 0.12))
    for dy in (-0.8, 0.8):
        box('cart side plank wood', (-2.6, 6.0 + dy, 0.95), (1.1, 0.06, 0.4))
    for dx in (-0.6, 0.6):
        cylinder('cart wheel iron', (-2.6 + dx, 6.0, 0.55), 0.55, 0.06, vertices=24)
        bpy.context.object.rotation_euler = (0, math.radians(90), 0)
    box('cart shaft wood', (-2.6, 7.6, 0.6), (0.08, 1.4, 0.08))
    # smoke above two chimneys (a volume box)
    box('chimney smoke', (-7.9, 10.0, 19.5), (3.5, 3.0, 6.0))
    box('chimney smoke 2', (8.0, 24.0, 20.5), (4.0, 3.5, 6.5))
    # the camera: a standing person in the middle of the lane
    camera_data = bpy.data.cameras.new('lane camera')
    camera_data.lens = 32
    camera_data.sensor_width = 36
    camera = bpy.data.objects.new('lane camera', camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (0.3, -10.0, 1.65)
    target = Vector((0.6, 24.0, 3.2))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = camera
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    build()
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print('saved', out, 'objects:', len(bpy.data.objects))


if __name__ == '__main__':
    main()
