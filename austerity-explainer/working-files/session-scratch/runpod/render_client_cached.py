# What this does (CACHED version): the cloud session's side of the rented RunPod graphics machine. The machine is started on demand from a saved template
# with a permanent store (Blender and all uploaded files survive), and it ends itself after 30 idle minutes, so RunPod bills per second of use.
# Order tried: the last-used store (Romania or Iceland) with its cards, then the other store, then any community card without a store
# (Blender then installs itself from mirror sites and the base folders are sent once). The first call after a pause waits 25 s to about 5 minutes.
# It talks to render_job_server.py on the machine over RunPod's
# HTTPS address (https://<pod id>-8000.proxy.runpod.net), with the secret token kept in ~/.runpod/server_token (never printed, never committed).
# Use (all paths are absolute; a file keeps the same path on the machine unless --remote is given):
#   python3 -I render_client_cached.py status
#   python3 -I render_client_cached.py upload LOCAL_FILE_OR_FOLDER [--remote REMOTE_PATH]
#   python3 -I render_client_cached.py run "SHELL COMMAND" [--cwd FOLDER]        -> prints a job id
#   python3 -I render_client_cached.py job JOB_ID                                 -> state, return code, end of the log
#   python3 -I render_client_cached.py wait JOB_ID [--limit SECONDS]              -> waits (asks every 10 s) until the job finishes
#   python3 -I render_client_cached.py download REMOTE_FILE_OR_FOLDER [--local LOCAL_PATH]
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
TOKEN = open(os.path.join(HOME, 'server_token')).read().strip()
STATE_PATH = os.path.join(HOME, 'cached_machine.json')
AUTH = open(os.path.join(HOME, 'auth_header')).read().strip().split(': ', 1)[1]
BASE = None
PIECE = 24 * 1024 * 1024


def runpod_api(method, path, body=None):
    request = urllib.request.Request('https://api.runpod.io' + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Authorization': AUTH, 'Content-Type': 'application/json', 'User-Agent': 'render-client/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read() or b'{}')
    except urllib.error.HTTPError as error:
        return error.code, {'error': error.read().decode(errors='replace')[:500]}


def server_answers(pod_id):
    request = urllib.request.Request(f'https://{pod_id}-8000.proxy.runpod.net/status', headers={'X-Token': TOKEN, 'User-Agent': 'render-client/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read()).get('blender_ready', False)
    except Exception:
        return False


def ensure_machine():
    global BASE
    import fcntl
    with open(os.path.join(HOME, 'machine.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.load(open(STATE_PATH))
        pod_id = state.get('pod_id')
        if pod_id:
            status, pod = runpod_api('GET', f'/v2/pods/{pod_id}')
            if status != 200 or pod.get('status') not in ('RUNNING', 'CREATED', 'STARTING', None):
                pod_id = None
        if not pod_id:
            stores = sorted(state['stores'], key=lambda store: store['volume_id'] != state.get('last_volume_id'))
            attempts = [(gpu, 'SECURE', store) for store in stores for gpu in store['gpu_choices']]
            attempts += [(gpu, 'COMMUNITY', None) for gpu in state.get('fallback_gpu_choices', [])]
            for attempt_pass in range(3):
                if attempt_pass:
                    time.sleep(20)
                for gpu_name, cloud, store in attempts:
                    body = {'name': 'blender-render-cached', 'cloud': cloud, 'templateId': state['template_id'], 'gpu': {'id': gpu_name, 'count': 1}}
                    if store:
                        body['dataCenterIds'] = [store['data_center']]
                        body['mounts'] = {'network': [{'volumeId': store['volume_id'], 'path': '/workspace'}]}
                    status, pod = runpod_api('POST', '/v2/pods', body)
                    if status in (200, 201):
                        pod_id = pod['id']
                        state['pod_volume_id'] = store['volume_id'] if store else None
                        if store:
                            state['last_volume_id'] = store['volume_id']
                        where = f"store in {store['data_center']}" if store else 'NO store (community fallback: Blender installs itself, base folders are sent)'
                        print(f'started a new machine ({gpu_name}, {cloud}, {where})', file=sys.stderr)
                        break
                if pod_id:
                    break
            if not pod_id:
                raise RuntimeError('NO CARD FREE on RunPod right now (all choices tried three times). Render on this machine instead, or try again in a few minutes.')
            state['pod_id'] = pod_id
            open(STATE_PATH, 'w').write(json.dumps(state, indent=1))
        started = time.time()
        while not server_answers(pod_id):
            if time.time() - started > 1200:
                raise RuntimeError('the machine did not get ready within 20 minutes')
            time.sleep(10)
        BASE = f'https://{pod_id}-8000.proxy.runpod.net'
        volume_id = state.get('pod_volume_id')
        needs_base = (volume_id and not state.get('synced_volumes', {}).get(volume_id)) or (not volume_id and state.get('base_sent_to') != pod_id)
        if needs_base:
            print('sending the base folders to this machine once (about 3-4 minutes)', file=sys.stderr)
            for folder in state.get('base_folders', []):
                if os.path.isdir(folder):
                    send_folder(folder, folder)
            if volume_id:
                state.setdefault('synced_volumes', {})[volume_id] = True
            else:
                state['base_sent_to'] = pod_id
            open(STATE_PATH, 'w').write(json.dumps(state, indent=1))


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


def send_folder(source, destination):
    import tarfile, tempfile
    bundle = tempfile.NamedTemporaryFile(suffix='.tar', delete=False).name
    with tarfile.open(bundle, 'w') as archive:
        archive.add(source, arcname='.')
    remote_bundle = '/workspace/uploads/' + os.path.basename(bundle)
    upload_file(bundle, remote_bundle)
    os.remove(bundle)
    job = call('POST', '/run', body=json.dumps({'command': f'mkdir -p "{destination}" && tar -xf "{remote_bundle}" -C "{destination}" && rm "{remote_bundle}"'}).encode())['id']
    while True:
        state = call('GET', '/jobs/' + job)
        if state['state'] != 'running':
            break
        time.sleep(2)
    if state.get('return_code') != 0:
        raise RuntimeError('unpacking failed: ' + state.get('log_tail', ''))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('target', nargs='?')
    parser.add_argument('--remote')
    parser.add_argument('--local')
    parser.add_argument('--cwd')
    parser.add_argument('--limit', type=float, default=570)
    arguments = parser.parse_args()
    ensure_machine()
    if arguments.action == 'status':
        print(json.dumps(call('GET', '/status'), indent=1))
    elif arguments.action == 'upload':
        source = os.path.abspath(arguments.target)
        destination = arguments.remote or source
        if os.path.isdir(source):
            send_folder(source, destination)
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
