"""What this does: the FREE SCOUT of a variations batch. Before a batch goes to the rented cards, `explainer-film-place variations scout FILE.json` draws the very same variations HERE,
on this computer, tiny (place_variations.scout_size_pixels, 240 x 160) and with few samples, in one job, measures them and says which variations would come out nearly the same as the
saved scene or as each other. It costs no card seconds and it is not a batch (the batch rule does not count it). Then `variations plan` and `variations run` read the scout by themselves and
drop those variations BEFORE anything goes to a card, each with a sentence that says why. The scout also reads what the saved scene really has for every dial the batch varies (lowest and
highest over its materials), so the settings check before drawing compares with the real scene instead of a dial's default.

How well it matches the card (measured, 23 October 2026, the small canal lock, two cameras): the two real card batches of 10 (moss, and cracks and chips; 600 x 400, 24 samples) were drawn
again as scouts (240 x 160, 8 samples, 37 to 39 s each here). With the scout's own limits (place_variations.scout_picture_mean_difference_min 0.75 and scout_picture_changed_share_min 0.3
percent; tiny low-sample pictures differ more than big ones) the scouts called exactly the same 22 pairs nearly the same as the cards did, and no other. One scene only: the margin was thin
for cracks (0.71 against 0.74), so the card's own check after drawing still runs on every batch.

Measurably is not always visibly: a pair that differs only by a faint, even shift (only the mean moved; almost no pixel changed by more than the pixel step) is NOT dropped but named
"may not be visible" (compare.py). Look at the scout sheet and take such variations out of the file yourself if you cannot tell them apart; `plan` repeats the warning.

When NOT to scout: when this computer needs more than a few minutes to open and draw the scene (a big place). The scout prints how long it took; then send the batch without it.

Where it goes: beside the variations file, in a folder named after it (moss-variations.json -> moss-variations-scout/), with variations-result.json ("scout": true), the pictures and a small
sheet. A scout is matched to a batch by the scene's checksum and each variation's fingerprint (its settings, its hook and the hook's checksum): a scout of an older scene, or of other
settings, is not used, and the plan says so.

A concrete example: moss-variations.json has 10 variations; the scout finds that 5 of them come out nearly the same as the saved scene (moss does not show from these cameras below a cover
of about 0.5). `variations plan moss-variations.json` then says "dropped ... in the free scout it came out nearly the same as the saved scene" for those 5 and keeps 5: spread the rest
wider (`variations make --range dials.moss_and_algae.cover 0.5 1`), scout again (free), and send 10 that show.
Plain Python; Blender is started as a program for the drawing.
"""
import hashlib
import json
import os
import time

from .. import house_numbers as numbers
from ..render import client as client_module
from . import compare, sheet, spec as spec_module


# ------------------------------------------------------------------ matching a scout to a batch
def scene_checksum(path):
    return client_module.file_checksum(path)[:16]


def fingerprint_of(variation):
    """A short hash of what a variation does: its settings, its hook's numbers, and the hook file's own checksum (a changed hook is a new variation). Its name does not count."""
    script = variation.get('script')
    hook = None
    if script:
        hook = client_module.file_checksum(script)[:16] if os.path.isfile(script) else os.path.basename(str(script))
    payload = {'set': variation.get('set') or {}, 'args': variation.get('args') or {}, 'hook': hook}
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]


def default_folder(spec):
    return os.path.join(spec['folder'], os.path.splitext(os.path.basename(spec['path']))[0] + '-scout')


def find_scout(spec, explicit=None, ignore=False):
    """(scout document or None, plain line or None). The scout is the variations-result.json of `explicit` (a file or its folder), else of the default folder beside the variations file."""
    if ignore:
        return None, 'LOOK scout: not used (--no-scout).'
    path = explicit or default_folder(spec)
    path = path if path.endswith('.json') else os.path.join(path, 'variations-result.json')
    if not os.path.exists(path):
        if explicit:
            return None, f'LOOK scout: {path} is not there, so no scout is used.'
        return None, None
    try:
        document = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None, f'LOOK scout: {path} could not be read, so no scout is used.'
    if not document.get('scout'):
        return None, f'LOOK scout: {path} is a batch drawn on a card, not a scout, so it is not used as one.'
    if document.get('scene_checksum') != scene_checksum(spec['scene']):
        return None, (f'LOOK scout: {path} was drawn from another version of the scene (the .blend changed since), so it is not used. Scout again (free): '
                      f'explainer-film-place variations scout {os.path.basename(spec["path"])}')
    document['path'] = path
    return document, f'PASS scout: using the free scout drawn here ({os.path.relpath(path, spec["folder"])}).'


def drops_from_scout(scout, kept):
    """(kept, dropped): the variations a scout found nearly the same as the saved scene, or as an earlier kept variation, are dropped. A variation the scout did not draw is kept and named."""
    by_print = {v['fingerprint']: v['name'] for v in scout.get('variations', []) if v.get('fingerprint')}
    invisible = set(scout.get('invisible') or [])
    alike = {frozenset(pair) for pair in scout.get('nearly_the_same') or []}
    gaps = {frozenset((p['a'], p['b'])): p for p in scout.get('pairs') or []}
    left, dropped, unscouted = [], [], []
    for variation in kept:
        name = by_print.get(fingerprint_of(variation))
        if name is None:
            unscouted.append(variation['name'])
            left.append(variation)
            continue
        if name in invisible:
            gap = gaps.get(frozenset(('baseline', name)), {})
            dropped.append({'name': variation['name'], 'like': 'baseline', 'by': 'scout',
                            'why': f'in the free scout it came out nearly the same as the saved scene (mean difference {gap.get("mean_difference", 0):.2f} of 255): it would not show on the card either'})
            continue
        twin = None
        for other in left:
            other_name = by_print.get(fingerprint_of(other))
            if other_name and frozenset((name, other_name)) in alike:
                twin = (other, gaps.get(frozenset((name, other_name)), {}))
                break
        if twin:
            dropped.append({'name': variation['name'], 'like': twin[0]['name'], 'by': 'scout',
                            'why': f'in the free scout it came out nearly the same as "{twin[0]["name"]}" (mean difference {twin[1].get("mean_difference", 0):.2f} of 255): keep one of the two'})
            continue
        left.append(variation)
    return left, dropped, unscouted


def faint_in_scout(scout, kept):
    """The pairs (by the batch's own names) that the scout found only faintly different, among the variations that are kept (and the baseline)."""
    by_print = {v['fingerprint']: v['name'] for v in scout.get('variations', []) if v.get('fingerprint')}
    scout_to_batch = {'baseline': 'baseline'}
    for variation in kept:
        name = by_print.get(fingerprint_of(variation))
        if name:
            scout_to_batch[name] = variation['name']
    return [(scout_to_batch[a], scout_to_batch[b]) for a, b in (scout.get('faint') or []) if a in scout_to_batch and b in scout_to_batch]


# ------------------------------------------------------------------ drawing the scout
def run_scout(options, say=print, blender=None):
    """`variations scout FILE.json`: the free scout. Returns the exit code."""
    from . import runner          # runner imports this module; imported here so the two do not import each other at load time
    spec = spec_module.read_spec(options.spec, scene=getattr(options, 'scene', None), settings=getattr(options, 'settings', None), cameras=getattr(options, 'cameras', None),
                                 engine=getattr(options, 'engine', None) if getattr(options, 'engine', None) not in (None, 'auto') else None)
    size = runner._size_option(getattr(options, 'size', None)) or list(numbers.value('place_variations.scout_size_pixels'))
    spec = dict(spec, size=[int(size[0]), int(size[1])], samples=getattr(options, 'samples', None) or None)
    checked = spec_module.check_before(spec)
    for line in checked['lines']:
        say(line)
    if checked['status'] == 'refuse' and not checked.get('too_many'):
        say('FAIL scout: nothing to draw.')
        return 1
    blender = blender or runner._find_blender(options)
    if not blender:
        say('FAIL Blender was not found: give --blender PATH, set BLENDER, or put blender on the PATH (the free scout draws on this computer).')
        return 2
    jobs = spec_module.split_jobs(checked['kept'], 1)
    for job in jobs:
        job['scout'] = True
    plan = {'spec': spec, 'checked': checked, 'jobs': jobs}
    folder = os.path.abspath(getattr(options, 'run_folder', None) or default_folder(spec))
    os.makedirs(folder, exist_ok=True)
    say(f'PASS scout: {len(checked["kept"])} variation(s) and the saved scene, drawn HERE in one job, {spec["size"][0]} x {spec["size"][1]}, few samples; free (no card seconds) and not counted as a batch.')
    began = time.time()
    records = runner.draw_here(plan, folder, blender, False, say)
    results, summaries = runner.collect(plan, records, folder)
    drawn = [r for r in results if r.get('ok') and r.get('pictures')]
    seconds = round(time.time() - began, 1)
    if not drawn:
        say('FAIL scout: no picture was drawn. Read the end of the job\'s log above.')
        return 1
    compare.measure_variations(results)
    pairs = compare.pair_differences(results, scout=True)
    pair_lines = runner.flag_results(results, pairs)
    faint = runner.faint_lines(results, pairs)
    saved = {}
    for summary in summaries.values():
        saved.update({key: value for key, value in (summary.get('saved_values') or {}).items() if value is not None})
    engine = next((s.get('engine') for s in summaries.values() if s.get('engine')), '?')
    cameras = spec['cameras'] or sorted({p['camera'] for r in results for p in r.get('pictures', [])})
    document = {'scout': True, 'change': spec['change'], 'change_id': spec['change_id'], 'scene': spec['scene'], 'scene_checksum': scene_checksum(spec['scene']), 'settings': spec['settings'],
                'cameras': cameras, 'engine': engine, 'size': spec['size'],
                'variations': [{'name': v['name'], 'set': v['set'], 'args': v['args'], 'script': v['script'], 'fingerprint': fingerprint_of(v)} for v in checked['kept']],
                'dropped': checked['dropped'], 'results': [runner._result_document(r, folder) for r in results], 'pairs': pairs['pairs'], 'nearly_the_same': pairs['nearly_same'],
                'invisible': pairs['invisible'], 'faint': pairs.get('faint', []), 'faint_against_baseline': pairs.get('faint_against_baseline', []),
                'saved_values': saved, 'seconds': seconds, 'jobs': records, 'job_summaries': summaries}
    kept_after, dropped_after, _ = drops_from_scout(document, checked['kept'])
    document['would_drop'] = dropped_after
    saved_line = saved_values_text(saved)
    made = sheet.make_sheet(os.path.join(folder, f'{spec["change_id"]}-scout-sheet.jpg'), results, cameras,
                            {'change': 'Free scout (drawn here, tiny): ' + spec['change'], 'scene': os.path.basename(spec['scene']), 'engine': str(engine).lower(),
                             'size': f'{spec["size"][0]} x {spec["size"][1]}', 'dropped': [],
                             'pair_lines': ['Nearly the same in the scout: ' + line for line in pair_lines] + ['May not be visible: ' + line for line in faint],
                             'card_lines': [f'Drawn on this computer in {seconds:.0f} s; no rented-card seconds were used; a scout is not a batch.'] + ([saved_line] if saved_line else []),
                             'baseline_note': saved_line})
    document['sheet'] = made
    result_path = os.path.join(folder, 'variations-result.json')
    runner._write_json(result_path, document)
    for line in pair_lines:
        say(f'LOOK nearly the same in the scout: {line}')
    for line in faint:
        say(f'LOOK may not be visible in the scout: {line}')
    if saved_line:
        say(f'PASS {saved_line}')
    if dropped_after:
        say(f'LOOK scout: {len(dropped_after)} of {len(checked["kept"])} variation(s) would not show on a card, so `plan` and `run` will drop them: ' + ', '.join(f'"{d["name"]}"' for d in dropped_after) + '.')
    elif faint:
        say(f'LOOK scout: all {len(checked["kept"])} variation(s) came out measurably different from the saved scene and from each other, but {len(pairs.get("faint", []))} pair(s) '
            'differ only by a faint, even shift (measurably, not always visibly, different): look at the scout sheet, and take out of the file any variation you cannot tell apart '
            'before you send the batch.')
    else:
        say(f'PASS scout: all {len(checked["kept"])} variation(s) came out measurably and clearly different from the saved scene and from each other.')
    minimum = int(numbers.value('place_variations.batch_size_min'))
    if len(kept_after) < int(numbers.value('place_variations.batch_size')):
        say(f'LOOK scout: {len(kept_after)} variation(s) would go to the card' + (f' (fewer than {minimum}: that is not a batch)' if len(kept_after) < minimum else '')
            + '. Spread the settings wider, or only over the part of a dial that shows (`variations make --keys ... --range KEY LOW HIGH`), and scout again: it is free.')
    say(f'PASS sheet: {made["path"]} ({made["bytes"] // 1024} KB)')
    say(f'PASS scout: drawn here in {seconds:.0f} s; no rented-card seconds were used. Result: {result_path}')
    say(f'NEXT: look at the scout sheet with the Read tool, then `explainer-film-place variations plan {os.path.basename(spec["path"])}` (it uses this scout by itself).')
    return 0


def saved_values_text(saved):
    """'The saved scene has: cracks and chips crack density 0.5; ...' (a range when the materials differ), or '' when nothing was read."""
    from . import keys
    pieces = []
    for key, value in sorted((saved or {}).items()):
        if value is None:
            continue
        low, high = value
        pieces.append(f'{keys.words_for_key(key)} {low:g}' if abs(high - low) < 1e-9 else f'{keys.words_for_key(key)} {low:g} to {high:g}')
    return ('The saved scene has: ' + '; '.join(pieces) + ' (over its materials).') if pieces else ''
