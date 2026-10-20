# What this does: re-runs the self-tests of the project's two measuring tools (lib/texture_compare.py = "same kind of surface?",
# lib/pixel_compare.py = "the same picture, dot for dot?") so the baking-and-checking guide can quote numbers it has a file for.
# It scores, against the brick reference: the reference itself, the reference slid by (311, 517) dots with wrap-around
# (tests/selftest_brick_rolled2), the reference blurred by about 6 dots (tests/selftest_brick_blur), a flat picture of the
# reference's average colour (made here, tiny), and the five other reference surfaces. It also scores every reference against
# the MUD reference, because the mud checker found the same-kind score does not separate mud from other surfaces well.
# Plain Python (run with python3 -I). Writes self_tests.json and the tools' own sheets for two cases into this folder.
# Use: python3 -I run_self_tests.py
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LIB = os.path.join(PROC, 'lib')
REFERENCE = os.path.join(PROC, 'reference')
TESTS = os.path.join(PROC, 'tests')
sys.path.insert(0, LIB)
import pixel_compare  # noqa: E402
import texture_compare  # noqa: E402


def make_flat_copy(reference_name, out_folder):
    """A 'do nothing' candidate: every dot the reference's average colour, a flat grey height, a flat normal map."""
    os.makedirs(out_folder, exist_ok=True)
    colour = cv2.imread(os.path.join(REFERENCE, reference_name, 'colour.png'))
    average = colour.reshape(-1, 3).mean(axis=0)
    flat = np.zeros_like(colour)
    flat[:] = np.round(average).astype(np.uint8)
    cv2.imwrite(os.path.join(out_folder, 'colour.png'), flat)
    cv2.imwrite(os.path.join(out_folder, 'height.png'), np.full(colour.shape[:2], 128, np.uint8))
    normal = np.zeros_like(colour)
    normal[:] = (255, 128, 128)          # OpenCV order blue, green, red: blue = 1, red = green = 0.5 -> a flat normal
    cv2.imwrite(os.path.join(out_folder, 'normal.png'), normal)
    return out_folder


def score(reference_name, candidate_folder, with_pixel=True):
    same_kind = texture_compare.score_set(reference_name, candidate_folder)
    row = {'same_kind_overall': same_kind['overall'], 'same_kind_groups': same_kind['groups'],
           'seam_ratio_candidate': same_kind['facts']['seam_ratio_candidate']}
    if with_pixel:
        dot = pixel_compare.pixel_report(reference_name, candidate_folder)
        for key in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached'):
            row[key] = dot.get(key)
    return row


def main():
    results = {'about': 'self-tests of lib/texture_compare.py and lib/pixel_compare.py, re-run for the cookbook guide',
               'brick_row': {}, 'mud_row': {}}
    flat_folder = make_flat_copy('brick', os.path.join(HERE, 'flat_brick_average'))
    brick_cases = [('the reference itself', os.path.join(REFERENCE, 'brick')),
                   ('slid by (311, 517) dots with wrap-around', os.path.join(TESTS, 'selftest_brick_rolled2')),
                   ('blurred by about 6 dots', os.path.join(TESTS, 'selftest_brick_blur')),
                   ('flat average colour', flat_folder)]
    brick_cases += [(f'the {name} reference', os.path.join(REFERENCE, name)) for name in ('slate', 'wood', 'metal', 'mud', 'gravel')]
    for label, folder in brick_cases:
        results['brick_row'][label] = score('brick', folder)
        print('brick |', label, json.dumps(results['brick_row'][label]), flush=True)
    for name in ('brick', 'slate', 'wood', 'metal', 'gravel'):
        results['mud_row'][f'the {name} reference'] = score('mud', os.path.join(REFERENCE, name), with_pixel=False)
        print('mud |', name, json.dumps(results['mud_row'][f'the {name} reference']), flush=True)
    with open(os.path.join(HERE, 'self_tests.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    # the tools' own sheets for the slid copy (same kind, but not the same dots)
    texture_compare.make_sheet('brick', os.path.join(TESTS, 'selftest_brick_rolled2'), os.path.join(HERE, 'sheet_same_kind_slid_copy.png'))
    pixel_compare.difference_sheet('brick', os.path.join(TESTS, 'selftest_brick_rolled2'), os.path.join(HERE, 'sheet_dot_for_dot_slid_copy.png'))


if __name__ == '__main__':
    main()
