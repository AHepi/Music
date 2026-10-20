# What this does (plain words): makes a NEW riveted-steel description from a seed number, so the generator can bake a new tile (or a bigger area) that is
# not a copy of the reference: how many straps, where they run, which panels get a diagonal brace, where the seam lines and rivets go, which tones the
# steel has and how heavy the rust is are all drawn at random from ranges measured on the reference (see sampler_model.json for the numbers and where
# they come from). The same seed always gives the same description. The parts that are NOT random: the picture of one rivet, the six shared strap-edge
# shading profiles and the colour ramps of the wear layers (they are the "style" of this surface, taken from the fitted description).
# numpy only (runs anywhere). Use:
#   import sample_description as sd ;  desc = sd.sample_description(seed=5, tile_multiple=1, model=sd.load_model())
#   python3 -I sample_description.py SEED OUT.json [--multiple 2]
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DESCRIPTION_FOLDER = os.path.join(PROC, 'recipes', 'metal', 'description')


def load_model(path=None):
    return json.load(open(path or os.path.join(DESCRIPTION_FOLDER, 'sampler_model.json')))


def rivets_along(rng, centre, angle_deg, length, spacing_range, clip=None):
    """Rivet positions along a bar's centre line, spaced at random between the two spacing numbers."""
    a = math.radians(angle_deg)
    d = np.array([math.cos(a), math.sin(a)])
    positions = []
    t = -length / 2 + rng.uniform(0.3, 1.0) * spacing_range[0]
    while t < length / 2:
        p = np.array(centre) + d * t
        positions.append(p)
        t += rng.uniform(*spacing_range)
    return positions


def sample_description(seed, tile_multiple=1, model=None, wear_amount=None):
    model = model or load_model()
    rng = np.random.default_rng(int(seed))
    m = int(tile_multiple)
    T = 1254.0 * m
    desc = {'format': 'metal_plate_v1', 'tile': T, 'maps': model['maps']}
    jitter = lambda base, spread: float(base + rng.uniform(-spread, spread))
    colour_jitter = lambda base, spread: [int(round(c + shift + rng.uniform(-1, 1))) for c, shift in zip(base, [rng.uniform(-spread, spread)] * 3)]
    plate = colour_jitter(model['plate'], 3)
    desc['plate'] = plate
    desc['plate_panels'] = []
    # ---- the straps: vertical ones (side a = the lit left edge), horizontal ones
    nv = int(rng.choice(model['vertical_count_choices'])) * m
    nh = int(rng.choice(model['horizontal_count_choices'])) * m
    x_off, y_off = rng.uniform(0, T / nv), rng.uniform(0, T / nh)
    xs = [(x_off + (i + 0.5 + rng.uniform(-0.28, 0.28)) * T / nv) % T for i in range(nv)]
    ys = [(y_off + (j + 0.5 + rng.uniform(-0.28, 0.28)) * T / nh) % T for j in range(nh)]
    xs.sort()
    ys.sort()
    vhalf = [float(np.clip(rng.normal(*model['vertical_half_width']), 56, 80)) for _ in xs]
    hhalf = [float(np.clip(rng.uniform(*model['horizontal_half_width_range']), 42, 86)) for _ in ys]
    bands, rivets = [], []
    profiles = dict(model['shared_profiles'])
    profiles.update(model['seam_profiles'])
    desc['profiles'] = profiles
    face = lambda: colour_jitter(model['face'], 3)
    order = 1
    # horizontal bars first (they sit under the vertical ones except where the model says otherwise), then verticals
    for y, h in zip(ys, hhalf):
        bands.append({'name': 'H', 'centre': [T / 2, y], 'angle': 0, 'length': T * 1.2, 'half': h, 'face': face(), 'a': 'lit_H', 'b': 'shade_H', 'order': order, 'clip': None, 'inner_a': None, 'inner_b': None})
        order += 1
    # panels = the cells between the straps (cell edges are the strap creases)
    cells = []
    for i in range(nv):
        for j in range(nh):
            x0 = xs[i] + vhalf[i]
            x1 = xs[(i + 1) % nv] - vhalf[(i + 1) % nv] + (T if i + 1 == nv else 0)
            y0 = ys[j] + hhalf[j]
            y1 = ys[(j + 1) % nh] - hhalf[(j + 1) % nh] + (T if j + 1 == nh else 0)
            if x1 - x0 > 120 and y1 - y0 > 120:
                cells.append((x0, y0, x1, y1))
    for (x0, y0, x1, y1) in cells:
        w, h = x1 - x0, y1 - y0
        aspect = w / h
        if w > 300 and h > 300 and 0.7 < aspect < 1.6 and rng.random() < model['brace_probability']:      # a brace only fits a roomy, roughly square panel (the reference's panels are 486 x 433 and 486 x 553)
            sign = 1.0 if rng.random() < model['brace_down_right_share'] else -1.0
            ang = float(np.clip(math.degrees(math.atan2(h, w)) * rng.uniform(1.0, 1.15), 44, 54)) * sign
            centre = [x0 + w * rng.uniform(0.42, 0.58), y0 + h * rng.uniform(0.42, 0.58)]
            half = float(np.clip(rng.normal(*model['brace_half_width']), 44, 56))
            length = math.hypot(w, h) * 1.1 + 90
            clip = [x0 - 45, y0 - 45, x1 + 45, y1 + 45]
            bands.append({'name': 'B', 'centre': centre, 'angle': ang, 'length': length, 'half': half, 'face': face(), 'a': 'lit_D', 'b': 'shade_D', 'order': 0, 'clip': clip, 'inner_a': None, 'inner_b': None})
            # rivets on the brace
            for p in rivets_along(rng, centre, ang, math.hypot(w, h) * 0.8, model['brace_rivet_spacing']):
                if x0 - 5 < p[0] < x1 + 5 and y0 - 5 < p[1] < y1 + 5:
                    rivets.append(p)
        elif rng.random() < model['seam_probability']:
            # a thin seam line across part of the panel
            if rng.random() < 0.6:
                y = y0 + h * rng.uniform(0.2, 0.8)
                xa = x0 + rng.uniform(0, 0.15) * w
                xb = xa + w * rng.uniform(0.35, 0.95)
                xb = min(xb, x1)
                bands.append({'name': 'S', 'centre': [(xa + xb) / 2, y], 'angle': 0, 'length': xb - xa, 'half': 2.5, 'face': [24, 22, 22], 'a': 'seam_soft', 'b': 'seam_lit', 'order': -1, 'clip': None, 'inner_a': 0, 'inner_b': 0})
            else:
                x = x0 + w * rng.uniform(0.2, 0.8)
                ya = y0 + rng.uniform(0, 0.15) * h
                yb = min(ya + h * rng.uniform(0.35, 0.95), y1)
                bands.append({'name': 'S', 'centre': [x, (ya + yb) / 2], 'angle': -90, 'length': yb - ya, 'half': 2.5, 'face': [24, 22, 22], 'a': 'seam_soft', 'b': 'seam_lit', 'order': -1, 'clip': None, 'inner_a': 0, 'inner_b': 0})
    for x, h in zip(xs, vhalf):
        bands.append({'name': 'V', 'centre': [x, T / 2], 'angle': -90, 'length': T * 1.2, 'half': h, 'face': face(), 'a': 'lit_V', 'b': 'shade_V', 'order': order, 'clip': None, 'inner_a': None, 'inner_b': None})
        order += 1
    # braces keep order 0 (under every strap); seams -1
    desc['bands'] = bands
    # ---- rivets on the straps
    rows_v = [(x, 0.0) for x in xs]
    for x in xs:
        for p in rivets_along(rng, [x, T / 2], 90, T, model['strap_rivet_spacing']):
            rivets.append(p + np.array([rng.normal(0, 1.5), 0]))
    for y, h in zip(ys, hhalf):
        rows = [0.0] if h < 70 else [-0.45 * h, 0.45 * h]
        for off in rows:
            for p in rivets_along(rng, [T / 2, y + off], 0, T, model['strap_rivet_spacing']):
                rivets.append(p + np.array([0, rng.normal(0, 1.5)]))
    # rivets at crossings
    for x in xs:
        for y in ys:
            if rng.random() < 0.8:
                rivets.append(np.array([x + rng.normal(0, 2), y + rng.normal(0, 2)]))
    # thin out rivets that sit on top of each other
    kept = []
    for p in rivets:
        q = np.array([p[0] % T, p[1] % T])
        if all(min(abs(q[0] - k[0]), T - abs(q[0] - k[0])) ** 2 + min(abs(q[1] - k[1]), T - abs(q[1] - k[1])) ** 2 > 52 ** 2 for k in kept):
            kept.append(q)
    desc['rivet'] = model['rivet']
    desc['rivets'] = [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in kept]
    # ---- the wear: the fitted layers, new seeds, a little change in scale and in how much rust there is
    proc = json.loads(json.dumps(model['procedural']))
    for i, layer in enumerate(proc['layers']):
        for part in ('fine', 'mod'):
            if part in layer:
                layer[part]['seed'] = int(rng.integers(1, 10000))
                for key in ('scale_u', 'scale_v'):
                    layer[part][key] = round(layer[part][key] * rng.uniform(0.88, 1.12), 2)
        if i > 0:
            layer['offset'] = round(layer.get('offset', 0.0) + (rng.uniform(-0.05, 0.05) if wear_amount is None else wear_amount), 3)
    proc['grain']['seed'] = int(rng.integers(1, 1000))
    desc['procedural'] = proc
    return desc


if __name__ == '__main__':
    seed = int(sys.argv[1])
    multiple = int(sys.argv[sys.argv.index('--multiple') + 1]) if '--multiple' in sys.argv else 1
    d = sample_description(seed, multiple)
    json.dump(d, open(sys.argv[2], 'w'), separators=(',', ':'))
    print('written', sys.argv[2], os.path.getsize(sys.argv[2]), 'bytes;', len(d['bands']), 'bars,', len(d['rivets']), 'rivets')
