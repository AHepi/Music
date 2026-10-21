# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# SHADE: how shaded and how enclosed each dot is. Three ingredients, mixed by the set's `shade` block (mode and weights):
#   openness   48 fixed rays spread over the hemisphere round the surface normal, 40 m long, against everything that stands (walls, props, posts, roofs, ground, and the set's
#              extra blockers such as leaf masses at a fraction); the share that escapes; stretched over the scene's own 2nd to 98th percentile so differences show
#   declared   a sun direction the set DECLARES (shade.toward_sun): lit = how squarely the surface faces it, cut to nothing when something stands between
#   year_sun   the sun over a year at the set's latitude (shade.latitude_deg, shade.north): the same test for ~48 sun positions, weighted by the sun's height
# shade = weight_sun x (1 - exposure) + weight_openness x (1 - openness), both stretched. Points can be on the ground (normal up) or on a wall (normal outward); the same code
# serves the ground plan (16 cm) and the wall sheets (8 cm).
import math

import numpy as np
from mathutils import Vector

from . import geom


def sun_positions(settings_shade):
    """[(unit vector toward the sun, weight)] for the declared direction or for the year sun. The kinds are named by the mode."""
    mode = settings_shade.get('mode', 'openness')
    result = []
    if 'declared' in mode:
        v = Vector(settings_shade['toward_sun']).normalized()
        result.append((v, 1.0))
    elif 'year_sun' in mode:
        latitude = math.radians(settings_shade.get('latitude_deg', 35.0))
        north = Vector(settings_shade.get('north', [0.0, 1.0, 0.0])).normalized()
        up = Vector((0, 0, 1))
        east = north.cross(up).normalized()
        count = int(settings_shade.get('year_sun_positions', 48))
        candidates = []
        for month in range(12):
            declination = math.radians(23.44) * math.sin(2 * math.pi * (month * 30.4 + 80 - 81) / 365.0 + 0.0)
            declination = math.radians(-23.44) * math.cos(2 * math.pi * (month * 30.4 + 10) / 365.0)
            for hour_angle_deg in (-67.5, -45, -22.5, 0, 22.5, 45, 67.5):
                h = math.radians(hour_angle_deg)
                sin_alt = math.sin(latitude) * math.sin(declination) + math.cos(latitude) * math.cos(declination) * math.cos(h)
                alt = math.asin(max(-1, min(1, sin_alt)))
                if alt < math.radians(3.0):
                    continue
                cos_az = (math.sin(declination) - math.sin(alt) * math.sin(latitude)) / max(1e-9, math.cos(alt) * math.cos(latitude))
                az = math.acos(max(-1, min(1, cos_az)))            # from north, toward east in the morning
                if hour_angle_deg > 0:
                    az = 2 * math.pi - az
                horizontal = north * math.cos(az) + east * math.sin(az)
                vec = horizontal * math.cos(alt) + up * math.sin(alt)
                candidates.append((vec.normalized(), math.sin(alt)))
        stride = max(1, len(candidates) // max(1, count))
        result = candidates[::stride][:count]
    return result


def stretch(a, valid=None, lo=2.0, hi=98.0):
    values = a[valid] if valid is not None else a.ravel()
    if values.size == 0:
        return a
    p0, p1 = np.percentile(values, [lo, hi])
    if p1 - p0 < 1e-6:
        return np.zeros_like(a)
    return np.clip((a - p0) / (p1 - p0), 0.0, 1.0).astype(np.float32)


def blockers(geo, settings, include_ground=True):
    """Tree of everything that stands in the way of light: every role except those that are only ground (unless include_ground), plus the set's extra blockers."""
    roles = list(settings.roles)
    use = [r for r in roles if include_ground or r not in settings.geometry['ground']['roles']]
    return geo.tree(use)


def openness_at(tree, points, normals, rays, length, extra_tree=None, extra_weight=0.0, progress=None):
    """Share of `rays` fixed directions round each normal that escape (0..1). points, normals: lists of Vector."""
    base = geom.hemisphere_directions(rays)
    out = np.ones(len(points), np.float32)
    up = Vector((0, 0, 1))
    for k, (p, n) in enumerate(zip(points, normals)):
        rot = up.rotation_difference(n)
        free = 0.0
        for d in base:
            direction = rot @ d
            origin = p + n * 0.03
            hit = tree.ray_cast(origin, direction, length)[0] if tree is not None else None
            if hit is not None:
                continue
            if extra_tree is not None and extra_tree.ray_cast(origin, direction, length)[0] is not None:
                free += 1.0 - extra_weight
            else:
                free += 1.0
        out[k] = free / len(base)
    return out


def sun_exposure_at(tree, points, normals, suns, length=60.0, extra_tree=None, extra_weight=0.0):
    """Weighted share of the sun positions that reach each point: lit = n . L (0 if facing away) unless something stands between."""
    out = np.zeros(len(points), np.float32)
    total = sum(w for _, w in suns) or 1.0
    for k, (p, n) in enumerate(zip(points, normals)):
        acc = 0.0
        for d, w in suns:
            facing = n.dot(d)
            if facing <= 0.0:
                continue
            origin = p + n * 0.03
            if tree is not None and tree.ray_cast(origin, d, length)[0] is not None:
                continue
            fraction = 1.0
            if extra_tree is not None and extra_tree.ray_cast(origin, d, length)[0] is not None:
                fraction = 1.0 - extra_weight
            acc += w * facing * fraction
        out[k] = acc / total
    return out


def weights_of(shade_settings):
    w = dict(shade_settings.get('weights', {}))
    mode = shade_settings.get('mode', 'openness')
    wo, ws = float(w.get('openness', 0.5)), float(w.get('sun', 0.5))
    if mode == 'openness':
        wo, ws = 1.0, 0.0
    if mode == 'none':
        wo = ws = 0.0
    total = wo + ws
    return (wo / total, ws / total) if total > 0 else (0.0, 0.0)


def make_ground(geo, settings, grid16, h16, has16, timer):
    """openness, sun shade and shade on the 16 cm ground grid. Returns dict of arrays."""
    shade = settings.get('shade') or {'mode': 'none'}
    tree = blockers(geo, settings)
    extra = geo.extra_tree(shade.get('extra_blockers', {}).get('objects', [])) if shade.get('extra_blockers') else None
    extra_w = (shade.get('extra_blockers') or {}).get('block', 0.0)
    pts, idx = [], []
    for j in range(grid16.height):
        for i in range(grid16.width):
            if has16[j, i]:
                pts.append(Vector((grid16.xs[i], grid16.ys[j], float(h16[j, i]) + 0.02)))
                idx.append((j, i))
    normals = [Vector((0, 0, 1))] * len(pts)
    wo, ws = weights_of(shade)
    openness = np.full(grid16.shape(), 0.5, np.float32)
    sun = np.full(grid16.shape(), 0.5, np.float32)
    if wo > 0 or shade.get('mode') == 'openness':
        o = openness_at(tree, pts, normals, int(shade.get('openness_rays', 48)), float(shade.get('ray_length_m', 40.0)), extra, extra_w)
        for (j, i), v in zip(idx, o):
            openness[j, i] = v
        openness = stretch(openness, has16) if shade.get('normalise_openness', True) else openness
    timer.mark('openness (ground)')
    suns = sun_positions(shade) if ws > 0 else []
    if suns:
        e = sun_exposure_at(tree, pts, normals, suns, 60.0, extra, extra_w)
        for (j, i), v in zip(idx, e):
            sun[j, i] = v
        sun = stretch(sun, has16)
    timer.mark(f'sun ({len(suns)} positions, ground)')
    sun_shade = 1.0 - sun if suns else np.full(grid16.shape(), 0.5, np.float32)
    shade_pic = wo * (1.0 - openness) + ws * sun_shade if (wo + ws) > 0 else np.full(grid16.shape(), 0.5, np.float32)
    shade_pic = np.clip(shade_pic, 0, 1).astype(np.float32)
    shade_pic[~has16] = 0.5
    return dict(openness=openness, sun_shade=sun_shade.astype(np.float32), shade=shade_pic), dict(sun_positions=len(suns), weights=[wo, ws])


def sheltered_ground(geo, settings, grid, h, has, reach_m=3.5, rays=24, cone_deg=35.0):
    """Ground-plan `sheltered`: the share of rays within cone_deg of straight up that meet something overhanging (a surface that is not upright) within reach_m: the ground
    under eaves, bridges and awnings stays dry."""
    tree = blockers(geo, settings, include_ground=False)
    dirs = geom.cone_directions(rays, cone_deg)
    out = np.zeros(grid.shape(), np.float32)
    if tree is None:
        return out
    ray = tree.ray_cast
    for j in range(grid.height):
        for i in range(grid.width):
            if not has[j, i]:
                continue
            origin = Vector((grid.xs[i], grid.ys[j], float(h[j, i]) + 0.03))
            n = 0
            for d in dirs:
                hit = ray(origin, d, reach_m)
                if hit[0] is not None and abs(hit[1].z) > 0.3:
                    n += 1
            out[j, i] = n / len(dirs)
    return out
