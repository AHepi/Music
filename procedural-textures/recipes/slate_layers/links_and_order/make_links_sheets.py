# What this does (plain words): two picture sheets and a few numbers for the guide.
#  1. THE DECLARED LINK AND THE STACK ORDER (links_sheet.jpg): the whole recipe at 768 dots with moss.damage_avoid 0 (moss ignores damage), 0.8 (the default)
#     and 1 (moss never on a damaged dot); with heavy damage at 0.8 and at 0; and with the stack order changed so moss is painted OVER damage and grows on it
#     (damage_attract 0.8). The same crop of each is shown enlarged. Numbers: the share of dots where moss covers a damaged dot, measured from the moss
#     and damage colours is not possible from a colour picture, so the sheet is for the eye; the independence table gives the exact numbers of the link.
#  2. TONE BLEND (tone_blend_sheet.jpg): the finished HEIGHT map at 640 dots with combine.tone_blend 0 (real relief only: chips sunk, moss raised),
#     0.35, 0.7 (the default) and 1 (height = brightness of the colour, the way the reference maps were made), next to the reference height.
# Use (plain python): python3 -I make_links_sheets.py
import os
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LINKS = [('avoid_0_moss_ignores_damage', 'moss.damage_avoid 0: moss ignores damage'), ('avoid_0p8_default', 'moss.damage_avoid 0.8 (default)'),
         ('avoid_1_moss_never_on_damage', 'moss.damage_avoid 1: never on damage'), ('damage_heavy_avoid_0', 'heavy damage, damage_avoid 0'),
         ('damage_heavy_avoid_0p8', 'heavy damage, damage_avoid 0.8'), ('order_moss_over_damage_attract_0p8', 'order: moss OVER damage, attract 0.8')]


def crop(picture, x, y, w, out):
    s = picture.shape[0] / 1254.0
    piece = picture[int(y * s):int((y + w) * s), int(x * s):int((x + w) * s)]
    return cv2.resize(piece, (out, out), interpolation=cv2.INTER_NEAREST if piece.shape[0] < out else cv2.INTER_AREA)


def label(piece, text):
    cv2.rectangle(piece, (0, 0), (piece.shape[1], 30), (255, 255, 255), -1)
    cv2.putText(piece, text[:52], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    return piece


panels = [label(crop(cv2.imread(os.path.join(HERE, f'{name}_colour.png')), 330, 560, 420, 560), words) for name, words in LINKS]
cv2.imwrite(os.path.join(HERE, 'links_sheet.jpg'), np.vstack([np.hstack(panels[0:3]), np.hstack(panels[3:6])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
heights = []
reference = cv2.imread(os.path.join(PROC, 'reference', 'slate', 'height_as_uploaded.png'), cv2.IMREAD_UNCHANGED)
reference = reference if reference.ndim == 2 else reference[..., 0]
heights.append(('reference height (a guide only)', reference.astype(np.float64) / 255.0))
for value, name in (('0', 'tone_blend_0'), ('0.35', 'tone_blend_35'), ('0.7 (default)', 'tone_blend_70'), ('1', 'tone_blend_100')):
    h = cv2.imread(os.path.join(HERE, f'{name}_height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    h = (h[..., 0] if h.ndim == 3 else h) / 65535.0
    heights.append((f'combine.tone_blend {value}', h))
panels = []
for words, h in heights:
    grey = np.clip(h * 255.0, 0, 255).astype(np.uint8)
    panels.append(label(cv2.cvtColor(crop(grey, 330, 560, 420, 420), cv2.COLOR_GRAY2BGR), words))
cv2.imwrite(os.path.join(HERE, 'tone_blend_sheet.jpg'), np.hstack(panels), [cv2.IMWRITE_JPEG_QUALITY, 90])
print('written')
