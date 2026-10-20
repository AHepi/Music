import sys; sys.path.insert(0, ".")
import sys, json
from region_tools import *
bgr = load_reference()
rows = []
for pre in ('none', 'bilateral'):
    for K in (16, 32):
        labels, centres = kmeans_labels(bgr, K, pre)
        pal = cv2.cvtColor(centres.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)
        for msize in (3, 5):
            L1 = mode_filter(labels, K, msize)
            for amin in (20, 80, 300, 1000):
                L2, _ = remove_small(L1, K, amin)
                ids, rl, ra = regions_of(L2, K)
                out = pal[L2]
                s = score_colour(out, 'tmp')
                rows.append({'pre': pre, 'K': K, 'mode': msize, 'amin': amin, 'regions': int(len(ra) - 1), **s})
                print(rows[-1], flush=True)
json.dump(rows, open('explore_regions.json', 'w'), indent=1)
