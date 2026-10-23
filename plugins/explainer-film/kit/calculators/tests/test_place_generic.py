"""What this does: keeps the plugin's place parts GENERAL. A place is built from the plain words of whoever asks, so nothing in the
plugin may be written around one particular request, or a model that is tested with such a request would only be reading its own
answer back. This test checks four things:
1. A short list of words that belong to one trade and one period (kept here only as SHA-256 hashes, because this test must not carry
   the words it keeps out) does not appear in any text of the parts of the plugin that are written for places: the skill, the
   agents, the hook, the workflow, the place kit (code, data and notes), the place tests and their fixtures, and the README.
2. No file of the plugin has a name that pairs two place words (an example file is named after a real place that was built).
3. The place presets are even-handed: the village preset lists as many stone, brick, tile or slate things as timber, thatch, forest or dirt
   things, starts from the same state as the generic preset, and its notes name none of the leaning words.
4. The example files in the kit are about places this project really built (a canal lock), and the skill's worked-example file names
   both real places and says what was measured and what was judged.
It uses only the Python standard library.
Run: python3 kit/calculators/tests/test_place_generic.py
"""
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, PLUGIN  # noqa: E402

check = Checker('place parts stay general: no word of one trade and period, even-handed presets, real worked examples')

# SHA-256 of single lower-case words (letters only). A word is found by hashing every word of a text.
KEPT_OUT = {
    '18cee5777a29d968d75a65b5a8fb7c4dc5a071cb1053c00b9005eafe8e9b8604', 'c46cf71604b2c0a7c4f53ef648438cca4d2cdef53e04f60b6856f462fa0e3551',
    '13bfabb07807921f6ce3a61897621a33098723b538b2db5b7fa82cf6adf0b45e', '19cafbf1323898a4513fc805f49a63439082ce88724562023eb48fe79209ca1e',
    'c670b23a57410814670c1905e62ff9e31a93d5eefb523fc5728a4c9a87896a12', 'f0672e740dedec60d93c8fada6cbb8e4a562be704c1fc9d27684e9c60b96aea0',
    '2cf5134c9cb48e57227b4c122da25de32f30e55438e8b54ae8c72637caaa36c8', '05b3b66d444b8ed761948161aa8e4b986d2df0588facc556b4c97dc60d44c286',
    'fd62862b6dc213bee77c2badd6311528253c6cb3107e03c16051aa15584eca1c', 'a2a52f3eba927ee4e451df164d0c2e0e42bef8c04713d493140f50620696a789',
}
TEXT_EXTENSIONS = {'.md', '.py', '.json', '.js', '.mjs', '.txt', '.sh'}
PLACE_PARTS = [
    'skills/surfaces-wear-and-construction/**', 'agents/place-*.md', 'hooks/**', 'workflows/build-a-place.js', 'README.md',
    'kit/place-kit/**', 'kit/calculators/place_audit_check.py', 'kit/calculators/picture_measures.py', 'kit/calculators/README.md',
    'kit/calculators/tests/test_place_*.py', 'kit/calculators/tests/test_build_a_place_workflow.py', 'kit/calculators/tests/test_picture_measures.py',
    'kit/calculators/tests/test_preflight_place.py', 'kit/calculators/tests/test_model_kit_surfaces.py', 'kit/calculators/tests/workflow_harness.mjs',
    'kit/calculators/tests/fixtures/place/**', 'kit/calculators/tests/fixtures/place-workflow/**', 'kit/calculators/tests/fixtures/place-skills/**',
    'kit/docs/LLM tips and tricks.md',
]


def files_of(patterns):
    found = set()
    for pattern in patterns:
        for path in glob.glob(os.path.join(PLUGIN, pattern), recursive=True):
            if os.path.isfile(path) and os.path.splitext(path)[1] in TEXT_EXTENSIONS:
                found.add(path)
    return sorted(found)


def kept_out_words(text):
    """The words of a text whose hash is on the list."""
    found = set()
    for word in set(re.findall(r'[a-z]+', text.lower())):
        if hashlib.sha256(word.encode()).hexdigest() in KEPT_OUT:
            found.add(word)
    return found


def read(path):
    with open(path, encoding='utf-8', errors='replace') as handle:
        return handle.read()


# ------------------------------------------------------------------------------------------ 1. the kept-out words
texts = files_of(PLACE_PARTS)
this_file = os.path.abspath(__file__)
hits = {}
for path in texts:
    found = kept_out_words(read(path))
    if found:
        hits[os.path.relpath(path, PLUGIN)] = len(found)
check.true(f'none of the kept-out words is in any of the {len(texts)} text files of the place parts', not hits, details=', '.join(sorted(hits)[:6]) or 'none found')
check.true('  (the check can fail: a text made here with one of the words in it is caught, and one without is not)',
           bool(kept_out_words('a plain sentence with ' + 'dun' + 'g in it')) and not kept_out_words('a plain sentence about a canal lock'))
check.true('  (the scan reaches the skill, an agent, the hook, the workflow and the data)', all(any(name in path for path in texts) for name in (
    'the-required-steps.md', 'place-planner.md', 'place-reminder.py', 'build-a-place.js', 'roles.json')))

# ------------------------------------------------------------------------------------------ 2. file names
name_problems = []
for path in glob.glob(os.path.join(PLUGIN, '**', '*'), recursive=True):
    if '.git' + os.sep in path or os.sep + 'node_modules' + os.sep in path:
        continue
    base = os.path.basename(path).lower()
    if 'forest' in base and 'village' in base:
        name_problems.append(os.path.relpath(path, PLUGIN))
check.true('no file of the plugin is named after a village in a forest', not name_problems, details=', '.join(name_problems) or 'none')

# ------------------------------------------------------------------------------------------ 3. even-handed presets
village = json.load(open(os.path.join(KIT, 'place-kit', 'data', 'place_types', 'village.json'), encoding='utf-8'))
generic = json.load(open(os.path.join(KIT, 'place-kit', 'data', 'place_types', 'generic.json'), encoding='utf-8'))
LEANING = re.compile(r'thatch|timber|forest|dirt|log\b')
EVEN = re.compile(r'stone|brick|tile|slate|paving|plaster')
leaning = [role for role in village['roles_likely'] if LEANING.search(role)]
even = [role for role in village['roles_likely'] if EVEN.search(role)]
check.true('the village preset lists at least as many stone, brick, tile, slate, paving or plaster roles as timber, thatch, forest or dirt roles',
           len(even) >= len(leaning), details=f'{len(even)} against {len(leaning)}')
check.equal('the village preset starts from the generic state (it does not assume damp ground under trees)', village['default_state'], generic['default_state'])
check.equal('...and from the same look', village['default_look'], generic['default_look'])
words_in_notes = re.findall(r'[a-z]+', (village['notes'] + ' ' + village['about']).lower())
check.true('the village preset names no forest, no road with ruts and no one roof material alone in its notes',
           'forest' not in words_in_notes and 'ruts' not in words_in_notes and not ('thatch' in words_in_notes and 'tile' not in words_in_notes),
           details=village['notes'][:100])
check.true('the village preset facts are the plain ones (a door, a roof pitch, a wall), none about carts or animals',
           all(fact in ('door_height', 'door_width', 'roof_pitch', 'wall_thickness') for fact in village['facts']), details=', '.join(village['facts']))

# ------------------------------------------------------------------------------------------ 4. the examples are real places
settings_example = json.load(open(os.path.join(KIT, 'place-kit', 'data', 'examples', 'canal-lock-place-settings.json'), encoding='utf-8'))
check.true('the kit example settings are the canal lock that was really built', settings_example['place'] == 'canal lock side' and settings_example['owners'] == 'canal-lock-ownership.json')
other_examples = sorted(os.path.basename(p) for p in glob.glob(os.path.join(KIT, 'place-kit', 'data', 'examples', '*')))
check.equal('the kit holds exactly the two canal lock example files and no other example place', other_examples, ['canal-lock-ownership.json', 'canal-lock-place-settings.json'])
worked = read(os.path.join(PLUGIN, 'skills', 'surfaces-wear-and-construction', 'worked-examples-garden-and-canal-lock.md'))
check.true('the worked-example file names both real places and says what was measured and what was judged',
           'Japanese garden' in worked and 'canal lock' in worked and '**measured**' in worked and '**judged**' in worked and worked.count('measured') >= 10)
skill = read(os.path.join(PLUGIN, 'skills', 'surfaces-wear-and-construction', 'SKILL.md'))
check.true('the skill points to the worked-example file and to no other worked example', 'worked-examples-garden-and-canal-lock.md' in skill and not re.search(r'a-[a-z-]+-example\.md', skill))
check.true('the skill still says the pass and the construction check are REQUIRED for every place (the routing is not weakened)',
           'REQUIRED for every place, set or prop you build in Blender' in skill and 'It must PASS before you draw, render or paint anything' in skill)
check.finish()
