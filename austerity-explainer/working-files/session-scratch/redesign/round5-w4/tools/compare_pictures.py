"""What this does (scratch, round 5 W4 helper): compares pictures of the same names in two folders, pixel by pixel,
and says how many pixels differ and by how much (0 levels everywhere means the two are the same picture).
Use: python3 compare_pictures.py OLD_FOLDER NEW_FOLDER [OUT_FOLDER for difference pictures]"""
import os
import sys

import cv2
import numpy as np

old_folder, new_folder = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else None
for name in sorted(os.listdir(old_folder)):
    if not name.endswith('.png'):
        continue
    a, b = cv2.imread(os.path.join(old_folder, name)), cv2.imread(os.path.join(new_folder, name))
    if b is None:
        print(f'{name}: missing in {new_folder}')
        continue
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    print(f'{name}: largest difference {d.max()} levels; pixels differing at all {(d > 0).mean():.4%}, by more than 2 levels '
          f'{(d > 2).mean():.4%}, by more than 8 {(d > 8).mean():.4%}')
    if out and d.max() > 0:
        os.makedirs(out, exist_ok=True)
        ys, xs = np.nonzero(d > 2)
        if len(ys):
            print(f'    where (more than 2 levels): rows {ys.min() / d.shape[0]:.2f} to {ys.max() / d.shape[0]:.2f} down, '
                  f'{xs.min() / d.shape[1]:.2f} to {xs.max() / d.shape[1]:.2f} across')
        cv2.imwrite(os.path.join(out, name.replace('.png', '-difference.png')), np.clip(d * 16, 0, 255).astype(np.uint8))
