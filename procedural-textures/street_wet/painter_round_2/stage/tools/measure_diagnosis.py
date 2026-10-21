"""What this file does (plain words): measures the plate-view pictures drawn by tools/render_diagnosis.sh (stills/diagnosis/*, each with some steps of the stage's finishing look switched off or changed) against the painting, the same way as the
first test and tools/measure_stage_round2.py do: how bright the road arrives over its painted brightness (whole road, far/middle/near thirds, the road's dark parts, share of dots crushed to black, fine detail kept), and for the
dry pictures how much they differ from the film's own dry picture (stills/before/dry_projector). Writes numbers/diagnosis_real_stage.json. Run: python3 -I tools/measure_diagnosis.py
"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from stage_common import central, central_mask, masks, er, load01, TEST1, FILM, W, H, P
def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def lum01(rgb): return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)
M = masks(TEST1 + 'alignment/facts_surfaces/')
road = er(central_mask(M['road']))
rows = np.where(road.any(axis=1))[0]; cuts = [rows[0], rows[int(len(rows) / 3)], rows[int(2 * len(rows) / 3)], rows[-1] + 1]
thirds = []
for i in range(3):
    m = np.zeros_like(road); m[cuts[i]:cuts[i + 1]] = road[cuts[i]:cuts[i + 1]]; thirds.append(m)
hp = lambda L: L - cv2.GaussianBlur(L, (0, 0), 2.0)
wet = lum01(central(load01(P('../paint/front_painting_final.png')))); dry = lum01(central(load01(FILM + 'lockout-painted.jpg')))
dark_w = road & (wet > 0.08) & (wet < 0.22)
dry_ref = lum(cv2.imread(P('stills/before/dry_projector/still-6.00.jpg')))
res = {}
folders = sys.argv[1:] or ['diagnosis']
for folder in folders:
    base = P('stills', folder)
    for name in sorted(os.listdir(base)):
        f = os.path.join(base, name, 'still-6.00.jpg')
        if not os.path.exists(f) or name.startswith('test_'): continue
        L = lum(cv2.imread(f)); is_dry = name.startswith('dry_')
        pt = dry if is_dry else wet
        r = {'road_arrives': float(L[road].mean() / pt[road].mean()), 'far_third': float(L[thirds[0]].mean() / pt[thirds[0]].mean()), 'middle_third': float(L[thirds[1]].mean() / pt[thirds[1]].mean()),
             'near_third': float(L[thirds[2]].mean() / pt[thirds[2]].mean())}
        if not is_dry:
            r['dark_parts_arrive_(painted_0.08_to_0.22)'] = float(L[dark_w].mean() / wet[dark_w].mean())
            r['crushed_to_black_share_(painted_over_0.08_arriving_under_0.03)'] = float(((wet > 0.08) & (L < 0.03))[road].mean())
            r['fine_detail_kept'] = float(np.std(hp(L)[road]) / np.std(hp(wet)[road]))
        else:
            d = np.abs(L - dry_ref); r['change_from_the_film_as_it_is_whole_picture_mean_abs'] = float(d.mean()); r['change_from_the_film_as_it_is_road_mean_abs'] = float(d[road].mean())
        res[f'{folder}/{name}'] = r
        print(f"{folder + '/' + name:30s} road {r['road_arrives']:.3f} (far {r['far_third']:.2f} mid {r['middle_third']:.2f} near {r['near_third']:.2f})" + (f"  dark parts {r['dark_parts_arrive_(painted_0.08_to_0.22)']:.2f}  crushed {r['crushed_to_black_share_(painted_over_0.08_arriving_under_0.03)']:.3f}  detail {r['fine_detail_kept']:.2f}" if not is_dry else f"  change from film: picture {r['change_from_the_film_as_it_is_whole_picture_mean_abs']:.4f}, road {r['change_from_the_film_as_it_is_road_mean_abs']:.4f}"))
json.dump(res, open(P('numbers', 'diagnosis_real_stage.json'), 'w'), indent=1)
