# What this does (plain words): makes a "mosaic" of flat patches of paint that fill a shape completely, like the reference's brick faces: scatter seed
# points, cut the shape into the cell nearest each seed (a Voronoi picture), bend the cell edges a little with a smooth wobble that is the SAME for two
# cells sharing an edge (so no gaps appear), and give each cell a palette colour. Neighbouring cells get similar tones because the colour is chosen by
# a slowly changing "tone dial" over the picture plus a bit of per-cell chance. Used by sample_description.py (style 'mosaic'). The sampler runs
# inside Blender (numpy only: every cell is a start square cut by straight lines half way to its neighbours).
import math

import numpy as np

def clip_convex(subject, clip):
    """Sutherland-Hodgman: cut a polygon by a convex polygon (counter-clockwise or clockwise, both fine)."""
    area = 0.0
    for i in range(len(clip)):
        x1, y1 = clip[i]
        x2, y2 = clip[(i + 1) % len(clip)]
        area += x1 * y2 - x2 * y1
    sign = 1.0 if area > 0 else -1.0
    output = [tuple(p) for p in subject]
    for i in range(len(clip)):
        if not output:
            break
        a = clip[i]
        b = clip[(i + 1) % len(clip)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        def inside(p):
            return sign * (ex * (p[1] - a[1]) - ey * (p[0] - a[0])) >= 0
        def cross(p, q):
            dpx, dpy = q[0] - p[0], q[1] - p[1]
            denom = ex * dpy - ey * dpx
            if abs(denom) < 1e-12:
                return q
            t = (ey * (p[0] - a[0]) - ex * (p[1] - a[1])) / denom
            return (p[0] + t * dpx, p[1] + t * dpy)
        previous = output[-1]
        new = []
        for current in output:
            if inside(current):
                if not inside(previous):
                    new.append(cross(previous, current))
                new.append(current)
            elif inside(previous):
                new.append(cross(previous, current))
            previous = current
        output = new
    return np.array(output, float) if len(output) >= 3 else None


def halfplane_clip(poly, point, normal, offset):
    """Keep the part of a polygon where (p - point) . normal <= offset (a straight cut)."""
    out = []
    n = len(poly)
    if n == 0:
        return poly
    values = (poly - point) @ normal - offset
    for i in range(n):
        j = (i + 1) % n
        vi, vj = values[i], values[j]
        if vi <= 0:
            out.append(poly[i])
        if (vi < 0 < vj) or (vj < 0 < vi):
            t = vi / (vi - vj)
            out.append(poly[i] + t * (poly[j] - poly[i]))
    return np.array(out) if len(out) >= 3 else None


def cell_polygon(seed_point, neighbours, reach):
    """The Voronoi cell of one seed: start from a big square round it and cut it by the straight line half way to every neighbouring seed."""
    poly = np.array([[seed_point[0] - reach, seed_point[1] - reach], [seed_point[0] + reach, seed_point[1] - reach],
                     [seed_point[0] + reach, seed_point[1] + reach], [seed_point[0] - reach, seed_point[1] + reach]], float)
    order = np.argsort(((neighbours - seed_point) ** 2).sum(1))
    for k in order:
        other = neighbours[k]
        d = other - seed_point
        dist = math.hypot(d[0], d[1])
        if dist < 1e-9:
            continue
        # farthest corner of the cell so far: if it is nearer than half the distance to this neighbour, no later neighbour can cut it either
        far = float(np.sqrt(((poly - seed_point) ** 2).sum(1)).max())
        if far < dist / 2.0:
            break
        poly = halfplane_clip(poly, (seed_point + other) / 2.0, d / dist, 0.0)
        if poly is None:
            return None
    return poly


def jittered_grid(x0, y0, x1, y1, mean_area, rng, jitter=0.55):
    """Seed points on a grid with random jitter: returns (seeds array shape (nx, ny, 2), spacing x, spacing y)."""
    spacing = math.sqrt(mean_area)
    nx, ny = max(int(round((x1 - x0) / spacing)), 1), max(int(round((y1 - y0) / spacing)), 1)
    gx, gy = (x1 - x0) / nx, (y1 - y0) / ny
    seeds = np.zeros((nx, ny, 2))
    for i in range(nx):
        for j in range(ny):
            seeds[i, j] = (x0 + (i + 0.5 + rng.uniform(-jitter, jitter)) * gx, y0 + (j + 0.5 + rng.uniform(-jitter, jitter)) * gy)
    return seeds, gx, gy


def grid_neighbours(seeds, i, j, gx, gy, wrap_tile=None, ring=2):
    """Seeds of the grid cells within `ring` steps of (i, j); with wrap_tile they continue round the tile edge (their positions are shifted a tile)."""
    nx, ny = seeds.shape[:2]
    out = []
    for di in range(-ring, ring + 1):
        for dj in range(-ring, ring + 1):
            if di == 0 and dj == 0:
                continue
            ii, jj = i + di, j + dj
            shift = np.zeros(2)
            if wrap_tile is not None:
                shift = np.array([(ii // nx) * wrap_tile, (jj // ny) * wrap_tile], float)
                ii, jj = ii % nx, jj % ny
            elif not (0 <= ii < nx and 0 <= jj < ny):
                continue
            out.append(seeds[ii, jj] + shift)
    return np.array(out)


class Wobble:
    """A smooth wobble of the plane (a mix of a few sine waves in random directions): moves every point by a small vector, the same for every cell."""

    def __init__(self, rng, amplitude, wavelengths=(7.0, 17.0)):
        self.waves = []
        for wl in wavelengths:
            for _ in range(3):
                angle = rng.uniform(0, 2 * math.pi)
                self.waves.append((2 * math.pi / wl * math.cos(angle), 2 * math.pi / wl * math.sin(angle), rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi), amplitude / math.sqrt(2 * len(wavelengths))))

    def __call__(self, pts):
        dx = np.zeros(len(pts))
        dy = np.zeros(len(pts))
        for kx, ky, p1, p2, a in self.waves:
            dx += a * np.sin(kx * pts[:, 0] + ky * pts[:, 1] + p1)
            dy += a * np.sin(kx * pts[:, 0] + ky * pts[:, 1] + p2)
        return np.stack([dx, dy], axis=1)


def subdivide(poly, step=4.0):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        length = float(np.hypot(*(b - a)))
        k = max(int(math.ceil(length / step)), 1)
        for j in range(k):
            out.append(a + (b - a) * (j / k))
    return np.array(out)


def distance_to_polygon_edge(pts, polygon):
    """Distance of every point to the nearest edge of a polygon."""
    best = np.full(len(pts), 1e9)
    n = len(polygon)
    for i in range(n):
        a, b = polygon[i], polygon[(i + 1) % n]
        ab = b - a
        denom = max(float(ab @ ab), 1e-12)
        t = np.clip(((pts - a) @ ab) / denom, 0, 1)
        proj = a + t[:, None] * ab
        best = np.minimum(best, np.hypot(*(pts - proj).T))
    return best


def mosaic_in_shape(shape, mean_area, rng, wobble, keep=1.0, edge_pin=3.0, jitter=0.55, step=4.0):
    """Fill a convex shape (polygon) with cells of about mean_area (each kept with chance `keep`). Returns (polygon, centre) pairs, wobbled but with
    the shape's own edge pinned in place."""
    x0, y0 = shape.min(0)
    x1, y1 = shape.max(0)
    seeds, gx, gy = jittered_grid(x0, y0, x1, y1, mean_area, rng, jitter)
    cells = []
    reach = 3.0 * max(gx, gy)
    for i in range(seeds.shape[0]):
        for j in range(seeds.shape[1]):
            if rng.random() > keep:
                continue
            poly = cell_polygon(seeds[i, j], grid_neighbours(seeds, i, j, gx, gy), reach)
            if poly is None:
                continue
            clipped = clip_convex(poly, shape)
            if clipped is None:
                continue
            dense = subdivide(clipped, step)
            pin = np.clip(distance_to_polygon_edge(dense, shape) / edge_pin, 0.0, 1.0)
            cells.append((dense + wobble(dense) * pin[:, None], seeds[i, j].copy()))
    return cells


def periodic_cells(tile, mean_area, rng, wobble, keep=1.0, jitter=0.55, step=4.0, skip=None):
    """Cells of a mosaic that wraps round the tile exactly (the seeds repeat every tile). skip(centre) -> True drops a cell (e.g. hidden under a brick)."""
    seeds, gx, gy = jittered_grid(0.0, 0.0, tile, tile, mean_area, rng, jitter)
    cells = []
    reach = 3.0 * max(gx, gy)
    for i in range(seeds.shape[0]):
        for j in range(seeds.shape[1]):
            centre = seeds[i, j]
            if rng.random() > keep or (skip is not None and skip(centre)):
                continue
            poly = cell_polygon(centre, grid_neighbours(seeds, i, j, gx, gy, wrap_tile=tile), reach)
            if poly is None:
                continue
            dense = subdivide(poly, step)
            cells.append((dense + wobble(dense), centre.copy()))
    return cells


def encode_polygon(colour, points, unit=0.5):
    """[colour, start x, start y, step x, step y, ...] in `unit` dots, ready for a 'regions' layer."""
    q = np.round(np.asarray(points) / unit).astype(int)
    steps = np.diff(q, axis=0).ravel().tolist()
    return [int(colour), int(q[0, 0]), int(q[0, 1])] + steps


class ToneDial:
    """A slowly changing number between 0 and 1 over the picture (sum of a few big sine waves, turned into an even spread by the normal curve)."""

    def __init__(self, rng, wavelengths=(110.0, 170.0, 260.0)):
        self.waves = []
        for wl in wavelengths:
            for _ in range(2):
                ang = rng.uniform(0, 2 * math.pi)
                self.waves.append((2 * math.pi / wl * math.cos(ang), 2 * math.pi / wl * math.sin(ang), rng.uniform(0, 2 * math.pi)))

    def __call__(self, x, y):
        z = sum(math.sin(kx * x + ky * y + ph) for kx, ky, ph in self.waves) / math.sqrt(len(self.waves) / 2.0)
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def colour_by_quantile(table, order, quantile):
    probs = np.array(table, float)[order]
    cdf = np.cumsum(probs / probs.sum())
    return int(order[int(min(np.searchsorted(cdf, quantile), len(order) - 1))])
