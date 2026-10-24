# What this file does: sends the three village scenes, the 4K drawing script and each village's shot
# settings to the rented machines' store, starts the drawing jobs (three or so views per job, so no job
# passes the endpoint's 55-minute limit; up to three cards work at once), waits for them, and downloads
# every finished 4K picture into renders/. It logs every step to run_4k_log.txt and can be run again.
import json, os, subprocess, sys, time

K = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(os.path.dirname(K), 'runpod', 'render_client_serverless.py')
STORE = '/runpod-volume/village-4k'
BLENDER = '/runpod-volume/blender/blender'
SCENES = {'sonnet': K + '/sonnet/village_with_cameras.blend', 'opus1': K + '/opus/village_pass1_with_cameras.blend',
          'opus2': K + '/opus/village_pass2_with_cameras.blend'}
GROUPS = [['01_village_from_above', '02_road_at_eye_level', '03_stable_close'],
          ['04_cottage_close', '05_road_surface_closeup', '06_second_cottage'],
          ['07_props_close', '08_stable_stalls', '09_puddle_ground_level'],
          ['10_road_into_forest', '11_village_low_drone']]


def log(message):
    line = time.strftime('%H:%M:%S ') + message
    print(line, flush=True)
    open(os.path.join(K, 'run_4k_log.txt'), 'a').write(line + '\n')


def client(*args, check=True):
    result = subprocess.run(['python3', '-I', CLIENT, *args], capture_output=True, text=True, cwd=os.path.dirname(CLIENT))
    if check and result.returncode != 0:
        raise RuntimeError(' '.join(args[:2]) + ': ' + result.stderr[-400:])
    return result.stdout


for name, path in SCENES.items():
    client('upload', path, '--remote', f'{STORE}/scenes/{name}.blend')
    client('upload', os.path.join(K, f'settings_{name}.json'), '--remote', f'{STORE}/settings_{name}.json')
    log(f'uploaded {name} scene and settings')
client('upload', os.path.join(K, 'render_4k.py'), '--remote', f'{STORE}/render_4k.py')

jobs = {}
for name in SCENES:
    for number, group in enumerate(GROUPS, 1):
        command = (f'{BLENDER} -b {STORE}/scenes/{name}.blend --python {STORE}/render_4k.py -- {STORE}/settings_{name}.json '
                   f'{STORE}/renders {name}_ ' + ' '.join(group) + " 2>&1 | grep -E 'VIEW_DONE|RENDER_4K_DONE|Error|rror:|Killed|out of memory' | tail -20")
        job_id = client('run', command, '--timeout', '3300').strip().splitlines()[-1]
        jobs[job_id] = (name, number, group)
        log(f'submitted {name} group {number}: {", ".join(group)}')
json.dump(jobs, open(os.path.join(K, 'jobs.json'), 'w'), indent=1)

os.makedirs(os.path.join(K, 'renders'), exist_ok=True)
pending = dict(jobs)
while pending:
    time.sleep(45)
    for job_id, (name, number, group) in list(pending.items()):
        try:
            state = json.loads(client('job', job_id, check=False) or '{}')
        except ValueError:
            continue
        if state.get('state') not in ('finished', 'failed', 'cancelled', 'timed_out', 'error'):
            continue
        del pending[job_id]
        log(f"{name} group {number} {state.get('state')} in {state.get('seconds')} s: {state.get('log_tail', '')[-300:]!r}")
        for picture in group:
            remote = f'{STORE}/renders/{name}_{picture}.jpg'
            local = os.path.join(K, 'renders', f'{name}_{picture}.jpg')
            out = subprocess.run(['python3', '-I', CLIENT, 'download', remote, '--local', local], capture_output=True, text=True,
                                 cwd=os.path.dirname(CLIENT))
            log(f'  download {name}_{picture}: ' + ('ok' if os.path.exists(local) else 'MISSING ' + out.stderr[-200:]))
log('ALL JOBS DONE')
