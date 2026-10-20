# What this does (plain words): puts the colour pictures of one tuning round side by side in a labelled JPEG sheet (top row: whole tiles; bottom
# row: the top-left quarter enlarged, to see edges), with the wood reference first as a guide. It also prints a few plain numbers per picture
# next to the reference's: the share of very dark dots (brightness under 35), the middle brightness, the share of rust-orange dots (red minus blue
# over 55), the share of grey-blue dots, and the average colour. (Copied from the brick trial's make_look_sheet.py; the numbers changed for wood.)
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
    warmth = rgb[..., 0] - rgb[..., 2]
    grey_blue = (warmth < 12) & (brightness > 40) & (brightness < 110)
    return (f'very dark {100 * (brightness < 35).mean():.1f}%  middle {np.median(brightness):.0f}  rust {100 * (warmth > 55).mean():.1f}%  '
            f'grey-blue {100 * grey_blue.mean():.1f}%  mean {rgb.reshape(-1, 3).mean(axis=0).round().astype(int).tolist()}')


def label(image, text):
    cv2.putText(image, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(image, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return image


pictures = [('reference (guide only)', cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png')))]
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
