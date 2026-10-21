# What this does (plain words): plain Python (no Blender). Takes the ground measurements from c8_shade_maps.py and (1) re-counts them for LAND only (not under the hall, not the pond bed),
# (2) draws one picture with three top-down maps of the garden: year sun, sky openness, and where the add-on put its own moss, with the main things outlined.
# Run: python3 c8b_make_maps.py PREFIX OUT.jpg OUT_STATS.json
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
prefix, out_jpg, out_stats = sys.argv[1:4]
g = np.load(prefix + '_ground.npz'); S = g['sun'].astype(np.float32); O = g['openness'].astype(np.float32); X0, Y0, STEP = float(g['x0']), float(g['y0']), float(g['step'])
m = np.load(prefix + '_moss_density.npz'); D = m['density']; CELL = float(m['cell'])
ny, nx = S.shape
xs = X0 + STEP * (np.arange(nx) + 0.5); ys = Y0 + STEP * (np.arange(ny) + 0.5)
XX, YY = np.meshgrid(xs, ys)
POND_C, POND_A, POND_B, POND_ROT = (-3.0, 1.0), 3.3, 2.5, math.radians(10)
def pond_radius(x, y):
    dx, dy = x - POND_C[0], y - POND_C[1]
    u = dx * math.cos(-POND_ROT) - dy * math.sin(-POND_ROT); v = dx * math.sin(-POND_ROT) + dy * math.cos(-POND_ROT)
    th = np.arctan2(v / POND_B, u / POND_A)
    wob = 1 + 0.10 * np.sin(3 * th + 0.8) + 0.06 * np.sin(5 * th + 2.1) + 0.04 * np.sin(2 * th)
    return np.hypot(u / POND_A, v / POND_B) / wob
pr = pond_radius(XX, YY)
hall = (XX > -5.25) & (XX < 5.65) & (YY > 4.6) & (YY < 10.3)
gravel = (XX > 0.9) & (XX < 9.1) & (YY > -5.9) & (YY < 1.9)
fin = ~np.isnan(S)
land = fin & ~hall & (pr > 1.05)
def stats(mask):
    return {'spots': int(mask.sum()), 'year_sun_mean': float(S[mask].mean()), 'year_sun_p10_p50_p90': [float(np.percentile(S[mask], q)) for q in (10, 50, 90)],
            'openness_mean': float(O[mask].mean()), 'share_below_0p2_year_sun': float((S[mask] < 0.2).mean()), 'share_below_0p35_year_sun': float((S[mask] < 0.35).mean())}
res = {'land_all': stats(land), 'land_not_gravel': stats(land & ~gravel), 'gravel_court': stats(fin & gravel), 'pond_bank_ring_1.05_to_1.4_of_pond_radius': stats(fin & (pr > 1.05) & (pr < 1.4) & ~hall)}
# the add-on's moss against shade, land only, 0.5 m cells
nxc, nyc = D.shape
cs = np.zeros((nxc, nyc)); co = np.zeros((nxc, nyc)); cn = np.zeros((nxc, nyc))
for j in range(ny):
    for i in range(nx):
        if not land[j, i]: continue
        a = min(nxc - 1, int((xs[i] - X0) / CELL)); b = min(nyc - 1, int((ys[j] - Y0) / CELL)); cs[a, b] += S[j, i]; co[a, b] += O[j, i]; cn[a, b] += 1
ok = cn > 0; cs[ok] /= cn[ok]; co[ok] /= cn[ok]
rank = lambda a: np.argsort(np.argsort(a)).astype(float)
sp = lambda a, b: float(np.corrcoef(rank(a), rank(b))[0, 1])
d = D[ok]
shade_cells = ok & (cs < 0.35)
res['moss_vs_shade_land_only'] = {'cells_0p5m': int(ok.sum()), 'cells_with_add_on_moss': int((d > 0).sum()), 'spearman_moss_vs_year_sun': sp(d, cs[ok]), 'spearman_moss_vs_openness': sp(d, co[ok]),
    'share_of_moss_points_in_cells_below_35pct_sun': float(D[shade_cells].sum() / max(1, D[ok].sum())), 'share_of_land_cells_below_35pct_sun': float(shade_cells.sum() / ok.sum()),
    'mean_year_sun_where_moss_weighted': float(np.average(cs[ok], weights=np.maximum(d, 1e-9))), 'mean_year_sun_all_land_cells': float(cs[ok].mean())}
json.dump(res, open(out_stats, 'w'), indent=1)
print(json.dumps(res, indent=1))

# ------------------------------------------------------------- the picture
SC = 19                      # pixels per metre
W, H = int(22 * SC), int(21 * SC)
def to_px(x, y): return ((x - X0) * SC, (21 - (y - Y0)) * SC)
def ramp(v, stops):
    v = np.clip(v, 0, 1); out = np.zeros(v.shape + (3,), np.float32)
    ps = [s[0] for s in stops]; cols = np.array([s[1] for s in stops], np.float32)
    for c in range(3): out[..., c] = np.interp(v, ps, cols[:, c])
    return out
SUN_RAMP = [(0, (28, 40, 90)), (0.25, (70, 90, 150)), (0.5, (140, 150, 160)), (0.75, (235, 200, 110)), (1.0, (255, 245, 190))]
OPN_RAMP = [(0, (20, 20, 30)), (0.4, (60, 90, 100)), (0.7, (150, 190, 170)), (1.0, (240, 250, 230))]
def panel(values, ramp_stops, title, mask_gray=None):
    img = np.full((ny, nx, 3), 40, np.float32); img[fin] = ramp(values[fin], ramp_stops)
    if mask_gray is not None: img[mask_gray] = img[mask_gray] * 0.35 + 25
    im = Image.fromarray(img.astype(np.uint8)).resize((W, H), Image.NEAREST).transpose(Image.FLIP_TOP_BOTTOM)
    dr = ImageDraw.Draw(im)
    # things (from the build script): hall, roof, gravel, pond, walls, bridge, path, lantern, trees, camera
    def rect(x0, y0, x1, y1, col, w=2):
        a, b = to_px(x0, y1), to_px(x1, y0); dr.rectangle([a, b], outline=col, width=w)
    rect(-5.25, 4.6, 5.65, 10.3, (255, 255, 255), 2); rect(0.9, -5.9, 9.1, 1.9, (240, 230, 200), 1)
    th = np.linspace(0, 2 * math.pi, 90); pts = []
    for t in th:
        w_ = 1 + 0.10 * math.sin(3 * t + 0.8) + 0.06 * math.sin(5 * t + 2.1) + 0.04 * math.sin(2 * t)
        ux, vy = POND_A * math.cos(t) * w_, POND_B * math.sin(t) * w_
        pts.append(to_px(POND_C[0] + ux * math.cos(POND_ROT) - vy * math.sin(POND_ROT), POND_C[1] + ux * math.sin(POND_ROT) + vy * math.cos(POND_ROT)))
    dr.line(pts + [pts[0]], fill=(90, 200, 255), width=2)
    dr.line([to_px(-10.4, 10.5), to_px(10.4, 10.5), to_px(10.4, 1.4)], fill=(255, 255, 255), width=3)
    dr.line([to_px(*p) for p in [(-0.55, -0.6), (-2.0, 1.0), (-3.9, 0.15), (-5.95, 1.55)]], fill=(255, 150, 60), width=3)
    path = [(4.3, -5.6), (3.2, -3.1), (2.4, -1.0), (2.0, 0.9), (2.2, 2.8)]
    for p in path: x, y = to_px(*p); dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255))
    x, y = to_px(0.95, 1.1); dr.rectangle([x - 4, y - 4, x + 4, y + 4], outline=(255, 120, 120), width=2)          # lantern
    x, y = to_px(-6.7, 1.3); dr.ellipse([x - 16, y - 16, x + 16, y + 16], outline=(255, 90, 40), width=2)            # maple
    x, y = to_px(7.6, 4.6); dr.ellipse([x - 10, y - 10, x + 10, y + 10], outline=(120, 220, 90), width=2)           # pine
    cx, cy = to_px(-5.2, -5.6); dr.polygon([(cx, cy - 6), (cx - 5, cy + 4), (cx + 5, cy + 4)], fill=(255, 0, 255))
    tx, ty = to_px(1.0, 3.9); dr.line([(cx, cy), (tx, ty)], fill=(255, 0, 255), width=1)
    dr.rectangle([0, 0, W, 20], fill=(0, 0, 0)); dr.text((6, 4), title, fill=(255, 255, 255))
    return im
sun_im = panel(S, SUN_RAMP, 'Year sun (35 N)  dark = shade, light = full sun', hall)
opn_im = panel(O, OPN_RAMP, 'Sky openness  dark = closed in', hall)
# the add-on's moss: points per 0.5 m cell, shown on the same grid
Dm = np.zeros((ny, nx), np.float32)
for j in range(ny):
    for i in range(nx):
        a = min(nxc - 1, int((xs[i] - X0) / CELL)); b = min(nyc - 1, int((ys[j] - Y0) / CELL)); Dm[j, i] = D[a, b]
Dm = Dm / max(1.0, np.percentile(D[D > 0], 95))
moss_im = panel(Dm, [(0, (30, 30, 30)), (0.02, (40, 60, 40)), (0.4, (70, 140, 60)), (1.0, (200, 255, 120))], 'Moss the add-on grew (real pieces, per 0.5 m)', hall)
sheet = Image.new('RGB', (W * 3 + 8, H + 70), (20, 20, 20)); sheet.paste(sun_im, (0, 0)); sheet.paste(opn_im, (W + 4, 0)); sheet.paste(moss_im, (2 * W + 8, 0))
dr = ImageDraw.Draw(sheet)
lines = ['White = hall (grey out: not ground), gravel court (cream), pond (blue), garden walls, bridge (orange), stepping stones (dots), lantern, maple (orange ring), pine (green ring); magenta = the photo camera (north is up).',
         f"Land only: year sun mean {res['land_all']['year_sun_mean']:.2f}; {res['land_all']['share_below_0p35_year_sun']*100:.0f} % of land gets under 35 % of an open spot's sun. Add-on moss against year sun: rank match {res['moss_vs_shade_land_only']['spearman_moss_vs_year_sun']:+.2f} (0 = none).",
         'Made from the real shapes: 48 sun positions (both solstices and the equinox, every hour), 32 sky directions per spot, leaves block 60 %. Assumes north is +y (hall faces south).']
for i, t in enumerate(lines): dr.text((6, H + 6 + i * 20), t, fill=(230, 230, 230))
sheet.save(out_jpg, quality=80)
print('saved', out_jpg, sheet.size)
