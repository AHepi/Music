"""What this file does (plain words): measures the stage pictures of this step (stills/FOLDER/NAME/still-6.00.jpg, 1080 x 1920), drawn from the COPY of the film's lockout stage with the new wet front painting and the new wet behind painting.
It is the first painter test's measuring script (tools/measure_stage_views.py of that test) redone for the new paintings, with the same definitions, plus a few extra numbers asked for in this step:
  1. PLATE VIEW (the first frame): how bright the road arrives in the stage compared with the painting (the painting cut to the stage's narrower lens). First test: wet road 0.75 of painted, the film's dry painting 0.92.
     Extra: the same for the road's DARK parts (painted brightness 0.08 to 0.22), for the road's far, middle and near thirds, for the walls, and how much of the road's fine detail (each picture minus its own blur: joints, stones, rubbish) arrives.
  2. MOVED VIEW (the end of the film's street move): the road's brightness, shine, blue tint, gutter and walls, for the film's dry painting, the new wet painting with the new wet behind painting, with the film's old DRY behind painting
     (the first test's problem picture) and with the wet front painting as its own behind painting (the reference).
  3. THE DRY-LOOKING PATCHES, with the first test's definition: the share of road and pavement dots whose (blurred) brightness differs by more than 0.04 from the same view with the front painting used as its own behind painting
     (first test: 71 % of the road and 70 % of the pavement, with the old dry behind painting). Extra: of those dots, how many are LIGHTER (a dry-looking behind painting is lighter and redder) and how many are darker, and the average
     signed difference (lighter minus darker), for the old dry behind painting and for the new wet one.
  4. WHAT EACH SURFACE WEARS (from the weights picture): painting, behind painting, own surface.
  5. THE MID-MOVE (6.0 s of the street move): the road's brightness and how many dots look different from the dry-behind version.
Writes numbers/stage_measurements_FOLDER.json (FOLDER = before or after the brightness fix). Masks come from Blender for the same cameras (first painter test's alignment/facts_surfaces and facts_surfaces_moved, read only).
Run: python3 -I tools/measure_stage_round2.py FOLDER
"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from stage_common import central, central_mask, masks, er, load01, TEST1, FILM, W, H, P
FOLDER = sys.argv[1] if len(sys.argv) > 1 else 'before'
def still(n): return cv2.imread(P('stills', FOLDER, n, 'still-6.00.jpg'))
def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def lum01(rgb):   # from an RGB 0..1 picture
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)
out = {'folder': FOLDER}

# ---- 1. plate view
M = masks(TEST1 + 'alignment/facts_surfaces/')
road_c, walls_c = er(central_mask(M['road'])), er(central_mask(M['walls']))
rows = np.where(road_c.any(axis=1))[0]
cuts = [rows[0], rows[int(len(rows) / 3)], rows[int(2 * len(rows) / 3)], rows[-1] + 1]
thirds = []
for i in range(3):
    m = np.zeros_like(road_c); m[cuts[i]:cuts[i + 1]] = road_c[cuts[i]:cuts[i + 1]]; thirds.append(m)
def hp(L): return L - cv2.GaussianBlur(L, (0, 0), 2.0)
res = {}
for name, ppath, sname in (('film_dry_painting', FILM + 'lockout-painted.jpg', 'dry_projector'), ('new_wet_front_painting', P('../paint/front_painting_final.png'), 'wet_projector')):
    painting = lum01(central(load01(ppath))); stage = lum(still(sname))
    dark = road_c & (painting > 0.08) & (painting < 0.22)
    a_s, b_s = cv2.GaussianBlur(painting, (0, 0), 3), cv2.GaussianBlur(stage, (0, 0), 3)
    res[name] = {'road_mean_painting': float(painting[road_c].mean()), 'road_mean_stage': float(stage[road_c].mean()), 'road_stage_over_painting': float(stage[road_c].mean() / painting[road_c].mean()),
                 'road_far_third_over_painting': float(stage[thirds[0]].mean() / painting[thirds[0]].mean()), 'road_middle_third_over_painting': float(stage[thirds[1]].mean() / painting[thirds[1]].mean()),
                 'road_near_third_over_painting': float(stage[thirds[2]].mean() / painting[thirds[2]].mean()),
                 'road_dark_parts_over_painting_(painted_0.08_to_0.22)': float(stage[dark].mean() / painting[dark].mean()), 'road_dark_parts_share_of_road': float(dark.sum() / road_c.sum()),
                 'road_dots_painted_over_0.08_but_arriving_under_0.03_(crushed_to_black)': float(((painting > 0.08) & (stage < 0.03))[road_c].mean()),
                 'road_fine_detail_kept_(stage_over_painting)': float(np.std(hp(stage)[road_c]) / np.std(hp(painting)[road_c])),
                 'road_mean_absolute_difference_blurred': float(np.abs(a_s - b_s)[road_c].mean()), 'road_correlation_blurred': float(np.corrcoef(a_s[road_c], b_s[road_c])[0, 1]),
                 'walls_stage_over_painting': float(stage[walls_c].mean() / painting[walls_c].mean()),
                 'whole_picture_mean_painting': float(painting.mean()), 'whole_picture_mean_stage': float(stage.mean()),
                 'share_of_dots_brighter_than_0.97_in_the_stage': float((stage > 0.97).mean())}
out['plate_view_stage_against_painting'] = res

# ---- 2. moved view
Mm = masks(TEST1 + 'alignment/facts_surfaces_moved/')
road_m, pav_m, walls_m, gut_m = er(Mm['road']), er(Mm['pavement'] | Mm['kerb'], 3), er(Mm['walls'], 3), er(Mm['gutter'], 3)
def glint(L, m):
    g8 = (np.clip(L, 0, 1) * 255).astype(np.uint8); med = cv2.medianBlur(g8, 31).astype(np.float32) / 255
    return float(((L - med) > 0.10)[m].mean())
moved = {}
for name in ('dry_moved', 'wet_moved', 'wetolddry_moved', 'wetown_moved'):
    im = still(name); L = lum(im)
    moved[name] = {'road_mean': float(L[road_m].mean()), 'road_p95': float(np.percentile(L[road_m], 95)), 'road_glint_share': glint(L, road_m),
                   'road_blue_minus_red': float((im[:, :, 0].astype(float) - im[:, :, 2])[road_m].mean() / 255), 'gutter_mean': float(L[gut_m].mean()) if gut_m.sum() > 50 else None,
                   'pavement_mean': float(L[pav_m].mean()), 'pavement_glint_share': glint(L, pav_m), 'walls_mean': float(L[walls_m].mean()),
                   'road_dots_under_0.03': float((L[road_m] < 0.03).mean()), 'road_fine_detail_(std_of_picture_minus_blur)': float(np.std(hp(L)[road_m]))}
for n in ('wet_moved', 'wetolddry_moved', 'wetown_moved'):
    moved[n]['road_mean_over_dry_moved'] = moved[n]['road_mean'] / moved['dry_moved']['road_mean']
out['moved_view'] = moved

# ---- 3. the dry-looking patches
ref = lum(still('wetown_moved'))
def patches(name):
    L = lum(still(name)); d = L - ref; ds = cv2.GaussianBlur(np.abs(d), (0, 0), 2); sd = cv2.GaussianBlur(d, (0, 0), 2)
    diff = ds > 0.04
    lighter, darker = diff & (sd > 0), diff & (sd < 0)
    r = {'share_of_frame_that_differs_more_than_0.04': float(diff.mean()), 'mean_difference_where_it_differs': float(ds[diff].mean()) if diff.any() else 0.0}
    for zone, m in (('road', road_m), ('pavement', pav_m), ('walls', walls_m)):
        r[f'share_of_{zone}_dots_that_differ'] = float(diff[m].mean())
        r[f'share_of_{zone}_dots_lighter_(dry_looking)'] = float(lighter[m].mean())
        r[f'share_of_{zone}_dots_darker'] = float(darker[m].mean())
        r[f'{zone}_mean_signed_difference_(lighter_minus_darker)'] = float(sd[m].mean())
    return r, ds
pt, ds_old = patches('wetolddry_moved'); out['dry_behind_patches_old_dry_behind'] = pt
pt, ds_new = patches('wet_moved'); out['dry_behind_patches_new_wet_behind'] = pt
cv2.imwrite(P('work', f'patches_map_old_dry_behind_{FOLDER}.jpg'), cv2.resize(np.clip(ds_old * 6, 0, 1) * 255, (540, 960)).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite(P('work', f'patches_map_new_wet_behind_{FOLDER}.jpg'), cv2.resize(np.clip(ds_new * 6, 0, 1) * 255, (540, 960)).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])

# ---- 4. what each surface wears (the weights picture)
wimg = still('wet_weights').astype(int)
B_, G_, R_ = wimg[:, :, 0], wimg[:, :, 1], wimg[:, :, 2]
blue = (B_ > R_ + 25) & (B_ > G_ + 10)
green = (G_ > R_ + 15) & (G_ > B_ + 15)
green_s = cv2.morphologyEx(green.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
orange = ~blue & ~green_s
out['moved_view_what_each_surface_wears_(by_colour_of_the_weights_picture)'] = {
    'whole_frame': {'painting': float(orange.mean()), 'behind_painting': float(green_s.mean()), 'own_3D_surface': float(blue.mean())},
    'road': {'painting': float(orange[road_m].mean()), 'behind_painting': float(green_s[road_m].mean()), 'own_3D_surface': float(blue[road_m].mean())},
    'pavement_kerb_gutter': {'painting': float(orange[pav_m].mean()), 'behind_painting': float(green_s[pav_m].mean()), 'own_3D_surface': float(blue[pav_m].mean())}}

# ---- 3b. the same, only where the behind painting is really worn (green in the weights picture): is the ground there dry-looking, or just different?
def patches_where_behind_is_worn(name):
    L = lum(still(name)); d = L - ref; ds = cv2.GaussianBlur(np.abs(d), (0, 0), 2); sd = cv2.GaussianBlur(d, (0, 0), 2); sd8 = cv2.GaussianBlur(d, (0, 0), 8)
    g_ = er(green_s, 5)
    r = {}
    for zone, m in (('road', road_m), ('pavement', pav_m)):
        z = m & g_
        r[zone] = {'dots_where_the_behind_painting_is_worn': int(z.sum()), 'share_that_differ_more_than_0.04': float((ds > 0.04)[z].mean()), 'share_lighter_than_the_reference_by_more_than_0.04': float(((sd > 0.04))[z].mean()),
                   'share_darker_than_the_reference_by_more_than_0.04': float(((sd < -0.04))[z].mean()), 'mean_signed_difference_(lighter_minus_darker)': float(sd[z].mean()),
                   'patch_scale_(blur_8_dots)_share_that_differ_more_than_0.04': float((np.abs(sd8) > 0.04)[z].mean()), 'patch_scale_share_lighter_by_more_than_0.04': float((sd8 > 0.04)[z].mean()), 'patch_scale_share_darker_by_more_than_0.04': float((sd8 < -0.04)[z].mean()), 'mean_brightness_here': float(L[z].mean()), 'reference_mean_brightness_here': float(ref[z].mean())}
    return r
out['where_the_behind_painting_is_worn_old_dry_behind'] = patches_where_behind_is_worn('wetolddry_moved')
out['where_the_behind_painting_is_worn_new_wet_behind'] = patches_where_behind_is_worn('wet_moved')

# ---- 5. the mid-move
if os.path.exists(P('stills', FOLDER, 'wet_move', 'still-6.00.jpg')):
    mm = {}
    for n in ('wet_move', 'dry_move'):
        L = lum(still(n)); mm[n] = {'frame_mean': float(L.mean()), 'lower_half_mean': float(L[H // 2:].mean())}
    out['mid_move'] = mm
json.dump(out, open(P('numbers', f'stage_measurements_{FOLDER}.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
