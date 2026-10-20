# What this is (plain words): the HONESTY CHECKER's own copy of tools/measure_repeats_round2.py, used to re-run the builder's repeat measures on the 4 x 4 area without touching the builder's files.
# The ONLY changes against the builder's script: BASE and PROC point at the builder's folders (so the pictures are the builder's), the result is written to check_honesty/round2/repeat_tests_rerun.json
# instead of scores/repeat_tests_round2.json, and cv2 is limited to one thread (the machine is shared). Everything else is the builder's code, unchanged.
# What this does (plain words): checks whether a BIG AREA made by the wood recipe repeats (round 2 version of tools/measure_repeats.py; it fixes the
# faults that the honesty checker found in the round 1 version). Written to scores/repeat_tests_round2.json. It reads the pictures made by
# tools/run_jobs.py with tests/jobs_r2_areas.json (area/area_4x4 colour and height, area/area_2x2, area/tile_repeated_2x2, the exact "which source dot was
# used" pictures, the board numbers, the landmark picture). It reads colour.png or colour.jpg and height.png, whichever is there.
# Checks:
#   1. SHIFT TEST: how much does the picture look like itself when slid sideways by one tile? 1.0 = identical, about 0 = nothing alike. The control
#      (the uploaded map repeated 4 x 4) is made with a whole number of dots per tile, so an exact repeat scores 1.000 (the round 1 control was half a dot
#      out and scored 0.972).
#   2. SOURCE REUSE: from the exact pictures: how much of the source is used, how often, how many boards show the same source row.
#   3. NEIGHBOURS: of all boards that touch (side by side, and above and below) how many take the same source row, and how many show a mirrored
#      or repeated piece next to each other (round 1 claimed "never"; it was 19 percent).
#   4. NEAR COPIES, two tests on the same picture:  (a) the research test (36 x 80 pieces at 1024 dots, searched in the other rows, also flipped; "has a near
#      copy" = best match over 0.8), and (b) the LOOK CHECKER's own test (pieces of 200 x 380 source dots, searched everywhere in the area, all four ways round;
#      share of pieces whose best match is over 0.6 / 0.7 / 0.8). Both are also run on the round 1 area and on the plain repeat of the map, so the numbers compare.
#   5. LANDMARKS: how often each recognisable place of the source shows up in the 4 x 4 area (from the landmark picture).
#   6. SEAM TEST of the default tile repeated 2 x 2, and "is the first tile of an area the default tile?".
# Run with:  python3 -I tools/measure_repeats_round2.py [--quick] [--only-switch]    (--only-switch redoes just the switched-off areas and keeps the rest of the JSON)      (numpy, PIL and cv2 only; no Blender)
import json
import math
import os
import sys

import cv2
cv2.setNumThreads(1)
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 'proc-work/recipes/wood_from_displacement'
PROC = 'proc-work'
T = 1254
SLICE_START = [189, 470, 709, 980]
LANDMARK_NAMES = ['knot K2', 'knot K3', 'knot K4', 'zigzag crack R2', 'hook splinter R2', 'rust cloud R3', 'hole R3', 'notch R3', 'splinter R4', 'splinter R5', 'stain cluster R5', 'rubble R5']


def find(folder, name):
    for ext in ('.png', '.jpg'):
        p = os.path.join(folder, name + ext)
        if os.path.exists(p):
            return p
    return None


def load_grey(folder, name='colour', size=None):
    """Grey picture 0..1 from colour.png / colour.jpg (brightness) or height.png (8 or 16 bit)."""
    p = find(folder, name)
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if a.ndim == 3:
        a = a[..., :3][..., ::-1].astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)
        a = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    else:
        a = a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)
    if size and a.shape[0] != size:
        a = cv2.resize(a, (size, size), interpolation=cv2.INTER_AREA)
    return a


def load_exact(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    a = a[..., 0] if a.ndim == 3 else a
    return a.astype(np.float64) / (255.0 if a.dtype == np.uint8 else 65535.0)


def shift_correlation(g, dx, dy):
    h, w = g.shape
    dx, dy = int(round(dx)), int(round(dy))
    a = g[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
    b = g[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    if a.size < 1000:
        return float('nan')
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / math.sqrt(float((a * a).sum() * (b * b).sum()) + 1e-12))


def shift_test(g, tile_px, tiles, rng, name):
    special = {}
    for label, (ux, uy) in {'one_tile_across': (1, 0), 'one_tile_down': (0, 1), 'one_tile_diagonal': (1, 1), 'half_tile_across': (0.5, 0)}.items():
        special[label] = round(shift_correlation(g, ux * tile_px, uy * tile_px), 3)
    background = []
    while len(background) < 300:
        ux, uy = rng.uniform(-(tiles - 0.8), (tiles - 0.8), 2)
        if abs(ux) < 0.3 and abs(uy) < 0.3:
            continue
        if (abs(ux - round(ux)) < 0.08 and round(ux) != 0) or (abs(uy - round(uy)) < 0.08 and round(uy) != 0):
            continue
        background.append(shift_correlation(g, ux * tile_px, uy * tile_px))
    background = np.array([b for b in background if not np.isnan(b)])
    sideways = np.array([shift_correlation(g, ux * tile_px, 0) for ux in np.linspace(0.3, tiles - 1.0, 60) if abs(ux - round(ux)) > 0.08])
    return {'picture': name, 'special_shifts_correlation': special,
            'background_random_shifts_highest': round(float(background.max()), 3), 'background_random_shifts_mean': round(float(background.mean()), 3),
            'background_sideways_only_highest': round(float(sideways.max()), 3)}


# ------------------------------------------------------------------------------------------------------------ source reuse and neighbours
def boards_from_debug(folder, tiles=4):
    sx = load_exact(os.path.join(folder, 'debug_source_x', 'height.png')) * T
    sy = load_exact(os.path.join(folder, 'debug_source_y', 'height.png')) * T
    ids = np.round(load_exact(os.path.join(folder, 'debug_boards_height', 'height.png')) * 65535.0).astype(np.int64)
    size = sx.shape[0]
    dpp = tiles * T / size
    order = np.argsort(ids.ravel(), kind='stable')
    sorted_ids = ids.ravel()[order]
    groups = np.split(order, np.flatnonzero(np.diff(sorted_ids)) + 1)
    label = np.full(size * size, -1, dtype=np.int64)
    boards = []
    ys_grid, xs_grid = np.divmod(np.arange(size * size), size)
    sxf, syf = sx.ravel(), sy.ravel()
    for grp in groups:
        if len(grp) < 600:
            continue
        xs_src = sxf[grp]
        band = int(np.argmin(np.abs(np.array(SLICE_START) + 130 - float(np.median(syf[grp])))))
        label[grp] = len(boards)
        boards.append({'x_out': float(np.median(xs_grid[grp] * dpp)), 'y_out': float(np.median(ys_grid[grp] * dpp)), 'lo': float(np.percentile(xs_src, 0.5)), 'hi': float(np.percentile(xs_src, 99.5)),
                       'band': band, 'length_out': float((xs_grid[grp].max() - xs_grid[grp].min()) * dpp)})
    return sx, sy, size, dpp, label.reshape(size, size), boards


def source_reuse_and_neighbours(folder, tiles=4):
    sx, sy, size, dpp, label, boards = boards_from_debug(folder, tiles)
    ix = np.clip(np.round(sx - 0.5).astype(np.int64), 0, T - 1)
    iy = np.clip(np.round(sy - 0.5).astype(np.int64), 0, T - 1)
    counts = np.bincount((iy * T + ix).ravel(), minlength=T * T).astype(np.float64) * dpp ** 2
    used = counts > 0
    out = {'source_dots_used_at_least_once': round(float(used.mean()), 3),
           'times_a_used_source_dot_appears_mean_median_90th': [round(float(counts[used].mean()), 1), round(float(np.median(counts[used])), 1), round(float(np.percentile(counts[used], 90)), 1)]}
    n = len(boards)
    out['boards_counted'] = n
    lengths = np.array([b['length_out'] for b in boards])
    out['board_length_in_tiles_median_and_90th_percent'] = [round(float(np.median(lengths)) / T, 2), round(float(np.percentile(lengths, 90)) / T, 2)]
    # neighbours: horizontal and vertical touching pairs
    pairs = set()
    for a, b in ((label[:, :-1], label[:, 1:]), (label[:-1, :], label[1:, :])):
        m = (a != b) & (a >= 0) & (b >= 0)
        for i, j in set(zip(a[m].tolist(), b[m].tolist())):
            pairs.add((min(i, j), max(i, j)))
    hpairs = set()
    a, b = label[:, :-1], label[:, 1:]
    m = (a != b) & (a >= 0) & (b >= 0)
    for i, j in set(zip(a[m].tolist(), b[m].tolist())):
        hpairs.add((min(i, j), max(i, j)))
    same_band_all = [p for p in pairs if boards[p[0]]['band'] == boards[p[1]]['band']]
    same_band_h = [p for p in hpairs if boards[p[0]]['band'] == boards[p[1]]['band']]

    def overlap(p):
        a_, b_ = boards[p[0]], boards[p[1]]
        inter = min(a_['hi'], b_['hi']) - max(a_['lo'], b_['lo'])
        return max(inter, 0.0) / max(min(a_['hi'] - a_['lo'], b_['hi'] - b_['lo']), 1.0)
    twins = [p for p in same_band_all if overlap(p) >= 0.5]
    out['touching_pairs'] = {'all_touching_pairs': len(pairs), 'side_by_side_pairs': len(hpairs),
                             'share_of_all_touching_pairs_with_the_same_source_row': round(len(same_band_all) / max(len(pairs), 1), 3),
                             'share_of_side_by_side_pairs_with_the_same_source_row': round(len(same_band_h) / max(len(hpairs), 1), 3),
                             'touching_pairs_with_the_same_source_row_AND_half_or_more_of_the_same_source_stretch': len(twins),
                             'share_of_all_touching_pairs': round(len(twins) / max(len(pairs), 1), 3)}
    # boards sharing source pieces anywhere (same source row, source stretches overlapping by half or more)
    best = np.zeros(n)
    for i in range(n):
        for j in range(i + 1, n):
            if boards[i]['band'] != boards[j]['band']:
                continue
            inter = min(boards[i]['hi'], boards[j]['hi']) - max(boards[i]['lo'], boards[j]['lo'])
            if inter <= 0:
                continue
            share = inter / min(boards[i]['hi'] - boards[i]['lo'], boards[j]['hi'] - boards[j]['lo'])
            best[i], best[j] = max(best[i], share), max(best[j], share)
    out['share_of_boards_sharing_half_or_more_of_the_same_source_stretch_with_another_board_(says_little_by_itself)'] = round(float((best >= 0.5).mean()), 3)
    return out


def landmark_counts(folder, tiles=4):
    """How often each landmark is SHOWN in the area: connected blobs of each landmark number in the landmark debug picture (exact 16-bit Height)."""
    p = os.path.join(folder, 'debug_landmarks', 'height.png')
    if not os.path.exists(p):
        return None
    a = np.round(load_exact(p) * 16.0).astype(np.int64)
    size = a.shape[0]
    dpp = tiles * T / size
    out = {}
    for i, name in enumerate(LANDMARK_NAMES):
        mask = (a == i + 1).astype(np.uint8)
        n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, connectivity=8)
        blobs = [(float(cent[k][0] * dpp), float(cent[k][1] * dpp)) for k in range(1, n) if stats[k][4] * dpp * dpp >= 400]
        # pieces of one landmark that a joint cut into two parts lie close together: blobs closer than 200 dots count as ONE showing
        instances = []
        for b in blobs:
            for inst in instances:
                if math.hypot(inst[0] - b[0], inst[1] - b[1]) < 200:
                    break
            else:
                instances.append(b)
        close = 0
        for x in range(len(instances)):
            for y in range(x + 1, len(instances)):
                if math.hypot(instances[x][0] - instances[y][0], instances[x][1] - instances[y][1]) < 1.0 * T:
                    close += 1
        out[name] = {'times_shown_in_16_tiles': len(instances), 'blobs_before_joining_parts': len(blobs), 'pairs_closer_than_one_tile': close}
    out['_total_shown_in_16_tiles'] = int(sum(v['times_shown_in_16_tiles'] for k, v in out.items() if not k.startswith('_')))
    return out


# ------------------------------------------------------------------------------------------------------------ near copies
def research_score(a, tpl_h=36, tpl_w=80, count=40, seed=3, rows=20):
    """The research test (research/tests/analyse_tests.py, as copied into tools/measure_repeats.py)."""
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
    return {'median_best_match': round(float(np.median(scores)), 2), 'share_with_a_near_copy_over_0.8': round(float((scores > 0.8).mean()), 2), 'templates': int(len(scores))}


def checker_score(a, tiles=4, count=60, seed=3):
    """The look checker's own test (check_look_round_1/find_repeats.py): pieces of 200 x 380 source dots, found anywhere in the area, all four ways round."""
    h, w = a.shape
    dpp = tiles * T / h
    ph, pw = int(round(200 / dpp)), int(round(380 / dpp))
    a32 = a.astype(np.float32)
    rng = np.random.default_rng(seed)
    res = []
    for _ in range(count * 3):
        if len(res) >= count:
            break
        y = int(rng.integers(10, h - ph - 10))
        x = int(rng.integers(10, w - pw - 10))
        patch = a32[y:y + ph, x:x + pw]
        if patch.std() < 0.03:
            continue
        best = -1.0
        for flip in range(4):
            pp = patch
            if flip & 1:
                pp = pp[:, ::-1]
            if flip & 2:
                pp = pp[::-1, :]
            m = cv2.matchTemplate(a32, np.ascontiguousarray(pp), cv2.TM_CCOEFF_NORMED)
            y0, y1 = max(0, y - ph), min(m.shape[0], y + ph)
            x0, x1 = max(0, x - pw), min(m.shape[1], x + pw)
            m[y0:y1, x0:x1] = -1
            best = max(best, float(m.max()))
        res.append(best)
    sc = np.array(res)
    return {'pieces': int(len(sc)), 'median': round(float(np.median(sc)), 3), 'share_over_0.6': round(float((sc > 0.6).mean()), 3), 'share_over_0.7': round(float((sc > 0.7).mean()), 3),
            'share_over_0.8': round(float((sc > 0.8).mean()), 3)}


# ------------------------------------------------------------------------------------------------------------ seam test of the default tile
def seam_test(folder):
    out = {}
    for channel in ('colour', 'height'):
        if find(os.path.join(folder, 'tile_repeated_2x2'), channel) is None:
            continue
        g = load_grey(os.path.join(folder, 'tile_repeated_2x2'), channel)
        n = g.shape[0] // 2
        typical_x = np.abs(np.diff(g, axis=1)).mean()
        typical_y = np.abs(np.diff(g, axis=0)).mean()
        diffs = np.abs(np.diff(g, axis=0)).mean(axis=1)
        quads = [g[:n, :n], g[:n, n:], g[n:, :n], g[n:, n:]]
        out[channel] = {'jump_across_the_vertical_tile_line_over_a_typical_jump': round(float(np.abs(g[:, n] - g[:, n - 1]).mean() / typical_x), 2),
                        'jump_across_the_horizontal_tile_line_over_a_typical_jump': round(float(np.abs(g[n] - g[n - 1]).mean() / typical_y), 2),
                        'largest_ordinary_row_boundary_jump_over_a_typical_jump_(for_comparison)': round(float(np.sort(diffs)[-6] / typical_y), 2),
                        'mean_difference_between_the_four_tiles_0_to_1': round(float(np.mean([np.abs(quads[0] - q).mean() for q in quads[1:]])), 4)}
    return out


def first_tile_check(area_folder, tile_folder, tiles=4):
    """Is the top-left tile of the area the default tile? (round 1: correlation 0.76)"""
    a = load_grey(os.path.join(area_folder, 'area_4x4'), 'height')
    px = a.shape[0] // tiles
    first = a[:px, :px]
    t = load_grey(tile_folder, 'height', size=px)
    out = {'top_left_tile_of_the_area_versus_the_default_tile_of_the_same_seed_correlation': round(float(np.corrcoef(first.ravel(), t.ravel())[0, 1]), 3)}
    others = []
    for i in range(tiles):
        for j in range(tiles):
            if i == 0 and j == 0:
                continue
            blk = a[i * px:(i + 1) * px, j * px:(j + 1) * px]
            others.append(float(np.corrcoef(blk.ravel(), t.ravel())[0, 1]))
    out['other_tiles_of_the_area_versus_the_default_tile_correlation_highest'] = round(float(np.max(np.abs(others))), 3)
    return out


def plain_repeat(tiles=4, tile_px=313):
    h = cv2.resize(np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'height_as_uploaded.png'))).astype(np.float32) / 255.0, (tile_px, tile_px), interpolation=cv2.INTER_AREA)
    return np.tile(h, (tiles, tiles))


def switched_part(area, quick=False):
    """The same two near-copy tests on 4 x 4 areas of height at 1024 dots with parts of the round 2 fixes switched off (tests/jobs_r2_switch.json)."""
    switched = {}
    for key in ('default', 'no_landmark_painting', 'no_bending_no_stretch', 'windows_only', 'three_boards_per_row'):
        folder = os.path.join(area, f'switch_{key}')
        if find(folder, 'height'):
            g = load_grey(folder, 'height')
            switched[key] = {'research_test_36x80': research_score(g, 36, 80, 40, 3), 'look_checker_test': checker_score(g, 4, 40, 3) if not quick else None}
    if not switched:
        return {}
    return {'near_copies_switching_parts_off': {'note': '4 x 4 areas of HEIGHT baked at 1024 dots (2 samples), seed 1, with parts of the round 2 fixes switched off (jobs in tests/jobs_r2_switch.json).', 'results': switched}}


def main():
    quick = '--quick' in sys.argv
    area = os.path.join(BASE, 'area')
    out_path = 'proc-work/recipes/wood_from_displacement/check_honesty/round2/repeat_tests_rerun.json'
    if '--only-switch' in sys.argv:                     # redo only the switched-off part and keep everything else measured before
        with open(out_path) as handle:
            result = json.load(handle)
        result.update(switched_part(area, quick))
        with open(out_path, 'w') as handle:
            json.dump(result, handle, indent=1)
        print(json.dumps(result.get('near_copies_switching_parts_off'), indent=1))
        return
    rng = np.random.default_rng(11)
    result = {'what_this_is': 'Repeat tests of the wood-from-maps recipe, round 2, written by tools/measure_repeats_round2.py (see the note at the top of that file). Seed 1, default settings.'}
    # 1. shift tests on pictures of 1252 dots across (one tile = 313 dots exactly)
    plain = plain_repeat(4, 313)
    shifts = {'control_plain_source_repeated_4x4_height_(exact_whole_dots)': shift_test(plain, 313, 4, rng, 'the uploaded height map repeated 4 x 4 (313 dots per tile, exact)')}
    h4 = load_grey(os.path.join(area, 'area_4x4'), 'height', 1252)
    shifts['new_area_4x4_height'] = shift_test(h4, 313, 4, rng, 'new 4 x 4 area, height')
    c4 = load_grey(os.path.join(area, 'area_4x4'), 'colour', 1252)
    shifts['new_area_4x4_colour_brightness'] = shift_test(c4, 313, 4, rng, 'new 4 x 4 area, colour brightness')
    if find(os.path.join(area, 'area_2x2'), 'height'):
        h2 = load_grey(os.path.join(area, 'area_2x2'), 'height', 1252)
        shifts['new_area_2x2_height_(one_tile_is_626_dots)'] = shift_test(h2, 626, 2, rng, 'new 2 x 2 area, height')
    if find(os.path.join(area, 'tile_repeated_2x2'), 'height'):
        t2 = load_grey(os.path.join(area, 'tile_repeated_2x2'), 'height', 1252)
        shifts['default_tile_repeated_2x2_on_purpose_height_(must_be_1.0)'] = shift_test(t2, 626, 2, rng, 'the default tile repeated on purpose')
    result['shift_test'] = shifts
    # 2/3/5 source reuse, neighbours, landmarks
    result['source_reuse_and_neighbours_4x4'] = source_reuse_and_neighbours(area, 4)
    result['landmarks_shown_in_the_4x4_area'] = landmark_counts(area, 4)
    # 4. near copies
    near = {}
    h4_1024 = cv2.resize(load_grey(os.path.join(area, 'area_4x4'), 'height'), (1024, 1024), interpolation=cv2.INTER_AREA)
    c4_1024 = cv2.resize(load_grey(os.path.join(area, 'area_4x4'), 'colour'), (1024, 1024), interpolation=cv2.INTER_AREA)
    plain_1024 = cv2.resize(np.tile(np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'height_as_uploaded.png'))).astype(np.float32) / 255.0, (4, 4)), (1024, 1024), interpolation=cv2.INTER_AREA)
    near['research_test_36x80_plain_source_repeated_height'] = research_score(plain_1024, 36, 80, 40, 3)
    near['research_test_36x80_new_area_height'] = research_score(h4_1024, 36, 80, 40, 3)
    near['research_test_36x80_new_area_colour_brightness'] = research_score(c4_1024, 36, 80, 40, 3)
    near['research_test_24x40_new_area_height'] = research_score(h4_1024, 24, 40, 40, 3)
    old = os.path.join(BASE, 'round1', 'area_4x4')
    if find(old, 'height'):
        near['research_test_36x80_ROUND_1_area_height'] = research_score(cv2.resize(load_grey(old, 'height'), (1024, 1024), interpolation=cv2.INTER_AREA), 36, 80, 40, 3)
    if not quick:
        h4_full = load_grey(os.path.join(area, 'area_4x4'), 'height')          # the same 2508 dots across as the look checker used
        c4_full = load_grey(os.path.join(area, 'area_4x4'), 'colour')
        near['look_checker_test_200x380_dots_new_area_height_50_pieces'] = checker_score(h4_full, 4, 50, 3)
        near['look_checker_test_200x380_dots_new_area_height_other_draw'] = checker_score(h4_full, 4, 50, 4)
        near['look_checker_test_200x380_dots_new_area_colour_brightness'] = checker_score(c4_full, 4, 50, 3)
        if find(old, 'height'):
            near['look_checker_test_200x380_dots_ROUND_1_area_height'] = checker_score(load_grey(old, 'height'), 4, 50, 3)
            near['look_checker_test_200x380_dots_ROUND_1_area_height_other_draw'] = checker_score(load_grey(old, 'height'), 4, 50, 4)
        near['look_checker_test_200x380_dots_plain_source_repeated_height'] = checker_score(cv2.resize(np.tile(np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'height_as_uploaded.png'))).astype(np.float32) / 255.0, (4, 4)), (1254, 1254), interpolation=cv2.INTER_AREA), 4, 30, 3)
    result['near_copies'] = near
    result.update(switched_part(area, quick))
    # 6. seam test and first tile
    result['seam_test_default_tile_2x2'] = seam_test(area)
    tile_folder = os.path.join(BASE, 'outputs', 'main_seed1')
    if find(tile_folder, 'height'):
        result['first_tile_of_the_area_versus_the_default_tile'] = first_tile_check(area, tile_folder)
    with open('proc-work/recipes/wood_from_displacement/check_honesty/round2/repeat_tests_rerun.json', 'w') as handle:
        json.dump(result, handle, indent=1)
    print(json.dumps(result, indent=1)[:8000])


if __name__ == '__main__':
    main()
