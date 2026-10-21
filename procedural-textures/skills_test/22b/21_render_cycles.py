# Trial 22b: draws the door camera of a blend file with Cycles (the "truth" renderer) using the street's own Cycles settings, on the rented card.
# Run: blender -b --disable-autoexec FILE.blend --python 21_render_cycles.py -- OUT.png WIDTH HEIGHT SAMPLES
# It saves nothing but the picture.
import os
import sys
import time

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/street_wet/tools')
import apply_wetness_to_set as aw  # noqa: E402

out, w, h, samples = sys.argv[sys.argv.index('--') + 1:][:4]
scene = bpy.context.scene
aw.cycles_settings(scene, int(w), int(h), int(samples))
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type != 'CPU']
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            if gpus:
                scene.cycles.device = 'GPU'
                print('CYCLES DEVICE', kind, [d.name for d in gpus])
                break
        except Exception as exc:
            print('device try failed', kind, exc)
except Exception as exc:
    print('no card for Cycles', exc)
os.makedirs(os.path.dirname(out), exist_ok=True)
scene.render.filepath = out
t = time.time()
bpy.ops.render.render(write_still=True)
print('DRAWN', out, round(time.time() - t, 1), 's', flush=True)
