"""What this does: tests the extended camera audit (kit/paper-film/tools/camera_audit.py). First that its old behaviour is
unchanged: chapter 2's old camera logs audit exactly as the old tool printed them (9 problems before the camera rule, 21
shots and 0 problems after, log 20). Then the page window worked out from the timeline (it must equal the page edges the
stage itself reported), and the built-and-painted set checks: round 4's filmed W1 slide (no turn, no drift, inside the
plate), log 29's turning clip (refused), a 1.5 degree turn under a 44-degree plate (leaves it, log 29 / lesson 90), the
notice corner's slide (the pail 1.45 times nearer, accepted by the user) and, as a hold-out, checkout C1's planned slide.
Run: python3 tests/test_camera_audit.py (or tests/run_all.py). Exits 1 if a check fails.
"""
import atexit
import contextlib
import gzip
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, work_folder  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
TOOLS = os.path.join(KIT, 'paper-film', 'tools')
AUDIT = os.path.join(TOOLS, 'camera_audit.py')
OURS = os.path.join(FIXTURES, 'effects-camera-light')
UNPACKED = tempfile.mkdtemp(prefix='camera-audit-test-')   # the whole camera logs ship gzipped; the tool reads plain JSON
atexit.register(shutil.rmtree, UNPACKED, True)


def unpacked(name):
    """A gzipped fixture written out as plain JSON (camera_audit.py reads a plain file)."""
    path = os.path.join(UNPACKED, name.replace('.gz', ''))
    with gzip.open(os.path.join(OURS, name), 'rb') as source, open(path, 'wb') as target:
        target.write(source.read())
    return path


OLD_LOGS = {   # whole camera logs (gzipped) and what the old tool printed for them at the time
    'before': (unpacked('old-chapter-2-before-camera-log.json.gz'), os.path.join(OURS, 'old-chapter-2-before-audit-by-old-tool.txt')),
    'round 4 film': (unpacked('round4-film-camera-every-frame.json.gz'), os.path.join(OURS, 'round4-film-audit-by-old-tool.txt')),
}
AFTER_LOG = unpacked('old-chapter-2-after-camera-log.json.gz')        # the chapter 2 work folder's stills/r20h-all-camera.json (log 20)
SINGLE_PAGE_LOG = unpacked('old-chapter-2-page-5-camera-log.json.gz')  # its stills/r20d-p5-camera.json (log 20)
sys.path.insert(0, TOOLS)
import camera_audit as audit  # noqa: E402
import frame_geometry as geometry  # noqa: E402
from settings import load_settings  # noqa: E402

settings = load_settings()
check = Checker('camera_audit: old behaviour, page window from the timeline, built-and-painted set checks')


def run(*args):
    found = subprocess.run([sys.executable, '-I', '-B', AUDIT, *args], capture_output=True, text=True)
    return found.returncode, found.stdout, found.stderr


def smoother(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (x * 6 - 15) + 10)


def still_shot_log(start, end, move_from, move_to, until, name='shot', page=1, step_seconds=0.1):
    """A camera log as render-paper-film.mjs writes it, for one kit.stillShot with one move (three.js position, target,
    fov; positions and targets eased together with the kit's smoother step)."""
    samples, t = [], 0.0
    while t <= until + 1e-9:
        k = smoother((t - move_from) / (move_to - move_from)) if t > move_from else 0.0
        lerp = lambda a, b: [a[i] + (b[i] - a[i]) * k for i in range(3)]
        samples.append({'page': page, 't': round(t, 4), 'shot': name, 'position': lerp(start['position'], end['position']),
                        'target': lerp(start['target'], end['target']), 'fov': start['fov'] + (end['fov'] - start['fov']) * k, 'focus': start.get('focus', 5)})
        t += step_seconds
    return {'scene': 'test', 'fps': 30, 'step': int(round(step_seconds * 30)), 'page_edges': [], 'samples': samples}


def write(data):
    path = os.path.join(work_folder('camera-audit-'), 'camera.json')
    with open(path, 'w') as handle:
        json.dump(data, handle)
    return path


def pose_from_blender(position, forward, fov):
    p3 = geometry.to_three(position)
    return {'position': p3, 'target': [p3[i] + 10 * geometry.to_three(forward)[i] for i in range(3)], 'fov': fov}


# ------------------------------------------------------------------------------------------------ old behaviour unchanged
excerpt = os.path.join(OURS, 'old-chapter-2-before-camera-pages-1-6-8.json')
code, out, _ = run(excerpt)
expected = open(os.path.join(OURS, 'old-chapter-2-before-pages-1-6-8-audit-by-old-tool.txt')).read()
check.true('old chapter 2, pages 1, 6 and 8 before the camera rule: the same report, word for word, as the old tool', out == expected and code == 1,
           details=out.strip().splitlines()[-1], recorded='tests/fixtures/effects-camera-light/old-chapter-2-before-pages-1-6-8-audit-by-old-tool.txt '
           '(the plugin kit\'s camera_audit.py before this change, commit 4e2c97b)', proves='the extension leaves the old audit as it was')
for label, (log, record) in OLD_LOGS.items():
    if os.path.exists(log) and os.path.exists(record):
        if label == 'round 4 film':   # the round 4 helper audited pages 3, 4 and 5 one by one (audit.txt holds the three reports)
            out = ''.join(run(log, '--page', str(n))[1] for n in (3, 4, 5))
        else:
            code, out, _ = run(log)
        recorded = open(record).read()
        same = out == recorded or out.strip() == recorded.strip()
        check.true(f'{label}: the whole log audits exactly as recorded at the time', same, details=out.strip().splitlines()[-1],
                   recorded=record, proves='the old behaviour is unchanged on a whole chapter (the record was printed by the old tool)')
    else:
        check.note(f'{label}: {log} is not here; skipped')
if os.path.exists(OLD_LOGS['before'][0]):
    code, out, _ = run(OLD_LOGS['before'][0])
    check.equal('before the camera rule: problems', out.strip().splitlines()[-1], '9 problem(s)', recorded='notes story log 20 ("9 shots break it")')
if os.path.exists(AFTER_LOG):
    code, out, _ = run(AFTER_LOG)
    check.true('after the camera rule: 21 shots, 0 problems', out.count('  shot ') == 21 and out.strip().endswith('0 problem(s)') and code == 0,
               details=f'{out.count("  shot ")} shots; {out.strip().splitlines()[-1]}', recorded='notes story log 20 ("21 shots, 0 problems")')
else:
    check.note(f'{AFTER_LOG} is not here; the 21-shot check was skipped')
code, out, _ = run()
check.true('no arguments: the old one-line use and exit 1', code == 1 and out.startswith('Use: python3 -I camera_audit.py'), recorded='the old tool')
code, out, _ = run('--help')
check.true('--help explains the new options', code == 0 and '--built-set' in out and '--timeline' in out)

# ------------------------------------------------------------------------------------------------ the page window from the timeline
timeline = json.load(open(os.path.join(KIT, 'examples', 'inflation-chapter-2', 'timeline.json')))
pages_folder = os.path.join(KIT, 'paper-film', 'scenes', 'inflation-chapter-2')
spans = json.load(open(os.path.join(OURS, 'old-chapter-2-after-page-spans.json')))
edges = spans['page_edges']
worst_edge, worst_span = 0.0, 0.0
for number in range(1, 11):
    window = audit.page_window(timeline, number, settings, pages_folder)
    if number < 10:
        worst_edge = max(worst_edge, abs(window['to'] - edges[number - 1]))
    if number > 1:
        worst_edge = max(worst_edge, abs(window['from'] - edges[number - 2]))
    first, last = spans['page_spans'][str(number)]
    worst_span = max(worst_span, max(0.0, window['from'] - first, last - window['to']), max(0.0, first - window['from'] - spans['step_seconds'] - 1e-6),
                     max(0.0, window['to'] - last - spans['step_seconds'] - 1e-6))
check.within('page windows from the timeline and page files against the stage\'s own page edges (largest difference, s)', worst_edge, 0, 1e-6,
             recorded='old-chapter-2-after-camera-log.json.gz page_edges (cinema-chapter.js joins; copied to old-chapter-2-after-page-spans.json)',
             proves='the window rule (last word + join wait + join length) is the stage\'s own, worked out without the browser')
check.within('each page\'s samples lie inside its window, missing at most one 0.1 s sample at either end (s)', worst_span, 0, 1e-6,
             recorded='old-chapter-2-after-page-spans.json page_spans')
window5 = audit.page_window(timeline, 5, settings, pages_folder)
check.true('page 5\'s plan window is first word - 0.8 s to last word + 1.3 s', abs(window5['plan_from'] - (timeline['pages'][4]['first_word_at'] - 0.8)) < 1e-9
           and abs(window5['plan_to'] - (timeline['pages'][4]['last_word_end_at'] + 1.3)) < 1e-9, recorded='film-settings.json timing.camera_plan_window_seconds '
           '(Plan 34 "Between pages")', proves='repeats the setting')
if os.path.exists(SINGLE_PAGE_LOG):
    code_a, typed, _ = run(SINGLE_PAGE_LOG, '--window', '95.2', '128.4')
    code_b, worked, _ = run(SINGLE_PAGE_LOG, '--timeline', os.path.join(KIT, 'examples', 'inflation-chapter-2', 'timeline.json'), '--page', '5',
                            '--page-files', pages_folder)
    body = '\n'.join(l for l in worked.splitlines() if not l.startswith('page 5 is on screen') and not l.startswith('settings used')) + '\n'
    check.true('a single-page test log: the timeline window gives the same audit as the window a person typed', body == typed and code_a == code_b,
               recorded='old-chapter-2-page-5-camera-log.json.gz (log 20, typed window 95.2-128.4)', proves='nobody needs to type the window')
else:
    check.note(f'{SINGLE_PAGE_LOG} is not here; the typed-window comparison was skipped')

# ------------------------------------------------------------------------------------------------ built set: round 4's filmed W1 slide
r4 = json.load(open(os.path.join(OURS, 'round4-works-w1.json')))
painted = [f'--painted={p["name"]}={p["point"][0]},{p["point"][1]},{p["point"][2]}' for p in r4['painted_points']]
code, out, _ = run(os.path.join(OURS, 'round4-film-camera-pages-3-4.json'), '--page', '3', '--built-set', '--shot', '3b', '--street', '0,1,0',
                   '--projector', os.path.join(OURS, 'works-camera-w1-round4.json'), '--floor', '0.135', *painted, '--json')
found = json.loads(out)
move = next(r for r in found['built_set'] if r['words'] != 'held')
check.true('round 4 W1 slide as filmed: the camera log still audits 0 problems (every third frame)', found['problems'] == 0,
           recorded='round4-film-audit-by-old-tool.txt (the round 4 helper\'s audit.txt; page 3: 2 shots, 1 move, 0 problems)')
check.within('round 4 W1 slide: turn during the move (degrees)', move['turn_degrees'], 0, 1e-6,
             recorded='working files redesign/round4-film/camera/facing.txt ("turns at most 0.0000 degrees")', proves='the turn test reads the filmed log as the round 4 helper did')
check.within('round 4 W1 slide: meeting point drift', move['meeting_point_drift'], 0, 1e-6, recorded='rule 11; facing.txt')
check.close('round 4 W1 slide: the nearest painted man comes nearer', move['magnification'], 7.2 / 6.0, 0.005,
            recorded='works-shot.json at commit 34756a4: man-7\'s feet at y 16.2, the slide 9.0 -> 10.2', proves='repeats depth over depth; passes the 1.286 limit')
tan = lambda v: math.tan(math.radians(v) / 2)
static_margin = (1 - tan(60.4) / tan(64.4)) / 2
check.close('round 4 W1 slide: the frame stays inside the plate by', move['plate_margin'], static_margin, 0.0005,
            recorded='closed form: (1 - tan(30.2) / tan(32.2)) / 2 for the film lens inside the plate lens at the plate spot',
            proves='the ray check agrees with the closed form where the two must agree (the slide\'s start); the forward slide never brings the frame nearer the edge')
code, out, _ = run(os.path.join(OURS, 'round4-film-camera-pages-3-4.json'), '--page', '3', '--built-set', '--shot', '3a', '--street', '0,1,0', '--json')
held = json.loads(out)['built_set']
check.true('round 4 page 3\'s held W3 shot gets one "held" row (no move to judge)', len(held) == 1 and held[0]['words'] == 'held' and not held[0]['problems'],
           details=str([(r['words'], r['problems']) for r in held]))

# ------------------------------------------------------------------------------------------------ built set: log 29's turning clip
lockout = json.load(open(os.path.join(OURS, 'lockout-camera.json')))
q = lockout['quaternion']
projector = geometry.camera_from_three(lockout['position'], q, lockout['fov'], 1080, 1920)
P3 = lockout['position']
forward3 = geometry.to_three(projector['forward'])
right3 = geometry.to_three(projector['right'])
ahead = geometry.normalise([forward3[0], 0, forward3[2]])
side = geometry.normalise([right3[0], 0, right3[2]])
end_position = [P3[i] + 1.4 * ahead[i] + 0.3 * side[i] + (0.05 if i == 1 else 0) for i in range(3)]


def turn_about(v, axis, degrees):
    axis = geometry.normalise(axis)
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [v[i] * c + geometry.cross(axis, v)[i] * s + axis[i] * geometry.dot(axis, v) * (1 - c) for i in range(3)]


look = turn_about(forward3, [0, 1, 0], -5)
look = turn_about(look, geometry.normalise(geometry.cross(look, [0, 1, 0])), -1.5)
start = {'position': P3, 'target': [P3[i] + 10 * forward3[i] for i in range(3)], 'fov': 40, 'focus': 9}
end = {'position': end_position, 'target': [end_position[i] + 10 * look[i] for i in range(3)], 'fov': 26, 'focus': 9}
clip = write(still_shot_log(start, end, 2.0, 7.2, 12.0, 'up the street'))
code, out, _ = run(clip, '--built-set', '--street', '0,1,0.069927', '--projector', os.path.join(OURS, 'lockout-camera.json'), '--floor', '0', '--json')
row = json.loads(out)['built_set'][0]
check.true('log 29\'s clip (rebuilt from lockout-test.js: 1.4 m up the street, turning 5 degrees right and 1.5 down) is refused for turning',
           any('turns' in p for p in row['problems']), details=f'turn {row["turn_degrees"]:.2f} degrees', recorded='lockout-test.js lines 141-149; story log 30 '
           '("the move turned")', proves='the turn test catches the move the log 30 critics found')
check.true('and for moving where the lines meet', any('lines meet' in p for p in row['problems']), details=f'drift {row["meeting_point_drift"]:.3f} of the width',
           recorded='story log 30: the turn slid the meeting point onto the colliery door; rule 11 (at most 0.02)', proves='the drift test catches it')
check.true('its narrowing lens keeps the frame inside the 44-degree plate', row['plate_margin'] > 0, details=f'closest {row["plate_margin"]:.3f} from the plate\'s edge',
           recorded='lockout-test.js lines 9-12 ("the frame never leaves the painted area (the narrower lens is what lets it turn at all)")',
           proves='the plate check agrees with what log 29 built on purpose')
check.note(f'log 29\'s clip ends {row["plate_margin"]:.3f} from the plate\'s edge: ' + ('inside the 0.03 fade too' if row['plate_margin'] >= 0.03 else
           'inside the painting but within its 0.03 faded edge, so the audit also lists it'))

# ------------------------------------------------------------------------------------------------ built set: a turn under a 44-degree plate
plate44 = write({'position': [0, 1.7, 0], 'quaternion': [0, 0, 0, 1], 'fov': 44, 'aspect': 0.5625})


def turned(degrees):
    yaw = [math.sin(math.radians(degrees)), 0, -math.cos(math.radians(degrees))]
    start = {'position': [0, 1.7, 0], 'target': [0, 1.7, -10], 'fov': 40}
    end = {'position': [0, 1.7, 0], 'target': [10 * yaw[0], 1.7, 10 * yaw[2]], 'fov': 40}
    code, out, _ = run(write(still_shot_log(start, end, 1.0, 3.0, 4.0)), '--built-set', '--projector', plate44, '--json')
    return json.loads(out)['built_set'][0]


check.true('a 1.5 degree turn with a 40-degree lens under a 44-degree plate leaves the plate', turned(1.5)['plate_margin'] < 0,
           details=f'{turned(1.5)["plate_margin"]:.4f} from the edge', recorded='design (log 35): "Log 29 plate (44 deg against the film\'s 40): a 1.5 deg turn '
           'leaves the plate (allowance 1.23 deg)"', proves='the plate check catches a turn past the plate')
low, high = 0.5, 2.0
for _ in range(14):
    middle = (low + high) / 2
    low, high = (middle, high) if turned(middle)['plate_margin'] > 0 else (low, middle)
allowance = geometry.turn_allowance_degrees(40, 44, 1080, 1920)['turn_each_way_degrees']
check.close('the largest turn that stays on the plate, found by the ray check (degrees)', (low + high) / 2, allowance, 0.01,
            recorded='frame_geometry.turn_allowance_degrees(40, 44) = 1.233 (core closed form; lesson 90: about 1 degree)',
            proves='two separate methods (rays through the frame\'s corners; half the difference of the lenses\' widths) agree')
low2, high2 = 0.0, 2.0
for _ in range(14):
    middle = (low2 + high2) / 2
    low2, high2 = (middle, high2) if turned(middle)['plate_margin'] > 0.03 else (low2, middle)
check.note(f'keeping out of the painting\'s faded edge (0.03, projected-set.js frameEdge) a 40-degree lens may turn only about {low2:.2f} degrees '
           'under a 44-degree plate, not the 1.23 degrees to its edge')

# ------------------------------------------------------------------------------------------------ built set: the notice corner and checkout C1
notice_facts = os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')
notice = json.load(open(notice_facts))
view = notice['views'][0]
forward = geometry.camera_from_place_facts(notice, settings, view['name'], 'composed', 'film')['forward']
clip = write(still_shot_log(pose_from_blender(view['slide']['start'], forward, 60.4), pose_from_blender(view['slide']['end'], forward, 60.4), 2.0, 8.4, 10.0,
                            'slide to the notice'))
code, out, _ = run(clip, '--built-set', '--place-facts', notice_facts, '--view', view['name'], '--json')
row = json.loads(out)['built_set'][0]
check.close('notice corner slide: the pail comes nearer', row['magnification'], 1.45, 0.006, recorded='skeptic (log 35) "pail 1.45x"; core test_frame_geometry '
            '(1.4525)', proves='only repeats the core\'s sum, through camera samples instead of the place facts\' slide')
check.true('the over-limit pail is reported as accepted by the user, not counted', not row['problems'] and any('accepted' in n for n in row.get('notes', [])),
           details='; '.join(row.get('notes', [])), recorded='notice-corner-place-facts.json accepted: slide_magnification 1.45 (decision 38: "Yes keep it")',
           proves='the audit reads the place\'s accepted list')
check.within('notice corner slide: turn and drift', max(row['turn_degrees'], row['meeting_point_drift']), 0, 1e-6, recorded='story log 32 ("the camera never turns")')

checkout = json.load(open(os.path.join(FIXTURES, 'checkout-c1', 'checkout-shot.json')))
c1 = checkout['views']['c1']
spots = [f'--painted={name}={p[0]},{p[1]},{p[2]}' for name, p in checkout['spots'].items() if name not in ('petrol-fascia', 'checkout-sign')]
clip = write(still_shot_log(pose_from_blender(c1['plate'], [0, 1, 0], 60.4), pose_from_blender(c1['composed'], [0, 1, 0], 60.4), 1.0, 4.0, 6.0, 'c1'))
code, out, _ = run(clip, '--built-set', '--street', '0,1,0', '--projector', os.path.join(FIXTURES, 'checkout-c1', 'checkout-camera-c1.json'), '--floor', '0', *spots, '--json')
row = json.loads(out)['built_set'][0]
check.close('hold-out, checkout C1\'s planned 0.7 m slide: the divider comes nearer', row['magnification'], 1.308, 0.002,
            recorded='core report (log 35): "C1\'s 0.7 m slide is 1.7% over the painting\'s limit at the divider bar (1.308)"',
            proves='the audit judges at the nearest painted thing, not the subject (the checkout helper judged the basket: 1.292)')
check.true('hold-out: the slide is refused (1.7% over, past the 1% "on the limit" band) with the longest safe slide named', any('0.65 m' in p for p in row['problems']),
           details='; '.join(row['problems']), recorded='core report: "The longest safe slide is 0.65 m"', proves='the same verdict as the core\'s slide command, on a place the rules were not built from')

check.finish()
