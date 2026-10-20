# What this does (plain words): puts the three final 1254-dot tiles of the mud trial (seed sets 1, 2 and 3) and the mud reference side by side in one
# JPEG, each with its same-kind and colour-group score, to see how much the seed alone changes the look. Use: python3 -I seed_sets_sheet.py
# (reads final/, final_scores.json; writes final_seed_sets.jpg)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
table = json.load(open(os.path.join(HERE, 'final_scores.json')))['table']
cells = []
for name in ('reference', 'seeds_1', 'seeds_2', 'seeds_3'):
    path = os.path.join(PROC, 'reference', 'mud', 'colour.png') if name == 'reference' else os.path.join(HERE, 'final', name, 'colour.png')
    tile = cv2.resize(cv2.imread(path), (560, 560), interpolation=cv2.INTER_AREA)
    texts = [('mud reference (a guide only)' if name == 'reference' else name)]
    if name != 'reference':
        texts.append(f"same-kind {table[name]['overall']:.3f}  colour {table[name]['colour']:.3f}")
    for y, text in zip((24, 50), texts):
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(tile)
cv2.imwrite(os.path.join(HERE, 'final_seed_sets.jpg'), np.hstack(cells), [cv2.IMWRITE_JPEG_QUALITY, 86])
print('wrote final_seed_sets.jpg')
