"""What this does (scratch, round 5 W4 helper): runs assemble_works.py in its own namespace (W4 state), prints where the
W4 corner's things and the No. 2 board's two halves are, and draws close-up pictures from W4's composed spot with a
narrow lens aimed (only for these looks) at the board and at the corner group.
Use: blender -b works-lane.blend --python look_close.py -- --assemble PATH --out FOLDER [--state w4]"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
def option(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
ASSEMBLE, OUT = option('--assemble'), option('--out')
os.makedirs(OUT, exist_ok=True)
g = {'__name__': '__main__', '__file__': ASSEMBLE}
exec(compile(open(ASSEMBLE).read(), ASSEMBLE, 'exec'), g)
g['set_state'](option('--state', 'w4'))
for name in ('gate-board-no-2', 'gate-board-no-2-back', 'w4-jacket', 'w4-peg', 'w4-crate-table', 'w4-cap', 'w4-mug', 'w4-wages', 'w4-upturned-crate'):
    o = bpy.data.objects.get(name)
    if o is None:
        print('look_close: missing', name)
        continue
    low, high = g['bounds_of'](g['parts_of'](o))
    print('look_close:', name, 'from', [round(v, 3) for v in low], 'to', [round(v, 3) for v in high], 'rotation', [round(math.degrees(v), 1) for v in o.rotation_euler])
camera = g['put_camera']('w4', 'composed', g['FILM_FOV'])
eye = camera.location.copy()
for label, target, fov, size in (('board', (3.5, 22.05, 4.4), 14.0, (900, 500)), ('corner', (1.5, 23.0, 1.15), 14.0, (700, 1000))):
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = (Vector(target) - eye).to_track_quat('-Z', 'Y')
    camera.data.sensor_fit = 'VERTICAL' if size[1] >= size[0] else 'HORIZONTAL'
    camera.data.angle = math.radians(fov)
    g['render'](os.path.join(OUT, f'close-{label}.png'), size[0], size[1], 16)
