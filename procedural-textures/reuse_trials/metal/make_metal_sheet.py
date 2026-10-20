# What this does (plain words): makes the two pictures for looking at the metal trial.
#   sheet_metal.jpg  row 1: the metal reference | the metal's own earlier recipe (new tile seed_1) | this trial's layered tile (seed set 1), whole
#                           tiles, with their same-kind scores written on them (all three scored by lib/texture_compare.py at 1254 dots, normals
#                           made from the height at strength 5 for the two made tiles);
#                    row 2: the same three, a 420 x 420 dot corner enlarged, to see edges, rivets and rust up close;
#                    row 3: what each box does on this surface: the layout's pieces (a random colour per piece), then the MASK of each layer
#                           (white = where it paints): COLOUR AND FADE (its fade strength), DAMAGE (chipped paint), MOSS (rust), OUTLINE AND
#                           SHADOW, EDGE LIGHT (new), RIVETS (new).
#   repeat_2x2_metal.jpg  the layered tile laid 2 x 2, to look for seams and for obvious repeats.
# The enlarged row is a 400 x 400 dot crop of each tile (enlarged to 600 for looking); where each crop sits is written on it (the crops sit in
# different places because the three walls have their bars in different places; each shows a bar, a rivet and rust).
# Use: python3 -I make_metal_sheet.py   (reads final/seeds_1, checks/masks, final_scores.json; writes the two JPEGs next to this file)
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
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2), (0, -2), (2, 0), (-2, 0)):      # a dark outline, same letter spacing as the white text
            cv2.putText(image, line, (position[0] + dx, position[1] + dy), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, line, position, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return image


def score_text(name):
    row = table[name]
    return f"same-kind {row['overall']:.3f}  colour {row['colour']:.3f}\nheight {row['height']:.3f}  normal {row['normal']:.3f}"


three = [('reference metal (a guide only)', os.path.join(PROC, 'reference', 'metal', 'colour.png'), None, (60, 190)),
         ('earlier metal recipe, new tile seed_1', os.path.join(PROC, 'recipes', 'metal', 'variations', 'seed_1', 'colour.png'),
          'baseline seed_1, normal remade at strength 5', (300, 400)),
         ('this trial: shared layers + new parts (seed set 1)', os.path.join(HERE, 'final', 'seeds_1', 'colour.png'), 'seeds_1', (850, 0))]
whole, close = [], []
for title, path, score_name, (crop_top, crop_left) in three:
    image = cv2.imread(path)
    tile = cv2.resize(image, (CELL, CELL), interpolation=cv2.INTER_AREA)
    label(tile, title)
    if score_name:
        label(tile, score_text(score_name), y=CELL - 40, scale=0.55)
    whole.append(tile)
    corner = cv2.resize(image[crop_top:crop_top + 400, crop_left:crop_left + 400], (CELL, CELL), interpolation=cv2.INTER_CUBIC)
    close.append(label(corner, f'400 x 400 dots (from x {crop_left}, y {crop_top}), enlarged'))
mask_names = [('pieces (new layout)', 'bundle_pieces'), ('COLOUR AND FADE', 'colour_and_fade_mask'), ('DAMAGE = chips', 'damage_mask'),
              ('MOSS = rust', 'moss_mask'), ('OUTLINE AND SHADOW', 'outline_and_shadow_mask'), ('EDGE LIGHT (new)', 'edge_light_mask'),
              ('RIVETS (new)', 'rivets_mask')]
small = (3 * CELL) // len(mask_names)
masks = []
for title, stem in mask_names:
    image = cv2.imread(os.path.join(HERE, 'checks', 'masks', stem + '_colour.png'))
    masks.append(label(cv2.resize(image, (small, small), interpolation=cv2.INTER_AREA), title, scale=0.42, y=18))
row = np.hstack(masks)
row = np.pad(row, ((0, 0), (0, 3 * CELL - row.shape[1]), (0, 0)))
sheet = np.vstack([np.hstack(whole), np.hstack(close), row])
cv2.imwrite(os.path.join(HERE, 'sheet_metal.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
tile = cv2.imread(os.path.join(HERE, 'final', 'seeds_1', 'colour.png'))
repeat = cv2.resize(np.vstack([np.hstack([tile, tile]), np.hstack([tile, tile])]), (1254, 1254), interpolation=cv2.INTER_AREA)
cv2.imwrite(os.path.join(HERE, 'repeat_2x2_metal.jpg'), repeat, [cv2.IMWRITE_JPEG_QUALITY, 88])
print('wrote sheet_metal.jpg and repeat_2x2_metal.jpg')
