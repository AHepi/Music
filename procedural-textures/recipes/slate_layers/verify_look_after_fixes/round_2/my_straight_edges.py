# FAILED TOOL (recorded on purpose): this automatic facet finder did NOT work. It found 0 slanted straight stretches of 30+ dots in the reference, 0 in the BEFORE
# tile and only 3 in the AFTER tile, while by eye at least 14 facets are plainly visible in the AFTER tile (see facets_marked_on_contrast_boosted_after.jpg).
# The facet edges are soft and low-contrast, so the finder misses them. Several other tries (Hough lines, structure tensor, flat-patch outlines) also found nothing.
# The facet count in critic_result.json is therefore by eye, not by this script.
# What this does (plain words): my own check for "flat paint facets with straight slanting edges" (a low-poly, cut-glass look).
# Method: OpenCV's line-segment finder run on a blurred grey picture (blur 1.5 dots); keep straight stretches whose middle lies on a slate
# face (25+ dots away from any joint or rim), whose length is at least 20, 30 or 40 dots, and that are neither upright nor level (more than
# 14 degrees off both). Counted per million dots of slate face, for the reference, the BEFORE tile and the AFTER tile. The faint facets are
# hard for a computer to catch (their edges are soft and low-contrast), so this number UNDER-counts; it is only a sign that the after tile has
# straight slanting edges and the other two almost none. The eye count is in the notes of critic_result.json.
# Use: python3 -I my_straight_edges.py   (prints a table, writes my_straight_edges.json and straight_edges_after.jpg with the finds in red)
import json
import cv2
import numpy as np
P = 'proc-work/'
SETS = {'reference': P + 'reference/slate/colour.png',
        'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png',
        'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV, 0.8, 0.6, 2.0, 22.5, 0, 0.7, 1024)
res = {}
for name, path in SETS.items():
    bgr = cv2.imread(path)
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    face = cv2.erode((grey > 30).astype(np.uint8), np.ones((51, 51), np.uint8)).astype(bool)   # 25 dots clear of joints and rims
    ls = lsd.detect(cv2.GaussianBlur(grey, (0, 0), 1.5))[0]
    length = np.hypot(ls[:, 2] - ls[:, 0], ls[:, 3] - ls[:, 1])
    angle = np.degrees(np.arctan2(ls[:, 3] - ls[:, 1], ls[:, 2] - ls[:, 0])) % 180
    mx = ((ls[:, 0] + ls[:, 2]) / 2).astype(int).clip(0, grey.shape[1] - 1)
    my = ((ls[:, 1] + ls[:, 3]) / 2).astype(int).clip(0, grey.shape[0] - 1)
    slanted = ((angle > 14) & (angle < 76)) | ((angle > 104) & (angle < 166))
    area = face.sum() / 1e6
    res[name] = {'slate_face_million_dots': round(float(area), 3)}
    for min_length in (20, 30, 40):
        keep = face[my, mx] & slanted & (length >= min_length)
        res[name]['slanted_straight_stretches_min%d' % min_length] = int(keep.sum())
        res[name]['per_million_min%d' % min_length] = round(float(keep.sum() / area), 1)
        if min_length == 20:
            vis = bgr.copy()
            for x1, y1, x2, y2 in ls[keep]:
                cv2.line(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
            cv2.imwrite('straight_edges_%s.jpg' % name, vis, [cv2.IMWRITE_JPEG_QUALITY, 88])
json.dump(res, open('my_straight_edges.json', 'w'), indent=1)
for k, v in res.items():
    print(k, v)
