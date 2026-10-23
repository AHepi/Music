"""What this does: tests, inside Blender, the place audit's four checks of the lessons round (23 October) on a tiny scene built in a FAULTY and a
MENDED version (fixtures/place/make_world_scene.py), plus the wear layers' sun (fixtures/place/probe_sun.py):
  1. place: film frame  fails a place marked "for_film": true drawn at 1200 x 800; passes 1080 x 1920.
  2. place: world       fails a clip end shorter than the far hills, rays below the horizon that hit nothing (the camera sees past the ground's
                        edge), a backdrop and a large far mill that cast shadows; passes the mended scene.
  3. place: sun         a LOOK when the low sun behind the wall shadows most of the seen ground, naming the wall; passes a high side sun.
  4. place: lettering   fails a shop sign with no lettering, but not the ledger book with a text object on it nor a floor board.
  5. finish turns the backdrop's shadow off, and says which sun the wear layers' shade used.
  6. the wear layers' shade follows the scene's one sun lamp (and changes when it turns); with two sun lamps or none it falls back to 135 degrees
     compass and 45 up, and says why.
Needs Blender (BLENDER, or machine-settings.env, or the PATH); without it the file says so and exits as skipped. About 20 seconds.
Run: BLENDER=/path/to/blender python3 kit/calculators/tests/test_place_world.py
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, KIT, FIXTURES, blender_program, skip, work_folder  # noqa: E402

blender = blender_program()
if not blender:
    skip('place audit: film frame, world, sun, lettering inside Blender', 'Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')

PLACE_KIT = os.path.join(KIT, 'place-kit')
LAUNCHER = os.path.join(PLACE_KIT, 'place_command.py')
MAKE = os.path.join(FIXTURES, 'place', 'make_world_scene.py')
PROBE = os.path.join(FIXTURES, 'place', 'probe_sun.py')
check = Checker('place audit inside Blender: film frame, world, sun, lettering; the wear layers\' sun')
work = work_folder('place-world-test-')
environment = {name: value for name, value in os.environ.items() if name not in ('RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_SETTINGS_FILE')}
environment.update(BLENDER=blender, PLACE_NO_XVFB='1')
settings = os.path.join(work, 'place-settings.json')
json.dump({'place': 'world test', 'for_film': True}, open(settings, 'w'))


def run(command, timeout=600):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=environment)


def audit_and_judge(version):
    scene = os.path.join(work, f'{version}.blend')
    made = run([blender, '-b', '--disable-autoexec', '--python', MAKE, '--', scene, version])
    if made.returncode != 0 or not os.path.exists(scene):
        return None, None, f'the scene was not made (exit {made.returncode}): {made.stderr[-300:]}'
    audit_path = os.path.join(work, f'{version}-audit.json')
    audited = run([sys.executable, '-I', '-B', LAUNCHER, 'audit', '--scene', scene, '--settings', settings, '--out', audit_path, '--no-judge'])
    if audited.returncode != 0 or not os.path.exists(audit_path):
        return None, None, f'the audit failed (exit {audited.returncode}): {(audited.stdout + audited.stderr)[-400:]}'
    judged_path = os.path.join(work, f'{version}-judged.json')
    run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'place_audit_check.py'), 'check', audit_path, '--skip-freshness', '--out', judged_path])
    return json.load(open(audit_path)), json.load(open(judged_path)), ''


def findings(judged, name):
    return [f for f in judged['checks'] if f['check'] == name]


faulty, faulty_judged, why = audit_and_judge('faulty')
mended, mended_judged, why_mended = audit_and_judge('mended')
if faulty is None or mended is None:
    check.true('the faulty and the mended scene are made and audited', False, why or why_mended)
    check.finish()

text = lambda judged, name, verdict: ' | '.join(f['text'] for f in findings(judged, name) if f['verdict'] == verdict)   # noqa: E731
verdicts = lambda judged, name: sorted({f['verdict'] for f in findings(judged, name)})                                    # noqa: E731

# 1. film frame
check.true('the case that must fail: a place marked for the film drawn at 1200 x 800 FAILS place: film frame',
           verdicts(faulty_judged, 'place: film frame') == ['fail'] and '1200 x 800' in text(faulty_judged, 'place: film frame', 'fail'), text(faulty_judged, 'place: film frame', 'fail')[:200])
check.equal('the mended scene (1080 x 1920) passes place: film frame', verdicts(mended_judged, 'place: film frame'), ['pass'])

# 2. world
world_text = text(faulty_judged, 'place: world', 'fail')
camera = faulty['views']['cameras'][0]
check.true('the faulty view sees past the ground\'s edge: rays below the horizon hit nothing', camera['empty_below_horizon'] > 0,
           f'{camera["empty_below_horizon"]} of {camera["rays_below_horizon"]} rays below the horizon hit nothing')
for words, why_here in (('stops drawing at 50 m', 'a clip end shorter than the far hills'), ('hit nothing', 'empty sky below the horizon'),
                        ('the backdrop Far hills casts shadows', 'a backdrop that casts shadows'), ('Distant mill', 'a large far object that casts shadows')):
    check.true(f'the case that must fail: place: world names {why_here}', words in world_text, world_text[:240])
check.equal('the mended scene passes place: world', verdicts(mended_judged, 'place: world'), ['pass'])
check.equal('the mended view sees no empty sky below the horizon', mended['views']['cameras'][0]['empty_below_horizon'], 0)

# 3. sun
sun_text = text(faulty_judged, 'place: sun', 'warn')
check.true('the low sun behind the 4 m wall shadows most of the seen ground: a LOOK naming the wall', 'Wall north' in sun_text and 'tan(sun height)' in sun_text, sun_text[:220])
check.true('...measured: more than half the ground points the view sees are shadowed', faulty['views']['cameras'][0]['sun']['shadowed_share'] > 0.5,
           json.dumps(faulty['views']['cameras'][0]['sun'])[:200])
check.true('a high side sun passes place: sun', 'warn' not in verdicts(mended_judged, 'place: sun') and 'fail' not in verdicts(mended_judged, 'place: sun'),
           str(verdicts(mended_judged, 'place: sun')))

# 4. lettering
lettered = {o['name']: o for o in faulty['lettering']['objects']}
letter_text = text(faulty_judged, 'place: lettering', 'fail')
check.true('the case that must fail: a shop sign with no lettering FAILS place: lettering', 'Shop sign' in ' '.join(f['where'] for f in findings(faulty_judged, 'place: lettering')),
           letter_text[:160])
check.true('the ledger book with a text object on it is found and carries lettering', 'Ledger book' in lettered and lettered['Ledger book']['lettering_on_it'],
           json.dumps(lettered.get('Ledger book')))
check.true('a floor board is not taken for a sign ("board" alone does not count)', not any('Floor board' in name for name in lettered), str(sorted(lettered)))
check.equal('the mended scene (the sign carries a text object) passes place: lettering', verdicts(mended_judged, 'place: lettering'), ['pass'])
check.true('the audit counts every object in the scene for place: budgets', faulty['counts'].get('objects_total', 0) >= 10, str(faulty['counts']))

# 5. finish turns the backdrop's shadow off and says which sun the wear layers used
finished_scene = os.path.join(work, 'faulty-finished.blend')
done = run([sys.executable, '-I', '-B', LAUNCHER, 'finish', '--scene', os.path.join(work, 'faulty.blend'), '--settings', settings, '--save-as', finished_scene, '--quick',
            '--out', os.path.join(work, 'finished-audit.json')])
finished = json.load(open(os.path.join(work, 'finished-audit.json'))) if os.path.exists(os.path.join(work, 'finished-audit.json')) else {}
check.true('finish turns the backdrop\'s shadow off (the far hills no longer cast shadows)', 'PASS backdrop' in done.stdout
           and not finished.get('world', {}).get('backdrops_casting_shadows'), [l for l in done.stdout.splitlines() if 'backdrop' in l][:2])
check.true('finish says which sun the wear layers\' shade used (the scene\'s own sun lamp)', 'PASS sun: the wear layers\' shade used the scene\'s sun lamp "Sun"' in done.stdout,
           [l for l in done.stdout.splitlines() if l.startswith('PASS sun')][:1])

# 6. the wear layers read the scene's sun
probe_out = os.path.join(work, 'sun.json')
probed = run([blender, '-b', '--disable-autoexec', os.path.join(work, 'mended.blend'), '--python', PROBE, '--', PLACE_KIT, probe_out])
sun = json.load(open(probe_out)) if os.path.exists(probe_out) else {}
one = sun.get('one sun at compass 20, 35 up', {}).get('record_sun', {})
check.true('with one sun lamp the shade uses it (compass 20, 35 up), not 135 and 45', abs(one.get('compass_degrees', 0) - 20) < 0.5 and abs(one.get('height_degrees', 0) - 35) < 0.5
           and 'sun lamp "Sun"' in one.get('from', ''), json.dumps(one))
check.true('turning the sun to the other side changes the shade mask', sun.get('shade_cells_that_differ_when_the_sun_turns', 0) > 0,
           f'{sun.get("shade_cells_that_differ_when_the_sun_turns")} cells differ')
for label, words in (('two sun lamps', '2 sun lamps'), ('no sun lamp', 'no sun lamp')):
    fallback = sun.get(label, {}).get('record_sun', {})
    check.true(f'with {label} the shade falls back to 135 degrees compass and 45 up, and says why', fallback.get('compass_degrees') == 135.0 and fallback.get('height_degrees') == 45.0
               and words in fallback.get('from', ''), json.dumps(fallback))
check.finish()
