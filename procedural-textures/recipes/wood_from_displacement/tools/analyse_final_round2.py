# What this does (plain words): the small checks on the finished pictures of the wood-from-maps recipe, round 2, written to scores/checks_round2.json.
# (Round 1 version: tools/analyse_final.py. This one reads the files where round 2 puts them, and it never throws away a section that was
# measured earlier: when a picture is missing, that section is left as it was in the file.)
#   * SOURCE UNCHANGED: with the arrangement switched off (setting debug.source_unchanged) the recipe must give back the uploaded height map, and the
#     normal map made from it (strength 8) must give back the uploaded normal map. This proves the picture-reading pipeline adds nothing of its own.
#   * HALF-TILE SHIFT: the default tile baked with the whole pattern slid by half a tile must equal the normal bake slid by half a tile (so the tile
#     repeats without a seam). A wrong slide is the control.
#   * TILE EDGE JUMPS of the default tile when it is repeated (left-right, top-bottom) compared with an ordinary neighbour step.
#   * COLOUR AND RELIEF MATCH: correlation of colour brightness with height, MAIN seeds 1-3, COMPARISON, and the uploaded maps.
#   * COLOUR MAP versus PALETTE: colour difference (Delta E) between the MAIN and COMPARISON colour of the same arrangement.
#   * SEED DIFFERENCE: how different two seeds are (correlation of their heights).
#   * WINDOW SQUEEZE: from the exact "which source dot" pictures of the seed 1 tile (tests/renders/source_x_seed1, source_y_seed1): how many source dots does one picture dot
#     cover along and across the grain? About 1 is right. A value under 0.6 means the source is magnified (blurred / smeared); round 2 had such smeared strips at first.
# Run with:  python3 -I tools/analyse_final_round2.py      (numpy, PIL, cv2; no Blender)
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import make_normal_from_height as mn  # noqa: E402

REF = os.path.join(PROC, 'reference', 'wood')
OUT = os.path.join(BASE, 'scores', 'checks_round2.json')


def rgb(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255.0


def height16(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    a = a[..., 0] if a.ndim == 3 else a
    return a.astype(np.float64) / (255.0 if a.dtype == np.uint8 else 65535.0)


def luma(c):
    return c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114


def srgb_to_lab(c):
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def main():
    out = {}
    if os.path.exists(OUT):
        with open(OUT) as handle:
            out = json.load(handle)
    out['what_this_is'] = 'Small checks on the finished wood-from-maps pictures, round 2 (tools/analyse_final_round2.py). Seed 1 unless it says otherwise. A section is only replaced when its pictures exist.'
    # ---- source unchanged (the colour part needs tests/renders/source_unchanged/colour.png, which tools/shrink_area_files_round2.py deletes: then the earlier colour numbers are kept)
    d = os.path.join(BASE, 'tests', 'renders', 'source_unchanged')
    if os.path.exists(os.path.join(d, 'height.png')):
        up_h = np.asarray(Image.open(os.path.join(REF, 'height_as_uploaded.png'))).astype(np.float64) / 255.0
        h = height16(os.path.join(d, 'height.png'))
        n = mn.normal_from_height(cv2.imread(os.path.join(d, 'height.png'), cv2.IMREAD_UNCHANGED)[..., 0], 8.0)
        up_n = cv2.imread(os.path.join(REF, 'normal.png'), cv2.IMREAD_UNCHANGED)[..., ::-1].astype(np.float64) / 255.0 * 2 - 1
        section = out.get('source_unchanged_check', {})
        section.update({
            'height_mean_absolute_difference_to_uploaded_0_to_1': round(float(np.abs(h - up_h).mean()), 5),
            'height_share_of_dots_differing_by_more_than_2_of_255': round(float((np.abs(h - up_h) > 2 / 255).mean()), 4),
            'normal_from_baked_height_strength_8_mean_absolute_difference_x_y_z': [round(float(np.abs(n[..., i] - up_n[..., i]).mean()), 4) for i in range(3)],
            'for_comparison_the_normal_rule_on_the_uploaded_height_itself_x_y_z': [round(float(np.abs(mn.normal_from_height(np.round(up_h * 255).astype(np.uint8), 8.0)[..., i] - up_n[..., i]).mean()), 4) for i in range(3)]})
        if os.path.exists(os.path.join(d, 'colour.png')):
            section['colour_mean_absolute_difference_to_uploaded_0_to_1'] = round(float(np.abs(rgb(os.path.join(d, 'colour.png')) - rgb(os.path.join(REF, 'colour.png'))).mean()), 5)
        out['source_unchanged_check'] = section
    # ---- half tile shift (colour part kept from the earlier measurement when its colour pictures were deleted)
    d0, d1 = os.path.join(BASE, 'outputs', 'main_seed1'), os.path.join(BASE, 'tests', 'renders', 'shift_half')
    res = out.get('half_tile_shift_test_1254', {})
    for channel, loader in (('colour', rgb), ('height', lambda p: height16(p)[..., None] * np.ones(3))):
        pa, pb = os.path.join(d0, channel + '.png'), os.path.join(d1, channel + '.png')
        if os.path.exists(pa) and os.path.exists(pb):
            a, b = loader(pa), loader(pb)
            half = 627
            rolled = np.roll(a, (-half, -half), axis=(0, 1))
            wrong = np.roll(a, (-half // 2 + 7, -half // 3), axis=(0, 1))
            diff = np.abs(rolled - b).mean(axis=2)
            wdiff = np.abs(wrong - b).mean(axis=2)
            res[channel] = {'slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1': round(float(diff.mean()), 5), 'share_of_dots_differing_by_more_than_0.1': round(float((diff > 0.1).mean()), 5),
                            'wrong_slide_control_mean': round(float(wdiff.mean()), 4), 'wrong_slide_control_share_over_0.1': round(float((wdiff > 0.1).mean()), 4)}
    if res:
        out['half_tile_shift_test_1254'] = res
    # ---- tile edge jumps of the default tile repeated (wrap-around) for the three seeds
    jumps = {}
    for sd in (1, 2, 3):
        p = os.path.join(BASE, 'outputs', f'main_seed{sd}')
        if not os.path.exists(os.path.join(p, 'height.png')):
            continue
        for channel, loader in (('colour', lambda q: luma(rgb(q))), ('height', height16)):
            g = loader(os.path.join(p, channel + '.png'))
            typical_x, typical_y = np.abs(np.diff(g, axis=1)).mean(), np.abs(np.diff(g, axis=0)).mean()
            jumps[f'seed{sd}_{channel}'] = {'left_right_wrap_jump_over_a_typical_jump': round(float(np.abs(g[:, 0] - g[:, -1]).mean() / typical_x), 2),
                                            'top_bottom_wrap_jump_over_a_typical_jump': round(float(np.abs(g[0] - g[-1]).mean() / typical_y), 2)}
    up_h = np.asarray(Image.open(os.path.join(REF, 'height_as_uploaded.png'))).astype(np.float64) / 255.0
    jumps['uploaded_height_for_comparison'] = {'left_right_wrap_jump_over_a_typical_jump': round(float(np.abs(up_h[:, 0] - up_h[:, -1]).mean() / np.abs(np.diff(up_h, axis=1)).mean()), 2),
                                               'top_bottom_wrap_jump_over_a_typical_jump': round(float(np.abs(up_h[0] - up_h[-1]).mean() / np.abs(np.diff(up_h, axis=0)).mean()), 2)}
    out['tile_wrap_edge_jumps'] = jumps
    # ---- is the tile edge just another row boundary? Compare the jump across the tile edge with the jumps across the ordinary row boundaries INSIDE the same tile
    # (every row boundary is a dark band with pebbles, so its jump is bigger than the average jump between neighbouring dot lines)
    peaks = {}
    for sd in (1, 2, 3):
        pth = os.path.join(BASE, 'outputs', f'main_seed{sd}', 'colour.png')
        if not os.path.exists(pth):
            continue
        g = luma(rgb(pth))
        typical = float(np.abs(np.diff(g, axis=0)).mean())
        prof = np.abs(np.diff(g, axis=0)).mean(axis=1) / typical            # jump between dot line y and y + 1, over a typical jump
        wrap = float(np.abs(g[0] - g[-1]).mean() / typical)
        found = []
        order = np.argsort(-prof)
        for y in order:
            if y < 12 or y > len(prof) - 12:
                continue
            if all(abs(int(y) - f[0]) > 80 for f in found):
                found.append((int(y), float(prof[y])))
            if len(found) == 4:
                break
        peaks[f'seed{sd}'] = {'jump_across_the_tile_edge_over_a_typical_jump': round(wrap, 2),
                              'jumps_across_the_four_strongest_ordinary_row_boundaries_inside_the_tile_(y_position, jump)': [[y, round(v, 2)] for y, v in sorted(found)]}
    if peaks:
        out['tile_edge_versus_ordinary_row_boundaries_colour'] = peaks
    # ---- colour and relief match
    corr = {}
    for name, cfolder, hfolder in (('main_seed1', 'main_seed1', 'main_seed1'), ('main_seed2', 'main_seed2', 'main_seed2'), ('main_seed3', 'main_seed3', 'main_seed3'),
                                   ('comparison_seed1_(colour_from_height)', 'comparison_seed1', 'main_seed1')):
        cp, hp = os.path.join(BASE, 'outputs', cfolder, 'colour.png'), os.path.join(BASE, 'outputs', hfolder, 'height.png')
        if os.path.exists(cp) and os.path.exists(hp):
            corr[name] = round(float(np.corrcoef(luma(rgb(cp)).ravel(), height16(hp).ravel())[0, 1]), 3)
    corr['uploaded_maps'] = round(float(np.corrcoef(luma(rgb(os.path.join(REF, 'colour.png'))).ravel(), up_h.ravel())[0, 1]), 3)
    out['colour_brightness_versus_height_correlation'] = corr
    # ---- palette versus map colour
    de = {}
    for sd in (1, 2, 3):
        a, b = os.path.join(BASE, 'outputs', f'main_seed{sd}', 'colour.png'), os.path.join(BASE, 'outputs', f'comparison_seed{sd}', 'colour.png')
        if os.path.exists(a) and os.path.exists(b):
            ma, mb = rgb(a), rgb(b)
            d_e = np.sqrt(((srgb_to_lab(ma) - srgb_to_lab(mb)) ** 2).sum(-1))
            de[f'seed{sd}'] = {'mean_delta_e': round(float(d_e.mean()), 2), 'ninety_fifth_percent_delta_e': round(float(np.percentile(d_e, 95)), 2),
                               'mean_colour_main_0_255': [round(float(v) * 255, 1) for v in ma.reshape(-1, 3).mean(0)], 'mean_colour_comparison_0_255': [round(float(v) * 255, 1) for v in mb.reshape(-1, 3).mean(0)],
                               'share_of_dots_more_blue_than_red_main_versus_comparison': [round(float((ma[..., 2] > ma[..., 0]).mean()), 3), round(float((mb[..., 2] > mb[..., 0]).mean()), 3)]}
    ref_c = rgb(os.path.join(REF, 'colour.png'))
    de['uploaded_colour_map_for_comparison_mean_colour_0_255_and_share_more_blue_than_red'] = [[round(float(v) * 255, 1) for v in ref_c.reshape(-1, 3).mean(0)], round(float((ref_c[..., 2] > ref_c[..., 0]).mean()), 3)]
    out['main_versus_comparison_colour'] = de
    # ---- seeds
    hs = [os.path.join(BASE, 'outputs', f'main_seed{s}', 'height.png') for s in (1, 2, 3)]
    if all(os.path.exists(p) for p in hs):
        h1, h2, h3 = [height16(p) for p in hs]
        out['seed_difference_height'] = {'correlation_seed1_seed2': round(float(np.corrcoef(h1.ravel(), h2.ravel())[0, 1]), 3), 'correlation_seed1_seed3': round(float(np.corrcoef(h1.ravel(), h3.ravel())[0, 1]), 3),
                                         'correlation_seed2_seed3': round(float(np.corrcoef(h2.ravel(), h3.ravel())[0, 1]), 3)}
    # ---- how much the windows are squeezed or stretched (blocks of 15 x 15 dots, median of the local scale)
    px, py = os.path.join(BASE, 'tests', 'renders', 'source_x_seed1', 'height.png'), os.path.join(BASE, 'tests', 'renders', 'source_y_seed1', 'height.png')
    if os.path.exists(px) and os.path.exists(py):
        sx, sy = height16(px) * 1254.0, height16(py) * 1254.0

        def block_median(a, k=15):
            h_, w_ = a.shape[0] // k * k, a.shape[1] // k * k
            return np.median(a[:h_, :w_].reshape(h_ // k, k, w_ // k, k), axis=(1, 3))
        across = block_median(np.abs(np.gradient(sy, axis=0)))
        along = block_median(np.abs(np.gradient(sx, axis=1)))
        out['window_squeeze_check_seed1_tile'] = {
            'source_dots_per_picture_dot_across_the_grain_percentiles_1_5_25_50_75_95': [round(float(v), 2) for v in np.percentile(across, [1, 5, 25, 50, 75, 95])],
            'source_dots_per_picture_dot_along_the_grain_percentiles_1_5_25_50_75_95': [round(float(v), 2) for v in np.percentile(along, [1, 5, 25, 50, 75, 95])],
            'share_of_blocks_across_under_0.6_(magnified_and_blurred)': round(float((across < 0.6).mean()), 4),
            'share_of_blocks_along_under_0.6': round(float((along < 0.6).mean()), 4)}
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(OUT, 'w') as handle:
        json.dump(out, handle, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
