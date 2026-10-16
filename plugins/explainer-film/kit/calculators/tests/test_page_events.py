"""What this does: tests paper-film/tools/page_events.mjs and the page-events notes in graphics.js and cinema-kit.js in a
real browser stage, on the small test chapter (paper-film/scenes/page-events-test.js, no paintings or models):
  1. normal drawing is unchanged: stills drawn by render-paper-film.mjs (notes off) and by page_events.mjs with the notes
     switched on are the same, byte for byte; when the film kit's graphics.js and cinema-kit.js (the files before the
     notes were added) are found, stills drawn with them are the same too; and a control with one fade changed by
     0.01 s comes out different, so the comparison can see a change;
  2. the events it writes reproduce the stored fixtures (tests/fixtures/page-timing/events-test-*.json.gz) exactly;
  3. the appear delays the running page reports equal the ones plan_page_timing.py reads from graphics.js.
It needs node, the kit's node_modules (playwright-core, three, the Inter font) and a Chromium. They are looked for in
PAPER_FILM_NODE_MODULES, the kit's paper-film/node_modules, and a film kit next to the plugin; without them it is skipped.
It builds a throw-away copy of the kit out of links in a temporary folder and deletes it afterwards.
Run: python3 kit/calculators/tests/test_page_events.py
"""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, skip  # noqa: E402
import plan_page_timing as timing  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
HERE = os.path.join(FIXTURES, 'page-timing')
NODE = shutil.which('node')
if not NODE:
    skip('page events in the stage', 'node is not installed')
film_kit = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(KIT))), 'austerity-explainer', 'film-kit')
candidates = [os.environ.get('PAPER_FILM_NODE_MODULES'), os.path.join(KIT, 'paper-film', 'node_modules'), os.path.join(film_kit, 'paper-film', 'node_modules')]
NODE_MODULES = next((c for c in candidates if c and os.path.isdir(os.path.join(c, 'playwright-core')) and os.path.isdir(os.path.join(c, 'three'))), None)
if not NODE_MODULES:
    skip('page events in the stage', 'no node_modules with playwright-core and three (set PAPER_FILM_NODE_MODULES)')
check = Checker('page events: the notes change nothing, and the events are reproducible')
TIMES = ['9.5', '13.88', '15.0', '18.5', '23.5']


def make_kit(folder, replace=None):
    """A kit made of links to this one (its own graphics.js or cinema-kit.js where `replace` says)."""
    kit = os.path.join(folder, 'kit')
    os.makedirs(os.path.join(kit, 'paper-film', 'scenes'))
    for name in ('calculators', 'examples', 'film-settings.json'):
        os.symlink(os.path.join(KIT, name), os.path.join(kit, name))
    for name in ('stage', 'tools'):
        os.symlink(os.path.join(KIT, 'paper-film', name), os.path.join(kit, 'paper-film', name))
    os.symlink(NODE_MODULES, os.path.join(kit, 'paper-film', 'node_modules'))
    scenes = os.path.join(KIT, 'paper-film', 'scenes')
    for name in os.listdir(scenes):
        target = os.path.join(kit, 'paper-film', 'scenes', name)
        if replace and name in replace:
            open(target, 'w').write(replace[name])
        else:
            os.symlink(os.path.join(scenes, name), target)
    return kit


def node(kit, tool, *args, timeout=600):
    done = subprocess.run([NODE, '--preserve-symlinks', '--preserve-symlinks-main', os.path.join(kit, 'paper-film', 'tools', tool), *args],
                          capture_output=True, text=True, timeout=timeout)
    return done.returncode, done.stdout + done.stderr


def digests(folder):
    return {name: hashlib.sha1(open(os.path.join(folder, name), 'rb').read()).hexdigest() for name in sorted(os.listdir(folder)) if name.endswith('.jpg')}


work = tempfile.mkdtemp(prefix='page-events-test-')
try:
    after = make_kit(os.path.join(work, 'after'))
    code, out = node(after, 'render-paper-film.mjs', 'page-events-test', os.path.join(work, 'stills-off'), '--stills', *TIMES)
    if code != 0 and ('No Chromium' in out or 'Executable doesn' in out):
        skip('page events in the stage', 'no Chromium found (set PAPER_FILM_BROWSER)')
    check.true('render-paper-film.mjs draws the test chapter (notes off)', code == 0, details=out[-300:])
    code, out = node(after, 'page_events.mjs', 'page-events-test', '--render-stills', os.path.join(work, 'stills-on'), *TIMES)
    check.true('page_events.mjs draws the same moments with the notes on', code == 0 and 'notes taken while drawing' in out, details=out[-300:])
    off, on = digests(os.path.join(work, 'stills-off')), digests(os.path.join(work, 'stills-on'))
    check.true(f'{len(off)} stills with the notes on are byte for byte the stills with them off', off and off == on,
               details=f'{sum(1 for k in off if off[k] == on.get(k))} of {len(off)} the same', proves='switching the notes on changes no pixel')
    before_files = {name: os.path.join(film_kit, 'paper-film', 'scenes', name) for name in ('graphics.js', 'cinema-kit.js')}
    if all(os.path.isfile(p) for p in before_files.values()) and 'APPEAR_DELAYS' not in open(before_files['graphics.js']).read():
        before = make_kit(os.path.join(work, 'before'), {name: open(path).read() for name, path in before_files.items()})
        code, out = node(before, 'render-paper-film.mjs', 'page-events-test', os.path.join(work, 'stills-before'), '--stills', *TIMES)
        old = digests(os.path.join(work, 'stills-before'))
        check.true('stills drawn with the film kit\'s graphics.js and cinema-kit.js (no notes) are the same as with the plugin\'s', code == 0 and old == off,
                   details=f'{sum(1 for k in off if off[k] == old.get(k))} of {len(off)} the same' + out[-200:],
                   recorded='film-kit/paper-film/scenes (the files the plugin\'s were copied from, before the notes)',
                   proves='normal drawing is unchanged by the notes (the film kit\'s cinema-kit.js lacks setFading, which this scene never calls)')
    else:
        check.note('the film kit\'s graphics.js and cinema-kit.js were not found next to the plugin: the before-and-after comparison was not run')
    changed = open(os.path.join(KIT, 'paper-film', 'scenes', 'graphics.js')).read().replace('const BUILD_WORDS_FADE_IN = 0.14;', 'const BUILD_WORDS_FADE_IN = 0.15;')
    control = make_kit(os.path.join(work, 'control'), {'graphics.js': changed})
    code, out = node(control, 'render-paper-film.mjs', 'page-events-test', os.path.join(work, 'stills-control'), '--stills', '13.88')
    differs = digests(os.path.join(work, 'stills-control')).get('still-13.88.jpg') != off.get('still-13.88.jpg')
    check.true('control: with one fade 0.01 s longer the still at 13.88 s differs', code == 0 and differs, proves='the comparison can see a small change')
    for variant, query in (('clean', []), ('faults', ['--query', 'variant=faults'])):
        events_file = os.path.join(work, f'events-{variant}.json')
        code, out = node(after, 'page_events.mjs', 'page-events-test', events_file, *query)
        check.true(f'page_events.mjs runs the {variant} test chapter', code == 0, details=out[-300:])
        if code != 0:
            continue
        fresh = json.load(open(events_file))
        stored = json.load(gzip.open(os.path.join(HERE, f'events-test-{variant}.json.gz'), 'rt'))
        same = all(fresh[key] == stored[key] for key in ('items', 'lookups', 'frames', 'effects', 'pages'))
        check.true(f'the {variant} events reproduce the stored fixture exactly (drawn things, lookups, frames, live things, pages)', same,
                   details=', '.join(key for key in ('items', 'lookups', 'frames', 'effects', 'pages') if fresh[key] != stored[key]) or 'all the same',
                   proves='the fixtures the other tests read are what the tool writes today')
        if variant == 'clean':
            check.equal('appear delays from the running page equal those read from graphics.js', {k: round(v, 6) for k, v in fresh['appear_delays'].items()},
                        timing.read_appear_delays(), proves='parity of the JavaScript table and the Python reading')
            check.equal('the clean chapter comes out the same drawn out of order', len(fresh['order_differences']), 0)
        else:
            check.true('the faults chapter\'s spark comes out different drawn out of order', len(fresh['order_differences']) > 0)
    code, out = node(after, 'page_events.mjs', '--help')
    check.true('page_events.mjs --help answers with a usage note (house rule)', code == 0 and 'Usage' in out)
finally:
    shutil.rmtree(work, ignore_errors=True)
check.finish()
