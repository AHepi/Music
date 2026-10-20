# What this does (plain words): puts pictures side by side so they can be LOOKED at: the reference, the old default and any test bakes, as
# full tiles, as an enlarged crop (the same window of each), or as height pictures (stretched so the 1 % darkest is black and the 1 % lightest
# white). It writes JPEG files only. It measures nothing.
# Use: python3 -I views.py OUT.jpg MODE SIZE PICTURE [PICTURE ...]
#   MODE: full | crop:X,Y,W (a W x W window from dot X,Y of a SIZE-dot tile, shown at 600 dots) | height | heightcrop:X,Y,W
#   PICTURE: a colour.png / height.png path, or "reference" (reference colour or height, shrunk to SIZE)
import os
import sys

import cv2
import numpy as np

PROC = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))


def load(path, size, as_height):
    if path == 'reference':
        path = os.path.join(PROC, 'reference', 'slate', 'height.png' if as_height else 'colour.png')
    picture = cv2.imread(path, cv2.IMREAD_UNCHANGED if as_height else cv2.IMREAD_COLOR)
    if as_height:
        picture = (picture[..., 0] if picture.ndim == 3 else picture).astype(np.float32)
    if picture.shape[0] != size:
        picture = cv2.resize(picture, (size, size), interpolation=cv2.INTER_AREA)
    if as_height:
        low, high = np.percentile(picture, [1, 99])
        picture = cv2.cvtColor(np.clip((picture - low) / (high - low) * 255, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    return picture


def main():
    out, mode, size, paths = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
    as_height = mode.startswith('height')
    tiles = []
    for path in paths:
        picture = load(path, size, as_height)
        if ':' in mode:
            x, y, w = [int(v) for v in mode.split(':')[1].split(',')]
            picture = cv2.resize(picture[y:y + w, x:x + w], (600, 600), interpolation=cv2.INTER_NEAREST if w <= 300 else cv2.INTER_AREA)
        tiles.append(picture)
        tiles.append(np.full((tiles[-1].shape[0], 10, 3), 255, np.uint8))
    cv2.imwrite(out, np.hstack(tiles[:-1]), [cv2.IMWRITE_JPEG_QUALITY, 90])


if __name__ == '__main__':
    main()
