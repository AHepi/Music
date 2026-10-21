# What this does: prints the overall size of the street file, and the biggest objects by size. Changes nothing.
import bpy
from mathutils import Vector
sc = bpy.context.scene
rows = []
for o in sc.objects:
    if o.type != 'MESH': continue
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    rows.append((o.name, lo, hi, (hi - lo).length))
lo = Vector([min(r[1][i] for r in rows) for i in range(3)]); hi = Vector([max(r[2][i] for r in rows) for i in range(3)])
print('ALL lo', tuple(round(v, 1) for v in lo), 'hi', tuple(round(v, 1) for v in hi), 'diag', round((hi - lo).length, 1))
for n, l, h, d in sorted(rows, key=lambda r: -r[3])[:12]:
    print('BIG', n, 'diag', round(d, 1), 'lo', tuple(round(v, 1) for v in l), 'hi', tuple(round(v, 1) for v in h))
# diag without the far backdrop
keep = [r for r in rows if not (r[0].startswith('moorland') or r[0].startswith('sky'))]
lo2 = Vector([min(r[1][i] for r in keep) for i in range(3)]); hi2 = Vector([max(r[2][i] for r in keep) for i in range(3)])
print('WITHOUT backdrop diag', round((hi2 - lo2).length, 1), tuple(round(v, 1) for v in lo2), tuple(round(v, 1) for v in hi2))
for r in rows:
    if r[0].startswith('moorland') or r[0].startswith('sky') or r[0] in ('ground',):
        print('BACKDROP', r[0], round(r[3], 1))
