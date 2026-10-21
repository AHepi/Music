# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A quick look inside a street file (the street copy, or the film's lockout shot file opened read-only; nothing is saved): lists every object that has a mesh with its
# name, its material names, where it stands (bounding box in street metres) and how many faces it has, so that the rubbish mask knows what stands on the ground.
# Run: blender -b --disable-autoexec FILE --python inspect_objects.py -- OUT_TEXT_FILE
import sys

import bpy
from mathutils import Vector

out = sys.argv[sys.argv.index('--') + 1]
depsgraph = bpy.context.evaluated_depsgraph_get()
rows = []
for obj in bpy.context.scene.objects:
    if obj.type not in ('MESH', 'LIGHT', 'CAMERA', 'CURVE', 'EMPTY'):
        continue
    if obj.type == 'MESH':
        ev = obj.evaluated_get(depsgraph)
        corners = [obj.matrix_world @ Vector(c) for c in ev.bound_box]
        lo = [min(c[i] for c in corners) for i in range(3)]
        hi = [max(c[i] for c in corners) for i in range(3)]
        mats = [m.name if m else None for m in obj.data.materials]
        rows.append(f"{obj.name:44s} MESH faces={len(obj.data.polygons):7d} x[{lo[0]:7.2f},{hi[0]:7.2f}] y[{lo[1]:7.2f},{hi[1]:7.2f}] z[{lo[2]:6.2f},{hi[2]:6.2f}] hide_render={obj.hide_render} mats={mats} parent={obj.parent.name if obj.parent else None} inst={obj.instance_type}")
    else:
        p = obj.matrix_world.translation
        rows.append(f"{obj.name:44s} {obj.type} at ({p.x:.2f},{p.y:.2f},{p.z:.2f}) hide_render={obj.hide_render}")
open(out, 'w').write('\n'.join(rows) + '\n')
print('WROTE', out, len(rows), flush=True)
