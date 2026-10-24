import sys
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy
from apply import kit as wk
k = wk.Kit.load('japanese_courtyard')
rm = k.role_map
rows = []
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        rows.append((o.name, rm.primary.get(o.name), o.name in rm.never_objects, [s.material.name for s in o.material_slots if s.material][:2], o.hide_render))
for r in rows:
    if r[1] is None: print('NOROLE', r)
print('VERANDA', [r for r in rows if 'Veranda' in r[0]])
print('EMPTIES', [(o.name, o.empty_display_type) for o in bpy.context.scene.objects if o.type=='EMPTY'])
print('never', sum(1 for r in rows if r[2]), 'role', sum(1 for r in rows if r[1]), 'total', len(rows))
