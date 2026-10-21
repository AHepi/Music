# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Draws the RUBBISH MASK of the street as ONE flat picture seen from above (a "plan"): a map of where rubbish gathers. It is a plain picture, so a person can open it in
# any paint program and brush more rubbish on, or take it away. One dot is 2 cm of street; the picture covers across the street x = -4.5 to 4.5 m and along it
# y = -12 to 72 m (450 x 4200 dots). The same map can be laid on the road, the pavements, the gutters and the kerbs in Blender (by their world position), and on the whole-street
# second texture coordinates of the .glb.
# THREE CHANNELS (colours of the picture), each 0 = none, 1 = most:
#   red    "dirt"   a thin film of coal dust, ash and soot over the ground colour: widest and softest; strongest in the gutter, along the foot of the house walls, at doorsteps,
#                   round the foot of rain pipes and lamp posts, and (lockout file only) round the fire drum
#   green  "pieces" where small separate bits of rubbish lie (cinders, paper, straw, leaves, a crock): narrower and patchier than dirt; used to decide where to scatter pieces
#   blue   "mud"    damp brown muck: the very bottom of the gutter, below rain pipes, by the doorsteps
# HOW (the rules, each one a rule of real streets, see the study note section 6):
#   * the gutter line gets the most (water carries muck to it and leaves it when it dries), the kerb foot on the pavement side less;
#   * the foot of a house wall gets a strip about 0.7 m wide, strongest at the wall itself (wind and sweeping push things against it; rain splash);
#   * doorsteps (the door's position from the plan probe) get a blob: ash is tipped out there and boots bring mud;
#   * the foot of each rain pipe, and each lamp post, gets a small blob;
#   * every household is a little different: each cottage's stretch of the street is made 0.6 to 1.3 times as dirty (fixed random numbers);
#   * everything is broken into patches by smooth noise, so nothing is a clean stripe.
# Input: work/plan_street.json (and work/plan_lockout.json for the lockout props), written by b07_probe_street_plan.py. Output: work/rubbish_plan_mask.png (the street alone),
# work/rubbish_plan_mask_lockout.png (the same plus the lockout shot's props: the fire drum, the coal slack heap, the dustbins, the sacks, the handcart),
# work/rubbish_plan_check.jpg (a look at it), work/rubbish_plan_numbers.json (the share of the ground each channel covers).
# Run: python3 -I b10_rubbish_plan_mask.py
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..', 'work'))
X0, X1, Y0, Y1, DOT = -4.5, 4.5, -12.0, 72.0, 0.02
WIDTH, HEIGHT = int(round((X1 - X0) / DOT)), int(round((Y1 - Y0) / DOT))
# the street's numbers (from the plan probe; the defaults are the values of the street file)
GUTTER_CENTRE = 2.3          # metres from the street's middle line to the middle of the gutter channel
KERB_FOOT = 2.8
WALL_X = 4.4                 # metres from the middle line to the foot of the house walls (replaced by the probe's answer when there is one)
GAINS = dict(gutter=0.9, kerb=0.45, wall_foot=0.7, doorstep=1.0, pipe=0.85, lamp=0.5, drum=1.0)
rng = np.random.default_rng(1926)


def smooth_noise(scale_m, seed, octaves=3):
    """Smooth random patches, 0..1, scale_m = size of the biggest patches in metres."""
    r = np.random.default_rng(seed)
    total = np.zeros((HEIGHT, WIDTH), np.float32)
    amplitude, norm = 1.0, 0.0
    for o in range(octaves):
        cells_x = max(2, int(np.ceil((X1 - X0) / (scale_m / 2 ** o))) + 2)
        cells_y = max(2, int(np.ceil((Y1 - Y0) / (scale_m / 2 ** o))) + 2)
        small = r.random((cells_y, cells_x)).astype(np.float32)
        total += amplitude * cv2.resize(small, (WIDTH, HEIGHT), interpolation=cv2.INTER_CUBIC)
        norm += amplitude
        amplitude *= 0.5
    total /= norm
    return np.clip((total - 0.5) * 2.2 + 0.5, 0, 1)


def build(plan_street, plan_lockout=None):
    global WALL_X
    xs = (np.arange(WIDTH) * DOT + X0 + DOT / 2).astype(np.float32)[None, :]
    ys = (np.arange(HEIGHT) * DOT + Y0 + DOT / 2).astype(np.float32)[:, None]
    ax = np.abs(xs) + 0 * ys
    # the wall line from the probe's rays (median of the hits)
    hits = [h['x'] for side in plan_street.get('wall_rays', {}).values() for h in side if h.get('hit') and h['x'] is not None]
    if hits:
        WALL_X = float(np.median(np.abs(hits)))
    print('wall line at |x| =', round(WALL_X, 3), '(from', len(hits), 'rays)')
    gutter = np.exp(-((ax - GUTTER_CENTRE) / 0.28) ** 2)
    road_side = 1 - np.clip((GUTTER_CENTRE - 0.15 - ax) / 0.5, 0, 1)         # fades toward the middle of the road
    gutter = gutter * np.where(ax < GUTTER_CENTRE, road_side, 1.0)
    kerb = np.exp(-((ax - KERB_FOOT) / 0.25) ** 2) * (ax > 2.6)
    wall_d = np.clip(WALL_X - ax, 0, None)
    wall_foot = np.exp(-wall_d / 0.28) * (ax > 3.2)
    dirt = np.maximum.reduce([GAINS['gutter'] * gutter, GAINS['kerb'] * kerb, GAINS['wall_foot'] * wall_foot]).astype(np.float32)
    mud = (0.9 * np.exp(-((ax - (GUTTER_CENTRE + 0.1)) / 0.14) ** 2)).astype(np.float32)
    household = np.ones((HEIGHT, 1), np.float32)
    door_ys = sorted(set(round(d['y'], 1) for d in plan_street.get('doors', [])))
    # one factor per house length (4.5 m) along the street, the same on both sides
    for k in range(int((Y1 - Y0) / 4.5) + 1):
        y_start = Y0 + k * 4.5
        a, b = int((y_start - Y0) / DOT), int((y_start + 4.5 - Y0) / DOT)
        household[a:b] = rng.uniform(0.6, 1.3)
    blobs = np.zeros((HEIGHT, WIDTH), np.float32)
    mud_blobs = np.zeros((HEIGHT, WIDTH), np.float32)
    for d in plan_street.get('doors', []):
        side = 1.0 if d['x'] > 0 else -1.0
        cx = side * (WALL_X - 0.35)
        blobs = np.maximum(blobs, GAINS['doorstep'] * np.exp(-(((xs - cx) / 0.5) ** 2 + ((ys - d['y']) / 0.6) ** 2)))
        mud_blobs = np.maximum(mud_blobs, 0.6 * np.exp(-(((xs - cx) / 0.45) ** 2 + ((ys - d['y']) / 0.5) ** 2)))
    # rain pipes: the probe lists the lowest vertices of each cottage's rain pipe (may be empty): otherwise one pipe at each party wall (every 9 m, a pair of cottages shares one)
    pipe_points = []
    for p in plan_street.get('rainwater_low_vertices', []):
        pass
    for k in range(int((Y1 - Y0) / 9.0) + 1):
        y_pipe = Y0 + k * 9.0 + 0.0
        for side in (-1.0, 1.0):
            pipe_points.append((side * (WALL_X - 0.12), y_pipe))
    for cx, cy in pipe_points:
        blobs = np.maximum(blobs, GAINS['pipe'] * np.exp(-(((xs - cx) / 0.32) ** 2 + ((ys - cy) / 0.32) ** 2)))
        mud_blobs = np.maximum(mud_blobs, 0.8 * np.exp(-(((xs - cx) / 0.3) ** 2 + ((ys - cy) / 0.3) ** 2)))
    lamp_list = plan_street.get('lamps') or [dict(x=3.03, y=11.0), dict(x=-3.03, y=25.0), dict(x=3.03, y=39.0), dict(x=-3.03, y=53.0), dict(x=3.03, y=64.5)]   # the gas lamp posts (from the light positions of the street file)
    for lamp in lamp_list:
        blobs = np.maximum(blobs, GAINS['lamp'] * np.exp(-(((xs - lamp['x']) / 0.35) ** 2 + ((ys - lamp['y']) / 0.35) ** 2)))
    drum = None
    prop_dirt = np.zeros((HEIGHT, WIDTH), np.float32)
    prop_pieces = np.zeros((HEIGHT, WIDTH), np.float32)
    if plan_lockout:
        props = plan_lockout.get('props', {})

        def centre(name):
            pr = props.get(name)
            return (0.5 * (pr['x'][0] + pr['x'][1]), 0.5 * (pr['y'][0] + pr['y'][1])) if pr else None

        def blob(c, sx, sy):
            return np.exp(-(((xs - c[0]) / sx) ** 2 + ((ys - c[1]) / sy) ** 2)).astype(np.float32)

        drum = centre('barrel_stove')
        if drum:       # the fire drum: ash, cinders, burnt bits all round it (the film's older painting had a soot-and-ash ring there)
            prop_dirt = np.maximum(prop_dirt, GAINS['drum'] * blob(drum, 0.85, 0.85))
            prop_pieces = np.maximum(prop_pieces, 1.0 * blob(drum, 0.95, 0.95))
        slack = centre('slack-heap')
        if slack:      # the coal slack heap: slack spilled round its foot
            prop_dirt = np.maximum(prop_dirt, 1.0 * blob(slack, 0.55, 0.45))
            prop_pieces = np.maximum(prop_pieces, 0.9 * blob(slack, 0.6, 0.5))
        for name in ('metal_trash_can', 'metal_trash_can_rust'):
            c = centre(name)
            if c:      # dustbins against the wall: ash and scraps have spilled at their foot
                prop_dirt = np.maximum(prop_dirt, 0.8 * blob(c, 0.55, 0.55))
                prop_pieces = np.maximum(prop_pieces, 1.0 * blob(c, 0.6, 0.6))
        for name in ('sack0', 'sack1'):
            c = centre(name)
            if c:      # coal sacks: dust
                prop_dirt = np.maximum(prop_dirt, 0.6 * blob(c, 0.6, 0.5))
        c = centre('cart-body')
        if c:          # the handcart: bits dropped round the wheels
            prop_dirt = np.maximum(prop_dirt, 0.5 * blob(c, 0.9, 1.3))
            prop_pieces = np.maximum(prop_pieces, 0.6 * blob(c, 0.9, 1.3))
        print('lockout props used; fire drum at', drum)
    drum_zone = prop_dirt
    patches = 0.35 + 1.0 * smooth_noise(1.6, 11) * 0.8
    dirt = np.maximum(dirt * household, np.maximum(blobs * household, drum_zone)) * patches
    dirt = np.clip(dirt, 0, 1)
    pieces_patch = smooth_noise(0.7, 23, octaves=2)
    pieces = np.clip((dirt ** 1.3) * np.clip((pieces_patch - 0.35) * 3.0, 0, 1) * 1.4, 0, 1)
    pieces = np.maximum(pieces, np.clip(prop_pieces * np.clip((pieces_patch - 0.15) * 3, 0, 1), 0, 1))
    mud = np.clip(np.maximum(mud * household, mud_blobs) * (0.4 + 0.9 * smooth_noise(1.1, 37)) * (np.clip(dirt * 1.4, 0, 1) > 0.05), 0, 1)
    return dirt, pieces, mud, drum


if __name__ == '__main__':
    plan_street = json.load(open(os.path.join(WORK, 'plan_street.json')))
    lockout_path = os.path.join(WORK, 'plan_lockout.json')
    plan_lockout = json.load(open(lockout_path)) if os.path.exists(lockout_path) else None
    dirt, pieces, mud, drum = build(plan_street, None)
    dirt_l, pieces_l, mud_l, drum_l = build(plan_street, plan_lockout) if plan_lockout else (dirt, pieces, mud, None)
    # the picture: row 0 is the HIGH y end in a normal image, but Blender image rows start at the BOTTOM (y = -12): write it with row 0 = y = -12 flipped for the file
    rgb = np.stack([dirt, pieces, mud], axis=-1)
    file_image = np.flipud((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    cv2.imwrite(os.path.join(WORK, 'rubbish_plan_mask.png'), file_image[..., ::-1])
    rgb_l = np.stack([dirt_l, pieces_l, mud_l], axis=-1)
    cv2.imwrite(os.path.join(WORK, 'rubbish_plan_mask_lockout.png'), np.flipud((np.clip(rgb_l, 0, 1) * 255).astype(np.uint8))[..., ::-1])
    numbers = dict(size=[WIDTH, HEIGHT], dot_m=DOT, x_range=[X0, X1], y_range=[Y0, Y1], wall_x=WALL_X,
                   share_over_0p3=dict(dirt=float((dirt > 0.3).mean()), pieces=float((pieces > 0.3).mean()), mud=float((mud > 0.3).mean())),
                   mean=dict(dirt=float(dirt.mean()), pieces=float(pieces.mean()), mud=float(mud.mean())), drum=drum)
    json.dump(numbers, open(os.path.join(WORK, 'rubbish_plan_numbers.json'), 'w'), indent=1)
    print(json.dumps(numbers, indent=1))
    # a look: the first 30 m of the street, rotated so the street runs left to right, as three stacked strips (dirt, pieces, mud) in colour
    view = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    strip = np.rot90(view[int((0 - Y0) / DOT):int((30 - Y0) / DOT)], k=1)     # y runs along the picture's width
    cv2.imwrite(os.path.join(WORK, 'rubbish_plan_check.jpg'), cv2.resize(strip[..., ::-1], (1500, 225), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 90])
