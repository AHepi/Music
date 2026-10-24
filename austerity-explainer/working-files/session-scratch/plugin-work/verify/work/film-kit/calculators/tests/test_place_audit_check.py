"""What this does: tests the JUDGE of a place audit (calculators/place_audit_check.py), which turns the audit's facts into PASS, LOOK, FAIL or KNOWN with the house numbers.
It needs no Blender: the audits are small files made by hand (fixtures/place/flat_hut_audit.json, made like what a model builds when it is only told "make a hut": plain boxes
with no normal maps, no wear, a floating plank; fixtures/place/finished_hut_audit.json, made like the same hut after `explainer-film-place finish`).
1. The flat hut fails and names what it lacks (normal maps, displacement on the ground, dirt, grime, weathering, bevels, shape damage, plants and litter); the finished hut passes.
2. One planted fault at a time on the finished hut, each caught by its own check and named: a quick trial, a changed scene file, a missing treatment, a missing or too small layer
   amount, a normal map in the wrong colour space, pointing the wrong way, with a leftover bump, a coarse mesh under displacement, a floating part, a door of the wrong size, too
   many plain boxes, copies of one object, a plant on a wheel track, too many triangles, no light, the wrong renderer, an off entry with too short a reason.
3. The ways a check must stay fair: wetness at amount 0 is fine when the place is dry; moss at 0 is fine for a kept look; a switched-off treatment with a real reason is KNOWN, not
   a failure; an axis with no slope is "not informative", not a failure.
4. The `fresh` verb (a fresh checker's result) and the `compare` verb (what appeared or vanished between two audits), and the exit codes (0, 1, 2).
Run: python3 kit/calculators/tests/test_place_audit_check.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
import place_audit_check as pac  # noqa: E402
from settings import load_settings  # noqa: E402

check = Checker('place audit judge: flat hut fails, finished hut passes, planted faults are named')
settings = load_settings()
folder = tempfile.mkdtemp(prefix='place-audit-test-')


def load(name):
    with open(os.path.join(FIXTURES, 'place', name)) as handle:
        return json.load(handle)


def judge(audit, **options):
    findings = pac.Judge(copy.deepcopy(audit), settings, **options).run_all()
    return findings


def verdicts(findings, check_name):
    return [f['verdict'] for f in findings if f['check'] == check_name]


def text_of(findings, check_name, verdict='fail'):
    return ' | '.join(f['where'] + ': ' + f['text'] for f in findings if f['check'] == check_name and f['verdict'] == verdict)


def run(args):
    return subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'place_audit_check.py')] + args, capture_output=True, text=True, timeout=120)


flat, finished = load('flat_hut_audit.json'), load('finished_hut_audit.json')

# ---------------------------------------------------------------- 1. flat versus finished
flat_findings = judge(flat, skip_freshness=True)
flat_text = ' '.join(f['text'] for f in flat_findings if f['verdict'] == 'fail')
check.true('the flat hut fails', pac.verdict_of(flat_findings) == 'fail')
for word in ('normal_map', 'displacement', 'dirt', 'grime', 'weathering', 'cracks_and_chips', 'bevelled_edges', 'shape_damage', 'plants', 'litter pieces'):
    check.true(f'the flat hut failure names {word}', word in flat_text, recorded='fixtures/place/flat_hut_audit.json (made by hand like a plain-box hut)')
finished_findings = judge(finished, skip_freshness=True)
check.equal('the finished hut passes', pac.verdict_of(finished_findings), 'pass')
check.true('the finished hut has no FAIL line at all', not [f for f in finished_findings if f['verdict'] == 'fail'])

# ---------------------------------------------------------------- 2. one planted fault at a time
quick = copy.deepcopy(finished)
quick['quick'] = True
quick['map_size_pixels'] = 256
check.true('a quick trial fails as a final and says "quick"', 'quick' in text_of(judge(quick, skip_freshness=True), 'place: quick output'))
check.equal('a quick trial with --allow-quick is a LOOK, not a fail', verdicts(judge(quick, skip_freshness=True, allow_quick=True), 'place: quick output'), ['warn'])

scene_file = os.path.join(folder, 'hut.blend')
with open(scene_file, 'wb') as handle:
    handle.write(b'scene as it was audited')
import hashlib  # noqa: E402
audited = copy.deepcopy(finished)
audited['scene_sha1'] = hashlib.sha1(b'scene as it was audited').hexdigest()
check.equal('an audit of this exact scene file is fresh', verdicts(judge(audited, blend=scene_file), 'place: stale audit'), ['pass'])
with open(scene_file, 'wb') as handle:
    handle.write(b'scene changed after the audit')
check.true('a scene changed after the audit is stale and the failure says so', 'changed after the audit' in text_of(judge(audited, blend=scene_file), 'place: stale audit'))
check.equal('with no scene file given the freshness is only a LOOK', verdicts(judge(audited), 'place: stale audit'), ['warn'])

missing = copy.deepcopy(finished)
missing['materials'][1]['treatments']['dirt']['has'] = False
text = text_of(judge(missing, skip_freshness=True), 'place: treatments')
check.true('a material that lost its dirt is named with the treatment', 'dirt' in text and missing['materials'][1]['name'] in text, text[:160])

silent = copy.deepcopy(finished)
silent['objects'][1]['layer_amounts_missing'] = ['dirt']
silent['objects'][1]['layer_amounts'].pop('dirt', None)
check.true('an object with no pk_dirt_amount is caught (the silent-zero trap)', 'silently read 0' in text_of(judge(silent, skip_freshness=True), 'place: layer amounts'))
tiny = copy.deepcopy(finished)
tiny['objects'][1]['layer_amounts']['grime'] = 0.02
check.true('a layer amount below the floor is caught and named', 'grime' in text_of(judge(tiny, skip_freshness=True), 'place: layer amounts'))

dry_wet = copy.deepcopy(finished)
dry_wet['state'] = 'dry'
for obj in dry_wet['objects']:
    if 'wetness' in obj['layer_amounts']:
        obj['layer_amounts']['wetness'] = 0.0
check.equal('wetness at 0 is fine in a dry place', verdicts(judge(dry_wet, skip_freshness=True), 'place: layer amounts'), ['pass'])
damp_wet = copy.deepcopy(dry_wet)
damp_wet['state'] = 'damp'
check.true('wetness at 0 is NOT fine in a damp place', 'wetness' in text_of(judge(damp_wet, skip_freshness=True), 'place: layer amounts'))
kept = copy.deepcopy(finished)
kept['look'] = 'kept'
for obj in kept['objects']:
    obj['look'] = 'kept'
    if 'moss_and_algae' in obj['layer_amounts']:
        obj['layer_amounts']['moss_and_algae'] = 0.0
check.equal('moss at 0 is fine for a kept look', verdicts(judge(kept, skip_freshness=True), 'place: layer amounts'), ['pass'])
lived = copy.deepcopy(kept)
lived['look'] = 'lived_in'
for obj in lived['objects']:
    obj['look'] = 'lived_in'
check.true('moss at 0 is NOT fine for a lived-in look', 'moss_and_algae' in text_of(judge(lived, skip_freshness=True), 'place: layer amounts'))

srgb = copy.deepcopy(finished)
srgb['normal_maps']['images'][0]['colourspace'] = 'sRGB'
check.true('a normal map left in sRGB fails', 'Non-Color' in text_of(judge(srgb, skip_freshness=True), 'place: normal maps'))
wrong = copy.deepcopy(finished)
wrong['normal_maps']['images'][0]['direction'] = {'x': 0.7, 'y': -0.9, 'method': 'height'}
check.true('a normal map with its green flipped fails and names the axis', 'direction y' in text_of(judge(wrong, skip_freshness=True), 'place: normal maps'))
flat_axis = copy.deepcopy(finished)
flat_axis['normal_maps']['images'][0]['direction'] = {'x': 0.8, 'y': 'not informative', 'method': 'height'}
check.equal('an axis with no slope is "not informative", not a fail', verdicts(judge(flat_axis, skip_freshness=True), 'place: normal maps'), ['pass'])
directx = copy.deepcopy(finished)
directx['normal_maps']['images'][0]['convention'] = 'directx'
check.true('a DirectX map fails', 'DirectX' in text_of(judge(directx, skip_freshness=True), 'place: normal maps'))
bump = copy.deepcopy(finished)
bump['materials'][1]['treatments']['normal_map']['detail']['bump_leftover'] = 1.0
check.true('a leftover Bump of strength 1 fails', 'leftover Bump' in text_of(judge(bump, skip_freshness=True), 'place: normal maps'))
no_test = copy.deepcopy(finished)
no_test['normal_maps'].pop('test_light', None)
check.true('a missing end-to-end test light fails as a final', 'test light' in text_of(judge(no_test, skip_freshness=True), 'place: normal maps'))

coarse = copy.deepcopy(finished)
ground = next(m for m in coarse['materials'] if m['role'].startswith('ground.'))
ground['treatments']['displacement']['detail']['mesh'] = 'coarse'
check.true('a coarse mesh under displacement fails', 'too coarse' in text_of(judge(coarse, skip_freshness=True), 'place: displacement'))
bump_only = copy.deepcopy(finished)
bump_only_ground = next(m for m in bump_only['materials'] if m['role'].startswith('ground.'))
bump_only_ground['treatments']['displacement']['detail']['method'] = 'BUMP'
check.true('displacement left on Bump Only fails', 'Bump Only' in text_of(judge(bump_only, skip_freshness=True), 'place: displacement'))

floating = copy.deepcopy(finished)
floating['objects'][-1]['construction'].update(floating=True, carried=False, gap_mm=60)
check.true('a floating part is named', floating['objects'][-1]['name'] in text_of(judge(floating, skip_freshness=True), 'place: construction'))
inside_out = copy.deepcopy(finished)
inside_out['objects'][2]['construction']['inside_out'] = True
check.true('an inside-out part fails', 'inside out' in text_of(judge(inside_out, skip_freshness=True), 'place: construction'))
no_floor = copy.deepcopy(finished)
no_floor['objects'][1]['construction']['opening_floor_gap_m'] = 0.6
check.true('a doorway with no floor close below fails', 'doorway' in text_of(judge(no_floor, skip_freshness=True), 'place: construction'))

low_door = copy.deepcopy(finished)
low_door['objects'][1]['scale'] = [{'fact': 'door_height', 'dimension': 'height', 'value': 1.0, 'min': 1.6, 'max': 1.9, 'unit': 'm', 'confidence': 'strong'}]
check.true('a door 1.0 m high fails the scale check', 'door_height' in text_of(judge(low_door, skip_freshness=True), 'place: scale'))
guess = copy.deepcopy(low_door)
guess['objects'][1]['scale'][0]['confidence'] = 'guess'
check.equal('the same door against a guessed fact is only a LOOK', (verdicts(judge(guess, skip_freshness=True), 'place: scale')), ['warn'])
with_facts = judge(low_door, skip_freshness=True, facts=[{'id': 'door_height', 'min': 0.9, 'max': 1.1, 'confidence': 'strong'}])
check.equal("the place's own facts file overrides the table (a 1.0 m door passes there)", verdicts(with_facts, 'place: scale'), ['pass'])

boxes = copy.deepcopy(finished)
for obj in boxes['objects']:
    obj['geometry'].update(plain_box=True, bevel=False)
check.true('mostly plain boxes fail and are named', 'plain sharp-edged boxes' in text_of(judge(boxes, skip_freshness=True), 'place: plain boxes'))
copies = copy.deepcopy(finished)
copies['siblings'] = {'timber.floor': {'count': 12, 'copies_share': 0.9, 'all_damaged': False}}
check.true('twelve boards that are mostly exact copies fail', 'exact copies' in text_of(judge(copies, skip_freshness=True), 'place: shape damage'))

on_track = copy.deepcopy(finished)
on_track['scatter'] = {'groups': [{'name': 'tuft', 'group': 'plant', 'count': 20, 'in_keepout': 0, 'in_puddle': 0, 'on_crown': 0, 'on_wheel_track': 2, 'within_5cm_of_litter': 0}]}
check.true('a plant on a wheel track fails (the gate is exact zero)', 'wheel track' in text_of(judge(on_track, skip_freshness=True), 'place: keep-out'))
flat_road = copy.deepcopy(finished)
flat_road['roads'] = [{'name': 'main lane', 'ground_objects': ['ground'], 'relief_m': 0.0, 'ruts_found': False}]
check.true('a road on flat ground with no ruts fails', 'main lane' in text_of(judge(flat_road, skip_freshness=True), 'place: ground relief'))
huge = copy.deepcopy(finished)
huge['counts']['triangles'] = 9_000_000
check.true('too many triangles fails', 'triangles' in text_of(judge(huge, skip_freshness=True), 'place: budgets'))
dark = copy.deepcopy(finished)
dark['light'] = {'any_light': False}
check.true('a scene with no light fails (it renders black)', 'black' in text_of(judge(dark, skip_freshness=True), 'place: light'))
wrong_renderer = copy.deepcopy(finished)
wrong_renderer['renderer'] = {'decision': 'CYCLES', 'reasons': ['lamp "lantern" is on'], 'settings_choice': 'eevee'}
check.true('EEVEE forced where a lamp is lit fails with the reason', 'lantern' in text_of(judge(wrong_renderer, skip_freshness=True), 'place: renderer'))

# ---------------------------------------------------------------- 3. off entries
short_reason = copy.deepcopy(finished)
short_reason['off'] = {'entries': [{'layer': 'moss_and_algae', 'roles': ['wall.*'], 'reason': 'n/a', 'reason_id': None}], 'allowed_ids': ['floors_indoors'], 'share': 0.05}
check.true('an off entry with a one-word reason fails', 'no real reason' in text_of(judge(short_reason, skip_freshness=True), 'place: off reasons'))
allowed = copy.deepcopy(finished)
allowed['off'] = {'entries': [{'layer': 'moss_and_algae', 'roles': ['floor.*'], 'reason': 'inside the buildings: dry, nothing grows', 'reason_id': 'floors_indoors'}], 'allowed_ids': ['floors_indoors'], 'share': 0.05}
check.equal('an off entry the place type allows, with a real reason, is KNOWN', verdicts(judge(allowed, skip_freshness=True), 'place: off reasons'), ['known'])
odd = copy.deepcopy(allowed)
odd['off']['entries'][0].update(roles=['wall.*'], reason_id='my_own_reason', reason='I did not feel like growing moss on the walls')
check.equal('an off entry that is not on the place type list is a LOOK for a person', verdicts(judge(odd, skip_freshness=True), 'place: off reasons'), ['warn'])
many = copy.deepcopy(allowed)
many['off']['share'] = 0.6
check.true('switching off most of the pass is called out', any('required treatment-and-role pairs' in f['text'] for f in judge(many, skip_freshness=True)))

# ---------------------------------------------------------------- 4. the fresh and compare verbs and the exit codes
audit_path = os.path.join(folder, 'finished.json')
flat_path = os.path.join(folder, 'flat.json')
json.dump(finished, open(audit_path, 'w'))
json.dump(flat, open(flat_path, 'w'))
done = run(['check', audit_path])
check.true('the command on the finished audit exits 0 (with a LOOK about the missing scene file)', done.returncode == 0 and 'PASS' in done.stdout, f'exit {done.returncode}')
done = run(['check', flat_path])
check.true('the command on the flat audit exits 1 and prints FAIL lines that say how to fix', done.returncode == 1 and 'FAIL place: treatments' in done.stdout and 'Fix:' in done.stdout, f'exit {done.returncode}')
done = run(['check', os.path.join(folder, 'nothing.json')])
check.equal('the command on a missing audit exits 2', done.returncode, 2)
done = run(['compare', flat_path, audit_path])
check.true('compare says which treatments appeared between the flat and the finished audit', done.returncode == 0 and 'normal_map' in done.stdout, f'exit {done.returncode}')
fresh_good = {'mode': 'look', 'was_blind': True, 'not_tested': ['the colour of the door'], 'claims_checked': [{'claim': 'the ground has ruts', 'holds': True, 'evidence': 'measured 6 cm deep'}],
              'art_style_kept': 'yes', 'lived_in': 'yes', 'construction_makes_sense': 'yes', 'problems': []}
fresh_bad = {'mode': 'look', 'was_blind': True, 'not_tested': ['nothing'], 'claims_checked': [{'claim': 'the ground has ruts', 'holds': False, 'evidence': 'the ground is flat'}],
             'art_style_kept': 'yes', 'lived_in': 'yes', 'construction_makes_sense': 'yes', 'problems': []}
fresh_no_blind = {'mode': 'look', 'claims_checked': [], 'art_style_kept': 'yes', 'lived_in': 'yes', 'construction_makes_sense': 'yes', 'problems': []}
for name, data in (('fresh_good.json', fresh_good), ('fresh_bad.json', fresh_bad), ('fresh_no_blind.json', fresh_no_blind)):
    json.dump(data, open(os.path.join(folder, name), 'w'))
done = run(['fresh', os.path.join(folder, 'fresh_good.json')])
check.equal('a fresh check whose claims hold exits 0', done.returncode, 0)
done = run(['fresh', os.path.join(folder, 'fresh_bad.json')])
check.true('a fresh check with a claim that does not hold exits 1 and names the claim', done.returncode == 1 and 'ruts' in done.stdout, f'exit {done.returncode}')
done = run(['fresh', os.path.join(folder, 'fresh_no_blind.json')])
check.true('a fresh check that does not say whether it was blind, or what it did not test, is a LOOK (exit 0)', done.returncode == 0 and 'LOOK' in done.stdout and 'blind' in done.stdout, f'exit {done.returncode}')
check.finish()
