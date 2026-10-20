# What this does (plain words): the WOOD SAMPLER. sample_description(seed) invents a NEW wood description (a small json-like dictionary) of the same kind as the
# reference: 4 to 6 planks of different heights with wavy dark gaps between them, long cracks, round knots with rings, rust-brown splatter clouds, pebbles in the
# gaps, and invented weathered paint (zones and strips) with fine dry-brush grain. Every number is drawn from the spreads measured on the reference (see
# analysis/sampler_stats.json and paint_model.json, copied into generator/fitted_distributions.json); nothing of the reference picture is used. Give it another seed
# and you get a different board layout, different cracks in different places, different knots and different paint; give it the same seed and you get the same
# description again. Options let a caller change the kind of surface (see sample_description's keyword arguments and the transfer test).
# Plain numpy/python; no Blender needed. Use:  import sampler; description = sampler.sample_description(7)
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_distributions(path=None):
    return json.load(open(path or os.path.join(HERE, 'fitted_distributions.json')))


def nearest(palette_lab, lab):
    return int(np.argmin(((np.asarray(palette_lab) - np.asarray(lab)) ** 2).sum(axis=1)))


def jitter_palette(rgb, rng, amount):
    """A slightly different palette per seed: all colours get lighter or darker together (a shift of about `amount` steps) and a little warmer or cooler (red up and blue down
    by a third of that); this keeps the colour family relations and never tints the wood pink or green."""
    lightness, warmth = rng.normal(0, amount), rng.normal(0, amount / 3.0)
    return [[int(np.clip(c[0] + lightness + warmth, 0, 255)), int(np.clip(c[1] + lightness, 0, 255)), int(np.clip(c[2] + lightness - warmth, 0, 255))] for c in rgb]


def random_waves(rng, count, max_k, amplitude, spread=1.0):
    """A few waves with whole numbers of repeats per tile (so the line repeats exactly). amplitude = about the size of the biggest wave."""
    ks = sorted(rng.choice(np.arange(1, max_k + 1), size=count, replace=False).tolist())
    return [[int(k), round(float(amplitude * rng.uniform(0.3, 1.0) / (1 + 0.12 * k) * spread), 2), round(float(rng.random()), 3)] for k in ks]


def sample_description(seed, distributions=None, **options):
    """options (all optional): boards (number of planks), palette_jitter (colour shift in steps), knots (number), crack_scale, cloud_scale, paint_scale, grain (dict),
    rate (stamp count scale), zone_amp, child_amp, tile (design size, default 1254)."""
    dist = distributions or load_distributions()
    rng = np.random.default_rng(int(seed))
    tile = int(options.get('tile', 1254))
    palette = jitter_palette(dist['palette_rgb'], rng, options.get('palette_jitter', 3.0))
    # the palette's Lab colours are kept from the fitted palette (the jitter is small; it is the same colours moved together)
    palette_lab = dist['palette_lab']
    darkest = 0
    scale = tile / 1254.0                       # a bigger design tile holds proportionally more planks, waves, knots and grain features
    n_boards = int(options.get('boards', int(round(rng.choice([4, 5, 5, 5, 6]) * scale))))
    stats = dist['sampler']
    heights = np.exp(rng.normal(stats['board_heights']['log_mean'], stats['board_heights']['log_sd'], n_boards))
    heights = heights / heights.sum() * tile
    tops = np.concatenate([[0.0], np.cumsum(heights)[:-1]]) + rng.uniform(0, tile)
    gaps = []
    for y in tops:
        gaps.append({'y': round(float(y % tile), 1), 'wave': random_waves(rng, 4, int(14 * scale), stats['gap_wobble']['sd'] * 1.1), 'width': round(float(np.clip(rng.normal(stats['gap_width']['median'], 1.0), 4.0, 9.0)), 2),
                     'width_wave': random_waves(rng, 3, int(12 * scale), stats['gap_width']['sd'] * 0.9)})
    gaps.sort(key=lambda g: g['y'])
    base = nearest(palette_lab, dist['board_lab'])
    layers = [{'type': 'plank_rows', 'gaps': gaps, 'colours': [base] * n_boards}]
    paint_model = dist['paint_model']
    stamps = {'type': 'stamps', 'seed': int(rng.integers(1 << 30)), 'model': paint_model, 'rate_scale': [options.get('rate', dist['tuned']['rate'])] * 8,
              'zone_amp': options.get('zone_amp', dist['tuned']['zone_amp']), 'child_amp': options.get('child_amp', dist['tuned']['child_amp']), 'paint_min_l': 16.0}
    layers.append(stamps)
    rust = [nearest(palette_lab, l) for l in stats['rust_palette_lab']]
    layers.append({'type': 'blobs', 'seed': int(rng.integers(1 << 30)), 'field': {'per_megapixel': stats['blob_clouds']['per_megapixel'] * options.get('cloud_scale', 1.0),
                                                                                    'n_log': [stats['blob_clouds']['n_log_mean'], stats['blob_clouds']['n_log_sd']],
                                                                                    'spread': [stats['blob_clouds']['spread_x_median'], stats['blob_clouds']['spread_y_median']],
                                                                                    'r': [stats['blob_clouds']['r_min_median'], stats['blob_clouds']['r_max_median']], 'colours': rust}})
    layers.append({'type': 'crack_field', 'seed': int(rng.integers(1 << 30)), 'colour': darkest, 'scale': options.get('crack_scale', 1.0),
                   'model': {'per_megapixel': stats['cracks']['per_megapixel_length_25_plus'] * 1.0, 'length': [stats['cracks']['length_log_mean'], stats['cracks']['length_log_sd']],
                             'width': [stats['cracks']['width_log_mean'] - 0.1, stats['cracks']['width_log_sd']], 'angle_sd': 0.07, 'corner_step': 18.0,
                             'along_gap_share': stats['cracks']['share_along_gaps'], 'gap_offset_sd': 7.0}})
    layers.append({'type': 'gap_ribbons', 'colour': darkest, 'width_scale': 1.15})
    # knots: away from the gaps and from each other; ring colours from the measured ring tone templates
    knot_count = int(options.get('knots', int(round(rng.choice([3, 4, 4, 5]) * scale * scale))))
    placed, knots = [], []
    gap_ys = np.array([g['y'] for g in gaps])
    for _ in range(knot_count):
        for attempt in range(60):
            rx = float(rng.uniform(30, 66))
            x, y = rng.uniform(0, tile), rng.uniform(0, tile)
            if np.min(np.abs(((y - gap_ys + tile / 2) % tile) - tile / 2)) < rx + 14:
                continue
            if any(np.hypot(x - px, (y - py)) < (rx + pr) * 1.1 for px, py, pr in placed):
                continue
            placed.append((x, y, rx))
            template = dist['sampler']['knots']['ring_lab_templates'][int(rng.integers(len(dist['sampler']['knots']['ring_lab_templates'])))]
            rings = [nearest(palette_lab, c) for c in reversed(template)]
            knots.append({'x': round(float(x)), 'y': round(float(y)), 'rx': round(rx), 'ry': round(rx * float(rng.uniform(0.8, 1.0))), 'angle': round(float(rng.normal(0, 0.12)), 2), 'rings': rings,
                          'ring_scale': [round(1.0 - i / len(rings), 3) for i in range(len(rings))], 'ragged': 0.05, 'seed': int(rng.integers(1 << 30)), 'core': 3.5, 'core_colour': darkest})
            break
    layers.append({'type': 'knots', 'list': knots})
    grey, light = nearest(palette_lab, [24, 3, 3]), nearest(palette_lab, [38, 4, 6])
    rows = [{'gap': i, 'x0': int(rng.integers(0, 80)), 'x1': int(tile - rng.integers(0, 80)), 'r': [2.4, 4.6], 'colours': [grey, grey, light]} for i in range(n_boards)]
    layers.append({'type': 'pebbles', 'seed': int(rng.integers(1 << 30)), 'rows': rows})
    maps = {'height': {'grey_low': 12.0, 'grey_high': 128.0, 'blur': 0.5}, 'normal': {'strength': 8}}
    grain = json.loads(json.dumps(options.get('grain', dist['tuned']['grain'])))
    for part in grain.values():
        part['u'], part['v'] = part['u'] * scale, part['v'] * scale      # feature counts are per tile: a bigger tile needs proportionally more
        if 'grain' not in options:
            part['seed'] = float(rng.integers(1, 10000))                  # every tile gets its OWN streak pattern (the same seed everywhere made all tiles share their fine grain)
    maps['grain'] = grain
    return {'format': 'wood-v1', 'note': f'sampled description, seed {seed}', 'tile': tile, 'palette': palette, 'ground': darkest, 'grow': 0.5, 'maps': maps, 'layers': layers}
