import bpy
for c in bpy.data.collections:
    if c.name in ('colliery', 'street', 'ground', 'lamps', 'sky', 'cameras'):
        print('COLL', c.name, [o.name for o in c.objects])
sc = bpy.context.scene
cam = sc.camera
print('CAM parent', cam.parent, 'rotmode', cam.rotation_mode, 'quat', tuple(round(v,4) for v in cam.rotation_quaternion), 'sensor_fit', cam.data.sensor_fit)
print('view layer passes: crypto', sc.view_layers[0].use_pass_cryptomatte_object)
print('eevee', sc.eevee.use_raytracing, sc.eevee.taa_render_samples)
print('markers/anim', sc.timeline_markers[:], cam.animation_data)
