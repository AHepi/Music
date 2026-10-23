"""What this does: measures, inside Blender, which sun the wear layers' shade uses (lessons round: the plan masks used to assume a sun at 135
degrees compass and 45 up, whatever the scene's own sun). On the open scene it records light.scene_sun_direction() and the plan masks' record
with one sun lamp as it is, with the sun turned to the opposite side (the shade mask must change), with a second sun lamp added (the fallback),
and with no sun lamp at all (the fallback). It writes the numbers as JSON; the test decides.
Run: blender -b --disable-autoexec SCENE.blend --python probe_sun.py -- PLACE_KIT_FOLDER OUT.json
"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, arguments[0])
out_path = arguments[1]
from place_kit import light, settings_file  # noqa: E402
from place_kit.wear import masks  # noqa: E402

settings = settings_file.Settings({'place': 'sun probe'})
result = {}


def aim(sun, compass, height):
    toward = Vector((math.cos(math.radians(compass)) * math.cos(math.radians(height)), math.sin(math.radians(compass)) * math.cos(math.radians(height)),
                     math.sin(math.radians(height))))
    sun.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()


def measure(label):
    plan, record = masks.build_plan_masks(settings, quick=True)
    result[label] = {'direction': light.scene_sun_direction(), 'record_sun': record['sun'], 'shade': plan.grids['shade'].astype(int).tolist()}


sun = bpy.data.objects['Sun']
aim(sun, 20.0, 35.0)
measure('one sun at compass 20, 35 up')
aim(sun, 200.0, 35.0)
measure('one sun at compass 200, 35 up')
second = bpy.data.objects.new('Second sun', bpy.data.lights.new('Second sun', 'SUN'))
second.data.energy = 1.0
bpy.context.scene.collection.objects.link(second)
measure('two sun lamps')
bpy.data.objects.remove(second)
bpy.data.objects.remove(sun)
measure('no sun lamp')
a, b = (np.array(result[k]['shade']) for k in ('one sun at compass 20, 35 up', 'one sun at compass 200, 35 up'))
result['shade_cells_that_differ_when_the_sun_turns'] = int((a != b).sum())
for value in result.values():
    if isinstance(value, dict):
        value.pop('shade', None)
json.dump(result, open(out_path, 'w'), indent=1)
print('probe_sun: written', out_path)
