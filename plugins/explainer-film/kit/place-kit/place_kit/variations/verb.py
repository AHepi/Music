"""What this does: the plain-Python side of the `explainer-film-place variations` verb: it dispatches the actions
    make     write a variations file that spreads settings across their ranges, so ten variations are measurably different by construction (a Latin hypercube: no two share a stratum of any setting);
             --range KEY LOW HIGH spreads a setting only over the part of its range that shows
    scout    the FREE SCOUT: draw the same file HERE, tiny, in one job, and say which variations would not show (no card seconds, not a batch); plan and run then drop those by themselves
    plan     read a variations file, check it BEFORE drawing (settings, and the scout's pictures when there is a scout), show the split into card jobs, the estimate and the allowance check:
             draws nothing and costs nothing
    run      plan, draw (here with --where local, or on rented cards), measure, check the pictures differ, make the contact sheet, write the ledger
    collect  finish a batch whose command was cut off after its jobs were sent (nothing is sent again)
    refine   write the SECOND batch around the variation(s) you picked in a finished run (several picks are blended); the batch rule allows one more batch for a change, no more
    sheet    make the contact sheet again from pictures already drawn
    keys     list every setting a variation may change, with its range
Exit: 0 done, 1 refused or a variation failed, 2 an input is missing or unusable. Plain Python (no Blender here: `run --where local` starts Blender as a program).

A concrete example:
    explainer-film-place variations make --keys amount.moss_and_algae dials.moss_and_algae.cover --range dials.moss_and_algae.cover 0.5 1 --count 10 --change "moss on the walls" \
        --scene lock.blend --cameras "Camera A" "Camera B" --out moss.json
    explainer-film-place variations scout moss.json                (free, here, about 40 s for a small place)
    explainer-film-place variations plan moss.json
    explainer-film-place variations run moss.json --where rented --helper builder-walls --role builder
"""
import json
import os

from .. import card_time
from . import keys, runner, spec as spec_module


def main_command(parsed, find_blender=None, say=print):
    action = parsed.action
    try:
        if action == 'keys':
            for line in keys.all_dial_lines():
                say(line)
            return 0
        if action == 'make':
            return make_file(parsed, say)
        if action == 'refine':
            return refine_file(parsed, say)
        if not parsed.spec:
            say(f'FAIL variations {action} needs the variations file (for sheet: the variations-result.json of a finished run; for collect: the run folder): explainer-film-place variations {action} FILE.json')
            return 2
        blender = None
        if find_blender and (action == 'scout' or (action == 'run' and getattr(parsed, 'where', 'auto') == 'local')):
            blender = find_blender(getattr(parsed, 'blender', None), None)
        return runner.run_variations(parsed, say=say, blender=blender)
    except spec_module.SpecProblem as problem:
        say(f'FAIL {problem}')
        return 2
    except card_time.LedgerProblem as problem:
        say(f'FAIL {problem}')
        return 2


def _write(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(content, handle, indent=1)


def beside(path, folder):
    """A path written relative to the folder of the variations file when it can be (the file then still works after the folder is moved or copied)."""
    if not path:
        return None
    try:
        return os.path.relpath(os.path.abspath(path), folder)
    except ValueError:          # another drive
        return os.path.abspath(path)


def make_file(parsed, say):
    count = int(parsed.count or 10)
    change = parsed.change or 'one change'
    out = parsed.out or f'{spec_module.safe_name(change)}-variations.json'
    here = os.path.dirname(os.path.abspath(out))
    scene = os.path.abspath(parsed.scene) if parsed.scene else None
    settings = os.path.abspath(parsed.settings) if parsed.settings else None
    limits = {row[0]: (row[1], row[2]) for row in (getattr(parsed, 'range', None) or [])}
    content = spec_module.make_variations(list(parsed.keys or []), count, parsed.seed, change, beside(scene, here), beside(settings, here), parsed.cameras, limits)
    _write(out, content)
    inside = ''.join(f'; {key} only from {low} to {high}' for key, (low, high) in limits.items())
    note = spec_module.name_note(list(parsed.keys or []))
    say(f'PASS made {out}: {count} variation(s) that spread {", ".join(parsed.keys)} across their ranges (seed {parsed.seed}{inside}); every pair differs by at least {100 // count}% of the '
        'spread on each setting.' + (f' {note}' if note else ''))
    if not scene:
        say('LOOK the file names no scene: add "scene": "place-finished.blend" to it (or pass --scene when you plan and run it), and the cameras ("cameras": ["Camera A"]).')
    say(f'NEXT: explainer-film-place variations scout {out}   (free, here; it says which variations would not show), then: explainer-film-place variations plan {out}')
    return 0


def refine_file(parsed, say):
    if not parsed.spec or not parsed.pick:
        raise spec_module.SpecProblem('refine needs the result of a finished run and the names you picked: explainer-film-place variations refine VARIATIONS-RESULT.json --pick NAME [NAME ...]')
    path = parsed.spec if os.path.isfile(parsed.spec) else os.path.join(parsed.spec, 'variations-result.json')
    if not os.path.exists(path):
        raise spec_module.SpecProblem(f'{path} is not there: give the variations-result.json of a finished run (or its folder)')
    result = json.load(open(path, encoding='utf-8'))
    content = spec_module.refine_variations(result, list(parsed.pick), int(parsed.count or 6), parsed.seed, parsed.radius)
    out = parsed.out or os.path.join(os.path.dirname(os.path.abspath(path)), f'{result.get("change_id", "change")}-batch2.json')
    for field in ('scene', 'settings'):
        if content.get(field):
            content[field] = beside(content[field], os.path.dirname(os.path.abspath(out)))
    _write(out, content)
    say(f'PASS made {out}: {len(content["variations"])} variation(s) around {", ".join(parsed.pick)}'
        + ('; the first is their blend' if len(parsed.pick) > 1 else '') + '. This is the last batch the rule allows for this change.')
    say(f'NEXT: explainer-film-place variations scout {out}   (free, here), then: explainer-film-place variations plan {out}')
    return 0
