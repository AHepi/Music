# What this does (plain words): puts the colour pictures of one tuning round side by side in a labelled JPEG sheet (top row: whole tiles; bottom
# row: the top-left quarter enlarged, to see edges), with the brick reference first as a guide. It also prints a few plain numbers per picture
# next to the reference's: the share of dark dots (brightness under 70), the share of pale mortar-like dots, and the average colour.
# Use: python3 -I make_look_sheet.py ROUND_FOLDER OUT.jpg view_name [view_name ...]   (reads ROUND_FOLDER/<view>_colour.png)
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
folder, out_path, names = sys.argv[1], sys.argv[2], sys.argv[3:]
CELL = 460


def numbers(bgr):
    rgb = bgr[..., ::-1].astype(np.float64)
    brightness = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    redness = rgb[..., 0] - rgb[..., 2]
    pale_mortar = (brightness > 85) & (redness < 50)
    return f'dark {100 * (brightness < 70).mean():.1f}%  pale-grey {100 * pale_mortar.mean():.1f}%  mean {rgb.reshape(-1, 3).mean(axis=0).round().astype(int).tolist()}'


def label(image, text):
    cv2.putText(image, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(image, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return image


pictures = [('reference (guide only)', cv2.imread(os.path.join(PROC, 'reference', 'brick', 'colour.png')))]
pictures += [(name, cv2.imread(os.path.join(folder, name + '_colour.png'))) for name in names]
top, bottom = [], []
for name, image in pictures:
    print(f'{name:40s} {numbers(image)}')
    whole = cv2.resize(image, (CELL, CELL), interpolation=cv2.INTER_AREA)
    quarter = image[:image.shape[0] // 3, :image.shape[1] // 3]
    zoom = cv2.resize(quarter, (CELL, CELL), interpolation=cv2.INTER_NEAREST)
    top.append(label(whole, name[:44]))
    bottom.append(label(zoom, 'top-left third, enlarged'))
sheet = np.vstack([np.hstack(top), np.hstack(bottom)])
cv2.imwrite(out_path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])
print('sheet:', out_path)
