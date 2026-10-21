# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Makes the flat pictures that the new JOINTS layer for the road setts needs. It runs in plain Python (numpy and OpenCV), NOT in Blender, and only writes into
# relief_and_rubbish/setts/maps/. It changes nothing else.
#
# Words: a "sett" is one squared stone of the road, a "joint" is the thin gap between two setts. The road's colour picture (Poly Haven "square cobblestone", CC0) is 2 m
# wide, so one dot is 1 mm, and it repeats every 2 m on the road. A picture that is laid on the road "through its own coordinates" lines up dot for dot with the colour picture.
#
# What it makes
#   sett_joints_clean.png          one picture with three grey channels (8 bits each; the smooth slope is in the relief picture below, which is 16 bits):
#        red   = CAVITY: 1 in the middle of a joint, falling softly to 0 about 1 cm into the stone. The layer uses it to make the joint darker and duller.
#        green = GROOVE PROFILE: 1 on the joint floor, 0 on the stone top, with a rounded edge about 6 mm wide. Only used to make the groove's relief picture below.
#        blue  = HALO: a very soft, wide shade (about 2 cm) so that the stone's edge is a little darker than the middle of the stone (the look of a stone seated in its bed).
#   sett_groove_normal_16bit.png   a relief picture ("normal map": for every dot, which way the surface leans) of a rounded groove 8 mm deep, made from the groove profile.
#                                  Blender's convention (red = lean toward +u, green = lean toward +v, v is up the picture). I checked the convention against Poly Haven's own
#                                  relief picture and height picture first (the correlations are printed when this script runs).
#   sett_joints_check.jpg          a look-at sheet: colour picture, old cavity picture (mild1's), new cavity, new groove profile.
#   joint_cores_new.png            the MEASURING mask for the new picture: red = middle of a joint, green = middle of a stone (same layout as the study's joint_cores.png).
#
# How the joints are found: the same trick as the study (b01_make_joint_mask.py): a "black top-hat" on the brightness keeps thin dark lines and drops wide dark smudges.
# What is new here (the cleaning, because the study's picture was ragged and its lines had gaps, so cross joints looked dashed in the middle distance):
#   1. gaps up to 6 cm along a joint line are bridged (the study bridged 4.5 cm; the first helper here used 8.5 cm, which also filled narrow stones);
#   2. specks (joint blobs under 500 dots that touch no other joint) and holes (stone islands under 6000 dots: a real sett is about 35000) are removed;
#   3. the outline is smoothed (blur 1.5 dots, cut at half) and every joint is at least 5 dots (5 mm) wide.
# ROUND 1 ADDITION (completing the grid): the dark-lines-only search above finds only the joints that are filled with dark moss or dirt. About half of the photo's joints (most in the
# lower half of the 2 m picture) are filled with pale sand and were not found, so the road had stretches of "long stones" with no groove. The new step finds the setts' regular
# grid from the photo: the 10 rows of horizontal joints (from how much each row of the picture differs in colour from the stone), then in each row of stones the vertical joints
# (the same for each column), fills a gap where one joint is plainly missing between two others about 20 cm apart, and draws the joints that the dark search missed as straight lines
# as wide as the ones it found. It adds only where the dark search found nothing. Look at work/joint_grid_check.jpg (made by this script) to see what was added (green) over what
# was found (red).
# Run: python3 -I make_joint_pictures.py
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SETTS = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath('proc-work/street_wet')          # street_wet (the real one; this copy lives under painter_round_2/plate)
STUDY_WORK = os.path.join(ROOT, 'relief_and_rubbish', 'study', 'work')
MAPS = os.path.join(SETTS, 'maps')
os.makedirs(MAPS, exist_ok=True)

GROOVE_DEPTH_MM = 8.0          # depth of the relief picture's groove
VERT_SIGMA = 3.5               # dots: the profile's softness along the vertical joints (round 2 plate fix; it was 2.5, the same as EDGE_SIGMA)
EDGE_SIGMA = 2.5               # dots: softness of the groove's edge (the edge ramp is about 6 sigma = 15 dots wide at the foot, steepest in the middle)
MIN_WIDTH = 5                  # dots
BRIDGE = 60                    # dots: gaps up to this length along a joint line are bridged (the completion step adds the joints the dark search missed; a long bridge would also fill a narrow stone)
CORE_ERODE = 4                 # dots: the dark middle of the gap is the gap narrowed by this much on each side

colour = cv2.imread(os.path.join(ROOT, 'set_copy', 'textures', 'square_cobblestone_colour.jpg'))
N = colour.shape[0]
assert N == 2048


def tile3(a):
    return np.tile(a, (3, 3))


def crop(a):
    return a[N:2 * N, N:2 * N]


def complete_missing_joints(mask0, colour_bgr, report):
    """Returns mask0 with the joints the dark search missed drawn in (uint8 0/1) and the added part alone. report: dict filled with numbers."""
    lab = cv2.cvtColor(colour_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    stone_median = np.array([np.median(lab[..., i]) for i in range(3)])
    blurred = cv2.GaussianBlur(lab, (0, 0), 3)
    F = np.sqrt(((blurred - stone_median) ** 2 * np.array([0.6, 1.0, 1.0])).sum(-1))       # how far a dot's colour is from the typical stone colour
    n = N

    def peaks(profile, min_dist, threshold_share):
        lo, hi = np.percentile(profile, 10), profile.max()
        taken = np.zeros(len(profile), bool)
        found = []
        for i in np.argsort(-profile):
            if profile[i] < lo + (hi - lo) * threshold_share:
                break
            if taken[np.arange(i - min_dist, i + min_dist + 1) % len(profile)].any():
                continue
            taken[i] = True
            found.append(int(i))
        return sorted(found)

    def smooth_circular(a, width):
        return np.convolve(np.concatenate([a, a, a]), np.ones(width) / width, 'same')[len(a):2 * len(a)]

    # the width of the joints that the dark search found: the typical length of a run of joint dots along a scan line (runs of 8 to 60 dots)
    runs = []
    for y in range(0, n, 16):
        line = np.concatenate([[0], mask0[y].astype(np.int8), [0]])
        edges = np.flatnonzero(np.diff(line))
        lengths = edges[1::2] - edges[::2]
        runs += [int(v) for v in lengths if 8 <= v <= 60]
    width = int(np.median(runs)) if runs else 24
    report['joint_width_dots'] = width
    # 1. the rows of horizontal joints
    rows = peaks(smooth_circular(F.mean(axis=1), 9), 120, 0.30)
    report['rows'] = rows
    Ft = np.tile(F, (3, 3))
    M3 = np.tile(mask0, (3, 3))
    added = np.zeros((3 * n, 3 * n), np.uint8)               # drawn on the tiled picture so that nothing breaks at the 2 m repeat
    # 2. horizontal joints: where a stretch of a row has no dark-search joint, draw it at the row's best place
    chunk = 64
    horizontals_added = 0
    for r in rows:
        ys, centres = [], []
        for x0 in range(0, n, chunk):
            window = Ft[n + r - 32:n + r + 33, n + x0:n + x0 + chunk].mean(axis=1)
            ys.append(int(np.argmax(window)) - 32 + r)
        ys = np.array(ys)
        ys = np.array([int(np.median(ys[[(i - 1) % len(ys), i, (i + 1) % len(ys)]])) for i in range(len(ys))])
        for i, x0 in enumerate(range(0, n, chunk)):
            yc = int(ys[i])
            # a joint that the dark search found within 30 dots of the best place counts as THE joint: nothing is added there (a second line next to it would make a double-wide joint)
            near = M3[n + yc - 30:n + yc + 31, n + x0:n + x0 + chunk]
            covered = (near.max(axis=0) > 0).mean()
            if covered < 0.5:
                cv2.line(added, (n + x0 - chunk // 2, n + yc), (n + x0 + chunk + chunk // 2, n + yc), 1, width)
                horizontals_added += 1
    report['horizontal_chunks_added'] = horizontals_added
    # 3. vertical joints in each row of stones
    verticals_found = verticals_filled = verticals_drawn = 0
    for index, r in enumerate(rows):
        r_next = rows[(index + 1) % len(rows)] + (n if index == len(rows) - 1 else 0)
        y0, y1 = r + 28, r_next - 28
        profile = smooth_circular(Ft[n + y0:n + y1, n:2 * n].mean(axis=0), 7)
        found = peaks(profile, 110, 0.35)
        spacing = np.median(np.diff(found + [found[0] + n])) if len(found) > 3 else 200
        final = list(found)
        verticals_found += len(found)
        ring = found + [found[0] + n]
        lo, hi = np.percentile(profile, 10), profile.max()
        for a, b in zip(ring[:-1], ring[1:]):
            gap = b - a
            if gap > 1.55 * spacing:
                parts = int(round(gap / spacing))
                for k in range(1, parts):
                    guess = int(a + gap * k / parts)
                    window = np.array([profile[(guess + d) % n] for d in range(-25, 26)])
                    best = guess - 25 + int(np.argmax(window))
                    if window.max() > lo + (hi - lo) * 0.20:
                        final.append(best % n)
                        verticals_filled += 1
        for x in final:
            window = np.array([profile[(x + d) % n] for d in range(-10, 11)])
            xc = x - 10 + int(np.argmax(window))
            ya, yb = n + y0 - 28, n + y1 + 28                  # run from the middle of one horizontal joint to the middle of the next
            wide = M3[ya + 28:yb - 28, n + xc - 75:n + xc + 76]
            if (wide.max(axis=1) > 0).mean() >= 0.6:           # a joint found by the dark search within 75 dots counts as THE joint (stones are about 200 wide)
                continue
            window = M3[ya + 28:yb - 28, n + xc - 45:n + xc + 46]
            if (window.max(axis=1) > 0).mean() > 0.15:          # part of it was found: carry on from where the found part stands, so that the two make one line
                columns = np.nonzero(window)[1]
                xc = xc - 45 + int(np.median(columns))
            cv2.line(added, (n + xc, ya), (n + xc, yb), 1, width)
            verticals_drawn += 1
    report.update(verticals_found=verticals_found, verticals_filled=verticals_filled, verticals_drawn=verticals_drawn)
    # fold the three copies back into one picture (the middle copy is complete, but a line that ran off one edge came back from the neighbour copy)
    fold = np.zeros((n, n), np.uint8)
    for dy in (-n, 0, n):
        for dx in (-n, 0, n):
            fold |= added[n + dy:2 * n + dy, n + dx:2 * n + dx] if (0 <= n + dy and 2 * n + dy <= 3 * n and 0 <= n + dx and 2 * n + dx <= 3 * n) else 0
    return np.maximum(mask0, fold), fold


# 1. find the joints (same as the study)
lab = cv2.cvtColor(colour, cv2.COLOR_BGR2LAB).astype(np.float32)
L_s = cv2.GaussianBlur(lab[..., 0], (0, 0), 2.5)
tiled = tile3(L_s)
closed = cv2.morphologyEx(tiled, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (51, 51)))
tophat = crop(closed - tiled)
raw = (tophat > 25).astype(np.uint8)
raw = cv2.morphologyEx(raw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
count, labels, stats, _ = cv2.connectedComponentsWithStats(raw, connectivity=8)
keep = np.zeros(count, bool)
keep[1:] = stats[1:, cv2.CC_STAT_AREA] > 300
mask0 = keep[labels].astype(np.uint8)
print('study mask joint share', round(float(mask0.mean()), 4))
completion_report = {}
mask_found = mask0.copy()
mask0, mask_added = complete_missing_joints(mask0, colour, completion_report)
print('completing the grid:', completion_report, '; joint share now', round(float(mask0.mean()), 4))

# 2. clean: bridge gaps along lines (8.5 cm), then drop specks and fill holes, smooth the outline, minimum width
t = tile3(mask0)
bridge_h = cv2.morphologyEx(t, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (BRIDGE, 1)))
bridge_v = cv2.morphologyEx(t, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (1, BRIDGE)))
t = np.maximum(bridge_h, bridge_v)
t = cv2.dilate(t, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
# specks: joint blobs (in the tiled picture) that are small
count, labels, stats, _ = cv2.connectedComponentsWithStats(t, connectivity=8)
big = np.zeros(count, bool)
big[1:] = stats[1:, cv2.CC_STAT_AREA] >= 500
t = big[labels].astype(np.uint8)
# holes: small stone islands
inv = 1 - t
count, labels, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
small = np.zeros(count, bool)
small[1:] = stats[1:, cv2.CC_STAT_AREA] < 6000
t = np.maximum(t, small[labels].astype(np.uint8))
# smooth the outline and keep every joint at least MIN_WIDTH wide
smooth = (cv2.GaussianBlur(t.astype(np.float32), (0, 0), 1.5) > 0.5).astype(np.uint8)
# widen thin places: where an opening with a MIN_WIDTH square removes the joint, the joint is thinner than MIN_WIDTH there: add a one-dot border
opened = cv2.morphologyEx(smooth, cv2.MORPH_OPEN, np.ones((MIN_WIDTH, MIN_WIDTH), np.uint8))
thin = smooth & (1 - opened)
thin = cv2.dilate(thin, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
t = np.maximum(smooth, thin)
clean_tiled = t
clean = crop(t)
print('clean mask joint share', round(float(clean.mean()), 4))

# 3. the three profiles (computed on the tiled picture so that the 2 m repeat has no seam)
tf = clean_tiled.astype(np.float32)
# The cleaned mask runs from stone edge to stone edge (the whole gap, about 2.5 cm in the colour picture). The groove's SHAPE uses all of it (the stone's rounded edge starts at the
# stone's visible edge). The DARKNESS belongs to the middle of the gap, so the cavity is made from the gap narrowed by 4 dots on each side.
core_tiled = cv2.erode(clean_tiled, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CORE_ERODE + 1, 2 * CORE_ERODE + 1))).astype(np.float32)
narrow = cv2.GaussianBlur(core_tiled, (0, 0), 4.0)
wide = cv2.GaussianBlur(tf, (0, 0), 10.0)
cavity = np.clip(np.clip(narrow * 1.7, 0, 1) * 0.85 + np.clip(wide * 1.2, 0, 1) * 0.15, 0, 1)
# round 2 plate fix (the checker saw short bright ticks with hooked, S-shaped ends on the vertical joints in the middle distance): the groove profile is blurred a little more ALONG the vertical joints
# (sigma 3.5 dots up and down the picture instead of 2.5), so that the little steps and notches in a vertical joint do not make short steep walls that catch the light
profile = cv2.GaussianBlur(tf, (0, 0), sigmaX=EDGE_SIGMA, sigmaY=VERT_SIGMA)
halo = np.clip(cv2.GaussianBlur(tf, (0, 0), 14.0) * 1.6, 0, 1)
cavity, profile, halo = crop(cavity), crop(profile), crop(halo)
rgb8 = np.zeros((N, N, 3), np.uint8)
rgb8[..., 2] = np.round(cavity * 255)       # OpenCV writes BGR: index 2 is red
rgb8[..., 1] = np.round(profile * 255)
rgb8[..., 0] = np.round(halo * 255)
cv2.imwrite(os.path.join(MAPS, 'sett_joints_clean.png'), rgb8)

# 4. the groove's relief picture. Height (up is positive): 0 on the stone top, -depth in the joint. Tangent-space normal in Blender's convention (checked below):
#    red = -d(height)/d(u), green = -d(height)/d(v) = +d(height)/d(row) (v runs up the picture, rows run down), blue = 1; the picture's dots are 1 mm so height is in mm.
height_up = -GROOVE_DEPTH_MM * np.pad(profile, 0)       # profile has no tiling seam (it was made on the tiled picture)
tiled_h = tile3(height_up)
dh_dcol = cv2.Sobel(tiled_h, cv2.CV_32F, 1, 0, ksize=3, scale=1 / 8.0)
dh_drow = cv2.Sobel(tiled_h, cv2.CV_32F, 0, 1, ksize=3, scale=1 / 8.0)
nx, ny, nz = crop(-dh_dcol), crop(dh_drow), np.ones((N, N), np.float32)
length = np.sqrt(nx * nx + ny * ny + nz * nz)
normal = np.stack([nx / length, ny / length, nz / length], axis=-1)
print('groove normal: steepest lean', round(float(np.degrees(np.arccos(normal[..., 2].min()))), 1), 'degrees; share of dots leaning more than 10 degrees', round(float((normal[..., 2] < np.cos(np.radians(10))).mean()), 3))
enc = np.round((normal * 0.5 + 0.5) * 65535).astype(np.uint16)
cv2.imwrite(os.path.join(MAPS, 'sett_groove_normal_16bit.png'), enc[..., ::-1])

# convention check against Poly Haven's own pictures (their height and relief): the correlations must be about +0.93 (red) and +0.90 (green) with these signs
ph_h = cv2.imread(os.path.join(ROOT, 'set_copy', 'polyhaven_maps', 'square_cobblestone_displacement.jpg'), 0).astype(np.float32) / 255
ph_n = cv2.imread(os.path.join(ROOT, 'set_copy', 'textures', 'square_cobblestone_normal.jpg'))[..., ::-1].astype(np.float32) / 255 * 2 - 1
hs = cv2.GaussianBlur(ph_h, (0, 0), 3)
sx = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=3)
sy = cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=3)
ns = cv2.GaussianBlur(ph_n, (0, 0), 3)


def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).mean() / (a.std() * b.std() + 1e-9))


check = dict(red_vs_minus_dh_dcol=corr(ns[..., 0], -sx), green_vs_plus_dh_drow=corr(ns[..., 1], sy))
print('convention check (Poly Haven):', check)

# 5. the measuring mask for the new picture (same layout as the study's joint_cores.png: red = joint core, green = stone core)
inside = clean_tiled
core = crop(cv2.erode(inside, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))))
dist_outside = crop(cv2.distanceTransform((1 - inside).astype(np.uint8), cv2.DIST_L2, 5))
stone_core = (dist_outside > 10).astype(np.uint8)
cores = np.zeros((N, N, 3), np.uint8)
cores[..., 2] = core * 255
cores[..., 1] = stone_core * 255
cv2.imwrite(os.path.join(MAPS, 'joint_cores_new.png'), cores)

# 5b. the check picture of the completion: the photo, with the joints the dark search found in red and the joints added in green
grid_check = colour.copy()
grid_check[..., 2] = np.maximum(grid_check[..., 2], mask_found * 255)
grid_check[..., 1] = np.maximum(grid_check[..., 1], mask_added * 255)
cv2.imwrite(os.path.join(MAPS, 'joint_grid_check.jpg'), cv2.resize(grid_check, (1200, 1200)), [cv2.IMWRITE_JPEG_QUALITY, 88])

# 6. the look-at sheet
old = cv2.imread(os.path.join(STUDY_WORK, 'joint_cavity_closed.png'), 0)
c = (slice(0, 700), slice(0, 700))
panels = [colour[c], cv2.cvtColor(old[c], cv2.COLOR_GRAY2BGR), cv2.cvtColor((cavity[c] * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR),
          cv2.cvtColor((profile[c] * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)]
sheet = np.concatenate([cv2.resize(p, (450, 450)) for p in panels], axis=1)
cv2.imwrite(os.path.join(MAPS, 'sett_joints_check.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
json.dump(dict(completion=completion_report, joint_share_study=float(mask0.mean()), joint_share_clean=float(clean.mean()), groove_depth_mm=GROOVE_DEPTH_MM, edge_sigma_dots=EDGE_SIGMA,
               convention_check=check), open(os.path.join(MAPS, 'sett_joints_numbers.json'), 'w'), indent=1)
