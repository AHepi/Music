# What this does (plain words): puts the four final 1254-dot tiles side by side in one JPEG (seed sets 1, 2 and 3 of the trial, and seed set 1
# built with the shared slate LAYOUT instead of the new brick layout), each with its same-kind and colour-group score, to see how much the
# seed alone changes the look. Use: python3 -I seed_sets_sheet.py   (writes final_seed_sets.jpg)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
table = json.load(open(os.path.join(HERE, 'final_scores.json')))['table']
cells = []
for name in ('seeds_1', 'seeds_2', 'seeds_3', 'shared_slate_layout_seeds_1'):
    tile = cv2.resize(cv2.imread(os.path.join(HERE, 'final', name, 'colour.png')), (560, 560), interpolation=cv2.INTER_AREA)
    for y, text in ((24, name), (50, f"same-kind {table[name]['overall']:.3f}  colour {table[name]['colour']:.3f}")):
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(tile)
cv2.imwrite(os.path.join(HERE, 'final_seed_sets.jpg'), np.hstack(cells), [cv2.IMWRITE_JPEG_QUALITY, 86])
print('wrote final_seed_sets.jpg')
