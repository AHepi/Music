import bpy, re, json
from mathutils import Vector
out = {}
def bb(o):
    pts=[o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(p[i] for p in pts),2) for i in range(3)]+[round(max(p[i] for p in pts),2) for i in range(3)]
pick = [r'^right_row_a_cottage_0[1-4]_(rainwater|doorway|trim)$', r'^left_row_a_cottage_0[1-3]_(rainwater|doorway)$', r'^gas_lamp_\d_post$', r'^right_row_b_cottage_01_doorway$', r'^right_row_a_cottage_01_walls$', r'^left_row_a_cottage_01_walls$']
for o in bpy.data.objects:
    for p in pick:
        if re.match(p, o.name):
            out[o.name] = dict(type=o.type, bbox=bb(o), loc=[round(v,2) for v in o.matrix_world.translation], rot_z=round(o.matrix_world.to_euler().z*57.2958,1), mesh=o.data.name if o.data else None)
lights = [(l.name, l.data.type, round(l.data.energy,1), [round(v,3) for v in (l.matrix_world.to_quaternion() @ Vector((0,0,1)))]) for l in bpy.data.objects if l.type=='LIGHT' and not re.search('window_light|lamp_|gas_lamp|engine', l.name)]
out['_lights']=lights
out['_doorway_count']=len([o for o in bpy.data.objects if o.name.endswith('_doorway')])
ys = sorted(round(o.matrix_world.translation.y,1) for o in bpy.data.objects if re.match(r'^right_row_a_cottage_\d+_doorway$', o.name))
out['_right_a_door_y']=ys
ys = sorted(round(o.matrix_world.translation.y,1) for o in bpy.data.objects if re.match(r'^left_row_a_cottage_\d+_doorway$', o.name))
out['_left_a_door_y']=ys
print('PROBE'+json.dumps(out))
