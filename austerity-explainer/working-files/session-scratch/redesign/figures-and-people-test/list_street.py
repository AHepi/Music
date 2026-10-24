import bpy
from collections import Counter
print('COLLECTIONS', [(c.name, len(c.objects)) for c in bpy.data.collections])
names = sorted(o.name for o in bpy.data.objects)
prefixes = Counter(n.rstrip('0123456789.').rstrip('_') for n in names)
print('PREFIXES', prefixes.most_common(60))
for o in bpy.data.objects:
    if o.type == 'LIGHT': print('LIGHT', o.name, tuple(round(v,2) for v in o.location), o.data.energy)
    if o.type == 'CAMERA': print('CAMERA', o.name)
