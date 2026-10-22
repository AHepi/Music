# What this does (plain words): "render_job" draws ONE picture of a garden scene file with Blender, on the rented graphics card (or locally, small), and
# writes a log so the picture can be reproduced and checked. It is the one script the RunPod job runs for every picture of the garden plan.
#   1 opens the scene you give it (the stages have already been applied and saved by the final step), or - for tests - applies stage_light first
#   2 picks the camera ('photo' or 'veranda'), the size, the samples and the seed
#   3 switches Cycles to the graphics card (OptiX first, then CUDA), PRINTS the devices and checks one really is in use (--require-gpu stops if not)
#   4 makes sure the light groups exist, draws, writes <out>.png (the look you see) and, with --exr, <out>.exr (multi-layer, linear, every light group)
#   5 writes <out>.json: engine, device, samples, seed, view transform, exposure, size, camera, seconds, Blender version and SHA-256 of the scene file and of
#     every file written; with --check-groups also whether the light groups add up to the picture (needs the EXR; use --no-denoise for an exact check)
# Run (inside Blender, headless):
#   blender -b --disable-autoexec SCENE.blend -P render_job.py -- --out /abs/base --camera photo --size 2400x1600 --samples 512 --seed 7 --exr
# Options:
#   --out BASE          output path without extension (required unless --dry-run)
#   --camera NAME       photo (default) or veranda   --size WxH   (default: the scene's)   --samples N (default 384)   --seed N (default 7)
#   --engine E          CYCLES (default) | BLENDER_EEVEE | BLENDER_WORKBENCH   (EEVEE and Workbench only for quick looks)
#   --apply-stage LOOK  real|painted: apply stage_light (this folder) to the open scene first (for testing the stage alone)
#   --stage-opts JSON   extra options for stage_light.apply, e.g. '{"sun_energy": 10}'
#   --evening           also apply stage_light.apply_evening() (needs --apply-stage, or a scene saved with the main stage)
#   --exposure X        override the view-transform exposure   --no-denoise   --exr   --check-groups   --require-gpu   --cpu   --dry-run
#   --pano X,Y,Z        draw a full 360-degree (equirectangular) picture from that spot instead of a camera, north in the middle
#   --hide PREFIXES     comma list of object-name prefixes to hide for a quick look (never for finals)
#   --hide-small        shortcut for the leaf/moss hide list used for local quick looks
import hashlib
import json
import math
import os
import sys
import time

import bpy

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))


def parse(argv):
    a = dict(out=None, camera='photo', size=None, samples=384, seed=7, engine='CYCLES', apply_stage=None, evening=False, exposure=None, denoise=True,
             exr=False, check_groups=False, require_gpu=False, cpu=False, dry_run=False, hide='', pct=100, stage_opts='', pano=None)
    i = 0
    while i < len(argv):
        k = argv[i]
        nxt = argv[i + 1] if i + 1 < len(argv) else None
        if k == '--out':
            a['out'] = nxt; i += 1
        elif k == '--camera':
            a['camera'] = nxt; i += 1
        elif k == '--size':
            a['size'] = nxt; i += 1
        elif k == '--samples':
            a['samples'] = int(nxt); i += 1
        elif k == '--seed':
            a['seed'] = int(nxt); i += 1
        elif k == '--engine':
            a['engine'] = nxt; i += 1
        elif k == '--apply-stage':
            a['apply_stage'] = nxt; i += 1
        elif k == '--exposure':
            a['exposure'] = float(nxt); i += 1
        elif k == '--hide':
            a['hide'] = nxt; i += 1
        elif k == '--pano':
            a['pano'] = nxt; i += 1
        elif k == '--stage-opts':
            a['stage_opts'] = nxt; i += 1
        elif k == '--pct':
            a['pct'] = int(nxt); i += 1
        elif k == '--hide-small':
            a['hide'] = 'Maple leaves,Pine pads,Bamboo leaves,Fallen leaves'
        elif k == '--evening':
            a['evening'] = True
        elif k == '--no-denoise':
            a['denoise'] = False
        elif k == '--exr':
            a['exr'] = True
        elif k == '--check-groups':
            a['check_groups'] = True; a['exr'] = True
        elif k == '--require-gpu':
            a['require_gpu'] = True
        elif k == '--cpu':
            a['cpu'] = True
        elif k == '--dry-run':
            a['dry_run'] = True
        else:
            raise SystemExit('unknown option ' + k)
        i += 1
    return a


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def pick_device(sc, want_cpu=False):
    """Cycles on the graphics card: OptiX first, then CUDA, then HIP/oneAPI; CPU if nothing. Returns a dict that says what is really used."""
    info = dict(requested='CPU' if want_cpu else 'GPU', backend='CPU', devices=[], gpu_in_use=False)
    if want_cpu:
        sc.cycles.device = 'CPU'
        return info
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            prefs.compute_device_type = t
        except TypeError:
            continue
        try:
            prefs.get_devices()
        except Exception:
            pass
        gpus = [d for d in prefs.devices if d.type == t]
        if gpus:
            for d in prefs.devices:
                d.use = (d.type == t)
            sc.cycles.device = 'GPU'
            info['backend'] = t
            info['devices'] = [(d.name, d.type, bool(d.use)) for d in prefs.devices]
            info['gpu_in_use'] = True
            return info
    sc.cycles.device = 'CPU'
    info['devices'] = [(d.name, d.type, bool(d.use)) for d in prefs.devices]
    return info


def exr_group_check(exr_path):
    """Do the light-group layers add up to the Combined layer? Returns a dict (needs OpenImageIO inside Blender)."""
    try:
        import numpy as np
        import OpenImageIO as oiio
    except Exception as e:
        return dict(error='no OpenImageIO/numpy: ' + str(e))
    inp = oiio.ImageInput.open(exr_path)
    if inp is None:
        return dict(error=oiio.geterror())
    parts, i = [], 0
    while inp.seek_subimage(i, 0):
        parts.append(inp.spec().getattribute('name') or '')
        i += 1
    inp.close()
    layers = {}
    for k, n in enumerate(parts):
        tail = n.split('.', 1)[-1]
        if tail == 'Combined' or tail.startswith('Combined_'):
            inp = oiio.ImageInput.open(exr_path)
            inp.seek_subimage(k, 0)
            spec = inp.spec()
            pix = np.array(inp.read_image(k, 0, 0, 3, 'float'), dtype=np.float32).reshape(spec.height, spec.width, 3)   # first argument = the part
            inp.close()
            layers[tail] = pix
    if 'Combined' not in layers:
        return dict(error='no Combined layer', parts=parts)
    groups = [g for g in layers if g != 'Combined']
    if not groups:
        return dict(error='no light-group layers', parts=parts)
    total = sum(layers[g] for g in groups)
    C = layers['Combined']
    lum = lambda x: 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    tot = float(lum(C).mean()) or 1e-9
    return dict(groups=groups, rel_error=round(float(np.abs(total - C).mean() / max(float(C.mean()), 1e-9)), 5),
                share={g[len('Combined_'):] if g.startswith('Combined_') else g: round(float(lum(layers[g]).mean()) / tot, 4) for g in groups})


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    a = parse(argv)
    sc = bpy.context.scene
    log = dict(blender=bpy.app.version_string, scene_file=bpy.data.filepath, args=a, stage=None)
    if bpy.data.filepath:
        log['scene_sha256'] = sha256(bpy.data.filepath)
    if a['apply_stage']:
        sys.path.insert(0, HERE)
        import stage_light
        opts = {'look': a['apply_stage']}
        if a['stage_opts']:
            opts.update(json.loads(a['stage_opts']))
        rep = stage_light.apply(opts)
        log['stage'] = dict(look=a['apply_stage'], created=rep['created'], changed=rep['changed'])
        if a['evening']:
            stage_light.apply_evening({'look': a['apply_stage']})
            log['stage']['evening'] = True
    elif a['evening']:
        sys.path.insert(0, HERE)
        import stage_light
        stage_light.apply_evening({'look': (sc.get('garden_light_applied') or 'real')})
        log['stage'] = dict(evening=True)
    cam = bpy.data.objects.get(a['camera'])
    if a['pano']:      # a full 360-degree look from one spot (x,y,z), north (+y) in the middle: proves the backdrop goes all the way round
        import math
        x, y, z = [float(v) for v in a['pano'].split(',')]
        cd = bpy.data.cameras.new('pano360')
        cd.type = 'PANO'
        try:
            cd.panorama_type = 'EQUIRECTANGULAR'
        except Exception:
            cd.cycles.panorama_type = 'EQUIRECTANGULAR'
        cam = bpy.data.objects.new('pano360', cd)
        bpy.context.scene.collection.objects.link(cam)
        cam.location = (x, y, z)
        cam.rotation_euler = (math.radians(90), 0, 0)
    if cam is None and a['camera'] == 'photo':
        cam = bpy.data.objects.get('Camera')
    if cam is None or cam.type != 'CAMERA':
        raise SystemExit('camera not found: ' + a['camera'])
    sc.camera = cam
    for prefix in [p for p in a['hide'].split(',') if p]:
        for ob in bpy.data.objects:
            if ob.name.startswith(prefix):
                ob.hide_render = True
    if a['size']:
        w, h = [int(v) for v in a['size'].lower().split('x')]
        sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = a['pct']
    sc.render.engine = a['engine']
    if a['exposure'] is not None:
        sc.view_settings.exposure = a['exposure']
    dev = None
    if a['engine'] == 'CYCLES':
        cy = sc.cycles
        cy.samples = a['samples']
        cy.seed = a['seed']
        cy.use_animated_seed = False
        cy.use_adaptive_sampling = True
        cy.adaptive_threshold = 0.01
        cy.use_denoising = bool(a['denoise'])
        cy.caustics_reflective = cy.caustics_refractive = False
        dev = pick_device(sc, a['cpu'])
        print('DEVICES', json.dumps(dev), flush=True)
        if a['require_gpu'] and not dev['gpu_in_use']:
            raise SystemExit('no graphics card for Cycles (--require-gpu)')
    elif a['engine'] == 'BLENDER_EEVEE':
        try:
            sc.eevee.taa_render_samples = max(16, min(a['samples'], 64))
        except Exception:
            pass
    log.update(engine=a['engine'], device=dev, samples=a['samples'], seed=a['seed'], camera=sc.camera.name,
               size=[sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
               view_transform=sc.view_settings.view_transform, look=sc.view_settings.look, exposure=sc.view_settings.exposure,
               denoise=bool(a['denoise']), lightgroups=[g.name for g in sc.view_layers[0].lightgroups], compositor=bool(sc.render.use_compositing))
    if a['dry_run']:
        print('DRY_RUN_PLAN', json.dumps(log, default=str, indent=1))
        return
    if not a['out']:
        raise SystemExit('--out is required')
    os.makedirs(os.path.dirname(a['out']) or '.', exist_ok=True)
    ims = sc.render.image_settings
    saved = (ims.media_type, ims.file_format, ims.color_depth, ims.color_mode, ims.color_management, sc.render.filepath)
    t0 = time.time()
    files = {}
    try:
        if a['exr']:
            ims.media_type = 'MULTI_LAYER_IMAGE'
            ims.color_depth = '16'
            try:
                ims.exr_codec = 'DWAA'
            except Exception:
                pass
            sc.render.filepath = a['out'] + '.exr'
            bpy.ops.render.render(write_still=True, scene=sc.name)
            files['exr'] = a['out'] + '.exr'
            ims.media_type = 'IMAGE'
            ims.file_format = 'PNG'
            ims.color_depth = '8'
            ims.color_mode = 'RGB'
            ims.color_management = 'FOLLOW_SCENE'
            bpy.data.images['Render Result'].save_render(filepath=a['out'] + '.png', scene=sc)
        else:
            ims.media_type = 'IMAGE'
            ims.file_format = 'PNG'
            ims.color_depth = '8'
            ims.color_mode = 'RGB'
            ims.color_management = 'FOLLOW_SCENE'
            sc.render.filepath = a['out'] + '.png'
            bpy.ops.render.render(write_still=True, scene=sc.name)
        files['png'] = a['out'] + '.png'
    finally:
        ims.media_type = saved[0]
        try:
            ims.file_format = saved[1]
        except TypeError:
            pass
        ims.color_depth, ims.color_mode, ims.color_management = saved[2], saved[3], saved[4]
        sc.render.filepath = saved[5]
    log['render_seconds'] = round(time.time() - t0, 2)
    log['files'] = {k: dict(path=v, bytes=os.path.getsize(v), sha256=sha256(v)) for k, v in files.items()}
    if a['check_groups'] and 'exr' in files:
        log['group_check'] = exr_group_check(files['exr'])
        log['group_check']['denoise_on'] = bool(a['denoise'])
    json.dump(log, open(a['out'] + '.json', 'w'), indent=1, default=str)
    print('RENDER_JOB_DONE', json.dumps({k: log[k] for k in ('engine', 'samples', 'seed', 'camera', 'size', 'render_seconds')}, default=str), flush=True)
    if 'group_check' in log:
        print('GROUP_CHECK', json.dumps(log['group_check']), flush=True)


if __name__ == '__main__':
    main()
