# What this file does (plain words): puts the reference picture (scaled to the same size) next to a baked picture and writes a zoomed crop, so they can be compared by eye.
# Use: python3 -I side.py PICTURE.png OUT_PREFIX [x0 y0 x1 y1 zoom]  (crop in the picture's own dots)
import sys
import cv2
import numpy as np
pic = cv2.imread(sys.argv[1])
n = pic.shape[0]
ref = cv2.imread('proc-work/reference/slate/colour.png')
ref = cv2.resize(ref, (n, n), interpolation=cv2.INTER_AREA)
cv2.imwrite(sys.argv[2] + '_side.png', np.hstack([ref, pic]))
if len(sys.argv) > 3:
    x0, y0, x1, y1, z = [int(v) for v in sys.argv[3:8]]
    crop = np.hstack([ref[y0:y1, x0:x1], pic[y0:y1, x0:x1]])
    cv2.imwrite(sys.argv[2] + '_crop.png', cv2.resize(crop, None, fx=z, fy=z, interpolation=cv2.INTER_NEAREST))
