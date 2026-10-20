# What this does (plain words): puts the four maps of seed set 1 side by side in one JPEG (colour, height, normal, roughness; each 400 dots wide,
# the top-left 800 dots of the tile shrunk), so the maps can be looked at: maps_seeds_1.jpg. Use: python3 -I make_maps_sheet.py
import os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
cells = []
for name, title in (('colour', 'colour'), ('height', 'height (16 bit)'), ('normal', 'normal (strength 10)'), ('roughness', 'roughness')):
    image = cv2.imread(os.path.join(HERE, 'final', 'seeds_1', name + '.png'), cv2.IMREAD_UNCHANGED)
    if image.dtype == np.uint16:
        image = (image / 257.0).astype(np.uint8)
    cell = cv2.resize(image[:800, :800], (400, 400), interpolation=cv2.INTER_AREA)
    cv2.putText(cell, title, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(cell, title, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(cell)
cv2.imwrite(os.path.join(HERE, 'maps_seeds_1.jpg'), np.hstack(cells), [cv2.IMWRITE_JPEG_QUALITY, 88])
print('wrote maps_seeds_1.jpg')
