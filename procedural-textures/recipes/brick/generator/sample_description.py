# What this does (plain words): makes NEW painted-tile descriptions (the same short-list-of-numbers format the generator reads) by drawing every
# element from statistics measured on the reference's own elements (analysis/fit_sampler_model.py wrote them into sampler_model_brick.json):
# how big the bricks and joints are, how often each brick colour occurs, how many patches of paint each brick carries, how big, how tilted, how
# ragged and which colours; plus soot smudges that run down several bricks and a small shift of the palette so every tile has its own overall tone.
# The same function, given a different "model" file (another surface's measured numbers), makes new tiles of that surface: that is how the recipe
# is carried to a surface it was not fitted on (see transfer/). Nothing here reads a picture.
# Use:  import sample_description as sd ; description = sd.sample_description(seed=5, model=json.load(open('sampler_model_brick.json')))
#       sd.sample_description(seed, model, tile=2508)   -> a bigger picture of new, non-repeating bricks (24 courses, 8 bricks per course)
import colorsys
import math

import numpy as np



def jitter_palette(palette, rng, strength=1.0):
    """Shift the whole palette a little (brightness, saturation, hue) so each tile has its own overall tone."""
    brightness = 1.0 + rng.normal(0, 0.035) * strength
    saturation = 1.0 + rng.normal(0, 0.05) * strength
    hue_shift = rng.normal(0, 0.006) * strength
    out = []
    for entry in palette:
        r, g, b = [v / 255.0 for v in entry[:3]]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h = (h + hue_shift) % 1.0
        s = min(max(s * saturation, 0.0), 1.0)
        v = min(max(v * brightness, 0.0), 1.0)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        out.append([int(round(r * 255)), int(round(g * 255)), int(round(b * 255))] + list(entry[3:]))
    return out


def sample_layout(model, rng, tile, rows_count=None):
    """Courses and bricks that wrap exactly: course heights and brick widths drawn from the measured spreads, joints of neighbouring courses kept apart."""
    lay = model['layout']
    n_rows = rows_count or max(int(round(tile / lay.get('row_pitch_target', 104.5))), 2)
    pitches = tile / n_rows * (1.0 + rng.normal(0, 0.012, n_rows))
    pitches *= tile / pitches.sum()
    gap_v = lay['vertical_gap']
    per_row = max(int(round(tile / lay['brick_pitch'][0])), 2)
    rel_sd = lay['brick_pitch'][1] / lay['brick_pitch'][0]
    rows, y = [], 0.0
    previous_joints = None
    for i in range(n_rows):
        face_top = y + gap_v / 2.0 + rng.normal(0, 0.4)
        face_bottom = y + pitches[i] - gap_v / 2.0 + rng.normal(0, 0.4)
        best, best_score = None, -1
        for attempt in range(60):
            widths = np.clip(1.0 + rng.normal(0, rel_sd, per_row), 0.55, 1.6)
            widths *= tile / widths.sum()
            start = rng.uniform(0, tile)
            joints = (start + np.concatenate([[0], np.cumsum(widths)[:-1]])) % tile
            if previous_joints is None:
                best = (joints, widths, start)
                break
            gaps = np.abs(((joints[:, None] - previous_joints[None, :]) + tile / 2) % tile - tile / 2)
            score = gaps.min()
            if score > best_score:
                best, best_score = (joints, widths, start), score
            if score >= 70:
                break
        joints, widths, start = best
        previous_joints = joints
        edges = start + np.concatenate([[0], np.cumsum(widths)])
        bricks = []
        gap_list = np.clip(rng.normal(lay['joint_gap'][0], lay['joint_gap'][1], per_row), 14, 30)
        for j in range(per_row):
            g_left = gap_list[j - 1]
            g_right = gap_list[j]
            x0 = edges[j] + g_left / 2.0
            x1 = edges[j + 1] - g_right / 2.0
            bricks.append([round(float(x0), 1), round(float(x1), 1), 0])
        rows.append({'y0': round(float(face_top), 1), 'y1': round(float(face_bottom), 1), 'bricks': bricks})
        y += pitches[i]
    return rows


def coarse_of(area):
    return 0 if area < 160 else (1 if area < 1300 else 2)


def draw_patches(bins, colour_table, class_key, region_area, rng, boost, ragged_level=0.75):
    """Patches for one kind of place (a brick face of a given class, or the mortar): for each size bin, as many as the measured density says,
    each with a size drawn inside the bin, a stretch (aspect) and a tilt from the measured spread, and a colour from the measured table.
    Returns a list of [centre unit x, centre unit y (0..1 inside the place), rx, ry, angle, colour, raggedness]."""
    out = []
    for b in bins:
        density = b['count_per_10000_dots']
        if density <= 0:
            continue
        count = rng.poisson(density * boost * region_area / 10000.0)
        lo, hi = b['area_range']
        for _ in range(count):
            area = math.exp(rng.uniform(math.log(lo), math.log(hi)))
            aspect = math.exp(abs(rng.normal(*b['log_aspect_mean_sd'])))
            rx = math.sqrt(area / math.pi * aspect)
            ry = math.sqrt(area / math.pi / aspect)
            angle = rng.normal(0, 12.0) if rng.random() < b['horizontal_share'] else rng.uniform(0, 180.0)
            ragged = float(np.clip(rng.normal(ragged_level, 0.12), 0.3, 1.0))
            probs = np.array(colour_table[class_key(coarse_of(area))], float)
            colour = int(rng.choice(len(probs), p=probs / probs.sum()))
            out.append([rng.uniform(), rng.uniform(), rx, ry, angle, colour, ragged])
    return out


def sample_description(seed, model, tile=None, style='mosaic', grain=0.14, palette_strength=0.5, smudges_per_tile=None, dark_share_in_smudges=0.8, patch_boost=1.3, cell_scale=1.0):
    rng = np.random.default_rng(int(seed))
    tile = float(tile or model['tile'])
    scale_area = (tile / model['tile']) ** 2
    palette = jitter_palette(model['palette'], rng, palette_strength)
    luma = np.array([0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in palette])
    n_colours = len(palette)
    rows = sample_layout(model, rng, tile)
    ring_colour = len(palette)
    freq = np.array(model['brick_base_colour']['frequency'], float)
    freq = freq / freq.sum()
    class_of_colour = model['brick_base_colour']['class_of_colour']
    # base colour of every brick
    for row in rows:
        for brick in row['bricks']:
            brick[2] = int(rng.choice(n_colours, p=freq))
    # patches on bricks
    blobs = []
    rects = []
    boost = float(patch_boost)
    brick_tables = model['brick_patches']['colour_probability']
    for row in rows:
        for x0, x1, colour in row['bricks']:
            rects.append((x0, row['y0'], x1, row['y1']))
            cls = class_of_colour[colour]
            for u, v, rx, ry, angle, colour_index, ragged in draw_patches(
                    model['brick_patches']['bins'], brick_tables,
                    lambda co, cls=cls: f'{cls}_{co}' if f'{cls}_{co}' in brick_tables else f'0_{co}',
                    (x1 - x0) * (row['y1'] - row['y0']), rng, boost):
                cx = x0 + u * (x1 - x0)
                cy = row['y0'] + v * (row['y1'] - row['y0'])
                # keep the patch inside its brick (the reference's patches stop at the brick edge): shrink it until its reach fits
                a = math.radians(angle)
                reach_x = 1.35 * math.hypot(rx * math.cos(a), ry * math.sin(a))
                reach_y = 1.35 * math.hypot(rx * math.sin(a), ry * math.cos(a))
                room_x = min(cx - x0, x1 - cx) + 2.0
                room_y = min(cy - row['y0'], row['y1'] - cy) + 2.0
                fit = max(min(1.0, room_x / reach_x, room_y / reach_y), 0.25)
                blobs.append([cx, cy, rx * fit, ry * fit, angle, colour_index, ragged])
    # patches in the mortar: positions are drawn over the whole tile again and again until one falls outside every brick face
    rect_array = np.array(rects)
    mortar_area = tile * tile - float(((rect_array[:, 2] - rect_array[:, 0]) * (rect_array[:, 3] - rect_array[:, 1])).sum())
    mortar_tables = model['mortar_patches']['colour_probability']
    for u, v, rx, ry, angle, colour_index, ragged in draw_patches(
            model['mortar_patches']['bins'], mortar_tables, lambda co: str(co), mortar_area, rng, boost):
        for attempt in range(200):
            cx, cy = rng.uniform(0, tile, 2)
            px = (cx - rect_array[:, 0]) % tile
            inside = (px < (rect_array[:, 2] - rect_array[:, 0])) & (cy >= rect_array[:, 1]) & (cy <= rect_array[:, 3])
            if not inside.any():
                blobs.append([cx, cy, rx, ry, angle, colour_index, ragged])
                break
    # soot smudges: dark patches gather in a few places and stretch downwards
    n_smudge = max(int(round((smudges_per_tile if smudges_per_tile is not None else model.get('smudges_per_tile', 8)) * scale_area)), 1)
    centres = rng.uniform(0, tile, (n_smudge, 2))
    for blob in blobs:
        if luma[blob[5]] < model.get('smudge_luma_limit', 75) and rng.random() < dark_share_in_smudges:
            c = centres[int(rng.integers(0, n_smudge))]
            blob[0] = (c[0] + rng.normal(0, 38)) % tile
            blob[1] = (c[1] + rng.normal(0, 70)) % tile
            if rng.random() < 0.6:
                blob[2], blob[3] = blob[3] * 0.8, blob[2] * 1.4
                blob[4] = 90.0 + rng.normal(0, 8)
    blobs.sort(key=lambda b: -(b[2] * b[3]))
    items = [[int(round(b[0])), int(round(b[1])), round(b[2], 1), round(b[3], 1), int(round(b[4])), int(b[5]), round(b[6], 1), int(rng.integers(1, 999))]
             for b in blobs]
    dark = int(np.argmin(luma))
    ring_colour = len(palette)
    palette = palette + [list(model.get('outline', {}).get('rgb_rough', [60, 43, 34, 0.9]))]
    outline = model.get('outline', {})          # optional per-surface outline settings (the brick numbers are the defaults)
    ring_colour_index = ring_colour if 'colour' not in outline else outline['colour']
    bricks_layer = {'type': 'bricks', 'corner_radius': model['layout']['corner_radius'], 'outline_width': outline.get('width', 2.0), 'outline_colour': ring_colour_index,
                    'ragged': outline.get('ragged', 2.0), 'ragged_wavelength': outline.get('ragged_wavelength', 12.0), 'rows': rows}
    ring_layer = {'type': 'outlines', 'colour': ring_colour_index, 'corner_radius': model['layout']['corner_radius'],
                  'inside': outline.get('ring_inside', [1.0, 1.0, 1.0, 1.5]), 'outside': outline.get('ring_outside', [1.0, 0.0, 1.5, 3.0]), 'rows': rows}
    if style == 'mosaic':
        order = [int(i) for i in np.argsort(luma[:len(model['palette'])])]
        if 'accents' in model:                       # explicit sets written in the model (the right way: a new surface says which colours are its dirt, chips, moss)
            accents = [{'name': a['name'], 'seed': int(rng.integers(1, 1 << 30)), 'count': max(int(round(a['count_per_tile'] * scale_area)), 1), 'sigma': a['sigma'],
                        'strength': a.get('strength', 0.9), 'colours': a['colours']} for a in model['accents']]
            mortar_accents = [a for a, spec in zip(accents, model['accents']) if spec.get('also_in_mortar')]
        else:                                        # fallback guess for the brick: soot = three darkest colours, spall = pale low-colour entries
            chroma = np.array([max(c[:3]) - min(c[:3]) for c in model['palette']])
            spall_colours = [int(i) for i in np.nonzero((chroma < 62) & (luma[:len(model['palette'])] > 70))[0]]
            soot_count = max(int(round(model.get('soot_per_tile', 12) * scale_area)), 1)
            spall_count = max(int(round(model.get('spall_per_tile', 14) * scale_area)), 1)
            accents = [{'name': 'soot', 'seed': int(rng.integers(1, 1 << 30)), 'count': soot_count, 'sigma': [42.0, 85.0], 'strength': 0.92, 'colours': order[:3]},
                       {'name': 'spall', 'seed': int(rng.integers(1, 1 << 30)), 'count': spall_count, 'sigma': [34.0, 30.0], 'strength': 0.9, 'colours': spall_colours}]
            mortar_accents = [accents[0]]
        tone = {'wavelengths': [110.0, 170.0, 260.0], 'jitter': 0.2}
        brick_tables = {k: [round(v, 3) for v in t] for k, t in model['brick_patches']['colour_probability'].items()}
        mortar_tables = {k: [round(v, 3) for v in t] for k, t in model['mortar_patches']['colour_probability'].items()}
        cs = float(cell_scale)
        layers = [
            {'type': 'mosaic', 'target': 'mortar', 'seed': int(rng.integers(1, 1 << 30)), 'rows': rows, 'luma_order': order, 'tone': {'wavelengths': [60.0, 110.0], 'jitter': 0.22},
             'scales': [{'area': 150.0 * cs, 'keep': 1.0, 'table': 'area', 'wobble': 1.3, 'jitter': 0.3}, {'area': 40.0 * cs, 'keep': 0.4, 'table': 'area', 'wobble': 0.9, 'wavelengths': [5.0, 11.0], 'jitter': 0.35}],
             'tables': mortar_tables, 'accents': mortar_accents},
            bricks_layer,
            {'type': 'mosaic', 'target': 'bricks', 'seed': int(rng.integers(1, 1 << 30)), 'rows': rows, 'corner_radius': model['layout']['corner_radius'], 'luma_order': order,
             'tone': tone, 'brick_tone_spread': model.get('brick_tone_spread', 0.2), 'base_classes': model['brick_base_colour']['class_of_colour'],
             'scales': [{'area': 1100.0 * cs, 'keep': 1.0, 'table': 'area', 'wobble': 1.3, 'jitter': 0.08}, {'area': 320.0 * cs, 'keep': 0.5, 'table': 'area', 'wobble': 1.3, 'jitter': 0.12},
                        {'area': 90.0 * cs, 'keep': 0.35, 'table': 'area', 'wobble': 0.9, 'wavelengths': [5.0, 11.0], 'jitter': 0.22},
                        {'area': 45.0 * cs, 'keep': 0.22, 'table': 'area', 'wobble': 0.8, 'wavelengths': [4.0, 9.0], 'jitter': 0.3}],
             'tables': brick_tables, 'accents': accents, 'exclude_accent_colours': True},
            ring_layer]
    else:
        layers = [bricks_layer, {'type': 'blobs', 'items': items}, ring_layer]
    description = {
        'format': 'painted-tile-1', 'surface': model.get('surface', 'brick'), 'tile': tile, 'seed': int(seed),
        'palette': palette, 'maps': model['maps'], 'backdrop': model['backdrop'], 'layers': layers,
    }
    if grain:
        description['grain'] = {'amount': grain, 'seed': int(seed) % 97 + 1}
    return description
