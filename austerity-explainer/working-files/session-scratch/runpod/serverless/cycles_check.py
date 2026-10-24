# What this does: a quick proof that Cycles uses the graphics card on a pay-per-second worker: switches the street to Cycles with
# OptiX on the card, draws one small picture, and prints which devices were used and how long it took.
import bpy, sys, time
out = sys.argv[sys.argv.index('--') + 1]
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'OPTIX'
print('DEVICES', [(d.name, d.type, d.use) for d in prefs.devices])
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 540, 960, 100
scene.render.filepath = out
started = time.time()
bpy.ops.render.render(write_still=True)
print('CYCLES DRAWN', round(time.time() - started, 1), 's')
