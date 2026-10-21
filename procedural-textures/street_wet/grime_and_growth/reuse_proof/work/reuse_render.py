# What this does (plain words): runs inside Blender on the rented machine. Opens the courtyard (never saves it), draws the three views of the proof BEFORE (the scene as the add-on
# built it), then puts the weathering kit on with ONE call (aw.apply) and draws the same three views AFTER; optional extra pictures (each layer alone, the where-pictures).
# Pictures are small JPG. Everything it measures goes into result.json.
#   blender -b --disable-autoexec courtyard_final.blend --python reuse_render.py -- CONFIG.json
import json, os, sys, time, traceback
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
sys.dont_write_bytecode = True
import bpy
import numpy as np
import apply_weathering as aw
from apply import settings as settings_module
from harness import cameras

cfg = json.load(open(sys.argv[sys.argv.index('--') + 1]))
OUT = cfg['out']
os.makedirs(OUT, exist_ok=True)
TAG = cfg.get('tag', 'r')
LOOK = cfg.get('look', 'mossy_courtyard_rough')
SAMPLES = cfg.get('samples', 64)
PLATE_H = cfg.get('plate_height', 1600)
SIZES = cfg['sizes']                       # {view: [w, h]}
result = dict(tag=TAG, look=LOOK, seconds={}, stats={}, errors=[])
scene = bpy.context.scene


def setup(w, h):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = w, h, 100
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 93
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.dither_intensity = 0.0
    scene.eevee.taa_render_samples = SAMPLES
    scene.eevee.use_raytracing = True
    scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
    scene.render.filter_size = 1.5
    if hasattr(scene.eevee, 'shadow_pool_size') and w > 1080:
        scene.eevee.shadow_pool_size = '1024'
        scene.eevee.shadow_resolution_scale = min(1.0, 1080 / w)


def read(path):
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = 'Non-Color'
    w, h = image.size
    a = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
    bpy.data.images.remove(image)
    return a


def draw(name, cam, view, handle=None):
    w, h = SIZES[view]
    setup(w, h)
    scene.camera = cam
    if handle is not None:
        handle.camera(cam, plate_height=PLATE_H)
    path = os.path.join(OUT, f'{TAG}_{name}.jpg')
    scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    result['seconds'][name] = round(time.time() - t, 2)
    return read(path)


def compare(a, b):
    d = np.abs(a - b)
    luma = lambda x: 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    la, lb = luma(a), luma(b)
    return dict(changed_over_3_steps=round(float((d.max(axis=2) > 3 / 255).mean()), 4), changed_over_10_steps=round(float((d.max(axis=2) > 10 / 255).mean()), 4),
                mean_brightness_before=round(float(la.mean()), 4), mean_brightness_after=round(float(lb.mean()), 4), brightness_ratio=round(float(lb.mean() / max(la.mean(), 1e-6)), 4),
                share_under_0p13_before=round(float((la < 0.13).mean()), 4), share_under_0p13_after=round(float((lb < 0.13).mean()), 4))


try:
    settings = settings_module.load_set('japanese_courtyard')
    cams = {'photo': bpy.data.objects['Camera']}
    made, notes = cameras.make_all(settings, 'courtyard')
    for name, obj in made.items():
        if name != 'photo':
            cams[name] = obj
    views = [v for v in cfg.get('views', ['photo', 'lantern_rocks', 'hall_posts']) if v in cams]
    before = {}
    if cfg.get('before', True):
        for view in views:
            before[view] = draw(f'{view}_before', cams[view], view)
    t = time.time()
    w = aw.apply('japanese_courtyard', LOOK, state='dry')
    result['seconds']['apply'] = round(time.time() - t, 1)
    result['problems'] = w.problems
    result['applied'] = {k: len(v) for k, v in w.applied.items()}
    rep = w.report()
    result['report'] = {k: rep[k] for k in ('roles', 'hookable', 'skipped', 'unassigned_objects', 'mask_pack', 'earlier_layers')}
    after = {}
    for view in views:
        after[view] = draw(f'{view}_after', cams[view], view, w)
        if view in before:
            result['stats'][view] = compare(before[view], after[view])
        try:
            rows = w.kit.growth.table(cams[view])
            kinds = {}
            for r in rows:
                kinds[r['species']] = kinds.get(r['species'], 0) + 1
            result['stats'].setdefault(view, {})['plants_total'] = len(rows)
            result['stats'][view]['plants_by_kind'] = kinds
        except Exception as error:
            result['errors'].append('growth table: ' + repr(error))
    again = draw('photo_after_again', cams['photo'], 'photo', w)
    result['stats']['two_draws_of_the_same_state'] = compare(after['photo'], again)
    # each layer alone
    solo = cfg.get('solo', [])
    keys = [k for k in w.layers]
    for view in cfg.get('solo_views', ['photo']):
        if view not in cams:
            continue
        for layer in solo:
            if layer not in keys:
                continue
            for k in keys:
                w.set_layer_master(k, 0.0)
            w.set_layer_master(layer, 1.0)
            pic = draw(f'{view}_solo_{layer}', cams[view], view, w)
            if view in before:
                result['stats'][f'solo_{view}_{layer}'] = compare(before[view], pic)
    for k in keys:
        w.set_layer_master(k, 1.0)
    # the where-pictures (plain light), main view
    for item in cfg.get('masks', []):
        view, mask = item if isinstance(item, list) else ('photo', item)
        try:
            w.show_mask(mask)
            draw(f'{view}_mask_{mask}', cams[view], view, w)
            w.hide_mask()
        except Exception as error:
            result['errors'].append(f'mask {mask}: {error!r}')
            try:
                w.hide_mask()
            except Exception:
                pass
    # the last test: take everything off and draw the main view again: must equal the scene as it was
    if cfg.get('remove_test', True) and 'photo' in before:
        t = time.time()
        w.remove()
        result['seconds']['remove'] = round(time.time() - t, 1)
        again = draw('photo_after_remove', cams['photo'], 'photo')
        result['stats']['remove_gives_the_scene_back'] = compare(before['photo'], again)
except Exception:
    result['errors'].append(traceback.format_exc())
json.dump(result, open(os.path.join(OUT, f'{TAG}_result.json'), 'w'), indent=1)
print('RESULT', json.dumps(result)[:3000])
