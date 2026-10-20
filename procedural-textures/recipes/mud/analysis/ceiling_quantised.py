# What this does (plain words): finds how close a "palette-only" copy of the mud picture can get: snap every dot to the nearest of K palette colours (optionally
# cleaning tiny specks with a median filter), make height and normal from it the way the reference ones were made, and score it dot for dot. This is the
# ceiling for any description that only says "which palette colour is where". Analysis only (reads the reference).
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score_tools as st
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
img = cv2.imread(PROC + '/reference/mud/colour.png')
labels = np.load('labels_k16.npy')
pal = json.load(open('palette_k16.json'))['palette_rgb_sorted_by_share']
pal_bgr = np.array([[c[2], c[1], c[0]] for c in pal], np.uint8)
out = {}
for name, lab in (('k16_raw', labels), ('k16_median3', cv2.medianBlur(labels, 3)), ('k16_median5', cv2.medianBlur(labels, 5))):
    q = pal_bgr[lab]
    folder = f'/tmp/mudscratch/{name}'
    st.write_folder(q, folder)
    r = st.score_folder(folder, texture=True)
    out[name] = {k: r.get(k) for k in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall')}
    print(name, out[name])
json.dump(out, open('ceiling_quantised.json', 'w'), indent=1)
