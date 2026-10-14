# What this does: checks the signs' lettering can be read on a phone. It draws each sign at the
# film's full size (1080 x 1920) with the sign filling a fifth of the frame width (216 pixels), seen
# from the front and a little to one side at dusk-ish light, and saves the frames for a look.
#
# Run: DISPLAY=:94 blender -b --python readability_test.py -- OUT_FOLDER

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_library as library  # noqa: E402
import render_contact_sheet as sheet  # noqa: E402

TESTS = [
    # (prop, the sign's width in metres, the sign's centre (x, y, z) in the prop)
    ('colliery-name-board', 2.4, (0, 0, 3.55)),
    ('notice-paper', 0.5, (0, 0, 0.35)),
    ('notice-on-board', 0.5, (0, 0, 0.46)),
]

if __name__ == '__main__':
    out = sys.argv[sys.argv.index('--') + 1]
    os.makedirs(out, exist_ok=True)
    for name, sign_width, centre in TESTS:
        library.empty_scene()
        camera = sheet.stage((1080, 1920))
        bpy.context.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
        bpy.ops.import_scene.gltf(filepath=os.path.join(library.PROPS_FOLDER, f'{name}.glb'))
        camera.data.lens = 35
        # the frame's width at the sign's distance must be five sign widths
        frame_width = sign_width * 5
        horizontal_fov = 2 * math.atan(camera.data.sensor_width / 2 / camera.data.lens)
        distance = frame_width / 2 / math.tan(horizontal_fov / 2)
        target = Vector(centre)
        camera.location = target + Vector((math.sin(math.radians(18)) * distance, -math.cos(math.radians(18)) * distance, 0.1 * distance))
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.sensor_fit = 'HORIZONTAL'
        bpy.context.scene.render.filepath = os.path.join(out, f'read-{name}.png')
        bpy.ops.render.render(write_still=True)
        print('drew', name)
