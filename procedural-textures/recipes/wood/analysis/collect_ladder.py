# What this does (plain words): collects the scores of every baked ladder class (scores/ladder_<name>.json + the bake time + the description size) into ONE table
# (scores/rate_distortion_table.json and a printed text table), and draws the ladder picture (reference and every class side by side, plus the difference picture of the
# best traced class) into guide_pictures/ladder.png. Plain Python (python3 -I).
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
SUFFIX = os.environ.get('LADDER_SUFFIX', '')            # 'w' = the traced classes made with patches that may join across the tile edge
base = ['S0_layout_only', 'S1_layout_paint_grain', 'M1_trace_20k', 'M2_trace_40k', 'M3_trace_62k', 'L1_trace_150k', 'L2_trace_300k', 'L3_trace_480k']
names = [n + (SUFFIX if n[0] in 'ML' else '') for n in base]
rows = []
for n in names:
    p = os.path.join(WOOD, 'scores', f'ladder_{n}.json')
    if not os.path.exists(p): continue
    s = json.load(open(p))
    b = json.load(open(os.path.join(WOOD, 'outputs', f'ladder_{n}', 'bake.json')))
    rows.append({'class': n.rstrip('w') if n[0] in 'ML' else n, 'file': n, 'bytes': os.path.getsize(os.path.join(WOOD, 'description', n + '.json')), 'tier': s['tier_reached'], 'colour_ssim': s['colour_ssim'], 'colour_mean_delta_e': s['colour_mean_delta_e'],
                 'edge_skill_2px': s['edge_skill_2px'], 'height_mae_best_fit_levels': s['height_mae_best_fit_levels'], 'normal_mean_angle_degrees': s['normal_mean_angle_degrees'],
                 'texture_compare_overall': s['texture_compare_overall'], 'seam_ratio': s['seam_ratio'], 'bake_seconds': b['total_s'], 'colour_render_seconds': b.get('colour_render_s')})
json.dump(rows, open(os.path.join(WOOD, 'scores', 'rate_distortion_table' + ('_wrap_aware' if SUFFIX else '_cut_at_edge') + '.json'), 'w'), indent=1)
print(f'{"class":24s}{"KB":>7s} {"tier":>7s} {"SSIM":>6s} {"dE":>6s} {"edge":>6s} {"hMAE":>6s} {"nrm":>6s} {"kind":>6s} {"seam":>5s} {"sec":>6s}')
for r in rows:
    print(f'{r["class"]:24s}{r["bytes"]/1024:7.1f} {r["tier"]:>7s} {r["colour_ssim"]:6.3f} {r["colour_mean_delta_e"]:6.2f} {r["edge_skill_2px"]:6.3f} {r["height_mae_best_fit_levels"]:6.1f} {r["normal_mean_angle_degrees"]:6.1f} {r["texture_compare_overall"]:6.3f} {r["seam_ratio"]:5.2f} {r["bake_seconds"]:6.1f}')
ref = cv2.imread(os.path.join(WOOD, '..', '..', 'reference', 'wood', 'colour.png'))
tiles = [('reference', ref)]
for r in rows:
    tiles.append((f'{r["class"]} {r["bytes"]/1024:.0f} KB', cv2.imread(os.path.join(WOOD, 'outputs', f'ladder_{r["file"]}', 'colour.png'))))
cells = []
for label, im in tiles:
    c = cv2.resize(im, (400, 400), interpolation=cv2.INTER_AREA)
    cv2.rectangle(c, (0, 0), (400, 26), (245, 245, 245), -1); cv2.putText(c, label, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    cells.append(c)
while len(cells) % 3: cells.append(np.full_like(cells[0], 255))
os.makedirs(os.path.join(WOOD, 'guide_pictures'), exist_ok=True)
cv2.imwrite(os.path.join(WOOD, 'guide_pictures', 'ladder' + ('' if SUFFIX else '_cut_at_edge') + '.png'), np.vstack([np.hstack(cells[i:i + 3]) for i in range(0, len(cells), 3)]))
