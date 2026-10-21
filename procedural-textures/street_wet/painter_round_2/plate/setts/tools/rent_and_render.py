# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Runs ONE job file on the rented machine (the one with the RTX 4090 graphics card) from this machine, in four steps, and tells you how long each took:
#   1. uploads the tool folders that may have changed (setts/tools, study/tools, setts/maps) and the job file,
#   2. starts run_jobs_rented.sh there (one Blender run: draws every picture of the job file, measures the joints, makes JPEGs),
#   3. waits for it (asks every 10 seconds),
#   4. downloads the finished folder (pictures as JPEG, measurements.json, the log, the measure table) into the same folder path on this machine.
# It uses the render client of the rented machine (runpod/render_client_cached.py) and never touches ~/.runpod.
# Use:  python3 -I rent_and_render.py JOB_FILE [--no-upload] [--no-download]       (JOB_FILE is the jobs_street.json or jobs_lockout.json made by make_job_lists.py)
# Run it in the background for long jobs (the shell tool stops a foreground command after 10 minutes) and read <folder>/rent_log.txt.
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SETTS = os.path.abspath(os.path.join(HERE, '..'))
STUDY_TOOLS = os.path.abspath(os.path.join(SETTS, '..', 'study', 'tools'))
CLIENT = 'scratchpad/runpod/render_client_cached.py'


def client(*args, timeout=900):
    result = subprocess.run(['python3', '-I', CLIENT, *args], capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def main():
    job_file = os.path.abspath(sys.argv[1])
    folder = os.path.dirname(job_file)
    log = open(os.path.join(folder, 'rent_log.txt'), 'a')

    def say(text):
        line = time.strftime('%H:%M:%S ') + text
        print(line, flush=True)
        log.write(line + '\n')
        log.flush()
    started = time.time()
    if '--no-upload' not in sys.argv:
        for path in (HERE, STUDY_TOOLS, os.path.join(SETTS, 'maps')):
            client('upload', path)
        client('upload', job_file)
        say(f'uploaded tools and job file ({time.time() - started:.0f} s)')
    kind = os.path.basename(job_file)[5:-5]
    job = client('run', f'bash {HERE}/run_jobs_rented.sh {job_file}', '--cwd', folder).strip().split()[-1]
    say('remote job ' + job)
    t0 = time.time()
    while True:
        state = json.loads(client('job', job))
        if state['state'] != 'running':
            break
        time.sleep(10)
    say(f"remote job {state['state']} return code {state.get('return_code')} after {time.time() - t0:.0f} s; tail: {state.get('log_tail', '')[-300:]!r}")
    if '--no-download' not in sys.argv:
        t1 = time.time()
        # one tar file instead of 100 small downloads (the small ones took 1 to 2 seconds each)
        stamp = f'{os.path.basename(folder)}_{int(time.time())}'
        remote_tar = f'/workspace/uploads/{stamp}.tar'
        tar_job = client('run', f'tar -cf {remote_tar} -C {folder} .', '--cwd', '/tmp').strip().split()[-1]
        while json.loads(client('job', tar_job))['state'] == 'running':
            time.sleep(1)
        local_tar = f'/tmp/{stamp}.tar'
        client('download', remote_tar, '--local', local_tar)
        subprocess.run(['tar', '-xf', local_tar, '-C', folder], check=True)
        os.remove(local_tar)
        client('run', f'rm -f {remote_tar}', '--cwd', '/tmp')
        say(f'downloaded the folder as one tar file ({time.time() - t1:.0f} s)')
    say(f'ALL DONE {kind} after {time.time() - started:.0f} s')


main()
