"""What this does: tests the place facts schema, its checker and the four converters (place_facts.py).
1. The four converted places (the Works, the notice corner, the people test, checkout C1) pass the schema and the sense
   checks, and rebuilding each from its source fixtures gives exactly the stored file (the converters are repeatable and
   the fixtures are up to date).
2. Planted faults are caught: a missing field, an unknown kind of shot, an accepted entry naming no view or without a
   date, a sign normal of the wrong length, a slide that does not end at the composed spot, no support surfaces.
3. The converted facts say what their sources say (counts, letter heights, which way the drums' words face), and the
   camera sums read straight from a place facts file give the same answers as from the original files.
4. The command line works end to end (frame_geometry.py slide --place-facts; place_facts.py check).
Run: python3 kit/calculators/tests/test_place_facts.py
"""
import copy
import json
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
import place_facts as pf  # noqa: E402
import frame_geometry as g  # noqa: E402
from settings import load_settings  # noqa: E402

check = Checker('place facts: schema, converters and what they carry')
settings = load_settings()
schema = pf.load_schema()


def fixture(*parts):
    return os.path.join(FIXTURES, *parts)


def load(*parts):
    with open(fixture(*parts)) as handle:
        return json.load(handle)


def run(args):
    return subprocess.run([sys.executable, '-I', '-B'] + args, capture_output=True, text=True, cwd=CALCULATORS, timeout=120)


STORED = {
    'works': ('works', 'works-place-facts.json',
              ['from-works', '--shot', fixture('works', 'works-shot.json'), '--cameras', fixture('works'), '--checks', fixture('works'),
               '--facts', fixture('works', 'round5-final-w1-quiet-facts.json'), fixture('works', 'round5-final-w1-working-facts.json'),
               '--facts-labels', 'w1-quiet', 'w1-working']),
    'notice corner': ('notice-corner', 'notice-corner-place-facts.json',
                      ['from-notice-corner', '--shot', fixture('notice-corner', 'notice-corner-shot.json'), '--camera', fixture('notice-corner', 'notice-corner-camera.json'),
                       '--check', fixture('notice-corner', 'notice-corner-shot-check.json'), '--facts', fixture('notice-corner', 'notice-corner-final-frame-facts.json'),
                       '--paintings', fixture('notice-corner', 'notice-corner-paintings.json')]),
    'people test': ('people-test', 'people-test-place-facts.json',
                    ['from-people-test', '--shot', fixture('people-test', 'people-test-shot.json'), '--camera', fixture('people-test', 'people-test-camera.json'),
                     '--check', fixture('people-test', 'people-test-shot-check.json'), '--paintings', fixture('people-test', 'people-test-paintings.json')]),
    'checkout C1': ('checkout-c1', 'checkout-c1-place-facts.json',
                    ['from-shot-facts', '--facts', fixture('checkout-c1', 'checkout-c1-check10-facts.json'), '--check', fixture('checkout-c1', 'checkout-c1-shot-check.json'),
                     '--place', 'checkout', '--view', 'c1', '--kind', 'interior']),
}


def comparable(facts):
    clean = copy.deepcopy(facts)
    clean['made_from'] = [os.path.basename(p) for p in clean['made_from']]
    return clean


# 1. every converted place passes, and rebuilds exactly
with tempfile.TemporaryDirectory() as folder:
    for name, (sub, file, args) in STORED.items():
        stored = load(sub, file)
        problems = pf.validate(stored, schema) + pf.sense_problems(stored, settings)
        check.true(f'{name}: the stored place facts pass the schema and sense checks', not problems, details='; '.join(problems[:3]) or 'no problems')
        out = os.path.join(folder, file)
        result = run(['place_facts.py'] + args + ['--out', out])
        rebuilt = json.load(open(out)) if os.path.exists(out) else {}
        check.true(f'{name}: rebuilding from the source fixtures gives the stored file', result.returncode == 0 and comparable(rebuilt) == comparable(stored),
                   details=(result.stdout + result.stderr)[-300:] if result.returncode else 'identical (apart from the folders in made_from)',
                   proves='the converter is repeatable and the stored fixture is its current output')

# 2. planted faults
works = load('works', 'works-place-facts.json')


def faults_in(change):
    planted = copy.deepcopy(works)
    change(planted)
    return pf.validate(planted, schema) + pf.sense_problems(planted, settings)


planted_cases = [
    ('a view without its kind of shot', lambda f: f['views'][0].pop('kind_of_shot'), 'missing "kind_of_shot"'),
    ('an unknown kind of shot', lambda f: f['views'][0]['kind_of_shot'].append('crowded street'), 'is not in film-settings.json'),
    ('an accepted entry naming no view', lambda f: f['accepted'].append({'rule': 'rule3_story_box', 'view': 'w9', 'reason': 'r', 'who': 'w', 'date': '2026-10-16'}),
     'is not one of the place'),
    ('an accepted entry without who accepted it', lambda f: f['accepted'].append({'rule': 'rule3_story_box', 'view': 'w1', 'reason': 'r', 'date': '2026-10-16'}),
     'missing "who"'),
    ('an accepted entry with a date in words', lambda f: f['accepted'].append({'rule': 'rule3_story_box', 'view': 'w1', 'reason': 'r', 'who': 'w', 'date': '16 October'}),
     'does not match'),
    ('a sign normal of length 2', lambda f: f['signs'][0].__setitem__('normal', [0, -2, 0]), 'has length 2.000'),
    ('a point with two numbers', lambda f: f['signs'][0].__setitem__('centre', [1, 2]), 'at least 3 item'),
    ('a slide that does not end at the composed spot', lambda f: next(v for v in f['views'] if v['slide'])['slide'].__setitem__('end', [0, 0, 0]),
     'not at the composed spot'),
    ('no support surfaces', lambda f: f.__setitem__('support_surfaces', []), 'no support surfaces'),
    ('a figure with no facing', lambda f: f['figures'][0].pop('facing'), 'missing "facing"'),
    ('an emitter of an unknown kind', lambda f: f['emitters'][0].__setitem__('kind', 'volcano'), 'is not one of'),
]
for label, change, words in planted_cases:
    found = faults_in(change)
    check.true(f'planted fault caught: {label}', any(words in p for p in found), details='; '.join(found[:2]) or 'nothing found')

# 3. what the converted facts carry
shot = load('works', 'works-shot.json')
check.equal('Works: every waiting man and worker is a figure (7 + 8 + 4)', len(works['figures']),
            len(shot['men_at_no_1']) + len(shot['men_at_no_2']) + sum(len(v) for v in shot['workers'].values() if isinstance(v, list)),
            recorded='works-shot.json men_at_no_1, men_at_no_2, workers')
heights = {s['name']: s['letter_height_metres'] for s in works['signs']}
check.equal('Works: letter heights are the props index\'s', [heights['no-1 board'], heights['no-2 board'], heights['bank sign'], heights['no-1-drum-petrol'],
                                                              heights['no-1-drum-diesel']], [0.266, 0.25, 0.305, 0.097, 0.106],
            recorded='works-shot.json letter_pixels "about" line; props/index.json letter_height_metres', proves='only that the converter copies them')
turned = []
for sign in works['signs']:
    if 'drum' not in sign['name']:
        continue
    view = 'w1' if sign['name'].startswith('no-1') else 'w2'
    camera = next(v for v in works['views'] if v['name'] == view)['camera']['composed']
    toward = g.normalise(g.subtract(camera, sign['centre']))
    angle = math.degrees(math.acos(max(-1, min(1, g.dot(sign['normal'], [toward[0], toward[1], 0]) / g.length([toward[0], toward[1], 0])))))
    turned.append((sign['name'], round(angle, 1)))
check.true('Works: every drum\'s word faces its gate view within its 44-degree wrap', all(a < settings.value('lettering.stencil_wrap_degrees') for _, a in turned),
           details=', '.join(f'{n} {a} degrees off' for n, a in turned), recorded='assemble_works.py DRUM_SPOTS turns (+12, +8; No. 2 mirrored)',
           proves='the turns written by hand do what they were for: the words face the camera')
w1 = g.camera_from_place_facts(works, settings, 'w1', 'composed', 'film')
man6 = next(f for f in works['figures'] if f['name'] == 'man-6')
check.close('Works: man 6 from the place facts\' W1 camera lands (down)', g.project_point(w1, man6['feet'])['down'], 0.696, 0.001,
            recorded='skeptic (log 35) 0.696; test_frame_geometry.py (from works-shot.json directly)', proves='a calculator can work from place facts alone')
lit = {l['name']: l for l in works['lights']}
check.equal('Works: the fire\'s watts come from the measured check facts', lit['brazier_light']['watts'], 80.0, recorded='round 5 final-w1-quiet facts.json lights (80 W)')
check.equal('Works: the gate lamp reaches only the gate, board and men (in either state)', lit['no-1-gate-lamp-light']['reaches_only'],
            ['man 1', 'man 2', 'man 3', 'man 4', 'man 5', 'man 6', 'man 7', 'no-1 board', 'no-1 gate'],
            recorded='round 5 final-w1-quiet and final-w1-working facts.json (light linking; the men are gone in the working state)')
notice = load('notice-corner', 'notice-corner-place-facts.json')
check.equal('notice corner: four accepted exceptions, each kept by the user\'s decision 38', [a['who'].startswith('the user kept the shot') for a in notice['accepted']],
            [True] * 4, recorded='notes/Decisions.md decision 38 ("Wow that\'s incredible. Yes keep it."), log 32')
sign = notice['signs'][0]
end = notice['views'][0]['camera']['composed']
level = g.normalise([end[0] - sign['centre'][0], end[1] - sign['centre'][1], 0])
check.true('notice corner: the notice faces the composed camera (as the build turned it)', g.dot(sign['normal'], level) > 0.9999,
           details=f'cosine {g.dot(sign["normal"], level):.6f} (seen from above)', recorded='assemble_notice_corner.py line 109')
people = load('people-test', 'people-test-place-facts.json')
camera = people['views'][0]['camera']['composed']
backs = [f['name'] for f in people['figures'] if g.dot(f['facing'], g.normalise([camera[0] - f['feet'][0], camera[1] - f['feet'][1], 0])) < 0]
facing = [f['name'] for f in people['figures'] if f['name'] not in backs]
check.equal('people test: only the facing man looks toward the camera; the other ten show their backs', facing, ['figure-facing'],
            recorded='people-test-shot.json figures[].faces ("the camera" only for figure-facing)', proves='the facing direction from a model\'s turn is right')
checkout = load('checkout-c1', 'checkout-c1-place-facts.json')
counter = next(s for s in checkout['support_surfaces'] if s['kind'] == 'counter')
check.close('checkout C1 (hold-out): the counter top found from the story things (m)', counter['height'], 0.885, 0.005,
            recorded='checkout-c1-check10-facts.json (divider 0.885, basket 0.886); plan 34 ("the counter 0.9 m up")',
            proves='a place facts file for an interior gets a support surface without anyone typing it')
check.true('checkout C1: marked as an interior', checkout['interior'] is True)

# 4. the command line, end to end
result = run(['frame_geometry.py', 'slide', '--place-facts', fixture('notice-corner', 'notice-corner-place-facts.json'), '--view', 'end', '--json'])
answer = json.loads(result.stdout) if result.returncode == 0 else {}
check.true('frame_geometry.py slide --place-facts: the pail decides, too far for the painting', answer.get('worst') == 'pail' and answer.get('verdict', '').startswith('too far'),
           details=f'worst {answer.get("worst")} {answer.get("worst_magnification")} against {answer.get("limit")}: {answer.get("verdict")}' if answer else result.stderr[-300:])
check.true('frame_geometry.py names the film-settings.json values it used', 'frame.painting_returned_size_pixels' not in answer.get('settings_used', {}) and
           'camera.slide_magnification_borderline_share' in answer.get('settings_used', {}),
           details=', '.join(answer.get('settings_used', {})), proves='a report says which house numbers it rests on (here the painting\'s own returned size replaced the table\'s)')
plain = run(['frame_geometry.py', 'slide', '--place-facts', fixture('works', 'works-place-facts.json'), '--view', 'w1', '--json'])
ground = run(['frame_geometry.py', 'slide', '--place-facts', fixture('works', 'works-place-facts.json'), '--view', 'w1', '--json', '--count-ground'])
plain, ground = json.loads(plain.stdout), json.loads(ground.stdout)
check.true('W1 slide: the men decide and pass; the painted ground at the bottom edge is shown but counted only when asked',
           plain['verdict'] == 'pass' and plain['worst'] == 'man-6' and ground['worst'].startswith('ground') and ground['verdict'].startswith('too far'),
           details=f'men: {plain["worst"]} {plain["worst_magnification"]}x ({plain["verdict"]}); with the ground: {ground["worst_magnification"]}x ({ground["verdict"]})',
           proves='whether the ground counts is left to a person (the notice corner\'s ground came about 1.53x nearer and the user kept it)')
result = run(['place_facts.py', 'check'] + [fixture(sub, file) for sub, file, _ in STORED.values()])
check.true('place_facts.py check: all four files fine (exit 0)', result.returncode == 0, details=result.stdout.splitlines()[0] if result.stdout else result.stderr[-200:])
with tempfile.TemporaryDirectory() as folder:
    broken = os.path.join(folder, 'broken.json')
    damaged = copy.deepcopy(works)
    damaged['accepted'].append({'rule': 'rule3_story_box', 'view': 'w1', 'reason': 'kept'})
    json.dump(damaged, open(broken, 'w'))
    result = run(['place_facts.py', 'check', broken])
    check.true('place_facts.py check: a damaged file exits 1 and says why', result.returncode == 1 and 'missing "who"' in result.stdout,
               details=[l.strip() for l in result.stdout.splitlines() if 'missing' in l][:2])
check.finish()
