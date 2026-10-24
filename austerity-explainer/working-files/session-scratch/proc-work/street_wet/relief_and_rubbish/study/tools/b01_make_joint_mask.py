# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Makes the "joint pictures" for the road setts from Poly Haven's square cobblestone colour picture (2048 x 2048 dots; it repeats every 2 m on the road, so one
# dot is 1 mm). The JOINTS are the thin gaps between the stones; the STONES are the faces.
#   joint_cores.png   (R = the joint (its edge dots trimmed by one dot), G = the middle of every stone face, B = 0): the MEASURING picture. Blender paints the road with it (through the
#                     road's own texture coordinates), so each dot of a render can be called "joint" or "stone" with no doubt (the dots near an edge are left out).
#   joint_cavity.png  (grey: 1 in the joint, falling smoothly to 0 about 12 mm into the stone): the SOLUTION picture ("cavity": how deep in a crevice a dot is, so how
#                     little light reaches it). Used in section 5 of the study to keep joints dark whatever the light.
#   joint_height.png  (grey: 1 in the joint, 0 on the stone, with an edge only about 3 mm wide): the groove profile for REAL GEOMETRY (section 5)
#   joint_mask_check.jpg  the check sheet (colour picture, mask, mask in red on the colour picture) to be judged by eye.
#   sett_numbers.json  the average colour of the picture (linear), of its stones, of its joints; the share of joint.
# How the joints are found (second try; the first used the height picture and was broken, because its joints are patchy): a "black top-hat" on the brightness (a
# picture trick: close the picture with a kernel wider than a joint, then subtract the picture; it keeps thin dark lines and drops wide dark blotches), threshold 25 of 255.
# Run: python3 -I b01_make_joint_mask.py
import json
import os

import cv2
import numpy as np

ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet'
OUT = os.path.join(ROOT, 'relief_and_rubbish/study/work')
colour = cv2.imread(os.path.join(ROOT, 'set_copy/textures/square_cobblestone_colour.jpg'))
N = colour.shape[0]
lab = cv2.cvtColor(colour, cv2.COLOR_BGR2LAB).astype(np.float32)
L_s = cv2.GaussianBlur(lab[..., 0], (0, 0), 2.5)
tiled = np.tile(L_s, (3, 3))
closed = cv2.morphologyEx(tiled, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (51, 51)))
tophat = (closed - tiled)[N:2 * N, N:2 * N]
raw = (tophat > 25).astype(np.uint8)
raw = cv2.morphologyEx(raw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
count, labels, stats, _ = cv2.connectedComponentsWithStats(raw, connectivity=8)
keep = np.zeros(count, bool)
keep[1:] = stats[1:, cv2.CC_STAT_AREA] > 300
mask = keep[labels].astype(np.uint8)
print('joint share (whole mask)', round(float(mask.mean()), 3), 'components kept', int(keep.sum()))
tiled_mask = np.tile(mask, (3, 3))
core = cv2.erode(tiled_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))[N:2 * N, N:2 * N]
dist_outside = cv2.distanceTransform((1 - tiled_mask).astype(np.uint8), cv2.DIST_L2, 5)[N:2 * N, N:2 * N]       # dots from the nearest joint dot (0 inside)
stone_core = (dist_outside > 10).astype(np.uint8)
print('joint core share', round(float(core.mean()), 3), 'stone core share', round(float(stone_core.mean()), 3))
cores = np.zeros((N, N, 3), np.uint8)
cores[..., 2] = core * 255          # OpenCV writes BGR: this is the R channel
cores[..., 1] = stone_core * 255
cv2.imwrite(os.path.join(OUT, 'joint_cores.png'), cores)
cavity = np.where(mask > 0, 1.0, np.exp(-dist_outside / 7.0)).astype(np.float32)
cavity = cv2.GaussianBlur(cavity, (0, 0), 1.2)
cv2.imwrite(os.path.join(OUT, 'joint_cavity.png'), (np.clip(cavity, 0, 1) * 255).astype(np.uint8))
# joint_height.png: the same joints as a SHARP groove profile for real geometry: 1 in the joint, falling to 0 over about 3 mm (a slightly rounded stone edge), so the stone tops stay flat
height_profile = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.6)
cv2.imwrite(os.path.join(OUT, 'joint_height.png'), (np.clip(height_profile, 0, 1) * 255).astype(np.uint8))


def to_linear(x):
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


rgb = colour[..., ::-1].astype(np.float32)
lin = to_linear(rgb)
numbers = dict(joint_share=float(mask.mean()), joint_core_share=float(core.mean()), stone_core_share=float(stone_core.mean()),
               mean_linear_rgb=[float(v) for v in lin.reshape(-1, 3).mean(0)],
               stone_linear_rgb=[float(v) for v in lin[stone_core > 0].mean(0)], joint_linear_rgb=[float(v) for v in lin[core > 0].mean(0)])
numbers['joint_over_stone_brightness'] = float(np.mean(numbers['joint_linear_rgb']) / np.mean(numbers['stone_linear_rgb']))
json.dump(numbers, open(os.path.join(OUT, 'sett_numbers.json'), 'w'), indent=1)
print(json.dumps(numbers, indent=1))
crop = (slice(0, 800), slice(0, 800))
c = colour[crop].copy()
over = c.copy()
over[core[crop] > 0] = (0, 0, 255)
over[stone_core[crop] > 0] = (255, 120, 0)
over = cv2.addWeighted(c, 0.45, over, 0.55, 0)
sheet = np.concatenate([cv2.resize(c, (500, 500)), cv2.resize(cv2.cvtColor((np.clip(cavity, 0, 1) * 255).astype(np.uint8)[crop], cv2.COLOR_GRAY2BGR), (500, 500)), cv2.resize(over, (500, 500))], axis=1)
cv2.imwrite(os.path.join(OUT, 'joint_mask_check.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
