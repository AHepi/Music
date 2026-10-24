# Integrator step 4: the full-size plates (1536 x 2730, EEVEE, shadow rays 4 / steps 16, 64 samples, wet 0.85 / puddles 0.5, lighting B for the lockout, A for the street),
# before ('base': earlier layers only) and after ('kit_all': everything), wet and dry, on the rented machine. PNGs and JPGs come back to integrated/plates/<scene>/.
#   python3 -I run_final_plates.py [TAG]
import json, os, sys, time
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote
W = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1] if len(sys.argv) > 1 else 'plates'
settings = settings_module.load_set('pit_village_street')
scenes = {s['id']: s for s in settings.scenes}
P = [1536, 2730, 64]
def job(name, camera, light, state, look, **extra):
    return dict(name=name, camera=camera, light=light, state=state, look=look, view='beauty', size=P, group='plate', plate_height=2730, keep_png=True, **extra)
plan = {
    'street': [job('final_main_A_wet_base', 'main', 'A', 'wet', 'base'), job('final_main_A_dry_base', 'main', 'A', 'dry', 'base'),
               job('final_main_A_wet_kit', 'main', 'A', 'wet', 'kit_all'), job('final_main_A_dry_kit', 'main', 'A', 'dry', 'kit_all')],
    'lockout': [job('final_lockout_B_wet_base', 'lockout', 'B', 'wet', 'base'), job('final_lockout_B_dry_base', 'lockout', 'B', 'dry', 'base'),
                job('final_lockout_B_wet_kit', 'lockout', 'B', 'wet', 'kit_all'), job('final_lockout_B_dry_kit', 'lockout', 'B', 'dry', 'kit_all'),
                job('final_lockout_B_wet_kit_behind', 'lockout', 'B', 'wet', 'kit_all', hide_roles=['prop', 'fire', 'sign'])],
}
for scene_id, jobs in plan.items():
    jobs.insert(0, dict(name=f'today_{scene_id}', camera=scenes[scene_id]['default_camera'], light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene=scene_id))
    spec = dict(set='pit_village_street', scene=scene_id, pack=True, feature_dirs=[], jobs=jobs)
    jd = os.path.join(W, tag, '_jobs'); os.makedirs(jd, exist_ok=True)
    path = os.path.join(jd, f'jobs_{scene_id}.json'); json.dump(spec, open(path, 'w'), indent=1)
    t = time.time()
    r = remote.run_batch(scenes[scene_id]['file'], [path], f'/workspace/wk_out/int_{tag}_{scene_id}', os.path.join(W, tag, scene_id), runner_script=os.path.join(KIT, 'growth', 'runner_growth.py'))
    r['wall_seconds'] = round(time.time() - t, 1); print(scene_id, r, flush=True)
