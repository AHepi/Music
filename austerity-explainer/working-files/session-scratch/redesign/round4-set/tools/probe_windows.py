import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
scene = bpy.context.scene
for view, prefixes in (('w1', ('left_row_a_cottage_04_', 'left_row_a_cottage_03_')), ('w2', ('right_row_a_cottage_04_', 'right_row_a_cottage_03_'))):
    cam = bpy.data.objects[f'camera-{view}']
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(prefixes) and ('glass' in o.name or 'door' in o.name or 'fanlight' in o.name):
            c = sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8
            p = world_to_camera_view(scene, cam, c)
            mats = [m.name for m in o.data.materials if m]
            print('PROBE', view, o.name, round(p.x, 3), round(1 - p.y, 3), round(p.z, 2), mats[:3])
