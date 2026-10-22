# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# FOOTFALL, KEEP-CLEAR, ENTRY RANDOM and EXISTING GROWTH on the ground plan, from the shapes the set file declares (settings footfall, keep_clear, entrances,
# existing_growth). Nothing here knows what a "road" or a "gravel court" is.
#   footfall (0..1)   how trodden: the strongest of the set's footfall shapes
#   keepclear (0..1)  hard "no plants here": the set's keep-clear shapes and wherever footfall is above the trodden limits
#   entry_rand        one random number per entrance, painted in a disc round it (0.5 elsewhere)
#   existing_growth   density of growth the set already has (its faces seen from above, blurred 15 cm)
# Shapes: band_along (a band across x), lines_along (lines at x positions), polyline (a path with a width), rect (min and max corners), auto_door_to_edge (a line from every
# entrance to the nearest dot of a ground role), auto_door_strip (the step treads and the entrance grown by reach), around_role (within a radius of a role's objects),
# from_footfall (where footfall is between two limits).
import numpy as np

from . import geom
from .grid import Grid, smoothstep
from .ground_plan import fill_triangles

import hashlib


def _feather(dist_outside, feather):
    """1 inside (dist <= 0), falling to 0 over `feather` metres."""
    if feather <= 0:
        return (dist_outside <= 0).astype(np.float32)
    return (1.0 - smoothstep(dist_outside, 0.0, feather)).astype(np.float32)


def _segment_distance(grid, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    t = np.clip(((grid.X - ax) * dx + (grid.Y - ay) * dy) / max(length2, 1e-9), 0, 1)
    return np.hypot(grid.X - (ax + t * dx), grid.Y - (ay + t * dy))


def shape_picture(rule, grid, entrances, role_dots, geo_role_distance):
    kind = rule['kind']
    weight = float(rule.get('weight', 1.0))
    feather = float(rule.get('feather_m', 0.3))
    out = np.zeros(grid.shape(), np.float32)
    if kind == 'band_along':
        x0, x1 = rule['x']
        out = _feather(np.maximum(np.maximum(x0 - grid.X, grid.X - x1), 0.0), feather)
    elif kind == 'lines_along':
        half = rule.get('width_m', 0.4) / 2.0
        for x in rule['x']:
            out = np.maximum(out, _feather(np.abs(grid.X - x) - half, feather))
    elif kind == 'polyline':
        half = rule.get('width_m', 1.0) / 2.0
        pts = rule['points']
        d = np.full(grid.shape(), 1e9, np.float32)
        for a, b in zip(pts[:-1], pts[1:]):
            d = np.minimum(d, _segment_distance(grid, a, b))
        out = _feather(d - half, feather)
    elif kind == 'rect':
        (x0, y0), (x1, y1) = rule['min'], rule['max']
        dx = np.maximum(np.maximum(x0 - grid.X, grid.X - x1), 0.0)
        dy = np.maximum(np.maximum(y0 - grid.Y, grid.Y - y1), 0.0)
        out = _feather(np.hypot(dx, dy), feather)
    elif kind == 'auto_door_to_edge' and rule.get('from_entrances'):
        half = rule.get('width_m', 0.9) / 2.0
        dots = role_dots(rule['to_role'])
        d = np.full(grid.shape(), 1e9, np.float32)
        if dots is not None and len(dots):
            for ex, ey, ez, _ in entrances:
                nearest = dots[np.argmin(np.hypot(dots[:, 0] - ex, dots[:, 1] - ey))]
                d = np.minimum(d, _segment_distance(grid, (ex, ey), (nearest[0], nearest[1])))
        out = _feather(d - half, feather)
    return out * weight


def make(geo, settings, grid, arrays, entrances, timer):
    """footfall, keepclear, entry_rand, existing_growth on `grid` (the normal ground grid). `arrays` holds ground_role, has_ground, step_top (fine, optional) from the ground plan."""
    role_names = arrays['_role_names']

    def role_dots(role):
        if role not in role_names:
            return None
        ids = role_names.index(role) + 1
        ys, xs = np.nonzero(arrays['ground_role'] == ids)
        return np.stack([grid.xs[xs], grid.ys[ys]], axis=1) if len(xs) else None

    footfall = np.zeros(grid.shape(), np.float32)
    for rule in settings.get('footfall') or []:
        footfall = np.maximum(footfall, shape_picture(rule, grid, entrances, role_dots, None))
    footfall[~arrays['has_ground']] = 0.0
    timer.mark('footfall')
    keep = np.zeros(grid.shape(), np.float32)
    for rule in settings.get('keep_clear') or []:
        kind = rule['kind']
        feather = float(rule.get('feather_m', 0.2))
        if kind == 'from_footfall':
            keep = np.maximum(keep, smoothstep(footfall, rule['above'], rule['to']).astype(np.float32))
        elif kind == 'around_role':
            tree = geo.tree([rule['role']])
            if tree is not None:
                d = geom.nearest_distances(tree, grid, arrays['ground_height'] + 0.3, rule['radius_m'] + feather + 0.01, arrays['has_ground'])
                keep = np.maximum(keep, _feather(d - rule['radius_m'], feather))
        elif kind == 'auto_door_strip' and rule.get('from_entrances'):
            reach = rule.get('reach_m', 0.5)
            d = np.full(grid.shape(), 1e9, np.float32)
            for ex, ey, ez, _ in entrances:
                d = np.minimum(d, np.hypot(grid.X - ex, grid.Y - ey) - 0.6)           # the doorstep is about 1.2 m across
            step = arrays.get('_step_top_coarse')
            if step is not None and step.any():
                import cv2
                dist = cv2.distanceTransform((step == 0).astype(np.uint8), cv2.DIST_L2, 5) * grid.dot
                d = np.minimum(d, dist)
            keep = np.maximum(keep, _feather(d - reach, feather))
        elif kind in ('rect', 'polyline'):
            keep = np.maximum(keep, shape_picture(dict(rule, weight=1.0), grid, entrances, role_dots, None))
    keep[~arrays['has_ground']] = 0.0
    timer.mark('keep clear')
    # entry random
    entry = np.full(grid.shape(), 0.5, np.float32)
    best = np.full(grid.shape(), 1e9, np.float32)
    for ex, ey, ez, name in entrances:
        value = int.from_bytes(hashlib.md5(f'{round(ex, 2)}|{round(ey, 2)}'.encode()).digest()[:8], 'big') / float(1 << 64)
        d = np.hypot(grid.X - ex, grid.Y - ey)
        closer = (d < 1.4) & (d < best)
        entry[closer] = value
        best[closer] = d[closer]
    # existing growth
    growth = np.zeros(grid.shape(), np.float32)
    spec = settings.get('existing_growth')
    if spec:
        canvas = np.zeros(grid.shape(), np.uint8)
        for role in settings.expand_roles(spec.get('objects', [])):
            data = geo.triangles([role])
            if data is None:
                continue
            v, t = data[0], data[1]
            n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
            nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
            fill_triangles(canvas, grid, v[:, :2], t[nz > 0.0], 1)
        growth = geom.blur(canvas.astype(np.float32), 0.15 / grid.dot)
        growth = np.clip(growth * 2.0, 0.0, 1.0).astype(np.float32)
    timer.mark('entry random, existing growth')
    return dict(footfall=footfall, keepclear=keep, entry_rand=entry, existing_growth=growth)
