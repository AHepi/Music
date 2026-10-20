# What this does (plain words): TRACES the brown ground of the mud picture into flat colour patches (the biggest layer of the description, the "tracing the
# picture" end of the ladder, reported honestly as tracing and not as procedural generation). Steps: (1) paint over the puddles and stones (they are described by
# their own layers) with the nearest ground colour so no patches are wasted there; (2) cut the picture into ~100,000 tiny same-colour areas (32 colours);
# (3) repeatedly join the two neighbouring areas whose joining changes the picture least (the Ward rule: sizes x colour difference) and remember the order;
# (4) for each wanted patch count, replay the merging, give each patch the average colour, squeeze the colours into a short palette, and write each patch outline as a
# polygon. Saves analysis/ground_trace/tree.pkl and ground_trace/patches_<count>.pkl. Analysis only (it reads the reference; the generator only sees the result).
# Use: python3 -I trace_ground.py [name] [count ...]
import os, pickle, sys, time, json
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import merge_trace as mt, trace_tools as tt, describe_tools as dt
import mud_layers as ml
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
name = sys.argv[1] if len(sys.argv) > 1 else 'mud'
counts = [int(a) for a in sys.argv[2:]] or [3000, 8000, 16000, 30000]
out = os.path.join(HERE, 'ground_trace_' + name); os.makedirs(out, exist_ok=True)
bgr = cv2.imread(f'{PROC}/reference/{name}/colour.png')
el = dt.load_elements(name)
level = dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
d = dt.make_description(el, level)
shapes = ml.make_shape_list(d)[1:]
d2 = dict(d); d2['palette'] = [[255, 255, 255]] * len(d['palette'])
mask = (ml.draw_preview(d2, shapes=shapes)[..., 0] > 128).astype(np.uint8)
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
_, nearest = cv2.distanceTransformWithLabels(1 - mask, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
ys, xs = np.nonzero(1 - mask); table = np.zeros(int(nearest.max()) + 1, np.int64); table[nearest[ys, xs]] = np.arange(len(ys))
fy, fx = np.nonzero(mask); src = table[nearest[fy, fx]]
ground = bgr.copy(); ground[fy, fx] = bgr[ys[src], xs[src]]
cv2.imwrite(os.path.join(out, 'ground_inpainted.png'), ground)
t0 = time.time()
comp, lab = mt.initial_regions(ground, colour_count=32)
print('initial regions', int(comp.max()) + 1, round(time.time() - t0, 1), 's', flush=True)
tree_path = os.path.join(out, 'tree.pkl')
if os.path.exists(tree_path):
    tree = pickle.load(open(tree_path, 'rb'))
else:
    tree = mt.build_merge_tree(comp, lab); pickle.dump(tree, open(tree_path, 'wb'))
print('merge tree built', round(time.time() - t0, 1), 's', flush=True)
for target in counts:
    t1 = time.time()
    region_labels, count = mt.labels_at(comp, tree, target)
    means, area = mt.region_colours(region_labels, lab, count)
    centres, index = mt.squeeze_palette(means, area, 32)
    regions = mt.trace_labelled_regions(region_labels, count, index, 1.0)
    palette_bgr = tt.palette_to_bgr(centres)
    pickle.dump({'regions': regions, 'palette_bgr': palette_bgr, 'target': target}, open(os.path.join(out, f'patches_{target}.pkl'), 'wb'))
    print('target', target, 'patches', len(regions), 'vertices', sum(len(r['p']) for r in regions), round(time.time() - t1, 1), 's', flush=True)
