# What this does (plain python): finds the "accent" colours that a k-means palette averages away: the mean colour of the brightest 1 percent, the darkest 1 percent
# and the most colourful 1 percent of pixels of each reference. Writes ../data/reference_extreme_colours.json
import json, os, sys, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import a01_measure_references as m
out = {}
for name in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel', 'mud_golden']:
    rgb = m.load_rgb_u8(os.path.join(m.REF, name, 'colour.png')); lab = m.to_lab(rgb)
    L = lab[..., 0]; chroma = np.hypot(lab[..., 1], lab[..., 2])
    def mean_hex(mask):
        c = rgb[mask].reshape(-1, 3).mean(axis=0); return '#%02x%02x%02x' % tuple(int(round(v)) for v in c)
    out[name] = {'brightest_1pct': mean_hex(L >= np.percentile(L, 99)), 'darkest_1pct': mean_hex(L <= np.percentile(L, 1)), 'most_colourful_1pct': mean_hex(chroma >= np.percentile(chroma, 99)),
                 'lightness_p99': float(np.percentile(L, 99)), 'lightness_p1': float(np.percentile(L, 1))}
    print(name, out[name])
json.dump(out, open(os.path.join(m.DATA, 'reference_extreme_colours.json'), 'w'), indent=1)
