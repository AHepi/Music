import bpy, os
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
bpy.ops.import_scene.gltf(filepath='/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models/factory-a.glb')
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        print('UVS', o.name, [u.name for u in o.data.uv_layers], len(o.data.polygons), [m.name for m in o.data.materials][:3])
imgs = [(i.name, i.size[:]) for i in bpy.data.images]
print('IMAGES', imgs)
