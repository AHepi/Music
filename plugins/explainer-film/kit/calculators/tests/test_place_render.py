"""What this does: tests the place kit's drawing side.
Part A (plain Python, always runs): the rented-card client with a FAKE card (a fake service that hands each job to the real job taker, worker/handler.py, working in a temporary
folder). It checks that the settings are read from the environment or a file kept outside any repository and are never shown; that a file goes up and comes back in pieces with
matching checksums (and a second upload of the same file says "same"); that a folder goes up as one bundle; that a job which waits in line while workers show idle makes the client STOP
(and that it sent no cancel, purge or endpoint change); that a whole render job goes to the fake card and its previews and logs come back (finals only on request); that a failing
card job gives exit 1 with the end of its log; that missing settings give exit 2; and that no output holds the fake key.
The 1.4.0 fix round adds: a dead network gives an error that holds neither the key nor the endpoint id (the "no answer" message used to start with the id); a settings file written as JSON
(with the names as keys, or api_key and endpoint_id) is read as well as NAME=VALUE lines, and the default store folder is /workspace; `auto` sends even previews to a card when the renderer is
Cycles and the settings are complete (and keeps tiny local previews when they are not or when the renderer is EEVEE).
Part B (needs Blender: BLENDER, machine-settings.env, or the PATH; otherwise the part is skipped and says so): the render verb on tiny scenes: no lamp picks EEVEE, a lamp or a glowing
material picks Cycles, a black scene is called out, a missing camera is called out, and every picture gets its JSON log.
Run: python3 kit/calculators/tests/test_place_render.py
"""
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, FIXTURES, blender_program  # noqa: E402

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
folder = tempfile.mkdtemp(prefix='place-render-test-')
os.environ['WORKER_VOLUME'] = os.path.join(folder, 'volume')
os.makedirs(os.environ['WORKER_VOLUME'])

from place_kit.render import client as rc  # noqa: E402

spec = importlib.util.spec_from_file_location('worker_handler', os.path.join(PLACE_KIT, 'place_kit', 'render', 'worker', 'handler.py'))
handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler)

check = Checker('place render: the rented-card client (fake card) and the render verb')

FAKE_KEY = 'rp' + 'a_' + 'k' * 24           # built here so no key-looking text is in this file
FAKE_ENDPOINT = 'endpoint' + 'x' * 14


class FakeCard:
    """Stands in for the rented-card service: each job goes to the real job taker, which works inside the temporary folder."""

    def __init__(self, queue_polls=0, idle=0):
        self.calls, self.jobs, self.queue_polls, self.idle, self.count = [], {}, queue_polls, idle, 0

    def _make(self, body):
        self.count += 1
        job_id = f'job{self.count}'
        output = handler.handle_job({'id': job_id, 'input': body['input']})
        self.jobs[job_id] = {'id': job_id, 'status': 'COMPLETED', 'output': output, 'executionTime': 1500, 'delayTime': 700, 'polls': 0}
        return job_id

    def call(self, method, path, body=None, attempts=1):
        self.calls.append((method, path))
        if path == '/runsync':
            return {key: value for key, value in self.jobs[self._make(body)].items() if key != 'polls'}
        if path == '/run':
            return {'id': self._make(body), 'status': 'IN_QUEUE'}
        if path.startswith('/status/'):
            job = self.jobs[path.split('/')[-1]]
            job['polls'] += 1
            if job['polls'] <= self.queue_polls:
                return {'id': job['id'], 'status': 'IN_QUEUE'}
            return {key: value for key, value in job.items() if key != 'polls'}
        if path == '/health':
            return {'workers': {'idle': self.idle, 'running': 0}}
        raise AssertionError('the client sent an unexpected call: ' + path)

    def graphql(self, query):
        self.calls.append(('POST', 'graphql'))
        return {'data': {'myself': {'clientBalance': 12.5, 'currentSpendPerHr': 0.0}}}


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


# ---------------------------------------------------------------- settings
environment = {rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT}
settings = rc.read_settings(environment)
check.equal('both settings from the environment are read', settings.missing(), [])
check.true('the text form of the settings never shows a value', FAKE_KEY not in repr(settings) and FAKE_ENDPOINT not in repr(settings) and FAKE_KEY not in ' '.join(settings.describe()),
           proves='printing the settings object by mistake cannot leak a key')
check.equal('missing settings are named', rc.read_settings({}).missing(), [rc.KEY_NAME, rc.ENDPOINT_NAME])
check.equal('an error text holding the key is scrubbed', settings.scrub(f'refused for {FAKE_KEY} at {FAKE_ENDPOINT}'), 'refused for [hidden] at [hidden]')
outside = os.path.join(folder, 'outside-settings.env')
with open(outside, 'w') as handle:
    handle.write(f'# a comment\nexport {rc.KEY_NAME}="{FAKE_KEY}"\n{rc.ENDPOINT_NAME}={FAKE_ENDPOINT}\n{rc.STORE_NAME}=/somewhere/store/\n')
from_file = rc.read_settings({rc.SETTINGS_FILE_NAME: outside})
check.true('a settings file outside any repository is read (export lines, quotes, comments)', from_file.key == FAKE_KEY and from_file.endpoint == FAKE_ENDPOINT and from_file.store_folder == '/somewhere/store',
           f'store folder {from_file.store_folder}')
check.equal('the environment wins over the file', rc.read_settings({rc.SETTINGS_FILE_NAME: outside, rc.KEY_NAME: 'other-value'}).key, 'other-value')
json_file = os.path.join(folder, 'outside-settings.json')
with open(json_file, 'w') as handle:
    json.dump({'api_key': FAKE_KEY, 'endpoint_id': FAKE_ENDPOINT, 'store_folder': '/json/store'}, handle)
from_json = rc.read_settings({rc.SETTINGS_FILE_NAME: json_file})
check.true('a settings file written as JSON (api_key, endpoint_id, store_folder) is read too (the docs once described exactly this and the client read it as "not set")', from_json.key == FAKE_KEY and from_json.endpoint == FAKE_ENDPOINT and from_json.store_folder == '/json/store')
json_names = os.path.join(folder, 'outside-names.json')
with open(json_names, 'w') as handle:
    json.dump({rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT}, handle)
check.equal('...and JSON with the NAME keys too', rc.read_settings({rc.SETTINGS_FILE_NAME: json_names}).missing(), [])
check.equal('the default store folder is /workspace (the docs once said another folder)', rc.read_settings({rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT}).store_folder, '/workspace')


class DeadNetwork:
    """An opener that never gets an answer, like a network that is down."""
    def __call__(self, request, timeout=None):
        import urllib.error
        raise urllib.error.URLError('no route')


dead = rc.WebTransport(settings, opener=DeadNetwork(), sleep=lambda seconds: None)
messages = []
for attempt in (lambda: dead.call('GET', '/health', attempts=2), lambda: dead.call('GET', '/status/job123', attempts=2), lambda: dead.graphql('query { x }')):
    try:
        attempt()
    except rc.RentFailed as problem:
        messages.append(str(problem))
check.true('a dead network gives errors that say what was asked (the action) and hold neither the endpoint id nor the key', len(messages) == 3 and all(FAKE_ENDPOINT not in m and FAKE_KEY not in m for m in messages) and '/health' in messages[0] and '/status/job123' in messages[1],
           ' | '.join(messages)[:200], recorded='the code review: the "no answer" message started with the endpoint id and the commands printed it',
           proves='a helper that pastes an error into a report cannot paste the id')
shown = rc.scrubbed(rc.RentFailed(f'something went wrong at {FAKE_ENDPOINT}'), {rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT})
check.equal('whatever the client prints is scrubbed with the person\'s settings first', shown, 'something went wrong at [hidden]')
no_card = {}
check.equal('auto previews stay tiny and local when the renderer is EEVEE, even with a card set up', rc.choose_where('auto', False, environment, engine='EEVEE')[0], 'local')
check.equal('auto previews go to the card when the renderer is Cycles and the card is set up (a Cycles picture here is 320 x 240 at 16 samples)', rc.choose_where('auto', False, environment, engine='CYCLES')[0], 'rented')
cycles_here = rc.choose_where('auto', False, no_card, engine='CYCLES')
check.true('auto Cycles previews with no card stay local and say that they are a poor look', cycles_here[0] == 'local' and 'poor look' in cycles_here[1], cycles_here[1][:160])
repository = os.path.join(folder, 'a-repository')
os.makedirs(os.path.join(repository, '.git'))
inside = os.path.join(repository, 'settings.env')
with open(inside, 'w') as handle:
    handle.write(f'{rc.KEY_NAME}={FAKE_KEY}\n')
try:
    rc.read_settings({rc.SETTINGS_FILE_NAME: inside})
    refused = False
except rc.RentProblem as problem:
    refused = 'git' in str(problem) and FAKE_KEY not in str(problem)
check.true('a settings file inside a git folder is refused, and the refusal does not repeat the key', refused)
source = open(os.path.join(PLACE_KIT, 'place_kit', 'render', 'client.py'), encoding='utf-8').read()
code_only = '\n'.join(line for line in source.splitlines() if not line.strip().startswith('#'))
forbidden = [word for word in ('/purge-queue', '/cancel/', 'saveEndpoint', 'deleteEndpoint', 'workersMax') if word in code_only]
check.equal('the client has no code that cancels a job, empties the line or changes the endpoint', forbidden, [])
check.true('the client does not name the personal settings folder as a path', not re.search(r'(~/|/)\.run' + r'pod\b', source))

# ---------------------------------------------------------------- files and folders
rc.PIECE = 1000                                   # small pieces so a short file travels in several
store = os.path.join(folder, 'store')
card = FakeCard()
client = rc.Client(card, sleep=lambda seconds: None)
local_file = os.path.join(folder, 'payload.bin')
payload = os.urandom(4500)
with open(local_file, 'wb') as handle:
    handle.write(payload)
remote_file = os.path.join(store, 'inbox', 'payload.bin')
how = client.upload_file(local_file, remote_file)
check.true('a file of 4500 bytes goes up in pieces and arrives identical', open(remote_file, 'rb').read() == payload, how)
puts = [call for call in card.calls if call[1] == '/runsync']
check.true('it travelled in more than one piece', len(puts) >= 5, f'{len(puts)} jobs for the upload')
check.equal('a second upload of the same file says same', client.upload_file(local_file, remote_file), 'same')
back = os.path.join(folder, 'back', 'payload.bin')
client.download_file(remote_file, back, len(payload))
check.true('the file comes back identical', open(back, 'rb').read() == payload)
bundle_source = os.path.join(folder, 'bundle-source')
os.makedirs(os.path.join(bundle_source, 'inner'))
for name in ('one.txt', os.path.join('inner', 'two.txt')):
    with open(os.path.join(bundle_source, name), 'w') as handle:
        handle.write('content of ' + name)
client.upload_folder(bundle_source, os.path.join(store, 'bundled'), os.path.join(store, 'uploads'))
check.true('a folder goes up as one bundle and is unpacked', open(os.path.join(store, 'bundled', 'inner', 'two.txt')).read() == 'content of ' + os.path.join('inner', 'two.txt') and not os.listdir(os.path.join(store, 'uploads')))
check.equal('an unknown job kind answers with a plain error and does not crash', handler.handle_job({'id': 'x', 'input': {'op': 'nonsense'}})['error'], 'unknown op: nonsense')
ran = handler.handle_job({'id': 'y', 'input': {'op': 'run', 'command': 'echo hello-from-the-card; exit 3'}})
check.true('a command returns its exit code and the end of its log', ran['return_code'] == 3 and 'hello-from-the-card' in ran['log_tail'])
timed = handler.handle_job({'id': 'z', 'input': {'op': 'run', 'command': 'sleep 5', 'timeout': 0.3}})
check.equal('a command over its time is given up and says timeout', timed['return_code'], 'timeout')

# ---------------------------------------------------------------- the wait rule
clock = FakeClock()
card = FakeCard(queue_polls=10 ** 9, idle=2)
patient = rc.Client(card, sleep=clock.sleep, clock=clock.time, poll_seconds=3.0)
job_id = patient.submit({'op': 'ping'})
try:
    patient.wait_for(job_id, limit=3600)
    stopped, message = False, ''
except rc.RentStuck as problem:
    stopped, message = True, str(problem)
waited = clock.now - 1000.0
check.true('a job that waits 5 minutes in line while workers show idle stops the client', stopped and 295 <= waited <= 320, f'stopped after {waited:.0f} seconds')
check.true('the stop message tells the person and promises no change', 'Nothing was cancelled' in message and 'tell the account owner' in message)
methods = {(method, path.split('/')[1] if path.startswith('/status') else path) for method, path in card.calls}
check.true('the client sent only a submit, status checks and a health check (no cancel, no purge)', methods <= {('POST', '/run'), ('GET', 'status'), ('GET', '/health')}, str(sorted(methods)))
clock = FakeClock()
card = FakeCard(queue_polls=10 ** 9, idle=0)
patient = rc.Client(card, sleep=clock.sleep, clock=clock.time, poll_seconds=3.0)
job_id = patient.submit({'op': 'ping'})
state = patient.wait_for(job_id, limit=900)
check.true('a job that waits while NO worker is idle keeps waiting until the limit (a card is starting up)', state.get('status') == 'IN_QUEUE' and clock.now - 1000.0 >= 900, f'status {state.get("status")}')
clock = FakeClock()
card = FakeCard(queue_polls=5, idle=2)
patient = rc.Client(card, sleep=clock.sleep, clock=clock.time, poll_seconds=3.0)
job_id = patient.submit({'op': 'run', 'command': 'echo done'})
check.equal('a job that waits briefly then runs completes', patient.wait_for(job_id, 3600).get('status'), 'COMPLETED')

# ---------------------------------------------------------------- choosing where
check.equal('auto without finals draws here', rc.choose_where('auto', False, environment)[0], 'local')
check.equal('auto with finals and settings goes to a card', rc.choose_where('auto', True, environment)[0], 'rented')
check.equal('auto with finals and no settings draws here and says why', (rc.choose_where('auto', True, {})[0], 'RUNPOD_API_KEY' in rc.choose_where('auto', True, {})[1]), ('local', True))
check.equal('rented asks for a card', rc.choose_where('rented', False, {})[0], 'rented')

# ---------------------------------------------------------------- a whole render job on the fake card
fake_blender = os.path.join(store, 'blender', 'blender')
os.makedirs(os.path.dirname(fake_blender))
with open(fake_blender, 'w') as handle:
    handle.write(f'''#!{sys.executable}
import json, os, sys
arguments = sys.argv[sys.argv.index('--') + 1:]
job = json.load(open(arguments[arguments.index('--job') + 1]))
finals = '--finals' in arguments
print('fake blender drawing', len(job['views']), 'view(s)')
os.makedirs(job['out_folder'], exist_ok=True)
for view in job['views']:
    if 'bad' in view['name']:
        print('boom: the scene has no camera'); sys.exit(3)
    kinds = ['preview'] + (['final'] if finals else [])
    for kind in kinds:
        base = os.path.join(job['out_folder'], view['name'] + '_' + kind)
        open(base + ('.jpg' if kind == 'preview' else '.png'), 'wb').write(b'x' * (30000 if kind == 'preview' else 500000))
        json.dump({{'view': view['name'], 'kind': kind, 'ok': True, 'where': 'card'}}, open(base + '.json', 'w'))
''')
os.chmod(fake_blender, os.stat(fake_blender).st_mode | stat.S_IEXEC)
scene_file = os.path.join(folder, 'work', 'tiny.blend')
os.makedirs(os.path.join(folder, 'work', 'maps'))
open(scene_file, 'wb').write(b'not really a scene' * 10)
open(os.path.join(folder, 'work', 'maps', 'one.png'), 'wb').write(b'map')
job_path = os.path.join(folder, 'work', 'job.json')
out_folder = os.path.join(folder, 'work', 'pictures')
json.dump({'scene': scene_file, 'out_folder': out_folder, 'views': [{'name': 'lane_a', 'camera': 'Camera A'}, {'name': 'lane_b'}]}, open(job_path, 'w'))


class Parsed:
    job, finals, engine, scene, json, out = job_path, False, 'auto', None, False, None


rented_environment = {rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT, rc.STORE_NAME: store, rc.REMOTE_BLENDER_NAME: fake_blender}
said = []
card = FakeCard()
client = rc.Client(card, sleep=lambda seconds: None)
code = rc.render_on_rented(Parsed, client, rented_environment, said.append)
text = '\n'.join(said)
check.equal('a render job on the fake card ends with exit 0', code, 0)
check.true('the previews and their logs came back', all(os.path.exists(os.path.join(out_folder, name)) for name in ('lane_a_preview.jpg', 'lane_a_preview.json', 'lane_b_preview.jpg')), ', '.join(sorted(os.listdir(out_folder))) if os.path.isdir(out_folder) else 'no folder')
check.true('without --finals no final picture was fetched', not os.path.exists(os.path.join(out_folder, 'lane_a_final.png')))
check.true('the scene and the maps beside it were uploaded', os.path.exists(os.path.join(store, 'place-jobs')) and any('one.png' in names for _, _, names in os.walk(os.path.join(store, 'place-jobs'))))
check.true('the kit was uploaded once to the store', os.path.exists(os.path.join(store, 'place-kit-run')) and any('blender_run.py' in names for _, _, names in os.walk(os.path.join(store, 'place-kit-run'))))
check.true('the report names the work seconds and says a price is not a bill', 'billed work 1500 ms' in text and 'not a bill' in text)
check.true('nothing the client printed holds the key or the endpoint id', FAKE_KEY not in text and FAKE_ENDPOINT not in text)
Parsed.finals = True
said2 = []
card2 = FakeCard()
code2 = rc.render_on_rented(Parsed, rc.Client(card2, sleep=lambda seconds: None), rented_environment, said2.append)
check.true('with --finals the final pictures come back too', code2 == 0 and os.path.exists(os.path.join(out_folder, 'lane_a_final.png')), said2[-1][:160])
uploads_second = [call for call in card2.calls if call[1] == '/runsync']
check.true('the second run finds the kit already on the store (fewer jobs than the first)', len(uploads_second) < len([c for c in card.calls if c[1] == '/runsync']), f'{len(uploads_second)} against {len([c for c in card.calls if c[1] == "/runsync"])}')
Parsed.finals = False
json.dump({'scene': scene_file, 'out_folder': os.path.join(folder, 'work', 'pictures-bad'), 'views': [{'name': 'bad_view'}]}, open(job_path, 'w'))
said3 = []
code3 = rc.render_on_rented(Parsed, rc.Client(FakeCard(), sleep=lambda seconds: None), rented_environment, said3.append)
check.true('a failing card job gives exit 1 and the end of its log', code3 == 1 and 'boom: the scene has no camera' in '\n'.join(said3), said3[-1][:160])
try:
    rc.render_on_rented(Parsed, rc.Client(FakeCard()), {}, lambda line: None)
    missing_code = None
except rc.RentProblem as problem:
    missing_code = 'RUNPOD_API_KEY' in str(problem)
check.true('missing settings stop a render with a sentence naming them (exit 2 from the command)', missing_code is True)
big_job = dict(json.load(open(job_path)), upload=['maps'])
os.makedirs(os.path.join(folder, 'work', 'maps'), exist_ok=True)
with open(os.path.join(folder, 'work', 'maps', 'huge.bin'), 'wb') as handle:
    handle.seek(310 * 1000 * 1000)
    handle.write(b'x')
json.dump(big_job, open(job_path, 'w'))
try:
    rc.render_on_rented(Parsed, rc.Client(FakeCard()), rented_environment, lambda line: None)
    too_big = False
except rc.RentProblem as problem:
    too_big = 'MB' in str(problem)
os.remove(os.path.join(folder, 'work', 'maps', 'huge.bin'))
check.true('a scene and files over the upload limit are refused before anything is sent', too_big)

# ---------------------------------------------------------------- the rent verb
class RentParsed:
    action, target, remote, cwd, timeout, limit, local, json, out = 'balance', [], None, None, None, None, None, True, None


import io
import contextlib
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    code = rc.main_command(RentParsed, rc.Client(FakeCard()), environment)
check.true('balance prints the money left and exits 0', code == 0 and '12.5' in buffer.getvalue(), 'exit ' + str(code))
RentParsed.action = 'status'
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    code = rc.main_command(RentParsed, rc.Client(FakeCard(idle=1)), environment)
check.true('status prints the card and the health and no key', code == 0 and 'endpoint_health' in buffer.getvalue() and FAKE_KEY not in buffer.getvalue())
buffer = io.StringIO()
error_buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(error_buffer):
    code = rc.main_command(RentParsed, rc.Client(FakeCard()), {})
check.true('no settings gives exit 2 and a sentence on the error channel', code == 2 and 'RUNPOD_API_KEY' in error_buffer.getvalue())

# ---------------------------------------------------------------- part B: the render verb inside Blender
blender = blender_program()
if not blender:
    check.note('part B skipped: Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')
else:
    environment_blender = {name: value for name, value in os.environ.items() if name not in (rc.KEY_NAME, rc.ENDPOINT_NAME, rc.SETTINGS_FILE_NAME, rc.STORE_NAME)}
    environment_blender['BLENDER'] = blender      # the test never sends a real job: the person's own card settings are removed from the environment here
    make_scene = os.path.join(FIXTURES, 'place', 'make_render_scene.py')
    launcher = os.path.join(PLACE_KIT, 'place_command.py')

    def make(name, *options):
        path = os.path.join(folder, name + '.blend')
        done = subprocess.run([blender, '-b', '--disable-autoexec', '--python', make_scene, '--', path, *options], capture_output=True, text=True, timeout=180)
        assert os.path.exists(path), done.stdout[-400:] + done.stderr[-400:]
        return path

    def last_line(done, which='stdout'):
        lines = [line for line in getattr(done, which).splitlines() if line.strip()]
        return lines[-1][:160] if lines else '(no output)'

    def draw(scene_path, views, *extra):
        out = os.path.join(folder, 'out-' + os.path.splitext(os.path.basename(scene_path))[0])
        job = os.path.join(folder, 'job-' + os.path.basename(scene_path) + '.json')
        json.dump({'out_folder': out, 'views': views}, open(job, 'w'))
        done = subprocess.run([sys.executable, '-I', '-B', launcher, 'render', '--scene', scene_path, '--job', job, *extra], capture_output=True, text=True, env=environment_blender, timeout=600)
        return done, out

    tiny_view = [{'name': 'a', 'camera': 'Camera A', 'width': 96, 'height': 64}]
    done, out = draw(make('daylight'), tiny_view)
    log = json.load(open(os.path.join(out, 'a_preview.json'))) if os.path.exists(os.path.join(out, 'a_preview.json')) else {}
    check.true('daylight alone: EEVEE draws a picture and writes its log', done.returncode == 0 and log.get('engine') == 'EEVEE' and os.path.exists(os.path.join(out, 'a_preview.jpg')), last_line(done))
    check.true('the log names the engine, reasons, size, samples, seconds and where', all(key in log for key in ('engine', 'reasons', 'width', 'height', 'samples', 'seconds', 'where', 'mean_luminance')) and log.get('where') == 'local', str(sorted(log)))
    check.true('the picture is not black', (log.get('mean_luminance') or 0) > 0.02, f'mean luminance {log.get("mean_luminance")}')
    done, out = draw(make('lamp', '--lamp'), tiny_view)
    log = json.load(open(os.path.join(out, 'a_preview.json'))) if os.path.exists(os.path.join(out, 'a_preview.json')) else {}
    check.true('a point lamp: the rule picks Cycles and says which lamp', done.returncode == 0 and log.get('engine') == 'CYCLES' and any('Lamp' in reason for reason in log.get('reasons', [])), last_line(done))
    done, out = draw(make('glow', '--glow'), tiny_view)
    log = json.load(open(os.path.join(out, 'a_preview.json'))) if os.path.exists(os.path.join(out, 'a_preview.json')) else {}
    check.true('a glowing material alone (no lamp): the rule picks Cycles', done.returncode == 0 and log.get('engine') == 'CYCLES' and any('glows' in reason for reason in log.get('reasons', [])), last_line(done))
    done, out = draw(make('daylight2'), tiny_view, '--engine', 'cycles')
    log = json.load(open(os.path.join(out, 'a_preview.json'))) if os.path.exists(os.path.join(out, 'a_preview.json')) else {}
    check.true('--engine cycles overrides the rule and the log says so', log.get('engine') == 'CYCLES' and any('forced' in reason for reason in log.get('reasons', [])), str(log.get('reasons')))
    done, out = draw(make('dark', '--dark'), tiny_view)
    check.true('a scene with no light: the render says the picture is nearly black and fails', done.returncode == 1 and 'nearly black' in done.stdout, last_line(done))
    done, out = draw(make('nocamera', '--no-camera'), [{'name': 'a', 'width': 96, 'height': 64}])
    check.true('no camera: the render says so plainly and fails', done.returncode == 1 and 'no camera' in done.stdout, last_line(done))
    done, out = draw(make('daylight3'), [{'name': 'a', 'camera': 'Not There'}])
    check.true('a camera name that does not exist is named in the failure', done.returncode == 1 and 'Not There' in done.stdout)
    done = subprocess.run([sys.executable, '-I', '-B', launcher, 'render', '--job', os.path.join(folder, 'no-such-job.json')], capture_output=True, text=True, env=environment_blender, timeout=120)
    check.true('a missing job file exits 2 with a sentence', done.returncode == 2 and 'job file' in done.stdout, last_line(done))
    # a view that says exactly which pictures to draw: one final at the given size and no preview beside it
    done, out = draw(make('kinds_final'), [{'name': 'a', 'camera': 'Camera A', 'width': 96, 'height': 64, 'kinds': ['final'], 'engine': 'eevee'}])
    final_log = json.load(open(os.path.join(out, 'a_final.json'))) if os.path.exists(os.path.join(out, 'a_final.json')) else {}
    check.true('"kinds": ["final"] draws only the final picture, at the size given', done.returncode == 0 and final_log.get('width') == 96 and final_log.get('height') == 64 and final_log.get('kind') == 'final'
               and os.path.exists(os.path.join(out, 'a_final.png')), last_line(done))   # a final is a PNG, a preview a JPEG
    check.true('"kinds": ["final"] draws no preview beside it', not os.path.exists(os.path.join(out, 'a_preview.jpg')) and not os.path.exists(os.path.join(out, 'a_preview.json')), str(sorted(os.listdir(out))))
    done, out = draw(make('kinds_name'), [{'name': 'closeup', 'camera': 'Camera A', 'width': 96, 'height': 64, 'kinds': ['close_up'], 'engine': 'eevee'}])
    check.true('a view called "closeup" drawn as a close-up is saved as closeup.*, not closeup_closeup.*', os.path.exists(os.path.join(out, 'closeup.jpg')) and not os.path.exists(os.path.join(out, 'closeup_closeup.jpg')),
               str(sorted(os.listdir(out))) if os.path.isdir(out) else 'no output folder')
    done, out = draw(make('kinds_both'), [{'name': 'b', 'camera': 'Camera A', 'width': 96, 'height': 64, 'kinds': ['preview', 'final'], 'engine': 'eevee'}])
    check.true('"kinds": ["preview", "final"] draws both, each in its own file', os.path.exists(os.path.join(out, 'b_preview.jpg')) and os.path.exists(os.path.join(out, 'b_final.png')), str(sorted(os.listdir(out))) if os.path.isdir(out) else 'no output folder')
    done, out = draw(make('daylight4'), tiny_view, '--where', 'rented')
    check.true('--where rented with no settings exits 2 and names what to set', done.returncode == 2 and 'RUNPOD_API_KEY' in done.stderr, last_line(done, 'stderr'))
check.finish()
