"""What this does: tests the PLACE stage of the preflight (preflight.py place, the command explainer-film-preflight place) on small made-up files, so it runs on any machine with the
plugin alone (no Blender).
1. The stage is listed with its inputs and the tool that makes each (the audit: explainer-film-place audit), and the order of the stages is said plainly (shots, build the place, place, plates).
2. A flat hut's audit stops the stage (exit 1) and the report names what is missing; the finished hut's audit passes it (exit 0) with a LOOK that no fresh checker has looked.
3. An audit made from one scene file does not pass for another: a changed scene file makes the audit STALE (exit 1).
4. A missing audit stops the stage (exit 2) and says which tool makes it. A quick trial audit fails as a final and passes only with --allow-quick, as a LOOK.
5. Pictures with no style guard are a LOOK; with a guard made from the first picture the pictures are measured (a flat picture fails); a guard that is still provisional is a LOOK.
6. A fresh checker's failed claim stops the stage.
7. The plates stage, given a scene file, asks for the place audit (a place built in Blender must pass its audit before a paid painting); given none, it says as a LOOK that no audit could be required.
8. The place stage with an audit writes its reports in a preflight-reports folder beside the audit (an explicit --reports wins); --facts is the same option as --real-world-facts and the place's own facts change the verdict.
Run: python3 kit/calculators/tests/test_preflight_place.py   (about 10 seconds)
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, skip  # noqa: E402

try:
    import numpy as np
    from PIL import Image
except ImportError:
    skip('preflight place stage', 'numpy and Pillow are needed to make the test pictures (pip install numpy pillow)')

import preflight  # noqa: E402

PREFLIGHT = os.path.join(CALCULATORS, 'preflight.py')
check = Checker('preflight: the place stage (audit, freshness, pictures, fresh checker) and the plates stage asking for it')
work = tempfile.mkdtemp(prefix='preflight-place-test-')


def run(*arguments, timeout=300):
    """Runs the preflight; returns (exit code, plain output, the report's JSON or {})."""
    done = subprocess.run([sys.executable, '-I', '-B', PREFLIGHT] + [str(a) for a in arguments], capture_output=True, text=True, timeout=timeout)
    reports = os.path.join(work, 'preflight-reports')
    stage = arguments[0]
    newest = preflight.newest_report(reports, stage) if os.path.isdir(reports) else None
    data = json.load(open(newest)) if newest and os.path.getmtime(newest) >= time.time() - timeout else {}
    return done.returncode, done.stdout + done.stderr, data


def load(name):
    with open(os.path.join(FIXTURES, 'place', name)) as handle:
        return json.load(handle)


def fail_texts(data):
    return ' | '.join(f['text'] for c in data.get('checks', []) for f in c['findings'] if f['verdict'] == 'fail')


def look_texts(data):
    return ' | '.join(f['text'] for c in data.get('checks', []) for f in c['findings'] if f['verdict'] == 'warn')


# the stand-in scene file and two audits that belong to it
scene = os.path.join(work, 'hut.blend')
with open(scene, 'wb') as handle:
    handle.write(b'a scene file for the freshness test')
sha = hashlib.sha1(open(scene, 'rb').read()).hexdigest()
finished = load('finished_hut_audit.json')
finished['scene_sha1'] = sha
flat = load('flat_hut_audit.json')
flat['scene_sha1'] = sha
finished_path, flat_path = os.path.join(work, 'finished-audit.json'), os.path.join(work, 'flat-audit.json')
json.dump(finished, open(finished_path, 'w'))
json.dump(flat, open(flat_path, 'w'))

try:
    # ---------------------------------------------------------------- 1. listed, with its order
    code, out, _ = run('place', '--list')
    check.true('--list names the place stage with the audit and the tool that makes it', code == 0 and '\nplace: after building a place' in out and '--place-audit' in out and 'explainer-film-place audit' in out, f'exit {code}')
    check.true('the stage list has the place stage between shots and plates', preflight.STAGES.index('shots') < preflight.STAGES.index('place') < preflight.STAGES.index('plates'),
               str(preflight.STAGES))
    code, out, plan_text = run('place', '--example-plan')
    check.true('--example-plan has a place entry with the audit, the scene and the pictures', code == 0 and '"place_audit"' in out and '"blend"' in out and '"place_pictures"' in out)

    # ---------------------------------------------------------------- 2. flat fails, finished passes
    code, out, data = run('place', '--project', work, '--place-audit', flat_path, '--blend', scene)
    check.true('the flat hut audit stops the stage (exit 1) and the first line says FAIL', code == 1 and out.startswith('Preflight place'), out.splitlines()[0])
    text = fail_texts(data)
    check.true('the report names what the flat hut lacks (normal maps, dirt, grime, displacement, bevels)', all(word in text for word in ('normal_map', 'dirt', 'grime', 'displacement', 'bevelled_edges')), text[:160])
    check.true('the long step (drawing the place) is blocked with its reason', 'BLOCKED' in out, out.splitlines()[1] if len(out.splitlines()) > 1 else '')
    code, out, data = run('place', '--project', work, '--place-audit', finished_path, '--blend', scene)
    check.equal('the finished hut audit passes the stage (exit 0)', code, 0)
    check.true('it still says, as a LOOK, that no fresh checker has looked', 'no fresh checker has looked' in look_texts(data), look_texts(data)[:160])
    check.true('the report says the order of the stages in its notes', any('shots (before building), build the place, place' in n for n in data.get('notes', [])), str(data.get('notes'))[:200])
    check.true('the report hashes its inputs (the audit and the scene file)', any(p.endswith('finished-audit.json') for p in data.get('inputs', {})) and any(p.endswith('hut.blend') for p in data.get('inputs', {})),
               str(list(data.get('inputs', {}))))

    # ---------------------------------------------------------------- 3. stale
    with open(scene, 'ab') as handle:
        handle.write(b' and then somebody changed it')
    code, out, data = run('place', '--project', work, '--place-audit', finished_path, '--blend', scene)
    check.true('a scene file changed after the audit makes the stage fail as stale', code == 1 and 'changed after the audit' in fail_texts(data), fail_texts(data)[:160])
    with open(scene, 'wb') as handle:
        handle.write(b'a scene file for the freshness test')

    # ---------------------------------------------------------------- 4. missing audit, quick
    code, out, data = run('place', '--project', work)
    check.true('no audit: exit 2, and it names the tool that makes one', code == 2 and 'explainer-film-place audit' in out, out.splitlines()[0])
    quick = copy.deepcopy(finished)
    quick['quick'] = True
    quick['map_size_pixels'] = 256
    quick_path = os.path.join(work, 'quick-audit.json')
    json.dump(quick, open(quick_path, 'w'))
    code, out, data = run('place', '--project', work, '--place-audit', quick_path, '--blend', scene)
    check.true('a quick trial audit fails as a final', code == 1 and 'quick' in fail_texts(data), fail_texts(data)[:160])
    code, out, data = run('place', '--project', work, '--place-audit', quick_path, '--blend', scene, '--allow-quick')
    check.equal('with --allow-quick the same audit passes (as a LOOK)', code, 0)

    # ---------------------------------------------------------------- 5. pictures and the guard
    rng = np.random.default_rng(5)
    folder = os.path.join(work, 'pictures')
    os.makedirs(folder)
    gentle = np.clip(0.45 + rng.normal(0, 0.03, (192, 288, 1)), 0, 1).repeat(3, axis=2)
    Image.fromarray((gentle * 255).astype(np.uint8)).save(os.path.join(folder, 'a.png'))
    code, out, data = run('place', '--project', work, '--place-audit', finished_path, '--blend', scene, '--place-pictures', folder)
    check.true('pictures with no style guard are a LOOK that says so', code == 0 and 'no style guard' in look_texts(data), look_texts(data)[:200])
    guard = os.path.join(work, 'guard.json')
    made = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'picture_measures.py'), 'make-guard', os.path.join(folder, 'a.png'), '--out', guard], capture_output=True, text=True)
    check.true('the guard is made from the first picture', made.returncode == 0 and os.path.exists(guard), f'exit {made.returncode}')
    code, out, data = run('place', '--project', work, '--place-audit', finished_path, '--blend', scene, '--place-pictures', folder, '--style-guard', guard)
    check.true('the same picture against its own guard passes, with a LOOK that the guard is provisional', code == 0 and 'has not been accepted by a person' in look_texts(data), f'exit {code}: ' + look_texts(data)[:160])
    flat_folder = os.path.join(work, 'flat-pictures')
    os.makedirs(flat_folder)
    Image.fromarray(np.full((192, 288, 3), 115, np.uint8)).save(os.path.join(flat_folder, 'a.png'))
    code, out, data = run('place', '--project', work, '--place-audit', finished_path, '--blend', scene, '--place-pictures', flat_folder, '--style-guard', guard)
    check.true('a flat grey picture against that guard stops the stage and the report names flat windows', code == 1 and 'flat' in fail_texts(data), fail_texts(data)[:200])

    # ---------------------------------------------------------------- 6. fresh checker
    fresh_bad = {'mode': 'look', 'was_blind': True, 'not_tested': ['the colour of the door'], 'claims_checked': [{'claim': 'the ground has ruts', 'holds': False, 'evidence': 'the ground is flat'}],
                 'art_style_kept': 'yes', 'lived_in': 'yes', 'construction_makes_sense': 'yes', 'problems': []}
    fresh_path = os.path.join(work, 'fresh.json')
    json.dump(fresh_bad, open(fresh_path, 'w'))
    code, out, data = run('place', '--project', work, '--place-audit', finished_path, '--blend', scene, '--fresh-check', fresh_path)
    check.true("a fresh checker's failed claim stops the stage", code == 1 and 'ruts' in fail_texts(data), fail_texts(data)[:160])

    # ---------------------------------------------------------------- 7. plates asks for the audit
    code, out, data = run('plates', '--project', work, '--blend', scene)
    check.true('the plates stage, given a scene file, lists the place audit among what it needs', code == 2 and '--place-audit' in out, out.splitlines()[0])
    check.true('the plates stage names the tool that makes the audit', 'explainer-film-place audit' in out, '')
    # ---------------------------------------------------------------- 8. the plates stage without a scene file says so, the place stage writes beside its audit, --facts is the same as --real-world-facts
    import shutil
    plates_folder = os.path.join(work, 'plates-no-scene')
    os.makedirs(os.path.join(plates_folder, 'facts'), exist_ok=True)
    plate_picture = os.path.join(plates_folder, 'works-w1-plate.png')
    shutil.copy(os.path.join(FIXTURES, 'effects-camera-light', 'busy-2-windows-79.00.png'), plate_picture)
    shot_report_stand_in = os.path.join(plates_folder, 'report.md')
    open(shot_report_stand_in, 'w').write('# report\n')
    plate_arguments = ['plates', '--project', work, '--check', os.path.join(FIXTURES, 'notice-corner', 'notice-corner-shot-check.json'), '--plate', plate_picture, '--plate-facts', os.path.join(plates_folder, 'facts'),
                       '--render-log', os.path.join(FIXTURES, 'effects-camera-light', 'render-log-works-plates-round5-excerpt.log'), '--shot-report', shot_report_stand_in]
    code, out, data = run(*plate_arguments)
    not_audited = [f for c in data.get('checks', []) for f in c['findings'] if f['check'] == 'place: not audited']
    check.true('plates with no scene file at all: a LOOK says no audit could be required, and what to give', len(not_audited) == 1 and not_audited[0]['verdict'] == 'warn' and '--blend' in not_audited[0]['fix'], str(not_audited)[:200])
    check.true('that LOOK does not stop a plate that has nothing to do with a scene built in Blender', not any(f['check'] == 'place: not audited' and f['verdict'] == 'fail' for c in data.get('checks', []) for f in c['findings']))

    elsewhere = os.path.join(work, 'elsewhere')
    os.makedirs(elsewhere, exist_ok=True)
    other_project = os.path.join(work, 'other-project')
    os.makedirs(other_project, exist_ok=True)
    beside_audit = os.path.join(elsewhere, 'finished-audit.json')
    json.dump(finished, open(beside_audit, 'w'))
    done = subprocess.run([sys.executable, '-I', '-B', PREFLIGHT, 'place', '--project', other_project, '--place-audit', beside_audit, '--blend', scene], capture_output=True, text=True, timeout=300)
    written_beside = [name for name in os.listdir(os.path.join(elsewhere, 'preflight-reports'))] if os.path.isdir(os.path.join(elsewhere, 'preflight-reports')) else []
    check.true('the place stage with an audit and no --reports writes its report in a preflight-reports folder beside the audit', done.returncode == 0 and any(n.startswith('preflight-place-') and n.endswith('.json') for n in written_beside),
               f'exit {done.returncode}; beside the audit: {written_beside}; ' + done.stdout[:120])
    check.true('and leaves nothing in the project folder it was started with', not os.path.exists(os.path.join(other_project, 'preflight-reports')), str(os.listdir(other_project)))
    explicit = os.path.join(work, 'explicit-reports')
    done = subprocess.run([sys.executable, '-I', '-B', PREFLIGHT, 'place', '--project', other_project, '--place-audit', beside_audit, '--blend', scene, '--reports', explicit], capture_output=True, text=True, timeout=300)
    check.true('control: an explicit --reports still wins over the folder beside the audit', done.returncode == 0 and os.path.isdir(explicit) and any(n.startswith('preflight-place-') for n in os.listdir(explicit)), done.stdout[:160])

    scaled = copy.deepcopy(finished)
    scaled['objects'][1]['scale'] = [{'fact': 'door_height', 'dimension': 'height', 'value': 2.0, 'min': 1.6, 'max': 2.3, 'unit': 'm', 'confidence': 'weak'}]       # a door 2 m high: right by the kit's own table
    scaled_path = os.path.join(work, 'scaled-audit.json')
    json.dump(scaled, open(scaled_path, 'w'))
    own_facts = os.path.join(work, 'own-facts.json')
    json.dump({'facts': [{'id': 'door_height', 'what': 'doors in this made-up place are knee high', 'dimension': 'height', 'min': 0.3, 'max': 0.5, 'unit': 'metres', 'kind': 'measured',
                          'source': 'a made-up test place', 'confidence': 'strong'}]}, open(own_facts, 'w'))
    code, out, data = run('place', '--project', work, '--place-audit', scaled_path, '--blend', scene)
    check.true('control: with no facts file of its own, a 2 m door passes the scale check', code == 0 and 'door_height' not in fail_texts(data), fail_texts(data)[:160])
    code, out, data = run('place', '--project', work, '--place-audit', scaled_path, '--blend', scene, '--real-world-facts', own_facts)
    check.true('--real-world-facts hands the place\'s own facts to the audit judge (the same door now fails)', code == 1 and 'door_height' in fail_texts(data), f'exit {code}: ' + fail_texts(data)[:160])
    code_alias, out_alias, data_alias = run('place', '--project', work, '--place-audit', scaled_path, '--blend', scene, '--facts', own_facts)
    check.true('--facts is the same option as --real-world-facts (the same door fails the same way)', code_alias == 1 and 'door_height' in fail_texts(data_alias), f'exit {code_alias}: ' + fail_texts(data_alias)[:160])
    check.true('the report lists the facts file among its inputs', any(p.endswith('own-facts.json') for p in data_alias.get('inputs', {})), str(list(data_alias.get('inputs', {})))[:200])
finally:
    pass
check.finish()
