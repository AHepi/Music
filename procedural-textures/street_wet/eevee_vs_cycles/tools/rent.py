# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Runs ONE job file of pair_runner.py on the rented machine and brings the finished folder back. It only uses the cached render client of the rented machine (never touches ~/.runpod).
# Steps: 1. sends this job's tools folder and the job file; 2. starts one Blender run there (street copy or the film's lockout shot file, both read-only); 3. waits, asking every 5 seconds,
# printing the Blender log as it grows; 4. brings the output folder back as ONE tar file into the same folder path here.
# Use: python3 -I rent.py JOB_FILE OUT_FOLDER [--no-upload] [--no-download]
# The folder of JOB_FILE decides nothing; OUT_FOLDER is created on the machine and here. The Blender log is OUT_FOLDER/log.txt.
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = 'scratchpad/runpod/render_client_cached.py'
STREET = 'proc-work/street_wet/set_copy/street.blend'
LOCKOUT = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend'
BLENDER = '/workspace/blender/blender'


def client(*args, timeout=900):
    result = subprocess.run(['python3', '-I', CLIENT, *args], capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def wait(job_id, poll=5, echo_log=None):
    while True:
        state = json.loads(client('job', job_id))
        if state['state'] != 'running':
            return state
        time.sleep(poll)


def main():
    job_file = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    kind = json.load(open(job_file))['kind']
    blend = STREET if kind == 'street' else LOCKOUT
    started = time.time()
    if '--no-upload' not in sys.argv:
        client('upload', HERE)
    client('upload', job_file)
    print(f'uploaded ({time.time() - started:.0f} s)', flush=True)
    gpu = 'nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader'
    command = f'mkdir -p {out} && ({gpu}; date +%s) >> {out}/gpu.txt; {BLENDER} -b --disable-autoexec {blend} --python {HERE}/pair_runner.py -- {job_file} {out} > {out}/log.txt 2>&1; echo BLENDER EXIT $? >> {out}/log.txt; ({gpu}; date +%s) >> {out}/gpu.txt'
    job = client('run', command, '--cwd', '/tmp').strip().split()[-1]
    print('remote job', job, flush=True)
    t0 = time.time()
    state = wait(job)
    print(f"remote job {state['state']} return code {state.get('return_code')} after {time.time() - t0:.0f} s", flush=True)
    if '--no-download' not in sys.argv:
        t1 = time.time()
        stamp = f'{os.path.basename(out)}_{int(time.time())}'
        remote_tar = f'/workspace/uploads/{stamp}.tar'
        tar_job = client('run', f'tar -cf {remote_tar} -C {out} .', '--cwd', '/tmp').strip().split()[-1]
        wait(tar_job, poll=1)
        local_tar = f'/tmp/{stamp}.tar'
        client('download', remote_tar, '--local', local_tar)
        os.makedirs(out, exist_ok=True)
        subprocess.run(['tar', '-xf', local_tar, '-C', out], check=True)
        os.remove(local_tar)
        client('run', f'rm -f {remote_tar}', '--cwd', '/tmp')
        print(f'downloaded ({time.time() - t1:.0f} s)', flush=True)
    print(f'ALL DONE after {time.time() - started:.0f} s', flush=True)


main()
