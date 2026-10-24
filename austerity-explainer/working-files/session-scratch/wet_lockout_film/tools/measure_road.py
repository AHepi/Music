"""What this file does (plain words): measures how bright the road (and the walls, and the road's dark parts) ARRIVE on screen compared with the painting, the same way the
wet street's stage step did (its definitions are reused: Blender's surface masks for the plate camera, read only; the painting cut to the film's narrower 40-degree lens).
Pictures to measure are given as LABEL=PICTURE_PATH_AT_1080x1920 pairs together with the painting they show:
  python3 -I measure_road.py PAINTING.jpg LABEL=PICTURE.jpg [LABEL=PICTURE.jpg ...]
Only pictures drawn from the plate's own camera (the still's 'projector' view, or the film's frames before the move starts at 2.0 s) can be measured this way.
Prints and writes numbers/road_NAME.json.
"""
import json, os, sys
import cv2, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/stage/tools')
from stage_common import central, central_mask, masks, er, load01, TEST1
def lum01(rgb): return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)
M = masks(TEST1 + 'alignment/facts_surfaces/')
road, walls = er(central_mask(M['road'])), er(central_mask(M['walls']))
rows = np.where(road.any(axis=1))[0]
cuts = [rows[0], rows[int(len(rows) / 3)], rows[int(2 * len(rows) / 3)], rows[-1] + 1]
thirds = []
for i in range(3):
    m = np.zeros_like(road); m[cuts[i]:cuts[i + 1]] = road[cuts[i]:cuts[i + 1]]; thirds.append(m)
painting = lum01(central(load01(sys.argv[1])))
dark = road & (painting > 0.08) & (painting < 0.22)
out = {'painting': sys.argv[1], 'road_mean_painting': float(painting[road].mean())}
for pair in sys.argv[2:]:
    label, path = pair.split('=', 1)
    img = cv2.imread(path); b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    s = 0.2126 * r + 0.7152 * g + 0.0722 * b
    out[label] = {'road_stage_over_painting': float(s[road].mean() / painting[road].mean()),
                  'road_far_third': float(s[thirds[0]].mean() / painting[thirds[0]].mean()), 'road_middle_third': float(s[thirds[1]].mean() / painting[thirds[1]].mean()), 'road_near_third': float(s[thirds[2]].mean() / painting[thirds[2]].mean()),
                  'road_dark_parts_(painted_0.08_to_0.22)': float(s[dark].mean() / painting[dark].mean()),
                  'road_dots_painted_over_0.08_arriving_under_0.03_(crushed_to_black)': float(((painting > 0.08) & (s < 0.03))[road].mean()),
                  'walls': float(s[walls].mean() / painting[walls].mean()), 'whole_picture_mean': float(s.mean())}
    print(label, json.dumps(out[label], indent=1))
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers'), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers', 'road_' + os.path.basename(sys.argv[1]).replace('.jpg', '') + '.json'), 'w'), indent=1)
