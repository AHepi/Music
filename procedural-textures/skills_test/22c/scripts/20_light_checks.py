# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22c, part 1: uses the lighting skill's own tools (bx_light.py of scenario-blender-lighting-rendering) on the wet street COPY, main camera, in the
# states "today" and "wet". It draws each state with the same EEVEE settings as the street's own tool (22_render_eevee.py) but through the skill's render
# helper (picture plus a linear EXR), then runs the skill's value (light/dark) and colour checks and writes the numbers and the pictures.
# Nothing is saved back to the street file; every picture goes into OUT_FOLDER.
# Run (on the rented machine): /workspace/blender/blender -b --disable-autoexec --factory-startup set_copy/street.blend --python-exit-code 1 \
#        --python scripts/20_light_checks.py -- out/light
import json
import os
import sys
import time

import bpy
import numpy as np

sys.dont_write_bytecode = True
SKILL = '/home/user/Music/.claude/skills/scenario-blender-lighting-rendering/scripts'
sys.path.append(SKILL)
import bx_light as BL  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import apply_wetness_to_set as aw  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
W, H, SAMPLES = 540, 960, 64
scene = bpy.context.scene
scene.camera = aw.cameras()['main']
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100
scene.eevee.taa_render_samples = SAMPLES
scene.eevee.use_raytracing = True                       # same switches as 22_render_eevee.py
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
scene.view_layers[0].use_pass_cryptomatte_object = True  # so the skill can cut a subject out of the EXR by object name

SUBJECTS = {
    'colliery': ['headframe_lattice', 'winding_wheel_left', 'winding_wheel_right', 'engine_house_walls', 'engine_house_trim', 'engine_house_glass'],
    'lamp0': ['gas_lamp_0_post', 'gas_lamp_0_glass'],
    'road': ['street_setts'],
}
log = {'blender': bpy.app.version_string, 'skill_version': BL.__version__, 'size': [W, H], 'samples': SAMPLES,
       'view': [scene.view_settings.view_transform, scene.view_settings.look, round(scene.view_settings.exposure, 3)]}


def r(x):
    """make numpy values plain so they can go in the JSON"""
    if isinstance(x, dict):
        return {k: r(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [r(v) for v in x]
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, np.bool_):
        return bool(x)
    return x


pngs = {}
applied = False
for state in ('today', 'wet'):
    if state == 'wet':
        aw.apply(wetness=0.0, puddles=0.0)
        applied = True
        aw.set_state(0.85, 0.5)
    base = os.path.join(out, f'main_{state}')
    res = BL.render(base, exr=True, depth='32')
    pngs[state] = res['png']
    entry = {'render_seconds': res['seconds'], 'color_audit': BL.color_audit()}
    # --- whole picture, no subject
    rep = BL.analyse(res['png'], None, exr=res['exr'])
    entry['whole_frame'] = rep
    entry['whole_frame_verdict'] = BL.verdict(rep)
    # --- three subjects cut out of the EXR by object name (cryptomatte)
    entry['subjects'] = {}
    for name, objs in SUBJECTS.items():
        try:
            mask = BL.mask_cryptomatte(res['exr'], objs)
            rep_s = BL.analyse(res['png'], mask, exr=res['exr'])
            entry['subjects'][name] = {'objects': objs, 'mask_area_pct': round(float(100 * (mask > 0.5).mean()), 2), 'report': rep_s, 'verdict': BL.verdict(rep_s)}
            BL.value_study(res['png'], os.path.join(out, f'values_{state}_{name}.png'), mask=mask)
            np.save(os.path.join(out, f'mask_{name}_{state}.npy'), (mask * 255).astype(np.uint8))
        except Exception as error:   # keep going, report it
            entry['subjects'][name] = {'error': repr(error)}
    log[state] = entry
    print('STATE', state, 'rendered in', res['seconds'], 's', flush=True)

# --- does the skill's render equal the film tool's own plate? (same settings, same camera)
film = {s: f'out/plates/main_{s}_film.png' for s in ('today', 'wet')}
cmp = {}
for s in ('today', 'wet'):
    if os.path.exists(film[s]):
        a = BL.load_rgba(film[s])[..., :3]
        b = BL.load_rgba(pngs[s])[..., :3]
        d = np.abs(a - b)
        cmp[s] = {'max_abs_diff_0_1': round(float(d.max()), 4), 'mean_abs_diff_0_1': round(float(d.mean()), 5)}
log['skill_render_vs_film_tool_png'] = cmp

# --- today against wet: the skill's per-shot brightness / hue table and a contact sheet
log['sheet_stats'] = BL.sheet_stats([pngs['today'], pngs['wet']])
BL.contact_sheet([pngs['today'], pngs['wet']], os.path.join(out, 'contact_today_wet.png'), cols=2, width=540)

# --- the skill's own mask by a flat Workbench picture, compared with the cryptomatte one (colliery)
try:
    wb = BL.mask_workbench([bpy.data.objects[n] for n in SUBJECTS['colliery']], path=os.path.join(out, 'wb_mask.png'))
    cm = np.load(os.path.join(out, 'mask_colliery_wet.npy')) / 255.0
    a, b = wb > 0.5, cm > 0.5
    log['mask_workbench_vs_cryptomatte_colliery'] = {'workbench_area_pct': round(float(100 * a.mean()), 2), 'crypto_area_pct': round(float(100 * b.mean()), 2),
                                                     'iou': round(float((a & b).sum() / max((a | b).sum(), 1)), 3)}
except Exception as error:
    log['mask_workbench_vs_cryptomatte_colliery'] = {'error': repr(error)}

# --- lights: the skill's light table aimed at the colliery (the story point) as seen from the main camera (state wet is on now)
try:
    tgt = [bpy.data.objects[n] for n in SUBJECTS['colliery']]
    lr = BL.light_report(target=tgt, cam=scene.camera)
    keep = [x for x in lr['lights'] if x['name'].startswith(('gas_lamp', 'engine_house', 'dusk', 'afterglow'))]
    log['light_report_target_colliery'] = {'flags': lr['flags'], 'n_lights': len(lr['lights']), 'rows_gas_engine_sun': keep}
    sun = [o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN']
    log['sun_azimuth'] = {o.name: BL.sun_azimuth(o) for o in sun}
except Exception as error:
    log['light_report_target_colliery'] = {'error': repr(error)}

# --- which lamp carries the picture? each lamp alone on the wet street, share of the light on the colliery and on the whole frame (today state is not on now; wet is)
try:
    lights = [o for o in scene.objects if o.type == 'LIGHT']
    mask = BL.mask_cryptomatte(os.path.join(out, 'main_wet.exr'), SUBJECTS['colliery'])
    t0 = time.time()
    contrib = BL.light_contributions(lights, mask, os.path.join(out, 'solo'), pct=50)
    log['light_contributions_colliery_seconds'] = round(time.time() - t0, 1)
    groups = {'gas_lamps': 0.0, 'cottage_window_lights': 0.0, 'engine_house_lights': 0.0, 'suns': 0.0, 'world': 0.0}
    for k, v in contrib.items():
        key = 'gas_lamps' if k.startswith('gas_lamp') else 'cottage_window_lights' if 'window_light' in k else 'engine_house_lights' if k.startswith('engine_house') else 'world' if k == 'World' else 'suns'
        groups[key] += v['share']
    log['light_contributions_colliery_group_share'] = {k: round(v, 3) for k, v in groups.items()}
    log['light_contributions_colliery_top5'] = sorted(((k, v['share'], v['ratio_to_strongest']) for k, v in contrib.items()), key=lambda t: -t[1])[:6]
except Exception as error:
    log['light_contributions_colliery'] = {'error': repr(error)}

json.dump(r(log), open(os.path.join(out, 'light_checks.json'), 'w'), indent=1)
print('DONE light checks ->', os.path.join(out, 'light_checks.json'))
