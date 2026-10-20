# What this does (plain words): turns the independence test's baked pictures into ONE sheet a person can read: one row per change (a layer's Amount set to 0,
# or its Seed + 1). In each row: the finished colour after the change, and a "where did it change" picture: RED = the finished colour changed here,
# DARK GREEN = the changing layer's own region (where its Mask is above zero, or the whole slate for COLOUR AND FADE), BLUE = height or roughness changed.
# If the layers are independent, every red dot lies inside the green region, and red-on-black (outside the region) never appears.
# Use (plain python): python3 -I make_independence_sheet.py [FOLDER]
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'independence_full')
NAMES = ['layout_Seed_plus_1', 'colour_and_fade_Amount_0', 'colour_and_fade_Seed_plus_1', 'damage_Amount_0', 'damage_Seed_plus_1', 'moss_Amount_0', 'moss_Seed_plus_1',
         'outline_and_shadow_Amount_0', 'outline_and_shadow_Seed_plus_1']
cell = 384


def label(picture, text):
    cv2.rectangle(picture, (0, 0), (cell, 26), (0, 0, 0), -1)
    cv2.putText(picture, text, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return picture


base = cv2.resize(cv2.imread(os.path.join(FOLDER, 'base_final', 'view_colour.png')), (cell, cell))
rows = [np.hstack([label(base.copy(), 'BASELINE (default settings)'), np.zeros((cell, cell, 3), np.uint8), np.zeros((cell, cell, 3), np.uint8)])]
for name in NAMES:
    colour = cv2.resize(cv2.imread(os.path.join(FOLDER, name + '_final', 'view_colour.png')), (cell, cell))
    where = cv2.resize(cv2.imread(os.path.join(FOLDER, name + '_where.png')), (cell, cell), interpolation=cv2.INTER_NEAREST)
    # the difference of the finished colours, amplified, as a plain grey picture
    diff = np.abs(colour.astype(int) - base.astype(int)).max(axis=2)
    diff = np.clip(diff * 4, 0, 255).astype(np.uint8)
    rows.append(np.hstack([label(colour, name.replace('_', ' ')), label(where, 'where: red+blue=changed, green=own region'), label(cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR), 'colour difference x4 (grey)')]))
cv2.imwrite(os.path.join(FOLDER, 'independence_sheet.png'), np.vstack(rows))
print('written')
