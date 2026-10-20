# What this does (plain words): asks "how much does the GROUND (the brown earth between the puddles and stones) matter, and at which size of detail?". It takes the real
# picture, paints over the puddles and stones with the nearest ground colour, blurs that ground by 24 / 12 / 6 / 3 / 0 dots, snaps it to the palette, puts the found
# puddles and stones back on top and scores the result dot for dot. Analysis only (reads the reference).
import os, sys, json
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import describe_tools as dt, score_tools as st, element_tools as et
import mud_layers as ml
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
bgr = cv2.imread(f'{PROC}/reference/mud/colour.png')
el = dt.load_elements('mud')
level = dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
d = dt.make_description(el, level)
shapes = ml.make_shape_list(d)[1:]            # drop the flat ground shape
# element mask = where the elements are drawn
canvas = np.zeros((1254, 1254, 3), np.uint8)
d2 = dict(d); d2['palette'] = [[255, 255, 255]] * len(d['palette'])
mask = (ml.draw_preview(d2, shapes=shapes)[..., 0] > 128).astype(np.uint8)     # drawn = white on a black canvas
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
print('elements cover', round(mask.mean() * 100, 1), '% of the picture')
# paint the elements' area with the nearest ground colour
dist_mask = mask.copy()
_, nearest = cv2.distanceTransformWithLabels(1 - dist_mask, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
ys, xs = np.nonzero(1 - dist_mask)
table = np.zeros(int(nearest.max()) + 1, np.int64)
table[nearest[ys, xs]] = np.arange(len(ys))
fy, fx = np.nonzero(dist_mask)
src = table[nearest[fy, fx]]
ground = bgr.copy()
ground[fy, fx] = bgr[ys[src], xs[src]]
cv2.imwrite('/tmp/mudscratch/ground_only.png', ground)
pal = np.array(d['palette'], np.uint8)[:, ::-1]
earth = [i for i, k in enumerate(el['kinds']) if k == 'earth']
pal_lab = cv2.cvtColor(pal.reshape(1, -1, 3).astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[0]
for sigma in (24, 12, 6, 3, 0):
    g = ground
    if sigma:
        padded = np.pad(ground, ((60, 60), (60, 60), (0, 0)), mode='wrap')
        g = cv2.GaussianBlur(padded, (0, 0), sigma)[60:-60, 60:-60]
    lab = cv2.cvtColor(g.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab).reshape(-1, 3)
    idx = np.zeros(len(lab), np.int32)
    for s in range(0, len(lab), 200000):
        dd = ((lab[s:s + 200000, None, :] - pal_lab[None, earth, :]) ** 2).sum(-1)
        idx[s:s + 200000] = np.array(earth)[dd.argmin(1)]
    q = pal[idx.reshape(1254, 1254)]
    # elements on top: draw the shapes onto q (numpy, same as the preview)
    big = cv2.resize(q, (1254 * 3, 1254 * 3), interpolation=cv2.INTER_NEAREST)
    k = 3.0
    for polygons, index in shapes:
        colour = tuple(int(v) for v in pal[index])
        for pts in polygons:
            pts = np.asarray(pts) - 1254 * np.floor(np.asarray(pts).mean(axis=0) / 1254)
            for ox, oy in ml.wrap_copy_count(pts, 1254):
                cv2.fillPoly(big, [((pts + [ox * 1254, oy * 1254]) * k).round().astype(np.int32)], colour, lineType=cv2.LINE_8)
    img = cv2.resize(big, (1254, 1254), interpolation=cv2.INTER_AREA)
    folder = f'/tmp/mudscratch/gs_{sigma}'
    st.write_folder(img, folder)
    r = st.score_folder(folder, texture=True)
    cv2.imwrite(f'/tmp/mudscratch/gs_{sigma}.png', img)
    print('ground blur', sigma, {k2: (round(r[k2], 3) if isinstance(r[k2], float) else r[k2]) for k2 in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'texture_compare_overall')})
