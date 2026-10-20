# What this does (plain words): finds every board joint (a dark crack that runs up and down) in the finished default tiles and puts a full-size
# (one dot = one dot) crop of each on a sheet, so that every joint can be looked at for visible cuts. A joint is found as a thin dark vertical run (brightness under 0.2) at
# least 60 dots tall in the colour picture. Output: sheets/joints_seed1.jpg, seed2, seed3 (and the number of joints found per tile).
# Use: python3 -I tools/joint_contact_sheet.py
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))


def find_joints(path):
    rgb = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255.0
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    dark = (luma < 0.20).astype(np.uint8)
    runs = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((60, 1), np.uint8))
    runs = cv2.morphologyEx(runs, cv2.MORPH_CLOSE, np.ones((9, 3), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(runs, connectivity=8)
    joints = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if h >= 60 and w <= 40:
            joints.append((int(x + w / 2), int(y + h / 2), int(h)))
    return rgb, sorted(joints, key=lambda j: (j[1] // 250, j[0]))


def sheet(seed):
    path = os.path.join(BASE, 'outputs', f'main_seed{seed}', 'colour.png')
    rgb, joints = find_joints(path)
    big = np.pad((rgb * 255).astype(np.uint8), ((130, 130), (130, 130), (0, 0)), mode='wrap')        # the tile repeats, so joints at the edge can be cropped whole
    tiles = []
    for cx, cy, h in joints:
        crop = Image.fromarray(big[cy:cy + 260, cx:cx + 260])                                         # (cx - 130 + 130, cy - 130 + 130) -> a 260 x 260 crop centred on the joint
        canvas = Image.new('RGB', (260, 280), (20, 20, 20))
        canvas.paste(crop, (0, 20))
        ImageDraw.Draw(canvas).text((4, 3), f'x {cx} y {cy} tall {h}', fill=(240, 240, 240))
        tiles.append(canvas)
    columns = 7
    rows = (len(tiles) + columns - 1) // columns
    out = Image.new('RGB', (columns * 264, rows * 284), (255, 255, 255))
    for i, t in enumerate(tiles):
        out.paste(t, ((i % columns) * 264, (i // columns) * 284))
    out.save(os.path.join(BASE, 'sheets', f'joints_seed{seed}.jpg'), quality=90)
    print(f'seed {seed}: {len(joints)} joints, sheet {out.size}')
    return len(joints)


if __name__ == '__main__':
    import json
    found = {}
    for s in (1, 2, 3):
        found[f'seed{s}'] = sheet(s)
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(os.path.join(BASE, 'scores', 'joints_found.json'), 'w') as handle:
        json.dump(found, handle)
