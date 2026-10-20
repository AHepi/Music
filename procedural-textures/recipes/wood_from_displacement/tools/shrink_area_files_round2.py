# What this does (plain words): makes the big area pictures of round 2 smaller once ALL measurements are done, to keep this folder under 150 MB:
#   * the colour pictures of the areas and crops (area/*/colour.png) become JPEG (quality 92);
#   * the 16-bit height pictures of the 4 x 4 area and of the switched-off areas (area/area_4x4, area/switch_*) become 8-bit PNG;
#   * the exact pictures (debug_*, tests/renders/boards_*, source_*_seed1) are NOT touched: the repeat counts and the joint sheets need their 16-bit numbers;
#   * the colour pictures of the slide test and the source-unchanged test (tests/renders/*/colour.png) are deleted (their height pictures stay).
# What can still be re-run after this: tools/measure_repeats_round2.py (reads JPEG or PNG; the near-copy numbers from 8-bit height and JPEG colour can differ from the numbers
# in the guide in the second decimal, because the guide's numbers were measured BEFORE shrinking), tools/analyse_final_round2.py (the colour part of the slide test and of the
# source-unchanged test is then missing and the section keeps what was measured before), tools/joint_contact_sheet_round2.py, tools/make_sheets_round2.py.
# To redo a measurement that needs a big original picture, bake it again with tools/run_jobs.py and the job lists in tests/jobs_r2_*.json.
# Use: python3 -I tools/shrink_area_files_round2.py
import os

import cv2
import numpy as np
from PIL import Image

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def colour_to_jpeg(folder):
    p = os.path.join(folder, 'colour.png')
    if os.path.exists(p):
        Image.open(p).convert('RGB').save(os.path.join(folder, 'colour.jpg'), quality=92)
        os.remove(p)


def height_to_8bit(folder):
    p = os.path.join(folder, 'height.png')
    if os.path.exists(p):
        a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if a.dtype == np.uint16:
            a = a[..., 0] if a.ndim == 3 else a
            cv2.imwrite(p, np.round(a / 257.0).astype(np.uint8))


def folder_size(path):
    return sum(os.path.getsize(os.path.join(d, f)) for d, _, files in os.walk(path) for f in files)


def main():
    before = folder_size(BASE)
    area = os.path.join(BASE, 'area')
    for name in sorted(os.listdir(area)):
        folder = os.path.join(area, name)
        if not os.path.isdir(folder) or name.startswith('debug_'):
            continue
        colour_to_jpeg(folder)
        if name == 'area_4x4' or name.startswith('switch_'):
            height_to_8bit(folder)
    for name in ('shift_half', 'source_unchanged'):
        p = os.path.join(BASE, 'tests', 'renders', name, 'colour.png')
        if os.path.exists(p):
            os.remove(p)
    print(f'folder size {before / 1e6:.1f} MB -> {folder_size(BASE) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
