# What this does (plain words): makes the two pictures a person looks at to judge the skeleton by eye (plain python).
#  1. compare_with_reference.png : the reference colour next to the skeleton's colour (the same crop, 2 x zoom, and the whole tile small).
#  2. two_by_two.png             : the skeleton colour tiled 2 x 2 (shows whether the tile repeats without a visible seam), plus the
#                                  reference tiled 2 x 2 beside it for comparison. A cross-shaped strip around the seam lines is cut out
#                                  and enlarged in the bottom row.
# The reference is only LOOKED at here; nothing of it goes into the recipe.
# Use: python3 -I make_comparison_sheets.py SKELETON_COLOUR_PNG OUT_FOLDER
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, '..', '..', '..', 'reference', 'slate', 'colour.png')
skeleton = cv2.imread(sys.argv[1])
folder = sys.argv[2]
os.makedirs(folder, exist_ok=True)
reference = cv2.imread(REFERENCE)


def label(image, text):
    banner = np.full((34, image.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([banner, image])


size = skeleton.shape[0]
crop = lambda image: cv2.resize(image[0:size // 2, 0:size // 2], None, fx=1.0, fy=1.0)
whole = lambda image: cv2.resize(image, (size // 2, size // 2), interpolation=cv2.INTER_AREA)
top = np.hstack([label(crop(cv2.resize(reference, (size, size))), 'reference: top-left quarter'), label(crop(skeleton), 'skeleton (layout + flat tones): same quarter')])
bottom = np.hstack([label(whole(reference), 'reference, whole tile at half size'), label(whole(skeleton), 'skeleton, whole tile at half size')])
cv2.imwrite(os.path.join(folder, 'compare_with_reference.png'), np.vstack([top, bottom]))

tiled = lambda image: np.tile(image, (2, 2, 1))
two_skeleton, two_reference = tiled(skeleton), tiled(cv2.resize(reference, (size, size)))
half = lambda image: cv2.resize(image, (image.shape[1] // 2, image.shape[0] // 2), interpolation=cv2.INTER_AREA)
row1 = np.hstack([label(half(two_skeleton), 'skeleton tiled 2 x 2'), label(half(two_reference), 'reference tiled 2 x 2')])


def seam_strip(image):
    s = size
    vertical = image[s // 2:s * 3 // 2, s - 150:s + 150]            # around the vertical seam (x = tile edge), one tile tall
    horizontal = image[s - 150:s + 150, s // 2:s * 3 // 2]          # around the horizontal seam
    return vertical, horizontal


v1, h1 = seam_strip(two_skeleton)
v2, h2 = seam_strip(two_reference)
strip = lambda v, h: np.hstack([cv2.resize(v, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), cv2.resize(np.rot90(h), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)])
a, b = strip(v1, h1), strip(v2, h2)
width = row1.shape[1] // 2
row2 = np.hstack([label(cv2.resize(a, (width, int(a.shape[0] * width / a.shape[1]))), 'skeleton: seams (left: vertical seam, right: horizontal seam turned)'),
                  label(cv2.resize(b, (width, int(b.shape[0] * width / b.shape[1]))), 'reference: the same two seams')])
pad = row1.shape[0] - row2.shape[0]
if pad > 0:
    row2 = np.vstack([row2, np.full((pad, row2.shape[1], 3), 255, np.uint8)])
cv2.imwrite(os.path.join(folder, 'two_by_two.png'), np.vstack([row1, row2[:row2.shape[0]]]) if pad <= 0 else np.vstack([row1, row2]))
print('ok')
