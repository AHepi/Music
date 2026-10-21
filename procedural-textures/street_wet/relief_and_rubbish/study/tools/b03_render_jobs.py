# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The runner for the study's pictures. It opens ONE street file (the street copy, or the film's lockout shot file opened READ-ONLY: it is never saved), puts the round 2
# wetness layer on every material, and then draws a LIST OF PICTURES ("jobs") from a job file, one after the other, so Blender is loaded only once per file.
# Each job says: which camera, which lighting (A to E), which wetness state, which variant of the road material (see b02_lighting_and_variants.py), size, samples.
# For every camera it also draws, once, the MASK picture (R = joint, G = stone face, B = road) that the measuring script needs.
# Optional key "after_apply": path of a Python script run once inside Blender after the layer is on (for a solution that is not a variant yet).
# Job file (JSON): {"masks": [["main", 540, 960]], "jobs": [{"name": "main_A_wet", "camera": "main", "light": "A", "state": "wet", "variant": "baseline", "args": {},
#                  "w": 540, "h": 960, "samples": 16}, ...]}
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 BLEND --python b03_render_jobs.py -- JOB_FILE OUT_FOLDER
# Writes OUT_FOLDER/<name>.png, OUT_FOLDER/<name>_seconds.txt, and OUT_FOLDER/mask_<camera>_<w>x<h>.png (only if missing). Skips a picture that already exists.
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import b02_lighting_and_variants as lv  # noqa: E402
import apply_wetness_to_set as aw  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
job_file, out_folder = args[0], args[1]
os.makedirs(out_folder, exist_ok=True)
spec = json.load(open(job_file))
scene = bpy.context.scene
cams = aw.cameras()
only_camera_names = set(j['camera'] for j in spec['jobs'])
print('FILE', bpy.data.filepath, 'jobs', len(spec['jobs']), flush=True)

for camera_name, w, h in spec.get('masks', []):
    path = os.path.join(out_folder, f'mask_{camera_name}_{w}x{h}.png')
    if os.path.exists(path):
        continue
    scene.camera = cams[camera_name]
    started = time.time()
    lv.render_mask(path, w, h)
    print('MASK', camera_name, round(time.time() - started, 1), 's', flush=True)

aw.apply(wetness=0.0, puddles=0.0)
if spec.get('after_apply'):
    # a script of the caller's own, run once after the layer is on: it can change the road's material (a new solution to be tested with the whole lighting set)
    exec(compile(open(spec['after_apply']).read(), spec['after_apply'], 'exec'), {'bpy': bpy, 'aw': aw, 'lv': lv, '__name__': 'after_apply'})
mix_info = []
tree = lv.road_tree()
for node in tree.nodes:
    if node.type == 'MIX':
        mix_info.append((node.name, [(s.name, s.type) for s in node.inputs]))
print('ROAD MIX NODE', mix_info[:1], flush=True)

for job in spec['jobs']:
    png = os.path.join(out_folder, job['name'] + '.png')
    if os.path.exists(png) or os.path.exists(png[:-4] + '.jpg'):
        print('SKIP', job['name'], flush=True)
        continue
    scene.camera = cams[job['camera']]
    print('ANISOTROPIC FILTER (before)', bpy.context.preferences.system.anisotropic_filter, flush=True)
    if job.get('aniso'):
        try:
            bpy.context.preferences.system.anisotropic_filter = job['aniso']
        except Exception as error:
            print('could not set the anisotropic filter', error, flush=True)
    lv.eevee_setup(job['w'], job['h'], job['samples'], raytracing=job.get('rt', True))
    lv.set_lighting(job['light'], job.get('light_args'))
    wet, pud = lv.parse_state(job['state'])
    aw.set_state(wet, pud)
    try:
        undo = lv.apply_variant(job.get('variant', 'baseline'), job.get('args'))
    except Exception:
        import traceback
        print('VARIANT FAILED', job['name'], flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        continue
    scene.render.filepath = png
    started = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        undo()
    seconds = round(time.time() - started, 1)
    open(os.path.join(out_folder, job['name'] + '_seconds.txt'), 'w').write(f'{seconds}\n')
    print('DRAWN', job['name'], seconds, 's', flush=True)
print('ALL JOBS DONE', flush=True)
