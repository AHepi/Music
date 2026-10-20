# What this does: measures the test pictures made by run_tests.py (they are in tests/renders/) and writes the numbers into
# research/tests_results.json. Numbers it makes:
#   * seam check   : how big the jump is across the tile edge compared with a normal jump between neighbouring dot lines (1.0 = no seam)
#   * repeat check : for 40 random small patches of a big picture, how well the best match elsewhere in the same picture fits
#                    (1.0 = an identical copy exists, about 0.3 = nothing alike). Looks at left-right flipped copies too.
#   * grey spread  : how much contrast the grey picture keeps (the source map has a standard deviation of 0.28)
#   * gap lines    : how many dark gap lines between board rows survive
#   * height versus colour : how well the colour brightness predicts the height in the same picture
#   * normal check : the normal map made from the plain full-size picture at strength 8 versus the uploaded normal map
# Run with:  python3 -I analyse_tests.py      (numpy, PIL and cv2 only; no Blender)
import json
import os
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(HERE, 'renders')
PROC = 'proc-work/'
RES = {'what_this_is': 'Numbers measured on the research test pictures (made by run_tests.py from the job files in this folder). Written by analyse_tests.py. Every block has a note that says what the number means.'}


def load(name, grey=True):
    path = os.path.join(REN, name)
    if not os.path.exists(path):
        return None
    image = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255.0
    return image[..., 1] if grey else image   # grey pictures: red = green = blue; colour pictures are compared through their brightness elsewhere


def luma(image):
    return 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]


def seam_ratio(a, period, rows_per_tile=5):
    """Jump across the line between dot lines (period-1, period) [and the outer wrap edge] over the typical jump; x and y.
    For y the tile edge is also compared with the other row boundaries inside the picture (a row boundary always has a bigger jump than an
    average dot line, because every row starts with a dark gap)."""
    out = {}
    h, w = a.shape
    typical_x = np.abs(a[:, 1:] - a[:, :-1]).mean()
    typical_y = np.abs(a[1:] - a[:-1]).mean()
    out['tile_edge_vertical_line_jump_over_typical_jump'] = round(float(np.abs(a[:, period] - a[:, period - 1]).mean() / typical_x), 2)
    out['outer_wrap_left_right_jump_over_typical_jump'] = round(float(np.abs(a[:, 0] - a[:, -1]).mean() / typical_x), 2)
    pitch = period / rows_per_tile
    boundaries = [int(round(k * pitch)) for k in range(1, int(round(h / pitch)))]
    jumps = {y: float(np.abs(a[y] - a[y - 1]).mean()) for y in boundaries}
    tile_edge = jumps.pop(period, None)
    other = list(jumps.values())
    out['tile_edge_horizontal_line_jump'] = round(tile_edge, 3) if tile_edge is not None else None
    out['ordinary_row_boundary_jumps_min_mean_max'] = [round(min(other), 3), round(float(np.mean(other)), 3), round(max(other), 3)]
    out['outer_wrap_top_bottom_jump'] = round(float(np.abs(a[0] - a[-1]).mean()), 3)
    return out


def same_tile_check(a, period):
    """In tile mode the 2 x 2 picture should be 4 copies of one tile (small differences come from the random sampling of the render)."""
    q = [a[:period, :period], a[:period, period:], a[period:, :period], a[period:, period:]]
    diffs = [np.abs(q[0] - x) for x in q[1:]]
    return {'mean_difference_between_tiles_0_to_1': round(float(np.mean([d.mean() for d in diffs])), 4),
            'share_of_dots_differing_by_over_0.05': round(float(np.mean([(d > 0.05).mean() for d in diffs])), 4)}


def repeat_score(a, tpl_h=36, tpl_w=80, count=40, seed=3, rows=20):
    """Does a board-sized piece of the picture appear again somewhere else? A template (tpl_h x tpl_w dots) is cut from the inside of a board row
    and searched for in all the OTHER rows of the same picture (same height within the row, plus or minus 3 dots), also left-right flipped.
    The score is the best normalised match (1.0 = identical copy, about 0.3 = nothing alike). Rows are 1/rows of the picture high."""
    rng = np.random.default_rng(seed)
    h, w = a.shape
    pitch = h / rows
    a8 = (a * 255).astype(np.uint8)
    scores = []
    tries = 0
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
                    res = res.copy(); res[:, max(0, x - tpl_w):x + tpl_w] = -1.0
                best = max(best, float(res.max()))
        scores.append(best)
    scores = np.array(scores)
    return {'median_best_match': round(float(np.median(scores)), 2), 'ninetieth_percent': round(float(np.percentile(scores, 90)), 2),
            'worst': round(float(scores.max()), 2), 'share_with_a_near_copy_over_0.8': round(float((scores > 0.8).mean()), 2), 'templates': int(len(scores))}


def gap_lines(a):
    """Number of dark horizontal gap lines: runs of lines where over half the dots are darker than 20 per cent grey."""
    frac = (a < 0.2).mean(1)
    flag = frac > 0.5
    runs = int(((flag[1:]) & (~flag[:-1])).sum() + (1 if flag[0] else 0))
    return runs


def grey_spread(a):
    hist = np.histogram(a, bins=20, range=(0, 1))[0] / a.size
    return {'standard_deviation': round(float(a.std()), 3), 'mean': round(float(a.mean()), 3),
            'unevenness_of_spread_(0 = perfectly even, bigger = bell shaped or lumpy)': round(float(np.abs(hist - 0.05).sum() / 2), 3)}


def lab(image):
    bgr = (np.clip(image, 0, 1) * 255).astype(np.uint8)[..., ::-1]
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32) * np.array([100 / 255, 1, 1], np.float32) - np.array([0, 128, 128], np.float32)


# ---------------------------------------------------------------- 1. seams (2 x 2 pictures made in tile mode, and the plain repeat)
seams = {}
for key, name in (('plain source repeated', 'plain_repeat_2x2_height.png'), ('pieces (curated), tile mode, height', 'seam_pieces_2x2_height.png'),
                  ('whole idea (masks), tile mode, height', 'seam_masks_2x2_height.png'), ('hex Gaussian, tile mode, height', 'hex_gauss_tilemode_2x2_height.png')):
    a = load(name)
    if a is None:
        continue
    seams[key] = seam_ratio(a, a.shape[0] // 2)
    seams[key]['four_tiles_compared'] = same_tile_check(a, a.shape[0] // 2)
for key, name in (('pieces (curated), tile mode, colour brightness', 'seam_pieces_2x2_colour.png'), ('whole idea (masks), tile mode, colour brightness', 'seam_masks_2x2_colour.png')):
    c = load(name, grey=False)
    if c is not None:
        seams[key] = seam_ratio(luma(c), c.shape[0] // 2)
        seams[key]['four_tiles_compared'] = same_tile_check(luma(c), c.shape[0] // 2)
RES['seam_check_2x2_tile_mode'] = {'note': 'ratio about 1.0 = no seam. The source picture repeated by itself is the comparison.', 'results': seams}

# ---------------------------------------------------------------- 2. repeat check on 4 x 4 pictures (1024 dots, one tile = 256 dots)
rep = {}
for key, name, is_colour in (('plain source repeated (4 x 4)', 'plain_repeat_4x4_height.png', False),
                             ('pieces, rows only (sideways shift + flip)', 'pieces_rows_only_b2_4x4_height.png', False),
                             ('pieces, free random start (full)', 'pieces_full_b2_4x4_height.png', False),
                             ('pieces, knots rationed (curated)', 'pieces_curated_b2_4x4_height.png', False),
                             ('pieces + stamps (curated + bombing)', 'bomb_area_4x4_height.png', False),
                             ('whole idea: pieces + stamps + large masks', 'masks_full_4x4_height.png', False),
                             ('pieces, free random start, shorter boards (3 per row)', 'pieces_full_4x4_height.png', False),
                             ('pieces, knots rationed, shorter boards (3 per row)', 'pieces_curated_4x4_height.png', False),
                             ('random tile bag of 16', 'bag16_b2_4x4_height.png', False),
                             ('random tile bag of 64', 'bag64_b2_4x4_height.png', False),
                             ('Voronoi patches with random shift (rows destroyed: score not comparable)', 'voronoi_patches_area_4x4_height.png', False),
                             ('whole idea, shorter boards (3 per row)', 'masks_b3_4x4_height.png', False),
                             ('whole idea, short boards (4 per row)', 'masks_b4_4x4_height.png', False),
                             ('hex Gaussian blend of the whole map (rows destroyed: score not comparable)', 'hex_gauss_area_4x4_height.png', False)):
    a = load(name)
    if a is not None:
        rep[key] = {'board_size_template_36x80': repeat_score(a), 'feature_size_template_24x40': repeat_score(a, 24, 40)}
RES['repeat_check_4x4'] = {'note': 'Height pictures, 4 x 4 tiles in 1024 dots, 20 rows. 40 random templates cut from inside a board row, searched in all other rows (left-right flipped too). '
                                   '1.0 = identical copy exists. A 36 x 80 template is about 175 x 390 source dots (most of a board); 24 x 40 is about 120 x 195 source dots (a knot or a crack pattern). '
                                   'Vertical zoom differences of up to 12 per cent between boards lower the score of a copy a little, so a score near 0.8 still means very alike.', 'results': rep}

# ---------------------------------------------------------------- 3. hex variants
hexres = {}
src = np.asarray(Image.open(PROC + 'reference/wood/height_as_uploaded.png')).astype(np.float32) / 255.0
hexres['the source map itself'] = dict(grey_spread(src), gap_lines_found=gap_lines(src))
for key, name in (('hex hard patches', 'hex_hard_1x1_height.png'), ('hex linear blend', 'hex_linear_1x1_height.png'), ('hex variance-kept blend', 'hex_variance_1x1_height.png'),
                  ('hex Gaussian (Heitz-Neyret style) blend', 'hex_gauss_1x1_height.png'), ('Voronoi patches (hard edges)', 'voronoi_patches_1x1_height.png'), ('pieces (curated)', 'pieces_curated_1x1_height.png'), ('plain repeat 512 view', 'plain_repeat_1x1_height.png')):
    a = load(name)
    if a is not None:
        hexres[key] = dict(grey_spread(a), gap_lines_found=gap_lines(a))
RES['grey_spread_and_gap_lines'] = {'note': 'The source has 4 clear dark gap lines between its 5 rows. A 512-dot view of the whole source shows them too (the "plain repeat 512 view" line).', 'results': hexres}

# ---------------------------------------------------------------- 4. height versus colour in the same arrangement
match = {}
for key, h_name, c_name in (('pieces (curated)', 'pieces_curated_1x1_height.png', 'pieces_curated_1x1_colour.png'), ('pieces + stamps', 'bomb_1x1_height.png', 'bomb_1x1_colour.png'),
                            ('whole idea (masks on)', 'masks_full_1x1_height.png', 'masks_full_1x1_colour.png'), ('whole idea (masks off)', 'masks_off_1x1_height.png', 'masks_off_1x1_colour.png'),
                            ('pieces + stamps made with a repeat zone', 'bomb_zone_1x1_height.png', 'bomb_zone_1x1_colour.png')):
    h = load(h_name); c = load(c_name, grey=False)
    if h is not None and c is not None:
        match[key] = round(float(np.corrcoef(luma(c).ravel(), h.ravel())[0, 1]), 3)
RES['colour_brightness_versus_height_correlation'] = {'note': 'Same arrangement, colour map sampled with exactly the same windows as the height map: how well the brightness of the colour predicts the height in the new picture '
                                                          '(the untouched source gives 0.981). Per-board tone and large masks lower it a little by design.', 'results': match}

# ---------------------------------------------------------------- 5. palette-from-height versus colour map
a, b = load('masks_full_1x1_colour.png', grey=False), load('palette_1x1_colour.png', grey=False)
if a is not None and b is not None:
    de = np.sqrt(((lab(a) - lab(b)) ** 2).sum(-1))
    RES['colour_from_height_comparison'] = {'mean_DeltaE_between_colour_map_version_and_palette_version': round(float(de.mean()), 2), '95th_percent': round(float(np.percentile(de, 95)), 2),
                                            'mean_colour_map_version_rgb_0_255': [round(float(v) * 255, 1) for v in a.reshape(-1, 3).mean(0)],
                                            'mean_palette_version_rgb_0_255': [round(float(v) * 255, 1) for v in b.reshape(-1, 3).mean(0)],
                                            'note': 'Same arrangement, same tone shifts, same masks. Only the colour source differs: the colour map versus a palette mapped from the height.'}

# ---------------------------------------------------------------- 6. normal made from sampled height at strength 8 versus the uploaded normal
def sobel(height, strength):
    hx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / 2.0
    hy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / 2.0
    nx, ny, nz = -strength * hx, strength * hy, np.ones_like(height)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / n, ny / n, nz / n], -1)


nref = np.asarray(Image.open(PROC + 'reference/wood/normal.png')).astype(np.float64) / 255 * 2 - 1
normal_res = {}
for key, name in (('harness default sampling (4 samples, pixel filter width 1.0)', 'plain_full_1x1_height.png'), ('sharp sampling (1 sample, pixel filter width 0.01)', 'plain_full_sharp_1x1_height.png')):
    full = load(name)
    if full is not None:
        mine = sobel(full.astype(np.float64), 8.0)
        normal_res[key] = {'height_render_versus_uploaded_height_mean_abs_diff_0_to_1': round(float(np.abs(full - src).mean()), 4),
                           'sobel_strength_8_normal_versus_uploaded_normal_mean_abs_diff_xyz': [round(float(np.abs(mine[..., i] - nref[..., i]).mean()), 4) for i in range(3)]}
RES['normal_check'] = {'note': 'The plain source rendered at full size (1254) through the Blender nodes, then turned into a normal map at strength 8, compared with the uploaded OpenGL normal map. '
                               'With the numpy filter straight on the uploaded height the difference is 0.004.', 'results': normal_res}

# ---------------------------------------------------------------- 7. picture reading modes (sharpness of arranged windows)
def grad(a):
    return float((np.abs(a[:, 1:] - a[:, :-1]).mean() + np.abs(a[1:] - a[:-1]).mean()) / 2)


modes = {}
base_src = load('plain_full_sharp_1x1_height.png')
for mode in ('closest', 'linear', 'cubic'):
    a = load(f'pieces_sharp_{mode}_1x1_height.png')
    if a is not None and base_src is not None:
        modes[mode] = round(grad(a) / grad(base_src), 3)
RES['reading_mode_edge_energy_ratio_to_source'] = {'note': 'Mean dot-to-dot jump of an arranged tile (rows squeezed 4 to 14 per cent to fit, so the number is above 1 for every mode) divided by the source value. '
                                                      'Compare the three modes with each other: Closest keeps the most edge energy (and shows staircase edges), Linear a little less, Cubic (a smoothing B-spline in Blender) the least.', 'results': modes}

with open(os.path.join(PROC, 'recipes/wood_from_displacement/research/tests_results.json'), 'w') as handle:
    json.dump(RES, handle, indent=1)
print(json.dumps(RES, indent=1))
