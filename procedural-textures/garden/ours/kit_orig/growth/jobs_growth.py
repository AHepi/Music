# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE JOB LISTS of the growth layer's test pictures (plain Python). make(settings, scene_id, name) returns a job file (the kit runner's format, drawn by runner_growth.py):
#   pilot   a quick look: one today picture, the plate camera without and with growth (wet), a gutter close view dry and wet without and with growth, the layer view, pieces.json
#   full    the kit's own test set in the look `solo:growth` (22 lighting pictures, close views, plates, the helper pictures the measures read, the growth layer's own mask pictures)
#           plus pieces.json of every plate camera
#   times   the plate cameras without and with growth, three draws each, and with the growth dials at 0.5, 1, 2 (time per 1,000 pieces); pieces.json of each
#   dials   what each main dial does, on one close camera (before and after pairs for the sheet)
#   zero    amount 0 against the plain picture (identical?) at plate size 16 bit, and with every dial at 0
# Every job names its dials in full (the runner keeps the last dials until told otherwise).
from harness import testset

PLATE_SAMPLES = 48


def _plate_size(settings):
    return list((settings.get('plate') or {})['size'])


def _plate_jobs(settings, scene_id, look, repeat=1, tag='', dials=None, pieces=False, hide=False):
    ts = settings.get('test_set') or {}
    plate = settings.get('plate') or {}
    jobs = []
    for camera, light, state in ts.get('plates', []):
        if ts.get('scene_of', {}).get(camera, scene_id) != scene_id:
            continue
        w, h = (ts.get('plate_sizes') or {}).get(camera, plate['size'])
        for r in range(repeat):
            name = f'plate_{camera}_{light}_{state}' + (f'_{tag}' if tag else '') + (f'_r{r + 1}' if repeat > 1 else '')
            job = dict(name=name, camera=camera, light=light, state=state, look=look, view='beauty', size=[w, h, PLATE_SAMPLES], group='plate', plate_height=h, label=camera, keep_png=(not tag))
            if dials:
                job['dials'] = dials
            if pieces and r == 0:
                job['pieces_json'] = True
            jobs.append(job)
    return jobs


def make(settings, scene_id, name, **kw):
    ts = settings.get('test_set') or {}
    pw, ph = _plate_size(settings)
    scene = next(s for s in settings.scenes if s['id'] == scene_id)
    spec = dict(set=settings.id, scene=scene_id, pack=True, feature_dirs=list(settings.get('feature_report_dirs', [])), jobs=[])
    jobs = spec['jobs']
    today_cam = scene.get('default_camera')
    views = ts.get('close_views') or []
    close_cam = kw.get('camera') or (settings.get('growth') or {}).get('close_camera') or (views[min(3, len(views) - 1)] if views else today_cam)     # the camera a close look is drawn from (the set's growth.close_camera, else its fourth close view)
    cam = close_cam
    jobs.append(dict(name=f'today_{scene_id}', camera=today_cam, light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene=scene_id))
    if name == 'pilot':
        for look in ('base', 'solo:growth'):
            tag = 'base' if look == 'base' else 'growth'
            jobs.append(dict(name=f'plate_main_{tag}', camera=today_cam, light='A', state='wet', look=look, view='beauty', size=[pw, ph, 48], group='plate', plate_height=ph, pieces_json=(look != 'base')))
            for state in ('dry', 'wet'):
                jobs.append(dict(name=f'close_{cam}_{state}_{tag}', camera=cam, light='A', state=state, look=look, view='beauty', size=[960, 720, 24], group='close', pieces_json=False))
        jobs.append(dict(name='layer_growth_plate_main', camera=today_cam, light='A', state='wet', look='solo:growth', view='layer:growth', size=[pw, ph, 1], plate_height=ph, group='layer'))
    elif name == 'full':
        spec['jobs'] = testset.make_jobs(settings, 'solo:growth', scene_id, ('t22', 'close', 'plates', 'masks'), layer_keys=('growth',))
        spec['jobs'] += [j for j in jobs if j['look'] == 'today']
        spec['jobs'] += [dict(j, name='plants_' + j['name'], keep_png=False, pieces_json=True, size=[270, 480, 1]) for j in spec['jobs'] if j.get('group') == 'plate' and j['look'] == 'solo:growth' and not j['name'].endswith('_behind')]
    elif name == 'times':
        spec['jobs'] += _plate_jobs(settings, scene_id, 'base', repeat=3, tag='base')
        for tag, mult in (('g1', 1.0), ('g05', 0.5), ('g2', 2.0)):
            dials = {'growth': {'weeds_amount': mult, 'cushions_amount': mult}}
            spec['jobs'] += _plate_jobs(settings, scene_id, 'solo:growth', repeat=3 if tag == 'g1' else 1, tag=tag, dials=dials, pieces=True)
    elif name == 'gain':
        cam = today_cam
        jobs.append(dict(name='gain_base_wet', camera=cam, light='A', state='wet', look='base', view='beauty', size=[pw, ph, 32], group='gain', plate_height=ph, keep_png=True))
        jobs.append(dict(name='gain_base_dry', camera=cam, light='A', state='dry', look='base', view='beauty', size=[pw, ph, 32], group='gain', plate_height=ph, keep_png=True))
        for gain in kw.get('gains', (3.4, 4.4, 5.4)):
            for state in ('dry', 'wet'):
                jobs.append(dict(name=f'gain{gain:g}_{state}', camera=cam, light='A', state=state, look='solo:growth', view='beauty', size=[pw, ph, 32], group='gain', plate_height=ph, keep_png=True,
                                 dials={'growth': {'colour_gain': gain}}))
        jobs.append(dict(name='layer_growth_plate_main', camera=cam, light='A', state='wet', look='solo:growth', view='layer:growth', size=[pw, ph, 1], plate_height=ph, group='layer',
                         dials={'growth': {'colour_gain': 1.0}}))
    elif name == 'sat':
        cam = today_cam
        jobs.append(dict(name='sat_base_wet', camera=cam, light='A', state='wet', look='base', view='beauty', size=[pw, ph, 32], group='sat', plate_height=ph, keep_png=True))
        for sat in kw.get('sats', (1.0, 0.75, 0.55, 0.4)):
            jobs.append(dict(name=f'sat{sat:g}_wet', camera=cam, light='A', state='wet', look='solo:growth', view='beauty', size=[pw, ph, 32], group='sat', plate_height=ph, keep_png=True,
                             dials={'growth': {'colour_gain': 1.0, 'colour_sat': sat}}))
        jobs.append(dict(name='layer_growth_plate_main', camera=cam, light='A', state='wet', look='solo:growth', view='layer:growth', size=[pw, ph, 1], plate_height=ph, group='layer',
                         dials={'growth': {'colour_gain': 1.0, 'colour_sat': 1.0}}))
    elif name == 'stress':
        spec['jobs'] += _plate_jobs(settings, scene_id, 'base', repeat=3, tag='base')
        for tag, cover in (('s1', 0.02), ('s2', 0.04), ('s3', 0.08)):
            dials = {'growth': {'weed_cover': 0.03, 'cushion_cover': cover, 'gutter_tuft_share': 0.1, 'max_pieces': 6000.0, 'distance': 25.0}}
            spec['jobs'] += _plate_jobs(settings, scene_id, 'solo:growth', repeat=3 if tag == 's3' else 1, tag=tag, dials=dials, pieces=True)
    elif name == 'tune':
        cams = [c for c, l, st in ts.get('plates', []) if ts.get('scene_of', {}).get(c, scene_id) == scene_id and (not kw.get('cameras') or c in kw['cameras'])]
        for cam in cams:
            light = next(l for c, l, st in ts['plates'] if c == cam)
            w, h = (ts.get('plate_sizes') or {}).get(cam, (pw, ph))
            for label, dial in kw.get('variants', ()):
                jobs.append(dict(name=f'tune_{label}_{cam}', camera=cam, light=light, state='wet', look='solo:growth', view='beauty', size=[w, h, 24], group='tune', plate_height=h, keep_png=True,
                                 dials={'growth': dial}))
            jobs.append(dict(name=f'layer_growth_plate_{cam}', camera=cam, light=light, state='wet', look='solo:growth', view='layer:growth', size=[w, h, 1], plate_height=h, group='layer',
                             dials={'growth': kw.get('variants', (('x', {}),))[0][1]}))
            jobs.append(dict(name=f'depth_{cam}', camera=cam, light=light, state='wet', look='solo:growth', view='depth', size=[w, h, 1], plate_height=h, group='layer',
                             dials={'growth': kw.get('variants', (('x', {}),))[0][1]}))
    elif name == 'spots':
        spec['extra_cameras'] = [dict(name=c['name'], location=c['location'], look_at=c['look_at'], fov_v=c.get('fov_v', 42.0)) for c in kw['cameras']]
        for c in kw['cameras']:
            jobs.append(dict(name=f'spots_{c["name"]}_base', camera=c['name'], light='A', state='wet', look='base', view='beauty', size=[960, 720, 32], group='spots', plate_height=ph))
            for state in ('wet', 'dry'):
                jobs.append(dict(name=f'spots_{c["name"]}_{state}_growth', camera=c['name'], light='A', state=state, look='solo:growth', view='beauty', size=[960, 720, 32], group='spots', plate_height=ph,
                                 pieces_json=(state == 'wet')))
    elif name == 'view':
        w, h = kw.get('size', (1200, 800))
        for tag, look in (('base', 'base'), ('growth', 'solo:growth')):
            jobs.append(dict(name=f'view_{tag}', camera=today_cam, light='A', state='dry', look=look, view='beauty', size=[w, h, 48], group='view', plate_height=ph, pieces_json=(tag == 'growth')))
        jobs.append(dict(name='view_layer', camera=today_cam, light='A', state='dry', look='solo:growth', view='layer:growth', size=[w, h, 1], group='view', plate_height=ph))
        jobs.append(dict(name='view_growth_neglected', camera=today_cam, light='A', state='dry', look='solo:growth', view='beauty', size=[w, h, 48], group='view', plate_height=ph,
                         dials={'growth': {'weeds_amount': 1.0, 'weed_cover': 0.012, 'gutter_tuft_share': 0.05, 'cushions_amount': 1.5, 'cushion_cover': 0.02}}))
    elif name == 'zero':
        cam = today_cam
        spec['jobs'] += [dict(name='zero_base', camera=cam, light='A', state='wet', look='base', view='beauty', size=[pw, ph, 16], group='zero', plate_height=ph, keep_png=True),
                         dict(name='zero_base_again', camera=cam, light='A', state='wet', look='base', view='beauty', size=[pw, ph, 16], group='zero', plate_height=ph, keep_png=True),
                         dict(name='zero_after_layer_off', camera=cam, light='A', state='wet', look='kit:none', view='beauty', size=[pw, ph, 16], group='zero', plate_height=ph, keep_png=True)]
        spec['jobs'] += [dict(name='zero_growth_amount0', camera=cam, light='A', state='wet', look='solo:growth', view='beauty', size=[pw, ph, 16], group='zero', plate_height=ph, keep_png=True,
                              dials={'growth': {'amount': 0.0}}),
                         dict(name='zero_growth_weeds0_cushions0', camera=cam, light='A', state='wet', look='solo:growth', view='beauty', size=[pw, ph, 16], group='zero', plate_height=ph, keep_png=True,
                              dials={'growth': {'amount': 1.0, 'weeds_amount': 0.0, 'cushions_amount': 0.0}})]
    elif name == 'dials':
        base = dict(camera=cam, light='A', state='dry', view='beauty', size=[960, 720, 24], group='dials', plate_height=ph)
        jobs.append(dict(base, name='dials_base', look='base'))
        table = [('default', {}), ('weeds0', {'weeds_amount': 0.0}), ('weeds2', {'weeds_amount': 2.0}), ('cushions0', {'cushions_amount': 0.0}), ('cushions2', {'cushions_amount': 2.0}),
                 ('size05', {'piece_size': 0.5}), ('size2', {'piece_size': 2.0}), ('dist10', {'distance': 10.0}), ('wet', {}), ('gain05', {'colour_gain': 0.6}), ('gain15', {'colour_gain': 1.5}),
                 ('dead0', {'dead_grass_share': 0.0, 'flower_share': 0.0}), ('flowers', {'flower_share': 0.3, 'dead_grass_share': 0.3}), ('spacing', {'min_spacing': 0.3}), ('cover2', {'weed_cover': 0.02, 'cushion_cover': 0.02})]
        full = {'weeds_amount': 1.0, 'cushions_amount': 1.0, 'piece_size': 1.0, 'distance': 18.0, 'colour_gain': 1.0, 'dead_grass_share': 0.15, 'flower_share': 0.08, 'min_spacing': 0.15,
                'weed_cover': 0.01, 'cushion_cover': 0.008, 'amount': 1.0}
        for label, change in table:
            jobs.append(dict(base, name=f'dials_{label}', look='solo:growth', state='wet' if label == 'wet' else 'dry', dials={'growth': dict(full, **change)}))
    else:
        raise KeyError(name)
    return spec
