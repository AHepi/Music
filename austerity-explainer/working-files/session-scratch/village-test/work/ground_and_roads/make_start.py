import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
print('objects', len(bpy.data.objects), 'scene', scene.name, 'world', scene.world)
bpy.ops.wm.save_as_mainfile(filepath='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/scene/start.blend', compress=True)
print('saved', flush=True)
