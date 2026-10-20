# What this does (plain words): puts several small test pictures side by side in one JPEG so they can be looked at together, each with its name written on it.
# The first picture of every sheet can be the new default tile shrunk to the same size, for comparison.
# Use (plain python): python3 -I make_look_sheet.py OUT.jpg COLUMNS PICTURE1 PICTURE2 ...   (a picture called "default" means outputs/default/colour.png)
import os
import sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
out, columns, names = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
panels = []
for name in names:
    path = os.path.join(HERE, '..', '..', 'outputs', 'default', 'colour.png') if name == 'default' else name
    picture = cv2.imread(path)
    picture = cv2.resize(picture, (512, 512), interpolation=cv2.INTER_AREA)
    cv2.rectangle(picture, (0, 0), (512, 22), (255, 255, 255), -1)
    cv2.putText(picture, os.path.basename(name).replace('_colour.png', '')[:60], (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    panels.append(picture)
while len(panels) % columns:
    panels.append(np.full((512, 512, 3), 255, np.uint8))
rows = [np.hstack(panels[i:i + columns]) for i in range(0, len(panels), columns)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
