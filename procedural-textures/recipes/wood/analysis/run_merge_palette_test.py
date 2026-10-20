# What this does (plain words): tests how many palette colours the traced wood patches need (48, 96, 192) at a fixed patch count (3000) and outline looseness (1.0),
# using the saved merge order from run_merge_ladder.py. Prints size and every dot-for-dot accuracy number. Analysis only (reads the reference).
import json, os, pickle, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import merge_trace as mt, score_tools as st, trace_tools as tt
bgr = cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
out = os.path.join(HERE, 'merge_ladder')
comp, lab = mt.initial_regions(bgr, colour_count=32)
tree = pickle.load(open(os.path.join(out, 'tree.pkl'), 'rb'))
for target, palette_size, epsilon in [(3000, 48, 1.0), (3000, 96, 1.0), (3000, 192, 1.0), (3000, 192, 0.8), (3000, 192, 1.4)]:
    t0 = time.time()
    region_labels, count = mt.labels_at(comp, tree, target)
    means, area = mt.region_colours(region_labels, lab, count)
    centres, index = mt.squeeze_palette(means, area, palette_size)
    regions = mt.trace_labelled_regions(region_labels, count, index, epsilon)
    palette_bgr = tt.palette_to_bgr(centres)
    picture = tt.draw_regions(regions, palette_bgr)
    folder = os.path.join(out, 'tmp2')
    st.write_folder(picture, folder)
    report = st.score_folder(folder, texture=False)
    print(json.dumps(dict(target=target, palette=palette_size, eps=epsilon, patches=len(regions), vertices=sum(len(r['p']) for r in regions),
          kb=round(tt.json_size(regions, palette_bgr.tolist()) / 1024, 1), ssim=report['colour_ssim'], dE=report['colour_mean_delta_e'], edge=report['edge_skill_2px'],
          hMAE=report['height_mae_best_fit_levels'], normal=report['normal_mean_angle_degrees'], tier=report['tier_reached'], s=round(time.time() - t0, 1))), flush=True)
