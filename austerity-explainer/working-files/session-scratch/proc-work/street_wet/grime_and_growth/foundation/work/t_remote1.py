import sys, json, os
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
from harness import remote
F = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/foundation'
jobs = [
 dict(name='today_main_dry', camera='main', light='A', state='dry', look='today', view='beauty', size=[270,480,8]),
 dict(name='base_main_wet', camera='main', light='A', state='wet', look='base', view='beauty', size=[270,480,8]),
 dict(name='demo_main_wet', camera='main', light='A', state='wet', look='kit:template_b', view='beauty', size=[270,480,8], dials={'template_b': {'demo': 1.0}}),
 dict(name='mask_shade', camera='main', light='A', state='dry', look='base', view='mask:shade', size=[270,480,1]),
 dict(name='mask_three', camera='main', light='A', state='dry', look='base', view='mask:wall_dist+lowness+crown', size=[270,480,1]),
 dict(name='class_main', camera='main', light='A', state='dry', look='base', view='class', size=[270,480,1]),
 dict(name='puddles_main', camera='main', light='A', state='wet', look='base', view='puddles', size=[270,480,1]),
 dict(name='dirt_main', camera='main', light='A', state='wet', look='base', view='dirt', size=[270,480,1]),
]
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[], jobs=jobs)
os.makedirs(F + '/work/jobs', exist_ok=True)
jf = F + '/work/jobs/t_remote1.json'
json.dump(spec, open(jf, 'w'), indent=1)
res = remote.run_batch('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/set_copy/street.blend', [jf], F + '/work/remote_out/t_remote1', F + '/work/out_t_remote1')
print(json.dumps(res))
