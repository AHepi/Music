# Plain note: measures how well a picture tiles. For each picture it compares the jump across the wrap-around edge (last column next to
# first column, last row next to first row) with the typical jump between two neighbouring columns / rows inside the picture.
# A ratio near 1.0 = seamless; 2 or more = a visible seam. Run: python3 -I seam_ratio.py PICTURE.png [PICTURE2.png ...]
import sys
import numpy as np, cv2
for p in sys.argv[1:]:
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED).astype(np.float64)
    if im.max() > 255: im = im / 257.0
    if im.ndim == 2: im = im[..., None]
    im = im[..., :3]
    h_in = np.abs(np.diff(im, axis=1)).mean(); h_wrap = np.abs(im[:, 0] - im[:, -1]).mean()
    v_in = np.abs(np.diff(im, axis=0)).mean(); v_wrap = np.abs(im[0] - im[-1]).mean()
    print('%-70s size %s  left-right seam %.2f  top-bottom seam %.2f' % (p[-70:], im.shape[:2], h_wrap / h_in, v_wrap / v_in))
