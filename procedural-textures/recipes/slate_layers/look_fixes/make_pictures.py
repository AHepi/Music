# What this does (plain words): makes the four "look at it" pictures of the look-fixes round, as JPEG files in this folder:
#   before_after_colour.jpg  the whole tile: reference | before (old default) | after (new default), each shrunk to 900 dots
#   before_after_zoom.jpg    the same 0.4-tile window of each at full size (1 picture dot = 1 dot of the 1254-dot tile)
#   before_after_lit.jpg     the tiles under a low raking light (made by lit_several.py): top row the whole tile, bottom row a 0.4-tile window
#   maps_after.jpg           the five maps of the new default: colour, height, normal, roughness, metallic
# It measures nothing. Use: python3 -I make_pictures.py
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REFERENCE = os.path.join(PROC, 'reference', 'slate')
BEFORE = os.path.join(HERE, '..', 'outputs', 'default_before_look_fixes')
AFTER = os.path.join(HERE, '..', 'outputs', 'default')
LIT = os.path.join(HERE, 'lit')


def label(picture, text):
    picture = picture.copy()
    cv2.rectangle(picture, (0, 0), (12 + 15 * len(text), 36), (0, 0, 0), -1)
    cv2.putText(picture, text, (6, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    return picture


def side_by_side(pictures, gap=10):
    out = []
    for picture in pictures:
        out += [picture, np.full((picture.shape[0], gap, 3), 255, np.uint8)]
    return np.hstack(out[:-1])


def save(name, picture):
    cv2.imwrite(os.path.join(HERE, name), picture, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('wrote', name, picture.shape[1], 'x', picture.shape[0])


def grey(path):
    picture = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if picture.ndim == 3:
        picture = picture[..., 0]
    picture = picture.astype(np.float32) / (65535.0 if picture.dtype == np.uint16 else 255.0)
    return cv2.cvtColor((picture * 255).round().astype(np.uint8), cv2.COLOR_GRAY2BGR)


def main():
    names = ['reference', 'before', 'after']
    colours = [cv2.imread(os.path.join(folder, 'colour.png')) for folder in (REFERENCE, BEFORE, AFTER)]
    save('before_after_colour.jpg', side_by_side([label(cv2.resize(c, (900, 900), interpolation=cv2.INTER_AREA), n) for c, n in zip(colours, names)]))
    window = int(round(0.4 * 1254))
    x0, y0 = int(0.3 * 1254), int(0.3 * 1254)
    save('before_after_zoom.jpg', side_by_side([label(c[y0:y0 + window, x0:x0 + window], n) for c, n in zip(colours, names)]))
    rows = []
    for kind in ('full', 'zoom'):
        pictures = [cv2.imread(os.path.join(LIT, f'{n}_{kind}.png')) for n in names]
        if all(p is not None for p in pictures):
            rows.append(side_by_side([label(p, f'{n} - raking light, {"whole tile" if kind == "full" else "0.4-tile window"}') for p, n in zip(pictures, names)]))
    if rows:
        lit = rows[0] if len(rows) == 1 else np.vstack([rows[0], np.full((10, rows[0].shape[1], 3), 255, np.uint8), rows[1]])
        save('before_after_lit.jpg', lit)
    maps = [('colour', cv2.imread(os.path.join(AFTER, 'colour.png'))), ('height (16 bit)', grey(os.path.join(AFTER, 'height.png'))),
            ('normal (strength 7)', cv2.imread(os.path.join(AFTER, 'normal.png'))), ('roughness', grey(os.path.join(AFTER, 'roughness.png'))),
            ('metallic', grey(os.path.join(AFTER, 'metallic.png')))]
    save('maps_after.jpg', side_by_side([label(cv2.resize(p, (600, 600), interpolation=cv2.INTER_AREA), n) for n, p in maps]))


if __name__ == '__main__':
    main()
