# The fix round's real round: the kit with the final look (no per-job dial overrides), drawn in batches so that no download is big.
#   python3 -I final_round.py BATCH SCENE [TAG]
#   BATCH  t22    the 22 lighting pictures of the scene (PNG kept, for the joint and wet-look measures) and the close views (JPG)
#          plates the full-size final plates 1536 x 2730, 64 samples, kit_all, wet and dry (lockout: also the 'behind' plate with props hidden), PNG kept; the wet ones also write the plant list
#          time   three draws of the main plate with the kit and three with the earlier layers only (drawing time)
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixrun import job, run, KIT, SET, scene_file
from apply import settings as settings_module
from harness import testset

batch, scene_id = sys.argv[1], sys.argv[2]
tag = sys.argv[3] if len(sys.argv) > 3 else 'final'
settings = settings_module.load_set(SET)
ts = settings.get('test_set') or {}
jobs = []
if batch == 't22':
    jobs += testset._lighting22(ts, scene_id, 'kit_all')
    jobs += testset._close_views(ts, scene_id, 'kit_all')
elif batch == 'plates':
    if scene_id == 'street':
        cam, light = 'main', 'A'
        plan = [('final_main_A_wet_kit', 'wet', {}), ('final_main_A_dry_kit', 'dry', {})]
    else:
        cam, light = 'lockout', 'B'
        plan = [('final_lockout_B_wet_kit', 'wet', {}), ('final_lockout_B_dry_kit', 'dry', {}), ('final_lockout_B_wet_kit_behind', 'wet', dict(hide_roles=['prop', 'fire', 'sign']))]
    for name, state, extra in plan:
        jobs.append(job(name, cam, light, state, size=(1536, 2730, 64), plate_height=2730, keep_png=True, group='plate', pieces_json=(state == 'wet' and 'behind' not in name), **extra))
elif batch == 'time':
    cam, light = ('main', 'A') if scene_id == 'street' else ('lockout', 'B')
    for i in (1, 2, 3):
        jobs.append(job(f'time_base_{i}', cam, light, 'wet', look='base', size=(1536, 2730, 48), plate_height=2730, group='plate'))
    for i in (1, 2, 3):
        jobs.append(job(f'time_kit_{i}', cam, light, 'wet', look='kit_all', size=(1536, 2730, 48), plate_height=2730, group='plate'))
run(scene_id, jobs, f'{tag}/{batch}')
