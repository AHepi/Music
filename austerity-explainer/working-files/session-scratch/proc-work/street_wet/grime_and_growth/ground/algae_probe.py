import os, sys, json
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as S
from harness import remote
WG = os.path.dirname(os.path.abspath(__file__))
cams = [dict(name='alg', location=[-2.8, 4.6, 1.3], look_at=[-4.08, 6.3, 0.05], fov_v=40.0)]
def job(name, look, view='beauty', dials=None):
    j = dict(name=name, camera='alg', light='A', state='wet', look=look, view=view, size=[640, 480, 1], group='probe')
    if dials: j['dials'] = dials
    return j
jobs = [job('base', 'base'), job('moss', 'solo:groundmoss'),
        job('alg3', 'solo:groundmoss', 'layer:groundmoss', {'groundmoss': {'show_part': 3}}),
        job('alg3_strong', 'solo:groundmoss', 'layer:groundmoss', {'groundmoss': {'show_part': 3, 'algae_fan': 1.0, 'outlet_reach': 1.0, 'algae_radius': 1.0}}),
        job('wall_dist', 'solo:groundmoss', 'mask:wall_dist'), job('vfoot', 'solo:groundmoss', 'mask:vertical_foot'), job('algsite', 'solo:groundmoss', 'mask:algae_site'),
        job('footfall', 'solo:groundmoss', 'mask:footfall'), job('keepclear', 'solo:groundmoss', 'mask:keepclear'), job('crown', 'solo:groundmoss', 'mask:crown'), job('exist', 'solo:groundmoss', 'mask:existing_growth')]
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[WG], jobs=jobs, extra_cameras=cams)
out = os.path.join(WG, 'runs', 'algae_probe'); os.makedirs(out, exist_ok=True)
jf = os.path.join(out, 'jobs.json'); json.dump(spec, open(jf, 'w'))
st = S.load_set('pit_village_street')
print(remote.run_batch(st.scene('street')['file'], [jf], '/workspace/wk_out/ground_algae_probe', os.path.join(out, 'out'), runner_script=os.path.join(KIT, 'ground', 'runner_ground.py')))
