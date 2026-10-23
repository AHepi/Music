"""What this does: the JOB TAKER that runs on each worker of a pay-per-second rented-card endpoint. A worker machine exists only while jobs wait or run, so the
account pays for the seconds of work and nothing while idle. Each job is one small task, and the client (../client.py) sends them:
  ping  say which card and which store this worker has
  info  list a folder (paths and sizes) or give one file's size and checksum
  put   write a piece of a file onto the permanent store (a job carries about 10 MB, so a file travels in pieces)
  get   read a piece of a file back
  run   run one shell command (for example Blender) and return its exit code, its seconds and the end of its log
The store is mounted at /runpod-volume (change it with WORKER_VOLUME). /workspace points into it, so a path under /workspace means the same thing in the client and here.
Folders your scenes refer to by their full path can be made to exist here too: set MIRROR_FOLDERS on the endpoint to a comma-separated list of absolute folders; each becomes
a link into the store (so a texture named by its full path is found).
The runpod library is imported only when the job taker starts, so the other functions can be tested anywhere (the tests call handle_job on a temporary folder).
A concrete example: {"op": "run", "command": "echo hi"} returns {"return_code": 0, "seconds": 0.0, "log_tail": "hi\n", ...}.
No key, endpoint id or machine id is stored in this file.
"""
import base64
import hashlib
import os
import socket
import subprocess
import time
import uuid

VOLUME = os.environ.get('WORKER_VOLUME', '/runpod-volume')
LIBRARIES = VOLUME + '/sls/libs'
JOB_LOGS = VOLUME + '/sls/job_logs'
PIECE_LIMIT = 7 * 1024 * 1024


def make_same_paths():
    """/workspace and every folder in MIRROR_FOLDERS become links into the store, unless something is already there."""
    links = {'/workspace': VOLUME}
    for folder in filter(None, (part.strip() for part in os.environ.get('MIRROR_FOLDERS', '').split(','))):
        if os.path.isabs(folder):
            links[folder] = VOLUME + '/mirror' + folder
    for link, target in links.items():
        if os.path.lexists(link):
            continue
        os.makedirs(target, exist_ok=True)
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink(target, link)
    os.makedirs(JOB_LOGS, exist_ok=True)


def file_checksum(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def put_piece(job_input):
    path, offset = job_input['path'], int(job_input.get('offset', 0))
    data = base64.b64decode(job_input.get('data', ''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = 'r+b' if offset and os.path.exists(path) else 'wb'
    with open(path, mode) as handle:
        handle.seek(offset)
        handle.write(data)
        if job_input.get('last'):
            handle.truncate(offset + len(data))
    return {'written': len(data), 'size': os.path.getsize(path)}


def get_piece(job_input):
    path, offset = job_input['path'], int(job_input.get('offset', 0))
    length = min(int(job_input.get('length', PIECE_LIMIT)), PIECE_LIMIT)
    if not os.path.isfile(path):
        return {'error': 'no such file', 'path': path}
    with open(path, 'rb') as handle:
        handle.seek(offset)
        data = handle.read(length)
    return {'data': base64.b64encode(data).decode(), 'length': len(data), 'size': os.path.getsize(path)}


def path_info(job_input):
    path = job_input['path']
    if os.path.isdir(path):
        entries = []
        for root, _folders, files in os.walk(path):
            for name in files:
                full = os.path.join(root, name)
                entries.append([full, os.path.getsize(full)])
        return {'folder': True, 'files': entries[:20000]}
    if not os.path.isfile(path):
        return {'error': 'no such file', 'path': path}
    return {'folder': False, 'size': os.path.getsize(path), 'sha256': file_checksum(path)}


def run_command(job_input, job_id):
    os.makedirs(JOB_LOGS, exist_ok=True)
    log_path = os.path.join(JOB_LOGS, job_id + '.log')
    environment = {**os.environ, **(job_input.get('env') or {})}
    if os.path.isdir(LIBRARIES):
        environment['LD_LIBRARY_PATH'] = LIBRARIES + (':' + environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else '')
    environment.pop('PYTHONPATH', None)
    started = time.time()
    with open(log_path, 'wb') as log_file:
        try:
            result = subprocess.run(['/bin/bash', '-c', job_input['command']], cwd=job_input.get('cwd') or VOLUME, stdout=log_file, stderr=subprocess.STDOUT,
                                    env=environment, timeout=float(job_input.get('timeout', 3300)))
            return_code = result.returncode
        except subprocess.TimeoutExpired:
            return_code = 'timeout'
    with open(log_path, 'rb') as log_file:
        log_file.seek(max(0, os.path.getsize(log_path) - int(job_input.get('tail', 6000))))
        tail = log_file.read().decode(errors='replace')
    return {'return_code': return_code, 'seconds': round(time.time() - started, 1), 'log_path': log_path, 'log_tail': tail}


def ping():
    try:
        gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
    except OSError:
        gpu = ''
    return {'gpu': gpu, 'host': socket.gethostname(), 'blender_ready': os.path.exists(VOLUME + '/blender/blender')}


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
    except Exception as problem:   # noqa: BLE001 - a job must answer with the reason, never crash the worker
        return {'error': f'{type(problem).__name__}: {problem}'}


if __name__ == '__main__':
    import runpod    # only on a worker: the library is kept on the store (start.sh points Python at it)
    make_same_paths()
    runpod.serverless.start({'handler': handle_job})
