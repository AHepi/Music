"""What this file does (plain words): measures, element by element, whether what the weathering kit put on the lockout plate is still there in the painting.
Pictures (all at the plate size 1536 x 2730): K = the kit's final wet lockout plate; B = the same plate drawn WITHOUT the kit (the integrator's base, earlier layers only);
P = the painting, lined up. The kit's own contribution is K minus B, so every number asks "is K minus B still in P?".
  1. WHERE: share of each surface's dots that the kit changed by more than 10 levels of 255 (walls, road, pavement, gutter, kerb, drum, rest of the props, colliery).
  2. PLANTS (weeds and moss): green patches in K (not in B), how many have a green patch in P at the same place, how big and how green in P compared with K, and green patches in P
     that have no plant in K ("invented").
  3. FOLLOWS THE KIT (grime, streaks, stains, cracks, rust): in each surface, the painting's fine brightness pattern (blur 3 minus blur 20 dots; and a coarser one, blur 6 minus 30)
     is first explained by the no-kit plate's pattern (a straight-line fit), and what is left over is compared with what the kit added. correlation 1 = the painting carries
     the kit's marks exactly, 0 = not at all; slope 1 = same strength, 0 = none. A control moves the kit's marks 60 dots sideways (it should give about 0).
  4. DRUM: brightness of the sooty top fifth against the middle, and how rust-red the drum is, in B, K and P.
Writes numbers/kit_elements.json. Run: python3 -I tools/measure_kit_elements.py
"""
import numpy as np, cv2, os, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B_ = 'proc-work/street_wet/'
AL = B_ + 'painter_test/alignment/'
W, H = 1536, 2730
def load(p): return cv2.resize(cv2.imread(p), (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
K = load(B_ + 'grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png')
Bp = load(B_ + 'grime_and_growth/integrated/plates/lockout/final_lockout_B_wet_base.png')
P = load(os.path.join(HERE, 'pictures/kit_painting_lined_up.png'))
P2 = load(B_ + 'painter_round_2/paint/front_painting_lined_up.png')   # painter round 2's painting of the no-kit plate (same painter and brief, minus the one new sentence)
def lum(im): return (0.2126 * im[:, :, 2] + 0.7152 * im[:, :, 1] + 0.0722 * im[:, :, 0]) / 255
LK, LB, LP, LP2 = lum(K), lum(Bp), lum(P), lum(P2)
G = lambda x, s: cv2.GaussianBlur(x, (0, 0), s)

def masks_from(folder):
    f = json.load(open(folder + '/facts.json'))
    ids = cv2.cvtColor(cv2.imread(folder + '/ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
    ms = {g: cv2.resize((np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0 for g, i in f['groups'].items()}
    return ms, ids
S, ids_s = masks_from(AL + 'facts_surfaces')
Pm, ids_p = masks_from(AL + 'facts')
sky = cv2.resize((ids_p.sum(axis=2) < 24).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
sky = cv2.dilate(sky.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
er = lambda m, n=7: cv2.erode(m.astype(np.uint8), np.ones((n, n), np.uint8)) > 0
other_props = S['props near'] & ~Pm['drum']
zones = {'walls': S['walls'], 'road': S['road'], 'pavement': S['pavement'], 'gutter': S['gutter'], 'kerb': S['kerb'], 'drum': Pm['drum'], 'other near props': other_props, 'colliery': S['colliery']}
zones = {k: er(v & ~sky) for k, v in zones.items()}
out = {'note': 'all at 1536 x 2730; K = kit plate, B = same plate without the kit, P = painting lined up; levels are 0-255; brightness 0-1'}

# 1. where
d = np.abs(K - Bp).max(axis=2)
d = G(d, 1.0)
out['where_the_kit_changed_the_plate'] = {k: {'zone_dots': int(m.sum()), 'share_changed_over_10_levels': round(float((d[m] > 10).mean()), 4), 'share_over_24_levels': round(float((d[m] > 24).mean()), 4)} for k, m in zones.items()}
nonsky = ~sky
out['where_the_kit_changed_the_plate']['whole picture without sky'] = {'zone_dots': int(nonsky.sum()), 'share_changed_over_10_levels': round(float((d[nonsky] > 10).mean()), 4), 'share_over_24_levels': round(float((d[nonsky] > 24).mean()), 4)}

# 2. plants
def green(im): return im[:, :, 1] - np.maximum(im[:, :, 0], im[:, :, 2])
gk, gb, gp = green(K), green(Bp), green(P)
def patches(mask, min_area):
    n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8)))
    r = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a >= min_area: r.append((int(x), int(y), int(w), int(h), int(a), float(cen[i][0]), float(cen[i][1]), i))
    return r, lab
newgreen = (gk > 8) & (gb < 4) & ~sky
pk, labk = patches(newgreen, 12)
pp, labp = patches((gp > 8) & ~sky, 12)
plant_rows = []
for (x, y, w, h, a, cx, cy, i) in pk:
    box = (slice(max(0, y - 8), y + h + 8), slice(max(0, x - 8), x + w + 8))
    pg = gp[box]; kg = gk[box]
    has = bool((pg > 8).any())
    plant_rows.append(dict(x=x, y=y, w=w, h=h, plate_green_dots=int(((gk[box] > 8) & (gb[box] < 4)).sum()), painting_green_dots_in_box=int((pg > 8).sum()), plate_peak_greenness=int(kg.max()), painting_peak_greenness=int(pg.max()), painting_has_green=has))
big = [r for r in plant_rows if r['plate_green_dots'] >= 40]
out['plants'] = {'note': 'a plant patch = 12 or more dots that are green (green minus the larger of red and blue over 8) in the kit plate and not in the no-kit plate; "big" = 40 or more dots. painting_has_green = the painting has 8+ greenness anywhere in the patch box widened by 8 dots.',
                 'plate_patches_12_dots_or_more': len(plant_rows), 'of_which_the_painting_has_green_there': sum(r['painting_has_green'] for r in plant_rows),
                 'big_patches_40_dots_or_more': len(big), 'big_with_green_in_painting': sum(r['painting_has_green'] for r in big),
                 'total_plate_green_dots': int(sum(r['plate_green_dots'] for r in plant_rows)), 'total_painting_green_dots_in_those_boxes': int(sum(r['painting_green_dots_in_box'] for r in plant_rows)),
                 'median_peak_greenness_plate': float(np.median([r['plate_peak_greenness'] for r in plant_rows])), 'median_peak_greenness_painting': float(np.median([r['painting_peak_greenness'] for r in plant_rows])),
                 'rows': plant_rows}
near_plant = cv2.dilate(((gk > 4) & ~sky).astype(np.uint8), np.ones((51, 51), np.uint8)) > 0
inv = [(x, y, w, h, a) for (x, y, w, h, a, cx, cy, i) in pp if not near_plant[int(cy), int(cx)]]
out['plants']['painting_green_patches_12_dots_or_more'] = len(pp)
out['plants']['painting_green_patches_with_no_plate_plant_within_25_dots_(invented)'] = len(inv)
out['plants']['invented_boxes_x_y_w_h_area'] = [list(map(int, t)) for t in inv[:20]]

# 3. follows the kit
def follow(zone, s1, s2, label):
    hpb = G(LB, s1) - G(LB, s2); hpp = G(LP, s1) - G(LP, s2)
    delta = (G(LK, s1) - G(LK, s2)) - hpb
    z = zone
    x, y = hpb[z], hpp[z]
    a = float(np.cov(x, y)[0, 1] / max(x.var(), 1e-9))
    r = y - a * x
    dd = delta[z]
    c = float(np.corrcoef(r, dd)[0, 1]); slope = float(np.cov(r, dd)[0, 1] / max(dd.var(), 1e-9))
    ctrl = []
    for sh in ((60, 0), (0, 60), (-60, 0), (0, -60)):
        dsh = np.roll(delta, sh, axis=(1, 0))[z]
        ctrl.append(float(np.corrcoef(r, dsh)[0, 1]))
    strong = z & (np.abs(delta) > 0.02)
    xs, ys = hpb[strong], hpp[strong]
    return {'zone_dots': int(z.sum()), 'kit_change_std': round(float(dd.std()), 4), 'correlation_of_painting_leftover_with_kit_marks': round(c, 3), 'slope_(1_same_strength)': round(slope, 3),
            'control_correlations_(kit_marks_moved_60_dots)': [round(v, 3) for v in ctrl], 'dots_where_the_kit_changed_local_contrast_by_over_0.02': int(strong.sum())}
out['follows_the_kit'] = {}
for k, z in list(zones.items()) + [('whole picture without sky', er(nonsky))]:
    out['follows_the_kit'][k] = {'fine_(blur 3 minus 20)': follow(z, 3, 20, 'fine'), 'coarse_(blur 6 minus 30)': follow(z, 6, 30, 'coarse')}

# 3b. the clean test: painting of the kit plate minus round 2's painting of the no-kit plate (the painter's own habits, such as strong outlines, cancel; its random strokes do not)
def follow2(zone, s1, s2):
    delta = (G(LK, s1) - G(LK, s2)) - (G(LB, s1) - G(LB, s2))
    dp = (G(LP, s1) - G(LP, s2)) - (G(LP2, s1) - G(LP2, s2))
    dd, pp = delta[zone], dp[zone]
    c = float(np.corrcoef(pp, dd)[0, 1]); slope = float(np.cov(pp, dd)[0, 1] / max(dd.var(), 1e-9))
    ctrl = [float(np.corrcoef(pp, np.roll(delta, sh, axis=(1, 0))[zone])[0, 1]) for sh in ((60, 0), (0, 60), (-60, 0), (0, -60))]
    return {'zone_dots': int(zone.sum()), 'kit_change_std': round(float(dd.std()), 4), 'painting_vs_painting_difference_std': round(float(pp.std()), 4), 'correlation': round(c, 3), 'slope_(1_same_strength)': round(slope, 3), 'control_correlations_(kit_marks_moved_60_dots)': [round(v, 3) for v in ctrl]}
out['follows_the_kit_clean_test_(against_round_2_painting_of_the_no_kit_plate)'] = {}
for k, z in list(zones.items()) + [('whole picture without sky', er(nonsky))]:
    out['follows_the_kit_clean_test_(against_round_2_painting_of_the_no_kit_plate)'][k] = {'fine_(blur 3 minus 20)': follow2(z, 3, 20), 'coarse_(blur 6 minus 30)': follow2(z, 6, 30)}

# 4. drum
dm = Pm['drum']
ys, xs = np.nonzero(dm)
y0, y1 = ys.min(), ys.max()
def band(l, f0, f1):
    m = dm & (np.arange(H)[:, None] >= y0 + f0 * (y1 - y0)) & (np.arange(H)[:, None] < y0 + f1 * (y1 - y0)) & er(dm, 15)
    return float(l[m].mean())
def redness(im):
    m = er(dm, 15)
    return float(((im[:, :, 2] - im[:, :, 0]) / 255)[m].mean())
drum = {}
for nm, l, im in (('no_kit_plate', LB, Bp), ('kit_plate', LK, K), ('painting_of_kit_plate', LP, P), ('round_2_painting_of_no_kit_plate', LP2, P2)):
    top, mid = band(l, 0.0, 0.2), band(l, 0.4, 0.6)
    drum[nm] = {'top_fifth_brightness': round(top, 3), 'middle_brightness': round(mid, 3), 'top_over_middle': round(top / mid, 3), 'red_minus_blue_(0-1)': round(redness(im), 3)}
out['drum_soot_and_rust'] = {'note': 'drum = Blender mask of the brazier drum; bands inside it from the rim down; red_minus_blue larger = more rust-red', **drum}
json.dump(out, open(os.path.join(HERE, 'numbers/kit_elements.json'), 'w'), indent=1)
w = out['where_the_kit_changed_the_plate']
for k, v in w.items(): print(f'{k:28s} {v["zone_dots"]:8d} dots, changed >10: {100*v["share_changed_over_10_levels"]:5.1f} %  >24: {100*v["share_over_24_levels"]:5.1f} %')
p = out['plants']
print({k: v for k, v in p.items() if k not in ('rows', 'invented_boxes_x_y_w_h_area')})
for k, v in out['follows_the_kit'].items():
    print(f'{k:28s} fine corr {v["fine_(blur 3 minus 20)"]["correlation_of_painting_leftover_with_kit_marks"]:6.3f} slope {v["fine_(blur 3 minus 20)"]["slope_(1_same_strength)"]:6.3f} ctrl {v["fine_(blur 3 minus 20)"]["control_correlations_(kit_marks_moved_60_dots)"]} | coarse corr {v["coarse_(blur 6 minus 30)"]["correlation_of_painting_leftover_with_kit_marks"]:6.3f} slope {v["coarse_(blur 6 minus 30)"]["slope_(1_same_strength)"]:6.3f} ctrl {v["coarse_(blur 6 minus 30)"]["control_correlations_(kit_marks_moved_60_dots)"]}')
for k, v in out['follows_the_kit_clean_test_(against_round_2_painting_of_the_no_kit_plate)'].items():
    f, c = v['fine_(blur 3 minus 20)'], v['coarse_(blur 6 minus 30)']
    print(f'CLEAN {k:28s} fine corr {f["correlation"]:6.3f} slope {f["slope_(1_same_strength)"]:6.3f} ctrl {f["control_correlations_(kit_marks_moved_60_dots)"]} | coarse corr {c["correlation"]:6.3f} slope {c["slope_(1_same_strength)"]:6.3f} ctrl {c["control_correlations_(kit_marks_moved_60_dots)"]}  (kit std {f["kit_change_std"]}, paint-paint std {f["painting_vs_painting_difference_std"]})')
print(drum)
