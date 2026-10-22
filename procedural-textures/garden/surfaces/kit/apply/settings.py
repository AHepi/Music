# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Reads and checks the two kinds of small files the kit runs on:
#   * a SET file  (sets/<set_id>.json): everything that belongs to one place: which objects are walls, ground, iron ..., the scenes (saved Blender files), lights,
#     traffic shapes, cameras, ...
#   * a LOOK file (presets/<look>.json): only dial values per layer ("a sooty coal town", "a kept mossy garden").
# Plain Python (no Blender), so it can be tested anywhere. Keys that start with an underscore are notes, not data.
# validate_set() returns a Report with ERRORS (the kit refuses to go on: unknown role, a regex that does not compile, a missing key) and WARNINGS (a scene file that is
# not there, a role found nowhere ...). Whether a regex matches anything in a scene needs the scene's objects: see roles.check_matches().
import json
import os
import re

from . import KIT_ROOT

SET_DIR = os.path.join(KIT_ROOT, 'sets')
LOOK_DIR = os.path.join(KIT_ROOT, 'presets')
SLOTS = ('A', 'B', 'C')
FOOTFALL_KINDS = ('band_along', 'lines_along', 'auto_door_to_edge', 'polyline', 'rect')
KEEP_CLEAR_KINDS = ('auto_door_strip', 'around_role', 'from_footfall', 'rect', 'polyline')
SHADE_MODES = ('declared', 'openness', 'year_sun', 'year_sun_and_openness', 'declared_and_openness', 'none')
REQUIRED_KEYS = ('schema', 'id', 'scenes', 'roles', 'apply', 'geometry')


class Report:
    """Errors stop the kit; warnings are told to the person."""

    def __init__(self, what=''):
        self.what = what
        self.errors = []
        self.warnings = []

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)

    @property
    def ok(self):
        return not self.errors

    def extend(self, other):
        self.errors += other.errors
        self.warnings += other.warnings

    def as_dict(self):
        return dict(what=self.what, ok=self.ok, errors=list(self.errors), warnings=list(self.warnings))

    def __str__(self):
        lines = [f'{self.what}: {"OK" if self.ok else "ERRORS"} ({len(self.errors)} errors, {len(self.warnings)} warnings)']
        lines += ['  ERROR ' + e for e in self.errors] + ['  warning ' + w for w in self.warnings]
        return '\n'.join(lines)


def strip_notes(value):
    """A copy without keys that start with an underscore (notes)."""
    if isinstance(value, dict):
        return {k: strip_notes(v) for k, v in value.items() if not str(k).startswith('_')}
    if isinstance(value, list):
        return [strip_notes(v) for v in value]
    return value


def _walk_strings(value, path=''):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_strings(item, f'{path}/{key}')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f'{path}/{index}')
    elif isinstance(value, str):
        yield path, value


class Settings:
    """A set file, read. .raw is the dict as written (notes included); .data is the same without notes."""

    def __init__(self, raw, path=None):
        self.raw = raw
        self.data = strip_notes(raw)
        self.path = path

    # ---- plain access (never fails on a missing optional block)
    @property
    def id(self):
        return self.data['id']

    @property
    def roles(self):
        return self.data.get('roles', {})

    @property
    def apply(self):
        return self.data.get('apply', {})

    @property
    def never(self):
        return self.data.get('never', {})

    @property
    def geometry(self):
        return self.data.get('geometry', {})

    @property
    def scenes(self):
        return self.data.get('scenes', [])

    def scene(self, scene_id=None):
        scenes = self.scenes
        if scene_id is None:
            return scenes[0]
        for entry in scenes:
            if entry['id'] == scene_id:
                return entry
        raise KeyError(f'set {self.id!r} has no scene {scene_id!r}; it has {[s["id"] for s in scenes]}')

    def get(self, key, default=None):
        return self.data.get(key, default)

    def role_names(self):
        return list(self.roles.keys())

    def expand_roles(self, names):
        """A layer's role list may name a role ('wall.trim') or a whole family ('wall' = every role that starts with 'wall.'). Returns the matching role names, in settings order."""
        result = []
        for name in names:
            matched = [r for r in self.roles if r == name or r.startswith(name + '.')]
            for r in matched:
                if r not in result:
                    result.append(r)
        return result

    def layer_roles(self, layer):
        spec = self.apply.get(layer)
        if not spec:
            return []
        return self.expand_roles(spec.get('roles', spec.get('targets', [])))

    def layer_keys(self):
        return list(self.apply.keys())

    def default_look(self):
        return self.data.get('looks', {}).get('default')

    def look_overrides(self):
        return self.data.get('looks', {}).get('overrides', {})

    def legacy(self):
        return self.data.get('legacy')

    def slot_positions(self):
        """Where each kit slot sits among the earlier layers (a number against the index in legacy.order). A: before the first earlier layer; B and C: after the second."""
        legacy = self.legacy() or {}
        return dict({'A': -0.5, 'B': 1.5, 'C': 1.6}, **legacy.get('slot_positions', {}))


def resolve_set_path(ref):
    if os.path.exists(ref):
        return os.path.abspath(ref)
    path = os.path.join(SET_DIR, ref if ref.endswith('.json') else ref + '.json')
    if os.path.exists(path):
        return path
    raise FileNotFoundError(f'no set file {ref!r} (looked in {SET_DIR})')


def load_set(ref):
    path = resolve_set_path(ref)
    with open(path) as handle:
        return Settings(json.load(handle), path)


def load_look(ref):
    """A look file as a dict {'id', 'layers': {layer: {dial: value}}}."""
    path = ref if os.path.exists(ref) else os.path.join(LOOK_DIR, ref if ref.endswith('.json') else ref + '.json')
    with open(path) as handle:
        data = json.load(handle)
    data['_path'] = path
    return data


def _compile(report, where, pattern):
    try:
        return re.compile(pattern)
    except re.error as error:
        report.error(f'{where}: the pattern {pattern!r} does not compile ({error})')
        return None


def validate_set(settings, check_files=True):
    """Checks a set file on its own (no scene needed). Unknown role = error; a pattern that does not compile = error."""
    report = Report(f'set {settings.data.get("id", "?")}')
    data = settings.data
    for key in REQUIRED_KEYS:
        if key not in data:
            report.error(f'missing key {key!r}')
    if report.errors:
        return report
    if not str(data['schema']).startswith('weathering-set/'):
        report.error(f'schema {data["schema"]!r} is not weathering-set/N')
    roles = data['roles']
    for name, rule in roles.items():
        if not isinstance(rule, dict):
            report.error(f'role {name!r} is not a table')
            continue
        if not any(k in rule for k in ('objects', 'collections', 'materials', 'custom_props')):
            report.error(f'role {name!r} has no way to find anything (needs objects, collections, materials or custom_props)')
        for kind in ('objects', 'collections', 'materials'):
            for pattern in rule.get(kind, []):
                _compile(report, f'roles.{name}.{kind}', pattern)
        if rule.get('type') not in (None, 'MESH', 'EMPTY', 'CURVE', 'LIGHT', 'ANY'):
            report.error(f'role {name!r}: type {rule.get("type")!r} is not MESH, EMPTY, CURVE, LIGHT or ANY')
    # never lists
    for kind in ('materials', 'objects', 'own_layer_later'):
        for pattern in data.get('never', {}).get(kind, []):
            _compile(report, f'never.{kind}', pattern)
    # apply: every role named must exist (or be a family prefix)
    for layer, spec in data['apply'].items():
        names = list(spec.get('roles', [])) + list(spec.get('targets', [])) + list(spec.get('sources', []))
        for name in names:
            if not settings.expand_roles([name]):
                report.error(f'apply.{layer}: unknown role {name!r}')
        for role in spec.get('role_dials', {}):
            if not settings.expand_roles([role]):
                report.error(f'apply.{layer}.role_dials: unknown role {role!r}')
    geometry = data['geometry']
    for key in ('solids_for_wall_dist',):
        for name in geometry.get(key, []):
            if not settings.expand_roles([name]):
                report.error(f'geometry.{key}: unknown role {name!r}')
    ground = geometry.get('ground')
    if ground:
        for name in ground.get('roles', []):
            if not settings.expand_roles([name]):
                report.error(f'geometry.ground.roles: unknown role {name!r}')
        if 'bounds' not in ground:
            report.error('geometry.ground has no bounds')
    for frame in geometry.get('frames', []):
        for name in frame.get('roles', []):
            if not settings.expand_roles([name]):
                report.error(f'geometry.frames: unknown role {name!r}')
    for name in (geometry.get('crown') or {}).get('roles', []):
        if not settings.expand_roles([name]):
            report.error(f'geometry.crown.roles: unknown role {name!r}')
    for name in geometry.get('ledges', {}).get('sources_from_roles', []):
        if not settings.expand_roles([name]):
            report.error(f'geometry.ledges.sources_from_roles: unknown role {name!r}')
    for rule in data.get('footfall', []) or []:
        if rule.get('kind') not in FOOTFALL_KINDS:
            report.error(f'footfall {rule.get("id")!r}: unknown kind {rule.get("kind")!r}')
        for key in ('from_role', 'to_role', 'role'):
            if key in rule and not settings.expand_roles([rule[key]]):
                report.error(f'footfall {rule.get("id")!r}: unknown role {rule[key]!r}')
    for rule in data.get('keep_clear', []) or []:
        if rule.get('kind') not in KEEP_CLEAR_KINDS:
            report.error(f'keep_clear {rule.get("id")!r}: unknown kind {rule.get("kind")!r}')
        for key in ('from_role', 'role'):
            if key in rule and not settings.expand_roles([rule[key]]):
                report.error(f'keep_clear {rule.get("id")!r}: unknown role {rule[key]!r}')
    shade = data.get('shade')
    if shade and shade.get('mode') not in SHADE_MODES:
        report.error(f'shade.mode {shade.get("mode")!r} is not one of {SHADE_MODES}')
    # looks
    looks = data.get('looks', {})
    if looks.get('default'):
        if looks['default'] not in looks.get('available', [looks['default']]):
            report.error(f'looks.default {looks["default"]!r} is not in looks.available')
        for name in looks.get('available', []):
            if not os.path.exists(os.path.join(LOOK_DIR, name + '.json')):
                report.error(f'look {name!r} has no file in presets/')
    # legacy stage ports
    legacy = data.get('legacy')
    if legacy:
        for name in legacy.get('order', []):
            if name not in legacy.get('stage_ports', {}):
                report.error(f'legacy.order names {name!r} but legacy.stage_ports has no entry')
        for name, ports in legacy.get('stage_ports', {}).items():
            for key in ('node', 'takes', 'gives'):
                if key not in ports:
                    report.error(f'legacy.stage_ports.{name} has no {key!r}')
            for pattern in ports.get('only_materials', []):
                _compile(report, f'legacy.stage_ports.{name}.only_materials', pattern)
    # hook adapters
    for adapter in data.get('hook', {}).get('adapters', []):
        for key in ('groups', 'outputs'):
            if key not in adapter:
                report.error(f'hook.adapters entry has no {key!r}')
        for pattern in adapter.get('groups', []):
            _compile(report, 'hook.adapters.groups', pattern)
    # files
    if check_files:
        for scene in data['scenes']:
            if not os.path.exists(scene['file']):
                report.warn(f'scene {scene["id"]!r}: the file {scene["file"]} is not here')
    return report


def validate_look(look, settings=None, table=None):
    """A look file: every layer that has a dial table must use known dial names and values inside the range (out of range = warning, unknown dial = error)."""
    from . import dials
    table = table or dials.TABLE
    report = Report(f'look {look.get("id", "?")}')
    if not str(look.get('schema', '')).startswith('weathering-look/'):
        report.error(f'schema {look.get("schema")!r} is not weathering-look/N')
    for layer, values in look.get('layers', {}).items():
        spec = table.layers.get(layer)
        if spec is None:
            report.warn(f'layer {layer!r} has no dial table (a builder has not registered it)')
            continue
        for dial, value in values.items():
            row = spec.row(dial)
            if row is None:
                report.error(f'{layer}.{dial}: unknown dial')
                continue
            if not isinstance(value, (int, float)):
                report.error(f'{layer}.{dial}: {value!r} is not a number')
            elif not (row['lo'] - 1e-9 <= value <= row['hi'] + 1e-9):
                report.warn(f'{layer}.{dial}: {value} is outside {row["lo"]} to {row["hi"]}')
    if settings is not None:
        for layer in look.get('layers', {}):
            if layer not in settings.apply and layer not in ('common',):
                report.warn(f'layer {layer!r} is in the look but the set does not apply it')
    return report
