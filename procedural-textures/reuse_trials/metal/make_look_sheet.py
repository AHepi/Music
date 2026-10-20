# What this does (plain words): joins the colour pictures of one tuning round (rounds/<name>/*_colour.png) into ONE labelled JPEG sheet for
# looking, and (if asked) puts the metal reference, shrunk to the same size, as the first picture. Optionally a 2 x enlarged corner of each.
# Use: python3 -I make_look_sheet.py ROUND_FOLDER OUT.jpg [columns] [--reference] [--corner]
import glob
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
arguments = [a for a in sys.argv[1:] if not a.startswith('--')]
folder, out = arguments[0], arguments[1]
columns = int(arguments[2]) if len(arguments) > 2 else 4
paths = sorted(glob.glob(os.path.join(folder, '*_colour.png')))
cell = 420
pictures = []
if '--reference' in sys.argv:
    paths = [os.path.join(PROC, 'reference', 'metal', 'colour.png')] + paths
for path in paths:
    image = cv2.imread(path)
    if '--corner' in sys.argv:
        size = image.shape[0]
        image = image[: size // 2, : size // 2]
    image = cv2.resize(image, (cell, cell), interpolation=cv2.INTER_AREA)
    name = 'reference' if 'reference' in path else os.path.basename(path).replace('_colour.png', '')
    cv2.putText(image, name, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(image, name, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    pictures.append(image)
while len(pictures) % columns:
    pictures.append(np.zeros((cell, cell, 3), np.uint8))
rows = [np.hstack(pictures[i:i + columns]) for i in range(0, len(pictures), columns)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
print('wrote', out, len(paths), 'pictures')
