import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=8; sc.cycles.use_denoising=True
sc.render.resolution_x=96; sc.render.resolution_y=64; sc.render.resolution_percentage=100
bpy.ops.mesh.primitive_plane_add(size=6); bpy.ops.mesh.primitive_uv_sphere_add(location=(0,0,1))
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); cam.location=(0,-6,3); cam.rotation_euler=(1.1,0,0); sc.camera=cam
for n,loc,e in (('a',(2,-2,4),500),('b',(-2,-2,4),300)):
    l=bpy.data.lights.new(n,'POINT'); l.energy=e; o=bpy.data.objects.new(n,l); o.location=loc; sc.collection.objects.link(o); o.lightgroup=n
vl=bpy.context.view_layer
for n in ('a','b'): bpy.ops.scene.view_layer_add_lightgroup(name=n)
sc.render.image_settings.media_type='MULTI_LAYER_IMAGE'
sc.render.image_settings.file_format='OPEN_EXR_MULTILAYER'
sc.render.filepath='proc-work/garden/check/tmp/tiny'
bpy.ops.render.render(write_still=True)
print('TINY_DONE')
