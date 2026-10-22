# POND BUILDER copy of fix_render.py (22 October character round): same harness, the stage is stage_pond.py in this folder; extra picture kind 'mask'.
# What this does (plain words): draws pictures of the garden for the FIX ROUND, on the rented card (or small, locally), in ONE Blender start.
# For every "variant" in the job file it (1) re-opens the saved garden scene (so each variant starts from the same place), (2) applies the fix stage
# (stage_pond.py, in this folder) with that variant's options, (3) draws the listed pictures: either small JPG previews (with an optional crop border)
# or final pictures through the light builder's render_job.main (PNG + light-group EXR + log, same settings as the first round).
# Run on the card:  /workspace/blender/blender -b --disable-autoexec -P fix_render.py -- JOBS.json
# JOBS.json = {"blend": ".../garden_real.blend", "look": "real"|"painted", "outdir": "/abs/folder",
#              "variants": [{"name": "A", "fix": {...options for stage_fix.apply...} | null,
#                            "pictures": [{"name": "hero", "camera": "photo", "size": "1200x800", "samples": 96, "seed": 7,
#                                          "mode": "preview"|"final", "exr": false, "border": [x0, y0, x1, y1] (fractions 0..1, optional), "extra": []}]}]}
import bpy
import sys
import os
import json
import math
import time
import traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_STAGE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final/stage'
for p in (FINAL_STAGE, HERE):          # HERE first
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

import render_job   # noqa: E402  (the first round's render job, read-only, on the store)

jobs = json.load(open(sys.argv[sys.argv.index('--') + 1]))
T0 = time.time()


def set_dot_angle(camera, height):
    """Same as the first round: Dot Angle on every weathering-kit scale node = angular size of one picture dot (real look only)."""
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


def preview(p, outdir, vname):
    sc = bpy.context.scene
    cam = bpy.data.objects[p.get('camera', 'photo')]
    sc.camera = cam
    w, h = [int(v) for v in p.get('size', '1200x800').lower().split('x')]
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
    dev = render_job.pick_device(sc, False)
    if not dev['gpu_in_use']:
        print('WARNING: no graphics card in use', flush=True)
    b = p.get('border')
    sc.render.use_border = bool(b)
    if b:
        sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = b
        sc.render.use_crop_to_border = True
    if jobs.get('look', 'real') == 'real':
        set_dot_angle(cam, h)
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'
    fmt = p.get('format', 'JPEG')
    ims.file_format = fmt
    if fmt == 'JPEG':
        ims.quality = int(p.get('quality', 88))
        ims.color_mode = 'RGB'
    ims.color_management = 'FOLLOW_SCENE'
    path = os.path.join(outdir, f"{vname}__{p['name']}.{'jpg' if fmt == 'JPEG' else 'png'}")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    sc.render.use_border = False
    print('PREVIEW_DONE', path, round(time.time() - t, 1), 's', flush=True)
    return path


def mask(p, outdir, vname):
    """Silhouette picture: only objects whose name starts with one of p['keep'] stay solid, every other mesh/curve object is a holdout (it still hides
    what is behind it), film transparent, RGBA PNG. The alpha channel is the visible silhouette of the kept parts."""
    sc = bpy.context.scene
    cam = bpy.data.objects[p.get('camera', 'photo')]
    sc.camera = cam
    w, h = [int(v) for v in p.get('size', '800x533').lower().split('x')]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.samples = int(p.get('samples', 4)); cy.use_denoising = False; cy.use_adaptive_sampling = False
    cy.seed = 7
    render_job.pick_device(sc, False)
    sc.render.film_transparent = True
    keep = tuple(p.get('keep', ['Maple ']))
    held = []
    for ob in bpy.data.objects:
        kept = (ob.name in keep) if p.get('exact') else ob.name.startswith(keep)
        if ob.type in ('MESH', 'CURVE') and not kept:
            held.append((ob, ob.is_holdout)); ob.is_holdout = True
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'; ims.file_format = 'PNG'; ims.color_mode = 'RGBA'; ims.color_depth = '8'
    ims.color_management = 'FOLLOW_SCENE'
    path = os.path.join(outdir, f"{vname}__{p['name']}.png")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    for ob, old in held:
        ob.is_holdout = old
    sc.render.film_transparent = False
    print('MASK_DONE', path, round(time.time() - t, 1), 's', flush=True)
    return path


def final(p, outdir, vname):
    cam = bpy.data.objects.get(p.get('camera', 'photo'))
    h = int(p['size'].lower().split('x')[1])
    nscale = set_dot_angle(cam, h) if jobs.get('look', 'real') == 'real' else 0
    base = os.path.join(outdir, p['name'])
    argv = ['--out', base, '--camera', p.get('camera', 'photo'), '--size', p['size'], '--samples', str(p.get('samples', 512)), '--seed', str(p.get('seed', 7)),
            '--require-gpu'] + (['--exr'] if p.get('exr') else []) + list(p.get('extra', []))
    sys.argv = [sys.argv[0], '--'] + argv
    print('FINAL_START', base, 'dot-angle nodes set:', nscale, flush=True)
    render_job.main()
    return base + '.png'


os.makedirs(jobs['outdir'], exist_ok=True)
results = []
for v in jobs['variants']:
    t = time.time()
    bpy.ops.wm.open_mainfile(filepath=jobs['blend'])
    bpy.context.preferences.filepaths.save_version = 0
    if v.get('fix') is not None:
        import stage_pond
        import importlib
        importlib.reload(stage_pond)
        opts = dict(v['fix'])
        try:
            rep = stage_pond.apply(opts)
            json.dump(rep, open(os.path.join(jobs['outdir'], f"{v['name']}__stage_report.json"), 'w'), indent=1, default=str)
        except Exception:
            traceback.print_exc()
            results.append((v['name'], 'STAGE ERROR'))
            continue
    if v.get('save_blend'):
        bpy.ops.wm.save_as_mainfile(filepath=v['save_blend'], copy=True)
        print('SAVED_BLEND', v['save_blend'], os.path.getsize(v['save_blend']), flush=True)
    for p in v['pictures']:
        try:
            out = {'final': final, 'mask': mask}.get(p.get('mode'), preview)(p, jobs['outdir'], v['name'])
            results.append((v['name'], p['name'], 'ok', out, round(time.time() - t, 1)))
        except SystemExit as e:
            results.append((v['name'], p['name'], 'exit: ' + str(e)))
        except Exception:
            traceback.print_exc()
            results.append((v['name'], p['name'], 'error'))
print('FIX_RENDER_ALL', json.dumps(results), 'total seconds', round(time.time() - T0, 1), flush=True)
