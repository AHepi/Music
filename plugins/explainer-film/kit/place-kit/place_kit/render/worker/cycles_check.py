"""What this does: a quick proof that Cycles uses the graphics card on a worker. Run it with Blender on the worker:
    /workspace/blender/blender -b --disable-autoexec --python cycles_check.py -- OUT.png
It tries OptiX, then CUDA, then HIP, switches Cycles to the card found, draws one small picture of Blender's own start scene, and prints which devices were used
and how many seconds it took. If it prints only the processor, the card or its driver was not seen: tell the account owner instead of drawing finals.
"""
import sys
import time

import bpy

out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp/cycles_check.png'
preferences = bpy.context.preferences.addons['cycles'].preferences
used = 'CPU'
for kind in ('OPTIX', 'CUDA', 'HIP'):
    try:
        preferences.compute_device_type = kind
        preferences.get_devices()
    except (TypeError, ValueError):
        continue
    found = [device for device in preferences.devices if device.type == kind]
    if found:
        for device in preferences.devices:
            device.use = device.type == kind
        used = kind
        break
print('DEVICES', [(device.name, device.type, device.use) for device in preferences.devices])
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU' if used != 'CPU' else 'CPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 540, 960, 100
scene.render.filepath = out
started = time.time()
bpy.ops.render.render(write_still=True)
print('CYCLES DRAWN on', used, round(time.time() - started, 1), 's ->', out)
