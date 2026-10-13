# What this does: checks the camera rule on a filmed chapter: "stay still unless it's essential",
# and at most 3 camera moves per shot (a shot runs from one cut to the next). It reads where the
# camera is every few frames (made by render-paper-film.mjs SCENE --camera FILE.json), finds the cuts,
# finds each stretch where the camera moves, names each move in the camera grammar (zoom in or out,
# pan left, right, up or down, move up or down, slide sideways) and prints one block per page. A shot
# with more than 3 moves, or a camera that never settles, is marked PROBLEM.
#
# Use: python3 -I camera_audit.py CAMERA.json [--page N] [--window FROM TO]
#   --window keeps only moments between FROM and TO seconds (needed when the camera file was made from
#   a single-page test scene, e.g. PAPER_FILM_PAGES=5 ... cinema-test-pages --camera FILE.json, where
#   the one page is asked about the whole chapter's time)
#
# How a move is found: between two samples the camera counts as moving when its aim turns faster than
# 0.6 degrees a second, or it travels more than 1.2% of its distance to what it looks at per second, or
# the lens widens or narrows by more than 1.2% a second. Moving stretches less than 0.35 s apart are
# one move. A jump bigger than a quarter of that distance, or a turn of more than 8 degrees, between
# two samples is a cut, and so is a change of still shot (pages made with kit.stillShot name theirs).

import json
import math
import sys

TURN_LIMIT = 0.6        # degrees a second
TRAVEL_LIMIT = 0.012    # share of the distance to the target, a second
LENS_LIMIT = 0.012      # share of the lens angle, a second
JOIN_GAP = 0.35         # seconds
CUT_JUMP = 0.25         # share of the distance to the target
CUT_TURN = 8.0          # degrees


def reference_distance(sample):
    """How far away the thing being watched is: the focus distance when known (in painted rooms the
    camera aims at a point far behind the picture, so the aim distance would make real moves look tiny)."""
    focus = sample.get('focus')
    if isinstance(focus, (int, float)) and focus > 0: return focus
    return length(subtract(sample['target'], sample['position'])) or 1.0


def subtract(a, b): return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
def length(a): return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
def unit(a):
    n = length(a) or 1.0
    return [a[0] / n, a[1] / n, a[2] / n]


def angle_between(a, b):
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(unit(a), unit(b)))))
    return math.degrees(math.acos(dot))


def heading_and_pitch(view):
    v = unit(view)
    heading = math.degrees(math.atan2(v[0], -v[2]))     # 0 = looking along -z, positive = turned right
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, v[1]))))
    return heading, pitch


def describe(first, last):
    """Name a move from the camera before it to the camera after it."""
    words = []
    view_a, view_b = subtract(first['target'], first['position']), subtract(last['target'], last['position'])
    distance_a = reference_distance(first)
    heading_a, pitch_a = heading_and_pitch(view_a)
    heading_b, pitch_b = heading_and_pitch(view_b)
    turn = (heading_b - heading_a + 180) % 360 - 180
    if turn > 2.5: words.append('pan right')
    if turn < -2.5: words.append('pan left')
    if pitch_b - pitch_a > 2.5: words.append('pan up')
    if pitch_b - pitch_a < -2.5: words.append('pan down')
    travel = subtract(last['position'], first['position'])
    forward = sum(x * y for x, y in zip(travel, unit(view_a)))
    lens = (last['fov'] - first['fov']) / first['fov']
    if forward > 0.08 * distance_a or lens < -0.06: words.append('zoom in')
    if forward < -0.08 * distance_a or lens > 0.06: words.append('zoom out')
    if travel[1] > 0.08 * distance_a: words.append('move up')
    if travel[1] < -0.08 * distance_a: words.append('move down')
    side = unit([-view_a[2], 0, view_a[0]])   # to the camera's right
    sideways = sum(x * y for x, y in zip(travel, side))
    if abs(sideways) > 0.12 * distance_a: words.append('slide right' if sideways > 0 else 'slide left')
    return ' + '.join(words) or 'small drift'


def audit(data, only_page=None, window=None):
    seconds_per_sample = data['step'] / data['fps']
    samples = [s for s in data['samples'] if s and 'position' in s]
    if window: samples = [s for s in samples if window[0] <= s['t'] <= window[1]]
    plans = {p['page']: p['plans'] for p in data.get('plans', [])}
    problems = 0
    pages = sorted({s['page'] for s in samples})
    for page in pages:
        if only_page is not None and page != only_page: continue
        page_samples = [s for s in samples if s['page'] == page]
        # shots: split at cuts
        shots, current = [], [page_samples[0]]
        for a, b in zip(page_samples, page_samples[1:]):
            distance = reference_distance(a)
            jump = length(subtract(b['position'], a['position'])) / distance
            turn = angle_between(subtract(a['target'], a['position']), subtract(b['target'], b['position']))
            if jump > CUT_JUMP or turn > CUT_TURN or a.get('shot') != b.get('shot'):
                shots.append(current); current = []
            current.append(b)
        shots.append(current)
        print(f'page {page}: {page_samples[0]["t"]:.1f}-{page_samples[-1]["t"]:.1f} s, {len(shots)} shot(s)')
        for number, shot in enumerate(shots, 1):
            moving = []
            for a, b in zip(shot, shot[1:]):
                dt = b['t'] - a['t'] or seconds_per_sample
                view_a, view_b = subtract(a['target'], a['position']), subtract(b['target'], b['position'])
                distance = reference_distance(a)
                turn = angle_between(view_a, view_b) / dt
                travel = length(subtract(b['position'], a['position'])) / distance / dt
                lens = abs(b['fov'] - a['fov']) / a['fov'] / dt
                moving.append(turn > TURN_LIMIT or travel > TRAVEL_LIMIT or lens > LENS_LIMIT)
            # moving stretches, joined when close
            stretches, start = [], None
            for i, is_moving in enumerate(moving):
                if is_moving and start is None: start = i
                if not is_moving and start is not None: stretches.append([start, i]); start = None
            if start is not None: stretches.append([start, len(moving)])
            joined = []
            for s in stretches:
                if joined and (shot[s[0]]['t'] - shot[joined[-1][1]]['t']) < JOIN_GAP: joined[-1][1] = s[1]
                else: joined.append(s)
            moves = [(shot[a]['t'], shot[b]['t'], describe(shot[a], shot[b])) for a, b in joined]
            still = (shot[-1]['t'] - shot[0]['t']) - sum(b - a for a, b, _ in moves)
            verdict = ''
            if len(moves) > 3:
                verdict = '  PROBLEM: more than 3 moves'; problems += 1
            elif moves and still < 0.25 * (shot[-1]['t'] - shot[0]['t']):
                verdict = '  PROBLEM: hardly ever still'; problems += 1
            label = f' ({shot[0]["shot"]})' if shot[0].get('shot') else ''
            print(f'  shot {number}{label}: {shot[0]["t"]:.1f}-{shot[-1]["t"]:.1f} s, {len(moves)} move(s), still {still:.1f} s{verdict}')
            for a, b, words in moves:
                print(f'    {a:6.2f}-{b:6.2f} s  {words}')
        for plan in plans.get(page, []):
            kinds = ', '.join(f'{m["kind"]} {m["from"]:.1f}-{m["to"]:.1f}' for m in plan['moves']) or 'no moves'
            print(f'  planned ({plan["name"]}): {kinds}')
    print(f'{problems} problem(s)')
    return problems


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Use: python3 -I camera_audit.py CAMERA.json [--page N] [--window FROM TO]'); sys.exit(1)
    data = json.load(open(sys.argv[1]))
    only = int(sys.argv[sys.argv.index('--page') + 1]) if '--page' in sys.argv else None
    window = None
    if '--window' in sys.argv:
        i = sys.argv.index('--window'); window = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
    sys.exit(1 if audit(data, only, window) else 0)
