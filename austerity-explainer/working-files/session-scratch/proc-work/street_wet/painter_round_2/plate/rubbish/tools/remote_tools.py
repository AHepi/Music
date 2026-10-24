# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Small helpers for using the rented machine (the one with the RTX 4090 card) from a script on this machine, through the render client in runpod/render_client_cached.py (it never touches ~/.runpod):
#   upload(path)                        copies a file or folder to the same path on the rented machine
#   run_blender(file, script, args, cwd) starts one Blender run there and waits for it; returns its log tail
#   fetch(folder)                       brings a finished folder back as ONE tar file (fast), into the same path here
# Use: import remote_tools as rt; rt.upload(tools_folder); rt.run_blender(street_file, script, [out_folder]); rt.fetch(out_folder)
import json
import os
import subprocess
import time

CLIENT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_cached.py'
HERE = os.path.dirname(os.path.abspath(__file__))
RUBBISH = os.path.abspath(os.path.join(HERE, '..'))
STREET_WET = os.path.abspath(os.path.join(RUBBISH, '..', '..'))
STREET_FILE = os.path.join(STREET_WET, 'set_copy', 'street.blend')
LOCKOUT_FILE = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend'


def client(*args, timeout=900):
    result = subprocess.run(['python3', '-I', CLIENT, *args], capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def upload(path):
    return client('upload', path)


def upload_tools():
    for sub in ('tools', 'maps'):
        client('upload', os.path.join(RUBBISH, sub))
    client('upload', os.path.join(RUBBISH, 'work', 'objects_street.txt'))


def wait(job_id, poll=3):
    while True:
        state = json.loads(client('job', job_id))
        if state['state'] != 'running':
            return state
        time.sleep(poll)


def run_blender(blend_file, script, args=(), cwd=None):
    command = f"/workspace/blender/blender -b --disable-autoexec {blend_file} --python {script} -- " + ' '.join(str(a) for a in args)
    job = client('run', command, '--cwd', cwd or RUBBISH).strip().split()[-1]
    state = wait(job)
    return state


def fetch(folder):
    stamp = f'{os.path.basename(folder)}_{int(time.time())}'
    remote_tar = f'/workspace/uploads/{stamp}.tar'
    job = client('run', f'tar -cf {remote_tar} -C {folder} .', '--cwd', '/tmp').strip().split()[-1]
    wait(job, poll=1)
    local_tar = f'/tmp/{stamp}.tar'
    client('download', remote_tar, '--local', local_tar)
    os.makedirs(folder, exist_ok=True)
    subprocess.run(['tar', '-xf', local_tar, '-C', folder], check=True)
    os.remove(local_tar)
    client('run', f'rm -f {remote_tar}', '--cwd', '/tmp')
