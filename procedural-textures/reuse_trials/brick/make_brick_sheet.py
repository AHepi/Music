# What this does (plain words): makes the two pictures for looking at the brick trial.
#   sheet_brick.jpg  row 1: the brick reference | the brick's own earlier recipe (new tile 11) | this trial's layered tile (seed set 1), whole tiles,
#                           with their same-kind scores written on them;
#                    row 2: the same three, a 400 x 400 dot corner enlarged, to see edges, soot and mortar up close;
#                    row 3: what each box does on this surface: the layout's bricks (a random colour per brick), then the MASK of each layer
#                           (white = where it paints): COLOUR AND FADE (its fade strength), DAMAGE, MOSS (switched off), OUTLINE AND SHADOW, GRIME.
#   repeat_2x2_brick.jpg  the layered tile laid 2 x 2, to look for seams and for obvious repeats.
# Use: python3 -I make_brick_sheet.py   (reads final/seeds_1, checks/masks, final_scores.json; writes the two JPEGs next to this file)
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


three = [('reference brick (a guide only)', os.path.join(PROC, 'reference', 'brick', 'colour.png'), None),
         ('earlier brick recipe, new tile 11', os.path.join(PROC, 'recipes', 'brick', 'variations', 'tile_11', 'colour.png'),
          'baseline tile_11, normal remade at strength 6'),
         ('this trial: shared layers + GRIME', os.path.join(HERE, 'final', 'seeds_1', 'colour.png'), 'seeds_1')]
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
mask_names = [('bricks (layout)', 'bundle_pieces'), ('COLOUR AND FADE', 'colour_and_fade_mask'), ('DAMAGE', 'damage_mask'),
              ('MOSS (off)', 'moss_mask'), ('OUTLINE AND SHADOW', 'outline_and_shadow_mask'), ('GRIME (new)', 'grime_mask')]
small = (3 * CELL) // len(mask_names)
masks = []
for title, stem in mask_names:
    image = cv2.imread(os.path.join(HERE, 'checks', 'masks', stem + '_colour.png'))
    masks.append(label(cv2.resize(image, (small, small), interpolation=cv2.INTER_AREA), title, scale=0.5))
sheet = np.vstack([np.hstack(whole), np.hstack(close), np.hstack(masks)])
cv2.imwrite(os.path.join(HERE, 'sheet_brick.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
tile = cv2.imread(os.path.join(HERE, 'final', 'seeds_1', 'colour.png'))
repeat = cv2.resize(np.vstack([np.hstack([tile, tile]), np.hstack([tile, tile])]), (1254, 1254), interpolation=cv2.INTER_AREA)
cv2.imwrite(os.path.join(HERE, 'repeat_2x2_brick.jpg'), repeat, [cv2.IMWRITE_JPEG_QUALITY, 88])
print('wrote sheet_brick.jpg and repeat_2x2_brick.jpg')
