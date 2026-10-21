# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Makes the `rubbish_heap` picture of a scene on the rented machine: the earlier rubbish layer's mask seen straight down over the ground bounds (red = litter), drawn by the runner's
# view plan:rubbish_heap with the pinned earlier layers; then rebuilds the scene's pack with it so the habitat fields keep moss and weeds off the heaps.
#     python3 -I harness/make_heap.py SET_ID SCENE_ID RAW_DIR
# Only for sets that have the rubbish layer (legacy.order names it); other sets keep rubbish_heap at 0.
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from harness import remote  # noqa: E402


def main(set_id, scene_id, raw_dir, work_dir):
    settings = settings_module.load_set(set_id)
    legacy = settings.legacy() or {}
    if 'rubbish' not in legacy.get('order', []):
        print('this set has no rubbish layer: rubbish_heap stays 0')
        return
    ground = settings.geometry['ground']
    w = int(round((ground['bounds']['x'][1] - ground['bounds']['x'][0]) / ground['dot_m']))
    h = int(round((ground['bounds']['y'][1] - ground['bounds']['y'][0]) / ground['dot_m']))
    jobs = [dict(name='rubbish_heap', light='A', state='dry', look='base', view='plan:rubbish_heap', size=[w, h, 1])]
    os.makedirs(work_dir, exist_ok=True)
    spec = dict(set=set_id, scene=scene_id, pack=True, feature_dirs=[], jobs=jobs)
    jobs_file = os.path.join(work_dir, f'jobs_heap_{scene_id}.json')
    json.dump(spec, open(jobs_file, 'w'), indent=1)
    scene = settings.scene(scene_id)
    out_local = os.path.join(work_dir, f'out_heap_{scene_id}')
    res = remote.run_batch(scene['file'], [jobs_file], os.path.join(work_dir, 'remote_heap_' + scene_id), out_local)
    print(res)
    png = os.path.join(out_local, 'rubbish_heap.png')
    shutil.copy(png, os.path.join(raw_dir, 'rubbish_heap.png'))
    subprocess.run(['python3', '-I', os.path.join(KIT_ROOT, 'masks', 'make_pack.py'), set_id, scene_id, raw_dir, '--rubbish', os.path.join(raw_dir, 'rubbish_heap.png')], check=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else os.path.join(raw_dir_default := os.getcwd(), 'heap_work'))
