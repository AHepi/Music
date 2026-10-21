# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Runs ONE job file (see write_jobs.py) on the rented machine (the one with the RTX 4090 graphics card) from this machine, in four steps, and tells you how long each took:
#   1. uploads the tool folders that may have changed (rubbish/tools, rubbish/maps, study/tools, setts/tools and setts/maps) and the job file,
#   2. starts run_rubbish_jobs.sh there (one Blender run: draws every picture, measures, makes JPEGs),
#   3. waits for it (asks every 5 seconds),
#   4. downloads the finished folder (as ONE tar file: much faster than picture by picture) into the same folder path here.
# It uses the render client of the rented machine (runpod/render_client_cached.py) and never touches ~/.runpod. Needs no argument but the job file.
# Use:  python3 -I rent_run.py JOB_FILE [--no-upload] [--no-download] [--keep]       (--keep: do not clear the run's folder on the rented machine first; the runner skips pictures that exist)
#             (--no-upload: the tools are already on the rented machine, only the job file is sent)
#       (run it in the background for long jobs and read <folder>/rent_log.txt)
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RUBBISH = os.path.abspath(os.path.join(HERE, '..'))
RELIEF = os.path.abspath(os.path.join(RUBBISH, '..'))
CLIENT = 'scratchpad/runpod/render_client_cached.py'


def client(*args, timeout=900):
    result = subprocess.run(['python3', '-I', CLIENT, *args], capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def job_state(job_id, tries=8):
    """The state of a remote job as a dict; asks again when the answer is not readable (a hiccup of the connection)."""
    text = ''
    for _ in range(tries):
        text = client('job', job_id)
        try:
            return json.loads(text)
        except ValueError:
            time.sleep(2)
    raise RuntimeError('cannot read the state of job ' + job_id + ': ' + repr(text[-300:]))


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
    if '--keep' not in sys.argv:
        # the runner skips pictures that already exist, so the old results on the rented machine must go first (otherwise a re-run brings the OLD pictures back)
        gone = client('run', f'rm -rf {folder}', '--cwd', '/tmp').strip().split()[-1]
        while job_state(gone)['state'] == 'running':      # round 2 plate: wait for it (with the cached client the removal runs in the background and raced the upload)
            time.sleep(0.5)
    if '--no-upload' in sys.argv:
        client('upload', job_file)                      # the tools are already there: only the job file goes up
    else:
        for path in (HERE, os.path.join(RUBBISH, 'maps'), os.path.join(RELIEF, 'study', 'tools'), os.path.join(RELIEF, 'study', 'work'), os.path.join(RELIEF, 'setts', 'tools'), os.path.join(RELIEF, 'setts', 'maps'),
                     os.path.join(RUBBISH, 'work', 'objects_street.txt')):
            client('upload', path)
        client('upload', job_file)
        say(f'uploaded tools and job file ({time.time() - started:.0f} s)')
    kind = json.load(open(job_file))['kind']
    job = client('run', f'bash {HERE}/run_rubbish_jobs.sh {job_file}', '--cwd', folder).strip().split()[-1]
    say('remote job ' + job)
    t0 = time.time()
    while True:
        state = job_state(job)
        if state['state'] != 'running':
            break
        time.sleep(5)
    say(f"remote job {state['state']} return code {state.get('return_code')} after {time.time() - t0:.0f} s; tail: {state.get('log_tail', '')[-300:]!r}")
    if '--no-download' not in sys.argv:
        t1 = time.time()
        stamp = f'{os.path.basename(folder)}_{int(time.time())}'
        remote_tar = f'/workspace/uploads/{stamp}.tar'
        tar_job = client('run', f'tar -cf {remote_tar} -C {folder} .', '--cwd', '/tmp').strip().split()[-1]
        while job_state(tar_job)['state'] == 'running':
            time.sleep(1)
        local_tar = f'/tmp/{stamp}.tar'
        client('download', remote_tar, '--local', local_tar)
        subprocess.run(['tar', '-xf', local_tar, '-C', folder], check=True)
        os.remove(local_tar)
        client('run', f'rm -f {remote_tar}', '--cwd', '/tmp')
        say(f'downloaded the folder as one tar file ({time.time() - t1:.0f} s)')
    say(f'ALL DONE {kind} after {time.time() - started:.0f} s')


main()
