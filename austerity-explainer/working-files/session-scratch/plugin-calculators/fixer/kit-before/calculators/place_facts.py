"""What this does: checks a place facts file (the standard facts every place's assemble script writes, described by
place_facts_schema.json) and builds one from the files a place already has, so every calculator can read the same names
for any place: its views (camera spots, turn, lenses, slide, subject, kind of shot), signs, emitters (chimney mouths,
fires), figures, lights, landmark tops, support surfaces (ground, pavement, counter, floor) and the "accepted" list
(rule, view, reason, who, date) of exceptions the project chose to keep.

Use:
  python3 place_facts.py check FILE [FILE ...]           the schema, plus sense checks (kinds of shot exist, accepted
                                                          entries name real views, directions have length 1 ...); exit 1 on any problem
  python3 place_facts.py from-works --shot works-shot.json --cameras FOLDER --checks FOLDER [--facts F ...] --out FILE
  python3 place_facts.py from-notice-corner --shot notice-corner-shot.json --camera notice-corner-camera.json
                                            --check shot-check.json --facts facts.json [--paintings P] --out FILE
  python3 place_facts.py from-people-test --shot people-test-shot.json --camera people-test-camera.json
                                          --check shot-check.json [--paintings P] --out FILE
  python3 place_facts.py from-shot-facts --facts facts.json --check shot-check.json --place NAME --view NAME
                                         --kind interior [--kind ...] --out FILE      (any place measured by shot_facts.py)
Each converter prints what it filled in, what it had to assume (marked in the file as "assumed" or "derived"), and
which film-settings.json values it used. A new place's assemble script should write this file itself.
"""
import argparse
import datetime
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings, MissingSetting  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402
import frame_geometry as geometry  # noqa: E402

SCHEMA_PATH = os.path.join(HERE, 'place_facts_schema.json')


# ------------------------------------------------------------------------------------------------ schema checking
def load_schema(path=SCHEMA_PATH):
    with open(path) as handle:
        return json.load(handle)


def resolve(schema, root):
    while isinstance(schema, dict) and '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/'):
            raise ValueError(f'only local references are supported: {ref}')
        node = root
        for part in ref[2:].split('/'):
            node = node[part]
        schema = node
    return schema


TYPES = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}


def type_matches(value, name):
    if name == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def validate(value, schema, root=None, where='file'):
    """The JSON Schema subset place_facts_schema.json uses (type, required, properties, additionalProperties, items,
    minItems, maxItems, enum, const, minimum, maximum, minLength, pattern, anyOf, local $ref). Returns plain problems."""
    root = root if root is not None else schema
    schema = resolve(schema, root)
    problems = []
    if 'anyOf' in schema:
        tries = [validate(value, option, root, where) for option in schema['anyOf']]
        if all(tries):
            problems.append(f'{where}: matches none of the allowed forms ({"; ".join(t[0] for t in tries)})')
        return problems
    wanted = schema.get('type')
    if wanted:
        names = wanted if isinstance(wanted, list) else [wanted]
        if not any(type_matches(value, n) for n in names):
            return [f'{where}: should be {" or ".join(names)}, is {type(value).__name__} ({json.dumps(value)[:60]})']
    if 'const' in schema and value != schema['const']:
        problems.append(f'{where}: should be {json.dumps(schema["const"])}')
    if 'enum' in schema and value not in schema['enum']:
        problems.append(f'{where}: "{value}" is not one of {", ".join(map(str, schema["enum"]))}')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'minimum' in schema and value < schema['minimum']:
            problems.append(f'{where}: {value} is below {schema["minimum"]}')
        if 'maximum' in schema and value > schema['maximum']:
            problems.append(f'{where}: {value} is above {schema["maximum"]}')
    if isinstance(value, str):
        if 'minLength' in schema and len(value) < schema['minLength']:
            problems.append(f'{where}: is empty')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            problems.append(f'{where}: "{value}" does not match {schema["pattern"]}')
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                problems.append(f'{where}: missing "{key}"')
        properties = schema.get('properties', {})
        extra = schema.get('additionalProperties', True)
        for key, child in value.items():
            if key in properties:
                problems += validate(child, properties[key], root, f'{where}.{key}')
            elif extra is False:
                problems.append(f'{where}: "{key}" is not allowed')
            elif isinstance(extra, dict):
                problems += validate(child, extra, root, f'{where}.{key}')
    if isinstance(value, list):
        if 'minItems' in schema and len(value) < schema['minItems']:
            problems.append(f'{where}: needs at least {schema["minItems"]} item(s), has {len(value)}')
        if 'maxItems' in schema and len(value) > schema['maxItems']:
            problems.append(f'{where}: at most {schema["maxItems"]} item(s), has {len(value)}')
        if 'items' in schema:
            for k, child in enumerate(value):
                label = child.get('name') if isinstance(child, dict) and isinstance(child.get('name'), str) else k
                problems += validate(child, schema['items'], root, f'{where}[{label}]')
    return problems


def sense_problems(facts, settings):
    """Checks a schema cannot express: names that must exist, directions of length 1, slides that match the spots."""
    problems = []
    try:
        profiles = settings.node('shot_kind_profiles')
        known_kinds = {k for k, v in profiles.items() if isinstance(v, dict) and 'rules' in v}
    except MissingSetting as problem:
        return [str(problem)]
    views = {v.get('name') for v in facts.get('views', []) if isinstance(v, dict)}
    for view in facts.get('views', []):
        name = view.get('name')
        for kind in view.get('kind_of_shot', []):
            if kind not in known_kinds:
                problems.append(f'view {name}: kind of shot "{kind}" is not in film-settings.json (known: {", ".join(sorted(known_kinds))})')
        camera = view.get('camera', {})
        if not camera.get('composed') and not camera.get('plate'):
            problems.append(f'view {name}: the camera has neither a composed nor a plate spot')
        slide = view.get('slide')
        if slide and camera.get('composed') and geometry.length(geometry.subtract(slide['end'], camera['composed'])) > 0.01:
            problems.append(f'view {name}: the slide ends at {slide["end"]}, not at the composed spot {camera["composed"]}')
        if slide and slide.get('length_metres') is not None:
            measured = geometry.length(geometry.subtract(slide['end'], slide['start']))
            if abs(measured - slide['length_metres']) > 0.01:
                problems.append(f'view {name}: slide length {slide["length_metres"]} m, but start to end is {measured:.3f} m')
    for sign in facts.get('signs', []):
        n = geometry.length(sign.get('normal', [0, 0, 0]))
        if abs(n - 1) > 0.01:
            problems.append(f'sign {sign.get("name")}: its normal has length {n:.3f}, not 1')
    for figure in facts.get('figures', []):
        n = geometry.length(figure.get('facing', [0, 0, 0]))
        if abs(n - 1) > 0.01:
            problems.append(f'figure {figure.get("name")}: its facing has length {n:.3f}, not 1')
    for k, entry in enumerate(facts.get('accepted', [])):
        if entry.get('view') not in views and entry.get('view') != 'all':
            problems.append(f'accepted[{k}] ({entry.get("rule")}): view "{entry.get("view")}" is not one of the place\'s views ({", ".join(sorted(views))})')
        try:
            datetime.date.fromisoformat(entry.get('date', ''))
        except ValueError:
            problems.append(f'accepted[{k}] ({entry.get("rule")}): "{entry.get("date")}" is not a date (YYYY-MM-DD)')
    if not facts.get('support_surfaces'):
        problems.append('no support surfaces: the reach and eye sums need the height of the surface things stand on')
    names = [s.get('name') for s in facts.get('signs', [])] + [f.get('name') for f in facts.get('figures', [])]
    repeated = sorted({n for n in names if names.count(n) > 1})
    if repeated:
        problems.append(f'names used twice: {", ".join(repeated)}')
    return problems


def check_file(path, settings, schema=None):
    with open(path) as handle:
        facts = json.load(handle)
    schema = schema or load_schema()
    return validate(facts, schema) + sense_problems(facts, settings)


# ------------------------------------------------------------------------------------------------ helpers for converters
def read(path):
    with open(path) as handle:
        return json.load(handle)


def facing_from_turn(turn_degrees):
    """A figure model at turn 0 faces +y (its back to a camera looking up +y); + turns it to the left."""
    t = math.radians(turn_degrees)
    return [round(-math.sin(t), 6), round(math.cos(t), 6), 0.0]


def front_from_turn(turn_degrees):
    """A lettered face that looks -y at turn 0, + turning it toward +x (the drums' stencils, notice-paper.glb)."""
    t = math.radians(turn_degrees)
    return [round(math.sin(t), 6), round(-math.cos(t), 6), 0.0]


def rounded(v, digits=4):
    return [round(float(x), digits) for x in v] if v is not None else None


def ground_at_bottom_edge(camera, floor_height):
    """The point on a level floor that lands on the frame's bottom edge (the nearest painted ground in view)."""
    eye = camera['position'][2] - floor_height
    meeting = geometry.project_direction(camera, [camera['forward'][0], camera['forward'][1], 0.0])
    depth = geometry.reach_distance(1.0, eye, meeting['down'] if meeting else 0.5, camera['vertical_fov_degrees'], camera['frame'][1])
    if depth is None:
        return None
    level = geometry.normalise([camera['forward'][0], camera['forward'][1], 0.0])
    horizontal = depth / geometry.dot(level, camera['forward']) if geometry.dot(level, camera['forward']) > 0 else depth
    point = geometry.add(camera['position'], geometry.scale(level, horizontal))
    point[2] = floor_height
    return rounded(point, 3)


def lights_from_facts(paths, labels=None):
    """Lights measured by shot_facts.py in one or more facts files, once each (name, kind, place, watts, colour, aim,
    reach, linking), noting which files show them."""
    found = {}
    for k, path in enumerate(paths or []):
        label = (labels or [])[k] if labels and k < len(labels) else os.path.basename(os.path.dirname(os.path.dirname(path))) or path
        for light in read(path).get('lights', []):
            entry = found.setdefault(light['name'], {
                'name': light['name'], 'kind': light.get('kind'), 'at': rounded(light['at'], 3), 'target': None,
                'aim': rounded(light['aim'], 4) if light.get('aim') else None, 'watts': light.get('energy'),
                'colour': light.get('colour') or [1.0, 1.0, 1.0], 'in_states': []})
            for key, name in (('spot_degrees', 'cone_degrees'), ('reach', 'reach_metres')):
                if light.get(key) is not None and name not in entry:
                    entry[name] = light[key]
            for key in ('reaches_only', 'skips'):   # light linking: what it reaches (or skips) in any of the states measured
                if light.get(key) is not None:
                    entry[key] = sorted(set(entry.get(key, [])) | set(light[key]))
            if label not in entry['in_states']:
                entry['in_states'].append(label)
    return list(found.values())


def base_facts(place, about, made_from):
    return {'place_facts_version': 1, 'place': place, 'about': about, 'made_by': f'kit/calculators/place_facts.py ({place} converter)',
            'made_from': made_from, 'interior': False, 'views': [], 'signs': [], 'emitters': [], 'figures': [], 'lights': [],
            'landmark_tops': [], 'support_surfaces': [], 'props': [], 'accepted': []}


# ------------------------------------------------------------------------------------------------ the Works
WORKS_KINDS = {
    # which shot-kind profiles each Works view uses, and why (the round 5 final checks, working files redesign/round5-set/checks)
    'w1': (['crowd', 'dark_subject'], 'No. 1\'s shut iron gate with its seven men gathered in front'),
    'w2': (['crowd', 'dark_subject'], 'No. 2\'s open gateway (a dark opening); its slowed state holds eight waiting men'),
    'w3': (['overview', 'crowd', 'dark_subject'], 'both gates from an upstairs window, the crowd 29-30 m away'),
    'w4': (['crowd'], 'No. 2\'s gate from inside its yard, the eight men outside (being reworked in round 5)'),
}
WORKS_DRUM_TURNS = {'no-1-drum-petrol': 12.0, 'no-1-drum-diesel': 8.0, 'no-2-drum-petrol': -12.0, 'no-2-drum-diesel': -8.0}   # assemble_works.py DRUM_SPOTS
WORKS_LETTERS = {'no-1-board': 0.266, 'no-2-board': 0.25, 'bank sign': 0.305, 'brass plate': 0.065, 'petrol': 0.097, 'diesel': 0.106,
                 'crate': 0.063, 'wages': 0.018}   # props/index.json letter_height_metres
DRUM_HEIGHT, DRUM_DIAMETER = 0.88, 0.607   # props/index.json steel drums


def from_works(args, settings):
    shot = read(args.shot)
    made_from = [args.shot]
    facts = base_facts('works', 'The Works (chapter 2, plan 34 part 1 "A"): a lane leading to two factories\' gates, No. 1 (left, quiet, '
                       'its men waiting) and No. 2 (right, flat out). Converted from works-shot.json and the camera files of round 5. '
                       'The round 5 final checks list 13 to 29 problems per view that nobody has accepted or fixed yet (skeptic, '
                       'log 35); the shot-kind profiles cover the systematic ones, the rest stay open, so "accepted" is empty.', made_from)
    lane = shot['lane']
    facts['lines'] = {'lane': [0, 1, 0], 'level': [0, 1, 0]}
    facts['lines_key'] = 'lane'
    facts['painting'] = {'plate_size': [settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels')],
                         'returned_size': None, 'source': 'no painting yet (the plates stand in); film-settings.json frame.painting_returned_size_pixels applies'}
    notes = []
    checks = {}
    for view in shot['views']:
        for suffix in ('', '-working', '-slowed'):
            path = os.path.join(args.checks, f'works-{view}{suffix}-shot-check.json') if args.checks else None
            if path and os.path.exists(path):
                checks.setdefault(view, read(path))
                made_from.append(path)
    film_fov, plate_fov = shot.get('film_fov_degrees'), shot.get('plate_fov_degrees')
    for name, view in shot['views'].items():
        camera_path = os.path.join(args.cameras, view['camera_file'])
        made_from.append(camera_path)
        projector = read(camera_path)
        plate_camera = geometry.camera_from_blender_quaternion(projector['blender']['location'], projector['blender']['rotation_quaternion_wxyz'],
                                                               plate_fov, 1080, 1920)
        angles = geometry.camera_angles(plate_camera)
        kinds, why = WORKS_KINDS.get(name, (['still_life'], 'not listed'))
        spot = view['composed'] or view['plate']
        floor = round(spot[2] - view['eye_height_metres'], 3)
        entry = {
            'name': name, 'about': view['about'], 'kind_of_shot': kinds, 'kind_of_shot_note': why,
            'camera': {'composed': view['composed'], 'plate': view['plate'], 'turn_degrees': round(angles['turn_degrees'], 4),
                       'tilt_degrees': round(angles['tilt_degrees'], 4), 'roll_degrees': round(angles['roll_degrees'], 4),
                       'film_vertical_fov_degrees': film_fov, 'plate_vertical_fov_degrees': plate_fov,
                       'eye_height_metres': view['eye_height_metres'], 'floor_height': floor, 'stands_on': view['stands_on'],
                       'camera_file': view['camera_file']},
            'slide': None,
            'subject': {'name': checks.get(name, {}).get('subject', 'gate'), 'point': view['subject'], 'dark': name in ('w1', 'w2', 'w3'),
                        'opening': name == 'w2'},
            'check_file': f'works-{name}-shot-check.json',
            'states': sorted({p['state'] for p in shot.get('plates', {}).values() if p['view'] == name}),
        }
        if view['composed'] and view['plate'] and geometry.length(geometry.subtract(view['composed'], view['plate'])) > 0.001:
            entry['slide'] = {'start': view['plate'], 'end': view['composed'],
                              'length_metres': round(geometry.length(geometry.subtract(view['composed'], view['plate'])), 4)}
        film_camera = geometry.camera_from_turn(spot, angles['turn_degrees'], angles['tilt_degrees'], 0, film_fov, 1080, 1920)
        painted = [{'name': 'brazier', 'point': [shot['brazier'][0], shot['brazier'][1], shot['coals_z']]}]
        for man in shot.get('men_at_no_1', []) + shot.get('men_at_no_2', []):
            painted.append({'name': man['name'], 'point': man['feet']})
        bottom = ground_at_bottom_edge(film_camera, floor)
        if bottom:
            painted.append({'name': 'ground at the frame\'s bottom edge (derived)', 'point': bottom})
        entry['painted_points'] = painted
        facts['views'].append(entry)
    # signs (letter heights from props/index.json; the drums turned as assemble_works.py DRUM_SPOTS)
    boards = shot['boards']
    facts['signs'] += [
        {'name': 'no-1 board', 'centre': boards['no-1-board'], 'normal': [0.0, -1.0, 0.0], 'letter_height_metres': WORKS_LETTERS['no-1-board'],
         'words': 'No. 1', 'must_read': True, 'both_faces': False},
        {'name': 'no-2 board', 'centre': boards['no-2-board'], 'normal': [0.0, -1.0, 0.0], 'letter_height_metres': WORKS_LETTERS['no-2-board'],
         'words': 'No. 2', 'must_read': True, 'both_faces': False, 'note': 'round 4 critic: its back is blank from inside the yard (W4)'},
        {'name': 'bank sign', 'centre': shot['bank']['sign'], 'normal': [0.0, -1.0, 0.0], 'letter_height_metres': WORKS_LETTERS['bank sign'],
         'words': 'BANK', 'must_read': True, 'both_faces': True, 'dim_until_named': settings.value('lettering.unnamed_sign_dim'),
         'note': 'a hanging sign square to the house front, lettered on both faces; dimmed until page 9 says "bank" (works-effects.js)'},
        {'name': 'bank brass plate', 'centre': shot['bank']['brass_plate'], 'normal': [1.0, 0.0, 0.0], 'letter_height_metres': WORKS_LETTERS['brass plate'],
         'words': 'BANK', 'must_read': False},
    ]
    for drum, at in shot['drums'].items():
        word = 'PETROL' if 'petrol' in drum else 'DIESEL'
        facts['signs'].append({'name': drum, 'centre': rounded([at[0], at[1], at[2] + DRUM_HEIGHT / 2], 3),
                               'normal': front_from_turn(WORKS_DRUM_TURNS[drum]), 'letter_height_metres': WORKS_LETTERS[word.lower()],
                               'words': word, 'must_read': True, 'wraps_degrees': settings.value('lettering.stencil_wrap_degrees'),
                               'note': f'stencil turned {WORKS_DRUM_TURNS[drum]:+.0f} degrees toward the gate view (assemble_works.py DRUM_SPOTS)'})
    if shot.get('no-2-crates'):
        facts['signs'].append({'name': 'no-2 crates', 'centre': shot['no-2-crates'], 'normal': [0.0, -1.0, 0.0], 'letter_height_metres': WORKS_LETTERS['crate'],
                               'words': 'THIS WAY UP', 'must_read': True, 'both_faces': True, 'note': 'normal assumed (facing down the lane)'})
    if shot.get('w4', {}).get('mug_and_wages'):
        facts['signs'].append({'name': 'wages envelope', 'centre': shot['w4']['mug_and_wages'], 'normal': [0.0, 1.0, 0.0],
                               'letter_height_metres': WORKS_LETTERS['wages'], 'words': 'WAGES', 'must_read': False,
                               'note': 'turned to face W4\'s camera (assumed); about 5 px at 6 m: the typed words do the reading'})
    notes.append('crate and envelope normals are assumed; every other sign\'s normal comes from the build')
    # emitters, lights, landmarks
    chimney_radius = {'no-1-chimney-top': 0.92, 'no-2-chimney-a-top': 0.68, 'no-2-chimney-b-top': 0.68}   # round 2 factories (1.84 m round, 1.36 m square tops)
    for name, top in shot['chimney_tops'].items():
        facts['emitters'].append({'name': name.replace('-top', ''), 'kind': 'chimney mouth', 'at': top, 'radius_metres': chimney_radius.get(name, 0.7)})
        facts['landmark_tops'].append({'name': name, 'top': top, 'identifies': 'No. 1' if name.startswith('no-1') else 'No. 2'})
    if shot.get('no-2-tank-top'):
        facts['landmark_tops'].append({'name': 'no-2-tank-top', 'top': shot['no-2-tank-top'], 'identifies': 'No. 2'})
    facts['emitters'].append({'name': 'brazier fire', 'kind': 'fire', 'at': [shot['brazier'][0], shot['brazier'][1], shot['coals_z']], 'radius_metres': 0.3})
    for name, at in shot.get('gate_lamps', {}).items():
        facts['emitters'].append({'name': f'{name} gate lamp', 'kind': 'lamp', 'at': at})
    facts['emitters'].append({'name': 'lantern', 'kind': 'lamp', 'at': shot['lantern']})
    measured = lights_from_facts(args.facts, args.facts_labels)
    made_from += list(args.facts or [])
    if measured:
        facts['lights'] = measured
    else:
        positions = dict(shot.get('lights', {}))
        positions.update({'brazier_light': shot['fire_light'], 'lantern_light': shot['lantern_light']})
        facts['lights'] = [{'name': n, 'at': at, 'target': None, 'watts': None, 'note': 'watts not in works-shot.json: give --facts'} for n, at in positions.items()]
        notes.append('lights have no watts: give the round 5 check facts (--facts) to fill them')
    # figures
    default_height = settings.value('people.figure_height_metres')
    for group, people in (('men at No. 1', shot.get('men_at_no_1', [])), ('men at No. 2', shot.get('men_at_no_2', []))):
        for person in people:
            facts['figures'].append({'name': person['name'], 'feet': person['feet'], 'turn_degrees': person['turn_degrees'],
                                     'facing': facing_from_turn(person['turn_degrees']), 'height_metres': person['height_metres'],
                                     'height_from': 'measured (works-shot.json)', 'figure': person['figure'], 'group': group})
    for side, people in shot.get('workers', {}).items():
        if not isinstance(people, list):
            continue
        for person in people:
            facts['figures'].append({'name': person['name'], 'feet': person['feet'], 'turn_degrees': person['turn_degrees'],
                                     'facing': facing_from_turn(person['turn_degrees']), 'height_metres': default_height,
                                     'height_from': 'default (film-settings.json people.figure_height_metres)', 'figure': person['figure'],
                                     'group': f'workers inside {side}'})
    # support surfaces (the pavement's height from W1's composed spot: camera z minus its eye height)
    w1 = shot['views'].get('w1', next(iter(shot['views'].values())))
    pavement = round((w1['composed'] or w1['plate'])[2] - w1['eye_height_metres'], 3)
    kerb, front = lane['kerb_face_x'], lane['house_front_x']
    facts['support_surfaces'] = [
        {'name': 'carriageway', 'kind': 'road', 'height': 0.0, 'x_range': [-kerb, kerb], 'y_range': [lane['cross_street']['north_kerb_y'], lane['works_wall_face_y']],
         'height_from': 'Blender ground 0 (build_street.py)'},
        {'name': 'left pavement', 'kind': 'pavement', 'height': pavement, 'x_range': [-front, -kerb], 'y_range': [0.0, lane['works_wall_face_y']],
         'height_from': 'W1 composed camera z minus its eye height (derived)'},
        {'name': 'right pavement', 'kind': 'pavement', 'height': pavement, 'x_range': [kerb, front], 'y_range': [0.0, lane['works_wall_face_y']],
         'height_from': 'as left pavement (derived)'},
    ]
    w4 = shot['views'].get('w4')
    if w4:
        facts['support_surfaces'].append({'name': 'No. 2\'s yard', 'kind': 'ground', 'height': round((w4['composed'] or w4['plate'])[2] - w4['eye_height_metres'], 3),
                                          'height_from': 'W4 camera z minus its eye height (derived)'})
    # props (positions; roles change from view to view, so they live in the check files)
    for name in ('brazier', 'lantern', 'lunch_tin', 'handcart', 'no-2-crates'):
        if shot.get(name):
            facts['props'].append({'name': name.replace('_', ' '), 'at': shot[name]})
    for name, at in shot['drums'].items():
        facts['props'].append({'name': name, 'at': at, 'size': [DRUM_DIAMETER, DRUM_DIAMETER, DRUM_HEIGHT], 'turn_degrees': WORKS_DRUM_TURNS[name]})
    facts['states'] = shot.get('states', {})
    facts['assumptions'] = notes
    return facts


# ------------------------------------------------------------------------------------------------ the notice corner
NOTICE_LETTER_PIXELS, NOTICE_DEPTH = 11, 4.88   # log 32 "left for later": PITS WILL BE CLOSED 11 px at the composed spot (facts depth 4.88 m)


def from_notice_corner(args, settings):
    shot, check = read(args.shot), read(args.check)
    measured = read(args.facts) if args.facts else {}
    made_from = [args.shot, args.camera, args.check] + ([args.facts] if args.facts else []) + ([args.paintings] if args.paintings else [])
    facts = base_facts('notice-corner', 'The notice corner (logs 31-32): a lock-out notice on a board in a pit-village street at dusk, '
                       'a fire drum, a chair with a lantern, a pail; the camera slides 1.5 m toward it without turning. Kept by the user '
                       '(decision 38: "Wow that\'s incredible. Yes keep it.").', made_from)
    facts['lines'] = check['lines']
    facts['lines_key'] = check.get('lines_key', 'street')
    paintings = read(args.paintings) if args.paintings else {}
    returned = next((p['returned_size'] for p in paintings.get('paintings', []) if p.get('returned_size')), None)
    facts['painting'] = {'plate_size': [settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels')],
                         'returned_size': returned, 'source': os.path.basename(args.paintings) if args.paintings else 'film-settings.json'}
    camera_measured = measured.get('camera', {})
    end, start = shot['camera_end'], shot['camera_start']
    eye = camera_measured.get('eye_height') or settings.value('camera.eye_height_default_metres')
    floor = round(end[2] - eye, 4)
    film = geometry.camera_from_turn(end, shot['yaw_degrees'], 0, 0, shot['film_fov_degrees'], 1080, 1920)
    groups = measured.get('groups', {})
    painted = [{'name': g, 'point': groups[g]['centre']} for g in ('pail', 'chair', 'drum', 'lantern', 'board', 'notice') if g in groups]
    slope = facts['lines'][facts['lines_key']][2]
    facts['views'].append({
        'name': 'end', 'about': 'the composed spot at the end of the slide', 'kind_of_shot': ['still_life'],
        'camera': {'composed': end, 'plate': start, 'turn_degrees': shot['yaw_degrees'], 'tilt_degrees': 0.0, 'roll_degrees': 0.0,
                   'film_vertical_fov_degrees': shot['film_fov_degrees'], 'plate_vertical_fov_degrees': shot['plate_fov_degrees'],
                   'eye_height_metres': eye, 'floor_height': floor, 'stands_on': 'the pavement', 'camera_file': os.path.basename(args.camera)},
        'slide': {'start': start, 'end': end, 'length_metres': round(geometry.length(geometry.subtract(end, start)), 4)},
        'subject': {'name': check['subject'], 'point': shot['notice_centre']},
        'painted_points': painted,
        'check_file': 'examples/notice-corner/shot-check.json',
    })
    board = shot['notice_centre']
    facing = math.degrees(math.atan2(end[0] - board[0], -(end[1] - board[1])))   # assemble_notice_corner.py line 109
    facts['signs'].append({'name': 'notice', 'centre': board, 'normal': front_from_turn(facing),
                           'letter_height_metres': round(NOTICE_LETTER_PIXELS * NOTICE_DEPTH / film['focal'], 4), 'words': 'PITS WILL BE CLOSED',
                           'must_read': True, 'note': 'letter height derived from the 11 px measured in log 32 at 4.88 m; the board is turned square '
                                                     'to the composed camera (assemble_notice_corner.py line 109)'})
    glow = shot.get('notice_glow', {})
    facts['emitters'] += [{'name': 'drum fire', 'kind': 'fire', 'at': [shot['drum'][0], shot['drum'][1], shot['coals_z']], 'radius_metres': 0.26},
                          {'name': 'lantern', 'kind': 'lamp', 'at': shot['lantern_light']},
                          {'name': 'corner lamp', 'kind': 'lamp', 'at': shot['corner_lamp_light']}]
    start_points = settings.value('light.starting_points.notice_corner')
    facts['lights'] = [
        {'name': 'fire light', 'kind': 'POINT', 'at': shot['fire_light'], 'target': None, 'watts': glow.get('fire_watts', start_points['fire_watts'])},
        {'name': 'notice glow', 'kind': 'SPOT', 'at': glow.get('at'), 'target': glow.get('aim_at'), 'watts': glow.get('watts'),
         'cone_degrees': glow.get('cone_degrees'), 'reach_metres': glow.get('reach'), 'reaches_only': ['notice', 'board']},
        {'name': 'lantern light', 'kind': 'POINT', 'at': shot['lantern_light'], 'target': None, 'watts': start_points['lantern_watts'],
         'skips': ['lantern'], 'note': 'watts from film-settings.json light.starting_points (assemble_notice_corner.py LANTERN_WATTS)'},
        {'name': 'corner lamp light', 'kind': 'POINT', 'at': shot['corner_lamp_light'], 'target': None, 'watts': start_points['corner_lamp_watts']},
    ]
    for g in ('winding wheels', 'chimney'):
        if g in groups:
            info = groups[g]
            facts['landmark_tops'].append({'name': f'{g} top', 'top': [info['centre'][0], info['centre'][1], info['top']], 'identifies': 'the colliery'})
    facts['support_surfaces'].append({'name': 'pavement', 'kind': 'pavement', 'height': floor, 'at': [end[0], end[1], floor], 'slope': [0.0, slope],
                                      'height_from': 'shot_facts eye height under the composed camera (derived)'})
    for g, support in check.get('stands_on', {}).items():
        top = measured.get('support_tops', {}).get(g, {}).get('top')
        if top is not None:
            facts['support_surfaces'].append({'name': f'{support} seat', 'kind': 'seat', 'height': top, 'at': groups[support]['centre'][:2] + [top],
                                              'height_from': 'shot_facts support_tops'})
    roles = {check['subject']: 'subject', check.get('support'): 'support'}
    roles.update({g: 'story' for g in check.get('story', []) if g not in roles})
    roles.update({g: 'work' for g in check.get('work', []) if g not in roles})
    for g, info in groups.items():
        facts['props'].append({'name': g, 'at': info['centre'], 'size': [info['width'], info['depth'], info['height']], 'role': roles.get(g, 'other')})
    kept = 'the user kept the shot: "Wow that\'s incredible. Yes keep it." (notes/Decisions.md, decision 38, log 32)'
    facts['accepted'] = [
        {'rule': 'rule6_lit_from_below', 'view': 'end', 'measured': 0.08, 'who': kept, 'date': '2026-10-14',
         'reason': 'the finished still measured 0.08 (needs 0.10); the film page lights the notice\'s own surface with a copy of the warm light and reached 0.23 (log 32)'},
        {'rule': 'rule10_quiet_side_weight', 'view': 'end', 'measured': 0.38, 'who': kept, 'date': '2026-10-14',
         'reason': 'the still\'s quiet side held 38% (aim 40-48%); the film page measured 46% (log 32)'},
        {'rule': 'rule8_bottom_left_share', 'view': 'end', 'measured': 0.021, 'who': kept + '; the gutter kept as a narrow lead-in line (log 32)', 'date': '2026-10-14',
         'reason': 'the painted end frame\'s gutter covered 2.1% of the bottom-left quarter (limit 1%): a thin lead-in line, not a dark lump'},
        {'rule': 'slide_magnification', 'view': 'end', 'measured': 1.45, 'who': kept, 'date': '2026-10-14',
         'reason': 'the pail comes 1.45 times nearer during the 1.5 m slide (the painting allows about 1.29); the slide was made before plan 34\'s limit (F13) and the user kept the film'},
    ]
    return facts


# ------------------------------------------------------------------------------------------------ the people test
def from_people_test(args, settings):
    shot, check = read(args.shot), read(args.check)
    made_from = [args.shot, args.camera, args.check] + ([args.paintings] if args.paintings else [])
    facts = base_facts('people-test', 'The people test (log 34): five working men round a brazier on the pit-village street, six small walkers '
                       'far up it, painted by fal to see how the painter treats figures. The camera holds still at the plate\'s spot.', made_from)
    facts['lines'] = check['lines']
    facts['lines_key'] = check.get('lines_key', 'street')
    paintings = read(args.paintings) if args.paintings else {}
    returned = next((p['returned_size'] for p in paintings.get('paintings', []) if p.get('returned_size')), None)
    facts['painting'] = {'plate_size': [settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels')],
                         'returned_size': returned, 'source': os.path.basename(args.paintings) if args.paintings else 'film-settings.json'}
    camera = shot['camera']
    eye = 1.81   # assemble_people_test.py EYE_HEIGHT
    floor = round(camera[2] - eye, 4)
    facts['views'].append({
        'name': 'still', 'about': 'the plate camera\'s spot, filmed with the film lens (no slide)', 'kind_of_shot': ['crowd'],
        'camera': {'composed': camera, 'plate': camera, 'turn_degrees': shot['yaw_degrees'], 'tilt_degrees': 0.0, 'roll_degrees': 0.0,
                   'film_vertical_fov_degrees': shot['film_fov_degrees'], 'plate_vertical_fov_degrees': shot['plate_fov_degrees'],
                   'eye_height_metres': eye, 'floor_height': floor, 'stands_on': 'the pavement', 'camera_file': os.path.basename(args.camera)},
        'slide': None,
        'subject': {'name': check['subject'], 'point': [shot['brazier'][0], shot['brazier'][1], shot['coals_z']]},
        'check_file': 'examples/people-test/shot-check.json',
    })
    for person in shot['figures']:
        facts['figures'].append({'name': person['name'], 'feet': person['feet'], 'turn_degrees': person['turn_degrees'],
                                 'facing': facing_from_turn(person['turn_degrees']), 'height_metres': person['height_metres'],
                                 'height_from': 'measured (people-test-shot.json)', 'figure': person['figure'],
                                 'group': 'walkers' if 'walker' in person['name'] else 'men at the brazier'})
    facts['emitters'] += [{'name': 'brazier fire', 'kind': 'fire', 'at': [shot['brazier'][0], shot['brazier'][1], shot['coals_z']], 'radius_metres': 0.26},
                          {'name': 'kerb lamp', 'kind': 'lamp', 'at': shot['kerb_lamp_light']}]
    facts['lights'] = [{'name': 'fire light', 'kind': 'POINT', 'at': shot['fire_light'], 'target': None, 'watts': None,
                        'note': 'watts not in people-test-shot.json'},
                       {'name': 'kerb lamp light', 'kind': 'POINT', 'at': shot['kerb_lamp_light'], 'target': None, 'watts': None,
                        'note': 'watts not in people-test-shot.json'}]
    slope = facts['lines'][facts['lines_key']][2]
    facts['support_surfaces'].append({'name': 'pavement', 'kind': 'pavement', 'height': floor, 'at': [camera[0], camera[1], floor], 'slope': [0.0, slope],
                                      'height_from': 'camera z minus assemble_people_test.py EYE_HEIGHT 1.81 (derived)'})
    facts['props'].append({'name': 'brazier', 'at': shot['brazier'], 'role': 'subject'})
    return facts


# ------------------------------------------------------------------------------------------------ any place measured by shot_facts.py
def from_shot_facts(args, settings):
    measured, check = read(args.facts), read(args.check)
    facts = base_facts(args.place, f'{args.place}, view {args.view}: converted from a shot_facts.py measurement and its check file '
                       '(a place without its own place facts yet). Sign letter heights and normals are not measured there: '
                       'normals are assumed to face the camera and letter heights are left empty.', [args.facts, args.check])
    kinds = args.kind or ['still_life']
    facts['interior'] = 'interior' in kinds
    facts['lines'] = check.get('lines', {'level': [0, 1, 0]})
    facts['lines_key'] = check.get('lines_key', next(iter(facts['lines'])))
    cam = measured['camera']
    eye = cam.get('eye_height') or settings.value('camera.eye_height_default_metres')
    floor = round(cam['at'][2] - eye, 4)
    camera = geometry.camera_from_turn(cam['at'], cam.get('turn_degrees', 0), cam.get('tilt_degrees', 0), cam.get('roll_degrees', 0),
                                       cam['vertical_fov_degrees'], *measured.get('size', [1080, 1920]))
    groups = measured['groups']
    subject = check.get('subject')
    facts['views'].append({
        'name': args.view, 'kind_of_shot': kinds,
        'camera': {'composed': cam['at'], 'plate': None, 'turn_degrees': cam.get('turn_degrees', 0.0), 'tilt_degrees': cam.get('tilt_degrees', 0.0),
                   'roll_degrees': cam.get('roll_degrees', 0.0), 'film_vertical_fov_degrees': cam['vertical_fov_degrees'],
                   'eye_height_metres': eye, 'floor_height': floor, 'stands_on': 'the floor' if facts['interior'] else 'the ground'},
        'slide': None,
        'subject': {'name': subject, 'point': groups[subject]['centre'] if subject in groups else cam['at']},
        'check_file': os.path.basename(args.check),
    })
    toward_camera = geometry.scale(camera['forward'], -1)
    for g in check.get('must_read', []):
        if g in groups:
            facts['signs'].append({'name': g, 'centre': groups[g]['centre'], 'normal': rounded(toward_camera, 6), 'letter_height_metres': None,
                                   'words': g, 'must_read': True, 'note': 'normal assumed to face the camera; letter height not measured'})
    facts['lights'] = lights_from_facts([args.facts], [args.view])
    facts['support_surfaces'].append({'name': 'floor' if facts['interior'] else 'ground', 'kind': 'floor' if facts['interior'] else 'ground',
                                      'height': floor, 'height_from': 'shot_facts eye height under the camera (derived)'})
    on_ground = set(check.get('on_ground', []))
    standing = check.get('story', []) + ([check['support']] if check.get('support') else ([subject] if subject else []))
    raised = {g: groups[g]['bottom'] for g in standing if g in groups and g not in on_ground and groups[g]['bottom'] > floor + 0.3}
    if raised:
        lowest = min(raised, key=raised.get)
        kind = 'counter' if facts['interior'] else 'other'
        facts['support_surfaces'].append({'name': 'story surface', 'kind': kind, 'height': round(raised[lowest], 3), 'interior': facts['interior'],
                                          'height_from': f'the lowest bottom of the {len(raised)} story things standing above the floor ({lowest}; '
                                                         f'derived from shot_facts, the others: '
                                                         f'{", ".join(f"{g} {b:.3f}" for g, b in raised.items() if g != lowest)})'})
    roles = {subject: 'subject', check.get('support'): 'support'}
    roles.update({g: 'story' for g in check.get('story', []) if g not in roles})
    roles.update({g: 'work' for g in check.get('work', []) if g not in roles})
    for g, info in groups.items():
        facts['props'].append({'name': g, 'at': info['centre'], 'size': [info['width'], info['depth'], info['height']], 'role': roles.get(g, 'other')})
    return facts


# ------------------------------------------------------------------------------------------------ command line
def summary_lines(facts, out):
    views = ', '.join(f'{v["name"]} ({" + ".join(v["kind_of_shot"])})' for v in facts['views'])
    lines = [f'Place facts for "{facts["place"]}"' + (f' written to {out}' if out else '') + '.',
             f'Views: {views}.',
             f'{len(facts["signs"])} signs, {len(facts["emitters"])} emitters, {len(facts["figures"])} figures, {len(facts["lights"])} lights, '
             f'{len(facts["landmark_tops"])} landmark tops, {len(facts["support_surfaces"])} support surfaces, {len(facts["accepted"])} accepted exceptions.']
    for note in facts.get('assumptions', []):
        lines.append(f'Assumed: {note}.')
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description='Checks or builds a place facts file (see the note at the top of this file).')
    commands = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(commands.add_parser('check', help='check place facts files against the schema and for sense'))
    p.add_argument('files', nargs='+')
    p = add_output_options(commands.add_parser('from-works', help='build the Works\' place facts'))
    p.add_argument('--shot', required=True)
    p.add_argument('--cameras', required=True, help='the folder holding works-camera-*.json')
    p.add_argument('--checks', help='the folder holding works-*-shot-check.json')
    p.add_argument('--facts', nargs='*', help='shot_facts facts.json files whose lights give watts and linking')
    p.add_argument('--facts-labels', nargs='*', help='a label for each facts file (default: its folder name)')
    p = add_output_options(commands.add_parser('from-notice-corner', help='build the notice corner\'s place facts'))
    for name in ('--shot', '--camera', '--check'):
        p.add_argument(name, required=True)
    p.add_argument('--facts')
    p.add_argument('--paintings')
    p = add_output_options(commands.add_parser('from-people-test', help='build the people test\'s place facts'))
    for name in ('--shot', '--camera', '--check'):
        p.add_argument(name, required=True)
    p.add_argument('--paintings')
    p = add_output_options(commands.add_parser('from-shot-facts', help='build place facts from a shot_facts measurement and its check file'))
    for name in ('--facts', '--check', '--place', '--view'):
        p.add_argument(name, required=True)
    p.add_argument('--kind', action='append', help='a kind of shot (repeat for several)')
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    try:
        if args.command == 'check':
            schema = load_schema()
            results, lines, bad = {}, [], 0
            for path in args.files:
                found = check_file(path, settings, schema)
                results[path] = found
                bad += bool(found)
                lines.append(f'{path}: ' + ('fine' if not found else f'{len(found)} problem(s)'))
                lines += [f'  {p}' for p in found]
            finish('place_facts check', {'files': results, 'problems': sum(len(v) for v in results.values())}, lines, settings, args)
            sys.exit(1 if bad else 0)
        builder = {'from-works': from_works, 'from-notice-corner': from_notice_corner, 'from-people-test': from_people_test,
                   'from-shot-facts': from_shot_facts}[args.command]
        facts = builder(args, settings)
        problems = validate(facts, load_schema()) + sense_problems(facts, settings)
        out = args.out
        args.out = None   # finish() writes the report wrapper; the place facts file itself is written here
        if out:
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            with open(out, 'w') as handle:
                json.dump(facts, handle, indent=1)
        lines = summary_lines(facts, out) + ([f'PROBLEM: {p}' for p in problems] or ['It passes the schema and the sense checks.'])
        finish(f'place_facts {args.command}', {'place_facts': facts if args.json else {'place': facts['place'], 'written_to': out},
                                               'problems': problems}, lines, settings, args)
        sys.exit(1 if problems else 0)
    except MissingSetting as problem:
        raise SystemExit(f'place_facts: {problem}')


if __name__ == '__main__':
    main()
