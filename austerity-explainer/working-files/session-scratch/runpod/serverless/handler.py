# What this does: the job taker for the pay-per-second (serverless) RunPod render endpoint. A worker machine only exists while
# jobs are waiting or running, so RunPod bills per second of use. Each job is one small task:
#   put  - write a piece of a file onto the permanent store (files arrive in pieces, because a job may carry about 10 MB)
#   get  - read a piece of a file back
#   info - list a folder (paths and sizes) or give a file's size and checksum
#   run  - run a shell command (for example Blender) and return its exit code and the end of its log
#   ping - say which card and which store this worker has
# The store is mounted at /runpod-volume. The same absolute paths as in the cloud session are made to work here
# (/tmp/claude-0, /home/user and /workspace point into the store), so scripts need no changes.
import base64
import hashlib
import os
import socket
import subprocess
import time
import uuid

import runpod

VOLUME = '/runpod-volume'
LIBRARIES = VOLUME + '/sls/libs'
JOB_LOGS = VOLUME + '/sls/job_logs'
PIECE_LIMIT = 7 * 1024 * 1024


def make_same_paths():
    links = {'/workspace': VOLUME, '/tmp/claude-0': VOLUME + '/mirror/tmp/claude-0', '/home/user': VOLUME + '/mirror/home/user'}
    for link, target in links.items():
        if os.path.lexists(link):
            continue
        os.makedirs(target, exist_ok=True)
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink(target, link)
    os.makedirs(JOB_LOGS, exist_ok=True)


def file_checksum(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file:
        for block in iter(lambda: file.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def put_piece(job_input):
    path, offset = job_input['path'], int(job_input.get('offset', 0))
    data = base64.b64decode(job_input.get('data', ''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = 'r+b' if offset and os.path.exists(path) else 'wb'
    with open(path, mode) as file:
        file.seek(offset)
        file.write(data)
        if job_input.get('last'):
            file.truncate(offset + len(data))
    return {'written': len(data), 'size': os.path.getsize(path)}


def get_piece(job_input):
    path, offset = job_input['path'], int(job_input.get('offset', 0))
    length = min(int(job_input.get('length', PIECE_LIMIT)), PIECE_LIMIT)
    if not os.path.isfile(path):
        return {'error': 'no such file', 'path': path}
    with open(path, 'rb') as file:
        file.seek(offset)
        data = file.read(length)
    return {'data': base64.b64encode(data).decode(), 'length': len(data), 'size': os.path.getsize(path)}


def path_info(job_input):
    path = job_input['path']
    if os.path.isdir(path):
        entries = []
        for root, folders, files in os.walk(path):
            for name in files:
                full = os.path.join(root, name)
                entries.append([full, os.path.getsize(full)])
        return {'folder': True, 'files': entries[:20000]}
    if not os.path.isfile(path):
        return {'error': 'no such file', 'path': path}
    return {'folder': False, 'size': os.path.getsize(path), 'sha256': file_checksum(path)}


def run_command(job_input, job_id):
    log_path = os.path.join(JOB_LOGS, job_id + '.log')
    environment = {**os.environ, **(job_input.get('env') or {})}
    environment['LD_LIBRARY_PATH'] = LIBRARIES + (':' + environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else '')
    environment.pop('PYTHONPATH', None)
    started = time.time()
    with open(log_path, 'wb') as log_file:
        try:
            result = subprocess.run(['/bin/bash', '-c', job_input['command']], cwd=job_input.get('cwd') or '/workspace', stdout=log_file,
                                    stderr=subprocess.STDOUT, env=environment, timeout=float(job_input.get('timeout', 3300)))
            return_code = result.returncode
        except subprocess.TimeoutExpired:
            return_code = 'timeout'
    with open(log_path, 'rb') as log_file:
        log_file.seek(max(0, os.path.getsize(log_path) - int(job_input.get('tail', 6000))))
        tail = log_file.read().decode(errors='replace')
    return {'return_code': return_code, 'seconds': round(time.time() - started, 1), 'log_path': log_path, 'log_tail': tail}


def ping():
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
    return {'gpu': gpu, 'host': socket.gethostname(), 'data_centre': os.environ.get('RUNPOD_DC_ID', ''),
            'blender_ready': os.path.exists(VOLUME + '/blender/blender'), 'worker': os.environ.get('RUNPOD_POD_ID', '')}


def handle_job(job):
    job_input = job.get('input') or {}
    operation = job_input.get('op')
    try:
        if operation == 'put':
            return put_piece(job_input)
        if operation == 'get':
            return get_piece(job_input)
        if operation == 'info':
            return path_info(job_input)
        if operation == 'run':
            return run_command(job_input, job.get('id') or uuid.uuid4().hex)
        if operation == 'ping':
            return ping()
        return {'error': 'unknown op: ' + str(operation)}
    except Exception as error:
        return {'error': f'{type(error).__name__}: {error}'}


if __name__ == '__main__':
    make_same_paths()
    runpod.serverless.start({'handler': handle_job})
