"""
What this file does: saves a copy of a scene with its camera moved to stand on the sand and look up the shore,
the sea on the right, so the water's edges (wet band, foam, swash, wrack line, driftwood) can be seen and checked.
It was made for the bach from the first blind test; the spot and the target are that beach's.

    python3 shore_view_camera.py -- SCENE.blend SCENE-shore-view.blend
"""
import sys

import bpy
from mathutils import Vector

source, target_file = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=source)
camera = bpy.context.scene.camera
camera.location = Vector((3.2, -6.5, 1.65))
looking_at = Vector((6.5, 18.0, 0.6))
camera.rotation_euler = (looking_at - camera.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=target_file)
