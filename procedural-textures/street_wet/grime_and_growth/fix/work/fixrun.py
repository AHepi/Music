# Fix round helper: writes a job list for one scene and draws it on the rented machine through the kit's own remote runner (which uses only render_client_cached.py).
#   from fixrun import job, run
# Dials given in a job's `dials` persist in the Blender run until another job sets them again, so every job of a variant names ALL the dials the run touches (see full_dials).
import json, os, sys, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.dirname(HERE)
SET = 'pit_village_street'


def scene_file(scene_id):
    st = settings_module.load_set(SET)
    return next(s for s in st.scenes if s['id'] == scene_id)


def preset_value(layer, dial, look='sooty_1926'):
    p = json.load(open(os.path.join(KIT, 'presets', look + '.json')))
    return p['layers'].get(layer, {}).get(dial)


def full_dials(touched, overrides, look='sooty_1926'):
    """touched: list of (layer, dial) any variant of the run changes; overrides: {layer: {dial: value}} of this variant. Returns {layer: {dial: value}} with the preset value for every touched dial the variant leaves alone."""
    out = {}
    for layer, dial in touched:
        v = overrides.get(layer, {}).get(dial)
        if v is None:
            v = preset_value(layer, dial, look)
        if v is None:
            raise KeyError(f'no preset value for {layer}.{dial}: give it in the variant')
        out.setdefault(layer, {})[dial] = v
    return out


def job(name, camera, light='A', state='wet', look='kit_all', size=(1536, 2730, 64), view='beauty', dials=None, plate_height=2730, keep_png=False, **extra):
    j = dict(name=name, camera=camera, light=light, state=state, look=look, view=view, size=list(size), group=extra.pop('group', 'fix'), plate_height=plate_height, keep_png=keep_png)
    if dials:
        j['dials'] = dials
    j.update(extra)
    return j


def run(scene_id, jobs, tag, extra_cameras=None, out_root=None, today=True):
    out_root = out_root or os.path.join(FIX, 'rounds')
    sc = scene_file(scene_id)
    jl = list(jobs)
    if today:
        jl.insert(0, dict(name=f'today_{scene_id}', camera=sc.get('default_camera'), light='A', state='wet', look='today', view='beauty', size=[270, 480, 4], group='today', scene=scene_id))
    spec = dict(set=SET, scene=scene_id, pack=True, feature_dirs=[], jobs=jl)
    if extra_cameras:
        spec['extra_cameras'] = extra_cameras
    jd = os.path.join(out_root, tag, '_jobs')
    os.makedirs(jd, exist_ok=True)
    path = os.path.join(jd, f'jobs_{scene_id}.json')
    json.dump(spec, open(path, 'w'), indent=1)
    local_out = os.path.join(out_root, tag, scene_id)
    remote_out = f'/workspace/wk_out/fix_{tag.replace("/", "_")}_{scene_id}'
    t = time.time()
    r = remote.run_batch(sc['file'], [path], remote_out, local_out, runner_script=os.path.join(KIT, 'growth', 'runner_growth.py'))
    r['wall_seconds'] = round(time.time() - t, 1)
    json.dump(r, open(os.path.join(out_root, tag, f'run_{scene_id}.json'), 'w'))
    print(scene_id, tag, r, flush=True)
    return r
