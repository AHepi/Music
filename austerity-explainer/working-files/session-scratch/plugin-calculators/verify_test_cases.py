"""Read-only check of the test cases proposed for the plugin's calculators (log 35 design notes).
Every number printed here is a known case from the project that a calculator must reproduce. Pure geometry and
arithmetic; reads works-shot.json and the round 5 smoke settings; changes no file.
Use: python3 -I verify_test_cases.py
"""
import json
import math

KIT = '/home/user/Music/austerity-explainer/film-kit'
SCRATCH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
W, H = 1080, 1920
FILM_V, PLATE_V = 60.4, 64.4


def focal(v_deg, h=H):
    return (h / 2) / math.tan(math.radians(v_deg) / 2)


def hfov(v_deg, aspect=W / H):
    return math.degrees(2 * math.atan(math.tan(math.radians(v_deg) / 2) * aspect))


F = focal(FILM_V)
print(f'[geometry] focal at {FILM_V} deg on 1920 high: {F:.1f} px (expect 1649.4); plate focal on 2730 high at {PLATE_V}: '
      f'{focal(PLATE_V, 2730):.0f} px (expect 2168)')


def project_level(cam, p, f=F, w=W, h=H, yaw_deg=0.0, facing=+1):
    """level camera looking along facing*y (Blender), turned yaw left; returns (across, down, depth)"""
    dx, dy, dz = p[0] - cam[0], (p[1] - cam[1]) * facing, p[2] - cam[2]
    if facing < 0:
        dx = -dx
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    depth = dy * c - dx * s
    side = dx * c + dy * s
    return 0.5 + f * side / (depth * w), 0.5 - f * dz / (depth * h), depth


shot = json.load(open(f'{KIT}/assets/models/inflation-chapter-2-newcomers/works/works-shot.json'))
views = shot['views']
print('\n[lettering] letter heights in px at each composed spot (works-shot.json letter_pixels)')
cases = [('w3 bank sign', 'w3', 'plate', shot['bank']['sign'], 0.305, 29.0),
         ('w3 No. 1 board', 'w3', 'plate', shot['boards']['no-1-board'], 0.266, 14.7),
         ('w3 No. 2 board', 'w3', 'plate', shot['boards']['no-2-board'], 0.25, 13.8),
         ('w1 No. 1 board', 'w1', 'composed', shot['boards']['no-1-board'], 0.266, 50.0),
         ('w2 No. 2 board', 'w2', 'composed', shot['boards']['no-2-board'], 0.25, 47.0),
         ('w1 PETROL', 'w1', 'composed', shot['drums']['no-1-drum-petrol'], 0.097, 22.1),
         ('w2 PETROL', 'w2', 'composed', shot['drums']['no-2-drum-petrol'], 0.097, 22.1)]
for name, view, spot, at, letter_m, expect in cases:
    cam = views[view][spot]
    _, _, d = project_level(cam, at)
    print(f'  {name:16s} depth {d:6.2f} m  px {letter_m * F / d:5.1f}  (works-shot.json {expect})')
print(f'  WAGES 0.018 m at 6 m: {0.018 * F / 6:.1f} px (round 2: about 5 px); 25 px needs {25 * 6 / F:.3f} m letters at 6 m')
print(f'  letter height for 18 px at 4.4 m (notice corner end): {18 * 4.4 / F * 100:.1f} cm')

print('\n[figures] W1 composed: feet down and head px (works-shot.json men_seen gives box bottoms 0.704/0.700/0.699)')
cam = views['w1']['composed']
for m in shot['men_at_no_1']:
    a, dn, d = project_level(cam, m['feet'])
    print(f'  {m["name"]}: depth {d:5.2f}  feet {dn:.3f} down  head {0.23 * F / d:4.1f} px  figure {m["height_metres"] * F / d:5.0f} px')
for d in (6.0, 6.5, 15.8, 17.0, 19.0):
    print(f'  head at {d:4.1f} m: {0.23 * F / d:5.1f} px')
print(f'  distance where a head is 24 px: {0.23 * F / 24:.1f} m; nearest for a 1.75 m man to be 0.25 of height: {1.75 * F / (0.25 * H):.2f} m')

print('\n[shot planner] reach, eye height, slide, plate')
for eye, ground, target, label in ((1.7, 0.0, 0.70, 'level lane, eye 1.7, feet on the road'),
                                   (1.835 - 0.139, 0.0, 0.70, 'W1 pavement eye over a man on the pavement'),
                                   (1.7, 0.0, 0.72, 'round 4 target 0.72')):
    print(f'  {label}: d_max for {target} down = {F * eye / ((target - 0.5) * H):.2f} m')
d_tail = 24.2
print(f'  W3 eye needed for a tail 24.2 m away at 0.70 down: {0.14 + 0.2 * H * d_tail / F:.2f} m above lane (used 5.6)')
ratio = (2730 / 1920) * math.tan(math.radians(FILM_V) / 2) / math.tan(math.radians(PLATE_V) / 2)
print(f'  slide magnification limit: {ratio:.3f}; W1 10.0 -> 8.8 m = {10.0 / 8.8:.2f}; notice corner 5.9 -> 4.4 = {5.9 / 4.4:.2f}; '
      f'checkout 3.1 -> 2.4 = {3.1 / 2.4:.2f}; L_max at d_end 8.8 = {8.8 * (ratio - 1):.2f} m')
for pv, fv in ((44, 40), (64.4, 60.4)):
    print(f'  turn allowance plate {pv} / film {fv}: {(hfov(pv) - hfov(fv)) / 2:.2f} deg each side; tilt {(pv - fv) / 2:.1f} deg')
tx = lambda v: math.tan(math.radians(v) / 2) * W / H
print(f'  sideways slide limit for nearest surface 4 m: {4 * (tx(PLATE_V) - tx(FILM_V)):.3f} m')
print(f'  one degree of turn moves things {F * math.pi / 180 / W:.4f} of the width')
yaw = math.degrees(math.atan((0.684 - 0.5) * W / F))
print(f'  turn for meeting point 0.684 across: {yaw:.2f} deg (notice corner 6.87)')
print(f'  notice corner subject share: notice 1.18 x 0.83 m? use board scale 1.11; share formula A*(f/d)^2/(W*H)')

print('\n[chimney tops vs title band] down of each chimney top from W1 composed and W3')
for v, spot in (('w1', 'composed'), ('w3', 'plate')):
    cam = views[v][spot]
    for name, top in shot['chimney_tops'].items():
        a, dn, d = project_level(cam, top)
        print(f'  {v} {name}: across {a:.3f} down {dn:.3f}')

print('\n[smoke] on-screen travel of No. 2 chimney a plume in W3 plate for two winds (round 5 heavy settings)')
settings = json.load(open(f'{SCRATCH}/redesign/round5-pages/tools/smoke-final.json'))
heavy = settings['kinds']['heavy']
tan_half = math.tan(math.radians(FILM_V) / 2)


def trace(wind, cam, top_b, kind, ages):
    wx, wy, wz = wind
    n = math.sqrt(wx * wx + wy * wy + wz * wz); wx, wy, wz = wx / n, wy / n, wz / n
    top = (top_b[0], top_b[2], -top_b[1])
    out = []
    for age in ages:
        k = age / kind['life']
        climb = kind['rise'] * k ** 0.75; blown = kind['drift'] * k ** 1.25
        X, Y, Z = top[0] + wx * blown, top[1] + 0.3 + climb + wy * blown, top[2] + wz * blown
        ahead = -Z - cam[1]
        sx = 0.5 + 0.5 * (X - cam[0]) / (ahead * tan_half * W / H)
        sy = 0.5 - 0.5 * (Y - cam[2]) / (ahead * tan_half)
        strength = kind['opacity'] * min(1, age / 0.2) * (1 - k) ** kind.get('fade', 1.0)
        out.append((age, sx, sy, strength))
    return out


ages = [i * 0.25 for i in range(int(heavy['life'] / 0.25))]
for label, wind in (('round 4 wind (0.3,-0.05,-0.95)', (0.3, -0.05, -0.95)), ('round 5 wind (-0.85,-0.12,-0.5)', settings['wind'])):
    tr = trace(wind, views['w3']['plate'], shot['chimney_tops']['no-2-chimney-a-top'], heavy, ages)
    visible = [t for t in tr if t[3] >= 0.1]
    span = max(t[1] for t in visible) - min(t[1] for t in visible)
    x_at_fade = visible[-1][1]
    print(f'  {label}: travel while strength >= 0.1 is {span:.3f} of width; last visible across {x_at_fade:.3f}; '
          f'centre down {min(t[2] for t in visible):.3f}-{max(t[2] for t in visible):.3f}')
# perpendicular wind from the view direction (+y Blender = -z three.js): cross(view, up)
print('  perpendicular to a +y view in three.js axes: (+-1, 0, 0); round 5 chose (-0.85, -0.12, -0.5)')

print('\n[money]')
mp = lambda w, h: w * h / 1e6
p1 = 4.8 * (mp(1504, 2672) + mp(1536, 2730) + mp(768, 1368))
p2 = 4.8 * (mp(1504, 2672) + mp(1536, 2730))
print(f'  people test at 4.8 c/MP: painting {p1:.1f} c, behind {p2:.1f} c, total {p1 + p2:.1f} c (ledger: about 85 c)')
print(f'  style picture at full plate size instead of 1 MP would add {2.4 * (mp(1536, 2730) - mp(768, 1368)):.1f} c at 2.4 c/MP (plan: about 7 c)')
print(f'  ElevenLabs: 6,300 characters x 0.000175 = US${6300 * 0.000175:.2f} (plan: about 1.10); 4,300 credits = US${4300 * 0.000175:.2f} (bill: about 0.75)')
print(f'  chapter 1 old prices: 47 pictures for 2.55 -> {2.55 / 47 * 100:.1f} c each')

print('\n[filming time]')
print(f'  pages 3-5: 2,283 frames x 1.4 s = {2283 * 1.4 / 60:.0f} min (round 4: 53); x 1.83 = {2283 * 1.83 / 60:.0f} min (round 3: 70)')
print(f'  chapter 1: 6,641 frames x 0.85 s = {6641 * 0.85 / 60:.0f} min one worker (Workflows: about 95; log 13 measured about 80)')
for spf, load in ((1.2, 30), (0.85, 3), (12, 5), (1.4, 45)):
    pf = max(60, min(math.ceil(load / (0.10 * spf)), math.floor(900 / spf)))
    print(f'  piece frames for {spf} s/frame, {load} s load: {pf} (loss at a stop <= {pf * spf / 60:.1f} min)')
print(f'  stretch frames under 6,600 s at 1.4 s/frame, 2 workers x 1.17: {int(6600 * 1.17 / 1.4)}')

print('\n[light]')
print(f'  lantern start watts = 200 x (0.15/1.1)^2 = {200 * (0.15 / 1.1) ** 2:.1f} W (hand: 60 -> 1 W)')
e = lambda c: 1 - math.cos(math.radians(c) / 2)
print(f'  same light per area when a 20 deg 200 W cone widens to 50 deg: {200 * e(50) / e(20):.0f} W (so 700 W at 50 deg was {700 / (200 * e(50) / e(20)):.1f}x too strong)')
print(f'  shadow resolution scale at 1536 wide: {min(1, 1080 / 1536):.3f}')

print('\n[sound]')
for secs in (180.0, 407.0):
    kbps = 28 * 8000 * 0.97 / secs - 128
    print(f'  sendable video kbps for {secs:.0f} s: {kbps:.0f}; size {(kbps + 128) * secs / 8000:.1f} MB')
