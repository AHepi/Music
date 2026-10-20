# What this does: joins the little squares made by sweep_tools.render_sweep into one labelled strip or grid picture
# (run with plain Python, not inside Blender).
# Use: python3 -I make_strip.py SWEEP_FOLDER OUT_PNG [--columns 5] [--title "text"] [--cell 256]
import json
import os
import sys

import cv2
import numpy as np

folder, out = sys.argv[1], sys.argv[2]
option = lambda name, default=None: sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
info = json.load(open(os.path.join(folder, 'sweep.json')))
cell = int(option('--cell', 256))
columns = int(option('--columns', len(info['files'])))
title = option('--title', os.path.basename(folder.rstrip('/')))
tiles = []
for file_name, label in zip(info['files'], info['labels']):
    image = cv2.imread(os.path.join(folder, file_name))
    image = cv2.resize(image, (cell, cell), interpolation=cv2.INTER_AREA)
    banner = np.full((34, cell, 3), 245, np.uint8)
    cv2.putText(banner, str(label)[:34], (6, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
    tiles.append(np.vstack([banner, image]))
while len(tiles) % columns:
    tiles.append(np.full_like(tiles[0], 255))
rows = [np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)]
grid = np.vstack(rows)
header = np.full((40, grid.shape[1], 3), 255, np.uint8)
cv2.putText(header, title, (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
cv2.imwrite(out, np.vstack([header, grid]))
print(out)
