# What this does (plain words): joins the small sweep pictures made by generator/sweeps_for_guide.py into labelled strips, each picture CROPPED to its middle (so the fine
# settings can be seen) and enlarged 2 x. Same job as lib/make_strip.py but with a crop. Output: guide_pictures/strip_<name>.png. Plain Python (python3 -I).
import json, os, sys
import cv2
import numpy as np
WOOD = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
pics = os.path.join(WOOD, 'guide_pictures')
for name in sorted(d[6:] for d in os.listdir(pics) if d.startswith('sweep_') and os.path.isdir(os.path.join(pics, d))):
    folder = os.path.join(pics, 'sweep_' + name)
    info = json.load(open(os.path.join(folder, 'sweep.json')))
    cells = []
    for f, label in zip(info['files'], info['labels']):
        im = cv2.imread(os.path.join(folder, f))
        h, w = im.shape[:2]
        crop = im[int(h * 0.28):int(h * 0.72), int(w * 0.10):int(w * 0.90)]                  # the middle 44 % tall and 80 % wide
        crop = cv2.resize(crop, None, fx=2.2, fy=2.2, interpolation=cv2.INTER_CUBIC)
        banner = np.full((34, crop.shape[1], 3), 245, np.uint8)
        cv2.putText(banner, str(label), (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 1, cv2.LINE_AA)
        cells.append(np.vstack([banner, crop]))
    grid = np.hstack(cells[:3]) if len(cells) >= 3 else np.hstack(cells)
    rows = [np.hstack(cells[i:i + 3] + [np.full_like(cells[0], 255)] * (3 - len(cells[i:i + 3]))) for i in range(0, len(cells), 3)]
    grid = np.vstack(rows)
    header = np.full((44, grid.shape[1], 3), 255, np.uint8)
    cv2.putText(header, info['title'], (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(pics, f'strip_{name}.png'), np.vstack([header, grid]))
    print('wrote strip_' + name + '.png', grid.shape)
