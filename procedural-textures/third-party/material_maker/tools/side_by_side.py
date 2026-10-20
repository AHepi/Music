# Plain note: makes one picture with the reference colour on the left and a candidate's colour (and optionally its normal map) on the right,
# so they can be judged by eye. Run: python3 -I side_by_side.py REFERENCE_NAME MAPS_FOLDER OUT.png [--normal]
import sys
import cv2, numpy as np
REF = 'proc-work/reference/'
name, folder, out = sys.argv[1:4]
tiles = [cv2.imread(REF + name + '/colour.png'), cv2.imread(folder + '/colour.png')]
if '--normal' in sys.argv:
    tiles += [cv2.imread(REF + name + '/normal.png'), cv2.imread(folder + '/normal.png')]
tiles = [cv2.resize(t, (600, 600), interpolation=cv2.INTER_AREA) for t in tiles]
cv2.imwrite(out, np.hstack(tiles))
