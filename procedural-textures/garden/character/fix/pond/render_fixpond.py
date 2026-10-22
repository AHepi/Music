# render_fixpond.py (POND FIX ROUND copy of render_character.py: applies the fixed stage_pond from this folder on top of the opened scene, extra picture kinds mask/branch masks, hide lists)
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
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)
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
    ims.file_format = 'JPEG'
    ims.quality = int(p.get('quality', 88))
    ims.color_mode = 'RGB'
    ims.color_management = 'FOLLOW_SCENE'
    path = os.path.join(outdir, '%s.jpg' % p['name'])
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


BASE_BLEND = bpy.data.filepath
STAGE_REPORT = None


def apply_variant(v):
    """(re)open the base scene and apply the pond stage with the variant's options (None = leave the scene as it is)."""
    global STAGE_REPORT
    opts = v.get('apply_pond')
    if opts is None:
        return
    import stage_pond
    import importlib
    importlib.reload(stage_pond)
    t_s = time.time()
    STAGE_REPORT = stage_pond.apply(dict(opts))
    bpy.context.view_layer.update()
    print('POND_STAGE_APPLIED', v.get('name'), 'seconds', round(time.time() - t_s, 1), flush=True)
    if v.get('stage_report'):
        os.makedirs(os.path.dirname(v['stage_report']), exist_ok=True)
        json.dump(STAGE_REPORT, open(v['stage_report'], 'w'), indent=1, default=str)
    if v.get('save_blend2'):
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=v['save_blend2'], compress=True, copy=True)
        print('SAVED_BLEND2', v['save_blend2'], os.path.getsize(v['save_blend2']), flush=True)


def hide_prefixes(prefixes, flag):
    old = []
    for ob in bpy.data.objects:
        if ob.name.startswith(tuple(prefixes)):
            old.append((ob, ob.hide_render)); ob.hide_render = flag
    return old


def branch_probe(p, outdir):
    """with the leaves hidden: for every maple trunk/branch object, how many pixels of the picture it covers (nothing else in front of it except other holdout geometry)."""
    import numpy as np
    sc = bpy.context.scene
    cam = bpy.data.objects[p['camera']]
    sc.camera = cam
    w, h = [int(v) for v in p.get('size', '600x400').lower().split('x')]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.samples = 1; cy.use_denoising = False; cy.use_adaptive_sampling = False; cy.seed = 7
    render_job.pick_device(sc, False)
    sc.render.film_transparent = True
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'; ims.file_format = 'PNG'; ims.color_mode = 'RGBA'; ims.color_depth = '8'; ims.color_management = 'FOLLOW_SCENE'
    old_h = [] if p.get('leaves_holdout') else hide_prefixes(['Maple leaves', 'Maple inner mass'], True)
    names = [o.name for o in bpy.data.objects if o.name.startswith(('Maple trunk', 'Maple branch'))]
    res = {}
    for nm in sorted(names):
        held = []
        for ob in bpy.data.objects:
            if ob.type in ('MESH', 'CURVE') and ob.name != nm and (p.get('leaves_holdout') or not ob.name.startswith(('Maple leaves', 'Maple inner mass'))):
                held.append((ob, ob.is_holdout)); ob.is_holdout = True
        path = os.path.join(outdir, 'bp_%s_%s.png' % (p['name'], nm.replace(' ', '_')))
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        for ob, o in held:
            ob.is_holdout = o
        img = bpy.data.images.load(path)
        a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a); bpy.data.images.remove(img)
        al = a.reshape(h, w, 4)[::-1, :, 3]
        ys, xs = np.nonzero(al > 0.5)
        res[nm] = dict(px=int(len(xs)), cx=float(xs.mean() / w) if len(xs) else None, cy=float(ys.mean() / h) if len(xs) else None,
                       bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None)
        os.remove(path)
    for ob, o in old_h:
        ob.hide_render = o
    sc.render.film_transparent = False
    json.dump(res, open(os.path.join(outdir, 'branchprobe_%s.json' % p['name']), 'w'), indent=1)
    print('BRANCH_PROBE', p['name'], {k: v['px'] for k, v in res.items()}, flush=True)
    return None


def mask(p, outdir):
    """alpha silhouette of the objects whose name starts with one of p['keep'] (all other meshes are holdouts); RGBA PNG."""
    sc = bpy.context.scene
    cam = bpy.data.objects[p['camera']]
    sc.camera = cam
    w, h = [int(v) for v in p.get('size', '900x600').lower().split('x')]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.samples = int(p.get('samples', 4)); cy.use_denoising = False; cy.use_adaptive_sampling = False; cy.seed = 7
    render_job.pick_device(sc, False)
    sc.render.film_transparent = True
    keep = tuple(p.get('keep', ['Maple ']))
    held = []
    for ob in bpy.data.objects:
        if ob.type in ('MESH', 'CURVE') and not ob.name.startswith(keep):
            held.append((ob, ob.is_holdout)); ob.is_holdout = True
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'; ims.file_format = 'PNG'; ims.color_mode = 'RGBA'; ims.color_depth = '8'; ims.color_management = 'FOLLOW_SCENE'
    path = os.path.join(outdir, '%s.png' % p['name'])
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for ob, o in held:
        ob.is_holdout = o
    sc.render.film_transparent = False
    print('MASK_DONE', path, flush=True)
    return path

os.makedirs(jobs['outdir'], exist_ok=True)
results = []
variants = jobs.get('variants') or [dict(name='', apply_pond=jobs.get('apply_pond'), stage_report=jobs.get('stage_report'), save_blend2=jobs.get('save_blend2'), pictures=jobs['pictures'])]
for vi, v in enumerate(variants):
    if vi > 0:
        bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
    apply_variant(v)
    pref = (v['name'] + '_') if v.get('name') else ''
    for p0 in v['pictures']:
        p = dict(p0)
        p['name'] = pref + p0['name']
        t = time.time()
        if p.get('exec'):
            exec(compile(p['exec'], 'picture_exec', 'exec'), {'bpy': bpy, 'math': math, 'p': p})
        try:
            hid = hide_prefixes(p['hide'], True) if p.get('hide') else []
            fn = {'final': final, 'mask': mask, 'branches': branch_probe}.get(p.get('mode'), preview)
            out = fn(p, jobs['outdir'])
            for ob, o in hid:
                ob.hide_render = o
            results.append((p['name'], 'ok', round(time.time() - t, 1)))
        except SystemExit as e:
            results.append((p['name'], 'exit: ' + str(e)))
        except Exception:
            traceback.print_exc()
            results.append((p['name'], 'error'))
print('CHARACTER_RENDER_ALL', json.dumps(results), 'total seconds', round(time.time() - T0, 1), flush=True)
