# What this does: the cloud session's side of the PAY-PER-SECOND (serverless) RunPod render endpoint. Workers exist only while a job
# waits or runs, so the account pays for the seconds of work (plus a short wake-up of about 20-30 s when none is warm), never for
# idle machines. Same actions as the older render_client_cached.py, so helpers can switch by changing only the script name:
#   python3 -I render_client_serverless.py status                                   -> wakes a worker, says which card it has
#   python3 -I render_client_serverless.py upload LOCAL_FILE_OR_FOLDER [--remote PATH]
#   python3 -I render_client_serverless.py run "SHELL COMMAND" [--cwd FOLDER] [--timeout SECONDS]   -> prints a job id
#   python3 -I render_client_serverless.py job JOB_ID                                -> state, return code, end of the log
#   python3 -I render_client_serverless.py wait JOB_ID [--limit SECONDS]             -> waits until the job finishes
#   python3 -I render_client_serverless.py download REMOTE_FILE_OR_FOLDER [--local PATH]
# A file keeps the same absolute path on the workers (the store is mounted there and /tmp/claude-0, /home/user and /workspace point
# into it). Blender there: /workspace/blender/blender -b --disable-autoexec ... (no xvfb-run). The key and the endpoint id are read
# from ~/.runpod and never printed.
import argparse
import base64
import hashlib
import json
import os
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

HOME = os.path.expanduser('~/.runpod')
AUTH = open(os.path.join(HOME, 'auth_header')).read().strip().split(': ', 1)[1]
ENDPOINT = json.load(open(os.path.join(HOME, 'cached_machine.json')))['serverless_endpoint_id']
BASE = f'https://api.runpod.ai/v2/{ENDPOINT}'
PIECE = 6 * 1024 * 1024
DONE = ('COMPLETED', 'FAILED', 'CANCELLED', 'TIMED_OUT')


def call(method, path, body=None, attempts=6):
    for attempt in range(attempts):
        request = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                         headers={'Authorization': AUTH, 'Content-Type': 'application/json', 'User-Agent': 'render-client/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read() or b'{}')
        except urllib.error.HTTPError as error:
            if error.code in (400, 401, 403, 404):
                raise RuntimeError(f'RunPod refused {method} {path}: {error.code} {error.read().decode(errors="replace")[:300]}')
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(2 ** attempt)
    raise RuntimeError(f'no answer from RunPod for {method} {path}')


def submit(job_input):
    return call('POST', '/run', {'input': job_input})['id']


def wait_for(job_id, limit=3600):
    started = time.time()
    while True:
        state = call('GET', '/status/' + job_id)
        if state.get('status') in DONE or time.time() - started > limit:
            return state
        time.sleep(3)


def do(job_input, limit=3600):
    state = call('POST', '/runsync', {'input': job_input})
    if state.get('status') not in DONE:
        state = wait_for(state['id'], limit)
    if state.get('status') != 'COMPLETED':
        raise RuntimeError(f"job {state.get('id')} ended {state.get('status')}: {str(state.get('error') or state.get('output'))[:400]}")
    output = state.get('output') or {}
    if isinstance(output, dict) and output.get('error'):
        raise RuntimeError(output['error'])
    return output


def checksum(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file:
        for block in iter(lambda: file.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def upload_file(local_path, remote_path):
    digest = checksum(local_path)
    try:
        if do({'op': 'info', 'path': remote_path}).get('sha256') == digest:
            return 'same'
    except RuntimeError:
        pass
    size = os.path.getsize(local_path)
    with open(local_path, 'rb') as file:
        offset = 0
        while True:
            piece = file.read(PIECE)
            last = offset + len(piece) >= size
            do({'op': 'put', 'path': remote_path, 'offset': offset, 'data': base64.b64encode(piece).decode(), 'last': last})
            offset += len(piece)
            if last:
                break
    if do({'op': 'info', 'path': remote_path}).get('sha256') != digest:
        raise RuntimeError(f'upload check failed for {local_path}')
    return f'{size} bytes'


def download_file(remote_path, local_path, size):
    os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
    with open(local_path, 'wb') as file:
        offset = 0
        while offset < size:
            piece = do({'op': 'get', 'path': remote_path, 'offset': offset, 'length': PIECE})
            data = base64.b64decode(piece['data'])
            if not data:
                break
            file.write(data)
            offset += len(data)


def job_summary(state):
    output = state.get('output') if isinstance(state.get('output'), dict) else {}
    finished = state.get('status') in DONE
    return {'id': state.get('id'), 'state': 'finished' if finished else 'running', 'runpod_status': state.get('status'),
            'return_code': output.get('return_code', None if finished else None), 'seconds': output.get('seconds'),
            'wake_up_ms': state.get('delayTime'), 'billed_work_ms': state.get('executionTime'),
            'log_tail': output.get('log_tail', '') or str(state.get('error') or '')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('target', nargs='?')
    parser.add_argument('--remote')
    parser.add_argument('--local')
    parser.add_argument('--cwd')
    parser.add_argument('--timeout', type=float, default=3300)
    parser.add_argument('--limit', type=float, default=3600)
    arguments = parser.parse_args()
    if arguments.action == 'status':
        print(json.dumps({**do({'op': 'ping'}), 'endpoint_health': call('GET', '/health')}, indent=1))
    elif arguments.action == 'upload':
        source = os.path.abspath(arguments.target)
        destination = arguments.remote or source
        if os.path.isdir(source):
            bundle = tempfile.NamedTemporaryFile(suffix='.tar', delete=False).name
            with tarfile.open(bundle, 'w') as archive:
                archive.add(source, arcname='.')
            remote_bundle = '/workspace/uploads/' + os.path.basename(bundle)
            print('bundle', upload_file(bundle, remote_bundle))
            os.remove(bundle)
            result = do({'op': 'run', 'command': f'mkdir -p "{destination}" && tar -xf "{remote_bundle}" -C "{destination}" && rm "{remote_bundle}"'})
            if result.get('return_code') != 0:
                raise RuntimeError('unpacking failed: ' + result.get('log_tail', ''))
            print(destination, 'unpacked')
        else:
            print(destination, upload_file(source, destination))
    elif arguments.action == 'run':
        print(submit({'op': 'run', 'command': arguments.target, 'cwd': arguments.cwd, 'timeout': arguments.timeout}))
    elif arguments.action == 'job':
        print(json.dumps(job_summary(call('GET', '/status/' + arguments.target)), indent=1))
    elif arguments.action == 'wait':
        print(json.dumps(job_summary(wait_for(arguments.target, arguments.limit)), indent=1))
    elif arguments.action == 'download':
        remote = arguments.target
        local = arguments.local or remote
        info = do({'op': 'info', 'path': remote})
        if info.get('folder'):
            for remote_path, size in info['files']:
                local_path = os.path.join(local, os.path.relpath(remote_path, remote))
                download_file(remote_path, local_path, size)
                print(local_path, size)
        else:
            download_file(remote, local, info['size'])
            print(local, info['size'])
    else:
        sys.exit('unknown action')


if __name__ == '__main__':
    main()
