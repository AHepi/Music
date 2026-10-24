# Scratch: lists the street's gas lamps (glass and light) in street.blend, for the light planner's lamp test.
import bpy, json, sys
out = {}
for o in bpy.data.objects:
    if o.name.startswith('gas_lamp_'):
        if o.type == 'MESH':
            from mathutils import Vector
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            out[o.name] = {'type': o.type, 'box_low': [round(min(p[i] for p in pts), 3) for i in range(3)], 'box_high': [round(max(p[i] for p in pts), 3) for i in range(3)]}
        else:
            out[o.name] = {'type': o.type, 'at': [round(v, 3) for v in o.matrix_world.translation], 'energy': getattr(o.data, 'energy', None)}
json.dump(out, open(sys.argv[-1], 'w'), indent=1)
