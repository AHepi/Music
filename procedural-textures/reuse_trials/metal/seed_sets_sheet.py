# What this does (plain words): puts the final 1254-dot layered metal tiles (seed sets 1, 2 and 3, and an extra set 4) side by side (2 x 2) in one JPEG, each with its
# same-kind score and colour-group score written on it, so you can see how much the seed alone changes the look and the score.
# Use: python3 -I seed_sets_sheet.py   (reads final/seeds_*/colour.png and final_scores.json; writes final_seed_sets.jpg)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
table = json.load(open(os.path.join(HERE, 'final_scores.json')))['table']
cells = []
for name in ('seeds_1', 'seeds_2', 'seeds_3', 'seeds_4'):
    tile = cv2.resize(cv2.imread(os.path.join(HERE, 'final', name, 'colour.png')), (600, 600), interpolation=cv2.INTER_AREA)
    for y, text in ((24, name + (' (first one I tuned on)' if name == 'seeds_1' else ' (extra, never looked at before baking)' if name == 'seeds_4' else '')), (50, f"same-kind {table[name]['overall']:.3f}  colour {table[name]['colour']:.3f}  height {table[name]['height']:.3f}")):
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2), (0, -2), (2, 0), (-2, 0)):      # a dark outline, same letter spacing as the white text
            cv2.putText(tile, text, (8 + dx, y + dy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(tile)
cv2.imwrite(os.path.join(HERE, 'final_seed_sets.jpg'), np.vstack([np.hstack(cells[:2]), np.hstack(cells[2:])]), [cv2.IMWRITE_JPEG_QUALITY, 86])
print('wrote final_seed_sets.jpg')
