"""What this file does (plain words): measures the stage pictures (stage/stills/*/still-6.00.jpg): (1) in the plate's own view, how closely the stage shows the painting as painted
(painting cut to the stage's narrower lens, compared with the stage picture); (2) in the moved view (1.4 m forward, 0.3 m right), how much of the wet look is left on the road
(brightness, shine, blue tint) for the dry painting, the wet painting with the film's dry "behind" painting, and the wet painting used as its own behind painting;
(3) how big the dry-looking patches are where the film's dry behind painting is shown instead of the wet painting; (4) the share of the moved view that wears the painting, the behind painting
or the 3D set's own surface (from the colour map). The live fire, flames and smoke are drawn on top in every picture alike. Masks (road, walls, ...) come from Blender for the
same cameras (alignment/facts_surfaces and alignment/facts_surfaces_moved). Writes numbers/stage_measurements.json.
Run: python3 -I tools/measure_stage_views.py
"""
import cv2, numpy as np, json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
W, H = 1080, 1920
def still(n): return cv2.imread(P('stage/stills', n, 'still-6.00.jpg'))
def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def masks(folder):
    f = json.load(open(P(folder, 'facts.json')))
    ids = cv2.cvtColor(cv2.imread(P(folder, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
    return {g: (np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24) for g, i in f['groups'].items()}
er = lambda m, n=4: cv2.erode(m.astype(np.uint8), np.ones((n, n), np.uint8)) > 0
out = {}

# ---- (1) plate view: the stage against the painting as painted
M = masks('alignment/facts_surfaces')
k = np.tan(np.radians(20)) / np.tan(np.radians(22))     # the stage's lens (40 deg) sees the middle 90.1 % of the plate's (44 deg)
def central(img):
    h, w = img.shape[:2]; ch, cw = int(round(h * k)), int(round(w * k)); y0, x0 = (h - ch) // 2, (w - cw) // 2
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_AREA)
def central_mask(m):
    h, w = m.shape; ch, cw = int(round(h * k)), int(round(w * k)); y0, x0 = (h - ch) // 2, (w - cw) // 2
    return cv2.resize(m[y0:y0 + ch, x0:x0 + cw].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
paint_wet = cv2.imread(P('pictures/wet_painting_lined_up.png'))
paint_dry = cv2.imread('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg')
road_c = er(central_mask(M['road']))
walls_c = er(central_mask(M['walls']))
res = {}
for name, painting, stage in (('dry', paint_dry, still('dry_projector')), ('wet', paint_wet, still('wet_projector'))):
    a, b = lum(central(painting)), lum(stage)
    a_s, b_s = cv2.GaussianBlur(a, (0, 0), 3), cv2.GaussianBlur(b, (0, 0), 3)
    res[name] = {'road_mean_painting': float(a[road_c].mean()), 'road_mean_stage': float(b[road_c].mean()), 'road_stage_over_painting': float(b[road_c].mean() / a[road_c].mean()),
                 'road_mean_absolute_difference_blurred': float(np.abs(a_s - b_s)[road_c].mean()), 'road_correlation_blurred': float(np.corrcoef(a_s[road_c], b_s[road_c])[0, 1]),
                 'walls_stage_over_painting': float(b[walls_c].mean() / a[walls_c].mean()),
                 'whole_picture_mean_painting': float(a.mean()), 'whole_picture_mean_stage': float(b.mean())}
out['plate_view_stage_against_painting'] = res

# ---- (2) moved view
Mm = masks('alignment/facts_surfaces_moved')
road_m, pav_m, walls_m, gut_m = er(Mm['road']), er(Mm['pavement'] | Mm['kerb'], 3), er(Mm['walls'], 3), er(Mm['gutter'], 3)
def glint(L, m):
    g8 = (np.clip(L, 0, 1) * 255).astype(np.uint8); med = cv2.medianBlur(g8, 31).astype(np.float32) / 255
    return float(((L - med) > 0.10)[m].mean())
moved = {}
for name in ('dry_moved', 'wet_moved', 'wetwet_moved'):
    im = still(name); L = lum(im)
    moved[name] = {'road_share_of_frame': float(road_m.mean()), 'road_mean': float(L[road_m].mean()), 'road_p95': float(np.percentile(L[road_m], 95)),
                   'road_glint_share': glint(L, road_m), 'road_blue_minus_red': float((im[:, :, 0].astype(float) - im[:, :, 2])[road_m].mean() / 255),
                   'gutter_mean': float(L[gut_m].mean()) if gut_m.sum() > 50 else None, 'pavement_glint_share': glint(L, pav_m), 'walls_mean': float(L[walls_m].mean())}
for n in ('wet_moved', 'wetwet_moved'):
    moved[n]['road_mean_over_dry_moved'] = moved[n]['road_mean'] / moved['dry_moved']['road_mean']
out['moved_view'] = moved

# ---- (3) the dry-looking patches: wet painting + dry behind against wet painting + wet behind
a, b = still('wet_moved'), still('wetwet_moved')
d = np.abs(lum(a) - lum(b)); ds = cv2.GaussianBlur(d, (0, 0), 2)
patch = ds > 0.04
out['dry_behind_patches'] = {'share_of_frame_that_differs_more_than_0.04': float(patch.mean()), 'mean_difference_where_it_differs': float(ds[patch].mean()) if patch.any() else 0.0,
                             'share_of_road_pixels_that_differ': float(patch[road_m].mean()), 'share_of_pavement_pixels_that_differ': float(patch[pav_m].mean()),
                             'share_of_walls_pixels_that_differ': float(patch[walls_m].mean())}
cv2.imwrite(P('pictures/stage_moved_dry_behind_patches_map.jpg'), cv2.resize(np.clip(ds * 6, 0, 1) * 255, (540, 960)).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])

# ---- (4) what each surface wears (from the colour map picture)
wimg = still('wet_weights').astype(int)
B_, G_, R_ = wimg[:, :, 0], wimg[:, :, 1], wimg[:, :, 2]
blue = (B_ > R_ + 25) & (B_ > G_ + 10)
green = (G_ > R_ + 15) & (G_ > B_ + 15)
orange = ~blue & ~green
out['moved_view_what_each_surface_wears_(rough, by colour of the map)'] = {'painting_share_of_frame': float(orange.mean()), 'behind_painting_share_of_frame': float(green.mean()), 'own_3D_surface_share_of_frame': float(blue.mean())}
json.dump(out, open(P('numbers/stage_measurements.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
