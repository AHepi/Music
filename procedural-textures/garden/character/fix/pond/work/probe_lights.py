import bpy, math
from mathutils import Vector
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        d = o.matrix_world.to_3x3() @ Vector((0, 0, -1))
        print(o.name, o.data.type, 'energy', round(o.data.energy, 2), 'color', tuple(round(c, 2) for c in o.data.color), 'dir', tuple(round(x, 3) for x in d), 'elev_deg', round(math.degrees(math.asin(-d.z)), 1) if o.data.type == 'SUN' else '', 'loc', tuple(round(x, 2) for x in o.location), 'lightgroup', o.lightgroup)
w = bpy.context.scene.world
print('world', w.name if w else None)
