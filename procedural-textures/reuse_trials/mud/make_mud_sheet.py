# What this does (plain words): makes the pictures for looking at the mud trial.
#   sheet_mud.jpg   row 1: the mud reference | the mud's own earlier recipe (new tile 101) | this trial's layered tile (seed set 1), whole tiles,
#                   with their same-kind scores written on them;
#                   row 2: the same three, a 400 x 400 dot corner enlarged, to see clods, ruts, puddle edges and stones up close;
#                   row 3: what each box does on this surface: the layout's ground patches (a random colour per patch), then the MASK of each layer
#                   (white = where it paints): COLOUR AND FADE (its fade strength), RUTS (new), MOSS (puddles), DAMAGE (switched off), STONES (new),
#                   OUTLINE AND SHADOW (switched off).
#   repeat_2x2_mud.jpg  the layered tile laid 2 x 2, to look for seams and for obvious repeats.
# Use: python3 -I make_mud_sheet.py   (reads final/seeds_1, checks/masks, final_scores.json; writes the two JPEGs next to this file)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
CELL = 600
with open(os.path.join(HERE, 'final_scores.json')) as handle:
    table = json.load(handle)['table']


def label(image, text, y=26, scale=0.62):
    for line_number, line in enumerate(text.split('\n')):
        position = (10, y + line_number * int(30 * scale / 0.62))
        cv2.putText(image, line, position, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(image, line, position, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return image


def score_text(name):
    row = table[name]
    return f"same-kind {row['overall']:.3f}  colour {row['colour']:.3f}\nheight {row['height']:.3f}  normal {row['normal']:.3f}"


BASELINE = 'baseline tile_101, normal remade at strength 9'
three = [('reference mud (a guide only)', os.path.join(PROC, 'reference', 'mud', 'colour.png'), None),
         ('earlier mud recipe, new tile 101', os.path.join(PROC, 'recipes', 'mud', 'variations', 'tile_101', 'colour.png'), BASELINE),
         ('this trial: shared layers + RUTS + STONES', os.path.join(HERE, 'final', 'seeds_1', 'colour.png'), 'seeds_1')]
whole, close = [], []
for title, path, score_name in three:
    image = cv2.imread(path)
    tile = cv2.resize(image, (CELL, CELL), interpolation=cv2.INTER_AREA)
    label(tile, title)
    if score_name:
        label(tile, score_text(score_name), y=CELL - 40, scale=0.55)
    whole.append(tile)
    corner = cv2.resize(image[420:820, 420:820], (CELL, CELL), interpolation=cv2.INTER_NEAREST)
    close.append(label(corner, '400 x 400 dots, enlarged'))
mask_names = [('ground patches (layout)', 'bundle_pieces'), ('COLOUR AND FADE', 'colour_and_fade_mask'), ('RUTS (new)', 'ruts_mask'), ('MOSS = puddles', 'moss_mask'),
              ('DAMAGE (off)', 'damage_mask'), ('STONES (new)', 'stones_mask'), ('OUTLINE (off)', 'outline_and_shadow_mask')]
small = (3 * CELL) // len(mask_names)
masks = []
for title, stem in mask_names:
    image = cv2.imread(os.path.join(HERE, 'checks', 'masks', stem + '_colour.png'))
    masks.append(label(cv2.resize(image, (small, small), interpolation=cv2.INTER_AREA), title, scale=0.45))
masks.append(np.zeros((small, 3 * CELL - small * len(mask_names), 3), np.uint8)) if 3 * CELL - small * len(mask_names) > 0 else None
sheet = np.vstack([np.hstack(whole), np.hstack(close), np.hstack(masks)])
cv2.imwrite(os.path.join(HERE, 'sheet_mud.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
tile = cv2.imread(os.path.join(HERE, 'final', 'seeds_1', 'colour.png'))
repeat = cv2.resize(np.vstack([np.hstack([tile, tile]), np.hstack([tile, tile])]), (1254, 1254), interpolation=cv2.INTER_AREA)
cv2.imwrite(os.path.join(HERE, 'repeat_2x2_mud.jpg'), repeat, [cv2.IMWRITE_JPEG_QUALITY, 88])
print('wrote sheet_mud.jpg and repeat_2x2_mud.jpg', sheet.shape)
