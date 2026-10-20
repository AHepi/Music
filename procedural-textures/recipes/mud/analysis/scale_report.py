# What this does (plain words): measures the three SCALE tests after Blender has baked them: (1) AREA: the 2508-dot picture of new unique mud: how well its edges wrap round (seam ratio:
# the jump across the wrap edge divided by an ordinary jump between neighbouring dots, 1.0 = invisible), whether any part repeats (the strongest "same picture again" peak of the
# picture's own correlation at a shift of 40 dots or more, 1 = an exact repeat, near 0 = never repeats), and how each of the four 1254 quadrants scores as a mud tile ("same kind");
# (2) RESOLUTION: bake time and sharpness at 512, 1254 and 2508 dots and how close the smaller pictures are to the biggest one shrunk down; (3) the half-tile SEAM test: the same
# description baked slid by half a tile compared with the first bake rolled by half a tile. Writes scores/scale_tests.json. Plain Python; reads the reference only to score quadrants.
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
import score_tools as st
pc, tc = st.pc, st.tc
out = {}
def grey(p):
    return cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY).astype(np.float64)
def seam(g):
    inner = np.abs(np.diff(g, axis=1)).mean(), np.abs(np.diff(g, axis=0)).mean()
    wrap = np.abs(g[:, 0] - g[:, -1]).mean(), np.abs(g[0, :] - g[-1, :]).mean()
    return round(float(wrap[0] / inner[0]), 3), round(float(wrap[1] / inner[1]), 3)
# ---------------------------------------------------------------- area
p = os.path.join(ROOT, 'area', 'area_2508', 'colour.png')
if os.path.exists(p):
    g = grey(p)
    f = np.fft.fft2(g - g.mean())
    ac = np.real(np.fft.ifft2(f * np.conj(f))); ac /= ac[0, 0]
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dy, dx = np.minimum(yy, h - yy), np.minimum(xx, w - xx)
    far = (np.hypot(dx, dy) >= 40)
    peak = float(ac[far].max())
    pos = np.unravel_index(np.argmax(np.where(far, ac, -1)), ac.shape)
    quad = {}
    for name, (r, c) in {'top_left': (0, 0), 'top_right': (0, 1254), 'bottom_left': (1254, 0), 'bottom_right': (1254, 1254)}.items():
        folder = os.path.join(ROOT, 'area', 'quadrant_' + name)
        os.makedirs(folder, exist_ok=True)
        cv2.imwrite(os.path.join(folder, 'colour.png'), cv2.imread(p)[r:r + 1254, c:c + 1254])
        st.write_folder(cv2.imread(os.path.join(folder, 'colour.png')), folder)       # maps from the colour (as the generator does)
        res = st.score_folder(folder, texture=True)
        quad[name] = {'kind_score': res['texture_compare_overall'], 'groups': {k: round(v, 3) for k, v in res['texture_compare_groups'].items()}, 'ssim_vs_reference': res['colour_ssim']}
    pair = {}
    names = list(quad)
    gq = {n: cv2.cvtColor(cv2.imread(os.path.join(ROOT, 'area', 'quadrant_' + n, 'colour.png')), cv2.COLOR_BGR2GRAY) for n in names}
    for i in range(4):
        for j in range(i + 1, 4):
            pair[f'{names[i]}-{names[j]}'] = round(pc.ssim(gq[names[i]], gq[names[j]]), 3)
    bake = json.load(open(os.path.join(ROOT, 'area', 'area_2508', 'bake.json')))
    out['area'] = {'size': 2508, 'seam_ratio_left_right_top_bottom': seam(g), 'strongest_repeat_peak_at_40_dots_or_more': round(peak, 3), 'at_shift': [int(pos[1]), int(pos[0])],
                   'quadrant_scores': quad, 'quadrant_pair_ssim': pair, 'bake_seconds': bake['total_s'], 'shapes': bake['shapes']}
# ---------------------------------------------------------------- resolution
res = {}
big_path = os.path.join(ROOT, 'resolution/size_2508/colour.png')
big = cv2.imread(big_path) if os.path.exists(big_path) else None
for size, folder in ((512, 'resolution/size_512'), (1254, 'variations/tile_101'), (2508, 'resolution/size_2508')):
    f = os.path.join(ROOT, folder)
    if not os.path.exists(os.path.join(f, 'colour.png')):
        continue
    img = cv2.imread(os.path.join(f, 'colour.png'))
    bake = json.load(open(os.path.join(f, 'bake.json')))
    row = {'bake_seconds': bake['total_s'], 'colour_render_seconds': bake['colour_render_s'], 'shapes': bake['shapes']}
    if big is not None:
        shrunk = cv2.resize(big, (size, size), interpolation=cv2.INTER_AREA)
        row['ssim_to_the_2508_bake_shrunk_to_this_size'] = round(pc.ssim(cv2.cvtColor(shrunk, cv2.COLOR_BGR2GRAY), cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), 4)
        row['mean_abs_difference_to_it'] = round(float(np.abs(shrunk.astype(float) - img).mean()), 2)
    res[size] = row
out['resolution'] = res
# ---------------------------------------------------------------- half-tile seam test
a, b = os.path.join(ROOT, 'variations/tile_101/colour.png'), os.path.join(ROOT, 'resolution/shifted_half/colour.png')
if os.path.exists(b):
    first = cv2.imread(a).astype(float); shifted = cv2.imread(b).astype(float)
    rolled = np.roll(first, (627, 627), axis=(0, 1))
    d = np.abs(rolled - shifted).mean(axis=-1)
    out['half_tile_seam_test'] = {'mean_abs_difference': round(float(d.mean()), 3), 'share_of_dots_differing_by_more_than_8_levels': round(float((d > 8).mean()), 5),
                                  'note': 'the shifted bake draws every shape slid by half a tile (wrapped); a perfectly periodic recipe gives 0 apart from anti-aliasing at shape edges'}
json.dump(out, open(os.path.join(ROOT, 'scores', 'scale_tests.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
