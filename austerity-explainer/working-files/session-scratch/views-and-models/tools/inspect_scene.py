"""Scratch (views-and-models helper): writes the open Blender scene's structure as JSON (objects, parents, collections,
materials, world boxes, lights, camera), read-only. Use: blender -b FILE.blend --disable-autoexec --python inspect_scene.py -- OUT.json"""
import json
import sys

import bpy

out = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
bpy.context.view_layer.update()
objects = []
for o in scene.objects:
    corners = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box] if o.type in ('MESH', 'CURVE', 'FONT') else []
    entry = {'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None,
             'collections': [c.name for c in o.users_collection], 'hide_render': o.hide_render,
             'materials': [s.material.name for s in o.material_slots if s.material] if o.type == 'MESH' else [],
             'location': [round(v, 3) for v in o.matrix_world.translation]}
    if corners:
        entry['low'] = [round(min(c[i] for c in corners), 3) for i in range(3)]
        entry['high'] = [round(max(c[i] for c in corners), 3) for i in range(3)]
    if o.type == 'LIGHT':
        entry['light'] = {'kind': o.data.type, 'energy': o.data.energy}
    objects.append(entry)
collections = {c.name: {'children': [k.name for k in c.children], 'objects': len(c.objects)} for c in bpy.data.collections}
camera = scene.camera
json.dump({'file': bpy.data.filepath, 'camera': camera.name if camera else None,
           'camera_at': list(camera.matrix_world.translation) if camera else None,
           'collections': collections, 'objects': objects}, open(out, 'w'), indent=1)
print('inspect_scene: wrote', out, len(objects), 'objects')
