# What this does (plain words): makes the three pictures for looking at the wood trial (a copy of the brick trial's make_brick_sheet.py and
# seed_sets_sheet.py with the wood names).
#   sheet_wood.jpg   row 1: the wood reference | the wood's own earlier recipe (new tile sample_101) | this trial's layered tile (seed set 1), whole
#                           tiles, with their same-kind scores written on them;
#                    row 2: the same three, a 400 x 400 dot piece enlarged, to see edges, grain and rust up close;
#                    rows 3 and 4: what each box does on this surface: the layout's boards (a random colour per board) and the MASK of each layer
#                           (white = where it paints): COLOUR AND FADE (its colour with the boards), GRAIN, MOSS, DAMAGE, CRACKS, KNOTS, OUTLINE AND SHADOW.
#   final_seed_sets.jpg  the three final tiles of the trial (seed sets 1, 2, 3) and the earlier recipe's tile, side by side with their scores.
#   repeat_2x2_wood.jpg  the trial's tile laid 2 x 2, to look for seams and for obvious repeats.
# Use: python3 -I make_pictures.py   (reads final/seeds_*, checks/masks, final_scores.json; writes the three JPEGs next to this file)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
CELL = 600
with open(os.path.join(HERE, 'final_scores.json')) as handle:
    table = json.load(handle)['table']
BASELINE = 'baseline sample_101, normal remade at strength 8'


def label(image, text, y=26, scale=0.62):
    for line_number, line in enumerate(text.split('\n')):
        position = (10, y + line_number * int(30 * scale / 0.62))
        cv2.putText(image, line, position, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(image, line, position, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return image


def score_text(name):
    row = table[name]
    return f"same-kind {row['overall']:.3f}  colour {row['colour']:.3f}\nheight {row['height']:.3f}  normal {row['normal']:.3f}"


three = [('reference wood (a guide only)', os.path.join(PROC, 'reference', 'wood', 'colour.png'), None),
         ('earlier wood recipe, new tile sample_101', os.path.join(PROC, 'recipes', 'wood', 'variations', 'sample_101', 'colour.png'), BASELINE),
         ('this trial: shared layers + new parts', os.path.join(HERE, 'final', 'seeds_1', 'colour.png'), 'seeds_1')]
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
mask_names = [('boards (layout)', 'bundle_pieces'), ('COLOUR AND FADE (colour)', 'colour_and_fade_colour'), ('GRAIN (new)', 'grain_mask'), ('MOSS (as rust)', 'moss_mask'),
              ('DAMAGE', 'damage_mask'), ('CRACKS (new)', 'cracks_mask'), ('KNOTS (new)', 'knots_mask'), ('OUTLINE AND SHADOW', 'outline_and_shadow_mask')]
small = (3 * CELL) // 4
masks = []
for title, stem in mask_names:
    image = cv2.imread(os.path.join(HERE, 'checks', 'masks', stem + '_colour.png'))
    masks.append(label(cv2.resize(image, (small, small), interpolation=cv2.INTER_AREA), title, scale=0.5))
sheet = np.vstack([np.hstack(whole), np.hstack(close), np.hstack(masks[:4]), np.hstack(masks[4:])])
cv2.imwrite(os.path.join(HERE, 'sheet_wood.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])

cells = []
for name, path in (('seeds_1', os.path.join(HERE, 'final', 'seeds_1', 'colour.png')), ('seeds_2', os.path.join(HERE, 'final', 'seeds_2', 'colour.png')),
                   ('seeds_3', os.path.join(HERE, 'final', 'seeds_3', 'colour.png')),
                   (BASELINE, os.path.join(PROC, 'recipes', 'wood', 'variations', 'sample_101', 'colour.png'))):
    tile = cv2.resize(cv2.imread(path), (560, 560), interpolation=cv2.INTER_AREA)
    shown = 'earlier recipe, sample_101' if name == BASELINE else name
    for y, text in ((24, shown), (50, f"same-kind {table[name]['overall']:.3f}  colour {table[name]['colour']:.3f}")):
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(tile, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(tile)
cv2.imwrite(os.path.join(HERE, 'final_seed_sets.jpg'), np.hstack(cells), [cv2.IMWRITE_JPEG_QUALITY, 86])
tile = cv2.imread(os.path.join(HERE, 'final', 'seeds_1', 'colour.png'))
repeat = cv2.resize(np.vstack([np.hstack([tile, tile]), np.hstack([tile, tile])]), (1254, 1254), interpolation=cv2.INTER_AREA)
cv2.imwrite(os.path.join(HERE, 'repeat_2x2_wood.jpg'), repeat, [cv2.IMWRITE_JPEG_QUALITY, 88])
print('wrote sheet_wood.jpg, final_seed_sets.jpg and repeat_2x2_wood.jpg')
