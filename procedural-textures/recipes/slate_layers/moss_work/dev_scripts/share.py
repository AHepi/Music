# What this file does (plain words): reads the pictures a dev.sh run made (NAME_mask_colour.png and NAME_joints_colour.png) and prints the share
# of slate dots that are covered by moss or lichen, so a setting can be tuned by looking AND by a number.
# Use: python3 -I share.py FOLDER NAME [NAME...]
import sys
import cv2
import numpy as np
folder = sys.argv[1]
for name in sys.argv[2:]:
    mask = cv2.imread(f'{folder}/{name}_mask_colour.png', 0).astype(np.float32) / 255.0
    joints = cv2.imread(f'{folder}/{name}_joints_colour.png', 0).astype(np.float32) / 255.0
    mask = mask ** 2.2 if False else mask
    slate = joints > 0.5
    # the picture is written in sRGB; a mask of 1 is 255 and 0 is 0, so a threshold at 0.5 grey is fine
    share = (mask[slate] > 0.5).mean()
    print(f'{name}: share of slate dots covered {share:.3f}')
