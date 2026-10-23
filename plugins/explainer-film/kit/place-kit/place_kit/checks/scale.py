"""What this does: compares the SIZE of every object with real-world facts (data/real_world_facts.json plus the place's own facts file) and
returns, per object, the measurements that apply: for example a door's height against 1.6 to 2.3 metres. It only gathers the numbers; the
verdict (a door 1.0 m high fails, 1.7 m passes) is the judge's (calculators/place_audit_check.py) so thresholds stay in one table.

How a fact applies to an object: its role matches the fact's applies_to_role pattern and, when given, its name matches applies_to_name.
How a dimension is read (so a model and a checker mean the same thing): height = the z extent; width = the larger horizontal extent;
depth = the smaller horizontal extent; thickness = the smallest of the three extents; middle = the middle one; span = the largest one;
pitch = the typical slope of a roof's up-facing faces in degrees; gauge = the distance between the wheel ruts of a road in the settings; rise = how far a step's top stands above
what it rests on or the next lower step beside it (measured by the construction check, top to top); free_span = the longest free stretch of a
plank or beam between its supports, which only the judge reads (a place's own sourced free_span fact lets a real longer span pass, such as a hall's
tie beam between its walls; it is never measured here).
Three guards against false alarms: a fact marked only_if_slab_like is used only when the object's smallest extent is at most 0.4 of its
middle one (a whole building in one object is not read as one thick wall); a fact marked skip_if_lying is not used for an object that is lower than
the fact's minimum and more than three times longer than it is high (a rail along a fence is not the fence); and an object made of several loose
pieces is not read for single-piece facts (the report says so).
The plain-Python part (measure_object) has no Blender in it and is tested without Blender.
"""
import re

SLAB_RATIO = 0.4
FLAT_ROOF_DEGREES = 5.0


def dimension_value(size, dimension, pitch=None):
    """One dimension of an object from its extents (x, y, z in metres) and its roof pitch (degrees or None)."""
    x, y, z = (float(v) for v in size)
    ordered = sorted((x, y, z))
    if dimension == 'height':
        return z
    if dimension == 'width':
        return max(x, y)
    if dimension == 'depth':
        return min(x, y)
    if dimension == 'thickness':
        return ordered[0]
    if dimension == 'middle':
        return ordered[1]
    if dimension == 'span':
        return ordered[2]
    if dimension == 'pitch':
        return pitch
    return None


def is_slab_like(size):
    ordered = sorted(float(v) for v in size)
    return ordered[0] <= SLAB_RATIO * ordered[1] if ordered[1] > 0 else False


def is_lying(size, minimum):
    """True for a long low piece: lower than `minimum` and more than three times longer than it is high (a rail, a board lying along something)."""
    x, y, z = (float(v) for v in size)
    return z < minimum and max(x, y) > 3.0 * z


def applicable_facts(role, name, facts):
    found = []
    for fact in facts:
        if not re.search(fact.get('applies_to_role', '.*'), role or ''):
            continue
        if fact.get('applies_to_name') and not re.search(fact['applies_to_name'], name or '', re.I):
            continue
        found.append(fact)
    return found


def measure_object(name, role, size, facts, parts_count=1, pitch=None):
    """The scale entries of one object: [{fact, dimension, value, min, max, unit, confidence}], and a list of notes about facts that were skipped."""
    entries, notes = [], []
    for fact in applicable_facts(role, name, facts):
        dimension = fact['dimension']
        if dimension in ('gauge', 'rise', 'free_span'):
            continue                                    # a gauge is read from the roads in the settings, a rise from the construction check (top to top), a free span by the judge from the construction check; none from an object's own extents
        if fact.get('only_if_slab_like') and not is_slab_like(size):
            notes.append(f'{fact["id"]}: skipped, the object is not slab-like')
            continue
        if fact.get('skip_if_lying') and is_lying(size, fact['min']):
            notes.append(f'{fact["id"]}: skipped, the object lies along something (it is a rail or a board, not the whole)')
            continue
        if parts_count > 1 and dimension != 'pitch':
            notes.append(f'{fact["id"]}: skipped, the object is made of {parts_count} loose pieces')
            continue
        if dimension == 'pitch' and (pitch is None or pitch < FLAT_ROOF_DEGREES):
            notes.append(f'{fact["id"]}: skipped, no pitched roof faces')
            continue
        value = dimension_value(size, dimension, pitch)
        if value is None:
            continue
        entries.append({'fact': fact['id'], 'dimension': dimension, 'value': round(float(value), 4), 'min': fact['min'], 'max': fact['max'],
                        'unit': fact.get('unit', 'metres'), 'confidence': fact.get('confidence', 'guess')})
    return entries, notes


def gauge_entries(roads, facts):
    """The cart gauge written in the settings' roads, against the gauge facts: [{'road', 'fact', ...}]."""
    entries = []
    for fact in facts:
        if fact.get('dimension') != 'gauge':
            continue
        for road in roads or []:
            if road.get('gauge') is not None:
                entries.append({'fact': fact['id'], 'dimension': 'gauge', 'value': float(road['gauge']), 'min': fact['min'], 'max': fact['max'],
                                'unit': fact.get('unit', 'metres'), 'confidence': fact.get('confidence', 'guess'), 'road': road.get('name')})
    return entries


def rise_entries(rise_metres, role, name, facts):
    """The step-rise entries of one step: the rise (top of the step minus the top of what it rests on or of the next lower step beside it) against the facts that apply to its role."""
    entries = []
    for fact in applicable_facts(role, name, facts):
        if fact.get('dimension') == 'rise' and rise_metres is not None:
            entries.append({'fact': fact['id'], 'dimension': 'rise', 'value': round(float(rise_metres), 4), 'min': fact['min'], 'max': fact['max'], 'unit': fact.get('unit', 'metres'),
                            'confidence': fact.get('confidence', 'guess')})
    return entries


def put_fact(merged, fact):
    """Adds the place's own fact on top of the generic one with the same id: the keys it gives replace the generic ones, the keys it leaves out stay (so a fact that only gives a new
    min and max for `door_height` still applies to doors only, not to every object)."""
    base = merged.get(fact['id'])
    merged[fact['id']] = {**base, **fact} if base else fact


def load_facts(settings_data, extra_facts_path=None):
    """The generic facts, with the place's own facts on top (see put_fact)."""
    import json
    from .. import settings_file
    merged = {f['id']: f for f in settings_file.facts_table()}
    own = settings_data.get('facts')
    sources = []
    if isinstance(own, str):
        sources.append(own)
    elif isinstance(own, list):
        for fact in own:
            put_fact(merged, fact)
    if extra_facts_path:
        sources.append(extra_facts_path)
    for path in sources:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        for fact in (data.get('facts', data) if isinstance(data, dict) else data):
            put_fact(merged, fact)
    return list(merged.values())


def scale_report(settings, objects_and_roles, extra_facts_path=None):
    """{object name: [scale entries]} for the given objects (Blender objects with their role dict). Needs Blender."""
    from .. import scene_read
    facts = load_facts(settings.data if hasattr(settings, 'data') else (settings or {}), extra_facts_path)
    report = {}
    for obj, role in objects_and_roles:
        size = scene_read.oriented_size(obj)           # the object's own rectangle, not its box along the world axes (a wall turned 45 degrees is still as thick as it is)
        labels, pieces = scene_read.loose_part_labels(obj.data)
        pitch = scene_read.facing_slope_degrees(obj) if (role or '').startswith('roof.') else None
        entries, _ = measure_object(obj.name, role, size, facts, parts_count=pieces, pitch=pitch)
        if entries:
            report[obj.name] = entries
    return report
