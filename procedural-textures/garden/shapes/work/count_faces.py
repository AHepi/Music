import sys, re
import bpy
tot = 0
rows = []
for ob in bpy.data.objects:
    if ob.type == 'MESH' and (ob.get('garden_owner') == 'shapes' or ob.name.startswith(('Rock', 'Pond edge', 'Stepping', 'Gravel', 'Raked'))):
        rows.append((len(ob.data.polygons), ob.name)); tot += len(ob.data.polygons)
rows.sort(reverse=True)
print('TOTAL faces in my objects', tot)
for r in rows[:14]: print('  ', r)
