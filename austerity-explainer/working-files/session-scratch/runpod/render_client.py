# What this does: the cloud session's side of the rented RunPod graphics machine. It talks to render_job_server.py on the machine over RunPod's
# HTTPS address (https://<pod id>-8000.proxy.runpod.net), with the secret token kept in ~/.runpod/server_token (never printed, never committed).
# Use (all paths are absolute; a file keeps the same path on the machine unless --remote is given):
#   python3 -I render_client.py status
#   python3 -I render_client.py upload LOCAL_FILE_OR_FOLDER [--remote REMOTE_PATH]
#   python3 -I render_client.py run "SHELL COMMAND" [--cwd FOLDER]        -> prints a job id
#   python3 -I render_client.py job JOB_ID                                 -> state, return code, end of the log
#   python3 -I render_client.py wait JOB_ID [--limit SECONDS]              -> waits (asks every 10 s) until the job finishes
#   python3 -I render_client.py download REMOTE_FILE_OR_FOLDER [--local LOCAL_PATH]
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HOME = os.path.expanduser('~/.runpod')
POD_ID = open(os.path.join(HOME, 'pod_id')).read().strip()
TOKEN = open(os.path.join(HOME, 'server_token')).read().strip()
BASE = f'https://{POD_ID}-8000.proxy.runpod.net'
PIECE = 24 * 1024 * 1024


def call(method, path, query=None, body=None, raw=False, attempts=5):
    url = BASE + path + ('?' + urllib.parse.urlencode(query) if query else '')
    for attempt in range(attempts):
        request = urllib.request.Request(url, data=body, method=method, headers={'X-Token': TOKEN, 'Content-Type': 'application/octet-stream', 'User-Agent': 'render-client/1.0 (blender jobs)'})
        try:
            with urllib.request.urlopen(request, timeout=95) as response:
                data = response.read()
                return data if raw else json.loads(data)
        except urllib.error.HTTPError as error:
            if error.code in (404, 403):
                raise
            time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 ** attempt)
    raise RuntimeError(f'no answer from the machine for {method} {path}')


def upload_file(local_path, remote_path):
    size = os.path.getsize(local_path)
    digest = hashlib.sha256(open(local_path, 'rb').read()).hexdigest()
    try:
        info = call('GET', '/info', {'path': remote_path}, attempts=1)
        if info.get('sha256') == digest:
            return 'same'
    except Exception:
        pass
    with open(local_path, 'rb') as file:
        offset = 0
        while True:
            piece = file.read(PIECE)
            if not piece and offset:
                break
            call('POST', '/file', {'path': remote_path, 'offset': offset}, body=piece)
            offset += len(piece)
            if not piece:
                break
    info = call('GET', '/info', {'path': remote_path})
    if info.get('sha256') != digest:
        raise RuntimeError(f'upload check failed for {local_path}')
    return f'{size} bytes'


def download_file(remote_path, local_path, size):
    os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
    with open(local_path, 'wb') as file:
        offset = 0
        while offset < size:
            piece = call('GET', '/file', {'path': remote_path, 'offset': offset, 'length': PIECE}, raw=True)
            file.write(piece)
            offset += len(piece)
            if not piece:
                break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('target', nargs='?')
    parser.add_argument('--remote')
    parser.add_argument('--local')
    parser.add_argument('--cwd')
    parser.add_argument('--limit', type=float, default=570)
    arguments = parser.parse_args()
    if arguments.action == 'status':
        print(json.dumps(call('GET', '/status'), indent=1))
    elif arguments.action == 'upload':
        source = os.path.abspath(arguments.target)
        destination = arguments.remote or source
        if os.path.isdir(source):
            import tarfile, tempfile
            bundle = tempfile.NamedTemporaryFile(suffix='.tar', delete=False).name
            with tarfile.open(bundle, 'w') as archive:
                archive.add(source, arcname='.')
            remote_bundle = '/workspace/uploads/' + os.path.basename(bundle)
            print('bundle', upload_file(bundle, remote_bundle))
            os.remove(bundle)
            job = call('POST', '/run', body=json.dumps({'command': f'mkdir -p "{destination}" && tar -xf "{remote_bundle}" -C "{destination}" && rm "{remote_bundle}"'}).encode())['id']
            while True:
                state = call('GET', '/jobs/' + job)
                if state['state'] != 'running':
                    break
                time.sleep(2)
            if state.get('return_code') != 0:
                raise RuntimeError('unpacking failed: ' + state.get('log_tail', ''))
            print(destination, 'unpacked')
        elif False:
            for root, dirs, files in os.walk(source):
                for name in files:
                    local_path = os.path.join(root, name)
                    remote_path = os.path.join(destination, os.path.relpath(local_path, source))
                    print(remote_path, upload_file(local_path, remote_path))
        else:
            print(destination, upload_file(source, destination))
    elif arguments.action == 'run':
        print(call('POST', '/run', body=json.dumps({'command': arguments.target, 'cwd': arguments.cwd}).encode())['id'])
    elif arguments.action == 'job':
        print(json.dumps(call('GET', '/jobs/' + arguments.target), indent=1))
    elif arguments.action == 'wait':
        started = time.time()
        while True:
            job = call('GET', '/jobs/' + arguments.target, {'tail': 1500})
            if job['state'] != 'running' or time.time() - started > arguments.limit:
                print(json.dumps(job, indent=1))
                break
            time.sleep(10)
    elif arguments.action == 'download':
        remote = arguments.target
        local = arguments.local or remote
        info = call('GET', '/info', {'path': remote})
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
