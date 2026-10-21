import json, os, sys, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote
W = os.path.dirname(os.path.abspath(__file__)); tag = sys.argv[1]
settings = settings_module.load_set('pit_village_street'); scene = next(s for s in settings.scenes if s['id'] == 'street')
jobs = [dict(name='today_street', camera='main', light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene='street')]
for look in ('base', 'solo:growth'):
    for r in range(3):
        jobs.append(dict(name=f'time_{look.replace(":", "_")}_{r+1}', camera='main', light='A', state='wet', look=look, view='beauty', size=[1536, 2730, 48], group='time', plate_height=2730, pieces_json=(look != 'base' and r == 0)))
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[], jobs=jobs)
jd = os.path.join(W, tag, '_jobs'); os.makedirs(jd, exist_ok=True); path = os.path.join(jd, 'jobs_mini.json'); json.dump(spec, open(path, 'w'), indent=1)
r = remote.run_batch(scene['file'], [path], f'/workspace/wk_out/int_mini_{tag}', os.path.join(W, tag, 'street'), runner_script=os.path.join(KIT, 'growth', 'runner_growth.py'))
print(r)
