# What this does (plain words): the "painter's list maker" for the GRAVEL generator. It reads a gravel description (a small JSON file: a soil recipe,
# a stone recipe, optional placed stones, optional traced patches) and turns it into ONE back-to-front list of flat coloured shapes
# (each shape = a polygon in tile dots, y pointing down, plus a colour). The Blender part (gravel_generator.py) then builds those shapes as real flat
# geometry and photographs them from above. This file is plain numpy (no Blender, no pictures): it only ever sees the description.
# The shapes, in painting order: 1 the ground colour (a square), 2 soil lumps (small round brown pieces and tiny dark and light specks),
# 3 stones (each stone: a soft shadow on the soil, a dark rim, the stone body, a lit top face, a shaded bottom face, flaky light/dark patches),
# 4 placed stones (the same stone made from a short list of numbers), 5 traced patches (flat coloured areas written out as outlines).
# Everything is drawn again one tile to the left/right/up/down where it crosses the tile edge (done in the Blender part), so the tile repeats.
import math

import numpy as np


# ----------------------------------------------------------------------------------------------------- small polygon tools
def convex_hull(points):
    """Convex hull of a few points (monotone chain), counter-clockwise on a y-up page. Needs 3 or more points."""
    pts = sorted(map(tuple, np.asarray(points, np.float64).tolist()))
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def clip_half_plane(poly, normal, offset):
    """Keep the part of a polygon where normal . point >= offset (Sutherland-Hodgman, one edge). Returns an array (may be empty)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da, db = float(np.dot(normal, a)) - offset, float(np.dot(normal, b)) - offset
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append(a + t * (b - a))
    return np.array(out) if len(out) >= 3 else np.zeros((0, 2))


def clip_convex(subject, clip):
    """Intersection of two convex polygons (clip by every edge of the second). Works for either winding."""
    if len(subject) < 3 or len(clip) < 3:
        return np.zeros((0, 2))
    area = 0.5 * np.sum(clip[:, 0] * np.roll(clip[:, 1], -1) - np.roll(clip[:, 0], -1) * clip[:, 1])
    sign = 1.0 if area > 0 else -1.0
    out = subject
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        edge = b - a
        normal = sign * np.array([-edge[1], edge[0]])        # points to the inside for the winding used
        out = clip_half_plane(out, normal, float(np.dot(normal, a)))
        if len(out) < 3:
            return np.zeros((0, 2))
    return out


def polygon_area(poly):
    return 0.5 * abs(np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1]))


def blob_polygon(rng, cx, cy, radius, sides, jitter, aspect=1.0, angle=0.0):
    """A random convex lump: `sides` corners at uneven angles, each at a radius of radius x (1 +- jitter), squashed by `aspect`, turned by `angle`."""
    sides = max(3, int(sides))
    base = np.sort(rng.uniform(0, 2 * math.pi, sides) * 0.0 + (np.arange(sides) + rng.uniform(-0.32, 0.32, sides)) * (2 * math.pi / sides) + rng.uniform(0, 2 * math.pi))
    radii = radius * (1.0 + jitter * rng.uniform(-1, 1, sides))
    x, y = radii * np.cos(base), radii * np.sin(base) * aspect
    ca, sa = math.cos(angle), math.sin(angle)
    pts = np.stack([cx + x * ca - y * sa, cy + x * sa + y * ca], axis=1)
    hull = convex_hull(pts)
    return hull if len(hull) >= 3 else pts


def rough_outline(rng, hull, amount, step):
    """Chips an outline: every edge is cut into pieces about `step` dots long and each new corner is pushed sideways by up to `amount` dots at random
    (the stones of the reference have chipped, uneven edges). The result is no longer exactly convex; that is fine for painting."""
    if amount <= 0:
        return hull
    centre = hull.mean(axis=0)
    out = []
    n = len(hull)
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        pieces = max(1, int(round(np.linalg.norm(b - a) / step)))
        for k in range(pieces):
            t = k / pieces
            point = a + (b - a) * t
            if k > 0:
                direction = point - centre
                direction = direction / (np.linalg.norm(direction) + 1e-9)
                point = point + direction * rng.uniform(-amount, amount)
            out.append(point)
    return np.array(out)


# ----------------------------------------------------------------------------------------------------- placement (blue-noise-like spacing, wrapping)
class WrapGrid:
    """Remembers where lumps are, so a new one can be refused when it would sit too close (distances wrap around the tile edge)."""

    def __init__(self, tile, cell=64.0):
        self.tile = float(tile)
        self.n = max(1, int(tile // cell))
        self.cell = self.tile / self.n
        self.cells = [[] for _ in range(self.n * self.n)]

    def _index(self, x, y):
        return (int(y // self.cell) % self.n) * self.n + int(x // self.cell) % self.n

    def add(self, x, y, r):
        self.cells[self._index(x, y)].append((x, y, r))

    def fits(self, x, y, r, spacing, reach):
        span = int(math.ceil(reach / self.cell))
        cx, cy = int(x // self.cell), int(y // self.cell)
        for dy in range(-span, span + 1):
            for dx in range(-span, span + 1):
                for (px, py, pr) in self.cells[((cy + dy) % self.n) * self.n + (cx + dx) % self.n]:
                    ddx = abs(px - x)
                    ddx = min(ddx, self.tile - ddx)
                    ddy = abs(py - y)
                    ddy = min(ddy, self.tile - ddy)
                    if ddx * ddx + ddy * ddy < (spacing * (r + pr)) ** 2:
                        return False
        return True


def draw_sizes(rng, low, high, count, shape=1.0):
    """`count` radii between low and high. shape 1 = equal chance per doubling in size (log-uniform); bigger shape = more small ones."""
    u = rng.uniform(0, 1, count) ** shape
    return low * (high / low) ** u


# ----------------------------------------------------------------------------------------------------- colours
def shift_colour(rgb, amount, tint=(1.0, 1.08, 1.22)):
    """Lighten (amount > 0) or darken (amount < 0) an sRGB colour by `amount` brightness steps, with a slight blue lean when lightening."""
    rgb = np.asarray(rgb, np.float64)
    t = np.asarray(tint)
    return np.clip(rgb + amount * (t if amount > 0 else np.ones(3)), 0, 255)


def pick_tone(rng, tones, weights):
    w = np.asarray(weights, np.float64)
    w = w / w.sum()
    return np.asarray(tones[int(rng.choice(len(tones), p=w))], np.float64)


# ----------------------------------------------------------------------------------------------------- one stone
def stone_shapes(rng, cx, cy, radius, aspect, angle, sides, jitter, base_rgb, stone_block, rusty, mottle_rgb, light):
    """The shapes (back to front) that make up ONE stone: shadow on the soil, dark rim, body, lit face, shaded face, extra facets, flaky patches.
    light = (lx, ly): the direction the light comes FROM, as a unit vector in picture dots (y down; (0, -1) = from the top)."""
    shapes = []
    tint = tuple(stone_block.get('tint', (1.0, 1.08, 1.22)))
    hull = blob_polygon(rng, cx, cy, radius, sides, jitter, aspect, angle)         # the plain convex stone (used for clipping)
    body = rough_outline(rng, hull, stone_block.get('chip', 0.07) * radius, max(stone_block.get('chip_step', 0.45) * radius, 2.5))
    centre = np.array([cx, cy])
    lx, ly = light
    away = np.array([-lx, -ly])
    rim_w = stone_block.get('rim', 0.8)
    shadow_w = stone_block.get('shadow', 6.0) * (0.5 + 0.5 * min(radius / 20.0, 1.6))
    if shadow_w > 0.5 and radius >= stone_block.get('shadow_min_radius', 5.0):
        shadow_rgb = np.asarray(stone_block.get('shadow_rgb', [34, 24, 18]), np.float64)
        wide = centre + (hull - centre) * ((radius + shadow_w) / radius) + away * shadow_w * 0.55
        shapes.append((wide, shadow_rgb))
        narrow = centre + (hull - centre) * ((radius + shadow_w * 0.5) / radius) + away * shadow_w * 0.3
        shapes.append((narrow, shadow_rgb * 0.62))
    if rim_w > 0.2:
        grown = centre + (body - centre) * ((radius + rim_w) / radius) + away * rim_w * 0.4
        shapes.append((grown, np.asarray(stone_block.get('rim_rgb', None) if stone_block.get('rim_rgb') else base_rgb * 0.45, np.float64)))
    shapes.append((body, base_rgb))
    n_vec = np.array([lx, ly]) / (np.linalg.norm([lx, ly]) + 1e-9)       # points toward the light
    lit_cut = rng.uniform(-0.45, 0.05) * radius
    lit = clip_half_plane(body, n_vec, float(np.dot(n_vec, centre)) + lit_cut)
    if len(lit) >= 3 and polygon_area(lit) > 6:
        shapes.append((lit, shift_colour(base_rgb, rng.uniform(*stone_block.get('lit_shift', [10, 26])), tint)))
    dark_cut = rng.uniform(0.15, 0.6) * radius
    shade = clip_half_plane(body, -n_vec, float(np.dot(-n_vec, centre)) + dark_cut)
    if len(shade) >= 3 and polygon_area(shade) > 6:
        shapes.append((shade, shift_colour(base_rgb, -rng.uniform(*stone_block.get('shade_shift', [5, 12])), tint)))
    # extra facets on bigger stones: more flat slices at other angles with their own tone (a block of rock has several faces)
    if radius >= stone_block.get('facet_min_radius', 14.0):
        for _ in range(int(stone_block.get('facets', 2))):
            theta = rng.uniform(0, 2 * math.pi)
            nrm = np.array([math.cos(theta), math.sin(theta)])
            piece = clip_half_plane(body, nrm, float(np.dot(nrm, centre)) + rng.uniform(0.0, 0.55) * radius)
            if len(piece) >= 3 and polygon_area(piece) > 12:
                shapes.append((piece, shift_colour(base_rgb, rng.uniform(-9, 14), tint)))
    # flaky patches: lighter or darker angular spots, clipped to the plain convex stone
    count = int(round(stone_block.get('mottle_per_radius', 0.25) * radius + rng.uniform(-0.5, 0.5))) if radius >= stone_block.get('mottle_min_radius', 9.0) else 0
    for _ in range(max(count, 0)):
        patch_radius = radius * rng.uniform(stone_block.get('mottle_size', [0.09, 0.3])[0], stone_block.get('mottle_size', [0.09, 0.3])[1])
        offset = rng.normal(0, 0.45 * radius, 2)
        spot = blob_polygon(rng, cx + offset[0], cy + offset[1], patch_radius, rng.integers(5, 9), 0.5, rng.uniform(0.5, 1.0), rng.uniform(0, 3.14))
        spot = clip_convex(spot, hull)
        if len(spot) < 3 or polygon_area(spot) < 5:
            continue
        if rusty and rng.uniform() < 0.7:
            colour = pick_tone(rng, mottle_rgb['grey'], [1] * len(mottle_rgb['grey'])) if rng.uniform() < 0.8 else shift_colour(base_rgb, rng.uniform(15, 30), tint)
        else:
            sign = 1.0 if rng.uniform() < stone_block.get('mottle_light_share', 0.55) else -1.0
            colour = shift_colour(base_rgb, sign * rng.uniform(*stone_block.get('mottle_shift', [8, 24])), tint)
        shapes.append((spot, colour))
    return shapes


# ----------------------------------------------------------------------------------------------------- where is soil? (from the description's own traced patches)
def is_soil_colour(rgb):
    """True for orange-brown colours (red clearly above blue)."""
    return (float(rgb[0]) - float(rgb[2])) >= 14.0


class SoilMask:
    """A coarse grid saying 'the traced patches paint soil colour here'. Built only from the description's own patch polygons (the generator never
    sees the reference). Used so that invented small soil lumps and pebbles are put on the soil patches, not on top of the big traced stones."""

    def __init__(self, shapes, tile, step=3.0, default=False):
        self.tile, self.step = float(tile), float(step)
        self.n = int(math.ceil(tile / step))
        grid = np.full((self.n, self.n), bool(default))     # default True = soil everywhere unless a traced stone patch covers it
        xs = (np.arange(self.n) + 0.5) * self.step
        for pts, rgb in shapes:
            pts = np.asarray(pts, np.float64)
            soil = is_soil_colour(rgb)
            low = np.maximum(np.floor(pts.min(axis=0) / self.step).astype(int), 0)
            high = np.minimum(np.ceil(pts.max(axis=0) / self.step).astype(int) + 1, self.n)
            if high[0] <= low[0] or high[1] <= low[1]:
                continue
            gx, gy = np.meshgrid(xs[low[0]:high[0]], xs[low[1]:high[1]])
            inside = np.zeros(gx.shape, bool)
            a, b = pts, np.roll(pts, -1, axis=0)
            for (x1, y1), (x2, y2) in zip(a, b):           # even-odd crossing test, one edge at a time
                if y1 == y2:
                    continue
                crosses = ((y1 <= gy) != (y2 <= gy)) & (gx < (x2 - x1) * (gy - y1) / (y2 - y1) + x1)
                inside ^= crosses
            grid[low[1]:high[1], low[0]:high[0]][inside] = soil
        self.grid = grid

    def soil_at(self, x, y):
        return bool(self.grid[int(y // self.step) % self.n, int(x // self.step) % self.n])


# ----------------------------------------------------------------------------------------------------- soil
def soil_shapes(block, tile, rng, mask=None):
    shapes = []
    for layer in block.get('layers', []):
        radii = draw_sizes(rng, layer['radius'][0], layer['radius'][1], int(layer['count']), layer.get('shape', 1.0))
        for r in radii:
            x, y = rng.uniform(0, tile, 2)
            if mask is not None and not mask.soil_at(x, y):
                continue
            tone = pick_tone(rng, block['tones'], layer.get('weights', [1] * len(block['tones'])))
            jitter = rng.normal(0, layer.get('jitter_tone', 3.0), 3)
            if block.get('jitter_mode') == 'brightness':
                jitter = np.full(3, jitter[0])
            tone = np.clip(tone + jitter, 0, 255)
            clod = blob_polygon(rng, x, y, r, rng.integers(layer.get('sides', [5, 8])[0], layer.get('sides', [5, 8])[1] + 1), layer.get('jitter', 0.3),
                                rng.uniform(layer.get('aspect', [0.7, 1.0])[0], layer.get('aspect', [0.7, 1.0])[1]), rng.uniform(0, 3.14))
            shapes.append((clod, tone))
            if r >= layer.get('top_min_radius', 4.5) and rng.uniform() < layer.get('top_share', 0.6):          # a lighter top on the clod, toward the light
                lit = clip_half_plane(clod, np.array([0.0, -1.0]), float(clod[:, 1].mean()) - rng.uniform(0.0, 0.35) * r)
                if len(lit) >= 3 and polygon_area(lit) > 3:
                    shapes.append((lit, shift_colour(tone, rng.uniform(*layer.get('top_shift', [10, 30])), (1.0, 0.95, 0.8))))
    for layer in block.get('specks', []):
        radii = draw_sizes(rng, layer['radius'][0], layer['radius'][1], int(layer['count']), layer.get('shape', 1.0))
        for r in radii:
            x, y = rng.uniform(0, tile, 2)
            if mask is not None and not mask.soil_at(x, y):
                continue
            tone = pick_tone(rng, layer['tones'], layer.get('weights', [1] * len(layer['tones'])))
            shapes.append((blob_polygon(rng, x, y, r, rng.integers(4, 7), 0.3, rng.uniform(0.7, 1.0), rng.uniform(0, 3.14)), tone))
    return shapes


# ----------------------------------------------------------------------------------------------------- stones
def make_stone_list(block, tile, rng, mask=None):
    """Statistical stones: for every size class a number of stones placed with blue-noise-like spacing, biggest class first so the small ones fill the gaps.
    Returns a list of dicts (x, y, radius, aspect, angle, sides, jitter, tone index/rgb, rusty, class)."""
    grid = WrapGrid(tile)
    rmax = max(c['radius'][1] for c in block['classes']) * 1.4
    stones = []
    order = sorted(range(len(block['classes'])), key=lambda i: -block['classes'][i]['radius'][1])
    for ci in order:
        cls = block['classes'][ci]
        wanted = int(cls['count'])
        radii = draw_sizes(rng, cls['radius'][0], cls['radius'][1], wanted, cls.get('shape', 1.0))
        radii = np.sort(radii)[::-1]
        placed = 0
        spacing = cls.get('spacing', 0.85)
        for r in radii:
            for _try in range(int(cls.get('tries', 14))):
                x, y = rng.uniform(0, tile, 2)
                if cls.get('only_on') == 'soil' and mask is not None and not mask.soil_at(x, y):
                    continue
                if grid.fits(x, y, r, spacing, r + rmax):
                    grid.add(x, y, r)
                    aspect = rng.uniform(*cls.get('aspect', [0.6, 1.0]))
                    stones.append(dict(x=float(x), y=float(y), radius=float(r), aspect=float(aspect), angle=float(rng.uniform(0, math.pi)),
                                       sides=int(rng.integers(cls.get('sides', [4, 6])[0], cls.get('sides', [4, 6])[1] + 1)), jitter=cls.get('jitter', 0.18),
                                       cls=ci, rusty=bool(rng.uniform() < cls.get('rust', 0.1)),
                                       tone=int(rng.choice(len(block['tones']), p=np.asarray(cls['weights']) / np.sum(cls['weights'])))))
                    placed += 1
                    break
    return stones


def stones_to_shapes(stones, block, rng, light):
    shapes = []
    tones = block['tones']
    rust_tones = block.get('rust_tones', [[96, 63, 42], [118, 81, 54]])
    mottle = {'grey': block.get('rust_grey', [[83, 93, 98], [111, 117, 116], [87, 84, 80]])}
    for s in sorted(stones, key=lambda s: s['radius']):                    # small first, big on top
        base = np.asarray(rust_tones[int(rng.integers(len(rust_tones)))] if s['rusty'] else tones[s['tone']], np.float64)
        jitter = rng.normal(0, block.get('tone_jitter', 2.5), 3)
        if block.get('jitter_mode') == 'brightness':
            jitter = np.full(3, jitter[0])                  # the same brightness step on red, green and blue: the hue stays
        base = np.clip(base + jitter, 0, 255)
        shapes.extend(stone_shapes(rng, s['x'], s['y'], s['radius'], s['aspect'], s['angle'], s['sides'], s.get('jitter', 0.18), base, block, s['rusty'], mottle, light))
    return shapes


# ----------------------------------------------------------------------------------------------------- traced patches
def decode_patch(entry, palette):
    """[colour index, [x0, y0, dx1, dy1, ...]] -> (points, rgb). Outlines are written as the first corner then small steps."""
    index, numbers = entry
    arr = np.asarray(numbers, np.float64).reshape(-1, 2)
    pts = np.cumsum(arr, axis=0)
    return pts, np.asarray(palette[index], np.float64)


def stamp_shapes(bands, palette, sides=8):
    """Tiny round 'stamps' (discs): description['stamps'] is a list of bands, biggest stamps first; a band is {colour index: [x, y, radius_in_half_dots, ...]}."""
    shapes = []
    angles = np.arange(sides) * (2 * math.pi / sides) + math.pi / sides
    unit = np.stack([np.cos(angles), np.sin(angles)], axis=1)
    for band in bands:
        for colour_index, numbers in band.items():
            rgb = np.asarray(palette[int(colour_index)], np.float64)
            arr = np.asarray(numbers, np.float64).reshape(-1, 3)
            for x, y, r2 in arr:
                r = max(r2 * 0.5, 0.8)
                shapes.append((np.array([x, y]) + unit * r * (1.0 + 0.04 * (sides - 8)), rgb))
    return shapes


def grow_polygon(points, amount):
    """Push a polygon outward from its middle by about `amount` dots (so neighbouring traced patches leave no hairline gap)."""
    if amount <= 0:
        return points
    c = points.mean(axis=0)
    d = points - c
    length = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    return points + d / length * amount


# ----------------------------------------------------------------------------------------------------- the whole list
def make_shape_list(description):
    """The back-to-front list of (polygon, rgb) for the whole tile. description['order'] says in which order the blocks are painted
    (default: ground, soil, stones, placed stones, traced patches). A hybrid that traces the big stones and invents the small ones uses
    ['patches', 'soil', 'stones']."""
    tile = float(description['tile'])
    shapes = []
    palette = description.get('palette', [])
    ground = description.get('ground', [79, 52, 34])
    shapes.append((np.array([[0, 0], [tile, 0], [tile, tile], [0, tile]], np.float64), ground))
    light = tuple(description.get('light', [0.0, -1.0]))
    traced = []
    grow = description.get('grow', 0.0)
    for entry in description.get('patches', []):
        pts, rgb = decode_patch(entry, palette)
        if len(pts) >= 3:
            traced.append((grow_polygon(pts, grow), rgb))
    mask = None
    if description.get('stamp_mask') is not None and traced:
        # invented soil lumps and pebbles are only put where the traced patches say "soil" (default False) or where no traced stone patch lies (default True)
        mask = SoilMask(traced, tile, default=bool(description['stamp_mask'].get('default', False)))
    for name in description.get('order', ['soil', 'stones', 'placed', 'patches', 'stamps']):
        if name == 'soil' and 'soil' in description:
            shapes.extend(soil_shapes(description['soil'], tile, np.random.default_rng(description['soil'].get('seed', 1)), mask))
        elif name == 'stones' and 'stones' in description:
            block = description['stones']
            rng = np.random.default_rng(block.get('seed', 1))
            stones = make_stone_list(block, tile, rng, mask) if block.get('classes') else []
            shapes.extend(stones_to_shapes(stones, block, rng, light))
        elif name == 'placed' and 'placed' in description:
            block = description['placed']
            rng = np.random.default_rng(block.get('seed', 1))
            stones = [dict(x=p[0], y=p[1], radius=p[2], aspect=p[3], angle=p[4], sides=int(p[5]), jitter=block.get('jitter', 0.18), tone=int(p[6]), rusty=bool(p[7]), cls=0)
                      for p in block['list']]
            shapes.extend(stones_to_shapes(stones, block, rng, light))
        elif name == 'patches':
            shapes.extend(traced)
        elif name == 'stamps' and 'stamps' in description:
            shapes.extend(stamp_shapes(description['stamps'], palette))
    return shapes


# ----------------------------------------------------------------------------------------------------- quick plain-numpy preview (no Blender)
def preview(shapes, size=1254, scale=2):
    """Draws the shape list with OpenCV at `scale` times the size, wrapping at the tile edge, then shrinks it. For fast checks only; the real pictures
    are photographed in Blender."""
    import cv2
    tile = size
    big = np.zeros((size * scale, size * scale, 3), np.uint8)
    for pts, rgb in shapes:
        pts = np.asarray(pts, np.float64)
        centre = pts.mean(axis=0)
        pts = pts - tile * np.floor(centre / tile)
        low, high = pts.min(axis=0), pts.max(axis=0)
        colour = tuple(int(round(float(v))) for v in rgb[::-1])
        for ox in (-1, 0, 1):
            if high[0] + ox * tile < 0 or low[0] + ox * tile >= tile:
                continue
            for oy in (-1, 0, 1):
                if high[1] + oy * tile < 0 or low[1] + oy * tile >= tile:
                    continue
                q = ((pts + [ox * tile, oy * tile]) * scale + 0.0).round().astype(np.int32)
                cv2.fillPoly(big, [q], colour, lineType=cv2.LINE_8)
    return cv2.resize(big, (size, size), interpolation=cv2.INTER_AREA)
