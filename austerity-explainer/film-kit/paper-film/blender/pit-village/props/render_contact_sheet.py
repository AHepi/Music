# What this does: draws every prop in index.json on its own, lit on a neutral grey ground from a
# three-quarter front view (EEVEE, small and quick), into one picture per prop. Then make_sheet.py
# lays them out as a labelled contact sheet.
#
# Run (EEVEE needs a virtual screen):
#   Xvfb :94 -screen 0 1920x1080x24 &
#   DISPLAY=:94 blender -b --python render_contact_sheet.py -- OUT_FOLDER [--size 1024] [prop-file-name ...]
#   (add --library inflation-chapter-2-newcomers, or a folder, to draw another library's props)

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_library as library  # noqa: E402


def stage(size):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.film_transparent = False
    world = bpy.data.worlds.new('world'); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.44, 0.47, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
    ground = bpy.data.meshes.new('ground')
    ground.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
    ground_object = bpy.data.objects.new('ground', ground); scene.collection.objects.link(ground_object)
    grey = bpy.data.materials.new('ground'); grey.use_nodes = True
    grey.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.36, 0.36, 0.37, 1)
    grey.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    ground.materials.append(grey)
    sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN'))
    sun.data.energy = 3.2; sun.data.angle = math.radians(6); sun.data.color = (1.0, 0.94, 0.85)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35)); scene.collection.objects.link(sun)
    fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN'))
    fill.data.energy = 0.9; fill.data.color = (0.75, 0.85, 1.0)
    fill.rotation_euler = (math.radians(65), 0, math.radians(140)); scene.collection.objects.link(fill)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.data.lens = 50; scene.collection.objects.link(camera); scene.camera = camera
    return camera


def frame(camera, low, high, aspect):
    centre = (low + high) / 2
    radius = (high - low).length / 2
    direction = Vector((math.sin(math.radians(-32)) * -1, -math.cos(math.radians(32)), 0.42)).normalized()
    fov = camera.data.angle if aspect >= 1 else 2 * math.atan(math.tan(camera.data.angle / 2) * aspect)
    distance = radius / math.sin(fov / 2) * 1.02
    camera.location = centre + direction * distance
    camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.clip_end = distance * 4; camera.data.clip_start = distance / 200


if __name__ == '__main__':
    arguments = library.take_folder_settings(sys.argv[sys.argv.index('--') + 1:])
    # --size N draws larger pictures (for example 1024, as references for an image model)
    side = 420
    if '--size' in arguments:
        at = arguments.index('--size'); side = int(arguments[at + 1]); del arguments[at:at + 2]
    out_folder, only = arguments[0], arguments[1:]
    os.makedirs(out_folder, exist_ok=True)
    with open(library.INDEX_PATH) as f: index = json.load(f)
    size = (side, side)
    for entry in index:
        name = entry['file'][:-4]
        if only and name not in only: continue
        library.empty_scene()
        camera = stage(size)
        bpy.ops.import_scene.gltf(filepath=os.path.join(library.PROPS_FOLDER, entry['file']))
        bpy.context.view_layer.update()
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name != 'ground']
        low, high = library.bounds(meshes)
        frame(camera, low, high, size[0] / size[1])
        bpy.context.scene.render.filepath = os.path.join(out_folder, f'{name}.png')
        bpy.ops.render.render(write_still=True)
        print('drew', name)
