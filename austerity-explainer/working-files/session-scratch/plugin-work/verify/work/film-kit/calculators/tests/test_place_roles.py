"""What this does: tests how the place kit decides what each object IS (place_kit/roles.py) and what each role needs, in plain Python over plain dictionaries (no Blender).
1. The order of the rule, first match wins: the object's own place_role property, then a "never" rule of the settings, then a role rule of the settings, then the name hints,
   then "unknown", which is listed and never skipped in silence.
2. Name hints read the way people write names: "wall_north" is a wall, "floor_plank_1" is a plank floor (the more specific role wins), "Hut 1 roof" is a roof, and a word that only
   sits inside another word does not count.
3. One object with two materials gets one role per material (a barrel with wood staves and iron bands) from material rules; a saved per-slot list wins.
4. A fallback role for an unknown object is a guess from its materials and is always reported (never silent).
5. What a role needs: its class decides REQUIRED and WANTED treatments; displace roles require displacement; require_more adds; exemptions (with reasons) take away; an "off" entry
   with a role pattern switches a treatment off for matching roles only.
6. The data agree: every role has a class, a surface and a hint list that is a valid pattern; every class names only treatments that exist; every treatment has its plain
   words, the words a person uses for it, the function that makes it and the test that proves it; the seventeen treatments are all there.
Run: python3 kit/calculators/tests/test_place_roles.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT  # noqa: E402

sys.path.insert(0, os.path.join(KIT, 'place-kit'))
from place_kit import roles, settings_file, names  # noqa: E402

check = Checker('place roles: how objects get a role, and what a role needs')
table = settings_file.roles_table()


def tag(name, settings=None, collections=(), materials=(), properties=None):
    obj = {'name': name, 'collections': list(collections), 'materials': list(materials), 'properties': properties or {}}
    return roles.tag_object(obj, settings or {}, table)


# ---------------------------------------------------------------- 1. the order
settings = {'never': [{'role': 'never.helper', 'match': {'names': ['^measure']}, 'reason': 'a hidden measuring stick'}],
            'roles': [{'role': 'prop.cart', 'match': {'names': ['^wall']}}, {'role': 'timber.beam', 'match': {'names': ['^measure wall']}}]}
check.equal('the object\'s own place_role wins over everything', tag('wall 1', settings, properties={'place_role': 'stone.well'})['role'], 'stone.well')
check.equal('...and says how it was found', tag('wall 1', settings, properties={'place_role': 'stone.well'})['how'], 'place_role property')
check.equal('a never rule wins over a role rule and a name hint', tag('measure wall', settings)['role'], 'never.helper')
check.equal('a role rule of the settings wins over a name hint (a "wall" named like a cart is a cart)', tag('wall 1', settings)['role'], 'prop.cart')
check.equal('with no rule the name hint decides', tag('wall 1')['role'], 'wall.plaster')
unknown = tag('qqq xyz')
check.true('an object nothing matches has no role and says so', unknown['role'] is None and unknown['how'] == 'unknown')
listed = roles.tag_objects([{'name': 'qqq xyz', 'collections': [], 'materials': [], 'properties': {}}, {'name': 'wall 2', 'collections': [], 'materials': [], 'properties': {}}], {}, table)
check.equal('the unknown object is listed by name, not skipped', listed['unknown'], ['qqq xyz'])

# ---------------------------------------------------------------- 2. name hints
check.true('"wall_north" (an underscore) is a wall', tag('wall_north')['role'].startswith('wall.'), tag('wall_north')['role'])
check.equal('"floor_plank_1" is a plank floor, not just a plank', tag('floor_plank_1')['role'], 'timber.floor')
check.true('"Hut 1 roof" is a roof', tag('Hut 1 roof')['role'].startswith('roof.'), tag('Hut 1 roof')['role'])
check.true('"ground" is a ground', tag('ground')['role'].startswith('ground.'), tag('ground')['role'])
check.equal('a word inside another word does not count ("fireplace" is not a place, a floor or a wall)', tag('fireplace')['role'], None)
check.true('a plural collection name is read ("Roofs" decides for "Object.012")', (tag('Object.012', collections=['Roofs'])['role'] or '').startswith('roof.'), str(tag('Object.012', collections=['Roofs'])['role']))
check.equal('a name like "Object.012" with nothing else to go on is the generic prop (a weak hint that only counts when nothing else fits)', tag('Object.012')['role'], 'prop.generic')
check.equal('the generic hint does not beat a material hint', tag('Object.012', materials=['timber planks'])['role'], 'timber.plank')
check.true('the object\'s own name counts more than its material', tag('door', materials=['stone wall'])['role'].startswith('timber.'), tag('door', materials=['stone wall'])['role'])

# ---------------------------------------------------------------- 3. one role per material slot
barrel_settings = {'roles': [{'role': 'prop.barrel', 'match': {'names': ['^barrel']}}, {'role': 'iron.fitting', 'match': {'materials': ['^iron band']}}]}
barrel = tag('barrel 1', barrel_settings, materials=['oak staves', 'iron band'])
check.equal('a barrel with wood staves and iron bands has two slot roles', barrel['slot_roles'], ['prop.barrel', 'iron.fitting'])
check.equal('the object\'s own role is the barrel', barrel['role'], 'prop.barrel')
material_first = {'roles': [{'role': 'iron.fitting', 'match': {'materials': ['^iron band']}}]}
barrel_two = tag('Prop barrel 1', material_first, materials=['oak staves', 'iron band'])
check.equal('a rule that names only a material gives that SLOT its role, not the whole object (the barrel stays a barrel, even when the rule is the only one)', (barrel_two['role'], barrel_two['slot_roles']), ('prop.barrel', ['prop.barrel', 'iron.fitting']))
check.equal('an object with only an "iron band" material and no other clue is iron (the material rule names it when nothing else can)', tag('thing 7', material_first, materials=['iron band'])['role'], 'iron.fitting')
saved = tag('barrel 1', barrel_settings, materials=['a', 'b'], properties={'pk_slot_roles': '["prop.wheel", "iron.fitting"]'})
check.equal('a saved per-slot list wins (the kit keeps it when it changes the materials)', saved['slot_roles'], ['prop.wheel', 'iron.fitting'])
check.equal('an object with no material still has one slot role', tag('barrel 1', barrel_settings)['slot_roles'], ['prop.barrel'])

# ---------------------------------------------------------------- 4. fallback
check.equal('an unknown object with a stone material gets a stone role as a guess', roles.fallback_for_unknown({'name': 'zzz', 'materials': ['grey stone']}, table), 'stone.rock')
check.equal('an unknown object with an iron material gets an iron role as a guess', roles.fallback_for_unknown({'name': 'zzz', 'materials': ['old iron']}, table), 'iron.fitting')
check.equal('an unknown object with nothing to go on gets the generic prop role', roles.fallback_for_unknown({'name': 'zzz', 'materials': []}, table), roles.FALLBACK_ROLE)
check.true('the fallback role is a real role', roles.FALLBACK_ROLE in table['roles'])

# ---------------------------------------------------------------- 5. what a role needs
wall = roles.requirements('wall.plaster', table)
check.true('a plaster wall requires normal map, dirt, grime, weathering, wetness, cracks, edge wear, moss and bevels',
           all(t in wall['required'] for t in ('normal_map', 'dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae', 'bevelled_edges')), ', '.join(wall['required']))
check.true('...and wants shape damage', 'shape_damage' in wall['wanted'])
lane = roles.requirements('ground.dirt_road', table)
check.true('a dirt road requires displacement (the role says displace), plants, litter pieces and rubbish', all(t in lane['required'] for t in ('displacement', 'plants', 'litter_pieces', 'rubbish')), ', '.join(lane['required']))
check.true('a dirt road does not also "want" displacement (it is required)', 'displacement' not in lane['wanted'])
check.true('earth, forest floor, gravel and paving ground also require displacement', all('displacement' in roles.requirements(r, table)['required'] for r in ('ground.earth', 'ground.forest_floor', 'ground.gravel', 'ground.stone_paving')))
check.true('thatch requires displacement too', 'displacement' in roles.requirements('roof.thatch', table)['required'])
snow = roles.requirements('ground.snow', table)
check.true('snow is exempt from rubbish, plants and moss and the reasons are written', all(len(snow['exempt'].get(t, '')) >= 15 for t in ('rubbish', 'plants', 'moss_and_algae')) and 'plants' not in snow['required'], str(snow['exempt']))
more = roles.requirements('wall.plaster', table, {'require_more': {'wall': ['rust']}})
check.true('require_more adds a treatment to a whole class', 'rust' in more['required'])
check.equal('an unknown role needs nothing', roles.requirements('no.such.role', table), {'required': [], 'wanted': [], 'exempt': {}})
off = {'off': [{'layer': 'moss_and_algae', 'roles': ['floor.*'], 'reason': 'inside the buildings: dry, nothing grows'}]}
check.equal('an off entry with a pattern fits matching roles', len(roles.off_entries_for('floor.planks', 'moss_and_algae', off)), 1)
check.equal('...and not other roles', roles.off_entries_for('wall.plaster', 'moss_and_algae', off), [])
check.equal('...and not other treatments', roles.off_entries_for('floor.planks', 'dirt', off), [])
check.true('the class of a role is the word before the dot, and never.* is never', roles.role_class('wall.plaster') == 'wall' and roles.is_never('never.glow') and not roles.is_never('wall.plaster'))

# ---------------------------------------------------------------- 6. the data agree
classes = table['classes']
check.true('every role has a class that exists, and a surface that exists (or none for never.*)',
           all(spec.get('class') in classes for spec in table['roles'].values()) and all((spec.get('surface') in settings_file.surfaces_table()) or spec.get('class') == 'never' for spec in table['roles'].values()),
           f'{len(table["roles"])} roles')
bad_patterns = []
for role, spec in table['roles'].items():
    for pattern in spec.get('name_hints', []):
        try:
            re.compile(pattern)
        except re.error:
            bad_patterns.append(f'{role}: {pattern}')
check.equal('every name hint is a valid pattern', bad_patterns, [])
used = {t for klass in classes.values() for t in klass.get('requires', []) + klass.get('wanted', [])}
check.true('every treatment a class names is one of the seventeen', used <= set(names.ALL_TREATMENTS), str(sorted(used - set(names.ALL_TREATMENTS))))
check.equal('there are seventeen treatments', len(names.ALL_TREATMENTS), 17)
treatments = settings_file.data_file('treatments.json')['treatments']
check.equal('each of the seventeen has an entry in treatments.json', sorted(treatments), sorted(names.ALL_TREATMENTS))
incomplete = [t for t, meta in treatments.items() if not (meta.get('plain') and meta.get('persons_words') and meta.get('made_by') and meta.get('tested_by') and meta.get('checked_by'))]
check.equal('each has plain words, the words a person uses, a maker, a test and a checker named', incomplete, [])
check.true('the words a person uses cover the request: normals, displacements, dirt, grime, weeds, weathering, damage',
           all(any(word in ' '.join(sum((m['persons_words'] for m in treatments.values()), [])).lower() for word in [w]) for w in ('normal', 'displacement', 'dirt', 'grime', 'weed', 'weathering', 'damage')),
           proves='a plain request that says any of these words reaches a treatment')
check.true('the nine wear layers are all treatments', set(names.LAYER_ORDER) <= set(names.ALL_TREATMENTS) and len(names.LAYER_ORDER) == 9)
check.finish()
