# What this does: a tiny check that Blender's EEVEE renderer works on this machine (it needs a virtual screen): draws a lit sphere on a floor.
import bpy
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
bpy.ops.mesh.primitive_plane_add(size=10)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); cam.location = (0, -6, 2); cam.rotation_euler = (1.3, 0, 0); scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 160, 120
scene.render.filepath = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/study/work/eevee_check.png'
bpy.ops.render.render(write_still=True)
print('EEVEE OK')
