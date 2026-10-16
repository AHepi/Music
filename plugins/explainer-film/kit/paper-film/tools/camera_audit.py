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
#   --timeline timeline.json (with --page N) works the page's window out instead of you typing it: the page
#   shows from the moment the page before it has turned (its last word + its join's wait and length) until it
#   has turned itself; the joins come from the page files (--page-files FOLDER: page-N.js's "join"), or the
#   chapter's default (film-settings.json timing). It also prints the plan's camera window (first word - 0.8 s
#   to last word + 1.3 s) and names any move outside it.
#
# Built-and-painted sets (--built-set): for every move it also checks the rules of a projected set
# (07 Composing a shot, rule 11; logs 29 to 34), with the core's camera sums (kit/calculators/frame_geometry.py):
#   - the camera never turns during a move (heading and pitch stay put, to within a camera log's rounding);
#   - where the street's lines meet moves no more than 0.02 of the frame's width (it would slide off the subject);
#   - the slide brings the nearest painted surface no more times nearer than the painting's detail allows
#     (painting rows over film rows, through the lenses: 1.29 for Flux's 2672-row paintings);
#   - the frame never leaves the painted plate: every 0.1 s the frame's corners and edge middles, at the nearest
#     painted depth, the ground and far away, must land inside the projector's frame (0.03 from its edge, where the
#     painting fades).
#   Give the place: --place-facts F --view V (the street's direction, the projector spot, the painted points, the
#   painting's height, and its accepted list: an accepted slide_magnification is reported, not counted), or each part:
#   --street x,y,z (Blender), --projector camera.json, --painted NAME=x,y,z, --nearest METRES, --floor Z,
#   --painting-height ROWS. --json prints the result as JSON, --out FILE writes it.
#
# How a move is found: between two samples the camera counts as moving when its aim turns faster than
# 0.6 degrees a second, or it travels more than 1.2% of its distance to what it looks at per second, or
# the lens widens or narrows by more than 1.2% a second. Moving stretches less than 0.35 s apart are
# one move. A jump bigger than a quarter of that distance, or a turn of more than 8 degrees, between
# two samples is a cut, and so is a change of still shot (pages made with kit.stillShot name theirs).
# (These six numbers are kept here as well as in film-settings.json camera.audit_*; calculators/tests/
# test_settings.py fails if the two ever differ.)

import argparse
import json
import math
import os
import re
import sys

TURN_LIMIT = 0.6        # degrees a second
TRAVEL_LIMIT = 0.012    # share of the distance to the target, a second
LENS_LIMIT = 0.012      # share of the lens angle, a second
JOIN_GAP = 0.35         # seconds
CUT_JUMP = 0.25         # share of the distance to the target
CUT_TURN = 8.0          # degrees

TURN_ROUNDING = 0.001  # degrees: a camera log's rounding, not a rule (a slide never turns: film-settings.json camera.turn_during_a_slide_degrees)

HERE = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'calculators')


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


def find_shots(data, only_page=None, window=None):
    """The audit's findings, page by page: shots, their moves (with the samples they span), still time and verdict.
    audit() prints exactly these; the built-set checks read them."""
    seconds_per_sample = data['step'] / data['fps']
    samples = [s for s in data['samples'] if s and 'position' in s]
    if window: samples = [s for s in samples if window[0] <= s['t'] <= window[1]]
    plans = {p['page']: p['plans'] for p in data.get('plans', [])}
    pages = sorted({s['page'] for s in samples})
    found = []
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
        page_found = {'page': page, 'from': page_samples[0]['t'], 'to': page_samples[-1]['t'], 'shots': [], 'plans': plans.get(page, [])}
        for shot in shots:
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
            moves = [{'from': shot[a]['t'], 'to': shot[b]['t'], 'words': describe(shot[a], shot[b]), 'samples': shot[a:b + 1]} for a, b in joined]
            still = (shot[-1]['t'] - shot[0]['t']) - sum(m['to'] - m['from'] for m in moves)
            verdict = ''
            if len(moves) > 3:
                verdict = 'more than 3 moves'
            elif moves and still < 0.25 * (shot[-1]['t'] - shot[0]['t']):
                verdict = 'hardly ever still'
            page_found['shots'].append({'name': shot[0].get('shot'), 'from': shot[0]['t'], 'to': shot[-1]['t'], 'samples': shot,
                                        'moves': moves, 'still': still, 'verdict': verdict})
        found.append(page_found)
    return found


def audit(data, only_page=None, window=None):
    """Prints the audit (one block per page) and returns the number of problems."""
    problems = 0
    for page in find_shots(data, only_page, window):
        print(f'page {page["page"]}: {page["from"]:.1f}-{page["to"]:.1f} s, {len(page["shots"])} shot(s)')
        for number, shot in enumerate(page['shots'], 1):
            if shot['verdict']: problems += 1
            verdict = f'  PROBLEM: {shot["verdict"]}' if shot['verdict'] else ''
            label = f' ({shot["name"]})' if shot['name'] else ''
            print(f'  shot {number}{label}: {shot["from"]:.1f}-{shot["to"]:.1f} s, {len(shot["moves"])} move(s), still {shot["still"]:.1f} s{verdict}')
            for move in shot['moves']:
                print(f'    {move["from"]:6.2f}-{move["to"]:6.2f} s  {move["words"]}')
        for plan in page['plans']:
            kinds = ', '.join(f'{m["kind"]} {m["from"]:.1f}-{m["to"]:.1f}' for m in plan['moves']) or 'no moves'
            print(f'  planned ({plan["name"]}): {kinds}')
    print(f'{problems} problem(s)')
    return problems


# ------------------------------------------------------------------------------------------------ the page window
def read_join(page_files, number):
    """A page's join (after, length) from its page file (`export const join = {...}` or `join: {...}` in build's
    return), or None when the file or its join is not found."""
    if not page_files:
        return None
    path = os.path.join(page_files, f'page-{number}.js')
    if not os.path.exists(path):
        return None
    with open(path) as handle:
        code = handle.read()
    found = re.search(r'join\s*[:=]\s*\{([^}]*)\}', code)
    if not found:
        return None
    after = re.search(r'after\s*:\s*([\d.]+)', found.group(1))
    span = re.search(r'length\s*:\s*([\d.]+)', found.group(1))
    if not after or not span:
        return None
    return float(after.group(1)), float(span.group(1))


def page_window(timeline, number, settings, page_files=None):
    """When page `number` is on screen in the chapter: from the moment the page before it has finished turning (its last
    word + its join's wait + the join's length; 0 for the first page) until this page has finished turning. Also the
    plan's camera window (Plan 34): first word - before, last word + after (film-settings.json timing)."""
    pages = {p['page']: p for p in timeline['pages']}
    if number not in pages:
        raise SystemExit(f'camera_audit: the timeline has no page {number} (pages: {", ".join(str(p) for p in pages)})')
    default = (settings.value('timing.turn_after_last_word_seconds'), settings.value('timing.peel_length_seconds'))
    joins = {}
    for n in pages:
        joins[n] = read_join(page_files, n) or default
    previous = pages.get(number - 1)
    start = previous['last_word_end_at'] + sum(joins[number - 1]) if previous else 0.0
    end = min(pages[number]['last_word_end_at'] + sum(joins[number]), timeline.get('chapter_seconds', math.inf))
    plan = settings.value('timing.camera_plan_window_seconds')
    return {'from': start, 'to': end, 'join': joins[number], 'joins_from': 'page files' if read_join(page_files, number) else 'the default join',
            'plan_from': pages[number]['first_word_at'] - plan['before_first_word'], 'plan_to': pages[number]['last_word_end_at'] + plan['after_last_word_end']}


# ------------------------------------------------------------------------------------------------ built-and-painted sets
def load_calculators():
    if CALCULATORS not in sys.path:
        sys.path.insert(0, CALCULATORS)
    import frame_geometry
    import settings as settings_module
    return frame_geometry, settings_module


def sample_camera(geometry, sample, width, height):
    """A camera from a camera-log sample (three.js position, target and vertical lens), in Blender metres, kept level
    (stillShot cameras have no roll)."""
    return geometry.camera_looking_at(geometry.from_three(sample['position']), geometry.from_three(sample['target']),
                                      sample['fov'], width, height, f't {sample["t"]:.2f}')


def read_projector(geometry, settings, path):
    """The projector (the plate camera) from a camera file (a projector JSON with its Blender place, or only the three.js
    position and quaternion), with the lens the file gives (fov), else the plate lens."""
    with open(path) as handle:
        data = json.load(handle)
    lens = data.get('fov') or settings.value('frame.plate_vertical_fov_degrees')
    width, height = settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels')
    if 'blender' not in data and 'position' in data and 'quaternion' in data:
        return geometry.camera_from_three(data['position'], data['quaternion'], lens, width, height, os.path.basename(path))
    camera = geometry.load_camera(path, settings, str(lens))
    return geometry.with_lens(camera, lens, width, height)


class BuiltSet:
    """What the built-set checks need about the place."""

    def __init__(self, args, geometry, settings):
        self.geometry, self.settings = geometry, settings
        self.street, self.projector, self.painted, self.nearest, self.painting_rows, self.floor = None, None, [], args.nearest, None, None
        self.accepted = {}
        if args.place_facts:
            with open(args.place_facts) as handle:
                facts = json.load(handle)
            views = {v['name']: v for v in facts['views']}
            view = views.get(args.view) if args.view else (next(iter(views.values())) if len(views) == 1 else None)
            if view is None:
                raise SystemExit(f'camera_audit: say which view (--view): {", ".join(views)}')
            lines = facts.get('lines', {})
            self.street = lines.get(facts.get('lines_key')) if facts.get('lines_key') else None
            if view['camera'].get('plate'):
                self.projector = geometry.camera_from_place_facts(facts, settings, view['name'], 'plate', 'plate')
                self.projector = geometry.with_lens(self.projector, self.projector['vertical_fov_degrees'],
                                                    settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels'))
            self.painted = [(p['name'], p['point']) for p in view.get('painted_points', [])]
            returned = (facts.get('painting') or {}).get('returned_size')
            self.painting_rows = returned[1] if returned else None
            self.floor = view['camera'].get('floor_height')
            # the place's accepted exceptions for this view (rule, reason, who, date): reported, not counted
            self.accepted = {a['rule']: a for a in facts.get('accepted', []) if a.get('view') == view['name']}
        if args.street:
            self.street = [float(v) for v in args.street.split(',')]
        if args.projector:
            self.projector = read_projector(geometry, settings, args.projector)
        for item in args.painted or []:
            name, _, point = item.rpartition('=')
            self.painted.append((name or f'point {len(self.painted) + 1}', [float(v) for v in point.split(',')]))
        if args.painting_height:
            self.painting_rows = args.painting_height
        if args.floor is not None:
            self.floor = args.floor
        if self.painting_rows is None:
            self.painting_rows = settings.value('frame.painting_returned_size_pixels')[1]


def frame_rays(geometry, camera):
    """The directions of the frame's 4 corners and 4 edge middles."""
    tan_v = math.tan(math.radians(camera['vertical_fov_degrees']) / 2)
    tan_h = tan_v * camera['frame'][0] / camera['frame'][1]
    rays = []
    for name, a, d in (('top left', -1, 1), ('top', 0, 1), ('top right', 1, 1), ('right', 1, 0), ('bottom right', 1, -1),
                       ('bottom', 0, -1), ('bottom left', -1, -1), ('left', -1, 0)):
        direction = geometry.add(camera['forward'], geometry.add(geometry.scale(camera['right'], a * tan_h), geometry.scale(camera['up'], d * tan_v)))
        rays.append((name, direction))
    return rays


def plate_margin(geometry, place, camera):
    """How far inside the projector's frame the film frame stays at this camera (the smallest distance of any frame
    corner or edge middle, at the nearest painted depth, at the ground and far away, from the projector frame's edge),
    and where the worst one is. Negative: outside."""
    worst = (math.inf, None)
    for name, direction in frame_rays(geometry, camera):
        depths = [1e4]
        if place.nearest:
            depths.append(place.nearest)
        if place.floor is not None and direction[2] < 0:
            t = (place.floor - camera['position'][2]) / direction[2]
            if t > 0:
                depths.append(t * geometry.dot(direction, camera['forward']))
        for depth in depths:
            scale = depth / geometry.dot(direction, camera['forward'])
            point = geometry.add(camera['position'], geometry.scale(direction, scale))
            landed = geometry.project_point(place.projector, point)
            if not landed['in_front']:
                return -1.0, f'{name} at {depth:.1f} m is behind the projector'
            margin = min(landed['across'], 1 - landed['across'], landed['down'], 1 - landed['down'])
            if margin < worst[0]:
                worst = (margin, f'{name} at {"far away" if depth >= 1e4 else f"{depth:.1f} m"}')
    return worst


def check_built_set(found, place, settings):
    """The built-set rules, shot by shot. Each move is judged over its span: from its start (the shot's start, for the
    first move) to the next move's start (or the shot's end), so the slow end of an eased move and the held frame after it
    count too. A shot with no move is checked against the plate only."""
    geometry = place.geometry
    width, height = settings.value('frame.width_pixels'), settings.value('frame.height_pixels')
    turn_tolerance = settings.value('camera.turn_during_a_slide_degrees') + TURN_ROUNDING
    drift_limit = settings.value('camera.meeting_point_drift_during_slide_share_of_width')
    every = settings.value('camera_audit_built_set.plate_check_every_seconds')
    edge = settings.value('frame.plate_frame_edge_fade_share')
    borderline = settings.value('camera.slide_magnification_borderline_share')
    plate_fov = place.projector['vertical_fov_degrees'] if place.projector else settings.value('frame.plate_vertical_fov_degrees')
    results = []
    for page in found:
        for number, shot in enumerate(page['shots'], 1):
            samples_all = shot['samples']
            starts = [samples_all.index(m['samples'][0]) for m in shot['moves']]
            spans = []
            for k, move in enumerate(shot['moves']):
                first = 0 if k == 0 else starts[k]
                last = starts[k + 1] if k + 1 < len(starts) else len(samples_all)
                spans.append((move, starts[k], first, last))
            if not spans:
                spans.append((None, 0, 0, len(samples_all)))
            for move, move_start, first, last in spans:
                moving = samples_all[move_start:last]
                row = {'page': page['page'], 'shot': number, 'shot_name': shot['name'],
                       'from': move['from'] if move else shot['from'], 'to': move['to'] if move else shot['to'],
                       'words': move['words'] if move else 'held', 'turn_degrees': 0.0, 'problems': [], 'notes': []}
                cameras = [sample_camera(geometry, s, width, height) for s in moving]
                if move:
                    base = heading_and_pitch(subtract(moving[0]['target'], moving[0]['position']))
                    row['turn_degrees'] = max(max(abs((heading_and_pitch(subtract(s['target'], s['position']))[0] - base[0] + 180) % 360 - 180),
                                                  abs(heading_and_pitch(subtract(s['target'], s['position']))[1] - base[1])) for s in moving)
                    if row['turn_degrees'] > turn_tolerance:
                        row['problems'].append(f'the camera turns {row["turn_degrees"]:.2f} degrees during the move (a slide never turns)')
                    if place.street:
                        across = [geometry.project_direction(c, place.street) for c in cameras]
                        across = [a['across'] for a in across if a]
                        if across:
                            drift = max(across) - min(across)
                            row['meeting_point_drift'] = drift
                            if drift > drift_limit:
                                row['problems'].append(f'where the lines meet moves {drift:.3f} of the width (at most {drift_limit}): it slides off the subject')
                    if place.painted:
                        start_camera = place.projector or cameras[0]
                        end_camera = cameras[-1]
                        seen = []
                        for name, point in place.painted:
                            landed = geometry.project_point(end_camera, point)
                            if landed['in_front'] and 0 <= landed['across'] <= 1 and 0 <= landed['down'] <= 1:
                                seen.append((name, point))
                        if seen:
                            limit = geometry.slide_limit(place.painting_rows, height, moving[-1]['fov'], plate_fov)
                            found_points = geometry.slide_magnifications(start_camera, end_camera, seen)
                            nearest = min(found_points, key=lambda f: f['depth_end'])
                            worst = max((f for f in found_points if f['magnification']), key=lambda f: f['magnification'])
                            over = worst['magnification'] / limit - 1
                            row.update({'nearest_painted': nearest['name'], 'nearest_depth_end': nearest['depth_end'], 'magnification': worst['magnification'],
                                        'magnified_most': worst['name'], 'limit': limit})
                            if over > borderline and 'slide_magnification' in place.accepted:
                                entry = place.accepted['slide_magnification']
                                row['notes'].append(f'{worst["name"]} {worst["magnification"]:.3f} times nearer (limit {limit:.3f}): accepted by {entry["who"]} '
                                                    f'on {entry["date"]} ({entry["reason"]})')
                            elif over > borderline:
                                row['problems'].append(f'{worst["name"]} comes {worst["magnification"]:.3f} times nearer than in the plate (the painting allows '
                                                       f'{limit:.3f}): it will look soft; the longest slide is {geometry.longest_slide(nearest["depth_end"], limit):.2f} m')
                            elif over > 0:
                                row['notes'].append(f'{worst["name"]} {worst["magnification"]:.3f} times nearer: on the limit ({limit:.3f}); judge it')
                if place.projector:
                    checked = samples_all[first:last]
                    worst_margin, where, when, last_t = math.inf, None, None, None
                    for s in checked:
                        if last_t is not None and s['t'] - last_t < every - 1e-9 and s is not checked[-1]:
                            continue
                        last_t = s['t']
                        margin, spot = plate_margin(geometry, place, sample_camera(geometry, s, width, height))
                        if margin < worst_margin:
                            worst_margin, where, when = margin, spot, s['t']
                    row.update({'plate_margin': worst_margin, 'plate_margin_where': where, 'plate_margin_at': when})
                    if worst_margin < edge:
                        row['problems'].append(f'the frame leaves the painted plate at {when:.2f} s ({where} lands {worst_margin:.3f} from the plate\'s '
                                               f'edge; it must stay {edge} inside, where the painting fades)')
                if shot.get('skip'):
                    row['skip'] = True
                results.append(row)
    return results


def print_built_set(results):
    problems = 0
    print('built-and-painted set checks:')
    if not results:
        print('  no moves')
    for row in results:
        parts = [f'turn {row["turn_degrees"]:.3f} degrees']
        if 'meeting_point_drift' in row:
            parts.append(f'meeting point drift {row["meeting_point_drift"]:.4f}')
        if 'magnification' in row:
            parts.append(f'{row["magnified_most"]} {row["magnification"]:.3f} times nearer (limit {row["limit"]:.3f})')
        if 'plate_margin' in row:
            parts.append(f'frame {row["plate_margin"]:.3f} inside the plate at its closest')
        label = f' ({row["shot_name"]})' if row['shot_name'] else ''
        what = 'held' if row['words'] == 'held' else f'move {row["from"]:.2f}-{row["to"]:.2f} s ({row["words"]})'
        print(f'  page {row["page"]} shot {row["shot"]}{label} {what}: ' + ', '.join(parts)
              + ('' if row['problems'] else ': fine'))
        for note in row.get('notes', []):
            print(f'    note: {note}')
        for problem in row['problems']:
            print(f'    PROBLEM: {problem}')
            problems += 1
    print(f'{problems} built-set problem(s)')
    return problems


def strip(value):
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items() if k != 'samples'}
    if isinstance(value, list):
        return [strip(v) for v in value]
    if isinstance(value, float):
        return round(value, 5)
    return value


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print('Use: python3 -I camera_audit.py CAMERA.json [--page N] [--window FROM TO]'); return 1
    parser = argparse.ArgumentParser(description='Checks the camera rule (at most 3 named moves a shot, still most of the time) on a camera '
                                                 'log, and with --built-set the rules of a built-and-painted set. See the note at the top.')
    parser.add_argument('camera', help='the camera log (render-paper-film.mjs SCENE --camera FILE.json)')
    parser.add_argument('--page', type=int, help='only this page')
    parser.add_argument('--window', type=float, nargs=2, metavar=('FROM', 'TO'), help='only moments between FROM and TO seconds')
    parser.add_argument('--timeline', help='with --page: work the page\'s window out from the timeline (instead of --window)')
    parser.add_argument('--page-files', help='the folder of the page files, for each page\'s join (default: the chapter\'s default join)')
    parser.add_argument('--built-set', action='store_true', help='also check the built-and-painted set rules for every move')
    parser.add_argument('--place-facts', help='the place facts file (street direction, projector spot, painted points, painting size)')
    parser.add_argument('--view', help='the view in the place facts')
    parser.add_argument('--shot', help='with --built-set: only shots whose name contains this (one projector per shot)')
    parser.add_argument('--street', help='the street\'s direction x,y,z (Blender), where its lines meet')
    parser.add_argument('--projector', help='the projector\'s camera file (e.g. works-camera-w1.json)')
    parser.add_argument('--painted', action='append', help='NAME=x,y,z (Blender): a painted thing for the magnification check (repeat)')
    parser.add_argument('--nearest', type=float, help='the nearest painted surface\'s distance (metres), for the plate check')
    parser.add_argument('--floor', type=float, help='the ground\'s height under the camera (Blender z), for the plate check')
    parser.add_argument('--painting-height', type=float, help='the painting\'s rows (default: the place facts, else film-settings.json)')
    parser.add_argument('--settings', help='the settings file (default kit/film-settings.json)')
    parser.add_argument('--json', action='store_true', help='print the findings as JSON instead of the plain report')
    parser.add_argument('--out', help='also write the findings as JSON to this file')
    args = parser.parse_args(argv)
    with open(args.camera) as handle:
        data = json.load(handle)
    window = tuple(args.window) if args.window else None
    uses_settings = args.timeline or args.built_set or args.json or args.out
    settings = None
    if uses_settings:
        geometry, settings_module = load_calculators()
        settings = settings_module.load_settings(args.settings)
    found_window = None
    if args.timeline:
        if args.page is None:
            raise SystemExit('camera_audit: --timeline needs --page N')
        with open(args.timeline) as handle:
            timeline = json.load(handle)
        found_window = page_window(timeline, args.page, settings, args.page_files)
        if window is None:
            window = (found_window['from'], found_window['to'])
    if args.json:
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            problems = audit(data, args.page, window)
    else:
        if found_window:
            print(f'page {args.page} is on screen {found_window["from"]:.2f}-{found_window["to"]:.2f} s (from the timeline; its join waits '
                  f'{found_window["join"][0]} s and lasts {found_window["join"][1]} s, from {found_window["joins_from"]}); the plan\'s camera window is '
                  f'{found_window["plan_from"]:.2f}-{found_window["plan_to"]:.2f} s')
        problems = audit(data, args.page, window)
    found = find_shots(data, args.page, window)
    result = {'camera_log': args.camera, 'window': window, 'page_window': found_window, 'problems': problems, 'pages': strip(found)}
    if found_window:
        outside = [(m['from'], m['to']) for p in found for s in p['shots'] for m in s['moves']
                   if m['from'] < found_window['plan_from'] - 1e-6 or m['to'] > found_window['plan_to'] + 1e-6]
        result['moves_outside_plan_window'] = outside
        if outside and not args.json:
            print('moves outside the plan\'s camera window: ' + ', '.join(f'{a:.2f}-{b:.2f} s' for a, b in outside))
    if args.built_set:
        place = BuiltSet(args, geometry, settings)
        chosen = found
        if args.shot:
            chosen = [dict(page, shots=[s if args.shot in (s['name'] or '') else dict(s, skip=True) for s in page['shots']]) for page in found]
        rows = [r for r in check_built_set(chosen, place, settings) if not r.pop('skip', False)]
        if args.json:
            built = sum(len(r['problems']) for r in rows)
        else:
            built = print_built_set(rows)
        result['built_set'] = strip(rows)
        result['built_set_problems'] = built
        problems += built
    if settings is not None:
        result['settings_file'] = settings.path
        result['settings_used'] = settings.used_json()
        if not args.json:
            print('settings used (film-settings.json): ' + '; '.join(settings.used_lines()))
    if args.json:
        print(json.dumps(result, indent=1))
    if args.out:
        with open(args.out, 'w') as handle:
            json.dump(result, handle, indent=1)
    return 1 if problems else 0


if __name__ == '__main__':
    if CALCULATORS not in sys.path:
        sys.path.insert(0, CALCULATORS)
    from calculator_output import run_main   # a missing or broken input file is answered in one plain sentence (exit 2)
    sys.exit(run_main(main, 'camera_audit'))
