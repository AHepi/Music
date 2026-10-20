# What this does (plain words): joins the pictures of the LAYOUT BUNDLE numbers (made by run_bundle_pictures.sh) into one labelled sheet,
# so a person can SEE what each number is: piece_id as a random colour per slate, row, local_x and local_y (0..1 across and down every
# slate), edge_distance, top_edge_distance, piece_width, piece_height, gap_mask and base_height.
# Use (plain python):  python3 -I make_bundle_sheet.py FOLDER_WITH_PICTURES OUT_PNG [cell size]
import os
import sys

import cv2
import numpy as np

folder, out = sys.argv[1], sys.argv[2]
cell = int(sys.argv[3]) if len(sys.argv) > 3 else 420
ORDER = [('bundle_piece_colour', 'piece_id (a random colour per slate)'), ('bundle_row', 'row (row number / rows)'),
         ('bundle_local_x', 'local_x (0 left .. 1 right)'), ('bundle_local_y', 'local_y (0 top .. 1 bottom)'),
         ('bundle_edge_distance', 'edge_distance (x25; 0 at the edge)'), ('bundle_top_edge_distance', 'top_edge_distance (x8)'),
         ('bundle_piece_width', 'piece_width (x5)'), ('bundle_piece_height', 'piece_height (x8)'),
         ('bundle_gap_mask', 'gap_mask (1 in the joint)'), ('bundle_base_height', 'base_height (0..1)')]
tiles = []
for name, label in ORDER:
    path = os.path.join(folder, name + '_colour.png')
    if not os.path.exists(path):
        continue
    image = cv2.resize(cv2.imread(path), (cell, cell), interpolation=cv2.INTER_AREA)
    banner = np.full((30, cell, 3), 245, np.uint8)
    cv2.putText(banner, label, (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    tiles.append(np.vstack([banner, image]))
columns = 5
while len(tiles) % columns:
    tiles.append(np.full_like(tiles[0], 255))
sheet = np.vstack([np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)])
cv2.imwrite(out, sheet)
print(out, sheet.shape)
