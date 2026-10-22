# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Draws the two plan pictures that the finished PACK of a scene cannot make for itself, on the rented machine, and stamps them onto the pack (masks/stamp_pack.py):
#   plan:puddles   the earlier water layer's puddle mask seen straight down over the ground bounds (2 cm dots), in the wet state the plates use  -> above_water (no plant stands in a puddle)
#   plan:litter    the 3D litter pieces of the objects named in growth.avoid_pieces_of (1 cm dots), white on black                              -> litter_dist (the growth layer's
#                  clearance from litter as a look-up instead of a search over every piece)
#     python3 -I harness/make_plan_pictures.py SET_ID SCENE_ID WORK_DIR [--state wet] [--only puddles|litter]
# Only for sets that have an earlier water layer / litter layer (legacy.order names 'wetness' / 'rubbish'); a set without them is left as it is. Draw them again whenever the puddle
# amount of the plates, the litter amount or its seed change: the pack holds what was drawn.
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from harness import remote  # noqa: E402


def main(set_id, scene_id, work_dir, state='wet', only=None, margin_m=0.03, litter_max_m=0.25):
    settings = settings_module.load_set(set_id)
    legacy = settings.legacy() or {}
    order = legacy.get('order', [])
    ground = settings.geometry['ground']
    bx, by = ground['bounds']['x'], ground['bounds']['y']
    jobs, flags = [], []
    if 'wetness' in order and only in (None, 'puddles'):
        w, h = int(round((bx[1] - bx[0]) / 0.02)), int(round((by[1] - by[0]) / 0.02))
        jobs.append(dict(name='plan_puddles', light='A', state=state, look='base', view='plan:puddles', size=[w, h, 1]))
        flags.append('puddles')
    avoid = ((settings.get('growth') or {}).get('avoid_pieces_of') or {}).get('objects', [])
    if 'rubbish' in order and avoid and only in (None, 'litter'):
        w, h = int(round((bx[1] - bx[0]) / 0.01)), int(round((by[1] - by[0]) / 0.01))
        jobs.append(dict(name='plan_litter', light='A', state='dry', look='base', view='plan:litter', size=[w, h, 1]))
        flags.append('litter')
    if not jobs:
        print('nothing to draw: this set has no earlier water layer or litter layer')
        return
    os.makedirs(work_dir, exist_ok=True)
    spec = dict(set=set_id, scene=scene_id, pack=True, feature_dirs=[], jobs=jobs)
    jobs_file = os.path.join(work_dir, f'jobs_plan_{scene_id}.json')
    json.dump(spec, open(jobs_file, 'w'), indent=1)
    scene = settings.scene(scene_id)
    out_local = os.path.join(work_dir, f'out_plan_{scene_id}')
    res = remote.run_batch(scene['file'], [jobs_file], f'/workspace/wk_out/plan_{set_id}_{scene_id}', out_local)
    print(res)
    cmd = ['python3', '-I', os.path.join(KIT_ROOT, 'masks', 'stamp_pack.py'), set_id, scene_id]
    if 'puddles' in flags:
        cmd += ['--puddles', os.path.join(out_local, 'plan_puddles.png'), '--puddle_margin_m', str(margin_m)]
    if 'litter' in flags:
        cmd += ['--litter', os.path.join(out_local, 'plan_litter.png'), '--litter_points', os.path.join(out_local, 'plan_litter_points.json'), '--litter_max_m', str(litter_max_m)]
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    argv = sys.argv[1:]
    opts = {}
    pos = []
    i = 0
    while i < len(argv):
        if argv[i].startswith('--'):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            pos.append(argv[i])
            i += 1
    main(pos[0], pos[1], pos[2], state=opts.get('--state', 'wet'), only=opts.get('--only'))
