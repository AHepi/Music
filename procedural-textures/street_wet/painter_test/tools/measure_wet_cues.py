"""What this file does (plain words): measures, with numbers, which wet cues of the wet plate survived in the new wet painting, next to the existing
dry lockout painting. Everything is measured at 1080 x 1920 on masks that Blender made for the lockout camera (the road, pavement, gutter, kerb, walls,
props, sky), so each number is about the same place in every picture. "Brightness" below means the picture's own pixel brightness from 0 (black) to 1
(white), not light in the real world. Writes numbers/measurements.json (and the same text is printed).
Pictures used: the wet plate (EEVEE, 1536 x 2730), the new wet painting (lined up), the existing dry lockout painting, and the earlier helper's DRY
plate of the same shot (only 540 x 960, so it is used only for averages).
Run: python3 -I tools/measure_wet_cues.py
"""
import cv2, numpy as np, json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
W, H = 1080, 1920
SW = 'proc-work/street_wet/work/r35/'

def load(path, interp=cv2.INTER_AREA):
    return cv2.resize(cv2.imread(path), (W, H), interpolation=interp)
imgs = {
    'plate_wet': load(SW + 'main_wet_plate.png'),
    'paint_wet': load(P('pictures/wet_painting_lined_up.png')),
    'paint_dry': load('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg'),
    'plate_dry_small': load(SW + 'main_today.png', cv2.INTER_CUBIC),
}
def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
L = {k: lum(v) for k, v in imgs.items()}

def masks_from(folder):
    f = json.load(open(P(folder, 'facts.json')))
    ids = cv2.cvtColor(cv2.imread(P(folder, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
    return {g: (np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24) for g, i in f['groups'].items()}, ids
S, ids_s = masks_from('alignment/facts_surfaces')
Pm, ids_p = masks_from('alignment/facts')
sky = ids_p.sum(axis=2) < 24
def erode(m, n=4): return cv2.erode(m.astype(np.uint8), np.ones((n, n), np.uint8)) > 0
road = erode(S['road'])
out = {'note': 'brightness is the picture pixel brightness 0..1 (Rec.709 weights); masks from Blender for the lockout camera; 1080 x 1920'}

# ---------------- A. road brightness by band
ys, xs = np.nonzero(road)
y0, y1 = ys.min(), ys.max()
edges = [y0, y0 + (y1 - y0) // 3, y0 + 2 * (y1 - y0) // 3, y1 + 1]
bands = {'far third of road': (edges[0], edges[1]), 'middle third': (edges[1], edges[2]), 'near third (brazier)': (edges[2], edges[3])}
out['road_rows'] = [int(y0), int(y1)]
def band_mask(a, b):
    m = np.zeros_like(road); m[a:b] = road[a:b]; return m
road_stats = {}
for name, (a, b) in list(bands.items()) + [('whole road', (y0, y1 + 1))]:
    m = band_mask(a, b)
    row = {}
    for k in imgs:
        v = L[k][m]
        row[k] = {'mean': float(v.mean()), 'p95': float(np.percentile(v, 95)), 'p99': float(np.percentile(v, 99)), 'over_0.9': float((v > 0.9).mean()), 'blue_minus_red': float((imgs[k][:, :, 0][m].astype(float) - imgs[k][:, :, 2][m]).mean() / 255)}
    road_stats[name] = row
out['road_brightness'] = road_stats
out['road_ratios'] = {n: {'plate_wet_over_plate_dry': road_stats[n]['plate_wet']['mean'] / road_stats[n]['plate_dry_small']['mean'],
                          'paint_wet_over_paint_dry': road_stats[n]['paint_wet']['mean'] / road_stats[n]['paint_dry']['mean']} for n in road_stats}

# ---------------- B. glints: pixels clearly brighter than their surroundings (sheen on setts / flags)
def glint_share(k, mask):
    g8 = (np.clip(L[k], 0, 1) * 255).astype(np.uint8)
    med = cv2.medianBlur(g8, 31).astype(np.float32) / 255
    return float(((L[k] - med) > 0.10)[mask].mean())
pav = erode(S['pavement'] | S['kerb'], 3)
out['glint_share'] = {'road': {k: glint_share(k, road) for k in ('plate_wet', 'paint_wet', 'paint_dry')},
                      'pavement and kerb': {k: glint_share(k, pav) for k in ('plate_wet', 'paint_wet', 'paint_dry')}}

# ---------------- C. overlap of bright reflection areas, and likeness of the light pattern, on the road
def smooth(k, s): return cv2.GaussianBlur(L[k], (0, 0), s)
overlap = {}
for name, (a, b) in list(bands.items()) + [('whole road', (y0, y1 + 1))]:
    m = band_mask(a, b)
    sm = {k: smooth(k, 8) for k in ('plate_wet', 'paint_wet', 'paint_dry')}
    top = {k: (sm[k] >= np.percentile(sm[k][m], 90)) & m for k in sm}
    iou = lambda A, B: float((A & B).sum() / max(1, (A | B).sum()))
    # likeness of the light pattern: correlation of smoothed brightness, raw and after removing each row's own average
    s12 = {k: smooth(k, 12) for k in sm}
    def corr(a_, b_, detrend):
        A, B = s12[a_][m].copy(), s12[b_][m].copy()
        if detrend:
            yy = np.nonzero(m)[0]
            for arr in (A, B):
                for r in np.unique(yy):
                    sel = yy == r
                    arr[sel] -= arr[sel].mean()
        return float(np.corrcoef(A, B)[0, 1])
    overlap[name] = {'top10pct_overlap_plate_vs_wet_painting': iou(top['plate_wet'], top['paint_wet']),
                     'top10pct_overlap_plate_vs_dry_painting': iou(top['plate_wet'], top['paint_dry']),
                     'chance_level_overlap_for_10pct_areas': 0.0526,
                     'light_pattern_correlation_plate_vs_wet_painting': corr('plate_wet', 'paint_wet', False),
                     'light_pattern_correlation_plate_vs_dry_painting': corr('plate_wet', 'paint_dry', False),
                     'light_pattern_correlation_after_removing_row_average_plate_vs_wet_painting': corr('plate_wet', 'paint_wet', True),
                     'light_pattern_correlation_after_removing_row_average_plate_vs_dry_painting': corr('plate_wet', 'paint_dry', True)}
out['bright_reflection_overlap'] = overlap

# ---------------- D. lamp reflection streaks on the far road: where are the column peaks
a, b = bands['far third of road']
fm = band_mask(a, b)
streaks = {}
for k in ('plate_wet', 'paint_wet', 'paint_dry'):
    num = np.where(fm, L[k], 0).sum(axis=0); cnt = fm.sum(axis=0)
    prof = np.where(cnt > 20, num / np.maximum(cnt, 1), np.nan)
    pf = np.nan_to_num(prof, nan=np.nanmean(prof))
    trend = cv2.GaussianBlur(pf.reshape(1, -1).astype(np.float32), (0, 0), 25).ravel()
    d = pf - trend; d[np.isnan(prof)] = 0
    peaks = []
    dd = d.copy()
    for _ in range(3):
        x = int(np.argmax(dd)); peaks.append((x, round(float(dd[x]), 3))); dd[max(0, x - 30):x + 31] = -9
    streaks[k] = peaks
out['far_road_column_peaks_(x_in_1080_wide, brightness_above_neighbours)'] = streaks

# ---------------- E. gutter: brightness profile along the gutter, high-pass part, plate vs paintings
gut = erode(S['gutter'], 3)
gy = np.nonzero(gut)[0]
bins = np.arange(gy.min(), gy.max() + 1, 12)
def gutter_profile(k):
    v = []
    for i in range(len(bins) - 1):
        m = gut[bins[i]:bins[i + 1]]
        vals = L[k][bins[i]:bins[i + 1]][m]
        v.append(vals.mean() if vals.size > 15 else np.nan)
    return np.array(v)
gp = {k: gutter_profile(k) for k in ('plate_wet', 'paint_wet', 'paint_dry', 'plate_dry_small')}
ok = ~np.isnan(gp['plate_wet'])
for k in gp: ok &= ~np.isnan(gp[k])
def hp(v):
    v = v[ok]; return v - cv2.GaussianBlur(v.reshape(1, -1).astype(np.float32), (0, 0), 4).ravel()
out['gutter'] = {'mean_brightness': {k: float(np.nanmean(gp[k][ok])) for k in gp},
                 'profile_correlation_with_wet_plate_after_removing_slow_trend': {k: float(np.corrcoef(hp(gp['plate_wet']), hp(gp[k]))[0, 1]) for k in ('paint_wet', 'paint_dry')},
                 'profile_correlation_with_wet_plate_raw': {k: float(np.corrcoef(gp['plate_wet'][ok], gp[k][ok])[0, 1]) for k in ('paint_wet', 'paint_dry')},
                 'bins_used': int(ok.sum())}

# ---------------- F. wall foot against mid-wall
walls = erode(S['walls'], 3)
ground = S['pavement'] | S['kerb'] | S['road'] | S['gutter']
foot, mid = [], []
for x in range(0, W, 2):
    col = walls[:, x]
    d = np.diff(np.concatenate([[0], col.astype(np.int8), [0]]))
    for s_, e_ in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
        ye = e_ - 1
        if ye > 0.45 * H and ye + 6 < H and ground[ye + 1:ye + 7, x].any():
            foot.append((x, ye))
foot = np.array(foot)
def wall_foot(k):
    fvals, mvals = [], []
    for x, ye in foot:
        c = walls[:, x]
        a_ = L[k][max(0, ye - 30):ye + 1, x][c[max(0, ye - 30):ye + 1]]
        b_ = L[k][max(0, ye - 200):max(0, ye - 90), x][c[max(0, ye - 200):max(0, ye - 90)]]
        if a_.size > 10 and b_.size > 20: fvals.append(a_.mean()); mvals.append(b_.mean())
    return float(np.mean(fvals)), float(np.mean(mvals)), len(fvals)
out['wall_foot'] = {'columns_measured': int(len(foot)), **{k: dict(zip(('foot_30px_mean', 'mid_wall_90_to_200px_above_mean', 'columns_used'), wall_foot(k))) for k in imgs}}
for k in imgs:
    d = out['wall_foot'][k]; d['foot_over_mid_wall'] = d['foot_30px_mean'] / d['mid_wall_90_to_200px_above_mean']

# ---------------- G. glare pool, and "nothing brighter than the notice"
low = np.zeros((H, W), bool); low[int(H * 2 / 3):] = True
notice = Pm['notice']
glare = {}
for k in ('plate_wet', 'paint_wet', 'paint_dry'):
    glare[k] = {'share_of_lower_third_over_0.95': float((L[k][low] > 0.95).mean()),
                'share_of_lower_third_over_0.85': float((L[k][low] > 0.85).mean()),
                'notice_paper_brightness_top20pct': float(np.percentile(L[k][notice], 80)),
                'brightest_1_in_1000_of_road': float(np.percentile(L[k][road], 99.9)),
                'brightest_road_over_notice': float(np.percentile(L[k][road], 99.9) / np.percentile(L[k][notice], 80))}
out['glare_pool'] = glare

# ---------------- H. ink outlines on the near props (a rough proxy: a dark thin line sits on the prop's outline)
def ink_share(k):
    g = L[k]
    mn = cv2.erode(g, np.ones((7, 7), np.uint8))
    av = cv2.blur(g, (31, 31))
    res = {}
    tot_n = tot_hit = 0
    for grp in ('drum', 'sacks', 'handcart', 'dustbins', 'coal pile', 'spade', 'pail', 'ladder'):
        m = Pm[grp].astype(np.uint8)
        e = (m - cv2.erode(m, np.ones((3, 3), np.uint8))) > 0
        hit = (mn < 0.6 * av) & (mn < 0.22)
        n = int(e.sum()); h = int((hit & e).sum()); tot_n += n; tot_hit += h
        res[grp] = h / max(1, n)
    res['all of them'] = tot_hit / max(1, tot_n)
    return res
out['dark_outline_share_on_prop_edges'] = {k: ink_share(k) for k in ('plate_wet', 'paint_wet', 'paint_dry')}

# ---------------- I. sky: clouds added?
sk = sky & (np.arange(H)[:, None] < 0.45 * H)
sky_res = {}
base = cv2.GaussianBlur(L['plate_wet'], (0, 0), 40)
for k in ('plate_wet', 'paint_wet', 'paint_dry'):
    sky_res[k] = {'mean_brightness': float(L[k][sk].mean()), 'share_clearly_brighter_than_plate_sky_by_0.12': float(((L[k] - base) > 0.12)[sk].mean()),
                  'share_over_0.5': float((L[k][sk] > 0.5).mean())}
out['sky'] = sky_res

# ---------------- J. how well each painting follows the plate's overall light and dark, picture-wide (blurred)
dif = {}
for k in ('paint_wet', 'paint_dry'):
    a_ = cv2.GaussianBlur(L['plate_wet'], (0, 0), 20); b_ = cv2.GaussianBlur(L[k], (0, 0), 20)
    dif[k] = {'mean_absolute_difference_of_blurred_brightness': float(np.abs(a_ - b_).mean()), 'correlation_of_blurred_brightness': float(np.corrcoef(a_.ravel(), b_.ravel())[0, 1]),
              'whole_picture_mean_brightness': float(L[k].mean())}
dif['plate_wet'] = {'whole_picture_mean_brightness': float(L['plate_wet'].mean())}
out['whole_picture'] = dif

json.dump(out, open(P('numbers/measurements.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
