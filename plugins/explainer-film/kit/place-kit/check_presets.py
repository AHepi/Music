"""What this does: checks the place kit's own data and code for the mistakes that would make it wrong for some place or leak
something private. It is plain Python (standard library only) and runs without Blender.

It checks, and prints PASS or FAIL for each group:
  1. every number in data/*.json carries a kind (measured, judged or invented) and a source;
  2. the data agree with each other: every role names an existing class, surface and scale facts; every surface names a
     height recipe that exists; every look has every wear layer; place types name roles and facts that exist;
  3. a treatment may be REQUIRED by a class only if the kit really makes it: its made_by function exists in the named file
     and a test file contains the phrase that proves it (decision D3 of the 1.4.0 design);
  4. no code under place_kit/ names a kind of place (the list is data/banned_place_nouns.json), so the kit works for any place;
  5. code that runs inside Blender does not import Pillow, OpenCV or SciPy (Blender's own Python has none of them);
  6. nothing private or machine-specific is written anywhere in the kit: email-like strings, long hex ids, key-looking
     values, personal folders, the add-on this project does not carry, the rented-card settings folder.
Use: python3 check_presets.py [--kit-root DIR] [--json]   (exit 0 when every group passes, 1 when one fails)
"""
import argparse
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT_DEFAULT = os.path.dirname(HERE)            # the kit folder (holds place-kit, calculators, film-settings.json)
KINDS = ('measured', 'judged', 'invented')
LAYERS = ('dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae', 'rust', 'rubbish')
NO_SURFACE_CLASSES = ('never', 'backdrop')     # role classes with no surface pass (place_kit/roles.py is_never)
TREATMENTS = ('normal_map', 'displacement', 'roughness_variation', 'colour_variation', 'bevelled_edges', 'dirt', 'grime', 'weathering', 'wetness',
              'cracks_and_chips', 'edge_wear', 'moss_and_algae', 'rust', 'rubbish', 'plants', 'litter_pieces', 'shape_damage')
# modules that may use outside packages because they never run inside Blender
PLAIN_PYTHON_FILES = ('render/client.py', 'render/worker/handler.py', 'render/worker/cycles_check.py', 'variations/compare.py', 'variations/sheet.py')
PRIVATE_PIECES = ('As' + 'tra', 'CT' + ' /', '/ho' + 'me/', 'claude' + '-0')
SETTINGS_FOLDER_PATTERN = re.compile(r'(~/|/)\.run' + r'pod\b|\.run' + r'pod/')   # the rented-card settings folder used as a path (naming it in a sentence is allowed)


def read_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def all_text_files(root, extensions=('.py', '.json', '.md', '.sh', '.js', '.txt', '.mjs')):
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for name in sorted(files):
            if name.endswith(extensions) or name in ('explainer-film-place',):
                yield os.path.join(folder, name)


def walk_entries(node, path=''):
    """Every dict that looks like a number entry ({value, ...}) with its dotted path."""
    if isinstance(node, dict):
        if 'value' in node and ('unit' in node or 'kind' in node or 'source' in node):
            yield path, node
        else:
            for key, child in node.items():
                yield from walk_entries(child, f'{path}.{key}' if path else key)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from walk_entries(child, f'{path}[{index}]')


# ---------------------------------------------------------------- 1. kind and source
def check_kind_and_source(data_dir):
    problems = []
    for name in ('surfaces.json', 'real_world_facts.json', 'dial_table.json', 'species.json', 'roles.json', 'looks', 'place_types'):
        full = os.path.join(data_dir, name)
        files = [full] if os.path.isfile(full) else sorted(os.path.join(full, f) for f in os.listdir(full)) if os.path.isdir(full) else []
        for path in files:
            if not path.endswith('.json'):
                continue
            data = read_json(path)
            label = os.path.relpath(path, data_dir)
            for where, entry in walk_entries(data):
                if entry.get('kind') not in KINDS:
                    problems.append(f'{label} {where}: kind "{entry.get("kind")}" is not one of {", ".join(KINDS)}')
                if not entry.get('source'):
                    problems.append(f'{label} {where}: no source')
            if name == 'roles.json':
                for group in ('classes', 'roles'):
                    for key, spec in data[group].items():
                        if spec.get('kind') not in KINDS or not spec.get('source'):
                            problems.append(f'{label} {group}.{key}: needs a kind and a source')
            if name == 'real_world_facts.json':
                for fact in data['facts']:
                    for field in ('id', 'dimension', 'min', 'max', 'unit', 'kind', 'source', 'confidence'):
                        if field not in fact:
                            problems.append(f'{label} fact {fact.get("id")}: no {field}')
                    if fact.get('confidence') not in ('strong', 'weak', 'guess'):
                        problems.append(f'{label} fact {fact.get("id")}: confidence must be strong, weak or guess')
            if name == 'dial_table.json':
                for layer, spec in list(data['layers'].items()) + list(data.get('growth', {}).items() and [('growth', data['growth'])]):
                    for dial in spec['dials']:
                        for field in ('name', 'lo', 'hi', 'default', 'unit', 'doc', 'kind', 'source'):
                            if field not in dial:
                                problems.append(f'{label} {layer}.{dial.get("name")}: no {field}')
            if name == 'species.json':
                for key, spec in data['kinds'].items():
                    if spec.get('kind') not in KINDS or not spec.get('source'):
                        problems.append(f'{label} kinds.{key}: needs a kind and a source')
            if name in ('looks', 'place_types'):
                if data.get('kind') not in KINDS or not data.get('source'):
                    problems.append(f'{label}: needs a kind and a source')
    polyhaven = os.path.join(data_dir, 'polyhaven_choices.json')
    if os.path.exists(polyhaven):
        for group in ('textures', 'models'):
            for item in read_json(polyhaven)[group]:
                if not item.get('date_read'):
                    problems.append(f'polyhaven_choices.json {item.get("slug")}: no date_read')
    return problems


# ---------------------------------------------------------------- 2. the data agree
def recipe_ids(place_kit):
    """The recipe ids in surfaces/heights.py, read without importing it (the file needs numpy only, but reading it is enough)."""
    path = os.path.join(place_kit, 'place_kit', 'surfaces', 'heights.py')
    if not os.path.exists(path):
        return None
    tree = ast.parse(open(path, encoding='utf-8').read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RECIPES' for t in node.targets) and isinstance(node.value, ast.Dict):
            return {key.value for key in node.value.keys if isinstance(key, ast.Constant)}
    return set()


def check_agreement(place_kit):
    data_dir = os.path.join(place_kit, 'data')
    problems = []
    roles = read_json(os.path.join(data_dir, 'roles.json'))
    surfaces = read_json(os.path.join(data_dir, 'surfaces.json'))['surfaces']
    facts = {f['id'] for f in read_json(os.path.join(data_dir, 'real_world_facts.json'))['facts']}
    recipes = recipe_ids(place_kit)
    for class_id, spec in roles['classes'].items():
        for key in ('requires', 'wanted'):
            for treatment in spec.get(key, []):
                if treatment not in TREATMENTS:
                    problems.append(f'roles.json class {class_id}: "{treatment}" is not a treatment')
    for role_id, spec in roles['roles'].items():
        if role_id.split('.')[0] != spec['class']:
            problems.append(f'roles.json {role_id}: its class "{spec["class"]}" does not match the name')
        if spec['class'] not in roles['classes']:
            problems.append(f'roles.json {role_id}: class "{spec["class"]}" does not exist')
        if spec['class'] not in NO_SURFACE_CLASSES and spec['surface'] not in surfaces:
            problems.append(f'roles.json {role_id}: surface "{spec["surface"]}" is not in surfaces.json')
        for fact in spec.get('scale', []):
            if fact not in facts:
                problems.append(f'roles.json {role_id}: scale fact "{fact}" is not in real_world_facts.json')
        for layer in spec.get('dials', {}):
            if layer not in LAYERS and layer not in TREATMENTS:
                problems.append(f'roles.json {role_id}: dial "{layer}" is not a wear layer')
        for treatment in spec.get('exempt', {}):
            if treatment not in TREATMENTS:
                problems.append(f'roles.json {role_id}: exempt "{treatment}" is not a treatment')
        for pattern in spec.get('name_hints', []) + spec.get('weak_name_hints', []):
            try:
                re.compile(pattern)
            except re.error as error:
                problems.append(f'roles.json {role_id}: name hint {pattern!r} is not a valid pattern ({error})')
    for surface_id, spec in surfaces.items():
        if recipes is not None and spec['height_recipe'] not in recipes:
            problems.append(f'surfaces.json {surface_id}: height recipe "{spec["height_recipe"]}" is not in heights.RECIPES')
        if spec.get('uv_method') not in ('box', 'planar', 'plank'):
            problems.append(f'surfaces.json {surface_id}: uv_method "{spec.get("uv_method")}" is not box, planar or plank')
    for look_id in ('kept', 'lived_in', 'neglected', 'derelict'):
        look = read_json(os.path.join(data_dir, 'looks', f'{look_id}.json'))
        for layer in LAYERS:
            if layer not in look['layers']:
                problems.append(f'looks/{look_id}.json: no layer "{layer}"')
    dial_layers = set(read_json(os.path.join(data_dir, 'dial_table.json'))['layers'])
    for layer in LAYERS:
        if layer not in dial_layers:
            problems.append(f'dial_table.json: no layer "{layer}"')
    for filename in sorted(os.listdir(os.path.join(data_dir, 'place_types'))):
        preset = read_json(os.path.join(data_dir, 'place_types', filename))
        for role_id in preset.get('roles_likely', []):
            if role_id not in roles['roles']:
                problems.append(f'place_types/{filename}: role "{role_id}" is not in roles.json')
        for fact in preset.get('facts', []):
            if fact not in facts:
                problems.append(f'place_types/{filename}: fact "{fact}" is not in real_world_facts.json')
        for entry in preset.get('allowed_off', []):
            for treatment in entry['treatments']:
                if treatment not in TREATMENTS:
                    problems.append(f'place_types/{filename}: allowed_off "{entry["id"]}" names "{treatment}", which is not a treatment')
    species = read_json(os.path.join(data_dir, 'species.json'))
    for key, spec in species['kinds'].items():
        for colour in spec['colours']:
            if colour not in species['palette']:
                problems.append(f'species.json {key}: colour "{colour}" is not in the palette')
    # the examples must agree with the data too
    example_dir = os.path.join(data_dir, 'examples')
    if os.path.isdir(example_dir):
        sys.path.insert(0, place_kit)
        try:
            from place_kit import settings_file
            for filename in sorted(os.listdir(example_dir)):
                if filename.endswith('place-settings.json'):
                    for problem in settings_file.validate(read_json(os.path.join(example_dir, filename))):
                        problems.append(f'examples/{filename}: {problem}')
        finally:
            sys.path.pop(0)
    return problems


# ---------------------------------------------------------------- 3. required treatments are made and tested
def check_required_are_real(place_kit, kit_root):
    problems = []
    data_dir = os.path.join(place_kit, 'data')
    roles = read_json(os.path.join(data_dir, 'roles.json'))
    treatments = read_json(os.path.join(data_dir, 'treatments.json'))['treatments']
    tests_dir = os.path.join(kit_root, 'calculators', 'tests')
    required = set()
    for spec in roles['classes'].values():
        required.update(spec.get('requires', []))
    for treatment in sorted(required):
        meta = treatments.get(treatment)
        if meta is None:
            problems.append(f'treatments.json has no entry for the required treatment "{treatment}"')
            continue
        made = meta['made_by']
        path = os.path.join(place_kit, 'place_kit', made['module'])
        if not os.path.exists(path):
            problems.append(f'{treatment}: made_by file {made["module"]} is not there')
        else:
            source = open(path, encoding='utf-8').read()
            if not re.search(rf'^def {re.escape(made["function"])}\(', source, re.M):
                problems.append(f'{treatment}: made_by function {made["function"]} is not in {made["module"]}')
        tested = meta['tested_by']
        test_path = os.path.join(tests_dir, tested['file'])
        if not os.path.exists(test_path):
            problems.append(f'{treatment}: the test file {tested["file"]} is not there')
        elif tested['phrase'] not in open(test_path, encoding='utf-8').read():
            problems.append(f'{treatment}: the test {tested["file"]} does not contain the phrase "{tested["phrase"]}"')
    return problems


# ---------------------------------------------------------------- 4. no place nouns in code
def code_files(place_kit):
    for path in all_text_files(os.path.join(place_kit, 'place_kit'), ('.py',)):
        yield path
    for name in ('place_command.py', 'blender_run.py', 'check_presets.py'):
        path = os.path.join(place_kit, name)
        if os.path.exists(path):
            yield path


def check_place_nouns(place_kit):
    banned = read_json(os.path.join(place_kit, 'data', 'banned_place_nouns.json'))['banned_nouns']
    pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in banned) + r')s?\b', re.I)
    problems = []
    for path in code_files(place_kit):
        for number, line in enumerate(open(path, encoding='utf-8'), start=1):
            found = pattern.search(line)
            if found:
                problems.append(f'{os.path.relpath(path, place_kit)} line {number}: the place word "{found.group(0)}" (code must work for any place)')
    return problems


# ---------------------------------------------------------------- 5. imports that Blender cannot satisfy
def check_blender_imports(place_kit):
    problems = []
    root = os.path.join(place_kit, 'place_kit')
    for path in all_text_files(root, ('.py',)):
        relative = os.path.relpath(path, root).replace(os.sep, '/')
        if relative in PLAIN_PYTHON_FILES:
            continue
        tree = ast.parse(open(path, encoding='utf-8').read())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [a.name.split('.')[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules = [node.module.split('.')[0]]
            for module in modules:
                if module in ('PIL', 'cv2', 'scipy', 'skimage'):
                    problems.append(f'{relative} line {node.lineno}: imports {module}, which Blender\'s own Python does not have')
    return problems


# ---------------------------------------------------------------- 6. privacy and machine-specific text
PRIVACY_PATTERNS = (
    (re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'), 'an email-like string'),
    (re.compile(r'\b[0-9a-f]{24,}\b'), 'a long hex id'),
    (re.compile(r'\b[Rr][Pp][Aa]_[A-Za-z0-9]{16,}\b'), 'a rented-card key'),
    (re.compile(r'\bsk-[A-Za-z0-9]{20,}\b'), 'an API key'),
    (re.compile(r'''(api_?key|apikey|secret|token|password|endpoint_?id)["']?\s*[:=]\s*["'][A-Za-z0-9_\-]{16,}["']''', re.I), 'a key-looking value'),
)


def scan_text_for_private_things(path, label=None):
    problems = []
    label = label or path
    try:
        text = open(path, encoding='utf-8').read()
    except (UnicodeDecodeError, OSError):
        return problems
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern, what in PRIVACY_PATTERNS:
            found = pattern.search(line)
            if found:
                problems.append(f'{label} line {number}: {what}')
        for piece in PRIVATE_PIECES:
            if piece in line:
                problems.append(f'{label} line {number}: "{piece}" (a personal or machine-specific name)')
        if SETTINGS_FOLDER_PATTERN.search(line) and not re.search(r"['\"`]\.run" + r"pod['\"`]", line):
            problems.append(f'{label} line {number}: the rented-card settings folder used as a path')
    return problems


def extra_places(kit_root):
    """Other plugin files the scan covers when they exist (the new skill, agents, workflow, wrapper, calculators)."""
    plugin = os.path.dirname(kit_root)
    found = []
    for relative in ('skills/surfaces-wear-and-construction', 'agents', 'workflows/build-a-place.js', 'bin/explainer-film-place',
                     'kit/calculators/place_audit_check.py', 'kit/calculators/picture_measures.py'):
        path = os.path.join(plugin, relative)
        if os.path.isdir(path):
            for file_path in all_text_files(path):
                if relative != 'agents' or os.path.basename(file_path).startswith('place-'):
                    found.append(file_path)
        elif os.path.isfile(path):
            found.append(path)
    return found


def check_privacy(place_kit, kit_root):
    problems = []
    plugin = os.path.dirname(kit_root)
    for path in all_text_files(place_kit):
        problems += scan_text_for_private_things(path, os.path.relpath(path, plugin))
    for path in extra_places(kit_root):
        problems += scan_text_for_private_things(path, os.path.relpath(path, plugin))
    return problems


def run_all(kit_root=None):
    """[(group name, problems list)] for every group (an empty list means PASS)."""
    kit_root = kit_root or KIT_ROOT_DEFAULT
    place_kit = os.path.join(kit_root, 'place-kit')
    data_dir = os.path.join(place_kit, 'data')
    return [
        ('every number in data/*.json carries a kind and a source', check_kind_and_source(data_dir)),
        ('the data agree with each other (roles, surfaces, recipes, looks, place types, examples)', check_agreement(place_kit)),
        ('every REQUIRED treatment is made by a real function and proved by a test', check_required_are_real(place_kit, kit_root)),
        ('no kit code names a kind of place', check_place_nouns(place_kit)),
        ('no code that runs inside Blender imports Pillow, OpenCV or SciPy', check_blender_imports(place_kit)),
        ('nothing private or machine-specific is written in the kit, the new skill, agents, workflow or wrapper', check_privacy(place_kit, kit_root)),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description='Checks the place kit\'s data and code (kinds and sources, agreement between data files, required treatments are made and tested, '
                                                 'no place words in code, no outside imports in Blender code, nothing private). See the note at the top of this file.')
    parser.add_argument('--kit-root', help='the kit folder (holds place-kit, calculators and film-settings.json); default: the kit this file is in')
    parser.add_argument('--json', action='store_true', help='print the result as JSON')
    args = parser.parse_args(argv)
    results = run_all(args.kit_root)
    failed = [name for name, problems in results if problems]
    if args.json:
        print(json.dumps({'groups': [{'check': name, 'problems': problems} for name, problems in results], 'verdict': 'fail' if failed else 'pass'}, indent=1))
    else:
        for name, problems in results:
            print(('FAIL ' if problems else 'PASS ') + name)
            for problem in problems[:12]:
                print('     ' + problem)
            if len(problems) > 12:
                print(f'     ... and {len(problems) - 12} more')
        print(f'{len(results) - len(failed)} of {len(results)} groups passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
