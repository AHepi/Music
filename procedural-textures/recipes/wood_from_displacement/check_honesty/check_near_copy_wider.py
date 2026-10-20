# What this does (plain words): the honesty checker's own, WIDER version of the builder's near-copy test. The builder's test (the research's test) looks for a copy of a
# board-sized piece only (a) at the same height inside a row, and (b) mirrored left-right but never upside down. But the recipe turns 40 percent of its boards upside down
# and a copy can sit anywhere inside a row. So this test searches the whole height of every row and tries all four ways round (as is, left-right, upside down, both).
# It uses the same pieces (same random choices) as the builder's test, so the two can be compared. A "near copy" is a best match above 0.8.
# Use: python3 -I check_near_copy_wider.py
import json
import os
import sys

import cv2
import numpy as np

CK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CK)
import measure_repeats_rerun as mr  # noqa: E402  (the builder's functions, copied; nothing runs on import)


def repeat_score_wide(a, tpl_h=36, tpl_w=80, count=40, seed=3, rows=20):
    rng = np.random.default_rng(seed)
    h, w = a.shape
    pitch = h / rows
    a8 = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    narrow, wide = [], []
    tries = 0
    while len(narrow) < count and tries < count * 5:
        tries += 1
        r = int(rng.integers(0, rows - 1))
        x = int(rng.integers(0, w - tpl_w))
        y0 = int(round(r * pitch + pitch * 0.16))
        tpl = a8[y0:y0 + tpl_h, x:x + tpl_w]
        if tpl.std() < 8:
            continue
        variants_wide = (tpl, tpl[:, ::-1].copy(), tpl[::-1, :].copy(), tpl[::-1, ::-1].copy())
        best_n, best_w = -1.0, -1.0
        for r2 in range(rows - 1):
            y2 = int(round(r2 * pitch + pitch * 0.16))
            band_n = a8[max(y2 - 3, 0):y2 + tpl_h + 3, :]
            band_w = a8[int(round(r2 * pitch)):int(round((r2 + 1) * pitch)) + tpl_h, :]        # the whole row, every height
            for v_index, v in enumerate(variants_wide):
                for kind, band in (('n', band_n), ('w', band_w)):
                    if kind == 'n' and v_index > 1:
                        continue
                    res = cv2.matchTemplate(band, v, cv2.TM_CCOEFF_NORMED)
                    if kind == 'n':
                        res = res[0:7]
                    if r2 == r:
                        res = res.copy()
                        res[:, max(0, x - tpl_w):x + tpl_w] = -1.0
                    m = float(res.max())
                    if kind == 'n':
                        best_n = max(best_n, m)
                    else:
                        best_w = max(best_w, m)
        narrow.append(best_n)
        wide.append(best_w)
    narrow, wide = np.array(narrow), np.array(wide)
    return {'templates': int(len(narrow)), 'builder_style_median': round(float(np.median(narrow)), 2), 'builder_style_share_over_0.8': round(float((narrow > 0.8).mean()), 2),
            'wider_median': round(float(np.median(wide)), 2), 'wider_share_over_0.8': round(float((wide > 0.8).mean()), 2)}


area = os.path.join(mr.BASE, 'area')
h4 = mr.load_height16(os.path.join(area, 'area_4x4', 'height.png')).astype(np.float32)
g = cv2.resize(h4, (1024, 1024), interpolation=cv2.INTER_AREA)
out = {'new_4x4_area_height_board_size': repeat_score_wide(g, 36, 80, 40, 3), 'new_4x4_area_height_feature_size': repeat_score_wide(g, 24, 40, 40, 3)}
from PIL import Image  # noqa: E402
plain = np.tile(np.asarray(Image.open(os.path.join(mr.PROC, 'reference', 'wood', 'height_as_uploaded.png'))).astype(np.float32) / 255.0, (4, 4))
gp = cv2.resize(plain, (1024, 1024), interpolation=cv2.INTER_AREA)
out['plain_repeat_height_board_size'] = repeat_score_wide(gp, 36, 80, 40, 3)
# a few more draws of the 40 pieces, to see the noise of the test
out['new_4x4_area_height_board_size_other_piece_draws'] = [repeat_score_wide(g, 36, 80, 40, s) for s in (4, 5, 6, 7)]
with open(os.path.join(CK, 'near_copy_wider.json'), 'w') as handle:
    json.dump(out, handle, indent=1)
print(json.dumps(out, indent=1))
