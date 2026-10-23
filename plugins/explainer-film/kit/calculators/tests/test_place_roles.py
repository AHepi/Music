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
7. The 1.4.0 fix round: the name hints read the harbour and mill words the newcomer judge tried (a "Waterwheel" is not a cart wheel, "Reed bed" is not a thatch roof, "Quay wall" is stone,
   "Haystack" is straw, "Fish boxes stack" is not a chimney, "Stone steps" are steps and "Step trench cheek" is NOT a step); every role has a plain meaning; `roles --list` prints them all
   without a scene; steps have their own role, and the indoor-floor skip of the place types does not cover a flagstone floor.
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
road = roles.requirements('ground.dirt_road', table)
check.true('a dirt road requires displacement (the role says displace), plants, litter pieces and rubbish', all(t in road['required'] for t in ('displacement', 'plants', 'litter_pieces', 'rubbish')), ', '.join(road['required']))
check.true('a dirt road does not also "want" displacement (it is required)', 'displacement' not in road['wanted'])
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
# ---------------------------------------------------------------- 7. the hints the newcomer judge tried, the meanings, the role list
wanted = {'Waterwheel': 'timber.generic', 'Water wheel': 'timber.generic', 'Waterwheel axle': 'timber.generic', 'Mill wheel pit': 'timber.generic', 'Reeds on the bank': 'plant.foliage',
          'Reed bed': 'plant.foliage', 'Reed roof': 'roof.thatch', 'thatch roof': 'roof.thatch', 'Haystack': 'prop.straw', 'Quay wall': 'wall.stone', 'Harbour wall': 'wall.stone',
          'Canal lock wall': 'wall.stone', 'Garden wall': 'wall.stone', 'Quay apron': 'ground.stone_paving', 'Slipway': 'ground.stone_paving', 'Seabed': 'ground.earth', 'Lobster pot': 'prop.wicker',
          'Piles': 'timber.post', 'Mast': 'timber.post', 'Bollard': 'iron.fitting', 'Mooring ring': 'iron.fitting', 'Cleat': 'iron.fitting', 'Weir': 'timber.generic', 'Gutter': 'timber.generic',
          'Millstone': 'stone.rock', 'Willow': 'tree.bark', 'Stone steps': 'stone.step', 'Step 3': 'stone.step', 'Front step': 'stone.step', 'Chimney stack': 'stone.chimney',
          'Fence post 3': 'timber.post', 'Hut 1 wall': 'wall.plaster', 'Cart wheel': 'prop.wheel', 'Wagon wheel': 'prop.wheel', 'Handcart': 'prop.cart', 'Cart 2': 'prop.cart'}
wrong = {name: (tag(name)['role'], role) for name, role in wanted.items() if tag(name)['role'] != role}
check.equal('the names the newcomer judge tried now read as what they are', wrong, {}, recorded='judge-blind-newcomers: 70 plain names run through the role guesser',
            proves='a Waterwheel is no longer a cart wheel, nor a Reed bed a roof')
check.true('"Step trench cheek" and "Fish boxes stack" are NOT guessed as steps or a chimney (they stay unknown, so a builder must say)', tag('Step trench cheek')['role'] is None and tag('Fish boxes stack')['role'] != 'stone.chimney',
           str((tag('Step trench cheek')['role'], tag('Fish boxes stack')['role'])))
check.true('there is a role for steps, in the stone class, that is carried by a part and measured for its rise', table['roles']['stone.step']['class'] == 'stone' and table['roles']['stone.step']['scale'] == ['step_rise'] and table['roles']['stone.step']['needs_support'] == 'part')
rise = next(f for f in settings_file.facts_table() if f['id'] == 'step_rise')
check.true('the step-rise fact applies to the ROLE stone.step, not to a name pattern, and reads the rise top to top', rise['applies_to_role'] == '^stone\\.step$' and rise['dimension'] == 'rise' and 'applies_to_name' not in rise, str(rise)[:200])
missing_meaning = [role for role, spec in table['roles'].items() if len((spec.get('meaning') or '').strip()) < 12]
check.equal('every role has a plain meaning of a line', missing_meaning, [])
lines = roles.role_list_lines(table)
check.true('the role list has one line for every role, grouped by class', sum(1 for line in lines if not line.startswith('==')) == len(table['roles']) and sum(1 for line in lines if line.startswith('==')) == len({s['class'] for s in table['roles'].values()}))
import subprocess  # noqa: E402
done = subprocess.run([sys.executable, '-I', '-B', os.path.join(KIT, 'place-kit', 'place_command.py'), 'roles', '--list'], capture_output=True, text=True, timeout=60)
check.true('`explainer-film-place roles --list` prints every role with its meaning, needs no scene and no Blender, and exits 0', done.returncode == 0 and 'stone.step: a stone step' in done.stdout and 'ground.dirt_road: a dirt road' in done.stdout, f'exit {done.returncode}, {len(done.stdout.splitlines())} lines')
for type_id in settings_file.place_type_ids():
    preset = settings_file.place_type(type_id)
    indoors = [e for e in preset.get('allowed_off', []) if e['id'] == 'floors_indoors']
    if indoors:
        roles_off = indoors[0]['roles']
        check.true(f'the {type_id} preset\'s indoor-floor skip does not cover floor.stone (a patio or steps outdoors keep their moss, wear and plants)', 'floor.stone' not in roles_off and 'floor.planks' in roles_off or type_id == 'interior', str(roles_off))
off_by_preset = {'off': [{'layer': 'moss_and_algae', 'roles': settings_file.place_type('village')['allowed_off'][0]['roles'], 'reason': 'inside the buildings: dry, nothing grows'}]}
check.true('...so moss is still required on a floor.stone object and a stone.step object of a village, and skipped on a plank floor',
           'moss_and_algae' in roles.requirements('stone.step', table, off_by_preset)['required'] and not roles.off_entries_for('stone.step', 'moss_and_algae', off_by_preset)
           and not roles.off_entries_for('floor.stone', 'moss_and_algae', off_by_preset) and roles.off_entries_for('floor.planks', 'moss_and_algae', off_by_preset))

# ---------------------------------------------------------------- 8. the place's own facts are put on top of the generic ones, key by key
import json
import tempfile
from place_kit.checks import scale  # noqa: E402
own_path = os.path.join(tempfile.mkdtemp(prefix='place-facts-test-'), 'own-facts.json')
partial = {'id': 'door_height', 'min': 0.3, 'max': 0.5, 'confidence': 'strong'}          # only a new range for a fact the kit already has
json.dump({'facts': [partial]}, open(own_path, 'w'))
merged = {f['id']: f for f in scale.load_facts({}, own_path)}['door_height']
check.true('control: the partial fact on its own would apply to a wall (that is what replacing the whole entry gave)', scale.applicable_facts('wall.plaster', 'House wall', [dict(partial, dimension='height')]) != [])
check.true('a partial own fact keeps the generic fact\'s pattern (it still applies to doors only) and takes the new range', merged['min'] == 0.3 and merged['max'] == 0.5 and merged['confidence'] == 'strong'
           and scale.applicable_facts('wall.plaster', 'House wall', [merged]) == [] and scale.applicable_facts('timber.door', 'Door', [merged]) == [merged], str(merged)[:200])
json.dump({'facts': [{'id': 'canal_lock_depth', 'what': 'a made-up fact of one place', 'applies_to_role': '^water\\.', 'dimension': 'height', 'min': 1.0, 'max': 3.0, 'unit': 'metres', 'confidence': 'weak'}]}, open(own_path, 'w'))
ids = [f['id'] for f in scale.load_facts({}, own_path)]
check.true('a new fact of the place is added beside the generic ones', 'canal_lock_depth' in ids and 'door_height' in ids)
check.finish()
