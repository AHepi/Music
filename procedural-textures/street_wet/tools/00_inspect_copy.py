# What this does: lists, for the COPY of the street (set_copy/street.blend), which objects wear which materials, which meshes are shared between objects,
# which texture-coordinate sets they have, where the gas lamps and cottages stand, and whether the pictures were found. It changes and saves nothing.
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/00_inspect_copy.py
import bpy
from collections import defaultdict
scene = bpy.context.scene
print('FILE', bpy.data.filepath)
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.has_data and i.size[0] == 0]
print('IMAGES', len(bpy.data.images), 'missing', missing)
by_material = defaultdict(list)
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    for slot in obj.material_slots:
        if slot.material:
            by_material[slot.material.name].append(obj.name)
for name, objs in sorted(by_material.items()):
    print('MAT', name, len(objs), objs[:3])
meshes = defaultdict(list)
for obj in scene.objects:
    if obj.type == 'MESH':
        meshes[obj.data.name].append(obj)
print('SHARED MESHES')
for name, objs in meshes.items():
    if len(objs) > 1:
        o = objs[0]
        print('  ', name, 'users', len(objs), 'mats', [m.name for m in o.data.materials], 'uv', [u.name for u in o.data.uv_layers], 'verts', len(o.data.vertices), 'rot', round(o.rotation_euler.z, 2), 'loc', tuple(round(v, 2) for v in o.location))
print('WALL OBJECTS')
for obj in scene.objects:
    if obj.type == 'MESH' and any((s.material and s.material.name in ('cottage_brick', 'cottage_stone')) for s in obj.material_slots) and obj.name.endswith('walls'):
        print('  ', obj.name, obj.data.name, [m.name for m in obj.data.materials], tuple(round(v, 2) for v in obj.location), round(obj.rotation_euler.z, 2), 'dims', tuple(round(v, 2) for v in obj.dimensions))
lamps = [o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'POINT' and o.data.energy > 200]
for o in lamps:
    print('LAMP', o.name, o.data.name, round(o.data.energy), tuple(round(v, 2) for v in o.location))
for o in scene.objects:
    if 'lamp' in o.name.lower() and o.type == 'MESH':
        print('LAMPMESH', o.name, tuple(round(v, 2) for v in o.location))
print('CAMERAS', [(o.name, tuple(round(v, 2) for v in o.location)) for o in scene.objects if o.type == 'CAMERA'], 'active', scene.camera.name)
print('RENDER', scene.render.engine, scene.render.resolution_x, scene.render.resolution_y, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure)
print('WORLD', tuple(scene.world.node_tree.nodes['Background'].inputs['Color'].default_value), scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value)
