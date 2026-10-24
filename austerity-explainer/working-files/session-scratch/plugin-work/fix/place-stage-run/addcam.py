import bpy, math
from mathutils import Vector
scene = bpy.context.scene
for name, loc in (('Camera A', (7.5, -9.0, 4.0)), ('Camera B', (-6.0, -8.0, 3.0))):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    cam.location = loc
    direction = Vector((0, 0, 1.2)) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = bpy.data.objects['Camera A']
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath('//hut-view.blend'))
