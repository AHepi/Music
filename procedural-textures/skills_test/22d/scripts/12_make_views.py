# What this does (plain words)
# --------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22d. Opens street_litter.blend and writes small variants of it for drawing: a chosen camera and, where wanted, heavier litter settings
# (the tree's own inputs). Only the litter modifier's inputs and the camera change; nothing else in the street.
# Run: blender -b --disable-autoexec --factory-startup set_copy/street_litter.blend --python scripts/12_make_views.py -- OUT_FOLDER
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bx_gn as G  # noqa: E402

OUT = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
host = bpy.data.objects['gutter_litter']
md = host.modifiers['Gutter Litter']
T = math.tan(math.radians(4.0))
gz = lambda y: min(y, 76.0) * T  # noqa: E731

VIEWS = {   # name: (eye, aim, vertical fov degrees)
    'lampfoot': ((0.8, 7.6, gz(7.6) + 0.9), (2.3, 10.3, gz(10.3) + 0.0), 35.0),
    'alongside': ((1.55, 6.0, gz(6.0) + 0.32), (2.4, 9.5, gz(9.5) + 0.02), 38.0),
    'kerbtop': ((0.2, 12.5, gz(12.5) + 1.4), (2.35, 15.5, gz(15.5) + 0.0), 38.0),
}
SETTINGS = {
    'shipped': {},
    'none': {'Paper Density': 0.0, 'Leaf Density': 0.0, 'Bottle Density': 0.0},   # the modifier stays ON (muting it would show the bare grey host strip)
    'messy': {'Paper Density': 3.5, 'Leaf Density': 9.0, 'Bottle Density': 0.5, 'Clumping': 0.5, 'Seed': 11},
}
RUNS = [('film', 'messy'), ('film', 'shipped'), ('lampfoot', 'none'), ('lampfoot', 'shipped'), ('lampfoot', 'messy'), ('alongside', 'messy'), ('alongside', 'none'), ('kerbtop', 'messy')]
base = G.get_inputs(md)
for view, setting in RUNS:
    if view == 'film':
        cam = bpy.data.objects['main_camera']          # the film's own main camera, untouched
    else:
        eye, aim, fov = VIEWS[view]
        cam = bpy.data.objects.get('litter_close_camera')
        cam.data.angle_y = math.radians(fov)
        cam.location = Vector(eye)
        cam.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    G.set_inputs(md, dict({k: base[k] for k in SETTINGS['messy']}, **SETTINGS[setting]))
    scene.camera = cam
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'street_litter_{view}_{setting}.blend'), copy=True)
    print('WROTE', view, setting, 'instances', len(G.instance_transforms(host)))
