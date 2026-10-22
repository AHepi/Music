"""What this does: makes the HEIGHT PICTURES the surface step turns into normal maps and displacement: soft, large, designed
shapes (clods, planks' grain, bunches of straw, courses of brick, cobbles, swell on water) as numpy arrays that repeat without a
seam. Nothing here is a photograph and nothing is finer than about 5 millimetres: the style rule is a few big, clean shapes, not
scan noise. It needs only numpy, so it works inside Blender's own Python and is tested without Blender.

A concrete example: make_height('earth_clods', size=256, seed=3, tile_metres=2.0) gives a 256 x 256 float32 array (zero mean,
white = high) of soft clods about 25 cm across that tiles seamlessly; calibrate_height(h, 30) scales it so the steepest one percent of
its slope tilts a normal by about 30 degrees.
Rows run from the TOP of the picture (row 0 = +V, the top edge); columns run left to right (+U).
"""
import math

import numpy as np

SMALLEST_FEATURE_METRES = 0.005


def _rng(seed):
    return np.random.default_rng(int(seed))


def smoothstep(low, high, x):
    t = np.clip((x - low) / (high - low + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def periodic_noise(size, seed, cycles=6.0, power=2.0):
    """Smooth periodic noise in [-1, 1]; `cycles` is how many ripples across the picture are still present (more = finer)."""
    rng = _rng(seed)
    spectrum = rng.standard_normal((size, size), dtype=np.float32) + 1j * rng.standard_normal((size, size), dtype=np.float32)
    fy = np.fft.fftfreq(size)[:, None] * size
    fx = np.fft.fftfreq(size)[None, :] * size
    k = np.sqrt(fx * fx + fy * fy) / max(cycles, 0.5)
    spectrum *= np.exp(-(k ** power)).astype(np.float32)
    spectrum[0, 0] = 0
    noise = np.real(np.fft.ifft2(spectrum)).astype(np.float32)
    return noise / (np.abs(noise).max() + 1e-9)


def blur(array, pixels):
    """A wrap-around gaussian blur (so a tile stays seamless), by the Fourier route. pixels = the gaussian's sigma."""
    if pixels <= 0:
        return array.astype(np.float32)
    size_y, size_x = array.shape
    fy = np.fft.fftfreq(size_y)[:, None]
    fx = np.fft.fftfreq(size_x)[None, :]
    kernel = np.exp(-(fx * fx + fy * fy) * (2.0 * math.pi ** 2) * (pixels ** 2)).astype(np.float32)
    return np.real(np.fft.ifft2(np.fft.fft2(array) * kernel)).astype(np.float32)


def worley(size, cells, seed, jitter=0.9, vectors=False):
    """Seamless cellular pattern: one jittered point in each of cells x cells squares. Returns (f1, f2, cell id) in units of one cell
    (f1 = distance to the nearest point, f2 = to the second nearest); f2 - f1 is small near the borders between cells.
    With vectors=True it also returns (dx, dy): the way from the pixel to its nearest point, in cell units."""
    rng = _rng(seed)
    cells = max(2, int(cells))
    points = (rng.random((cells, cells, 2), dtype=np.float32) - 0.5) * jitter + 0.5          # (row, col) -> (x, y) inside the cell
    coordinate = (np.arange(size, dtype=np.float32) + 0.5) / size * cells
    row_cell = np.floor(coordinate).astype(np.int64)
    best1 = np.full((size, size), 1e9, np.float32)
    best2 = np.full((size, size), 1e9, np.float32)
    best_id = np.zeros((size, size), np.int64)
    best_dx = np.zeros((size, size), np.float32)
    best_dy = np.zeros((size, size), np.float32)
    px = coordinate[None, :]
    py = coordinate[:, None]
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rows = (row_cell + dr)
            cols = (row_cell + dc)
            wrapped_rows = rows % cells
            wrapped_cols = cols % cells
            # the point's position in unwrapped coordinates (so the distance is measured across the picture edge correctly)
            qx = points[wrapped_rows[:, None], wrapped_cols[None, :], 0] + cols[None, :]
            qy = points[wrapped_rows[:, None], wrapped_cols[None, :], 1] + rows[:, None]
            distance = np.sqrt((px - qx) ** 2 + (py - qy) ** 2)
            ident = wrapped_rows[:, None] * cells + wrapped_cols[None, :]
            closer = distance < best1
            best2 = np.where(closer, best1, np.minimum(best2, distance))
            best_id = np.where(closer, ident, best_id)
            if vectors:
                best_dx = np.where(closer, qx - px, best_dx)
                best_dy = np.where(closer, qy - py, best_dy)
            best1 = np.where(closer, distance, best1)
    if vectors:
        return best1, best2, best_id, best_dx, best_dy
    return best1, best2, best_id


def cell_values(ident, seed, low=0.0, high=1.0):
    """A repeatable random number in [low, high] for each cell id (an array of ids in, an array of numbers out)."""
    rng = _rng(seed + 7919)
    table = rng.random(int(ident.max()) + 1).astype(np.float32)
    return low + (high - low) * table[ident]


def _cycles(tile_metres, feature_metres):
    return max(2.0, tile_metres / feature_metres)


def _normalise(h):
    h = h.astype(np.float32)
    h = h - h.mean()
    peak = np.abs(h).max()
    return h / peak if peak > 0 else h


# ------------------------------------------------------------------ the recipes (size, seed, tile_metres) -> float32 (size, size)
def soft_noise(size, seed, tile_metres=1.0):
    return _normalise(periodic_noise(size, seed, _cycles(tile_metres, 0.2)) + 0.4 * periodic_noise(size, seed + 1, _cycles(tile_metres, 0.08)))


def earth_clods(size, seed, tile_metres=2.0):
    f1, f2, ident = worley(size, int(_cycles(tile_metres, 0.28)), seed)
    clods = 1.0 - smoothstep(0.1, 0.75, f1)
    clods = clods * cell_values(ident, seed, 0.6, 1.0)
    return _normalise(blur(clods, size / 256.0) + 0.5 * periodic_noise(size, seed + 2, _cycles(tile_metres, 0.6)))


def cracked_earth(size, seed, tile_metres=2.0):
    f1, f2, ident = worley(size, int(_cycles(tile_metres, 0.4)), seed)
    edge = f2 - f1
    crack = 1.0 - smoothstep(0.0, 0.08, edge)
    plates = cell_values(ident, seed, 0.0, 0.25)
    return _normalise(blur(plates - 1.2 * crack, size / 400.0) + 0.3 * periodic_noise(size, seed + 3, _cycles(tile_metres, 0.5)))


def planks_grain(size, seed, tile_metres=1.0):
    """Grain along u (left to right): wavy grooves 1 to 2 cm apart, a few soft knots-free swells and two thin checks."""
    rng = _rng(seed)
    x = (np.arange(size) + 0.5) / size
    y = (np.arange(size) + 0.5) / size
    X, Y = np.meshgrid(x, y)
    h = np.zeros((size, size), np.float32)
    lines = max(8, int(tile_metres / 0.02))
    for k in range(lines):
        y0 = (k + rng.uniform(0.1, 0.9)) / lines
        amp = rng.uniform(0.003, 0.012)
        wobble = amp * np.sin(2 * math.pi * int(rng.integers(1, 3)) * X + rng.uniform(0, 6.28)) + 0.3 * amp * np.sin(2 * math.pi * int(rng.integers(2, 5)) * X + rng.uniform(0, 6.28))
        distance = np.abs(Y - (y0 + wobble))
        distance = np.minimum(distance, 1 - distance)
        visible = np.clip(0.5 + 0.9 * np.sin(2 * math.pi * int(rng.integers(1, 4)) * X + rng.uniform(0, 6.28)), 0, 1) ** 1.4
        h -= (rng.uniform(0.5, 1.0) * visible * np.exp(-(distance / (0.004 + 0.001 * (tile_metres - 0.5))) ** 2)).astype(np.float32)
    for k in range(2):
        y0, x0, length = rng.uniform(0.15, 0.85), rng.uniform(0, 1), rng.uniform(0.18, 0.4)
        along = np.clip(((X - x0) % 1.0) / length, 0, 1)
        inside = (((X - x0) % 1.0) < length).astype(np.float32)
        distance = np.abs(Y - (y0 + 0.004 * np.sin(2 * math.pi * 2 * X + rng.uniform(0, 6.28))))
        distance = np.minimum(distance, 1 - distance)
        h -= (1.2 * inside * np.exp(-(distance / 0.004) ** 2) * np.sin(math.pi * np.clip(along, 0.02, 0.98)) ** 0.5).astype(np.float32)
    return _normalise(h + 0.45 * periodic_noise(size, seed + 11, 3.0))


def log_bark(size, seed, tile_metres=1.0):
    """Deep ridges running down (along v): ragged plates of bark with a groove between them."""
    columns = max(5, int(tile_metres / 0.06))
    f1, f2, ident = worley(size, columns, seed)
    squashed = periodic_noise(size, seed + 1, _cycles(tile_metres, 0.05))
    # stretch the noise along v by sampling a coarse picture along rows
    ridge = np.abs(np.sin(math.pi * columns * (np.arange(size)[None, :] + 0.5) / size + 2.0 * periodic_noise(size, seed + 2, 4.0)))
    return _normalise(0.8 * ridge + 0.4 * cell_values(ident, seed, 0, 1) - 0.8 * (1.0 - smoothstep(0.0, 0.08, f2 - f1)) + 0.15 * squashed)


def plaster_blotch(size, seed, tile_metres=1.5):
    rng = _rng(seed)
    h = periodic_noise(size, seed, _cycles(tile_metres, 0.5)) + 0.5 * periodic_noise(size, seed + 1, _cycles(tile_metres, 0.2))
    x = (np.arange(size) + 0.5) / size
    X, Y = np.meshgrid(x, x)
    for _ in range(3):
        cx, cy, radius = rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0.1, 0.2)
        dx = np.minimum(np.abs(X - cx), 1 - np.abs(X - cx))
        dy = np.minimum(np.abs(Y - cy), 1 - np.abs(Y - cy))
        ring = np.exp(-((np.sqrt(dx * dx + dy * dy) - radius) / 0.02) ** 2)
        h += 0.35 * ring.astype(np.float32)
    return _normalise(h)


def stone_blocks(size, seed, tile_metres=1.5):
    """Rough fitted stones: irregular cells, each its own height, a dark joint between them, softly rounded."""
    f1, f2, ident = worley(size, int(_cycles(tile_metres, 0.32)), seed, jitter=0.8)
    joint = 1.0 - smoothstep(0.0, 0.07, f2 - f1)
    dome = 1.0 - smoothstep(0.2, 0.9, f1)
    return _normalise(blur(cell_values(ident, seed, 0.0, 0.5) + 0.5 * dome - 1.0 * joint, size / 300.0) + 0.2 * periodic_noise(size, seed + 4, _cycles(tile_metres, 0.2)))


def brick_courses(size, seed, tile_metres=1.5):
    rng = _rng(seed)
    rows = max(2, int(round(tile_metres / 0.075)))
    per_row = max(2, int(round(tile_metres / 0.225)))
    v = (np.arange(size) + 0.5) / size * rows
    u = (np.arange(size) + 0.5) / size * per_row
    row_index = np.floor(v).astype(int)
    h = np.zeros((size, size), np.float32)
    shift = np.where(row_index % 2 == 0, 0.0, 0.5)
    uu = u[None, :] + shift[:, None]
    brick_index = np.floor(uu).astype(int) % per_row
    heights = rng.random((rows, per_row)).astype(np.float32)
    h += 0.35 * heights[row_index[:, None] % rows, brick_index]
    within_v = v - np.floor(v)
    within_u = uu - np.floor(uu)
    groove = (within_v[:, None] < 0.14) | (within_v[:, None] > 0.86) | (within_u < 0.045) | (within_u > 0.955)
    h = np.where(groove, -0.5, h + 0.4)
    return _normalise(blur(h.astype(np.float32), size / 350.0) + 0.12 * periodic_noise(size, seed + 5, _cycles(tile_metres, 0.1)))


def cobbles(size, seed, tile_metres=1.5):
    f1, f2, ident = worley(size, int(_cycles(tile_metres, 0.2)), seed, jitter=0.75)
    radius = 0.75 + 0.15 * cell_values(ident, seed, -1, 1)
    dome = np.sqrt(np.clip(1.0 - (f1 / radius) ** 2, 0.0, 1.0))
    joint = 1.0 - smoothstep(0.0, 0.1, f2 - f1)
    return _normalise(blur(0.8 * dome + 0.2 * cell_values(ident, seed + 3, 0, 1) - 0.6 * joint, size / 300.0))


def gravel_bits(size, seed, tile_metres=1.5):
    f1, f2, ident = worley(size, int(min(_cycles(tile_metres, 0.05), size / 6)), seed, jitter=0.9)
    dome = np.sqrt(np.clip(1.0 - (f1 / 0.8) ** 2, 0.0, 1.0))
    return _normalise(blur(dome * cell_values(ident, seed, 0.4, 1.0), size / 500.0) + 0.25 * periodic_noise(size, seed + 6, _cycles(tile_metres, 0.4)))


def sand_ripples(size, seed, tile_metres=2.0):
    warp = periodic_noise(size, seed, _cycles(tile_metres, 0.8))
    x = (np.arange(size) + 0.5) / size
    X, Y = np.meshgrid(x, x)
    ripples = np.sin(2 * math.pi * (round(tile_metres / 0.14) * Y + 0.7 * warp))
    return _normalise(0.7 * ripples + 0.4 * periodic_noise(size, seed + 1, _cycles(tile_metres, 0.3)))


def thatch_bunches(size, seed, tile_metres=1.5):
    """Bunches of straw about 12 cm wide running down the slope (along v), tied in bands every 30 cm, each bunch its own height."""
    rng = _rng(seed)
    bunches = max(4, int(tile_metres / 0.12))
    bands = max(2, int(tile_metres / 0.3))
    u = (np.arange(size) + 0.5) / size
    v = (np.arange(size) + 0.5) / size
    wobble = 0.15 * periodic_noise(size, seed + 1, 3.0) / bunches
    U = u[None, :] + wobble
    index = np.floor(U * bunches).astype(int) % bunches
    within = (U * bunches) - np.floor(U * bunches)
    height = rng.random(bunches).astype(np.float32)
    ridge = np.sin(math.pi * np.clip(within, 0, 1)) ** 0.8
    band = 0.25 * np.sin(2 * math.pi * bands * v[:, None] + 2.0 * periodic_noise(size, seed + 2, 2.0)[:, :1]) ** 2
    return _normalise(0.7 * ridge * (0.6 + 0.8 * height[index]) + band + 0.15 * periodic_noise(size, seed + 3, _cycles(tile_metres, 0.1)))


def shingle_rows(size, seed, tile_metres=1.0):
    rng = _rng(seed)
    rows = max(3, int(tile_metres / 0.1))
    per_row = max(3, int(tile_metres / 0.12))
    v = (np.arange(size) + 0.5) / size * rows
    u = (np.arange(size) + 0.5) / size * per_row
    row_index = np.floor(v).astype(int)
    uu = u[None, :] + np.where(row_index % 2 == 0, 0.0, 0.5)[:, None]
    shingle = np.floor(uu).astype(int) % per_row
    amount = rng.random((rows, per_row)).astype(np.float32)
    within_v = (v - np.floor(v))[:, None]
    within_u = uu - np.floor(uu)
    slope = within_v * 0.9 + 0.3 * amount[row_index[:, None] % rows, shingle]       # rises toward the lower edge, then drops to the next row
    gap = (within_u < 0.04) | (within_u > 0.96)
    return _normalise(blur(np.where(gap, -0.2, slope).astype(np.float32), size / 400.0) + 0.1 * periodic_noise(size, seed + 4, _cycles(tile_metres, 0.12)))


def tile_rows(size, seed, tile_metres=1.0):
    rng = _rng(seed)
    rows = max(3, int(tile_metres / 0.2))
    per_row = max(3, int(tile_metres / 0.15))
    v = (np.arange(size) + 0.5) / size * rows
    u = (np.arange(size) + 0.5) / size * per_row
    within_u = (u - np.floor(u))[None, :]
    barrel = np.sin(math.pi * within_u) ** 0.7                            # a half-round tile across its width
    within_v = (v - np.floor(v))[:, None]
    overlap = within_v * 0.5
    tile_index = (np.floor(v).astype(int)[:, None] * 7 + np.floor(u).astype(int)[None, :]) % 97
    random = rng.random(97).astype(np.float32)
    return _normalise(blur((barrel * 0.8 + overlap + 0.2 * random[tile_index]).astype(np.float32), size / 500.0))


def iron_pits(size, seed, tile_metres=0.5):
    f1, f2, ident = worley(size, int(_cycles(tile_metres, 0.04)), seed, jitter=1.0)
    pits = (cell_values(ident, seed, 0, 1) > 0.78).astype(np.float32) * (1.0 - smoothstep(0.0, 0.5, f1))
    return _normalise(0.4 * periodic_noise(size, seed + 1, _cycles(tile_metres, 0.12)) - 0.9 * pits)


def straw_strands(size, seed, tile_metres=1.0):
    rng = _rng(seed)
    h = np.zeros((size, size), np.float32)
    strands = 260
    for _ in range(strands):
        x0, y0 = rng.random(2) * size
        angle = rng.uniform(0, math.pi)
        length = rng.uniform(0.08, 0.25) * size
        t = np.linspace(0, length, int(length) + 1)
        xs = (x0 + t * math.cos(angle)).astype(int) % size
        ys = (y0 + t * math.sin(angle)).astype(int) % size
        np.add.at(h, (ys, xs), rng.uniform(0.5, 1.0))
    return _normalise(blur(h, max(1.5, size / 220.0)))


def fabric_weave(size, seed, tile_metres=0.5):
    period = max(0.012, 0.02)
    count = max(4, int(round(tile_metres / period)))
    x = (np.arange(size) + 0.5) / size
    X, Y = np.meshgrid(x, x)
    weave = np.sin(2 * math.pi * count * X) * np.sin(2 * math.pi * count * Y)
    return _normalise(0.6 * weave + 0.5 * periodic_noise(size, seed, _cycles(tile_metres, 0.12)))


def wave_swell(size, seed, tile_metres=4.0):
    rng = _rng(seed)
    x = (np.arange(size) + 0.5) / size
    X, Y = np.meshgrid(x, x)
    h = np.zeros((size, size), np.float32)
    for _ in range(5):
        a, b = int(rng.integers(-3, 4)), int(rng.integers(-3, 4))
        if a == 0 and b == 0:
            a = 1
        h += (rng.uniform(0.4, 1.0) * np.sin(2 * math.pi * (a * X + b * Y) + rng.uniform(0, 6.28))).astype(np.float32)
    return _normalise(h + 0.2 * periodic_noise(size, seed + 1, 5.0))


def rock_facets(size, seed, tile_metres=2.0):
    """Angular rock: each cell is a tilted flat face, with sharp breaks between them."""
    rng = _rng(seed)
    cells = int(_cycles(tile_metres, 0.4))
    f1, f2, ident, dx, dy = worley(size, cells, seed, jitter=1.0, vectors=True)
    ax = cell_values(ident, seed + 1, -1, 1)
    ay = cell_values(ident, seed + 2, -1, 1)
    return _normalise(-ax * dx - ay * dy + cell_values(ident, seed + 3, 0.0, 0.6) + 0.2 * periodic_noise(size, seed + 4, _cycles(tile_metres, 0.25)))


def rope_twist(size, seed, tile_metres=0.5):
    twists = max(4, int(tile_metres / 0.05))
    x = (np.arange(size) + 0.5) / size
    X, Y = np.meshgrid(x, x)
    return _normalise(np.sin(2 * math.pi * (twists * X + 0.6 * twists * Y)) + 0.3 * periodic_noise(size, seed, _cycles(tile_metres, 0.1)))


RECIPES = {
    'soft_noise': soft_noise, 'earth_clods': earth_clods, 'cracked_earth': cracked_earth, 'planks_grain': planks_grain, 'log_bark': log_bark,
    'plaster_blotch': plaster_blotch, 'stone_blocks': stone_blocks, 'brick_courses': brick_courses, 'cobbles': cobbles, 'gravel_bits': gravel_bits,
    'sand_ripples': sand_ripples, 'thatch_bunches': thatch_bunches, 'shingle_rows': shingle_rows, 'tile_rows': tile_rows, 'iron_pits': iron_pits,
    'straw_strands': straw_strands, 'fabric_weave': fabric_weave, 'wave_swell': wave_swell, 'rock_facets': rock_facets, 'rope_twist': rope_twist,
}


def make_height(recipe, size, seed, tile_metres):
    """The height picture of one recipe: float32 (size, size), zero mean, within [-1, 1]; seamless."""
    if recipe not in RECIPES:
        raise KeyError(f'no height recipe "{recipe}" (known: {", ".join(RECIPES)})')
    return RECIPES[recipe](int(size), int(seed), float(tile_metres))


def calibrate_height(h, tilt_degrees=30.0):
    """Scales a height picture (in pixel units) so the steepest one percent of its slope tilts the surface by about tilt_degrees.
    After this, height_to_normal(h, strength=1.0) gives the right amount of tilt and strength 2.0 doubles the slope."""
    h = np.asarray(h, np.float32)
    gy, gx = np.gradient(h)
    magnitude = np.sqrt(gx * gx + gy * gy)
    steep = float(np.percentile(magnitude, 99.0)) + 1e-9
    return h * (math.tan(math.radians(tilt_degrees)) / steep)


def normalise_unit(h):
    """The height picture stretched to 0..1 (what the Displacement node reads, with mid level 0.5 taken from the average)."""
    h = np.asarray(h, np.float32)
    low, high = float(h.min()), float(h.max())
    return (h - low) / (high - low + 1e-12)


def is_seamless(h, tolerance=0.15):
    """True when the picture repeats without a seam: the jump across the picture edge is no bigger than the biggest jump anywhere
    inside the picture (a sawtooth pattern has big jumps inside it too, and is still seamless)."""
    h = np.asarray(h, np.float32)
    inside_u = np.abs(np.diff(h, axis=1)).mean(axis=0)
    inside_v = np.abs(np.diff(h, axis=0)).mean(axis=1)
    edge_u = float(np.abs(h[:, 0] - h[:, -1]).mean())
    edge_v = float(np.abs(h[0, :] - h[-1, :]).mean())
    return bool(edge_u <= inside_u.max() * (1.0 + tolerance) + 1e-6 and edge_v <= inside_v.max() * (1.0 + tolerance) + 1e-6)
