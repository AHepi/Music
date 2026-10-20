# What this does (plain words): reads a "painted tile" description (a short list of numbers: a colour palette, a brick layout, patches of
# paint, traced regions, tiny specks) and turns it into an ordered stack of flat-coloured shapes (polygons), painted back to front like a
# painter would. It is the "what goes where" half of the generator; brick_generator.py is the Blender half that turns the stack into real
# geometry and photographs it. It never reads a reference picture, only the description. numpy only, so it runs inside Blender and outside it.
#
# One shape = a dict: points (an N x 2 array in tile dots, x to the right, y DOWN the picture like the reference), colour (palette index),
# convex (True when a simple triangle fan can fill it), kind (what made it: backdrop / outline / brick / blob / region / speck).
#
# Layers a description can hold (they are painted in the order they are listed):
#   bricks   rows of bricks (rounded rectangles with a dark outline); each brick has its own base colour
#   blobs    patches: ragged ellipses  [centre x, centre y, radius x, radius y, angle, colour, raggedness, seed]
#   regions  traced patches: [colour, start x, start y, step x, step y, ...] in half dots (the "tracing the picture" layer)
#   specks   tiny dots scattered at random (made from a count, a size range, colours and a seed)
# Everything that crosses the tile edge is repeated one tile over, so the picture wraps round and the tile is seamless.
import math

import numpy as np

import mosaic_tools as mt

TILE = 1254.0


# ---------------------------------------------------------------------------------------------------- small helpers
def smooth_ring_noise(count, rng):
    """Random values on a ring that join up smoothly (used to make an outline ragged): returns a function of t in 0..1."""
    knots = rng.uniform(-1.0, 1.0, count)

    def value(t):
        position = (np.asarray(t) % 1.0) * count
        i0 = np.floor(position).astype(int) % count
        i1 = (i0 + 1) % count
        f = position - np.floor(position)
        f = f * f * (3.0 - 2.0 * f)
        return knots[i0] * (1 - f) + knots[i1] * f
    return value


def resample_closed(points, spacing):
    """Put points along a closed outline at (about) equal spacing."""
    closed = np.vstack([points, points[:1]])
    lengths = np.sqrt(((closed[1:] - closed[:-1]) ** 2).sum(1))
    total = lengths.sum()
    count = max(int(total / spacing), 8)
    distance = np.concatenate([[0], np.cumsum(lengths)])
    targets = np.linspace(0, total, count, endpoint=False)
    x = np.interp(targets, distance, closed[:, 0])
    y = np.interp(targets, distance, closed[:, 1])
    return np.stack([x, y], axis=1), total


def roughen_outline(points, amplitude, wavelength, rng, spacing=3.0):
    """Push every point of a closed outline sideways by smooth random amounts (ragged edge). amplitude in dots."""
    if amplitude <= 0:
        return points
    dense, total = resample_closed(points, spacing)
    n = len(dense)
    tangent = np.roll(dense, -1, axis=0) - np.roll(dense, 1, axis=0)
    length = np.sqrt((tangent ** 2).sum(1)) + 1e-9
    normal = np.stack([tangent[:, 1], -tangent[:, 0]], axis=1) / length[:, None]
    t = np.arange(n) / n
    coarse = smooth_ring_noise(max(int(total / max(wavelength, 2.0)), 3), rng)
    fine = smooth_ring_noise(max(int(total / max(wavelength / 3.0, 1.0)), 5), rng)
    push = amplitude * (coarse(t) + 0.45 * fine(t))
    return dense + normal * push[:, None]


def rounded_rectangle(x0, y0, x1, y1, radius, steps=4):
    radius = max(0.0, min(radius, (x1 - x0) / 2.0 - 0.01, (y1 - y0) / 2.0 - 0.01))
    if radius < 0.5:
        return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)
    pts = []
    for cx, cy, a0 in ((x1 - radius, y0 + radius, -90), (x1 - radius, y1 - radius, 0), (x0 + radius, y1 - radius, 90), (x0 + radius, y0 + radius, 180)):
        for s in range(steps + 1):
            a = math.radians(a0 + 90.0 * s / steps)
            pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return np.array(pts, float)


def ragged_ellipse(cx, cy, rx, ry, angle_degrees, raggedness, seed, spacing=3.0):
    """A patch of paint: an ellipse whose edge wobbles at three scales (a few big lumps, some middle bumps, fine chips).
    raggedness 0 = smooth ellipse, 0.4 = hand-cut, 0.8 = very irregular amoeba."""
    rng = np.random.default_rng(int(seed))
    perimeter = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
    count = int(min(max(perimeter / spacing, 12), 72))
    theta = np.arange(count) * (2 * math.pi / count)
    t = theta / (2 * math.pi)
    big = smooth_ring_noise(int(rng.integers(3, 6)), rng)
    middle = smooth_ring_noise(int(rng.integers(6, 11)), rng)
    fine = smooth_ring_noise(max(count // 2, 7), rng)
    scale = 1.0 + raggedness * (0.50 * big(t) + 0.32 * middle(t) + 0.18 * fine(t))
    scale = np.maximum(scale, 0.2)
    x = rx * scale * np.cos(theta)
    y = ry * scale * np.sin(theta)
    a = math.radians(angle_degrees)
    return np.stack([cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)], axis=1)


# ---------------------------------------------------------------------------------------------------- wrap copies
def wrapped_copies(points, tile):
    """The shape plus copies one tile over when it crosses an edge (so what leaves on one side comes back on the other)."""
    x0, y0 = points.min(0)
    x1, y1 = points.max(0)
    shifts_x = [0.0] + ([tile] if x0 < 0 else []) + ([-tile] if x1 > tile else [])
    shifts_y = [0.0] + ([tile] if y0 < 0 else []) + ([-tile] if y1 > tile else [])
    return [points + np.array([dx, dy]) for dx in shifts_x for dy in shifts_y]


# ---------------------------------------------------------------------------------------------------- layers
def layer_bricks(layer, shapes, tile, rng):
    radius = layer.get('corner_radius', 9.0)
    outline = layer.get('outline_width', 2.0)
    outline_colour = layer.get('outline_colour', 0)
    ragged = layer.get('ragged', 0.0)
    wavelength = layer.get('ragged_wavelength', 14.0)
    for row in layer['rows']:
        y0, y1 = row['y0'], row['y1']
        for brick in row['bricks']:
            x0, x1, colour = brick[0], brick[1], brick[2]
            if outline > 0:
                outer = rounded_rectangle(x0 - outline, y0 - outline, x1 + outline, y1 + outline, radius + outline)
                outer = roughen_outline(outer, ragged, wavelength, rng) if ragged > 0 else outer
                shapes.append({'points': outer, 'colour': outline_colour, 'convex': ragged <= 0, 'kind': 'outline'})
            face = rounded_rectangle(x0, y0, x1, y1, radius)
            face = roughen_outline(face, ragged, wavelength, rng) if ragged > 0 else face
            shapes.append({'points': face, 'colour': colour, 'convex': ragged <= 0, 'kind': 'brick'})


def layer_blobs(layer, shapes, tile, rng):
    for item in layer['items']:
        cx, cy, rx, ry, angle, colour = item[:6]
        raggedness = item[6] if len(item) > 6 else 0.4
        seed = item[7] if len(item) > 7 else int(cx * 7 + cy * 13)
        shapes.append({'points': ragged_ellipse(cx, cy, rx, ry, angle, raggedness, seed), 'colour': int(colour), 'convex': False, 'kind': 'blob'})


def layer_regions(layer, shapes, tile, rng):
    scale = layer.get('unit', 0.5)           # one step unit in dots (0.5 = half dots)
    for item in layer['items']:
        colour = int(item[0])
        steps = np.asarray(item[3:], float).reshape(-1, 2)
        start = np.array([item[1], item[2]], float)
        points = np.vstack([start, start + np.cumsum(steps, axis=0)]) * scale
        shapes.append({'points': points, 'colour': colour, 'convex': False, 'kind': 'region', 'wrap': layer.get('wrap', False)})


def layer_specks(layer, shapes, tile, rng):
    count = int(layer['count'])
    low, high = layer.get('size', [1.5, 4.0])
    colours = layer['colours']
    sub = np.random.default_rng(int(layer.get('seed', 1)))
    for _ in range(count):
        cx, cy = sub.uniform(0, tile, 2)
        r = sub.uniform(low, high) / 2.0
        shape = ragged_ellipse(cx, cy, r, r * sub.uniform(0.6, 1.0), sub.uniform(0, 180), 0.5, int(sub.integers(1, 1 << 30)), spacing=2.0)
        shapes.append({'points': shape, 'colour': int(colours[int(sub.integers(0, len(colours)))]), 'convex': False, 'kind': 'speck'})


def layer_outlines(layer, shapes, tile, rng):
    """Dark ring along the edge of every brick, drawn on top of whatever is below (a ring = an outer outline with a hole).
    inside = how far the ring reaches into the brick, outside = how far out into the mortar, each as [left, top, right, bottom] in dots."""
    radius = layer.get('corner_radius', 9.0)
    inside = layer.get('inside', [1.5, 1.5, 1.5, 2.5])
    outside = layer.get('outside', [1.5, 0.5, 2.5, 4.5])
    colour = layer['colour']
    for row in layer['rows']:
        y0, y1 = row['y0'], row['y1']
        for brick in row['bricks']:
            x0, x1 = brick[0], brick[1]
            outer = rounded_rectangle(x0 - outside[0], y0 - outside[1], x1 + outside[2], y1 + outside[3], radius + 1.5)
            inner = rounded_rectangle(x0 + inside[0], y0 + inside[1], x1 - inside[2], y1 - inside[3], max(radius - 1.5, 0.0))
            shapes.append({'points': outer, 'holes': [inner], 'colour': colour, 'convex': False, 'kind': 'outline_ring'})


def layer_mosaic(layer, shapes, tile, rng):
    """A mosaic of flat paint patches: cells cut by straight lines half way between random seed points, edges bent by a smooth wobble, colours drawn
    from tables by a slowly changing tone dial (so neighbours look alike) with some cells made soot-dark near a few smudge centres.
    target 'bricks': fills every brick face (rows given); target 'mortar': fills the whole tile (the cells hidden under bricks are skipped).
    Parameters: seed, scales [{area, keep, table, wobble, wavelengths, step}], tables {key: probability per palette colour}, base_classes,
    luma_order (palette indices from dark to light), tone {wavelengths, jitter}, accents [{seed, count, sigma [x, y], strength, colours}] (places where
    cells take dark soot or pale spall colours), exclude_accent_colours (true = the ordinary tone table never uses the accent colours)."""
    sub = np.random.default_rng(int(layer.get('seed', 1)))
    order = np.array(layer['luma_order'])
    tone_info = layer.get('tone', {})
    dial = mt.ToneDial(sub, tuple(tone_info.get('wavelengths', (110.0, 170.0, 260.0))))
    jitter = tone_info.get('jitter', 0.2)
    accents = []
    for acc in layer.get('accents', []):
        centres = np.random.default_rng(int(acc['seed'])).uniform(0, tile, (int(acc['count']), 2))
        accents.append((acc, centres))
    excluded = set(int(c) for acc, _ in accents for c in acc['colours']) if layer.get('exclude_accent_colours') else set()

    def accent_probability(acc, centres, x, y):
        sx, sy = acc.get('sigma', [42.0, 85.0])
        dx = (x - centres[:, 0] + tile / 2) % tile - tile / 2
        dy = (y - centres[:, 1] + tile / 2) % tile - tile / 2
        raw = float(np.exp(-(dx * dx / (2 * sx * sx) + dy * dy / (2 * sy * sy))).sum())
        core = acc.get('core', [0.45, 0.9])                  # below core[0] never, above core[1] always: clouds are solid in the middle, clear at the edge
        return float(np.clip((raw - core[0]) / (core[1] - core[0]), 0.0, 1.0)) * acc.get('strength', 0.9)

    def pick_colour(table_key, centre, jitter_here, shift=0.0):
        for acc, centres in accents:
            if sub.random() < accent_probability(acc, centres, centre[0], centre[1]):
                return int(acc['colours'][int(sub.integers(0, len(acc['colours'])))])
        q = float(np.clip(dial(centre[0], centre[1]) + shift + sub.normal(0, jitter_here), 0.0, 0.999))
        table = np.array(layer['tables'][table_key], float)
        for c in excluded:
            table[c] = 0.0
        return mt.colour_by_quantile(table, order, q)

    wobbles = [mt.Wobble(sub, sc.get('wobble', 1.3), tuple(sc.get('wavelengths', (7.0, 17.0)))) for sc in layer['scales']]
    if layer['target'] == 'bricks':
        radius = layer.get('corner_radius', 9.0)
        classes = layer['base_classes']
        for row in layer['rows']:
            for brick in row['bricks']:
                face = rounded_rectangle(brick[0], row['y0'], brick[1], row['y1'], radius)
                cls = classes[brick[2]]
                brick_shift = float(sub.normal(0.0, layer.get('brick_tone_spread', 0.0)))      # every brick a little lighter or darker than its neighbours
                for sc, wob in zip(layer['scales'], wobbles):
                    key = f"{cls}_{sc['table']}" if f"{cls}_{sc['table']}" in layer['tables'] else f"0_{sc['table']}"
                    for points, centre in mt.mosaic_in_shape(face, sc['area'], sub, wob, keep=sc.get('keep', 1.0), step=sc.get('step', 4.0)):
                        shapes.append({'points': points, 'colour': pick_colour(key, centre, sc.get('jitter', jitter), brick_shift), 'convex': False, 'kind': 'cell'})
    else:
        rects = np.array([[b[0] - 6.0, row['y0'] - 6.0, b[1] + 6.0, row['y1'] + 6.0] for row in layer['rows'] for b in row['bricks']])

        def hidden(centre):
            inside = ((centre[0] - rects[:, 0]) % tile < (rects[:, 2] - rects[:, 0])) & (centre[1] >= rects[:, 1]) & (centre[1] <= rects[:, 3])
            return bool(inside.any())
        for sc, wob in zip(layer['scales'], wobbles):
            for points, centre in mt.periodic_cells(tile, sc['area'], sub, wob, keep=sc.get('keep', 1.0), step=sc.get('step', 4.0), skip=hidden):
                shapes.append({'points': points, 'colour': pick_colour(str(sc['table']), centre, sc.get('jitter', jitter)), 'convex': False, 'kind': 'cell'})


LAYER_BUILDERS = {'mosaic': layer_mosaic, 'bricks': layer_bricks, 'outlines': layer_outlines, 'blobs': layer_blobs, 'regions': layer_regions, 'specks': layer_specks}


# ---------------------------------------------------------------------------------------------------- the whole stack
def build_shape_stack(description, wrap=True, shift=0.0):
    """description -> list of shapes in painting order (first = at the back). The first shape is the backdrop (the whole tile).
    shift moves every shape right and down by that many dots (wrapping round): used to prove the tile is seamless."""
    tile = float(description.get('tile', TILE))
    rng = np.random.default_rng(int(description.get('seed', 1)))
    shapes = [{'points': np.array([[0, 0], [tile, 0], [tile, tile], [0, tile]], float), 'colour': int(description.get('backdrop', 0)),
               'convex': True, 'kind': 'backdrop'}]
    for layer in description['layers']:
        LAYER_BUILDERS[layer['type']](layer, shapes, tile, rng)
    if not wrap:
        return shapes
    stack = [shapes[0]]
    for shape in shapes[1:]:
        points = shape['points'] + shift
        if not shape.get('wrap', True):                            # traced regions are cut at the tile edge already: no copies
            entry = {**shape, 'points': points}
            if 'holes' in shape:
                entry['holes'] = [h + shift for h in shape['holes']]
            stack.append(entry)
            continue
        centre = points.mean(0)
        points = points - np.floor(centre / tile) * tile          # bring the shape's middle inside the tile, then add edge copies
        moved = points - shape['points'] - shift                  # how far the middle-fix moved this shape
        for copy in wrapped_copies(points, tile):
            offset = copy[0] - points[0]
            holes = [h + shift + moved[0] + offset for h in shape['holes']] if 'holes' in shape else None
            entry = {**shape, 'points': copy}
            if holes is not None:
                entry['holes'] = holes
            stack.append(entry)
    return stack


def palette_info(description):
    """Palette as arrays: colours (n, 3) sRGB 0..255, roughness (n,)."""
    colours, roughness = [], []
    for entry in description['palette']:
        colours.append(entry[:3])
        roughness.append(entry[3] if len(entry) > 3 else 0.8)
    return np.array(colours, float), np.array(roughness, float)
