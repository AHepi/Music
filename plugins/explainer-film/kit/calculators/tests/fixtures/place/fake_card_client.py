#!/usr/bin/env python3
# What this does: a STAND-IN for a command-line card client (the older style: upload, run, job, download), used by the variations tests. The "store" is a local folder
# named by FAKE_CARD_STORE; the path /workspace means that folder. `run` only writes the command down and prints a job id; `job ID` answers IN_QUEUE the first time and then really runs the command
# (so the waiting loop of the caller is exercised) and answers COMPLETED with the same fields the real client prints: id, state, runpod_status, return_code, seconds, wake_up_ms, billed_work_ms, log_tail.
# `upload` and `download` copy files and folders. Nothing here talks to a network.
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

STORE = os.environ['FAKE_CARD_STORE']
JOBS = os.path.join(STORE, '_jobs')


def mapped(path):
    return path.replace('/workspace', STORE, 1) if path and path.startswith('/workspace') else path


parser = argparse.ArgumentParser()
parser.add_argument('action')
parser.add_argument('target', nargs='?')
parser.add_argument('--remote')
parser.add_argument('--local')
parser.add_argument('--cwd')
parser.add_argument('--timeout', type=float, default=3300)
arguments = parser.parse_args()
os.makedirs(JOBS, exist_ok=True)
if arguments.action == 'upload':
    destination = mapped(arguments.remote)
    if os.path.isdir(arguments.target):
        shutil.copytree(arguments.target, destination, dirs_exist_ok=True)
    else:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy(arguments.target, destination)
    print(destination, 'ok')
elif arguments.action == 'run':
    job_id = f'fakejob{len(os.listdir(JOBS)) + 1}'
    json.dump({'command': arguments.target, 'cwd': arguments.cwd, 'polls': 0}, open(os.path.join(JOBS, job_id + '.json'), 'w'))
    print(job_id)
elif arguments.action == 'job':
    path = os.path.join(JOBS, arguments.target + '.json')
    record = json.load(open(path))
    record['polls'] += 1
    if 'result' not in record:
        if record['polls'] == 1:
            json.dump(record, open(path, 'w'))
            print(json.dumps({'id': arguments.target, 'state': 'running', 'runpod_status': 'IN_QUEUE', 'return_code': None, 'seconds': None, 'wake_up_ms': None, 'billed_work_ms': None, 'log_tail': ''}))
            sys.exit(0)
        started = time.time()
        command = record['command'].replace('/workspace', STORE)
        run = subprocess.run(['/bin/bash', '-c', command], cwd=mapped(record['cwd']) or STORE, capture_output=True, text=True)
        seconds = round(time.time() - started, 1)
        record['result'] = {'id': arguments.target, 'state': 'finished', 'runpod_status': 'COMPLETED', 'return_code': run.returncode, 'seconds': seconds, 'wake_up_ms': 21500 + 100 * len(os.listdir(JOBS)),
                            'billed_work_ms': int(seconds * 1000) + 40000, 'log_tail': (run.stdout + run.stderr)[-500:]}
        json.dump(record, open(path, 'w'))
    print(json.dumps(record['result'], indent=1))
elif arguments.action == 'download':
    source = mapped(arguments.target)
    if not os.path.exists(source):
        sys.exit(f'no such file {arguments.target}')
    os.makedirs(os.path.dirname(os.path.abspath(arguments.local)), exist_ok=True)
    shutil.copy(source, arguments.local)
    print(arguments.local, os.path.getsize(source))
else:
    sys.exit('unknown action')
