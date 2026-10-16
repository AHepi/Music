"""What this does: proves the page-side twin kit/paper-film/scenes/frame-geometry.js gives the same answers as
frame_geometry.py. It makes a few thousand cases (fixed seed: the same every run) from the project's real cameras and
from random ones (turned, tilted, leaning, aimed at a point, from Blender and three.js quaternions; points in front,
off the frame and behind the camera), runs them through both, and compares every number (to 1e-9) and every yes/no.
It needs node (skipped, exit 77, without it). Run: python3 kit/calculators/tests/test_frame_geometry_parity.py
(FRAME_GEOMETRY_JS=OTHER.js runs it against another copy, to see that it does catch a difference.)
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, TESTS, CALCULATORS, skip  # noqa: E402
import frame_geometry as g  # noqa: E402

TITLE = 'frame geometry: Python and JavaScript give the same numbers'
NODE = shutil.which('node')
if not NODE:
    skip(TITLE, 'node is not installed, so the JavaScript twin cannot be run here')
SCRIPT = os.environ.get('FRAME_GEOMETRY_JS') or os.path.join(os.path.dirname(CALCULATORS), 'paper-film', 'scenes', 'frame-geometry.js')
RUNNER = os.path.join(TESTS, 'frame_geometry_parity_runner.mjs')
random.seed(35)


def fixture(*parts):
    with open(os.path.join(FIXTURES, *parts)) as handle:
        return json.load(handle)


def r(low, high):
    return random.uniform(low, high)


def point():
    return [r(-30, 30), r(-30, 60), r(-5, 30)]


cameras = []
works4, notice = fixture('works', 'works-camera-w4.json'), fixture('notice-corner', 'notice-corner-camera.json')
cameras.append({'from': 'blender_quaternion', 'args': [works4['blender']['location'], works4['blender']['rotation_quaternion_wxyz'], 64.4, 1080, 1920, 'w4']})
cameras.append({'from': 'blender_quaternion', 'args': [notice['blender']['location'], notice['blender']['rotation_quaternion_wxyz'], 60.4, 1080, 1920, 'notice']})
cameras.append({'from': 'three', 'args': [notice['position'], notice['quaternion'], 64.4, 1080, 1920, 'notice three']})
cameras.append({'from': 'turn', 'args': [[3.1, 17.85, 3.1882], 6.87, 0.0, 0.0, 60.4, 1080, 1920, 'notice end']})
for k in range(8):
    cameras.append({'from': 'turn', 'args': [point(), r(-180, 180), r(-30, 30), r(-10, 10), r(20, 90), random.choice([1080, 1536]),
                                             random.choice([1920, 2730]), f'random {k}']})
for k in range(4):
    cameras.append({'from': 'looking_at', 'args': [point(), point(), r(20, 90), 1080, 1920, f'aimed {k}']})

cases = []


def add(function, args, camera=None, cameras_=None):
    cases.append({'id': len(cases), 'function': function, 'args': args, 'camera': camera, 'cameras': cameras_})


for cam in cameras:
    add('camera', [], cam)
    add('camera_angles', [], cam)
    for _ in range(40):
        add('project_point', [point()], cam)
    for _ in range(10):
        add('project_direction', [[r(-1, 1), r(-1, 1), r(-1, 1)]], cam)
    low = point()
    add('project_box', [[[low[0] + dx, low[1] + dy, low[2] + dz] for dx in (0, 2) for dy in (0, 3) for dz in (0, 1.5)]], cam)
    for _ in range(5):
        depth = r(0.5, 80)
        add('metres_per_pixel', [depth], cam)
        add('size_in_pixels', [r(0.01, 30), depth], cam)
        add('size_needed', [r(5, 500), depth], cam)
        add('distance_for_size', [r(0.01, 30), r(5, 500)], cam)
        add('frame_share', [r(0.01, 20), depth], cam)
        add('distance_for_width_share', [r(0.1, 10), r(0.05, 0.9)], cam)
for _ in range(60):
    fov, width, height = r(20, 90), random.choice([1080, 1536]), random.choice([1920, 2730])
    meeting = r(0.3, 0.6)
    add('focal_length_pixels', [fov, height])
    add('horizontal_fov_degrees', [fov, width, height])
    add('meeting_point_level', [r(-40, 40), r(-0.2, 0.2), fov, width, height])
    add('turn_for_meeting_point', [r(0, 1), fov, width, height])
    add('turn_moves_per_degree', [fov, width, height])
    add('ground_point_down', [r(0.5, 60), r(0.2, 8), meeting, fov, height])
    add('reach_distance', [r(0.2, 1.0), r(0.2, 8), meeting, fov, height])   # some give None (the surface never comes that low)
    add('eye_needed', [r(0.5, 60), r(0.5, 1.0), meeting, r(0, 5), fov, height])
    add('slide_for_screen_shift', [r(-0.3, 0.3), r(0.5, 60), fov, width, height])
    near = r(1, 10)
    add('parallax_sideways_pixels', [r(0, 1), near, near + r(0.1, 20), fov, height])
    add('parallax_forward_pixels', [r(-500, 500), r(0, 0.9), near, near + r(0.1, 20)])
    add('slide_limit', [r(1500, 3000), height, fov, fov + r(0, 10)])
    add('longest_slide', [near, r(1.0, 1.5)])
    add('turn_allowance_degrees', [fov, fov + r(0, 10), width, height])
    add('sideways_allowance_metres', [near, fov, fov + r(0, 10), width, height])
    add('to_three', [point()])
    add('from_three', [point()])
for k in range(10):
    end = {'from': 'turn', 'args': [point(), r(-180, 180), 0.0, 0.0, 60.4, 1080, 1920, 'end']}
    start = dict(end, args=[point()] + end['args'][1:])
    add('slide_magnifications', [[[f'p{j}', point()] for j in range(6)]], cameras_=[start, end])

python_side = {'camera': None}


def build(spec):
    builder = {'turn': g.camera_from_turn, 'looking_at': g.camera_looking_at, 'blender_quaternion': g.camera_from_blender_quaternion,
               'three': g.camera_from_three}[spec['from']]
    return builder(*spec['args'])


def run_python(case):
    if case['function'] == 'camera':
        return build(case['camera'])
    function = getattr(g, case['function'])
    if case['function'] == 'slide_magnifications':
        return function(build(case['cameras'][0]), build(case['cameras'][1]), case['args'][0])
    args = ([build(case['camera'])] if case['camera'] else []) + case['args']
    return function(*args)


def snake(key):
    return re.sub(r'([A-Z])', lambda m: '_' + m.group(1).lower(), key)


def differences(a, b, where=''):
    """Every place two results differ (numbers by more than 1e-9, relative for large ones)."""
    if isinstance(a, dict) and isinstance(b, dict):
        b = {snake(k): v for k, v in b.items()}
        found = [f'{where}.{k}: only in one' for k in set(a) ^ set(b)]
        for k in set(a) & set(b):
            found += differences(a[k], b[k], f'{where}.{k}')
        return found
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return [f'{where}: {len(a)} items against {len(b)}']
        return [d for k, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, f'{where}[{k}]')]
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str) or isinstance(b, str):
        return [] if a == b else [f'{where}: {a!r} against {b!r}']
    if abs(a - b) > 1e-9 * max(1.0, abs(a), abs(b)):
        return [f'{where}: {a!r} against {b!r}']
    return []


check = Checker(TITLE)
expected = [run_python(case) for case in cases]
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, 'cases.json')
    with open(path, 'w') as handle:
        json.dump(cases, handle)
    run = subprocess.run([NODE, RUNNER, path, SCRIPT], capture_output=True, text=True, timeout=300)
if run.returncode != 0:
    check.true('node ran the JavaScript twin', False, details=run.stderr[-800:])
    check.finish()
answers = {a['id']: a for a in json.loads(run.stdout)}
errors = [a for a in answers.values() if 'error' in a]
check.true('every case ran in JavaScript', not errors, details=f'{len(answers)} answers, {len(errors)} errors' + (f': {errors[:3]}' if errors else ''))
by_function, bad = {}, []
for case, value in zip(cases, expected):
    answer = answers.get(case['id'], {})
    found = differences(value, answer.get('value')) if 'value' in answer else ['no answer']
    by_function.setdefault(case['function'], [0, 0])
    by_function[case['function']][0] += 1
    if found:
        by_function[case['function']][1] += 1
        bad.append((case['function'], found[:2]))
for function, (count, wrong) in sorted(by_function.items()):
    check.true(f'{function}: {count} cases agree', wrong == 0, details=f'{count - wrong} of {count} agree' + (f'; e.g. {[b for b in bad if b[0] == function][0][1]}' if wrong else ''),
               proves='the page-side sums are the same sums as the calculators\' (no drift between the two copies)')
behind = sum(1 for case, value in zip(cases, expected) if case['function'] == 'project_point' and not value['in_front'])
none_reach = sum(1 for case, value in zip(cases, expected) if case['function'] == 'reach_distance' and value is None)
check.true('the cases include points behind the camera and surfaces that never reach', behind > 0 and none_reach > 0,
           details=f'{behind} points behind a camera, {none_reach} reaches that cannot happen (both sides must say so the same way)')
check.note(f'{len(cases)} cases from {len(cameras)} cameras; node {subprocess.run([NODE, "--version"], capture_output=True, text=True).stdout.strip()}')
check.finish()
