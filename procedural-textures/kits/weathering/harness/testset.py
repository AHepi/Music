# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE TEST SET as a list of picture jobs, from the set file's `test_set` block (so another set writes its own list without code):
#   lighting22   the earlier 22 lighting pictures: cameras x lights x states (dry 0/0, wet 0.85/0.5, heavy 1.0/0.8); names '<label>_<light>_<state>'
#   close views  five close views of the places (wall foot, downpipe, doorstep, gutter, cracked flag) x lights x states; names '<view>_<light>_<state>'
#   plates       the plate-size pictures of the set's plate cameras (plus the "behind" plate with the props hidden); names 'plate_<camera>_<light>_<state>[_behind]'
#   masks        the helper pictures the measures need (names are fixed, the measure scripts look for them):
#                  jmask_<camera>_<W>x<H>       joint / stone / road mask of the road for the sett joint measure (look base only)
#                  puddle_<label>_<state>       the water layer's puddle mask (red)       dirt_<label>_<state>   the earlier rubbish mask (red)       (look base only)
#                  zones_<camera>_<W>x<H>       footfall (R), crown (G), keepclear (B) bus masks, seen from the camera (look base)
#                  class_<camera>_<W>x<H>       a flat number per role (16 bit, /64)       depth_<camera>_<W>x<H>  distance in metres / 128 (16 bit)    (every look)
#                  layer_<key>_<label>_<state>  a kit layer's own mask for each t22 camera and wet state; layer_<key>_plate_<camera> at plate size (kit looks)
#   chart        a chart plate (widths and contrasts) is made by the integrator
# make_jobs(settings, look, scene_id, parts) returns the job dicts for ONE scene file in ONE look.
SAMPLES_PLATE = 48


def _lighting22(ts, scene_id, look):
    jobs = []
    for label, rows in ts['lighting22'].items():
        camera = ts['camera_of'][label]
        if ts.get('scene_of', {}).get(label, scene_id) != scene_id:
            continue
        w, h, samples = ts['size_of'][label]
        for light, states in rows:
            for state in states:
                jobs.append(dict(name=f'{label}_{light}_{state}', camera=camera, light=light, state=state, look=look, view='beauty', size=[w, h, samples], group='t22', label=label, keep_png=True))
    return jobs


def _close_views(ts, scene_id, look):
    jobs = []
    for view in ts.get('close_views', []):
        if ts.get('scene_of', {}).get(view, scene_id) != scene_id:
            continue
        for light in ts.get('close_view_lights', ['A']):
            for state in ts.get('close_view_states', ['dry', 'wet', 'heavy']):
                jobs.append(dict(name=f'{view}_{light}_{state}', camera=view, light=light, state=state, look=look, view='beauty', size=[960, 720, 24], group='close', label=view))
    return jobs


def _plates(ts, scene_id, look, settings):
    jobs = []
    plate = settings.get('plate') or {}
    for camera, light, state in ts.get('plates', []):
        if ts.get('scene_of', {}).get(camera, scene_id) != scene_id:
            continue
        w, h = (ts.get('plate_sizes') or {}).get(camera, plate['size'])
        base = dict(camera=camera, light=light, state=state, look=look, view='beauty', size=[w, h, SAMPLES_PLATE], group='plate', plate_height=h, keep_png=True)
        jobs.append(dict(base, name=f'plate_{camera}_{light}_{state}', label=camera))
        if settings.get('roles', {}).get('prop') and scene_id in (settings.get('roles', {}).get('prop', {}).get('scenes') or []):
            jobs.append(dict(base, name=f'plate_{camera}_{light}_{state}_behind', hide_roles=['prop', 'fire', 'sign'], label=camera))
    return jobs


def _plate_list(ts, scene_id, settings):
    """[(camera, w, h)] of the plate pictures of this scene."""
    plate = settings.get('plate') or {}
    out = []
    for camera, light, state in ts.get('plates', []):
        if ts.get('scene_of', {}).get(camera, scene_id) != scene_id:
            continue
        w, h = (ts.get('plate_sizes') or {}).get(camera, plate['size'])
        if (camera, w, h) not in out:
            out.append((camera, w, h))
    return out


def _masks(ts, scene_id, look, t22, settings, layer_keys):
    """The helper pictures for the measures (see the header). Joint, puddle and dirt pictures only in the look base (the earlier layers do not change with the kit)."""
    jobs, seen_cam, seen_ps = [], set(), set()
    base_look = look == 'base'
    for j in t22:
        if j['group'] != 't22':
            continue
        key = (j['camera'], j['size'][0], j['size'][1])
        if key not in seen_cam:
            seen_cam.add(key)
            w, h = j['size'][0], j['size'][1]
            if base_look:
                jobs.append(dict(name=f'jmask_{j["camera"]}_{w}x{h}', camera=j['camera'], light='A', state='dry', look='base', view='joint_mask', size=[w, h, 32], group='mask'))
            for view in ('class', 'depth'):
                jobs.append(dict(name=f'{view}_{j["camera"]}_{w}x{h}', camera=j['camera'], light='A', state='dry', look=look, view=view, size=[w, h, 1], group='mask'))
            jobs.append(dict(name=f'zones_{j["camera"]}_{w}x{h}', camera=j['camera'], light='A', state='dry', look='base', view='mask:footfall+crown+keepclear', size=[w, h, 1], group='mask'))
        ps = (j['label'], j['state'])
        if ps not in seen_ps:
            seen_ps.add(ps)
            w, h = j['size'][0], j['size'][1]
            if base_look and j['state'] != 'dry':
                jobs.append(dict(name=f'puddle_{j["label"]}_{j["state"]}', camera=j['camera'], light='A', state=j['state'], look='base', view='puddles', size=[w, h, 4], group='mask'))
                jobs.append(dict(name=f'dirt_{j["label"]}_{j["state"]}', camera=j['camera'], light='A', state=j['state'], look='base', view='dirt', size=[w, h, 4], group='mask'))
            for layer in layer_keys:
                jobs.append(dict(name=f'layer_{layer}_{j["label"]}_{j["state"]}', camera=j['camera'], light='A', state=j['state'], look=look, view='layer:' + layer, size=[w, h, 4], group='mask'))
    for camera, w, h in _plate_list(ts, scene_id, settings):
        for view in ('class', 'depth'):
            jobs.append(dict(name=f'{view}_{camera}_{w}x{h}', camera=camera, light='A', state='dry', look=look, view=view, size=[w, h, 1], group='mask', plate_height=h))
        for layer in layer_keys:
            jobs.append(dict(name=f'layer_{layer}_plate_{camera}', camera=camera, light='A', state='wet', look=look, view='layer:' + layer, size=[w, h, 1], group='mask', plate_height=h))
    return jobs


def make_jobs(settings, look, scene_id, parts=('t22', 'close', 'plates', 'masks'), layer_keys=()):
    ts = settings.get('test_set') or {}
    jobs = []
    t22 = _lighting22(ts, scene_id, look) if ts.get('lighting22') else []
    if 't22' in parts:
        jobs += t22
    if 'close' in parts:
        jobs += _close_views(ts, scene_id, look)
    if 'plates' in parts:
        jobs += _plates(ts, scene_id, look, settings)
    if 'masks' in parts:
        jobs += _masks(ts, scene_id, look, t22, settings, layer_keys)
    return jobs


# The masks of the debug sheet "where each thing may go": a few of the bus masks that matter most, seen from the set's cameras (plain light, raw numbers)
SHEET_MASKS = ['height', 'shade', 'dampness', 'sheltered', 'drip', 'wall_dist', 'lowness', 'crown', 'footfall', 'keepclear', 'moss_site', 'weed_site', 'algae_site', 'edge_dist']


def mask_view_jobs(settings, scene_id, names=None, small=(270, 480)):
    """One job per mask and camera of the set's lighting pictures in this scene (names maskview_<mask>_<camera>), size = a quarter of the test picture, one sample."""
    ts = settings.get('test_set') or {}
    jobs, seen = [], set()
    for label, cam in ts.get('camera_of', {}).items():
        if ts.get('scene_of', {}).get(label, scene_id) != scene_id or cam in seen:
            continue
        seen.add(cam)
        w, h = ts['size_of'][label][:2]
        k = small[0] / float(w)
        size = [int(round(w * k)), int(round(h * k)), 1]
        for name in (names or SHEET_MASKS):
            jobs.append(dict(name=f'maskview_{name}_{cam}', camera=cam, light='A', state='dry', look='today', view=f'mask:{name}', size=size, group='maskview', plate_height=settings.get('plate')['size'][1]))
    return jobs
