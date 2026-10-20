# What this does (plain words): the MUD SAMPLER. sample_description(seed) invents a NEW mud description (a small dictionary) of the same kind as the reference: wheel ruts that
# cross and bend (some in pairs), ragged blue-grey puddles with flat water tones, many dark angular stones of every size (with a lit face and a shaded face), and crumbly
# ground clods whose colours follow the ruts. Every number is drawn from the spreads measured on the reference (analysis/fit_sampler_stats.py, fit_ground_model.py, copied into
# generator/fitted_distributions_mud.json); nothing of the reference picture is used. Same seed = same description; another seed = a different tile.
# Options let a caller change the KIND of surface by changing numbers only (see the transfer test): palette (list of [r,g,b]), tones (a dict naming which palette entries play
# which part), counts (stone_scale, puddle_scale, rut_scale, clod_count), tile (design size in dots: a bigger tile holds proportionally more of everything).
# Plain numpy (+ OpenCV only to find the outline of a puddle blob); runs outside Blender. Use:  import sampler; d = sampler.sample_description(7)
import json
import math
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
import mud_layers as ml

MAPS = {'height': {'grey_low': 20.0, 'grey_high': 128.0, 'blur': 0.5, 'mode': 'from_colour'}, 'normal': {'strength': 9}}


def load_distributions(path=None):
    return json.load(open(path or os.path.join(HERE, 'fitted_distributions_mud.json')))


def jitter_palette(rgb, rng, amount):
    """All colours get lighter/darker together by about `amount` steps and a little warmer or cooler (red up, blue down by a third of that)."""
    lightness, warmth = rng.normal(0, amount), rng.normal(0, amount / 3.0)
    return [[int(np.clip(c[0] + lightness + warmth, 0, 255)), int(np.clip(c[1] + lightness, 0, 255)), int(np.clip(c[2] + lightness - warmth, 0, 255))] for c in rgb]


# ----------------------------------------------------------------------------------------------------- ruts
def random_ruts(rng, stats, tile, scale, twin_chance=0.55, options_k=2):
    """Wheel ruts as smooth wandering curves (a heading that bends slowly), some with a twin beside them (a second wheel). Start points are anywhere; curves wrap round the tile."""
    r = stats['ruts']
    n = max(int(round(r['count_per_tile'] * scale * 0.4)), 2)
    hist = np.asarray(r['direction_histogram_12_bins_over_180_degrees'], float); hist /= hist.sum()
    items = []
    dominant = [(rng.choice(12, p=hist) + rng.random()) / 12.0 * math.pi for _ in range(int(options_k))]   # two or three main directions of travel in this tile
    for _ in range(n):
        length = float(np.clip(np.exp(rng.normal(r['length_log_mean'] + 0.45, r['length_log_sd'])), 260, 1400))
        theta = dominant[int(rng.integers(len(dominant)))] + rng.normal(0, 0.22) if rng.random() < 0.85 else (rng.choice(12, p=hist) + rng.random()) / 12.0 * math.pi
        x, y = rng.uniform(0, tile), rng.uniform(0, tile)
        step = 14.0
        pts, curvature = [(x, y)], 0.0
        for _ in range(int(length / step)):
            curvature = 0.93 * curvature + rng.normal(0, 0.0105)
            theta += curvature
            x += step * math.cos(theta); y += step * math.sin(theta)
            pts.append((x, y))
        pts = np.array(pts)
        items.append(pts)
        if rng.random() < twin_chance:
            off = rng.uniform(45, 95) * rng.choice([-1, 1])
            tang = np.gradient(pts, axis=0); tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
            nrm = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
            wob = np.cumsum(rng.normal(0, 1.2, len(pts)))
            items.append(pts + nrm * (off + wob)[:, None])
    out = []
    for pts in items:
        out.append({'p': np.round(pts).astype(int).tolist(), 'length': round(float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum()), 1)})
    return out


# ----------------------------------------------------------------------------------------------------- puddles
def random_puddle(rng, stats, tile, area_target, tone_ids, scale_noise=1.0):
    """One ragged puddle: a chain of overlapping round lobes (a random walk), with a scalloped edge; its outline is found on a small canvas. Returns the outline and the flat
    water tones inside (large soft patches of lighter and darker water). All numbers in picture dots."""
    size = int(2.6 * math.sqrt(area_target) / 1.0) + 60
    scale = 1.0
    canvas = np.zeros((size, size), np.float32)
    cx, cy = size / 2.0, size / 2.0
    lobe_r = float(np.clip(math.sqrt(area_target) * 0.22, 14, 34))
    heading = rng.uniform(0, 2 * math.pi)
    placed, total = 0, 0.0
    px, py = cx, cy
    direction = rng.uniform(0, 2 * math.pi)
    while total < area_target * 1.05 and placed < 90:
        r = lobe_r * rng.uniform(0.7, 1.3)
        cv2.circle(canvas, (int(px), int(py)), int(r), 1.0, -1)
        total = float(canvas.sum())
        direction += rng.normal(0, 0.9)
        # pull back to the middle so the chain does not leave the canvas
        to_c = math.atan2(cy - py, cx - px)
        d_c = math.hypot(cx - px, cy - py)
        if d_c > size * 0.28:
            direction = to_c + rng.normal(0, 0.4)
        px += math.cos(direction) * r * 1.15; py += math.sin(direction) * r * 1.15
        placed += 1
    # scalloped edge: blur, add a fine noise, cut
    blur = cv2.GaussianBlur(canvas, (0, 0), lobe_r * 0.35)
    coarse = cv2.GaussianBlur(rng.normal(size=canvas.shape).astype(np.float32), (0, 0), 5.0)
    fine = cv2.GaussianBlur(rng.normal(size=canvas.shape).astype(np.float32), (0, 0), 2.0)
    noise = coarse / max(coarse.std(), 1e-6) * 0.20 + fine / max(fine.std(), 1e-6) * 0.14
    mask = ((blur + noise) > 0.5).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, comp, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return None
    best = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    mask = (comp == best).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = max(contours, key=cv2.contourArea)
    outline = cv2.approxPolyDP(contour, 1.4, True)[:, 0, :].astype(np.float64)
    if len(outline) < 4:
        return None
    # water tones: a smooth noise cut into lighter / darker water, plus a few dark reflection patches
    smooth = cv2.GaussianBlur(rng.normal(size=canvas.shape).astype(np.float32), (0, 0), 16.0 * scale_noise)
    smooth = (smooth - smooth.mean()) / max(smooth.std(), 1e-6)
    tones = []
    base, light, dark = tone_ids['water_base'], tone_ids['water_light'], tone_ids['water_dark']
    for colour, cond in [(light, smooth > 0.1)] + ([(dark, smooth < -1.0)] if dark is not None else []):
        m = (cond & (mask > 0)).astype(np.uint8)
        m = cv2.medianBlur(m * 255, 5) > 0
        nn, cc, ss, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=4)
        for j in range(1, nn):
            if ss[j, cv2.CC_STAT_AREA] < 60:
                continue
            cs, _ = cv2.findContours((cc == j).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.5, True)[:, 0, :]
            if len(poly) >= 3:
                tones.append((colour, poly.astype(np.float64)))
    return outline, tones, float(mask.sum())


# ----------------------------------------------------------------------------------------------------- stones
def clip_halfplane(poly, point, normal):
    """Keep the part of a convex polygon on the side of `normal` (dot(p - point, normal) >= 0): Sutherland-Hodgman for one edge."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da, db = float((a - point) @ normal), float((b - point) @ normal)
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append(a + t * (b - a))
    return np.array(out) if len(out) >= 3 else None


def random_stone(rng, stats, area, tone_probs, transitions, light_dir=np.array([-0.7071, -0.7071])):
    """A convex lump of 5 to 8 sides (radius jittered per corner) with up to three flat faces made by chords turned toward the light: the face toward the light gets the lighter
    neighbour tone, the face away the darker. Returns (base colour, outline corners relative to the centre, [(colour, corners), ...])."""
    k = int(rng.integers(6, 10)) if area > 60 else int(rng.integers(5, 8))
    r0 = math.sqrt(area / math.pi) * 1.08
    aspect = float(np.clip(np.exp(rng.normal(0.08, 0.12)), 1.0, 1.4))
    ang = np.sort(rng.uniform(0, 2 * math.pi, k)) if k < 5 else np.linspace(0, 2 * math.pi, k, endpoint=False) + rng.uniform(0, 2 * math.pi / k)
    rad = r0 * rng.uniform(0.86, 1.14, k)
    pts = np.stack([rad * np.cos(ang) * aspect, rad * np.sin(ang) / aspect], axis=1)
    rot = rng.uniform(0, math.pi)
    c, s = math.cos(rot), math.sin(rot)
    pts = pts @ np.array([[c, -s], [s, c]]).T
    base = int(rng.choice(len(tone_probs), p=tone_probs))
    faces = []
    if area >= 40:
        for _ in range(int(rng.choice([1, 2, 2, 3]))):
            direction = light_dir + rng.normal(0, 0.55, 2)
            direction /= max(np.linalg.norm(direction), 1e-9)
            offset = rng.uniform(-0.15, 0.35) * r0
            sign = rng.choice([1.0, 1.0, -1.0])
            piece = clip_halfplane(pts, direction * offset * sign, direction * sign)
            if piece is None:
                continue
            row = transitions[base]
            if row.sum() <= 0:
                continue
            colour = int(rng.choice(len(row), p=row / row.sum()))
            if colour != base:
                faces.append((colour, piece))
    return base, pts, faces


def sample_description(seed, distributions=None, **options):
    """options (all optional): tile (design size in dots, default 1254; bigger = proportionally more of everything), palette (replace the palette), tones (dict naming palette entries:
    ground, band, groove, bank, wet, water_base, water_light, water_dark), stone_scale, puddle_scale, rut_scale, clod_count (default 36000, calibrated so the density of fine edges matches the reference), clod_size_shift (default -0.35: smaller clods), pebble_cluster_share (default 0.5: the share of the small stones placed around big stones), palette_jitter, zone_weight, twin_chance, maps (height stretch and normal strength)."""
    dist = distributions or load_distributions()
    stats, ground = dist['stats'], dist['ground']
    rng = np.random.default_rng(int(seed))
    tile = int(options.get('tile', 1254))
    area_scale = (tile / 1254.0) ** 2
    palette = options.get('palette') or jitter_palette(stats['palette_rgb'], rng, options.get('palette_jitter', 3.0))
    tones = {'ground': int(np.argmax(ground['ground_share_by_tone'])) if False else ground['earth_palette_ids'][int(np.argmax(ground['ground_share_by_tone']))],
             'band': 3, 'groove': 7, 'bank': 4, 'wet': 5, 'water_base': 8, 'water_light': 2, 'water_dark': None}
    tones.update(options.get('tones', {}))
    layers = []
    # ---- ruts
    ruts = random_ruts(rng, stats, tile, area_scale * options.get('rut_scale', 1.0), options.get('twin_chance', 0.55))
    rut_items = [{'p': r['p'], 'w': float(np.clip(rng.normal(34, 6), 20, 52)), 'bw': 15, 'gw': float(np.clip(rng.normal(8, 1.5), 4, 12)), 'band': tones['band'], 'groove': tones['groove'],
                  'bank': tones['bank'], 'wet': tones['wet'] if rng.random() < 0.5 else -1} for r in ruts]
    layers.append({'type': 'ruts', 'seed': int(seed), 'wobble': 2.0, 'items': rut_items})
    # ---- clods
    earth_ids = ground['earth_palette_ids']
    lightness = [float(np.dot([0.299, 0.587, 0.114], palette[i])) for i in earth_ids]
    order = list(np.argsort(lightness))
    chances = np.array(ground['tone_chance_by_side_and_distance'])[:, :, order]
    layers.append({'type': 'clods', 'seed': int(seed), 'count': int(options.get('clod_count', 36000) * area_scale), 'tones': [earth_ids[i] for i in order],
                   'zone': {'scale': 30.0, 'weight': options.get('zone_weight', 0.6)}, 'bins': ground['distance_bins'][:-1], 'chances': np.round(chances, 3).tolist(),
                   'area_log_mean': round(ground['patch_area_log_mean'] + options.get('clod_size_shift', -0.35), 3), 'area_log_sd': round(ground['patch_area_log_sd'], 3), 'aspect_median': round(ground['patch_aspect_median'], 2),
                   'along': 0.8, 'flow_range': 60, 'skip': [tones['ground']]})
    # ---- puddles
    ps = stats['puddles']
    n_p = int(round(ps['count_per_tile'] * area_scale * options.get('puddle_scale', 1.0)))      # 0 is allowed (no puddles)
    puddle_items = []
    for _ in range(n_p):
        target = float(np.clip(np.exp(rng.normal(ps['area_log_mean'], ps['area_log_sd'])), 2500, 36000))
        made = random_puddle(rng, stats, tile, target, tones)
        if made is None:
            continue
        outline, water, _ = made
        cx, cy = rng.uniform(0, tile, 2)
        centre = outline.mean(axis=0)
        outline = outline - centre + [cx, cy]
        item = {'b': tones['water_base'], 'p': ml.encode(np.round(outline).astype(int)), 't': [[int(c), ml.encode(np.round(poly - centre + [cx, cy]).astype(int))] for c, poly in water]}
        puddle_items.append(item)
    layers.append({'type': 'puddles', 'items': puddle_items})
    # ---- stones
    st = stats['stones']
    areas_ref = np.array(st['area_sorted_every_5th'], float)
    n_s = int(options.get('stone_count', 950) * area_scale * options.get('stone_scale', 1.0))
    sizes = np.clip(rng.choice(areas_ref, n_s) * np.exp(rng.normal(0, 0.25, n_s)), 14, 9000)
    zone = ml.smooth_field(rng, tile, 90.0)
    pos = []
    # pebbles gather around the big stones: a share of the small stones is placed within 1 to 2.6 stone radii of a big one (the rest is scattered, more where a slow density field is high)
    cluster_share = float(options.get('pebble_cluster_share', 0.5))
    big_order = np.argsort(-sizes)
    n_big = min(max(int(0.08 * n_s), 1), n_s)
    big_pos = []
    for i in range(n_big):
        j = big_order[i]
        for _ in range(60):
            x, y = rng.uniform(0, tile, 2)
            if rng.random() < 1.0 / (1.0 + math.exp(-2.6 * float(zone(x, y)) - 0.6)):
                break
        big_pos.append((x, y, sizes[j]))
    if not big_pos:
        big_pos = [(0.0, 0.0, 1.0)]
    placed_sizes = list(sizes[big_order[:n_big]])
    pos = [(x, y) for x, y, a in big_pos]
    small_idx = list(big_order[n_big:])
    for j in small_idx:
        if rng.random() < cluster_share and n_big > 0:
            bx, by, ba = big_pos[int(rng.integers(len(big_pos)))]
            r = math.sqrt(ba / math.pi) * rng.uniform(1.0, 2.6) + 4
            a = rng.uniform(0, 2 * math.pi)
            pos.append((bx + r * math.cos(a), by + r * math.sin(a)))
        else:
            while True:
                x, y = rng.uniform(0, tile, 2)
                if rng.random() < 1.0 / (1.0 + math.exp(-2.6 * float(zone(x, y)) - 0.6)):
                    break
            pos.append((x, y))
    sizes = np.array(list(sizes[big_order[:n_big]]) + list(sizes[small_idx]))
    trans = np.array(st['face_tone_transition_from_base'], float)
    size_classes = [((0, 30), '0-30'), ((30, 150), '30-150'), ((150, 600), '150-600'), ((600, 1e9), '600-99999')]
    stone_items = []
    for (x, y), area in sorted(zip(pos, sizes), key=lambda t: -t[1]):
        key = next(k for (lo, hi), k in size_classes if lo <= area < hi)
        probs = np.asarray(st['tone_by_size'][key]['base_tone_share'], float)
        if probs.sum() <= 0:
            continue
        probs = probs / probs.sum()
        base, pts, faces = random_stone(rng, st, float(area), probs, trans)
        stone_items.append([int(base), ml.encode(np.round(pts + [x, y]).astype(int)), [[int(c), ml.encode(np.round(f + [x, y]).astype(int))] for c, f in faces]])
    layers.append({'type': 'stones', 'items': stone_items})
    return {'name': f'mud_sample_{seed}', 'tile': tile, 'seed': int(seed), 'palette': palette, 'ground': {'colour': tones['ground']}, 'layers': layers, 'maps': options.get('maps', MAPS)}
