"""What this does: tests calculators/plan_effects.py (the effects planner) against the project's recorded cases: the
Works' chimney plumes of rounds 4 and 5 (log 34), the round 4 critic's trace, the skeptic's top-edge finding, the
choice of wind, the smoke colours against the W3 plate, the notice corner's dropped chimney smokes and contact shadows
(log 32), the "busy" window change (rounds 4 and 5), the glow pulse and flames, and the paper-page lint. Each check
says where its number is recorded and whether it proves something or only repeats a sum.
Run: python3 tests/test_plan_effects.py (or tests/run_all.py). Exits 1 if a check fails.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
OURS = os.path.join(FIXTURES, 'effects-camera-light')
WORKS_FACTS = os.path.join(FIXTURES, 'works', 'works-place-facts.json')
NOTICE_FACTS = os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')
WORKS_EFFECTS = os.path.join(KIT, 'paper-film', 'scenes', 'inflation-chapter-2-newcomers', 'works-effects.js')
W3_PLATE = '/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/works/works-w3-plate.jpg'
NOTICE_BLEND = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/notice-corner.blend'
LOWER_CARD = [65 / 1080, 314 / 1920, 972 / 1080, 454 / 1920]   # page-5.js RULE_CARDS.lower [TEXT_LEFT, 314, TEXT_RIGHT - TEXT_LEFT, 140]
UPPER_CARD = [65 / 1080, 158 / 1920, 972 / 1080, 298 / 1920]

import plan_effects as effects  # noqa: E402
import frame_geometry as geometry  # noqa: E402
from settings import load_settings  # noqa: E402

settings = load_settings()
check = Checker('plan_effects: wind, plumes, colour, contact shadows, window change, fire, lint')
facts = json.load(open(WORKS_FACTS))
step = settings.value('effects_planner.trace_step_seconds')
emitters = {e['name']: e for e in facts['emitters']}
w3 = geometry.camera_from_place_facts(facts, settings, 'w3', 'composed', 'film')


def run(*args):
    """The command line, as a person would run it; returns (exit code, JSON result)."""
    found = subprocess.run([sys.executable, '-B', os.path.join(CALCULATORS, 'plan_effects.py'), *args, '--json'], capture_output=True, text=True)
    try:
        return found.returncode, json.loads(found.stdout)
    except json.JSONDecodeError:
        return found.returncode, {'stdout': found.stdout, 'stderr': found.stderr}


# ------------------------------------------------------------------------------------------------ the model follows the page code
code = open(WORKS_EFFECTS).read()
place = code[code.index('place(puffs, t, settings, bornFrom, bornUntil)'):code.index('// ------', code.index('place(puffs, t, settings, bornFrom, bornUntil)'))]
for text, constant in (('Math.pow(k, 0.75)', effects.RISE_POWER), ('Math.pow(k, 1.25)', effects.DRIFT_POWER), ('this.top.y + 0.3', effects.MOUTH_LIFT),
                       ('(life - mouthFor), 0.8)', effects.WIDEN_POWER), ('Math.min(1, age / 0.2)', effects.FADE_IN_SECONDS),
                       ('settings.fade ?? 1.3', effects.DEFAULT_FADE)):
    check.true(f'ChimneySmoke still uses {text}', text in place, recorded='kit/paper-film/scenes/inflation-chapter-2-newcomers/works-effects.js '
               'ChimneySmoke.place()', proves=f'the planner\'s copy of this constant ({constant}) has not drifted from the page code')
smoke_code = open(os.path.join(KIT, 'paper-film', 'scenes', 'effects.js')).read()
for text in ('scale * 1.7 * k', '0.35 + 1.1 * k', '0.5 * Math.min(1, age / 0.25) * (1 - k)', 'size: 0.8 + random() * 0.5'):
    check.true(f'effects.js Smoke still uses {text}', text in smoke_code, recorded='kit/paper-film/scenes/effects.js Smoke.set()',
               proves='the fire-smoke model has not drifted from the page code')

# ------------------------------------------------------------------------------------------------ settings read three ways
ROUND5 = os.path.join(OURS, 'round5-smoke-final.json')
from_record = effects.read_smoke(settings, ROUND5)
from_page = effects.read_smoke(settings, WORKS_EFFECTS)
from_table = effects.read_smoke(settings)
FIELDS = ('life', 'rise', 'drift', 'opacity', 'fade', 'mouth_seconds', 'mouth_size')
check.true('film-settings.json effects.smoke_kinds hold round 5\'s heavy smoke', all(abs(from_table['kinds']['heavy'][f] - from_record['kinds']['heavy'][f]) < 1e-9
                                                                                    for f in FIELDS),
           recorded='kit/film-settings.json effects.smoke_kinds; scratchpad redesign/round5-pages/tools/smoke-final.json',
           proves='the shared table holds the round 5 numbers (working and thin lack mouth seconds there; the planner fills in '
                  'effects_planner.mouth_seconds_default 2)')
changed = sorted({f'{k} {f} {from_record["kinds"][k][f]:g} -> {from_page["kinds"][k][f]:g}' for k in from_record['kinds'] if k in from_page['kinds']
                  for f in FIELDS if abs(from_page['kinds'][k][f] - from_record['kinds'][k][f]) > 1e-9})
if changed or max(abs(a - b) for a, b in zip(from_page['wind'], from_record['wind'])) > 1e-12:
    check.note(f'the plugin kit\'s works-effects.js no longer holds round 5\'s smoke ({"; ".join(changed) or "the wind"}): the recorded cases below use '
               'round 5\'s own settings (fixture); run plan_effects.py wind on the new page to judge it')
else:
    check.note('the plugin kit\'s works-effects.js still holds round 5\'s smoke and wind (read from its SMOKE and WIND)')

# ------------------------------------------------------------------------------------------------ round 4 fails, round 5 passes
kinds5 = from_record['kinds']
round4_wind = geometry.normalise([0.3, -0.05, -0.95])
round5_wind = from_record['wind']
top_a = emitters['no-2-chimney-a']['at']
trace4 = effects.trace_plume(w3, top_a, kinds5['heavy'], round4_wind, step)
trace5 = effects.trace_plume(w3, top_a, kinds5['heavy'], round5_wind, step)
others = [('no-1-chimney', geometry.project_point(w3, emitters['no-1-chimney']['at'])['across'], 0.0)]
first_across = geometry.project_point(w3, top_a)['across']
judged4 = effects.judge_plume(trace4, settings, others=others, emitter_across=first_across)
judged5 = effects.judge_plume(trace5, settings, others=others, emitter_across=first_across)
check.close('round 4 wind: travel while seen in W3 (No. 2 chimney a, heavy)', judged4['travel'], 0.044, 0.0015,
            recorded='scratchpad plugin-calculators/verify_test_cases-output.txt ("travel ... 0.044"); skeptic (log 35)',
            proves='the trace repeats the design\'s own sum (same model); the verdict below is the real check')
check.true('round 4 wind is refused (travels under 0.15 of the width)', any('travels only' in p for p in judged4['problems']),
           recorded='round4-result.json critique finding 4: the puffs piled up as rings and a hook',
           proves='the planner refuses the wind a critic rejected by eye')
check.close('round 5 wind: travel while seen', judged5['travel'], 0.188, 0.0015, recorded='verify_test_cases-output.txt ("0.188")',
            proves='repeats the design\'s sum')
check.close('round 5 wind: last seen at', judged5['last_visible'][0], 0.432, 0.002, recorded='verify_test_cases-output.txt; works-effects.js '
            '("fading out by about 0.45 across")', proves='the plume fades where the round 5 helper saw it fade')
gap = judged5['other_chimneys'][0]['gap']
check.close('round 5 wind: fades short of No. 1\'s chimney (0.375 across) by', gap, 0.057, 0.002, recorded='skeptic (log 35): "0.057 clear of No. 1\'s chimney at 0.375"',
            proves='the other-chimney test measures the clearance the round 5 helper relied on')
check.true('round 5 wind passes travel and the other chimney', not judged5['problems'], details='; '.join(judged5['problems']) or 'no problems',
           recorded='works-effects.js WIND comment (round 5 kept this wind)', proves='the planner accepts the wind round 5 kept (without word cards)')
check.within('round 5 middles from', judged5['centre_down_range'][0], 0.237, 0.239, recorded='verify_test_cases-output.txt ("centre down 0.238-0.265")')
check.within('round 5 middles to', judged5['centre_down_range'][1], 0.264, 0.266, recorded='verify_test_cases-output.txt')

# the skeptic's top-edge finding: centres pass under the lower card, top edges do not
judged5_cards = effects.judge_plume(trace5, settings, cards=[('lower', LOWER_CARD)], others=others, emitter_across=first_across)
check.close('round 5: puff top edges (strength 0.2 or more) reach', judged5_cards['top_edge_min'], 0.221, 0.0015,
            recorded='scratchpad redesign/round5-pages/tools/smoke-final-trace.txt (heavy no-2-chimney-a-top: top0.221 at 3 s)',
            proves='the edge test reads the same tops the round 5 trace printed')
check.true('the lower card (ends 0.2365 down) covers the plume\'s top: flagged by edges, not by middles',
           any('top edges reach' in p for p in judged5_cards['problems']) and not any('middles are inside' in p for p in judged5_cards['problems']),
           details='; '.join(judged5_cards['problems']), recorded='skeptic (log 35): "It tests puff centres, not puff edges ... tops at 0.209-0.228 down, '
           'above the lower card\'s 0.236 bottom"; page-5.js RULE_CARDS.lower',
           proves='the planner follows the skeptic: the round 5 plume tucks about 0.015 of the height under the card (a person must judge it)')

# the round 4 critic's own trace (round 4 settings and wind)
smoke4 = effects.read_smoke(settings, os.path.join(OURS, 'round4-smoke.json'))
heavy4 = smoke4['kinds']['heavy']
start = geometry.project_point(w3, effects.puff_centre_blender(top_a, smoke4['wind'], effects.puff_at(heavy4, 0.0)))
end = geometry.project_point(w3, effects.puff_centre_blender(top_a, smoke4['wind'], effects.puff_at(heavy4, heavy4['life'])))
check.close('round 4 critic: a puff starts across', start['across'], 0.625, 0.002, recorded='round4-result.json critique finding 4 ("from 0.625 across, 0.237 down")',
            proves='the planner\'s sums match the critic\'s hand trace (made separately in round 4)')
check.close('round 4 critic: starts down', start['down'], 0.237, 0.002, recorded='round4-result.json finding 4')
check.close('round 4 critic: ends across', end['across'], 0.748, 0.002, recorded='round4-result.json finding 4 ("to 0.748, 0.309")')
check.close('round 4 critic: ends down', end['down'], 0.309, 0.002, recorded='round4-result.json finding 4')

# ------------------------------------------------------------------------------------------------ choosing the wind
code_run, chosen = run('wind', '--place-facts', WORKS_FACTS, '--smoke', ROUND5, '--smoking', 'no-1-chimney=working', '--smoking',
                       'no-2-chimney-a=heavy', '--smoking', 'no-2-chimney-b=heavy', '--card', 'w3:upper=' + ','.join(map(str, UPPER_CARD)),
                       '--card', 'w3:lower=' + ','.join(map(str, LOWER_CARD)))
wind = chosen.get('chosen_wind_three_axes', [0, 0, 0])
check.true('choosing on its own, the planner picks the round 5 wind (-0.85, -0.12, -0.5) normalised',
           max(abs(a - b) for a, b in zip(wind, geometry.normalise([-0.85, -0.12, -0.5]))) < 1e-6,
           details=f'chosen {effects.fmt_vector(wind)}; tried ' + '; '.join(f'{t["label"]}: {len(t["problems"])} problem(s), shortest trail '
                                                                            f'{t["smallest_travel"]:.3f}' for t in chosen.get('tried', [])),
           recorded='works-effects.js WIND (round 5)', proves='only the sign is the planner\'s own choice: the across, away and down parts come from '
           'round 5\'s wind (effects_planner.wind_mix), and the sign is won on the longer shortest trail (0.161 against 0.158), both signs having '
           'the same two card problems')
check.true('both signs are refused only for the W3 word cards', all(all('card' in p for p in t['problems']) for t in chosen.get('tried', [])),
           recorded='works-effects.js: No. 1\'s plume in W3 comes out under the lower card on purpose ("hides the chimney\'s mouth")',
           proves='the remaining problems are the deliberate card overlap and the skeptic\'s top edge, not the wind')
check.true('W4 drops all three chimney smokes (W4 looks the other way)', sorted(c for v, c in chosen['tried'][0]['dropped'] if v == 'w4') ==
           ['no-1-chimney', 'no-2-chimney-a', 'no-2-chimney-b'], recorded='place facts: W4 is turned 180 degrees (works-camera-w4.json)',
           proves='an emitter outside the frame for the whole shot is dropped (log 32 rule)')
check.equal('the command exits 1 while a problem stands', code_run, 1)

# ------------------------------------------------------------------------------------------------ the notice corner's dropped chimney smokes
notice = json.load(open(NOTICE_FACTS))
cottage = {'life': 4.2, 'scale': 0.8, 'wind': 0.8, 'above_coals_metres': 0.4}   # notice-corner.js at 27086ad (log 31)
decisions, detail = [], []
for top in ([-7.65, 26.5, 12.998], [-7.65, 39.5, 13.908]):
    entered = False
    for spot in ('plate', 'composed'):
        camera = geometry.camera_from_place_facts(notice, settings, 'end', spot, 'film')
        samples = effects.trace_fire_smoke(camera, top, cottage, step)
        entered = entered or any(s['right'] > 0 and s['left'] < 1 and s['bottom'] > 0 and s['top'] < 1 for s in samples)
        landed = geometry.project_point(camera, top)
    held = [landed['across'], landed['down']] if landed['in_front'] else None
    decisions.append(effects.should_drop(entered, held))
    detail.append(f'top at {held[0]:.3f} across where the shot holds, plume {"enters" if entered else "never enters"} the frame')
check.true('both of the notice corner\'s cottage chimney smokes are dropped', all(decisions), details='; '.join(detail),
           recorded='notes story log 32 ("the two chimney smokes dropped (both chimneys are out of the frame)"); their tops from notice-corner.js '
           'at commit 27086ad lines 145-147', proves='the drop rule makes the call log 32 made by eye. The far one\'s top sits 0.009 inside the left '
           'edge at the slide\'s start and its smoke drifts 0.03 to 0.08 into the frame, so a plume-only rule would have kept it')

# ------------------------------------------------------------------------------------------------ colour against the W3 plate
if os.path.exists(W3_PLATE):
    code5, colour5 = run('colour', '--place-facts', WORKS_FACTS, '--view', 'w3', '--picture', W3_PLATE, '--smoke', ROUND5,
                         '--smoking', 'no-1-chimney=working', '--smoking', 'no-2-chimney-a=heavy')
    code4, colour4 = run('colour', '--place-facts', WORKS_FACTS, '--view', 'w3', '--picture', W3_PLATE, '--smoke', os.path.join(OURS, 'round4-smoke.json'),
                         '--wind=0.3,-0.05,-0.95', '--smoking', 'no-1-chimney=working', '--smoking', 'no-2-chimney-a=heavy')
    by5 = {p['chimney']: p for p in colour5['plumes']}
    by4 = {p['chimney']: p for p in colour4['plumes']}
    check.within('round 5 heavy smoke: levels lighter than the sky behind it', by5['no-2-chimney-a']['lighter_than_sky_levels'], 5, 15,
                 recorded='measured here on film-kit works-w3-plate.jpg (round 5 plate); round 5 chose a brownish grey of about 90 to 100 (works-effects.js)')
    check.true('round 4 pale smoke is refused as a glow (about 50 levels lighter)', any('reads as a glow' in p for p in by4['no-2-chimney-a']['problems']),
               details=f'{by4["no-2-chimney-a"]["lighter_than_sky_levels"]:+.0f} levels', recorded='round4-result.json finding 4 ("pale grey on the dark sky reads as glow")',
               proves='only that the measure orders the two the way the critic did: the 30-level limit was placed between these two cases')
    check.true('round 5 smoke passes lightness and colour difference', not [p for p in by5['no-2-chimney-a']['problems'] if 'mouth' not in p],
               details=f'colour difference {by5["no-2-chimney-a"]["colour_difference"]:.0f}', recorded='round 5 still at 117.1 s shows the plume clearly '
               '(scratchpad redesign/round5-pages/smoke-4)', proves='repeats where the limits came from (both invented)')
    check.true('No. 1\'s working mouth (1.7 m) is narrower than its 1.84 m top: flagged', any('narrower' in p for p in by5['no-1-chimney']['problems']),
               recorded='place facts: no-1 chimney radius 0.92 (round 2 factories); works-effects.js SMOKE.working mouth 1.7',
               proves='a finding for a person: the design\'s mouth rule (invented) fails round 5\'s working smoke by 8%')
else:
    check.note(f'colour checks skipped: the W3 plate is not here ({W3_PLATE})')

# ------------------------------------------------------------------------------------------------ contact shadows
code_run, shadows = run('contact-shadows', '--place-facts', NOTICE_FACTS, '--props', 'drum,chair,pail', '--footprints',
                        os.path.join(OURS, 'footprints-notice-corner.json'), '--slide-start', '2.0')
sides = {s['prop']: s['shadow_side'] for s in shadows['shadows']}
hand = {'drum': 1.0, 'chair': 0.75, 'pail': 0.55}   # notice-corner.js lines 129-135
check.close('drum: 1.2 x its measured base diagonal', sides['drum'], 1.0, 0.15, recorded='notice-corner.js line 131 (drum 1.0 x 1.0); base measured '
            'in notice-corner.blend by set_measurements.py footprints (0.584 x 0.584 m)', proves='the rule reproduces the hand size from the model')
check.close('pail: 1.2 x its measured base diagonal', sides['pail'], 0.55, 0.15, recorded='notice-corner.js line 131 (pail 0.55); base 0.267 x 0.269 m')
check.close('chair: 1.2 x its measured base diagonal (the legs\' spread)', sides['chair'], 0.97, 0.01, recorded='base 0.569 x 0.577 m (set_measurements.py)',
            proves='repeats the sum')
check.note(f'the chair comes out {sides["chair"]:.2f} m against the hand\'s 0.75: the rule over-sizes an open-legged thing (the design\'s "all within '
           f'0.15 m" used footprints nobody recorded; measured bases fit the drum and pail, not the chair)')
check.equal('the shadows fade in from the slide\'s start over 0.8 s', [shadows['shadows'][0]['fade_from'], shadows['shadows'][0]['fade_in_seconds']], [2.0, 0.8],
            recorded='notice-corner.js line 175 (0.55 x smooth((t - T.move) / 0.8)); film-settings.json effects.contact_shadow')
code_run, default = run('contact-shadows', '--place-facts', NOTICE_FACTS, '--footprints', os.path.join(OURS, 'footprints-notice-corner.json'))
names = sorted(s['prop'] for s in default['shadows'])
check.true('without a list, the lantern (on the chair\'s seat) and the notice (on its board) get no ground shadow',
           'lantern' not in names and 'notice' not in names and {'drum', 'chair', 'pail'} <= set(names),
           details=f'chosen: {names}', recorded='notice-corner.js shadows: drum, chair and pail only', proves='the shot checker\'s resting tolerances '
           '(composing.resting_*) leave out props resting on a raised surface or hanging above the ground (the board is still offered: the hand '
           'chose none for it)')
blender = os.environ.get('BLENDER') or '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
if os.path.exists(blender) and os.path.exists(NOTICE_BLEND):
    out = tempfile.mkdtemp(prefix='plan-effects-')
    try:
        subprocess.run([blender, '-b', NOTICE_BLEND, '--python', os.path.join(KIT, 'paper-film', 'blender', 'set_measurements.py'), '--', 'footprints',
                        '--check', os.path.join(FIXTURES, 'notice-corner', 'notice-corner-shot-check.json'), '--groups', 'drum,chair,pail',
                        '--out', os.path.join(out, 'f.json')], capture_output=True, text=True, timeout=300)
        again = json.load(open(os.path.join(out, 'f.json')))['footprints']
        kept = json.load(open(os.path.join(OURS, 'footprints-notice-corner.json')))['footprints']
        check.true('set_measurements.py footprints measures the same bases again', all(abs(again[g]['width'] - kept[g]['width']) < 1e-4 and
                                                                                       abs(again[g]['depth'] - kept[g]['depth']) < 1e-4 for g in ('drum', 'chair', 'pail')),
                   recorded='tests/fixtures/effects-camera-light/footprints-notice-corner.json', proves='the Blender companion still runs and agrees with its fixture')
    finally:
        shutil.rmtree(out, ignore_errors=True)
else:
    check.note('Blender or notice-corner.blend is not here: the live footprint measurement was skipped')

# ------------------------------------------------------------------------------------------------ window change ("busy")
passes, boost = effects.judge_window_change(3.0, settings)
check.true('round 4 "busy": 130 -> 133 levels is too small, about 5 times more needed', not passes and abs(boost - 5.0) < 1e-9,
           recorded='round4-result.json finding 8 ("No. 2\'s windows go from 130 to 133 levels"; "aim for at least 15")', proves='only repeats 15 / 3')
found = effects.window_change([0, 0, 300, 220], os.path.join(OURS, 'busy-new-windows-79.00.png'), [os.path.join(OURS, 'busy-new-windows-79.80.png')], settings)
check.close('round 5 final burst: size of change at 79.8 s', found['others'][0]['size_of_change'], 28.1, 0.15,
            recorded='measured here on scratchpad redesign/round5-pages/busy-new/still-79.00.jpg and still-79.80.jpg (crop 320,480,620,700); the same '
            'numbers as round 5\'s window_change.py', proves='the planner\'s measure equals the round 5 tool\'s')
check.true('round 5 final burst passes (15 levels or more)', effects.judge_window_change(found['others'][0]['size_of_change'], settings)[0])
earlier = effects.window_change([0, 0, 300, 220], os.path.join(OURS, 'busy-2-windows-79.00.png'), [os.path.join(OURS, 'busy-2-windows-79.80.png')], settings)
check.close('an earlier round 5 try (busy-2): size of change at 79.8 s', earlier['others'][0]['size_of_change'], 11.3, 0.15,
            recorded='measured here on scratchpad redesign/round5-pages/busy-2 stills', proves='the measure separates a weaker try from the final one '
            '(nobody recorded a verdict on busy-2; the final burst replaced it)')
check.true('the earlier try is under 15 levels', not effects.judge_window_change(earlier['others'][0]['size_of_change'], settings)[0])

# ------------------------------------------------------------------------------------------------ fire: glow pulse and flames
glows = {g['name']: g for g in effects.read_glow_pulse(os.path.join(KIT, 'paper-film', 'scenes', 'notice-corner.js'))}
check.close('notice corner glow pulse (kept, log 32): 0.02 / 1.25', glows['fireGlow']['swing_share'] if 'swing_share' in glows['fireGlow'] else
            glows['fireGlow']['amplitude'] / glows['fireGlow']['base'], 0.016, 1e-9, recorded='notice-corner.js poseAt (1.25 + 0.02 sin)', proves='repeats the code')
code_run, fire_old = run('fire', '--glow', '1.25,0.1')
check.true('the log 31 pulse 1.25 + 0.1 sin (8%) is refused', code_run == 1 and fire_old['problems'], recorded='notice-corner.js at commit 9c77add '
           '(1.25 + 0.1 sin); log 32: its rim slid 20 px on the road, filmed swing 2.8%', proves='the setting limit refuses the pulse the user\'s film lost')
code_run, fire_now = run('fire', '--page-file', os.path.join(KIT, 'paper-film', 'scenes', 'notice-corner.js'),
                         '--effects-file', os.path.join(KIT, 'paper-film', 'scenes', 'pit-village-effects.js'))
check.true('the kept notice corner pulse (1.6%) passes and the kept flames vary enough', code_run == 0 and not fire_now['problems'],
           details=f'glows {[round(g["swing_share"], 4) for g in fire_now["glows"]]}, flames {fire_now["flames"]}',
           recorded='notice-corner.js fireGlow (log 32); pit-village-effects.js Flames (sizes 0.7-1.3, leans +-0.25 rad)',
           proves='repeats where the limits came from (the kept settings)')
works_glows = effects.read_glow_pulse(WORKS_EFFECTS)
check.note('the Works\' glow pulse in the plugin kit\'s works-effects.js: ' + ', '.join(f'{g["name"]} {g["base"]} + {g["amplitude"]} '
           f'({g["amplitude"] / g["base"] * 100:.2f}%)' for g in works_glows))
row = os.path.join(tempfile.mkdtemp(prefix='plan-effects-'), 'flames.js')
open(row, 'w').write('export class Flames {\n  constructor() { this.tongues = [[0, 0, 0.4, 0.1], [0.1, 0, 0.4, 0.1], [0.2, 0, 0.4, 0.1]]\n'
                     '      .map(([dx, dz, height, width], i) => { const size = 1.0 + random() * 0.0;\n'
                     '        return { lean: (random() - 0.5) * 0.0 }; }); }\n}\n')
code_run, fire_row = run('fire', '--effects-file', row)
check.true('a neat row of identical flames is refused', code_run == 1 and len(fire_row['problems']) == 2, recorded='log 29 ("flames like a neat row of '
           'cartoon teardrops")', proves='the variety check catches no variety (a planted case)')
shutil.rmtree(os.path.dirname(row), ignore_errors=True)

# ------------------------------------------------------------------------------------------------ lint and fire smoke
pages = os.path.join(KIT, 'paper-film', 'scenes', 'austerity-chapter-1', 'page-*.js')
code_run, linted = run('lint', pages)
check.true('chapter 1\'s paper pages make every effect through kit.effect', code_run == 0 and linted['problems'] == 0 and len(linted['pages']) >= 10,
           recorded='kit/paper-film/scenes/austerity-chapter-1 (lesson 29\'s fix)', proves='the lint passes the pages that follow lesson 29')
bad = os.path.join(tempfile.mkdtemp(prefix='plan-effects-'), 'page-bad.js')
open(bad, 'w').write("import { PaperKit } from '../paper-kit.js';\nconst dust = new Dust(kit.scene, {});\nconst smoke = kit.effect(new Smoke(kit.scene, {}));\n"
                     "const later = new Sparks(kit.scene);\nkit.effect(later);\n")
code_run, linted_bad = run('lint', bad)
check.true('a paper page making Dust outside kit.effect is caught (only that one)', code_run == 1 and linted_bad['problems'] == 1,
           details='; '.join(linted_bad['pages'][0]['problems']), recorded='lesson 29 (page 8\'s dust stayed on pages 9 and 10)', proves='a planted fault is found')
shutil.rmtree(os.path.dirname(bad), ignore_errors=True)
camera = geometry.camera_from_place_facts(facts, settings, 'w1', 'composed', 'film')
fire = settings.value('effects_planner.fire_smoke')
brazier = emitters['brazier fire']['at']
figures = effects.figure_boxes(facts, camera, settings)
near_man = [f for f in figures if f['name'] == 'man-2']
samples = effects.trace_fire_smoke(camera, brazier, fire, step)
planted = {'name': 'planted man', 'box': [samples[4]['left'], samples[4]['top'], samples[4]['right'], 0.75]}
crossing = [s for s in samples if s['strength'] > 0.2 and effects.overlaps([s['left'], s['top'], s['right'], s['bottom']], planted['box'])]
check.true('a man planted in the brazier\'s smoke is crossed by thick smoke', bool(crossing), recorded='round1-result.json checked.findings[9] (a man in '
           'the brazier smoke read as a grey ghost)', proves='the fire-smoke trace finds a planted case')
crossing_man2 = [s for s in samples if s['strength'] > 0.2 and near_man and effects.overlaps([s['left'], s['top'], s['right'], s['bottom']], near_man[0]['box'])]
check.note(f'W1: the brazier\'s thick smoke overlaps the box of man 2 (the stooped man warming his hands over it) at {len(crossing_man2)} traced ages: '
           'a geometric overlap at his head; whether he reads as a ghost needs a person\'s eye')

check.finish()
