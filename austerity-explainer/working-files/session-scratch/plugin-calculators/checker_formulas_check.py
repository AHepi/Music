"""Checks the closed-form camera formulas proposed for a pre-build camera solver against what shot_facts.py measured
for the notice corner (log 31 final frame) and against the numbers quoted in logs 30 to 34. Read only; prints a table.

Formulas (level camera, sensor fit vertical, frame W x H, vertical lens angle V, turn psi left of +y, street direction
(0, 1, s) with the ground rising at the same slope s):
  f            = (H / 2) / tan(V / 2)                          focal length in pixels
  u_meet       = 0.5 + f * tan(psi) / W                         where the lines meet, across
  v_meet       = 0.5 - f * s / (H * cos(psi))                   where the lines meet, down (level camera)
  m_per_px(d)  = d / f                                          metres per pixel at depth d
  v_foot(d)    = v_meet + f * eye / (d * H)                     a point on the ground at depth d (eye above the camera's ground)
  d_reach(r)   = f * eye / ((r - v_meet) * H)                   deepest a ground prop's front foot may stand to reach r down
  turn per deg = f * (pi / 180) / W                             share of the width one degree of turn moves things near the middle
  slide limit  = (plate_H / film_H) * tan(film_V / 2) / tan(plate_V / 2)   plate pixels per film pixel at the plate's spot
  head_px(d)   = f * 0.23 / d                                    a 0.23 m head at depth d
  figure_px(d) = f * 1.75 / d
"""
import json
import math
import sys

FACTS = sys.argv[1] if len(sys.argv) > 1 else ('/home/user/Music/austerity-explainer/experiments/31 Notice corner - working files/'
                                                'final frame measurements/facts.json')
facts = json.load(open(FACTS))
W, H = facts['size']
cam = facts['camera']
V = math.radians(cam['vertical_fov_degrees'])
psi = math.radians(cam['turn_degrees'])
f = (H / 2) / math.tan(V / 2)
s = 0.069927
eye = cam['eye_height']

u_meet = 0.5 + f * math.tan(psi) / W
v_meet = 0.5 - f * s / (H * math.cos(psi))
print(f'focal {f:.1f} px')
print(f'where the lines meet: formula {u_meet:.4f}, {v_meet:.4f}; shot_facts {facts["lines_meet"]["street"]}')
for g in ('notice', 'drum', 'pail', 'handcart'):
    info = facts['groups'][g]
    print(f'{g:9s} metres per pixel: formula {info["distance"] / f:.6f}; shot_facts {info["metres_per_pixel"]}')
pail = facts['groups']['pail']
front = pail['distance'] - pail['depth'] / 2
eye_over_pail_ground = cam['at'][2] - pail['bottom']
print(f'pail front foot down: formula (eye over its own ground) {0.5 + f * eye_over_pail_ground / (front * H):.3f}; '
      f'formula (v_meet + f*eye/(d*H)) {v_meet + f * eye / (front * H):.3f}; shot_facts unclipped bottom {pail["screen_box_unclipped"][3]}')
print(f'one degree of turn moves things {f * math.pi / 180 / W:.4f} of the width (07 Composing a shot says about 0.027 at 60 degrees)')
for reach, vm, e, label in ((0.70, v_meet, eye, 'notice corner'), (0.70, 0.5, 1.7, 'Works W1 (level lane, eye 1.7)')):
    print(f'{label}: a ground story prop must stand within {f * e / ((reach - vm) * H):.2f} m to reach {reach} down')
print(f'Works W1 nearest man at 7.6 m: feet {0.5 + f * 1.7 / (7.6 * H):.3f} down (critic round 4 said about 0.72)')
plate_ratio = (2730 / 1920) * math.tan(math.radians(60.4) / 2) / math.tan(math.radians(64.4) / 2)
print(f'slide limit (plate 1536 x 2730 at 64.4 degrees, film 1080 x 1920 at 60.4): {plate_ratio:.3f} (plan F13: about 1.3)')
for d in (6.0, 6.5, 16.0, 19.0, 50.0):
    print(f'at {d:5.1f} m: head {f * 0.23 / d:5.1f} px, figure {f * 1.75 / d:6.1f} px ({f * 1.75 / d / H:.2f} of the height)')
for d in (3.3, 4.2, 4.9):
    print(f'at {d} m: rule 4 overlap 15 px = {15 * d / f:.3f} m, gap 18 px = {18 * d / f:.3f} m; rule 3 box 0.40 x 0.50 = '
          f'{0.40 * W * d / f:.2f} m x {0.50 * H * d / f:.2f} m; rule 1 tolerance 0.03 of width = {0.03 * W * d / f:.3f} m')
# where a work prop of height h stands for its middle to fall in the 0.45 to 0.62 band
for h in (0.6, 1.1):
    near = f * (eye - h / 2) / ((0.62 - v_meet) * H)
    far = f * (eye - h / 2) / ((0.47 - v_meet) * H) if 0.47 > v_meet else float('inf')
    print(f'work prop {h} m tall: middle inside 0.47 to 0.62 down when it stands {near:.1f} to {far:.1f} m away')
