# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# DRAWS THE GROWTH LAYER'S TEST PICTURES on the rented machine and brings them back (plain Python here; the drawing is runner_growth.py there).
#     python3 -I growth/run_growth.py SET_ID SCENE_ID OUT_FOLDER --jobs NAME [--look solo:growth]
# Job sets (growth/jobs_growth.py): pilot, close, plates, times, zero, wet, plan ...  One Blender run per call, states start with 'today', pictures land in OUT_FOLDER.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from harness import remote  # noqa: E402
from growth import jobs_growth  # noqa: E402


def run(set_id, scene_id, out_folder, job_set, tag=None, extra=None, look=None):
    settings = settings_module.load_set(set_id)
    scene = next(s for s in settings.scenes if s['id'] == scene_id)
    spec = jobs_growth.make(settings, scene_id, job_set, **(extra or {}))
    if look:
        for job in spec['jobs']:
            if job.get('look') == 'solo:growth':
                job['look'] = look
    os.makedirs(out_folder, exist_ok=True)
    jobs_path = os.path.join(out_folder, f'jobs_{job_set}.json')
    json.dump(spec, open(jobs_path, 'w'), indent=1)
    remote_out = f'/workspace/wk_out/growth_{set_id}_{scene_id}_{tag or job_set}'
    t = time.time()
    result = remote.run_batch(scene['file'], [jobs_path], remote_out, out_folder, runner_script=os.path.join(HERE, 'runner_growth.py'))
    result['wall_seconds'] = round(time.time() - t, 1)
    json.dump(result, open(os.path.join(out_folder, f'run_time_{job_set}.json'), 'w'), indent=1)
    return result


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {}
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith('--'):
            opts[a] = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--') else True
    for v in opts.values():
        if isinstance(v, str) and v in args:
            args.remove(v)
    print(run(args[0], args[1], args[2], opts.get('--jobs', 'pilot'), tag=opts.get('--tag')))
