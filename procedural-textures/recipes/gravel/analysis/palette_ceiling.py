# What this does (plain words): measures how few colours the gravel picture needs. It snaps every dot of the reference colour picture to the nearest
# of k palette colours (k-means in a perceptual colour space) and reports the average colour difference (Delta E; about 2.3 is "just visible")
# and the picture-structure score (SSIM) of the snapped picture against the original. Also how many separate same-colour areas ("patches") the
# snapped picture has at different smallest sizes, and how big a list of their outlines would be. Analysis only: reads the reference.
import json, os, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'lib'))
import trace_tools as tt
import pixel_compare as pc

bgr = tt.load_reference_colour()
rows = []
for count in (8, 12, 16, 24, 32, 48):
    centres = tt.make_palette(bgr, count)
    labels = tt.assign_labels(bgr, centres)
    palette_bgr = tt.palette_to_bgr(centres)
    snapped = palette_bgr[labels]
    ref = bgr.astype(np.float64)
    lab_ref = pc.tc.srgb_to_lab(ref[..., ::-1] / 255.0)
    lab_c = pc.tc.srgb_to_lab(snapped.astype(np.float64)[..., ::-1] / 255.0)
    de = float(np.sqrt(((lab_ref - lab_c) ** 2).sum(-1)).mean())
    grey = lambda x: cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    ssim = pc.ssim(grey(ref), grey(snapped.astype(np.float64)))
    n_patch = sum(cv2.connectedComponents((labels == k).astype(np.uint8), connectivity=4)[0] - 1 for k in range(count))
    rows.append(dict(colours=count, delta_e=round(de, 2), ssim=round(ssim, 3), patches_raw=int(n_patch)))
    print(rows[-1], flush=True)
json.dump(rows, open(os.path.join(HERE, '..', 'scores', 'palette_ceiling.json'), 'w'), indent=1)
