"""What this file does (plain words): measures the stage pictures of this step (stage/stills/*/still-6.00.jpg, 1080 x 1920) from the COPY of the film's lockout stage, in the moved view (the end of the film's street move):
  A. WHAT WEARS WHAT: the share of the frame, the road and the pavement that wears the painting (orange in the weights picture), the behind painting (green) and the 3D set's own surface (blue).
  B. DRY PATCHES: how bright, and how blue-or-red, the road and pavement are WHERE THE BEHIND PAINTING IS SHOWN (green), against the road and pavement that wear the front painting (orange) in the same rows
     (a dry behind painting shows as a lighter, redder ground; a matching wet one as the same brightness), for three combinations: the new front painting with the film's old DRY behind painting,
     with the new wet behind painting before the free colour match, and with it after the match.
  C. THE SEAM: along the border between the front painting and the behind painting on the road and pavement, how big the step in brightness is across the border (blurred brightness 8 to 16 dots on the behind side against
     8 to 16 dots on the painting side, averaged along the border), and the share of the border where the step is over 0.04.
  D. CHANGE FROM THE OLD BEHIND: the share of the road and the pavement whose brightness changes by more than 0.04 when the new wet behind painting replaces the old dry one.
The masks (road, pavement, ...) are Blender's, for the moved camera, from the first painter test's folder (read only). The live fire, flames and smoke are drawn on top in every picture alike. Writes numbers/stage_measurements.json.
Run: python3 -I tools/measure_stage_behind.py
"""
import json, os
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
FOLDER = 'proc-work/street_wet/painter_test/alignment/facts_surfaces_moved/'
W, H = 1080, 1920
def still(n): return cv2.imread(P('stage/stills', n, 'still-6.00.jpg'))
def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
f = json.load(open(FOLDER + 'facts.json'))
ids = cv2.cvtColor(cv2.imread(FOLDER + 'ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
M = {g: (np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24) for g, i in f['groups'].items()}
er = lambda m, n=3: cv2.erode(m.astype(np.uint8), np.ones((n, n), np.uint8)) > 0
road, pav = er(M['road'], 4), er(M['pavement'] | M['kerb'] | M['gutter'], 3)
w = still('r2_weights').astype(int)
B_, G_, R_ = w[:, :, 0], w[:, :, 1], w[:, :, 2]
blue = (B_ > R_ + 25) & (B_ > G_ + 10)
green = (G_ > R_ + 15) & (G_ > B_ + 15)
orange = ~blue & ~green
green_s = cv2.morphologyEx(green.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0       # tidy the colour map's speckle
orange_s = orange & ~green_s
out = {'A_what_wears_what_(moved_view,_rough,_by_colour_of_the_weights_picture)': {
    'whole_frame': {'painting': float(orange_s.mean()), 'behind_painting': float(green_s.mean()), 'own_3D_surface': float(blue.mean())},
    'road': {'painting': float(orange_s[road].mean()), 'behind_painting': float(green_s[road].mean()), 'own_3D_surface': float(blue[road].mean())},
    'pavement_kerb_gutter': {'painting': float(orange_s[pav].mean()), 'behind_painting': float(green_s[pav].mean()), 'own_3D_surface': float(blue[pav].mean())}}}
variants = {'old_dry_behind': 'r2_moved_drybehind', 'new_wet_behind_not_colour_matched': 'r2_moved_wetbehind_notmatched', 'new_wet_behind_colour_matched': 'r2_moved_wetbehind'}
rows_all = np.arange(H)[:, None] * np.ones((1, W), int)
def same_rows_reference(L, tgt, ref):
    """for the dots of tgt, the mean of the ref dots in the same row (a simple 'same distance, front painting' reference); rows with too few ref dots are left out"""
    num = np.where(ref, L, 0).sum(axis=1); cnt = ref.sum(axis=1)
    ok_rows = cnt >= 40
    refrow = np.where(ok_rows, num / np.maximum(cnt, 1), np.nan)
    return refrow
res = {}
for name, folder in variants.items():
    im = still(folder); L = lum(im); Ls = cv2.GaussianBlur(L, (0, 0), 4)
    bmr = (im[:, :, 0].astype(np.float32) - im[:, :, 2]) / 255
    row = {}
    for zone_name, zone in (('road', road), ('pavement_kerb_gutter', pav)):
        g_ = zone & green_s & er(green_s, 7); o_ = zone & orange_s & er(orange_s, 7)
        if g_.sum() < 300:
            row[zone_name] = {'dots_on_the_behind_painting': int(g_.sum())}; continue
        refrow = same_rows_reference(L, g_, o_)
        rr = np.nanmean(np.where(g_, refrow[:, None] * np.ones((1, W)), np.nan))
        refrow_b = same_rows_reference(bmr, g_, o_)
        rb = np.nanmean(np.where(g_, refrow_b[:, None] * np.ones((1, W)), np.nan))
        row[zone_name] = {'dots_on_the_behind_painting': int(g_.sum()), 'dots_on_the_front_painting': int(o_.sum()),
                          'mean_brightness_on_the_behind_painting': float(L[g_].mean()), 'mean_brightness_on_the_front_painting_in_the_same_rows': float(rr),
                          'ratio_behind_over_front_same_rows': float(L[g_].mean() / rr),
                          'blue_minus_red_on_the_behind_painting': float(bmr[g_].mean()), 'blue_minus_red_on_the_front_painting_in_the_same_rows': float(rb)}
    # the seam: border dots between green and orange
    gd = cv2.dilate(green_s.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    border = gd & orange_s & (cv2.dilate(green_s.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
    inner = cv2.erode(green_s.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
    # steps: for each border dot, mean of the blurred brightness 8..16 dots into the green side minus 8..16 dots into the orange side, via two rings of the green mask
    d_in = cv2.distanceTransform(green_s.astype(np.uint8), cv2.DIST_L2, 3)
    d_out = cv2.distanceTransform((~green_s).astype(np.uint8), cv2.DIST_L2, 3)
    ring_g = green_s & (d_in >= 8) & (d_in <= 16)
    ring_o = (~green_s) & orange & (d_out >= 8) & (d_out <= 16)
    zone = road | pav
    seam = {}
    for zname, zm in (('road', road), ('pavement_kerb_gutter', pav), ('road_and_pavement', zone)):
        a, b = ring_g & zm, ring_o & zm
        if a.sum() > 300 and b.sum() > 300:
            # compare local means (so different places along the border do not cancel): mean over each ring, in blocks of 64 rows
            steps = []
            for y0 in range(0, H, 64):
                aa, bb = a[y0:y0 + 64], b[y0:y0 + 64]
                if aa.sum() > 40 and bb.sum() > 40:
                    steps.append(float(Ls[y0:y0 + 64][aa].mean() - Ls[y0:y0 + 64][bb].mean()))
            steps = np.array(steps)
            seam[zname] = {'blocks_of_64_rows': int(len(steps)), 'mean_step_behind_minus_front': float(steps.mean()), 'mean_absolute_step': float(np.abs(steps).mean()), 'share_of_blocks_with_a_step_over_0.04': float((np.abs(steps) > 0.04).mean())}
    row['seam_between_front_and_behind_painting_(brightness_step_across_the_border)'] = seam
    res[name] = row
out['B_C_ground_that_wears_the_behind_painting_against_the_ground_that_wears_the_front_painting_and_the_seam'] = res
# D. the first test's "dry-looking patches" number, the same way: each picture against the one where the front painting is also its own behind painting (no dry or wet behind picture at all)
own = still('r2_moved_ownbehind'); Lown = lum(own); bown = (own[:, :, 0].astype(np.float32) - own[:, :, 2]) / 255
dd = {}
for name, folder in variants.items():
    im = still(folder); L = lum(im); bmr_ = (im[:, :, 0].astype(np.float32) - im[:, :, 2]) / 255
    dif = cv2.GaussianBlur(L - Lown, (0, 0), 2); patch = np.abs(dif) > 0.04
    row = {'share_of_frame_that_differs_more_than_0.04': float(patch.mean())}
    for zname, zm in (('road', road), ('pavement_kerb_gutter', pav)):
        sel = patch & zm
        row[zname] = {'share_of_these_dots_that_differ_more_than_0.04': float(patch[zm].mean()),
                      'mean_signed_brightness_change_where_it_differs_(picture_minus_front_painting_as_own_behind)': float(dif[sel].mean()) if sel.any() else None,
                      'share_of_them_lighter': float((dif[sel] > 0).mean()) if sel.any() else None,
                      'mean_blue_minus_red_change_where_it_differs': float(cv2.GaussianBlur(bmr_ - bown, (0, 0), 2)[sel].mean()) if sel.any() else None}
    dd[name] = row
out['D_the_first_tests_dry_patch_number_(picture_against_the_front_painting_used_as_its_own_behind_painting)'] = dd
# E. where the new wet behind painting changes the picture against the old dry one
a, b = lum(still('r2_moved_drybehind')), lum(still('r2_moved_wetbehind'))
d = cv2.GaussianBlur(np.abs(a - b), (0, 0), 2)
patch = d > 0.04
out['E_where_the_new_wet_behind_painting_changes_the_picture_against_the_old_dry_one'] = {'share_of_frame': float(patch.mean()), 'share_of_road': float(patch[road].mean()), 'share_of_pavement_kerb_gutter': float(patch[pav].mean()),
                                                                                      'mean_brightness_change_on_the_road_where_it_changes_(new_minus_old)': float((cv2.GaussianBlur(b - a, (0, 0), 2))[patch & road].mean()) if (patch & road).any() else None}
cv2.imwrite(P('pictures/stage_moved_old_dry_vs_new_wet_behind_difference_map.jpg'), cv2.resize(np.clip(d * 6, 0, 1) * 255, (540, 960)).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
json.dump(out, open(P('numbers/stage_measurements.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
