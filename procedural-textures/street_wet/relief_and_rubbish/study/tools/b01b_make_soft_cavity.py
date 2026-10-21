# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The first joint picture (joint_cavity.png) is as ragged as the colour picture's own joints, and made the joints jet black with ragged edges (first try, section 5).
# This makes a SOFTER one, joint_cavity_soft.png: the joints (taken from the R channel of joint_cores.png) blurred about 4 mm and scaled so that the middle of an ordinary joint is 1,
# plus a faint wide halo (the stone's edge 1 cm into the stone is a little in shadow). Result: an evenly dark joint with soft edges, not a ragged black block.
# Run: python3 -I b01b_make_soft_cavity.py
import os

import cv2
import numpy as np

WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work'))
cores = cv2.imread(os.path.join(WORK, 'joint_cores.png'))
joint = (cores[..., 2] > 127).astype(np.float32)           # OpenCV order is BGR: index 2 is R = the joint
N = joint.shape[0]
# CLOSED version: bridge the gaps in the joint lines (the colour picture's lighter stretches of joint left holes: dashes instead of lines). A closing with a long thin kernel
# along each direction fills gaps shorter than 45 dots (4.5 cm) in a horizontal or vertical line and leaves everything else as it was.
tiled0 = np.tile(joint.astype(np.uint8), (3, 3))
closed_h = cv2.morphologyEx(tiled0, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1)))
closed_v = cv2.morphologyEx(tiled0, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 45)))
closed = np.maximum(closed_h, closed_v)
closed = cv2.dilate(closed, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
joint_closed = closed[N:2 * N, N:2 * N].astype(np.float32)
print('joint share before', round(float(joint.mean()), 3), 'after closing', round(float(joint_closed.mean()), 3))
cv2.imwrite(os.path.join(WORK, 'joint_mask_closed_check.png'), (joint_closed * 255).astype(np.uint8))
tiled = np.tile(joint_closed, (3, 3))
narrow = cv2.GaussianBlur(tiled, (0, 0), 4.0)[N:2 * N, N:2 * N]
wide = cv2.GaussianBlur(tiled, (0, 0), 10.0)[N:2 * N, N:2 * N]
soft = np.clip(narrow * 1.7, 0, 1) * 0.85 + np.clip(wide * 1.2, 0, 1) * 0.15
soft = np.clip(soft, 0, 1)
cv2.imwrite(os.path.join(WORK, 'joint_cavity_closed.png'), (soft * 255).astype(np.uint8))   # (the closed version is a NEW file: joint_cavity_closed.png; joint_cavity_soft.png keeps the first, dashed version)
print('mean', soft.mean().round(3), 'share above 0.8', float((soft > 0.8).mean()))
