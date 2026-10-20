# What this does (plain words): checks whether a sampled brick tile WITHOUT grain shows a seam where the tile repeats. Grain (a random number per dot)
# raises the normal dot-to-dot jump and so can hide a seam from the jump measure; this tile has no grain, so the measure is fair.
# Two measures, both on the colour picture's brightness:
#   1. dot jump: the mean jump between the last and the first column (and row) of the tile, divided by the mean jump between neighbouring columns
#      (rows) inside the tile. 1.0 = the wrap edge is as smooth as anywhere else.
#   2. slow tone jump: the brightness averaged over a 40-dot band on each side of a line, compared band against band along the line (in 40-dot steps).
#      This catches a slow change of tone (the generator's "tone dial" is made of sine waves that do not repeat every 1254 dots) that a dot measure misses.
#      The wrap edge is compared with 20 ordinary lines inside the tile.
# Also writes a 2 x 2 repeat of a 400-dot square around the corner where four tiles meet, to look at.
# Run: python3 -I seam_check.py TILE_FOLDER OUT_JSON OUT_PNG
# The tile checked for the brick guide: description_14_no_grain.json = recipes/brick/variations/description_14.json with only the grain removed (the checker
# made it as recipes/brick/verify/var14_nograin.json), baked at 1254 dots, 16 samples, with recipes/brick/generator/brick_generator.py (bake_tile_14_no_grain.json).
import json
import sys

import cv2
import numpy as np

folder, out_json, out_png = sys.argv[1:4]
colour = cv2.imread(folder + '/colour.png')[..., ::-1].astype(float)
grey = colour @ np.array([0.299, 0.587, 0.114])
size = grey.shape[0]


def dot_jump(g):
    edge = np.abs(g[:, 0] - g[:, -1]).mean()
    inside = np.abs(np.diff(g, axis=1)).mean()
    return float(edge / inside)


def band_jump(g, x, band=40, step=40):
    """Mean difference of band averages left and right of the vertical line at x (wrapping round)."""
    rolled = np.roll(g, -x, axis=1)                      # the line now sits between column size-1 and column 0
    left = rolled[:, -band:].mean(1)
    right = rolled[:, :band].mean(1)
    rows = size // step
    left = left[:rows * step].reshape(rows, step).mean(1)
    right = right[:rows * step].reshape(rows, step).mean(1)
    return float(np.abs(left - right).mean())


result = {'dot_jump_ratio_sideways': round(dot_jump(grey), 3), 'dot_jump_ratio_up_down': round(dot_jump(grey.T), 3)}
for name, g in (('sideways', grey), ('up_down', grey.T)):
    inner = [band_jump(g, int(x)) for x in np.linspace(60, size - 60, 20)]
    result[f'slow_tone_jump_at_wrap_edge_{name}'] = round(band_jump(g, 0), 2)
    result[f'slow_tone_jump_inner_lines_{name}_mean'] = round(float(np.mean(inner)), 2)
    result[f'slow_tone_jump_inner_lines_{name}_max'] = round(float(np.max(inner)), 2)
    result[f'wrap_edge_rank_among_21_lines_{name}'] = int(sum(v > band_jump(g, 0) for v in inner) + 1)
json.dump(result, open(out_json, 'w'), indent=1)
print(json.dumps(result, indent=1))
tiled = np.tile(colour, (2, 2, 1))
piece = tiled[size - 200:size + 200, size - 200:size + 200]
piece = cv2.resize(piece.astype(np.uint8), (600, 600), interpolation=cv2.INTER_NEAREST)
cv2.imwrite(out_png, piece[..., ::-1])
