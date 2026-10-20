# What this does: draws the three point sets made by t06_relax_repeat_zone.py (random / Poisson Disk / Repeat-zone relaxation) as circles, each shown as a 2 x 2 repeat
# of the tile, so you can SEE whether circles overlap across the tile edge (the edge lines are drawn in red). Run (plain Python): python3 -I fig_relax_points.py
import os
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 't06_relax')
RADIUS = 0.032
cell = 420
panels = []
for name, title in (('points_a.npy', 'A random: circles overlap'), ('points_b.npy', 'B Poisson Disk: ok inside, not across the red lines'), ('points_c40.npy', 'C Repeat zone x40: no overlap anywhere')):
    points = np.load(os.path.join(OUT, name))
    image = np.full((cell * 2, cell * 2, 3), 250, np.uint8)
    for tile_x in range(2):
        for tile_y in range(2):
            for x, y in points:
                centre = (int((x + tile_x) * cell), int(((1 - y) + tile_y) * cell))      # picture rows go down, tile y goes up
                cv2.circle(image, centre, int(RADIUS * cell), (60, 60, 60), 1, cv2.LINE_AA)
    cv2.line(image, (cell, 0), (cell, cell * 2), (0, 0, 220), 2)
    cv2.line(image, (0, cell), (cell * 2, cell), (0, 0, 220), 2)
    banner = np.full((34, cell * 2, 3), 255, np.uint8)
    cv2.putText(banner, title, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 1, cv2.LINE_AA)
    panels.append(np.vstack([banner, image]))
cv2.imwrite(os.path.join(HERE, 'out', 'fig_relax_points.png'), np.hstack([cv2.resize(p, None, fx=0.62, fy=0.62, interpolation=cv2.INTER_AREA) for p in panels]))
print('ok')
