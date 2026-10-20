# What this does (plain words): the part of the slate generator that does NOT need Blender. It reads the layers of a description and turns
# them into ONE back-to-front list of flat shapes (each shape = the corner points of a polygon and a palette colour number):
#     layer 1  background: the black joints between slates (one big square in the gap colour)
#     layer 2  slates: one polygon per slate in its own base colour (outlines from the description)
#     layer 3  patches: the flat paint patches on the slates, big ones first, small ones on top
# Every polygon is grown outwards by half a dot ("grow") because an outline that runs through the middle of the edge dots would, once drawn
# with soft anti-aliased edges, leave a thin hairline of the colour below between two neighbouring patches.
# Plain numpy only (no Blender), so the same code can be used by the quick preview painter and tested without Blender.
import numpy as np


def delta_decode(flat):
    """[x0, y0, dx1, dy1, ...] -> n x 2 array of corner points (the description stores small steps because they make shorter text)."""
    steps = np.asarray(flat, np.float64).reshape(-1, 2)
    return np.cumsum(steps, axis=0)


def grow_polygon(points, distance):
    """Push every corner outwards by `distance` dots (mitred, never more than 3 x distance). Works for either direction of travel."""
    pts = np.asarray(points, np.float64)
    if distance == 0 or len(pts) < 3:
        return pts
    nxt = np.roll(pts, -1, axis=0)
    prv = np.roll(pts, 1, axis=0)
    area = 0.5 * np.sum(pts[:, 0] * nxt[:, 1] - nxt[:, 0] * pts[:, 1])
    sign = 1.0 if area > 0 else -1.0

    def outward(a, b):
        edge = b - a
        length = np.maximum(np.linalg.norm(edge, axis=1, keepdims=True), 1e-9)
        return sign * np.stack([edge[:, 1], -edge[:, 0]], axis=1) / length

    n1 = outward(prv, pts)         # normal of the edge arriving at each corner
    n2 = outward(pts, nxt)         # normal of the edge leaving it
    bisector = n1 + n2
    scale = 1.0 / np.maximum(1.0 + (n1 * n2).sum(axis=1, keepdims=True), 0.34)
    offset = bisector * scale * distance
    length = np.linalg.norm(offset, axis=1, keepdims=True)
    limit = 3.0 * abs(distance)
    offset = np.where(length > limit, offset / np.maximum(length, 1e-9) * limit, offset)
    return pts + offset


# ----------------------------------------------------------------------------------------------------- layout: rows of slates -> outlines
def value_noise(rng, length, scale, count):
    """A smooth wobbly line: random heights every `scale` dots, joined smoothly, sampled at `count` evenly spaced places; scaled to a spread of 1."""
    knots = rng.normal(size=int(length / scale) + 4)
    positions = np.linspace(0, length / scale, count)
    index = np.floor(positions).astype(int)
    fraction = positions - index
    smooth = fraction * fraction * (3 - 2 * fraction)
    values = knots[index] * (1 - smooth) + knots[index + 1] * smooth
    return values / max(values.std(), 1e-6)


def rough_line(rng, length, scale, count):
    """Two layers of wobble (big and small) so the edge looks chipped rather than wavy."""
    return 0.8 * value_noise(rng, length, scale, count) + 0.6 * value_noise(rng, length, scale / 3.0, count)


def slate_outline(x0, x1, slant_l, slant_r, top, bottom, corner, rough, rng, step=4.0, bottom_round=0.0):
    """One slate: a rounded rectangle whose sides may lean a little and whose four edges are ragged. Corner points in tile dots (y down).
    corner = radius of the four corners in dots. bottom_round (0..1) makes the two LOWER corners rounder: 1.0 = a half circle (fish-scale tiles)."""
    ymid = 0.5 * (top + bottom)
    left_x = lambda y: x0 + slant_l * (y - ymid)
    right_x = lambda y: x1 + slant_r * (y - ymid)
    scale = rough.get('scale', 14.0)
    corner_top = min(corner, 0.45 * (bottom - top), 0.45 * (x1 - x0))
    corner_bottom = corner_top if bottom_round <= 0 else min(max(corner_top, bottom_round * 0.5 * (x1 - x0)), 0.95 * (bottom - top), 0.5 * (x1 - x0))
    count_x = max(int((x1 - x0) / step), 3)
    # top edge, left to right
    xs_top = np.linspace(left_x(top) + corner_top, right_x(top) - corner_top, count_x)
    top_pts = np.stack([xs_top, top + rough['top'] * rough_line(rng, len(xs_top) * step, scale, len(xs_top)) * 0.55], axis=1)
    ys_right = np.linspace(top + corner_top, bottom - corner_bottom, max(int((bottom - top - corner_top - corner_bottom) / step), 3))
    right_pts = np.stack([right_x(ys_right) + rough['side'] * rough_line(rng, len(ys_right) * step, scale, len(ys_right)) * 0.55, ys_right], axis=1)
    xs_bot = np.linspace(right_x(bottom) - corner_bottom, left_x(bottom) + corner_bottom, max(int((x1 - x0 - 2 * corner_bottom) / step) + 2, 3))
    bot_pts = np.stack([xs_bot, bottom + rough['bottom'] * rough_line(rng, len(xs_bot) * step, scale, len(xs_bot)) * 0.55], axis=1)
    ys_left = np.linspace(bottom - corner_bottom, top + corner_top, max(int((bottom - top - corner_top - corner_bottom) / step), 3))
    left_pts = np.stack([left_x(ys_left) + rough['side'] * rough_line(rng, len(ys_left) * step, scale, len(ys_left)) * 0.55, ys_left], axis=1)

    def arc(cx, cy, radius, start_deg, points=5):
        angles = np.radians(start_deg + np.linspace(0, 90, points)[1:-1])
        return np.stack([cx + radius * np.cos(angles), cy + radius * np.sin(angles)], axis=1)
    bottom_points = 5 if corner_bottom < 12 else 11
    pieces = [top_pts, arc(right_x(top + corner_top) - corner_top, top + corner_top, corner_top, -90), right_pts,
              arc(right_x(bottom - corner_bottom) - corner_bottom, bottom - corner_bottom, corner_bottom, 0, bottom_points), bot_pts,
              arc(left_x(bottom - corner_bottom) + corner_bottom, bottom - corner_bottom, corner_bottom, 90, bottom_points), left_pts,
              arc(left_x(top + corner_top) + corner_top, top + corner_top, corner_top, 180)]
    return np.concatenate(pieces, axis=0)


def row_slates(row, tile):
    """The slates of one row as [x0, x1, slant_l, slant_r, top_shift, bottom_shift, palette index] taken from its joints.
    A row lists its joints [x, lean, gap] left to right; slate k lies between joint k - 1 and joint k (the first slate starts at the last
    joint of the row, one tile to the left, so the row wraps). Old-style rows that list their slates directly are passed through."""
    if 'joints' not in row:
        return [list(s) for s in row['slates']]
    joints = row['joints']
    n = len(joints)
    slates = []
    for k in range(n):
        left = joints[k - 1] if k > 0 else [joints[-1][0] - tile, joints[-1][1], joints[-1][2]]
        right = joints[k]
        slates.append([left[0] + left[2] / 2.0, right[0] - right[2] / 2.0, left[1], right[1], row['top_shift'][k] if 'top_shift' in row else 0.0,
                       row['bottom_shift'][k] if 'bottom_shift' in row else 0.0, row['colour'][k] if 'colour' in row else 1])
    return slates


def expand_layout(layout, tile):
    """The layout block -> [(outline points, palette index), ...] one per slate. layout = {'rows': [{'top', 'bottom', 'joints': [[x, lean, gap], ...],
    'top_shift': [...], 'bottom_shift': [...], 'colour': [...]}], 'corner': dots, 'rough': {'top', 'bottom', 'side', 'scale'}, 'seed': number}"""
    rng = np.random.default_rng(int(layout.get('seed', 1)))
    shapes = []
    for row in layout['rows']:
        for slate in row_slates(row, tile):
            x0, x1, slant_l, slant_r, top_shift, bottom_shift = slate[:6]
            colour = int(slate[6]) if len(slate) > 6 else 1
            points = slate_outline(x0, x1, slant_l, slant_r, row['top'] + top_shift, row['bottom'] + bottom_shift, layout.get('corner', 8.0), layout['rough'], rng,
                                   bottom_round=layout.get('bottom_round', 0.0))
            shapes.append((points, colour))
    return shapes


# ----------------------------------------------------------------------------------------------------- paint: scattered stamps
def stamp_polygon(rng, w, h, ragged=0.30, spike_chance=0.65):
    """A paint patch about w wide and h tall centred on (0, 0): an irregular many-cornered blob, with thin drip spikes at the top and the bottom
    (the reference's patches are streaky: spiky blobs standing upright). Corner points in dots, y down."""
    n = int(np.clip(5 + 2.2 * np.log2(max(w * h, 8.0) / 8.0), 6, 18))
    angle = 2 * np.pi * (np.arange(n) + rng.uniform(-0.3, 0.3, n)) / n + rng.uniform(0, 2 * np.pi / n)
    radius = 1.0 + ragged * rng.uniform(-1, 1, n)
    xs, ys = 0.5 * w * radius * np.cos(angle), 0.5 * h * radius * np.sin(angle)
    extra = []
    if h > 14:
        for sign in (-1.0, 1.0):
            if rng.random() < spike_chance:
                for _ in range(1 + int(rng.random() < 0.4) + int(h > 60 and rng.random() < 0.5)):
                    centre = rng.uniform(-0.35, 0.35) * w
                    half = max(1.0, rng.uniform(0.06, 0.16) * w)
                    reach = rng.uniform(1.05, 1.6) * 0.5 * h
                    extra += [(centre - half, sign * 0.62 * h * 0.5), (centre, sign * reach), (centre + half, sign * 0.62 * h * 0.5)]
    points = np.concatenate([np.stack([xs, ys], axis=1), np.array(extra).reshape(-1, 2)], axis=0)
    order = np.argsort(np.arctan2(points[:, 1], points[:, 0]))
    return points[order]


def streak_polygon(rng, w, h, tooth_width=(6.0, 15.0), tooth_length=(0.04, 0.42), side_wobble=0.04):
    """A paint patch built the way the reference's are: left and right sides nearly upright, top and bottom edges a row of thin upright
    triangles (drips): long pointed teeth of random width and length. Centred on (0, 0), y down."""
    def edge(sign):
        xs, ys = [], []
        x = -0.5 * w
        while x < 0.5 * w - 1.0:
            step = float(np.clip(rng.uniform(*tooth_width), 2.0, 0.5 * w + 1.0))
            step = min(step, 0.5 * w - x)
            base = sign * 0.5 * h * rng.uniform(0.78, 1.0)
            tip = base + sign * h * rng.uniform(*tooth_length) * (1.0 if rng.random() < 0.8 else 0.1)
            xs += [x, x + 0.5 * step]
            ys += [base, tip]
            x += step
        xs.append(0.5 * w)
        ys.append(sign * 0.5 * h * rng.uniform(0.8, 1.0))
        return np.array(xs), np.array(ys)
    xt, yt = edge(-1.0)
    xb, yb = edge(1.0)
    wobble = lambda n: side_wobble * w * rng.uniform(-1, 1, n)
    right = np.stack([0.5 * w + wobble(2), np.array([yt[-1] * 0.4, yb[-1] * 0.4])], axis=1)
    left = np.stack([-0.5 * w + wobble(2), np.array([yb[0] * 0.4, yt[0] * 0.4])], axis=1)
    top = np.stack([xt, yt], axis=1)
    bottom = np.stack([xb[::-1], yb[::-1]], axis=1)
    return np.concatenate([top, right, bottom, left], axis=0)


def pick_colour(rng, paint_model, family, target_grey, palette_grey):
    """Palette number of the colour in `family` nearest in brightness to target_grey (a little random choice among the two nearest)."""
    members = paint_model['family_colours'][family]
    if not members:
        members = paint_model['family_colours']['blue']
    distance = np.array([abs(palette_grey[i] - target_grey) for i in members])
    order = np.argsort(distance)
    if len(members) > 1 and rng.random() < 0.25:
        return members[order[1]]
    return members[order[0]]


def expand_paint(paint, layout_shapes_info, palette, tile, tag_band=False):
    """The 'paint' block -> flat shapes [(points, palette index), ...] (big patches first, specks last, per slate). layout_shapes_info: one dict per
    slate with its inner rectangle: {'x0', 'x1', 'top', 'bottom', 'tone', 'olive', 'tan'}. paint = {'model': {...}, 'seed': n, 'rate_scale': [...]}"""
    model = paint['model']
    rng = np.random.default_rng(int(paint.get('seed', 1)))
    palette_grey = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in palette]
    spread = model['slate_spread']
    shapes = []
    bands = model['band']
    families = model['families']
    scale = paint.get('rate_scale') or [1.0] * len(bands)
    for info in layout_shapes_info:
        info = dict(info)
        info['field_waves'] = [(rng.uniform(-1, 1), rng.uniform(-1, 1) * 0.6, rng.uniform(0, 2 * np.pi)) for _ in range(4)]
        x0, x1, top, bottom = info['x0'], info['x1'], info['top'], info['bottom']
        width, height = x1 - x0, bottom - top
        area = width * height
        olive_factor = info['olive'] / max(spread['olive'][0], 1e-3)
        tan_factor = info['tan'] / max(spread['tan'][0], 1e-3)
        for b in reversed(range(len(bands))):                          # biggest patches first
            if b not in paint.get('bands_used', range(len(bands))):
                continue
            band = bands[b]
            count = rng.poisson(band['count_per_1000_area'] * scale[b] * area / 1000.0)
            for _ in range(count):
                lw, lh = rng.multivariate_normal([band['log_w'][0], band['log_h'][0]], [[band['log_w'][1] ** 2, band['log_corr'] * band['log_w'][1] * band['log_h'][1]],
                                                                                       [band['log_corr'] * band['log_w'][1] * band['log_h'][1], band['log_h'][1] ** 2]])
                w = float(np.clip(np.exp(lw), 3, 0.95 * width))
                h = float(np.clip(np.exp(lh), 3, 0.97 * height))
                y_bin = rng.choice(model['y_bins'], p=np.array(model['y_hist'][b]) / np.sum(model['y_hist'][b]))
                cy_rel = (y_bin + rng.random()) / model['y_bins']
                cx = x0 + rng.random() * width
                cy = top + cy_rel * height
                mix = np.array(model['family_by_y'][b][y_bin], float)
                if mix.sum() == 0:
                    mix = np.array([1.0, 0, 0, 0])
                mix[1] *= olive_factor
                mix[2] *= tan_factor
                mix = np.minimum(mix, [1, 0.9, 0.9, 1]) if False else mix
                mix /= mix.sum()
                family = families[rng.choice(len(families), p=mix)]
                spread_b = band.get('tone_residual_std', band['tone_delta'][1])
                field = model.get('field', {'amp': 0.0})
                coherent = field['amp'] * np.sum([np.cos(2 * np.pi * (kx * (cx - x0) / field['scale_x'] + ky * (cy - top) / field['scale_y']) + ph) for kx, ky, ph in info['field_waves']]) / np.sqrt(len(info['field_waves'])) if field['amp'] else 0.0
                target = info['tone'] + paint.get('contrast', 1.0) * (model['tone_by_y'][y_bin] + coherent + rng.normal(0, paint.get('noise_scale', 1.0) * spread_b))
                if family == 'blue':
                    colour = pick_colour(rng, model, 'blue', target, palette_grey)
                else:
                    weights = np.array([model['colour_weight'][i] for i in model['family_colours'][family]])
                    colour = int(model['family_colours'][family][rng.choice(len(weights), p=weights / weights.sum())])
                if paint.get('shape') == 'library' and model.get('library') and w * h >= 60:
                    # real outlines from the shape library, chosen among those whose height / width is close to the wanted one, stretched to w x h, sometimes mirrored
                    wanted = h / w
                    options = [e for e in model['library'] if 1 / 1.7 < e['a'] / wanted < 1.7] or model['library']
                    entry = options[rng.integers(len(options))]
                    unit = np.array(entry['p'], np.float64).reshape(-1, 2) / 100.0
                    if rng.random() < 0.5:
                        unit[:, 0] *= -1
                    polygon = unit * [w, h] + [cx, cy]
                elif paint.get('shape', 'streak') in ('streak', 'library') and w > 14 and h > 22:
                    polygon = streak_polygon(rng, w, h) + [cx, cy]
                else:
                    polygon = stamp_polygon(rng, w, h) + [cx, cy]
                # keep the patch inside the slate (squash anything that sticks out onto the edge)
                polygon[:, 0] = np.clip(polygon[:, 0], x0 + 2.0, x1 - 2.0)
                polygon[:, 1] = np.clip(polygon[:, 1], top + 1.5, bottom - 1.5)
                shapes.append((polygon, int(b) if tag_band else int(colour)))
    return shapes


def make_shape_list(description):
    """The description's layers -> [(points, palette index), ...] back to front."""
    tile = float(description['tile'])
    grow = float(description.get('grow', 0.5))
    shapes = []
    pad = 2.0
    shapes.append((np.array([[-pad, -pad], [tile + pad, -pad], [tile + pad, tile + pad], [-pad, tile + pad]]), int(description.get('gap', 0))))
    if 'layout' in description and description['layout'].get('draw', True):      # slates from the layout block (procedural outlines)
        for points, colour in expand_layout(description['layout'], tile):
            shapes.append((grow_polygon(points, grow), colour))
    for slate in description.get('slates', []):       # slates with their outline written out (traced)
        shapes.append((grow_polygon(delta_decode(slate['o']), grow), int(slate['c'])))
    for patch in description.get('patches', []):
        shapes.append((grow_polygon(delta_decode(patch[1]), grow), int(patch[0])))
    if 'paint' in description and 'layout' in description:
        infos = []
        tones = description['paint'].get('slates')
        k = 0
        for r, row in enumerate(description['layout']['rows']):
            for i, slate in enumerate(row_slates(row, tile)):
                tone, olive, tan = tones[r][i] if tones else (64.0, 0.07, 0.06)
                infos.append({'x0': slate[0] + 0.0, 'x1': slate[1], 'top': row['top'] + slate[4], 'bottom': row['bottom'] + slate[5], 'tone': tone, 'olive': olive, 'tan': tan})
        for points, colour in expand_paint(description['paint'], infos, description['palette'], tile):
            shapes.append((points, colour))
    return shapes
