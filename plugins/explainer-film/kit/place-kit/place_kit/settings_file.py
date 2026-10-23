"""What this does: reads, checks and drafts the small place-settings.json that holds everything one place needs (its look,
its state dry/damp/wet, its owners, extra role rules, what is switched off and why, its roads and footpaths) and loads the
kit's data files (roles, surfaces, looks, place types, facts, dials, species). Plain Python, standard library only, so it
works inside Blender and outside it and is tested without Blender.

A concrete example of a settings file (everything is optional; an empty file means "a lived-in place, dry, every role from names"):
    {"place": "demo", "place_type": "generic", "look": "neglected", "state": "damp",
     "roads": [{"name": "towpath", "polyline": [[0, 0], [30, 5]], "width": 3.0, "gauge": 1.3, "rut_depth": 0.08, "hoof": true}],
     "off": [{"layer": "moss_and_algae", "roles": ["floor.*"], "reason": "inside: dry, nothing grows", "reason_id": "floors_indoors"}]}
"""
import copy
import json
import os
import re

from . import names

HERE = os.path.dirname(os.path.abspath(__file__))
PLACE_KIT = os.path.dirname(HERE)
DATA = os.path.join(PLACE_KIT, 'data')

SHAPES = ('band_along', 'lines_along', 'polyline', 'rect', 'around_role', 'auto_door_strip')
OFF_REASON_MIN_LETTERS = 15            # "n/a" is not a reason
IMPLEMENTED_TREATMENTS = names.ALL_TREATMENTS


# ------------------------------------------------------------------ the kit's own data files
_data_cache = {}


def read_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def data_file(relative):
    """A parsed file from kit/place-kit/data (read once per run)."""
    path = os.path.join(DATA, relative)
    if path not in _data_cache:
        _data_cache[path] = read_json(path)
    return _data_cache[path]


def roles_table():
    return data_file('roles.json')


def surfaces_table():
    return data_file('surfaces.json')['surfaces']


def facts_table():
    return data_file('real_world_facts.json')['facts']


def dial_table():
    return data_file('dial_table.json')


def species_table():
    return data_file('species.json')


def look(look_id):
    """A look preset by id (kept, lived_in, neglected, derelict); an unknown id stops with the known ones named."""
    if look_id not in names.LOOKS:
        raise ValueError(f'the look "{look_id}" is not one of {", ".join(names.LOOKS)}')
    return data_file(f'looks/{look_id}.json')


def place_type(type_id):
    path = os.path.join('place_types', f'{type_id}.json')
    if not os.path.exists(os.path.join(DATA, path)):
        known = sorted(f[:-5] for f in os.listdir(os.path.join(DATA, 'place_types')) if f.endswith('.json'))
        raise ValueError(f'the place type "{type_id}" is not one of {", ".join(known)}')
    return data_file(path)


def place_type_ids():
    return sorted(f[:-5] for f in os.listdir(os.path.join(DATA, 'place_types')) if f.endswith('.json'))


def number(entry):
    """The value of a data entry ({value, unit, kind, source}) or the plain value."""
    return entry['value'] if isinstance(entry, dict) and 'value' in entry else entry


def surface(surface_id):
    table = surfaces_table()
    if surface_id not in table:
        raise KeyError(f'no surface "{surface_id}" in data/surfaces.json (it has {len(table)}; for example {", ".join(list(table)[:5])})')
    return table[surface_id]


# ------------------------------------------------------------------ the settings object
class Settings:
    """A place's settings (a dict) with the questions the kit asks of it."""

    def __init__(self, data, path=None):
        self.data = data
        self.path = path

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]

    @property
    def place(self):
        return self.data.get('place') or 'place'

    @property
    def place_type_id(self):
        return self.data.get('place_type') or 'generic'

    @property
    def look_id(self):
        return self.data.get('look') or 'lived_in'

    @property
    def state(self):
        return self.data.get('state') or look(self.look_id).get('state_default', 'dry')

    @property
    def seed(self):
        return int(self.data.get('seed', 1))

    @property
    def roads(self):
        return list(self.data.get('roads') or [])

    @property
    def picture(self):
        return dict(self.data.get('picture') or {})

    @property
    def off_entries(self):
        return list(self.data.get('off') or [])

    def look_for_role(self, role):
        """The look id for a role: the first look_by_role pattern that fits ('wall.*': 'lived_in'), else the place's look."""
        for pattern, look_id in (self.data.get('look_by_role') or {}).items():
            regex = '^' + re.escape(pattern).replace('\\*', '.*') + '$'
            if re.match(regex, role or ''):
                return look_id
        return self.look_id

    def rules_dict(self):
        """The part of the settings the role matcher reads."""
        return {'roles': self.data.get('roles') or [], 'never': self.data.get('never') or [], 'require_more': self.data.get('require_more') or {},
                'off': self.data.get('off') or []}

    def owner_of(self, obj):
        """The owner of an object (a dict with name, collections, materials, properties): its place_owner property, else the first owner
        whose collections, name patterns or materials fit, else None."""
        properties = obj.get('properties') or {}
        if properties.get(names.OWNER):
            return str(properties[names.OWNER])
        for owner, spec in (self.data.get('owners') or {}).items():
            if not isinstance(spec, dict):
                continue
            if any(re.search(p, c, re.I) for p in spec.get('collections', []) for c in obj.get('collections') or []):
                return owner
            if any(re.search(p, obj.get('name', ''), re.I) for p in spec.get('objects', [])):
                return owner
            if any(re.search(p, m, re.I) for p in spec.get('materials', []) for m in obj.get('materials') or []):
                return owner
        for collection in obj.get('collections') or []:
            if collection.startswith(names.PART_COLLECTION_PREFIX):
                return collection[len(names.PART_COLLECTION_PREFIX):]
        return None


def load(path):
    """Reads a place-settings.json; a missing or unreadable file stops with a plain sentence."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} is not there. Make a draft with: explainer-film-place new-settings --scene SCENE.blend --place NAME --type TYPE --out {path}')
    try:
        data = read_json(path)
    except json.JSONDecodeError as problem:
        raise ValueError(f'{path} is not valid JSON (line {problem.lineno}, column {problem.colno}: {problem.msg})')
    if not isinstance(data, dict):
        raise ValueError(f'{path} must hold one JSON object')
    return Settings(data, path)


def defaults_for(type_id):
    """The place type's starting settings (look, state, require_more, off entries) as a dict that a place file may override."""
    preset = place_type(type_id)
    off = []
    for entry in preset.get('allowed_off', []):
        for treatment in entry['treatments']:
            off.append({'layer': treatment, 'roles': entry['roles'], 'reason': entry['reason'], 'reason_id': entry['id']})
    return {'place_type': type_id, 'look': preset['default_look'], 'state': preset['default_state'], 'require_more': copy.deepcopy(preset.get('require_more') or {}),
            'off': off, 'footfall': [], 'keep_clear': []}


def merged(data):
    """A place's own settings on top of its place type's defaults (the place wins; lists in the place replace the type's lists)."""
    result = defaults_for(data.get('place_type') or 'generic') if (data.get('place_type') in (None, *place_type_ids())) else {}
    result.update(copy.deepcopy(data))
    return result


# ------------------------------------------------------------------ checking
def validate(data):
    """Plain-words problems with a settings dict (an empty list means it is usable). Never raises for a mistake in the file."""
    problems = []
    table = roles_table()
    known_roles = set(table['roles'])
    if data.get('place_type') and data['place_type'] not in place_type_ids():
        problems.append(f'place_type "{data["place_type"]}" is not one of {", ".join(place_type_ids())}')
    if data.get('look') and data['look'] not in names.LOOKS:
        problems.append(f'look "{data["look"]}" is not one of {", ".join(names.LOOKS)}')
    if data.get('state') and data['state'] not in names.STATES:
        problems.append(f'state "{data["state"]}" is not one of {", ".join(names.STATES)}')
    for pattern, look_id in (data.get('look_by_role') or {}).items():
        if look_id not in names.LOOKS:
            problems.append(f'look_by_role "{pattern}": the look "{look_id}" is not one of {", ".join(names.LOOKS)}')
    for index, rule in enumerate(data.get('roles') or [], start=1):
        if rule.get('role') not in known_roles:
            problems.append(f'roles rule {index}: the role "{rule.get("role")}" is not in data/roles.json')
        if not rule.get('match'):
            problems.append(f'roles rule {index}: it has no "match" block, so it fits nothing')
        elif not isinstance(rule['match'], dict) or not any(rule['match'].get(k) for k in ('names', 'collections', 'materials', 'properties')):
            problems.append(f'roles rule {index}: "match" needs names, collections, materials or properties')
    for index, rule in enumerate(data.get('never') or [], start=1):
        if not str(rule.get('role', 'never.helper')).startswith('never.'):
            problems.append(f'never rule {index}: the role must start with "never." (for example never.helper)')
        if not rule.get('reason'):
            problems.append(f'never rule {index}: say why this object gets no surface (a "reason")')
    for index, entry in enumerate(data.get('off') or [], start=1):
        layer = entry.get('layer') or entry.get('treatment')
        if layer not in names.ALL_TREATMENTS:
            problems.append(f'off entry {index}: "{layer}" is not a treatment ({", ".join(names.ALL_TREATMENTS)})')
        reason = (entry.get('reason') or '').strip()
        if len(reason) < OFF_REASON_MIN_LETTERS:
            problems.append(f'off entry {index} ({layer}): a reason of at least {OFF_REASON_MIN_LETTERS} letters is needed (a word like "n/a" does not count)')
    for klass, extras in (data.get('require_more') or {}).items():
        if klass not in table['classes']:
            problems.append(f'require_more: "{klass}" is not a role class ({", ".join(table["classes"])})')
        for treatment in extras:
            if treatment not in IMPLEMENTED_TREATMENTS:
                problems.append(f'require_more {klass}: "{treatment}" is not a treatment')
    for index, road in enumerate(data.get('roads') or [], start=1):
        points = road.get('polyline') or []
        if len(points) < 2 or any(len(p) != 2 for p in points):
            problems.append(f'roads entry {index}: "polyline" needs at least two [x, y] points')
        for key in ('width', 'gauge'):
            if key in road and not (isinstance(road[key], (int, float)) and road[key] > 0):
                problems.append(f'roads entry {index}: "{key}" must be a number above 0')
    for group in ('footfall', 'keep_clear'):
        for index, shape in enumerate(data.get(group) or [], start=1):
            if shape.get('shape') not in SHAPES:
                problems.append(f'{group} entry {index}: shape "{shape.get("shape")}" is not one of {", ".join(SHAPES)}')
    if data.get('renderer') and data['renderer'] not in ('auto', 'cycles', 'eevee'):
        problems.append('renderer must be auto, cycles or eevee')
    owners = data.get('owners')
    if isinstance(owners, dict):
        for owner, spec in owners.items():
            if not isinstance(spec, dict):
                problems.append(f'owners "{owner}": give collections, objects or materials')
    return problems


def road_warnings(data):
    """Plain sentences about roads that will fail the audit later (not errors: the verbs go on, the person reads them). A rut shallower than the ground relief the audit asks for makes
    the audit's relief check fail, and the draft gave no hint of it."""
    from . import house_numbers
    floor = house_numbers.value('place_wear.ground_relief_metres_min')
    found = []
    for index, road in enumerate(data.get('roads') or [], start=1):
        depth = road.get('rut_depth')
        if isinstance(depth, (int, float)) and depth < floor:
            found.append(f'road "{road.get("name", index)}": a rut depth of {depth} m is under the {floor} m of ground relief the audit asks for, so its ground-relief check would fail; use at least {round(floor * 1.5, 3)} m')
    return found


# ------------------------------------------------------------------ drafting
def draft(objects, place, type_id, hints_only=True):
    """A draft settings dict from the scene's objects (dicts with name, collections, materials, properties), plus the report:
    {'guessed': {name: [role, how]}, 'unknown': [names], 'owners': [...]}. Unknown objects are named with the cheapest way to classify them."""
    from . import roles as roles_module
    table = roles_table()
    defaults = defaults_for(type_id)
    tagged = roles_module.tag_objects(objects, {}, table)
    owners = {}
    for obj in objects:
        for collection in obj.get('collections') or []:
            if collection.startswith(names.PART_COLLECTION_PREFIX):
                owner = collection[len(names.PART_COLLECTION_PREFIX):]
                owners.setdefault(owner, {'collections': [f'^{re.escape(collection)}$']})
    settings = {'about': f'Place settings for {place}, drafted by explainer-film-place new-settings. Edit it: add role rules for the objects listed in "unknown", '
                         'set the look and state, add roads and footpaths. Every key is optional.',
                'place': place, 'place_type': type_id, 'look': defaults['look'], 'state': defaults['state'], 'seed': 1,
                'owners': owners, 'roles': [], 'never': [], 'off': defaults['off'], 'require_more': defaults['require_more'],
                'roads': [], 'footfall': defaults['footfall'], 'keep_clear': [], 'renderer': 'auto'}
    guessed = {name: [t['role'], t['how']] for name, t in tagged['by_object'].items() if t['role']}
    unknown = []
    for name in tagged['unknown']:
        unknown.append({'name': name, 'fix': f'add a role rule to "roles" (for example {{"role": "prop.wood", "match": {{"names": ["^{re.escape(name)}$"]}}}}) or set the object\'s place_role property'})
    settings['unknown_objects'] = unknown
    return settings, {'guessed': guessed, 'unknown': unknown, 'owners': sorted(owners)}
