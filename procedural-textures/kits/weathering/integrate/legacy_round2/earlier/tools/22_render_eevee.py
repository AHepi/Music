# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2: draws the street (the COPY, or a shot file opened read-only) with EEVEE, the fast renderer the film's PLATES are drawn with (the round 1 pictures were Cycles,
# which hides the speckle EEVEE shows). Any camera, any state, any size. Ray tracing is ON (the film's files have it off, but then puddles are pale flat patches; see the
# recipe note). States: today = the street exactly as it is (the layer not yet put on), dry = the layer on at 0, wet = wetness 0.85 / puddles 0.5, heavy = 1.0 / 0.8.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 BLEND --python tools/22_render_eevee.py -- OUT_FOLDER CAMERA STATES WIDTH HEIGHT SAMPLES [key=value ...]
#   BLEND:   set_copy/street.blend (the street), or one of the film project's shot files opened read-only (it is never saved: this script saves nothing)
#   CAMERA:  main | lockout | notice | close_road | wall_lamp    (main = the camera the file is set to)
#   STATES:  for example today,wet,heavy
#   key=value: a layer setting for every material (e.g. puddle_roughness=0.08) or a switch: rt=0 (ray tracing off), wetness=0.85 puddles=0.5 (what 'wet' means),
#   shadow_rays=4 shadow_steps=16 (EEVEE's soft shadow quality: the round 2 speckle cure), border=x0,x1,y0,y1 (draw only that part, 0..1,
#   y from the bottom), tag=NAME (adds NAME to the file names), settings=FILE.json (a file of per-material overrides, see apply_wetness_to_set.py)
#   one more state: wet_r1 = round 1's road and pavement settings (to see the speckle again; run it after the other states)
# Writes OUT_FOLDER/<camera>_<state><tag>.png and ..._seconds.txt
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out_folder, camera_name, states = args[0], args[1], args[2].split(',')
width, height, samples = int(args[3]), int(args[4]), int(args[5])
extra = [a for a in args[6:] if '=' in a]
options = {a.split('=', 1)[0]: a.split('=', 1)[1] for a in extra}
tag = options.pop('tag', '')
raytracing = options.pop('rt', '1') == '1'
border = options.pop('border', None)
settings_file = options.pop('settings', None)
wet_wetness = float(options.pop('wetness', 0.85))
wet_puddles = float(options.pop('puddles', 0.5))
shadow_rays = int(options.pop('shadow_rays', 4))          # round 2: 4 rays and 16 steps calm the soft-shadow noise that shows as speckle on a wet road (EEVEE's default is 1 and 6)
shadow_steps = int(options.pop('shadow_steps', 16))
overrides = {k: float(v) for k, v in options.items()}
if settings_file:
    for material_name, values in json.load(open(settings_file)).items():
        aw.MATERIALS.setdefault(material_name, {}).update(values)
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
scene.camera = cams[camera_name]
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = width, height
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = samples
scene.eevee.use_raytracing = raytracing
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = shadow_rays, shadow_steps
if hasattr(scene.eevee, 'shadow_pool_size') and width > 1080:
    # the same shadow memory settings the film's own plate script uses for pictures wider than 1080 (set_dressing.py, log 31)
    scene.eevee.shadow_pool_size = '1024'
    scene.eevee.shadow_resolution_scale = min(1.0, 1080 / width)
if border:
    x0, x1, y0, y1 = (float(v) for v in border.split(','))
    scene.render.use_border, scene.render.use_crop_to_border = True, False
    scene.render.border_min_x, scene.render.border_max_x, scene.render.border_min_y, scene.render.border_max_y = x0, x1, y0, y1
STATE_VALUES = {'dry': (0.0, 0.0), 'wet': (wet_wetness, wet_puddles), 'heavy': (1.0, 0.8)}
applied = False
for state in states:
    if state != 'today' and not applied:
        aw.apply(wetness=0.0, puddles=0.0, **overrides)
        applied = True
    if state in STATE_VALUES:
        aw.set_state(*STATE_VALUES[state])
    elif state == 'wet_r1':
        # round 1's road and pavement as they were (no smoothed relief picture, round 1's flatten and roughness), everything else as it now is: to see round 1's speckle again
        aw.set_state(wet_wetness, wet_puddles)
        for material_name, flatten, wet_roughness in (('street_setts', 0.35, 0.3), ('pavement_flags', 0.6, 0.45)):
            group = aw.APPLIED[material_name][0]
            group.inputs['Grain Fill'].default_value = 0.0
            group.inputs['Relief Flatten'].default_value = flatten
            group.inputs['Wet Roughness'].default_value = wet_roughness
    scene.render.filepath = os.path.join(out_folder, f'{camera_name}_{state}{tag}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = round(time.time() - started, 1)
    open(os.path.join(out_folder, f'{camera_name}_{state}{tag}_seconds.txt'), 'w').write(f'{seconds}\n')
    print('DRAWN', camera_name, state, seconds, 's', flush=True)
