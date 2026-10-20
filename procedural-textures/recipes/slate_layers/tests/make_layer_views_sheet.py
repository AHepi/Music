# What this does (plain words): joins the "each layer alone" debug pictures (made with the recipe's debug_view) into one sheet:
# one row per layer, columns Mask, Colour, Height (0.5 = no change), Roughness (0.5 = no change). Plain python.
# Use: python3 -I make_layer_views_sheet.py FOLDER_WITH_PICTURES OUT_PNG
import os
import sys

import cv2
import numpy as np

folder, out = sys.argv[1], sys.argv[2]
layers = ['colour_and_fade', 'moss', 'damage', 'outline_and_shadow']
whats = ['mask', 'colour', 'height', 'roughness']
cell = 300
rows = []
for layer in layers:
    tiles = []
    for what in whats:
        image = cv2.resize(cv2.imread(os.path.join(folder, f'{layer}_{what}_colour.png')), (cell, cell), interpolation=cv2.INTER_AREA)
        banner = np.full((26, cell, 3), 245, np.uint8)
        cv2.putText(banner, f'{layer} {what}', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
        tiles.append(np.vstack([banner, image]))
    rows.append(np.hstack(tiles))
cv2.imwrite(out, np.vstack(rows))
print(out)
