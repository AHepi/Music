"""What this does: tests frame_geometry.py against numbers the project recorded, and against two places the camera
sums were not worked out from (checkout C1 and the people test). Each line says the number got, the number recorded,
where it is recorded, and what the check proves. Several checks only repeat a sum someone already did with the same
formula (marked "repeats"): they prove the code matches the project, not that the house rules are right.
Run: python3 kit/calculators/tests/test_frame_geometry.py   (or tests/run_all.py)
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # run with python3 -I too
from checks import Checker, FIXTURES  # noqa: E402
import frame_geometry as g
from settings import load_settings

settings = load_settings()
W, H = settings.value('frame.width_pixels'), settings.value('frame.height_pixels')
FILM, PLATE = settings.value('frame.film_vertical_fov_degrees'), settings.value('frame.plate_vertical_fov_degrees')
F = g.focal_length_pixels(FILM, H)
check = Checker('frame geometry: recorded cases and hold-outs')


def fixture(*parts):
    with open(os.path.join(FIXTURES, *parts)) as handle:
        return json.load(handle)


def facts_camera(facts):
    c = facts['camera']
    return g.camera_from_turn(c['at'], c['turn_degrees'], c['tilt_degrees'], c['roll_degrees'], c['vertical_fov_degrees'], *facts['size'])


def rounding_bound(camera, point, step):
    """How far a projection can move when a stored position is rounded by up to `step` metres on each axis."""
    here = g.project_point(camera, point)
    worst = 0.0
    for axis in range(3):
        for sign in (-1, 1):
            moved = list(point)
            moved[axis] += sign * step
            there = g.project_point(camera, moved)
            worst = max(worst, abs(there['across'] - here['across']), abs(there['down'] - here['down']))
    return 3 * worst


# ------------------------------------------------------------------------------------------------ lenses
check.close('film focal length (pixels)', F, 1649.4, 0.05, recorded='plan 34 T1; layout_calc.py; geometry_check.py (960 / tan 30.2 degrees)',
            proves='repeats the lens sum the helpers re-derived five times')
check.close('plate focal length (pixels)', g.focal_length_pixels(PLATE, 2730), 2168, 0.5, recorded='plan 34 T1 (2168 px)', proves='repeats the lens sum')
check.close('one degree of turn moves things (share of width)', g.turn_moves_per_degree(FILM, W, H), 0.027, 0.0005,
            recorded='07 Composing a shot.md rule 1 ("about 0.027")', proves='repeats rule 1\'s figure from the lens')

# ------------------------------------------------------------------------------------------------ the notice corner (where the rules were measured)
notice = fixture('notice-corner', 'notice-corner-final-frame-facts.json')
camera = facts_camera(notice)
met = g.meeting_point_level(6.87, 0.069927, FILM, W, H)
check.close('notice corner meeting point across (closed form)', met['across'], notice['lines_meet']['street'][0], 0.0001,
            recorded='experiments/31 Notice corner - working files/final frame measurements/facts.json lines_meet (0.68401)',
            proves='the closed form agrees with Blender\'s own camera (shot_facts.py projects the street direction with Blender)')
check.close('notice corner meeting point down (closed form)', met['down'], notice['lines_meet']['street'][1], 0.0001,
            recorded='same facts.json (0.43949)', proves='as above, for the street\'s 4-degree rise')
met = g.project_direction(camera, [0, 1, 0.069927])
check.close('notice corner meeting point, full projection', math.hypot(met['across'] - 0.68401, met['down'] - 0.43949), 0.0, 0.0001,
            recorded='same facts.json', proves='the full camera sum (turn as Blender sets it) agrees with Blender')
check.close('turn that puts the meeting point at 0.684 (degrees)', g.turn_for_meeting_point(0.684, FILM, W, H), 6.87, 0.01,
            recorded='assemble_notice_corner.py CAMERA_YAW_DEGREES 6.87', proves='the inverse sum gives the turn the scene was built with')
worst, count = 0.0, 0
for light in notice['lights']:
    if light['on_screen']:
        landed = g.project_point(camera, light['at'])
        error = max(abs(landed['across'] - light['on_screen'][0]), abs(landed['down'] - light['on_screen'][1]))
        allowed = rounding_bound(camera, light['at'], 0.0005) + 1e-5
        worst = max(worst, error / allowed)
        count += 1
check.within(f'notice corner: {count} lights land where Blender put them (worst error as a share of what rounding allows)', worst, 0, 1,
             recorded='same facts.json lights[].on_screen (Blender world_to_camera_view; positions stored to 1 mm)',
             proves='project_point is Blender\'s projection for a turned camera on a sloping street')
for group, recorded in (('notice', 0.002958), ('drum', 0.002521), ('pail', 0.001973), ('handcart', 0.006526)):
    depth = g.project_point(camera, notice['groups'][group]['centre'])['depth']
    check.close(f'notice corner metres per pixel at the {group}', g.metres_per_pixel(camera, depth), recorded, 0.000002,
                recorded=f'same facts.json groups.{group}.metres_per_pixel', proves='depth along the view matches Blender\'s (metres per pixel repeats d / f)')
pail = notice['groups']['pail']
low, high = g.box_from_centre(pail['centre'], [pail['width'], pail['depth'], pail['height']])
check.close('notice corner pail\'s box bottom (down)', g.project_box(camera, g.box_corners(low, high))['box'][3], pail['screen_box_unclipped'][3], 0.005,
            recorded='same facts.json groups.pail.screen_box_unclipped (0.9403; the design: front foot 0.941)',
            proves='the reach of a story prop on a sloping street comes out within 0.005 of Blender (the box here is upright, Blender\'s follows the turned pail)')
rule12 = fixture('notice-corner', 'notice-corner-final-check-problems.json')['rule12_line']
rendered_right = {name: float(value) for name, value in re.findall(r'(\w[\w ]*?) (0\.\d+)', rule12.split('(', 1)[1])}
boxes_right = {}
for name in rendered_right:
    info = notice['groups'][name]
    low, high = g.box_from_centre(info['centre'], [info['width'], info['depth'], info['height']])
    boxes_right[name] = g.project_box(camera, g.box_corners(low, high))['box'][2]
check.true('notice corner: whole-box right edges never fall short of the rendered ones (boxes only warn early)',
           all(boxes_right[n] >= rendered_right[n] - 0.006 for n in rendered_right),
           details=', '.join(f'{n} {boxes_right[n]:.3f}/{rendered_right[n]}' for n in rendered_right),
           recorded='experiments/32 Notice corner - the shot checker\'s report.md, rule 12 line (rendered, 90th percentile of rows)',
           proves='the boxes command can flag a thing near the phone buttons before rendering without missing one the render would catch')
check.close('notice corner: the flat notice\'s right edge by box against the render', boxes_right['notice'], rendered_right['notice'], 0.01,
            recorded='same rule 12 line ("notice 0.89")', proves='for a thing square to the camera the box is the thing (turned things come out wider)')
check.close('notice corner: deepest a story prop may stand to reach 0.70 (m)',
            g.reach_distance(0.70, notice['camera']['eye_height'], 0.43949, FILM, H), 5.95, 0.01,
            recorded='inventory "story must reach down the frame": 5.95 m at the notice corner (checker_formulas_check.py)', proves='repeats the reach sum')

# ------------------------------------------------------------------------------------------------ the Works (round 5)
shot = fixture('works', 'works-shot.json')
views = shot['views']


def works_camera(view, spot, fov=FILM):
    projector = fixture('works', views[view]['camera_file'])
    turn = g.camera_angles(g.camera_from_blender_quaternion([0, 0, 0], projector['blender']['rotation_quaternion_wxyz'], fov))['turn_degrees']
    return g.camera_from_turn(views[view][spot] or views[view]['plate'], turn, 0, 0, fov, W, H)


letters = {'w3 bank sign': ('w3', shot['bank']['sign'], 0.305), 'w3 No. 1 board': ('w3', shot['boards']['no-1-board'], 0.266),
           'w3 No. 2 board': ('w3', shot['boards']['no-2-board'], 0.25), 'w1 No. 1 board': ('w1', shot['boards']['no-1-board'], 0.266),
           'w2 No. 2 board': ('w2', shot['boards']['no-2-board'], 0.25), 'w1 PETROL': ('w1', shot['drums']['no-1-drum-petrol'], 0.097),
           'w2 PETROL': ('w2', shot['drums']['no-2-drum-petrol'], 0.097)}
for name, (view, point, letter) in letters.items():
    cam = works_camera(view, 'composed')
    pixels = g.size_in_pixels(cam, letter, g.project_point(cam, point)['depth'])
    check.close(f'Works letter height {name} (px)', round(pixels, 1), shot['letter_pixels'][name], 0.05,
                recorded='works-shot.json letter_pixels (written by assemble_works.py lines 1933-1936)',
                proves='repeats the build\'s own pinhole sum (consistency, not that 22 px is readable)')
check.close('W1 (level lane, eye 1.7 m): deepest a thing may stand to reach 0.70 (m)', g.reach_distance(0.70, 1.7, 0.5, FILM, H), 7.30, 0.005,
            recorded='skeptic (log 35); inventory "story must reach down the frame" (7.30 m at W1)', proves='repeats the reach sum')
w1 = works_camera('w1', 'composed')
man6 = next(m for m in shot['men_at_no_1'] if m['name'] == 'man-6')
landed = g.project_point(w1, man6['feet'])
check.close('W1: man 6 (the nearest, 7.42 m) feet land (down)', landed['down'], 0.696, 0.001, recorded='skeptic (log 35): 0.696',
            proves='the sum the skeptic used, from the composed camera')
box_bottom = next(m for m in shot['men_seen']['w1 composed'] if m['name'] == 'man-6')['film_frame_box'][3]
check.within('W1: man 6\'s feet sit just above his box bottom measured by Blender', box_bottom - landed['down'], 0.0, 0.015,
             recorded=f'works-shot.json men_seen "w1 composed" man-6 box bottom {box_bottom} (Blender, his whole model)',
             proves='a figure\'s feet predict where it reaches down the frame to within 0.015 (shoes and the model\'s box reach a little lower)')
check.true('W1: the round 4 critic\'s "nearest man about 0.72 down" is not what the camera gives',
           g.ground_point_down(7.6, 1.835 - 0.139, 0.5, FILM, H) < 0.70,
           details=f'a man at 7.6 m lands {g.ground_point_down(7.6, 1.835 - 0.139, 0.5, FILM, H):.3f} down',
           recorded='round4-result.json finding 3 and assemble_works.py comment ("about 0.72"); skeptic: 0.692',
           proves='the formula corrects a hand estimate (the 0.72 was the DIESEL drum, below)')
drum = shot['drums']['no-1-drum-diesel']
front = [drum[0], drum[1] - 0.607 / 2, drum[2]]   # props/index.json steel-drum-diesel: 0.607 m across the hoops
check.close('W1: DIESEL drum\'s front edge lands (down)', g.project_point(w1, front)['down'], 0.723, 0.002,
            recorded='skeptic (log 35): 0.723', proves='repeats the skeptic\'s sum')
check.close('W1: DIESEL drum against the round 5 rendered check (down)', g.project_point(w1, front)['down'], 0.72, 0.006,
            recorded='scratchpad redesign/round5-set/checks/final-w1-quiet/report.md rule 7: "diesel drum, reaching 0.72 down" (rendered)',
            proves='the sum predicts the rendered reach (to the report\'s two decimals) before anything is drawn')
round4 = g.camera_from_turn([-3.7, 10.2, 1.835], 0, 0, 0, FILM, W, H)
check.close('W1 from round 4\'s spot (y 10.2): the same drum lands (down)', g.project_point(round4, front)['down'], 0.653, 0.002,
            recorded='skeptic (log 35): 0.653; round 4 critic: the story sat 0.53 to 0.65 down (a fail)',
            proves='the 3 m move of round 5 is what lifted the reach past 0.70 (round 4 had other props, so this is the same drum seen from the old spot)')
check.close('a 0.23 m head at 6 m (px)', g.size_in_pixels(w1, 0.23, 6.0), 63.0, 0.5, recorded='skeptic (log 35): 63 px; plan 34 (6 m rule)', proves='repeats the size sum')
check.close('a 0.23 m head at 6.5 m (px)', g.size_in_pixels(w1, 0.23, 6.5), 58.0, 0.5, recorded='plan 34 T8 ("about 58")', proves='repeats the size sum')
check.close('distance where a 1.75 m man is a quarter of the height (m)', g.distance_for_size(w1, 1.75, 0.25 * H), 6.0, 0.02,
            recorded='plan 34 line 124 (6 m)', proves='the 6 m rule is exactly "a quarter of the frame"')
check.close('W3 eye needed for a queue tail 24.2 m away to reach 0.70 (m)', g.eye_needed(24.2, 0.70, 0.5, 0.14, FILM, H), 5.77, 0.01,
            recorded='design (log 35): 5.77 m; built 5.6 m (assemble_works.py W3_EYE)', proves='repeats the eye sum; the build chose 0.17 m lower')

# ------------------------------------------------------------------------------------------------ slides and the plate
limit_plate = g.slide_limit(2730, H, FILM, PLATE)
limit_painting = g.slide_limit(settings.value('frame.painting_returned_size_pixels')[1], H, FILM, PLATE)
check.close('slide limit from the plate\'s 2730 rows', limit_plate, 1.314, 0.001, recorded='plan 34 F13 (1.314)', proves='repeats the plan\'s sum')
check.close('slide limit from the painting\'s 2672 rows', limit_painting, 1.29, 0.005,
            recorded='skeptic (log 35): (2672/1920) x tan(30.2)/tan(32.2) = 1.29; people-test-paintings.json returned_size',
            proves='the limit now rests on what the painter returns, as the skeptic asked')
nc = fixture('notice-corner', 'notice-corner-shot.json')
end = g.camera_from_turn(nc['camera_end'], nc['yaw_degrees'], 0, 0, FILM, W, H)
start = g.moved_to(end, nc['camera_start'])
found = {f['name']: f for f in g.slide_magnifications(start, end, [(name, notice['groups'][name]['centre']) for name in ('pail', 'notice')])}
check.close('notice corner slide: the pail comes nearer (times)', found['pail']['magnification'], 1.45, 0.01,
            recorded='skeptic (log 35): pail 4.8/3.3 = 1.45', proves='the nearest painted prop magnifies most; the accepted notice corner is over the limit')
check.note(f'notice corner slide: the notice itself comes {found["notice"]["magnification"]:.3f} times nearer by the camera files '
           f'(the design and plan quoted 5.9 -> 4.4 m = 1.34 for an earlier layout)')
check.close('W1 slide 10.0 -> 8.8 m from the wall (times)', (22.0 - 12.0) / (22.0 - 13.2), 1.14, 0.005, recorded='plan 34 / round 5 (1.14x)', proves='repeats the ratio')
checkout_ratio = 3.1 / 2.4
check.true('checkout C1\'s planned slide 3.1 -> 2.4 m is on the limit (over it by under 1%)',
           0 < checkout_ratio / limit_painting - 1 <= settings.value('camera.slide_magnification_borderline_share'),
           details=f'{checkout_ratio:.3f} against {limit_painting:.3f}: {100 * (checkout_ratio / limit_painting - 1):.2f}% over',
           recorded='plan 34 (C1 3.1 to 2.4 m); skeptic (log 35): "sits right on the limit"', proves='the borderline band reports it as "judge it"')
turns = g.turn_allowance_degrees(40, 44, W, H)
check.close('turn allowance for a 44-degree plate over a 40-degree film lens (degrees each way)', turns['turn_each_way_degrees'], 1.0, 0.25,
            recorded='lesson 90 ("about 1 degree each side")', proves='the sum agrees with what log 29 saw by turning')
check.close('turn allowance for the house lenses (64.4 over 60.4)', g.turn_allowance_degrees(FILM, PLATE, W, H)['turn_each_way_degrees'], 1.38, 0.01,
            recorded='inventory "plate lens 4 degrees wider": about 1.4 degrees', proves='repeats the sum')
check.close('sideways step allowed with the nearest surface 4 m away (m)', g.sideways_allowance_metres(4, FILM, PLATE, W, H), 0.107, 0.001,
            recorded='design (log 35): 0.107 m; the notice corner used a 0.14 m sideways shift at about 4.4-4.9 m',
            proves='repeats the sum')
check.close('rule 4 clear overlap at 4.2 m in metres (15 px)', 15 * 4.2 / F, 0.038, 0.001, recorded='inventory rule 4 in metres (0.038 m)', proves='repeats the sum')
shift = 0.14 * F / (4.88 * W)   # what the notice corner's 0.14 m sideways slide (log 31) does to the notice, 4.88 m away
check.close('slide_for_screen_shift gives back the 0.14 m slide from the shift it causes (m)', g.slide_for_screen_shift(shift, 4.88, FILM, W, H), 0.14, 1e-9,
            recorded='log 31: the checker slid the camera 0.14 m right without turning (the critics worked out 0.12 m by hand)',
            proves='only that the inverse is exact (the shift itself was never recorded)')
check.close('parallax of a near thing (3.3 m) against the wall (4.9 m) for a 0.14 m sideways step (px)',
            g.parallax_sideways_pixels(0.14, 3.3, 4.9, FILM, H), F * 0.14 * (1 / 3.3 - 1 / 4.9), 1e-9, proves='repeats the formula (no project record)')

# ------------------------------------------------------------------------------------------------ camera files
projector = fixture('works', 'works-camera-w1.json')
from_blender = g.camera_from_blender_quaternion(projector['blender']['location'], projector['blender']['rotation_quaternion_wxyz'], PLATE, W, H)
from_three = g.camera_from_three(projector['position'], projector['quaternion'], PLATE, W, H)
a, b = g.project_point(from_blender, man6['feet']), g.project_point(from_three, man6['feet'])
check.close('a camera file read as Blender and as three.js lands a point in the same place', abs(a['across'] - b['across']) + abs(a['down'] - b['down']), 0, 1e-6,
            recorded='works-camera-w1.json (both forms written by assemble_works.py projector_json)', proves='the three.js conversion (x, z, -y) is right')
w4 = fixture('works', 'works-camera-w4.json')
turn4 = g.camera_angles(g.camera_from_blender_quaternion(w4['blender']['location'], w4['blender']['rotation_quaternion_wxyz'], PLATE))['turn_degrees']
check.close('W4 looks down the lane (turn, degrees)', abs(turn4), 180.0, 0.01, recorded='works-shot.json views.w4 faces "-y (down the lane)"', proves='turns are read right from a camera file')

# ------------------------------------------------------------------------------------------------ hold-out 1: checkout C1 (an indoor place the sums were not worked out from)
checkout = fixture('checkout-c1', 'checkout-c1-check10-facts.json')
cam = facts_camera(checkout)
errors = []
for light in checkout['lights']:
    if light['on_screen']:
        landed = g.project_point(cam, light['at'])
        errors.append(max(abs(landed['across'] - light['on_screen'][0]), abs(landed['down'] - light['on_screen'][1])))
check.within(f'checkout C1 (hold-out): {len(errors)} lights, largest difference from Blender (share of frame)', max(errors), 0, 0.00002,
             recorded='scratchpad redesign/round5-checkout/check10/facts/facts.json lights[].on_screen (copied 2026-10-16)',
             proves='project_point equals Blender\'s projection at a place nobody used to write these sums (points off the frame too)')
depth_errors = [abs(g.project_point(cam, info['centre'])['depth'] - info['distance']) for info in checkout['groups'].values()]
check.within('checkout C1 (hold-out): depth of every group against Blender (m)', max(depth_errors), 0, 0.001,
             recorded='same facts.json groups[].distance', proves='depth along the view matches Blender')
divider = checkout['groups']['divider']
front = [divider['centre'][0], divider['centre'][1] - divider['depth'] / 2, divider['bottom']]
eye_above_counter = checkout['camera']['at'][2] - divider['bottom']
reach = g.ground_point_down(front[1] - checkout['camera']['at'][1], eye_above_counter, 0.5, FILM, H)
check.close('checkout C1 (hold-out): the divider\'s front edge on the counter, reach sum (down)', reach, divider['screen_box_unclipped'][3], 0.0005,
            recorded='same facts.json groups.divider.screen_box_unclipped (0.7761)',
            proves='the reach sum works on a counter 0.885 m up when given the counter\'s height (the skeptic\'s interior point)')
results = fixture('checkout-c1', 'checkout-c1-check-results.json')
rendered = float(results['check10']['rule7_line'].split('reaching ')[1].split(' down')[0])
check.close('checkout C1 (hold-out): the same, against the rendered rule 7 reach (down)', reach, rendered, 0.006,
            recorded='scratchpad redesign/round5-checkout/check10/report.md: "divider, reaching 0.78 down the frame"',
            proves='a planned reach on a counter predicts the rendered one')
shot = fixture('checkout-c1', 'checkout-shot.json')
c1 = shot['views']['c1']
projector = fixture('checkout-c1', 'checkout-camera-c1.json')
end = g.camera_from_turn(c1['composed'], g.camera_angles(g.camera_from_blender_quaternion([0, 0, 0], projector['blender']['rotation_quaternion_wxyz'], FILM))['turn_degrees'],
                         0, 0, FILM, W, H)
start = g.moved_to(end, c1['plate'])
basket = g.slide_magnifications(start, end, [('basket', shot['spots']['basket'])])[0]
check.close('checkout C1 (hold-out): its real slide brings the basket nearer (times)', basket['magnification'], c1['slide']['nearer_times'], 0.001,
            recorded='checkout-shot.json views.c1.slide.nearer_times 1.292 (worked out by the checkout helper at 06:50, after the limit was set)',
            proves='our slide sum agrees with another helper\'s own at a place nobody derived the limit from')
bill = g.project_point(end, shot['spots']['bill-words'])
check.close('checkout C1 (hold-out): the bill\'s 0.1 m letters at the composed spot (px)', g.size_in_pixels(end, 0.1, bill['depth']), shot['letter_pixels']['bill big words'], 0.1,
            recorded='checkout-shot.json letter_pixels "bill big words" 55.0 (decisions: "letters 0.1 m tall")', proves='the size sum agrees with the checkout helper\'s')
plate_spot = g.moved_to(end, c1['plate'])
check.close('checkout C1 (hold-out): the same letters from the plate spot (px)', g.size_in_pixels(plate_spot, 0.1, g.project_point(plate_spot, shot['spots']['bill-words'])['depth']),
            shot['letter_pixels']['bill big words, plate spot'], 0.1, recorded='checkout-shot.json letter_pixels "bill big words, plate spot" 44.6')
nearest = min(g.slide_magnifications(start, end, [(name, point) for name, point in shot['spots'].items()]), key=lambda f: f['depth_end'])
check.note(f'checkout C1: judged at its nearest painted thing ({nearest["name"]}, {nearest["depth_end"]:.2f} m at the end) the 0.7 m slide brings it '
           f'{nearest["magnification"]:.3f} times nearer against the painting\'s {limit_painting:.3f}: '
           f'{100 * (nearest["magnification"] / limit_painting - 1):.1f}% over; the longest slide for it is '
           f'{g.longest_slide(nearest["depth_end"], limit_painting):.2f} m (the helper judged it at the basket: 1.292, 0.4% over)')
d_max = g.reach_distance(0.70, eye_above_counter, 0.5, FILM, H)
check.note(f'checkout C1: with the eye {eye_above_counter:.3f} m above the counter, a story thing reaches 0.70 down only within {d_max:.2f} m '
           f'(the divider stands {front[1] - checkout["camera"]["at"][1]:.2f} m away)')

# ------------------------------------------------------------------------------------------------ hold-out 2: the people test (a sloping street, a turned camera, eleven figures)
people = fixture('people-test', 'people-test-shot.json')
cam = g.camera_from_turn(people['camera'], people['yaw_degrees'], 0, 0, people['film_fov_degrees'], W, H)
gaps = []
for person in people['figures']:
    landed = g.project_point(cam, person['feet'])
    gaps.append(person['film_frame_box'][3] - landed['down'])
check.within('people test (hold-out): every figure\'s feet against its box bottom from Blender (smallest gap)', min(gaps), 0.0, 0.015,
             recorded='people-test-shot.json figures[].film_frame_box (assemble_people_test.py, Blender world_to_camera_view)',
             proves='feet land just above the model\'s lowest corner for all 11 figures, near (6.6 m) and far (55 m)')
check.within('people test (hold-out): the largest gap', max(gaps), 0.0, 0.015, recorded='same', proves='as above')
distances = [abs(math.hypot(p['feet'][0] - people['camera'][0], p['feet'][1] - people['camera'][1]) - p['distance_metres']) for p in people['figures']]
check.within('people test: ground distances recomputed from the feet (m)', max(distances), 0, 0.006, recorded='people-test-shot.json distance_metres',
             proves='only that the file is read right (the same subtraction)')
check.finish()
