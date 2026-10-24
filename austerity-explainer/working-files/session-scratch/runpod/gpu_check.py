# What this does: run inside Blender on the rented machine; prints which graphics system Blender uses, then draws the default scene with EEVEE
# and with Cycles on the graphics card (OptiX), and prints how long each took.
import time, bpy, gpu
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 540, 960, 100
scene.render.engine = 'BLENDER_EEVEE'
scene.render.filepath = '/workspace/test/eevee.png'
started = time.time(); bpy.ops.render.render(write_still=True); print('EEVEE SECONDS', round(time.time() - started, 2))
try:
    print('GPU BACKEND', gpu.platform.backend_type_get(), '|', gpu.platform.vendor_get(), '|', gpu.platform.renderer_get(), '|', gpu.platform.version_get())
except Exception as problem:
    print('GPU BACKEND unknown', problem)
started = time.time(); bpy.ops.render.render(write_still=True); print('EEVEE SECOND RUN SECONDS', round(time.time() - started, 2))
preferences = bpy.context.preferences.addons['cycles'].preferences
preferences.compute_device_type = 'OPTIX'
preferences.refresh_devices()
for device in preferences.devices:
    device.use = True
print('CYCLES DEVICES', [(d.name, d.type, d.use) for d in preferences.devices])
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64
scene.render.filepath = '/workspace/test/cycles.png'
started = time.time(); bpy.ops.render.render(write_still=True); print('CYCLES SECONDS', round(time.time() - started, 2))
