# Integrator: drawing time per layer (plate 1536x2730x48, best of three) and the road's wet/dry per layer (small pictures), street scene, growth runner.
import json, os, sys, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote
W = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1]
settings = settings_module.load_set('pit_village_street')
scene = next(s for s in settings.scenes if s['id'] == 'street')
layers = ['soot', 'runoff', 'foot', 'steps', 'wallcracks', 'wallgrowth', 'dirt', 'groundcracks', 'groundmoss', 'iron', 'growth']
looks = ['base'] + ['solo:' + k for k in layers] + ['kit_all']
jobs = [dict(name='today_street', camera='main', light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene='street')]
for look in looks:
    tagl = look.replace(':', '_')
    for r in range(3):
        jobs.append(dict(name=f'time_{tagl}_{r + 1}', camera='main', light='A', state='wet', look=look, view='beauty', size=[1536, 2730, 48], group='time', plate_height=2730))
if '--no-p2' not in sys.argv:
    for look in ['base', 'solo:dirt', 'solo:groundcracks', 'solo:groundmoss', 'solo:growth', 'solo:iron']:
        tagl = look.replace(':', '_')
        for light, state, cam, size in (('C', 'dry', 'main', [540, 960, 16]), ('C', 'wet', 'main', [540, 960, 16]), ('E', 'dry', 'main', [540, 960, 16]), ('E', 'wet', 'main', [540, 960, 16]),
                                        ('A', 'dry', 'close_road', [640, 480, 24]), ('A', 'wet', 'close_road', [640, 480, 24])):
            jobs.append(dict(name=f'p2_{tagl}_{cam}_{light}_{state}', camera=cam, light=light, state=state, look=look, view='beauty', size=size, group='p2', keep_png=True))
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[], jobs=jobs)
job_dir = os.path.join(W, tag, '_jobs'); os.makedirs(job_dir, exist_ok=True)
path = os.path.join(job_dir, 'jobs_time_p2.json'); json.dump(spec, open(path, 'w'), indent=1)
out = os.path.join(W, tag, 'street')
t = time.time()
r = remote.run_batch(scene['file'], [path], f'/workspace/wk_out/int_time_{tag}', out, runner_script=os.path.join(KIT, 'growth', 'runner_growth.py'))
r['wall_seconds'] = round(time.time() - t, 1)
print(r)
