import json, os, sys
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote
W = os.path.dirname(os.path.abspath(__file__)); tag = sys.argv[1]
settings = settings_module.load_set('pit_village_street'); scene = next(s for s in settings.scenes if s['id'] == 'street')
jobs = [dict(name='today_street', camera='main', light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene='street')]
for look in ('base', 'kit_all'):
    for label, cam, light, size in (('main', 'main', 'C', [540, 960, 16]), ('main', 'main', 'E', [540, 960, 16]), ('main', 'main', 'A', [540, 960, 16]), ('close', 'close_road', 'A', [640, 480, 24])):
        for state in ('dry', 'wet', 'heavy'):
            if state == 'heavy' and light != 'A':
                continue
            jobs.append(dict(name=f'p2_{look}_{label}_{light}_{state}', camera=cam, light=light, state=state, look=look, view='beauty', size=size, group='p2', keep_png=True))
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[], jobs=jobs)
jd = os.path.join(W, tag, '_jobs'); os.makedirs(jd, exist_ok=True); path = os.path.join(jd, 'jobs_p2.json'); json.dump(spec, open(path, 'w'), indent=1)
print(remote.run_batch(scene['file'], [path], f'/workspace/wk_out/int_p2_{tag}', os.path.join(W, tag, 'street'), runner_script=os.path.join(KIT, 'growth', 'runner_growth.py')))
