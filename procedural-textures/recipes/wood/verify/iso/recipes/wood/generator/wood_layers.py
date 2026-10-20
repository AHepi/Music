# What this does (plain words): the part of the WOOD generator that does not need Blender. It reads the "layers" of a wood description file and turns
# them into ONE back-to-front list of flat coloured shapes. A shape is: a list of polygons (corner points in tile dots, y pointing down) and one
# palette colour number. The Blender part (wood_generator.py) draws that list as flat pieces of mesh and photographs it from above.
# Layer types a description may contain (in painting order, back to front; every layer is optional):
#   "boards"   the planks: each plank is a band between a top edge line and a bottom edge line (ragged), in its own base colour; what is left
#              uncovered between planks is the dark ground = the gaps. Edges are given as lists of [x, y] or made from {y, h} plus a roughness.
#   "stamps"   statistical paint: many flat ragged horizontal patches (splinter strips, weathered areas), drawn from a fitted model + a seed.
#   "speckle"  tiny horizontal dashes sprinkled over the planks (fine paint grain), from a model + a seed.
#   "patches"  traced flat patches: [palette colour, [x0, y0, dx1, dy1, ...]] (corner steps), painted as listed.
#   "blobs"    round dark splatters: single blobs [colour, x, y, radius] and/or "clouds" of many blobs.
#   "cracks"   dark lines of changing width: {"c": colour, "pts": [[x, y, width], ...]}.
#   "knots"    round ring patterns: {"x", "y", "rx", "ry", "angle", "rings": [colours outer to inner], "core": radius}.
#   "pebbles"  small round stones in the gaps between planks: rows of pebbles from a model + a seed.
#   "plank_rows"   a compact way to write the boards: the gap lines between planks as a height plus a few waves (whole numbers of waves per tile, so they repeat),
#              and the colour of the planks. Painted like "boards". "gap_ribbons" then draws the dark gaps (their widths) on top, "crack_field" invents the cracks
#              (a model + a seed), blobs may hold a "field" of splatter clouds (a model + a seed).
# The same code is used by the quick numpy preview painter and by the Blender bake. Plain numpy only.
import numpy as np


# ----------------------------------------------------------------------------------------------------- small helpers
def delta_decode(flat):
    """[x0, y0, dx1, dy1, ...] -> n x 2 array of corner points (a description stores small steps because they make shorter text)."""
    return np.cumsum(np.asarray(flat, np.float64).reshape(-1, 2), axis=0)


def grow_polygon(points, distance):
    """Push every corner outwards by `distance` dots (mitred, never more than 3 x distance). Works for either direction of travel."""
    pts = np.asarray(points, np.float64)
    if distance == 0 or len(pts) < 3:
        return pts
    nxt, prv = np.roll(pts, -1, axis=0), np.roll(pts, 1, axis=0)
    area = 0.5 * np.sum(pts[:, 0] * nxt[:, 1] - nxt[:, 0] * pts[:, 1])
    sign = 1.0 if area > 0 else -1.0

    def outward(a, b):
        edge = b - a
        length = np.maximum(np.linalg.norm(edge, axis=1, keepdims=True), 1e-9)
        return sign * np.stack([edge[:, 1], -edge[:, 0]], axis=1) / length

    n1, n2 = outward(prv, pts), outward(pts, nxt)
    scale = 1.0 / np.maximum(1.0 + (n1 * n2).sum(axis=1, keepdims=True), 0.34)
    offset = (n1 + n2) * scale * distance
    length = np.linalg.norm(offset, axis=1, keepdims=True)
    limit = 3.0 * abs(distance)
    offset = np.where(length > limit, offset / np.maximum(length, 1e-9) * limit, offset)
    return pts + offset


def smooth_noise_1d(rng, length, scale, count, octaves=((1.0, 1.0), (0.45, 3.0))):
    """A wobbly line: `count` evenly spaced samples over `length` dots; features about `scale` dots long (and finer octaves); spread about 1."""
    total = np.zeros(count)
    for amplitude, factor in octaves:
        knots = rng.normal(size=int(length / (scale / factor)) + 4)
        position = np.linspace(0, length / (scale / factor), count)
        index = np.floor(position).astype(int)
        fraction = position - index
        smooth = fraction * fraction * (3 - 2 * fraction)
        total += amplitude * (knots[index] * (1 - smooth) + knots[index + 1] * smooth)
    return total / max(total.std(), 1e-6)


class WaveField:
    """A smooth random 2-D field (a sum of a few waves, longer along x than y) with values about -1..1. Used for slow changes of tone over the tile.
    It repeats exactly across the tile if wavelengths divide the tile (they are rounded to whole numbers of waves)."""

    def __init__(self, rng, tile, scale_x, scale_y, waves=6):
        self.tile = tile
        kx = np.maximum(1, np.round(tile / scale_x * rng.uniform(0.6, 1.4, waves))).astype(int)
        ky = np.maximum(0, np.round(tile / scale_y * rng.uniform(0.6, 1.4, waves))).astype(int)
        ky = np.where(rng.random(waves) < 0.12, 0, ky)
        sign = rng.choice([-1, 1], waves)
        self.params = (kx, ky * sign, rng.uniform(0, 2 * np.pi, waves), rng.uniform(0.6, 1.0, waves))

    def __call__(self, x, y):
        kx, ky, phase, amp = self.params
        arg = 2 * np.pi * (np.multiply.outer(np.asarray(x, np.float64), kx) + np.multiply.outer(np.asarray(y, np.float64), ky)) / self.tile + phase
        return (np.cos(arg) * amp).sum(axis=-1) / np.sqrt((amp ** 2).sum() / 2.0)


def wrap_copy_count(points, tile):
    """Which whole-tile shifts (ox, oy) make a copy of the shape touch the tile (for pictures that repeat)."""
    low, high = np.min(points, axis=0), np.max(points, axis=0)
    shifts = []
    for ox in (-1, 0, 1):
        if high[0] + ox * tile < -1 or low[0] + ox * tile > tile + 1:
            continue
        for oy in (-1, 0, 1):
            if high[1] + oy * tile < -1 or low[1] + oy * tile > tile + 1:
                continue
            shifts.append((ox, oy))
    return shifts


# ----------------------------------------------------------------------------------------------------- boards
def board_edge_line(rng, y, rough, x0, x1, step=8.0):
    """One ragged board edge at height y from x0 to x1: [[x, y], ...]. rough = {'amp': dots, 'scale': dots}."""
    count = max(int((x1 - x0) / step) + 1, 4)
    xs = np.linspace(x0, x1, count)
    wobble = smooth_noise_1d(rng, x1 - x0, rough.get('scale', 40.0), count) * rough.get('amp', 2.0)
    return np.stack([xs, y + wobble], axis=1)


def edge_from_samples(y_values, x_from, x_to):
    """A board edge given as heights at evenly spaced places: [[x, y], ...]."""
    y_values = np.asarray(y_values, np.float64)
    return np.stack([np.linspace(x_from, x_to, len(y_values)), y_values], axis=1)


def expand_boards(layer, tile, rng):
    shapes = []
    rough = layer.get('rough', {'amp': 2.0, 'scale': 40.0})
    for board in layer['boards']:
        if 'top_y' in board:                                    # edges as heights at evenly spaced places (what the fitted descriptions use)
            top = edge_from_samples(board['top_y'], board.get('x_from', -25.0), board.get('x_to', tile + 25.0))
            bottom = edge_from_samples(board['bottom_y'], board.get('x_from', -25.0), board.get('x_to', tile + 25.0))
        elif 'top' in board:                                    # edges as explicit corner lists
            top = np.asarray(board['top'], np.float64)
            bottom = np.asarray(board['bottom'], np.float64)
        else:                                                   # edges made from a height and a roughness (what the sampler uses)
            top = board_edge_line(rng, board['y'], rough, -tile * 0.02, tile * 1.02)
            bottom = board_edge_line(rng, board['y'] + board['h'], rough, -tile * 0.02, tile * 1.02)
        polygon = np.concatenate([top, bottom[::-1]], axis=0)
        shapes.append(([polygon], int(board['colour'])))
    return shapes


def gap_lines_of(layer_list, tile):
    """The top edge of every board = the centre line of the gap above it, as [[x, y], ...] (used to place pebbles and cracks along the gaps)."""
    lines = []
    for layer in layer_list:
        if layer.get('type') != 'boards':
            continue
        for board in layer['boards']:
            if 'top_y' in board:
                lines.append(edge_from_samples(board['top_y'], board.get('x_from', -25.0), board.get('x_to', tile + 25.0)))
            elif 'top' in board:
                lines.append(np.asarray(board['top'], np.float64))
            else:
                lines.append(np.array([[-tile * 0.02, board['y']], [tile * 1.02, board['y']]]))
    return lines


def board_rows_of(layer_list, tile):
    """The board bands (y_top, y_bottom) as plain numbers (the middle of the top/bottom lines), used to place paint inside boards."""
    rows = []
    for layer in layer_list:
        if layer.get('type') == 'plank_rows':
            gaps = plank_gap_lines(layer, tile)
            for i, g in enumerate(gaps):
                nxt = gaps[(i + 1) % len(gaps)]
                rows.append((float(np.mean(g['y'])), float(np.mean(nxt['y'])) + (tile if i + 1 == len(gaps) else 0.0), int(layer['colours'][i % len(layer['colours'])] if 'colours' in layer else layer['colour'])))
            continue
        if layer.get('type') != 'boards':
            continue
        for board in layer['boards']:
            if 'top_y' in board:
                rows.append((float(np.mean(board['top_y'])), float(np.mean(board['bottom_y'])), int(board['colour'])))
            elif 'top' in board:
                rows.append((float(np.mean(np.asarray(board['top'])[:, 1])), float(np.mean(np.asarray(board['bottom'])[:, 1])), int(board['colour'])))
            else:
                rows.append((float(board['y']), float(board['y'] + board['h']), int(board['colour'])))
    return rows


# ----------------------------------------------------------------------------------------------------- polylines with width (cracks), blobs, knots, pebbles
def octagon(cx, cy, r, sides=8):
    a = np.arange(sides) * 2 * np.pi / sides + np.pi / sides
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def ribbon_polygons(points):
    """A polyline [[x, y, width], ...] as one quad per segment plus a round-ish cap at every corner; all in one shape."""
    pts = np.asarray(points, np.float64)
    polygons = []
    for (x0, y0, w0), (x1, y1, w1) in zip(pts[:-1], pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        length = np.hypot(dx, dy)
        if length < 1e-6:
            continue
        nx, ny = -dy / length, dx / length
        polygons.append(np.array([[x0 + nx * w0 / 2, y0 + ny * w0 / 2], [x1 + nx * w1 / 2, y1 + ny * w1 / 2],
                                  [x1 - nx * w1 / 2, y1 - ny * w1 / 2], [x0 - nx * w0 / 2, y0 - ny * w0 / 2]]))
    for x, y, w in pts:
        if w >= 1.5:
            polygons.append(octagon(x, y, w / 2))
    return polygons


def periodic_wave(x, waves, tile):
    """Sum of cosine waves that repeat exactly every tile: waves = [[whole number of waves per tile, amplitude in dots, phase in turns], ...]."""
    x = np.asarray(x, np.float64)
    total = np.zeros_like(x)
    for k, amplitude, phase in waves:
        total += amplitude * np.cos(2 * np.pi * (k * x / tile + phase))
    return total


def plank_gap_lines(layer, tile):
    """For a 'plank_rows' layer: x positions, and for every gap its centre line y(x) and its width w(x). Gaps repeat every tile."""
    xs = np.linspace(-25.0, tile + 25.0, int((tile + 50) / 24.0) + 1)
    gaps = []
    for g in layer['gaps']:
        y = g['y'] + periodic_wave(xs, g.get('wave', []), tile)
        w = np.maximum(g.get('width', 6.5) + periodic_wave(xs, g.get('width_wave', []), tile), 1.5)
        gaps.append({'x': xs, 'y': y, 'w': w})
    return gaps


def gap_geometry(layer_list, tile):
    """The gaps between planks as [{'x', 'y', 'w'}, ...] from the first 'plank_rows' layer, or from the top edges of an explicit 'boards' layer."""
    for layer in layer_list:
        if layer.get('type') == 'plank_rows':
            return plank_gap_lines(layer, tile)
    out = []
    for line in gap_lines_of(layer_list, tile):
        out.append({'x': line[:, 0], 'y': line[:, 1], 'w': np.full(len(line), 6.5)})
    return out


def expand_plank_rows(layer, tile, rng):
    gaps = plank_gap_lines(layer, tile)
    shapes = []
    n = len(gaps)
    for i in range(n):
        top = np.stack([gaps[i]['x'], gaps[i]['y']], axis=1)
        nxt = gaps[(i + 1) % n]
        bottom = np.stack([nxt['x'], nxt['y'] + (tile if i + 1 == n else 0.0)], axis=1)
        colour = layer['colours'][i % len(layer['colours'])] if 'colours' in layer else layer['colour']
        shapes.append(([np.concatenate([top, bottom[::-1]], axis=0)], int(colour)))
    return shapes


def expand_gap_ribbons(layer, tile, rng, gaps):
    out = []
    for g in gaps:
        pts = np.stack([g['x'], g['y'], g['w'] * layer.get('width_scale', 1.0)], axis=1)
        out.append((ribbon_polygons(pts), int(layer['colour'])))
    return out


def crack_polylines(layer, tile, gaps, rows):
    """Cracks in RUNS: a crack event is a run of 1 to 6 dashes along a nearly straight line (dash lengths and widths from the model, gaps of 4 to 40 dots between dashes)."""
    m = layer['model']
    cr = np.random.default_rng(int(layer.get('seed', 1)))
    mean_dashes = 2.6
    n_events = cr.poisson(m['per_megapixel'] * layer.get('scale', 1.0) * tile * tile / 1e6 / mean_dashes)
    lines = []
    for _ in range(n_events):
        x = cr.uniform(0, tile)
        if gaps and cr.random() < m.get('along_gap_share', 0.35):
            g = gaps[cr.integers(len(gaps))]
            y = float(np.interp(x, g['x'], g['y'])) + cr.normal(0, m.get('gap_offset_sd', 7.0))
        elif rows:
            top, bottom, _ = rows[cr.integers(len(rows))]
            y = cr.uniform(top + 8, bottom - 8)
        else:
            y = cr.uniform(0, tile)
        drift = cr.normal(0, m.get('angle_sd', 0.1) * 0.6)
        for _d in range(int(min(1 + cr.geometric(0.4) - 1, 6))):
            length = float(np.clip(np.exp(cr.normal(*m['length'])), 25.0, tile * 0.4))
            width0 = float(np.clip(np.exp(cr.normal(*m['width'])), 1.2, 14.0))
            step = m.get('corner_step', 18.0)
            count = max(int(length / step), 2)
            direction = drift + cr.normal(0, m.get('angle_sd', 0.1) * 0.5)
            pts = []
            for i in range(count + 1):
                taper = np.clip(np.sin(np.pi * i / count), 0, 1) ** 0.6
                pts.append([x + i * step, y, max(width0 * taper, 1.0)])
                direction = 0.7 * direction + cr.normal(0, m.get('angle_sd', 0.1) * 0.5)
                y += step * np.tan(direction)
            lines.append(pts)
            x += count * step + cr.uniform(4, 40)
    return lines


def expand_crack_field(layer, tile, rng, gaps, rows):
    return [(ribbon_polygons(pts), int(layer['colour'])) for pts in crack_polylines(layer, tile, gaps, rows)]


def expand_cracks(layer, tile, rng):
    return [(ribbon_polygons(c['pts']), int(c['c'])) for c in layer['list'] if len(c['pts']) >= 2]


def blob_polygon(rng, cx, cy, r, squash=0.85, ragged=0.28, sides=None):
    n = sides or int(np.clip(7 + r * 0.7, 8, 18))
    angle = 2 * np.pi * (np.arange(n) + rng.uniform(-0.25, 0.25, n)) / n
    radius = r * (1.0 + ragged * rng.uniform(-1, 1, n))
    return np.stack([cx + radius * np.cos(angle), cy + squash * radius * np.sin(angle)], axis=1)


def blob_list(layer, tile, rng):
    """Every splatter blob of a 'blobs' layer as [(palette colour, x, y, radius), ...]: single blobs, compact cloud rows, and clouds invented from a model (`field`)."""
    out = [(int(c), x, y, r) for c, x, y, r in layer.get('list', [])]
    clouds = list(layer.get('clouds', []))
    for i, (cx_, cy_, n_, sx_, sy_, r0_, r1_) in enumerate(layer.get('cloud_list', [])):          # compact clouds: [x, y, count, spread x, spread y, smallest r, biggest r]
        clouds.append({'x': cx_, 'y': cy_, 'n': int(n_), 'spread': [sx_, sy_], 'r': [r0_, r1_], 'colours': layer['colours'], 'seed': int(layer.get('seed', 1)) * 1000 + i})
    if layer.get('field'):                                         # invented splatter clouds from a model: counts, sizes and spreads of the measured kind
        f = layer['field']
        fr = np.random.default_rng(int(layer.get('seed', 1)) + 7)
        for i in range(fr.poisson(f['per_megapixel'] * tile * tile / 1e6)):
            n = int(max(3, np.exp(fr.normal(f['n_log'][0], f['n_log'][1]))))
            clouds.append({'x': fr.uniform(0, tile), 'y': fr.uniform(0, tile), 'n': n, 'spread': [f['spread'][0] * fr.uniform(0.6, 1.5), f['spread'][1] * fr.uniform(0.6, 1.5)],
                           'r': [f['r'][0], f['r'][1] * fr.uniform(0.7, 1.6)], 'colours': f['colours'], 'seed': int(fr.integers(1 << 30))})
    for cloud in clouds:
        cr = np.random.default_rng(int(cloud.get('seed', rng.integers(1 << 30))))
        n = int(cloud['n'])
        spread_x, spread_y = cloud['spread'][0], cloud['spread'][1]
        # biggest blobs near the middle, small ones further out (rust splatters have a dense core and a sprinkled edge)
        radii = np.exp(cr.uniform(np.log(cloud['r'][0]), np.log(cloud['r'][1]), n))
        radii = radii[np.argsort(-radii)]
        distance = np.sqrt(cr.random(n)) * (0.4 + 0.6 * (1.0 - radii / radii.max()))
        angle = cr.uniform(0, 2 * np.pi, n)
        colours = cloud['colours']
        weights = np.asarray(cloud.get('weights', [1.0] * len(colours)), np.float64)
        for i in range(n):
            out.append((int(colours[cr.choice(len(colours), p=weights / weights.sum())]), cloud['x'] + spread_x * distance[i] * np.cos(angle[i]),
                        cloud['y'] + spread_y * distance[i] * np.sin(angle[i]), float(radii[i])))
    return out


def expand_blobs(layer, tile, rng):
    br = np.random.default_rng(int(layer.get('seed', 1)) + 99)
    return [([blob_polygon(br, x, y, r)], colour) for colour, x, y, r in blob_list(layer, tile, rng)]


def ellipse_polygon(rng, cx, cy, rx, ry, angle, ragged=0.04, sides=40):
    a = np.arange(sides) * 2 * np.pi / sides
    wobble = 1.0 + ragged * smooth_noise_1d(rng, sides, 5.0, sides, ((1.0, 1.0),))
    x, y = rx * wobble * np.cos(a), ry * wobble * np.sin(a)
    c, s = np.cos(angle), np.sin(angle)
    return np.stack([cx + c * x - s * y, cy + s * x + c * y], axis=1)


def expand_knots(layer, tile, rng):
    """Round ring patterns. Each knot: centre (x, y), half-sizes rx, ry, tilt `angle`, `rings` = palette colours from the OUTSIDE to the inside, `ring_scale` = the size
    of each ring as a share of rx, ry (default: evenly shrinking), an optional black hole (`core` radius in `core_colour`)."""
    shapes = []
    for k in layer['list']:
        kr = np.random.default_rng(int(k.get('seed', rng.integers(1 << 30))))
        rings = k['rings']
        n = len(rings)
        scales = k.get('ring_scale') or [1.0 - i / n for i in range(n)]
        for colour, f in zip(rings, scales):
            shapes.append(([ellipse_polygon(kr, k['x'], k['y'], max(k['rx'] * f, 1.5), max(k['ry'] * f, 1.5), k.get('angle', 0.0), k.get('ragged', 0.05))], int(colour)))
        if k.get('core_colour') is not None:
            shapes.append(([ellipse_polygon(kr, k['x'], k['y'], k['core'], k['core'], 0.0, 0.1, 16)], int(k['core_colour'])))
    return shapes


def expand_pebbles(layer, tile, rng, gap_lines):
    """Small round stones lying in the gaps. A row = {gap: which gap line to follow (or y: a fixed height), x0, x1, r: [smallest, biggest] radius, colours, highlight}."""
    shapes = []
    pr = np.random.default_rng(int(layer.get('seed', 1)))
    for row in layer['rows']:
        x = row['x0']
        while x < row['x1']:
            r = pr.uniform(*row['r'])
            if row.get('gap') is not None and gap_lines:
                line = gap_lines[int(row['gap']) % len(gap_lines)]
                centre_y = float(np.interp(x + r, line[:, 0], line[:, 1]))
            else:
                centre_y = float(row['y'])
            cy = centre_y + pr.normal(0, row.get('jitter', 2.5))
            colour = row['colours'][pr.integers(len(row['colours']))]
            shapes.append(([blob_polygon(pr, x + r, cy, r, squash=0.8, ragged=0.2, sides=9)], int(colour)))
            if row.get('highlight') is not None and r > 3:
                shapes.append(([blob_polygon(pr, x + r * 0.9, cy - r * 0.25, r * 0.5, squash=0.7, ragged=0.15, sides=7)], int(row['highlight'])))
            x += 2 * r * pr.uniform(0.7, 1.3)
    return shapes


# ----------------------------------------------------------------------------------------------------- statistical paint (stamps and speckle)
def srgb_to_lab(rgb255):
    """sRGB numbers (0-255, n x 3) -> Lab (L 0-100), plain numpy (D65), the same scale the analysis used."""
    c = np.asarray(rgb255, np.float64).reshape(-1, 3) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = lin @ np.array([[0.4124564, 0.2126729, 0.0193339], [0.3575761, 0.7151522, 0.1191920], [0.1804375, 0.0721750, 0.9503041]]) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], axis=1)


def strip_polygon(rng, length, thickness, pointed=0.5, step_length=(7.0, 30.0), step_size=(1.0, 2.5), end_square=6.0):
    """A horizontal splinter-strip patch, centred on (0, 0): long and thin, tapered (pointed) or square at the ends, with STAIR-STEP top and bottom edges:
    each edge holds one height for 7-30 dots, then jumps by 1-2.5 dots, as the painted edges of the reference do."""
    n = max(int(length / np.mean(step_length)), 2)
    xs = np.concatenate([[-length / 2], np.sort(rng.uniform(-length / 2, length / 2, n)), [length / 2]])
    t = (xs + length / 2) / length
    if rng.random() < pointed:
        envelope = np.clip(np.sin(np.pi * t), 0, 1) ** 0.45
    else:
        envelope = np.clip(np.minimum(t * length, (1 - t) * length) / end_square, 0.35, 1.0)
    half = thickness / 2.0

    def edge(sign):
        walk, ys = 0.0, []
        for i in range(len(xs)):
            if rng.random() < 0.7:
                walk = 0.6 * walk + rng.choice([-1.0, 1.0]) * rng.uniform(*step_size)
            ys.append(sign * half * envelope[i] + walk * min(1.0, half / 3.0))
        pts = []
        for i in range(len(xs)):
            if i > 0:
                pts.append((xs[i], ys[i - 1]))
            pts.append((xs[i], ys[i]))
        return np.array(pts)

    top, bottom = edge(-1.0), edge(1.0)
    return np.concatenate([top, bottom[::-1]], axis=0)


def clamp_lab(lab, layer):
    """Keep the lightness of invented paint inside [paint_min_l, paint_max_l] (the blackest dots belong to the cracks and gaps, not to the paint)."""
    lab = np.array(lab, np.float64)
    lab[0] = np.clip(lab[0], layer.get('paint_min_l', 14.0), layer.get('paint_max_l', 70.0))
    return lab


def nearest_palette(palette_lab, lab):
    return int(np.argmin(((palette_lab - lab) ** 2).sum(axis=1)))


class TileGrid:
    """A coarse picture (one cell = `cell` dots) of the palette index currently visible, kept while stamps are painted, so a new stamp can ask 'what colour is
    beneath me?'. A cell is set to a stamp's colour inside the stamp's ellipse (wrap-around)."""

    def __init__(self, tile, cell=3, start=0):
        self.cell, self.n = cell, int(np.ceil(tile / cell))
        self.grid = np.full((self.n, self.n), start, np.int16)

    def get(self, x, y):
        return int(self.grid[int(y // self.cell) % self.n, int(x // self.cell) % self.n])

    def paint(self, x, y, half_length, half_thickness, value):
        hx, hy = max(int(half_length / self.cell), 1), max(int(half_thickness / self.cell), 1)
        cx, cy = int(x // self.cell), int(y // self.cell)
        ix = (np.arange(cx - hx, cx + hx + 1)) % self.n
        iy = (np.arange(cy - hy, cy + hy + 1)) % self.n
        gx, gy = np.meshgrid(np.arange(-hx, hx + 1) / hx, np.arange(-hy, hy + 1) / hy)
        inside = gx ** 2 + gy ** 2 <= 1.0
        block = self.grid[np.ix_(iy, ix)]
        block[inside] = value
        self.grid[np.ix_(iy, ix)] = block


def expand_stamps(layer, rows, tile, palette):
    """The statistical paint (it invents strips of the measured kind; it does not copy the reference).
    Step 1, ZONES: inside every board, rows of long strips cover the whole board; each strip's colour comes from three slow random fields (a colour in the Lab
    colour space: mean + spread of the fitted model), so warm brown, grey-blue and dark zones form large areas.
    Step 2, STRIPS: for every size class, from the biggest to the smallest, random horizontal strips; each strip's colour is the colour BENEATH it plus a random
    colour change (fitted mean and spread per size group); the nearest palette colour is used. `rate_scale` scales the number of strips per class."""
    model = layer['model']
    rng = np.random.default_rng(int(layer.get('seed', 1)))
    palette_lab = srgb_to_lab(palette)
    grid = TileGrid(tile, 3, start=rows[0][2] if rows else 0)
    zone = model['zone']
    shapes = []
    fields = [WaveField(rng, tile, zone['scale'][0], zone['scale'][1], waves=7) for _ in range(3)]
    chol = np.asarray(zone['chol'], np.float64)
    zone_mean = np.asarray(zone['lab_mean'], np.float64)
    jitter = layer.get('zone_jitter', 0.35)
    zone_amp, child_amp = layer.get('zone_amp', 1.0), layer.get('child_amp', 1.0)
    for top, bottom, _ in rows:
        y = top - rng.uniform(0, zone['row_height'][0] * 0.5)
        while y < bottom:
            height = float(np.clip(np.exp(rng.normal(np.log(zone['row_height'][0]), zone['row_height'][1] * 0.7)), 6.0, 90.0))
            height = min(height, bottom - y + 4.0)
            x = -rng.uniform(0, zone['strip_length'][0])
            while x < tile:
                length = float(np.clip(np.exp(rng.normal(np.log(zone['strip_length'][0]), zone['strip_length'][1] * 0.8)), 30.0, tile * 0.6))
                cx, cy = x + length / 2, y + height / 2
                f = np.array([fields[i](cx, cy) for i in range(3)]) + rng.normal(0, jitter, 3)
                colour = nearest_palette(palette_lab, clamp_lab(zone_mean + zone_amp * (chol @ f), layer))
                cy_here = cy + rng.uniform(-0.35, 0.35) * height
                polygon = strip_polygon(rng, length * 1.1, height * rng.uniform(0.9, 1.7), pointed=layer.get('zone_pointed', 0.8)) + [cx, cy_here]
                shapes.append(([polygon], colour))
                grid.paint(cx, cy_here, length / 2, height / 2, colour)
                x += length * rng.uniform(0.7, 0.95)
            y += height * rng.uniform(0.8, 0.95)
    scale = layer.get('rate_scale') or [1.0] * len(model['classes'])
    row_heights = np.array([max(b - t, 1.0) for t, b, _ in rows]) if rows else np.array([tile])
    for ci in sorted(model['child_classes'], reverse=True):
        cls = model['classes'][ci]
        child = model['child'][str(model['class_group'][ci])]
        child_mean, child_chol = np.asarray(child['mean']), np.asarray(child['chol'])
        n = rng.poisson(cls['per_megapixel'] * scale[ci] * (tile * tile * layer.get('coverage', 1.0)) / 1e6)
        for _ in range(n):
            length = float(np.clip(np.exp(rng.normal(np.log(cls['length'][0]), cls['length'][1])), 3.0, tile * 0.5))
            aspect = float(np.clip(np.exp(rng.normal(np.log(cls['aspect'][0]), cls['aspect'][1])), 1.0, 14.0))
            thickness = max(length / aspect, 1.5)
            if rows:
                pick = rng.choice(len(rows), p=row_heights / row_heights.sum())
                top, bottom, _ = rows[pick]
                cy = rng.uniform(top + thickness / 2, max(bottom - thickness / 2, top + thickness / 2 + 0.01))
            else:
                cy = rng.uniform(0, tile)
            cx = rng.uniform(0, tile)
            parent = grid.get(cx, cy)
            colour = nearest_palette(palette_lab, clamp_lab(palette_lab[parent] + child_mean + child_amp * (child_chol @ rng.normal(size=3)), layer))
            polygon = strip_polygon(rng, length, thickness, layer.get('child_pointed', 0.85)) + [cx, cy]
            shapes.append(([polygon], colour))
            grid.paint(cx, cy, length / 2, thickness / 2, colour)
    return shapes


def expand_speckle(layer, rows, tile, palette):
    """Tiny horizontal dashes (fine paint grain). Each takes a colour near the tone of the (stamp-free) board colour, a little lighter or darker."""
    model = layer['model']
    rng = np.random.default_rng(int(layer.get('seed', 1)))
    shapes = []
    n = rng.poisson(model['per_megapixel'] * tile * tile / 1e6)
    palette_grey = np.array([0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in palette])
    order = np.argsort(palette_grey)
    for _ in range(n):
        w = float(np.clip(np.exp(rng.normal(np.log(model['length'][0]), model['length'][1])), 1.0, 40.0))
        h = float(np.clip(w / np.exp(rng.normal(np.log(model['aspect'][0]), 0.25)), 1.0, 6.0))
        cx, cy = rng.uniform(0, tile, 2)
        colour = int(rng.choice(palette_count_of(palette), p=np.asarray(model['colour_weights'], np.float64) / np.sum(model['colour_weights'])))
        polygon = np.array([[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2], [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2]])
        shapes.append(([polygon], colour))
    return shapes


def palette_count_of(palette):
    return len(palette)


# ----------------------------------------------------------------------------------------------------- the whole list
def make_shape_list(description):
    """The description's layers -> [(list of polygons, palette index), ...] back to front. Every layer is expanded in the order it is listed."""
    tile = float(description['tile'])
    palette = description['palette']
    grow = float(description.get('grow', 0.5))
    pad = 2.0
    shapes = [([np.array([[-pad, -pad], [tile + pad, -pad], [tile + pad, tile + pad], [-pad, tile + pad]])], int(description.get('ground', 0)))]
    rows = board_rows_of(description['layers'], tile)
    for layer in description['layers']:
        kind = layer['type']
        rng = np.random.default_rng(int(layer.get('seed', 1)))
        if kind == 'boards':
            if layer.get('draw', True):                       # draw: false = the boards only give the gap lines (to place pebbles and cracks), nothing is painted
                shapes += expand_boards(layer, tile, rng)
        elif kind == 'plank_rows':
            shapes += expand_plank_rows(layer, tile, rng)
        elif kind == 'gap_ribbons':
            shapes += expand_gap_ribbons(layer, tile, rng, gap_geometry(description['layers'], tile))
        elif kind == 'crack_field':
            shapes += expand_crack_field(layer, tile, rng, gap_geometry(description['layers'], tile), rows)
        elif kind == 'stamps':
            shapes += expand_stamps(layer, rows, tile, palette)
        elif kind == 'speckle':
            shapes += expand_speckle(layer, rows, tile, palette)
        elif kind == 'patches':
            for colour, flat in layer['list']:
                shapes.append(([grow_polygon(delta_decode(flat) + 0.5, grow)], int(colour)))
        elif kind == 'blobs':
            shapes += expand_blobs(layer, tile, rng)
        elif kind == 'cracks':
            shapes += expand_cracks(layer, tile, rng)
        elif kind == 'knots':
            shapes += expand_knots(layer, tile, rng)
        elif kind == 'pebbles':
            shapes += expand_pebbles(layer, tile, rng, [np.stack([g['x'], g['y']], axis=1) for g in gap_geometry(description['layers'], tile)])
        else:
            raise ValueError('unknown layer type ' + kind)
    return shapes
