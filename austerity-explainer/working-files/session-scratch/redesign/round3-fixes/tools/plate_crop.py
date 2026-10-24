# What this does (scratch check): run after the scratch copy of assemble_people_test.py, in the same Blender: draws
# only the part of the PLATE (1536 x 2730, the plate's lens 64.4 degrees) round the waiting men, at the plate's full
# pixel size (Blender's render border, cropped), so the figures can be judged as the painter will see them.
# Settings by environment: PLATE_CROP_OUT (the picture), PLATE_CROP_SAMPLES (default 32),
# PLATE_CROP_BOX (left,top,right,bottom as fractions of the plate, from its top left; default round the men).
import math
import os
import sys

import bpy

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village')
from set_dressing import render  # noqa: E402   (the plates' own render settings: engine, shadows)

out = os.environ['PLATE_CROP_OUT']
samples = int(os.environ.get('PLATE_CROP_SAMPLES', '32'))
left, top, right, bottom = (float(v) for v in os.environ.get('PLATE_CROP_BOX', '0.09,0.42,0.82,0.71').split(','))
scene = bpy.context.scene
camera = bpy.data.objects['main_camera']
camera.data.sensor_fit = 'VERTICAL'
camera.data.angle_y = math.radians(64.4)
scene.camera = camera
scene.render.use_border = True
scene.render.use_crop_to_border = True
scene.render.border_min_x, scene.render.border_max_x = left, right
scene.render.border_min_y, scene.render.border_max_y = 1 - bottom, 1 - top
render(out, 1536, 2730, samples)
print('plate_crop: wrote', out)
