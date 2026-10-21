# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Works out how much of the road's joints (and of its stone faces) lie under a puddle, from the "puddle mask" pictures of the checking view (red = puddle, green = wet, in raw numbers)
# and the joint / stone / road mask of the same camera. Prints, for each picture: the share of the ROAD that is puddle (above 0.5), the share of JOINT dots that are under a puddle, the share of
# STONE dots under a puddle, and the share of the road that is wet at all (above 0.5). Plain Python.
# Run: python3 -I b12_puddles_over_joints.py FOLDER     (reads FOLDER/*_puddlemask.png and FOLDER/mask_<camera>_<w>x<h>.png)
import glob
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b04_measure_joints import load_mask  # noqa: E402

folder = sys.argv[1]
sizes = {'main': (540, 960), 'close': (640, 480)}
print(f"{'picture':32s} {'road is puddle':>15s} {'joint dots in puddle':>21s} {'stone dots in puddle':>21s} {'road wet at all':>16s}")
for path in sorted(glob.glob(os.path.join(folder, '*_puddlemask.*'))):
    name = os.path.basename(path).rsplit('.', 1)[0]
    kind = name.split('_')[0]
    w, h = sizes[kind]
    mask_file = os.path.join(folder, 'mask_main_540x960.png' if kind == 'main' else 'mask_close_road_640x480.png')
    J, S, R = load_mask(mask_file)
    image = cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
    puddle, wet = image[..., 0], image[..., 1]
    road = R > 0.99
    joint = (J > 0.5) & road
    stone = (S > 0.9) & road
    print(f"{name:32s} {puddle[road].__gt__(0.5).mean():15.3f} {puddle[joint].__gt__(0.5).mean():21.3f} {puddle[stone].__gt__(0.5).mean():21.3f} {wet[road].__gt__(0.5).mean():16.3f}")
