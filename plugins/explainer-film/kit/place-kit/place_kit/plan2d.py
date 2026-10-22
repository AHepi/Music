"""What this does: the small flat-map maths the kit needs, in plain numpy (no Blender, no OpenCV, no SciPy), so it works inside Blender's
own Python and is tested without Blender: how far a point is from a polyline (a road, a path) and on which side, painting triangles into a
grid of cells (the ground's height, where walls stand), blurring a grid, and a distance map (how far every cell is from the nearest marked cell).
A "grid" here is an array indexed [row, column] where row = steps along +y from the bottom edge y0 and column = steps along +x from the left edge
x0, in cells of `cell` metres (the same order as a Blender image's pixels, so a grid can be written to an image without flipping).

A concrete example: distance_to_polyline(np.array([[1.0, 2.0]]), [[0, 0], [10, 0]]) gives distance 2.0 on the left side (sign +1).
"""
import numpy as np


def polyline_points(polyline):
    return np.asarray(polyline, dtype=np.float64).reshape(-1, 2)


def distance_to_polyline(points, polyline):
    """For points (n, 2): the distance to the nearest segment of the polyline, the sign (+1 on the left of its direction of travel, -1 on the
    right), and how far along the polyline (metres from its start) the nearest point lies. Returns three arrays of length n."""
    p = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    line = polyline_points(polyline)
    best = np.full(len(p), np.inf)
    sign = np.ones(len(p))
    along = np.zeros(len(p))
    travelled = 0.0
    for a, b in zip(line[:-1], line[1:]):
        segment = b - a
        length = float(np.hypot(*segment))
        if length < 1e-12:
            continue
        direction = segment / length
        t = np.clip(((p - a) @ direction), 0.0, length)
        nearest = a + t[:, None] * direction
        distance = np.hypot(*(p - nearest).T)
        side = direction[0] * (p[:, 1] - a[1]) - direction[1] * (p[:, 0] - a[0])
        closer = distance < best
        best = np.where(closer, distance, best)
        sign = np.where(closer, np.where(side >= 0, 1.0, -1.0), sign)
        along = np.where(closer, travelled + t, along)
        travelled += length
    return best, sign, along


def grid_centres(x0, y0, cell, shape):
    """The x and y of every cell centre: two arrays of the grid's shape."""
    rows, cols = shape
    xs = x0 + (np.arange(cols) + 0.5) * cell
    ys = y0 + (np.arange(rows) + 0.5) * cell
    return np.meshgrid(xs, ys)


def polyline_field(x0, y0, cell, shape, polyline, radius):
    """Distance, side and distance-along of a polyline for every cell of a grid, worked out only for cells within `radius` of the polyline's
    box (others get distance inf). Returns (distance, sign, along) grids."""
    rows, cols = shape
    line = polyline_points(polyline)
    low = line.min(axis=0) - radius
    high = line.max(axis=0) + radius
    c0 = max(0, int((low[0] - x0) // cell))
    c1 = min(cols, int((high[0] - x0) // cell) + 2)
    r0 = max(0, int((low[1] - y0) // cell))
    r1 = min(rows, int((high[1] - y0) // cell) + 2)
    distance = np.full(shape, np.inf)
    sign = np.ones(shape)
    along = np.zeros(shape)
    if c1 <= c0 or r1 <= r0:
        return distance, sign, along
    xs = x0 + (np.arange(c0, c1) + 0.5) * cell
    ys = y0 + (np.arange(r0, r1) + 0.5) * cell
    gx, gy = np.meshgrid(xs, ys)
    d, s, a = distance_to_polyline(np.stack([gx.ravel(), gy.ravel()], axis=1), line)
    distance[r0:r1, c0:c1] = d.reshape(gx.shape)
    sign[r0:r1, c0:c1] = s.reshape(gx.shape)
    along[r0:r1, c0:c1] = a.reshape(gx.shape)
    return distance, sign, along


def rasterize_triangles(vertices, triangles, x0, y0, cell, shape, mode='max'):
    """Paints triangles seen from above into a grid. mode 'max' keeps the highest z in each cell, 'min' the lowest, 'cover' marks 1 where any
    triangle covers the cell centre (z ignored). Cells no triangle covers hold nan (or 0 for 'cover'). Triangles smaller than a cell are
    painted at their centre."""
    rows, cols = shape
    grid = np.full(shape, np.nan if mode != 'cover' else 0.0)
    v = np.asarray(vertices, dtype=np.float64)
    for tri in np.asarray(triangles):
        a, b, c = v[tri[0]], v[tri[1]], v[tri[2]]
        lo_x, hi_x = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        lo_y, hi_y = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        c0, c1 = int(np.floor((lo_x - x0) / cell - 0.5)), int(np.ceil((hi_x - x0) / cell - 0.5))
        r0, r1 = int(np.floor((lo_y - y0) / cell - 0.5)), int(np.ceil((hi_y - y0) / cell - 0.5))
        c0, c1, r0, r1 = max(c0, 0), min(c1, cols - 1), max(r0, 0), min(r1, rows - 1)
        if c1 < c0 or r1 < r0:
            continue
        xs = x0 + (np.arange(c0, c1 + 1) + 0.5) * cell
        ys = y0 + (np.arange(r0, r1 + 1) + 0.5) * cell
        gx, gy = np.meshgrid(xs, ys)
        denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(denominator) < 1e-12:
            continue
        w1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / denominator
        w2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / denominator
        w3 = 1.0 - w1 - w2
        inside = (w1 >= -1e-9) & (w2 >= -1e-9) & (w3 >= -1e-9)
        if not inside.any():
            if hi_x - lo_x < cell and hi_y - lo_y < cell:
                col_index = int(((a[0] + b[0] + c[0]) / 3 - x0) / cell)
                row_index = int(((a[1] + b[1] + c[1]) / 3 - y0) / cell)
                if 0 <= col_index < cols and 0 <= row_index < rows:
                    _paint(grid, row_index, col_index, (a[2] + b[2] + c[2]) / 3, mode)
            continue
        if mode == 'cover':
            grid[r0:r1 + 1, c0:c1 + 1][inside] = 1.0
            continue
        z = w1 * a[2] + w2 * b[2] + w3 * c[2]
        window = grid[r0:r1 + 1, c0:c1 + 1]
        current = window[inside]
        new = z[inside]
        if mode == 'max':
            window[inside] = np.where(np.isnan(current), new, np.maximum(current, new))
        else:
            window[inside] = np.where(np.isnan(current), new, np.minimum(current, new))
    return grid


def _paint(grid, row, col, z, mode):
    if mode == 'cover':
        grid[row, col] = 1.0
    elif np.isnan(grid[row, col]):
        grid[row, col] = z
    else:
        grid[row, col] = max(grid[row, col], z) if mode == 'max' else min(grid[row, col], z)


def fill_nan(grid, fallback):
    """Cells nobody painted get the value of the nearest painted cell by spreading outward (or `fallback` when nothing was painted)."""
    painted = ~np.isnan(grid)
    if not painted.any():
        return np.full(grid.shape, fallback)
    result = np.where(painted, grid, 0.0)
    weight = painted.astype(np.float64)
    for _ in range(max(grid.shape)):
        if weight.min() > 0:
            break
        total, count = np.zeros_like(result), np.zeros_like(result)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            shifted_r = np.roll(result * weight, (dr, dc), axis=(0, 1))
            shifted_w = np.roll(weight, (dr, dc), axis=(0, 1))
            total += shifted_r
            count += shifted_w
        new = (weight == 0) & (count > 0)
        result = np.where(new, total / np.maximum(count, 1e-9), result)
        weight = np.where(new, 1.0, weight)
    return result


def box_blur(grid, radius_cells):
    """A box blur by integral images (edges repeat the nearest cell)."""
    radius = int(max(0, round(radius_cells)))
    if radius == 0:
        return np.asarray(grid, dtype=np.float64)
    padded = np.pad(np.asarray(grid, dtype=np.float64), radius, mode='edge')
    integral = np.pad(padded.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))
    size = 2 * radius + 1
    rows, cols = np.asarray(grid).shape
    total = integral[size:size + rows, size:size + cols] - integral[:rows, size:size + cols] - integral[size:size + rows, :cols] + integral[:rows, :cols]
    return total / (size * size)


def distance_to_marked(marked, cell, max_metres):
    """Distance in metres from every cell to the nearest marked cell (marked = boolean grid), by repeated relaxation with chamfer steps (good
    to about 8 percent); cells farther than max_metres hold max_metres. With nothing marked every cell holds max_metres."""
    marked = np.asarray(marked, dtype=bool)
    far = float(max_metres)
    if not marked.any():
        return np.full(marked.shape, far)
    steps = int(np.ceil(max_metres / cell)) + 1
    distance = np.where(marked, 0.0, far)
    straight, diagonal = cell, cell * 1.4142
    for _ in range(steps):
        before = distance
        best = distance
        for dr, dc, weight in ((1, 0, straight), (-1, 0, straight), (0, 1, straight), (0, -1, straight),
                               (1, 1, diagonal), (1, -1, diagonal), (-1, 1, diagonal), (-1, -1, diagonal)):
            shifted = np.full_like(distance, far)
            r_from, r_to = (slice(0, -1), slice(1, None)) if dr == 1 else (slice(1, None), slice(0, -1)) if dr == -1 else (slice(None), slice(None))
            c_from, c_to = (slice(0, -1), slice(1, None)) if dc == 1 else (slice(1, None), slice(0, -1)) if dc == -1 else (slice(None), slice(None))
            shifted[r_to, c_to] = distance[r_from, c_from] + weight
            best = np.minimum(best, shifted)
        distance = np.minimum(best, far)
        if np.array_equal(before, distance):
            break
    return distance


def smoothstep(low, high, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - low) / (high - low + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def shadow_map(height_above_ground, cell, azimuth_degrees, elevation_degrees, max_metres=12.0, threshold=0.05):
    """A flat shadow estimate: 1 where something taller (a wall, a tree) lies between the cell and the sun at that sun direction, else 0.
    height_above_ground: grid of how high things stand above the ground (0 where nothing). azimuth: the direction TOWARD the sun, degrees
    from +x toward +y. Not a render: a plan-view estimate good enough to say where it is shady."""
    azimuth = np.radians(azimuth_degrees)
    toward_sun = np.array([np.cos(azimuth), np.sin(azimuth)])
    tangent = np.tan(np.radians(max(elevation_degrees, 5.0)))
    shadow = np.zeros_like(height_above_ground, dtype=np.float64)
    steps = int(min(max_metres / cell, 200))
    for k in range(1, steps + 1):
        # a cell is shaded by a taller thing k cells toward the sun if that thing is higher than the sun's ray over that distance
        dx, dy = toward_sun * k
        shift_cols, shift_rows = int(round(dx)), int(round(dy))
        source = np.roll(height_above_ground, (-shift_rows, -shift_cols), axis=(0, 1))
        shadow = np.maximum(shadow, (source - k * cell * tangent > threshold).astype(np.float64))
    return shadow
