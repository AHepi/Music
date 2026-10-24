import bpy, json, math
out = {}
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name.startswith(('lamp_', 'door', 'chimney', 'wheel_', 'engine', 'marker')):
        out[o.name] = [round(v, 3) for v in o.matrix_world.translation]
cam = bpy.data.objects.get('main_camera')
out['main_camera'] = [round(v, 3) for v in cam.matrix_world.translation] if cam else None
cols = {c.name: len(c.objects) for c in bpy.data.collections}
print('MARKERS', json.dumps(out))
print('COLLECTIONS', json.dumps(cols))
names = sorted(o.name for o in bpy.data.objects if o.type == 'MESH')
print('MESHES', len(names), names[:80])
