"""What this does: plans a shot before anything is built, drawn or painted, from a place's facts (place facts, see
place_facts.py) and a short shot list (the subject, the story things, the kind of shot). It is pure geometry, done with
the core's camera sums (frame_geometry.py), and it does two jobs:

  plan   where the camera stands and how it turns: its place across the street (in line with the subject's or its
         support's near edge, rule 1), its height (a standing eye above the surface under it, rule 2), how far back it
         stands (the nearest story thing reaches 0.70 down the frame, rule 7; figures stay 6 m away), its turn (where
         the street's lines meet), the sideways slide that clears the phone buttons (rule 12, never a turn), the
         slide's start (the plate's spot) and its longest safe length, and the plate's lens and size;
  judge  for that camera (or one you give, or a view as it was built) it predicts the numbers the shot checker
         (check_shot.py) will measure: where the lines meet and the gap to the subject (rule 1), the eye height
         (rule 2), how far down the story reaches (rule 7), the right edges near the phone buttons (rule 12), the
         story box (rule 3), the main rule's spots, the subject's share, work props and the bottom-left quarter
         (rule 8); and the people (backs turned and 6 m away from every camera place along the slide, faces, a
         crowd's long axis across every view, two deep, heads apart on screen), the signs' facing, the slide's
         magnification at the nearest painted thing and the plate's coverage. Each failure says by how much, in
         metres, and what to move.

The limits come from the view's kinds of shot (shot-kind profiles in film-settings.json: still life, crowd, overview,
interior, dark subject; the loosest wins) and every exception in the place's "accepted" list is reported as known, not
as a failure. Numbers marked "estimate" come from upright boxes round each thing (a turned or round thing comes out a
little bigger than it renders): they warn early; the shot checker on the render decides. This tool never suggests a
black silhouette for a figure (lesson 137: they read as shadow puppets); a face that shows gets the painter's "face
lost in shadow" words and a skin check after painting instead.

Use:
  python3 plan_shot.py --place-facts PLACE.json --shots SHOTS.json [--shot NAME ...]
        plans or judges every shot in a shot list (the format is below)
  python3 plan_shot.py --place-facts PLACE.json --view w1 [--at x,y,z --turn DEGREES] [--plate-at x,y,z]
        judges a view of the place facts as it was built, or with its camera moved (for example round 4's spot); its story
        is taken from the props' roles in the place facts, else the view's painted things (painted_points): give a shot list
        for the real story and sizes
  python3 plan_shot.py --place-facts PLACE.json --view w1 --plan
        plans the view's camera afresh from its subject and story
  --count-ground  also count the painted ground at the frame's bottom edge in the slide check (a judgement: see
                  frame_geometry.py slide)
  --strict        exit 1 when any shot has a failure that is not accepted (for a preflight)
  --json / --out FILE / --report FILE / --settings FILE   as every calculator (calculator_output.py)

The shot list (JSON; every key but "shots" and each shot's "subject" may be left out):
  {"about": "...", "place_facts": "works-place-facts.json",            (read relative to the shot list)
   "shots": [{
     "name": "w1",                     the shot's name (also the view to start from, if the place facts has one)
     "view": "w1",                     an existing view to take the camera, subject and kinds of shot from
     "kind_of_shot": ["crowd", "dark_subject"],
     "subject": "no-1 gate", "support": null,
     "story": ["brazier", "no-1-drum-diesel", "group:men at No. 1"],   ("group:NAME" = every figure of that group)
     "work": [], "fill": ["handcart"],  (fill: props an overview may use to reach down the frame)
     "must_read": ["no-1 board"],       (default: the place's signs marked must_read among the subject and story)
     "box_excludes": ["no-1 board"],    (left out of rule 3's box, as in the check file)
     "crowds": ["men at No. 1"],        (figure groups judged as crowds; default: every story group of 3 or more)
     "things": {"no-1 gate": {"base": [-3.5, 22.3, 0.0], "size": [2.95, 0.12, 2.93]}},   (add or correct things:
                                         "base" is the bottom middle, "centre" the middle; size is x, y, z metres)
     "figures": [{"name": "man-7", "feet": [x, y, z], "turn_degrees": 0, "height_metres": 1.75, "group": "..."}],
                                        (replace or add figures, for example an older layout)
     "crowd_layout": {"group": "men at No. 1", "count": 7, "front_middle": [-3.9, 21.6]},
                                        (propose a loose crowd two deep across the view, backs to the camera, from the
                                         people settings; it replaces that group's figures and is judged like any)
     "turn_toward": {"notice": {"target": "camera", "front_axis_degrees": 180}},
                                        (the turn that faces a prop's front at a target: a thing's name, "camera" or [x, y];
                                         front_axis_degrees is the way its front faces at turn 0, 0 = +y, + to the left)
     "camera": {"plan": true,            plan it (default: judge the view's camera, or "at" when given)
                "at": [x, y, z], "turn_degrees": 0, "plate_at": [x, y, z],   (a given camera: the composed spot)
                "stands_on": "left pavement", "eye_height_metres": 1.7,
                "line_up": "near edge" | "centre" | "far edge",      (rule 1: which edge of the subject or support)
                "meeting_point_across": 0.684 | "straight" | "rightmost",   (default "rightmost": the subject as
                                         far right as the phone buttons allow, as in the picture the user liked)
                "spot": [x, y],          (an overview from a window: the camera's place; its height is worked out)
                "along": 17.85,          (fix the camera's place along the street, its coordinate along the lines,
                                         instead of working it out from the reach and the subject's size)
                "slide_metres": 1.2}     (plan a slide of this length toward the subject's middle)
   }]}
Places are Blender metres: x across, y forward (up the street), z up; turns are + to the left of +y.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings, resolve_profile, judge, MissingSetting  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402
import frame_geometry as g  # noqa: E402

SECTION = 'shot_planner'
GRID_CELLS = 20   # a figure's box is tested against the boxes in front on a 20 x 20 grid (a resolution, not a house rule)


# ------------------------------------------------------------------------------------------------ the frame and lenses
class Frame:
    """The frame size and lenses (film-settings.json frame), read once."""

    def __init__(self, settings, facts):
        own = facts.get('frame') or {}
        self.width = own.get('width') or settings.value('frame.width_pixels')
        self.height = own.get('height') or settings.value('frame.height_pixels')
        self.film = settings.value('frame.film_vertical_fov_degrees')
        self.plate = settings.value('frame.plate_vertical_fov_degrees')
        self.focal = g.focal_length_pixels(self.film, self.height)

    def camera(self, position, turn, fov=None, name=''):
        return g.camera_from_turn(position, turn, 0.0, 0.0, fov or self.film, self.width, self.height, name)


def heading(direction):
    """The turn (degrees, + left of +y) that looks along a horizontal direction."""
    return math.degrees(math.atan2(-direction[0], direction[1]))


def along_and_right(turn_degrees):
    """Unit vectors (x, y): straight ahead for a turn, and to its right."""
    t = math.radians(turn_degrees)
    return (-math.sin(t), math.cos(t)), (math.cos(t), math.sin(t))


def dot2(a, b):
    return a[0] * b[0] + a[1] * b[1]


def round_all(value, digits=4):
    return g.round_all(value, digits)


# ------------------------------------------------------------------------------------------------ the place's things
class Place:
    """The place facts, with every thing (prop, sign, figure, or a thing the shot list adds) as an upright box or a point,
    and the surfaces things stand on."""

    def __init__(self, facts, settings, shot):
        self.facts = facts
        self.settings = settings
        self.notes = []
        lines = facts.get('lines') or {'level': [0, 1, 0]}
        self.lines_key = facts.get('lines_key') or next(iter(lines))
        self.lines = lines[self.lines_key]
        horizontal = math.hypot(self.lines[0], self.lines[1])
        self.slope = self.lines[2] / horizontal if horizontal else 0.0
        self.lines_turn = heading(self.lines)
        self.surfaces = facts.get('support_surfaces') or []
        self.things = {}
        self.shoulder = settings.value(f'{SECTION}.figure_shoulder_width_metres')
        self.figure_box = settings.value(f'{SECTION}.figure_box_metres')
        for prop in facts.get('props', []):
            self.add_prop(prop['name'], prop, 'prop')
        for sign in facts.get('signs', []):
            known = self.things.get(sign['name'])
            entry = known or {'name': sign['name'], 'kind': 'sign', 'centre': list(sign['centre']), 'size': None, 'bottom': sign['centre'][2],
                              'how': 'a point (the sign\'s middle; no size in the place facts)'}
            entry.update({'normal': sign.get('normal'), 'letter_height': sign.get('letter_height_metres'), 'must_read': sign.get('must_read', False),
                          'wraps_degrees': sign.get('wraps_degrees'), 'is_sign': True})
            self.things[sign['name']] = entry
        figures = {f['name']: f for f in facts.get('figures', [])}
        for f in shot.get('figures', []):
            figures[f['name']] = dict(f, height_from=f.get('height_from', 'the shot list'))
        default_height = settings.value('people.figure_height_metres')
        for f in figures.values():
            height = f.get('height_metres') or default_height
            turn = f.get('turn_degrees', 0.0)
            facing = f.get('facing') or [-math.sin(math.radians(turn)), math.cos(math.radians(turn)), 0.0]
            feet = list(f['feet'])
            box = f.get('size') or [self.figure_box[0], self.figure_box[1], height]
            self.things[f['name']] = {'name': f['name'], 'kind': 'figure', 'feet': feet, 'height': height, 'facing': facing, 'turn_degrees': turn,
                                      'group': f.get('group', ''), 'centre': [feet[0], feet[1], feet[2] + height / 2],
                                      'size': [box[0], box[1], height], 'bottom': feet[2],
                                      'how': f'a figure {height:.2f} m tall in a {box[0]} x {box[1]} m box '
                                             f'({"its own size" if f.get("size") else "the median of the waiting men\'s models"}; feet as given)'}
        for name, extra in (shot.get('things') or {}).items():
            self.add_prop(name, extra, 'thing', given=True)

    def surface_height(self, x, y, near=None, lowest=False):
        """The height of the support surface under (x, y): the one whose ranges hold the point (the highest at or below
        `near` when several do; the lowest with lowest=True), sloped as written; surfaces without ranges count only where
        no surface with ranges covers the point; None when no surface covers it."""
        found = []
        for s in self.surfaces:
            if 'x_range' in s and not s['x_range'][0] - 1e-6 <= x <= s['x_range'][1] + 1e-6:
                continue
            if 'y_range' in s and not s['y_range'][0] - 1e-6 <= y <= s['y_range'][1] + 1e-6:
                continue
            height = s['height']
            if s.get('slope') and s.get('at'):
                height += s['slope'][0] * (x - s['at'][0]) + s['slope'][1] * (y - s['at'][1])
            found.append((height, s))
        if not found:
            return None
        ranged = [f for f in found if 'x_range' in f[1] or 'y_range' in f[1]]
        found = ranged or found
        if lowest:
            return min(found, key=lambda f: f[0])[0]
        if near is not None:
            below = [f for f in found if f[0] <= near + 0.05]
            if below:
                return max(below, key=lambda f: f[0])[0]
        return min(found, key=lambda f: f[0])[0]

    def named_surface(self, name):
        return next((s for s in self.surfaces if s['name'] == name), None)

    def add_prop(self, name, prop, kind, given=False):
        size = prop.get('size')
        if 'base' in prop or 'centre' in prop:
            if 'base' in prop:
                base = list(prop['base'])
                centre = [base[0], base[1], base[2] + (size[2] / 2 if size else 0.0)]
            else:
                centre = list(prop['centre'])
            how = 'as the shot list gives it'
        else:
            at = list(prop['at'])
            centre, how = at, 'a point (no size in the place facts)'
            if size:
                under = self.surface_height(at[0], at[1], lowest=True)
                if under is not None and at[2] - size[2] / 2 < under - 0.05:
                    centre = [at[0], at[1], at[2] + size[2] / 2]
                    how = (f'"at" read as its bottom middle (as its middle it would sink {under - (at[2] - size[2] / 2):.2f} m into the '
                           f'surface under it)')
                else:
                    how = '"at" read as its middle'
        entry = self.things.get(name, {'name': name, 'kind': kind})
        entry.update({'centre': centre, 'size': list(size) if size else None, 'bottom': centre[2] - (size[2] / 2 if size else 0.0), 'how': how})
        for key in ('role', 'turn_degrees', 'opening', 'dark', 'must_read', 'normal', 'letter_height_metres', 'front_axis_degrees'):
            if key in prop:
                entry[key] = prop[key]
        self.things[name] = entry

    def expand(self, names):
        """Names, with "group:NAME" standing for every figure of that group."""
        found = []
        for name in names or []:
            if name.startswith('group:'):
                group = name[len('group:'):]
                members = [t['name'] for t in self.things.values() if t['kind'] == 'figure' and t['group'] == group]
                if not members:
                    raise SystemExit(f'plan_shot: no figure is in group "{group}"')
                found += members
            elif name not in self.things:
                raise SystemExit(f'plan_shot: "{name}" is not a prop, sign or figure of the place facts '
                                 f'(known: {", ".join(sorted(self.things))}); add it under the shot\'s "things"')
            else:
                found.append(name)
        return list(dict.fromkeys(found))

    def corners(self, name):
        t = self.things[name]
        if t.get('size'):
            low, high = g.box_from_centre(t['centre'], t['size'])
            return g.box_corners(low, high)
        return [list(t['centre'])]

    def bottom_points(self, name):
        """The points a thing reaches lowest with on the frame: a figure's feet; a box's four bottom corners; a point."""
        t = self.things[name]
        if t['kind'] == 'figure':
            return [t['feet']]
        return [c for c in self.corners(name) if abs(c[2] - t['bottom']) < 1e-9] or [list(t['centre'])]


# ------------------------------------------------------------------------------------------------ where things land
def landed_box(place, camera, name):
    """The frame box [left, top, right, bottom] of a thing (unclipped), its nearest depth, and whether it is all in front."""
    return g.project_box(camera, place.corners(name))


def clip(box):
    return [min(max(box[0], 0.0), 1.0), min(max(box[1], 0.0), 1.0), min(max(box[2], 0.0), 1.0), min(max(box[3], 0.0), 1.0)]


def shows(box):
    return box is not None and box[2] > 0 and box[0] < 1 and box[3] > 0 and box[1] < 1


def reach_of(place, camera, name):
    """How far down the frame a thing reaches (its lowest point that is in front of the camera)."""
    lows = [g.project_point(camera, p) for p in place.bottom_points(name)]
    lows = [p for p in lows if p['in_front']]
    return max(p['down'] for p in lows) if lows else None


def gap_to_box(px, py, box, width, height):
    """Pixels from a point to the nearest edge of a box (also when the point is inside it, as check_shot measures to
    the outline), and the pixels across and down."""
    l, t, r, b = box[0] * width, box[1] * height, box[2] * width, box[3] * height
    inside = l <= px <= r and t <= py <= b
    if inside:
        options = [(px - l, -(px - l), 0.0), (r - px, r - px, 0.0), (py - t, 0.0, -(py - t)), (b - py, 0.0, b - py)]
        distance, dx, dy = min(options, key=lambda o: o[0])
        return distance, dx, dy, True
    dx = (l - px) if px < l else (r - px) if px > r else 0.0
    dy = (t - py) if py < t else (b - py) if py > b else 0.0
    return math.hypot(dx, dy), dx, dy, False


# ------------------------------------------------------------------------------------------------ the planner
class Shot:
    def __init__(self, name, spec, place, settings, frame, view, count_ground):
        self.name = name
        self.spec = spec
        self.place = place
        self.settings = settings
        self.frame = frame
        self.view = view or {}
        self.count_ground = count_ground
        self.kinds = spec.get('kind_of_shot') or self.view.get('kind_of_shot') or ['still_life']
        self.rules = resolve_profile(settings, self.kinds)
        subject = spec.get('subject') or (self.view.get('subject') or {}).get('name')
        if not subject:
            raise SystemExit(f'plan_shot: shot {name} names no subject')
        if subject not in place.things and self.view.get('subject'):
            point = self.view['subject']['point']
            place.things[subject] = {'name': subject, 'kind': 'thing', 'centre': list(point), 'size': None, 'bottom': point[2],
                                     'how': 'a point (the view\'s subject point; give its size under the shot\'s "things")'}
        self.subject = place.expand([subject])[0]
        self.support = place.expand([spec['support']])[0] if spec.get('support') else None
        self.story = [s for s in place.expand(spec.get('story', [])) if s not in (self.subject,)]
        self.work = place.expand(spec.get('work', []))
        self.fill = place.expand(spec.get('fill', []))
        self.box_excludes = set(spec.get('box_excludes', []))
        listed = spec.get('must_read')
        if listed is None:
            listed = [n for n in [self.subject, self.support] + self.story if n and place.things.get(n, {}).get('must_read')]
        self.must_read = place.expand(listed)
        self.camera_spec = spec.get('camera') or {}
        self.checks = []
        self.steps = []
        self.accepted = [a for a in place.facts.get('accepted', []) if a.get('view') in (name, self.view.get('name'), 'all')]

    # -------------------------------------------------------------------------------------------- small helpers
    def value(self, key):
        return self.settings.value(key)

    def rule(self, rule_id):
        return self.rules[rule_id]

    def add(self, rule_id, about, verdict, measured=None, limit=None, fix='', estimate=False, things=None, **extra):
        item = {'rule': rule_id, 'about': about, 'verdict': verdict, 'measured': measured, 'limit': limit, 'fix': fix,
                'estimate': estimate, 'things': things or []}
        item.update(extra)
        if verdict == 'fail':
            known = self.accepted_entry(rule_id, things or [])
            if known:
                worse = worse_than_accepted(known.get('measured'), measured, limit, self.value(f'{SECTION}.check_shot_accepted_worse_share'))
                if worse:
                    item['accepted_but_worse'] = known
                    item['fix'] = (item.get('fix') or '') + f' (Accepted at {known["measured"]} by {known.get("who")}; it is now {measured}: worse than accepted.)'
                else:
                    item['verdict'] = 'known'
                    item['accepted'] = known
        self.checks.append(item)
        return item

    def accepted_entry(self, rule_id, things):
        for entry in self.accepted:
            if entry.get('rule') != rule_id:
                continue
            named = entry.get('things')
            if named and not set(named) & set(things):
                continue
            return {k: entry[k] for k in ('rule', 'view', 'reason', 'who', 'date', 'measured') if k in entry}
        return None

    def camera_at(self, position, turn, fov=None, name=''):
        return self.frame.camera(position, turn, fov, name)

    def floor_under(self, x, y, near=None):
        view_camera = self.view.get('camera') or {}
        if not self.camera_spec.get('stands_on') and view_camera.get('floor_height') is not None and any(
                spot and abs(spot[0] - x) < 1e-6 and abs(spot[1] - y) < 1e-6 for spot in (view_camera.get('composed'), view_camera.get('plate'))):
            return view_camera['floor_height'], f'the view\'s floor (height {view_camera["floor_height"]:.2f} m)'
        stands_on = self.camera_spec.get('stands_on')
        if stands_on:
            surface = self.place.named_surface(stands_on)
            if surface is None:
                raise SystemExit(f'plan_shot: shot {self.name}: no support surface "{stands_on}" '
                                 f'(known: {", ".join(s["name"] for s in self.place.surfaces)})')
            height = surface['height']
            if surface.get('slope') and surface.get('at'):
                height += surface['slope'][0] * (x - surface['at'][0]) + surface['slope'][1] * (y - surface['at'][1])
            return height, surface['name']
        found = self.place.surface_height(x, y, near)
        if found is not None:
            return found, 'the surface under it'
        floor = (self.view.get('camera') or {}).get('floor_height')
        if floor is not None:
            return floor, 'the view\'s floor'
        return 0.0, 'height 0 (no surface given)'

    def meeting_point(self, camera):
        return g.project_direction(camera, self.place.lines)

    # -------------------------------------------------------------------------------------------- placing the camera
    def given_camera(self):
        """The composed (end) spot and turn: from --at / the shot's camera "at", else the view as built."""
        spec = self.camera_spec
        view_camera = self.view.get('camera') or {}
        at = spec.get('at') or view_camera.get('composed') or view_camera.get('plate')
        turn = spec.get('turn_degrees', view_camera.get('turn_degrees', self.place.lines_turn))
        plate = spec.get('plate_at')
        if plate is None and not spec.get('at'):
            slide = self.view.get('slide')
            plate = slide['start'] if slide else view_camera.get('plate')
        if plate is not None and at is not None and g.length(g.subtract(plate, at)) < 1e-6:
            plate = None
        if at is None:
            raise SystemExit(f'plan_shot: shot {self.name} has no camera to judge: give camera "at", or "plan": true')
        self.steps.append(f'Camera as given: composed spot ({at[0]:.3f}, {at[1]:.3f}, {at[2]:.3f}), turned {turn:.2f} degrees'
                          + (f'; the plate\'s spot (the slide\'s start) ({plate[0]:.3f}, {plate[1]:.3f}, {plate[2]:.3f}).' if plate else '; no slide.'))
        return list(at), turn, list(plate) if plate else None

    def eye_above_floor(self):
        eye = self.camera_spec.get('eye_height_metres') or self.value('camera.eye_height_default_metres')
        return eye

    def target(self):
        return self.support or self.subject

    def plan_camera(self):
        """Rule 1 (in line with the near edge), rule 2 (a standing eye), rule 7 (reach) and people (6 m), then the turn
        and rule 12's sideways slide; the slide's start toward the subject's middle."""
        spec, place = self.camera_spec, self.place
        lines_turn = place.lines_turn
        ahead, right = along_and_right(lines_turn)
        eye = self.eye_above_floor()
        if 'spot' in spec:   # an overview from a window: the place is given, the height is worked out
            return self.plan_overview(spec['spot'], lines_turn, eye)
        target = self.target()
        corners = place.corners(target)
        laterals = [dot2(c, right) for c in corners]
        line_up = spec.get('line_up', 'near edge')
        side = 'right' if spec.get('subject_side', 'right') == 'right' else 'left'
        if line_up == 'centre':
            lateral = dot2(place.things[target]['centre'], right)
            words = f'the middle of {target}'
        elif (line_up == 'near edge') == (side == 'right'):
            lateral = min(laterals)
            words = f'{target}\'s {"near" if line_up == "near edge" else "far"} (left) edge'
        else:
            lateral = max(laterals)
            words = f'{target}\'s {"near" if line_up == "near edge" else "far"} (right) edge'
        self.lined_up_lateral = lateral
        self.steps.append(f'Rule 1: stand in line with {words}: {lateral:.3f} m across the street\'s lines (the line through it along the '
                          f'street then lands exactly where the lines meet, whatever the turn).')
        surface = place.named_surface(spec['stands_on']) if spec.get('stands_on') else None
        if surface and 'x_range' in surface and abs(right[0]) > 0.999:
            low, high = sorted(v * right[0] for v in surface['x_range'])
            if not low <= lateral <= high:
                clamped = min(max(lateral, low), high)
                self.steps.append(f'That line is off {surface["name"]} ({low:.2f} to {high:.2f}); the camera stands at its edge, {clamped:.2f}, '
                                  f'{abs(clamped - lateral):.2f} m out of line (see rule 1 below).')
                lateral = clamped
        # how far back: the story's reach first, then the people
        subject_centre = place.things[self.subject]['centre']
        turn = lines_turn

        def spot(a, lateral_now=None):
            lat = lateral if lateral_now is None else lateral_now
            x, y = right[0] * lat + ahead[0] * a, right[1] * lat + ahead[1] * a
            floor, _ = self.floor_under(x, y)
            return [x, y, floor + eye]

        reachers = [n for n in [self.subject] + self.story if place.things[n].get('size') or place.things[n]['kind'] == 'figure']
        aim = self.rule('rule7_story_reaches_down')['value'] + self.value(f'{SECTION}.reach_aim_margin_down')
        found = []
        for n in reachers:
            a = solve_along(lambda a, n=n: reach_of(place, self.camera_at(spot(a), turn), n), aim, dot2(place.things[n]['centre'], ahead))
            if a is not None:
                found.append((a, n))
        if not found:
            raise SystemExit(f'plan_shot: shot {self.name}: no story thing can reach {aim:.2f} down from this street (give their sizes)')
        a_reach, reacher = min(found)
        self.steps.append(f'Rule 7: {reacher} reaches {aim:.2f} down (the rule\'s {aim - self.value(f"{SECTION}.reach_aim_margin_down"):.2f} '
                          f'plus a {self.value(f"{SECTION}.reach_aim_margin_down"):.2f} margin for the render) with the camera '
                          f'{dot2(place.things[reacher]["centre"], ahead) - a_reach:.2f} m back from its middle along the street: the furthest back '
                          f'the camera may stand.')
        a = a_reach
        share_range = self.value('composing.subject_frame_share')
        subject_thing = place.things[self.subject]
        if spec.get('along') is not None:
            a = spec['along']
            self.steps.append(f'The camera\'s place along the street is given: {a:.3f} m (the reach and the subject\'s size are judged below).')
        elif self.kinds == ['still_life'] and subject_thing.get('size'):
            area = subject_thing['size'][0] * subject_thing['size'][2]
            wanted = sum(share_range) / 2
            depth = self.frame.focal * math.sqrt(area / (wanted * self.frame.width * self.frame.height))
            a_share = dot2(subject_centre, ahead) - depth
            if a_share > a:
                a = a_share
                self.steps.append(f'Still life: the subject {self.subject} fills about {wanted:.1%} of the frame (the liked picture\'s '
                                  f'{share_range[0]:.1%} to {share_range[1]:.1%}) from {depth:.2f} m: the camera comes that near.')
            else:
                self.steps.append(f'Still life: at {depth:.2f} m {self.subject} would fill {wanted:.1%}, but the reach needs the camera nearer, '
                                  f'so it comes out bigger (see the subject\'s share below; or scale it down).')
        position = spot(a)
        # rule 1 and 12: the turn, then a sideways slide (never a turn) for the phone buttons
        wanted = spec.get('meeting_point_across', 'rightmost')
        if isinstance(wanted, (int, float)):
            turn = lines_turn + g.turn_for_meeting_point(wanted, self.frame.film, self.frame.width, self.frame.height)
            self.steps.append(f'Turn {turn:.2f} degrees so the lines meet {wanted:.3f} across (as asked).')
        elif wanted == 'rightmost':
            limit = self.rule('rule12_must_read_right_edge')['value'] - self.value(f'{SECTION}.right_edge_aim_margin_share')
            names = self.must_read or [self.subject]
            turn = solve_turn(lambda t: max(landed_box(place, self.camera_at(position, t), n)['box'][2] for n in names), limit, lines_turn,
                              self.frame)
            met = self.meeting_point(self.camera_at(position, turn))
            if met is None or met['across'] < 0.5 or met['across'] > self.rule('rule12_must_read_right_edge')['value']:
                turn = lines_turn
                self.steps.append('Turn: straight along the lines (the turn that puts the words at the right edge would put where the lines '
                                  'meet left of the middle or past the phone buttons).')
            else:
                self.steps.append(f'Turn {turn:.2f} degrees: the lines meet {met["across"]:.3f} across, which puts the right edge of '
                                  f'{" and ".join(names)} at {limit:.3f} (the phone buttons\' {self.rule("rule12_must_read_right_edge")["value"]} '
                                  f'less {self.value(f"{SECTION}.right_edge_aim_margin_share")}).')
        else:
            self.steps.append('Turn: straight along the lines.')
        camera = self.camera_at(position, turn)
        slide = self.buttons_slide(camera)
        self.buttons_slide_metres = slide
        if slide > 0:
            lateral_now = lateral + slide
            position = spot(a, lateral_now)
            # the slide moves the camera across the lines (right of the view), keep its height on the floor
            camera = self.camera_at(position, turn)
            self.steps.append(f'Rule 12: slide the camera {slide:.3f} m to the right without turning, so every word to read ends left of '
                              f'{self.rule("rule12_must_read_right_edge")["value"]} across (where the lines meet stays put).')
        # the slide's start: back along the line from the end to the subject's middle
        plate = None
        length = spec.get('slide_metres')
        if length:
            toward = [subject_centre[0] - position[0], subject_centre[1] - position[1]]
            n = math.hypot(*toward)
            x, y = position[0] - length * toward[0] / n, position[1] - length * toward[1] / n
            plate = [x, y, position[2]]
            self.steps.append(f'The slide: {length} m toward {self.subject}\'s middle, level (the same height) and the same turn; '
                              f'it starts (the plate\'s spot) at ({plate[0]:.3f}, {plate[1]:.3f}, {plate[2]:.3f}).')
        self.steps.append(f'Planned camera: composed spot ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f}), turned {turn:.2f} degrees, '
                          f'eye {eye:.2f} m above the floor.')
        return position, turn, plate

    def plan_overview(self, spot2, turn, eye_floor):
        """An overview from a raised place: the eye that lets the nearest story thing reach down the frame (never tilt)."""
        place = self.place
        floor, where = self.floor_under(spot2[0], spot2[1])
        aim = self.rule('rule7_story_reaches_down')['value'] + self.value(f'{SECTION}.reach_aim_margin_down')
        best = None
        for n in [self.subject] + self.story:
            if not (place.things[n].get('size') or place.things[n]['kind'] == 'figure'):
                continue
            z = solve_height(lambda z, n=n: reach_of(place, self.camera_at([spot2[0], spot2[1], z], turn), n), aim, floor + 1.0)
            if z is not None and (best is None or z < best[0]):
                best = (z, n)
        given = self.camera_spec.get('eye_height_metres')
        top = floor + self.rule('rule2_eye_height')['value'][1]
        if best:
            self.steps.append(f'Overview: for {best[1]} to reach {aim:.2f} down the eye must stand {best[0]:.2f} m high '
                              f'({best[0] - floor:.2f} m above {where}); raise the eye, never tilt.')
            z = best[0] if given is None else floor + given
            if given is None and z > top:
                z = top
                fill = 'fill' in self.rule('rule7_story_reaches_down').get('who_may_reach', '')
                reached = [n for n in self.fill if (reach_of(place, self.camera_at([spot2[0], spot2[1], z], turn), n) or 0) >= aim] if fill else []
                self.steps.append(f'That is above the {" + ".join(self.rule("rule2_eye_height")["from_kinds"])} eye range (up to '
                                  f'{self.rule("rule2_eye_height")["value"][1]} m above {where}): the eye stays at {z:.2f} m'
                                  + (f', and {", ".join(reached)} (a fill prop, which an overview allows) makes the reach.' if reached else
                                     '; nothing else reaches: come nearer, or add a fill prop in the bottom third.'))
        else:
            z = floor + (given or eye_floor)
        if given is not None:
            self.steps.append(f'The shot gives the eye {given:.2f} m above {where}: the camera stands at {z:.2f} m.')
        return [spot2[0], spot2[1], z], turn, None

    def buttons_slide(self, camera):
        """How far to slide right (metres, never turning) so every word to read ends left of the must-read edge."""
        limit = self.rule('rule12_must_read_right_edge')['value']
        slide = 0.0
        for n in self.must_read:
            landed = landed_box(self.place, camera, n)
            if landed['box'] and landed['box'][2] > limit:
                slide = max(slide, (landed['box'][2] - limit + 0.005) * self.frame.width * landed['nearest_depth'] / self.frame.focal)
        return slide

    # -------------------------------------------------------------------------------------------- judging a camera
    def judge(self, position, turn, plate):
        place, frame = self.place, self.frame
        camera = self.camera_at(position, turn, name='composed')
        self.camera = camera
        met = self.meeting_point(camera)
        self.judge_eye(position, camera)
        self.judge_rule1(camera, met)
        self.judge_reach(camera, met, position)
        self.judge_buttons(camera)
        boxes = self.judge_story_box(camera)
        self.judge_together()
        self.judge_spots(camera, met, boxes)
        self.judge_share(camera)
        self.judge_work_and_corner(camera)
        cameras = self.slide_cameras(position, turn, plate)
        self.judge_people(cameras)
        self.judge_signs(camera)
        slide = self.judge_slide(position, turn, plate)
        result = {'camera': {'composed': round_all(position), 'plate': round_all(plate) if plate else None, 'turn_degrees': round(turn, 4),
                             'film_vertical_fov_degrees': frame.film, 'plate_vertical_fov_degrees': frame.plate,
                             'eye_above_floor_metres': round(self.eye_now, 4), 'floor': self.floor_words},
                  'meeting_point': round_all(met) if met else None, 'slide': slide}
        return result

    def judge_eye(self, position, camera):
        floor, where = self.floor_under(position[0], position[1], near=position[2] - 1.0)
        eye = position[2] - floor
        self.eye_now, self.floor_words = eye, where
        entry = self.rule('rule2_eye_height')
        verdict = judge(entry, eye)
        low, high = entry['value']
        target = min(max(eye, low + self.value('camera.eye_height_fix_margin_metres')), high - self.value('camera.eye_height_fix_margin_metres'))
        self.add('rule2_eye_height', f'The eye stands {eye:.2f} m above {where} (allowed {low} to {high} m for {" + ".join(entry["from_kinds"])}).',
                 verdict, round(eye, 3), [low, high], fix='' if verdict == 'pass' else f'{"Lower" if eye > target else "Raise"} the camera {abs(eye - target):.2f} m.')
        angles = g.camera_angles(camera)
        level = abs(angles['tilt_degrees']) <= self.value('camera.level_tolerance_degrees')
        self.add('rule2_level', f'The camera is level (tilt {angles["tilt_degrees"]:.2f} degrees): the planner never tilts; an overview raises the eye.',
                 'pass' if level else 'fail', round(angles['tilt_degrees'], 3), self.value('camera.level_tolerance_degrees'))

    def judge_rule1(self, camera, met):
        target = self.target()
        entry = self.rule('rule1_meeting_point_gap')
        if met is None:
            self.add('rule1_meeting_point_gap', 'The street\'s lines meet behind the camera: it faces down the street.', 'fail',
                     fix='Turn the camera to face up the street.')
            return
        landed = landed_box(self.place, camera, target)
        if not self.place.things[target].get('size') or landed['box'] is None:
            self.add('rule1_meeting_point_gap', f'Not judged: {target} has no size (give it under the shot\'s "things").', 'info')
            return
        w, h = self.frame.width, self.frame.height
        mx, my = met['across'] * w, met['down'] * h
        distance, dx, dy, inside = gap_to_box(mx, my, landed['box'], w, h)
        gap = distance / w
        measure = entry.get('measure', '')
        thing = self.place.things[target]
        across_only = 'across only' in entry.get('unit', '')
        if across_only and 'opening' in measure and landed['box'][0] <= met['across'] <= landed['box'][2]:
            verdict, judged_gap, words = 'pass', 0.0, f'where the lines meet lies inside {target}\'s outline across ({" + ".join(entry["from_kinds"])})'
        elif across_only:
            across_gap = 0.0 if landed['box'][0] <= met['across'] <= landed['box'][2] else min(abs(met['across'] - landed['box'][0]),
                                                                                                abs(met['across'] - landed['box'][2]))
            verdict, judged_gap, words = judge(entry, across_gap), across_gap, f'judged across only ({" + ".join(entry["from_kinds"])})'
        else:
            verdict, judged_gap, words = judge(entry, gap), gap, f'{target}\'s outline (an upright box)'
        depth = landed['nearest_depth']
        sideways_metres = abs(dx) * depth / self.frame.focal
        if verdict == 'fail' and judged_gap <= 2 * entry['value']:
            verdict = 'look'   # an upright box's outline is not the thing's: near the limit the checker decides
        fixes = []
        if verdict != 'pass':
            metres = depth / self.frame.focal
            if abs(dx) > 4:
                fixes.append(f'slide the camera {abs(dx) * metres:.2f} m to the {"right" if dx > 0 else "left"} (or move {target} the other way)')
            if abs(dy) > 4 and not across_only:
                fixes.append(f'{"lower" if dy > 0 else "raise"} the camera {abs(dy) * metres:.2f} m (or raise or lower {target})')
        self.add('rule1_meeting_point_gap',
                 f'The lines meet {met["across"]:.3f} across, {met["down"]:.3f} down; the nearest edge of {target} is {gap:.3f} of the width away '
                 f'({abs(dx):.0f} px across, {abs(dy):.0f} px down{", inside its outline" if inside else ""}); {words}; limit {entry["value"]}.',
                 verdict, round(judged_gap, 4), entry['value'], fix='; '.join(fixes).capitalize() + ('.' if fixes else ''), estimate=True,
                 things=[target], dark=bool(thing.get('dark')), gap_share=round(gap, 4), sideways_metres=round(sideways_metres, 3))

    def judge_reach(self, camera, met, position):
        entry = self.rule('rule7_story_reaches_down')
        place = self.place
        story = [n for n in [self.subject] + self.story if place.things[n].get('size') or place.things[n]['kind'] == 'figure']
        reaches = {n: reach_of(place, camera, n) for n in story}
        reaches = {n: r for n, r in reaches.items() if r is not None and r <= 1.0 + 1e-9 and shows(landed_box(place, camera, n)['box'])}
        fill = 'fill' in entry.get('who_may_reach', '')
        fills = {n: reach_of(place, camera, n) for n in self.fill} if fill else {}
        fills = {n: r for n, r in fills.items() if r is not None and r <= 1.0 + 1e-9}
        if not reaches and not fills:
            self.add('rule7_story_reaches_down', 'Not judged: no story thing with a size shows.', 'info')
            return
        lowest = max(reaches, key=reaches.get) if reaches else None
        reach = reaches.get(lowest, 0.0)
        ok = judge(entry, reach) == 'pass'
        shoes = self.value(f'{SECTION}.figure_shoes_below_feet_down')
        margin = self.value(f'{SECTION}.reach_aim_margin_down')
        near = None
        if lowest and not ok and place.things[lowest]['kind'] == 'figure' and reach >= entry['value'] - shoes:
            near = (f'; a figure\'s shoes reach up to {shoes} lower than its feet\'s point, so it may just make it: '
                    f'confirm with the shot checker')
        elif lowest and ok and reach < entry['value'] + margin and place.things[lowest]['kind'] != 'figure':
            near = (f'; within {margin} of the limit, and a box\'s corner reaches a little lower than a round or tapered thing: '
                    f'confirm with the shot checker')
        words = f'The lowest story thing is {lowest}, reaching {reach:.3f} down (limit {entry["value"]})' if lowest else 'No story thing shows'
        fix, nearer = '', None
        if not ok and fills:
            best = max(fills, key=fills.get)
            if judge(entry, fills[best]) == 'pass':
                self.add('rule7_story_reaches_down', words + f'; the fill prop {best} reaches {fills[best]:.3f}, which an overview allows '
                         f'({entry.get("who_may_reach")}).', 'pass', round(fills[best], 4), entry['value'], things=[best])
                self.overview_eye(position, lowest, entry)
                return
        if not ok and lowest:
            thing = place.things[lowest]
            low = max(place.bottom_points(lowest), key=lambda p: g.project_point(camera, p)['down'])
            depth = g.project_point(camera, low)['depth']
            eye_above = position[2] - low[2] - place.slope * (dot2(low, along_and_right(g.camera_angles(camera)['turn_degrees'])[0])
                                                              - dot2(position, along_and_right(g.camera_angles(camera)['turn_degrees'])[0]))
            v_meet = met['down'] if met else 0.5
            d_max = g.reach_distance(entry['value'], eye_above, v_meet, self.frame.film, self.frame.height)
            nearer = depth - d_max if d_max else None
            fix = (f'Bring the camera {nearer:.2f} m nearer along its view (or {lowest} that much nearer the camera): it may stand at most '
                   f'{d_max:.2f} m from {lowest}\'s front ({"its feet are" if thing["kind"] == "figure" else "the bottom of its box is"} now '
                   f'{depth:.2f} m away)') if nearer else f'{lowest} stands on a surface whose lines never come that low: raise the eye.'
            if 'overview' in self.kinds:
                needed = self.overview_eye(position, lowest, entry, quiet=True)
                if needed:
                    fix += f'; or, for an overview, raise the eye to {needed:.2f} m (never tilt)'
            fix += '.'
        self.add('rule7_story_reaches_down', words + (near or '') + '.', 'look' if near else 'pass' if ok else 'fail', round(reach, 4),
                 entry['value'], fix=fix, estimate=True, things=[lowest] if lowest else [],
                 nearer_metres=round(nearer, 3) if not ok and lowest and nearer else None)
        if 'overview' in self.kinds and lowest:
            self.overview_eye(position, lowest, entry)

    def overview_eye(self, position, lowest, entry, quiet=False):
        aim = entry['value']
        z = solve_height(lambda z: reach_of(self.place, self.camera_at([position[0], position[1], z], g.camera_angles(self.camera)['turn_degrees']), lowest),
                         aim, position[2] - 3.0)
        if z is not None and not quiet:
            self.add('overview_eye_for_story', f'For the story itself ({lowest}) to reach {aim} down, the eye would have to stand {z:.2f} m high '
                     f'(it stands {position[2]:.2f} m).', 'info', round(z, 3), things=[lowest])
        return z

    def judge_buttons(self, camera):
        place = self.place
        must = self.rule('rule12_must_read_right_edge')
        story_entry = self.rule('rule12_story_right_edge')
        strip = self.value('safe_area.button_strip_down')
        for n in self.must_read:
            landed = landed_box(place, camera, n)
            if not shows(landed['box']):
                continue
            if not place.things[n].get('size'):
                self.add('rule12_must_read_right_edge', f'{n} (to read): not judged, it has no size (its middle lands '
                         f'{landed["box"][2]:.3f} across; give its size under the shot\'s "things").', 'info', things=[n])
                continue
            right = landed['box'][2]
            verdict = judge(must, right)
            fix = '' if verdict == 'pass' else (f'Slide the camera {(right - must["value"] + 0.005) * self.frame.width * landed["nearest_depth"] / self.frame.focal:.2f} m '
                                                f'to the right without turning (then check rule 1 again).')
            self.add('rule12_must_read_right_edge', f'{n} (to read) ends {right:.3f} across (limit {must["value"]}).', verdict, round(right, 4),
                     must['value'], fix=fix, estimate=True, things=[n])
        rows, over = [], []
        for n in [self.subject] + self.story:
            if n in self.must_read:
                continue
            landed = landed_box(place, camera, n)
            box = landed['box']
            if not shows(box) or box[3] < strip[0] or box[1] > strip[1]:
                continue
            rows.append({'thing': n, 'right': round(box[2], 4)})
            if judge(story_entry, box[2]) == 'fail':   # the checker judges the 90th percentile of the rows in the strip: a box's corner warns early
                over.append((n, box[2], landed['nearest_depth']))
        if rows:
            fixes = [f'{n}: move it {(r - story_entry["value"] + 0.005) * self.frame.width * d / self.frame.focal:.2f} m left, or slide the camera right'
                     for n, r, d in over]
            self.add('rule12_story_right_edge', f'Story things in the button strip ({strip[0]} to {strip[1]} down) end at: '
                     + ', '.join(f'{r["thing"]} {r["right"]:.2f}' for r in rows) + f' across (limit {story_entry["value"]}).',
                     'look' if over else 'pass', round(max(r['right'] for r in rows), 4), story_entry['value'],
                     fix='; '.join(fixes) + ' (a box corner warns early: confirm with the shot checker).' if over else '', estimate=True,
                     things=[n for n, _, _ in over], rows=rows)

    def story_boxes(self, camera):
        boxes = {}
        for n in dict.fromkeys([self.subject] + self.story):
            if n in self.box_excludes:
                continue
            landed = landed_box(self.place, camera, n)
            if shows(landed['box']):
                boxes[n] = clip(landed['box'])
        return boxes

    def judge_story_box(self, camera):
        boxes = self.story_boxes(camera)
        if not boxes:
            return boxes
        entry = self.rule('rule3_story_box')
        l, t = min(b[0] for b in boxes.values()), min(b[1] for b in boxes.values())
        r, b = max(v[2] for v in boxes.values()), max(v[3] for v in boxes.values())
        size = [r - l, b - t]
        verdict = judge(entry, size)
        if verdict == 'fail':
            verdict = 'look'   # boxes are upper bounds: the checker measures only what shows of each thing
        edges = {'left': min(boxes, key=lambda n: boxes[n][0]), 'right': max(boxes, key=lambda n: boxes[n][2]),
                 'top': min(boxes, key=lambda n: boxes[n][1]), 'bottom': max(boxes, key=lambda n: boxes[n][3])}
        fix = ''
        if verdict == 'look':
            depth = landed_box(self.place, camera, edges['left'])['nearest_depth']
            over = max(0.0, size[0] - entry['value'][0])
            fix = (f'Bring {edges["left"]} or {edges["right"]} in about {over * self.frame.width * depth / self.frame.focal:.2f} m toward the subject '
                   f'(at {depth:.1f} m one share of the width is {self.frame.width * depth / self.frame.focal:.2f} m), or check the kind of shot.') if over else \
                  'Bring the top or bottom thing in toward the subject.'
        self.add('rule3_story_box', f'The story things fill a box {size[0]:.2f} wide and {size[1]:.2f} tall (limit {entry["value"][0]} x {entry["value"][1]} '
                 f'for {" + ".join(entry["from_kinds"])}); edges: {edges["left"]} (left), {edges["right"]} (right), {edges["top"]} (top), '
                 f'{edges["bottom"]} (bottom).', verdict, [round(size[0], 3), round(size[1], 3)], entry['value'], fix=fix, estimate=True,
                 things=list(boxes))
        return boxes

    def judge_together(self):
        entry = self.rule('rule3_story_together_metres')
        place = self.place
        standing = [n for n in self.story if place.things[n].get('size') and place.things[n]['kind'] != 'sign']
        support = self.support
        worst = None
        for n in standing:
            a = place.things[n]
            gaps = []
            for o in self.story + [self.subject] + ([support] if support else []):
                if o == n or not place.things[o].get('size'):
                    continue
                gaps.append((footprint_gap(a, place.things[o]), o))
            if gaps:
                gap, other = min(gaps)
                if worst is None or gap > worst[0]:
                    worst = (gap, n, other)
        if worst is None:
            return
        gap, n, other = worst
        verdict = judge(entry, gap)
        self.add('rule3_story_together_metres', f'The story things stand together in the street: the loneliest, {n}, is {gap:.2f} m from {other} '
                 f'(limit {entry["value"]} m between footprints).', verdict, round(gap, 3), entry['value'],
                 fix='' if verdict == 'pass' else f'Move {n} about {gap - 0.1:.2f} m toward {other}.', estimate=True, things=[n, other])
        if support and place.things[support].get('size'):
            behind = self.value('composing.story_depth_behind_support_metres')
            ahead, _ = along_and_right(g.camera_angles(self.camera)['turn_degrees'])
            base = dot2(place.things[support]['centre'], ahead)
            late = [(dot2(place.things[n]['centre'], ahead) - base, n) for n in standing if n != support]
            late = [(d, n) for d, n in late if d > behind]
            for d, n in late:
                self.add('rule3_story_in_front_of_support', f'{n} stands {d:.2f} m behind {support} (the story stands in front of its backdrop).', 'fail',
                         round(d, 3), behind, fix=f'Move {n} {d + 0.3 - behind:.2f} m nearer the camera.', estimate=True, things=[n])

    def judge_spots(self, camera, met, boxes):
        entry = self.rule('main_rule_spot_box')
        planning = self.value(f'{SECTION}.planning_spot_box')
        spots = {}
        if met:
            spots['where the lines meet'] = (met['across'], met['down'])
        subject_box = landed_box(self.place, camera, self.subject)['box']
        if subject_box and shows(subject_box):
            b = clip(subject_box)
            spots[f'middle of {self.subject}'] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        if boxes:
            areas = {n: max(1e-9, (b[2] - b[0]) * (b[3] - b[1])) for n, b in boxes.items()}
            total = sum(areas.values())
            spots['middle of the story things'] = (sum(areas[n] * (b[0] + b[2]) / 2 for n, b in boxes.items()) / total,
                                                   sum(areas[n] * (b[1] + b[3]) / 2 for n, b in boxes.items()) / total)
        if len(spots) < 2:
            return
        xs, ys = [v[0] for v in spots.values()], [v[1] for v in spots.values()]
        size = [max(xs) - min(xs), max(ys) - min(ys)]
        verdict = 'pass' if size[0] <= planning[0] and size[1] <= planning[1] else ('look' if judge(entry, size) == 'pass' else 'fail')
        self.add('main_rule_spot_box', 'The spots that can be worked out before rendering (' + '; '.join(f'{k} {v[0]:.2f}, {v[1]:.2f}' for k, v in spots.items())
                 + f') span {size[0]:.2f} x {size[1]:.2f} (the plan keeps them inside {planning[0]} x {planning[1]} so the brightest parts and the warm '
                 f'light have room within the rule\'s {entry["value"][0]} x {entry["value"][1]}).', verdict, [round(size[0], 3), round(size[1], 3)],
                 planning, estimate=True)

    def judge_share(self, camera):
        thing = self.place.things[self.subject]
        if not thing.get('size'):
            return
        landed = landed_box(self.place, camera, self.subject)
        if not shows(landed['box']):
            return
        b = clip(landed['box'])
        share = (b[2] - b[0]) * (b[3] - b[1])
        wanted = self.value('composing.subject_frame_share')
        judged = self.kinds == ['still_life']
        verdict = ('pass' if wanted[0] <= share <= wanted[1] else 'look') if judged else 'info'
        scale = math.sqrt(sum(wanted) / 2 / share) if share > 0 else None
        self.add('subject_frame_share', f'{self.subject} fills about {share:.1%} of the frame (its box; the liked picture\'s notice '
                 f'{wanted[0]:.1%} to {wanted[1]:.1%}{"" if judged else "; judged only for a still life"}).', verdict, round(share, 4), wanted,
                 fix='' if verdict != 'look' else f'Scale {self.subject} by about {scale:.2f}, or move the camera.', estimate=True, things=[self.subject])

    def judge_work_and_corner(self, camera):
        place = self.place
        band = self.value('composing.work_prop_middle_band_down')
        share_entry = self.rule('rule8_work_prop_share')
        for n in self.work:
            landed = landed_box(place, camera, n)
            if not shows(landed['box']):
                self.add('rule8_work_prop_band', f'{n} does not show.', 'info', things=[n])
                continue
            b = clip(landed['box'])
            middle = (b[1] + b[3]) / 2
            share = (b[2] - b[0]) * (b[3] - b[1])
            verdict = 'pass' if band[0] <= middle <= band[1] else 'look'   # the checker takes the middle of what shows
            fix = ''
            if verdict == 'look':
                eye = self.camera['position'][2] - place.things[n]['bottom']
                height = (place.things[n].get('size') or [0, 0, 0])[2]
                met = self.meeting_point(camera)
                v = met['down'] if met else 0.5
                near = self.frame.focal * (eye - height / 2) / ((band[1] - v) * self.frame.height) if band[1] > v else None
                far = self.frame.focal * (eye - height / 2) / ((band[0] - v) * self.frame.height) if band[0] > v else None
                fix = (f'Stand {n} between {near:.1f} and {far:.1f} m from the camera (now {landed["nearest_depth"]:.1f} m), unless only a part of it '
                       f'shows: the checker takes the middle of what shows.' if near and far
                       else f'Move {n} into the middle band, unless only a part of it shows (the checker takes the middle of what shows).')
            self.add('rule8_work_prop_band', f'{n}\'s middle is {middle:.2f} down (the middle band is {band[0]} to {band[1]}).', verdict,
                     round(middle, 3), band, fix=fix, estimate=True, things=[n])
            verdict = judge(share_entry, share)
            self.add('rule8_work_prop_share', f'{n} covers at most {share:.1%} of the frame (its box; limit {share_entry["value"]:.0%}).',
                     'pass' if verdict == 'pass' else 'look', round(share, 4), share_entry['value'], estimate=True, things=[n])
        entry = self.rule('rule8_bottom_left_share')
        story_things = set([self.subject] + self.story)
        base = self.settings.value('shot_kind_profiles.still_life.rules.rule8_bottom_left_share')
        corner_rows = []
        for n in dict.fromkeys([self.subject] + self.story + self.work + self.fill + [k for k, t in place.things.items() if t.get('size')]):
            landed = landed_box(place, camera, n)
            if not shows(landed['box']) or not landed['all_in_front']:
                continue
            b = clip(landed['box'])
            inside = max(0.0, min(b[2], 0.5) - b[0]) * max(0.0, b[3] - max(b[1], 0.5))
            if inside <= 0:
                continue
            limit = entry['value'] if (n in story_things or 'story' not in entry.get('applies_to', '')) else base
            corner_rows.append({'thing': n, 'share': round(inside, 4), 'limit': limit})
        over = [r for r in corner_rows if r['share'] > r['limit']]   # upper bounds: a box covers more than the thing in it
        if corner_rows:
            self.add('rule8_bottom_left_share', 'In the bottom-left quarter, where the eye enters, the boxes cover: '
                     + ', '.join(f'{r["thing"]} {r["share"]:.1%}' + (' (over its ' + f'{r["limit"]:.0%})' if r in over else '') for r in corner_rows)
                     + f' (limit {base:.0%} a thing' + (f', {entry["value"]:.0%} for a story thing in a {" + ".join(entry["from_kinds"])} shot' if entry['value'] != base else '')
                     + '; a box covers more than the thing in it, so these are upper bounds).', 'look' if over else 'pass',
                     round(max(r['share'] for r in corner_rows), 4), entry['value'],
                     fix=('Confirm on the render (the shot checker measures the real outlines); if it holds, move '
                          + ', '.join(r['thing'] for r in over) + ' out of the bottom-left quarter.') if over else '',
                     estimate=True, things=[r['thing'] for r in over], rows=corner_rows)

    # -------------------------------------------------------------------------------------------- the slide and the people
    def slide_cameras(self, position, turn, plate):
        steps = self.value(f'{SECTION}.slide_sample_steps')
        if not plate:
            return [('composed spot', self.camera_at(position, turn))]
        cameras = []
        for k in range(steps + 1):
            t = k / steps
            p = [plate[i] + t * (position[i] - plate[i]) for i in range(3)]
            label = 'the plate\'s spot (start)' if k == 0 else 'composed spot (end)' if k == steps else f'{t:.0%} along the slide'
            cameras.append((label, self.camera_at(p, turn)))
        return cameras

    def judge_people(self, cameras):
        place = self.place
        minimum = self.value('people.backs_to_camera_min_distance_metres')
        head = self.value('people.head_height_metres')
        face_max = self.value('people.facing_head_max_pixels')
        visible_dot = self.value(f'{SECTION}.face_visible_dot_min')
        end = cameras[-1][1]
        shown = [n for n, t in place.things.items() if t['kind'] == 'figure' and any(g.in_frame(g.project_point(c, t['feet'])) or
                                                                                      g.in_frame(g.project_point(c, t['centre'])) for _, c in cameras)]
        backs = []
        for n in shown:
            t = place.things[n]
            nearest = min(((g.project_point(c, t['feet'])['depth'], label, c) for label, c in cameras), key=lambda v: v[0])
            depth, label, camera = nearest
            to_camera = [camera['position'][0] - t['feet'][0], camera['position'][1] - t['feet'][1]]
            length = math.hypot(*to_camera)
            facing = dot2(t['facing'], (to_camera[0] / length, to_camera[1] / length)) if length else -1.0
            if facing > visible_dot:
                pixels = g.size_in_pixels(camera, head, depth)
                verdict = 'pass' if pixels <= face_max else 'look'
                away = math.degrees(math.acos(max(-1.0, min(1.0, visible_dot)))) - math.degrees(math.acos(max(-1.0, min(1.0, facing))))
                self.add('people_face_shows', f'{n}\'s face or profile shows (it faces {math.degrees(math.acos(max(-1, min(1, facing)))):.0f} degrees from '
                         f'the camera); its head is {pixels:.0f} px tall at {depth:.2f} m ({label}); the house limit {face_max} px is invented and untested.',
                         verdict, round(pixels, 1), face_max,
                         fix='' if verdict == 'pass' else (f'Add "face lost in shadow" to the painter\'s words for {n} and check the head for skin pixels '
                                                           f'after painting (the people test\'s facing man at 7 m got no features that way), or turn him '
                                                           f'at least {away:.0f} degrees further away. Never a black silhouette (lesson 137).'),
                         things=[n])
            else:
                backs.append({'figure': n, 'depth': round(depth, 3), 'at': label})
        if backs:
            near = [b for b in backs if b['depth'] < minimum]
            nearest = min(backs, key=lambda b: b['depth'])
            self.add('people_backs_distance', f'Figures with their backs to the camera, at the nearest camera place along the slide: '
                     + ', '.join(f'{b["figure"]} {b["depth"]:.2f} m' for b in sorted(backs, key=lambda b: b['depth']))
                     + f' (at least {minimum} m: a 1.75 m man is a quarter of the frame there; nearest {nearest["figure"]} at {nearest["at"]}).',
                     'fail' if near else 'pass', nearest['depth'], minimum,
                     fix='; '.join(f'move {b["figure"]} {minimum - b["depth"]:.2f} m further from the camera' for b in near).capitalize()
                     + ' (or the camera back that much, then check the reach again).' if near else '', things=[b['figure'] for b in near], rows=backs)
        self.judge_crowds(shown, end)

    def judge_crowds(self, shown, end_camera):
        place = self.place
        listed = self.spec.get('crowds')
        story = set(self.story)
        groups = {}
        for n in shown:
            t = place.things[n]
            if t['group']:
                groups.setdefault(t['group'], []).append(n)
        minimum = self.value(f'{SECTION}.crowd_min_figures')
        if listed is None:
            listed = [grp for grp, members in groups.items() if len(members) >= minimum and set(members) & story]
        axis_min = self.value('people.crowd_axis_min_angle_to_view_degrees')
        elongation_min = self.value(f'{SECTION}.crowd_axis_min_elongation')
        views = self.views_for_crowds()
        for grp in listed:
            members = [n for n, t in place.things.items() if t['kind'] == 'figure' and t['group'] == grp]
            if len(members) < 2:
                continue
            feet = [place.things[n]['feet'] for n in members]
            axis, elongation = long_axis(feet)
            for view_name, camera in views:
                seen = [n for n in members if g.in_frame(g.project_point(camera, place.things[n]['feet'])) or
                        g.in_frame(g.project_point(camera, place.things[n]['centre']))]
                if not seen:
                    continue
                look = (camera['forward'][0], camera['forward'][1])
                n_look = math.hypot(*look)
                look = (look[0] / n_look, look[1] / n_look)
                if elongation < elongation_min:
                    self.add('crowd_axis_angle', f'Crowd "{grp}" ({len(members)} figures) from {view_name}: no long axis (it spreads about as much '
                             f'one way as the other, {elongation:.2f} to 1): nobody stands in file along the view.', 'pass', None, axis_min, things=members)
                    continue
                angle = math.degrees(math.acos(min(1.0, abs(dot2(axis, look)))))
                verdict = 'pass' if angle >= axis_min else 'fail'
                self.add('crowd_axis_angle', f'Crowd "{grp}" from {view_name}: its long axis makes {angle:.0f} degrees with the view '
                         f'(at least {axis_min}; it spreads {elongation:.1f} times as far along it as across).', verdict, round(angle, 1), axis_min,
                         fix='' if verdict == 'pass' else 'Stand them across the view, not along it: a loose crowd two deep across the gate, '
                                                          f'backs to the camera, {self.value("people.crowd_shoulder_gap_metres")} m between shoulders, '
                                                          f'the back row about {self.value("people.crowd_back_row_behind_metres")} m behind.',
                         things=members, view=view_name)
            self.judge_rows(grp, members)
            self.judge_heads(grp, members)

    def views_for_crowds(self):
        """The cameras that may see a crowd: this shot's composed spot and every view of the place (composed and plate)."""
        views = [(f'this shot ({self.name})', self.camera)]
        for v in self.place.facts.get('views', []):
            if v.get('name') in (self.name, self.view.get('name')):
                continue
            c = v.get('camera', {})
            for spot in ('composed', 'plate'):
                if c.get(spot):
                    views.append((f'view {v["name"]} ({spot})', self.camera_at(c[spot], c.get('turn_degrees', 0.0))))
                    break
        return views

    def judge_rows(self, grp, members):
        place = self.place
        ahead, right = along_and_right(g.camera_angles(self.camera)['turn_degrees'])
        split = self.value('people.crowd_back_row_behind_metres') / 2   # half the back row's distance starts a new row
        ordered = sorted(members, key=lambda n: dot2(place.things[n]['feet'], ahead))
        rows = [[ordered[0]]]
        for n in ordered[1:]:
            if dot2(place.things[n]['feet'], ahead) - dot2(place.things[rows[-1][-1]]['feet'], ahead) > split:
                rows.append([n])
            else:
                rows[-1].append(n)
        gap_range = self.value('people.crowd_shoulder_gap_metres')
        gaps = []
        for row in rows:
            across = sorted(row, key=lambda n: dot2(place.things[n]['feet'], right))
            for a, b in zip(across, across[1:]):
                gaps.append((dot2(place.things[b]['feet'], right) - dot2(place.things[a]['feet'], right) - self.place.shoulder, a, b))
        outside = [(gp, a, b) for gp, a, b in gaps if not gap_range[0] <= gp <= gap_range[1]]
        self.add('crowd_rows', f'Crowd "{grp}": {len(rows)} row{"s" if len(rows) != 1 else ""} deep from this view (front to back: '
                 + '; '.join(', '.join(r) for r in rows) + ').', 'pass' if len(rows) >= 2 else 'look', len(rows), 2,
                 fix='' if len(rows) >= 2 else 'Make it two deep: a back row about '
                                                f'{self.value("people.crowd_back_row_behind_metres")} m behind, each between two of the front row.',
                 things=members)
        if gaps:
            self.add('crowd_shoulder_gaps', f'Crowd "{grp}": gaps between neighbours\' shoulders in a row ({self.place.shoulder} m shoulders): '
                     + ', '.join(f'{a}-{b} {gp:.2f} m' for gp, a, b in gaps) + f' (house range {gap_range[0]} to {gap_range[1]} m).',
                     'pass' if not outside else 'look', [round(min(x[0] for x in gaps), 3), round(max(x[0] for x in gaps), 3)], gap_range,
                     fix='' if not outside else 'Check by eye: ' + ', '.join(f'{a}-{b} {gp:.2f} m' for gp, a, b in outside)
                     + ' (a back-row man standing between two of the front row fills a wide gap).', things=members)

    def judge_heads(self, grp, members):
        place = self.place
        camera = self.camera
        width = self.value(f'{SECTION}.figure_head_width_metres')
        need = self.value('people.crowd_head_spacing_head_widths')
        heads = {}
        for n in members:
            t = place.things[n]
            centre = [t['feet'][0], t['feet'][1], t['feet'][2] + t['height'] - self.value('people.head_height_metres') / 2]
            landed = g.project_point(camera, centre)
            if landed['in_front'] and g.in_frame(landed):
                heads[n] = (landed['x_pixels'], landed['y_pixels'], width * camera['focal'] / landed['depth'])
        worst = None
        names = list(heads)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                ax, ay, aw = heads[a]
                bx, by, bw = heads[b]
                apart = math.hypot(ax - bx, ay - by) / min(aw, bw)
                if worst is None or apart < worst[0]:
                    worst = (apart, a, b)
        if worst:
            verdict = 'pass' if worst[0] >= need else 'fail'
            self.add('crowd_head_spacing', f'Crowd "{grp}" from this shot: the closest two heads, {worst[1]} and {worst[2]}, are {worst[0]:.2f} head '
                     f'widths apart on screen (at least {need}, so each head can be counted).', verdict, round(worst[0], 3), need,
                     fix='' if verdict == 'pass' else f'Move {worst[1]} or {worst[2]} sideways about '
                                                     f'{(need - worst[0]) * width:.2f} m (head widths are {width} m), or change their heights.',
                     estimate=True, things=[worst[1], worst[2]])
        self.judge_visible(grp, members)

    def judge_visible(self, grp, members):
        """Each figure at least half seen: its box against the boxes of nearer things (figures and story props), on a coarse grid."""
        place, camera = self.place, self.camera
        need = self.value('people.crowd_figure_visible_share_min')
        cells = GRID_CELLS
        others = list(dict.fromkeys([n for n, t in place.things.items() if t['kind'] == 'figure'] + self.story + [self.subject]))
        landed = {n: landed_box(place, camera, n) for n in others}
        worst = None
        for n in members:
            box = landed[n]['box']
            if not shows(box):
                continue
            box = clip(box)
            front = [clip(landed[o]['box']) for o in others if o != n and shows(landed[o]['box'])
                     and landed[o]['nearest_depth'] < landed[n]['nearest_depth'] - 0.05 and place.things[o].get('size')]
            seen = visible_share(box, front, cells)
            if worst is None or seen < worst[0]:
                worst = (seen, n)
        if worst:
            verdict = 'pass' if worst[0] >= need else 'look'
            self.add('crowd_visible_share', f'Crowd "{grp}": the most hidden figure, {worst[1]}, shows about {worst[0]:.0%} of its box (at least '
                     f'{need:.0%}; boxes, so a figure behind a gap between two others shows more than this).', verdict, round(worst[0], 3), need,
                     fix='' if verdict == 'pass' else f'Move {worst[1]} sideways into a gap, or check on the render.', estimate=True, things=[worst[1]])

    def judge_signs(self, camera):
        limit = self.value(f'{SECTION}.sign_edge_on_degrees')
        for n in self.must_read:
            t = self.place.things[n]
            normal = t.get('normal')
            if not normal:
                continue
            to_camera = [camera['position'][0] - t['centre'][0], camera['position'][1] - t['centre'][1]]
            length = math.hypot(*to_camera)
            n_length = math.hypot(normal[0], normal[1])
            if not length or not n_length:
                continue
            cosine = (normal[0] * to_camera[0] + normal[1] * to_camera[1]) / (length * n_length)
            angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
            allowed = t.get('wraps_degrees') or limit
            turn_needed = math.degrees(math.atan2(normal[0] * to_camera[1] - normal[1] * to_camera[0], normal[0] * to_camera[0] + normal[1] * to_camera[1]))
            verdict = 'pass' if angle <= allowed else 'fail'
            self.add('sign_facing', f'{n}\'s lettered face points {angle:.1f} degrees away from the camera (allowed {allowed:.0f}'
                     f'{": the word wraps that far round" if t.get("wraps_degrees") else ": beyond it the face is seen edge-on"}).', verdict,
                     round(angle, 2), allowed,
                     fix='' if verdict == 'pass' else f'Turn {n} {abs(turn_needed):.0f} degrees {"left" if turn_needed > 0 else "right"} (seen from above) to face the camera.',
                     things=[n], turn_to_face_camera_degrees=round(turn_needed, 2))

    def judge_slide(self, position, turn, plate):
        frame = self.frame
        if not plate:
            self.add('slide_magnification', 'A still shot: no slide.', 'info')
            return None
        end = self.camera_at(position, turn)
        start = self.camera_at(plate, turn)
        painting = (self.place.facts.get('painting') or {}).get('returned_size') or self.value('frame.painting_returned_size_pixels')
        limit = g.slide_limit(painting[1], frame.height, frame.film, frame.plate)
        nearest = None
        for n, t in self.place.things.items():
            landed = landed_box(self.place, end, n)
            if not shows(landed['box']) or not landed['all_in_front']:
                continue
            for corner in self.place.corners(n):
                at_end = g.project_point(end, corner)
                if not at_end['in_front']:
                    continue
                if nearest is None or at_end['depth'] < nearest[0]:
                    nearest = (at_end['depth'], n, corner)
        ground = None
        floor_z = position[2] - self.eye_now
        bottom = ground_at_bottom(end, floor_z, self.place.slope, frame)
        if bottom:
            ground = bottom
        length = g.length(g.subtract(position, plate))
        borderline = self.value('camera.slide_magnification_borderline_share')
        result = {'length_metres': round(length, 4), 'limit': round(limit, 4), 'painting_rows': painting[1]}
        if nearest:
            depth_end, name, corner = nearest
            depth_start = g.project_point(start, corner)['depth']
            magnification = depth_start / depth_end
            longest = g.longest_slide(depth_end, limit)
            over = magnification / limit - 1
            verdict = 'pass' if over <= 0 else 'look' if over <= borderline else 'fail'
            result.update({'nearest_painted_thing': name, 'depth_end': round(depth_end, 3), 'magnification': round(magnification, 4),
                           'longest_slide_metres': round(longest, 3)})
            self.add('slide_magnification', f'The {length:.2f} m slide brings the nearest painted thing, {name} (its nearest corner {depth_end:.2f} m away '
                     f'at the end), {magnification:.3f} times nearer; the painting\'s {painting[1]} rows allow {limit:.3f}; the longest slide for it '
                     f'is {longest:.2f} m.', verdict, round(magnification, 4), round(limit, 4),
                     fix='' if verdict == 'pass' else f'Shorten the slide to {longest:.2f} m, or move {name} back {depth_end * (magnification / limit - 1):.2f} m.',
                     things=[name])
        if ground:
            depth_end = g.project_point(end, ground)['depth']
            depth_start = g.project_point(start, ground)['depth']
            m = depth_start / depth_end
            counted = self.count_ground
            verdict = ('pass' if m <= limit else 'fail') if counted else 'info'
            self.add('slide_magnification_ground', f'The painted ground at the frame\'s bottom edge ({depth_end:.2f} m away) comes {m:.3f} times nearer'
                     + ('' if counted else ' (not counted: nobody has judged whether its softness shows; --count-ground counts it)') + '.',
                     verdict, round(m, 4), round(limit, 4))
        self.judge_plate(start, end, plate, position, turn, result)
        return result

    def judge_plate(self, start, end, plate, position, turn, result):
        frame = self.frame
        fade = self.value('frame.plate_frame_edge_fade_share')
        steps = self.value(f'{SECTION}.slide_sample_steps')
        floor_z = position[2] - self.eye_now
        needed = 0.0
        for k in range(steps + 1):
            t = k / steps
            p = [plate[i] + t * (position[i] - plate[i]) for i in range(3)]
            film = self.camera_at(p, turn)
            for across, down in ((0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0), (0.5, 1), (0, 0.5), (1, 0.5)):
                direction = ray(film, across, down)
                hit = hit_floor(film['position'], direction, floor_z, position, self.place.slope, film)
                if hit is None:
                    seen = g.project_direction(start, direction)
                    if seen is None:
                        continue
                    tan_x, tan_y = (seen['across'] - 0.5) * 2, (seen['down'] - 0.5) * 2
                else:
                    seen = g.project_point(start, hit)
                    tan_x, tan_y = (seen['across'] - 0.5) * 2, (seen['down'] - 0.5) * 2
                needed = max(needed, abs(tan_x), abs(tan_y))
        # needed is the share of the film frame's half-size, in the start camera with the film lens; with the fade band
        tan_film = math.tan(math.radians(frame.film) / 2)
        tan_needed = needed * tan_film / (1 - 2 * fade)
        plate_needed = math.degrees(2 * math.atan(tan_needed))
        verdict = 'pass' if plate_needed <= frame.plate + 1e-9 else 'fail'
        rows = math.ceil(frame.height * (result.get('magnification') or 1.0) * math.tan(math.radians(frame.plate) / 2) / tan_film)
        painting_rows = result['painting_rows']
        allowance = g.turn_allowance_degrees(frame.film, frame.plate, frame.width, frame.height)
        nearest = result.get('depth_end')
        result.update({'plate_lens_needed_degrees': round(plate_needed, 3), 'plate_rows_needed': rows,
                       'turn_allowance_degrees': round(allowance['turn_each_way_degrees'], 3),
                       'sideways_allowance_metres': round(g.sideways_allowance_metres(nearest, frame.film, frame.plate, frame.width, frame.height), 4)
                       if nearest else None})
        self.add('plate_lens', f'Casting the film frame\'s corners and edge middles onto the floor every {100 // steps}% of the slide, the plate needs a lens '
                 f'of at least {plate_needed:.2f} degrees (with the {fade} fade band at its edge); the house plate lens is {frame.plate} '
                 f'(film {frame.film} + {self.value("frame.plate_lens_extra_degrees")}); the camera may turn {allowance["turn_each_way_degrees"]:.2f} '
                 f'degrees each way inside it.', verdict, round(plate_needed, 3), frame.plate,
                 fix='' if verdict == 'pass' else f'Draw the plate with a {math.ceil(plate_needed * 10) / 10:.1f}-degree lens, or shorten the slide.')
        self.add('plate_rows', f'For the slide\'s worst magnification the plate would need {rows} rows of real detail; the painter returns '
                 f'{painting_rows} (the house plate is {self.value("frame.plate_width_pixels")} x {self.value("frame.plate_height_pixels")}).',
                 'pass' if rows <= painting_rows else 'info', rows, painting_rows)

    # -------------------------------------------------------------------------------------------- placing people and props
    def propose_crowd(self):
        """A loose crowd two deep across the view, backs to the camera (people settings): the front row across the line of sight,
        the back row behind it, each back-row figure between two of the front, turned a little each way, heights a little apart."""
        layout, place = self.spec['crowd_layout'], self.place
        group, count = layout['group'], int(layout['count'])
        look = self.camera_spec.get('turn_degrees', (self.view.get('camera') or {}).get('turn_degrees', place.lines_turn))
        ahead, right = along_and_right(look)
        gap_range = self.value('people.crowd_shoulder_gap_metres')
        gap = layout.get('gap_metres', sum(gap_range) / 2)
        behind = layout.get('back_row_behind_metres', self.value('people.crowd_back_row_behind_metres'))
        turns_range = self.value('people.crowd_turn_degrees')
        scales = self.value('people.crowd_scale_range')
        height = layout.get('height_metres', self.value('people.figure_height_metres'))
        spacing = self.place.shoulder + gap
        front = (count + 1) // 2
        middle = layout['front_middle']
        jitter = [turns_range[0] + (turns_range[1] - turns_range[0]) * k / 4 for k in (1, 3, 0, 4, 2)]
        stature = [1.0, scales[1], scales[0], (1.0 + scales[1]) / 2, (1.0 + scales[0]) / 2]
        figures = []
        for k in range(count):
            row, slot = (0, k) if k < front else (1, k - front)
            across = (slot - (front - 1) / 2) * spacing + (spacing / 2 if row else 0.0)
            x, y = middle[0] + right[0] * across - ahead[0] * behind * row, middle[1] + right[1] * across - ahead[1] * behind * row
            floor = place.surface_height(x, y)
            z = layout.get('z', floor if floor is not None else 0.0)
            turn = look + jitter[k % len(jitter)] * (1 if k % 2 else -1)
            figures.append({'name': f'{group} {k + 1}', 'feet': [x, y, z], 'turn_degrees': turn, 'height_metres': height * stature[k % len(stature)],
                            'group': group})
        for name in [n for n, t in place.things.items() if t['kind'] == 'figure' and t['group'] == group]:
            del place.things[name]
        replaced = Place({'props': [], 'signs': [], 'figures': figures, 'support_surfaces': place.surfaces, 'lines': place.facts.get('lines'),
                          'lines_key': place.lines_key}, self.settings, {})
        place.things.update(replaced.things)
        self.story = [n for n in self.story if n in place.things] + [f['name'] for f in figures if f['name'] not in self.story]
        self.steps.append(f'People: a loose crowd of {count} ("{group}") two deep across the view: the front row (nearest what they face) round '
                          f'({middle[0]:.2f}, {middle[1]:.2f}), {front} figures {spacing:.2f} m apart ({gap:.2f} m between {self.place.shoulder} m '
                          f'shoulders); the back row of {count - front} stands {behind} m behind them (nearer the camera), each between two of the '
                          f'front; backs to the camera, turned {turns_range[0]} to {turns_range[1]} degrees either way, heights {scales[0]} to '
                          f'{scales[1]} of {height} m.')
        return figures

    def prop_turns(self, position):
        """The turn that faces each listed prop's front at its target (front_axis_degrees: the way its front faces at turn 0)."""
        found = {}
        for name, want in self.spec['turn_toward'].items():
            thing = self.place.things[self.place.expand([name])[0]]
            target = want.get('target', 'camera')
            if target == 'camera':
                point = position
            elif isinstance(target, str):
                point = self.place.things[self.place.expand([target])[0]]['centre']
            else:
                point = target
            towards = heading([point[0] - thing['centre'][0], point[1] - thing['centre'][1]])
            turn = (towards - want.get('front_axis_degrees', 0.0) + 180.0) % 360.0 - 180.0
            found[name] = {'turn_degrees': round(turn, 3), 'toward': target if isinstance(target, str) else list(target),
                           'front_axis_degrees': want.get('front_axis_degrees', 0.0)}
            self.add('prop_turn', f'Turn {name} {turn:.2f} degrees (+ left) to face its front at {target if isinstance(target, str) else "the given spot"} '
                     f'(its front faces {want.get("front_axis_degrees", 0.0)} degrees at turn 0).', 'info', round(turn, 3), things=[name])
        return found

    # -------------------------------------------------------------------------------------------- the whole shot
    def run(self, override_at=None, override_turn=None, override_plate=None, plan=None):
        spec = self.camera_spec
        if override_at is not None:
            spec = dict(spec, at=override_at)
            if override_turn is not None:
                spec['turn_degrees'] = override_turn
            spec['plate_at'] = override_plate
            self.camera_spec = spec
        planning = plan if plan is not None else bool(spec.get('plan')) and override_at is None
        proposed = self.propose_crowd() if self.spec.get('crowd_layout') else None
        if planning:
            position, turn, plate = self.plan_camera()
        else:
            position, turn, plate = self.given_camera()
        result = self.judge(position, turn, plate)
        if proposed:
            result['proposed_figures'] = round_all(proposed)
        if self.spec.get('turn_toward'):
            result['prop_turns'] = self.prop_turns(position)
        if planning and hasattr(self, 'lined_up_lateral'):
            result['camera']['lined_up_across_metres'] = round(self.lined_up_lateral, 4)
            result['camera']['buttons_slide_metres'] = round(getattr(self, 'buttons_slide_metres', 0.0), 4)
        result.update({'name': self.name, 'planned': planning, 'kind_of_shot': self.kinds, 'subject': self.subject, 'support': self.support,
                       'story': self.story, 'must_read': self.must_read, 'steps': self.steps, 'checks': round_all(self.checks),
                       'closed_forms': self.closed_forms(position, turn)})
        counts = {}
        for c in self.checks:
            counts[c['verdict']] = counts.get(c['verdict'], 0) + 1
        result['counts'] = counts
        result['verdict'] = 'fail' if counts.get('fail') else 'look' if counts.get('look') else 'pass'
        return result

    def closed_forms(self, position, turn):
        """The hand-found numbers, worked out: what one degree of turn moves, the deepest a story thing may stand (above its
        own surface), the eye for an overview, the slide limit, the allowances, a figure's sizes."""
        frame, place = self.frame, self.place
        met = self.meeting_point(self.camera)
        v = met['down'] if met else 0.5
        reach = self.rule('rule7_story_reaches_down')['value']
        found = {'one_degree_of_turn_share': g.turn_moves_per_degree(frame.film, frame.width, frame.height),
                 'meeting_point_down': v, 'eye_above_floor': self.eye_now,
                 'deepest_for_reach_on_the_floor_metres': g.reach_distance(reach, self.eye_now, v, frame.film, frame.height),
                 'figure_quarter_height_distance_metres': g.distance_for_size(self.camera, self.value('people.figure_height_metres'), 0.25 * frame.height),
                 'head_pixels_at_6_metres': g.size_in_pixels(self.camera, self.value('people.head_height_metres'), 6.0),
                 'slide_limit': g.slide_limit(((place.facts.get('painting') or {}).get('returned_size') or
                                               self.value('frame.painting_returned_size_pixels'))[1], frame.height, frame.film, frame.plate),
                 'rule4_clear_overlap_metres_per_metre_of_depth': math.ceil(self.value('composing.clear_overlap_pixels_at_1536') * frame.width / 1536) / frame.focal,
                 'rule4_clear_gap_metres_per_metre_of_depth': math.ceil(self.value('composing.clear_gap_pixels_at_1536') * frame.width / 1536) / frame.focal}
        story = [n for n in [self.subject] + self.story if place.things[n].get('size') or place.things[n]['kind'] == 'figure']
        ahead, _ = along_and_right(turn)
        per_thing = {}
        for n in story:
            low = place.bottom_points(n)[0]
            eye_above = position[2] - low[2] - place.slope * (dot2(low, ahead) - dot2(position, ahead))
            per_thing[n] = round(g.reach_distance(reach, eye_above, v, frame.film, frame.height) or 0, 3)
        found['deepest_for_reach_per_story_thing_metres'] = per_thing
        return round_all(found)


# ------------------------------------------------------------------------------------------------ small solvers and sums
def worse_than_accepted(accepted, measured, limit, share):
    """True when a number accepted at `accepted` has moved more than `share` further past its limit (a max limit when the
    accepted number lies above it, a min limit when below)."""
    if not isinstance(accepted, (int, float)) or not isinstance(measured, (int, float)) or not isinstance(limit, (int, float)):
        return False
    if accepted >= limit:
        return measured > accepted * (1 + share)
    return measured < accepted * (1 - share)


def solve_along(reach_at, aim, upper):
    """The camera's place along the street (a coordinate along its view) at which a thing reaches `aim` down: bisection
    between far back and the thing itself (the reach grows as the camera comes nearer)."""
    low, high = upper - 400.0, upper - 0.05
    r_high = reach_at(high)
    if r_high is None or r_high < aim:
        return None
    r_low = reach_at(low)
    if r_low is not None and r_low >= aim:
        return low
    for _ in range(80):
        middle = (low + high) / 2
        r = reach_at(middle)
        if r is not None and r >= aim:
            high = middle
        else:
            low = middle
    return high


def solve_height(reach_at, aim, low):
    """The camera height at which a thing reaches `aim` down (raising the eye lowers a ground thing on the frame)."""
    high = low + 200.0
    r = reach_at(high)
    if r is None or r < aim:
        return None
    r = reach_at(low)
    if r is not None and r >= aim:
        return low
    for _ in range(80):
        middle = (low + high) / 2
        r = reach_at(middle)
        if r is not None and r >= aim:
            high = middle
        else:
            low = middle
    return high


def solve_turn(right_edge_at, limit, start, frame):
    """The turn (degrees) at which a right edge lands at `limit` across (turning left moves things right)."""
    low, high = start - 45.0, start + 45.0
    for _ in range(80):
        middle = (low + high) / 2
        if right_edge_at(middle) > limit:
            high = middle
        else:
            low = middle
    return low


def footprint_gap(a, b):
    """Metres between two upright boxes' footprints (0 when they touch or overlap)."""
    gx = max(0.0, abs(a['centre'][0] - b['centre'][0]) - (a['size'][0] + b['size'][0]) / 2)
    gy = max(0.0, abs(a['centre'][1] - b['centre'][1]) - (a['size'][1] + b['size'][1]) / 2)
    return math.hypot(gx, gy)


def long_axis(points):
    """The direction (unit x, y) a group of feet spreads along most, and how many times more than across (from the
    spread of the feet: the principal axis)."""
    n = len(points)
    mx, my = sum(p[0] for p in points) / n, sum(p[1] for p in points) / n
    sxx = sum((p[0] - mx) ** 2 for p in points) / n
    syy = sum((p[1] - my) ** 2 for p in points) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points) / n
    angle = 0.5 * math.atan2(2 * sxy, sxx - syy)
    axis = (math.cos(angle), math.sin(angle))
    along = sum(((p[0] - mx) * axis[0] + (p[1] - my) * axis[1]) ** 2 for p in points) / n
    across = sum((-(p[0] - mx) * axis[1] + (p[1] - my) * axis[0]) ** 2 for p in points) / n
    return axis, math.sqrt(along / across) if across > 1e-12 else float('inf')


def visible_share(box, front, cells):
    """The share of a box not covered by the boxes in front, on a cells x cells grid over the box."""
    l, t, r, b = box
    if r <= l or b <= t:
        return 0.0
    seen = 0
    for i in range(cells):
        x = l + (i + 0.5) * (r - l) / cells
        for j in range(cells):
            y = t + (j + 0.5) * (b - t) / cells
            if not any(f[0] <= x <= f[2] and f[1] <= y <= f[3] for f in front):
                seen += 1
    return seen / (cells * cells)


def ray(camera, across, down):
    """The direction through a spot of the frame (across, down shares)."""
    width, height = camera['frame']
    f = camera['focal']
    x = (across - 0.5) * width / f
    y = (0.5 - down) * height / f
    return g.add(g.add(camera['forward'], g.scale(camera['right'], x)), g.scale(camera['up'], y))


def hit_floor(origin, direction, floor_z, reference, slope, camera):
    """Where a ray meets the floor plane (height floor_z under the reference spot, rising `slope` along the camera's view),
    or None if it never does (it looks up into the sky or the far buildings)."""
    ahead = (camera['forward'][0], camera['forward'][1])
    n = math.hypot(*ahead)
    ahead = (ahead[0] / n, ahead[1] / n)
    # plane: z = floor_z + slope * (ahead . (p - reference)) ; solve origin + s d on it
    base = origin[2] - floor_z - slope * (ahead[0] * (origin[0] - reference[0]) + ahead[1] * (origin[1] - reference[1]))
    rate = direction[2] - slope * (ahead[0] * direction[0] + ahead[1] * direction[1])
    if rate >= -1e-9:
        return None
    s = -base / rate
    return g.add(origin, g.scale(direction, s))


def ground_at_bottom(camera, floor_z, slope, frame):
    """The point of the floor that lands on the frame's bottom edge, in the middle."""
    return hit_floor(camera['position'], ray(camera, 0.5, 1.0), floor_z, camera['position'], slope, camera)


# ------------------------------------------------------------------------------------------------ the report
SYMBOL = {'pass': 'ok', 'fail': 'FAIL', 'look': 'look', 'known': 'known', 'info': 'info', 'off': 'off'}


def report_lines(result):
    lines = [f'Shot {result["name"]} ({" + ".join(result["kind_of_shot"])}): subject {result["subject"]}'
             + (f' on {result["support"]}' if result['support'] else '') + f'; story {", ".join(result["story"]) or "none"}.',
             f'{"Planned" if result["planned"] else "Judged"}: ' + ' '.join(result['steps'])]
    cam = result['camera']
    met = result.get('meeting_point')
    lines.append(f'Camera: composed spot {cam["composed"]}, turned {cam["turn_degrees"]} degrees, eye {cam["eye_above_floor_metres"]} m above {cam["floor"]}'
                 + (f'; plate spot {cam["plate"]}' if cam['plate'] else '; no slide')
                 + (f'; the lines meet {met["across"]:.3f} across, {met["down"]:.3f} down.' if met else '.'))
    counts = result['counts']
    lines.append(f'Verdict: {result["verdict"].upper()} ({", ".join(f"{n} {SYMBOL.get(k, k)}" for k, n in sorted(counts.items()))}). '
                 '"look" = an estimate from boxes near its limit, or a judgement: confirm with the shot checker on the render.')
    order = {'fail': 0, 'known': 1, 'look': 2, 'pass': 3, 'info': 4, 'off': 5}
    for c in sorted(result['checks'], key=lambda c: order.get(c['verdict'], 9)):
        mark = SYMBOL.get(c['verdict'], c['verdict'])
        text = f'  [{mark}] {c["rule"]}: {c["about"]}'
        if c.get('estimate'):
            text += ' (estimate)'
        lines.append(text)
        if c.get('fix') and c['verdict'] in ('fail', 'look'):
            lines.append(f'         fix: {c["fix"]}')
        if c.get('accepted'):
            a = c['accepted']
            lines.append(f'         accepted ({a.get("who")}, {a.get("date")}): {a.get("reason")}')
    return lines


# ------------------------------------------------------------------------------------------------ command line
def parse_point(text):
    return g.parse_point(text) if text else None


def load_json(path):
    with open(path) as handle:
        return json.load(handle)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Plans a shot\'s camera, slide, plate and people from place facts and predicts what the '
                                                 'shot checker will measure (see the note at the top of this file).')
    parser.add_argument('--place-facts', help='the place facts file (default: the shot list\'s "place_facts")')
    parser.add_argument('--shots', help='a shot list (JSON; format in the note at the top of this file)')
    parser.add_argument('--shot', nargs='*', help='only these shots of the list')
    parser.add_argument('--view', help='judge (or with --plan, plan) this view of the place facts, without a shot list')
    parser.add_argument('--plan', action='store_true', help='with --view: plan the camera afresh instead of judging the built one')
    parser.add_argument('--at', help='with --view or one --shot: judge the camera at this composed spot x,y,z instead')
    parser.add_argument('--turn', type=float, help='with --at: the turn in degrees (default: the view\'s)')
    parser.add_argument('--plate-at', help='with --at: the slide\'s start x,y,z (default: no slide)')
    parser.add_argument('--count-ground', action='store_true', help='count the painted ground at the frame\'s bottom edge in the slide check')
    parser.add_argument('--strict', action='store_true', help='exit 1 when a shot has a failure that is not accepted')
    add_output_options(parser)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    shots_file = load_json(args.shots) if args.shots else {}
    facts_path = args.place_facts or (os.path.join(os.path.dirname(os.path.abspath(args.shots)), shots_file['place_facts'])
                                      if shots_file.get('place_facts') else None)
    if not facts_path:
        parser.error('give --place-facts (or a shot list with "place_facts")')
    facts = load_json(facts_path)
    views = {v['name']: v for v in facts.get('views', [])}
    if args.view:
        if args.view not in views:
            raise SystemExit(f'plan_shot: no view "{args.view}" in {facts_path} (views: {", ".join(views)})')
        view = views[args.view]
        painted = [p['name'] for p in view.get('painted_points', []) if '(derived)' not in p['name'] and p['name'] != view['subject']['name']]
        known_things = {p['name'] for p in facts.get('props', [])} | {f['name'] for f in facts.get('figures', [])}
        spec = {'name': args.view, 'view': args.view, 'subject': view['subject']['name'], 'camera': {'plan': args.plan},
                'story': [n for n in painted if n in known_things]}
        roles = {p['name']: p.get('role') for p in facts.get('props', []) if p.get('role')}
        if any(r in ('support', 'story', 'work') for r in roles.values()):   # the place facts say each prop's part: use it
            spec['support'] = next((n for n, r in roles.items() if r == 'support'), None)
            spec['story'] = [n for n, r in roles.items() if r in ('story', 'support')]
            spec['work'] = [n for n, r in roles.items() if r == 'work']
        shots = [spec]
    else:
        if not args.shots:
            parser.error('give --shots FILE, or --view NAME')
        shots = shots_file.get('shots', [])
        if args.shot:
            shots = [s for s in shots if s.get('name') in args.shot]
            if not shots:
                raise SystemExit(f'plan_shot: none of {args.shot} is in the shot list')
    results, lines = [], []
    try:
        for spec in shots:
            name = spec.get('name') or spec.get('view') or 'shot'
            view = views.get(spec.get('view') or name)
            place = Place(facts, settings, spec)
            frame = Frame(settings, facts)
            shot = Shot(name, spec, place, settings, frame, view, args.count_ground)
            result = shot.run(parse_point(args.at), args.turn, parse_point(args.plate_at))
            result['assumptions'] = place.notes + [f'{n}: {t["how"]}' for n, t in place.things.items()
                                                   if n in [shot.subject, shot.support] + shot.story + shot.work + shot.fill and n and t.get('how')]
            results.append(result)
            lines += report_lines(result) + ['  Assumed: ' + '; '.join(result['assumptions'])] + ['']
    except MissingSetting as problem:
        raise SystemExit(f'plan_shot: {problem}')
    verdicts = [r['verdict'] for r in results]
    summary = {'place_facts': facts_path, 'shots': results, 'verdict': 'fail' if 'fail' in verdicts else 'look' if 'look' in verdicts else 'pass'}
    finish('plan_shot', summary, lines, settings, args)
    if args.strict and 'fail' in verdicts:
        sys.exit(1)
    return summary


if __name__ == '__main__':
    sys.exit(run_main(main, 'plan_shot'))
