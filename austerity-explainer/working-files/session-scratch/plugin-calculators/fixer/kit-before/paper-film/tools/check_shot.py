"""What this does: checks a shot against the composing rules ("07 Composing a shot.md") and, if given, a
reference picture, and says exactly what is wrong and what to change, in plain words and metres.

It reads what shot_facts.py measured in Blender (flat colour pictures of every named group of props, the
exact camera, where the street's lines meet, the lights, and what each prop stands on), and optionally the
finished picture of the same frame (for the light rules). It writes:
    report.md     the problems, worst first, each with its numbers and the fix; then what passed, notes,
                  and what this tool does not check
    marked.jpg    the frame with each problem's place drawn on it, numbered as in the report
    known.json    only when the check file has "kind_of_shot" or "accepted": the problems, and the known and allowed ones,
                  for other tools (a preflight)
Use:
    python3 check_shot.py --check shot-check.json --facts FACTS_FOLDER [--picture FRAME.png] --out OUT_FOLDER [--settings FILE]
    (--settings: film-settings.json for "kind_of_shot" and "accepted"; default kit/film-settings.json or FILM_SETTINGS)
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
    "story_reaches_down"  optional (off unless given): rule 7's use of the frame's height, checked as "some story prop
                    or the subject reaches at least this far down the frame" (a fraction, for example 0.70), so the
                    story group fills the frame into its lower part instead of standing small and high over bare
                    ground (the notice corner's drum, chair and pail fill 0.45 to 0.8 down)
    "kind_of_shot"  optional: the view's kinds of shot (still_life, crowd, overview, interior, dark_subject; film-settings.json
                    shot_kind_profiles, read through kit/calculators/settings.py). A problem a kind switches off or loosens is
                    listed under "Known and allowed" instead of as a problem; a kind's replacement test is added (a crowd: heads
                    apart and every figure half seen, for the groups listed in "figures"; a dark subject: its outline against
                    the light round it). Without it nothing changes.
    "accepted"      optional: problems the project chose to keep, each {"rule": a shot_kind_profiles rule name or the
                    report's rule words, "things": [groups] (optional), "reason", "who", "date", "measured" (optional)}.
                    A matching problem is listed under "Known and allowed", not as a new problem, unless it has grown more
                    than 5% past the number it was accepted at. An entry that matches nothing is noted (the problem has gone).
    "figures"       optional: the groups that are people (a crowd's rule 4 between figures is replaced by head spacing)
    "fill"          optional: props an overview may use to reach down the frame (rule 7)
    "support_surfaces"  optional: indoors, [{"name": "counter", "height": 0.885}]: a prop "landed high" on one of them rests
    "reference"     optional: the picture to match: where its lines meet; boxes of groups in it
                    ("compare": "top" judges a box's top instead of its middle, for things cut by the
                    frame; "landmark": true marks a building used only to match the camera); and
                    "camera_match" landmarks (points and lines read off the picture, with the same things
                    in Blender metres)
Positions are fractions of the frame: 0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom.
Pixel limits are the rules file's, which are set on a frame 1,536 pixels wide, scaled to this frame's width.
"""
import argparse
import hashlib
import json
import math
import os
import re

import cv2
import numpy as np

VERSION = hashlib.sha1(open(__file__, 'rb').read()).hexdigest()[:8]

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


def past(value, limit, unit):
    """How far a value is past its limit, counted in steps of `unit` (a step a viewer would notice): 1 at the limit,
    2 one step past, at most 10. Every composing problem is scored this way, so "worst first" compares like with like."""
    return 1 + min(9.0, abs(value - limit) / unit)


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
            if solo is None:
                raise SystemExit(f'check_shot: the flat-colour picture of "{g}" is missing ({args.facts}/solo/{g}.png): measure the scene again.')
            self.alone[g] = solo.max(axis=2) > 8
        self.picture = None
        if args.picture:
            self.picture = cv2.imread(args.picture)
            if self.picture is None:
                raise SystemExit(f'check_shot: can\'t read the finished picture {args.picture}.')
            ph, pw = self.picture.shape[:2]
            if abs(pw / ph - self.width / self.height) > 0.01:
                raise SystemExit(f'check_shot: the finished picture is {pw} x {ph}, a different shape from the measured frame '
                                 f'({self.width} x {self.height}): it can\'t be the same view.')
            if (ph, pw) != (self.height, self.width):
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
        if self.subject not in self.facts['groups']:
            raise SystemExit(f'check_shot: the check file must name the shot\'s "subject", one of its measured groups '
                             f'({", ".join(self.facts["groups"])}); it gives {self.subject!r}.')
        self.support = self.check.get('support')
        self.story = [g for g in self.check.get('story', []) if g in self.facts['groups']]
        self.core = [g for g in dict.fromkeys([self.subject] + self.story) if g in self.facts['groups']]
        self.on_ground = set(self.check.get('on_ground', []))
        self.rests_on = self.check.get('stands_on', {})
        self.reference = self.check.get('reference') or {}
        self.reference_note = ''
        shape = (self.reference.get('camera_match') or {}).get('picture_size')
        if shape and abs(shape[0] / shape[1] - self.width / self.height) > 0.02:
            self.reference_note = (f'The reference picture is {shape[0]} x {shape[1]}, a different shape from this frame ({self.width} x '
                                   f'{self.height}), so its places can\'t be compared as fractions of the frame: only its landmarks are used.')
            self.reference = {'camera_match': self.reference.get('camera_match')}
        self.camera_fault = False
        self.fitted_eye = None
        self.rule12_over = set()
        self.apart = []

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

    def add(self, rule, passed, what, numbers='', fix='', mark=None, area=False, kind='story', how_bad=1.0, arrow=None, name=None, pair=None,
            rule_id=None, measured=None, things=None):
        """One check. `kind` (see KINDS) and `how_bad` (how far past its limit) set the order of the problems;
        `name` lets other problems point at this one ("<<name>>" in their text becomes "problem N"). `rule_id` (a rule of
        film-settings.json's shot_kind_profiles), `measured` (the number judged) and `things` (the groups it is about) are kept
        for the kinds of shot and the accepted list (apply_kinds_and_accepted); they change nothing printed."""
        passed = bool(passed)   # numpy's yes/no would slip past the report's checks
        if mark is not None and not area:
            l, t, r, b = mark
            area = (r - l) > 130 or (b - t) > 160   # bigger than a small place on a 1080-wide frame: draw it as an area
        item = dict(rule=rule, passed=passed, what=what, numbers=numbers, fix='' if passed else fix,
                    mark=None if passed else mark, area=area, kind=kind, how_bad=float(how_bad),
                    arrow=None if passed else arrow, name=name, number=None, pair=pair, rule_id=rule_id, measured=measured,
                    things=list(things) if things else (list(pair) if pair else []))
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
    half_w, half_d = 0.7 * info['width'] / 2, 0.7 * info['depth'] / 2   # a round drum or a turned chair fills about 70% of its box
    riding = {h for h, on in shot.rests_on.items() if on == g} | {shot.rests_on.get(g)} | {g, shot.subject}
    clash = lambda px, py, o: abs(px - o['centre'][0]) < half_w + 0.35 * o['width'] and abs(py - o['centre'][1]) < half_d + 0.35 * o['depth']
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
    info = shot.info(g)
    metres = info['metres_per_pixel']
    # a small move of a prop that rests on another is made on its seat or top; a big one moves what carries it
    small = carrier and g != shot.subject and max(abs(dx), abs(dy)) * metres * 4 <= 0.12
    mover = g if small or not carrier else carrier
    name = (f'{g} on {carrier}\'s seat or top' if small else f'{carrier} (with {g} on it)') if carrier else g
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


def edge_run(shot, front, back, need_overlap, scale):
    """A long stretch where the back prop's visible edge runs right along the front prop's edge and stops there,
    instead of clearly passing behind it (a post standing exactly at a board's edge). Measured on what shows, so a
    deep overlap somewhere else (a hidden collar) doesn't excuse it. Returns (length in pixels, the stretch, 'sideways'
    or 'up and down': which way to move to fix it), or None."""
    seen_front = without_wires(shot.visible[front], shot.width)
    seen_back = without_wires(shot.visible[back], shot.width)
    if not (seen_front.any() and seen_back.any()):
        return None
    near = seen_back & cv2.dilate(seen_front.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)   # back pixels within 2 of the front
    if near.sum() < 20 * scale:
        return None
    joined = cv2.dilate(near.astype(np.uint8), np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(joined)
    depth = int(math.ceil(need_overlap))
    best = None
    for k in range(1, n):
        segment = (labels == k) & near
        length = max(stats[k, cv2.CC_STAT_WIDTH], stats[k, cv2.CC_STAT_HEIGHT])
        if length < 40 * scale:
            continue
        band = cv2.dilate(segment.astype(np.uint8), np.ones((2 * depth + 1, 2 * depth + 1), np.uint8)).astype(bool) & seen_front
        if band.sum() == 0:
            continue
        # how much of the front edge's band has the back prop under it, row by row along an upright edge (column by
        # column along a level one): the longest stretch where it hasn't is the run. Judged as a whole, a board's panel
        # passing deep behind the drum's top excused its post running 2 pixels behind the drum's side below (log 32)
        upright = stats[k, cv2.CC_STAT_HEIGHT] >= stats[k, cv2.CC_STAT_WIDTH]
        axis = 1 if upright else 0
        in_band = band.sum(axis=axis)
        under = (band & shot.alone[back]).sum(axis=axis)
        lines = np.nonzero(in_band)[0]
        touching = np.zeros(len(in_band), bool)
        touching[lines] = under[lines] < 0.35 * in_band[lines]
        run, start, longest, longest_at = 0, 0, 0, (0, 0)
        for i, t in enumerate(touching):
            run = run + 1 if t else 0
            if run == 1:
                start = i
            if run > longest:
                longest, longest_at = run, (start, i + 1)
        if longest >= 40 * scale and (best is None or longest > best[0]):
            stretch = np.zeros_like(segment)
            if upright:
                stretch[longest_at[0]:longest_at[1], :] = segment[longest_at[0]:longest_at[1], :]
            else:
                stretch[:, longest_at[0]:longest_at[1]] = segment[:, longest_at[0]:longest_at[1]]
            best = (int(longest), stretch, 'sideways' if upright else 'up and down')
    return best


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


def picture_mismatch(shot):
    """The props whose outlines in the finished picture don't line up with where Blender measured them (a picture
    made before the scene changed). A prop that moved lines up clearly better with the picture's edges when its
    outline is slid a little; a prop whose edges are just faint (dark on dark) lines up no better anywhere."""
    # edges in brightness and in colour: a rusty orange drum against a blue-grey road is about as bright as the road,
    # so a brightness-only edge finder missed its whole side (log 31)
    lab = cv2.cvtColor(cv2.GaussianBlur(shot.picture, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
    edges = cv2.Canny(lab[:, :, 0], 20, 60) > 0
    for colour in (1, 2):
        edges |= cv2.Canny(lab[:, :, colour], 10, 30) > 0
    near = cv2.dilate(edges.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    step, reach = max(2, shot.width // 270), shot.width // 30   # slides of up to a thirtieth of the frame's width
    off = []
    for g in dict.fromkeys(shot.core + shot.check.get('pairs_also', [])):
        if not shot.shows(g) or shot.visible[g].sum() < 400:
            continue
        # the story props always; others only when they cover 0.5% of the frame: small far dustbins among the
        # houses' windows lined up with some other edge when slid, by chance (gain 0.19 in an up-to-date picture)
        if g not in shot.core and shot.visible[g].sum() < 0.005 * shot.width * shot.height:
            continue
        mask = shot.visible[g].astype(np.uint8)
        ys, xs = np.nonzero((mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0)

        def agree(dx, dy):
            y, x = ys + dy, xs + dx
            inside = (y >= 0) & (y < shot.height) & (x >= 0) & (x < shot.width)
            return near[y[inside], x[inside]].sum() / max(1, inside.sum())
        here = agree(0, 0)
        best, dx, dy = max((agree(dx, dy), dx, dy) for dx in range(-reach, reach + 1, step) for dy in range(-reach, reach + 1, step))
        # up-to-date pictures: no prop lined up better when slid (gain 0, even a dim drum at 0.64); props that had
        # since moved gained 0.09 to 0.23, or lined up under 0.45 everywhere (log 31)
        if best - here >= 0.08 or best < 0.45:
            ways = [f'{abs(dx)} pixels {"right" if dx > 0 else "left"}'] * (dx != 0) + [f'{abs(dy)} pixels {"down" if dy > 0 else "up"}'] * (dy != 0)
            slid = f'; {best:.0%} when slid {" and ".join(ways)}' if best - here >= 0.08 else ''
            off.append(f'{g} ({here:.0%} of its outline lines up{slid})')
    return off


def check_set_up(report, shot):
    for g in shot.facts.get('missing_groups', []):
        if g in [shot.subject, shot.support] + shot.story:   # the shot can't be judged without it
            report.add('set-up', False, f'No object in the scene matches the group "{g}", so it was not measured.',
                       fix=f'Check the name patterns of "{g}" in the check file against the objects\' names in Blender.', kind='set-up', how_bad=10)
        else:   # a background prop this version of the scene may simply not have
            report.note('set-up', f'No object in the scene matches the group "{g}", so it was not measured (if the scene should have it, '
                                  f'check the name patterns of "{g}" in the check file against the objects\' names in Blender).')


def check_camera(report, shot):
    cam = shot.camera
    tilt, roll = cam['tilt_degrees'], cam['roll_degrees']
    level = not shot.tilted()
    fixes = []
    if abs(tilt) > 0.5:
        fixes.append(f'tilt the camera {plain(abs(tilt), 1)} degrees {"down" if tilt > 0 else "up"} (level)')
    if abs(roll) > 0.5:
        fixes.append(f'take out the camera\'s {plain(abs(roll), 1)}-degree lean')
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
               kind='camera', how_bad=abs(eye - target) / 0.1 + 1, name='camera-height', rule_id='rule2_eye_height', measured=eye)


def camera_axes(turn, tilt=0.0, roll=0.0):
    """The camera's ahead, right and up directions in Blender space (turn + is left, tilt + is up)."""
    yaw, pitch, lean = (math.radians(v) for v in (turn, tilt, roll))
    ahead = np.array([-math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    right = np.array([math.cos(yaw), math.sin(yaw), 0.0])
    up = np.cross(right, ahead)
    return ahead, right * math.cos(lean) - up * math.sin(lean), up * math.cos(lean) + right * math.sin(lean)


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
    low_eye, high_eye = shot.check.get('eye_height', [1.5, 1.9])
    beyond = ''
    if cam.get('eye_height') is not None and not low_eye <= fitted[2] - pavement <= high_eye:   # the reference's camera stands too high or low
        kept = min(max(fitted[2] - pavement, low_eye), high_eye)
        beyond = (f' The reference\'s camera is {fitted[2] - pavement:.2f} m above the pavement, outside a standing person\'s eye height '
                  f'({low_eye:.2f} to {high_eye:.2f} m, rule 2), so the fix keeps it at {kept:.2f} m.')
        fitted = (fitted[0], fitted[1], pavement + kept, fitted[3], fitted[4])
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
    shot.fitted_eye = fitted[2] - pavement
    if ok:
        what = (f'Our camera is within {abs(height):.2f} m in height, {abs(side):.2f} m sideways, {abs(turn):.1f} degrees of turn '
                f'and {abs(view):.1f} degrees of view of the camera that best matches the reference. Even that best camera misses '
                f'the reference\'s landmarks by up to {worst_best:.0f} pixels (the reference is a painting, not an exact photo), '
                f'so differences this small mean nothing.' + beyond)
    else:
        worst = max(ours_errors, key=ours_errors.get)
        what = (f'The camera that best matches the reference (at our distance up the street) is {describe(fitted)}; ours is '
                f'{describe(ours)}. Ours misses the reference\'s landmarks by up to {ours_errors[worst]:.0f} pixels ({worst}); '
                f'the best camera by up to {worst_best:.0f}.' + beyond)
    report.add('reference: the camera', ok, what,
               'landmarks missed by ours, in pixels: ' + ', '.join(f'{k} {v:.0f}' for k, v in ours_errors.items()),
               fix=capital('; '.join(fixes)) + '.' if fixes else '', kind='camera',
               how_bad=10 + max(abs(height) / 0.1, abs(side) / 0.15, abs(turn) / 0.75, abs(view) / 2), name='camera-match')   # the fullest camera fix


def one_camera_fix(report, shot):
    """When the reference camera's fix fails, it already moves and turns the camera fully: the other camera items
    point to it instead of giving their own, different moves."""
    match = next((i for i in report.items if i.get('name') == 'camera-match' and i['passed'] is False), None)
    if not match:
        return
    for i in report.items:
        if i['passed'] is False and i.get('name') == 'camera-height':
            i['fix'] = (f'The camera fix in <<camera-match>> covers this: it puts the camera\'s eye {shot.fitted_eye:.2f} m above the pavement. '
                        'Check again after it.')
        if i['passed'] is False and i.get('name') == 'camera-lines':
            i['fix'] = 'This follows from the camera: the fix in <<camera-match>> moves where the lines meet too. Check again after it.'


def check_camera_distance(report, shot):
    """If most props look bigger or smaller than in the reference by about the same amount, the camera stands too near
    or too far, not every prop: one camera move instead of a move for each prop."""
    sizes = []
    for g, wanted in shot.reference.get('boxes', {}).items():
        info = shot.info(g)
        if wanted.get('landmark') or wanted.get('compare') == 'top' or not info or not shot.alone[g].any():
            continue
        l, t, r, b = box_of(shot.alone[g])
        want = wanted['box']
        if t <= 1 or b >= shot.height - 2:
            continue   # cut by the frame: its height is not its own
        sizes.append((g, (b - t) / shot.height / max(1e-6, want[3] - want[1]), info['distance']))
    if len(sizes) < 4:
        return
    middle = float(np.median([s for _, s, _ in sizes]))
    agree = [x for x in sizes if abs(x[1] - middle) <= 0.15]
    if abs(middle - 1) <= 0.15 or len(agree) < 0.75 * len(sizes):
        report.add('reference: how far the camera stands', True, f'The props are about the reference\'s size (middle of {len(sizes)}: {middle:.2f} times).', kind='camera')
        return
    move = float(np.median([d * (1 - s) for _, s, d in agree]))   # + is nearer
    report.add('reference: how far the camera stands', False,
               f'Most props look {middle:.2f} times as tall as in the reference (' + ', '.join(f'{g} {s:.2f}' for g, s, _ in sizes) + '): the camera stands '
               f'too {"far from" if middle < 1 else "near to"} them, not the props in the wrong places.',
               fix=f'Move the camera about {abs(move):.2f} m {"toward the props (up the street)" if move > 0 else "back (down the street)"}, without turning it, then check again.',
               kind='camera', how_bad=10 + abs(middle - 1) / 0.15, name='camera-distance')


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
        fixes.append(f'Ours meet {abs(dx):.3f} of the frame width {"left" if dx < 0 else "right"} of the reference\'s: turn the camera '
                     f'about {abs(turn):.1f} degrees {"left" if turn > 0 else "right"} (turning left slides everything on screen to the right).')
    if abs(dy) > 0.03:
        where = 'lower' if dy > 0 else 'higher'
        if shot.tilted():
            fixes.append(f'Ours meet {abs(dy):.2f} of the frame height {where} than the reference\'s because our camera is not level '
                         f'(<<camera-level>>): level it and check again.')
        else:
            above = 0.5 - wanted[1]   # how far above the middle the reference's lines meet
            if above > 0.005 and shot.street_slope > 0:
                view = 2 * math.degrees(math.atan(shot.street_slope / (2 * above * math.cos(math.radians(shot.camera['turn_degrees'])))))
                fixes.append(f'Ours meet {abs(dy):.2f} of the frame height {where} than the reference\'s. Our camera is level, so that '
                             f'height is set by the view angle: about {view:.0f} degrees top to bottom would match (ours is '
                             f'{shot.camera["vertical_fov_degrees"]:.1f}). Compare with the camera item first: the reference is a painting, '
                             f'and its street may simply be drawn steeper.')
            else:
                fixes.append(f'Ours meet {abs(dy):.2f} of the frame height {where} than the reference\'s; with a level camera this is the view angle.')
    ok = not fixes
    report.add('reference: where the lines meet', ok,
               f'Ours meet at {meet[0]:.3f} across, {meet[1]:.3f} down; the reference\'s at {wanted[0]:.3f}, {wanted[1]:.3f}: '
               f'{abs(dx):.3f} of the frame width and {abs(dy):.3f} of its height apart '
               f'(a drawn picture\'s lines rarely meet at one exact point, so 0.03 either way is allowed).',
               fix=' '.join(fixes), kind='reference', how_bad=10 + max(abs(dx), abs(dy)) / 0.03, name='camera-lines',
               mark=(meet[0] * shot.width - 22, meet[1] * shot.height - 22, meet[0] * shot.width + 22, meet[1] * shot.height + 22))


# ---------------------------------------------------------------------------------------- props resting where they should
def check_resting(report, shot):
    good = []
    for g in shot.check.get('on_ground', []):
        info = shot.info(g)
        if not info:
            continue
        air, on = info['stands_above_surface_below'], info.get('stands_on')
        x, y = info['centre'][:2]
        street = shot.camera['at'][2] - (shot.camera.get('eye_height') or 0) + shot.street_slope * (y - shot.camera['at'][1])
        known = shot.camera.get('eye_height') is not None and shot.check.get('lines_key', 'street') in shot.check.get('lines', {})
        high = info['bottom'] - street if known else info['stands_above_ground']
        spot = f'at Blender x {x:.2f}, y {y:.2f}'
        if air is None:
            report.add('props rest where they should', False, f'{g} has nothing under it at all ({spot}): it is off the edge of the set.',
                       fix=f'Move {g} back over the street.', kind='resting', how_bad=10, name=f'resting:{g}')
        elif air < -0.05:   # a few centimetres sunk can't be seen
            report.add('props rest where they should', False, f'{g} is sunk {-air:.2f} m into the pavement or road ({spot}).',
                       fix=f'Raise {g} by {-air:.2f} m so it stands on top.', mark=box_of(shot.alone[g]) if shot.alone[g].any() else None,
                       kind='resting', how_bad=-air / 0.03, name=f'resting:{g}')
        elif air > 0.03:
            under = f'the top of {on}' if on and on != 'the set' else 'the pavement or road'
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
                       fix=f'Place {g} again from just above the pavement.', kind='resting', how_bad=high / 0.3, name=f'resting:{g}',
                       rule_id='resting_on', measured={'bottom': info['bottom'], 'above_street': high}, things=[g])
        else:
            good.append(g)
    if good:
        report.add('props rest where they should', True, f'{", ".join(good)} stand on the pavement or road (within 3 cm).', kind='resting')
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
        dx, dy = under['centre'][0] - info['centre'][0], under['centre'][1] - info['centre'][1]
        apart = math.hypot(dx, dy)
        top = (shot.facts.get('support_tops', {}).get(g) or {}).get('top')

        def go(x_metres, y_metres):
            """Words for a move in the street: across it (Blender x) and along it (Blender y)."""
            parts = []
            if abs(x_metres) >= 0.03:
                parts.append(f'about {abs(x_metres):.2f} m to the {"right" if x_metres > 0 else "left"} (across the street)')
            if abs(y_metres) >= 0.03:
                parts.append(f'about {abs(y_metres):.2f} m {"up the street, away from the camera" if y_metres > 0 else "down the street, toward the camera"}')
            return ' and '.join(parts)
        lift = (top - info['bottom']) if top is not None else None
        onto = ''
        if lift is not None and abs(lift) >= 0.03:
            onto = f', and {"lift" if lift > 0 else "lower"} it {abs(lift):.2f} m so it stands on {support}\'s seat or top (Blender height {top:.2f} m)'
        where = (f' {support} stands {apart:.2f} m from {g} ({support}\'s middle at Blender x {under["centre"][0]:.2f}, y {under["centre"][1]:.2f}; '
                 f'{g}\'s at x {info["centre"][0]:.2f}, y {info["centre"][1]:.2f}), so one of them has moved.') if apart > 0.1 else ''
        put_back = (f'move {g} {go(dx, dy)} so it is over the middle of {support}' if apart > 0.1 else f'keep {g} where it is') + onto
        mark = box_of(shot.alone[g]) if shot.alone[g].any() else None
        if air > 0.03:
            report.add('props rest where they should', False, f'{g} should rest on {support}, but there is {air:.2f} m of air under it.{where}',
                       fix=(f'Move {support} {go(-dx, -dy)} so it is back under {g}; or {put_back}.' if apart > 0.1 else capital(put_back) + '.'),
                       mark=mark, kind='resting', how_bad=air / 0.03, name=f'resting:{g}')
        else:
            report.add('props rest where they should', False,
                       f'{g} should rest on {support}, but it stands on {"the pavement" if on in (None, "the set") else on} instead.{where}',
                       fix=capital(put_back) + '.', mark=mark, kind='resting', how_bad=8, name=f'resting:{g}')


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
        if not outside and not shot.alone[g].any():   # its box reaches into the frame, but none of it does
            cx_, cy_ = (l + r) / 2, (t + b) / 2
            outside = ('past the right edge' if cx_ > 1 else 'past the left edge' if cx_ < 0 else 'below the bottom' if cy_ > 1 else
                       'above the top' if cy_ < 0 else 'just outside the edge')
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
                limit = 0.90 if g in shot.check.get('must_read', []) else 0.95
                if tx + (r - l) / 2 > limit - 0.01:   # the reference's own spot may break rule 12: stop short of the buttons
                    tx = limit - 0.01 - (r - l) / 2
                    aim += f', but its right edge should stay left of {limit:.2f} (rule 12)'
            else:
                tx = min(max(cx, 0.05 + (r - l) / 2), 0.95 - (r - l) / 2)
                ty = min(max(cy, 0.03 + (b - t) / 2), 0.97 - (b - t) / 2)
                aim = 'bring it just inside the frame'
            words = move_words(shot, g, (tx - cx) * shot.width, (ty - cy) * shot.height, cy * shot.height) \
                or move_words(shot, g, (tx - cx) * shot.width, 0, cy * shot.height)
            fix = (capital(words) + f' ({aim}).') if words else f'Moving {g} along the ground can\'t bring it into the frame: move the camera.'
            ex, ey = min(max(cx, 0.03), 0.97) * shot.width, min(max(cy, 0.03), 0.97) * shot.height   # where it leaves the frame
            report.add('rule 3: story props in the frame', False,
                       f'{g} is outside the frame, {outside}: it would sit {l:.2f} to {r:.2f} across, {t:.2f} to {b:.2f} down.{resting}',
                       fix=fix, mark=(ex - 35, ey - 35, ex + 35, ey + 35), kind='missing', how_bad=10, name=f'missing:{g}')
        else:
            under = shot.alone[g]
            covered = {o: int((shot.visible[o] & under).sum()) for o in shot.visible if o != g}
            hider = max(covered, key=covered.get) if covered and max(covered.values()) > 0 else 'the set (a wall or a house)'
            report.add('rule 3: story props in the frame', False, f'{g} is in the frame but hidden behind {hider}.{resting}',
                       fix=f'Move {g} out from behind {hider}, or in front of it.', mark=box_of(under), kind='missing', how_bad=9, name=f'missing:{g}')


def check_words_hidden(report, shot):
    """Words to read (the notice) hidden by a prop in front. Its bottom fifth may be covered (rule 3: the chair's back
    may hide the signature, never the key words)."""
    for g in shot.check.get('must_read', []):
        if not shot.shows(g):
            continue
        whole = shot.alone[g]
        l, t, r, b = box_of(whole)
        upper = whole.copy()
        upper[int(b - 0.2 * (b - t)):] = False
        hidden = upper & ~shot.visible[g]
        share = hidden.sum() / max(1, upper.sum())
        if share <= 0.05:
            report.add('rule 3: nothing hides the words', True, f'{share:.0%} of {g}\'s words are hidden (its bottom fifth, the signature, may be covered).', kind='story')
            continue
        covering = {o: int((shot.visible[o] & hidden).sum()) for o in shot.visible if o != g}
        hider = max(covering, key=covering.get) if covering and max(covering.values()) > 0.3 * hidden.sum() else None
        hx, hy = centre_of(hidden)
        cx = (l + r) / 2
        fix = f'Move whatever stands in front of {g} out of the way.'
        if hider:
            ways = []
            hl, ht, hr, hb = box_of(shot.alone[hider])
            columns = np.nonzero(hidden.any(axis=0))[0]
            # slide it sideways off the words (away from their middle, by the width it covers plus a clear gap), unless that
            # takes it past the phone buttons or out of the frame
            push = (columns.max() - columns.min() + 25 * shot.width / 1536) * (1 if hx > cx else -1)
            limit = 0.95 if hider in shot.story else 1.0
            if (push > 0 and (hr + push) / shot.width <= limit) or (push < 0 and (hl + push) / shot.width >= 0.05):
                words = move_words(shot, hider, push, 0)
                if words:
                    ways.append(words)
            # a prop below the words, standing on the ground: nearer the camera it drops on screen, off the words
            if shot.grounded(hider) and hy < (ht + hb) / 2:
                for k in range(5, int(0.3 * shot.height), 5):
                    dropped = np.zeros_like(shot.alone[hider])
                    dropped[k:] = shot.alone[hider][:-k]
                    if (upper & dropped).sum() / max(1, upper.sum()) <= 0.05:   # what it would still cover of the words
                        words = move_words(shot, hider, 0, k, ht)
                        if words:
                            ways.append(words)
                        break
            # a prop that isn't part of the story can go behind the board instead
            behind = shot.carrier(g) or g
            back = shot.info(behind)['distance'] + 0.3 - shot.info(hider)['distance']
            if back > 0 and hider not in shot.core:
                ways.append(f'move {hider} about {back:.2f} m further from the camera, behind {behind}')
            if ways:
                fix = capital('; or '.join(ways)) + f', so it no longer hides {g}\'s words.'
        report.add('rule 3: nothing hides the words', False,
                   f'{share:.0%} of {g}\'s words are hidden' + (f' behind {hider}' if hider else '') + ' (only its bottom fifth, the signature, may be covered).',
                   f'the hidden part is around {hx / shot.width:.2f} across, {hy / shot.height:.2f} down', fix=fix, mark=box_of(hidden),
                   kind='story', how_bad=past(share, 0.05, 0.05))


def check_cut_by_edge(report, shot):
    """Story props cut by the frame's left, top or bottom edge (the right edge is rule 12's, with the phone buttons)."""
    for g in shot.core:
        info = shot.info(g)
        if not shot.shows(g) or not info.get('screen_box_unclipped'):
            continue
        whole = shot.alone[g]
        sides = [side for side, touches in (('left', whole[:, :2].any()), ('top', whole[:2].any()), ('bottom', whole[-2:].any())) if touches]
        if not sides or g == shot.support and sides == ['top']:
            continue
        l, t, r, b = info['screen_box_unclipped']
        inside = max(0, min(r, 1) - max(l, 0)) * max(0, min(b, 1) - max(t, 0))
        share = inside / max(1e-6, (r - l) * (b - t))
        dx = (0.03 - l) * shot.width if 'left' in sides else 0
        dy = -(b - 0.97) * shot.height if 'bottom' in sides else (0.03 - t) * shot.height if 'top' in sides else 0
        words = move_words(shot, g, dx, dy, (t + b) / 2 * shot.height)
        report.add('rule 12: nothing important cut by the frame edge', False,
                   f'{g} is cut by the frame\'s {" and ".join(sides)} edge: about {share:.0%} of it is inside.',
                   f'it would sit {l:.2f} to {r:.2f} across, {t:.2f} to {b:.2f} down',
                   (capital(words) + ' to bring it all in.') if words else 'Move the camera back or sideways to bring it all in.',
                   mark=box_of(shot.visible[g]), kind='edges', how_bad=past(1 - share, 0, 0.05))


# ---------------------------------------------------------------------------------------- rule 1: where the lines meet
def check_lines(report, shot):
    key = shot.check.get('lines_key', 'street')
    if key not in shot.facts.get('lines_meet', {}):
        report.note('rule 1: aim the street at the story', f'Not checked: the check file gives no street direction "{key}" under "lines".')
        return
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
               mark=(mx - 22, my - 22, mx + 22, my + 22), kind='lines', how_bad=past(gap, 0.03, 0.03), rule_id='rule1_meeting_point_gap',
               measured={'gap': gap, 'across_pixels': dx, 'down_pixels': dy, 'span': [l / shot.width, r / shot.width], 'meet_across': shot.meet[0]},
               things=[target])


# ---------------------------------------------------------------------------------------- rules 3 and 4: the story props as one group
def check_pairs(report, shot):
    """Every pair of the listed groups: a clear overlap or a clear gap, never two edges just touching (rule 4).
    Returns which pairs touch or overlap at all (for rule 3)."""
    scale = shot.width / 1536
    # the rules' 20 and 25 pixels on a 1,536-wide frame, rounded up to whole pixels here so the printed limit is the one used
    need_overlap, need_gap, margin = math.ceil(20 * scale), math.ceil(25 * scale), 4 * scale
    names = [g for g in dict.fromkeys(shot.core + shot.check.get('pairs_also', [])) if g in shot.alone and shot.alone[g].any()]
    solid = {g: without_wires(shot.alone[g], shot.width) for g in names}
    touching = {}
    found = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} <= {shot.subject, shot.support}:
                continue   # the subject hangs on its support: they always share an edge
            if shot.rests_on.get(a) == b or shot.rests_on.get(b) == a:
                continue   # one stands on the other (the lantern on the chair): they always share an edge
            whole_overlap = shot.alone[a] & shot.alone[b]
            touching[(a, b)] = bool(whole_overlap.any()) or float(np.where(shot.alone[b], distance_outside(shot.alone[a]), np.inf).min()) <= 3 * scale
            front, back = sorted((a, b), key=lambda g: shot.info(g)['distance'])
            kind = 'story' if a in shot.core or b in shot.core else 'background'   # anything against a story prop is part of the story group
            run = edge_run(shot, front, back, need_overlap, scale)
            if run:
                length, segment, across = run
                found += 1
                sx, sy = centre_of(segment)
                fx, fy = centre_of(shot.visible[front])
                mover = back if back not in (shot.subject, shot.support) else front
                sign = (1 if fx > sx else -1) * (1 if mover == back else -1)   # toward passing behind the front one
                dx, dy = ((sign, 0) if across == 'sideways' else (0, (1 if fy > sy else -1) * (1 if mover == back else -1)))
                into = move_words(shot, mover, dx * (need_overlap + margin), dy * (need_overlap + margin), sy)
                apart = move_words(shot, mover, -dx * (need_gap + margin), -dy * (need_gap + margin), sy)
                ways = ([f'{into} so {back} clearly passes behind {front}'] if into else []) + ([f'{apart} to leave a clear gap'] if apart else [])
                l, t, r, b_ = box_of(segment)
                report.add('rule 4: overlap clearly or leave a clear gap', False,
                           f'{back}\'s edge runs right along {front}\'s edge for {pixels(length)}, without clearly passing behind it. '
                           f'Edges that just meet make near and far things look stuck together.',
                           f'from {t / shot.height:.2f} to {b_ / shot.height:.2f} down, around {sx / shot.width:.2f} across; {front} is nearer the camera',
                           capital(', or '.join(ways)) + '.' if ways else f'Move {back} or {front} sideways.',
                           mark=(l - 10, t - 10, r + 10, b_ + 10), kind=kind, pair=(a, b), how_bad=past(length, 40 * scale, 40 * scale),
                           rule_id='rule4_near_touch', measured=length)
                continue
            both = solid[a] & solid[b]
            if both.any():
                showing = both & (shot.visible[a] | shot.visible[b])
                if showing.sum() < 0.3 * both.sum():
                    continue   # a third thing in front hides the overlap
                if float(np.where(showing, distance_outside(shot.visible[back]), np.inf).min()) > need_gap:
                    continue   # the back one's part there can't be seen (hidden by a third thing): nothing for the eye to judge
                depth = float(max(distance_inside(solid[a])[showing].max(), distance_inside(solid[b])[showing].max()))
                if depth >= need_overlap:
                    if depth < 1.3 * need_overlap:
                        report.note('rule 4: overlap clearly or leave a clear gap', f'{front} overlaps {back} by {pixels(depth)}: it passes, but only '
                                    f'just (the limit is {need_overlap}); a small move of the camera could make the overlap too shallow.')
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
                           mark=box_of(showing), kind=kind, pair=(a, b), how_bad=past(depth, need_overlap, need_overlap / 2),
                           rule_id='rule4_near_touch', measured=depth)
                continue
            # no clear overlap: how far apart are the parts that show? Where only thin parts (a wire) overlap,
            # leave the thin parts out
            # what shows, plus the outline just behind a thin thing in front (a chair post hiding a board's edge)
            near = lambda g: cv2.dilate(shot.visible[g].astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
            va = shot.visible[a] | (shot.alone[a] & near(a) & ~shot.alone[b])
            vb = shot.visible[b] | (shot.alone[b] & near(b) & ~shot.alone[a])
            if whole_overlap.any():
                va, vb = without_wires(va, shot.width), without_wires(vb, shot.width)
            if not (va.any() and vb.any()):
                continue
            gaps = np.where(vb, distance_outside(va), np.inf)
            gap = float(gaps.min())
            if gap >= need_gap:
                if gap < 1.3 * need_gap:
                    report.note('rule 4: overlap clearly or leave a clear gap', f'{a} and {b} are {pixels(gap)} apart: they pass, but only just '
                                f'(the limit is {need_gap}); a small move of the camera could make them nearly touch.')
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
                       mark=(min(x, ax) - 14, min(y, ay) - 14, max(x, ax) + 14, max(y, ay) + 14), kind=kind, pair=(a, b), how_bad=past(gap, need_gap, need_gap / 2),
                       rule_id='rule4_near_touch', measured=gap)
    if not found:
        report.add('rule 4: overlap clearly or leave a clear gap', True,
                   f'No two of {", ".join(names)} just touch (overlaps at least {need_overlap:.0f} pixels deep, gaps at least {need_gap:.0f}).')
    return touching


def check_story_in_3d(report, shot):
    """The story props stand together in the street, not only on screen: each one in front of the support (the board
    is the backdrop), and none more than 0.3 m from every other one (footprints, Blender metres)."""
    support = shot.info(shot.support) if shot.support else None
    standing = [g for g in shot.story if g != shot.support and g in shot.on_ground and shot.info(g)]
    for g in standing:
        info = shot.info(g)
        if support and info['distance'] > support['distance'] + 0.1:
            back = info['distance'] - support['distance'] + 0.3
            report.add('rule 3: story props together in the street', False,
                       f'{g} stands behind {shot.support}: {info["distance"]:.2f} m from the camera against {support["distance"]:.2f} m. On screen it '
                       f'may still look close, but the story props stand in front of {shot.support}.',
                       fix=f'Move {g} about {back:.2f} m nearer to the camera, in front of {shot.support}.',
                       mark=box_of(shot.alone[g]) if shot.alone[g].any() else None, kind='story', how_bad=past(back, 0.3, 0.3), name=f'depth:{g}')
            continue
        gaps = []
        for o in shot.story:
            if o == g or not shot.info(o):
                continue
            p = shot.info(o)
            gx = max(0.0, abs(info['centre'][0] - p['centre'][0]) - (info['width'] + p['width']) / 2)
            gy = max(0.0, abs(info['centre'][1] - p['centre'][1]) - (info['depth'] + p['depth']) / 2)
            gaps.append((math.hypot(gx, gy), o))
        if gaps and min(gaps)[0] > 0.3:
            gap, o = min(gaps)
            p = shot.info(o)
            dx, dy = p['centre'][0] - info['centre'][0], p['centre'][1] - info['centre'][1]
            scale = (gap - 0.1) / max(1e-6, math.hypot(dx, dy))
            report.add('rule 3: story props together in the street', False,
                       f'{g} stands {gap:.2f} m from the nearest other story prop ({o}) in the street: the group should stand together.',
                       fix=f'Move {g} about {abs(dx * scale):.2f} m {"right" if dx > 0 else "left"} (across the street) and {abs(dy * scale):.2f} m '
                           f'{"up" if dy > 0 else "down"} the street, toward {o}.',
                       mark=box_of(shot.alone[g]) if shot.alone[g].any() else None, kind='story', how_bad=past(gap, 0.3, 0.3), name=f'depth:{g}',
                       rule_id='rule3_story_together_metres', measured=gap, things=[g, o])
    if support and standing:
        gaps = []
        for g in standing:
            p = shot.info(g)
            gx = max(0.0, abs(support['centre'][0] - p['centre'][0]) - (support['width'] + p['width']) / 2)
            gy = max(0.0, abs(support['centre'][1] - p['centre'][1]) - (support['depth'] + p['depth']) / 2)
            gaps.append((math.hypot(gx, gy), g))
        gap, nearest = min(gaps)
        if gap > 0.3:
            p = shot.info(nearest)
            dy = p['centre'][1] - support['centre'][1]
            report.add('rule 3: story props together in the street', False,
                       f'{shot.support} stands {gap:.2f} m from the nearest story prop ({nearest}): the group should stand together.',
                       fix=f'Move {shot.support} about {gap - 0.1:.2f} m {"up" if dy > 0 else "down"} the street, toward {nearest}.',
                       mark=box_of(shot.alone[shot.support]) if shot.alone[shot.support].any() else None, kind='story',
                       how_bad=past(gap, 0.3, 0.3), name=f'depth:{shot.support}', rule_id='rule3_story_together_metres', measured=gap,
                       things=[shot.support, nearest])
    if standing and not any(i.get('name', '') and i['name'].startswith('depth:') for i in report.items):
        report.add('rule 3: story props together in the street', True, f'{", ".join(standing)} stand in front of {shot.support} and within 0.3 m of each other.', kind='story')


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
    apart_mask = np.any([shot.visible[g] for g in apart], axis=0) if apart else None
    report.add('rule 3: one touching group', not apart, what, fix=capital('; '.join(fixes)) + '.' if fixes else '',
               mark=box_of(apart_mask) if apart else None, kind='story', how_bad=1 + 3 * len(apart), name='apart')
    shot.apart = apart
    # how big a box the group fills (a tall board on its own would set the top, so the check file can leave it out)
    excluded = set(shot.check.get('box_excludes', []))
    in_box = [g for g in dict.fromkeys([shot.subject] + shown) if g not in excluded and shot.shows(g)]
    if not in_box:
        report.note('rule 3: story props close together', 'Not checked: no story prop shows once "box_excludes" are left out.')
        return np.any([shot.visible[g] for g in shown], axis=0)
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
            reference_words = (f' (The rule says 0.40 wide and 0.50 tall, but the reference fills {rw:.2f} by {rh:.2f}, so up to '
                               f'{limit_w:.2f} by {limit_h:.2f} is allowed.)')
    ok = w <= limit_w and h <= limit_h
    fixes = []
    sx, sy = centre_of(shot.visible[shot.subject]) if shot.shows(shot.subject) else ((l + r) / 2, (t + b) / 2)
    if w > limit_w:
        far = edge['left'] if abs(boxes[edge['left']][0] - sx) > abs(boxes[edge['right']][2] - sx) else edge['right']
        push = (w - limit_w) * shot.width + 4
        cut_right = boxes[edge['right']][2] >= shot.width - 2 or (shot.info(edge['right']).get('screen_box_unclipped') or [0, 0, 0])[2] > 0.95
        if far == edge['right'] and cut_right:
            fixes.append(f'this follows from <<rule12>>: once {far} is moved in from the right edge, the box narrows')
        else:
            fixes.append(move_words(shot, far, push if far == edge['left'] else -push, 0) or f'bring {far} in toward {shot.subject}')
    if h > limit_h:
        far = edge['top'] if abs(boxes[edge['top']][1] - sy) > abs(boxes[edge['bottom']][3] - sy) else edge['bottom']
        push = (h - limit_h) * shot.height + 4
        anchor = boxes[far][1] if far == edge['top'] else boxes[far][3]
        fixes.append(move_words(shot, far, 0, push if far == edge['top'] else -push, anchor) or f'bring {far} in toward {shot.subject}')
    unclipped = shot.info(edge['right']).get('screen_box_unclipped')
    right_text = (f'{unclipped[2]:.2f}, past the frame\'s edge' if r >= shot.width - 2 and unclipped and unclipped[2] > 1 else f'{r / shot.width:.2f}')
    report.add('rule 3: story props close together', ok,
               f'The story props{" (leaving out " + ", ".join(sorted(excluded)) + ")" if excluded else ""} fill a box {w:.2f} of the frame wide '
               f'and {h:.2f} tall (limit {limit_w:.2f} x {limit_h:.2f}). Its edges: {edge["left"]}\'s left side ({l / shot.width:.2f} across), '
               f'{edge["right"]}\'s right side ({right_text}), {edge["top"]}\'s top ({t / shot.height:.2f} down) and {edge["bottom"]}\'s '
               f'bottom ({b / shot.height:.2f}).{reference_words}',
               fix=capital('; '.join(fixes)) + '.' if fixes else '', mark=(l, t, r, b), area=True, kind='story',
               how_bad=max(past(w, limit_w, 0.04) if w > limit_w else 1, past(h, limit_h, 0.04) if h > limit_h else 1),
               rule_id='rule3_story_box', measured={'size': [w, h], 'limit_used': [limit_w, limit_h]}, things=list(boxes))
    return np.any([shot.visible[g] for g in dict.fromkeys([shot.subject] + shown) if shot.shows(g)], axis=0)


# ---------------------------------------------------------------------------------------- rule 7: the story uses the frame's height
def check_story_reaches_down(report, shot):
    """Rule 7, the frame filled top to bottom, in one measurable part: when the check file gives "story_reaches_down"
    (a fraction of the frame's height), some story prop or the subject must reach at least that far down the frame (what
    shows of it, not what is hidden). Off unless the check file asks for it, so shots checked before it are unchanged."""
    limit = shot.check.get('story_reaches_down')
    if limit is None:
        return
    shown = [g for g in shot.core if shot.shows(g)]
    if not shown:
        report.note('rule 7: the story reaches the frame\'s lower part', 'Not checked: no story prop or subject shows.')
        return
    bottoms = {g: box_of(shot.visible[g])[3] for g in shown}
    lowest = max(bottoms, key=bottoms.get)
    reach = (bottoms[lowest] + 1) / shot.height
    ok = reach >= limit
    fix = ''
    if not ok:
        words = move_words(shot, lowest, 0, limit * shot.height - bottoms[lowest], bottoms[lowest])
        fix = (capital(words) + ' so its bottom reaches ' + f'{limit:.2f} down' if words else
               f'Bring a story prop nearer the camera, or the camera nearer the story, until one reaches {limit:.2f} down')
        fix += '; or bring the camera nearer the whole group (that moves everything on screen, so check the other rules again).'
    report.add('rule 7: the story reaches the frame\'s lower part', ok,
               f'The lowest story thing that shows is {lowest}, reaching {reach:.2f} down the frame (the check file asks for at least {limit:.2f}).',
               fix=fix, mark=box_of(shot.visible[lowest]), kind='story', how_bad=past(reach, limit, 0.03), name='reach',
               rule_id='rule7_story_reaches_down', measured=reach, things=[lowest])


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
    shot.rule12_over = {g for g, _, _ in over}
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
    exact = lambda v, limit: f'{v:.3f}' if abs(v - limit) < 0.005 else f'{v:.2f}'   # "0.95 (limit 0.95)" would read as a pass
    reads = [f'{g} reaches {exact(right, limit)} across (limit {limit:.2f})' for g, right, limit in over]
    same = [f'{g} {v["box"][2]:.2f}' for g, v in shot.reference.get('boxes', {}).items() if g in limits and v['box'][2] > limits[g]]
    if same:
        reads.append(f'(the reference has the same fault: {", ".join(same)})')
    camera_fixes = []
    if slide > 0:
        held = [g for g, _, _ in over if g in tied]
        camera_fixes.append(f'For {" and ".join(held)}: move the camera about {slide:.2f} m to the right without turning it. Near props slide '
                            f'left on screen more than far ones, and where the lines meet stays where it is. Then check again: the props '
                            f'slide by different amounts, so their overlaps change (rule 4).')
        if shot.reference.get('camera_match') or shot.reference.get('lines_meet'):
            camera_fixes.append('Don\'t turn the camera instead: that would move where the lines meet away from the reference\'s.')
        else:
            camera_fixes.append(f'Or turn the camera about {turn:.1f} degrees right: everything slides left together, where the lines meet too.')
    # props past the limit on their own: when one sticks out further than the board and notice, its own move comes first
    own = [(g, right, limit) for g, right, limit in over if g not in tied and (slide == 0 or after_slide(g, right) > limit)]
    own_first = bool(own) and max(r - l for _, r, l in own) > max([r - l for g, r, l in over if g in tied] or [0])
    own_fixes = []
    for g, right, limit in own:
        reach = (right if own_first or slide == 0 else after_slide(g, right)) - limit + 0.005
        words = move_words(shot, g, -reach * shot.width, 0)
        own_fixes.append(capital(words) + ('.' if own_first or slide == 0 else ' (after the camera move).'))
    fixes = own_fixes + camera_fixes if own_first else camera_fixes + own_fixes
    fix = ' '.join(fixes)
    worst = max(over, key=lambda o: o[1] - o[2])
    marks = [box_of(shot.visible[g]) for g, _, _ in over]
    report.add('rule 12: room for phone buttons', False,
               '; '.join(reads) + '. Video apps put their buttons down the right edge, from a little above the middle to near the bottom.',
               fix=fix, mark=(min(m[0] for m in marks), min(m[1] for m in marks), shot.width - 1, max(m[3] for m in marks)), area=True,
               kind='edges', how_bad=past(worst[1], worst[2], 0.02), name='rule12', rule_id='rule12_right_edges',
               measured=max(right for _, right, _ in over), things=[g for g, _, _ in over])


def check_titles(report, shot, blurred):
    zone = shot.check.get('title_zone')
    if not zone:
        report.note('rule 12: titles in dim sky', 'Not checked: the check file has no "title_zone".')
        return
    if not (0 <= zone[0] < zone[2] <= 1 and 0 <= zone[1] < zone[3] <= 1) or (zone[2] - zone[0]) * (zone[3] - zone[1]) < 0.001:
        report.add('set-up', False, f'The check file\'s "title_zone" {zone} is not an area given in fractions of the frame (0 to 1).',
                   fix='Give it as [left, top, right, bottom], each between 0 and 1, for example [0.05, 0.02, 0.62, 0.12].', kind='set-up', how_bad=3)
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
               '; '.join(numbers), fix='Move the title area into darker, emptier sky, or move what is in it.', mark=(l, t, r, b), area=True, kind='edges',
               rule_id='rule12_title_zone_sky_share', measured={'sky': sky, 'others': [p for p in problems if not p.startswith('only ')]})


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
        cy = centre_of(shot.visible[g])[1]
        target = min(max(cy / shot.height, 0.47), 0.60)   # just inside the middle band: the smallest move that does
        words = move_words(shot, g, 0, (target - cy / shot.height) * shot.height, cy) if abs(target - cy / shot.height) > 0.01 else None
        fix = (capital(words) + f' (its middle then sits about {target:.2f} down)' + (', and keep it in shadow.' if average is not None else '.')) if words \
            else f'Keep {g} where it is but in shadow.'
        report.add('rule 8: work props small, far and dim', not problems, (what + '. ' + capital('; '.join(problems)) + '.') if problems else what + '.',
                   fix=fix, mark=box_of(shot.visible[g]), kind='background', how_bad=1 + len(problems), rule_id='rule8_work_prop_share',
                   measured=share, things=[g])
    corner = np.zeros((shot.height, shot.width), bool)
    corner[shot.height // 2:, :shot.width // 2] = True
    big = []
    for g, mask in shot.visible.items():
        share = (mask & corner).sum() / total
        if share > 0.01:
            big.append(g)
            fix = f'Move {g} out of the bottom-left quarter.'
            if g in shot.check.get('work', []):   # a work prop belongs further up the street, in the middle band
                cy = centre_of(mask)[1]
                words = move_words(shot, g, 0, (0.60 * shot.height - cy), cy)
                fix = capital(words) + ' (its middle then about 0.60 down, out of the corner and just inside the middle band, rule 8).' if words else fix
            report.add('rule 8: nothing big where the eye enters', False, f'{g} fills {share:.1%} of the frame in the bottom-left quarter, where the eye enters (limit 1%).',
                       fix=fix, mark=box_of(mask & corner), kind='story', how_bad=past(share, 0.01, 0.01), rule_id='rule8_bottom_left_share',
                       measured=share, things=[g])
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
    what = (f'The biggest dark shape where the eye enters (the bottom-left quarter) covers {share:.{2 if abs(share - 0.01) < 0.001 else 1}%} of the frame (limit 1%): brightness '
            f'{float(shot.grey[piece].mean()):.2f} against {lit:.2f} for the lit ground around it.')
    if owner:
        what += f' Most of it is {owner}.'
        fix = f'Move {owner} out of the bottom-left quarter, or light it.'
    else:
        what += ' It is not a prop: probably a shadow cast across the ground.'
        fix = ('First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): '
               'a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each '
               'light\'s shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.')
    report.add('rule 8: nothing big and dark where the eye enters', ok, what, f'from {l / shot.width:.2f} to {r / shot.width:.2f} across, '
               f'{t / shot.height:.2f} to {b / shot.height:.2f} down', fix=fix, mark=(l, t, r, b), area=True, kind='light', how_bad=past(share, 0.01, 0.01),
               rule_id='rule8_dark_entry', measured=share, things=[owner] if owner else [])


# ---------------------------------------------------------------------------------------- the light rules (5, 6, 10) and the main rule
def light_reaching(light, point, group=None):
    """How strongly a light reaches a point in the street (its strength over distance squared), or 0 when the
    point is outside a spotlight's beam, past the light's set reach, or on something the light was set not to
    reach (light linking; group None is the street itself). Anything shading it is ignored."""
    if light['kind'] == 'SUN':
        return 0.0
    if 'reaches_only' in light and group not in light['reaches_only']:
        return 0.0
    if group is not None and group in light.get('skips', []):
        return 0.0
    offset = np.array(point, float) - np.array(light['at'], float)
    distance = float(np.linalg.norm(offset))
    if light.get('reach') is not None and distance > light['reach']:
        return 0.0
    if light['kind'] == 'SPOT' and light.get('aim') is not None and distance > 1e-6:
        angle = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(offset / distance, light['aim']))))))
        if angle > light['spot_degrees'] / 2:
            return 0.0
    return light['energy'] / max(distance, 0.3) ** 2


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
        strength = light_reaching(light, spot)
        if strength > 0:
            found.append((strength, light['name'], distance, where))
    total = sum(f[0] for f in found) or 1
    return [f'{name} ({distance:.1f} m from it, {where}; about {strength / total:.0%} of the warm light reaching it if nothing shades it)'
            for strength, name, distance, where in sorted(found, reverse=True)[:2]]


def lit_from_below_fix(shot, subject, spread_too_wide):
    """Words for warming the subject's bottom more than its top, naming the lights by their Blender names."""
    info = shot.info(subject)
    middle = info['centre'][2]
    near = lambda l, metres: l['kind'] == 'SUN' or float(np.linalg.norm(np.array(l['at']) - np.array(info['centre']))) <= metres
    can_reach = lambda l: ('reaches_only' not in l or subject in l['reaches_only']) and subject not in l.get('skips', [])   # light linking
    lights = [l for l in shot.facts.get('lights', []) if can_reach(l)]
    warm_below = [l['name'] for l in lights if l['colour'][0] - l['colour'][2] >= 0.15 and l['kind'] != 'SUN' and l['at'][2] < middle and near(l, 3)]
    eye = np.array(shot.camera['at'])
    facing = lambda l: l['kind'] == 'SUN' or np.dot(np.array(l['at']) - np.array(info['centre']), eye - np.array(info['centre'])) > 0
    cool_above = [l['name'] for l in lights if facing(l) and ((l['colour'][2] > l['colour'][0] and near(l, 8)) or (l['kind'] != 'SUN' and l['at'][2] > middle and near(l, 4)))]
    words = f'Give {subject}\'s bottom more warm light than its top: '
    below = (f'bring the warm light below it closer under its bottom edge, or aim it there ({", ".join(warm_below)})' if warm_below
             else 'add a warm light below it, aimed at its bottom edge')
    above = f'dim or whiten the light from above ({", ".join(cool_above)})' if cool_above else ''
    if spread_too_wide and above:   # warm light already spreads too far: cool the top rather than add warmth
        words += above + f'; or {below}'
    else:
        words += below + (f'; or {above}' if above else '')
    return words + '. Then check again.'


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
               mark=box_of(biggest) if owner != subject else box_of(on_subject), area=True, kind='light', how_bad=max(past(share_subject, 0.40, 0.1) if share_subject < 0.40 else 1, past(share_group, 0.75, 0.1) if share_group < 0.75 else 1),
               rule_id='rule5_brightest_share_on_subject', measured={'on_subject': share_subject, 'in_story_box': share_group}, things=[subject])
    if has_subject:
        ratio = float(grey[shot.visible[subject]].mean() / grey.mean())
        report.add(f'rule 5: {subject} is bright', ratio >= 1.8, f'{subject} is {ratio:.2f} times as bright as the frame\'s average (need 1.8).',
                   fix=f'Light {subject} more, or darken what is around it.', mark=box_of(shot.visible[subject]), kind='light', how_bad=past(ratio, 1.8, 0.3),
                   rule_id='rule5_subject_brightness_ratio', measured=ratio, things=[subject])
    top_row = [float(grey[:height // 3, a:b].mean()) for a, b in ((0, width // 3), (width // 3, 2 * width // 3), (2 * width // 3, width))]
    report.add('rule 5: keep the sky dim', max(top_row) <= 0.36,
               f'The top third\'s brightness, left to right: {", ".join(f"{v:.2f}" for v in top_row)} (limit 0.36).',
               fix='Darken the sky (or ask the painter for a darker sky).', mark=(0, 0, width - 1, height // 3), area=True, kind='light', how_bad=past(max(top_row), 0.36, 0.05),
               rule_id='rule5_top_third_brightness', measured=max(top_row))
    # rule 6: warm light, mostly round the story props
    blue, _, red = [c.astype(np.float32) for c in cv2.split(picture)]
    warmth = np.clip((red - blue) / 255, 0, 1)
    warm = warmth * grey > 0.18
    share_warm = float(warm.mean())
    near_story = cv2.dilate(story_box.astype(np.uint8), np.ones((int(0.06 * width) | 1,) * 2, np.uint8)) > 0
    inside = (warm & near_story).sum() / max(1, warm.sum())
    problems, fixes, mark = [], [], None
    if share_warm > 0.03:
        problems.append(f'warm light covers {share_warm:.{2 if share_warm < 0.031 else 1}%} of the frame, {share_warm / 0.03:.{2 if share_warm < 0.031 else 1}f} times the most allowed (3%)')
    if share_warm < 0.015:
        problems.append(f'warm light covers only {share_warm:.1%} of the frame (aim for 1.5 to 3%)')
        fixes.append('Let the fire and the lantern light more.')
    elif share_warm > 0.03 and inside >= 0.5:
        fixes.append('Most of it is round the story props: shorten how far the fire\'s and the lantern\'s light reaches, or lower the '
                     'lantern\'s strength a little (the fire\'s light also lights the notice from below).')
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
            surface = max(on, key=on.get) if on and max(on.values()) > 0.3 * patch.sum() else \
                ('the road or pavement' if ground_point(shot, px, py) is not None else 'the house walls')
            lights = warm_lights_near(shot, px, py)
            mark = box_of(patch)
            fixes.append(f'{1 - inside:.0%} of the warm light is away from the story props; the largest patch is on {surface} at {px / width:.2f} across, '
                         f'{py / height:.2f} down (marked). The warm lights lighting it most: {"; ".join(lights) if lights else "none found"}. '
                         f'Shorten how far their light reaches (Blender\'s "custom distance" for a light) rather than their strength, so the '
                         f'notice keeps its warm light from below.')
    report.add('rule 6: warm light from the people\'s own lights', not problems,
               (capital('; '.join(problems)) + '.') if problems else f'Warm light covers {share_warm:.1%} of the frame, {inside:.0%} of it round the story props.',
               f'warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py)', fix=' '.join(fixes),
               mark=mark, area=True, kind='light', how_bad=max(past(share_warm, 0.03, 0.01) if share_warm > 0.03 else 1, past(share_warm, 0.015, 0.005) if share_warm < 0.015 else 1,
                                                                past(inside, 0.5, 0.1) if inside < 0.5 else 1),
               rule_id='rule6_warm_share', measured={'share': share_warm, 'round_story': inside})
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
                   f'The bottom of {subject} is {plain(lift, 3 if abs(lift - 0.10) < 0.005 else 2)} warmer than its top, on a scale where 0 is the same colour and 1 is pure red against '
                   f'pure blue; it needs 0.10 (the reference measures about 0.17).',
                   fix=lit_from_below_fix(shot, subject, share_warm > 0.03), name='lit-below',
                   mark=box_of(shot.visible[subject]), kind='light', how_bad=past(lift, 0.10, 0.05), rule_id='rule6_lit_from_below', measured=lift,
                   things=[subject])
    # rule 5: no story prop as bright as the subject ("dirty the chair a little so it stays darker than the notice")
    if has_subject:
        paper = float(np.median(grey[shot.visible[subject]]))
        glaring = []
        for g in shot.story:
            if g in (subject, shot.support) or not shot.shows(g) or shot.visible[g].sum() < 400:
                continue
            top5 = float(np.percentile(grey[shot.visible[g]], 95))
            if g in shot.check.get('lights_in_story', []):
                # a prop that is itself a light (a lit lantern): its flame may outshine the notice, but not its glass and
                # body; a small flame lit 6% of the lantern this bright, its whole glass glowing 18 to 22% (log 32)
                share = float((grey[shot.visible[g]] >= paper - 0.05).mean())
                if share > 0.10:
                    glaring.append((g, top5, share))
            elif top5 >= paper - 0.05:
                glaring.append((g, top5, None))
        lights_on = lambda g: [x for x in sorted(((light_reaching(l, shot.info(g)['centre'], g), l['name']) for l in shot.facts.get('lights', [])),
                                                 reverse=True)[:1] if x[0] > 0]
        lit = [g for g in shot.story if g in shot.check.get('lights_in_story', []) and shot.shows(g)]
        report.add(f'rule 5: nothing in the story group as bright as {subject}', not glaring,
                   ('; '.join(f'the brightest parts of {g} reach {v:.2f}, as bright as {subject} ({paper:.2f})'
                              + (f': {share:.0%} of it, where a lamp\'s flame alone is about 6%' if share is not None else '')
                              for g, v, share in glaring) + '.') if glaring
                   else f'Every story prop stays darker than {subject} ({paper:.2f})'
                        + (f', apart from the small flame of {", ".join(lit)}' if lit else '') + '.',
                   fix=' '.join((f'Dim {g}\'s glass or glow, so only its flame is as bright as {subject}' if share is not None else
                                 f'Make {g} darker (its own colour) or move it further from the light on it'
                                 + (f' ({lights_on(g)[0][1]})' if lights_on(g) else '')) + '.' for g, _, share in glaring),
                   mark=box_of(np.any([shot.visible[g] for g, _, _ in glaring], axis=0)) if glaring else None, kind='light',
                   how_bad=max([past(v, paper - 0.05, 0.05) for _, v, _ in glaring] or [1]), rule_id='rule5_nothing_in_story_as_bright',
                   things=[g for g, _, _ in glaring])
    # burnt-out colour: pure white or one colour at its limit loses all detail, and the painter can't recover it
    clipped = picture.max(axis=2) >= 254
    burnt = []
    for g, mask in shot.visible.items():
        n = int((clipped & mask).sum())
        if n > 0.0002 * width * height and n > 0.03 * mask.sum():
            burnt.append((g, n / mask.sum(), box_of(clipped & mask)))
    rest = clipped & ~np.any(list(shot.visible.values()), axis=0)
    if rest.sum() > 0.001 * width * height:
        burnt.append(('the set (walls, road or sky)', rest.sum() / (width * height), box_of(rest)))
    report.add('rule 5: no burnt-out colour', not burnt,
               ('Colour at its limit (pure white, or one colour at full strength), where all detail is lost: ' +
                '; '.join(f'{g} ({share:.0%} of it)' if not g.startswith('the set') else f'{g} ({share:.2%} of the frame)' for g, share, _ in burnt) + '.')
               if burnt else 'Nothing apart from tiny highlights is at its colour limit.',
               fix='Dim the light on it, or darken its own colour or glow, until nothing but a lamp\'s flame reaches the limit.',
               mark=burnt[0][2] if burnt else None, kind='light', how_bad=1 + 2 * len(burnt))
    # a warm patch away from the story props, however dim: is it lit by something meant?
    hue = (red - blue) / np.maximum(red + blue, 1)
    stray = (hue > 0.25) & (grey > 0.25) & ~np.any([shot.visible[g] for g in shot.visible], axis=0)
    stray = cv2.morphologyEx(stray.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    m, parts, part_stats, _ = cv2.connectedComponentsWithStats(stray)
    patches = sorted(((part_stats[k, cv2.CC_STAT_AREA], k) for k in range(1, m)), reverse=True)[:3]
    patches = [(area, k) for area, k in patches if area > 0.002 * width * height]
    if patches:
        words = []
        for area, k in patches:
            px, py = centre_of(parts == k)
            lit_by = warm_lights_near(shot, px, py)
            words.append(f'at {px / width:.2f} across, {py / height:.2f} down ({area / (width * height):.1%} of the frame' +
                         (f'; lit most by {lit_by[0].split(" (")[0]}' if lit_by else '') + ')')
        report.note('rule 6: warm light from the people\'s own lights',
                    'Warm patches on the set (walls, road): ' + '; '.join(words) + '. Check each is lit by something you meant (a window, a lamp, '
                    'the fire\'s glow on the road), not by a light meant for the notice that shines through or past it.')
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
               how_bad=0.8 * past(quiet, 0.40 if quiet < 0.40 else 0.48, 0.04),   # the weakest rule: it doesn't make a shot work on its own
               rule_id='rule10_quiet_side_weight', measured=quiet)
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
                   mark=(x - 25, y - 25, x + 25, y + 25) if brightest_there >= notice_bright else None, kind='light', how_bad=2,
                   rule_id='rule10_nothing_on_quiet_side_outshines', things=big)
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
               kind='main', how_bad=max(past(r - l, 0.40, 0.05) if r - l > 0.40 else 1, past(b - t, 0.50, 0.05) if b - t > 0.50 else 1),
               rule_id='main_rule_spot_box', measured=[r - l, b - t])
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
        first_move = next((i['name'] for i in report.items if i['passed'] is False and i.get('name') in (f'resting:{g}', f'depth:{g}', f'missing:{g}')), None)
        if first_move:
            report.note('reference: where each prop stands', f'{g}: compare with the reference again after <<{first_move}>>.')
            continue
        if g in shot.rule12_over:
            report.note('reference: where each prop stands', f'{g}: compare with the reference again after <<rule12>> (it is past the phone-button limit).')
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
        size = (ours[3] - ours[1]) / max(1e-6, want[3] - want[1])   # how tall, against the reference
        cut = max(ours[2], want[2]) > 0.995 or min(ours[0], want[0]) < 0.005   # a box cut by the frame edge has no true width
        wide = None if cut else (ours[2] - ours[0]) / max(1e-6, want[2] - want[0])
        size_ok = top or 0.8 <= size <= 1.25
        fixes = []
        across_off = abs(ox - wx) > 0.04
        limit = 0.90 if g in shot.check.get('must_read', []) else 0.95 if g in shot.story else None
        new_right = (r / shot.width) + (wx - ox)
        carrier = shot.carrier(g)
        if carrier and shot.alone[carrier].any() and carrier in shot.story:   # the prop it rides on moves too
            carrier_right = box_of(shot.alone[carrier])[2] / shot.width + (wx - ox)
            if carrier_right - 0.95 > new_right - (limit or 1):
                new_right, limit = carrier_right, 0.95
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
            if wide is not None and 0.9 <= wide <= 1.1:   # as wide as the reference's: only its shape differs
                fixes.append(f'it is as wide as the reference\'s ({ours[2] - ours[0]:.2f} against {want[2] - want[0]:.2f} of the frame) but '
                             f'{size:.2f} times as tall: make it about {1 / size:.2f} times {"taller" if size < 1 else "shorter"} without making it wider')
            else:
                mover = shot.carrier(g) or g
                change = info['distance'] * (1 - size)   # + is nearer
                words = f'make it {1 / size:.2f} times {"bigger" if size < 1 else "smaller"}'
                taken = spot_taken(shot, mover, -change)
                crowded = change > 0 and any(i['rule'].startswith('rule 12: room') and i['passed'] is False for i in report.items)
                if taken:
                    words += f' (moving {mover} {abs(change):.2f} m {"nearer" if change > 0 else "further"} instead would put it where {taken} stands)'
                elif crowded:
                    words += f' (don\'t move {mover} nearer instead: that would push it further into the phone buttons, rule 12)'
                else:
                    words += (f', or move {f"{mover} (with {g} on it)" if mover != g else "it"} about {abs(change):.2f} m '
                              f'{"nearer to" if change > 0 else "further from"} the camera (which also moves it on screen)')
                fixes.append(words)
        ok = not across_off and abs(oy - wy) <= 0.04 and size_ok
        report.add('reference: where each prop stands', ok,
                   f'{g}: ours at {ox:.2f} across, {oy:.2f} down; the reference\'s at {wx:.2f}, {wy:.2f}' +
                   ('' if top else f'; ours is ' + (f'{wide:.2f} times as wide and ' if wide is not None else '') + f'{size:.2f} times as tall as the reference\'s') + '.',
                   fix=(capital('; '.join(fixes)) + '.') if fixes else '', mark=(l, t, r, b), area=True, kind='reference',
                   how_bad=max(abs(ox - wx) if across_off else 0, abs(oy - wy)) / 0.04 + (0 if size_ok else abs(math.log(size)) * 4),
                   arrow=((ox * shot.width, oy * shot.height), (wx * shot.width, wy * shot.height)))
    if landmarks:
        report.note('reference: landmarks', 'These are buildings, not props: they are never moved; they only show whether the camera matches. '
                    + '; '.join(landmarks) + '.')


# ---------------------------------------------------------------------------------------- kinds of shot and the accepted list
CALCULATORS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'calculators')


def calculators():
    """kit/calculators/settings.py (read only when a check file names kinds of shot or accepted problems)."""
    import sys
    if CALCULATORS not in sys.path:
        sys.path.insert(0, CALCULATORS)
    try:
        import settings as kit_settings
    except ImportError:
        raise SystemExit(f'check_shot: the check file names "kind_of_shot" or "accepted", which need kit/calculators/settings.py and '
                         f'kit/film-settings.json; not found at {CALCULATORS}.')
    return kit_settings


def known_item(item, how, words, entry=None):
    item['passed'] = 'known'
    item['known'] = {'how': how, 'words': words, 'entry': entry}


def rejudge(item, rule_id, rules, shot, kit):
    """How a problem (or a pass) stands under the view's kinds of shot: ('pass' | 'fail' | 'off', words) or None (unchanged)."""
    entry = rules[rule_id]
    kinds = ' + '.join(entry.get('from_kinds', []))
    measured = item.get('measured')
    if not entry.get('applies', True):
        if rule_id == 'rule12_title_zone_sky_share' and isinstance(measured, dict) and measured.get('others'):
            return None   # only the sky share is replaced; story props in the band or a bright band still count
        instead = f'; instead: {entry["replaced_by"]}' if entry.get('replaced_by') else ''
        return 'off', f'off for a {kinds} shot ({entry.get("source", "")}){instead}'
    limit = entry.get('value')
    if rule_id == 'rule1_meeting_point_gap' and isinstance(measured, dict):
        left, right = measured['span']
        if 'opening' in entry.get('measure', '') and left <= measured['meet_across'] <= right:
            return 'pass', f'where the lines meet lies inside the outline across, which a {kinds} shot allows ({entry.get("measure")})'
        if 'across only' in entry.get('unit', ''):
            across = 0.0 if left <= measured['meet_across'] <= right else min(abs(measured['meet_across'] - left), abs(measured['meet_across'] - right))
            return ('pass' if across <= limit else 'fail'), f'judged across only for a {kinds} shot: {across:.3f} of the width (limit {limit})'
        return None
    if rule_id == 'rule2_eye_height':
        if 'eye_height' in shot.check:
            return None   # the check file's own range is the view's
        return kit.judge(entry, measured), f'the eye range for a {kinds} shot is {limit[0]} to {limit[1]} m'
    if rule_id == 'rule3_story_box' and isinstance(measured, dict):
        used = measured['limit_used']
        box = [max(limit[0], used[0]), max(limit[1], used[1])]
        w, h = measured['size']
        return ('pass' if w <= box[0] and h <= box[1] else 'fail'), f'a {kinds} shot\'s story box may be {box[0]:.2f} x {box[1]:.2f}'
    if rule_id == 'rule5_brightest_share_on_subject' and isinstance(measured, dict):
        other = rules.get('rule5_brightest_share_in_story_box', {})
        on_ok = kit.judge(entry, measured['on_subject']) in ('pass', 'off')
        box_ok = kit.judge(other, measured['in_story_box']) in ('pass', 'off') if other else True
        return ('pass' if on_ok and box_ok else 'fail'), f'the {kinds} limits: {entry.get("value")} on the subject, {other.get("value")} in the story box'
    if rule_id == 'rule6_warm_share' and isinstance(measured, dict):
        return ('pass' if kit.judge(entry, measured['share']) == 'pass' and measured['round_story'] >= 0.5 else 'fail'), \
            f'a {kinds} shot\'s warm share is {limit[0]:.1%} to {limit[1]:.1%}'
    if rule_id == 'rule7_story_reaches_down':
        verdict = kit.judge(entry, measured)
        if verdict == 'fail' and 'fill' in entry.get('who_may_reach', ''):
            fills = {g: (box_of(shot.visible[g])[3] + 1) / shot.height for g in shot.check.get('fill', []) if shot.shows(g)}
            reached = {g: v for g, v in fills.items() if v >= limit}
            if reached:
                g = max(reached, key=reached.get)
                return 'pass', f'the fill prop {g} reaches {reached[g]:.2f} down, which a {kinds} shot allows ({entry.get("who_may_reach")})'
        return verdict, f'a {kinds} shot asks for {limit} down'
    if rule_id == 'rule8_bottom_left_share':
        things = item.get('things') or []
        if 'story' in entry.get('applies_to', '') and not (set(things) & set(shot.core)):
            return None   # the crowd's allowance is for story things only
        return kit.judge(entry, measured), f'a story thing in a {kinds} shot may cover {limit:.0%}'
    if rule_id == 'resting_on' and isinstance(measured, dict):
        surfaces = shot.check.get('support_surfaces') or []
        for surface in surfaces:
            air = measured['bottom'] - surface['height']
            if -0.05 <= air <= limit:
                return 'pass', f'it rests on the {surface["name"]} (declared at {surface["height"]:.3f} m; {air:+.3f} m), which an {kinds} shot allows'
        return None
    if isinstance(measured, (int, float)) and entry.get('limit_type') in ('max', 'min', 'range'):
        return kit.judge(entry, measured), f'the {kinds} limit is {limit}'
    return None


def crowd_heads(report, shot, kit, settings):
    """A crowd's replacement for rule 4 between figures: head centres at least a head width apart on screen, and every
    figure at least half seen (people.crowd_head_spacing_head_widths, people.crowd_figure_visible_share_min)."""
    figures = [g for g in shot.check.get('figures', []) if shot.shows(g) and shot.alone[g].any()]
    if len(figures) < 2:
        report.note('crowd: heads apart', 'Not checked: list the people\'s groups under "figures" in the check file (a crowd\'s rule 4 between '
                    'figures is replaced by this test).')
        return
    need = settings.value('people.crowd_head_spacing_head_widths')
    seen_min = settings.value('people.crowd_figure_visible_share_min')
    head_share = settings.value('people.head_height_metres') / settings.value('people.figure_height_metres')
    heads = {}
    for g in figures:
        ys, xs = np.nonzero(shot.alone[g])
        top, height = ys.min(), ys.max() - ys.min() + 1
        rows = ys < top + max(2, head_share * height)
        heads[g] = (float(xs[rows].mean()), float(ys[rows].mean()), float(xs[rows].max() - xs[rows].min() + 1))
    worst = None
    for i, a in enumerate(figures):
        for b in figures[i + 1:]:
            apart = math.hypot(heads[a][0] - heads[b][0], heads[a][1] - heads[b][1]) / min(heads[a][2], heads[b][2])
            if worst is None or apart < worst[0]:
                worst = (apart, a, b)
    apart, a, b = worst
    report.add('crowd: heads apart', apart >= need,
               f'The closest two heads, {a}\'s and {b}\'s, are {apart:.2f} head widths apart on screen (at least {need}, so every head can be '
               f'counted; this replaces rule 4 between figures in a crowd).',
               fix=f'Move {a} or {b} sideways (or change one\'s height) until their heads are a head width apart.',
               mark=box_of(shot.alone[a] | shot.alone[b]), kind='story', how_bad=past(apart, need, 0.25), rule_id='crowd_head_spacing',
               measured=apart, things=[a, b])
    shares = {g: float(shot.visible[g].sum()) / float(shot.alone[g].sum()) for g in figures}
    hidden = {g: v for g, v in shares.items() if v < seen_min}
    report.add('crowd: every figure half seen', not hidden,
               (f'{", ".join(f"{g} shows {v:.0%}" for g, v in sorted(hidden.items(), key=lambda x: x[1]))} of itself (at least {seen_min:.0%}).'
                if hidden else f'Every figure shows at least {seen_min:.0%} of itself (the least: {min(shares, key=shares.get)}, '
                               f'{min(shares.values()):.0%}).'),
               fix='Move the hidden figures sideways into the gaps between the ones in front.',
               mark=box_of(np.any([shot.alone[g] for g in hidden], axis=0)) if hidden else None, kind='story',
               how_bad=1 + 2 * len(hidden), rule_id='crowd_figure_visible_share', measured=min(shares.values()), things=list(hidden))


def silhouette_contrast(report, shot, entry, settings):
    """A dark subject's replacement for "the subject is the brightest": its outline must stand out against the light round it,
    (surround + 0.05) / (subject + 0.05) in linear light over a band round its outline (the people test's figure measure)."""
    subject = shot.subject
    if shot.picture is None or not shot.shows(subject):
        report.note('dark subject: its outline against the light', 'Not checked: needs the finished picture and the subject showing.')
        return
    linear = shot.picture.astype(np.float32) / 255
    linear = np.where(linear <= 0.04045, linear / 12.92, ((linear + 0.055) / 1.055) ** 2.4)
    luminance = 0.0722 * linear[:, :, 0] + 0.7152 * linear[:, :, 1] + 0.2126 * linear[:, :, 2]
    size = max(3, int(settings.value('shot_planner.check_shot_silhouette_band_share_of_width') * shot.width) | 1)
    grown = cv2.dilate(shot.alone[subject].astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))) > 0
    others = np.any([v for g, v in shot.visible.items() if g != subject] or [np.zeros_like(grown)], axis=0)
    band = grown & ~shot.alone[subject] & ~others
    if band.sum() < 100:
        report.note('dark subject: its outline against the light', f'Not checked: too little of the light round {subject} shows.')
        return
    inside, around = float(luminance[shot.visible[subject]].mean()), float(luminance[band].mean())
    ratio = (around + 0.05) / (inside + 0.05)
    report.add('dark subject: its outline against the light', ratio >= entry['value'],
               f'{subject} (a dark subject) against the light round its outline: (surround + 0.05) / (subject + 0.05) = {ratio:.2f} '
               f'(at least {entry["value"]}; it replaces "the subject is the brightest" for a dark subject; {entry.get("note", "")}).',
               fix=f'Light what is behind or round {subject} more (a lit yard, a doorway, a lamp beyond it), not {subject} itself.',
               mark=box_of(band), area=True, kind='light', how_bad=past(ratio, entry['value'], 0.3), rule_id='silhouette_contrast', measured=ratio,
               things=[subject])


def matches(entry, item):
    rule = str(entry.get('rule', '')).strip().lower()
    if not rule or not (rule == str(item.get('rule_id') or '').lower() or item['rule'].lower().startswith(rule)):
        return False
    things = entry.get('things') or []
    named = set(item.get('things') or []) | set(item.get('pair') or ())
    return all(t in named or t in item['what'] for t in things)


def worse_than_accepted(entry, item, share, rules):
    """True when a problem has moved more than `share` (of the accepted number) further past its limit than when it was accepted."""
    accepted, measured = entry.get('measured'), item.get('measured')
    if not isinstance(accepted, (int, float)) or not isinstance(measured, (int, float)):
        return False
    rule = rules.get(item.get('rule_id') or '', {})
    step = share * abs(accepted)
    if rule.get('limit_type') == 'min':
        return measured < accepted - step
    if rule.get('limit_type') == 'range' and isinstance(rule.get('value'), list):
        low, high = rule['value']
        past = lambda v: max(low - v, v - high, 0.0)
        return past(measured) > past(accepted) + step
    return measured > accepted + step


# the rules this tool measures (a check file's accepted entry for any other rule, the slide for example, is for other tools)
CHECKED_RULES = {'rule1_meeting_point_gap', 'rule2_eye_height', 'resting_on', 'rule3_story_box', 'rule3_story_together_metres', 'rule4_near_touch',
                 'rule4_between_figures', 'rule5_brightest_share_on_subject', 'rule5_brightest_share_in_story_box', 'rule5_subject_brightness_ratio',
                 'rule5_top_third_brightness', 'rule5_nothing_in_story_as_bright', 'rule6_warm_share', 'rule6_lit_from_below',
                 'rule7_story_reaches_down', 'rule8_work_prop_share', 'rule8_bottom_left_share', 'rule8_dark_entry', 'rule10_quiet_side_weight',
                 'rule10_nothing_on_quiet_side_outshines', 'rule12_right_edges', 'rule12_title_zone_sky_share', 'main_rule_spot_box',
                 'crowd_head_spacing', 'crowd_figure_visible_share', 'silhouette_contrast'}


def apply_kinds_and_accepted(report, shot, settings_path=None):
    """The view's kinds of shot and its accepted problems (check file "kind_of_shot" and "accepted"). Does nothing, and changes
    nothing in the report, when the check file has neither."""
    kinds, accepted = shot.check.get('kind_of_shot'), shot.check.get('accepted')
    if kinds is None and accepted is None:
        return None
    kit = calculators()
    settings = kit.load_settings(settings_path)
    kinds = list(kinds or ['still_life'])
    rules = kit.resolve_profile(settings, kinds)
    changed = {r for r, e in rules.items() if e.get('from_kinds') != ['still_life']}
    figures = set(shot.check.get('figures', []))
    for item in list(report.items):
        rule_id = item.get('rule_id')
        if not rule_id or item['passed'] is None:
            continue
        if rule_id == 'rule4_near_touch' and item.get('pair') and set(item['pair']) <= figures:
            rule_id = 'rule4_between_figures'
        if rule_id not in changed and not (rule_id == 'rule5_brightest_share_on_subject' and 'rule5_brightest_share_in_story_box' in changed):
            continue
        found = rejudge(item, rule_id, rules, shot, kit)
        if found is None:
            continue
        verdict, words = found
        if item['passed'] is False and verdict in ('pass', 'off'):
            known_item(item, 'allowed', words, {'rule': rule_id, 'kinds': rules[rule_id].get('from_kinds'), 'value': rules[rule_id].get('value'),
                                                'source': rules[rule_id].get('source')})
        elif item['passed'] is True and verdict == 'fail':
            item['passed'] = False
            item['fix'] = f'This kind of shot is stricter: {words}.'
            item['what'] += f' ({words}.)'
    if not rules.get('rule4_between_figures', {}).get('applies', True):
        crowd_heads(report, shot, kit, settings)
    contrast = rules.get('silhouette_contrast')
    if contrast and contrast.get('applies', True) and 'dark_subject' in kinds:
        if getattr(shot, 'light_judged', False):
            silhouette_contrast(report, shot, contrast, settings)
        else:
            report.note('dark subject: its outline against the light', 'Not checked: the light rules were not judged (no finished picture, '
                        'or one made before the scene changed).')
    if not rules.get('rule12_title_zone_sky_share', {}).get('applies', True):
        report.note('rule 12: titles in dim sky', f'For a {" + ".join(kinds)} shot the title band need not be sky: '
                    f'{rules["rule12_title_zone_sky_share"].get("replaced_by")}. Check that the page draws it.')
    share = settings.value('shot_planner.check_shot_accepted_worse_share')
    unmatched = []
    for entry in accepted or []:
        hits = [i for i in report.items if i['passed'] is False and matches(entry, i)]
        if not hits:
            unmatched.append(entry)
            continue
        for item in hits:
            if worse_than_accepted(entry, item, share, rules):
                item['what'] += (f' (The check file accepts this at {entry["measured"]}, {entry.get("who")}, {entry.get("date")}: it is now '
                                 f'worse than that, so it counts again.)')
                continue
            known_item(item, 'accepted', f'{entry.get("reason")} ({entry.get("who")}, {entry.get("date")})', entry)
    for entry in unmatched:
        rule = str(entry.get('rule', ''))
        measured_here = rule in CHECKED_RULES or rule.lower().startswith(('rule ', 'main rule', 'set-up', 'reference', 'props rest', 'crowd', 'dark subject'))
        report.note('accepted', f'The check file accepts "{rule}"' + (f' for {", ".join(entry["things"])}' if entry.get('things') else '')
                    + f' ({entry.get("reason")}), ' + ('but no such problem was found: it may have been fixed; take the entry out.' if measured_here else
                                                         'which this tool does not measure (it is for other tools: plan_shot.py, the slide '
                                                         'and painting checks); kept as it is.'))
    return {'kinds': kinds, 'settings_file': settings.path, 'settings_used': settings.used_json()}


# ---------------------------------------------------------------------------------------- drawing and writing
LEGEND = ('On marked.jpg each problem\'s place is boxed, with its number on a dark tag (red: a small place; orange: a large area). '
          'Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles '
          '(main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, '
          'the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.')

WORDS = ('Words used: "where the lines meet" is the spot where the street\'s straight edges (kerbs, gutters, roof lines) run together '
         'in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are '
         'the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, '
         'brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop '
         'in one plain colour, as measured in Blender.')

NOT_CHECKED = [
    'rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame '
    'the story reaches is measured, and only when the check file gives "story_reaches_down".',
    'rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.',
    'rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.',
    'whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.',
]

# words in Blender's log that mean the finished picture's light can't be trusted, and what each does
RENDER_FAULTS = {'Shadow buffer full': 'it ran out of shadow memory, which draws false hard shadows',
                 'Could not allocate shadow atlas': 'it could not set up its shadow memory at all, so shadows are missing'}

SPOT_COLOURS = {'where the lines meet': (200, 60, 200), 'centre of the brightest parts': (255, 255, 255),
                'centre of the warm light': (180, 105, 255), 'centre of the story props': (255, 140, 30)}


def label(image, text, x, y, colour, taken):
    """The problem's number on a small dark tag at (x, y), moved down until it covers no other tag, kept in the frame."""
    height, width = image.shape[:2]
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
    w, h = w + 12, h + 14
    x, y = int(min(max(x, 2), width - w - 2)), int(min(max(y, 2), height - h - 2))
    while any(x < tx + tw and tx < x + w and y < ty + th and ty < y + h for tx, ty, tw, th in taken):
        y += h + 2
        if y > height - h - 2:
            y, x = 2, min(x + w + 2, width - w - 2)
    taken.append((x, y, w, h))
    cv2.rectangle(image, (x, y), (x + w, y + h), (20, 20, 20), -1)
    cv2.rectangle(image, (x, y), (x + w, y + h), colour, 2)
    cv2.putText(image, text, (x + 6, y + h - 8), cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 2, cv2.LINE_AA)


def draw_marked(path, shot, ranked, spots):
    image = (shot.picture if shot.picture is not None else shot.ids_picture).copy()
    width, height = shot.width, shot.height
    for x in (0.90, 0.95):   # rule 12's right-edge limits
        for y in range(0, height, 24):
            cv2.line(image, (int(x * width), y), (int(x * width), y + 12), (0, 200, 255), 2)
    for name, (x, y) in (spots or {}).items():   # the main rule's circles first, so no number tag hides under one
        colour = SPOT_COLOURS.get(name, (60, 220, 60))
        centre = (int(x * width), int(y * height))
        cv2.circle(image, centre, 18, (0, 0, 0), 9, cv2.LINE_AA)
        cv2.circle(image, centre, 18, colour, 4, cv2.LINE_AA)
    taken = []
    marked = [i for i in ranked if i['mark'] is not None]
    for item in sorted(marked, key=lambda i: not i['area']):   # areas first, small places on top
        l, t, r, b = (int(v) for v in item['mark'])
        l, t, r, b = max(l, 1), max(t, 1), min(r, width - 2), min(b, height - 2)
        colour, thick = ((0, 170, 255), 2) if item['area'] else ((40, 40, 255), 4)
        cv2.rectangle(image, (l, t), (r, b), (0, 0, 0), thick + 3)
        cv2.rectangle(image, (l, t), (r, b), colour, thick)
    for item in sorted(marked, key=lambda i: i['area']):   # small places' tags first, beside their boxes
        l, t, r, b = (int(v) for v in item['mark'])
        colour = (0, 170, 255) if item['area'] else (40, 40, 255)
        if item['area']:
            label(image, str(item['number']), l + 4, t + 4, colour, taken)   # inside the box, at its top-left
        else:
            label(image, str(item['number']), r + 6, t, colour, taken)
    for item in ranked:
        if item['arrow']:
            (x0, y0), (x1, y1) = item['arrow']
            cv2.arrowedLine(image, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 0), 7, cv2.LINE_AA, tipLength=0.2)
            cv2.arrowedLine(image, (int(x0), int(y0)), (int(x1), int(y1)), (255, 255, 0), 3, cv2.LINE_AA, tipLength=0.2)
    if shot.picture is None:
        cv2.rectangle(image, (0, height - 50), (width, height), (0, 0, 0), -1)
        cv2.putText(image, 'flat-colour picture: no finished picture was given', (14, height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, 88])


def write_report(path, report, ranked, title, shot):
    checks = sum(1 for i in report.items if i['passed'] is not None)
    known = [i for i in report.items if i['passed'] == 'known']
    extra = getattr(shot, 'kinds_and_accepted', None)
    counted = (f' ({len(known)} more known: accepted in the check file or allowed for a {" + ".join(extra["kinds"])} shot, listed under '
               f'"Known and allowed")') if extra is not None else ''
    lines = [f'# Shot check: {title}', '',
             f'{len(ranked)} problem{"s" if len(ranked) != 1 else ""} found in {checks} checks{counted}, numbered worst first (the camera first, '
             'because it moves everything on screen).', '',
             f'How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). '
             f'Pixels are this frame\'s ({shot.width} wide). Metres are metres in the street; "Blender x, y" is a spot on the street\'s map '
             '(x across the street, y up it). ' + LEGEND, '', WORDS, '',
             f'Made by check_shot.py version {VERSION}; a report made by another version may give other numbers.', '']
    if shot.picture is None:
        lines += ['No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main '
                  'rule, and the dark shape in rule 8) are not checked.', '']
    if ranked:
        first = ranked[0]
        lines += ['## Fix first', '', f'Problem 1 ({first["rule"]}). ' + (first['fix'] or first['what'])]
        if first['kind'] == 'camera':
            lines.append('Fix the camera before anything else, then check again: the places of the props on screen will all change.')
        lines += ['', '## Problems', '']
        for item in ranked:
            lines.append(f'{item["number"]}. **{item["rule"]}.** {item["what"]}' + (f' ({item["numbers"]})' if item['numbers'] else ''))
            if item['fix']:
                lines.append(f'   - Fix: {item["fix"]}')
        lines.append('')
    if extra is not None:
        lines += ['## Known and allowed', '', f'Kinds of shot: {" + ".join(extra["kinds"])} (film-settings.json shot_kind_profiles, '
                  f'{extra["settings_file"]}). Accepted problems are the check file\'s "accepted" list.', '']
        for item in known:
            how = item['known']
            lines.append(f'- **{item["rule"]}.** {item["what"]}' + (f' ({item["numbers"]})' if item['numbers'] else ''))
            lines.append(f'   - {"Accepted" if how["how"] == "accepted" else "Allowed"}: {how["words"]}')
        if not known:
            lines.append('- none')
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
    parser.add_argument('--settings', help='film-settings.json, for the check file\'s "kind_of_shot" and "accepted" (default: kit/film-settings.json)')
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    shot = Shot(args)
    report = Report()
    check_set_up(report, shot)
    if shot.reference_note:
        report.note('reference', shot.reference_note)
    size = shot.check.get('size')
    if size and list(size) != [shot.width, shot.height]:
        report.add('set-up', False, f'The check file is for a {size[0]} x {size[1]} frame, but the measured frame is {shot.width} x {shot.height}.',
                   fix='Use the check file made for this frame, or measure the scene at the check file\'s size.', kind='set-up', how_bad=8)
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
    check_camera_distance(report, shot)
    one_camera_fix(report, shot)
    shot.camera_fault = any(i['kind'] == 'camera' and i['passed'] is False for i in report.items)
    check_resting(report, shot)
    check_missing(report, shot)
    check_lines(report, shot)
    touching = check_pairs(report, shot)
    check_story_in_3d(report, shot)
    story_union = check_story_props(report, shot, touching)
    check_story_reaches_down(report, shot)
    for item in report.problems():   # a prop standing apart: its rule 3 move fixes its near-touches too; don't undo it
        loner = next((g for g in (item.get('pair') or ()) if g in shot.apart), None)
        if loner and item['rule'].startswith('rule 4'):
            item['fix'] = f'The move in <<apart>> (bringing {loner} into the group) fixes this too, if it ends in a clear overlap; check again after it.'
    check_words_hidden(report, shot)
    check_cut_by_edge(report, shot)
    check_right_edge(report, shot)
    blurred = cv2.GaussianBlur(shot.grey, (0, 0), shot.width * 0.01) if shot.grey is not None else None
    check_titles(report, shot, blurred)
    check_work_props(report, shot)
    spots = None
    off = picture_mismatch(shot) if shot.picture is not None else []
    if off:
        report.add('set-up: the finished picture matches the scene', False,
                   'The finished picture does not match the scene as measured: ' + ', '.join(off) + (' stand' if len(off) > 1 else ' stands') + ' somewhere else in it. '
                   'It was probably made before the scene changed, so the light rules were not judged.',
                   fix='Render a new finished picture of the scene as it is now, and check again.', kind='set-up', how_bad=6)
    elif shot.grey is not None:
        check_dark_entry(report, shot)
        spots = check_light(report, shot, story_union, blurred)
        shot.light_judged = True
    check_reference_places(report, shot)
    shot.kinds_and_accepted = apply_kinds_and_accepted(report, shot, args.settings)
    if shot.kinds_and_accepted is not None:
        shot.camera_fault = any(i['kind'] == 'camera' and i['passed'] is False for i in report.items)
    if shot.camera_fault:
        report.camera_first()
    ranked = report.rank()
    draw_marked(os.path.join(args.out, 'marked.jpg'), shot, ranked, spots)
    print(write_report(os.path.join(args.out, 'report.md'), report, ranked, args.title or os.path.basename(os.path.normpath(args.facts)), shot))
    if shot.kinds_and_accepted is not None:
        plain_item = lambda i: {k: i.get(k) for k in ('number', 'rule', 'rule_id', 'what', 'numbers', 'fix', 'things', 'known')}
        with open(os.path.join(args.out, 'known.json'), 'w') as handle:
            json.dump({'about': 'check_shot.py: the problems, and the problems known (accepted in the check file) or allowed for the view\'s '
                                'kinds of shot', 'version': VERSION, **shot.kinds_and_accepted,
                       'problems': [plain_item(i) for i in ranked], 'known': [plain_item(i) for i in report.items if i['passed'] == 'known']},
                      handle, indent=1, default=str)


if __name__ == '__main__':
    main()
