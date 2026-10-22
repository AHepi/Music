# render_character.py - draws pictures of the combined garden (garden_character.blend) on the rented card, in ONE Blender start.
# Plain words: the scene file already has the four builders' stages applied and saved (build_character.py). This script opens it (given on the
# command line), and for every picture in the job file sets the camera, sets the weathering kit's Dot Angle for that picture height (exactly as the
# earlier finals did), and draws either a small preview JPG (Cycles, adaptive, denoised) or a FINAL through the first round's render_job.main
# (PNG + light-group EXR + log json, 512 samples, same seed 7, same exposure and compositor).
# Run:  /workspace/blender/blender -b --disable-autoexec garden_character.blend -P render_character.py -- JOB.json
# JOB.json = {"outdir": "/abs/folder", "pictures": [{"name": "hero", "camera": "photo", "size": "2400x1600", "samples": 512, "seed": 7,
#             "mode": "final"|"preview", "exr": true, "border": [x0, y0, x1, y1] (fractions, previews only, optional)}]}
import bpy
import sys
import os
import json
import math
import time
import traceback

sys.dont_write_bytecode = True
FINAL_STAGE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final/stage'
if FINAL_STAGE in sys.path:
    sys.path.remove(FINAL_STAGE)
sys.path.insert(0, FINAL_STAGE)
import render_job   # noqa: E402  (the first round's render job, read-only, on the store)

jobs = json.load(open(sys.argv[sys.argv.index('--') + 1]))
T0 = time.time()


def set_dot_angle(camera, height):
    """Dot Angle on every weathering-kit scale node = angular size of one picture dot (real look only), as in the earlier finals."""
    if camera is None or camera.type != 'CAMERA':
        return 0
    val = 2.0 * math.tan(camera.data.angle_y / 2.0) / float(height)
    n = 0
    for m in bpy.data.materials:
        nt = m.node_tree
        if nt is None:
            continue
        for node in nt.nodes:
            if node.get('wk') == 'scale':
                node.inputs['Dot Angle'].default_value = val
                n += 1
    return n


def preview(p, outdir):
    sc = bpy.context.scene
    cam = bpy.data.objects[p['camera']]
    sc.camera = cam
    w, h = [int(v) for v in p.get('size', '960x640').lower().split('x')]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.samples = int(p.get('samples', 96))
    cy.seed = int(p.get('seed', 7))
    cy.use_animated_seed = False
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.01
    cy.use_denoising = True
    cy.caustics_reflective = cy.caustics_refractive = False
    dev = render_job.pick_device(sc, bool(jobs.get('cpu')))
    if not dev['gpu_in_use'] and not jobs.get('cpu'):
        print('WARNING: no graphics card in use', flush=True)
    b = p.get('border')
    sc.render.use_border = bool(b)
    if b:
        sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = b
        sc.render.use_crop_to_border = True
    set_dot_angle(cam, h / (b[3] - b[1]) if b else h)
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'
    fmt = p.get('format', 'JPEG')
    ims.file_format = fmt
    if fmt == 'JPEG':
        ims.quality = int(p.get('quality', 88))
        ims.color_mode = 'RGB'
    else:
        ims.color_mode = 'RGBA'
    ims.color_management = 'FOLLOW_SCENE'
    path = os.path.join(outdir, '%s.%s' % (p['name'], 'jpg' if fmt == 'JPEG' else 'png'))
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    sc.render.use_border = False
    print('PREVIEW_DONE', path, round(time.time() - t, 1), 's', flush=True)
    return path


def final(p, outdir):
    cam = bpy.data.objects.get(p['camera'])
    h = int(p['size'].lower().split('x')[1])
    nscale = set_dot_angle(cam, h)
    base = os.path.join(outdir, p['name'])
    argv = ['--out', base, '--camera', p['camera'], '--size', p['size'], '--samples', str(p.get('samples', 512)), '--seed', str(p.get('seed', 7)),
            '--require-gpu'] + (['--exr'] if p.get('exr') else []) + (['--check-groups'] if p.get('check_groups') else []) + list(p.get('extra', []))
    sys.argv = [sys.argv[0], '--'] + argv
    print('FINAL_START', base, 'dot-angle nodes set:', nscale, flush=True)
    render_job.main()
    return base + '.png'


# optional (for quick looks that do not use the saved scene): apply the four stages here, in the given order, and add extra cameras
if jobs.get('apply_stages'):
    CH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
    import importlib
    for n in ('wood', 'roof', 'ground', 'pond', 'final'):
        sys.path.append(CH + '/' + n)
    for n in jobs['apply_stages']:
        mod = importlib.import_module('stage_' + n)
        mod.apply({})
    bpy.context.view_layer.update()
if jobs.get('extra_cameras'):
    from mathutils import Vector
    for nm, (loc, tgt, lens) in jobs['extra_cameras'].items():
        if bpy.data.objects.get('G6 final cam ' + nm):
            continue
        cd = bpy.data.cameras.new('G6 final cam ' + nm)
        cd.lens = lens
        cd.clip_start = 0.05
        co = bpy.data.objects.new('G6 final cam ' + nm, cd)
        co['garden_owner'] = 'final'
        co.location = loc
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.collection.objects.link(co)

if jobs.get('save_blend'):      # keep the extra cameras in the delivered scene (images are packed already)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=jobs['save_blend'], compress=True)
    print('SAVED_BLEND', jobs['save_blend'], os.path.getsize(jobs['save_blend']), flush=True)

os.makedirs(jobs['outdir'], exist_ok=True)
results = []
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
variants = jobs.get('variants') or [{'name': 'base', 'pictures': jobs['pictures']}]
import importlib


def cam_exists(n):
    return bpy.data.objects.get(n) is not None


for vi, v in enumerate(variants):
    tv = time.time()
    if vi > 0 or v.get('reopen'):
        bpy.ops.wm.open_mainfile(filepath=v.get('blend') or jobs['blend'])
        bpy.context.preferences.filepaths.save_version = 0
    if v.get('wood') is not None:           # re-apply the (fixed) wood stage on top of the combined scene, with this variant's options
        import stage_wood
        importlib.reload(stage_wood)
        try:
            rep = stage_wood.apply(dict(v['wood']))
            json.dump(rep, open(os.path.join(jobs['outdir'], '%s__wood_report.json' % v['name']), 'w'), indent=1, default=str)
        except Exception:
            traceback.print_exc()
            results.append((v['name'], 'WOOD STAGE ERROR'))
            continue
        bpy.context.view_layer.update()
    if v.get('post'):
        try:
            import wood_jobs
            importlib.reload(wood_jobs)
            getattr(wood_jobs, v['post'])(v, jobs['outdir'])
        except Exception:
            traceback.print_exc()
            results.append((v['name'], 'POST ERROR'))
            continue
    if v.get('save_blend'):
        bpy.ops.wm.save_as_mainfile(filepath=v['save_blend'], copy=True, compress=True)
    for p in v['pictures']:
        t = time.time()
        pp = dict(p)
        if p.get('exec'):
            exec(compile(p['exec'], 'picture_exec', 'exec'), {'bpy': bpy, 'math': math, 'p': p})
        if len(variants) > 1 or v.get('prefix'):
            pp['name'] = '%s__%s' % (v['name'], p['name'])
        try:
            out = (final if p.get('mode') == 'final' else preview)(pp, jobs['outdir'])
            results.append((v['name'], p['name'], 'ok', round(time.time() - t, 1)))
        except SystemExit as e:
            results.append((v['name'], p['name'], 'exit: ' + str(e)))
        except Exception:
            traceback.print_exc()
            results.append((v['name'], p['name'], 'error'))
print('CHARACTER_RENDER_ALL', json.dumps(results), 'total seconds', round(time.time() - T0, 1), flush=True)
