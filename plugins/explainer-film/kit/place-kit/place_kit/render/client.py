"""What this does: the RENTED-CARD CLIENT of the place kit. It sends small jobs to a pay-per-second RunPod endpoint of the person's own account (a worker starts when a job
waits and stops soon after its last job, so only the seconds of work are billed), uploads and downloads files in pieces, and draws a whole render job on a card:
`explainer-film-place render --job JOB.json --where rented`. Plain Python (standard library only); it does not need Blender.

Settings (the person's own; they are read at run time and never printed, stored or put in any report):
    RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID   from the environment, or from the file named by RENDER_SETTINGS_FILE (lines NAME=VALUE; the environment wins). A JSON file with the same names
                                         as keys, or with api_key, endpoint_id, store_folder and remote_blender, is read too.
    RENDER_STORE_FOLDER                  the folder on the card's permanent store where jobs go (default /workspace)
    RENDER_REMOTE_BLENDER                Blender on the store (default STORE/blender/blender)
A settings file that sits inside a git folder is refused (a key kept there can be committed by mistake): keep it outside every repository.
What this file never does: print a key or an endpoint id (an error that would contain one is scrubbed first), cancel a job, empty the waiting line or change the endpoint.
The wait rule: when a job has waited in line for place_render.jobs_waiting_stop_minutes while the workers show idle, the client STOPS and says so (the account may be out of money,
or the endpoint switched off); it does not retry, purge or change anything. The person decides.
Actions of `explainer-film-place rent ...`: status, upload LOCAL [--remote PATH], run "COMMAND" [--cwd FOLDER] [--timeout SECONDS], job ID, wait ID [--limit SECONDS],
download REMOTE [--local PATH], balance (read-only: the account's money left).
Exit: 0 done, 1 a job failed or the wait was stopped, 2 a setting or input is missing or unusable.
A concrete example: with the three settings in place, `rent status` wakes a worker (about 20 to 25 s when none is warm) and says which card it has.
"""
import base64
import hashlib
import json
import os
import shlex
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

from .. import house_numbers as numbers

KEY_NAME, ENDPOINT_NAME, STORE_NAME = 'RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_STORE_FOLDER'
REMOTE_BLENDER_NAME, SETTINGS_FILE_NAME = 'RENDER_REMOTE_BLENDER', 'RENDER_SETTINGS_FILE'
PIECE = 6 * 1024 * 1024
DONE = ('COMPLETED', 'FAILED', 'CANCELLED', 'TIMED_OUT')
SETTINGS_HELP = (f'set {KEY_NAME} and {ENDPOINT_NAME} (your own RunPod account\'s API key and serverless endpoint) in the environment, or put NAME=VALUE lines in a file kept OUTSIDE any '
                 f'repository and name it in {SETTINGS_FILE_NAME}; {STORE_NAME} names the folder on the card\'s store for jobs (default /workspace)')


class RentProblem(Exception):
    """A setting or input is missing or unusable (exit 2)."""


class RentFailed(Exception):
    """A job failed, or the wait was stopped (exit 1)."""


class RentStuck(RentFailed):
    """Jobs wait in line while the workers show idle (exit 1; nothing is cancelled or changed)."""


# ------------------------------------------------------------------ settings
def inside_git_folder(path):
    folder = os.path.dirname(os.path.realpath(path))
    while True:
        if os.path.exists(os.path.join(folder, '.git')):
            return True
        parent = os.path.dirname(folder)
        if parent == folder:
            return False
        folder = parent


JSON_KEY_NAMES = {'api_key': KEY_NAME, 'endpoint_id': ENDPOINT_NAME, 'store_folder': STORE_NAME, 'remote_blender': REMOTE_BLENDER_NAME}


def read_settings_file(path):
    """The settings file's values by NAME: lines NAME=VALUE (the form the setup script and every message describe), or a JSON object whose keys are those names or the short names
    api_key, endpoint_id, store_folder and remote_blender."""
    if inside_git_folder(path):
        raise RentProblem(f'the settings file {path} sits inside a git folder, where a key can be committed by mistake. Move it outside every repository and name its new place in {SETTINGS_FILE_NAME}.')
    if not os.path.isfile(path):
        raise RentProblem(f'{SETTINGS_FILE_NAME} names {path}, which is not there')
    values = {}
    with open(path, encoding='utf-8') as handle:
        text = handle.read()
    if text.lstrip().startswith('{'):
        try:
            loaded = json.loads(text)
        except ValueError:
            raise RentProblem(f'{SETTINGS_FILE_NAME} names {path}, which looks like JSON but is not valid JSON; write lines NAME=VALUE instead')
        if isinstance(loaded, dict):
            for key, value in loaded.items():
                if isinstance(value, str):
                    values[JSON_KEY_NAMES.get(key, key)] = value.strip()
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        line = line[7:] if line.startswith('export ') else line
        if '=' in line:
            name, value = line.split('=', 1)
            values[name.strip()] = value.strip().strip('"\'')
    return values


class RentSettings:
    """The person's rented-card settings. Its text form never shows a value."""

    def __init__(self, key, endpoint, store_folder, remote_blender, source):
        self.key, self.endpoint, self.store_folder, self.remote_blender, self.source = key, endpoint, store_folder, remote_blender, source

    def missing(self):
        return [name for name, value in ((KEY_NAME, self.key), (ENDPOINT_NAME, self.endpoint)) if not value]

    def describe(self):
        return [f'{KEY_NAME}: {"set" if self.key else "NOT set"}', f'{ENDPOINT_NAME}: {"set" if self.endpoint else "NOT set"}', f'store folder: {self.store_folder}', f'read from: {self.source}']

    def scrub(self, text):
        text = str(text)
        for secret in (self.key, self.endpoint):
            if secret:
                text = text.replace(secret, '[hidden]')
        return text

    def __repr__(self):
        return 'RentSettings(values hidden)'


def read_settings(environ=None):
    environ = os.environ if environ is None else environ
    values = {name: (environ.get(name) or '').strip() for name in (KEY_NAME, ENDPOINT_NAME, STORE_NAME, REMOTE_BLENDER_NAME)}
    source = 'the environment'
    file_path = (environ.get(SETTINGS_FILE_NAME) or '').strip()
    if file_path:
        from_file = read_settings_file(file_path)
        for name in values:
            values[name] = values[name] or from_file.get(name, '')
        source = 'the environment and the file named in ' + SETTINGS_FILE_NAME
    store = values[STORE_NAME] or '/workspace'
    return RentSettings(values[KEY_NAME], values[ENDPOINT_NAME], store.rstrip('/') or '/', values[REMOTE_BLENDER_NAME] or store.rstrip('/') + '/blender/blender', source)


def require_settings(environ=None):
    settings = read_settings(environ)
    if settings.missing():
        raise RentProblem('the rented-card settings are not complete (' + ', '.join(settings.missing()) + ' missing): ' + SETTINGS_HELP)
    return settings


# ------------------------------------------------------------------ the wire
class WebTransport:
    """Sends calls to the person's own endpoint. Tests give the client a fake with the same two methods (call and graphql)."""

    def __init__(self, settings, opener=None, sleep=time.sleep):
        self.settings, self.sleep = settings, sleep
        self.opener = opener or urllib.request.urlopen
        self.base = f'https://api.runpod.ai/v2/{settings.endpoint}'

    def _where(self, url):
        """The part of a web address that says WHAT is asked (/health, /status/JOB), never the endpoint's own id: this goes into error messages that a helper pastes into reports."""
        if '/v2/' in url:
            rest = url.split('/v2/', 1)[1]
            return '/' + (rest.split('/', 1)[1] if '/' in rest else '')
        return '/' + url.split('//', 1)[-1].split('/', 1)[-1]

    def _send(self, method, url, body, attempts):
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(attempts):
            request = urllib.request.Request(url, method=method, data=data, headers={'Authorization': f'Bearer {self.settings.key}', 'Content-Type': 'application/json',
                                                                                     'User-Agent': 'place-kit-render-client/1.0'})
            try:
                with self.opener(request, timeout=120) as response:
                    return json.loads(response.read() or b'{}')
            except urllib.error.HTTPError as problem:
                if problem.code in (400, 401, 403, 404):
                    raise RentFailed(self.settings.scrub(f'the rented-card service refused {method} {self._where(url)[:40]}: {problem.code} {problem.read().decode(errors="replace")[:300]}'))
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                pass
            self.sleep(2 ** attempt)
        raise RentFailed(self.settings.scrub(f'no answer from the rented-card service for {method} {self._where(url)[:40]}'))

    def call(self, method, path, body=None, attempts=6):
        return self._send(method, self.base + path, body, attempts)

    def graphql(self, query):
        return self._send('POST', 'https://api.runpod.io/graphql', {'query': query}, 3)


# ------------------------------------------------------------------ the client
def file_checksum(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


class Client:
    def __init__(self, transport, sleep=time.sleep, clock=time.time, poll_seconds=3.0):
        self.transport, self.sleep, self.clock, self.poll_seconds = transport, sleep, clock, poll_seconds

    # -- jobs
    def submit(self, job_input):
        return self.transport.call('POST', '/run', {'input': job_input})['id']

    def status(self, job_id):
        return self.transport.call('GET', '/status/' + job_id)

    def do(self, job_input, limit=3600):
        """Runs one small job and waits for its answer."""
        state = self.transport.call('POST', '/runsync', {'input': job_input})
        if state.get('status') not in DONE:
            state = self.wait_for(state['id'], limit)
        if state.get('status') != 'COMPLETED':
            raise RentFailed(f'job {state.get("id")} ended {state.get("status")}: {str(state.get("error") or state.get("output"))[:400]}')
        output = state.get('output') or {}
        if isinstance(output, dict) and output.get('error'):
            raise RentFailed(str(output['error']))
        return output

    def wait_for(self, job_id, limit=3600):
        """Waits for a job. Stops (RentStuck) when it waited in line for the house number of minutes while the workers show idle. Returns the last state when the limit ends."""
        started = self.clock()
        queued_since = None
        stop_after = numbers.value('place_render.jobs_waiting_stop_minutes') * 60
        while True:
            state = self.status(job_id)
            if state.get('status') in DONE:
                return state
            now = self.clock()
            if state.get('status') == 'IN_QUEUE':
                queued_since = now if queued_since is None else queued_since
                if now - queued_since >= stop_after:
                    health = self.transport.call('GET', '/health')
                    idle = int((health.get('workers') or {}).get('idle', 0) or 0)
                    if idle > 0:
                        raise RentStuck(f'stopped: job {job_id} has waited {int((now - queued_since) // 60)} minutes in line while {idle} worker(s) show idle. The account may be out of money or the '
                                        'endpoint switched off. Nothing was cancelled or changed; tell the account owner (the balance action shows the money left).')
            else:
                queued_since = None
            if now - started > limit:
                return state
            self.sleep(self.poll_seconds)

    # -- files
    def upload_file(self, local_path, remote_path):
        digest = file_checksum(local_path)
        try:
            if self.do({'op': 'info', 'path': remote_path}).get('sha256') == digest:
                return 'same'
        except RentFailed:
            pass
        size = os.path.getsize(local_path)
        with open(local_path, 'rb') as handle:
            offset = 0
            while True:
                piece = handle.read(PIECE)
                last = offset + len(piece) >= size
                self.do({'op': 'put', 'path': remote_path, 'offset': offset, 'data': base64.b64encode(piece).decode(), 'last': last})
                offset += len(piece)
                if last:
                    break
        if self.do({'op': 'info', 'path': remote_path}).get('sha256') != digest:
            raise RentFailed(f'the upload of {os.path.basename(local_path)} did not arrive intact (checksums differ)')
        return f'{size} bytes'

    def upload_folder(self, local_folder, remote_folder, uploads_folder):
        """The folder travels as one tar bundle (one wake-up, not one per file) and is unpacked on the store."""
        handle, bundle = tempfile.mkstemp(suffix='.tar')
        os.close(handle)
        try:
            with tarfile.open(bundle, 'w') as archive:
                archive.add(local_folder, arcname='.')
            remote_bundle = uploads_folder.rstrip('/') + '/' + os.path.basename(bundle)
            how = self.upload_file(bundle, remote_bundle)
        finally:
            os.remove(bundle)
        result = self.do({'op': 'run', 'command': f'mkdir -p {shlex.quote(remote_folder)} && tar -xf {shlex.quote(remote_bundle)} -C {shlex.quote(remote_folder)} && rm {shlex.quote(remote_bundle)}'})
        if result.get('return_code') != 0:
            raise RentFailed('unpacking on the store failed: ' + str(result.get('log_tail', ''))[-300:])
        return how

    def download_file(self, remote_path, local_path, size):
        os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
        with open(local_path, 'wb') as handle:
            offset = 0
            while offset < size:
                piece = self.do({'op': 'get', 'path': remote_path, 'offset': offset, 'length': PIECE})
                data = base64.b64decode(piece['data'])
                if not data:
                    break
                handle.write(data)
                offset += len(data)

    def list_remote(self, remote_path):
        info = self.do({'op': 'info', 'path': remote_path})
        return info['files'] if info.get('folder') else []


def job_summary(state):
    output = state.get('output') if isinstance(state.get('output'), dict) else {}
    finished = state.get('status') in DONE
    return {'id': state.get('id'), 'state': 'finished' if finished else 'running', 'runpod_status': state.get('status'), 'return_code': output.get('return_code'), 'seconds': output.get('seconds'),
            'wake_up_ms': state.get('delayTime'), 'billed_work_ms': state.get('executionTime'), 'log_tail': output.get('log_tail', '') or str(state.get('error') or '')}


# ------------------------------------------------------------------ choosing where to draw
def choose_where(requested, finals, environ=None, engine=None):
    """('rented' | 'local', plain reason). auto = tiny previews here, except when the renderer is Cycles (the rule says something is lit, or Cycles was asked for) and the card is set up:
    Cycles here would be a 320 x 240 picture at 16 samples, too small to judge, so even previews go to the card. Finals go to a card when the settings are complete, else they are drawn
    here with a plain warning. `engine` is 'CYCLES', 'EEVEE' or None (not known)."""
    if requested in ('local', 'on-card'):
        return 'local', 'asked for this computer'
    if requested == 'rented':
        return 'rented', 'asked for a rented card'
    complete = not read_settings(environ).missing()
    if not finals:
        if engine == 'CYCLES' and complete:
            return 'rented', 'the renderer is Cycles and a rented card is set up: even previews go to the card (Cycles here would be tiny and too noisy to judge)'
        return 'local', 'previews are drawn here (tiny and quick)' + (' (the renderer is Cycles, so they are a poor look: set up a rented card, or ask for --where rented)' if engine == 'CYCLES' else '')
    if not complete:
        return 'local', 'finals were asked but the rented-card settings are not complete, so they would be drawn here (very slow): ' + SETTINGS_HELP
    return 'rented', 'finals go to a rented card'


# ------------------------------------------------------------------ drawing a render job on a card
IGNORED_NAMES = shutil.ignore_patterns('__pycache__', '*.pyc', 'tests')


def kit_bundle_folder(destination):
    """Copies the parts of the kit a card needs (place-kit, calculators/settings.py and calculator_output.py, film-settings.json) into destination/kit."""
    place_kit_folder = numbers.PLACE_KIT
    target = os.path.join(destination, 'kit')
    shutil.copytree(place_kit_folder, os.path.join(target, 'place-kit'), ignore=IGNORED_NAMES)
    os.makedirs(os.path.join(target, 'calculators'))
    for name in ('settings.py', 'calculator_output.py'):
        shutil.copy(os.path.join(numbers.CALCULATORS, name), os.path.join(target, 'calculators', name))
    shutil.copy(numbers.settings_path(), os.path.join(target, 'film-settings.json'))
    return target


def folder_digest(folder):
    digest = hashlib.sha256()
    for root, folders, files in sorted(os.walk(folder)):
        folders.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            digest.update(os.path.relpath(path, folder).encode())
            digest.update(file_checksum(path).encode())
    return digest.hexdigest()[:12]


def extra_uploads(scene_path, job):
    """Files and folders next to the scene that its pictures need (the job's "upload" list, else maps and textures when they exist), as (local path, relative name)."""
    folder = os.path.dirname(os.path.abspath(scene_path))
    names = job.get('upload') if isinstance(job.get('upload'), list) else [n for n in ('maps', 'textures') if os.path.exists(os.path.join(folder, n))]
    found = []
    for name in names:
        path = os.path.normpath(os.path.join(folder, name))
        if not path.startswith(folder + os.sep):
            raise RentProblem(f'the job\'s upload entry "{name}" points outside the scene\'s folder; list only files and folders next to the scene')
        if not os.path.exists(path):
            raise RentProblem(f'the job\'s upload entry "{name}" is not there next to the scene ({folder})')
        found.append((path, name))
    return found


def size_of(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    return sum(os.path.getsize(os.path.join(root, name)) for root, _folders, files in os.walk(path) for name in files)


def _read_job(path):
    if not path or not os.path.exists(path):
        raise RentProblem(f'give the job file: explainer-film-place render --job JOB.json --where rented (the job file {path or ""} is not there)')
    try:
        with open(path, encoding='utf-8') as handle:
            job = json.load(handle)
    except ValueError as problem:
        raise RentProblem(f'the job file {path} is not valid JSON ({problem})')
    if not isinstance(job, dict) or not isinstance(job.get('views'), list) or not job['views'] or not job.get('out_folder'):
        raise RentProblem(f'the job file {path} needs "views" (a list) and "out_folder"')
    return job


def render_on_rented(parsed, client=None, environ=None, say=print):
    """Draws the job's pictures on a rented card and brings the previews (and with --finals the finals) and the logs back. Returns the exit code (RentProblem and RentFailed pass up)."""
    job = _read_job(parsed.job)
    scene = job.get('scene') or getattr(parsed, 'scene', None)
    if not scene or not os.path.exists(scene):
        raise RentProblem('the scene to draw is not named or not there: give "scene" in the job file or --scene FILE.blend')
    settings = require_settings(environ)
    client = client or Client(WebTransport(settings))
    extras = extra_uploads(scene, job)
    megabytes = (os.path.getsize(scene) + sum(size_of(path) for path, _ in extras)) / 1e6
    limit = numbers.value('place_render.upload_megabytes_max')
    if megabytes > limit:
        raise RentProblem(f'the scene and its files come to {megabytes:.0f} MB, over {limit} MB: upload it once by hand (rent upload) and name it in the job; each upload costs wake-up time')
    job_name = os.path.splitext(os.path.basename(parsed.job))[0] + '-' + file_checksum(scene)[:8]
    store = settings.store_folder
    remote = {'folder': f'{store}/place-jobs/{job_name}', 'uploads': f'{store}/place-jobs/uploads'}
    remote['scene'] = f'{remote["folder"]}/{os.path.basename(scene)}'
    remote['out'] = f'{remote["folder"]}/pictures'
    lines = []
    with tempfile.TemporaryDirectory() as work:
        bundle = kit_bundle_folder(os.path.join(work, 'kit-bundle'))
        remote['kit'] = f'{store}/place-kit-run/{folder_digest(bundle)}'
        marker = remote['kit'] + '/kit/place-kit/blender_run.py'
        try:
            have_kit = client.do({'op': 'info', 'path': marker}).get('size', 0) > 0
        except RentFailed:
            have_kit = False
        lines.append('PASS kit: ' + ('already on the store' if have_kit else 'uploaded ' + client.upload_folder(os.path.dirname(bundle), remote['kit'], remote['uploads'])))
        lines.append(f'PASS scene: {client.upload_file(scene, remote["scene"])}')
        for path, name in extras:
            if os.path.isdir(path):
                lines.append(f'PASS {name}: ' + client.upload_folder(path, f'{remote["folder"]}/{name}', remote['uploads']))
            else:
                lines.append(f'PASS {name}: ' + client.upload_file(path, f'{remote["folder"]}/{name}'))
        remote_job = dict(job, scene=remote['scene'], out_folder=remote['out'])
        job_file = os.path.join(work, 'job.json')
        with open(job_file, 'w', encoding='utf-8') as handle:
            json.dump(remote_job, handle, indent=1)
        remote['job'] = f'{remote["folder"]}/job.json'
        client.upload_file(job_file, remote['job'])
    command = (f'{shlex.quote(settings.remote_blender)} -b --disable-autoexec --python-exit-code 1 {shlex.quote(remote["scene"])} --python {shlex.quote(remote["kit"] + "/kit/place-kit/blender_run.py")} '
               f'-- render --job {shlex.quote(remote["job"])} --where on-card' + (' --finals' if parsed.finals else '') + (f' --engine {parsed.engine}' if parsed.engine not in (None, 'auto') else ''))
    minutes = numbers.value('place_render.job_minutes_max')
    job_id = client.submit({'op': 'run', 'command': command, 'cwd': remote['folder'], 'timeout': minutes * 60})
    lines.append(f'PASS job sent (id {job_id})')
    try:
        state = client.wait_for(job_id, minutes * 60 + 120)
    except RentStuck as problem:
        for line in lines:
            say(line)
        say('FAIL ' + str(problem))
        return 1
    summary = job_summary(state)
    for line in lines:
        say(line)
    if state.get('status') != 'COMPLETED' or summary['return_code'] != 0:
        say(f'FAIL the card job ended {summary["runpod_status"]}, exit {summary["return_code"]}; the end of its log:')
        say(str(summary['log_tail'])[-1500:])
        return 1
    say(f'PASS drawn on the card in {summary["seconds"]} s of work (wake-up {summary["wake_up_ms"]} ms, billed work {summary["billed_work_ms"]} ms; a price shown on the day is '
        f'US${numbers.value("place_render.card_dollars_per_hour")} an hour, which is not a bill: never promise a cost from seconds alone)')
    return _bring_back(client, remote['out'], os.path.abspath(job['out_folder']), parsed.finals, say)


def _bring_back(client, remote_out, local_out, finals, say):
    small = numbers.value('place_render.preview_download_kilobytes_max') * 1024
    worst = 0
    os.makedirs(local_out, exist_ok=True)
    for remote_path, size in client.list_remote(remote_out):
        name = os.path.basename(remote_path)
        is_log = name.endswith('.json')
        is_preview = '_preview.' in name
        if not (is_log or is_preview or finals):
            say(f'LOOK {name}: left on the card ({size // 1024} KB); fetch it with: explainer-film-place rent download {remote_path} --local {os.path.join(local_out, name)}')
            continue
        if is_preview and size > small:
            say(f'LOOK {name}: {size // 1024} KB is more than the {small // 1024} KB for a preview; left on the card (rent download fetches it)')
            continue
        client.download_file(remote_path, os.path.join(local_out, name), size)
        say(f'PASS {name} ({size // 1024} KB) -> {os.path.join(local_out, name)}')
    for log_name in sorted(n for n in os.listdir(local_out) if n.endswith('.json')):
        try:
            with open(os.path.join(local_out, log_name), encoding='utf-8') as handle:
                log = json.load(handle)
        except ValueError:
            continue
        if log.get('ok') is False:
            worst = 1
            say(f'FAIL {log_name}: the card said this picture failed')
    return worst


# ------------------------------------------------------------------ the `rent` verb
def _print_json(parsed, payload):
    if getattr(parsed, 'out', None):
        os.makedirs(os.path.dirname(os.path.abspath(parsed.out)) or '.', exist_ok=True)
        with open(parsed.out, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=1)
    if getattr(parsed, 'json', False) or not getattr(parsed, 'out', None):
        print(json.dumps(payload, indent=1))


def main_command(parsed, client=None, environ=None):
    """The `rent` verb. Returns the exit code (see the note at the top)."""
    try:
        action = parsed.action or 'status'
        settings = require_settings(environ)
        client = client or Client(WebTransport(settings))
        target = list(parsed.target or [])
        if action == 'status':
            _print_json(parsed, {**client.do({'op': 'ping'}), 'endpoint_health': client.transport.call('GET', '/health')})
        elif action == 'balance':
            answer = client.transport.graphql('query { myself { clientBalance currentSpendPerHr } }')
            money = ((answer.get('data') or {}).get('myself')) or {}
            _print_json(parsed, {'money_left': money.get('clientBalance'), 'spend_per_hour_now': money.get('currentSpendPerHr')})
        elif action == 'upload':
            if not target:
                raise RentProblem('rent upload needs the file or folder to send: explainer-film-place rent upload LOCAL [--remote PATH]')
            source = os.path.abspath(target[0])
            if not os.path.exists(source):
                raise RentProblem(f'{source} is not there')
            destination = parsed.remote or source
            how = client.upload_folder(source, destination, settings.store_folder + '/place-jobs/uploads') if os.path.isdir(source) else client.upload_file(source, destination)
            print(f'PASS {destination}: {how}')
        elif action == 'run':
            if not target:
                raise RentProblem('rent run needs the command: explainer-film-place rent run "COMMAND" [--cwd FOLDER] [--timeout SECONDS]')
            print(client.submit({'op': 'run', 'command': target[0], 'cwd': parsed.cwd, 'timeout': parsed.timeout or numbers.value('place_render.job_minutes_max') * 60}))
        elif action in ('job', 'wait'):
            if not target:
                raise RentProblem(f'rent {action} needs the job id')
            state = client.status(target[0]) if action == 'job' else client.wait_for(target[0], parsed.limit or 3600)
            _print_json(parsed, job_summary(state))
        elif action == 'download':
            if not target:
                raise RentProblem('rent download needs the remote file or folder')
            remote = target[0]
            local = parsed.local or remote
            info = client.do({'op': 'info', 'path': remote})
            if info.get('folder'):
                for remote_path, size in info['files']:
                    client.download_file(remote_path, os.path.join(local, os.path.relpath(remote_path, remote)), size)
                    print(f'PASS {remote_path} ({size} bytes)')
            elif info.get('size') is not None:
                client.download_file(remote, local, info['size'])
                print(f'PASS {local} ({info["size"]} bytes)')
            else:
                raise RentProblem(f'{remote} is not on the store')
        else:
            raise RentProblem(f'unknown rent action: {action}')
        return 0
    except RentProblem as problem:
        print(f'FAIL {scrubbed(problem, environ)}', file=sys.stderr)
        return 2
    except RentFailed as problem:
        print(f'FAIL {scrubbed(problem, environ)}')
        return 1


def scrubbed(problem, environ=None):
    """The text of an error with the key and the endpoint id (if the person's settings are readable) replaced, so nothing the client prints can carry them."""
    try:
        return read_settings(environ).scrub(problem)
    except RentProblem:
        return str(problem)


def render_command(parsed, client=None, environ=None):
    """`render --where rented` (or auto with finals and the settings set): the exit code."""
    try:
        return render_on_rented(parsed, client, environ)
    except RentProblem as problem:
        print(f'FAIL {scrubbed(problem, environ)}', file=sys.stderr)
        return 2
    except RentFailed as problem:
        print(f'FAIL {scrubbed(problem, environ)}')
        return 1
