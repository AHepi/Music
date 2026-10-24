# What this does: lists, for a checker, the role of every object in a finished village and the cameras (read only, never saved).
import bpy, collections
scene = bpy.context.scene
roles = collections.Counter(o.get('place_role') for o in scene.objects)
print('roles', sorted(roles.items(), key=lambda kv: str(kv[0])))
for r in ('wall', 'plinth', 'foundation', 'fence', 'post'):
    names = [o.name for o in scene.objects if r in str(o.get('place_role'))][:12]
    print(r, names)
for o in scene.objects:
    if o.type == 'CAMERA':
        print('camera', o.name, tuple(round(v, 2) for v in o.matrix_world.translation), o.data.lens, o.data.sensor_width, o.data.sensor_fit)
print('render', scene.render.resolution_x, scene.render.resolution_y)
