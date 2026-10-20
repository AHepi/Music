# What this does (plain words): puts a full-size (one dot = one dot) crop of EVERY board joint of the default tiles on a sheet, so that every joint can be looked at for a
# visible cut. Round 1 found joints by looking for dark runs in the picture, which can miss faint or short joints (the honesty checker pointed this out). Round 2 finds them
# EXACTLY: the recipe can write the board number of every dot (debug view 'boards', jobs in tests/jobs_r2_joints.json, pictures in tests/renders/boards_seed1..3); a joint is
# a place where the board number changes from one dot to the next one to the right, over a stretch at least 25 dots tall. A stepped joint has an upper and a lower part
# that lie some way apart; neighbouring parts (within 150 dots) are put on one crop.
# Output: sheets/joints_seed1.jpg .. seed3, and scores/joints_found_round2.json (how many joints, how many crops).
# Use: python3 -I tools/joint_contact_sheet_round2.py
import json
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))


def find_joints(seed):
    ids = cv2.imread(os.path.join(BASE, 'tests', 'renders', f'boards_seed{seed}', 'height.png'), cv2.IMREAD_UNCHANGED)
    ids = ids[..., 0] if ids.ndim == 3 else ids
    ids = ids.astype(np.int64)
    changed = (ids[:, :-1] != ids[:, 1:]).astype(np.uint8)
    changed = np.pad(changed, ((0, 0), (0, 1)))
    n, labels, stats, cent = cv2.connectedComponentsWithStats(changed, connectivity=8)
    parts = [(float(cent[i][0]), float(cent[i][1]), int(stats[i][3])) for i in range(1, n) if stats[i][3] >= 25 and stats[i][2] <= 140]
    clusters = []
    for cx, cy, h in sorted(parts, key=lambda p: (p[1], p[0])):
        for c in clusters:
            if abs(c['x'] - cx) < 150 and abs(c['y'] - cy) < 150:
                c['members'].append((cx, cy, h))
                c['x'] = float(np.mean([m[0] for m in c['members']]))
                c['y'] = float(np.mean([m[1] for m in c['members']]))
                break
        else:
            clusters.append({'x': cx, 'y': cy, 'members': [(cx, cy, h)]})
    return len(parts), clusters


def sheet(seed):
    parts, clusters = find_joints(seed)
    rgb = np.asarray(Image.open(os.path.join(BASE, 'outputs', f'main_seed{seed}', 'colour.png')).convert('RGB'))
    big = np.pad(rgb, ((150, 150), (150, 150), (0, 0)), mode='wrap')        # the tile repeats, so joints at the edge can be cropped whole
    tiles = []
    for c in sorted(clusters, key=lambda c: (round(c['y'] / 250.0), c['x'])):
        cx, cy = int(round(c['x'])), int(round(c['y']))
        crop = Image.fromarray(big[cy:cy + 300, cx:cx + 300])
        canvas = Image.new('RGB', (300, 320), (20, 20, 20))
        canvas.paste(crop, (0, 20))
        ImageDraw.Draw(canvas).text((4, 3), f'x {cx} y {cy} parts {len(c["members"])}', fill=(240, 240, 240))
        tiles.append(canvas)
    columns = 6
    rows = (len(tiles) + columns - 1) // columns
    out = Image.new('RGB', (columns * 304, rows * 324), (255, 255, 255))
    for i, t in enumerate(tiles):
        out.paste(t, ((i % columns) * 304, (i // columns) * 324))
    os.makedirs(os.path.join(BASE, 'sheets'), exist_ok=True)
    out.save(os.path.join(BASE, 'sheets', f'joints_seed{seed}.jpg'), quality=90)
    print(f'seed {seed}: {parts} joint parts, {len(tiles)} crops, sheet {out.size}')
    return {'joint_parts_at_least_25_dots_tall': parts, 'crops_on_the_sheet': len(tiles)}


if __name__ == '__main__':
    found = {'what_this_is': 'How many board joints were found in the default tiles of round 2 by tools/joint_contact_sheet_round2.py: exact, from the board numbers written by the recipe (a place where the board number changes, at least 25 dots tall); neighbouring parts of a stepped joint share one crop.'}
    for s in (1, 2, 3):
        if os.path.exists(os.path.join(BASE, 'tests', 'renders', f'boards_seed{s}', 'height.png')):
            found[f'seed{s}'] = sheet(s)
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(os.path.join(BASE, 'scores', 'joints_found_round2.json'), 'w') as handle:
        json.dump(found, handle, indent=1)
