# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Draws the SAME street pictures with EEVEE and with Cycles, one after the other, in ONE Blender run on the rented machine, so that everything except the renderer is identical:
# the same file (the street copy, or the film's lockout shot file opened read-only and never saved), the same camera, the same lighting, the same WETNESS, JOINTS and RUBBISH layers
# at their final defaults (put on exactly as rubbish_runner.py of the rubbish job puts them on), the same size.
# EEVEE = the plate settings of the recipe (ray tracing on, shadow rays 4, shadow steps 16, 64 samples), through the same helper the plates use (lv.eevee_setup).
# Cycles = the card (OptiX), the OptiX denoiser, adaptive sampling; the numbers are in the job file ("cycles": {...}) and printed in the log for every picture.
# It changes NO layer. Only renderer settings differ between the two pictures of a pair. Nothing is saved except the pictures and small text files.
# Job file (JSON): {"kind": "street"|"lockout", "masks": [["main",1080,1920]], "ground_masks": [...], "cameras": {"name": {"loc": [x,y,z], "look": [x,y,z], "fov": 40}},
#   "cycles": {default Cycles dials}, "jobs": [{"name":..., "engine": "eevee"|"cycles", "camera":..., "light":"A", "state":"today"|"dry"|"wet", "w":..,"h":..,"samples":..,
#      "look": "today"|"round2"|"joints"|"rubbish", "view": "beauty"|"puddles"|"dirt", "cycles": {per-picture Cycles dials}, "diag": null|"dome_dark"|"glow_dark"}]}
# Run: blender -b --disable-autoexec FILE --python pair_runner.py -- JOB_FILE OUT_FOLDER
# Writes OUT_FOLDER/<name>.png, <name>_seconds.txt, mask pictures, run_summary.json.
import json
import os
import sys
import time

import bpy

BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet'
RUBBISH_TOOLS = BASE + '/relief_and_rubbish/rubbish/tools'
SETTS_TOOLS = BASE + '/relief_and_rubbish/setts/tools'
STUDY_TOOLS = BASE + '/relief_and_rubbish/study/tools'
sys.path.insert(0, RUBBISH_TOOLS)
sys.path.insert(0, SETTS_TOOLS)
sys.path.insert(0, STUDY_TOOLS)
sys.dont_write_bytecode = True
import b02_lighting_and_variants as lv  # noqa: E402
import apply_wetness_to_set as aw  # noqa: E402
import apply_joints_to_set as aj  # noqa: E402
import apply_rubbish_to_set as ar  # noqa: E402
import rubbish_layer as rl  # noqa: E402
import rubbish_pieces as rp  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
job_file, out_folder = args[0], args[1]
os.makedirs(out_folder, exist_ok=True)
spec = json.load(open(job_file))
kind = spec['kind']
scene = bpy.context.scene
cams = aw.cameras()
# the extra cameras the rubbish job used (identical numbers), plus the ones this job file names
cams['gutter_close'] = aw.make_camera('gutter_close', (0.9, 4.6, 0.95), look_at=(2.45, 8.6, 0.72), fov_vertical=40.0)
cams['wall_close'] = aw.make_camera('wall_close', (3.05, 6.2, 0.82), look_at=(4.0, 11.5, 0.88), fov_vertical=44.0)
cams['drum_close'] = aw.make_camera('drum_close', (2.0, 6.3, 1.30), look_at=(0.7, 9.6, 0.85), fov_vertical=50.0)
cams['doorstep_close'] = aw.make_camera('doorstep_close', (2.3, 5.6, 1.10), look_at=(3.55, 7.4, 0.85), fov_vertical=42.0)
for cam_name, c in spec.get('cameras', {}).items():
    cams[cam_name] = aw.make_camera(cam_name, tuple(c['loc']), look_at=tuple(c['look']), fov_vertical=c.get('fov', 40.0))
print('FILE', bpy.data.filepath, 'kind', kind, 'jobs', len(spec['jobs']), 'blender', bpy.app.version_string, flush=True)
summary = dict(kind=kind, file=bpy.data.filepath, blender=bpy.app.version_string, timings={}, notes={}, settings={})
t_start = time.time()


# ------------------------------------------------------------------------------------------------------------------------------- measuring masks (same as the rubbish job, engine-independent)
for camera_name, w, h in spec.get('masks', []):
    path = os.path.join(out_folder, f'mask_{camera_name}_{w}x{h}.png')
    if os.path.exists(path):
        continue
    scene.camera = cams[camera_name]
    started = time.time()
    lv.render_mask(path, w, h)
    print('MASK', camera_name, w, h, round(time.time() - started, 1), 's', flush=True)


def render_ground_mask(path, w, h, samples=8):
    """White on the ground (road, gutter stones, kerbs, pavements), black elsewhere, raw numbers (copied unchanged from rubbish_runner.py)."""
    view_layer = bpy.context.view_layer
    names = ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements')
    old_index = {n: bpy.data.objects[n].pass_index for n in names}
    for n in names:
        bpy.data.objects[n].pass_index = 1
    material = bpy.data.materials.new('ground_only_mask')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    info = tree.nodes.new('ShaderNodeObjectInfo')
    compare = tree.nodes.new('ShaderNodeMath')
    compare.operation = 'COMPARE'
    compare.inputs[1].default_value, compare.inputs[2].default_value = 1.0, 0.1
    tree.links.new(info.outputs['Object Index'], compare.inputs[0])
    emission = tree.nodes.new('ShaderNodeEmission')
    combine = tree.nodes.new('ShaderNodeCombineColor')
    for channel in ('Red', 'Green', 'Blue'):
        tree.links.new(compare.outputs[0], combine.inputs[channel])
    tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    keep = (scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma, scene.render.dither_intensity)
    background = scene.world.node_tree.nodes['Background']
    world_keep = (tuple(background.inputs['Color'].default_value), background.inputs['Strength'].default_value)
    lv.eevee_setup(w, h, samples, raytracing=False)
    scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = 'Raw', 'None', 0.0, 1.0
    scene.render.dither_intensity = 0.0
    background.inputs['Color'].default_value, background.inputs['Strength'].default_value = (0, 0, 0, 1), 0.0
    view_layer.material_override = material
    scene.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        view_layer.material_override = None
        for n, v in old_index.items():
            bpy.data.objects[n].pass_index = v
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma, scene.render.dither_intensity = keep
        background.inputs['Color'].default_value, background.inputs['Strength'].default_value = world_keep
        bpy.data.materials.remove(material)


for camera_name, w, h in spec.get('ground_masks', []):
    path = os.path.join(out_folder, f'ground_{camera_name}_{w}x{h}.png')
    if os.path.exists(path):
        continue
    scene.camera = cams[camera_name]
    render_ground_mask(path, w, h)
    print('GROUND MASK', camera_name, flush=True)


# ------------------------------------------------------------------------------------------------------------------------------- Cycles on the card
def enable_card():
    """OptiX first, then CUDA; only the graphics card is switched on (not the processor cores)."""
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for compute in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = compute
            try:
                prefs.get_devices()
            except Exception:
                prefs.refresh_devices()
            gpus = [d for d in prefs.devices if d.type != 'CPU']
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            if gpus:
                print('CYCLES DEVICE', compute, [d.name for d in gpus], flush=True)
                return compute, [d.name for d in gpus]
        except Exception as error:
            print('device try failed', compute, error, flush=True)
    return None, []


CARD = enable_card()
summary['notes']['cycles_device'] = CARD

CYCLES_DEFAULT = dict(samples=256, seed=0, adaptive_threshold=0.01, adaptive_min_samples=32, denoise=True, denoiser='OPTIX', max_bounces=8, diffuse_bounces=4, glossy_bounces=4,
                      transmission_bounces=4, transparent_bounces=8, volume_bounces=0, clamp_direct=0.0, clamp_indirect=10.0, caustics=True, light_tree=True)
CYCLES_DEFAULT.update(spec.get('cycles', {}))


def setup_cycles(w, h, samples, per_picture):
    o = dict(CYCLES_DEFAULT)
    o.update(per_picture or {})
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    c = scene.cycles
    c.device = 'GPU' if CARD[0] else 'CPU'
    c.samples = int(samples)
    c.seed = int(o['seed'])
    c.use_animated_seed = False
    c.use_adaptive_sampling = o['adaptive_threshold'] > 0
    c.adaptive_threshold = o['adaptive_threshold'] if o['adaptive_threshold'] > 0 else 0.01
    c.adaptive_min_samples = int(o['adaptive_min_samples'])
    c.use_denoising = bool(o['denoise'])
    if o['denoise']:
        c.denoiser = o['denoiser']
        c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        c.denoising_prefilter = 'ACCURATE'
        if hasattr(c, 'denoising_use_gpu'):
            c.denoising_use_gpu = True
    c.max_bounces = int(o['max_bounces'])
    c.diffuse_bounces = int(o['diffuse_bounces'])
    c.glossy_bounces = int(o['glossy_bounces'])
    c.transmission_bounces = int(o['transmission_bounces'])
    c.transparent_max_bounces = int(o['transparent_bounces'])
    c.volume_bounces = int(o['volume_bounces'])
    c.sample_clamp_direct = float(o['clamp_direct'])
    c.sample_clamp_indirect = float(o['clamp_indirect'])
    c.caustics_reflective = bool(o['caustics'])
    c.caustics_refractive = bool(o['caustics'])
    c.use_light_tree = bool(o['light_tree'])
    c.pixel_filter_type = 'BLACKMAN_HARRIS'            # what the file has (the mask pictures had switched it to BOX)
    c.filter_width = 1.5
    c.film_exposure = 1.0
    c.time_limit = 0.0
    c.use_fast_gi = False
    scene.render.use_persistent_data = False
    return o


def cycles_report():
    c = scene.cycles
    keys = ('device', 'samples', 'seed', 'use_adaptive_sampling', 'adaptive_threshold', 'adaptive_min_samples', 'use_denoising', 'denoiser', 'denoising_input_passes', 'denoising_prefilter',
            'denoising_use_gpu', 'max_bounces', 'diffuse_bounces', 'glossy_bounces', 'transmission_bounces', 'transparent_max_bounces', 'volume_bounces', 'sample_clamp_direct',
            'sample_clamp_indirect', 'caustics_reflective', 'caustics_refractive', 'use_light_tree', 'light_sampling_threshold', 'pixel_filter_type', 'filter_width', 'film_exposure', 'use_fast_gi')
    return {k: getattr(c, k) for k in keys if hasattr(c, k)}


def eevee_report():
    e = scene.eevee
    keys = ('taa_render_samples', 'use_raytracing', 'ray_tracing_method', 'shadow_ray_count', 'shadow_step_count', 'shadow_pool_size', 'shadow_resolution_scale', 'use_fast_gi', 'fast_gi_method',
            'light_threshold', 'clamp_surface_indirect', 'use_shadows')
    return {k: str(getattr(e, k)) if not isinstance(getattr(e, k), (int, float, bool)) else getattr(e, k) for k in keys if hasattr(e, k)}


# ------------------------------------------------------------------------------------------------------------------------------- the looks (copied from rubbish_runner.py, unchanged)
DEFAULT_DIALS = dict(rl.DEFAULTS)
DEFAULT_DIALS.update(rp.PIECE_DEFAULTS)
LAYERS = {'on': False}


def put_layers_on():
    """The wetness layer, then JOINTS, then the rubbish, in this order and with these calls: exactly as rubbish_runner.py does."""
    aw.apply(wetness=0.0, puddles=0.0)
    aj.apply()
    t0 = time.time()
    ar.apply(places=kind, amount=0.0)
    ar.pieces(False)
    summary['timings']['build_layers_s'] = round(time.time() - t0, 1)
    LAYERS['on'] = True


def set_look(job):
    look = job.get('look', 'rubbish')
    if look == 'today':
        return
    if look == 'round2':
        aj.set_dials(strength=0.0)
        ar.set_dials(**dict(DEFAULT_DIALS, amount=0.0))
        ar.pieces(False)
    elif look == 'joints':
        aj.set_dials(strength=1.0)
        ar.set_dials(**dict(DEFAULT_DIALS, amount=0.0))
        ar.pieces(False)
    else:
        aj.set_dials(strength=job.get('joint_strength', 1.0))
        dials = dict(DEFAULT_DIALS)
        dials.update(job.get('dials', {}))
        ar.set_dials(**dials)
        ar.pieces(dials['pieces_density'] > 0 and dials['amount'] > 0 and not job.get('no_pieces'))


# ------------------------------------------------------------------------------------------------------------------------------- diagnostics (never part of a pair)
def glow_objects():
    """Meshes whose material emits light (windows, lamp glass, brazier coals, the sky dome): in Cycles they light the street, in EEVEE they do not."""
    found = []
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        glows = False
        for slot in obj.material_slots:
            m = slot.material
            if m is None or not m.use_nodes:
                continue
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED' and n.inputs['Emission Strength'].default_value > 0 and max(n.inputs['Emission Color'].default_value[:3]) > 0:
                    glows = True
        if glows:
            found.append(obj)
    return found


def diag_on(diag):
    saved = []
    if not diag:
        return saved
    targets = [scene.objects['sky_dome']] if diag == 'dome_dark' else glow_objects()
    for obj in targets:
        saved.append((obj, obj.visible_diffuse, obj.visible_glossy, obj.visible_transmission))
        obj.visible_diffuse = False
        obj.visible_glossy = False
        obj.visible_transmission = False
    print('DIAG', diag, 'objects', len(targets), flush=True)
    return saved


def diag_off(saved):
    for obj, d, g, t in saved:
        obj.visible_diffuse, obj.visible_glossy, obj.visible_transmission = d, g, t


# ------------------------------------------------------------------------------------------------------------------------------- drawing
WARM = set()


def warm_up(engine, camera_name):
    """One tiny picture per engine and per stage (today / layers on), not timed as a picture: builds the shaders and loads the card, so that the picture times are the steady times."""
    key = (engine, LAYERS['on'])
    if key in WARM:
        return
    WARM.add(key)
    scene.camera = cams[camera_name]
    if engine == 'eevee':
        lv.eevee_setup(160, 120, 1, raytracing=True)
    else:
        setup_cycles(160, 120, 1, {'denoise': False})
    scene.render.filepath = os.path.join(out_folder, '_warmup.png')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = round(time.time() - t, 1)
    summary['timings'][f'warmup_{engine}_{"layers" if LAYERS["on"] else "today"}_s'] = seconds
    print('WARMUP', engine, 'layers' if LAYERS['on'] else 'today', seconds, 's', flush=True)


def draw(job, png, engine=None, samples=None):
    engine = engine or job['engine']
    samples = samples or job['samples']
    ee_saved = {}
    scene.camera = cams[job['camera']]
    if engine == 'eevee':
        lv.eevee_setup(job['w'], job['h'], samples, raytracing=job.get('rt', True))
        for key, value in job.get('eevee_set', {}).items():          # a named EEVEE setting changed for this one picture only (put back after the picture)
            ee_saved[key] = getattr(scene.eevee, key)
            setattr(scene.eevee, key, value)
    else:
        used = setup_cycles(job['w'], job['h'], samples, job.get('cycles'))
        summary['settings'][job['name']] = dict(cycles_used=used, cycles_blender=cycles_report())
    lv.set_lighting(job['light'], job.get('light_args'))
    if job.get('look', 'rubbish') != 'today':
        wet, pud = lv.parse_state(job['state'])
        aw.set_state(wet, pud)
        ar.set_state(wet)
    scene.render.filepath = png
    saved = diag_on(job.get('diag')) if engine == 'cycles' else []
    if engine == 'eevee':
        summary['settings'].setdefault(job['name'], {})['eevee'] = eevee_report()
    t = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        diag_off(saved)
        for key, value in ee_saved.items():
            setattr(scene.eevee, key, value)
    return round(time.time() - t, 2)


done = 0
for job in spec['jobs']:
    png = os.path.join(out_folder, job['name'] + '.png')
    if os.path.exists(png):
        print('SKIP', job['name'], flush=True)
        continue
    view = job.get('view', 'beauty')
    look = job.get('look', 'rubbish')
    if look != 'today' and not LAYERS['on']:
        put_layers_on()
        print('LAYERS ON', summary['timings']['build_layers_s'], 's', flush=True)
    undo_view = None
    started = time.time()
    seconds = None
    try:
        set_look(job)
        if view == 'beauty':
            warm_up(job['engine'], job['camera'])
            seconds = draw(job, png)
        elif view == 'dirt':
            # the rubbish mask, raw, pieces hidden (the study's dirt picture): where there is rubbish; same for both engines (EEVEE, 4 samples, as the rubbish job draws it)
            set_look(dict(job, look='rubbish'))
            ar.pieces(False)
            undo_view = ar.show_mask('total', raw=True)
            seconds = draw(dict(job, engine='eevee'), png, engine='eevee', samples=4)
        elif view == 'puddles':
            set_look(dict(job, look='joints'))
            undo_view = lv.VARIANTS['show_masks']()
            seconds = draw(dict(job, engine='eevee'), png, engine='eevee', samples=4)
        else:
            raise ValueError('unknown view ' + view)
    except Exception:
        import traceback
        print('JOB FAILED', job['name'], flush=True)
        traceback.print_exc()
        sys.stdout.flush()
    finally:
        if undo_view:
            undo_view()
    open(os.path.join(out_folder, job['name'] + '_seconds.txt'), 'w').write(f'{seconds}\n')
    summary['timings'][job['name']] = seconds
    done += 1
    print('DRAWN', job['name'], job.get('engine'), 'render seconds', seconds, 'with set-up', round(time.time() - started, 1), flush=True)
try:
    set_look(dict(look='rubbish', dials={}))
    summary['notes']['pieces_in_scene_at_default'] = ar.piece_count()
except Exception as error:
    summary['notes']['piece_count_error'] = str(error)
summary['timings']['total_s'] = round(time.time() - t_start, 1)
summary['notes']['pictures_drawn'] = done
json.dump(summary, open(os.path.join(out_folder, 'run_summary.json'), 'w'), indent=1)
print('ALL JOBS DONE', summary['timings']['total_s'], 's', flush=True)
