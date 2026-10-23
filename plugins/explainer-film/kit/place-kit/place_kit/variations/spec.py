"""What this does: reads a VARIATIONS FILE, checks it BEFORE anything is drawn, and plans the drawing: which variations are kept, which are dropped as near-duplicates (and why, in plain
words), how many card jobs they are split into (up to place_render.workers_max at the same time, at least place_variations.min_variations_per_job variations in each so a wake-up is shared)
and about how many card seconds that will take. Plain Python (standard library only); no Blender needed.

A variations file is JSON:
    {"change": "moss on the lock walls",               the one change this batch tries, in plain words (the batch rule counts batches for each change)
     "scene": "canal_finished.blend",                  the saved, finished scene (path relative to this file)
     "settings": "place-settings.json",                optional: needed only when a variation sets "state" or "look"
     "cameras": ["Camera A", "Camera B"],              the cameras to look through (none named: the scene's own camera)
     "variations": [
        {"name": "moss-light", "set": {"amount.moss_and_algae": 0.4}},                     amount and master SCALE what the saved scene has: 1 = as saved, 0 = off, 2 = twice
        {"name": "moss-thick-damp", "set": {"amount.moss_and_algae": 1.8, "dials.moss_and_algae.cover": 0.9, "state": "damp"}},
        {"name": "lean-more", "script": "hooks/lean.py", "args": {"lean_degrees": 8}, "ranges": {"lean_degrees": [0, 20]}}   a small script hook
     ]}
The settings a variation may set are listed at the top of keys.py (`explainer-film-place variations keys` prints them with their ranges). "engine", "picture": {"size": [600, 400], "samples": 24}
are optional. "baseline" is a reserved name: the saved scene as it is is always drawn too, because every measure is against it.
A variation with a script hook is always drawn from a freshly reopened scene; a variation made only of settings is reset by putting the old values back and checking them ("reset": "reopen"
forces a reopen).

Before drawing, a variation is dropped when no setting of it differs from the saved scene by place_variations.settings_difference_min_share of its range, or when no setting differs from an
earlier variation by that much. The later one goes, never the earlier. Every drop is said in a sentence. When a free scout of the same file was drawn (scout.py), its pictures decide too:
a variation the scout found nearly the same as the saved scene, or as an earlier variation, is dropped before anything goes to a card (scout.py says how, and how well it matched the card).

A concrete example: ten values of the moss amount 0.2 apart (0, 0.2, 0.4, 0.6, 0.8, 1.2, 1.4, 1.6, 1.8, 2.0: the range is 0 to 2, so 0.2 is 10 percent of it) are all kept; 1.0 would be
the saved scene again, and an eleventh at 0.45 is dropped as a near-duplicate of the one at 0.4 (2.5 percent apart).
"""
import json
import math
import os
import random
import re

from .. import house_numbers as numbers
from . import keys


class SpecProblem(Exception):
    """The variations file or an option cannot be used (exit 2); the sentence says which and what to write."""


NAME_OK = re.compile(r'^[a-z0-9][a-z0-9_-]{0,39}$')


def safe_name(text, fallback='change'):
    word = re.sub(r'[^a-z0-9]+', '-', str(text or '').strip().lower()).strip('-')
    if len(word) > 40:                                 # cut between words, not in the middle of one
        word = word[:41].rsplit('-', 1)[0] if '-' in word[:41] else word[:40]
    return (word or fallback)[:40].strip('-') or fallback


def _resolve(folder, path):
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(folder, path))


def read_spec(path, scene=None, settings=None, cameras=None, engine=None, size=None, samples=None):
    """The variations file as a plan-ready dictionary. All the problems found are said at once. Options given on the command line win over the file."""
    if not path or not os.path.exists(path):
        raise SpecProblem(f'the variations file {path or "(none given)"} is not there. Write one (see `explainer-film-place variations --help`) or make one with `explainer-film-place variations make`.')
    try:
        with open(path, encoding='utf-8') as handle:
            raw = json.load(handle)
    except ValueError as problem:
        raise SpecProblem(f'the variations file {path} is not valid JSON ({problem})')
    if not isinstance(raw, dict) or not isinstance(raw.get('variations'), list) or not raw['variations']:
        raise SpecProblem(f'the variations file {path} needs a "variations" list with at least two entries: {{"variations": [{{"name": "a", "set": {{"amount.dirt": 0.3}}}}, ...]}}')
    folder = os.path.dirname(os.path.abspath(path))
    problems = []
    scene_path = scene or raw.get('scene')
    if not scene_path:
        problems.append('name the saved, finished scene: "scene": "place-finished.blend" in the file, or --scene FILE.blend')
    else:
        scene_path = os.path.abspath(scene_path) if scene else _resolve(folder, scene_path)
        if not os.path.exists(scene_path):
            problems.append(f'the scene {scene_path} is not there (save the finished place first; a variation round starts from a saved scene)')
    settings_path = settings or raw.get('settings')
    if settings_path:
        settings_path = os.path.abspath(settings_path) if settings else _resolve(folder, settings_path)
        if not os.path.exists(settings_path):
            problems.append(f'the place settings {settings_path} are not there')
    camera_list = list(cameras) if cameras else raw.get('cameras') or []
    if not isinstance(camera_list, list) or any(not isinstance(c, str) or not c for c in camera_list):
        problems.append('"cameras" must be a list of camera names, for example ["Camera A", "Camera B"] (leave it out to use the scene\'s own camera)')
        camera_list = []
    ranges_all = raw.get('ranges') if isinstance(raw.get('ranges'), dict) else {}
    variations, seen = [], set()
    for index, item in enumerate(raw['variations'], 1):
        if not isinstance(item, dict):
            problems.append(f'variation {index} is not an object like {{"name": "a", "set": {{...}}}}')
            continue
        name = str(item.get('name') or f'v{index:02d}').strip()
        if name == 'baseline':
            problems.append('"baseline" is a reserved name (the saved scene as it is is always drawn as the baseline)')
            continue
        if not NAME_OK.match(name):
            problems.append(f'variation {index}: the name "{name}" must be 1 to 40 plain characters: lower-case letters, digits, - and _ (it names the picture files)')
            continue
        if name in seen:
            problems.append(f'two variations are called "{name}": every name must be its own')
            continue
        seen.add(name)
        try:
            settings_set, set_problems = keys.clean_set(item.get('set'))
        except keys.KeyProblem as problem:
            settings_set, set_problems = {}, [str(problem)]
        problems += [f'variation "{name}": {p}' for p in set_problems]
        script = item.get('script')
        if script is not None:
            script = _resolve(folder, str(script))
            if not os.path.isfile(script):
                problems.append(f'variation "{name}": the script hook {script} is not there')
        args = item.get('args') if isinstance(item.get('args'), dict) else {}
        if item.get('args') is not None and not isinstance(item.get('args'), dict):
            problems.append(f'variation "{name}": "args" must be an object of numbers and words')
        if args and not script:
            problems.append(f'variation "{name}": "args" belong to a script hook; add "script": "file.py" or put the settings in "set"')
        if ('state' in settings_set or 'look' in settings_set) and not settings_path:
            problems.append(f'variation "{name}": "state" and "look" need the place settings: give "settings": "place-settings.json" in the file (or --settings)')
        reset = str(item.get('reset') or 'auto')
        if reset not in ('auto', 'restore', 'reopen'):
            problems.append(f'variation "{name}": "reset" must be auto, restore or reopen')
            reset = 'auto'
        ranges = {**{k: v for k, v in ranges_all.items() if k in args}, **(item.get('ranges') if isinstance(item.get('ranges'), dict) else {})}
        variations.append({'name': name, 'set': settings_set, 'script': script, 'args': args, 'ranges': ranges, 'reset': 'reopen' if script else reset})
    if len(variations) < 1 and not problems:
        problems.append('the file holds no usable variation')
    if problems:
        shown = problems[:10]
        raise SpecProblem(f'the variations file {path} has {len(problems)} problem(s):\n  - ' + '\n  - '.join(shown) + ('\n  - ...' if len(problems) > 10 else ''))
    picture = raw.get('picture') if isinstance(raw.get('picture'), dict) else {}
    chosen_size = size or picture.get('size') or numbers.value('place_variations.picture_size_pixels')
    return {'path': os.path.abspath(path), 'folder': folder, 'about': raw.get('about'), 'change': str(raw.get('change') or 'one change'), 'change_id': safe_name(raw.get('change') or 'one change'),
            'scene': scene_path, 'settings': settings_path, 'cameras': camera_list, 'engine': (engine or raw.get('engine') or 'auto').lower(),
            'size': [int(chosen_size[0]), int(chosen_size[1])], 'samples': int(samples or picture.get('samples') or 0) or None, 'variations': variations}


# ------------------------------------------------------------------ the check before drawing
def as_baseline():
    return {'name': 'baseline', 'set': {}, 'script': None, 'args': {}, 'ranges': {}, 'reset': 'auto'}


def _percent(ratio):
    return f'{ratio * float(numbers.value("place_variations.settings_difference_min_share")) * 100:.0f}%'


def check_before(spec, saved=None):
    """Drops near-duplicates before anything is drawn. Returns {'kept': [...], 'dropped': [{'name', 'why', 'like'}], 'unchecked': [names], 'lines': [plain lines], 'status': 'ok'|'refuse'}.
    saved: what the saved scene has for its dials ({key: [lowest, highest]}, from a scout); without it a dial's default stands in for the saved scene."""
    kept, dropped, unchecked = [], [], []
    baseline = as_baseline()
    need = float(numbers.value('place_variations.settings_difference_min_share'))
    for variation in spec['variations']:
        if keys.has_nothing_to_compare(variation):
            dropped.append({'name': variation['name'], 'why': 'it changes nothing (no setting, no script): it would draw the saved scene again', 'like': 'baseline'})
            continue
        far, best, key, checkable = keys.apart(variation, baseline, saved)
        if checkable and not far:
            dropped.append({'name': variation['name'], 'why': f'no setting of it is more than {need:.0%} of its range away from the saved scene (the largest gap, {keys.words_for_key(key)}, is '
                            f'{_percent(best)}): it would draw the baseline again', 'like': 'baseline'})
            continue
        twin = None
        for other in kept:
            far_other, best_other, key_other, checkable_other = keys.apart(variation, other, saved)
            if not checkable_other:
                continue
            if not far_other:
                twin = (other, best_other, key_other)
                break
        if twin:
            other, best_other, key_other = twin
            dropped.append({'name': variation['name'], 'why': f'it is a near-duplicate of "{other["name"]}": the largest gap between them ({keys.words_for_key(key_other) if key_other != "script" else "script"}) is '
                            f'{_percent(best_other)} of its range, and at least {need:.0%} is needed', 'like': other['name']})
            continue
        if variation.get('script') and not variation['set'] and not any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (variation.get('args') or {}).values()):
            unchecked.append(variation['name'])
        kept.append(variation)
    lines = []
    asked = len(spec['variations'])
    status = 'ok'
    minimum = int(numbers.value('place_variations.batch_size_min'))
    maximum = int(numbers.value('place_variations.batch_size_max'))
    lines.append(f'{"PASS" if not dropped else "LOOK"} before drawing: {asked} variation(s) asked, {len(kept)} kept' + (f', {len(dropped)} dropped' if dropped else '') + '.')
    for drop in dropped:
        lines.append(f'LOOK dropped "{drop["name"]}": {drop["why"]}.')
    for name in unchecked:
        lines.append(f'LOOK "{name}" is a script hook with no numbers: its settings cannot be compared before drawing, so the pictures will decide (they are compared afterwards).')
    if not kept:
        status = 'refuse'
        lines.append('FAIL before drawing: nothing is left to draw. Make the variations further apart (each setting at least '
                     f'{need:.0%} of its range from the others), or change a different setting.')
    elif len(kept) < minimum:
        lines.append(f'LOOK before drawing: only {len(kept)} measurably different variation(s) are left; a batch is about {numbers.value("place_variations.batch_size")} ({minimum} at least). Spread the settings further apart, or '
                     'draw one picture instead of a batch.')
    if len(kept) > maximum:
        status = 'refuse'
        lines.append(f'FAIL before drawing: {len(kept)} variations is more than {maximum}: that is wandering, not looking. Keep the {numbers.value("place_variations.batch_size")} that differ most and send those.')
    return {'kept': kept, 'dropped': dropped, 'unchecked': unchecked, 'lines': lines, 'status': status, 'too_many': len(kept) > maximum}


# ------------------------------------------------------------------ the split and the estimate
def jobs_wanted(count, requested=None):
    """How many card jobs: the number asked for (at most place_render.workers_max), else enough that each holds at least place_variations.min_variations_per_job variations."""
    top = int(numbers.value('place_render.workers_max'))
    if requested:
        return max(1, min(int(requested), top, max(1, count)))
    per_job = int(numbers.value('place_variations.min_variations_per_job'))
    return max(1, min(top, math.ceil(count / per_job)))


def split_jobs(kept, requested=None):
    """The jobs: a list of {'index', 'entries': [{'name', 'set', 'script', 'args', 'reset', 'is_baseline'}...]}. The variations go round the jobs one by one (a mix in each); the baseline goes
    into the job that has the fewest, and is drawn first there."""
    count = jobs_wanted(len(kept), requested)
    buckets = [[] for _ in range(count)]
    for position, variation in enumerate(kept):
        buckets[position % count].append(dict(variation, is_baseline=False))
    smallest = min(range(count), key=lambda i: (len(buckets[i]), i))
    buckets[smallest].insert(0, dict(as_baseline(), is_baseline=True))
    return [{'index': i + 1, 'entries': bucket} for i, bucket in enumerate(buckets)]


def estimate_job(job, camera_count):
    """One job's card seconds, from the house estimates: wake-up + idle tail + opening the scene + the first picture + the others + a reopen for each script hook."""
    wake = float(numbers.value('place_card_time.estimated_wake_up_seconds'))
    tail = float(numbers.value('place_card_time.idle_tail_seconds'))
    opening = float(numbers.value('place_variations.estimated_seconds_open_scene'))
    first = float(numbers.value('place_variations.estimated_seconds_first_picture'))
    each = float(numbers.value('place_variations.estimated_seconds_per_picture'))
    drawn = len(job['entries']) * max(1, camera_count)
    reopens = sum(1 for e in job['entries'] if e.get('reset') == 'reopen' or e.get('script'))
    return wake + tail + opening + first + max(0, drawn - 1) * each + reopens * opening


def estimate(jobs, camera_count):
    """Planning numbers: (card seconds in all, seconds from start to finish with the jobs side by side, pictures). From the house estimates, until a real batch has measured better ones."""
    wake = float(numbers.value('place_card_time.estimated_wake_up_seconds'))
    tail = float(numbers.value('place_card_time.idle_tail_seconds'))
    cameras = max(1, camera_count)
    totals, pictures = [], 0
    for job in jobs:
        pictures += len(job['entries']) * cameras
        totals.append(estimate_job(job, cameras))
    set_up = wake + tail                      # uploads and the check of the kit wake one worker
    return round(sum(totals) + set_up, 0), round(max(totals) + set_up if totals else 0.0, 0), pictures


# ------------------------------------------------------------------ making a spread of variations
def stratified_values(key_list, count, seed=1, radius=None, centre=None, limits=None):
    """For each key a list of `count` values, spread so that no two variations share a stratum of any key (a Latin hypercube): every pair differs by at least 1/count of the range on every key.
    With radius (and centre values) the values spread inside centre +- radius of the range instead of the whole range; with limits ({key: (low, high)}) inside that part of the range.
    Words (state, look) and seeds are dealt out in turn."""
    rng = random.Random(seed)
    table = {}
    for key in key_list:
        info = keys.describe_key(key)
        if info['choices'] is not None:
            choices = list(info['choices'])
            rng.shuffle(choices)
            table[key] = [choices[i % len(choices)] for i in range(count)]
            continue
        order = list(range(count))
        rng.shuffle(order)
        low, high = info['low'], info['high']
        if info['dial'] == 'seed':
            table[key] = [float(int(low + (order[i] + 0.5) / count * (high - low))) for i in range(count)]
            continue
        if radius is not None and centre and key in centre:
            span = (high - low) * radius
            start, stop = max(low, centre[key] - span), min(high, centre[key] + span)
        elif limits and key in limits:
            start, stop = float(limits[key][0]), float(limits[key][1])
        else:
            start, stop = low, high
        table[key] = [round(start + (order[i] + 0.5) / count * (stop - start), 4) for i in range(count)]
    return table


def check_limits(key_list, limits):
    """The part of a range to spread inside ({key: (low, high)}, from `make --range KEY LOW HIGH`): each must name a key being spread, be numbers, low under high, inside the key's own range."""
    clean = {}
    for key, pair in (limits or {}).items():
        if key not in key_list:
            raise SpecProblem(f'--range names {key}, which is not one of the --keys being spread ({", ".join(key_list)})')
        info = keys.describe_key(key)
        if info['choices'] is not None or info['dial'] == 'seed':
            raise SpecProblem(f'--range cannot limit {key}: it is a word or a seed, not a number with a range')
        try:
            low, high = float(pair[0]), float(pair[1])
        except (TypeError, ValueError, IndexError):
            raise SpecProblem(f'--range {key} needs two numbers, LOW and HIGH, for example --range {key} {info["low"]:g} {info["high"]:g}')
        if not (info['low'] <= low < high <= info['high']):
            raise SpecProblem(f'--range {key} {low:g} {high:g} must have LOW under HIGH, both inside {info["low"]:g} to {info["high"]:g}')
        clean[key] = (low, high)
    return clean


def name_note(key_list):
    """One plain sentence on what the numbers in the made names mean, with an example from the first number setting among the first two keys, or '' when none is a number.
    Example: 'Names show each of the first two settings as a percent of its whole range: crackwid25 = a quarter of the way from 0.002 to 0.05 m, that is 0.014 m (not 25 of anything).'"""
    for key in key_list[:2]:
        info = keys.describe_key(key)
        if info['choices'] is not None or info['dial'] == 'seed' or info['low'] is None:
            continue
        short = (info['dial'] or key).replace('_metres', '').replace('_', '')[:8]
        unit = ' m' if (info['dial'] or '').endswith('_metres') else ''
        quarter = info['low'] + 0.25 * (info['high'] - info['low'])
        return (f'Names show each of the first two settings as a percent of its whole range: {short}25 = a quarter of the way from {info["low"]:g} to {info["high"]:g}{unit}, '
                f'that is {quarter:.3g}{unit} (not 25 of anything).')
    return ''


def make_variations(key_list, count, seed=1, change='one change', scene=None, settings=None, cameras=None, limits=None):
    """A variations file's content: `count` variations that spread the keys across their ranges (see stratified_values), or across the part of a range named in limits
    ({key: (low, high)}: the part of a dial that shows, found by a scout). Names are v01-cover65-film12 (the first two keys, in percent of the whole range)."""
    if not key_list:
        raise SpecProblem('name the settings to vary: --keys amount.moss_and_algae dials.moss_and_algae.cover ... (`explainer-film-place variations keys` lists them with their ranges)')
    try:
        for key in key_list:
            keys.describe_key(key)
        limits = check_limits(key_list, limits)
    except keys.KeyProblem as problem:
        raise SpecProblem(str(problem))
    values = stratified_values(key_list, count, seed, limits=limits)
    variations = []
    for i in range(count):
        chosen = {key: values[key][i] for key in key_list}
        tag = ''
        for key in key_list[:2]:
            info = keys.describe_key(key)
            if info['choices'] is not None or info['dial'] == 'seed':
                tag += f'-{chosen[key]}'.replace('.0', '')
            else:
                tag += f'-{(info["dial"] or key).replace("_metres", "").replace("_", "")[:8]}{round((chosen[key] - info["low"]) / (info["high"] - info["low"]) * 100):d}'
        variations.append({'name': f'v{i + 1:02d}{tag}'[:40], 'set': chosen})
    inside = ''.join(f'; {key} only from {low:g} to {high:g}' for key, (low, high) in limits.items())
    note = name_note(key_list)
    content = {'about': f'Made by `explainer-film-place variations make`: {count} variations that spread {", ".join(key_list)} across their ranges (seed {seed}{inside}).'
               + (f' {note}' if note else ''), 'change': change}
    if scene:
        content['scene'] = scene
    if settings:
        content['settings'] = settings
    if cameras:
        content['cameras'] = list(cameras)
    content['variations'] = variations
    return content


def refine_variations(result, picks, count=6, seed=1, radius=0.3):
    """The second batch: from the variations that were picked (names in a finished run's result file). One pick: variations spread around it. Several: the first variation is their blend (the
    mean of each number; a word that disagrees takes the first pick's), then the rest spread around the blend. Returns a variations file's content."""
    by_name = {v['name']: v for v in result.get('variations', [])}
    missing = [p for p in picks if p not in by_name]
    if missing:
        raise SpecProblem(f'the picks {", ".join(missing)} are not in that result (its variations: {", ".join(by_name)})')
    chosen = [by_name[p] for p in picks]
    if any(v.get('script') for v in chosen):
        raise SpecProblem('a pick that is a script hook cannot be refined automatically: write the next batch by hand, with the hook\'s numbers around the pick\'s')
    blend = {}
    for key in sorted({k for v in chosen for k in v['set']}):
        info = keys.describe_key(key)
        values = [v['set'][key] for v in chosen if key in v['set']]
        blend[key] = values[0] if info['choices'] is not None else round(sum(values) / len(values), 4)
    if not blend:
        raise SpecProblem('the picked variation(s) set nothing, so there is nothing to refine')
    spread = stratified_values(list(blend), count, seed, radius=radius, centre={k: v for k, v in blend.items() if not isinstance(v, str)})
    variations = []
    if len(chosen) > 1:
        variations.append({'name': safe_name('blend-' + '-'.join(pick.split('-')[0] for pick in picks), 'blend')[:40].strip('-'), 'set': dict(blend)})
    for i in range(count - len(variations)):
        item = {key: (blend[key] if isinstance(blend[key], str) else spread[key][i]) for key in blend}
        variations.append({'name': f'r{i + 1:02d}', 'set': item})
    content = {'about': f'The second batch, around {", ".join(picks)} (radius {radius:.0%} of each range, seed {seed}).', 'change': result.get('change', 'one change'), 'variations': variations}
    for field in ('scene', 'settings', 'cameras'):
        if result.get(field):
            content[field] = result[field]
    return content
