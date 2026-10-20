# What this does (plain words): checks whether a BIG AREA made by the wood recipe repeats. It needs the pictures made by
# tools/run_jobs.py with tests/jobs_final_b.json (area/area_4x4 colour and height, the exact "which source dot was used" pictures, the
# board colours and the flips/knots picture, and area/tile_repeated_2x2). Four checks, each written to scores/repeat_tests_round1.json:
#   1. SHIFT TEST (copy of itself shifted): how much does the picture look like itself when it is slid sideways by one tile (1254 dots,
#      the width of the source map), by half a tile, or by random amounts? 1.0 = an identical copy, 0 = nothing alike. A picture that repeats
#      every tile (the plain source repeated, or the default tile repeated on purpose) scores 1.0 at one tile; a real non-repeating picture
#      scores at the level of all the other shifts ("the background").
#   2. SOURCE REUSE: the recipe can write, for every dot of the area, which dot of the source map it was taken from. From that: how much of the
#      source map is used at all, how many times a source dot appears in the area, how many boards show the same piece of a source row (window
#      overlap) and how far apart those boards are, and how many knot boards there are and how far apart.
#   3. NEAR COPIES (the research test): 40 board-sized patches (36 x 80 at 1024 dots for 4 x 4 tiles) are cut out and searched for in the other rows;
#      the share whose best match is above 0.8 is "has a near copy". Same function as research/tests/analyse_tests.py so that the numbers compare.
#   4. SEAM TEST of the default tile: the tile repeated 2 x 2 (area/tile_repeated_2x2) must show no step at the tile lines, and the four tiles must be equal.
# Run with:  python3 -I tools/measure_repeats.py            (numpy, PIL and cv2 only; no Blender)
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
T = 1254
SLICE_START = [189, 470, 709, 980]


def load_grey(path, size=None):
    im = Image.open(path)
    a = np.asarray(im).astype(np.float32)
    a = a / (65535.0 if a.max() > 255 else 255.0)
    if a.ndim == 3:
        a = a[..., :3]
        a = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    if size and a.shape[0] != size:
        a = cv2.resize(a, (size, size), interpolation=cv2.INTER_AREA)
    return a


def load_height16(path):
    """A 16-bit height picture exactly (0..1)."""
    return cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0


def shift_correlation(g, dx, dy):
    """Pearson correlation between the picture and itself slid by (dx, dy) picture dots (only the overlapping part is compared)."""
    h, w = g.shape
    dx, dy = int(dx), int(dy)
    a = g[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
    b = g[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    if a.size < 1000:
        return float('nan')
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / math.sqrt(float((a * a).sum() * (b * b).sum()) + 1e-12))


def shift_test(g, tile_px, tiles, rng, name):
    """Correlation at the special shifts and the background of random shifts. g: grey picture of a (tiles x tiles) area, tile_px dots per tile."""
    special = {}
    for label, (ux, uy) in {'one_tile_across': (1, 0), 'one_tile_down': (0, 1), 'one_tile_diagonal': (1, 1), 'two_tiles_across': (2, 0),
                            'half_tile_across': (0.5, 0), 'one_and_a_half_tiles_across': (1.5, 0)}.items():
        special[label] = round(shift_correlation(g, ux * tile_px, uy * tile_px), 3)
    background = []
    while len(background) < 400:
        ux, uy = rng.uniform(-(tiles - 0.8), (tiles - 0.8), 2)
        if abs(ux) < 0.3 and abs(uy) < 0.3:
            continue
        # keep away from whole-tile multiples so that "background" really is the other shifts
        if min(abs(ux - round(ux)), 9) < 0.08 and round(ux) != 0 or min(abs(uy - round(uy)), 9) < 0.08 and round(uy) != 0:
            continue
        background.append(shift_correlation(g, ux * tile_px, uy * tile_px))
    background = np.array([b for b in background if not np.isnan(b)])
    # the same for horizontal-only shifts: they are the nearest relatives of "one tile across"
    sideways = np.array([shift_correlation(g, ux * tile_px, 0) for ux in np.linspace(0.3, tiles - 1.0, 60) if abs(ux - round(ux)) > 0.08])
    return {'picture': name, 'special_shifts_correlation': special,
            'background_random_shifts': {'mean': round(float(background.mean()), 3), 'std': round(float(background.std()), 3),
                                         'highest': round(float(background.max()), 3), 'ninety_ninth_percent': round(float(np.percentile(background, 99)), 3),
                                         'count': int(len(background))},
            'background_sideways_only': {'mean': round(float(sideways.mean()), 3), 'highest': round(float(sideways.max()), 3), 'count': int(len(sideways))}}


# ------------------------------------------------------------------------------------------------------------ source reuse
def source_reuse(folder, tiles=4):
    sx = load_height16(os.path.join(folder, 'debug_source_x', 'height.png')) * T
    sy = load_height16(os.path.join(folder, 'debug_source_y', 'height.png')) * T
    size = sx.shape[0]
    dots_per_pixel = tiles * T / size
    ix = np.clip(np.round(sx - 0.5).astype(np.int64), 0, T - 1)
    iy = np.clip(np.round(sy - 0.5).astype(np.int64), 0, T - 1)
    counts = np.bincount((iy * T + ix).ravel(), minlength=T * T).astype(np.float64) * dots_per_pixel ** 2     # in dots of the area
    used = counts > 0
    out = {'dots_of_the_area': int((tiles * T) ** 2), 'source_dots_in_the_map': T * T,
           'share_of_source_dots_used_at_least_once': round(float(used.mean()), 3),
           'times_a_used_source_dot_appears_in_the_area_(mean_median_90th_percent)': [round(float(counts[used].mean()), 1), round(float(np.median(counts[used])), 1), round(float(np.percentile(counts[used], 90)), 1)]}
    by_row = {}
    for name, (a, b) in {'R1_(not_used_by_design)': (0, 189), 'R2': (189, 470), 'R3': (470, 709), 'R4': (709, 980), 'R5': (980, T)}.items():
        block = counts[a * T:b * T].reshape(-1)
        by_row[name] = {'share_used': round(float((block > 0).mean()), 3), 'mean_times_per_used_dot': round(float(block[block > 0].mean()), 1) if (block > 0).any() else 0.0}
    out['by_source_row'] = by_row
    # ---- boards (windows)
    colours = np.asarray(Image.open(os.path.join(folder, 'debug_boards', 'colour.png')).convert('RGB')).astype(np.int64)
    ids = colours[..., 0] * 65536 + colours[..., 1] * 256 + colours[..., 2]
    flips = np.asarray(Image.open(os.path.join(folder, 'debug_flips', 'colour.png')).convert('RGB')).astype(np.int64)
    order = np.argsort(ids.ravel(), kind='stable')
    sorted_ids = ids.ravel()[order]
    boundaries = np.flatnonzero(np.diff(sorted_ids)) + 1
    groups = np.split(order, boundaries)
    boards = []
    ys_grid, xs_grid = np.divmod(np.arange(size * size), size)
    sxf, syf = sx.ravel(), sy.ravel()
    for grp in groups:
        if len(grp) < 400:                                  # tiny leftovers at picture edges and anti-alias dots
            continue
        x_out, y_out = xs_grid[grp] * dots_per_pixel, ys_grid[grp] * dots_per_pixel
        xs_src = sxf[grp]
        lo, hi = float(np.percentile(xs_src, 0.5)), float(np.percentile(xs_src, 99.5))
        band = int(np.argmin(np.abs(np.array(SLICE_START) + 130 - float(np.median(syf[grp])))))
        boards.append({'x_out': float(np.median(x_out)), 'y_out': float(np.median(y_out)), 'lo': lo, 'hi': hi, 'band': band, 'length_out': float(x_out.max() - x_out.min()),
                       'knot': bool((flips.reshape(-1, 3)[grp[0]][2]) > 200)})
    n = len(boards)
    best_overlap = np.zeros(n)
    partner_distance = np.full(n, np.nan)
    pairs_50, pairs_80 = [], []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = boards[i], boards[j]
            if a['band'] != b['band']:
                continue
            inter = min(a['hi'], b['hi']) - max(a['lo'], b['lo'])
            if inter <= 0:
                continue
            share = inter / min(a['hi'] - a['lo'], b['hi'] - b['lo'])
            dist = math.hypot(a['x_out'] - b['x_out'], a['y_out'] - b['y_out']) / T
            if share > best_overlap[i]:
                best_overlap[i], partner_distance[i] = share, dist
            if share > best_overlap[j]:
                best_overlap[j], partner_distance[j] = share, dist
            if share >= 0.5:
                pairs_50.append(dist)
            if share >= 0.8:
                pairs_80.append(dist)
    out['boards'] = {'number_of_boards_counted': n,
                     'share_of_boards_that_show_at_least_half_of_the_same_source_piece_as_another_board': round(float((best_overlap >= 0.5).mean()), 3),
                     'share_with_at_least_80_percent_the_same_piece': round(float((best_overlap >= 0.8).mean()), 3),
                     'share_with_nearly_nothing_in_common_(under_25_percent)': round(float((best_overlap < 0.25).mean()), 3),
                     'pairs_sharing_half_or_more': len(pairs_50), 'pairs_sharing_80_percent_or_more': len(pairs_80),
                     'distance_between_such_pairs_in_tiles_(median_and_closest)': [round(float(np.median(pairs_50)), 2) if pairs_50 else None, round(float(np.min(pairs_50)), 2) if pairs_50 else None],
                     'closest_pair_sharing_80_percent_in_tiles': round(float(np.min(pairs_80)), 2) if pairs_80 else None,
                     'share_of_the_close_pairs_(sharing_half)_that_are_less_than_one_tile_apart': round(float((np.array(pairs_50) < 1.0).mean()), 3) if pairs_50 else None}
    knots = [b for b in boards if b['knot']]
    knot_summary = {'knot_boards_in_the_area': len(knots), 'rows_in_the_area': 20 * 4 // 4 * 1}
    for band, name in ((0, 'K2_from_row_R2'), (2, 'K3_from_row_R4')):
        pts = [(b['x_out'], b['y_out']) for b in knots if b['band'] == band]
        d = [math.hypot(p[0] - q[0], p[1] - q[1]) / T for i, p in enumerate(pts) for q in pts[i + 1:]]
        knot_summary[name] = {'boards': len(pts), 'closest_two_in_tiles': round(float(min(d)), 2) if d else None}
    out['knots'] = knot_summary
    return out


# ------------------------------------------------------------------------------------------------------------ near copies (research test)
def repeat_score(a, tpl_h=36, tpl_w=80, count=40, seed=3, rows=20):
    """The research test (research/tests/analyse_tests.py, copied): board-sized templates searched in the other rows, flipped too."""
    rng = np.random.default_rng(seed)
    h, w = a.shape
    pitch = h / rows
    a8 = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    scores, tries = [], 0
    while len(scores) < count and tries < count * 5:
        tries += 1
        r = int(rng.integers(0, rows - 1))
        x = int(rng.integers(0, w - tpl_w))
        y0 = int(round(r * pitch + pitch * 0.16))
        tpl = a8[y0:y0 + tpl_h, x:x + tpl_w]
        if tpl.std() < 8:
            continue
        best = -1.0
        for flipped in (tpl, tpl[:, ::-1].copy()):
            for r2 in range(rows - 1):
                y2 = int(round(r2 * pitch + pitch * 0.16))
                band = a8[max(y2 - 3, 0):y2 + tpl_h + 3, :]
                res = cv2.matchTemplate(band, flipped, cv2.TM_CCOEFF_NORMED)[0:7]
                if r2 == r:
                    res = res.copy()
                    res[:, max(0, x - tpl_w):x + tpl_w] = -1.0
                best = max(best, float(res.max()))
        scores.append(best)
    scores = np.array(scores)
    return {'median_best_match': round(float(np.median(scores)), 2), 'ninetieth_percent': round(float(np.percentile(scores, 90)), 2),
            'worst': round(float(scores.max()), 2), 'share_with_a_near_copy_over_0.8': round(float((scores > 0.8).mean()), 2), 'templates': int(len(scores))}


def near_copies(g_area, label):
    g = cv2.resize(g_area.astype(np.float32), (1024, 1024), interpolation=cv2.INTER_AREA)
    return {'picture': label, 'board_size_36x80': repeat_score(g, 36, 80, 40, 3), 'feature_size_24x40': repeat_score(g, 24, 40, 40, 3)}


def plain_repeat_height(tiles=4):
    h = np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'height_as_uploaded.png'))).astype(np.float32) / 255.0
    return np.tile(h, (tiles, tiles))


# ------------------------------------------------------------------------------------------------------------ seam test of the default tile
def seam_test(folder):
    out = {}
    for channel in ('colour', 'height'):
        path = os.path.join(folder, 'tile_repeated_2x2', channel + '.png')
        if not os.path.exists(path):
            continue
        g = load_grey(path)
        n = g.shape[0] // 2
        typical_x = np.abs(np.diff(g, axis=1)).mean()
        typical_y = np.abs(np.diff(g, axis=0)).mean()
        edge_x = float(np.abs(g[:, n] - g[:, n - 1]).mean() / typical_x)
        edge_y = float(np.abs(g[n] - g[n - 1]).mean() / typical_y)
        # the ordinary row boundaries inside the picture (every row boundary is a cut between two source rows hidden in a dark gap)
        diffs = np.abs(np.diff(g, axis=0)).mean(axis=1)
        quads = [g[:n, :n], g[:n, n:], g[n:, :n], g[n:, n:]]
        diff_tiles = float(np.mean([np.abs(quads[0] - q).mean() for q in quads[1:]]))
        out[channel] = {'jump_across_the_vertical_tile_line_over_a_typical_jump': round(edge_x, 2),
                        'jump_across_the_horizontal_tile_line_over_a_typical_jump': round(edge_y, 2),
                        'largest_ordinary_row_boundary_jump_over_a_typical_jump_(for_comparison)': round(float(np.sort(diffs)[-6] / typical_y), 2),
                        'mean_difference_between_the_four_tiles_0_to_1': round(diff_tiles, 4)}
    return out


def main():
    area = os.path.join(BASE, 'area')
    rng = np.random.default_rng(11)
    result = {'what_this_is': 'Repeat tests of the wood-from-maps recipe, written by tools/measure_repeats.py (see the note at the top of that file). Seed 1, default settings.'}
    # 1. shift tests (grey = height, and colour brightness), picture shrunk to 1254 dots for the 4 x 4 area: one tile = 313 dots
    plain = plain_repeat_height(4)
    plain_small = cv2.resize(plain, (1254, 1254), interpolation=cv2.INTER_AREA)
    shifts = {'control_plain_source_repeated_4x4_height': shift_test(plain_small, 313, 4, rng, 'the uploaded height map repeated 4 x 4 (what we want to get away from)')}
    h4 = load_grey(os.path.join(area, 'area_4x4', 'height.png'), 1254)
    shifts['new_area_4x4_height'] = shift_test(h4, 313, 4, rng, 'new 4 x 4 area, height')
    c4 = load_grey(os.path.join(area, 'area_4x4', 'colour.png'), 1254)
    shifts['new_area_4x4_colour_brightness'] = shift_test(c4, 313, 4, rng, 'new 4 x 4 area, colour brightness')
    h2 = load_grey(os.path.join(area, 'area_2x2', 'height.png'), 1254)
    shifts['new_area_2x2_height_(one_tile_is_627_dots)'] = shift_test(h2, 627, 2, rng, 'new 2 x 2 area, height')
    t2 = load_grey(os.path.join(area, 'tile_repeated_2x2', 'height.png'), 1254)
    shifts['default_tile_repeated_2x2_on_purpose_height'] = shift_test(t2, 627, 2, rng, 'the default tile repeated on purpose (it must score 1.0 at one tile)')
    result['shift_test'] = shifts
    # 2. source reuse
    result['source_reuse_4x4'] = source_reuse(area, 4)
    # 3. near copies
    h4_full = load_height16(os.path.join(area, 'area_4x4', 'height.png')).astype(np.float32)
    result['near_copies_research_test_4x4'] = [near_copies(plain, 'plain source repeated 4 x 4'), near_copies(h4_full, 'new 4 x 4 area (default settings, seed 1)')]
    # 4. seam test
    result['seam_test_default_tile_2x2'] = seam_test(area)
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(os.path.join(BASE, 'scores', 'repeat_tests_round1.json'), 'w') as handle:
        json.dump(result, handle, indent=1)
    print(json.dumps(result, indent=1)[:6000])


if __name__ == '__main__':
    main()
