"""What this does: decides what each object in a place IS (its role, for example wall.timber_frame or ground.dirt_road)
from plain facts about the object: its name, the collections it sits in, the names of its materials and its custom
properties. It is plain Python over plain dictionaries, so it is tested without Blender.

The order, first match wins (this is the rule a builder can rely on):
  1. the object's own place_role property (a builder who tags an object has said what it is);
  2. a "never" rule of the place settings (sky, lights, helpers and scattered pieces have no surface to give);
  3. a role rule of the place settings, in the order they are written;
  4. the name hints in data/roles.json (a wall called "hut wall 2" is a wall);
  5. nothing matched: the object is "unknown" and is reported, never skipped in silence.
A role rule may also match a material by name, so an object with two materials (a barrel with wood staves and iron
bands) can have a different role in each slot: the object's role is the first slot's, and slot_roles lists them all.

A concrete example: the object "Hut 1 plank floor" in the collection "Place: huts" with the material "oak" has
no place_role; the settings have the rule {"role": "timber.floor", "match": {"names": ["plank floor"]}}; the answer is
{"role": "timber.floor", "how": "settings rule 1", "slot_roles": ["timber.floor"]}.
"""
import json
import re

FALLBACK_ROLE = 'prop.generic'


def _regex_match(patterns, text):
    return any(re.search(pattern, text, re.I) for pattern in patterns or [])


def rule_matches(match, obj):
    """True when a rule's match block fits the object. All given parts must fit (names, collections, materials, properties);
    a part that is not given is not tested. An empty match block fits nothing (a rule must say something)."""
    if not match:
        return False
    tested = False
    if match.get('names'):
        tested = True
        if not _regex_match(match['names'], obj.get('name', '')):
            return False
    if match.get('collections'):
        tested = True
        collections = obj.get('collections') or []
        if not any(_regex_match(match['collections'], name) for name in collections):
            return False
    if match.get('materials'):
        tested = True
        materials = obj.get('materials') or []
        if not any(_regex_match(match['materials'], name) for name in materials):
            return False
    if match.get('properties'):
        tested = True
        properties = obj.get('properties') or {}
        for key, wanted in match['properties'].items():
            if properties.get(key) != wanted:
                return False
    return tested


def material_rule_role(settings_roles, material_name):
    """The role a material name alone maps to (rules that only match materials), or None."""
    for rule in settings_roles:
        match = rule.get('match') or {}
        if match.get('materials') and not (match.get('names') or match.get('collections') or match.get('properties')):
            if _regex_match(match['materials'], material_name):
                return rule.get('role')
    return None


def hint_role(roles_table, obj):
    """The first role in data/roles.json whose name hint fits the object's name, collection or material names."""
    texts = [re.sub(r'[_\-.]+', ' ', t) for t in [obj.get('name', '')] + list(obj.get('collections') or []) + list(obj.get('materials') or [])]
    best = None
    for role_id, spec in roles_table.get('roles', {}).items():
        for pattern in spec.get('name_hints', []):
            for position, text in enumerate(texts):
                if re.search(pattern, text, re.I):
                    # the object's own name counts most, then its collection, then its materials
                    rank = position if position == 0 else 1 + position
                    if best is None or rank < best[0]:
                        best = (rank, role_id)
                    break
    return best[1] if best else None


def tag_object(obj, settings, roles_table):
    """The role of one object (a dict with name, collections, materials, properties): {'role', 'how', 'slot_roles', 'surface'}.
    role is None when nothing matched ('how' says so)."""
    properties = obj.get('properties') or {}
    result = {'role': None, 'how': 'unknown', 'slot_roles': [], 'surface': None}
    own = properties.get('place_role')
    if own:
        result.update(role=str(own), how='place_role property')
    else:
        for index, rule in enumerate(settings.get('never') or [], start=1):
            if rule_matches(rule.get('match'), obj):
                result.update(role=rule.get('role') or 'never.helper', how=f'never rule {index}')
                break
        else:
            for index, rule in enumerate(settings.get('roles') or [], start=1):
                if rule_matches(rule.get('match'), obj):
                    result.update(role=rule['role'], how=f'settings rule {index}', surface=rule.get('surface'))
                    break
            else:
                hinted = hint_role(roles_table, obj)
                if hinted:
                    result.update(role=hinted, how='name hint')
    if result['role'] is None:
        return result
    slot_roles = []
    for material_name in obj.get('materials') or []:
        slot_roles.append(material_rule_role(settings.get('roles') or [], material_name) or result['role'])
    saved = properties.get('pk_slot_roles')
    if saved:
        slot_roles = json.loads(saved) if isinstance(saved, str) else list(saved)
    result['slot_roles'] = slot_roles or [result['role']]
    return result


def tag_objects(objects, settings, roles_table):
    """{object name: tag_object result} for every object, plus the list of unknown names and counts by role."""
    by_object = {}
    unknown = []
    by_role = {}
    for obj in objects:
        tagged = tag_object(obj, settings, roles_table)
        by_object[obj['name']] = tagged
        if tagged['role'] is None:
            unknown.append(obj['name'])
        else:
            by_role[tagged['role']] = by_role.get(tagged['role'], 0) + 1
    return {'by_object': by_object, 'unknown': unknown, 'by_role': by_role}


def role_class(role_id):
    """'wall.plaster' -> 'wall'; 'never.sky' -> 'never'."""
    return (role_id or '').split('.', 1)[0]


def is_never(role_id):
    return role_class(role_id) == 'never'


def fallback_for_unknown(obj, roles_table):
    """A role for an object nothing matched: the class guessed from its material names (stone, wood, iron ...) or prop.generic.
    The caller must record it (a LOOK in the audit, and an entry in the settings) so a fallback is never silent."""
    texts = ' '.join(list(obj.get('materials') or []) + [obj.get('name', '')]).lower()
    guesses = (('stone', 'stone.rock'), ('rock', 'stone.rock'), ('brick', 'wall.brick'), ('iron', 'iron.fitting'), ('metal', 'iron.fitting'),
               ('steel', 'iron.fitting'), ('wood', 'prop.wood'), ('plank', 'timber.plank'), ('cloth', 'prop.cloth'), ('glass', 'glass.window'),
               ('water', 'water.still'), ('leaf', 'plant.foliage'), ('grass', 'ground.grass'))
    for word, role in guesses:
        if word in texts and role in roles_table.get('roles', {}):
            return role
    return FALLBACK_ROLE


def requirements(role_id, roles_table, settings=None):
    """What a role needs: {'required': [treatments], 'wanted': [treatments], 'exempt': {treatment: reason}}.
    From its class in data/roles.json, plus the settings' require_more, minus the role's own exemptions. A treatment the
    settings turn off (an 'off' entry with a reason) is removed here and reported by the audit as known."""
    spec = roles_table.get('roles', {}).get(role_id)
    if spec is None:
        return {'required': [], 'wanted': [], 'exempt': {}}
    klass = roles_table.get('classes', {}).get(spec.get('class'), {})
    required = list(klass.get('requires', []))
    wanted = list(klass.get('wanted', []))
    if spec.get('displace'):
        if 'displacement' not in required:
            required.append('displacement')
        wanted = [w for w in wanted if w != 'displacement']
    for extra in ((settings or {}).get('require_more') or {}).get(spec.get('class'), []):
        if extra not in required:
            required.append(extra)
        wanted = [w for w in wanted if w != extra]
    exempt = dict(spec.get('exempt') or {})
    required = [t for t in required if t not in exempt]
    wanted = [t for t in wanted if t not in exempt]
    return {'required': required, 'wanted': wanted, 'exempt': exempt}


def off_entries_for(role_id, treatment, settings):
    """The settings' 'off' entries that switch a treatment off for a role (role patterns like 'wall.*' are allowed)."""
    found = []
    for entry in (settings or {}).get('off') or []:
        layer = entry.get('layer') or entry.get('treatment')
        if layer != treatment:
            continue
        patterns = entry.get('roles') or ['*']
        for pattern in patterns:
            regex = '^' + re.escape(pattern).replace('\\*', '.*') + '$'
            if re.match(regex, role_id or ''):
                found.append(entry)
                break
    return found
