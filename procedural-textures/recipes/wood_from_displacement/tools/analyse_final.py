# What this does (plain words): the small checks on the finished pictures of the wood-from-maps recipe, written to scores/checks_round1.json:
#   * SOURCE UNCHANGED: with the arrangement switched off (setting debug.source_unchanged) the recipe must give back the uploaded height map, and the
#     normal map made from it (strength 8) must give back the uploaded normal map. This proves the picture-reading pipeline (nodes, the photograph
#     with a narrow pixel filter, the normal rule) adds nothing of its own.
#   * HALF-TILE SHIFT: the default tile baked with the whole pattern slid by half a tile must equal the normal bake slid by half a tile (so the tile
#     repeats without a seam). A wrong slide is the control.
#   * COLOUR AND RELIEF MATCH: correlation of colour brightness with height, MAIN seeds 1-3, the area, and the uploaded maps for comparison.
#   * COLOUR MAP versus PALETTE: colour difference (Delta E) between the MAIN and COMPARISON colour of the same arrangement.
#   * SEED DIFFERENCE: how different two seeds are (mean brightness difference, correlation).
# Run with:  python3 -I tools/analyse_final.py      (numpy, PIL, cv2; no Blender)
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


def rgb(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255.0


def height16(path):
    return cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0


def luma(c):
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114


def srgb_to_lab(c):
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def main():
    out = {'what_this_is': 'Small checks on the finished wood-from-maps pictures (tools/analyse_final.py). Seed 1 unless it says otherwise.'}
    # ---- source unchanged
    d = os.path.join(BASE, 'tests', 'renders', 'source_unchanged')
    if os.path.exists(os.path.join(d, 'height.png')):
        up_h = np.asarray(Image.open(os.path.join(REF, 'height_as_uploaded.png'))).astype(np.float64) / 255.0
        h = height16(os.path.join(d, 'height.png'))
        up_c = rgb(os.path.join(REF, 'colour.png'))
        c = rgb(os.path.join(d, 'colour.png'))
        n = mn.normal_from_height(cv2.imread(os.path.join(d, 'height.png'), cv2.IMREAD_UNCHANGED), 8.0)
        up_n = cv2.imread(os.path.join(REF, 'normal.png'), cv2.IMREAD_UNCHANGED)[..., ::-1].astype(np.float64) / 255.0 * 2 - 1
        out['source_unchanged_check'] = {
            'height_mean_absolute_difference_to_uploaded_0_to_1': round(float(np.abs(h - up_h).mean()), 5),
            'height_share_of_dots_differing_by_more_than_2_of_255': round(float((np.abs(h - up_h) > 2 / 255).mean()), 4),
            'colour_mean_absolute_difference_to_uploaded_0_to_1': round(float(np.abs(c - up_c).mean()), 5),
            'normal_from_baked_height_strength_8_mean_absolute_difference_x_y_z': [round(float(np.abs(n[..., i] - up_n[..., i]).mean()), 4) for i in range(3)],
            'for_comparison_the_normal_rule_on_the_uploaded_height_itself_x_y_z': [round(float(np.abs(mn.normal_from_height(np.round(up_h * 255).astype(np.uint8), 8.0)[..., i] - up_n[..., i]).mean()), 4) for i in range(3)]}
    # ---- half tile shift
    d0, d1 = os.path.join(BASE, 'tests', 'renders', 'shift_0'), os.path.join(BASE, 'tests', 'renders', 'shift_half')
    if os.path.exists(os.path.join(d1, 'height.png')):
        res = {}
        for channel, loader in (('colour', rgb), ('height', lambda p: height16(p)[..., None] * np.ones(3))):
            a, b = loader(os.path.join(d0, channel + '.png')), loader(os.path.join(d1, channel + '.png'))
            half = 627
            rolled = np.roll(a, (-half, -half), axis=(0, 1))
            wrong = np.roll(a, (-half // 2 + 7, -half // 3), axis=(0, 1))
            diff = np.abs(rolled - b).mean(axis=2)
            wdiff = np.abs(wrong - b).mean(axis=2)
            res[channel] = {'slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1': round(float(diff.mean()), 5), 'share_of_dots_differing_by_more_than_0.1': round(float((diff > 0.1).mean()), 5),
                            'wrong_slide_control_mean': round(float(wdiff.mean()), 4), 'wrong_slide_control_share_over_0.1': round(float((wdiff > 0.1).mean()), 4)}
        out['half_tile_shift_test_1254'] = res
    # ---- colour and relief match
    corr = {}
    for name, folder in (('main_seed1', 'outputs/main_seed1'), ('main_seed2', 'outputs/main_seed2'), ('main_seed3', 'outputs/main_seed3'), ('comparison_seed1_(colour_from_height)', 'outputs/main_seed1')):
        cp = os.path.join(BASE, folder.replace('main', 'comparison') if name.startswith('comparison') else folder, 'colour.png')
        if os.path.exists(cp):
            corr[name] = round(float(np.corrcoef(luma(rgb(cp)).ravel(), height16(os.path.join(BASE, folder, 'height.png')).ravel())[0, 1]), 3)
    corr['uploaded_maps'] = round(float(np.corrcoef(luma(rgb(os.path.join(REF, 'colour.png'))).ravel(), (np.asarray(Image.open(os.path.join(REF, 'height_as_uploaded.png'))).astype(float) / 255).ravel())[0, 1]), 3)
    out['colour_brightness_versus_height_correlation'] = corr
    # ---- palette versus map colour
    de = {}
    for s in (1, 2, 3):
        a, b = os.path.join(BASE, 'outputs', f'main_seed{s}', 'colour.png'), os.path.join(BASE, 'outputs', f'comparison_seed{s}', 'colour.png')
        if os.path.exists(a) and os.path.exists(b):
            d_e = np.sqrt(((srgb_to_lab(rgb(a)) - srgb_to_lab(rgb(b))) ** 2).sum(-1))
            ma, mb = rgb(a), rgb(b)
            de[f'seed{s}'] = {'mean_delta_e': round(float(d_e.mean()), 2), 'ninety_fifth_percent_delta_e': round(float(np.percentile(d_e, 95)), 2),
                              'mean_colour_main_0_255': [round(float(v) * 255, 1) for v in ma.reshape(-1, 3).mean(0)], 'mean_colour_comparison_0_255': [round(float(v) * 255, 1) for v in mb.reshape(-1, 3).mean(0)]}
    out['main_versus_comparison_colour'] = de
    # ---- seeds
    h1, h2, h3 = [height16(os.path.join(BASE, 'outputs', f'main_seed{s}', 'height.png')) for s in (1, 2, 3)] if os.path.exists(os.path.join(BASE, 'outputs', 'main_seed3', 'height.png')) else (None,) * 3
    if h1 is not None:
        out['seed_difference_height'] = {'mean_absolute_difference_seed1_seed2': round(float(np.abs(h1 - h2).mean()), 3), 'mean_absolute_difference_seed1_seed3': round(float(np.abs(h1 - h3).mean()), 3),
                                         'correlation_seed1_seed2': round(float(np.corrcoef(h1.ravel(), h2.ravel())[0, 1]), 3), 'correlation_seed1_seed3': round(float(np.corrcoef(h1.ravel(), h3.ravel())[0, 1]), 3)}
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(os.path.join(BASE, 'scores', 'checks_round1.json'), 'w') as handle:
        json.dump(out, handle, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
