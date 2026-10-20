# What this does (plain words): makes the picture sheet of the BRICK reuse test: the finished brick wall, the brick wall with only the COLOUR AND FADE
# layer, where DAMAGE, MOSS and OUTLINE AND SHADOW paint on the bricks (their masks, white = the layer paints there), and the slate default tile for
# comparison; every panel is the whole 1254-dot tile shrunk, plus one enlarged crop of the finished wall. It also scores the brick wall against the BRICK
# reference with the project's "same kind" tool, only as a sanity check (the brick reference was NOT used to tune anything).
# Use (plain python): python3 -I make_reuse_sheet.py
import json, os, subprocess
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
B = os.path.join(HERE, 'baked')
panels = [('brick_all_colour.png', 'BRICK: all layers (finished)'), ('brick_colour_and_fade_only_colour.png', 'BRICK: COLOUR AND FADE alone'),
          ('mask_damage_colour.png', 'DAMAGE mask on bricks'), ('mask_moss_colour.png', 'MOSS mask on bricks'),
          ('mask_outline_colour.png', 'OUTLINE AND SHADOW mask on bricks'), (os.path.join('..', '..', 'outputs', 'default', 'colour.png'), 'SLATE default (same layer files)')]
cell = 600
tiles = []
for name, text in panels:
    picture = cv2.resize(cv2.imread(os.path.join(B, name)), (cell, cell), interpolation=cv2.INTER_AREA)
    cv2.rectangle(picture, (0, 0), (cell, 34), (255, 255, 255), -1)
    cv2.putText(picture, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2)
    tiles.append(picture)
grid = np.vstack([np.hstack(tiles[0:3]), np.hstack(tiles[3:6])])
crop = cv2.imread(os.path.join(B, 'brick_all_colour.png'))[300:600, 300:900]
crop = cv2.resize(crop, (1800, 900), interpolation=cv2.INTER_NEAREST)
cv2.putText(crop, 'finished brick wall, enlarged 3 x (600 x 300 dots of the 1254-dot tile)', (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
cv2.imwrite(os.path.join(HERE, 'reuse_sheet.png'), np.vstack([grid, crop]))
# sanity check against the brick reference (not a target)
score_folder = os.path.join(HERE, 'score_against_brick')
os.makedirs(score_folder, exist_ok=True)
for kind, name in (('colour', 'brick_all_colour.png'), ('height', 'brick_all_height.png'), ('normal', 'brick_all_normal.png')):
    target = os.path.join(score_folder, kind + '.png')
    if os.path.lexists(target):
        os.remove(target)
    os.symlink(os.path.join(B, name), target)
subprocess.run(['python3', '-I', os.path.join(PROC, 'lib', 'texture_compare.py'), 'brick', score_folder, '--json', os.path.join(score_folder, 'score.json')], capture_output=True)
for kind in ('colour', 'height', 'normal'):
    os.remove(os.path.join(score_folder, kind + '.png'))
score = json.load(open(os.path.join(score_folder, 'score.json')))
print('against the BRICK reference: overall', score['overall'], 'groups', score['groups'])
