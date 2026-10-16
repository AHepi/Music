"""What this does: tests the shot planner (plan_shot.py) on the project's recorded cases, from the shot lists in
fixtures/shot-planner/ (written from the check files and build scripts; each says where it came from), and on checkout C1,
a place nothing in the planner was written from (the hold-out). Each line gives the number got, the number recorded,
where it is recorded, and what the check proves. Where a check only repeats a sum the project already did (or the very
choice the planner's margin was set from), it says so.

What it covers:
 - the Works W1 (round 5) as built passes; round 4's spot fails rule 7 at 0.653 and says how many metres nearer; the
   planned W1 lands within 0.11 m of the spot round 5 chose by hand;
 - the crowd: round 3's and round 4's single file up the lane fails the 60-degree rule from W1 and W3, the round 5 crowd
   and a planned crowd pass; where Blender recorded the men's boxes, the planner's feet land just above them;
 - W3 (an overview): the crowd reaches only 0.67 and needs an eye of about 6.8 m; the handcart (a fill prop) makes the reach;
 - the notice corner: the support's edge (2.96 m), rule 12's slide (built 3.10 m), the rule 1 gap after it (the checker's
   0.004-0.005), the reach, the accepted slide reported as known, and a worse slide not hidden by that acceptance;
 - the people test: everyone at least 6 m away, the facing man flagged with the "face lost in shadow" words and never a
   silhouette;
 - checkout C1 (hold-out): the predicted numbers against what the shot checker measured on the render (check 10);
 - prop turns from a stored front axis; the command line, its JSON and its settings list.
Run: python3 kit/calculators/tests/test_plan_shot.py   (or tests/run_all.py)
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, CALCULATORS  # noqa: E402
import plan_shot  # noqa: E402

check = Checker('shot planner: recorded cases and the checkout hold-out')
SHOTS = os.path.join(FIXTURES, 'shot-planner')


def run(shots_file, names=None, extra=()):
    """Runs plan_shot.py's command line quietly and returns {shot name: result}."""
    with tempfile.TemporaryDirectory() as folder:
        out = os.path.join(folder, 'plan.json')
        argv = ['--shots', os.path.join(SHOTS, shots_file), '--json', '--out', out] + (['--shot'] + names if names else []) + list(extra)
        with contextlib.redirect_stdout(io.StringIO()):
            plan_shot.main(argv)
        with open(out) as handle:
            full = json.load(handle)
    return {s['name']: s for s in full['shots']}, full


def item(result, rule, thing=None):
    found = [c for c in result['checks'] if c['rule'] == rule and (thing is None or thing in c.get('things', []) or thing in c['about'])]
    return found[0] if found else None


def fixture(*parts):
    with open(os.path.join(FIXTURES, *parts)) as handle:
        return json.load(handle)


# ------------------------------------------------------------------------------------------------ the Works, W1 (round 5)
works, works_full = run('works-shots.json')
w1 = works['w1']
reach = item(w1, 'rule7_story_reaches_down')
check.close('W1 as built: the DIESEL drum\'s reach (down)', reach['measured'], 0.72, 0.006,
            recorded='working files redesign/round5-set/checks/final-w1-quiet/report.md rule 7: "diesel drum, reaching 0.72 down" (rendered)',
            proves='the planner predicts the rendered reach from the place facts before anything is drawn (the core checks the drum\'s front middle, '
                   '0.723; the planner uses its box corner)')
check.equal('W1 as built: rule 7 passes and nothing fails outright', (reach['verdict'], w1['counts'].get('fail', 0)), ('pass', 0),
            recorded='round 5 final checks (rule 7 passed; the open problems there are light, near-touches and the petrol drum, which the planner '
                     'reports as "look" from boxes)')
backs = item(w1, 'people_backs_distance')
check.close('W1: the nearest man with his back turned (m)', backs['measured'], 7.42, 0.01,
            recorded='works-shot.json men_seen "w1 composed" man-6 7.42 m (assemble_works.py)', proves='repeats the distance sum (depth along the view)')
axes = [c for c in w1['checks'] if c['rule'] == 'crowd_axis_angle']
check.true('W1: the round 5 crowd stands across both views that see it (W1 and W3), at least 60 degrees', axes and all(c['verdict'] == 'pass' for c in axes),
           details='; '.join(f'{c.get("view")}: {c["measured"]} degrees' for c in axes),
           recorded='round 4 finding 2 and round 5 new_layout.txt ("a loose crowd two deep across the gateway")')
check.equal('W1: the round 5 crowd is two rows deep from W1', item(w1, 'crowd_rows')['measured'], 2, recorded='round 5 new_layout.txt ("two deep")')
rule1 = item(w1, 'rule1_meeting_point_gap')
check.equal('W1 (dark subject): where the lines meet lies inside the gate across, so rule 1 passes', rule1['verdict'], 'pass',
            recorded='shot_kind_profiles.dark_subject rule1 ("a meeting point inside the opening passes"); round 5 W1 report: rule 1 passed',
            proves='the kinds of shot reach the planner (as still life the box gap would be 0.185 of the width)')
slide = item(w1, 'slide_magnification')
check.true('W1: the 1.2 m slide stays inside the painting\'s limit at its nearest painted thing', slide['verdict'] == 'pass' and slide['measured'] <= slide['limit'],
           details=f'{slide["about"]}', recorded='plan 34 F13; round 5 W1 slide 12.0 -> 13.2 m')
plate = item(w1, 'plate_lens')
check.true('W1: casting the frame\'s corners along the slide, the house plate lens (64.4) covers the slide', plate['verdict'] == 'pass',
           details=f'needs {plate["measured"]} degrees', recorded='frame.plate_vertical_fov_degrees (film + 4, lesson 90)',
           proves='the 4 extra degrees cover a forward slide and the 0.03 fade band (a straight push needs about 63.5)')

# round 4's spot, the same layout: the bottom third bare
r4 = works['w1 from round 4\'s spot']
reach = item(r4, 'rule7_story_reaches_down')
check.close('W1 from round 4\'s spot (y 10.2): the story\'s reach (down)', reach['measured'], 0.653, 0.002,
            recorded='skeptic (log 35): 0.653; round 4 critic: "the story sits small and high, 0.53 to 0.65 down" (round4-result.json finding 3)',
            proves='the planner fails what the critic failed by eye')
check.equal('W1 from round 4\'s spot: rule 7 fails', reach['verdict'], 'fail')
check.within('W1 from round 4\'s spot: the fix brings the camera nearer by (m)', reach['nearer_metres'], 2.0, 3.0,
             recorded='round 4 critic: "bring both composed spots about 3 m nearer"; round 5 moved 3.0 m (10.2 -> 13.2)',
             proves='the metres the planner asks for (2.23 m, to reach exactly 0.70) agree with the move the project made (3 m, to 0.72)')

# W1 planned from its subject and story
planned = works['w1 planned']
check.close('W1 planned: the camera\'s place along the lane (y, m)', planned['camera']['composed'][1], 13.2, 0.15,
            recorded='works-shot.json views.w1 composed y 13.2 (round 5, chosen by hand)',
            proves='the reach sum alone puts the camera where round 5 put it (partly a repeat: the 0.02 margin was set knowing W1 reached 0.72)')
check.close('W1 planned: the camera in line with the gate\'s middle (x, m)', planned['camera']['lined_up_across_metres'], -3.5, 1e-6,
            recorded='works-shot.json gates.no-1 centre x -3.5 (built: -3.7, the pavement spot kept clear of the house fronts, which the place facts '
                     'do not hold)', proves='the dark subject\'s line-up (only that the line-up is the gate\'s middle)')
check.close('W1 planned: the slide starts 1.2 m back toward the gate (y, m)', planned['camera']['plate'][1], 13.0933 - 1.2, 0.001,
            recorded='plan 34 (1.2 m slides at W1 and W2)', proves='repeats the slide rule (start = end - L toward the subject\'s middle)')

# the crowd: single file up the lane fails, across the gate passes
for name, record in (('w1 round 4 (single file)', 'round4 w1 composed'), ('w1 round 3 (single file)', 'round3 w1 composed')):
    shot = works[name]
    axes = [c for c in shot['checks'] if c['rule'] == 'crowd_axis_angle']
    check.true(f'{name}: the crowd\'s long axis lies within 20 degrees of the W1 and W3 views, so it fails the 60-degree rule',
               len(axes) == 2 and all(c['verdict'] == 'fail' and c['measured'] < 20 for c in axes),
               details='; '.join(f'{c.get("view")}: {c["measured"]} degrees' for c in axes),
               recorded='round4-result.json finding 2 ("a single file running up the lane is seen end-on and the men stack behind each other"); '
                        'design: "axis within 10 deg of W1 and W3" (the stooped man off the file tilts it to 12-14)',
               proves='the rule catches the layout the critic rejected, from the feet alone')
    heads = item(shot, 'crowd_head_spacing')
    check.equal(f'{name}: the heads stack (less than a head width apart on screen)', heads['verdict'], 'fail',
                recorded='round 4 critic: "W1: 4 or 5 men merge into one black mass"')
    boxes = fixture('shot-planner', 'works-shots.json')['recorded'][record]
    shot_spec = next(s for s in fixture('shot-planner', 'works-shots.json')['shots'] if s['name'] == name)
    feet = {f['name']: f['feet'] for f in shot_spec['figures']}
    import frame_geometry as g  # noqa: E402
    from settings import load_settings  # noqa: E402
    settings = load_settings()
    camera = g.camera_from_turn(shot_spec['camera']['at'], 0, 0, 0, settings.value('frame.film_vertical_fov_degrees'), 1080, 1920)
    gaps = [boxes[m][3] - g.project_point(camera, feet[m])['down'] for m in boxes]
    check.within(f'{name}: Blender\'s box bottoms lie this far below the feet the planner projects (smallest)', min(gaps), -0.001, 0.015,
                 recorded=f'works-shot.json men_seen "w1 composed" as committed for {record.split()[0]} (7b3fe7d, 34756a4)',
                 proves='feet predict where a figure reaches down the frame on layouts the planner was not written from (shoes reach a little lower)')
    check.within(f'{name}: the same, largest', max(gaps), -0.001, settings.value('shot_planner.figure_shoes_below_feet_down') + 0.002,
                 recorded='the same records', proves='the shoes allowance (0.012, measured on round 5 and the people test) holds on rounds 3 and 4')
crowd = works['w1 with a planned crowd']
names = [c['rule'] for c in crowd['checks'] if c['verdict'] != 'pass' and c['rule'].startswith(('crowd', 'people'))]
check.equal('a planned crowd (7 men, two deep across No. 1\'s gate) passes the axis, rows, shoulder, head and 6 m tests', names, ['crowd_visible_share'],
            recorded='people settings (two deep, 0.3-0.5 m between shoulders, 0.8 m back row, 6 m)',
            proves='the proposer\'s layout meets the rules it was built from (a repeat); the box estimate of how much of each figure shows stays a "look"')
check.equal('a planned crowd: the proposer wrote 7 figures', len(crowd.get('proposed_figures', [])), 7)

# W3, the overview
w3 = works['w3']
reach = item(w3, 'rule7_story_reaches_down')
check.equal('W3 (overview): the crowd misses 0.70 but the handcart (a fill prop) makes the reach, which an overview allows', reach['verdict'], 'pass',
            recorded='works-shot.json decisions.round_4 (the handcart in W3\'s bottom third); shot_kind_profiles.overview rule 7 who_may_reach')
story_reach = float(re.search(r'reaching ([\d.]+) down', reach['about']).group(1))
check.close('W3: the crowd\'s own reach (down)', story_reach, 0.67, 0.01, recorded='skeptic (log 35): "W3\'s crowd at 29-30 m reaches only 0.67 down"',
            proves='repeats the core\'s figure from the place facts')
eye = item(w3, 'overview_eye_for_story')
check.close('W3: the eye the crowd itself would need (m)', eye['measured'], 6.8, 0.15,
            recorded='skeptic (log 35): "the planner would demand an eye of about 6.9 m"; design formula: feet z + 0.2 x 1920 x d / 1649.4',
            proves='the overview sum (the skeptic rounded; man 2 at 29.2 m gives 6.78)')
planned_w3 = works['w3 planned']
check.true('W3 planned: the story would need an eye above the overview\'s range, so the plan stops at 7.0 m and says what makes the reach',
           abs(planned_w3['camera']['eye_above_floor_metres'] - 7.0) < 1e-6 and any('above the overview eye range' in s for s in planned_w3['steps']),
           details=planned_w3['steps'][0][:200], recorded='shot_kind_profiles.overview rule2 [0.8, 7.0]')

# prop turns from a stored front axis
turns = crowd['prop_turns']
check.close('the PETROL drum\'s stencil turned toward W1 (degrees)', turns['no-1-drum-petrol']['turn_degrees'], 12.0, 0.5,
            recorded='assemble_works.py DRUM_SPOTS no-1 petrol turn 12 ("words turned to the gate view")',
            proves='turn = heading to the target minus the model\'s front axis reproduces the build\'s turn')
check.note(f'the DIESEL drum toward W1 would turn {turns["no-1-drum-diesel"]["turn_degrees"]:.1f} degrees; the build used 8, between W1\'s 5.0 and '
           f'W3\'s 8.7 (both views read it)')

# ------------------------------------------------------------------------------------------------ the notice corner
notice, _ = run('notice-corner-shots.json')
end = notice['end']
gap = item(end, 'rule1_meeting_point_gap')
check.close('notice corner as built: the rule 1 gap to the board (share of the width)', gap['measured'], 0.0045, 0.003,
            recorded='log 31-32: the checker measured the rule 1 gap at 0.004 to 0.005', proves='the box outline gives the checker\'s gap within 0.003')
reach = item(end, 'rule7_story_reaches_down')
check.close('notice corner: the pail\'s reach (down)', reach['measured'], 0.9403, 0.006,
            recorded='experiments/31 .../facts.json groups.pail.screen_box_unclipped bottom 0.9403 (Blender)', proves='the reach on a sloping street, before drawing')
right = item(end, 'rule12_must_read_right_edge', 'notice')
check.close('notice corner: the notice\'s right edge (across)', right['measured'], 0.89, 0.01,
            recorded='experiments/32 report rule 12 line ("notice 0.89", rendered)', proves='rule 12 for a sign square to the camera')
check.close('notice corner: the deepest a story thing may stand for 0.70 (m)', end['closed_forms']['deepest_for_reach_on_the_floor_metres'], 5.95, 0.02,
            recorded='inventory (design): 5.95 m (eye 1.80, lines meeting 0.4395)', proves='repeats the reach sum')
known = item(end, 'slide_magnification')
check.equal('notice corner: its slide is over the painting\'s limit and reported as known (the accepted list)', known['verdict'], 'known',
            recorded='notice-corner-place-facts.json accepted slide_magnification (decision 38: the user kept the film)',
            proves='an accepted exception is reported as known, not as a failure')
check.within('notice corner: the slide at the pail\'s nearest corner (times nearer)', known['measured'], 1.44, 1.50,
             recorded='skeptic (log 35): pail 1.45 (its middle); the corner comes a little nearer')
box = item(end, 'rule3_story_box')
check.equal('notice corner: the story box from boxes (0.52 wide) is only a "look", since the render measured 0.43 within 0.48', box['verdict'], 'look',
            recorded='experiments/32 report: "rule 3: story props close together" passed (0.43 x 0.42, limit 0.48 x 0.50 from the reference)',
            proves='an upper-bound estimate warns without failing a shot the render passes')
turn = notice['end']['prop_turns']['notice']['turn_degrees']
facts = fixture('notice-corner', 'notice-corner-shot.json')
import math  # noqa: E402
built = math.degrees(math.atan2(facts['camera_end'][0] - facts['notice_centre'][0], -(facts['camera_end'][1] - facts['notice_centre'][1])))
check.close('notice corner: the notice turned to face the composed camera (degrees)', turn, built, 0.01,
            recorded='assemble_notice_corner.py line 109: facing = atan2(cam.x - board.x, -(cam.y - board.y))', proves='the prop turn sum matches the build\'s')
reference = notice['planned with the reference']
check.close('notice corner planned: in line with the board\'s near edge before rule 12 (x, m)', reference['camera']['lined_up_across_metres'], 2.96, 0.01,
            recorded='design (log 35): "support edge = board centre 3.45 - 0.88 x 1.11 / 2 = 2.96 m, exactly the first landmark match\'s camera x"',
            proves='rule 1\'s line-up from the place facts gives the camera the landmark match found')
check.close('notice corner planned: after rule 12\'s sideways slide (x, m)', reference['camera']['composed'][0], 3.10, 0.03,
            recorded='assemble_notice_corner.py CAMERA_END x 3.10 (the checker slid it 0.14 m in log 31)',
            proves='the planner\'s slide for the phone buttons (0.12 m) agrees with the checker\'s advice to within 3 cm')
gap = item(reference, 'rule1_meeting_point_gap')
check.close('notice corner planned: the rule 1 gap after that slide', gap['measured'], 0.0045, 0.003, recorded='log 31-32: 0.004 to 0.005 after the slide',
            proves='the sliding (not turning) fix keeps the lines on the board, as the checker found')
worse = notice['planned']
slide = item(worse, 'slide_magnification')
check.true('notice corner planned without the reference (nearer, 3.3% subject): its slide is worse than the accepted one, so it fails again',
           slide['verdict'] == 'fail' and 'accepted_but_worse' in slide, details=slide['about'],
           recorded='accepted at 1.45 (place facts); shot_planner.check_shot_accepted_worse_share 0.05',
           proves='an acceptance covers the shot that was accepted, not a worse one')

# ------------------------------------------------------------------------------------------------ the people test
people, _ = run('people-test-shots.json')
still = people['still']
backs = item(still, 'people_backs_distance')
check.equal('people test: every man with his back turned is at least 6 m away', backs['verdict'], 'pass',
            recorded='people-test-shot.json distance_metres (nearest 6.62 m)', proves='the 6 m rule on a turned camera and a sloping street')
face = item(still, 'people_face_shows', 'figure-facing')
check.close('people test: the facing man\'s head (px)', face['measured'], 55.0, 2.0, recorded='skeptic (log 35): "the facing man at about 7 m (head about 53 px)"',
            proves='repeats the size sum')
check.true('people test: the facing man is a "look" with the painter\'s "face lost in shadow" words, never a silhouette',
           face['verdict'] == 'look' and 'face lost in shadow' in face['fix'] and 'Never a black silhouette' in face['fix'],
           details=face['fix'][:160], recorded='lesson 137 (silhouettes read as shadow puppets); log 34: the facing man got no features with that prompt',
           proves='the skeptic\'s change: no silhouette fallback')
reach = item(still, 'rule7_story_reaches_down')
check.equal('people test: the nearest man\'s feet land 0.692, just short of 0.70, so it is a "look" (his shoes may make it)', reach['verdict'], 'look',
            recorded='people-test-shot.json figure-arms-folded film_frame_box bottom 0.7013 (Blender)', proves='the shoes allowance turns a false fail into a look')
axis = item(still, 'crowd_axis_angle')
check.note(f'people test: the five men round the brazier lie {axis["measured"]} degrees to the view (the invented 60-degree rule fails them) while their '
           f'heads are {item(still, "crowd_head_spacing")["measured"]} head widths apart; the painting test found them readable, so the axis rule '
           f'suits a waiting crowd better than a ring round a fire (people.crowd_axis_min_angle_to_view_degrees is invented: calibrate)')

# ------------------------------------------------------------------------------------------------ hold-out: checkout C1, judged as built
checkout, _ = run('checkout-c1-shots.json')
c1 = checkout['c1']
recorded = 'working files redesign/round5-checkout/check10/report.md (the shot checker on the render, 2026-10-16)'
check.close('checkout C1 (hold-out): where the lines meet, across', c1['meeting_point']['across'], 0.500, 0.001, recorded=recorded)
gap = item(c1, 'rule1_meeting_point_gap')
check.close('checkout C1 (hold-out): the rule 1 gap to the bill stand', gap['measured'], 0.005, 0.006, recorded=recorded + ' ("0.005 of the frame width")',
            proves='the line-up holds at a place the planner was not written from')
reach = item(c1, 'rule7_story_reaches_down')
check.close('checkout C1 (hold-out): the story\'s reach on the counter (down)', reach['measured'], 0.78, 0.006, recorded=recorded + ' ("divider, reaching 0.78")',
            proves='the reach above a counter, predicted (the basket\'s box corner and the divider land within 0.001 of each other)')
rendered = {'bill': 0.82, 'bread label': 0.57, 'milk label': 0.68, 'butter label': 0.60, 'cheese label': 0.70, 'checkout sign': 0.81, 'petrol fascia': 0.51}
got = {n: item(c1, 'rule12_must_read_right_edge', n)['measured'] for n in rendered}
worst = max(abs(got[n] - rendered[n]) for n in rendered)
check.within('checkout C1 (hold-out): seven lettered things\' right edges against the render (largest difference)', worst, 0, 0.011,
             recorded=recorded + ' rule 12 line', proves='rule 12 is predicted for every word to read before rendering')
story = item(c1, 'rule12_story_right_edge')
rows = {r['thing']: r['right'] for r in story['rows']}
check.true('checkout C1 (hold-out): story things\' right edges by box are never short of the render (basket 0.82, divider 0.79)',
           rows['basket'] >= 0.82 - 0.006 and rows['divider'] >= 0.79 - 0.006, details=f'basket {rows["basket"]:.3f}, divider {rows["divider"]:.3f}',
           recorded=recorded, proves='a box warns early and never misses (the checker takes the 90th percentile of the rows)')
box = item(c1, 'rule3_story_box')
check.true('checkout C1 (hold-out): the story box by boxes is at least the rendered 0.36 x 0.35 and close to it',
           box['measured'][0] >= 0.36 - 0.01 and abs(box['measured'][1] - 0.35) <= 0.01 and box['measured'][0] - 0.36 <= 0.05,
           details=f'{box["measured"]}', recorded=recorded + ' ("0.36 of the frame wide and 0.35 tall")')
spots = item(c1, 'main_rule_spot_box')['about']
bill = [float(v) for v in re.search(r'middle of bill ([\d.]+), ([\d.]+)', spots).groups()]
check.true('checkout C1 (hold-out): the bill\'s middle on screen (0.66, 0.52 rendered)', abs(bill[0] - 0.66) <= 0.01 and abs(bill[1] - 0.52) <= 0.015,
           details=f'{bill}', recorded=recorded + ' main rule line')
till = item(c1, 'rule8_work_prop_band', 'till')
check.close('checkout C1 (hold-out): the till\'s middle (down)', till['measured'], 0.61, 0.01, recorded=recorded + ' ("till ... its middle 0.61 down")')
rack = item(c1, 'rule8_work_prop_band', 'bag rack')
check.true('checkout C1 (hold-out): the bag rack\'s box middle (0.75) misses the rendered 0.60 because the counter hides its lower part, and the planner '
           'says "look", not "fail"', rack['verdict'] == 'look' and abs(rack['measured'] - 0.60) > 0.1, details=f'{rack["measured"]}',
           recorded=recorded + ' ("bag rack ... its middle 0.60 down")', proves='a known weakness of boxes, reported as a judgement')
eye = item(c1, 'rule2_eye_height')
check.equal('checkout C1: the eye (1.6 m) is inside the interior profile\'s 1.5 to 1.7 m', eye['verdict'], 'pass', recorded='checkout-c1-shot-check.json eye_height')
slide = item(c1, 'slide_magnification')
check.true('checkout C1: the 0.7 m slide is over the painting\'s limit at its nearest painted thing (the basket\'s front corner)',
           slide['verdict'] == 'fail' and 1.30 < slide['measured'] < 1.33, details=slide['about'],
           recorded='checkout-shot.json nearer_times 1.292 (the helper judged the basket\'s middle); core: divider 1.308 (1.7% over)',
           proves='the same finding as the core, at the nearest corner: the slide should be about 0.63 m')
c1p = checkout['c1 planned']
check.close('checkout C1 planned (hold-out): in line with the bill stand\'s near edge (x, m)', c1p['camera']['composed'][0], -0.16, 0.02,
            recorded='checkout-shot.json decisions.camera ("in line with the bill\'s left edge (x -0.16)")',
            proves='rule 1\'s line-up gives the helper\'s choice within 2 cm (the stand is 1.7 cm wider than the bill)')
check.equal('checkout C1 planned: nothing fails outright', c1p['counts'].get('fail', 0), 0)

# ------------------------------------------------------------------------------------------------ the command line
check.true('the JSON names the settings it used, including the planner\'s own section',
           any(k.startswith('shot_planner.') for k in works_full['settings_used']) and 'people.backs_to_camera_min_distance_metres' in works_full['settings_used'],
           details=f'{len(works_full["settings_used"])} settings')
with contextlib.redirect_stdout(io.StringIO()) as printed:
    plan_shot.main(['--place-facts', os.path.join(FIXTURES, 'works', 'works-place-facts.json'), '--view', 'w1'])
text = printed.getvalue()
check.true('--view judges a view as built and prints a plain report with the settings used', 'Shot w1' in text and 'Settings used' in text,
           details=text.splitlines()[0])
check.finish()
