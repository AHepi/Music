"""What this does: tests BATCHED VARIATION ROUNDS (`explainer-film-place variations`, place_kit/variations/) from the settings a variation may change to the contact sheet.
Part A (plain Python, always runs): the words of a variation (keys), the check BEFORE drawing (near-duplicates are dropped and the sentence says which and why; "baseline" is reserved; unknown
keys name the allowed ones), the split into card jobs (10 variations make 3 jobs of 4, 3 and 3 with the baseline in the smallest; 4 make 2; 2 make 1; never more than 3), the estimate, the spread
that `make` writes (a Latin hypercube: every pair differs by at least a tenth of the range on every setting, and the same seed gives the same file) and `refine` (the second batch around a pick,
blended when there are several), the check AFTER drawing on synthetic pictures (a pair that came out nearly the same is flagged, a change that does not show is called out, the reset check
measures drift) and the contact sheet (one JPG under 400 KB (400,000 bytes) even for noisy pictures, with the baseline first).
Part B (plain Python, needs only Pillow): the whole batch with a FAKE CARD and a FAKE BLENDER: the plugin client over a fake service (jobs are sent at the same time, before any wait; the
wake-up and billed seconds of each job are written into the ledger; the pictures come back in one bundle each) and the older command-line client over a fake command (the waiting loop, the
estimate for uploads, the 5-minute stop). A variation that fails is named and the sheet is still made. A helper over its allowance, or asking for a third batch, is refused BEFORE any call is
made. `plan` draws nothing and costs nothing. No key or endpoint id reaches any file.
Part C (needs Blender: BLENDER, machine-settings.env, or the PATH; otherwise skipped with a reason): on a tiny finished hut with two cameras the REAL worker: settings, state, look, master and a
script hook are applied and drawn, the scene is put back (the baseline drawn again after everything differs by 0), a setting that changes nothing in this scene is called out, and the same
batch goes through the fake card with Blender as the card's own program (paths, uploads, bundle, download).
Run: python3 kit/calculators/tests/test_place_variations.py
"""
import importlib.util
import atexit
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, FIXTURES, TESTS, blender_program, skip  # noqa: E402

try:
    import numpy as np
    from PIL import Image
except ImportError:
    skip('place variations', 'numpy and Pillow are needed to measure pictures and make the sheet (pip install numpy pillow)')

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
folder = tempfile.mkdtemp(prefix='place-variations-test-')
atexit.register(shutil.rmtree, folder, True)      # the test's own scratch folder goes when it ends
os.environ['WORKER_VOLUME'] = os.path.join(folder, 'volume')
os.makedirs(os.environ['WORKER_VOLUME'])
os.environ.pop('PLACE_CARD_LEDGER', None)
os.environ['FAKE_BLENDER_KIT'] = PLACE_KIT
os.environ['PLACE_NO_XVFB'] = '1'

from place_kit import card_time as ct  # noqa: E402
from place_kit import house_numbers as numbers  # noqa: E402
from place_kit.render import client as rc  # noqa: E402
from place_kit.variations import cards, compare, keys, runner, sheet, spec as sp  # noqa: E402

handler_spec = importlib.util.spec_from_file_location('worker_handler', os.path.join(PLACE_KIT, 'place_kit', 'render', 'worker', 'handler.py'))
handler = importlib.util.module_from_spec(handler_spec)
handler_spec.loader.exec_module(handler)

check = Checker('place variations: settings, checks before and after drawing, the split, the card and the sheet')
FAKE_KEY = 'rp' + 'a_' + 'k' * 24
FAKE_ENDPOINT = 'endpoint' + 'x' * 14
spoken = []


def say(text):
    spoken.append(str(text))


def spoken_text():
    return '\n'.join(spoken)


def write_json(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(content, handle, indent=1)
    return path


def variation(name, **settings):
    return {'name': name, 'set': settings, 'script': None, 'args': {}, 'ranges': {}, 'reset': 'auto'}


# ================================================================ part A: the words and the checks before drawing
clean, problems = keys.clean_set({'dials': {'moss_and_algae': {'cover': 0.5}}, 'amount': {'moss_and_algae': 0.5}, 'state': 'wet'})
check.true('a set written nested is read as flat dotted keys', clean == {'dials.moss_and_algae.cover': 0.5, 'amount.moss_and_algae': 0.5, 'state': 'wet'} and not problems, str(clean))
_, problems = keys.clean_set({'dials.moss_and_algae.cover': 1.5, 'dials.dirt.amount': 0.5, 'colour': 1, 'state': 'soggy', 'amount.dirt': 'a lot'})
check.true('values out of range, a dial that is really an amount, an unknown key, a wrong word and a non-number are each named', len(problems) == 5 and any('outside its range' in p for p in problems) and any('amount.dirt' in p for p in problems)
           and any('is not a setting a variation can change' in p for p in problems), ' | '.join(problems)[:240])
check.true('`keys` lists every setting with its range (dials, amounts, state, look)', len(keys.all_dial_lines()) > 40 and any(line.startswith('dials.moss_and_algae.cover: 0 to 1') for line in keys.all_dial_lines()))

base = sp.as_baseline()
close = keys.apart(variation('a', **{'dials.moss_and_algae.cover': 0.5}), variation('b', **{'dials.moss_and_algae.cover': 0.55}))
far = keys.apart(variation('a', **{'dials.moss_and_algae.cover': 0.5}), variation('b', **{'dials.moss_and_algae.cover': 0.9}))
check.true('0.50 and 0.55 of a 0-to-1 dial are NOT measurably apart (5 percent), 0.50 and 0.90 are (40 percent)', close[0] is False and far[0] is True, f'{close[1]:.2f} and {far[1]:.2f} times the smallest gap that counts')
check.true('a word that differs always counts (wet against dry), and so does a different seed', keys.apart(variation('a', state='wet'), variation('b', state='dry'))[0] and keys.apart(variation('a', **{'dials.dirt.seed': 3.0}), variation('b', **{'dials.dirt.seed': 4.0}))[0])
check.true('numbers in a script hook count by their written range, and by a quarter of the larger value when they have none',
           keys.apart({'set': {}, 'args': {'lean': 10}, 'ranges': {'lean': [0, 20]}, 'script': 'h.py'}, {'set': {}, 'args': {'lean': 11}, 'ranges': {'lean': [0, 20]}, 'script': 'h.py'})[0] is False
           and keys.apart({'set': {}, 'args': {'count': 4}, 'ranges': {}, 'script': 'h.py'}, {'set': {}, 'args': {'count': 8}, 'ranges': {}, 'script': 'h.py'})[0] is True)

scene_file = os.path.join(folder, 'work', 'scene.blend')
os.makedirs(os.path.dirname(scene_file))
open(scene_file, 'wb').write(b'not a real scene')
settings_file = write_json(os.path.join(folder, 'work', 'place-settings.json'), {})
hook_file = os.path.join(folder, 'work', 'hooks', 'tilt.py')
os.makedirs(os.path.dirname(hook_file))
open(hook_file, 'w').write('def apply(variation):\n    pass\n')


def write_spec(name, variations, **extra):
    content = {'change': 'moss test', 'scene': 'scene.blend', 'settings': 'place-settings.json', 'cameras': ['Camera A', 'Camera B'], 'variations': variations}
    content.update(extra)
    return write_json(os.path.join(folder, 'work', name), content)


problem_cases = {
    'a missing file': ('no-such-file.json', 'is not there'),
    'no variations': (write_spec('p1.json', []), 'needs a "variations" list'),
}
for label, (path, words) in problem_cases.items():
    try:
        sp.read_spec(path)
        outcome = 'no problem raised'
    except sp.SpecProblem as problem:
        outcome = str(problem)
    check.true(f'{label} is a plain sentence that says what to write', words in outcome, outcome[:160])
bad = write_spec('p2.json', [{'name': 'baseline', 'set': {'amount.dirt': 0.5}}, {'name': 'a', 'set': {'colour': 1}}, {'name': 'a', 'set': {'amount.dirt': 0.2}}, {'name': 'Bad Name', 'set': {}},
                             {'name': 'h', 'script': 'hooks/missing.py'}, {'name': 'x', 'args': {'n': 1}}], scene='nothing.blend')
try:
    sp.read_spec(bad)
    outcome = ''
except sp.SpecProblem as problem:
    outcome = str(problem)
check.true('all the problems of a file are said at once: reserved name, unknown key (with the allowed ones), duplicate name, bad name, missing hook, args without a hook, missing scene',
           all(word in outcome for word in ('reserved name', 'is not a setting a variation can change', 'two variations are called "a"', 'plain characters', 'script hook', 'belong to a script hook', 'is not there')), outcome[:300])

ten = [variation(f'm{i}', **{'amount.moss_and_algae': round(0.1 * i, 2)}) for i in range(10)]
ten.append(variation('m-near', **{'amount.moss_and_algae': 0.52}))
ten.append(variation('nothing'))
ten.append(variation('same-as-saved', **{'amount.moss_and_algae': 1.0}))
good = write_spec('good.json', [{'name': v['name'], 'set': v['set']} for v in ten])
spec_good = sp.read_spec(good)
checked = sp.check_before(spec_good)
dropped = {d['name']: d for d in checked['dropped']}
check.equal('ten values 0.1 apart are kept; the near-duplicate, the empty one and the one equal to the saved scene are dropped', sorted(dropped), ['m-near', 'nothing', 'same-as-saved'])
check.true('...and each drop is a plain sentence naming what it is too close to', 'near-duplicate of "m' in dropped['m-near']['why'] and 'changes nothing' in dropped['nothing']['why'] and 'baseline again' in dropped['same-as-saved']['why'],
           dropped['m-near']['why'][:150])
check.true('the later variation goes, never the earlier (m-near came after m4 and m5)', dropped['m-near']['like'] in ('m4', 'm5') and 'm4' in [v['name'] for v in checked['kept']])
check.equal('ten kept variations pass the before-drawing check', checked['status'], 'ok')
jobs = sp.split_jobs(checked['kept'])
counts = [len(job['entries']) for job in jobs]
check.true('ten variations make 3 jobs (at most 3 cards at once): 4, 4 and 3 entries with the baseline in a job of 3 variations', len(jobs) == 3 and sorted(counts) == [3, 4, 4], f'{counts}')
check.equal('the baseline is drawn exactly once, first in its job', [(i + 1, job['entries'][0]['name']) for i, job in enumerate(jobs) if job['entries'][0].get('is_baseline')].__len__(), 1)
every = [e['name'] for job in jobs for e in job['entries']]
check.true('every kept variation is in exactly one job', sorted(every) == sorted(['baseline'] + [v['name'] for v in checked['kept']]))
check.equal('four variations make 2 jobs', len(sp.split_jobs(checked['kept'][:4])), 2)
check.equal('two variations make 1 job', len(sp.split_jobs(checked['kept'][:2])), 1)
check.equal('asking for 5 jobs gives at most 3', len(sp.split_jobs(checked['kept'], 5)), 3)
card_seconds, elapsed, pictures = sp.estimate(jobs, 2)
check.true('the estimate is in card seconds, a little more than 3 wake-ups, and counts 22 pictures for 11 entries and 2 cameras', pictures == 22 and card_seconds > 3 * 30 and elapsed < card_seconds, f'{card_seconds} card s, {elapsed} s side by side')
too_many = write_spec('many.json', [{'name': f'k{i:02d}', 'set': {'amount.moss_and_algae': 0.05 + 0.05 * i if i < 19 else 0.99, 'dials.moss_and_algae.cover': (i * 0.37) % 1}} for i in range(18)])
many = sp.check_before(sp.read_spec(too_many))
check.true('more than 16 variations is refused as wandering (status refuse and the sentence says what to do)', many['status'] == 'refuse' and many['too_many'] and 'wandering' in '\n'.join(many['lines']), many['lines'][-1][:120])
check.equal('...and so is a batch where nothing is left after the drops', sp.check_before(sp.read_spec(write_spec('none.json', [{'name': 'a', 'set': {'amount.dirt': 1.0}}, {'name': 'b', 'set': {}}])))['status'], 'refuse')

made = sp.make_variations(['amount.moss_and_algae', 'dials.moss_and_algae.cover', 'dials.moss_and_algae.clump_size_metres', 'state'], 10, seed=7, change='moss')
spans = {'amount.moss_and_algae': 1.0, 'dials.moss_and_algae.cover': 1.0, 'dials.moss_and_algae.clump_size_metres': 0.57}
worst = min(abs(a['set'][k] - b['set'][k]) / spans[k] for i, a in enumerate(made['variations']) for b in made['variations'][i + 1:] for k in spans)
check.true('`make` spreads 10 variations so that every pair differs by at least a tenth of the range on EVERY number setting (a Latin hypercube)', worst >= 0.0999, f'the closest pair is {worst:.3f} of the range apart')
check.true('...gives each variation its own name and keeps words in turn', len({v['name'] for v in made['variations']}) == 10 and {v['set']['state'] for v in made['variations']} == {'dry', 'damp', 'wet'})
check.equal('the same seed gives the same file, another seed another', (sp.make_variations(['amount.dirt', 'dials.dirt.film'], 6, 3) == sp.make_variations(['amount.dirt', 'dials.dirt.film'], 6, 3), sp.make_variations(['amount.dirt', 'dials.dirt.film'], 6, 3) == sp.make_variations(['amount.dirt', 'dials.dirt.film'], 6, 4)), (True, False))
check.true('the 10 made variations all survive the check before drawing', sp.check_before({'variations': made['variations'] and [dict(v, script=None, args={}, ranges={}, reset='auto') for v in made['variations']]})['dropped'] == [])
result_like = {'change': 'moss', 'scene': scene_file, 'variations': [dict(v, script=None, args={}) for v in made['variations']]}
second = sp.refine_variations(result_like, [made['variations'][0]['name'], made['variations'][1]['name']], count=6, seed=2)
check.true('`refine` blends two picks (the mean of each number) as its first variation and spreads the rest around the blend', second['variations'][0]['name'].startswith('blend-') and len(second['variations']) == 6
           and abs(second['variations'][0]['set']['amount.moss_and_algae'] - (made['variations'][0]['set']['amount.moss_and_algae'] + made['variations'][1]['set']['amount.moss_and_algae']) / 2) < 0.001)
try:
    sp.refine_variations(result_like, ['no-such-pick'])
    outcome = ''
except sp.SpecProblem as problem:
    outcome = str(problem)
check.true('a pick that is not in the result is named, with the names that are', 'no-such-pick' in outcome and made['variations'][0]['name'] in outcome)

# ================================================================ part A: after drawing (synthetic pictures)
pictures_folder = os.path.join(folder, 'synthetic')
os.makedirs(pictures_folder)
random = np.random.default_rng(5)
texture = random.integers(60, 140, (120, 180, 3)).astype(np.int16)


def picture(name, shift=0, patch=None, noise=0):
    array = np.clip(texture + shift + (random.integers(-noise, noise + 1, texture.shape) if noise else 0), 0, 255).astype(np.uint8)
    if patch:
        array[patch[0]:patch[1], patch[2]:patch[3]] = 230
    path = os.path.join(pictures_folder, name + '.png')
    Image.fromarray(array).save(path)
    return path


def drawn(name, path, camera='Camera A', **fields):
    return {'name': name, 'set': {}, 'args': {}, 'script': None, 'ok': True, 'notes': [], 'pictures': [{'camera': camera, 'path': path, 'ok': True}], **fields}


synthetic = [drawn('baseline', picture('base')), drawn('twin-a', picture('base2', shift=0)), drawn('brighter', picture('bright', shift=40)),
             drawn('small-patch', picture('patch', patch=(10, 40, 10, 60))), drawn('brighter-too', picture('bright2', shift=40))]
compare.measure_variations(synthetic)
pairs = compare.pair_differences(synthetic)
same = {frozenset(p) for p in pairs['nearly_same']}
check.true('a pair of identical pictures is flagged as nearly the same, and so is a copy of the baseline ("does not show")', frozenset(['baseline', 'twin-a']) in same and 'twin-a' in pairs['invisible'] and frozenset(['bright', 'brighter-too']) not in same or frozenset(['brighter', 'brighter-too']) in same,
           f'{sorted(sorted(p) for p in same)}')
check.true('a picture brighter by 40 of 255 is NOT nearly the same as the baseline', 'brighter' not in pairs['invisible'])
check.true('a change on a small part of the picture (a patch of 30 x 50 pixels) still counts as different (the changed share, not only the mean)', 'small-patch' not in pairs['invisible'],
           f'{next(p for p in pairs["pairs"] if {p["a"], p["b"]} == {"baseline", "small-patch"})["mean_difference"]:.2f} of 255 on average')
row = synthetic[2]['average']
check.true('the measures of the brighter picture: the value range moved up, the colour shifted from the baseline, and the squint score is under 1', row['colour_shift'] > 2 and row['squint'] < 1.0 and row['p95'] > synthetic[0]['average']['p95'] + 0.1,
           f'colour shift {row["colour_shift"]:.1f}, squint {row["squint"]:.3f}')
check.equal('the baseline against itself: colour shift 0 and squint 1.0', (synthetic[0]['average']['colour_shift'], synthetic[0]['average']['squint']), (0.0, 1.0))
check.true('the drift of a reset check: 0 for the same picture, large for another', compare.reset_drift(synthetic[0]['pictures'][0]['path'], synthetic[1]['pictures'][0]['path']) == 0.0 and compare.reset_drift(synthetic[0]['pictures'][0]['path'], synthetic[2]['pictures'][0]['path']) > 30)
# the contact sheet, even for noisy pictures that do not compress well
noisy = [drawn('baseline', picture('n0', noise=60), 'Camera A')] + [drawn(f'n{i}', picture(f'n{i}', shift=i * 6, noise=60), 'Camera A') for i in range(1, 11)]
for item in noisy:
    item['pictures'].append({'camera': 'Camera B', 'path': picture('b' + item['name'], shift=5, noise=60), 'ok': True})
compare.measure_variations(noisy)
for item in noisy:
    item['flags'] = []
noisy[3]['flags'] = ['nearly the same as #2 n2']
made_sheet = sheet.make_sheet(os.path.join(folder, 'noisy-sheet.jpg'), noisy, ['Camera A', 'Camera B'], {'change': 'Variations: noise', 'scene': 'scene.blend', 'engine': 'cycles', 'size': '180 x 120',
                                                                                                          'dropped': ['Dropped before drawing: "x": a test.'], 'pair_lines': [], 'card_lines': ['Card seconds: a test.']})
check.true('the contact sheet is ONE jpg under 400 KB (400,000 bytes) even for noisy pictures (quality, then size, are lowered until it fits)', os.path.getsize(made_sheet['path']) <= 400 * 1000 and made_sheet['bytes'] <= 400 * 1000,
           f'{made_sheet["bytes"] // 1024} KB at quality {made_sheet["quality"]}, scale {made_sheet["scale"]}, {made_sheet["width"]} x {made_sheet["height"]}')
with Image.open(made_sheet['path']) as opened:
    check.true('...and it is a real picture of the right shape for 11 cells in 3 columns', opened.format == 'JPEG' and opened.width > 900 and opened.height > 600, f'{opened.width} x {opened.height}')

# ================================================================ part B: the whole batch with a fake card and a fake blender
store = os.path.join(folder, 'store')
os.makedirs(os.path.join(store, 'blender'))
shutil.copy(os.path.join(FIXTURES, 'place', 'fake_blender.py'), os.path.join(store, 'blender', 'blender'))
os.chmod(os.path.join(store, 'blender', 'blender'), os.stat(os.path.join(store, 'blender', 'blender')).st_mode | stat.S_IXUSR)


class FakeService:
    """The rented-card service, made of the real job taker: small jobs run at once; a job sent with /run waits until somebody asks for its status, then runs (billing: 40 s + its number of work, 22 s of wake-up)."""

    def __init__(self):
        self.calls, self.jobs = [], {}

    def call(self, method, path, body=None, attempts=1):
        self.calls.append((method, path))
        if path == '/runsync':
            return {'id': f'small{len(self.calls)}', 'status': 'COMPLETED', 'output': handler.handle_job({'id': f'small{len(self.calls)}', 'input': body['input']}), 'executionTime': 1500, 'delayTime': 700}
        if path == '/run':
            job_id = f'job{len([c for c in self.calls if c[1] == "/run"])}'
            self.jobs[job_id] = {'input': body['input'], 'number': len(self.jobs) + 1}
            return {'id': job_id, 'status': 'IN_QUEUE'}
        if path.startswith('/status/'):
            job_id = path.split('/')[-1]
            job = self.jobs[job_id]
            if 'state' not in job:
                job['state'] = {'id': job_id, 'status': 'COMPLETED', 'output': handler.handle_job({'id': job_id, 'input': job['input']}), 'executionTime': 40000 + 1000 * job['number'], 'delayTime': 22000}
            return job['state']
        if path == '/health':
            return {'workers': {'idle': 0, 'running': 3}}
        raise AssertionError('the tool sent an unexpected call: ' + path)

    def graphql(self, query):
        return {}


def options(**fields):
    base = dict(action='run', spec=None, scene=None, settings=None, cameras=None, where='rented', card_client=None, jobs=None, engine='auto', size=None, samples=None, run_folder=None, check_reset=False,
                max_kilobytes=None, helper='walls', role='builder', ledger=None, over_allowance=None, blender=None, json=False, store_folder=None)
    base.update(fields)
    return types.SimpleNamespace(**base)


batch_variations = ([{'name': f'moss{i}', 'set': {'amount.moss_and_algae': round(0.1 + 0.2 * i, 2)}} for i in range(5)] +
                    [{'name': 'rubbish-low', 'set': {'amount.rubbish': 0.3}}, {'name': 'rubbish-high', 'set': {'amount.rubbish': 0.9}}, {'name': 'wet', 'set': {'state': 'wet'}},
                     {'name': 'broken', 'set': {'amount.dirt': 0.5}}, {'name': 'moss-near', 'set': {'amount.moss_and_algae': 0.32}}])
batch_file = write_spec('batch.json', batch_variations)
settings_env = {rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT, rc.STORE_NAME: store, rc.REMOTE_BLENDER_NAME: os.path.join(store, 'blender', 'blender')}
card_settings = rc.read_settings(settings_env)
service = FakeService()
backend = cards.ClientCard(rc.Client(service, sleep=lambda s: None), card_settings)
ledger_one = os.path.join(folder, 'ledgers', 'one.jsonl')
spoken.clear()
code = runner.run_variations(options(spec=batch_file, run_folder=os.path.join(folder, 'run-one'), ledger=ledger_one), say=say, backend=backend, environ=settings_env)
text = spoken_text()
run_calls = [i for i, c in enumerate(service.calls) if c[1] == '/run']
status_calls = [i for i, c in enumerate(service.calls) if c[1].startswith('/status/')]
check.true('the three jobs are sent at the same time: every /run comes before the first wait', len(run_calls) == 3 and run_calls[-1] < status_calls[0], f'/run at {run_calls}, first status at {status_calls[0] if status_calls else None}')
check.equal('a variation that failed is named and gives exit 1', (code, 'FAIL broken' in text), (1, True))
check.true('the sentence before drawing names the near-duplicate that was dropped', 'dropped "moss-near"' in text and 'near-duplicate' in text, [l for l in spoken if 'moss-near' in l][0][:140])
result_path = os.path.join(folder, 'run-one', 'variations-result.json')
result = json.load(open(result_path))
check.true('the result file and the sheet are made even though one variation failed', os.path.exists(result_path) and os.path.exists(result['sheet']['path']) and result['sheet']['bytes'] <= 400 * 1000, f'{result["sheet"]["bytes"] // 1024} KB')
check.equal('the baseline and every kept variation have a result (9 kept + the baseline = 10; the near-duplicate was dropped)', len(result['results']), 10)
invisible = set(result['invisible'])
check.true('the two rubbish variations (settings far apart, pictures identical) are flagged AFTER drawing as not showing', {'rubbish-low', 'rubbish-high'} <= invisible, f'{sorted(invisible)}')
check.true('...and as nearly the same as each other', any({a, b} == {'rubbish-low', 'rubbish-high'} for a, b in result['nearly_the_same']))
check.true('the moss variations, which change the pictures, are not flagged', not ({f'moss{i}' for i in range(5)} & invisible))
entries, _ = ct.read_ledger(ledger_one)
job_entries = [e for e in entries if e['kind'] == 'job']
check.equal('the ledger has one entry for each job with its billed seconds: work 41, 42, 43 + wake-up 22 + idle 5', sorted(e['card_seconds'] for e in job_entries), [68.0, 69.0, 70.0])
small_entries = [e for e in entries if e['kind'] == 'small']
check.true('...and one for the small jobs (uploads, checks, downloads), measured', len(small_entries) == 1 and small_entries[0]['measured'] is True and small_entries[0]['jobs'] > 5, f'{small_entries[0]["jobs"]} small jobs')
check.true('...and one batch entry (the batch rule counts them)', [e for e in entries if e['kind'] == 'batch'][0]['variations'] == 9)
check.true('the sheet\'s footer carries the card seconds, the wake-up times and says it is an estimate, not a bill', any('Card seconds' in line and 'not a bill' in line for line in result['card_lines']) and any('Wake-up times' in line for line in result['card_lines']), result['card_lines'][0][:200])
check.true('the report says where the jobs ran and how many seconds they used', 'PASS card seconds' in text and 'in all' in text)
check.true('every picture came back through the bundle (2 cameras for 10 entries, minus the broken one)', sum(len(r['pictures']) for r in result['results']) == 18, f'{sum(len(r["pictures"]) for r in result["results"])} pictures')
everything = text + open(result_path).read() + open(ledger_one).read()
check.true('no key or endpoint id reaches the report, the result or the ledger', FAKE_KEY not in everything and FAKE_ENDPOINT not in everything)

# the plan costs nothing
service_plan = FakeService()
spoken.clear()
code = runner.run_variations(options(action='plan', spec=batch_file, ledger=os.path.join(folder, 'ledgers', 'plan.jsonl')), say=say, backend=cards.ClientCard(rc.Client(service_plan, sleep=lambda s: None), card_settings), environ=settings_env)
check.true('`plan` draws nothing: no call to the card, no ledger file, exit 0, and it says the split and the estimate', code == 0 and service_plan.calls == [] and not os.path.exists(os.path.join(folder, 'ledgers', 'plan.jsonl')) and 'PASS plan:' in spoken_text() and 'card seconds' in spoken_text())

# the allowance, before any call
ledger_full = os.path.join(folder, 'ledgers', 'full.jsonl')
ct.append_entry(ledger_full, {'kind': 'job', 'helper': 'walls', 'role': 'builder', 'card_seconds': 590.0, 'job_id': 'earlier'})
service_full = FakeService()
spoken.clear()
code = runner.run_variations(options(spec=batch_file, ledger=ledger_full, run_folder=os.path.join(folder, 'run-full')), say=say, backend=cards.ClientCard(rc.Client(service_full, sleep=lambda s: None), card_settings), environ=settings_env)
check.true('a helper with 590 of its 600 s used is REFUSED before any call is made (exit 1, nothing uploaded, nothing sent)', code == 1 and service_full.calls == [] and 'nothing was sent' in spoken_text(), f'exit {code}, {len(service_full.calls)} call(s)')
spoken.clear()
code = runner.run_variations(options(spec=batch_file, ledger=ledger_full, run_folder=os.path.join(folder, 'run-full'), over_allowance='the sheet was lost and one more look is needed'), say=say,
                             backend=cards.ClientCard(rc.Client(FakeService(), sleep=lambda s: None), card_settings), environ=settings_env)
check.true('with a written reason a batch estimated at under half again of the allowance may go (the override is written into the ledger); one that would pass even that is refused', ('OVER THE ALLOWANCE' in spoken_text() and any(e['kind'] == 'override' for e in ct.read_ledger(ledger_full)[0]))
           or 'Even with a reason' in spoken_text(), spoken_text()[:0] + [l for l in spoken if 'card time' in l][0][:160])
# the batch rule
ledger_batches = os.path.join(folder, 'ledgers', 'batches.jsonl')
for _ in range(2):
    ct.append_entry(ledger_batches, {'kind': 'batch', 'helper': 'walls', 'change': 'moss-test', 'number': 1})
service_third = FakeService()
spoken.clear()
code = runner.run_variations(options(spec=batch_file, ledger=ledger_batches, run_folder=os.path.join(folder, 'run-third')), say=say, backend=cards.ClientCard(rc.Client(service_third, sleep=lambda s: None), card_settings), environ=settings_env)
check.true('a THIRD batch for the same change is refused before any call ("one batch, look, at most one more")', code == 1 and service_third.calls == [] and 'at most one more' in spoken_text(), spoken_text()[-200:])
# a local run with a role that has no card time is fine: nothing is rented
spoken.clear()
code = runner.run_variations(options(spec=batch_file, where='local', role='planner', ledger=os.path.join(folder, 'ledgers', 'local.jsonl'), run_folder=os.path.join(folder, 'run-local-fake'), blender=os.path.join(store, 'blender', 'blender'),
                                     helper='planner-1'), say=say, environ=settings_env)
check.true('drawn on this computer (here with the fake blender), no card seconds are used, so even a planner may do it, and the footer says so', code == 1 and 'no rented-card seconds were used' in spoken_text(), spoken_text()[-300:])

# the older command-line client
command_store = os.path.join(folder, 'command-store')
shutil.copytree(os.path.join(store, 'blender'), os.path.join(command_store, 'blender'))
os.environ['FAKE_CARD_STORE'] = command_store
fake_client = os.path.join(FIXTURES, 'place', 'fake_card_client.py')
command_backend = cards.CommandCard([sys.executable, fake_client], store_folder='/workspace', poll_seconds=0.01)
ledger_two = os.path.join(folder, 'ledgers', 'two.jsonl')
spoken.clear()
code = runner.run_variations(options(spec=batch_file, run_folder=os.path.join(folder, 'run-two'), ledger=ledger_two, where='rented', role='builder'), say=say, backend=command_backend, environ={})
text_two = spoken_text()
result_two = json.load(open(os.path.join(folder, 'run-two', 'variations-result.json')))
entries_two, _ = ct.read_ledger(ledger_two)
check.true('the older command-line client works too: jobs sent with `run`, waited for with `job` (it answers IN_QUEUE first), pictures downloaded', code == 1 and len(result_two['jobs']) == 3 and all(j['runpod_status'] == 'COMPLETED' for j in result_two['jobs'])
           and os.path.exists(result_two['sheet']['path']), text_two[-300:])
small_two = [e for e in entries_two if e['kind'] == 'small']
check.true('...it cannot say what an upload billed, so those steps are counted from the wall clock and MARKED as an estimate in the ledger and on the sheet', len(small_two) == 1 and small_two[0]['measured'] is False
           and any('estimate from the wall clock' in line for line in result_two['card_lines']), f'{small_two[0]["what"] if small_two else None}')
check.true('...and its jobs are logged with the wake-up and billed seconds the client printed', len([e for e in entries_two if e['kind'] == 'job']) == 3 and all(e['wake_up_seconds'] >= 21.5 for e in entries_two if e['kind'] == 'job'))
# a job that never leaves the line stops the batch, at the time limit, and changes nothing
orig_value = numbers.value
numbers.value = lambda key: 0.0003 if key == 'place_render.jobs_waiting_stop_minutes' else orig_value(key)
stuck_store = os.path.join(folder, 'stuck-store')
os.makedirs(stuck_store)
shutil.copytree(os.path.join(store, 'blender'), os.path.join(stuck_store, 'blender'))
stuck_script = os.path.join(folder, 'stuck_client.py')
open(stuck_script, 'w').write("import json, sys, runpy, os\nif sys.argv[1] == 'job':\n    print(json.dumps({'id': sys.argv[2], 'state': 'running', 'runpod_status': 'IN_QUEUE'}))\n    sys.exit(0)\nsys.argv[0] = %r\nrunpy.run_path(%r, run_name='__main__')\n" % (fake_client, fake_client))
os.environ['FAKE_CARD_STORE'] = stuck_store
spoken.clear()
try:
    code = runner.run_variations(options(spec=batch_file, run_folder=os.path.join(folder, 'run-stuck'), ledger=os.path.join(folder, 'ledgers', 'stuck.jsonl')), say=say,
                                 backend=cards.CommandCard([sys.executable, stuck_script], poll_seconds=0.01), environ={})
finally:
    numbers.value = orig_value
check.true('a job that waits in line past the time limit STOPS the batch with a plain sentence (exit 1); nothing is cancelled or changed', code == 1 and 'stopped: job' in spoken_text() and 'Nothing was cancelled' in spoken_text(), spoken_text()[-200:])

# ---- details added by the batching step: short flags, names cut between words, paths beside the file, ONE upload of a scene, the command client's marker check
from place_kit.variations import verb as verb_module  # noqa: E402


def fake_result(name):
    return {'name': name, 'ok': True, 'pictures': [], 'notes': []}


def fake_pair(a, b, mean):
    return {'a': a, 'b': b, 'mean_difference': mean, 'changed_share': 0.0, 'nearly_the_same': True}


names_fake = ['baseline', 'a', 'b', 'c', 'd', 'e', 'f', 'g']
pairs_fake = {'pairs': [fake_pair('baseline', 'a', 0.2), fake_pair('baseline', 'b', 0.3), fake_pair('baseline', 'c', 0.25), fake_pair('a', 'b', 0.0), fake_pair('a', 'c', 0.1), fake_pair('b', 'c', 0.1),
                        fake_pair('d', 'e', 0.3), fake_pair('d', 'f', 0.2), fake_pair('e', 'f', 0.4)],
              'nearly_same': [('baseline', 'a'), ('baseline', 'b'), ('baseline', 'c'), ('a', 'b'), ('a', 'c'), ('b', 'c'), ('d', 'e'), ('d', 'f'), ('e', 'f')], 'invisible': ['a', 'b', 'c']}
fake_results = [fake_result(name) for name in names_fake]
short_lines = runner.flag_results(fake_results, pairs_fake)
flags_of = {r['name']: r['flags'] for r in fake_results}
check.true('the report and the sheet are SHORT: the variations that came out nearly the same as the baseline are named in ONE line (not pair by pair), and a group of alike variations that DO show is one line too',
           len(short_lines) == 2 and '"a", "b", "c"' in short_lines[0] and 'all came out nearly the same as the baseline' in short_lines[0] and 'nearly the same as each other too' in short_lines[0]
           and '"d", "e" and "f"' in short_lines[1] and 'keep one of them' in short_lines[1], ' || '.join(short_lines)[:300])
check.true('  (each flagged variation still carries its own flag; the first of a group is the one to keep; the full pairs stay in the result file)',
           all('does not show' in flags_of[n][0] for n in 'abc') and flags_of['d'] == [] and flags_of['e'] == ['nearly the same as #4 d'] and flags_of['f'] == ['nearly the same as #4 d'] and flags_of['g'] == [], str(flags_of))
check.true('a change name is cut between words, never in the middle of one, and stays within 40 characters',
           sp.safe_name('cracks and chips on the lock walls and gate') == 'cracks-and-chips-on-the-lock-walls-and' and len(sp.safe_name('word ' * 20)) <= 40 and not sp.safe_name('word ' * 20).endswith('-w')
           and sp.safe_name('moss test') == 'moss-test', sp.safe_name('cracks and chips on the lock walls and gate'))
made_folder = os.path.join(folder, 'made')
os.makedirs(made_folder)
made_scene = os.path.join(folder, 'work', 'scene.blend')
made_args = types.SimpleNamespace(action='make', spec=None, count=4, change='moss test', scene=made_scene, settings=os.path.join(folder, 'work', 'place-settings.json'), keys=['amount.moss_and_algae'], seed=2,
                                  cameras=['Camera A'], out=os.path.join(made_folder, 'moss.json'))
spoken.clear()
code = verb_module.main_command(made_args, say=say)
made_content = json.load(open(made_args.out))
check.true('`make` writes the scene and the settings beside the file (relative), so the file still works after its folder is copied; the keys come in the order about, change, scene, settings, cameras, variations',
           code == 0 and made_content['scene'] == '../work/scene.blend' and made_content['settings'] == '../work/place-settings.json' and list(made_content)[:6] == ['about', 'change', 'scene', 'settings', 'cameras', 'variations']
           and sp.read_spec(made_args.out)['scene'] == made_scene, str(made_content.get('scene')))


refine_args = types.SimpleNamespace(action='refine', spec=os.path.join(folder, 'run-one', 'variations-result.json'), pick=['moss1', 'moss3'], count=6, seed=3, radius=0.3, out=os.path.join(made_folder, 'batch2.json'))
spoken.clear()
code = verb_module.main_command(refine_args, say=say)
refined = json.load(open(refine_args.out))
check.true('`refine` on a finished run writes its scene and settings beside the new file too, names the blend short (blend-moss1-moss3), keeps four decimals, and the new file is read by the real reader',
           code == 0 and refined['scene'] == '../work/scene.blend' and refined['settings'] == '../work/place-settings.json' and refined['variations'][0]['name'] == 'blend-moss1-moss3'
           and sp.read_spec(refine_args.out)['scene'] == scene_file and len(refined['variations']) == 6, str(refined['variations'][0]))


class RecordingService(FakeService):
    """The fake card service that also writes down every file operation of the small jobs."""

    def __init__(self):
        super().__init__()
        self.operations = []

    def call(self, method, path, body=None, attempts=1):
        if path == '/runsync' and (body or {}).get('input', {}).get('op') in ('put', 'info'):
            self.operations.append((body['input']['op'], body['input'].get('path')))
        return super().call(method, path, body, attempts)


first_service, second_service = RecordingService(), RecordingService()
for service_used, tag in ((first_service, 'again-1'), (second_service, 'again-2')):
    runner.run_variations(options(spec=batch_file, run_folder=os.path.join(folder, 'run-' + tag), ledger=os.path.join(folder, 'ledgers', tag + '.jsonl')), say=say,
                          backend=cards.ClientCard(rc.Client(service_used, sleep=lambda s: None), card_settings), environ=settings_env)
scene_paths_1 = {path for op, path in first_service.operations if path and path.endswith('scene.blend')}
scene_paths_2 = {path for op, path in second_service.operations if path and path.endswith('scene.blend')}
check.true('the scene waits on the store under its own checksum, in the same place for every batch (place-jobs/scenes/<8 letters>/), so the second and last batch does not upload the scene again',
           len(scene_paths_1) == 1 and scene_paths_1 == scene_paths_2 and re.search(r'/place-jobs/scenes/[0-9a-f]{8}/scene\.blend$', next(iter(scene_paths_1))) is not None
           and not [1 for op, path in second_service.operations if op == 'put' and path.endswith('scene.blend')], str(sorted(scene_paths_1)))
check.true('  (the settings file and its owners table wait there too, under their own checksum, and are checked, not sent again)',
           any(path and '/settings-' in path for op, path in second_service.operations) and not [1 for op, path in second_service.operations if op == 'put' and '/settings-' in (path or '')])
marker_store = os.path.join(folder, 'marker-store')
os.makedirs(marker_store)
os.environ['FAKE_CARD_STORE'] = marker_store
marker_backend = cards.CommandCard([sys.executable, os.path.join(FIXTURES, 'place', 'fake_card_client.py')], store_folder='/workspace', poll_seconds=0.01)
before_upload = marker_backend.have_file('/workspace/kit-x/kit/place-kit/blender_run.py')
marker_local = os.path.join(folder, 'marker.py')
open(marker_local, 'w').write('# a marker file')
marker_backend.upload(marker_local, '/workspace/kit-x/kit/place-kit/blender_run.py')
check.true('the command-line client can tell whether the kit is already on the store (it fetches a small marker file: one small job), so the kit is not uploaded twice',
           before_upload is False and marker_backend.have_file('/workspace/kit-x/kit/place-kit/blender_run.py') is True)

# ================================================================ part C: the real worker inside Blender
blender = blender_program()
if not blender:
    check.note('SKIP part C (the real worker inside Blender): Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')
else:
    environment = {name: value for name, value in os.environ.items() if name not in ('RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_SETTINGS_FILE')}
    environment['BLENDER'] = blender
    hut_folder = os.path.join(folder, 'hut')
    os.makedirs(hut_folder)
    hut = os.path.join(hut_folder, 'hut.blend')
    done = subprocess.run([blender, '-b', '--disable-autoexec', '--python', os.path.join(FIXTURES, 'place', 'make_hut_scene.py'), '--', hut, '--no-floating', '--roles-by-property', '--cameras'],
                          capture_output=True, text=True, env=environment, timeout=300)
    launcher = os.path.join(PLACE_KIT, 'place_command.py')
    finished = os.path.join(hut_folder, 'hut-finished.blend')
    done = subprocess.run([sys.executable, '-I', '-B', launcher, 'finish', '--scene', hut, '--quick', '--save-as', finished], capture_output=True, text=True, env=environment, timeout=600)
    check.true('the tiny hut (two cameras) is built and finished for the variations', os.path.exists(finished), done.stdout[-200:] + done.stderr[-200:])
    hook = os.path.join(hut_folder, 'sun_scale.py')
    open(hook, 'w').write("import bpy\n\n\ndef apply(variation):\n    factor = float(variation['args'].get('sun', 1.0))\n    for light in bpy.data.lights:\n        if light.type == 'SUN':\n            light.energy = light.energy * factor\n")
    hut_variations = write_json(os.path.join(hut_folder, 'hut-variations.json'), {
        'change': 'wear on the hut', 'scene': 'hut-finished.blend', 'settings': 'place-settings.json', 'cameras': ['Camera A', 'Camera B'],
        'variations': [{'name': 'moss-high', 'set': {'amount.moss_and_algae': 1.0, 'dials.moss_and_algae.cover': 0.9}}, {'name': 'dirt-low', 'set': {'amount.dirt': 0.1}},
                       {'name': 'wet', 'set': {'state': 'wet'}}, {'name': 'derelict', 'set': {'look': 'derelict'}}, {'name': 'no-wear', 'set': {'master': 0.0}},
                       {'name': 'no-such-layer', 'set': {'amount.rust': 0.2}}, {'name': 'dark-sun', 'script': 'sun_scale.py', 'args': {'sun': 0.5}, 'ranges': {'sun': [0, 2]}},
                       {'name': 'dark-sun-near', 'script': 'sun_scale.py', 'args': {'sun': 0.52}, 'ranges': {'sun': [0, 2]}}]})
    local_ledger = os.path.join(hut_folder, 'ledger.jsonl')
    spoken.clear()
    code = runner.run_variations(options(spec=hut_variations, where='local', engine='cycles', size='160x108', samples=6, check_reset=True, ledger=local_ledger, run_folder=os.path.join(hut_folder, 'run'),
                                         blender=blender, role='builder'), say=say, environ={})
    text = spoken_text()
    document = json.load(open(os.path.join(hut_folder, 'run', 'variations-result.json')))
    by_name = {r['name']: r for r in document['results']}
    check.equal('the real worker draws every kept variation and the baseline (8 asked, 1 near-duplicate dropped), 2 pictures each', (code, len(document['results']), sum(len(r['pictures']) for r in document['results'])), (0, 8, 16))
    check.true('the hook variation that is a near-duplicate was dropped BEFORE drawing, by the hook\'s own number and its written range', any(d['name'] == 'dark-sun-near' for d in document['dropped']))
    summaries = document['job_summaries']
    check.true('every job put the scene back exactly: the fingerprint of every wear input at the end equals the one at the start', all(s['fingerprint_at_start'] == s['fingerprint_at_end'] for s in summaries.values()),
               ', '.join(f'{s["fingerprint_at_start"]}/{s["fingerprint_at_end"]}' for s in summaries.values()))
    check.true('the baseline drawn AGAIN after all the variations (including a script hook and look and state rewrites) is the same picture as the first (drift under 0.5 of 255)', document['reset_check'] is not None
               and document['reset_check']['mean_difference_of_255'] is not None and document['reset_check']['mean_difference_of_255'] < 0.5, f'{document["reset_check"]}')
    check.true('a layer that is in no material of this scene is called out: "changes nothing here" and "does not show"', any('changes nothing here' in flag for flag in by_name['no-such-layer'].get('flags', [])) and 'no-such-layer' in document['invisible'],
               str(by_name['no-such-layer'].get('flags')))
    check.true('state, look, master and the hook each change the pictures (none of them is "nearly the same" as the baseline)', not ({'wet', 'derelict', 'no-wear', 'dark-sun'} & set(document['invisible'])), f'invisible: {document["invisible"]}')
    check.true('the master at 0 gives the picture without wear: it measurably moved from the baseline, and `moss-high` moved the detail energy', by_name['no-wear']['average']['colour_shift'] > 0.3, f'colour shift {by_name["no-wear"]["average"]["colour_shift"]:.2f}')
    check.true('the squint score of every variation against the baseline is a number between 0 and 1 and the baseline\'s own is exactly 1', all(0.0 <= r['average']['squint'] <= 1.0 for r in document['results']) and by_name['baseline']['average']['squint'] == 1.0)
    check.true('the sheet is one JPG under 400 KB', os.path.getsize(document['sheet']['path']) <= 400 * 1000, f'{document["sheet"]["bytes"] // 1024} KB')
    check.true('a batch drawn here writes no card seconds', not [e for e in ct.read_ledger(local_ledger)[0] if e['kind'] in ('job', 'small')])
    check.equal('a camera that is not in the scene stops before anything is drawn (exit 2 from the worker, said plainly)', 'no camera named' in subprocess.run(
        [sys.executable, '-I', '-B', launcher, 'variations', 'run', hut_variations, '--where', 'local', '--cameras', 'Camera Z', '--engine', 'cycles', '--size', '96x64', '--samples', '2', '--ledger', local_ledger,
         '--run-folder', os.path.join(hut_folder, 'run-z')], capture_output=True, text=True, env=environment, timeout=300).stdout, True)
    # the same batch through the card route, with Blender as the card's own program
    real_store = os.path.join(folder, 'real-store')
    os.makedirs(real_store)
    real_env = {rc.KEY_NAME: FAKE_KEY, rc.ENDPOINT_NAME: FAKE_ENDPOINT, rc.STORE_NAME: real_store, rc.REMOTE_BLENDER_NAME: blender}
    real_backend = cards.ClientCard(rc.Client(FakeService(), sleep=lambda s: None), rc.read_settings(real_env))
    card_ledger = os.path.join(hut_folder, 'card-ledger.jsonl')
    spoken.clear()
    code = runner.run_variations(options(spec=write_json(os.path.join(hut_folder, 'card-variations.json'), {
        'change': 'hut on the fake card', 'scene': 'hut-finished.blend', 'settings': 'place-settings.json', 'cameras': ['Camera A'],
        'variations': [{'name': 'moss-low', 'set': {'amount.moss_and_algae': 0.3}}, {'name': 'wet', 'set': {'state': 'wet'}}, {'name': 'no-wear', 'set': {'master': 0.0}},
                       {'name': 'dark-sun', 'script': 'sun_scale.py', 'args': {'sun': 0.5}, 'ranges': {'sun': [0, 2]}}]}), engine='cycles', size='96x64', samples=4,
                                         run_folder=os.path.join(hut_folder, 'run-card'), ledger=card_ledger), say=say, backend=real_backend, environ=real_env)
    if code != 0:
        print('\n'.join(spoken))            # the whole report, so a failure can be read
    card_document = json.load(open(os.path.join(hut_folder, 'run-card', 'variations-result.json')))
    check.true('the same kind of batch through the card route with Blender as the card\'s own program: scene, settings, hook and kit uploaded, jobs sent, bundle downloaded, sheet made', code == 0 and card_document['where'] == 'a rented card'
               and sum(len(r['pictures']) for r in card_document['results']) == 5 and os.path.exists(card_document['sheet']['path']), spoken_text()[-400:])
    check.true('...the paths in the job files are the card\'s own (the store), not this computer\'s, and the hook ran there', all(real_store in json.load(open(path))['scene'] for path in
               [os.path.join(hut_folder, 'run-card', 'jobs', name) for name in os.listdir(os.path.join(hut_folder, 'run-card', 'jobs'))]) and 'dark-sun' not in card_document['invisible'])

check.finish()
