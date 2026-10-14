# What this does: breaks a dressed scene on purpose, to test that the shot checker catches the fault.
# Run between the dressing script and shot_facts.py:
#   blender -b street.blend --python assemble_notice_corner.py --python tests/break_scene.py --python shot_facts.py -- \
#       --view end --break "wooden-pail:0,0,5.6" --check ... --facts ...
# --break takes NAME:dx,dy,dz (metres; several separated by ';'): moves every top-level object whose name
# starts with NAME by that much.
import sys

import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
moves = arguments[arguments.index('--break') + 1] if '--break' in arguments else ''
for move in filter(None, moves.split(';')):
    name, offset = move.split(':')
    offset = Vector(float(v) for v in offset.split(','))
    moved = [o for o in bpy.context.scene.objects if o.parent is None and o.name.startswith(name)]
    for o in moved:
        o.location += offset
    print(f'break_scene: moved {len(moved)} object(s) named {name}* by {tuple(offset)}')
bpy.context.view_layer.update()
