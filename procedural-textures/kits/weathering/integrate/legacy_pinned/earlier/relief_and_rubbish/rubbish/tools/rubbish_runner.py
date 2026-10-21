# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The picture runner for the rubbish work. It opens ONE street file (the street copy, or the film's lockout shot file opened READ-ONLY: it is never saved), puts the three layers
# on (wetness, JOINTS, RUBBISH) and then draws a LIST OF PICTURES from a job file, one after another, so that Blender is loaded only once per file.
# Each picture says: which camera, which lighting (A to E, see study/tools/b02_lighting_and_variants.py), which wetness state (dry, wet, heavy), the size, the samples, and the LOOK:
#     round2   the street as round 2 left it (JOINTS off, no rubbish)
#     joints   with the JOINTS layer (the setts' round), no rubbish
#     rubbish  joints plus the rubbish, with the dials the job gives (anything not named stays at its default)
# and the VIEW: beauty (the picture), mask_colours / mask_total (the rubbish mask drawn on the ground; add "film_look": true to keep the film's colours so the street can be seen),
# puddles (the puddle mask, raw numbers), plan (the mask seen straight from above; needs "plan": [y0, y1]).
# Job file (JSON): {"kind": "street" or "lockout", "masks": [["main", 540, 960]], "jobs": [{"name": "main_A_wet_rubbish", "camera": "main", "light": "A", "state": "wet",
#                  "w": 540, "h": 960, "samples": 16, "look": "rubbish", "dials": {"amount": 1.0}, "view": "beauty", "dirt": true}, ...]}
#     "masks" are the joint measuring masks (Cycles, drawn once per camera and size, as in the study). "dirt": true also draws <name>_dirt.png (the rubbish mask, raw, pieces hidden) for the measure.
# Run: blender -b --disable-autoexec BLEND --python rubbish_runner.py -- JOB_FILE OUT_FOLDER
# Writes OUT_FOLDER/<name>.png, <name>_seconds.txt, run_summary.json and OUT_FOLDER/mask_<camera>_<w>x<h>.png. Skips a picture that already exists (png or jpg).
import json
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
RUBBISH = os.path.abspath(os.path.join(HERE, '..'))
STUDY_TOOLS = os.path.abspath(os.path.join(RUBBISH, '..', 'study', 'tools'))
SETTS_TOOLS = os.path.abspath(os.path.join(RUBBISH, '..', 'setts', 'tools'))
sys.path.insert(0, HERE)
sys.path.insert(0, SETTS_TOOLS)
sys.path.insert(0, STUDY_TOOLS)
sys.dont_write_bytecode = True
import b02_lighting_and_variants as lv  # noqa: E402
import apply_wetness_to_set as aw  # noqa: E402
import apply_joints_to_set as aj  # noqa: E402
import apply_rubbish_to_set as ar  # noqa: E402
import rubbish_layer as rl  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
job_file, out_folder = args[0], args[1]
os.makedirs(out_folder, exist_ok=True)
spec = json.load(open(job_file))
kind = spec['kind']
scene = bpy.context.scene
cams = aw.cameras()
# extra cameras for the close-ups (the street copy's own metres): the right gutter and kerb, the foot of the right wall by the first lamp, a right-hand doorstep, the road looking at the drum
cams['gutter_close'] = aw.make_camera('gutter_close', (0.9, 4.6, 0.95), look_at=(2.45, 8.6, 0.72), fov_vertical=40.0)
cams['wall_close'] = aw.make_camera('wall_close', (3.05, 6.2, 0.82), look_at=(4.0, 11.5, 0.88), fov_vertical=44.0)
cams['drum_close'] = aw.make_camera('drum_close', (2.0, 6.3, 1.30), look_at=(0.7, 9.6, 0.85), fov_vertical=50.0)
cams['doorstep_close'] = aw.make_camera('doorstep_close', (2.3, 5.6, 1.10), look_at=(3.55, 7.4, 0.85), fov_vertical=42.0)
cams['left_gutter_close'] = aw.make_camera('left_gutter_close', (-0.9, 4.6, 0.95), look_at=(-2.45, 8.6, 0.72), fov_vertical=40.0)
print('FILE', bpy.data.filepath, 'kind', kind, 'jobs', len(spec['jobs']), flush=True)
summary = dict(kind=kind, file=bpy.data.filepath, timings={}, notes={})
t_start = time.time()

for camera_name, w, h in spec.get('masks', []):
    path = os.path.join(out_folder, f'mask_{camera_name}_{w}x{h}.png')
    if os.path.exists(path):
        continue
    scene.camera = cams[camera_name]
    started = time.time()
    lv.render_mask(path, w, h)
    print('MASK', camera_name, round(time.time() - started, 1), 's', flush=True)



def render_ground_mask(path, w, h, samples=8):
    """A picture that is white on the ground (road, gutter stones, kerbs, pavements) and black everywhere else, raw numbers: so that the rubbish mask picture can be cut down to the ground."""
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

aw.apply(wetness=0.0, puddles=0.0)
aj.apply()
t0 = time.time()
ar.apply(places=kind, amount=0.0)
ar.pieces(False)
summary['timings']['build_rubbish_s'] = round(time.time() - t0, 1)
print('BUILT rubbish in', summary['timings']['build_rubbish_s'], 's', flush=True)
DEFAULT_DIALS = dict(rl.DEFAULTS)
DEFAULT_DIALS.update({k: rl.__dict__.get(k) for k in ()})
import rubbish_pieces as rp  # noqa: E402
DEFAULT_DIALS.update(rp.PIECE_DEFAULTS)


def set_look(job):
    look = job.get('look', 'rubbish')
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


def plan_camera(y0, y1):
    data = bpy.data.cameras.new('plan_camera')
    data.type = 'ORTHO'
    data.sensor_fit = 'VERTICAL'
    data.ortho_scale = y1 - y0
    data.clip_start, data.clip_end = 1.0, 400.0
    obj = bpy.data.objects.new('plan_camera', data)
    scene.collection.objects.link(obj)
    obj.location = (0.0, 0.5 * (y0 + y1), 80.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    return obj


def draw(job, png):
    scene.camera = cams[job['camera']] if job.get('camera') in cams else scene.camera
    lv.eevee_setup(job['w'], job['h'], job['samples'], raytracing=job.get('rt', True))
    lv.set_lighting(job['light'], job.get('light_args'))
    wet, pud = lv.parse_state(job['state'])
    aw.set_state(wet, pud)
    ar.set_state(wet)
    scene.render.filepath = png
    bpy.ops.render.render(write_still=True)


done = 0
for job in spec['jobs']:
    png = os.path.join(out_folder, job['name'] + '.png')
    if os.path.exists(png) or os.path.exists(png[:-4] + '.jpg'):
        print('SKIP', job['name'], flush=True)
        continue
    view = job.get('view', 'beauty')
    started = time.time()
    undo_view, hidden, plan_obj = None, [], None
    try:
        set_look(job)
        if view == 'beauty':
            draw(job, png)
            if job.get('dirt'):
                ar.pieces(False)
                undo = ar.show_mask('total', raw=True)
                try:
                    job2 = dict(job, samples=4)
                    draw(job2, os.path.join(out_folder, job['name'] + '_dirt.png'))
                finally:
                    undo()
        elif view in ('mask_colours', 'mask_total'):
            set_look(dict(job, look='rubbish'))
            undo_view = ar.show_mask('colours' if view == 'mask_colours' else 'total', raw=not job.get('film_look', False))
            if not job.get('pieces_in_mask', False):
                ar.pieces(False)
            draw(job, png)
        elif view == 'puddles':
            undo_view = lv.VARIANTS['show_masks']()
            draw(job, png)
        elif view == 'plan':
            y0, y1 = job['plan']
            plan_obj = plan_camera(y0, y1)
            cams['plan'] = plan_obj
            job = dict(job, camera='plan')
            for obj in scene.objects:
                if obj.type == 'MESH' and (obj.name.endswith('_roof') or obj.name.endswith('_trim') or obj.name.startswith('gas_lamp')):
                    if not obj.hide_render:
                        obj.hide_render = True
                        hidden.append(obj)
            if job.get('mode', 'colours') != 'beauty':
                set_look(dict(job, look='rubbish'))
                undo_view = ar.show_mask(job.get('mode', 'colours'), raw=not job.get('film_look', False))
            if not job.get('pieces_in_mask', False):
                ar.pieces(False)
            draw(job, png)
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
        for obj in hidden:
            obj.hide_render = False
        if plan_obj is not None:
            bpy.data.objects.remove(plan_obj)
            cams.pop('plan', None)
    seconds = round(time.time() - started, 1)
    open(os.path.join(out_folder, job['name'] + '_seconds.txt'), 'w').write(f'{seconds}\n')
    summary['timings'][job['name']] = seconds
    done += 1
    print('DRAWN', job['name'], seconds, 's', flush=True)
try:
    set_look(dict(look='rubbish', dials={}))
    summary['notes']['pieces_in_scene_at_default'] = ar.piece_count()
except Exception as error:
    summary['notes']['piece_count_error'] = str(error)
summary['timings']['total_s'] = round(time.time() - t_start, 1)
summary['notes']['pictures_drawn'] = done
json.dump(summary, open(os.path.join(out_folder, 'run_summary.json'), 'w'), indent=1)
print('ALL JOBS DONE', summary['timings']['total_s'], 's', flush=True)
