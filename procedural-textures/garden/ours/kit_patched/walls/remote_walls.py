# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# A thin helper the walls tests and sheets use to draw jobs on the rented machine through the kit's own remote runner (harness/remote.py, which uses only
# runpod/render_client_cached.py). Two small differences from calling it directly: (1) it keeps its OWN record of what was sent (the kit's shared record file is written by every
# helper working at the same time, so two helpers could overwrite each other's record), and (2) it writes the job file and names the folders for you.
#     from walls import remote_walls
#     remote_walls.run(SET_ID, SCENE_ID, jobs, out_dir, tag='r1')      # jobs: the runner's job dicts (see harness/runner.py); pictures come back into out_dir/tag
# Nothing here reads or writes ~/.runpod, nothing stops a machine.
import json
import os
import sys
import tempfile


HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from harness import remote  # noqa: E402

PRIVATE_STATE = os.path.join(os.environ.get('WALLS_WORK', tempfile.gettempdir()), 'remote_state_walls.json')       # set WALLS_WORK to the work folder


def scene_file(set_id, scene_id):
    settings = settings_module.load_set(set_id)
    return settings.scene(scene_id)['file']


def run(set_id, scene_id, jobs, out_dir, tag='r1', extra_roots=(), timeout=3000, extra_cameras=None):
    """Draws the jobs (one Blender run). Returns the result dict of the remote runner plus the local folder."""
    remote.STATE_FILE = PRIVATE_STATE
    local = os.path.join(out_dir, tag)
    os.makedirs(local, exist_ok=True)
    job_path = os.path.join(out_dir, '_jobs', f'jobs_{scene_id}_{tag}.json')
    os.makedirs(os.path.dirname(job_path), exist_ok=True)
    settings = settings_module.load_set(set_id)
    spec = dict(set=set_id, scene=scene_id, pack=True, feature_dirs=list(settings.get('feature_report_dirs', [])), jobs=jobs, extra_cameras=list(extra_cameras or []))
    json.dump(spec, open(job_path, 'w'), indent=1)
    remote_out = f'/workspace/wk_out/walls_{set_id}_{scene_id}_{tag}'
    result = remote.run_batch(scene_file(set_id, scene_id), [job_path], remote_out, local, runner_script=os.path.join(HERE, 'runner_walls.py'), extra_roots=list(extra_roots), timeout=timeout)
    result['local'] = local
    return result


def run_script(set_id, scene_id, script, script_args, out_dir, tag='s1', timeout=3000, extra_roots=()):
    """Runs one Blender script of the kit on the scene remotely (self-tests); '{out}' in an argument becomes the remote folder. The folder comes back into out_dir/tag."""
    remote.STATE_FILE = PRIVATE_STATE
    local = os.path.join(out_dir, tag)
    remote_out = f'/workspace/wk_out/walls_{set_id}_{scene_id}_{tag}'
    result = remote.run_script(scene_file(set_id, scene_id), script, script_args, remote_out, local, extra_roots=list(extra_roots), timeout=timeout)
    result['local'] = local
    return result
