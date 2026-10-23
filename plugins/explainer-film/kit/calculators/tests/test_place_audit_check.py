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
5. The gaps the 1.4.0 smoke check, review and newcomer judge found in the gate (section 2b): an object with no material at all, ground that must grow things whatever its material, things drawn
   that are not meshes, an audit of nothing, too many fallback roles, a dirt road with no road entry or one whose outline grew, a scene lit by its world alone, a seat error that names its ground,
   a step rise judged top to top; each is planted in the finished hut, must fail there with the object's name, and must NOT fail when the fault is taken out again.
6. The lessons round's checks (23 October; inside Blender they are tested by test_place_world.py): an audit made before they existed says "not measured by this audit" (a LOOK,
   never a FAIL) for place: film frame, world, sun, lettering and the object count; a place for the film at a preview size of the same tall shape passes, a view camera set to a
   wide size fails; too many objects fail place: budgets; a wear-layer sun far from the scene's sun is a LOOK; a sign with a lettering picture passes; a haze volume is a LOOK.
7. The fix round's changes (23 October): a prop built alone (3 m across, not for the film) gets a LOOK, not a FAIL, for a view that sees past its small ground, while the same prop
   for the film, or a place 40 m across, still fails; a clip end too short names the figure needed; 1,500 objects is a LOOK and 5,000 a FAIL; a beam with 2.8 m free fails and names its
   role's 2.5 m, and passes when the place's own facts file holds a sourced "free_span" fact for it (not when the fact has no source, nor past the fact's own figure).
Run: python3 kit/calculators/tests/test_place_audit_check.py
"""
import copy
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, work_folder  # noqa: E402
import place_audit_check as pac  # noqa: E402
from settings import load_settings  # noqa: E402

check = Checker('place audit judge: flat hut fails, finished hut passes, planted faults are named')
settings = load_settings()
folder = work_folder('place-audit-test-')


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
flat_road['roads'] = [{'name': 'main road', 'ground_objects': ['ground'], 'relief_m': 0.0, 'ruts_found': False}]
check.true('a road on flat ground with no ruts fails', 'main road' in text_of(judge(flat_road, skip_freshness=True), 'place: ground relief'))
huge = copy.deepcopy(finished)
huge['counts']['triangles'] = 9_000_000
check.true('too many triangles fails', 'triangles' in text_of(judge(huge, skip_freshness=True), 'place: budgets'))
dark = copy.deepcopy(finished)
dark['light'] = {'any_light': False}
check.true('a scene with no light fails (it renders black)', 'black' in text_of(judge(dark, skip_freshness=True), 'place: light'))
wrong_renderer = copy.deepcopy(finished)
wrong_renderer['renderer'] = {'decision': 'CYCLES', 'reasons': ['lamp "lantern" is on'], 'settings_choice': 'eevee'}
check.true('EEVEE forced where a lamp is lit fails with the reason', 'lantern' in text_of(judge(wrong_renderer, skip_freshness=True), 'place: renderer'))

# ---------------------------------------------------------------- 2b. the gaps found in the 1.4.0 fix round
def after(audit, check_name, verdict='fail'):
    return text_of(judge(audit, skip_freshness=True), check_name, verdict)


bare = copy.deepcopy(finished)
bare['objects'][1].update(materials=[], has_normal_map=False, unsurfaced=True, surface_missing=['normal_map', 'roughness_variation', 'colour_variation', 'dirt', 'grime'])
text = after(bare, 'place: treatments')
check.true('an object with no material at all FAILS by name and names what it lacks (the hole the smoke check found: no material, so no material row to fail)', 'wall_north' in text and 'no material' in text and 'normal_map' in text, text[:200],
           recorded='smoke check of the canal lock: a scene of objects with no material passed with zero normal maps, zero wear and zero weeds', proves='the per-object check is independent of the material rows')
bare['objects'][1].update(unsurfaced=False, surface_missing=[])
check.true('...and the same object with its surface present is not named', 'wall_north' not in after(bare, 'place: treatments'))
never = copy.deepcopy(bare)
never['objects'][1].update(unsurfaced=True, surface_missing=['normal_map'], exempt=True)
check.true('an exempt object (a helper, scattered litter) is not failed for having no material', 'wall_north' not in after(never, 'place: treatments'))
nothing_required = copy.deepcopy(bare)
nothing_required['objects'][1].update(unsurfaced=True, surface_missing=[])
check.true('an object whose role requires nothing in a material (glass) is not failed for having none', 'wall_north' not in after(nothing_required, 'place: treatments'))

bare_ground = copy.deepcopy(finished)
bare_ground['materials'] = [m for m in bare_ground['materials'] if not m['role'].startswith('ground.')]
bare_ground['scatter']['required'] = {'plants': {'required_by': ['ground'], 'count': 0, 'per_100_square_metres': 0.0, 'has': False}, 'litter_pieces': {'required_by': ['ground'], 'count': 0, 'per_100_square_metres': 0.0, 'has': False}}
text = after(bare_ground, 'place: treatments')
check.true('a ground with no material must still grow plants and litter: both are failed from the ground ROLE, with no ground material row to say it', 'no plants on the ground' in text and 'no litter pieces on the ground' in text, text[:200])
bare_ground['scatter']['required']['plants'].update(count=300, per_100_square_metres=300.0, has=True)
check.true('...and it passes once plants grow there', 'no plants' not in after(bare_ground, 'place: treatments'))
twice = copy.deepcopy(finished)
twice['materials'][0]['treatments']['plants']['has'] = False
twice['scatter']['required'] = {'plants': {'required_by': ['ground'], 'count': 0, 'per_100_square_metres': 0.0, 'has': False}}
check.equal('a ground whose material and role both say "no plants" is reported once, not twice', sum(1 for f in judge(twice, skip_freshness=True) if f['verdict'] == 'fail' and 'no plants' in f['text']), 1)

drawn = copy.deepcopy(finished)
drawn['non_mesh'] = [{'name': 'Rope 1', 'type': 'curve', 'what': 'a curve object that draws faces'}, {'name': 'Barrel instance', 'type': 'instance', 'what': 'an empty that instances the collection "barrel"'}]
text = after(drawn, 'place: object types')
check.true('a curve, text or instance that is drawn but is not a mesh FAILS by name (they escaped the whole pass)', 'Rope 1' in text and 'Barrel instance' in text and 'not meshes' in text, text[:200])
check.equal('...and an audit with none of them passes that check', verdicts(judge(finished, skip_freshness=True), 'place: object types'), ['pass'])

nothing = copy.deepcopy(finished)
nothing['counts']['objects_visible'] = 0
nothing['objects'] = []
check.true('an audit of nothing FAILS (an empty scene, or the wrong file), it no longer passes "every visible object has a role (0 objects)"', 'no visible mesh objects' in after(nothing, 'place: roles'))

fallbacks = copy.deepcopy(finished)
fallbacks['roles']['fallback'] = ['wall_north', 'wall_south', 'roof']
check.true('a third of the objects on a fallback role FAILS (the share is 15 percent, not the 50 the design first said)', 'fallback role' in after(fallbacks, 'place: roles'))
fallbacks['roles']['fallback'] = ['roof']
check.equal('...and one object in nine (11 percent) is only a LOOK', verdicts(judge(fallbacks, skip_freshness=True), 'place: roles'), ['warn'])

road = copy.deepcopy(finished)
road['objects'][0].update(role='ground.dirt_road')
road['objects'][0]['geometry'].update(road_entry=False, relief_m=0.0)
text = after(road, 'place: ground relief')
check.true('a dirt-road object with no road in the settings and no relief FAILS and says to write a road (a plain request drafted none before)', 'ground' in text and 'no entry' in text, text[:200])
road['objects'][0]['geometry'].update(relief_m=0.08)
check.true('...and the same road with real relief does not', 'no entry' not in after(road, 'place: ground relief'))
road['objects'][0]['geometry'].update(road_entry=True, relief_m=0.0)
check.true('...and one with a road entry is judged by the roads section, not by this', 'no entry' not in after(road, 'place: ground relief'))
grown = copy.deepcopy(finished)
grown['objects'][0]['geometry']['area_growth'] = 3.4
check.true('a ground object whose outline grew 3.4 times (a curved road turned into its box) FAILS and says so', 'bigger than before' in after(grown, 'place: ground relief'))
grown['objects'][0]['geometry']['area_growth'] = 1.0
check.true('...and one that kept its outline does not', 'bigger than before' not in after(grown, 'place: ground relief'))

world_only = copy.deepcopy(finished)
world_only['light'] = {'any_light': True, 'lamps': 0, 'world_light': True, 'clip_share': None}
check.equal('a scene lit only by its world colour is a LOOK ("no lamp, so no direction of light")', verdicts(judge(world_only, skip_freshness=True), 'place: light'), ['warn'])
world_only['light']['lamps'] = 1
check.equal('...and with a lamp it passes', verdicts(judge(world_only, skip_freshness=True), 'place: light'), ['pass'])

seated = copy.deepcopy(finished)
seated['objects'][1]['construction'].update(seat_error_m=-2.0, needs_ground=True, seat_ground_object='Towpath', seat_ground_m=0.0)
findings = judge(seated, skip_freshness=True)
text = text_of(findings, 'place: construction')
check.true('a seat error names the ground it was measured against, so a corner over another ground object can be told from a real fault', 'Towpath' in text and '-2.00 m' in text, text[:200])
fix_text = ' '.join(f['fix'] for f in findings if f['check'] == 'place: construction')
check.true('...and its fix says what to do when the ground named is not the one the part stands on', 'corner of the part lies over that other ground' in fix_text)
hung = copy.deepcopy(finished)
hung['objects'][1]['construction'].update(hung=True, hang_allowed=False)
fix_text = ' '.join(f['fix'] for f in judge(hung, skip_freshness=True) if f['check'] == 'place: construction')
check.true('a hung part\'s fix names the framed-in joinery (two carried parts) and the roles that may hang', 'TWO carried parts' in fix_text and 'timber.fence' not in fix_text and 'doors, shutters, fences' in fix_text)

steps = copy.deepcopy(finished)
steps['objects'][1]['scale'] = [{'fact': 'step_rise', 'dimension': 'rise', 'value': 1.83, 'min': 0.1, 'max': 0.25, 'unit': 'metres', 'confidence': 'weak'}]
check.true('a step with a rise of 1.83 m FAILS the scale check', 'step_rise' in after(steps, 'place: scale'))
steps['objects'][1]['scale'][0]['value'] = 0.17
check.equal('a step with a rise of 17 cm passes', verdicts(judge(steps, skip_freshness=True), 'place: scale'), ['pass'])

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

# ---------------------------------------------------------------- the place settings the audit was made with (--place-settings)
settings_file_path = os.path.join(folder, 'place-settings.json')
with open(settings_file_path, 'w') as handle:
    handle.write('{"look": "lived_in"}\n')
with open(settings_file_path, 'rb') as handle:
    settings_sha = hashlib.sha1(handle.read()).hexdigest()
with_settings = copy.deepcopy(finished)
with_settings['settings_sha1'] = settings_sha
audit_with_settings = os.path.join(folder, 'audit-with-settings.json')
json.dump(with_settings, open(audit_with_settings, 'w'))
done = run(['check', audit_with_settings, '--skip-freshness', '--place-settings', settings_file_path])
check.true('the audit made with this settings file passes the settings check (and says so)', done.returncode == 0 and 'PASS place: stale settings' in done.stdout, f'exit {done.returncode}: ' + done.stdout[:200])
with open(settings_file_path, 'w') as handle:
    handle.write('{"look": "derelict"}\n')
done = run(['check', audit_with_settings, '--skip-freshness', '--place-settings', settings_file_path])
check.true('a settings file edited after the audit fails it as stale and says what to run', done.returncode == 1 and 'FAIL place: stale settings' in done.stdout and 'audit again' in done.stdout, f'exit {done.returncode}: ' + done.stdout[:300])
done = run(['check', audit_with_settings, '--skip-freshness'])
check.true('control: with no --place-settings the same audit has no settings check at all (the option is what asks for it)', done.returncode == 0 and 'stale settings' not in done.stdout, f'exit {done.returncode}')
no_hash = copy.deepcopy(finished)
no_hash['settings_sha1'] = None
audit_no_hash = os.path.join(folder, 'audit-no-hash.json')
json.dump(no_hash, open(audit_no_hash, 'w'))
done = run(['check', audit_no_hash, '--skip-freshness', '--place-settings', settings_file_path])
check.true('an audit that records no settings hash is a LOOK, not a pass', done.returncode == 0 and 'LOOK place: stale settings' in done.stdout, f'exit {done.returncode}')
done = run(['check', audit_with_settings, '--skip-freshness', '--place-settings', os.path.join(folder, 'no-such-settings.json')])
check.true('a settings file that is not there exits 2 and names the command that makes one', done.returncode == 2 and 'new-settings' in done.stdout + done.stderr, f'exit {done.returncode}')

# ---------------------------------------------------------------- 6. the lessons round's checks (film frame, world, sun, lettering, object count)
older = copy.deepcopy(finished)
for key in ('views', 'world', 'sun', 'lettering'):
    older.pop(key, None)
older['counts'].pop('objects_total', None)
older_findings = judge(older, skip_freshness=True)
for name in ('place: film frame', 'place: world', 'place: sun', 'place: lettering', 'place: budgets'):
    check.true(f'an audit made before the lessons round: {name} says "not measured by this audit" as a LOOK, never a FAIL',
               'warn' in verdicts(older_findings, name) and 'fail' not in verdicts(older_findings, name) and 'not measured by this audit' in text_of(older_findings, name, 'warn'),
               str(verdicts(older_findings, name)))
check.true('...so the older audit still has no FAIL line (exit 0)', not [f for f in older_findings if f['verdict'] == 'fail'])
film = copy.deepcopy(finished)
film['views']['for_film'] = True
film['views']['render_size'] = [540, 960, 100]
check.equal('a place for the film at a preview size of the same tall shape (540 x 960) passes place: film frame', verdicts(judge(film, skip_freshness=True), 'place: film frame'), ['pass'])
film['views']['cameras'][0]['view_size'] = [1200, 800]
check.true('the case that must fail: a view camera set to 1200 x 800 in a place for the film FAILS place: film frame',
           verdicts(judge(film, skip_freshness=True), 'place: film frame') == ['fail'] and 'Camera A' in after(film, 'place: film frame'), after(film, 'place: film frame')[:160])
film['views']['for_film'] = False
check.equal('...and the same camera is fine when the place is not for the film', verdicts(judge(film, skip_freshness=True), 'place: film frame'), ['pass'])
crowded = copy.deepcopy(finished)
crowded['counts']['objects_total'] = 5000
check.true('the case that must fail: 5,000 objects FAIL place: budgets and say to build in bulk', 'in bulk' in after(crowded, 'place: budgets'), after(crowded, 'place: budgets')[:200])
turned = copy.deepcopy(finished)
turned['sun'] = {'name': 'Evening sun', 'compass_degrees': 300.0, 'height_degrees': 12.0, 'energy': 3.0}
check.true('a wear-layer sun far from the scene\'s sun is a LOOK that says to finish again', 'finish again' in ' '.join(f['fix'] for f in judge(turned, skip_freshness=True) if f['check'] == 'place: sun' and f['verdict'] == 'warn'),
           text_of(judge(turned, skip_freshness=True), 'place: sun', 'warn')[:200])
signs = copy.deepcopy(finished)
signs['lettering'] = {'checked': 2, 'objects': [{'name': 'Bank sign', 'word': 'sign', 'found_by': 'name', 'picture_texture': True, 'text_made': False, 'lettering_on_it': []},
                                                 {'name': 'Notice 2', 'word': 'notice', 'found_by': 'name', 'picture_texture': False, 'text_made': False, 'lettering_on_it': []}]}
letter_findings = judge(signs, skip_freshness=True)
check.true('a sign with a lettering picture passes and a bare notice FAILS place: lettering, named', 'Notice 2' in ' '.join(f['where'] for f in letter_findings if f['check'] == 'place: lettering' and f['verdict'] == 'fail')
           and 'Bank sign' not in ' '.join(f['where'] for f in letter_findings if f['check'] == 'place: lettering' and f['verdict'] == 'fail'), text_of(letter_findings, 'place: lettering')[:160])
hazy = copy.deepcopy(finished)
hazy['world']['haze_volume'] = True
check.true('a haze volume in the world is a LOOK', 'haze' in text_of(judge(hazy, skip_freshness=True), 'place: world', 'warn'))

# ---------------------------------------------------------------- 7. the fix round (23 October): a prop built alone, the clip end's figure, the object count's band, a sourced long span
prop = copy.deepcopy(finished)
prop['world']['place_span_m'] = 3.0          # the verify step's crate: one crate on a 3 m square of ground and one close camera; 290 of 544 rays below the horizon hit nothing
prop['views']['cameras'][0].update({'name': 'View crate', 'rays_below_horizon': 544, 'empty_below_horizon': 290, 'empty_below_horizon_share': 290 / 544})
prop_findings = judge(prop, skip_freshness=True)
check.true('a prop built alone (3 m across, not for the film) whose close camera sees past its small ground gets a LOOK in place: world, not a FAIL, and the LOOK says why',
           verdicts(prop_findings, 'place: world') == ['warn'] and 'built alone' in text_of(prop_findings, 'place: world', 'warn'), str(verdicts(prop_findings, 'place: world')))
prop['views']['for_film'] = True
check.true('...the case that must fail: the same prop marked for the film FAILS place: world', 'fail' in verdicts(judge(prop, skip_freshness=True), 'place: world'))
prop['views']['for_film'] = False
prop['world']['place_span_m'] = 40.0
check.true('...and so does a place 40 m across (the test yard\'s size)', 'fail' in verdicts(judge(prop, skip_freshness=True), 'place: world'))
far = copy.deepcopy(finished)
far['views']['cameras'][0].update({'clip_end_m': 1000.0, 'farthest_depth_m': 1958.99, 'farthest_object': 'Ground'})
far_fix = ' '.join(f['fix'] for f in judge(far, skip_freshness=True) if f['check'] == 'place: world' and f['verdict'] == 'fail')
check.true('a 1000 m clip end with a ground reaching 1959 m deep FAILS, and the fix names the figure needed (at least 1960 m), not only "1000 m or more"',
           'at least 1960 m' in far_fix and 'past the far edge of the ground and the backdrop' in far_fix, far_fix[-220:])
busy = copy.deepcopy(finished)
busy['counts']['objects_total'] = 1500
busy_findings = judge(busy, skip_freshness=True)
check.true('1,500 objects (over 1,000, under 3,000) is a LOOK in place: budgets, not a FAIL: a large place can be over for honest reasons',
           'warn' in verdicts(busy_findings, 'place: budgets') and 'fail' not in verdicts(busy_findings, 'place: budgets') and 'honest' in text_of(busy_findings, 'place: budgets', 'warn'),
           str(verdicts(busy_findings, 'place: budgets')))
gallery = copy.deepcopy(finished)
beam = copy.deepcopy(next(o for o in gallery['objects'] if o['name'] == 'floor_plank_1'))
beam.update({'name': 'Gallery beam', 'role': 'timber.beam'})
beam['construction'].update({'span_max_m': 2.8, 'max_span_m': 2.5})      # a gallery beam on posts 3.0 m apart has 2.8 m free (the newcomer judge's measure)
gallery['objects'].append(beam)
span_text = after(gallery, 'place: construction')
span_fix = ' '.join(f['fix'] for f in judge(gallery, skip_freshness=True) if f['check'] == 'place: construction' and f['verdict'] == 'fail')
check.true('the case that must fail: a beam with 2.8 m free FAILS place: construction and names its role\'s own limit (2.5 m), and the fix names every role\'s limit and the free_span fact',
           'Gallery beam' in span_text and 'allows 2.5 m' in span_text and '1.38 m' in span_fix and '2.5 m' in span_fix and 'free_span' in span_fix, span_text[:200])
fact = {'id': 'gallery_bay_span', 'applies_to_role': '^timber\\.beam$', 'applies_to_name': 'gallery', 'dimension': 'free_span', 'max': 3.0, 'unit': 'metres', 'kind': 'judged',
        'source': 'the place plan: the gallery bays are 3 m between posts', 'confidence': 'good'}
allowed = judge(gallery, skip_freshness=True, facts=[fact])
check.true('...a sourced "free_span" fact in the place\'s own facts file (3.0 m for the gallery beam) lets it pass, and the pass line names the fact',
           'fail' not in verdicts(allowed, 'place: construction') and 'gallery_bay_span' in text_of(allowed, 'place: construction', 'pass'), str(verdicts(allowed, 'place: construction')))
unsourced = dict(fact, source='')
check.true('...a free_span fact with no source does not count (the span still FAILS)', 'fail' in verdicts(judge(gallery, skip_freshness=True, facts=[unsourced]), 'place: construction'))
beam['construction']['span_max_m'] = 3.4
check.true('...and a span longer than the fact allows still FAILS, naming the fact\'s figure',
           'gallery_bay_span 3 m' in text_of(judge(gallery, skip_freshness=True, facts=[fact]), 'place: construction'), text_of(judge(gallery, skip_freshness=True, facts=[fact]), 'place: construction')[:200])
check.finish()
