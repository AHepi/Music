# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE DEBUG SHEET "where each thing may go": the bus masks that matter most seen from each of the set's cameras (the pictures drawn by run_testset.py --maskviews, one per mask and
# camera, plain light, raw numbers: white = 1, black = 0 or no surface). One tile per mask and camera, two masks side by side per row, under 400 KB.
#     python3 -I harness/mask_debug_sheet.py SET_ID OUT.jpg FOLDER [FOLDER ...]
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402
import sheets  # noqa: E402
import testset  # noqa: E402


def make(set_id, out, folders, names=None, columns=6, cell_width=140):
    settings = mc.load_set(set_id)
    names = names or testset.SHEET_MASKS
    ts = settings.get('test_set') or {}
    cameras = []
    for label, cam in ts['camera_of'].items():
        if cam not in cameras:
            cameras.append(cam)
    items = []
    for name in names:
        for cam in cameras:
            path = next((os.path.join(f, f'maskview_{name}_{cam}.png') for f in folders if os.path.exists(os.path.join(f, f'maskview_{name}_{cam}.png'))), None)
            if path is None:
                continue
            rgb = mc.read_rgb(path)
            items.append(((np.clip(rgb, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy(), f'{name} | {cam}'))
    return sheets.contact_sheet(items, out, columns=columns, cell_width=cell_width, title='Where each thing may go: the bus masks seen from the cameras (white = 1, black = 0 or no surface of a hooked material)')


if __name__ == '__main__':
    print(make(sys.argv[1], sys.argv[2], sys.argv[3:]))
