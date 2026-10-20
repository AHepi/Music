# What this does (plain python): measures the typical length (pixels) of the straight horizontal / vertical runs along the outline of flat patches
# ("stair steps"): a smooth edge gives long runs on near-horizontal parts and short on diagonals, a blocky edge gives runs about the block size. Uses
# patch outlines from a palette-label picture (k-means 12 colours, 5x5 majority filter for the references; the generated flat pictures use 8 colours without filter).
# Prints median run length (all runs of 2 px or more) for the references and for pictures given as label=path.
import os, sys, json, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import a01_measure_references as m
def runs_of(contour):
    pts = contour[:, 0, :]
    d = np.diff(np.vstack([pts, pts[:1]]), axis=0)
    runs = []; cur = None; length = 0
    for step in map(tuple, d):
        if step == cur: length += 1
        else:
            if cur is not None and cur[0] * cur[1] == 0 and (cur != (0, 0)): runs.append(length)      # only axis-aligned moves
            cur = step; length = 1
    return runs
def stair(path, k, filt):
    rgb = m.load_rgb_u8(path); lab = m.to_lab(rgb)
    centres = m.kmeans_lab(lab, k); labels, _ = m.nearest_labels(lab, centres)
    if filt: labels = m.mode_filter(labels, k, 5)
    runs = []
    for index in range(k):
        mask = (labels == index).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        for c in contours:
            if len(c) < 60: continue
            runs += runs_of(c)
    runs = np.array(runs)
    return {'median_run_px': float(np.median(runs)), 'mean_run_px': float(runs.mean()), 'share_of_runs_1px': float((runs == 1).mean()), 'runs': int(len(runs))}
out = {}
for n in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']:
    out['reference ' + n] = stair(os.path.join(m.PROC, 'reference', n, 'colour.png'), 12, True)
for item in sys.argv[1:]:
    label, path = item.split('=', 1)
    out[label] = stair(path, 8, False)
for k, v in out.items(): print(f"{k:40s} median run {v['median_run_px']:.1f}  mean {v['mean_run_px']:.1f}  share of 1-px runs {v['share_of_runs_1px']*100:.0f}%")
json.dump(out, open(os.path.join(m.DATA, 'a06_stair_steps.json'), 'w'), indent=1)
