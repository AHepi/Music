"""What this does: tests the place kit's DATA and the checker of that data (place-kit/check_presets.py), in plain Python (no Blender).
1. The six groups of check_presets pass on the kit as it is: every number has a kind and a source; the data files agree with each other; every REQUIRED treatment is made by a real
   function and proved by a test phrase; no kit code names a kind of place; no Blender code imports Pillow, OpenCV or SciPy; nothing private is written anywhere.
2. The checker is not blind: on a copy of the kit with one planted fault at a time (a number with no source, a role with a surface that does not exist, a required treatment whose test
   phrase is gone, the word "harbour" in code, an import of PIL in a Blender module, an email-like string, a key-looking value, a personal folder), the right group fails and names it.
3. The data make sense on their own: the four looks rise from kept to derelict in every layer; every dial default sits inside its range; every surface names a recipe that exists, a
   believable tile size and a valid palette; every plant kind has a size range of at least 3 to 1 and a builder that exists; every place type's allowed-off reasons are real sentences.
4. The settings file reader: a model's plain settings are checked with plain-words problems (a bad look, a one-word off reason, a road with one point, an unknown role, an unknown
   shape), a missing file is drafted, the place type's defaults sit under the place's own settings, and the example settings and ownership files for a worked place pass.
5. The house numbers: the place_* sections of film-settings.json are read by the one reader (settings.py), carry kind and source, and no more than about a tenth is invented.
6. The 1.4.0 fix round: a rut shallower than the ground relief the audit asks for is warned about when the settings are read (the draft gave no hint); the numbers the fixes added exist
   (sunk in 4 cm, outline growth 1.5, fallback share 0.15, Cycles for water); the rut-depth numbers cite the yard's real 0.15 m, not the 4 to 9 cm the design remembered.
Run: python3 kit/calculators/tests/test_place_data.py   (about 5 seconds)
"""
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, CALCULATORS, TESTS  # noqa: E402

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
sys.path.insert(0, CALCULATORS)
import check_presets  # noqa: E402
from place_kit import settings_file, names, house_numbers  # noqa: E402
from place_kit.surfaces import heights  # noqa: E402
from place_kit.growth import pieces  # noqa: E402

check = Checker('place data: presets agree, the checker is not blind, the numbers make sense')
data_dir = os.path.join(PLACE_KIT, 'data')


def read(*parts):
    with open(os.path.join(data_dir, *parts), encoding='utf-8') as handle:
        return json.load(handle)


# ---------------------------------------------------------------- 1. the six groups on the kit as it is
results = check_presets.run_all(KIT)
check.equal('there are six groups', len(results), 6)
for name, problems in results:
    check.true(f'check_presets: {name}', not problems, '; '.join(problems[:3]) if problems else 'passes')
done = subprocess.run([sys.executable, '-I', '-B', os.path.join(PLACE_KIT, 'check_presets.py')], capture_output=True, text=True)
check.true('the command exits 0 and says "6 of 6 groups passed"', done.returncode == 0 and '6 of 6 groups passed' in done.stdout, done.stdout.strip().splitlines()[-1])

# ---------------------------------------------------------------- 2. the checker is not blind (planted faults on a copy)
copy_root = tempfile.mkdtemp(prefix='place-data-test-')
copy_kit = os.path.join(copy_root, 'plugin', 'kit')
os.makedirs(os.path.join(copy_kit, 'calculators', 'tests'))
shutil.copytree(PLACE_KIT, os.path.join(copy_kit, 'place-kit'), ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for name in os.listdir(TESTS):
    if name.startswith('test_place_blender'):
        shutil.copy(os.path.join(TESTS, name), os.path.join(copy_kit, 'calculators', 'tests', name))


def edit(relative, old, new, count=1):
    path = os.path.join(copy_kit, 'place-kit', relative)
    with open(path, encoding='utf-8') as handle:
        text = handle.read()
    assert old in text, f'the planted-fault test could not find {old!r} in {relative}'
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text.replace(old, new, count))


def append(relative, text):
    with open(os.path.join(copy_kit, 'place-kit', relative), 'a', encoding='utf-8') as handle:
        handle.write(text)


def group(index):
    return check_presets.run_all(copy_kit)[index][1]


baseline = [problems for _, problems in check_presets.run_all(copy_kit)]
check.true('the copy used for planting passes before any fault goes in (apart from the test file, which may not exist yet)', all(not p for i, p in enumerate(baseline) if i != 2), str([len(p) for p in baseline]))

edit('data/surfaces.json', '"source": "the coal mine yard depths and the design"', '"source": ""')
check.true('a number with no source is caught (group 1)', any('no source' in p for p in group(0)))
edit('data/surfaces.json', '"source": ""', '"source": "the coal mine yard depths and the design"')
edit('data/roles.json', '"surface": "plaster_lime"', '"surface": "no_such_surface"')
check.true('a role with a surface that does not exist is caught and named (group 2)', any('no_such_surface' in p for p in group(1)))
edit('data/roles.json', '"surface": "no_such_surface"', '"surface": "plaster_lime"')
edit('data/looks/kept.json', '"rubbish"', '"rubbish_gone"')
check.true('a look without a wear layer is caught (group 2)', any('no layer "rubbish"' in p for p in group(1)))
edit('data/looks/kept.json', '"rubbish_gone"', '"rubbish"')
if os.path.exists(os.path.join(copy_kit, 'calculators', 'tests', 'test_place_blender.py')):
    test_path = os.path.join(copy_kit, 'calculators', 'tests', 'test_place_blender.py')
    text = open(test_path, encoding='utf-8').read()
    open(test_path, 'w', encoding='utf-8').write(text.replace('layer dirt', 'layer d1rt'))
    check.true('a required treatment whose test phrase is gone is caught (group 3)', any('dirt' in p and 'phrase' in p for p in group(2)))
    open(test_path, 'w', encoding='utf-8').write(text)
    check.true('...and passes again when the phrase is back', not group(2))
else:
    check.note('the group 3 planted fault was skipped: test_place_blender.py is not there to copy')
edit('data/treatments.json', '"function": "give_surfaces"', '"function": "no_such_function"')
check.true('a required treatment whose maker function does not exist is caught (group 3)', any('no_such_function' in p for p in group(2)))
edit('data/treatments.json', '"function": "no_such_function"', '"function": "give_surfaces"')
append('place_kit/names.py', '\n# a plain comment about the harbour is not allowed in code\n')
check.true('the word "harbour" in kit code is caught (group 4)', any('harbour' in p for p in group(3)))
edit('place_kit/names.py', '# a plain comment about the harbour is not allowed in code\n', '')
append('place_kit/surfaces/heights.py', '\nimport PIL  # a Blender module may not import Pillow\n')
check.true('an import of Pillow in a module that runs in Blender is caught (group 5)', any('PIL' in p or 'Pillow' in p for p in group(4)))
edit('place_kit/surfaces/heights.py', '\nimport PIL  # a Blender module may not import Pillow\n', '')
EMAIL = 'someone' + '@' + 'example.org'
append('data/examples/canal-lock-place-settings.json.note.md', f'write to {EMAIL}\n')
check.true('an email-like string is caught (group 6)', any('email' in p for p in group(5)))
os.remove(os.path.join(copy_kit, 'place-kit', 'data/examples/canal-lock-place-settings.json.note.md'))
append('data/examples/key.md', 'api_key = "' + 'k' * 24 + '"\n')
check.true('a key-looking value is caught (group 6)', any('key-looking' in p for p in group(5)))
os.remove(os.path.join(copy_kit, 'place-kit', 'data/examples/key.md'))
append('data/examples/folder.md', 'read ~/.run' + 'pod/auth_header\n')
check.true('the personal settings folder used as a path is caught (group 6)', any('settings folder' in p for p in group(5)))
os.remove(os.path.join(copy_kit, 'place-kit', 'data/examples/folder.md'))
append('data/examples/sentence.md', 'the person keeps the key in their own `.run' + 'pod` settings folder, which the kit never reads.\n')
check.true('naming that folder in a sentence is allowed', not group(5))
os.remove(os.path.join(copy_kit, 'place-kit', 'data/examples/sentence.md'))
append('data/examples/hex.md', 'machine ' + 'a1b2c3d4' * 4 + '\n')
check.true('a long hex id is caught (group 6)', any('hex' in p for p in group(5)))
os.remove(os.path.join(copy_kit, 'place-kit', 'data/examples/hex.md'))
after = [problems for _, problems in check_presets.run_all(copy_kit)]
has_blender_test = os.path.exists(os.path.join(copy_kit, 'calculators', 'tests', 'test_place_blender.py'))
check.true('after every planted fault is taken out the copy is clean again', all(not p for i, p in enumerate(after) if i != 2 or has_blender_test), str([len(p) for p in after]))

# ---------------------------------------------------------------- 3. the data make sense
looks = {look: read('looks', f'{look}.json') for look in names.LOOKS}
rising = []
for layer in names.LAYER_ORDER:
    amounts = [looks[look]['layers'][layer]['amount'] for look in names.LOOKS]
    if amounts != sorted(amounts) or not all(0.0 <= a <= 1.0 for a in amounts):
        rising.append(f'{layer}: {amounts}')
check.equal(f'every layer rises from {names.LOOKS[0]} to {names.LOOKS[-1]} and stays between 0 and 1', rising, [])
check.true('a lived-in place has visibly more wear than a kept one (dirt amount at least 1.5 times)', looks['lived_in']['layers']['dirt']['amount'] >= 1.5 * looks['kept']['layers']['dirt']['amount'])
check.equal('the four looks are kept, lived_in, neglected, derelict', list(names.LOOKS), ['kept', 'lived_in', 'neglected', 'derelict'])
dials = read('dial_table.json')
outside = []
for layer, spec in dials['layers'].items():
    for dial in spec['dials']:
        if not (dial['lo'] <= dial['default'] <= dial['hi']):
            outside.append(f'{layer}.{dial["name"]}')
check.equal('every dial default sits inside its range', outside, [])
surfaces = read('surfaces.json')['surfaces']
problems = []
for surface_id, spec in surfaces.items():
    tile = settings_file.number(spec['tile_metres'])
    low, high = settings_file.number(spec['roughness']['low']), settings_file.number(spec['roughness']['high'])
    palette = settings_file.number(spec['colour']['palette'])
    if spec['height_recipe'] not in heights.RECIPES:
        problems.append(f'{surface_id}: recipe')
    if not (0.1 <= tile <= 12):
        problems.append(f'{surface_id}: tile {tile} m')
    if not (0 <= low < high <= 1):
        problems.append(f'{surface_id}: roughness {low}..{high}')
    if not palette or not all(re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in palette):
        problems.append(f'{surface_id}: palette')
    strength = settings_file.number(spec['normal_strength'])
    if not (0.2 <= strength <= 2.0):
        problems.append(f'{surface_id}: normal strength {strength}')
check.equal(f'every one of the {len(surfaces)} surfaces has a recipe that exists, a tile size, roughness, a palette and a normal strength that make sense', problems, [])
no_depth = [role for role, spec in read('roles.json')['roles'].items() if spec.get('displace') and not settings_file.number(surfaces[spec['surface']].get('displacement_depth_metres') or 0)]
check.equal('every role that displaces has a surface with a displacement depth', no_depth, [])
species = read('species.json')
narrow = [k for k, v in species['kinds'].items() if v['size_cm'][1] / v['size_cm'][0] < 3.0]
check.equal('every plant and litter kind has a size range of at least 3 to 1', narrow, [])
check.true('every kind names a builder that exists', all(v['builder'] in pieces.BUILDERS for v in species['kinds'].values()))
check.true('every place type has an id that is its file name, and a reason of 15 letters or more for each allowed-off entry', all(
    read('place_types', f)['id'] == f[:-5] and all(len(e['reason']) >= 15 for e in read('place_types', f).get('allowed_off', [])) for f in os.listdir(os.path.join(data_dir, 'place_types'))))
check.equal('the place type list has the generic default and the named presets', settings_file.place_type_ids(), sorted(['farm', 'garden', 'generic', 'harbour', 'interior', 'mine', 'town', 'village']))
facts = read('real_world_facts.json')['facts']
check.true('every real-world fact has a minimum below its maximum', all(f['min'] < f['max'] for f in facts), f'{len(facts)} facts')
banned = read('banned_place_nouns.json')
check.true('the banned place words include the place kinds the design names', all(word in banned['banned_nouns'] for word in ('town', 'harbour', 'mine', 'farm', 'garden', 'interior', 'forest')))

# ---------------------------------------------------------------- 4. the settings file reader
good = {'place_type': 'harbour', 'look': 'neglected', 'state': 'damp', 'roads': [{'name': 'road', 'polyline': [[0, 0], [10, 2]], 'width': 3.0, 'gauge': 1.3}],
        'off': [{'layer': 'moss_and_algae', 'roles': ['floor.*'], 'reason': 'inside the buildings: dry, nothing grows'}]}
check.equal('a good settings dict has no problems', settings_file.validate(good), [])
bad_cases = {
    'a look that does not exist': ({'look': 'shiny'}, 'look "shiny"'),
    'a state that does not exist': ({'state': 'soaked'}, 'state "soaked"'),
    'a place type that does not exist': ({'place_type': 'moon base'}, 'place_type'),
    'a one-word off reason': ({'off': [{'layer': 'dirt', 'roles': ['wall.*'], 'reason': 'n/a'}]}, '15 letters'),
    'an off entry for something that is not a treatment': ({'off': [{'layer': 'sparkle', 'roles': ['wall.*'], 'reason': 'because it is fine as it is'}]}, 'not a treatment'),
    'a road with one point': ({'roads': [{'name': 'road', 'polyline': [[0, 0]]}]}, 'at least two'),
    'a road with a width of zero': ({'roads': [{'name': 'road', 'polyline': [[0, 0], [1, 1]], 'width': 0}]}, '"width"'),
    'a role rule for a role that does not exist': ({'roles': [{'role': 'wall.paper', 'match': {'names': ['x']}}]}, 'wall.paper'),
    'a role rule that matches nothing': ({'roles': [{'role': 'wall.plaster'}]}, 'no "match"'),
    'a never rule with no reason': ({'never': [{'role': 'never.helper', 'match': {'names': ['x']}}]}, 'reason'),
    'a footfall shape that does not exist': ({'footfall': [{'shape': 'spiral'}]}, 'spiral'),
    'a renderer that does not exist': ({'renderer': 'rtx'}, 'renderer'),
}
for label, (settings_dict, word) in bad_cases.items():
    found = settings_file.validate(settings_dict)
    check.true(f'{label} is reported in plain words', any(word in p for p in found), '; '.join(found)[:160])
draft, report = settings_file.draft([{'name': 'wall 1', 'collections': [], 'materials': [], 'properties': {}}, {'name': 'qqq xyz', 'collections': [], 'materials': [], 'properties': {}}], 'a place', 'generic')
check.true('a draft lists the object it could not classify, with the cheapest fix', report['unknown'] and 'qqq xyz' in report['unknown'][0]['name'] and 'role' in report['unknown'][0]['fix'])
check.true('a draft starts from the place type (the generic type gives the indoor-floor off entries)', any(e['layer'] == 'plants' for e in draft['off']))
merged = settings_file.merged({'place_type': 'harbour', 'look': 'derelict'})
check.true("the place's own look wins over the place type's default look, the type's state default stays (the harbour starts wet, the generic default is dry)", merged['look'] == 'derelict' and merged['state'] == 'wet')
check.true('the place type\'s off entries come with their reasons', all(len(e['reason']) >= 15 for e in merged['off']))
try:
    settings_file.look('shiny')
    raised = ''
except ValueError as problem:
    raised = str(problem)
check.true('an unknown look stops with the known ones named', 'kept' in raised and 'derelict' in raised, raised)
for example in ('canal-lock-place-settings.json', 'canal-lock-ownership.json'):
    check.true(f'the example {example} exists and is valid JSON', os.path.exists(os.path.join(data_dir, 'examples', example)))
example_settings = read('examples', 'canal-lock-place-settings.json')
check.equal('the example place settings pass the reader', settings_file.validate(settings_file.merged(example_settings)), [])
example_owners = read('examples', 'canal-lock-ownership.json')
check.true('the example ownership names four owners and freezes the cameras, lights, world and render settings', len(example_owners['owners']) == 4 and all(example_owners['frozen'].values()))
template = os.path.join(data_dir, 'templates', 'stage_template.py')
try:
    py_compile.compile(template, cfile=os.path.join(copy_root, 'stage_template.pyc'), doraise=True)
    compiled = True
except py_compile.PyCompileError:
    compiled = False
check.true('the stage file template is valid Python and says "What this does"', compiled and 'What this does' in open(template).read())

# ---------------------------------------------------------------- 5. the house numbers
done = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'settings.py'), 'check'], capture_output=True, text=True)
check.true('settings.py check finds no problem in film-settings.json', done.returncode == 0 and '0 problem(s)' in done.stdout, done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-120:])
with open(os.path.join(KIT, 'film-settings.json'), encoding='utf-8') as handle:
    table = json.load(handle)
def entries_of(node):
    """Every number entry ({value, kind, source}) in a settings table, at any depth."""
    if isinstance(node, dict):
        if 'kind' in node and 'value' in node:
            yield node
        else:
            for child in node.values():
                yield from entries_of(child)


place_entries = [e for section, body in table.items() if section.startswith('place_') for e in entries_of(body)]
all_entries = list(entries_of(table))
invented = [e for e in all_entries if e['kind'] == 'invented']
check.true('the place_* sections have many numbers, every one with kind and source', len(place_entries) > 120 and all(e.get('source') and e['kind'] in ('measured', 'judged', 'invented') for e in place_entries), f'{len(place_entries)} numbers')
check.true('no more than a tenth of ALL the numbers in the table are invented (the rest are measured or judged, with their source)', len(invented) <= 0.10 * len(all_entries), f'{len(invented)} of {len(all_entries)}')
check.equal('the one reader gives a number', house_numbers.value('place_render.preview_samples'), 96)
check.true('the numbers the 1.4.0 fix round added are there: a part may sit 4 cm into its carrier, an outline may grow 1.5 times, a fallback role share of 15 percent fails, water in view gives Cycles',
           house_numbers.value('place_construction.sunk_in_centimetres_max') == 4 and house_numbers.value('place_audit.ground_area_growth_max') == 1.5
           and house_numbers.value('place_audit.fallback_role_share_fail') == 0.15 and house_numbers.value('place_render.cycles_when_water_in_view') is True)
rut_sources = ' '.join(table['place_wear'][key]['source'] for key in ('rut_depth_metres', 'ground_relief_metres_min'))
check.true('the rut-depth numbers cite the coal yard\'s real 0.15 m (the 4 to 9 cm of the first design was a wrong memory)', '4 to 9' not in rut_sources and '0.15' in rut_sources, rut_sources[:160])
shallow = settings_file.road_warnings({'roads': [{'name': 'towpath', 'polyline': [[0, 0], [5, 0]], 'rut_depth': 0.025}, {'name': 'road', 'polyline': [[0, 0], [5, 0]], 'rut_depth': 0.08}]})
check.true('a rut of 2.5 cm is warned about by name (the audit would fail its relief later), a rut of 8 cm is not', len(shallow) == 1 and 'towpath' in shallow[0] and 'at least' in shallow[0], str(shallow))
check.equal('a road with no rut_depth written has nothing to warn about', settings_file.road_warnings({'roads': [{'name': 'x', 'polyline': [[0, 0], [1, 0]]}]}), [])
try:
    house_numbers.value('place_render.preview_sample')
    message = ''
except Exception as problem:   # noqa: BLE001
    message = str(problem)
check.true('a key that is not in the table stops with the nearest real keys named', 'preview_samples' in message, message[:160])
check.finish()
