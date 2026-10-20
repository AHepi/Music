# What this does (plain words): ANALYSIS tools that find the separate THINGS in a mud colour picture: the puddles (blue-grey ragged water areas) and the stones
# (dark, mostly blue-grey lumps, with a lighter face and a darker face). They read the reference picture (analysis only; the Blender generator never does) and
# return short lists: for a puddle its outline and the flat water tones inside it; for a stone its outline and its few flat faces. Everything is stored as
# whole-number corner lists (a corner is a step from the one before), never as pictures.
# The palette is found by k-means in Lab (a colour space where distance looks like what the eye sees); each palette colour is then sorted into a kind
# (water, stone, earth) by simple rules on its red / blue balance and brightness, so the same tools run unchanged on mud and on mud_golden.
import cv2
import numpy as np
import trace_tools as tt

PAD_WRAP = 220


def classify_palette(palette_bgr):
    """kind per palette colour, from its Lab colour: 'water' (bluish: b below -4 and not dark), 'stone' (grey or near-black: little colour, chroma under 9.5),
    'earth' (everything with an orange-brown tint, including the dark brown grooves and the tan highlights)."""
    lab = cv2.cvtColor(np.asarray(palette_bgr, np.uint8).reshape(1, -1, 3).astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[0]
    kinds = []
    for L, a, b in lab:
        chroma = float(np.hypot(a, b))
        if b <= -4 and L > 30:
            kinds.append('water')
        elif chroma < 9.5:
            kinds.append('stone')
        else:
            kinds.append('earth')
    return kinds


def wrap_pad(array, pad=PAD_WRAP):
    return np.pad(array, ((pad, pad), (pad, pad)) + ((0, 0),) * (array.ndim - 2), mode='wrap')


def fill_holes(mask):
    """Fill the holes inside connected areas of a 0/1 mask (flood from the border; what is not reached is a hole)."""
    h, w = mask.shape
    padded = np.pad(mask, 1)
    flood = padded.copy().astype(np.uint8)
    seed = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(flood, seed, (0, 0), 2)
    holes = (flood == 0)[1:-1, 1:-1]
    return (mask | holes).astype(np.uint8)


def contour_polygon(mask_crop, offset, epsilon):
    contours, _ = cv2.findContours(np.pad(mask_crop, 1), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    simple = cv2.approxPolyDP(contour, epsilon, True)[:, 0, :] + np.array([offset[0] - 1, offset[1] - 1])
    return simple if len(simple) >= 3 else None


def non_earth_mask(bgr, threshold=7.0):
    """Dots whose Lab 'b' number (yellow-blue balance) is under `threshold`: grey, blue-grey, black. Orange-brown earth has b above 10, so this picks out the
    stones and the water and leaves the earth (a tan or orange stone is NOT found; the traced patches layer paints those). Returns a padded 0/1 mask."""
    lab = cv2.cvtColor(wrap_pad(bgr).astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    mask = (lab[..., 2] < threshold).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return fill_holes(mask)


def water_dots_mask(bgr):
    """Dots that are clearly water: bluish (Lab b under -3.5) and not dark (L over 30). Stone clusters are dark; stones' lit faces are small. Padded 0/1."""
    lab = cv2.cvtColor(wrap_pad(bgr).astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    return ((lab[..., 2] < -3.5) & (lab[..., 0] > 30)).astype(np.uint8)


def solidity_of(component_mask):
    contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 1.0
    c = max(contours, key=cv2.contourArea)
    hull = cv2.contourArea(cv2.convexHull(c))
    return float(cv2.contourArea(c) / max(hull, 1.0))


def split_puddles_and_stones(mask, open_size=13, puddle_min_area=1500, puddle_max_solidity=0.82, big_area=9000, water_dots=None, min_water_share=0.4):
    """Cut the non-earth mask into puddle areas and the rest. A puddle survives a big opening (it is wide), is big, and is ragged (solidity under 0.82) or very big.
    Returns (puddle mask, stone-ish mask), both padded 0/1."""
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_size, open_size)))
    n, comp, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    cores = np.zeros_like(mask)
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < puddle_min_area:
            continue
        x, y, ww, hh = stats[i, :4]
        sol = solidity_of((comp[y:y + hh, x:x + ww] == i).astype(np.uint8))
        is_water = True if water_dots is None else (water_dots[y:y + hh, x:x + ww][comp[y:y + hh, x:x + ww] == i].mean() >= min_water_share)
        if is_water and (sol < puddle_max_solidity or area >= big_area):
            cores[comp == i] = 1
    grown = cores
    # re-grow the puddle edge back to the mask (the opening cut the raggedness off): geodesic dilation, one 3 x 3 step at a time, never leaving the mask
    for _ in range(8):
        grown = cv2.dilate(grown, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))) & mask
    stones = mask & (1 - grown)
    return grown, stones


def find_puddles(bgr, labels, kinds, threshold=7.0, epsilon=1.5, tone_epsilon=2.5, tone_min_area=30, **split_options):
    """Puddles as outlines (corners in tile dots, may lie outside the tile) and the flat water tones inside them (palette labels, stones inside are painted over)."""
    h, w = labels.shape
    pad = PAD_WRAP
    padded = wrap_pad(labels)
    mask = non_earth_mask(bgr, threshold)
    puddle_mask, _ = split_puddles_and_stones(mask, water_dots=water_dots_mask(bgr), **split_options)
    n, comp, stats, centroids = cv2.connectedComponentsWithStats(puddle_mask, connectivity=8)
    puddles = []
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        cx, cy = centroids[i]
        if not (pad <= cx < pad + w and pad <= cy < pad + h):
            continue
        inside = (comp[y:y + hh, x:x + ww] == i)
        outline = contour_polygon(inside.astype(np.uint8), (x, y), epsilon)
        if outline is None:
            continue
        sub = padded[y:y + hh, x:x + ww].astype(np.uint8)
        smooth = cv2.medianBlur(sub, 5)
        patches = []
        for k in np.unique(smooth[inside]):
            m = ((smooth == k) & inside).astype(np.uint8)
            if m.sum() < tone_min_area:
                continue
            nn, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
            for j in range(1, nn):
                if st[j, cv2.CC_STAT_AREA] < tone_min_area:
                    continue
                xx, yy, w2, h2 = st[j, :4]
                poly = contour_polygon((cc[yy:yy + h2, xx:xx + w2] == j).astype(np.uint8), (x + xx, y + yy), tone_epsilon)
                if poly is not None:
                    patches.append({'c': int(k), 'p': (poly - pad).astype(int).tolist(), 'a': float(st[j, cv2.CC_STAT_AREA])})
        puddles.append({'p': (outline - pad).astype(int).tolist(), 'area': float(area), 'centre': [float(cx - pad), float(cy - pad)], 'tones': patches})
    return puddles


def find_stones(bgr, labels, threshold=7.0, min_area=12, split_h=0.4, **split_options):
    """Stones: the non-earth areas that are not puddles, touching ones split by a distance-transform watershed. Returns dicts with the cropped mask and the palette
    labels inside, centre and size, in padded dots (the caller removes PAD_WRAP)."""
    h, w = labels.shape
    pad = PAD_WRAP
    padded = wrap_pad(labels)
    mask = non_earth_mask(bgr, threshold)
    _, stone_mask = split_puddles_and_stones(mask, water_dots=water_dots_mask(bgr), **split_options)
    stone_mask = cv2.morphologyEx(stone_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    mask = stone_mask
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    soft = cv2.GaussianBlur(dist, (0, 0), 1.2)
    local_max = cv2.dilate(soft, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    sure = (soft >= (1.0 - split_h) * local_max) & (soft >= local_max - 1e-6) & (mask > 0) & (dist > 1.5)
    n_m, markers = cv2.connectedComponents(sure.astype(np.uint8))
    markers = np.where(markers > 0, markers + 1, 0).astype(np.int32)          # 0 = not yet decided, 1 = outside, 2.. = one marker per stone
    markers[mask == 0] = 1
    colour3 = cv2.cvtColor((mask * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    ws = cv2.watershed(colour3, markers)
    stones = []
    for region_id in range(2, n_m + 1):
        region = (ws == region_id)
        area = int(region.sum())
        if area < min_area:
            continue
        ys, xs = np.nonzero(region)
        cx, cy = xs.mean(), ys.mean()
        if not (pad <= cx < pad + w and pad <= cy < pad + h):
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        stones.append({'crop': region[y0:y1, x0:x1].astype(np.uint8), 'x0': int(x0), 'y0': int(y0), 'area': area, 'centre': (float(cx - pad), float(cy - pad)),
                       'labels': padded[y0:y1, x0:x1]})
    return stones


def stone_description(stone, epsilon_outline=1.4, epsilon_face=1.6, face_min_area=10, max_faces=7):
    """One stone as: base palette colour (the most common label), outline corners, and a few flat faces inside (palette index + corners), biggest first.
    Faces are drawn over the base from big to small."""
    crop, x0, y0 = stone['crop'], stone['x0'], stone['y0']
    labs = stone['labels']
    outline = contour_polygon(crop, (x0, y0), epsilon_outline)
    if outline is None:
        return None
    inside = crop > 0
    counts = np.bincount(labs[inside].ravel(), minlength=int(labs.max()) + 1)
    base = int(counts.argmax())
    faces = []
    smooth = cv2.medianBlur(labs.astype(np.uint8), 3)
    for k in np.nonzero(counts)[0]:
        if k == base:
            continue
        m = ((smooth == k) & inside).astype(np.uint8)
        nn, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
        for j in range(1, nn):
            if st[j, cv2.CC_STAT_AREA] < face_min_area:
                continue
            xx, yy, w2, h2 = st[j, :4]
            poly = contour_polygon((cc[yy:yy + h2, xx:xx + w2] == j).astype(np.uint8), (x0 + xx, y0 + yy), epsilon_face)
            if poly is not None:
                faces.append((int(k), poly, float(st[j, cv2.CC_STAT_AREA])))
    faces.sort(key=lambda f: -f[2])
    return {'base': base, 'outline': outline, 'faces': faces[:max_faces], 'area': stone['area'], 'centre': stone['centre']}
