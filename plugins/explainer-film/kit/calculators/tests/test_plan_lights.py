"""What this does: tests calculators/plan_lights.py (the light planner) against the project's recorded light rounds: the
notice corner's 26 hand rounds (logs 31-32: fire 70 W, lantern 60 -> 1 W, the notice glow's 1.4 m reach, the lamps log 31
removed and dimmed, which lights skip what), the Works' gate lamp (round 4 on the pier's face, round 5 on its inner face,
linked), the dark gate (round 5 could not make it brightest), the render log's shadow fault (log 31's black wedge),
exposure per view (W1 1.6) and, as a hold-out, checkout C1 (built after the rules: its check 10 found the bill burnt out).
Each check says where its number is recorded and whether it proves something or only repeats a sum.
Run: python3 tests/test_plan_lights.py (or tests/run_all.py). Exits 1 if a check fails.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
OURS = os.path.join(FIXTURES, 'effects-camera-light')
NOTICE = os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')
WORKS = os.path.join(FIXTURES, 'works', 'works-place-facts.json')
CHECKOUT = os.path.join(FIXTURES, 'checkout-c1', 'checkout-c1-place-facts.json')
WORKS_ASSETS = '/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/works'
NOTICE_BLEND = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/notice-corner.blend'

import plan_lights as lights  # noqa: E402
from settings import load_settings  # noqa: E402

settings = load_settings()
check = Checker('plan_lights: watts, reach, cone, links, surfaces, lamps, dark subject, render log, exposure')
temporary = tempfile.mkdtemp(prefix='plan-lights-')


def run(*args):
    found = subprocess.run([sys.executable, '-B', os.path.join(CALCULATORS, 'plan_lights.py'), *args, '--json'], capture_output=True, text=True)
    try:
        return found.returncode, json.loads(found.stdout)
    except json.JSONDecodeError:
        return found.returncode, {'stdout': found.stdout, 'stderr': found.stderr}


def changed_facts(path, change, name):
    facts = json.load(open(path))
    change(facts)
    out = os.path.join(temporary, name)
    json.dump(facts, open(out, 'w'))
    return out


def by_name(result):
    return {row['light']: row for row in result['lights']}


# ------------------------------------------------------------------------------------------------ the notice corner
code, notice = run('plan', '--place-facts', NOTICE, '--view', 'end', '--beam-hits', f'notice glow={os.path.join(OURS, "beam-notice-glow.json")}',
                   '--lamps', os.path.join(OURS, 'street-lamps.json'))
rows = by_name(notice)
check.equal('roles: fire light, notice glow, lantern light, corner lamp light', [rows[n]['role'] for n in ('fire light', 'notice glow', 'lantern light', 'corner lamp light')],
            ['fire', 'accent', 'lamp', 'lamp'], recorded='notice-corner-place-facts.json lights; assemble_notice_corner.py', proves='the roles come from the place facts alone')
check.equal('only the fire casts shadows (the notice glow, lantern and corner lamp none)', notice['shadow_casters'], ['fire light'],
            recorded='assemble_notice_corner.py (notice glow "no shadow"); story log 32 (the fire\'s long shadows from the pail and chair); round 3 rule')
check.true('the fire\'s light should skip the drum and the chair', set(rows['fire light'].get('housing', [])) == {'drum', 'chair'},
           details=str(rows['fire light'].get('housing')), recorded='story log 32 ("The fire\'s light skips the drum and the chair"; lesson 120)',
           proves='the container rule (props within 0.6 m of a fire, an invented distance) finds the links log 32 chose by eye')
check.close('the fire\'s starting watts by the inverse square from the notice glow', rows['fire light']['start_watts'], 70, 3,
            recorded='assemble_notice_corner.py FIRE_WATTS 70 (film-settings.json light.starting_points.notice_corner)', proves='not independent: the notice '
            'glow\'s 200 W was tuned in the same rounds, so this shows the inverse square keeps the ratio the hand rounds settled on')
lantern_start = rows['lantern light']['start_watts']
check.within('the lantern\'s starting watts (its nearest surface 0.11 m away)', lantern_start, 1.0, 5.0,
             recorded='assemble_notice_corner.py LANTERN_WATTS history: 60, 15, 5, 3, 2, 1 W', proves='the start lands inside the range the hand rounds walked '
             'through, about 28 times below the first try; the last steps (to 1 W) still need the shot checker')
check.equal('the lantern light skips its own lantern', rows['lantern light'].get('housing'), ['lantern'], recorded='notice-corner-place-facts.json lights '
            '(skips: lantern); lesson 120 ("the lantern lit its own brass frame")')
reach = rows['notice glow']['reach']
check.close('notice glow reach from Blender ray hits (farthest lit part of the notice + 0.2 m)', reach['reach_metres'], 1.4, 0.05,
            recorded='notice-corner-shot.json notice_glow.reach 1.4 (log 31)', proves='the margin 0.2 m was read off this light; the check shows the measured '
            'geometry gives the 1.2 m the design assumed')
beam = json.load(open(os.path.join(OURS, 'beam-notice-glow.json')))
walls = [h['distance'] for r in beam['rays'] for i, h in enumerate(r['hits']) if i == 0 and (h['object'] or '').startswith('right_row_a_cottage_06_walls')]
axis_wall = next(h['distance'] for h in beam['rays'][0]['hits'] if (h['object'] or '').startswith('right_row_a_cottage_06'))
check.true('the reach stops short of the house wall behind the board', reach['reach_metres'] < min(walls), details=f'first wall face in the cone {min(walls):.2f} m, '
           f'along the beam\'s axis {axis_wall:.2f} m', recorded='story log 31 ("the beam went through the board onto the wall until a reach of 1.4 m was '
           'set"); design: "wall at 2.1 m"', proves='the ray cast finds the wall the hand rounds hit (2.09 m along the axis, 1.52 m at the cone\'s edge)')
unlinked = changed_facts(NOTICE, lambda f: [l.pop('reaches_only', None) for l in f['lights'] if l['name'] == 'notice glow'], 'notice-unlinked.json')
code, plain = run('plan', '--place-facts', unlinked, '--view', 'end', '--beam-hits', f'notice glow={os.path.join(OURS, "beam-notice-glow.json")}')
check.true('without its link the notice glow would also light the pavement behind the drum (1.34 m): flagged', any('pavement' in p for p in
           by_name(plain)['notice glow']['problems']), details='; '.join(by_name(plain)['notice glow']['problems']),
           recorded='lesson 120 and log 32 (the link was added after the reach)', proves='the reach alone cannot keep a shadowless light off everything; the link is needed')
cones = rows['notice glow']['cones']
check.true('the hand cone (50 degrees) lies between the cone aimed at the bottom edge and the even cone', cones['from_below_cone_degrees'] < 50 < cones['even_cone_degrees'],
           details=f'from below {cones["from_below_cone_degrees"]:.0f}, even {cones["even_cone_degrees"]:.0f}', recorded='assemble_notice_corner.py notice glow cone 50 '
           '(after 20 degrees warmed only a patch, log 31)', proves='only brackets the hand value: neither formula gives 50; a person still picks within the range')
check.true('aimed at the bottom edge, the notice\'s top stays outside the cone (warm bottom, cool top)', cones['from_below_leaves_top_unlit'],
           recorded='rule 6 (the liked notice warms by 0.17 from top to bottom, log 30)')
lamps = {r['lamp']: r for r in notice['lamps']}
flagged = sorted(n for n, r in lamps.items() if r['problems'])
check.true('the street lamps at y 39 and 64.5 land on the board or where the lines meet: flagged', 'gas_lamp_2_post' in flagged and 'gas_lamp_4_post' in flagged,
           details=str(flagged), recorded='assemble_notice_corner.py lines 96-100 (both removed: "just above the board\'s top and its left post ... the far one '
           'right where the lines meet", log 31)', proves='projecting the street builder\'s lamps finds the two log 31 removed by eye')
check.true('the lamp behind the camera at 260 W floods the near ground: flagged; the kept lamps at y 25 and 53 are not',
           'gas_lamp_0_light' in flagged and not any(n.startswith('gas_lamp_1') or n.startswith('gas_lamp_3') for n in flagged),
           details=f'{lamps["gas_lamp_0_light"].get("near_ground_light", 0):.3f} W/m2 on the near ground', recorded='assemble_notice_corner.py lines 93-95 '
           '(turned down to 70 W); street.blend lamps 1 and 3 kept', proves='the near-ground limit (0.025, invented between the two states) separates them')
dimmed = os.path.join(temporary, 'lamps-dimmed.json')
data = json.load(open(os.path.join(OURS, 'street-lamps.json')))
data['objects']['gas_lamp_0_light']['watts'] = 70
json.dump(data, open(dimmed, 'w'))
code, after = run('plan', '--place-facts', NOTICE, '--view', 'end', '--lamps', dimmed)
check.true('turned down to 70 W (the hand fix), the lamp behind the camera passes', not {r['lamp']: r for r in after['lamps']}['gas_lamp_0_light']['problems'],
           recorded='assemble_notice_corner.py line 95 (energy = 70)', proves='repeats where the limit was placed')
check.close('the notice corner\'s subject gets about 1.4 times its key in all (kept, no burnt colour)', notice['subject_light_over_key'], 1.4, 0.1,
            recorded='notice corner final check (no burnt-out colour; experiments/32 report)', proves='sets the scale for the hold-out below')
check.equal('EEVEE settings for a 1536-wide plate', [notice['eevee']['shadow_pool_size'], round(notice['eevee']['shadow_resolution_scale'], 3)], ['1024', 0.703],
            recorded='set_dressing.py render() (lesson 110); verify_test_cases-output.txt "0.703"', proves='only repeats min(1, 1080 / 1536)')

# ------------------------------------------------------------------------------------------------ the Works: the gate lamp and the dark gate
surfaces = os.path.join(OURS, 'works-w1-gate-surfaces.json')


def move_lamp(facts, at, watts, keep_link):
    for light in facts['lights']:
        if light['name'] == 'no-1-gate-lamp-light':
            if at:
                light['at'], light['watts'] = at, watts
            if not keep_link:
                light.pop('reaches_only', None)
    for emitter in facts['emitters']:
        if emitter['name'] == 'no-1 gate lamp' and at:
            emitter['at'] = at


round4 = changed_facts(WORKS, lambda f: move_lamp(f, [-5.45, 21.67, 3.62], 14.0, False), 'works-round4-lamp.json')
code, w1_round4 = run('plan', '--place-facts', round4, '--view', 'w1', '--state', 'w1-quiet', '--surfaces', surfaces)
lamp4 = by_name(w1_round4)['no-1-gate-lamp-light']
check.true('round 4: the gate lamp on the pier\'s lane face lights the pier far more than the gate: flagged', any('outer pier (lane face)' in p for p in lamp4['problems']),
           details='; '.join(lamp4['problems']), recorded='round4-result.json critique finding 5 ("the gate lamp turns No. 1\'s left pier into a big bright orange slab"); '
           'its place (-5.45, 21.67, 3.62) and 14 W from the same finding and assemble_works.py ("half of 14 W")', proves='the face-irradiance test catches the fault a critic saw')
code, w1_round5 = run('plan', '--place-facts', WORKS, '--view', 'w1', '--state', 'w1-quiet', '--surfaces', surfaces)
check.true('round 5 as built (inner face, 7 W, linked to the gate, board and men): not flagged', not by_name(w1_round5)['no-1-gate-lamp-light']['problems'],
           recorded='assemble_works.py gate_furniture (round 5); round5-set/checks/w1-quiet-d/light/report.md (lit from below 0.25)')
unlinked5 = changed_facts(WORKS, lambda f: move_lamp(f, None, None, False), 'works-round5-unlinked.json')
code, w1_unlinked = run('plan', '--place-facts', unlinked5, '--view', 'w1', '--state', 'w1-quiet', '--surfaces', surfaces)
check.true('round 5\'s place without its link would light the pier\'s inner face about as much as the gate: flagged', any('inner face' in p for p in
           by_name(w1_unlinked)['no-1-gate-lamp-light']['problems']), recorded='assemble_works.py ("reaches only the gate\'s leaves ... (light linking)")',
           proves='the move to the inner face needs the link as well')
check.true('W1\'s gate is a dark subject: no inverse-square starts, a plan to light behind it', w1_round5['dark_subject'] and 'dark_subject_plan' in w1_round5
           and 'no-1-yard-dusk' in w1_round5['dark_subject_plan']['lights_behind_subject'], recorded='works-place-facts.json (subject dark); round 5 final W1 '
           'check: the gate 0.85 times the mean after the yard light went 260 -> 900 W', proves='the planner does not chase a brightness the gate cannot reach')
check.true('W1 shadow casters: the fire, the lit doorways and the sky only', {r['light'] for r in w1_round5['lights'] if r['casts_shadow']} ==
           {'brazier_light', 'dusk_skylight', 'afterglow', 'no-2-doorway-spill', 'no-2-gateway-spill', 'no-2-yard-spill', 'no-2-gateway-beam', 'no-2-room-light'},
           recorded='assemble_works.py lines 984-1047; round 3 ("Shadows only from the fire, the yards\' lit doorways and the sky")')
for view, expected in (('w1', 1.24), ('w2', 2.19)):
    code, measured = run('contrast', '--place-facts', WORKS, '--view', view, '--picture', os.path.join(OURS, f'{view}-quiet-subject-picture-crop.jpg'),
                         '--subject-mask', os.path.join(OURS, f'{view}-quiet-subject-mask-crop.png'), '--frame-height', '1920')
    check.close(f'{view} (round 5 final): the gate\'s silhouette contrast', measured['contrast'], expected, 0.02,
                recorded=f'measured here on scratchpad redesign/round5-set/checks/final-{view}-quiet/picture.png with its shot_facts solo mask (cropped to the '
                'fixtures; the full frame gives the same to 0.002), by the people test\'s own method (people-paint/check-figures/scripts/films.py)',
                proves='a hold-out for the dark-subject number: 2.2 was measured on painted figures (people test), never on a gate')
check.note('round 5\'s W1 gate measures 1.24 against the dark-subject 2.2 (well short: light behind it, or judge 2.2 unsuited to an iron gate); W2\'s '
           'dark gateway measures 2.19, just at it. A person must judge (the 2.2 was measured on painted figures, not gates).')

# ------------------------------------------------------------------------------------------------ hold-out: checkout C1
code, c1 = run('plan', '--place-facts', CHECKOUT, '--view', 'c1')
check.true('checkout C1 (hold-out): the bill gets far more than 3 times its key, mostly from the warm bounce below it: flagged before any render',
           c1['subject_light_over_key'] > 3 and any('bill-warm-bounce' in p and 'burn' in p for p in c1['problems']),
           details=f'{c1["subject_light_over_key"]:.0f} times', recorded='checkout C1 check 10 ("Colour at its limit ... bill (23% of it)"; '
           'tests/fixtures/checkout-c1/checkout-c1-check-results.json)', proves='the planner predicts, from distances alone, the burnt bill the render showed, '
           'on a place the rules were not built from (the 3-times limit is invented; the notice corner sits at 1.4 and C1 at about 60)')
c1rows = by_name(c1)
check.true('C1\'s key spot (20 degrees) covers only part of the bill: the planner\'s cones are wider', c1rows['bill-cool']['cones']['even_cone_degrees'] > 20,
           details=f'even {c1rows["bill-cool"]["cones"]["even_cone_degrees"]:.0f}, from below {c1rows["bill-cool"]["cones"]["from_below_cone_degrees"]:.0f} degrees',
           recorded='checkout-c1-place-facts.json (bill-cool cone 20); check 10 ("The bottom of bill is -0.29 warmer than its top")',
           proves='a finding, not a proof: the narrow key aimed above the bill\'s middle may explain the cool top and warm bottom')

# ------------------------------------------------------------------------------------------------ render logs and exposure
code, logs = run('render-log', os.path.join(OURS, 'render-log-notice-corner-plate-log31.log'), os.path.join(OURS, 'render-log-works-plates-round5-excerpt.log'))
check.true('log 31\'s notice corner plate is refused for "Shadow buffer full"; round 5\'s Works plates pass', code == 1 and logs['refused'] ==
           [os.path.join(OURS, 'render-log-notice-corner-plate-log31.log')], recorded='scratchpad plan3/corner/plate.log (43 fault lines; lesson 110: the black '
           'wedge three critics blamed on the lighting); scratchpad redesign/round5-set/plates/plates.log', proves='the log check refuses the picture that misled log 31')
times = {r['picture']: r['minutes'] for r in logs['logs'][1]['drawing_minutes']}
check.close('round 5 W1 plate drawing time (minutes, read from the log)', times['works-w1-plate.png'], 5.76, 0.05,
            recorded='plates.log "Saved" times 06:05.827 and 11:51.229; round 3: "about 6 minutes" with three shadow lights', proves='plate times are read, not predicted (skeptic)')
code, exposure = run('exposure', '--mean', 'w1=35', '--mean', 'w2=49', '--mean', 'w3=59')
check.close('W1 exposure from the plates\' mean brightness (35 against 49 and 59)', exposure['views']['w1']['exposure'], 1.6, 0.1,
            recorded='page-3.js LOOK_W1 1.6 (round 3: W1 35, W2 49, W3 59 levels)', proves='the other views\' mean gives the hand value within 0.06')
check.equal('W2 and W3 stay at 1.0', [exposure['views']['w2']['exposure'], exposure['views']['w3']['exposure']], [1.0, 1.0], recorded='page-3.js LOOK (1.0)')
plates = {v: os.path.join(WORKS_ASSETS, f'works-{v}-plate.jpg') for v in ('w1', 'w2', 'w3')}
if all(os.path.exists(p) for p in plates.values()):
    code, now = run('exposure', *[a for v, p in plates.items() for a in ('--picture', f'{v}={p}')])
    check.within('round 5 plates: W1 exposure, measured on the pictures', now['views']['w1']['exposure'], 1.4, 1.8,
                 recorded='film-kit assets works-w1/w2/w3-plate.jpg (round 5); the hand value 1.6 was set on round 3\'s plates', proves='a hold-out on newer plates: '
                 'still about 1.6 (measure again on the paintings, as the skeptic asked)')
else:
    check.note('the round 5 plates are not here; the picture exposure check was skipped')

# ------------------------------------------------------------------------------------------------ the Blender ray cast still runs
blender = os.environ.get('BLENDER') or '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
if os.path.exists(blender) and os.path.exists(NOTICE_BLEND):
    out = os.path.join(temporary, 'beam.json')
    subprocess.run([blender, '-b', NOTICE_BLEND, '--python', os.path.join(KIT, 'paper-film', 'blender', 'set_measurements.py'), '--', 'beam', '--check',
                    os.path.join(FIXTURES, 'notice-corner', 'notice-corner-shot-check.json'), '--at', '2.78,22.0,2.6301', '--aim', '3.45,22.75,2.3251',
                    '--cone', '50', '--far', '4', '--name', 'notice glow', '--out', out], capture_output=True, text=True, timeout=300)
    again = lights.reach_from_beam(json.load(open(out)), {'notice'}, {'drum', 'board', 'notice'}, False, settings)
    check.close('set_measurements.py beam in notice-corner.blend gives the same reach again', again['reach_metres'], reach['reach_metres'], 1e-3,
                recorded='tests/fixtures/effects-camera-light/beam-notice-glow.json', proves='the Blender companion still runs and agrees with its fixture')
else:
    check.note('Blender or notice-corner.blend is not here: the live ray cast was skipped')

shutil.rmtree(temporary, ignore_errors=True)
check.finish()
