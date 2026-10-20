# What this does (plain words): builds the S0 description (layout only: boards, gaps, cracks, knots, splatter clouds, pebbles) of the wood reference, writes it to
# ../description/S0_layout_only.json, paints a quick numpy preview into ../outputs/preview_S0 and scores it. Plain Python (python3 -I). Reads analysis results.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cv2
import make_descriptions as md
import preview as pv
import score_tools as st
bgr = cv2.imread(os.path.join(md.PROC, 'reference', 'wood', 'colour.png'))
palette, palette_lab = md.make_s_palette(bgr, 16)
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
cracks = json.load(open(os.path.join(HERE, 'cracks_fitted.json')))
crack_count = int(sys.argv[1]) if len(sys.argv) > 1 else 60
d = md.base_description(palette, 'S0: layout only (boards, gaps, cracks, knots, splatter clouds, pebbles); flat colour per board')
d['layers'] = md.layout_layers(fit, cracks, palette_lab, crack_count=crack_count)
size = md.write(d, os.path.join(HERE, '..', 'description', 'S0_layout_only.json'))
print('S0 bytes', size)
out = os.path.join(HERE, '..', 'outputs', 'preview_S0')
r = pv.run(os.path.join(HERE, '..', 'description', 'S0_layout_only.json'), out, 2, True)
print(json.dumps({k: r.get(k) for k in ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall']}))
