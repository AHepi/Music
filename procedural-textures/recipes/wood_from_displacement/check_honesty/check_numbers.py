# What this does (plain words): the honesty checker's own measurements of the wood-from-maps pictures, written independently of the builder's scripts.
# It needs only numpy and cv2 (no Blender). It checks: (a) the half-tile slide test, (b) whether the default tile wraps without a step at its own edges,
# (c) whether the 4 x 4 area in the folder really is what the recipe makes (one full-size piece baked again today), (d) how much the 16 tiles of the
# 4 x 4 area look like each other, (e) the shift test, (f) how often a dot of the source map is used (from the exact "which source dot" pictures).
# Use: python3 -I check_numbers.py
# NOTE: the big pictures it reads (rebake_default_1254, shift_half, crop_1p5_1p5) were deleted afterwards to save disk (the folder must stay under 150 MB). The answers are kept in check_numbers.json.
# To redo: bake the default tile with the standard harness command into rebake_default_1254, and run ../tools/run_jobs.py with jobs_check.json.
import json
import math
import os

import cv2
import numpy as np

CK = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(CK, '..'))
REF = os.path.abspath(os.path.join(W, '..', '..', 'reference', 'wood'))
T = 1254
out = {}


def rd(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a.ndim == 3:
        a = a[..., :3][..., ::-1]
    a = a.astype(np.float64)
    return a / (65535.0 if a.dtype != np.uint8 and a.max() > 255 else 255.0)


def h16(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    a = a[..., 0] if a.ndim == 3 else a
    return a.astype(np.float64) / (255.0 if a.dtype == np.uint8 else 65535.0)


# ---------------------------------------------------------------- (a) half-tile slide test (a fresh bake with shift 0.5 / 0.5 against the fresh default bake slid by hand)
base_c, base_h = rd(f'{CK}/rebake_default_1254/colour.png'), h16(f'{CK}/rebake_default_1254/height.png')
sh_c, sh_h = rd(f'{CK}/shift_half/colour.png'), h16(f'{CK}/shift_half/height.png')
res = {}
for name, a, b in (('colour', base_c, sh_c), ('height', base_h, sh_h)):
    best = None
    for dy in (-627, 627):          # the sign of the slide is not known from the job file: try both and report the better one and the wrong one
        for dx in (-627, 627):
            rolled = np.roll(a, (dy, dx), axis=(0, 1))
            d = np.abs(rolled - b)
            d = d.mean(axis=2) if d.ndim == 3 else d
            if best is None or d.mean() < best[0]:
                best = (float(d.mean()), float((d > 0.1).mean()), dy, dx)
    wrong = np.roll(a, (-313, -209), axis=(0, 1))
    dw = np.abs(wrong - b)
    dw = dw.mean(axis=2) if dw.ndim == 3 else dw
    res[name] = {'mean_abs_diff_slid_bake_vs_slid_picture': round(best[0], 5), 'share_over_0.1': round(best[1], 5), 'roll_used': [best[2], best[3]],
                 'wrong_slide_control_mean': round(float(dw.mean()), 4), 'wrong_slide_control_share_over_0.1': round(float((dw > 0.1).mean()), 4)}
out['half_tile_slide_test'] = res

# ---------------------------------------------------------------- (b) does the default tile wrap? jump across the wrap edge against ordinary neighbouring-dot jumps
def jumps(g):
    g = g if g.ndim == 2 else g.mean(axis=2)
    lr_wrap = np.abs(g[:, 0] - g[:, -1]).mean()
    lr_norm = np.abs(g[:, 1:] - g[:, :-1]).mean()
    tb_wrap = np.abs(g[0, :] - g[-1, :]).mean()
    tb_norm = np.abs(g[1:, :] - g[:-1, :]).mean()
    rows = np.abs(g[1:, :] - g[:-1, :]).mean(axis=1)       # jump per dot line going down: the row boundaries show as peaks
    return {'left_right_wrap_jump_over_typical': round(float(lr_wrap / lr_norm), 3), 'top_bottom_wrap_jump_over_typical': round(float(tb_wrap / tb_norm), 3),
            'top_bottom_wrap_jump_over_the_median_dot_line_jump': round(float(tb_wrap / np.median(rows)), 3), 'largest_ordinary_dot_line_jump_over_median': round(float(rows.max() / np.median(rows)), 3)}


ref_h = np.asarray(cv2.imread(f'{REF}/height_as_uploaded.png', cv2.IMREAD_UNCHANGED)).astype(np.float64) / 255.0
out['tile_wrap_edges'] = {'new_tile_height': jumps(base_h), 'new_tile_colour': jumps(base_c), 'uploaded_height_for_comparison': jumps(ref_h)}

# ---------------------------------------------------------------- (c) the 4 x 4 area in the folder is the recipe's output: compare a fresh full-size piece with the area picture
area_h = h16(f'{W}/area/area_4x4/height.png')            # 2508 dots, shrunk to 8 bit after the measurements
crop_h = h16(f'{CK}/crop_1p5_1p5/height.png')            # fresh bake, window [1.5, 1.5, 1], 1254 dots, tile 1254 source dots
half = area_h.shape[0] // 4                                # one tile in the 2508 picture
x0 = int(1.5 * half)
piece = area_h[x0:x0 + half, x0:x0 + half]
small = cv2.resize(crop_h, (half, half), interpolation=cv2.INTER_AREA)
out['area_4x4_matches_a_fresh_bake'] = {'area_shape': list(area_h.shape), 'piece_shape': list(piece.shape),
                                         'mean_abs_difference_area_piece_vs_fresh_bake_shrunk': round(float(np.abs(piece - small).mean()), 5),
                                         'correlation': round(float(np.corrcoef(piece.ravel(), small.ravel())[0, 1]), 4),
                                         'control_correlation_with_a_different_place_of_the_area': round(float(np.corrcoef(area_h[0:half, 0:half].ravel(), small.ravel())[0, 1]), 4)}

# ---------------------------------------------------------------- (d) the 16 tiles of the 4 x 4 area against each other, and against the default tile
tiles = [area_h[j * half:(j + 1) * half, i * half:(i + 1) * half] for j in range(4) for i in range(4)]
default_small = cv2.resize(base_h, (half, half), interpolation=cv2.INTER_AREA)
cc = np.array([[np.corrcoef(a.ravel(), b.ravel())[0, 1] for b in tiles] for a in tiles])
off = cc[~np.eye(16, dtype=bool)]
to_default = [float(np.corrcoef(t.ravel(), default_small.ravel())[0, 1]) for t in tiles]
out['tiles_of_the_4x4_area'] = {'correlation_between_two_different_tiles_max': round(float(off.max()), 3), 'mean': round(float(off.mean()), 3),
                                'correlation_with_the_default_tile_max': round(float(max(to_default)), 3), 'first_tile_of_area_vs_default_tile': round(to_default[0], 3)}


# ---------------------------------------------------------------- (e) shift test (the same definition as the builder's: Pearson correlation of the overlap)
def shift_corr(g, dx, dy):
    h, w = g.shape
    dx, dy = int(dx), int(dy)
    a = g[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
    b = g[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / math.sqrt(float((a * a).sum() * (b * b).sum()) + 1e-12))


rng = np.random.default_rng(5)
res = {}
plain = np.tile(cv2.resize(ref_h, (half, half), interpolation=cv2.INTER_AREA), (4, 4))
for name, g in (('new_4x4_area_height', area_h), ('plain_uploaded_map_repeated_4x4', plain)):
    special = {k: round(shift_corr(g, ux * half, uy * half), 3) for k, (ux, uy) in {'one_tile_across': (1, 0), 'one_tile_down': (0, 1), 'one_tile_diagonal': (1, 1), 'two_tiles_across': (2, 0), 'half_tile_across': (0.5, 0)}.items()}
    bg = []
    while len(bg) < 300:
        ux, uy = rng.uniform(-3.2, 3.2, 2)
        if abs(ux) < 0.3 and abs(uy) < 0.3:
            continue
        if (abs(ux - round(ux)) < 0.08 and round(ux) != 0) or (abs(uy - round(uy)) < 0.08 and round(uy) != 0):
            continue
        bg.append(shift_corr(g, ux * half, uy * half))
    res[name] = {'special': special, 'background_highest_of_300_random_shifts': round(float(np.max(bg)), 3), 'background_mean': round(float(np.mean(bg)), 3)}
# the default tile repeated on purpose (must be 1.0)
rep = np.tile(default_small, (4, 4))
res['default_tile_repeated_4x4_on_purpose'] = {'one_tile_across': round(shift_corr(rep, half, 0), 3)}
out['shift_test'] = res

# ---------------------------------------------------------------- (f) source reuse from the exact 'which source dot' pictures (kept 16-bit)
sx = h16(f'{W}/area/debug_source_x/height.png') * T
sy = h16(f'{W}/area/debug_source_y/height.png') * T
size = sx.shape[0]
dpp = 4 * T / size
ix = np.clip(np.round(sx - 0.5).astype(np.int64), 0, T - 1)
iy = np.clip(np.round(sy - 0.5).astype(np.int64), 0, T - 1)
counts = np.bincount((iy * T + ix).ravel(), minlength=T * T).astype(np.float64) * dpp ** 2
used = counts > 0
out['source_reuse_4x4'] = {'share_of_source_dots_used': round(float(used.mean()), 3), 'times_a_used_dot_appears_mean_median_p90': [round(float(counts[used].mean()), 1), round(float(np.median(counts[used])), 1), round(float(np.percentile(counts[used], 90)), 1)],
                           'debug_picture_shape': list(sx.shape), 'debug_dtype_16bit': bool(cv2.imread(f'{W}/area/debug_source_x/height.png', cv2.IMREAD_UNCHANGED).dtype == np.uint16)}

with open(f'{CK}/check_numbers.json', 'w') as handle:
    json.dump(out, handle, indent=1)
print(json.dumps(out, indent=1))
