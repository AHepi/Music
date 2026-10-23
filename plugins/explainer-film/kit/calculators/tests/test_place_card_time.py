"""What this does: tests the CARD-TIME LEDGER and the ALLOWANCE (place_kit/card_time.py) and the way the rented-card client uses them, in plain Python (no Blender, no network).
What it proves:
  1. The house numbers are there and say what the notes say: a builder 10 minutes, a fixer 5, a planner none, an unknown role the default; card seconds are work + wake-up + the idle tail.
  2. The ledger: it is a text file with one line for each job; a missing file reads as empty; a line that is not JSON is reported and skipped (never silently); the same job id is never written
     twice; where it lives is the option, else the environment, else the folder you run in.
  3. The gate: OK below 80 percent, a warning above it, a REFUSAL past the allowance (with the plain sentence that says what to do), an override only with a written reason of at least 15 letters
     and only up to half again, never for a role with no card time, and never past the whole job's total (the person's own cap, written by `card-time start`).
  4. The batch rule: the first batch for a change is fine, the second is "the last one", the third is refused unless a reason is written.
  5. The verb `card-time`: show, check, add (not twice), start; exit 1 for a refusal and 2 for an unusable input.
  6. The rented-card client: `rent status` writes its small job's billed seconds into the ledger; `rent run` for a helper that has used up its allowance is refused BEFORE any call is made; a finished
     job seen by `rent wait` is logged once.
Run: python3 kit/calculators/tests/test_place_card_time.py
"""
import atexit
import json
import os
import shutil
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT  # noqa: E402

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
folder = tempfile.mkdtemp(prefix='place-card-time-test-')
atexit.register(shutil.rmtree, folder, True)      # the test's own scratch folder goes when it ends
os.environ.pop('PLACE_CARD_LEDGER', None)
os.environ.pop('PLACE_HELPER', None)
os.environ.pop('PLACE_HELPER_ROLE', None)

from place_kit import card_time as ct  # noqa: E402
from place_kit import house_numbers as numbers  # noqa: E402
from place_kit.render import client as rc  # noqa: E402

check = Checker('place card time: the ledger, the allowance and the batch rule')
lines = []


def say(text):
    lines.append(text)


def say_all(text):
    lines.append(text)


# ---------------------------------------------------------------- 1. the numbers
check.equal('a builder may use 600 s (10 minutes)', ct.allowance_seconds('builder'), 600.0, recorded='film-settings.json place_card_time.allowance_minutes.builder')
check.equal('a fixer may use 300 s (5 minutes)', ct.allowance_seconds('fixer'), 300.0)
check.equal('a planner may use none', ct.allowance_seconds('planner'), 0.0)
check.equal('a role nobody has heard of gets the default (5 minutes)', ct.allowance_seconds('wizard'), 300.0)
pieces = ct.card_seconds_of(40000, 22000)
check.equal('card seconds are work + wake-up + the idle tail (40 + 22 + 5)', pieces['card_seconds'], 67.0, proves='a number is never too small: the wake-up and the tail are counted')
check.true('the price made from seconds says it is an estimate and not a bill', 'not a bill' in ct.dollars_text(100), ct.dollars_text(100))

# ---------------------------------------------------------------- 2. the ledger
ledger = os.path.join(folder, 'ledger.jsonl')
check.equal('a missing ledger reads as empty', ct.read_ledger(ledger), ([], []))
check.equal('the ledger is where --ledger says', ct.ledger_path(ledger, {}), os.path.abspath(ledger))
check.equal('...else where PLACE_CARD_LEDGER says', ct.ledger_path(None, {ct.ENV_LEDGER: ledger}), os.path.abspath(ledger))
check.equal('...else card-time-ledger.jsonl in the folder you run in', os.path.basename(ct.ledger_path(None, {})), ct.LEDGER_NAME)
check.equal('who: the options win over the environment', ct.who(types.SimpleNamespace(helper='a', role='fixer'), {ct.ENV_HELPER: 'b', ct.ENV_ROLE: 'builder'}), ('a', 'fixer'))
check.equal('...then the environment', ct.who(types.SimpleNamespace(), {ct.ENV_HELPER: 'b', ct.ENV_ROLE: 'builder'}), ('b', 'builder'))
check.equal('...then the plain defaults', ct.who(types.SimpleNamespace(), {}), ('unnamed-helper', 'default'))
first = ct.log_job(ledger, 'walls', 'builder', {'id': 'job-1', 'billed_work_ms': 40000, 'wake_up_ms': 22000, 'runpod_status': 'COMPLETED'}, 'a test job')
again = ct.log_job(ledger, 'walls', 'builder', {'id': 'job-1', 'billed_work_ms': 40000, 'wake_up_ms': 22000, 'runpod_status': 'COMPLETED'}, 'a test job')
entries, problems = ct.read_ledger(ledger)
check.true('a job is written once with its billed seconds, and the same job id is never written twice', first and again is None and len(entries) == 1 and entries[0]['card_seconds'] == 67.0 and entries[0]['measured'] is True,
           f'{len(entries)} entry, {entries[0]["card_seconds"]} s')
with open(ledger, 'a') as handle:
    handle.write('this line is not JSON\n')
entries, problems = ct.read_ledger(ledger)
check.true('a line that is not JSON is reported and skipped, never silently', len(entries) == 1 and len(problems) == 1 and 'not JSON' in problems[0], problems[0] if problems else 'no problem reported')
check.equal('used seconds are the helper\'s own', (ct.used_seconds(entries, 'walls'), ct.used_seconds(entries, 'someone else')), (67.0, 0.0))
small = ct.log_small_jobs(ledger, 'walls', 'builder', [{'id': 'a', 'work_ms': 1500, 'wake_up_ms': 700}, {'id': 'b', 'work_ms': 500, 'wake_up_ms': 0}], 'set-up')
check.true('small jobs are written as ONE entry (work, wake-up and one idle tail)', small['card_seconds'] == round(2.0 + 0.7 + 5, 1) and small['jobs'] == 2, f'{small["card_seconds"]} s for {small["jobs"]} jobs')
estimate = ct.log_wall_clock(ledger, 'walls', 'builder', 12.0, 'uploads (wall clock)')
check.true('a step a client cannot measure is counted from the wall clock and marked as an estimate', estimate['measured'] is False and estimate['card_seconds'] == 17.0 and 'wall clock' in estimate['estimate_note'])

# ---------------------------------------------------------------- 3. the gate
fresh = []
ok = ct.check(fresh, 'x', 'builder', 100)
check.equal('a fresh builder asking for 100 s is OK', ok['status'], 'ok')
used_480 = [{'kind': 'job', 'helper': 'x', 'card_seconds': 480.0}]
warn = ct.check(used_480, 'x', 'builder', 0)
check.true('at 80 percent of the allowance there is a warning', warn['status'] == 'warn' and 'LOOK' in warn['lines'][0], warn['lines'][0])
refuse = ct.check(used_480, 'x', 'builder', 200)
check.true('past the allowance the step is REFUSED, and the sentence says nothing was sent and how to go over', refuse['status'] == 'refuse' and 'nothing was sent' in refuse['lines'][0] and '--over-allowance' in refuse['lines'][0],
           refuse['lines'][0][:200])
short = ct.check(used_480, 'x', 'builder', 200, 'too short')
check.equal('a reason under 15 letters does not open the door', short['status'], 'refuse')
reasoned = ct.check(used_480, 'x', 'builder', 200, 'the first batch missed the wall, one more batch is needed')
check.true('a written reason goes over by up to half again, and it is said to be an override', reasoned['status'] == 'warn' and reasoned['override'] is True and 'OVER THE ALLOWANCE' in reasoned['lines'][0], reasoned['lines'][0][:160])
too_far = ct.check(used_480, 'x', 'builder', 500, 'the first batch missed the wall, one more batch is needed')
check.true('even with a reason nothing passes the allowance by more than half again', too_far['status'] == 'refuse' and 'person' in too_far['lines'][0], too_far['lines'][0][:160])
planner = ct.check([], 'p', 'planner', 0)
check.true('a planner has no card time, even for a free-looking step', planner['status'] == 'refuse' and 'no card time' in planner['lines'][0])
capped = [{'kind': 'start', 'team_minutes': 5.0}, {'kind': 'job', 'helper': 'a', 'card_seconds': 250.0}]
team = ct.check(capped, 'b', 'builder', 100, 'a long enough reason to try it anyway')
check.true('the whole job\'s total (the person\'s own cap) cannot be passed, reason or not', team['status'] == 'refuse' and 'whole job' in team['lines'][0], team['lines'][0][:160])
check.equal('without a start entry the house total (60 minutes) is used', ct.team_total_seconds([]), 3600.0)

# ---------------------------------------------------------------- 4. the batch rule
batch = lambda n: [{'kind': 'batch', 'helper': 'x', 'change': 'moss'}] * n  # noqa: E731
check.true('the first batch for a change is fine', ct.check_batch(batch(0), 'x', 'moss')['status'] == 'ok' and ct.check_batch(batch(0), 'x', 'moss')['number'] == 1)
second = ct.check_batch(batch(1), 'x', 'moss')
check.true('the second batch is allowed and called the last one', second['status'] == 'warn' and second['number'] == 2 and 'the last one' in second['lines'][0], second['lines'][0])
third = ct.check_batch(batch(2), 'x', 'moss')
check.true('the third batch for the same change is refused (one batch, look, at most one more)', third['status'] == 'refuse' and 'at most one more' in third['lines'][0], third['lines'][0][:140])
check.equal('...unless a reason is written', ct.check_batch(batch(2), 'x', 'moss', 'the second batch lost the best version')['status'], 'warn')
check.equal('another change starts again at batch one', ct.check_batch(batch(2), 'x', 'dirt')['number'], 1)

# ---------------------------------------------------------------- 5. the verb
verb_ledger = os.path.join(folder, 'verb-ledger.jsonl')
def namespace(**fields):
    base = {'ledger': verb_ledger, 'helper': 'verb-helper', 'role': 'fixer', 'action': 'show'}
    base.update(fields)
    return types.SimpleNamespace(**base)


lines.clear()
code = ct.main_command(namespace(action='add', work_seconds=30.0, wake_up_seconds=20.0, job_id='by-hand', what='a job I ran by hand'), {}, say)
check.true('add logs a job you ran by hand (30 + 20 + 5 = 55 s)', code == 0 and '55' in lines[-1], lines[-1])
lines.clear()
ct.main_command(namespace(action='add', work_seconds=30.0, job_id='by-hand'), {}, say)
check.true('...and not the same job twice', 'already in the ledger' in lines[-1])
check.equal('add without work seconds is an unusable input (exit 2)', ct.main_command(namespace(action='add'), {}, say), 2)
lines.clear()
check.equal('check says exit 1 for a refusal (a fixer with 55 s used asks for 400 s)', ct.main_command(namespace(action='check', estimate_seconds=400.0), {}, say), 1)
check.equal('check says exit 0 when it fits', ct.main_command(namespace(action='check', estimate_seconds=50.0), {}, say), 0)
lines.clear()
ct.main_command(namespace(action='show'), {}, say)
shown = '\n'.join(lines)
check.true('show names the ledger, the whole job, the helper, the allowance and what is left', verb_ledger in shown and 'verb-helper (role fixer)' in shown and 'left' in shown and 'The whole job' in shown, shown[:300])
lines.clear()
check.equal('start writes the person\'s total cap', ct.main_command(namespace(action='start', team_minutes=3.0), {}, say), 0)
check.equal('...and the gate then uses it (180 s)', ct.team_total_seconds(ct.read_ledger(verb_ledger)[0]), 180.0)
check.equal('a role that does not exist is an unusable input (exit 2)', ct.main_command(namespace(role='wizard'), {}, say), 2)

# ---------------------------------------------------------------- 6. the rented-card client
FAKE_KEY = 'rp' + 'a_' + 'k' * 24
FAKE_ENDPOINT = 'endpoint' + 'x' * 14


class FakeTransport:
    """A transport that answers every small job at once and notes every call."""

    def __init__(self):
        self.calls = []

    def call(self, method, path, body=None, attempts=1):
        self.calls.append((method, path))
        if path == '/runsync':
            return {'id': f'small{len(self.calls)}', 'status': 'COMPLETED', 'output': {'gpu': 'fake'}, 'executionTime': 1500, 'delayTime': 700}
        if path == '/health':
            return {'workers': {'idle': 1}}
        if path.startswith('/status/'):
            return {'id': path.split('/')[-1], 'status': 'COMPLETED', 'output': {'return_code': 0, 'seconds': 3.0}, 'executionTime': 3000, 'delayTime': 21000}
        if path == '/run':
            return {'id': 'jobrun1', 'status': 'IN_QUEUE'}
        raise AssertionError('unexpected call ' + path)


environment = {rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT}
client_ledger = os.path.join(folder, 'client-ledger.jsonl')
status_args = types.SimpleNamespace(action='status', target=[], out=None, json=False, ledger=client_ledger, helper='walls', role='builder', over_allowance=None)
transport = FakeTransport()
code = rc.main_command(status_args, client=rc.Client(transport), environ=environment)
entries, _ = ct.read_ledger(client_ledger)
small_entries = [e for e in entries if e['kind'] == 'small']
check.true('`rent status` writes the billed seconds of its small job into the ledger (1.5 + 0.7 + 5)', code == 0 and len(small_entries) == 1 and small_entries[0]['card_seconds'] == 7.2, f'{[e["card_seconds"] for e in small_entries]}')
planner_args = types.SimpleNamespace(action='run', target=['echo hi'], out=None, json=False, cwd=None, timeout=None, ledger=client_ledger, helper='a-planner', role='planner', over_allowance=None)
transport = FakeTransport()
code = rc.main_command(planner_args, client=rc.Client(transport), environ=environment)
check.true('`rent run` for a role with no card time is refused BEFORE any call is made (exit 1, the fake service saw nothing)', code == 1 and transport.calls == [], f'exit {code}, {len(transport.calls)} call(s)')
wait_args = types.SimpleNamespace(action='wait', target=['jobrun1'], out=None, json=False, limit=60, ledger=client_ledger, helper='walls', role='builder', over_allowance=None)
rc.main_command(wait_args, client=rc.Client(FakeTransport(), sleep=lambda s: None), environ=environment)
rc.main_command(wait_args, client=rc.Client(FakeTransport(), sleep=lambda s: None), environ=environment)
jobs = [e for e in ct.read_ledger(client_ledger)[0] if e['kind'] == 'job']
check.true('a finished job seen by `rent wait` is logged ONCE with its wake-up and work (21 + 3 + 5 = 29 s)', len(jobs) == 1 and jobs[0]['card_seconds'] == 29.0, f'{len(jobs)} job entry')
missing_settings = types.SimpleNamespace(action='status', target=[], out=None, json=False, ledger=os.path.join(folder, 'never.jsonl'), helper='x', role='builder', over_allowance=None)
code = rc.main_command(missing_settings, environ={})
check.true('missing settings give exit 2 and write no ledger at all', code == 2 and not os.path.exists(os.path.join(folder, 'never.jsonl')))
check.true('no ledger was written into the kit folder or the current folder by this test', not os.path.exists(os.path.join(PLACE_KIT, ct.LEDGER_NAME)) and not os.path.exists(os.path.join(os.getcwd(), ct.LEDGER_NAME)))
check.true('no key or endpoint id is in any ledger written here', all(FAKE_KEY not in open(path).read() and FAKE_ENDPOINT not in open(path).read() for path in (ledger, verb_ledger, client_ledger)))

check.finish()
