"""What this does: tests the shot-kind profiles in film-settings.json against what the shot checker found on the views the
project kept. It reads the checker's numbered problems word for word (fixtures copied from the round 5 final checks of the
Works, the finished notice corner and checkout C1), turns each into a rule and a measured number, and judges it twice:
by the still-life rules alone (the notice corner's, which the skeptic said would reject the Works) and by the view's own
kinds of shot from its place facts. It prints, view by view, what each profile covers and what stays open.

What it proves, and what not:
 - the Works part only repeats the numbers the crowd, overview and dark-subject profiles were written from (they are
   not a hold-out); it proves the profiles say what they were meant to say, and lists the problems they do NOT excuse;
 - the overview's "a fill prop may reach 0.70" is checked with the camera sums from the place facts (W3's crowd reaches
   0.67, the handcart 0.79);
 - the notice corner's open problems are all in its accepted list (kept by the user, decision 38);
 - checkout C1: the interior profile clears check 1's four false "landed high" alarms but leaves check 10's three real
   light problems open (the profile was written partly from check 1, so only the second half is a hold-out).
Run: python3 kit/calculators/tests/test_shot_kind_profiles.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES  # noqa: E402
from settings import load_settings, resolve_profile, judge  # noqa: E402
import frame_geometry as g  # noqa: E402

check = Checker('shot-kind profiles against the views the project kept')
settings = load_settings()


def fixture(*parts):
    with open(os.path.join(FIXTURES, *parts)) as handle:
        return json.load(handle)


FIGURE = re.compile(r'^(no-2 )?man \d+$')
number = r'(-?[\d.]+)'


def reading(problem, story):
    """(rule id, measured, words) for one of the checker's problems; rule id None when no profile rule covers its kind."""
    rule, text = problem['rule'], problem['text']
    if rule.startswith('rule 3: story props close together'):
        m = re.search(rf'fill a box {number} of the frame wide and {number} tall', text)
        return 'rule3_story_box', [float(m.group(1)), float(m.group(2))], 'story box'
    if rule.startswith('rule 3: story props together in the street'):
        m = re.search(rf'stands {number} m from the nearest', text)
        return 'rule3_story_together_metres', float(m.group(1)), 'apart in the street'
    if rule.startswith('rule 4'):
        names = re.match(r"^(.+?)(?:'s edge runs right along | and | only just overlaps )(.+?)(?:'s edge| almost| by|:)", text)
        a, b = (names.group(1).strip(), names.group(2).strip()) if names else ('?', '?')
        between_figures = bool(FIGURE.match(a) and FIGURE.match(b))
        return ('rule4_between_figures' if between_figures else 'rule4_near_touch'), None, f'{a} / {b}'
    if rule.startswith('rule 8: nothing big where the eye enters'):
        m = re.match(rf'^(.+?) fills {number}% of the frame', text)
        thing = m.group(1)
        return 'rule8_bottom_left_share', float(m.group(2)) / 100, thing + (' (story)' if thing in story else ' (not story)')
    if rule.startswith('rule 12: titles in dim sky'):
        m = re.search(rf'Only {number}% of the title area is sky', text)
        return 'rule12_title_zone_sky_share', float(m.group(1)) / 100, 'title band sky'
    if rule.startswith('rule 1: aim the street at the story'):
        m = re.search(rf'is {number} of the frame width away.*?(\d+) pixels to the (left|right) and (\d+) pixels (below|above).*?spans {number} to {number} across',
                      text)
        return 'rule1_meeting_point_gap', {'gap': float(m.group(1)), 'across_pixels': int(m.group(2)), 'span': [float(m.group(6)), float(m.group(7))]}, 'meeting point'
    if rule.startswith('rule 5') and ' is bright' in rule:
        return 'rule5_subject_brightness_ratio', float(re.search(rf'is {number} times as bright', text).group(1)), 'subject brightness'
    if rule.startswith('rule 5') and 'biggest bright thing' in rule:
        m = re.search(rf'{number}% lie on .+? \(need 40%\) and {number}% in the', text)
        return 'rule5_brightest_share_on_subject', float(m.group(1)) / 100, f'brightest parts: {m.group(1)}% on the subject, {m.group(2)}% in the box'
    if rule.startswith('rule 5: nothing in the story group as bright'):
        return 'rule5_nothing_in_story_as_bright', None, 'story things brighter than the subject'
    if rule.startswith('rule 6: lit from below'):
        return 'rule6_lit_from_below', float(re.search(rf'is {number} warmer', text).group(1)), 'lit from below'
    if rule.startswith('rule 6: warm light'):
        return 'rule6_warm_share', float(re.search(rf'covers (?:only )?{number}% of the frame', text).group(1)) / 100, 'warm light'
    if rule.startswith('rule 10: the quiet side'):
        return 'rule10_quiet_side_weight', float(re.search(rf'holds {number}% of the weight', text).group(1)) / 100, 'quiet side weight'
    if rule.startswith('rule 10: nothing on the quiet side'):
        return 'rule10_nothing_on_quiet_side_outshines', None, 'a light on the quiet side'
    return None, None, rule


def verdict(rule_id, measured, rules):
    """'covered' when the view's profile passes or switches the rule off; 'open' otherwise."""
    if rule_id is None or rule_id not in rules:
        return 'open'
    entry = rules[rule_id]
    if rule_id == 'rule1_meeting_point_gap' and isinstance(measured, dict):
        if not entry.get('applies', True):
            return 'covered'
        if 'opening' in entry.get('measure', '') and measured['span'][0] <= 0.5 <= measured['span'][1]:
            return 'covered'   # the meeting point lies inside the opening (the street is level: it meets at 0.5 across)
        across = measured['across_pixels'] / settings.value('frame.width_pixels')
        return 'covered' if ('across only' in entry.get('unit', '') and across <= entry['value']) else 'open'
    result = judge(entry, measured) if measured is not None else ('off' if not entry.get('applies', True) else 'fail')
    if rule_id == 'rule8_bottom_left_share' and result == 'pass' and 'story things' in entry.get('applies_to', '') and measured > 0.01:
        return 'covered'   # only story things get the crowd's 0.02 (handled by the caller passing story membership)
    return 'covered' if result in ('pass', 'off') else 'open'


def at_printed_limit(rule_id, measured, rules):
    """True when the report's rounded number sits exactly on a limit (whole percentages, two decimals)."""
    if rule_id not in rules or not isinstance(measured, (int, float)):
        return False
    limit = rules[rule_id].get('value')
    bounds = limit if isinstance(limit, list) else [limit]
    return any(isinstance(b, (int, float)) and abs(measured - b) < 0.0051 for b in bounds)


works = fixture('works', 'works-place-facts.json')
kinds_of = {v['name']: v['kind_of_shot'] for v in works['views']}
problems = fixture('works', 'round5-final-check-problems.json')['views']
check_files = {'w1-quiet': 'works-w1-shot-check.json', 'w1-quiet-light': 'works-w1-shot-check.json', 'w1-working': 'works-w1-working-shot-check.json',
               'w2-quiet': 'works-w2-shot-check.json', 'w2-slowed': 'works-w2-slowed-shot-check.json', 'w3-quiet': 'works-w3-shot-check.json'}
still_life = resolve_profile(load_settings(), ['still_life'])
open_by_view = {}
for name, report in problems.items():
    view = name.split('-')[0]
    story = set(fixture('works', check_files[name]).get('story', [])) | {fixture('works', check_files[name]).get('subject')}
    rules = resolve_profile(load_settings(), kinds_of[view])
    rows = []
    for problem in report['problems']:
        rule_id, measured, words = reading(problem, story)
        if rule_id == 'rule8_bottom_left_share' and '(not story)' in words:
            own = verdict(rule_id, measured, still_life)   # other things keep 0.01
        else:
            own = verdict(rule_id, measured, rules)
        rows.append((problem['rule'], words, verdict(rule_id, measured, still_life), own, at_printed_limit(rule_id, measured, still_life)))
    still_open = [r for r in rows if r[2] == 'open']
    on_limit = [r for r in rows if r[2] != 'open' and r[4]]
    kept_open = [r for r in rows if r[3] == 'open']
    open_by_view[name] = kept_open
    check.equal(f'{name}: the still-life rules alone reject every problem the checker listed', len(still_open) + len(on_limit), len(rows),
                recorded=report['source'], proves='the skeptic\'s point: notice-corner limits would block the views the helpers kept')
    for r in on_limit:
        check.note(f'{name}: "{r[0]}" printed exactly at the still-life limit ({r[1]}): the checker rounds its percentages, so it was just past it')
    print(f'      {name} ({" + ".join(kinds_of[view])}): {len(rows)} problems, {len(rows) - len(kept_open)} covered by its profiles, {len(kept_open)} open:')
    for rule, words, _, own, _ in rows:
        print(f'        {"covered" if own == "covered" else "OPEN   "}  {rule}: {words}')

EXPECTED_OPEN = {   # what the profiles deliberately do NOT excuse (fix them, or accept them by name with a reason)
    'w1-quiet': {'set-up: the finished picture matches the scene', 'rule 4: overlap clearly or leave a clear gap', 'rule 8: nothing big where the eye enters'},
    'w2-quiet': {'rule 3: story props together in the street', 'rule 6: warm light from the people\'s own lights', 'rule 3: one touching group',
                 'rule 4: overlap clearly or leave a clear gap', 'rule 8: nothing big and dark where the eye enters'},
}
for name, expected in EXPECTED_OPEN.items():
    got = {r[0] for r in open_by_view[name]}
    check.equal(f'{name}: the kinds of problem the profiles leave open', got, expected,
                proves='the profiles excuse only what the project kept on purpose (the crowd\'s width, figure near-touches, a dark subject\'s light)')
w1 = {r[1] for r in open_by_view['w1-quiet']}
check.true('W1: the petrol drum at 1.4% bottom-left stays open (it is not a story thing, so the crowd\'s 2% does not apply)', 'petrol drum (not story)' in w1,
           details=', '.join(sorted(w1)))
check.true('W1: the near-touches between men are covered, the lantern touching man 1 is not', 'lantern / man 1' in w1 and not any('man 3 / man 6' in x for x in w1))
w1light = {r[0] for r in open_by_view['w1-quiet-light']}
check.true('W1 light rules: the dark subject switches off "subject brightest" and "lit from below"',
           not any(k in w1light for k in ('rule 5: no-1 gate is bright', 'rule 5: no-1 gate is the biggest bright thing', 'rule 6: lit from below')),
           details=f'open: {sorted(w1light)}')

# overview: the fill prop reaches 0.70 where the far crowd cannot (camera sums on the place facts)
w3 = next(v for v in works['views'] if v['name'] == 'w3')
camera = g.camera_from_place_facts(works, settings, 'w3', 'plate', 'film')
men = [f for f in works['figures'] if f['group'] == 'men at No. 1']
crowd_reach = max(g.project_point(camera, f['feet'])['down'] for f in men)
handcart = next(p for p in works['props'] if p['name'] == 'handcart')
handcart_reach = g.project_point(camera, handcart['at'])['down']
check.close('W3: the crowd\'s nearest feet reach (down)', crowd_reach, 0.67, 0.01, recorded='skeptic (log 35): "W3\'s crowd at 29-30 m reaches only 0.67 down"',
            proves='the sum gives the skeptic\'s number from the place facts')
rule7 = resolve_profile(load_settings(), w3['kind_of_shot'])['rule7_story_reaches_down']
check.true('W3: under the overview profile the handcart (a fill prop) makes the 0.70 reach', 'fill prop' in rule7.get('who_may_reach', '') and handcart_reach >= rule7['value'],
           details=f'handcart foot {handcart_reach:.3f} down; who may reach: {rule7.get("who_may_reach")}',
           recorded='works-shot.json decisions.round_4 ("The handcart is on the right pavement in W3\'s bottom third")')

# the notice corner: still life, kept by the user
notice = fixture('notice-corner', 'notice-corner-place-facts.json')
final = fixture('notice-corner', 'notice-corner-final-check-problems.json')
accepted = {a['rule'] for a in notice['accepted']}
rules = resolve_profile(load_settings(), ['still_life'])
open_rules = []
for problem in final['problems']:
    rule_id, measured, words = reading(problem, set())
    if problem['rule'].startswith('reference'):
        continue   # matching the liked picture, not a house rule
    if verdict(rule_id, measured, rules) == 'open' and rule_id not in accepted:
        open_rules.append(problem['rule'])
check.equal('notice corner: every house-rule problem on the kept still is in its accepted list', open_rules, [],
            recorded='experiments/32 Notice corner - the shot checker\'s report.md; notes/Decisions.md decision 38',
            proves='an accepted list lets a checker report a kept shot as known instead of failing it')
slide = g.slide_magnifications(g.moved_to(g.camera_from_place_facts(notice, settings, 'end', 'composed', 'film'), notice['views'][0]['slide']['start']),
                               g.camera_from_place_facts(notice, settings, 'end', 'composed', 'film'),
                               [(p['name'], p['point']) for p in notice['views'][0]['painted_points']])
worst = max(s['magnification'] for s in slide)
written = next(a for a in notice['accepted'] if a['rule'] == 'slide_magnification')['measured']
check.close('notice corner: the accepted slide magnification is what the sums give from the place facts', worst, written, 0.01,
            recorded='notice-corner-place-facts.json accepted (1.45, the skeptic\'s pail figure)')

# checkout C1: interior
results = fixture('checkout-c1', 'checkout-c1-check-results.json')
checkout = fixture('checkout-c1', 'checkout-c1-place-facts.json')
inside = resolve_profile(load_settings(), checkout['views'][0]['kind_of_shot'])
counter = next(s for s in checkout['support_surfaces'] if s['kind'] == 'counter')['height']
cleared = 0
for line in results['check1']['landed_high']:
    bottom = float(re.search(rf'its bottom is {number} m above', line).group(1))
    air = bottom - counter
    cleared += judge(inside['resting_on'], air) == 'pass'
check.equal('checkout C1: check 1\'s four "landed on something high" alarms rest on the counter under the interior profile', cleared, 4,
            recorded='working files redesign/round5-checkout/check1/report.md (bottoms 0.89-0.90 m; the counter top 0.885 m from check 10\'s facts)',
            proves='a declared support surface ends the street rule\'s false alarm indoors (repeats where the profile came from)')
open_checkout = [p['rule'] for p in results['check10']['problems'] if verdict(reading(p, set())[0], reading(p, set())[1], inside) == 'open']
check.equal('checkout C1 (hold-out half): the interior profile leaves check 10\'s light problems open', len(open_checkout), len(results['check10']['problems']),
            recorded='working files redesign/round5-checkout/check10/report.md (lit from below -0.29, burnt-out 23%, a dark shape 1.5%)',
            proves='the profile excuses only what it was written for; real faults at a new place still show')
check.finish()
