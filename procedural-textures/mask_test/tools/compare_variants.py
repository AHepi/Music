# What this does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------
# It compares the baked versions of the slate (folders compare/1_node_made, 2_moss_stamps, 3_chip_stamps, 4_both_stamps, 5_both_multiplied) with the
# reference slate picture:
#   1. makes each version's normal map from its height (the reference's way, strength 7);
#   2. runs the look measures (olive share, tan share, largest moss clump, lightness spread inside moss, gradients ...) from
#      recipes/slate_layers/look_fixes/measure_look.py;
#   3. runs lib/texture_compare.py (same-kind score against the slate reference);
#   4. writes compare/measures.json and compare/measures_table.md;
#   5. draws the two sheets:  sheets/masks_compare.jpg (reference | node-made | stamps)   and   sheets/masks_compare_all_versions.jpg.
# Run:  python3 -I compare_variants.py [measures] [sheets]      (no argument = both)
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MASK = os.path.join(PROC, 'mask_test')
sys.path.insert(0, os.path.join(PROC, 'recipes', 'slate_layers', 'look_fixes'))
sys.path.insert(0, os.path.join(PROC, 'recipes', 'slate_layers', 'integration'))
import make_normal  # noqa: E402
import measure_look as ml  # noqa: E402

VARIANTS = ['1_node_made', '2_moss_stamps', '3_chip_stamps', '4_both_stamps', '5_both_multiplied']
NICE = {'reference': 'reference (the person\'s picture)', '1_node_made': '1 node-made masks (the copy, unchanged)', '2_moss_stamps': '2 generated stamps for moss',
        '3_chip_stamps': '3 generated stamps for chips', '4_both_stamps': '4 stamps for moss and chips', '5_both_multiplied': '5 node mask x stamp mask (moss and chips)'}
REFERENCE_COLOUR = os.path.join(PROC, 'reference', 'slate', 'colour.png')


def make_normals():
    for name in VARIANTS:
        folder = os.path.join(MASK, 'compare', name)
        height = cv2.imread(os.path.join(folder, 'height.png'), cv2.IMREAD_UNCHANGED)
        height = height[..., 0] if height.ndim == 3 else height
        normal = make_normal.sobel_normal_from_height(height, 7.0)
        cv2.imwrite(os.path.join(folder, 'normal.png'), ((normal * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])


def run_measures():
    make_normals()
    out = {'look_measures': {}, 'same_kind_score': {}}
    out['look_measures']['reference'] = ml.measure('reference')
    for name in VARIANTS:
        folder = os.path.join(MASK, 'compare', name)
        out['look_measures'][name] = ml.measure(folder)
        report_path = os.path.join(folder, 'score_same_kind.json')
        subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'texture_compare.py'), 'slate', folder, '--json', report_path],
                       stdout=subprocess.DEVNULL, check=True)
        report = json.load(open(report_path))
        out['same_kind_score'][name] = {'overall': report['overall'], 'groups': report['groups'], 'scores': report['scores']}
    json.dump(out, open(os.path.join(MASK, 'compare', 'measures.json'), 'w'), indent=1)
    lines = ['| picture | ' + ' | '.join(f'{label}' for label, _ in ml.ORDER[:11]) + ' |', '|---|' + '---|' * 11]
    for name in ['reference'] + VARIANTS:
        m = out['look_measures'][name]
        lines.append(f'| {NICE[name]} | ' + ' | '.join((fmt % m[label]) for label, fmt in ml.ORDER[:11]) + ' |')
    lines += ['', '| version | same-kind overall | colour | height | normal | tiling |', '|---|---|---|---|---|---|']
    for name in VARIANTS:
        s = out['same_kind_score'][name]
        g = s['groups']
        lines.append(f"| {NICE[name]} | {s['overall']:.3f} | {g['colour']:.3f} | {g['height']:.3f} | {g['normal']:.3f} | {g['tiling']:.3f} |")
    open(os.path.join(MASK, 'compare', 'measures_table.md'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


# ---------------------------------------------------------------------------------------------------------------- the sheets
def lab_masks(colour):
    light, a_star, b_star = ml.lab_of(colour)
    olive = (b_star > 6) & (a_star < 1)
    tan = (b_star > 6) & (a_star > 0) & (light > 30)
    return olive, tan


def best_window(mask, size=400, stride=25, avoid=None):
    """Top-left corner of the size x size window that holds the most `mask` dots (picked by counting with an integral picture)."""
    integral = cv2.integral(mask.astype(np.uint8)).astype(np.int64)
    best, where = -1, (0, 0)
    for y in range(0, mask.shape[0] - size + 1, stride):
        for x in range(0, mask.shape[1] - size + 1, stride):
            total = integral[y + size, x + size] - integral[y, x + size] - integral[y + size, x] + integral[y, x]
            if total > best:
                best, where = total, (x, y)
    return where


def label_strip(picture, text, height=34):
    bar = np.full((height, picture.shape[1], 3), 245, np.uint8)
    cv2.putText(bar, text, (8, height - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([bar, picture])


def load_colour(name):
    path = REFERENCE_COLOUR if name == 'reference' else os.path.join(MASK, 'compare', name, 'colour.png')
    return cv2.imread(path)


def make_sheet(names, column_width, crop_scale, out_path, crop_size=400):
    columns = []
    for name in names:
        colour = load_colour(name)
        olive, tan = lab_masks(colour)
        mx, my = best_window(olive, crop_size)
        tx, ty = best_window(tan, crop_size)
        full = cv2.resize(colour, (column_width, column_width), interpolation=cv2.INTER_AREA)
        moss_crop = colour[my:my + crop_size, mx:mx + crop_size]
        edge_crop = colour[ty:ty + crop_size, tx:tx + crop_size]
        side = int(crop_size * crop_scale)
        resize = lambda c: cv2.resize(c, (side, side), interpolation=cv2.INTER_NEAREST if crop_scale == int(crop_scale) else cv2.INTER_CUBIC)
        moss_crop, edge_crop = resize(moss_crop), resize(edge_crop)
        pad = lambda c: cv2.copyMakeBorder(c, 0, 0, 0, column_width - c.shape[1], cv2.BORDER_CONSTANT, value=(245, 245, 245)) if c.shape[1] < column_width else c[:, :column_width]
        column = np.vstack([label_strip(full, NICE[name]),
                            label_strip(pad(moss_crop), f'most moss: {crop_size} x {crop_size} dots at x{crop_scale:g}'),
                            label_strip(pad(edge_crop), f'most chips: {crop_size} x {crop_size} dots at x{crop_scale:g}')])
        columns.append(column)
        columns.append(np.full((column.shape[0], 6, 3), 245, np.uint8))
    sheet = np.hstack(columns[:-1])
    cv2.imwrite(out_path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])
    print('sheet', out_path, sheet.shape)


def run_sheets():
    os.makedirs(os.path.join(MASK, 'sheets'), exist_ok=True)
    make_sheet(['reference', '1_node_made', '4_both_stamps'], 800, 2.0, os.path.join(MASK, 'sheets', 'masks_compare.jpg'))
    make_sheet(['reference'] + VARIANTS, 400, 1.0, os.path.join(MASK, 'sheets', 'masks_compare_all_versions.jpg'))


if __name__ == '__main__':
    todo = sys.argv[1:] or ['measures', 'sheets']
    if 'measures' in todo:
        run_measures()
    if 'sheets' in todo:
        run_sheets()
