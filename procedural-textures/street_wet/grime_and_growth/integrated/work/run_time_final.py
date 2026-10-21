# Integrator: final drawing times of the plate (1536x2730, 48 samples), best of three, base vs everything on, both scene files, plus the first picture after putting the kit on.
import json, os, sys, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote
W = os.path.dirname(os.path.abspath(__file__)); tag = sys.argv[1]
settings = settings_module.load_set('pit_village_street')
for scene_id, cam, light in (('street', 'main', 'A'), ('lockout', 'lockout', 'B')):
    scene = next(s for s in settings.scenes if s['id'] == scene_id)
    jobs = [dict(name=f'today_{scene_id}', camera=cam, light=light, state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene=scene_id)]
    for look in ('base', 'kit_all'):
        for r in range(3):
            jobs.append(dict(name=f'time_{look}_{r+1}', camera=cam, light=light, state='wet', look=look, view='beauty', size=[1536, 2730, 48], group='time', plate_height=2730))
    spec = dict(set='pit_village_street', scene=scene_id, pack=True, feature_dirs=[], jobs=jobs)
    jd = os.path.join(W, tag, '_jobs'); os.makedirs(jd, exist_ok=True); path = os.path.join(jd, f'jobs_{scene_id}.json'); json.dump(spec, open(path, 'w'), indent=1)
    print(scene_id, remote.run_batch(scene['file'], [path], f'/workspace/wk_out/int_tfinal_{tag}_{scene_id}', os.path.join(W, tag, scene_id), runner_script=os.path.join(KIT, 'growth', 'runner_growth.py')), flush=True)
