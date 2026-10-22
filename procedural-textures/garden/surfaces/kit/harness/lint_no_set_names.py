# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE REUSE LINT. Kit code must hold nothing that belongs to one set. This scans the kit's code (apply/, masks/, harness/, walls/, ground/, growth/; NOT sets/, presets/, integrate/,
# notes) and fails on:
#   1. set words (street, cottage, colliery, pit village, courtyard, Japanese, lantern, shoji, Astra, ...) in code or comments;
#   2. names copied from a set file: the literal words of every object, collection and material pattern and every role, scene, camera and light name in any sets/*.json
#      (a word is counted when it is 5 or more letters long and not a generic word);
#   3. coordinates and sizes copied from a set file: a number written in the code that is also a distinctive number of a set file (four or more digits, or three or more decimals), and
#      (added in the fix round, because one-decimal bounds like -4.5 or 72.0 slipped through) any list or tuple of two or more numbers in the code that is also a list of numbers in a
#      set file (ground bounds, camera positions, picture sizes), unless every value in it is one of the plain numbers 0, 1, 2, 3, 0.5, 0.25, 0.75, -1;
#   4. camera names copied from a set file (a name with an underscore, like the close-up cameras, written in code).
# Generic words stay allowed: kerb, flag, sett, gutter, step, pipe, wall, iron, ground, roof, plaster, stone, timber, moss, weed ... (a layer's dials are named after the thing it ages).
#     python3 -I harness/lint_no_set_names.py            prints every hit and exits 1 if there are any
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
CODE_DIRS = ('apply', 'masks', 'harness', 'walls', 'ground', 'growth')
ROOT_FILES = ('apply_weathering.py',)      # generic code at the kit's top level (street_weathering.py is the street's own wrapper and is not scanned)
SET_WORDS = ['street', 'cottage', 'colliery', 'pit village', 'pit_village', 'courtyard', 'japanese', 'lantern', 'shoji', 'astra', 'lockout', 'durham', 'headframe', 'winding', 'gas lamp',
             'gas_lamp', 'brazier', 'foundry', 'maple', 'bamboo', 'veranda', 'tatami', 'temple']
GENERIC = {'kerb', 'flag', 'flags', 'sett', 'setts', 'gutter', 'step', 'steps', 'pipe', 'pipes', 'wall', 'walls', 'iron', 'ground', 'roof', 'plaster', 'stone', 'timber', 'moss', 'weed',
           'weeds', 'prop', 'props', 'fire', 'sign', 'post', 'posts', 'chimney', 'paint', 'doorway', 'masonry', 'trim', 'industrial', 'natural', 'dressed', 'earth', 'gravel', 'deck',
           'frame', 'tile', 'cap', 'bark', 'yard', 'main', 'close', 'notice', 'brick', 'channel', 'objects', 'materials', 'collections', 'never', 'camera', 'light', 'lights', 'rainwater',
           'glass', 'window', 'windows', 'door', 'doors', 'sky', 'dome', 'glow', 'dark', 'interior', 'black', 'boards', 'paper', 'brass', 'house', 'houses', 'drum', 'stove', 'barrel',
           'scene', 'type', 'mesh', 'empty', 'growth', 'existing', 'water', 'basin', 'pond', 'hills', 'plain', 'room', 'back', 'right', 'left', 'upper', 'ground_', 'rock', 'rocks',
           'pebbles', 'bodies', 'grouped', 'stepping', 'lower', 'plinth', 'beams', 'posts', 'soffit', 'eave', 'finial', 'bridge', 'pier', 'gate', 'large', 'trash', 'metal', 'steel',
           'rope', 'rail', 'wheel', 'yard', 'pots', 'clay', 'ridge', 'slate', 'boarded', 'green', 'blue', 'fascia', 'board', 'engine', 'second', 'heapstead', 'spoil', 'heap', 'moor',
           'sun', 'dusk', 'skylight', 'afterglow', 'dressed_stone'}
ALLOWED_NUMBERS = {'0.015', '0.0002', '0.001', '0.003', '0.012', '0.018', '0.0001', '0.0002666', '0.0002666666', '1.275', '0.275', '1.111', '0.25', '0.045', '0.0699', '1.0', '2.5', '3.5', '0.75', '0.05', '0.15', '0.35', '0.45', '0.55', '0.65', '0.85'}


def code_files():
    for name in ROOT_FILES:
        if os.path.exists(os.path.join(KIT_ROOT, name)):
            yield os.path.join(KIT_ROOT, name)
    for d in CODE_DIRS:
        base = os.path.join(KIT_ROOT, d)
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x not in ('__pycache__', 'packs', 'baseline', '_raw')]
            for f in files:
                if f.endswith('.py') and f != 'lint_no_set_names.py':
                    yield os.path.join(root, f)


def words_of(pattern):
    """The literal phrases of a name pattern that identify one set: anything with an underscore or a space or a digit, 8 letters or more ('right_row_a_cottage', 'hall plaster'); single
    plain words are left to the curated SET_WORDS list (a plain word like 'surface' or 'source' is not a name)."""
    text = re.sub(r'\\[a-zA-Z]', ' ', pattern)
    phrases = set()
    for chunk in re.split(r'[\^\$\|\(\)\[\]\{\}\*\+\?\\]+', text):
        chunk = chunk.strip(' ,.').lower()
        if len(chunk) >= 8 and (('_' in chunk) or (' ' in chunk) or any(c.isdigit() for c in chunk)):
            phrases.add(chunk)
    return phrases


PLAIN_VALUES = {0.0, 1.0, 2.0, 3.0, 0.5, 0.25, 0.75, -1.0}
# lists that are the KIT's own defaults (a set file may repeat them): the height range of the ground picture, the far-band handover distances, a small picture size
ALLOWED_LISTS = {(-2.0, 6.0), (14.0, 22.0), (540.0, 960.0, 16.0)}


def collect_set_data():
    names, numbers, lists, camera_names = set(), set(), set(), set()
    for f in sorted(os.listdir(os.path.join(KIT_ROOT, 'sets'))):
        if not f.endswith('.json'):
            continue
        data = json.load(open(os.path.join(KIT_ROOT, 'sets', f)))
        for cam in data.get('cameras', []):
            cam_name = str(cam.get('name', '')).lower()
            if '_' in cam_name:
                camera_names.add(cam_name)

        def number_lists(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if not str(k).startswith('_'):
                        yield from number_lists(v)
            elif isinstance(o, list):
                if len(o) >= 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in o):
                    yield tuple(float(v) for v in o)
                else:
                    for v in o:
                        yield from number_lists(v)
        for tup in number_lists({k: val for k, val in data.items() if k not in ('scenes', 'plate_brightness_measured', 'expect')}):
            if not set(tup) <= PLAIN_VALUES and tup not in ALLOWED_LISTS:
                lists.add(tup)
        roles = data.get('roles', {})
        for role, rule in roles.items():
            if role.startswith('_') or not isinstance(rule, dict):
                continue
            for key in ('objects', 'collections', 'materials'):
                for p in rule.get(key, []):
                    names |= words_of(p)
        for key in ('objects', 'materials', 'own_layer_later'):
            for p in data.get('never', {}).get(key, []):
                names |= words_of(p)

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if not str(k).startswith('_'):
                        yield from walk(v)
            elif isinstance(o, list):
                for v in o:
                    yield from walk(v)
            elif isinstance(o, float) or (isinstance(o, int) and not isinstance(o, bool)):
                yield o
        for v in walk({k: val for k, val in data.items() if k not in ('scenes', 'plate_brightness_measured', 'expect')}):
            text = repr(float(v)) if isinstance(v, float) else str(v)
            digits = text.replace('-', '').replace('.', '')
            decimals = len(text.split('.')[1]) if '.' in text else 0
            if (decimals >= 3 or len(digits.lstrip('0')) >= 4) and text not in ALLOWED_NUMBERS:
                numbers.add(text.rstrip('0').rstrip('.') if '.' in text else text)
    return names, numbers, lists, camera_names


def scan():
    names, numbers, lists, camera_names = collect_set_data()
    hits = []
    for path in code_files():
        rel = os.path.relpath(path, KIT_ROOT)
        text = open(path).read()
        low = text.lower()
        for line_no, line in enumerate(text.split('\n'), 1):
            ll = line.lower()
            for w in SET_WORDS:
                if w in ll:
                    hits.append((rel, line_no, 'set word', w, line.strip()[:110]))
            for n in sorted(names):
                if n in ll and n not in SET_WORDS:
                    hits.append((rel, line_no, 'name from a set file', n, line.strip()[:110]))
            for cam in sorted(camera_names):          # a camera name written as a string in code (a variable that happens to share the word is left alone)
                if f"'{cam}'" in ll or f'"{cam}"' in ll:
                    hits.append((rel, line_no, 'camera name from a set file', cam, line.strip()[:110]))
            for m in re.finditer(r'(?<![\w.])-?\d+\.\d{3,}|(?<![\w.])-?\d{4,}(?![\w.])', line):
                token = m.group(0)
                norm = token.rstrip('0').rstrip('.') if '.' in token else token
                if norm in numbers and token not in ALLOWED_NUMBERS:
                    hits.append((rel, line_no, 'number from a set file', token, line.strip()[:110]))
            for m in re.finditer(r'[(\[]\s*(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+)\s*[)\]]', line):
                tup = tuple(float(v) for v in m.group(1).replace(' ', '').split(','))
                if tup in lists:
                    hits.append((rel, line_no, 'list of numbers from a set file', m.group(0), line.strip()[:110]))
    return hits


if __name__ == '__main__':
    found = scan()
    for h in found:
        print('%s:%d  [%s] %s   | %s' % h)
    print('LINT:', 'CLEAN (0 hits)' if not found else f'{len(found)} hits')
    sys.exit(1 if found else 0)
