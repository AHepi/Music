# What this does (plain words): puts several small pictures side by side in one JPEG with a name on each, for looking at during tuning.
# Use: python3 -I contact_sheet.py OUT.jpg CELL_SIZE COLUMNS picture1.png[:label] picture2.png[:label] ...
import sys
import cv2
import numpy as np
out, cell, columns = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tiles = []
for item in sys.argv[4:]:
    path, _, label = item.partition(':')
    image = cv2.imread(path)
    image = cv2.resize(image, (cell, cell), interpolation=cv2.INTER_AREA if image.shape[0] >= cell else cv2.INTER_NEAREST)
    text = label or path.split('/')[-1]
    cv2.putText(image, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(image, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    tiles.append(image)
while len(tiles) % columns:
    tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
