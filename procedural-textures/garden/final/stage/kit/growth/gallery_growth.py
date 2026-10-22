# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE PIECE GALLERY (Blender code): every variant of every kind of the piece library standing on a plain grey-brown ground at real size, one kind to a row, seen from a low oblique
# camera, dry and wet. Used for the sheet and for checking by eye that the pieces are not gems and matchsticks. Any scene file will do (the ground and the lights are made here).
#     blender -b --disable-autoexec ANY.blend --python growth/gallery_growth.py -- OUT_FOLDER [WIDTH HEIGHT SAMPLES] [kind,kind,...]
# Writes gallery_dry.jpg, gallery_wet.jpg, gallery_faces.json (faces and sizes of every variant). The pieces use their plain species colours here (GAIN 1): the plate brightening is for the
# dusk-lit plate, not for a neutral light.
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from growth import pieces  # noqa: E402


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    out = args[0]
    w, h, samples = (int(args[1]), int(args[2]), int(args[3])) if len(args) >= 4 else (1800, 1100, 48)
    wanted = args[4].split(',') if len(args) >= 5 else None
    os.makedirs(out, exist_ok=True)
    scene = bpy.context.scene
    for obj in list(scene.objects):                       # a clean stage: hide everything of the scene file
        obj.hide_render = True
    lib = pieces.Library()
    names = wanted or list(lib.species['kinds'])
    lib.build(names)
    pieces.set_value_node('GAIN', 1.0)
    row_gap = 0.0
    placed = []
    y = 0.0
    max_x = 0.0
    for name in names:
        info = lib.kinds[name]
        x = 0.0
        row_depth = max(info['widths'])
        for obj in info['objects']:
            width = max(obj['wk_width_m'], 0.03)
            inst = bpy.data.objects.new('gallery_' + obj.name, obj.data)
            inst.location = (x + width / 2.0, y, 0.0)
            scene.collection.objects.link(inst)
            placed.append(inst)
            x += width + 0.045
        max_x = max(max_x, x)
        y += row_depth + 0.05
    ground = bpy.data.objects.new('gallery_ground', bpy.data.meshes.new('gallery_ground'))
    ground.data.from_pydata([(-0.3, -0.3, -0.001), (max_x + 0.3, -0.3, -0.001), (max_x + 0.3, y + 0.1, -0.001), (-0.3, y + 0.1, -0.001)], [], [(0, 1, 2, 3)])
    scene.collection.objects.link(ground)
    mat = bpy.data.materials.new('gallery_ground')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.084, 0.08, 1.0)
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
    ground.data.materials.append(mat)
    sun = bpy.data.objects.new('gallery_sun', bpy.data.lights.new('gallery_sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    scene.collection.objects.link(sun)
    scene.world = bpy.data.worlds.new('gallery_world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.35, 0.40, 0.45, 1.0)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
    cam = bpy.data.objects.new('gallery_camera', bpy.data.cameras.new('gallery_camera'))
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y = math.radians(36)
    scene.collection.objects.link(cam)
    centre = Vector((max_x / 2.0, y / 2.0 - 0.1, 0.03))
    cam.location = centre + Vector((0.0, -y * 0.75 - 0.5, y * 0.85 + 0.45))
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = w, h, 100
    scene.eevee.taa_render_samples = samples
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 90
    for state, wet in (('dry', 0.0), ('wet', 0.85)):
        pieces.set_wetness(wet)
        scene.render.filepath = os.path.join(out, f'gallery_{state}.jpg')
        bpy.ops.render.render(write_still=True)
    json.dump({k: dict(faces=v['faces'], widths_cm=[round(x * 100, 1) for x in v['widths']], heights_cm=[round(x * 100, 1) for x in v['heights']]) for k, v in lib.kinds.items()}, open(os.path.join(out, 'gallery_faces.json'), 'w'), indent=1)
    print('GALLERY DONE', flush=True)


if __name__ == '__main__':
    main()
