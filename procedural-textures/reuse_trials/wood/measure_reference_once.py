# What this does (plain words): measures the wood reference ONCE, as a guide for choosing settings by hand. It only reads numbers that describe
# the whole picture (its general character), never the place or outline of any single board, crack, knot or blot:
#   * copies the stored summary numbers of the earlier wood build: the 16-colour palette (recipes/wood/analysis/palette16.json), the colour
#     family shares and board/gap summary (wood_measurements.json), the strip sizes (paint_model.json), the height rule (derivation_ceiling.json);
#   * measures four new whole-picture numbers on reference/wood/colour.png: the spread of grey (brightness) as percentiles, the share of very
#     dark dots, the share of grey-blue dots and the share of rust-orange dots.
# It writes reference_measures.json next to this file. It never writes per-element lists and is run once.
# Use: python3 -I measure_reference_once.py
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
ANALYSIS = os.path.join(PROC, 'recipes', 'wood', 'analysis')

palette = json.load(open(os.path.join(ANALYSIS, 'palette16.json')))
paint_model = json.load(open(os.path.join(ANALYSIS, 'paint_model.json')))
measurements = json.load(open(os.path.join(ANALYSIS, 'wood_measurements.json')))
derivation = json.load(open(os.path.join(ANALYSIS, 'derivation_ceiling.json')))

colour = np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'colour.png')).convert('RGB')).astype(np.float64)
red, green, blue = colour[..., 0], colour[..., 1], colour[..., 2]
grey = 0.299 * red + 0.587 * green + 0.114 * blue
warmth = red - blue                                   # how orange a dot is
result = {
    '_what': 'whole-picture numbers of the wood reference, measured once as a guide (no positions of single things)',
    'palette16_rgb_dark_to_light': sorted(palette['palette_rgb'], key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]),
    'colour_family_share': measurements['family_share'],
    'strip_length_dots_median': paint_model['zone']['strip_length'][0],
    'strip_row_height_dots_median': paint_model['zone']['row_height'][0],
    'height_rule': {'straight_line_grey_low': derivation['straight_line']['grey_low'], 'straight_line_grey_high': derivation['straight_line']['grey_high'],
                    'normal_strength': derivation['normal_from_uploaded_height']['strength']},
    'grey_percentiles_5_25_50_75_95': [round(float(np.percentile(grey, p)), 1) for p in (5, 25, 50, 75, 95)],
    'share_grey_below_35_very_dark': round(float((grey < 35).mean()), 4),
    'share_grey_above_128': round(float((grey > 128).mean()), 4),
    'share_grey_blue_dots (red - blue < 12, grey 40..110)': round(float(((warmth < 12) & (grey > 40) & (grey < 110)).mean()), 4),
    'share_rust_orange_dots (red - blue > 55)': round(float((warmth > 55).mean()), 4),
    'mean_rgb': [round(float(c.mean()), 1) for c in (red, green, blue)],
    'from_the_surveyor_plan_dots_at_1254': {'board_heights': [281, 239, 270, 178, 286], 'gap_width': 6.8, 'crack_very_dark_share': 0.064,
                                            'crack_median_length': 47, 'crack_width': 2.9, 'knots': '4, half-size 30 to 64',
                                            'rust_splatter': '513 blobs of radius about 3 in 70 clouds about 42 x 35'},
}
with open(os.path.join(HERE, 'reference_measures.json'), 'w') as handle:
    json.dump(result, handle, indent=1)
print(json.dumps(result, indent=1))
