# What this does: lists cameras, lights, collections and object counts of the street COPY; changes and saves nothing.
import bpy, math
sc = bpy.context.scene
print('FILE', bpy.data.filepath)
print('ENGINE', sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, 'view', sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
print('ACTIVE CAMERA', sc.camera.name if sc.camera else None)
for o in sc.objects:
    if o.type == 'CAMERA':
        d = o.data
        print('CAM', o.name, 'loc', tuple(round(v, 3) for v in o.location), 'rot_deg', tuple(round(math.degrees(v), 2) for v in o.rotation_euler), 'lens', d.lens, 'sensor', d.sensor_width, d.sensor_fit, 'fov_deg', round(math.degrees(d.angle), 2))
n = {}
for o in sc.objects:
    n[o.type] = n.get(o.type, 0) + 1
print('COUNTS', n)
for o in sc.objects:
    if o.type == 'LIGHT':
        print('LIGHT', o.name, o.data.type, round(o.data.energy, 1), tuple(round(v, 2) for v in o.location))
print('COLLECTIONS', [(c.name, len(c.objects)) for c in bpy.data.collections])
print('EMPTIES', [o.name for o in sc.objects if o.type == 'EMPTY'][:80])
print('WORLD', tuple(sc.world.node_tree.nodes['Background'].inputs['Color'].default_value), sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value)
names = sorted(o.name for o in sc.objects if o.type == 'MESH')
print('MESHES', len(names), names[:200])
