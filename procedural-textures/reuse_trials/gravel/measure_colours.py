# What this does (plain words): a quick look at the colours of a picture, for hand tuning: the average colour of the soil dots and of the stone
# dots, the share of stone, and how bright the stones are (average and a few steps of the brightness curve). "Soil" here means a dot whose
# red is clearly above its blue (orange-brown); for the layered picture the layout's own stone mask can be given instead. The reference
# is measured the same simple way, once, only as a GUIDE for hand tuning (nothing is optimised against it).
# Use: python3 -I measure_colours.py PICTURE.png [STONE_MASK.png]
import os
import sys
import cv2
import numpy as np

colour = cv2.imread(sys.argv[1])[..., ::-1].astype(np.float64)
if len(sys.argv) > 2:
    stone = cv2.imread(sys.argv[2], 0) > 127
    if stone.shape != colour.shape[:2]:
        stone = cv2.resize(stone.astype(np.uint8), colour.shape[1::-1], interpolation=cv2.INTER_NEAREST) > 0
else:
    stone = (colour[..., 0] - colour[..., 2]) < 28
soil = ~stone
grey = colour @ np.array([0.299, 0.587, 0.114])
print(os.path.basename(sys.argv[1]), 'stone share %.3f' % stone.mean())
print('  soil mean colour', np.round(colour[soil].mean(axis=0)).astype(int), ' soil brightness percentiles 10/50/90', np.round(np.percentile(grey[soil], [10, 50, 90])).astype(int))
print('  stone mean colour', np.round(colour[stone].mean(axis=0)).astype(int), ' stone brightness percentiles 10/50/90', np.round(np.percentile(grey[stone], [10, 50, 90])).astype(int))
print('  stone blue minus red (mean)', round(float((colour[stone][:, 2] - colour[stone][:, 0]).mean()), 1))
