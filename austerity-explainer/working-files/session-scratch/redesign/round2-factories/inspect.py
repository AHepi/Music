import bpy, sys
for o in bpy.data.objects:
    if o.type == 'MESH':
        zs = [ (o.matrix_world @ v.co) for v in o.data.vertices]
        lo = min(p.z for p in zs); ylo = min(p.y for p in zs)
        if lo < -0.15 or ylo < 0.5:
            print('ODD', o.name, round(lo,2), round(ylo,2), tuple(round(c,2) for c in o.location), tuple(round(c,2) for c in o.rotation_euler))
print('COLLECTIONS', [c.name for c in bpy.data.collections])
