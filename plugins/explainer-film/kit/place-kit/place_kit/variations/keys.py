"""What this does: the WORDS of a variation: which settings a variation may change, how far apart two settings are, and how a setting reads in plain words on the contact sheet.
Plain Python (standard library only); no Blender needed.

A variation changes a place that is already finished and saved. It names the change with a "set" table of dotted keys:
    master                        0 to 2     scales every wear layer of the saved scene (1 = as saved; 0 gives exactly the picture without wear; 2 = twice as strong)
    amount.<layer>                0 to 2     scales one wear layer of the saved scene (1 = as saved; 0 = that layer does nothing; 1.6 = 60 percent stronger)
    dials.<layer>.<dial>          the dial's own range (from data/dial_table.json): cover, film, foot_height_metres, puddles ... ; dials.<layer>.seed picks another random pattern
    state                         dry, damp or wet   (rewrites the wetness amount on every object)
    look                          kept, lived_in, neglected or derelict   (rewrites every layer's amount on every object from that look)
The layers are the nine of the wear pass: dirt, grime, weathering, rust, wetness, cracks_and_chips, edge_wear, moss_and_algae, rubbish.
Anything else (the shape of a tree, the number of boards, a new prop) goes in a small SCRIPT HOOK: a Python file with apply(variation) that runs inside Blender after the scene is reset; its
numbers go in "args". Numbers in args may carry their range in the variations file ("ranges": {"branch_count": [3, 12]}); without a range the difference is read as a share of the larger value.

Measurably different, BEFORE drawing: two variations are different enough when at least one setting differs by place_variations.settings_difference_min_share (8 percent) of that setting's range
(a number in a script hook with no range: place_variations.number_without_range_difference_min_share, 25 percent of the larger value; a word such as wet and dry, or a seed: any difference counts).
A setting a variation does not name stays as the saved scene has it. For master and amount.<layer> the saved scene is exactly 1 (they scale what is saved). For a dial the saved value
is read from the scene by a free scout (`variations scout`, see spec.py) when there is one; without a scout it is read here as the dial's default (the pictures drawn afterwards decide
whether that guess was right).

A concrete example: {"dials.moss_and_algae.cover": 0.5} and {"dials.moss_and_algae.cover": 0.55} are 5 percent of the range apart, so the second is a near-duplicate; 0.5 and 0.9 are 40 percent apart.
{"amount.moss_and_algae": 1.6} is 30 percent of the range (0 to 2) away from the saved scene (1.0), so it is far enough; 1.1 is only 5 percent away and would draw the baseline again.
"""
import math
import re

from .. import house_numbers as numbers, names, settings_file

CATEGORICAL = ('state', 'look')


class KeyProblem(Exception):
    """A key or a value in a variation cannot be used (exit 2); the sentence says what is allowed."""


def known_keys_text():
    layers = ', '.join(names.LAYER_ORDER)
    return (f'master; amount.<layer>; dials.<layer>.<dial>; state ({", ".join(names.STATES)}); look ({", ".join(names.LOOKS)}). The layers are: {layers}. '
            'See the note at the top of place_kit/variations/keys.py; `explainer-film-place variations keys` lists every dial with its range.')


def amount_scale_max():
    """The top of master and amount.<layer> (house number place_variations.amount_scale_max): they SCALE what the saved scene has, so 1 is the saved scene."""
    return float(numbers.value('place_variations.amount_scale_max'))


def dial_rows(layer):
    """{dial: (low, high, default)} for a layer, from the dial table (the common dials amount and seed included)."""
    table = settings_file.dial_table()
    rows = list(table['common']) + list(table['layers'][layer]['dials'])
    return {row['name']: (float(row['lo']), float(row['hi']), float(row['default'])) for row in rows}


def all_dial_lines():
    """Plain lines naming every key a variation may set, with its range and default."""
    top = amount_scale_max()
    lines = [f'master: 0 to {top:g} (1 = every wear layer as the saved scene has it; 0 = no wear)', 'state: ' + ', '.join(names.STATES), 'look: ' + ', '.join(names.LOOKS)]
    for layer in names.LAYER_ORDER:
        lines.append(f'amount.{layer}: 0 to {top:g} (1 = as the saved scene has it; 0 = off; {top:g} = {top:g} times as strong)')
    for layer in names.LAYER_ORDER:
        for dial, (low, high, default) in dial_rows(layer).items():
            if dial == 'amount':
                continue
            lines.append(f'dials.{layer}.{dial}: {low:g} to {high:g} (default {default:g})')
    return lines


def describe_key(key):
    """What a key is, as a dictionary: kind, layer, dial, low, high, default, categorical (True for words and seeds), choices."""
    parts = key.split('.')
    if key == 'master':
        return {'kind': 'master', 'layer': None, 'dial': None, 'low': 0.0, 'high': amount_scale_max(), 'default': 1.0, 'categorical': False, 'choices': None}
    if key == 'state':
        return {'kind': 'state', 'layer': None, 'dial': None, 'low': None, 'high': None, 'default': None, 'categorical': True, 'choices': list(names.STATES)}
    if key == 'look':
        return {'kind': 'look', 'layer': None, 'dial': None, 'low': None, 'high': None, 'default': None, 'categorical': True, 'choices': list(names.LOOKS)}
    if len(parts) == 2 and parts[0] == 'amount':
        if parts[1] not in names.LAYER_ORDER:
            raise KeyProblem(f'the key "{key}" names the layer "{parts[1]}", which is not one of {", ".join(names.LAYER_ORDER)}')
        return {'kind': 'amount', 'layer': parts[1], 'dial': 'amount', 'low': 0.0, 'high': amount_scale_max(), 'default': 1.0, 'categorical': False, 'choices': None}
    if len(parts) == 3 and parts[0] == 'dials':
        layer, dial = parts[1], parts[2]
        if layer not in names.LAYER_ORDER:
            raise KeyProblem(f'the key "{key}" names the layer "{layer}", which is not one of {", ".join(names.LAYER_ORDER)}')
        rows = dial_rows(layer)
        if dial not in rows or dial == 'amount':
            raise KeyProblem(f'the layer "{layer}" has no dial "{dial}" (its dials: {", ".join(name for name in rows if name != "amount")}; write the layer\'s strength as amount.{layer})')
        low, high, default = rows[dial]
        return {'kind': 'dial', 'layer': layer, 'dial': dial, 'low': low, 'high': high, 'default': default, 'categorical': dial == 'seed', 'choices': None}
    raise KeyProblem(f'"{key}" is not a setting a variation can change. Allowed: {known_keys_text()}')


def flatten_set(raw):
    """A "set" written flat ({"dials.dirt.film": 0.3}) or nested ({"dials": {"dirt": {"film": 0.3}}, "amount": {"dirt": 0.5}}) as one flat dictionary."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise KeyProblem('"set" must be an object of settings, for example {"dials.moss_and_algae.cover": 0.8}')
    flat = {}

    def walk(prefix, value):
        if isinstance(value, dict):
            for key, inner in value.items():
                walk(f'{prefix}.{key}' if prefix else str(key), inner)
        else:
            flat[prefix] = value

    walk('', raw)
    return flat


def clean_set(raw):
    """(settings, problems): numbers as floats clamped into their range (a clamp is reported), words checked against their choices. The first problem stops nothing: all are collected."""
    problems, clean = [], {}
    for key, value in flatten_set(raw).items():
        try:
            info = describe_key(key)
        except KeyProblem as problem:
            problems.append(str(problem))
            continue
        if info['choices'] is not None:
            if value not in info['choices']:
                problems.append(f'"{key}" must be one of {", ".join(info["choices"])}, not {value!r}')
                continue
            clean[key] = value
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            problems.append(f'"{key}" must be a number from {info["low"]:g} to {info["high"]:g}, not {value!r}')
            continue
        number = float(value)
        if number < info['low'] or number > info['high']:
            problems.append(f'"{key}" is {number:g}, outside its range {info["low"]:g} to {info["high"]:g}')
            continue
        clean[key] = number
    return clean, problems


# ------------------------------------------------------------------ how far apart two variations are
def _ratio_numbers(a, b, share_needed, span):
    return (abs(a - b) / span) / share_needed if span > 0 else 0.0


def saved_value_of(key, info, saved=None):
    """The saved scene's value of a setting as (lowest, highest) over its materials: from `saved` ({key: [lowest, highest]}, read from the scene by a scout or a finished run) when it is
    there, else the dial's default for both. master and amount.<layer> are always (1, 1): they scale what is saved."""
    if info['kind'] in ('master', 'amount'):
        return 1.0, 1.0
    if saved and key in saved and saved[key] is not None:
        value = saved[key]
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return float(value[0]), float(value[1])
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value), float(value)
    return info['default'], info['default']


def setting_ratios(first, second, saved=None):
    """{key: ratio}: for every setting either variation names, how many times the smallest difference that counts the two are apart (1.0 or more = far enough on that setting).
    first and second are {"set": {...}, "args": {...}, "ranges": {...}, "script": path-or-None}. A setting only one of them names is compared with the saved scene's value (saved_value_of):
    when the saved scene has different values in different materials, the variation is as far away as its LARGEST gap, because the change shows wherever any material moves enough."""
    share = float(numbers.value('place_variations.settings_difference_min_share'))
    unranged = float(numbers.value('place_variations.number_without_range_difference_min_share'))
    ratios = {}
    for key in sorted(set(first['set']) | set(second['set'])):
        info = describe_key(key)
        a, b = first['set'].get(key), second['set'].get(key)
        if info['categorical']:
            ratios[key] = 0.0 if a == b else 1.0
            continue
        span = info['high'] - info['low']
        if a is not None and b is not None:
            ratios[key] = _ratio_numbers(a, b, share, span)
            continue
        given = a if a is not None else b
        lowest, highest = saved_value_of(key, info, saved)
        ratios[key] = max(_ratio_numbers(given, lowest, share, span), _ratio_numbers(given, highest, share, span))
    if first.get('script') != second.get('script'):
        ratios['script'] = 1.0
    for key in sorted(set(first.get('args', {})) | set(second.get('args', {}))):
        a, b = first.get('args', {}).get(key), second.get('args', {}).get(key)
        name = f'args.{key}'
        if a is None or b is None:
            ratios[name] = 0.0 if a is b else 1.0
        elif isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            ratios[name] = 0.0 if a == b else 1.0
        else:
            ranges = {**second.get('ranges', {}), **first.get('ranges', {})}
            if key in ranges and ranges[key][1] > ranges[key][0]:
                ratios[name] = _ratio_numbers(float(a), float(b), share, float(ranges[key][1]) - float(ranges[key][0]))
            else:
                larger = max(abs(float(a)), abs(float(b)))
                ratios[name] = 0.0 if larger == 0 else (abs(float(a) - float(b)) / larger) / unranged
    return ratios


def apart(first, second, saved=None):
    """(far_enough, best_ratio, key, can_be_checked): whether two variations are measurably different by their settings. can_be_checked is False when neither names any setting
    (a script hook with no numbers cannot be compared before drawing; the pictures decide). saved: the saved scene's values (see saved_value_of)."""
    ratios = setting_ratios(first, second, saved)
    if not ratios:
        return False, 0.0, None, False
    key, best = max(ratios.items(), key=lambda item: item[1])
    return best >= 1.0, best, key, True


def has_nothing_to_compare(variation):
    return not variation['set'] and not variation.get('args') and not variation.get('script')


# ------------------------------------------------------------------ plain words
def words_for_key(key):
    if key.startswith('dials.'):
        _, layer, dial = key.split('.')
        return f'{layer.replace("_", " ")} {dial.replace("_", " ")}'
    if key.startswith('amount.'):
        return f'{key.split(".")[1].replace("_", " ")} amount'
    return key.replace('_', ' ')


def describe_variation(variation, limit=3):
    """A short plain line: 'moss and algae cover 0.9; moss and algae amount 1; state wet' (the first `limit` settings, then 'and N more')."""
    pieces = [f'{words_for_key(key)} {value:g}' if isinstance(value, float) else f'{words_for_key(key)} {value}' for key, value in variation['set'].items()]
    if variation.get('script'):
        pieces.append('hook ' + str(variation['script']).split('/')[-1])
    for key, value in (variation.get('args') or {}).items():
        pieces.append(f'{key.replace("_", " ")} {value:g}' if isinstance(value, float) else f'{key.replace("_", " ")} {value}')
    if not pieces:
        return 'no change (the saved scene as it is)'
    extra = len(pieces) - limit
    return '; '.join(pieces[:limit]) + (f'; and {extra} more' if extra > 0 else '')


def file_word(text):
    """A name as it appears in a picture file name: lower-case letters and digits with - between."""
    return re.sub(r'[^A-Za-z0-9]+', '-', str(text)).strip('-').lower() or 'x'


def file_label(position, name):
    """The start of every file the worker writes for one variation: 03_moss-heavy (the position in its job, then the name)."""
    return f'{position:02d}_{file_word(name)}'
