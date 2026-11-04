"""
What this file does: smooth random wandering (gradient noise) for many points at once, shared by the store's ground
tools: lumps in mud, patches of grass, the wobble of an edge. The same seed gives the same values everywhere. (A name
starting with '_' keeps it out of the store's list of tools.)

    import _noise
    lumps = _noise.wander(x, y, scale=0.08, seed=3)              # x, y: arrays in metres; about -1 .. 1, lumps about 8 cm
    rough = _noise.wander(x, y, scale=0.08, seed=3, layers=3)    # rougher: finer and finer layers added
    streaks = _noise.wander(along, across, scale=(0.5, 0.01))    # stretched: long streaks along the first measure
"""

import numpy

_TABLES = {}


def _table(seed):
    table = _TABLES.get(seed)
    if table is None:
        rng = numpy.random.RandomState(int(seed) % (2 ** 31 - 1))
        order = rng.permutation(256)
        angles = rng.uniform(0.0, 2.0 * numpy.pi, 256)
        table = (numpy.concatenate([order, order]), numpy.cos(angles), numpy.sin(angles))
        _TABLES[seed] = table
    return table


def gradient(x, y, seed=0):
    """Gradient noise at the points (x, y), in grid units (one lump about every unit): about -1 .. 1, 0 on average."""
    order, gx, gy = _table(seed)
    x = numpy.asarray(x, dtype=numpy.float64)
    y = numpy.asarray(y, dtype=numpy.float64)
    x0, y0 = numpy.floor(x), numpy.floor(y)
    fx, fy = x - x0, y - y0
    xi = x0.astype(numpy.int64) & 255
    yi = y0.astype(numpy.int64) & 255

    def corner(dx, dy):
        h = order[order[(xi + dx) & 255] + ((yi + dy) & 255)]
        return gx[h] * (fx - dx) + gy[h] * (fy - dy)
    u = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    v = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)
    bottom = corner(0, 0) + u * (corner(1, 0) - corner(0, 0))
    top = corner(0, 1) + u * (corner(1, 1) - corner(0, 1))
    return (bottom + v * (top - bottom)) * 1.41


def wander(x, y, scale=1.0, seed=0, layers=1, roughness=0.5):
    """Smooth wandering about -1 .. 1 with features about `scale` metres across (or (scale along x, scale along y) for
    streaks); `layers` adds finer and finer copies, each `roughness` as strong as the one before."""
    sx, sy = (scale, scale) if numpy.isscalar(scale) else scale
    x = numpy.asarray(x, dtype=numpy.float64) / sx
    y = numpy.asarray(y, dtype=numpy.float64) / sy
    total = numpy.zeros(numpy.broadcast(x, y).shape)
    weight, strength, growth = 0.0, 1.0, 1.0
    for layer in range(int(layers)):
        total = total + strength * gradient(x * growth + 31.7 * layer, y * growth - 17.3 * layer, seed + 101 * layer)
        weight += strength
        strength *= roughness
        growth *= 2.03
    return total / weight


def clods(x, y, scale=0.06, seed=0, jitter=1.0):
    """Lumps like broken clods of earth, about `scale` metres across: each a rounded bump with a crease between it and
    its neighbours (0 in the creases to about 1 on top), from scattered centres (the nearest and next-nearest of them)."""
    from scipy.spatial import cKDTree
    x = numpy.asarray(x, dtype=numpy.float64)
    y = numpy.asarray(y, dtype=numpy.float64)
    if not x.size:
        return numpy.zeros(x.shape)
    low = numpy.array([x.min(), y.min()]) - 2.0 * scale
    high = numpy.array([x.max(), y.max()]) + 2.0 * scale
    cells = numpy.maximum(numpy.ceil((high - low) / scale).astype(int), 1)
    rng = numpy.random.default_rng([int(seed) % (2 ** 32), 7])
    grid_x, grid_y = numpy.meshgrid(numpy.arange(cells[0]), numpy.arange(cells[1]), indexing='ij')
    centres = numpy.column_stack([grid_x.ravel(), grid_y.ravel()]).astype(numpy.float64)
    centres = (centres + 0.5 + jitter * (rng.random(centres.shape) - 0.5)) * scale + low
    distance, _ = cKDTree(centres).query(numpy.column_stack([x.ravel(), y.ravel()]), k=2)
    edge = (distance[:, 1] - distance[:, 0]) / scale                     # 0 on the crease between two clods
    top = numpy.clip(edge * 2.2, 0.0, 1.0)
    return (top * (2.0 - top)).reshape(x.shape)
