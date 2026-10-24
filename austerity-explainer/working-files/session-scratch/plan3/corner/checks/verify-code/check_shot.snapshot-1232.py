"""What this does: checks a shot against the composing rules ("07 Composing a shot.md") and, if given, a
reference picture, and says exactly what is wrong and what to change, in plain words and metres.

It reads what shot_facts.py measured in Blender (flat colour pictures of every named group of props, the
exact camera, where the street's lines meet, the lights, and what each prop stands on), and optionally the
finished picture of the same frame (for the light rules). It writes:
    report.md     the problems, worst first, each with its numbers and the fix; then what passed, notes,
                  and what this tool does not check
    marked.jpg    the frame with each problem's place drawn on it, numbered as in the report
Use:
    python3 check_shot.py --check shot-check.json --facts FACTS_FOLDER [--picture FRAME.png] --out OUT_FOLDER
(paper-film/tools/check-shot.sh runs Blender and this in one go.)

The check file (see examples/notice-corner/shot-check.json):
    "size"          the frame's width and height in pixels
    "groups"        each prop's name and the name patterns of its objects (* stands for any letters)
    "subject"       the group the shot is about (the notice); "support": what it hangs on (the board)
    "story"         the story props (near, touching, lit); "work": the work props (small, far, dim)
    "pairs_also"    more groups checked for edges that just touch (rule 4), e.g. a lamp post and the winding wheels
    "on_ground"     groups that should stand on the ground; "stands_on": {group: the group it rests on}
    "must_read"     groups with words to read (kept left of 0.90 across)
    "eye_height"    the camera's allowed height above the pavement under it, in metres (default 1.5 to 1.9)
    "box_excludes"  groups left out of rule 3's box (a tall board would set its top edge on its own)
    "lines"         street directions as Blender x, y, z steps (this street rises 0.07 m per metre);
                    "lines_key" says which one the rules use
    "title_zone"    [left, top, right, bottom] fractions of the frame where titles go
    "reference"     optional: the picture to match: where its lines meet; boxes of groups in it
                    ("compare": "top" judges a box's top instead of its middle, for things cut by the
                    frame; "landmark": true marks a building used only to match the camera); and
                    "camera_match" landmarks (points and lines read off the picture, with the same things
                    in Blender metres)
Positions are fractions of the frame: 0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom.
Pixel limits are the rules file's, which are set on a frame 1,536 pixels wide, scaled to this frame's width.
"""
import argparse
import json
import math
import os
import re

import cv2
import numpy as np

# the kinds of problem, and the order to fix them in: the camera moves everything, so it comes first; then props
# resting in the wrong place or missing; then the main rule; then the other composing faults, worst (furthest past
# its limit) first; then the background; then matching the reference
KINDS = ['set-up', 'camera', 'resting', 'missing', 'main', 'lines', 'story', 'edges', 'light', 'background', 'reference']
TIER = {'set-up': 0, 'camera': 1, 'resting': 2, 'missing': 3, 'main': 4, 'lines': 5, 'story': 5, 'edges': 5, 'light': 5,
        'background': 6, 'reference': 7}
COMPOSING = {'main', 'lines', 'story', 'edges', 'light', 'background'}


# ---------------------------------------------------------------------------------------- small helpers
def plain(value, digits=2):
    """A number without a minus sign on zero ("0.0", never "-0.0")."""
    text = f'{value:.{digits}f}'
    return text[1:] if text.startswith('-') and float(text) == 0 else text


def box_of(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def centre_of(mask):
    ys, xs = np.nonzero(mask)
    return float(xs.mean()), float(ys.mean())


def nearest_point(mask, x, y):
    ys, xs = np.nonzero(mask)
    k = int(np.argmin((xs - x) ** 2 + (ys - y) ** 2))
    return float(xs[k]), float(ys[k])


def unit(dx, dy):
    length = math.hypot(dx, dy)
    return (dx / length, dy / length) if length > 1e-6 else (0.0, -1.0)


def capital(text):
    return text[:1].upper() + text[1:]


def without_specks(mask):
    """Keeps the pieces of a prop that really show; drops slivers peeking between other things (for
    example a few pixels of the notice between a chair's slats), which the eye doesn't read."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    if n <= 1:
        return mask
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = np.zeros(n, bool)
    keep[1:] = areas >= max(60, 0.02 * areas.sum())
    return keep[labels]


def without_wires(mask, width):
    """Drops parts thinner than about 6 pixels (on a frame 1,080 wide), such as a lantern's wire handle:
    the eye doesn't read a hairline crossing an edge as a clear overlap."""
    size = max(3, int(round(6 * width / 1080)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel) > 0


def distance_outside(mask):
    """For every pixel, how many pixels it is from the nearest pixel of `mask`."""
    return cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 5)


def distance_inside(mask):
    """For every pixel of `mask`, how many pixels it is from the mask's own edge."""
    return cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)


# ---------------------------------------------------------------------------------------- the shot
class Shot:
    """Everything the checks share: the check file, the measured facts, the masks and the camera."""

    def __init__(self, args):
        self.check = json.load(open(args.check))
        self.facts = json.load(open(os.path.join(args.facts, 'facts.json')))
        self.width, self.height = self.facts['size']
        ids = cv2.cvtColor(cv2.imread(os.path.join(args.facts, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
        self.ids_picture = cv2.imread(os.path.join(args.facts, 'ids.png'))
        self.sky = ids.sum(axis=2) < 24   # nothing drawn there: the sky
        self.visible, self.alone = {}, {}   # the parts that show; the whole prop as if nothing hid it
        for g, info in self.facts['groups'].items():
            self.visible[g] = without_specks(np.abs(ids - np.array(info['colour'])).sum(axis=2) < 24)
            solo = cv2.imread(os.path.join(args.facts, 'solo', f'{g}.png'))
            self.alone[g] = solo.max(axis=2) > 8
        self.picture = None
        if args.picture:
            self.picture = cv2.imread(args.picture)
            if self.picture.shape[:2] != (self.height, self.width):
                self.picture = cv2.resize(self.picture, (self.width, self.height), interpolation=cv2.INTER_AREA)
        self.grey = cv2.cvtColor(self.picture, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255 if self.picture is not None else None
        self.camera = self.facts['camera']
        # the camera's focal length in pixels: how far a 1-in-1 slope reaches across the screen
        self.focal = (self.height / 2) / math.tan(math.radians(self.camera['vertical_fov_degrees']) / 2)
        yaw = math.radians(self.camera['turn_degrees'])
        self.ahead = np.array([-math.sin(yaw), math.cos(yaw)])   # straight ahead along the ground, Blender x and y
        key = self.check.get('lines_key', 'street')
        self.meet = self.facts['lines_meet'].get(key)
        street = self.check.get('lines', {}).get(key, [0, 1, 0])
        self.street_slope = street[2] / max(1e-6, math.hypot(street[0], street[1]))
        # things moving along the street run toward where its lines meet: that height on screen is where a
        # prop on the ground ends up as it goes further away
        self.ground_horizon = (self.meet or self.facts['lines_meet'].get('level') or [0.5, 0.5])[1] * self.height
        self.subject = self.check.get('subject')
        self.support = self.check.get('support')
        self.story = [g for g in self.check.get('story', []) if g in self.facts['groups']]
        self.core = [g for g in dict.fromkeys([self.subject] + self.story) if g in self.facts['groups']]
        self.on_ground = set(self.check.get('on_ground', []))
        self.rests_on = self.check.get('stands_on', {})
        self.reference = self.check.get('reference') or {}
        self.camera_fault = False

    def info(self, g):
        return self.facts['groups'].get(g)

    def shows(self, g):
        return g in self.visible and bool(self.visible[g].any())

    def tilted(self):
        return abs(self.camera['tilt_degrees']) > 0.5 or abs(self.camera['roll_degrees']) > 0.5

    def carrier(self, g):
        """The prop that g rests or hangs on and moves with (the lantern's chair, the notice's board), or None."""
        held_by = self.rests_on.get(g) or (self.support if g == self.subject else None)
        return held_by if held_by and held_by != g and self.info(held_by) else None

    def grounded(self, g):
        return g in self.on_ground or self.carrier(g) in self.on_ground or g in self.rests_on


# ---------------------------------------------------------------------------------------- the report
class Report:
    def __init__(self):
        self.items = []

    def add(self, rule, passed, what, numbers='', fix='', mark=None, area=False, kind='story', how_bad=1.0, arrow=None, name=None):
        """One check. `kind` (see KINDS) and `how_bad` (how far past its limit) set the order of the problems;
        `name` lets other problems point at this one ("<<name>>" in their text becomes "problem N")."""
        passed = bool(passed)   # numpy's yes/no would slip past the report's checks
        item = dict(rule=rule, passed=passed, what=what, numbers=numbers, fix='' if passed else fix,
                    mark=None if passed else mark, area=area, kind=kind, how_bad=float(how_bad),
                    arrow=None if passed else arrow, name=name, number=None)
        self.items.append(item)
        return item

    def note(self, rule, what, numbers=''):
        self.items.append(dict(rule=rule, passed=None, what=what, numbers=numbers, fix='', mark=None, kind='note', arrow=None, name=None))

    def problems(self):
        return [i for i in self.items if i['passed'] is False]

    def camera_first(self):
        """When the camera is wrong, the composing faults were measured with the wrong camera: say so in their fixes."""
        for i in self.problems():
            if i['kind'] in COMPOSING and i['fix']:
                i['fix'] = 'Fix the camera first (<<camera>>) and check again: this may change. If it stays: ' + i['fix']

    def rank(self):
        """Numbers the problems 1 to N, worst first: by kind (the camera first), then by how far past the limit."""
        ranked = sorted(self.problems(), key=lambda i: (TIER[i['kind']], -i['how_bad']))
        for number, item in enumerate(ranked, 1):
            item['number'] = number
        names = {i['name']: i['number'] for i in ranked if i['name']}
        firsts = {}
        for i in ranked:
            firsts.setdefault(i['kind'], i['number'])

        def refer(match):
            key = match.group(1)
            number = names.get(key) or firsts.get(key)
            return f'problem {number}' if number else 'its own problem'
        for i in self.items:
            for field in ('what', 'fix', 'numbers'):
                i[field] = re.sub(r'<<([^>]+)>>', refer, i[field])
        return ranked


# ---------------------------------------------------------------------------------------- turning screen moves into metres
def spot_taken(shot, g, change):
    """If group g moved `change` metres further from the camera (negative: nearer), would it stand where
    another prop already stands? Returns that prop's name, or None."""
    info = shot.info(g)
    x, y = np.array(info['centre'][:2]) + shot.ahead * change
    half_w, half_d = info['width'] / 2 - 0.03, info['depth'] / 2 - 0.03
    riding = {h for h, on in shot.rests_on.items() if on == g} | {shot.rests_on.get(g)} | {g, shot.subject}
    clash = lambda px, py, o: abs(px - o['centre'][0]) < half_w + o['width'] / 2 - 0.03 and abs(py - o['centre'][1]) < half_d + o['depth'] / 2 - 0.03
    for other in sorted(shot.on_ground | set(shot.story)):
        if other in riding or not shot.info(other):
            continue
        o = shot.info(other)
        if clash(x, y, o) and not clash(info['centre'][0], info['centre'][1], o):   # their boxes may already overlap (a turned chair)
            return other
    return None


def move_words(shot, g, dx, dy, anchor_y=None):
    """Plain words for moving group g so it slides dx pixels right and dy pixels down the screen, or None if
    moving the prop can't do it. A prop on the ground can't be lifted: it slides down the screen as it comes
    nearer, so an up or down slide becomes a move nearer to or further from the camera. A prop resting on
    another moves with it."""
    carrier = shot.carrier(g)
    mover = carrier or g
    name = f'{carrier} (with {g} on it)' if carrier else g
    info = shot.info(g)
    metres = info['metres_per_pixel']
    parts = []
    if abs(dx) >= 1 and abs(dx) >= 0.3 * abs(dy):
        parts.append(f'about {abs(dx) * metres:.2f} m to the {"right" if dx > 0 else "left"}')
    if abs(dy) >= 1 and abs(dy) >= 0.3 * abs(dx):
        if shot.grounded(g):
            if anchor_y is None:
                anchor_y = centre_of(shot.alone[g])[1] if shot.alone[g].any() else shot.height / 2
            now, wanted = anchor_y - shot.ground_horizon, anchor_y + dy - shot.ground_horizon
            if now * wanted > 0 and min(abs(now), abs(wanted)) > 0.02 * shot.height:
                distance = info['distance']
                change = distance * now / wanted - distance
                words = f'about {abs(change):.2f} m {"further from" if change > 0 else "nearer to"} the camera'
                taken = spot_taken(shot, mover, change)
                if taken:
                    words += f' (but {taken} stands there)'
                parts.append(words)
            else:
                return None   # moving it along the ground can't slide it that far up or down the screen
        else:
            parts.append(f'about {abs(dy) * metres:.2f} m {"lower" if dy > 0 else "higher"}')
    if not parts:
        return f'leave {name} where it is'
    return f'move {name} ' + ' and '.join(parts)


def two_ways(shot, front, back, into, away, anchor_y):
    """The fix for edges that just touch: slide the nearer prop into a clear overlap, or away to a clear gap."""
    overlap, gap = move_words(shot, front, *into, anchor_y), move_words(shot, front, *away, anchor_y)
    ways = ([f'{overlap} so it clearly overlaps {back}'] if overlap else []) + ([f'{gap} to leave a clear gap'] if gap else [])
    return capital(', or '.join(ways)) + '.' if ways else f'Moving {front} along the ground can\'t fix this: move the camera, or move {back}.'


def pixels(value):
    return f'{value:.0f} pixel' + ('' if round(value) == 1 else 's')


def side_words(box):
    """Where an unclipped screen box lies when it is wholly outside the frame."""
    l, t, r, b = box
    sides = []
    if l > 0.99:
        sides.append('past the right edge')
    if r < 0.01:
        sides.append('past the left edge')
    if t > 0.99:
        sides.append('below the bottom')
    if b < 0.01:
        sides.append('above the top')
    return ' and '.join(sides)


# ---------------------------------------------------------------------------------------- the camera (rule 2 and the reference)
def our_projection(shot, point):
    """Where a Blender point lands in our frame (pixels across and down), and whether it is in front of the camera."""
    cam = shot.camera
    where, depth = project((*cam['at'], cam['turn_degrees'], cam['vertical_fov_degrees']), point, (shot.width, shot.height),
                           cam['tilt_degrees'], cam['roll_degrees'])
    return where, depth > 0


def ground_point(shot, px, py):
    """The spot on the street seen at pixel (px, py): where the line of sight through it meets the ground, which
    rises with the street from the pavement under the camera. None if that pixel looks above the ground."""
    cam = shot.camera
    ahead, right, up = camera_axes(cam['turn_degrees'], cam['tilt_degrees'], cam['roll_degrees'])
    direction = ahead + right * (px - shot.width / 2) / shot.focal - up * (py - shot.height / 2) / shot.focal
    eye = np.array(cam['at'], float)
    base = eye[2] - (cam.get('eye_height') or 1.7)
    falling = direction[2] - shot.street_slope * direction[1]
    if falling >= -1e-6:
        return None
    return eye + direction * (base - eye[2]) / falling


def check_set_up(report, shot):
    for g in shot.facts.get('missing_groups', []):
        report.add('set-up', False, f'No object in the scene matches the group "{g}", so it was not measured.',
                   fix='Check its name patterns in the check file against the objects\' names in Blender.', kind='set-up', how_bad=10)


def check_camera(report, shot):
    cam = shot.camera
    tilt, roll = cam['tilt_degrees'], cam['roll_degrees']
    level = not shot.tilted()
    fixes = []
    if abs(tilt) > 0.5:
        fixes.append(f'tilt it {plain(abs(tilt), 1)} degrees {"down" if tilt > 0 else "up"}')
    if abs(roll) > 0.5:
        fixes.append(f'take out its {plain(abs(roll), 1)}-degree lean')
    report.add('rule 2: keep the camera level', level,
               f'The camera is not level: tilted {plain(abs(tilt), 1)} degrees {"up" if tilt > 0 else "down"} and leaning {plain(abs(roll), 1)} degrees to one side.'
               if not level else f'The camera is level (tilt {plain(tilt, 1)}, lean {plain(roll, 1)} degrees).',
               fix=capital(' and '.join(fixes)) + ', so posts, drainpipes and chimneys stay upright.' if fixes else '',
               kind='camera', how_bad=max(abs(tilt), abs(roll)) / 0.5, name='camera-level')
    low, high = shot.check.get('eye_height', [1.5, 1.9])
    eye = cam.get('eye_height')
    if eye is None:
        report.note('rule 2: stand at eye height', 'Nothing was found under the camera, so its height above the pavement is unknown.')
        return
    ok = low <= eye <= high
    target = min(max(eye, low + 0.05), high - 0.05)
    report.add('rule 2: stand at eye height', ok,
               f'The camera\'s eye is {eye:.2f} m above the pavement under it (a standing person: {low:.2f} to {high:.2f} m).',
               fix=f'{"Lower" if eye > target else "Raise"} the camera about {abs(eye - target):.2f} m.',
               kind='camera', how_bad=abs(eye - target) / 0.1 + 1, name='camera-height')


def camera_axes(turn, tilt=0.0, roll=0.0):
    """The camera's ahead, right and up directions in Blender space (turn + is left, tilt + is up)."""
    yaw, pitch, lean = (math.radians(v) for v in (turn, tilt, roll))
    ahead = np.array([-math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    right = np.array([math.cos(yaw), math.sin(yaw), 0.0])
    up = np.cross(right, ahead)
    return ahead, right * math.cos(lean) + up * math.sin(lean), up * math.cos(lean) - right * math.sin(lean)


def project(camera, point, size, tilt=0.0, roll=0.0):
    """Where a Blender point lands in a picture of `size` pixels, seen by camera (x, y, z, turn, view angle)."""
    x, y, z, turn, fov = camera
    width, height = size
    ahead, right, up = camera_axes(turn, tilt, roll)
    v = np.array(point) - np.array([x, y, z])
    depth = v @ ahead
    focal = (height / 2) / math.tan(math.radians(fov) / 2)
    return np.array([width / 2 + focal * (v @ right) / depth, height / 2 - focal * (v @ up) / depth]), depth


def camera_errors(camera, match, size, tilt=0.0, roll=0.0):
    """How many pixels each landmark of the reference picture is from where this camera draws it."""
    errors = {}
    for name, item in match.get('points', {}).items():
        drawn, depth = project(camera, item['at'], size, tilt, roll)
        errors[name] = float(np.hypot(*(drawn - np.array(item['seen'])))) if depth > 0 else 1e5
    for name, item in match.get('lines', {}).items():
        p0, direction = np.array(item['through']), np.array(item['along'], float)
        start = p0 + direction * max(0.0, (camera[1] + 4 - p0[1]) / max(1e-6, direction[1]))
        a, da = project(camera, start, size, tilt, roll)
        b, db = project(camera, start + direction * 56, size, tilt, roll)
        along = (b - a) / np.linalg.norm(b - a)
        across = np.array([-along[1], along[0]])
        errors[name] = math.sqrt(sum(((np.array(p) - a) @ across) ** 2 for p in item['seen']) / len(item['seen'])) if min(da, db) > 0 else 1e5
    return errors


def nelder_mead(f, start, steps, rounds=3000):
    """Finds the numbers that make f smallest, by rolling a small shape of guesses downhill."""
    points = [np.array(start, float)] + [np.array(start, float) + np.eye(len(start))[i] * steps[i] for i in range(len(start))]
    values = [f(p) for p in points]
    for _ in range(rounds):
        order = np.argsort(values)
        points, values = [points[i] for i in order], [values[i] for i in order]
        centre = np.mean(points[:-1], axis=0)
        reflected = centre + (centre - points[-1])
        fr = f(reflected)
        if fr < values[0]:
            expanded = centre + 2 * (centre - points[-1])
            fe = f(expanded)
            points[-1], values[-1] = (expanded, fe) if fe < fr else (reflected, fr)
        elif fr < values[-2]:
            points[-1], values[-1] = reflected, fr
        else:
            contracted = centre + 0.5 * (points[-1] - centre)
            fc = f(contracted)
            if fc < values[-1]:
                points[-1], values[-1] = contracted, fc
            else:
                points = [points[0] + 0.5 * (p - points[0]) for p in points]
                values = [f(p) for p in points]
    best = int(np.argmin(values))
    return points[best], values[best]


def check_camera_match(report, shot):
    """Finds the level camera that best lines up the reference picture's landmarks with our street (at our
    camera's distance up the street), and says how far ours is from it."""
    match = shot.reference.get('camera_match')
    if not match:
        return
    cam = shot.camera
    if shot.tilted():
        report.note('reference: the camera', f'Not compared: our camera is not level (tilt {plain(cam["tilt_degrees"], 1)}, '
                    f'lean {plain(cam["roll_degrees"], 1)} degrees; <<camera-level>>). Level it, then check again.')
        return
    size = match['picture_size']
    ours = (cam['at'][0], cam['at'][1], cam['at'][2], cam['turn_degrees'], cam['vertical_fov_degrees'])
    cost = lambda p: sum(e * e for e in camera_errors((p[0], ours[1], p[1], p[2], p[3]), match, size).values())
    best, _ = nelder_mead(cost, (ours[0], ours[2], ours[3], ours[4]), (0.3, 0.3, 1.5, 4.0))
    fitted = (best[0], ours[1], best[1], best[2], best[3])
    scale = shot.width / size[0]
    ours_errors = {k: v * scale for k, v in camera_errors(ours, match, size).items()}
    fit_errors = {k: v * scale for k, v in camera_errors(fitted, match, size).items()}
    pavement = cam['at'][2] - (cam.get('eye_height') or 0)
    height, side, turn, view = ours[2] - fitted[2], ours[0] - fitted[0], ours[3] - fitted[3], ours[4] - fitted[4]
    ok = abs(height) <= 0.1 and abs(side) <= 0.15 and abs(turn) <= 0.75 and abs(view) <= 2
    fixes = []
    if abs(height) > 0.1:
        fixes.append(f'{"lower" if height > 0 else "raise"} the camera about {abs(height):.2f} m')
    if abs(side) > 0.15:
        fixes.append(f'move it about {abs(side):.2f} m to the {"left" if side > 0 else "right"} (across the street)')
    if abs(turn) > 0.75:
        fixes.append(f'turn it about {abs(turn):.1f} degrees {"right" if turn > 0 else "left"}')
    if abs(view) > 2:
        fixes.append(f'{"narrow" if view > 0 else "widen"} its view by about {abs(view):.1f} degrees (top to bottom)')

    def describe(c):
        across = f'{abs(c[0]):.2f} m {"right" if c[0] > 0 else "left"} of the street\'s middle line'
        facing = f'turned {abs(c[3]):.1f} degrees {"left" if c[3] > 0 else "right"} of straight up the street'
        return f'{c[2] - pavement:.2f} m above the pavement, {across}, {facing}, seeing {c[4]:.1f} degrees top to bottom'
    worst_best = max(fit_errors.values())
    if ok:
        what = (f'Our camera is within {abs(height):.2f} m in height, {abs(side):.2f} m sideways, {abs(turn):.1f} degrees of turn '
                f'and {abs(view):.1f} degrees of view of the camera that best matches the reference. Even that best camera misses '
                f'the reference\'s landmarks by up to {worst_best:.0f} pixels (the reference is a painting, not an exact photo), '
                f'so differences this small mean nothing.')
    else:
        worst = max(ours_errors, key=ours_errors.get)
        what = (f'The camera that best matches the reference (at our distance up the street) is {describe(fitted)}; ours is '
                f'{describe(ours)}. Ours misses the reference\'s landmarks by up to {ours_errors[worst]:.0f} pixels ({worst}); '
                f'the best camera by up to {worst_best:.0f}.')
    report.add('reference: the camera', ok, what,
               'landmarks missed by ours, in pixels: ' + ', '.join(f'{k} {v:.0f}' for k, v in ours_errors.items()),
               fix=capital('; '.join(fixes)) + '.' if fixes else '', kind='camera',
               how_bad=10 + max(abs(height) / 0.1, abs(side) / 0.15, abs(turn) / 0.75, abs(view) / 2), name='camera-match')   # the fullest camera fix


def check_reference_lines(report, shot):
    wanted = shot.reference.get('lines_meet')
    if not wanted or not shot.meet:
        return
    meet = shot.meet
    dx, dy = meet[0] - wanted[0], meet[1] - wanted[1]
    fixes = []
    if abs(dx) > 0.03:
        ours_angle = math.atan((meet[0] - 0.5) * shot.width / shot.focal)
        wanted_angle = math.atan((wanted[0] - 0.5) * shot.width / shot.focal)
        turn = math.degrees(wanted_angle - ours_angle)   # + means the meeting point must slide right: turn left
        fixes.append(f'Ours meet {abs(dx):.2f} of the frame width {"left" if dx < 0 else "right"} of the reference\'s: turn the camera '
                     f'about {abs(turn):.1f} degrees {"left" if turn > 0 else "right"} (turning left slides everything on screen to the right).')
    if abs(dy) > 0.03:
        where = 'lower' if dy > 0 else 'higher'
        if shot.tilted():
            fixes.append(f'Ours meet {abs(dy):.2f} of the frame height {where} than the reference\'s because our camera is not level '
                         f'(<<camera-level>>): level it and check again.')
        else:
            above = 0.5 - wanted[1]   # how far above the middle the reference's lines meet
            if above > 0.005 and shot.street_slope > 0:
                view = 2 * math.degrees(math.atan(shot.street_slope / (2 * above)))
                fixes.append(f'Ours meet {abs(dy):.2f} of the frame height {where} than the reference\'s. Our camera is level, so that '
                             f'height is set by the view angle: about {view:.0f} degrees top to bottom would match (ours is '
                             f'{shot.camera["vertical_fov_degrees"]:.1f}). Compare with the camera item first: the reference is a painting, '
                             f'and its street may simply be drawn steeper.')
            else:
                fixes.append(f'Ours meet {abs(dy):.2f} of the frame height {where} than the reference\'s; with a level camera this is the view angle.')
    ok = not fixes
    report.add('reference: where the lines meet', ok,
               f'Ours meet at {meet[0]:.3f} across, {meet[1]:.3f} down; the reference\'s at {wanted[0]:.3f}, {wanted[1]:.3f} '
               f'(a drawn picture\'s lines rarely meet at one exact point, so 0.03 either way is allowed).',
               fix=' '.join(fixes), kind='camera', how_bad=max(abs(dx), abs(dy)) / 0.03, name='camera-lines',
               mark=(meet[0] * shot.width - 22, meet[1] * shot.height - 22, meet[0] * shot.width + 22, meet[1] * shot.height + 22))


# ---------------------------------------------------------------------------------------- props resting where they should
def check_resting(report, shot):
    good = []
    for g in shot.check.get('on_ground', []):
        info = shot.info(g)
        if not info:
            continue
        air, on, high = info['stands_above_surface_below'], info.get('stands_on'), info['stands_above_ground']
        x, y = info['centre'][:2]
        spot = f'at Blender x {x:.2f}, y {y:.2f}'
        if air is None:
            report.add('props rest where they should', False, f'{g} has nothing under it at all ({spot}): it is off the edge of the set.',
                       fix=f'Move {g} back over the street.', kind='resting', how_bad=10, name=f'resting:{g}')
        elif air > 0.03:
            under = f'the top of {on}' if on and on != 'the set' else 'the surface'
            fix = f'Lower {g} by {air:.2f} m so it stands on what is under it.'
            if high is not None and high - air > 0.5:
                fix = (f'Put {g} back on the pavement: lowering it {air:.2f} m would land it on something {high - air:.2f} m above the street '
                       f'(a roof edge, a wall top or a sill). Place it again from just above the pavement.')
            report.add('props rest where they should', False,
                       f'{g} is floating: there is {air:.2f} m of air between its bottom and {under} under it ({spot}).',
                       f'its bottom is at Blender height {info["bottom"]:.2f} m', fix, kind='resting', how_bad=air / 0.03, name=f'resting:{g}')
        elif on and on not in ('the set', g):
            report.add('props rest where they should', False, f'{g} rests on {on}, not on the ground ({spot}).',
                       fix=f'Move {g} off {on} and place it again from just above the pavement.', kind='resting', how_bad=5, name=f'resting:{g}')
        elif high is not None and high > 0.5:
            report.add('props rest where they should', False,
                       f'{g} has landed on something high: its bottom is {high:.2f} m above the street under it ({spot}): a roof edge, a wall top or a sill.',
                       fix=f'Place {g} again from just above the pavement.', kind='resting', how_bad=high / 0.3, name=f'resting:{g}')
        else:
            good.append(g)
    if good:
        report.add('props rest where they should', True, f'{", ".join(good)} stand on the ground (within 3 cm).', kind='resting')
    for g, support in shot.rests_on.items():
        info, under = shot.info(g), shot.info(support)
        if not info or not under:
            continue
        if 'stands_on' not in info:
            report.note('props rest where they should', f'Not judged whether {g} rests on {support}: these measurements are older than '
                        'shot_facts.py\'s "stands_on"; measure again.')
            continue
        air, on = info['stands_above_surface_below'] or 0, info.get('stands_on')
        if on == support and air <= 0.03:
            report.add('props rest where they should', True, f'{g} rests on {support}.', kind='resting')
            continue
        apart = math.hypot(under['centre'][0] - info['centre'][0], under['centre'][1] - info['centre'][1])
        moved = (f' {support}\'s middle is {apart:.2f} m from {g}\'s ({support} at Blender x {under["centre"][0]:.2f}, y {under["centre"][1]:.2f}; '
                 f'{g} at x {info["centre"][0]:.2f}, y {info["centre"][1]:.2f}), so one of them has moved.') if apart > 0.1 else ''
        if air > 0.03:
            report.add('props rest where they should', False, f'{g} should rest on {support}, but there is {air:.2f} m of air under it.{moved}',
                       fix=f'Either move {support} back under {g}, or move {g} over {support} and lower it {air:.2f} m onto it.',
                       kind='resting', how_bad=air / 0.03, name=f'resting:{g}')
        else:
            report.add('props rest where they should', False,
                       f'{g} should rest on {support}, but it stands on {"the ground" if on in (None, "the set") else on} instead.{moved}',
                       fix=f'Put {g} back on {support}: move it over {support}, then lower it onto the top.', kind='resting', how_bad=8, name=f'resting:{g}')


# ---------------------------------------------------------------------------------------- story props missing or cut by the frame
def check_missing(report, shot):
    """Story props that don't show at all: out of the frame (which side, how far) or hidden behind something."""
    for g in dict.fromkeys(shot.core + shot.check.get('must_read', [])):
        info = shot.info(g)
        if not info or shot.shows(g):
            continue
        box = info.get('screen_box_unclipped')
        if box is None:
            report.add('rule 3: story props in the frame', False, f'{g} is behind the camera.', fix=f'Move {g} in front of the camera.',
                       kind='missing', how_bad=10, name=f'missing:{g}')
            continue
        l, t, r, b = box
        outside = side_words(box)
        resting = f' (it is also not resting where it should: <<resting:{g}>>)' if any(i.get('name') == f'resting:{g}' and i['passed'] is False for i in report.items) else ''
        if outside:
            wanted = shot.reference.get('boxes', {}).get(g, {}).get('box')
            cx, cy = (l + r) / 2, (t + b) / 2
            air = info['stands_above_surface_below'] or 0
            if resting and air > 0.03:
                # where it lands on screen once lowered (a level camera sees it the same size)
                where, ahead = our_projection(shot, [info['centre'][0], info['centre'][1], info['centre'][2] - air])
                if ahead:
                    lx, ly = where[0] / shot.width, where[1] / shot.height
                    landed = (lx - (r - l) / 2, ly - (b - t) / 2, lx + (r - l) / 2, ly + (b - t) / 2)
                    still = side_words(landed)
                    if not still and landed[0] >= 0 and landed[2] <= 1:
                        report.add('rule 3: story props in the frame', False, f'{g} is outside the frame, {outside}, because it is floating{resting}.',
                                   fix=f'Lowering it brings it back into the frame, at about {lx:.2f} across, {ly:.2f} down.',
                                   kind='missing', how_bad=10, name=f'missing:{g}')
                        continue
                    l, t, r, b = landed
                    cx, cy = lx, ly
                    outside = (still or 'cut by the frame edge') + ', even once lowered'
            if wanted:
                tx, ty = (wanted[0] + wanted[2]) / 2, (wanted[1] + wanted[3]) / 2
                aim = f'the reference has it at {wanted[0]:.2f} to {wanted[2]:.2f} across'
            else:
                tx = min(max(cx, 0.05 + (r - l) / 2), 0.95 - (r - l) / 2)
                ty = min(max(cy, 0.03 + (b - t) / 2), 0.97 - (b - t) / 2)
                aim = 'bring it just inside the frame'
            words = move_words(shot, g, (tx - cx) * shot.width, (ty - cy) * shot.height, cy * shot.height) \
                or move_words(shot, g, (tx - cx) * shot.width, 0, cy * shot.height)
            fix = (capital(words) + f' ({aim}).') if words else f'Moving {g} along the ground can\'t bring it into the frame: move the camera.'
            report.add('rule 3: story props in the frame', False,
                       f'{g} is outside the frame, {outside}: it would sit {l:.2f} to {r:.2f} across, {t:.2f} to {b:.2f} down.{resting}',
                       fix=fix, kind='missing', how_bad=10, name=f'missing:{g}')
        else:
            under = shot.alone[g]
            covered = {o: int((shot.visible[o] & under).sum()) for o in shot.visible if o != g}
            hider = max(covered, key=covered.get) if covered and max(covered.values()) > 0 else 'the set (a wall or a house)'
            report.add('rule 3: story props in the frame', False, f'{g} is in the frame but hidden behind {hider}.{resting}',
                       fix=f'Move {g} out from behind {hider}, or in front of it.', kind='missing', how_bad=9, name=f'missing:{g}')


def check_cut_by_edge(report, shot):
    for g in shot.core:
        info = shot.info(g)
        if not shot.shows(g) or not info.get('screen_box_unclipped'):
            continue
        l, t, r, b = info['screen_box_unclipped']
        inside = max(0, min(r, 1) - max(l, 0)) * max(0, min(b, 1) - max(t, 0))
        share = inside / max(1e-6, (r - l) * (b - t))
        if 0.02 < share < 0.6:
            dx = -(r - 0.95) * shot.width if r > 1 else (0.05 - l) * shot.width if l < 0 else 0
            dy = -(b - 0.97) * shot.height if b > 1 else (0.03 - t) * shot.height if t < 0 else 0
            report.add('rule 12: nothing important cut by the frame edge', False,
                       f'{g} is cut by the frame edge: only {share:.0%} of it is inside.', f'it would sit {l:.2f} to {r:.2f} across, {t:.2f} to {b:.2f} down',
                       capital(move_words(shot, g, dx, dy, (t + b) / 2 * shot.height) or 'turn or move the camera') + ' to bring it all in.',
                       mark=box_of(shot.visible[g]), kind='edges', how_bad=1 / share)


# ---------------------------------------------------------------------------------------- rule 1: where the lines meet
def check_lines(report, shot):
    if shot.meet is None:
        report.add('rule 1: aim the street at the story', False, 'The street\'s lines meet behind the camera: it faces down the street.',
                   fix='Turn the camera to face up the street.', kind='lines', how_bad=10)
        return
    target = shot.support or shot.subject
    mx, my = shot.meet[0] * shot.width, shot.meet[1] * shot.height
    if not shot.shows(target):
        report.note('rule 1: aim the street at the story', f'The lines meet at {shot.meet[0]:.3f} across, {shot.meet[1]:.3f} down; {target} does not show.')
        return
    mask = shot.visible[target]
    outline = mask & ~cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    ex, ey = nearest_point(outline, mx, my)
    dx, dy = ex - mx, ey - my   # from where the lines meet to the edge: + is right of it, below it
    gap = math.hypot(dx, dy) / shot.width
    ok = gap <= 0.03
    l, t, r, b = box_of(mask)
    metres = shot.info(target)['metres_per_pixel']
    fixes = []
    if abs(dy) > 4:
        other = move_words(shot, target, 0, -dy, ey)
        fixes.append(f'{"lower" if dy > 0 else "raise"} the camera about {abs(dy) * metres:.2f} m ({target} then {"rises" if dy > 0 else "drops"} '
                     f'on screen while where the lines meet stays put)' + (f', or {other}' if other else ''))
    if abs(dx) > 4:
        other = move_words(shot, target, -dx, 0, ey)
        fixes.append(f'move the camera about {abs(dx) * metres:.2f} m to the {"right" if dx > 0 else "left"}' + (f', or {other}' if other else ''))
    report.add('rule 1: aim the street at the story', ok,
               f'The street\'s lines meet at {shot.meet[0]:.3f} across, {shot.meet[1]:.3f} down; the nearest edge of {target} is {gap:.3f} of the frame '
               f'width away (limit 0.03)' + (f': {abs(dx):.0f} pixels to the {"right" if dx > 0 else "left"} and {abs(dy):.0f} pixels '
                                              f'{"below" if dy > 0 else "above"}.' if not ok else '.'),
               f'{target} spans {l / shot.width:.2f} to {r / shot.width:.2f} across, {t / shot.height:.2f} to {b / shot.height:.2f} down',
               'Turning the camera won\'t help: it moves where the lines meet and the props together. ' + capital('; and '.join(fixes)) + '.',
               mark=(mx - 22, my - 22, mx + 22, my + 22), kind='lines', how_bad=gap / 0.03)


# ---------------------------------------------------------------------------------------- rules 3 and 4: the story props as one group
def check_pairs(report, shot):
    """Every pair of the listed groups: a clear overlap or a clear gap, never two edges just touching (rule 4).
    Returns which pairs touch or overlap at all (for rule 3)."""
    scale = shot.width / 1536
    need_overlap, need_gap, margin = 20 * scale, 25 * scale, 4 * scale
    names = [g for g in dict.fromkeys(shot.core + shot.check.get('pairs_also', [])) if g in shot.alone and shot.alone[g].any()]
    solid = {g: without_wires(shot.alone[g], shot.width) for g in names}
    touching = {}
    found = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} <= {shot.subject, shot.support}:
                continue   # the subject hangs on its support: they always share an edge
            whole_overlap = shot.alone[a] & shot.alone[b]
            touching[(a, b)] = bool(whole_overlap.any()) or float(np.where(shot.alone[b], distance_outside(shot.alone[a]), np.inf).min()) <= 3 * scale
            front, back = sorted((a, b), key=lambda g: shot.info(g)['distance'])
            kind = 'story' if a in shot.core and b in shot.core else 'background'
            both = solid[a] & solid[b]
            if both.any():
                showing = both & (shot.visible[a] | shot.visible[b])
                if showing.sum() < 0.3 * both.sum():
                    continue   # a third thing in front hides the overlap
                depth = float(max(distance_inside(solid[a])[showing].max(), distance_inside(solid[b])[showing].max()))
                if depth >= need_overlap:
                    continue
                cx, cy = centre_of(showing)
                fx, fy = centre_of(solid[front])
                ux, uy = unit(cx - fx, cy - fy)   # from the front one's middle toward the overlap
                more, less = need_overlap + margin - depth, depth + need_gap + margin
                found += 1
                report.add('rule 4: overlap clearly or leave a clear gap', False,
                           f'{front} only just overlaps {back}: it reaches {pixels(depth)} into it. Edges that just meet make near and far '
                           f'things look stuck together (a clear overlap is at least {need_overlap:.0f} pixels deep; a clear gap at least {need_gap:.0f}).',
                           f'at {cx / shot.width:.2f} across, {cy / shot.height:.2f} down; {front} is nearer the camera',
                           two_ways(shot, front, back, (ux * more, uy * more), (-ux * less, -uy * less), cy),
                           mark=box_of(showing), kind=kind, how_bad=need_overlap / max(depth, 1))
                continue
            # no clear overlap: how far apart are the parts that show? Where only thin parts (a wire) overlap,
            # leave the thin parts out
            va, vb = shot.visible[a], shot.visible[b]
            if whole_overlap.any():
                va, vb = without_wires(va, shot.width), without_wires(vb, shot.width)
            if not (va.any() and vb.any()):
                continue
            gaps = np.where(vb, distance_outside(va), np.inf)
            gap = float(gaps.min())
            if gap >= need_gap:
                continue
            y, x = np.unravel_index(np.argmin(gaps), gaps.shape)
            ax, ay = nearest_point(va, x, y)
            front_point, back_point = ((ax, ay), (x, y)) if front == a else ((x, y), (ax, ay))
            if gap >= 1:
                ux, uy = unit(back_point[0] - front_point[0], back_point[1] - front_point[1])
            else:
                fx, fy = centre_of(shot.alone[front])
                ux, uy = unit(front_point[0] - fx, front_point[1] - fy)
            more, less = gap + need_overlap + margin, need_gap + margin - gap
            found += 1
            report.add('rule 4: overlap clearly or leave a clear gap', False,
                       f'{a} and {b} almost touch: {pixels(gap)} apart. Edges that just meet make near and far things look stuck together '
                       f'(a clear overlap is at least {need_overlap:.0f} pixels deep; a clear gap at least {need_gap:.0f}).',
                       f'at {x / shot.width:.2f} across, {y / shot.height:.2f} down; {front} is nearer the camera',
                       two_ways(shot, front, back, (ux * more, uy * more), (-ux * less, -uy * less), front_point[1]),
                       mark=(min(x, ax) - 14, min(y, ay) - 14, max(x, ax) + 14, max(y, ay) + 14), kind=kind, how_bad=need_gap / max(gap, 1))
    if not found:
        report.add('rule 4: overlap clearly or leave a clear gap', True,
                   f'No two of {", ".join(names)} just touch (overlaps at least {need_overlap:.0f} pixels deep, gaps at least {need_gap:.0f}).')
    return touching


def check_story_props(report, shot, touching):
    shown = [g for g in shot.story if shot.shows(g)]
    if not shown:
        return None
    hidden = [g for g in shot.story if not shot.shows(g)]
    linked = {g: {g} for g in shown}
    for (a, b), touches in touching.items():
        if touches and a in linked and b in linked:
            joined = linked[a] | linked[b]
            for g in joined:
                linked[g] = joined
    apart = [g for g in shown if len(linked[g]) == 1]
    what = 'Every story prop that shows touches or overlaps another.' if not apart else f'Standing apart from the others: {", ".join(apart)}.'
    if hidden:
        what += ' Not showing at all: ' + ', '.join(f'{g} (<<missing:{g}>>)' for g in hidden) + '.'
    fixes = []
    for g in apart:
        others = [o for o in shown if o != g]
        if not others:
            continue
        outside = distance_outside(shot.alone[g])
        nearest = min(others, key=lambda o: float(np.where(shot.alone[o], outside, np.inf).min()))
        gx, gy = centre_of(shot.alone[g])
        ox, oy = nearest_point(shot.alone[nearest], gx, gy)
        px, py = nearest_point(shot.alone[g], ox, oy)
        ux, uy = unit(ox - px, oy - py)
        reach = math.hypot(ox - px, oy - py) + 20 * shot.width / 1536 + 6
        words = move_words(shot, g, ux * reach, uy * reach, py)
        fixes.append(f'{words} so it overlaps {nearest}' if words else f'move {nearest} toward {g} until they overlap')
    report.add('rule 3: one touching group', not apart, what, fix=capital('; '.join(fixes)) + '.' if fixes else '', kind='story', how_bad=3 * len(apart))
    # how big a box the group fills (a tall board on its own would set the top, so the check file can leave it out)
    excluded = set(shot.check.get('box_excludes', []))
    in_box = [g for g in dict.fromkeys([shot.subject] + shown) if g not in excluded and shot.shows(g)]
    boxes = {g: box_of(shot.visible[g]) for g in in_box}
    l, t = min(v[0] for v in boxes.values()), min(v[1] for v in boxes.values())
    r, b = max(v[2] for v in boxes.values()), max(v[3] for v in boxes.values())
    edge = {'left': min(boxes, key=lambda g: boxes[g][0]), 'right': max(boxes, key=lambda g: boxes[g][2]),
            'top': min(boxes, key=lambda g: boxes[g][1]), 'bottom': max(boxes, key=lambda g: boxes[g][3])}
    w, h = (r - l) / shot.width, (b - t) / shot.height
    limit_w, limit_h = 0.40, 0.50
    reference_words = ''
    wanted = {g: v['box'] for g, v in shot.reference.get('boxes', {}).items() if g in in_box}
    if len(wanted) >= 3:
        rw = max(v[2] for v in wanted.values()) - min(v[0] for v in wanted.values())
        rh = max(v[3] for v in wanted.values()) - min(v[1] for v in wanted.values())
        if rw + 0.02 > limit_w or rh + 0.02 > limit_h:
            limit_w, limit_h = max(limit_w, round(rw + 0.02, 2)), max(limit_h, round(rh + 0.02, 2))
            reference_words = f' The rule\'s limit is 0.40 x 0.50, but the reference measures {rw:.2f} x {rh:.2f} by the same count, so its size plus 0.02 is allowed.'
    ok = w <= limit_w and h <= limit_h
    fixes = []
    sx, sy = centre_of(shot.visible[shot.subject]) if shot.shows(shot.subject) else ((l + r) / 2, (t + b) / 2)
    if w > limit_w:
        far = edge['left'] if abs(boxes[edge['left']][0] - sx) > abs(boxes[edge['right']][2] - sx) else edge['right']
        push = (w - limit_w) * shot.width + 4
        fixes.append(move_words(shot, far, push if far == edge['left'] else -push, 0) or f'bring {far} in toward {shot.subject}')
    if h > limit_h:
        far = edge['top'] if abs(boxes[edge['top']][1] - sy) > abs(boxes[edge['bottom']][3] - sy) else edge['bottom']
        push = (h - limit_h) * shot.height + 4
        anchor = boxes[far][1] if far == edge['top'] else boxes[far][3]
        fixes.append(move_words(shot, far, 0, push if far == edge['top'] else -push, anchor) or f'bring {far} in toward {shot.subject}')
    report.add('rule 3: story props close together', ok,
               f'The story props{" (leaving out " + ", ".join(sorted(excluded)) + ")" if excluded else ""} fill a box {w:.2f} of the frame wide '
               f'and {h:.2f} tall (limit {limit_w:.2f} x {limit_h:.2f}). Its edges: {edge["left"]}\'s left side ({l / shot.width:.2f} across), '
               f'{edge["right"]}\'s right side ({r / shot.width:.2f}), {edge["top"]}\'s top ({t / shot.height:.2f} down) and {edge["bottom"]}\'s '
               f'bottom ({b / shot.height:.2f}).{reference_words}',
               fix=capital('; '.join(fixes)) + '.' if fixes else '', mark=(l, t, r, b), area=True, kind='story',
               how_bad=max(w / limit_w, h / limit_h))
    return np.any([shot.visible[g] for g in dict.fromkeys([shot.subject] + shown) if shot.shows(g)], axis=0)


# ---------------------------------------------------------------------------------------- rule 12: room for phone buttons and titles
def check_right_edge(report, shot):
    must_read = set(shot.check.get('must_read', []))
    limits = {g: 0.95 for g in shot.story}
    limits.update({g: 0.90 for g in must_read})
    # the buttons run down the right edge from a little above the middle to near the bottom; a story prop's
    # parts above or below that strip don't matter (words to read are kept clear at any height)
    top, bottom = int(0.45 * shot.height), int(0.95 * shot.height)
    over, rows = [], []
    for g, limit in limits.items():
        if not shot.shows(g):
            continue
        box = shot.info(g).get('screen_box_unclipped')
        if g in must_read:
            right = box[2] if box else box_of(shot.visible[g])[2] / shot.width
        else:
            rows_in = [np.nonzero(row)[0].max() for row in shot.alone[g][top:bottom] if row.any()]
            if not rows_in:
                continue
            last = float(np.percentile(rows_in, 90))   # a cap or corner under a tenth of its height doesn't count
            right = max(last / shot.width, box[2] if box and last >= shot.width - 2 else 0)   # cut by the frame: where it would end
        rows.append(f'{g} {right:.2f}')
        if right > limit:
            over.append((g, right, limit))
    if not over:
        report.add('rule 12: room for phone buttons', True, f'Everything to read is left of 0.90 across, and the story props left of 0.95 '
                   f'where the buttons are ({", ".join(rows)}).', kind='edges')
        return
    # The subject and its support are tied to where the lines meet (rule 1), so they move by moving the camera.
    # Best: slide the camera to the right without turning it. Near things slide left on screen more than far ones,
    # and where the lines meet stays put (it depends only on which way the camera faces). Or turn it right:
    # everything slides left together, lines included. Other props still past their limit are moved on their own.
    tied = {shot.subject, shot.support} | set(shot.check.get('must_read', []))
    slide, turn = 0.0, 0.0
    for g, right, limit in over:
        if g in tied:
            slide = max(slide, (right - limit + 0.005) * shot.width * shot.info(g)['metres_per_pixel'])
            now = math.atan((right - 0.5) * shot.width / shot.focal)
            wanted = math.atan((limit - 0.005 - 0.5) * shot.width / shot.focal)
            turn = max(turn, math.degrees(now - wanted))
    after_slide = lambda g, right: right - slide / shot.info(g)['metres_per_pixel'] / shot.width
    reads = [f'{g} reaches {right:.2f} across (limit {limit:.2f})' for g, right, limit in over]
    same = [f'{g} {v["box"][2]:.2f}' for g, v in shot.reference.get('boxes', {}).items() if g in limits and v['box'][2] > limits[g]]
    fixes = []
    if slide > 0:
        fixes.append(f'Move the camera about {slide:.2f} m to the right without turning it: near props slide left on screen more than '
                     f'far ones, and where the lines meet stays where it is (check rule 1 again afterwards). Or turn the camera about '
                     f'{turn:.1f} degrees right: everything slides left together, but where the lines meet moves too.')
        if same:
            fixes.append(f'(The reference has the same fault: {", ".join(same)}.)')
    for g, right, limit in over:
        if g in tied or after_slide(g, right) <= limit:
            continue
        words = move_words(shot, g, -(after_slide(g, right) - limit + 0.005) * shot.width, 0)
        fixes.append(capital(words) + (' (after the camera move).' if slide > 0 else '.'))
    fix = ' '.join(fixes)
    worst = max(over, key=lambda o: o[1] - o[2])
    marks = [box_of(shot.visible[g]) for g, _, _ in over]
    report.add('rule 12: room for phone buttons', False,
               '; '.join(reads) + '. Video apps put their buttons down the right edge, from a little above the middle to near the bottom.',
               fix=fix, mark=(min(m[0] for m in marks), min(m[1] for m in marks), shot.width - 1, max(m[3] for m in marks)), area=True,
               kind='edges', how_bad=worst[1] / worst[2])


def check_titles(report, shot, blurred):
    zone = shot.check.get('title_zone')
    if not zone:
        report.note('rule 12: titles in dim sky', 'Not checked: the check file has no "title_zone".')
        return
    l, t, r, b = int(zone[0] * shot.width), int(zone[1] * shot.height), int(zone[2] * shot.width), int(zone[3] * shot.height)
    sky = float(shot.sky[t:b, l:r].mean())
    crossing = [g for g in shot.core if shot.shows(g) and shot.visible[g][t:b, l:r].mean() > 0.01]
    problems, numbers = [], [f'{sky:.0%} of the title area is sky']
    if sky < 0.85:
        problems.append(f'only {sky:.0%} of the title area is sky (need 85%)')
    if crossing:
        problems.append(f'{", ".join(crossing)} reach into it')
    if blurred is not None:
        brightness = float(shot.grey[t:b, l:r].mean())
        numbers.append(f'its brightness {brightness:.2f}')
        if brightness > 0.36:
            problems.append(f'it is too bright for titles ({brightness:.2f}, limit 0.36)')
        y, x = np.unravel_index(np.argmax(blurred), blurred.shape)
        pad_x, pad_y = 0.05 * shot.width, 0.05 * shot.height
        if l - pad_x <= x <= r + pad_x and t - pad_y <= y <= b + pad_y:
            problems.append(f'the brightest light in the frame ({x / shot.width:.2f} across, {y / shot.height:.2f} down) is next to it')
    report.add('rule 12: titles in dim sky', not problems,
               (capital('; '.join(problems)) + '.') if problems else f'The title area ({zone[0]:.2f} to {zone[2]:.2f} across, {zone[1]:.2f} to {zone[3]:.2f} down) is dim, empty sky.',
               '; '.join(numbers), fix='Move the title area into darker, emptier sky, or move what is in it.', mark=(l, t, r, b), area=True, kind='edges')


# ---------------------------------------------------------------------------------------- rule 8: props by meaning
def check_work_props(report, shot):
    total = shot.width * shot.height
    average = float(shot.grey.mean()) if shot.grey is not None else None
    for g in shot.check.get('work', []):
        if not shot.shows(g):
            if shot.info(g):
                report.note('rule 8: work props small, far and dim', f'{g} does not show in this frame.')
            continue
        share = shot.visible[g].sum() / total
        down = centre_of(shot.visible[g])[1] / shot.height
        problems = []
        if share > 0.02:
            problems.append(f'it covers {share:.1%} of the frame (limit 2%)')
        if not 0.45 <= down <= 0.62:
            problems.append(f'its middle is {down:.2f} down (the middle band is 0.45 to 0.62)')
        size_words = f'covers {share:.1%} of the frame' if share >= 0.001 else 'hardly shows (under 0.1% of the frame)'
        what = f'{g} {size_words}, its middle {down:.2f} down'
        if average is not None:
            mean = float(shot.grey[shot.visible[g]].mean())
            what += f', its brightness {mean:.2f} (it must stay under the frame\'s average, {average:.2f})'
            if mean >= average:
                problems.append('it is brighter than the frame\'s average')
        report.add('rule 8: work props small, far and dim', not problems, (what + '. ' + capital('; '.join(problems)) + '.') if problems else what + '.',
                   fix=f'Move {g} further up the street, or into shadow.', mark=box_of(shot.visible[g]), kind='background', how_bad=1 + len(problems))
    corner = np.zeros((shot.height, shot.width), bool)
    corner[shot.height // 2:, :shot.width // 2] = True
    big = []
    for g, mask in shot.visible.items():
        share = (mask & corner).sum() / total
        if share > 0.01:
            big.append(g)
            report.add('rule 8: nothing big where the eye enters', False, f'{g} fills {share:.1%} of the frame in the bottom-left quarter, where the eye enters (limit 1%).',
                       fix=f'Move {g} out of the bottom-left quarter.', mark=box_of(mask & corner), kind='story', how_bad=share / 0.01)
    if not big:
        report.add('rule 8: nothing big where the eye enters', True, 'No prop fills more than 1% of the frame in the bottom-left quarter.', kind='story')


def check_dark_entry(report, shot):
    """A big dark shape (a long shadow, a dark lump) in the bottom-left quarter, measured against the lit
    ground around it rather than the whole frame, which is dark at night anyway. The story props' own shaded
    sides don't count: they belong to the group the eye is led to (the picture the user liked has a dark drum there)."""
    top, right = shot.height // 2, shot.width // 2
    quarter = cv2.GaussianBlur(shot.grey[top:, :right], (0, 0), max(1.0, 0.004 * shot.width))
    lit = float(np.percentile(quarter, 75))
    dark = quarter < 0.6 * lit
    story = np.any([shot.visible[g] for g in shot.core if shot.shows(g)] or [np.zeros((shot.height, shot.width), bool)], axis=0)
    dark &= ~story[top:, :right]
    size = max(3, int(0.01 * shot.width) | 1)
    dark = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(dark)
    # dark that runs on out of the top of the quarter is the far street fading into the night, not a shape
    far = {k for k in range(1, n) if (labels[0] == k).sum() > 0.25 * right}
    shapes = [k for k in range(1, n) if k not in far]
    if not shapes:
        report.add('rule 8: nothing big and dark where the eye enters', True, 'Nothing in the bottom-left quarter is much darker than the lit ground '
                   'around it (the far street fading into the dark, and the story props\' own shaded sides, are left out).', kind='light')
        return
    biggest = max(shapes, key=lambda k: stats[k, cv2.CC_STAT_AREA])
    piece = np.zeros((shot.height, shot.width), bool)
    piece[top:, :right] = labels == biggest
    share = piece.sum() / (shot.width * shot.height)
    ok = share <= 0.01
    owners = {g: int((m & piece).sum()) for g, m in shot.visible.items()}
    owner = max(owners, key=owners.get) if owners and max(owners.values()) > 0.3 * piece.sum() else None
    l, t, r, b = box_of(piece)
    what = (f'The biggest dark shape where the eye enters (the bottom-left quarter) covers {share:.1%} of the frame (limit 1%): brightness '
            f'{float(shot.grey[piece].mean()):.2f} against {lit:.2f} for the lit ground around it.')
    if owner:
        what += f' Most of it is {owner}.'
        fix = f'Move {owner} out of the bottom-left quarter, or light it.'
    else:
        what += ' It is not a prop: probably a shadow cast across the ground.'
        fix = ('First give the tool the render\'s log (--render-log): a render that ran out of shadow memory draws false hard shadows. '
               'If the log is clean, find what casts it: turn off each light\'s shadow in turn (the warm lights first), see which one makes '
               'it vanish, and move that light or the thing in its way.')
    report.add('rule 8: nothing big and dark where the eye enters', ok, what, f'from {l / shot.width:.2f} to {r / shot.width:.2f} across, '
               f'{t / shot.height:.2f} to {b / shot.height:.2f} down', fix=fix, mark=(l, t, r, b), area=True, kind='light', how_bad=share / 0.01)


# ---------------------------------------------------------------------------------------- the light rules (5, 6, 10) and the main rule
def warm_lights_near(shot, px, py):
    """The warm lights that send the most light to the spot of ground seen at pixel (px, py): each light's
    strength over its distance squared (ignoring anything that shades it), as words."""
    spot = ground_point(shot, px, py)
    if spot is None:
        return []
    found = []
    for light in shot.facts.get('lights', []):
        red, _, blue = light['colour']
        if red - blue < 0.15 or light['energy'] <= 0 or light['kind'] == 'SUN':
            continue
        distance = float(np.linalg.norm(np.array(light['at']) - spot))
        seen = light['on_screen']
        where = 'in the frame' if seen and 0 <= seen[0] <= 1 and 0 <= seen[1] <= 1 else 'out of the frame'
        found.append((light['energy'] / max(distance, 0.5) ** 2, light['name'], distance, where))
    total = sum(f[0] for f in found) or 1
    return [f'{name} ({distance:.1f} m from it, {where}; about {strength / total:.0%} of the warm light reaching it if nothing shades it)'
            for strength, name, distance, where in sorted(found, reverse=True)[:2]]


def check_light(report, shot, story_union, blurred):
    grey, picture = shot.grey, shot.picture
    width, height = shot.width, shot.height
    subject = shot.subject
    brightest = blurred >= np.percentile(blurred, 97)
    has_subject = shot.shows(subject)
    on_subject = cv2.dilate(shot.visible[subject].astype(np.uint8), np.ones((9, 9), np.uint8)) > 0 if has_subject else np.zeros_like(brightest)
    story_box = np.zeros_like(brightest)
    if story_union is not None:
        l, t, r, b = box_of(story_union)
        story_box[t:b + 1, l:r + 1] = True
    share_subject = (brightest & on_subject).sum() / brightest.sum()
    share_group = (brightest & story_box).sum() / brightest.sum()
    n, labels, stats, _ = cv2.connectedComponentsWithStats(brightest.astype(np.uint8))
    biggest = labels == (1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))) if n > 1 else np.zeros_like(brightest)
    owners = {g: int((m & biggest).sum()) for g, m in shot.visible.items()}
    owner = max(owners, key=owners.get) if owners and max(owners.values()) > 0.2 * biggest.sum() else 'the set (no named prop)'
    ok = share_subject >= 0.40 and share_group >= 0.75
    report.add(f'rule 5: {subject} is the biggest bright thing', ok,
               f'Of the brightest parts (the brightest 3% of the frame), {share_subject:.0%} lie on {subject} (need 40%) and {share_group:.0%} in the '
               f'story props\' box (need 75%). The largest bright patch belongs to {owner}.',
               fix=f'Dim {owner} (the marked bright patch), or light {subject} more.' if owner != subject else f'Light {subject} more, or dim what is around it.',
               mark=box_of(biggest) if owner != subject else box_of(on_subject), area=True, kind='light', how_bad=max(0.40 / max(share_subject, 0.01), 0.75 / max(share_group, 0.01)))
    if has_subject:
        ratio = float(grey[shot.visible[subject]].mean() / grey.mean())
        report.add(f'rule 5: {subject} is bright', ratio >= 1.8, f'{subject} is {ratio:.2f} times as bright as the frame\'s average (need 1.8).',
                   fix=f'Light {subject} more, or darken what is around it.', mark=box_of(shot.visible[subject]), kind='light', how_bad=1.8 / max(ratio, 0.1))
    top_row = [float(grey[:height // 3, a:b].mean()) for a, b in ((0, width // 3), (width // 3, 2 * width // 3), (2 * width // 3, width))]
    report.add('rule 5: keep the sky dim', max(top_row) <= 0.36,
               f'The top third\'s brightness, left to right: {", ".join(f"{v:.2f}" for v in top_row)} (limit 0.36).',
               fix='Darken the sky (or ask the painter for a darker sky).', mark=(0, 0, width - 1, height // 3), area=True, kind='light', how_bad=max(top_row) / 0.36)
    # rule 6: warm light, mostly round the story props
    blue, _, red = [c.astype(np.float32) for c in cv2.split(picture)]
    warmth = np.clip((red - blue) / 255, 0, 1)
    warm = warmth * grey > 0.18
    share_warm = float(warm.mean())
    near_story = cv2.dilate(story_box.astype(np.uint8), np.ones((int(0.06 * width) | 1,) * 2, np.uint8)) > 0
    inside = (warm & near_story).sum() / max(1, warm.sum())
    problems, fixes, mark = [], [], None
    if share_warm > 0.03:
        problems.append(f'warm light covers {share_warm:.1%} of the frame, {share_warm / 0.03:.1f} times the most allowed (3%)')
    if share_warm < 0.015:
        problems.append(f'warm light covers only {share_warm:.1%} of the frame (aim for 1.5 to 3%)')
        fixes.append('Let the fire and the lantern light more.')
    if warm.any() and inside < 0.5:
        problems.append(f'only {inside:.0%} of it lies round the story props (need most of it)')
    if share_warm > 0.03 or (warm.any() and inside < 0.5):
        outside = (warm & ~near_story).astype(np.uint8)
        outside = cv2.morphologyEx(outside, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        m, parts, part_stats, _ = cv2.connectedComponentsWithStats(outside)
        if m > 1:
            patch = parts == (1 + int(np.argmax(part_stats[1:, cv2.CC_STAT_AREA])))
            px, py = centre_of(patch)
            on = {g: int((v & patch).sum()) for g, v in shot.visible.items()}
            surface = max(on, key=on.get) if on and max(on.values()) > 0.3 * patch.sum() else 'the ground and walls'
            lights = warm_lights_near(shot, px, py)
            mark = box_of(patch)
            fixes.append(f'{1 - inside:.0%} of the warm light is away from the story props; the largest patch is on {surface} at {px / width:.2f} across, '
                         f'{py / height:.2f} down (marked). The warm lights lighting it most: {"; ".join(lights) if lights else "none found"}. '
                         f'Shorten their reach (lower their strength or the distance their light travels) first.')
    report.add('rule 6: warm light from the people\'s own lights', not problems,
               (capital('; '.join(problems)) + '.') if problems else f'Warm light covers {share_warm:.1%} of the frame, {inside:.0%} of it round the story props.',
               f'warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py)', fix=' '.join(fixes),
               mark=mark, area=True, kind='light', how_bad=max(share_warm / 0.03, 0.015 / max(share_warm, 1e-4), 0.5 / max(inside, 0.01)))
    if has_subject:
        ys, xs = np.nonzero(shot.visible[subject])
        rows = np.arange(height)[:, None]
        span = ys.max() - ys.min()
        top_band = shot.visible[subject] & (rows < ys.min() + 0.15 * span)
        bottom_band = shot.visible[subject] & (rows > ys.max() - 0.15 * span)
        # how much redder than blue each part is, whatever its brightness (a dim cream and a bright cream count the same)
        hue = (red - blue) / np.maximum(red + blue, 1)
        lift = float(hue[bottom_band].mean() - hue[top_band].mean())
        report.add('rule 6: lit from below', lift >= 0.10,
                   f'The bottom of {subject} is {plain(lift)} warmer than its top, on a scale where 0 is the same colour and 1 is pure red against '
                   f'pure blue; it needs 0.10 (the picture the user liked measures about 0.17).',
                   fix=f'Bring the lantern or the fire\'s light closer below {subject}, or turn down the cool light from above.',
                   mark=box_of(shot.visible[subject]), kind='light', how_bad=0.10 / max(lift, 0.01))
    # rule 10: the quiet side
    edges = cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.GaussianBlur(grey, (0, 0), 2), cv2.CV_32F)), (0, 0), 25)
    contrast = np.abs(grey - grey.mean())
    weight = edges / edges.mean() + contrast / contrast.mean()
    subject_right = (centre_of(shot.visible[subject])[0] if has_subject else width / 2) >= width / 2
    quiet_cols = slice(0, width // 2) if subject_right else slice(width // 2, width)
    quiet_name = 'left' if subject_right else 'right'
    quiet = float(weight[:, quiet_cols].sum() / weight.sum())
    ok = 0.40 <= quiet <= 0.48
    report.add('rule 10: the quiet side keeps the frame from tipping', ok,
               f'The {quiet_name} half (away from {subject}) holds {quiet:.0%} of the weight (aim for 40 to 48%).',
               fix=(f'Add a few small dim lights or details in the {quiet_name} half (a lit window, a distant lamp) until it holds about 42%.'
                    if quiet < 0.40 else f'The {quiet_name} half is too busy: dim or remove some of its detail.'), kind='light',
               how_bad=0.40 / max(quiet, 0.01) if quiet < 0.40 else quiet / 0.48)
    if has_subject:
        notice_bright = float(grey[shot.visible[subject]].mean())
        side = blurred[:, quiet_cols]
        y, x = np.unravel_index(np.argmax(side), side.shape)
        x += quiet_cols.start
        brightest_there = float(side.max())
        big = [g for g, v in shot.visible.items() if v[:, quiet_cols].sum() / (width * height) > 0.02 and g not in shot.core]
        problems = []
        if brightest_there >= notice_bright:
            problems.append(f'a light in the {quiet_name} half (at {x / width:.2f} across, {y / height:.2f} down) is {brightest_there:.2f} bright, as bright as {subject} ({notice_bright:.2f})')
        if big:
            problems.append(f'{", ".join(big)} cover more than 2% of the frame there')
        report.add('rule 10: nothing on the quiet side outshines the subject', not problems,
                   (capital('; '.join(problems)) + '.') if problems else f'Nothing in the {quiet_name} half is as bright as {subject}, and no prop there covers more than 2%.',
                   fix='Dim that light (or move it further away), and move or shrink big props on that side.',
                   mark=(x - 25, y - 25, x + 25, y + 25) if brightest_there >= notice_bright else None, kind='light', how_bad=2)
    # the main rule: every strong thing points at the same place
    spots = {}
    if shot.meet:
        spots['where the lines meet'] = (shot.meet[0], shot.meet[1])
    bx, by = centre_of(brightest)
    spots['centre of the brightest parts'] = (bx / width, by / height)
    if warm.any():
        wx, wy = centre_of(warm)
        spots['centre of the warm light'] = (wx / width, wy / height)
    if story_union is not None:
        sx, sy = centre_of(story_union)
        spots['centre of the story props'] = (sx / width, sy / height)
    if has_subject:
        nx, ny = centre_of(shot.visible[subject])
        spots[f'centre of {subject}'] = (nx / width, ny / height)
    l, r = min(v[0] for v in spots.values()), max(v[0] for v in spots.values())
    t, b = min(v[1] for v in spots.values()), max(v[1] for v in spots.values())
    ok = (r - l) <= 0.40 and (b - t) <= 0.50
    middle = (float(np.median([v[0] for v in spots.values()])), float(np.median([v[1] for v in spots.values()])))
    odd = max(spots, key=lambda k: math.hypot(spots[k][0] - middle[0], spots[k][1] - middle[1]))
    report.add('main rule: every strong thing points at the same place', ok,
               '; '.join(f'{k} {v[0]:.2f} across, {v[1]:.2f} down' for k, v in spots.items()) +
               f'. Together they span {r - l:.2f} of the frame wide and {b - t:.2f} tall (limit 0.40 x 0.50, holding {subject}).',
               fix=f'The odd one out is the {odd}: fix that first.', mark=(l * width, t * height, r * width, b * height), area=True,
               kind='main', how_bad=max((r - l) / 0.40, (b - t) / 0.50))
    return spots


# ---------------------------------------------------------------------------------------- matching the reference's placing
def check_reference_places(report, shot):
    boxes = shot.reference.get('boxes', {})
    if not boxes:
        return
    if shot.camera_fault:
        report.note('reference: where each prop stands',
                    'Not judged: the camera is wrong (<<camera>>), and the camera moves everything on screen. Fix the camera, then check again; '
                    'don\'t move any prop yet.')
        return
    landmarks = []
    for g, wanted in boxes.items():
        info = shot.info(g)
        if not info:
            continue
        if wanted.get('landmark'):
            if shot.alone[g].any():
                l, t, r, b = box_of(shot.alone[g])
                ours = ((l + r) / 2 / shot.width, (t if wanted.get('compare') == 'top' else (t + b) / 2) / shot.height)
                want = ((wanted['box'][0] + wanted['box'][2]) / 2, wanted['box'][1] if wanted.get('compare') == 'top' else (wanted['box'][1] + wanted['box'][3]) / 2)
                landmarks.append(f'{g} ours at {ours[0]:.2f} across, {ours[1]:.2f} down; the reference\'s at {want[0]:.2f}, {want[1]:.2f}')
            continue
        if any(i.get('name') == f'resting:{g}' and i['passed'] is False for i in report.items):
            report.note('reference: where each prop stands', f'{g}: not compared until it rests where it should (<<resting:{g}>>).')
            continue
        if not shot.alone[g].any():
            if g not in shot.core:
                box = info.get('screen_box_unclipped')
                where = side_words(box) if box else 'behind the camera'
                report.add('reference: where each prop stands', False, f'{g} is in the reference but not in our frame ({where or "hidden"}).',
                           fix=f'Bring {g} into the frame near {wanted["box"][0]:.2f} to {wanted["box"][2]:.2f} across.', kind='reference', how_bad=3)
            continue   # a story prop that doesn't show has its own problem
        l, t, r, b = box_of(shot.alone[g])   # the whole prop, as if nothing hid it
        ours = np.array([l / shot.width, t / shot.height, r / shot.width, b / shot.height])
        want = np.array(wanted['box'])
        top = wanted.get('compare') == 'top'
        point = lambda box: ((box[0] + box[2]) / 2, box[1] if top else (box[1] + box[3]) / 2)
        (ox, oy), (wx, wy) = point(ours), point(want)
        size = (ours[3] - ours[1]) / max(1e-6, want[3] - want[1])
        size_ok = top or 0.8 <= size <= 1.25
        fixes = []
        across_off = abs(ox - wx) > 0.04
        limit = 0.90 if g in shot.check.get('must_read', []) else 0.95 if g in shot.story else None
        new_right = (r / shot.width) + (wx - ox)
        if across_off and wx > ox and limit and new_right > limit:
            report.note('reference: where each prop stands',
                        f'{g}: the reference has it {wx - ox:.2f} of the frame width further right (ours at {ox:.2f} across, the reference\'s at '
                        f'{wx:.2f}), but matching that would push its right edge to {new_right:.2f}, past rule 12\'s limit of {limit:.2f}: '
                        f'leave it (the reference breaks rule 12 there).')
            across_off = False   # judged in the note; not a problem
        if across_off or abs(oy - wy) > 0.04:
            fixes.append(move_words(shot, g, (wx - ox) * shot.width if across_off else 0,
                                    (wy - oy) * shot.height if abs(oy - wy) > 0.04 else 0, oy * shot.height)
                         or f'moving {g} along the ground can\'t bring it to that height on screen; the camera or the reference differs')
        if not size_ok:
            mover = shot.carrier(g)
            fixes.append(f'it is {size:.2f} times as tall as the reference\'s: make it {1 / size:.2f} times {"bigger" if size < 1 else "smaller"}, '
                         f'or move {f"{mover} (with {g} on it)" if mover else "it"} about {abs(info["distance"] * (1 - size)):.2f} m '
                         f'{"nearer to" if size < 1 else "further from"} the camera (which also moves it on screen)')
        ok = not across_off and abs(oy - wy) <= 0.04 and size_ok
        report.add('reference: where each prop stands', ok,
                   f'{g}: ours at {ox:.2f} across, {oy:.2f} down; the reference\'s at {wx:.2f}, {wy:.2f}' +
                   ('' if top else f'; ours is {size:.2f} times as tall as the reference\'s') + '.',
                   fix=(capital('; '.join(fixes)) + '.') if fixes else '', mark=(l, t, r, b), area=True, kind='reference',
                   how_bad=max(abs(ox - wx) if across_off else 0, abs(oy - wy)) / 0.04 + (0 if size_ok else abs(math.log(size)) * 4),
                   arrow=((ox * shot.width, oy * shot.height), (wx * shot.width, wy * shot.height)))
    if landmarks:
        report.note('reference: landmarks', 'These are buildings, not props: they are never moved; they only show whether the camera matches. '
                    + '; '.join(landmarks) + '.')


# ---------------------------------------------------------------------------------------- drawing and writing
LEGEND = ('Boxes on marked.jpg carry the problem\'s number (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 '
          'limits of rule 12. Yellow arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the '
          'lines meet; white, the centre of the brightest parts; orange, the warm light; blue, the story props; green, the subject.')

NOT_CHECKED = [
    'rule 7 (story props stacked in upright columns, something in the top third): judge by eye.',
    'rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.',
    'rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.',
    'whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.',
]

# words in Blender's log that mean the finished picture's light can't be trusted, and what each does
RENDER_FAULTS = {'Shadow buffer full': 'it ran out of shadow memory, which draws false hard shadows',
                 'Could not allocate shadow atlas': 'it could not set up its shadow memory at all, so shadows are missing'}

SPOT_COLOURS = {'where the lines meet': (200, 60, 200), 'centre of the brightest parts': (255, 255, 255),
                'centre of the warm light': (0, 150, 255), 'centre of the story props': (255, 140, 30)}


def label(image, text, x, y, colour):
    height, width = image.shape[:2]
    x, y = int(min(max(x, 4), width - 18 * len(text) - 6)), int(min(max(y, 30), height - 8))
    cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 6, cv2.LINE_AA)
    cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 2, cv2.LINE_AA)


def draw_marked(path, shot, ranked, spots):
    image = (shot.picture if shot.picture is not None else shot.ids_picture).copy()
    width, height = shot.width, shot.height
    for x in (0.90, 0.95):   # rule 12's right-edge limits
        for y in range(0, height, 24):
            cv2.line(image, (int(x * width), y), (int(x * width), y + 12), (0, 200, 255), 2)
    for item in sorted([i for i in ranked if i['mark'] is not None], key=lambda i: not i['area']):   # areas first, small places on top
        l, t, r, b = (int(v) for v in item['mark'])
        l, t, r, b = max(l, 1), max(t, 1), min(r, width - 2), min(b, height - 2)
        colour, thick = ((0, 170, 255), 2) if item['area'] else ((40, 40, 255), 4)
        cv2.rectangle(image, (l, t), (r, b), (0, 0, 0), thick + 3)
        cv2.rectangle(image, (l, t), (r, b), colour, thick)
        if item['area']:
            label(image, str(item['number']), l + 6, b - 10, colour)
        else:
            label(image, str(item['number']), r + 6, t + 26, colour)
    for item in ranked:
        if item['arrow']:
            (x0, y0), (x1, y1) = item['arrow']
            cv2.arrowedLine(image, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 0), 7, cv2.LINE_AA, tipLength=0.2)
            cv2.arrowedLine(image, (int(x0), int(y0)), (int(x1), int(y1)), (0, 220, 255), 3, cv2.LINE_AA, tipLength=0.2)
    for name, (x, y) in (spots or {}).items():
        colour = SPOT_COLOURS.get(name, (60, 220, 60))
        centre = (int(x * width), int(y * height))
        cv2.circle(image, centre, 18, (0, 0, 0), 9, cv2.LINE_AA)
        cv2.circle(image, centre, 18, colour, 4, cv2.LINE_AA)
    if shot.picture is None:
        cv2.rectangle(image, (0, height - 50), (width, height), (0, 0, 0), -1)
        cv2.putText(image, 'flat-colour picture: no finished picture was given', (14, height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, 88])


def write_report(path, report, ranked, title, shot):
    checks = sum(1 for i in report.items if i['passed'] is not None)
    lines = [f'# Shot check: {title}', '',
             f'{len(ranked)} problem{"s" if len(ranked) != 1 else ""} found in {checks} checks, numbered worst first (the camera first, '
             'because it moves everything on screen).', '',
             f'How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). '
             f'Pixels are this frame\'s ({shot.width} wide). Metres are metres in the street; "Blender x, y" is a spot on the street\'s map '
             '(x across the street, y up it). ' + LEGEND, '']
    if shot.picture is None:
        lines += ['No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main '
                  'rule, and the dark shape in rule 8) are not checked.', '']
    if ranked:
        first = ranked[0]
        lines += ['## Fix first', '', f'Problem 1 ({first["rule"]}). ' + (first['fix'] or first['what'])]
        if shot.camera_fault:
            lines.append('Fix the camera before anything else, then check again: the places of the props on screen will all change.')
        lines += ['', '## Problems', '']
        for item in ranked:
            lines.append(f'{item["number"]}. **{item["rule"]}.** {item["what"]}' + (f' ({item["numbers"]})' if item['numbers'] else ''))
            if item['fix']:
                lines.append(f'   - Fix: {item["fix"]}')
        lines.append('')
    lines += ['## Passed', '']
    lines += [f'- {i["rule"]}: {i["what"]}' for i in report.items if i['passed'] is True]
    notes = [i for i in report.items if i['passed'] is None]
    if notes:
        lines += ['', '## Notes', ''] + [f'- {i["rule"]}: {i["what"]}' + (f' ({i["numbers"]})' if i['numbers'] else '') for i in notes]
    lines += ['', '## Not checked by this tool', ''] + [f'- {text}' for text in NOT_CHECKED]
    text = '\n'.join(lines) + '\n'
    open(path, 'w').write(text)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', required=True)
    parser.add_argument('--facts', required=True)
    parser.add_argument('--picture')
    parser.add_argument('--out', required=True)
    parser.add_argument('--title', default='')
    parser.add_argument('--render-log', help='the log Blender wrote while rendering the finished picture, to catch render faults')
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    shot = Shot(args)
    report = Report()
    check_set_up(report, shot)
    if args.render_log:
        log = open(args.render_log, errors='replace').read()
        faults = {words: log.count(words) for words in RENDER_FAULTS if words in log}
        report.add('set-up: the finished picture rendered cleanly', not faults,
                   'The render\'s log says ' + '; '.join(f'"{w}" {n} time{"s" if n != 1 else ""} ({RENDER_FAULTS[w]})' for w, n in faults.items()) + '.'
                   if faults else 'The render\'s log shows no shadow-memory faults.',
                   fix='Render again so the log is clean (set_dressing.render keeps the shadow memory at \'1024\' and lowers the shadows\' '
                       'resolution for wide pictures), and judge the light rules on that picture.', kind='set-up', how_bad=5)
    check_camera(report, shot)
    check_camera_match(report, shot)
    check_reference_lines(report, shot)
    shot.camera_fault = any(i['kind'] == 'camera' and i['passed'] is False for i in report.items)
    check_resting(report, shot)
    check_missing(report, shot)
    check_lines(report, shot)
    touching = check_pairs(report, shot)
    story_union = check_story_props(report, shot, touching)
    check_cut_by_edge(report, shot)
    check_right_edge(report, shot)
    blurred = cv2.GaussianBlur(shot.grey, (0, 0), shot.width * 0.01) if shot.grey is not None else None
    check_titles(report, shot, blurred)
    check_work_props(report, shot)
    spots = None
    if shot.grey is not None:
        check_dark_entry(report, shot)
        spots = check_light(report, shot, story_union, blurred)
    check_reference_places(report, shot)
    if shot.camera_fault:
        report.camera_first()
    ranked = report.rank()
    draw_marked(os.path.join(args.out, 'marked.jpg'), shot, ranked, spots)
    print(write_report(os.path.join(args.out, 'report.md'), report, ranked, args.title or os.path.basename(os.path.normpath(args.facts)), shot))


if __name__ == '__main__':
    main()
