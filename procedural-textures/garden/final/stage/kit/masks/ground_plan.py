# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The GROUND PLAN: pictures of the set's ground seen from above (world x and y), made by asking the real 3D shapes. One dot = settings.geometry.ground.dot_m (4 cm); the
# "fine" pictures (steps, edges, stone gaps) use fine_dot_m (2 cm). Which objects are ground, walls, props, pipes ... comes from the roles the set file names, never from names.
# Made here (every number 0..1 unless it says metres; the bus gives them back by name, see masks/names.py):
#   ground_height (metres), has_ground, ground_role       the height of the ground at each dot by a ray from above, and which ground role was hit
#   slope, lowness, crown                                  gradient over 8 cm; "how much lower than the ground nearby"; "how much higher than the lowest ground of the same role"
#   wall_dist, prop_dist, inside_corner, step_foot, vertical_foot, cover_dist   where things catch (the earlier "places" pictures, from the real shapes)
#   seam_dist                                              distance to the line where two ground roles meet
#   water_dist, above_water                                the set's water level against the ground height
#   (fine grid) step_top, step_edge, edge_dist, piece_gap  steps, outward sharp edges, boundaries between separate stones
import math

import numpy as np
from mathutils import Vector

from . import geom
from .geom import Grid, blur, smoothstep

WALL_REACH_DEFAULT = 1.275


def _clip01(a):
    return np.clip(a, 0.0, 1.0).astype(np.float32)


def entrances(geo, settings):
    """World (x, y, z) of every entrance: the origins of the objects of the role the set names (geometry.entrances: role, optional names patterns)."""
    import re
    spec = settings.geometry.get('entrances')
    if not spec:
        return []
    import bpy
    result = []
    for name in geo.role_map.members.get(spec['role'], []):
        if spec.get('names') and not any(re.match(p, name) for p in spec['names']):
            continue
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        if obj.type == 'EMPTY':
            p = obj.matrix_world.translation
        else:
            corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
            p = sum(corners, Vector()) / 8.0
        result.append((float(p.x), float(p.y), float(p.z), name))
    return result


def ground_height(geo, settings, grid, timer):
    ground_roles = settings.geometry['ground']['roles']
    tree, owner, owners = geo.owners_tree(ground_roles)
    if tree is None:
        raise RuntimeError('the set has no ground geometry (geometry.ground.roles found nothing)')
    lo, hi = geo.bounds(ground_roles)
    z_top = float(hi[2]) + 5.0
    depth = float(hi[2] - lo[2]) + 10.0
    height = np.zeros(grid.shape(), np.float32)
    has = np.zeros(grid.shape(), bool)
    role_id = np.zeros(grid.shape(), np.uint8)
    role_names = settings.expand_roles(ground_roles)
    owner_role = np.array([role_names.index(geo.role_map.primary[o]) + 1 for o in owners], np.uint8)
    down = Vector((0, 0, -1))
    ray = tree.ray_cast
    for j, y in enumerate(grid.ys):
        for i, x in enumerate(grid.xs):
            hit = ray(Vector((x, y, z_top)), down, depth)
            if hit[0] is not None:
                height[j, i] = hit[0].z
                has[j, i] = True
                role_id[j, i] = owner_role[owner[hit[2]]]
    timer.mark('ground height')
    return height, has, role_id, role_names


def slope_picture(h, has, grid):
    gy, gx = np.gradient(h, grid.dot * 2.0 / 2.0)           # per metre, central differences over 2 dots (8 cm)
    angle = np.degrees(np.arctan(np.hypot(gx, gy)))
    out = _clip01(angle / 30.0)
    out[~has] = 0.0
    return out


def lowness_picture(h, has, grid, radius_m, scale_m):
    k = int(round(radius_m / grid.dot)) * 2 + 1
    import cv2
    num = cv2.blur(np.where(has, h, 0.0).astype(np.float32), (k, k))
    den = cv2.blur(has.astype(np.float32), (k, k))
    mean = np.where(den > 0.02, num / np.maximum(den, 1e-6), h)
    out = _clip01((mean - h) / scale_m)
    out[~has] = 0.5
    return out


def crown_picture(h, has, role_id, role_names, settings, grid):
    spec = settings.geometry.get('crown')
    out = np.zeros(grid.shape(), np.float32)
    if not spec:
        return out
    import cv2
    wanted = [role_names.index(r) + 1 for r in settings.expand_roles(spec['roles']) if r in role_names]
    mask = np.isin(role_id, wanted) & has
    if not mask.any():
        return out
    # remove the plane the ground leans on (the set's overall slope) so that "lowest within reach" is the lowest across, not down the hill
    ys, xs = np.nonzero(mask)
    A = np.stack([grid.xs[xs], grid.ys[ys], np.ones(len(xs))], axis=1)
    coef, *_ = np.linalg.lstsq(A, h[ys, xs].astype(np.float64), rcond=None)
    detr = h - (coef[0] * grid.X + coef[1] * grid.Y + coef[2]).astype(np.float32)
    # the minimum filter runs on a coarse grid (16 cm): the crown is a broad shape
    step = max(1, int(round(0.16 / grid.dot)))
    big = np.where(mask, detr, 1e3).astype(np.float32)
    ph, pw = (-big.shape[0]) % step, (-big.shape[1]) % step
    padded = np.pad(big, ((0, ph), (0, pw)), mode='constant', constant_values=1e3)
    small = padded.reshape(padded.shape[0] // step, step, padded.shape[1] // step, step).min(axis=(1, 3))          # true minimum of each 16 cm block
    reach = int(round(spec['reach_m'] / (grid.dot * step)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * reach + 1, 2 * reach + 1))
    low = cv2.erode(small, kernel)
    low_full = cv2.resize(low, (padded.shape[1], padded.shape[0]), interpolation=cv2.INTER_LINEAR)[:grid.height, :grid.width]
    low_full = np.where(low_full > 5e2, detr, low_full)
    out = _clip01((detr - low_full - spec['allow_m']) / spec['scale_m'])
    out[~mask] = 0.0
    return out


def distance_pictures(geo, settings, grid, h, has, timer):
    """wall_dist, prop_dist, inside_corner, step_foot, vertical_foot, cover_dist."""
    g = settings.geometry
    reach = g.get('wall_reach_m', WALL_REACH_DEFAULT)
    solids = geo.tree(g.get('solids_for_wall_dist', []))
    props = geo.tree(g.get('prop_roles', []))
    feet_roles = (g.get('vertical_feet') or {}).get('roles', [])
    feet = geo.tree(feet_roles)
    covers = geo.tree([(g.get('covers') or {}).get('role')]) if (g.get('covers') or {}).get('role') in settings.roles else None
    z = h + 0.03
    d_solid = geom.nearest_distances(solids, grid, z, reach, has) if solids else np.full(grid.shape(), reach, np.float32)
    timer.mark('wall distance')
    d_prop = geom.nearest_distances(props, grid, z, reach, has) if props else np.full(grid.shape(), reach, np.float32)
    d_feet = geom.nearest_distances(feet, grid, z, 0.6, has) if feet else np.full(grid.shape(), 0.6, np.float32)
    d_cover = geom.nearest_distances(covers, grid, z, reach, has) if covers else np.full(grid.shape(), reach, np.float32)
    timer.mark('prop, feet, cover distances')
    # inside corners: many of 12 short sideways rays blocked although the nearest wall is far
    all_tree = geo.tree(list(g.get('solids_for_wall_dist', [])) + list(g.get('prop_roles', [])) + list(feet_roles))
    d_any = np.minimum.reduce([d_solid, d_prop, np.where(d_feet < 0.6, d_feet, 9.0)])
    ray_r, rays, ray_h = 0.45, 12, 0.25
    directions = [Vector((math.cos(2 * math.pi * k / rays), math.sin(2 * math.pi * k / rays), 0.0)) for k in range(rays)]
    blocked = np.zeros(grid.shape(), np.float32)
    candidates = np.argwhere(has & (d_any < ray_r) & (d_any > 0.015))
    if all_tree is not None:
        for j, i in candidates:
            origin = Vector((grid.xs[i], grid.ys[j], float(h[j, i]) + ray_h))
            n = 0
            for d in directions:
                if all_tree.ray_cast(origin, d, ray_r)[0] is not None:
                    n += 1
            blocked[j, i] = n / rays
    planar = np.where(d_any < ray_r, np.arccos(np.clip(d_any / ray_r, 0, 1)) / math.pi, 0.0)
    corner = np.clip((blocked - planar - 0.08) / 0.30, 0, 1) * (d_any < ray_r)
    timer.mark(f'inside corners ({len(candidates)} dots)')
    # steps' feet: a soft spot round every entrance; vertical feet: pipes, posts and other standing iron
    spec = g.get('entrances') or {}
    rx, ry = spec.get('foot_radius_m', [0.55, 0.65])
    foot = np.zeros(grid.shape(), np.float32)
    for ex, ey, ez, name in entrances(geo, settings):
        foot = np.maximum(foot, np.exp(-(((grid.X - ex) / rx) ** 2 + ((grid.Y - ey) / ry) ** 2)))
    radius = (g.get('vertical_feet') or {}).get('radius_m', 0.2)
    vfoot = np.exp(-(d_feet / radius) ** 2) * (d_feet < 0.6)
    out = dict(wall_dist=d_solid / reach, prop_dist=d_prop / reach, inside_corner=corner, step_foot=foot, vertical_foot=vfoot, cover_dist=d_cover / reach)
    for name in out:
        out[name] = _clip01(out[name])
        if name in ('inside_corner', 'step_foot', 'vertical_foot'):
            out[name][~has] = 0.0
        else:
            out[name][~has] = 1.0
    out['_d_solid_m'] = d_solid
    return out


def seam_picture(role_id, has, grid, reach_m=0.5):
    import cv2
    ids = role_id.astype(np.int32)
    boundary = np.zeros(grid.shape(), np.uint8)
    for dy, dx in ((0, 1), (1, 0)):
        a = ids[dy:, dx:]
        b = ids[:ids.shape[0] - dy, :ids.shape[1] - dx]
        diff = (a != b) & (a > 0) & (b > 0)
        boundary[dy:, dx:][diff] = 1
        boundary[:ids.shape[0] - dy, :ids.shape[1] - dx][diff] = 1
    if boundary.sum() == 0:
        return np.ones(grid.shape(), np.float32), boundary
    dist = cv2.distanceTransform((1 - boundary).astype(np.uint8), cv2.DIST_L2, 5) * grid.dot
    out = _clip01(dist / reach_m)
    out[~has] = 1.0
    return out, boundary


def water_pictures(settings, grid, h, has):
    spec = settings.geometry.get('water')
    if not spec:
        return np.ones(grid.shape(), np.float32), np.ones(grid.shape(), np.float32), None
    import cv2
    level = spec['level_z']
    water = has & (h < level)
    if water.any() and (~water).any():
        dist_to_water = cv2.distanceTransform((~water).astype(np.uint8), cv2.DIST_L2, 5) * grid.dot
    else:
        dist_to_water = np.full(grid.shape(), 1.5, np.float32)
    water_dist = _clip01(dist_to_water / 1.5)
    above = _clip01((h - level) / 1.0)
    above[~has] = 1.0
    return water_dist, above, water


def make(geo, settings, timer):
    """Everything on the normal grid. Returns (grid, arrays dict, stats dict)."""
    grid = Grid.from_settings(settings, 'dot_m')
    h, has, role_id, role_names = ground_height(geo, settings, grid, timer)
    low_spec = settings.geometry.get('lowness', {'radius_m': 1.0, 'scale_m': 0.05})
    arrays = dict(ground_height=h, has_ground=has, ground_role=role_id)
    arrays['slope'] = slope_picture(h, has, grid)
    arrays['lowness'] = lowness_picture(h, has, grid, low_spec['radius_m'], low_spec['scale_m'])
    arrays['crown'] = crown_picture(h, has, role_id, role_names, settings, grid)
    timer.mark('slope, lowness, crown')
    dist = distance_pictures(geo, settings, grid, h, has, timer)
    arrays.update(dist)
    arrays['seam_dist'], seam_boundary = seam_picture(role_id, has, grid)
    arrays['water_dist'], arrays['above_water'], water = water_pictures(settings, grid, h, has)
    timer.mark('seams, water')
    stats = dict(role_names=role_names, ground_dots=int(has.sum()), size=[grid.width, grid.height])
    return grid, arrays, stats


# ------------------------------------------------------------------------------------------------------------------------------- the fine grid
def components(tris):
    """Connected pieces of a triangle list by shared vertices: returns an array with the piece number of every triangle."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for t in tris:
        r = find(int(t[0]))
        for v in (int(t[1]), int(t[2])):
            rv = find(v)
            if rv != r:
                parent[rv] = r
    roots = {}
    labels = np.zeros(len(tris), np.int32)
    for k, t in enumerate(tris):
        labels[k] = roots.setdefault(find(int(t[0])), len(roots) + 1)
    return labels, len(roots)


def fill_triangles(image, grid, verts_xy, tris, value):
    import cv2
    for t in tris:
        pts = np.array([[(verts_xy[v][0] - grid.x0) / grid.dot, (verts_xy[v][1] - grid.y0) / grid.dot] for v in t], np.float32)
        cv2.fillConvexPoly(image, np.round(pts * 16).astype(np.int32), value, lineType=cv2.LINE_8, shift=4)


def fine_pictures(geo, settings, coarse_grid, arrays, entrance_list, timer):
    """step_top, step_edge, edge_dist, piece_gap on the fine grid. Returns (fine grid, dict)."""
    import cv2
    g = settings.geometry
    fine = Grid.from_settings(settings, 'fine_dot_m')
    h_fine = cv2.resize(arrays['ground_height'], (fine.width, fine.height), interpolation=cv2.INTER_LINEAR)
    has_fine = cv2.resize(arrays['has_ground'].astype(np.uint8), (fine.width, fine.height), interpolation=cv2.INTER_NEAREST) > 0
    out = {}
    # ---- steps: up-facing faces of the step roles at least min_height above the ground, near an entrance
    spec = g.get('steps') or {}
    tread = np.zeros(fine.shape(), np.uint8)
    steps_data = geo.triangles(spec.get('from', [])) if spec else None
    step_count = 0
    if steps_data is not None:
        v, t = steps_data[0], steps_data[1]
        n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
        area = np.linalg.norm(n, axis=1) * 0.5
        up = (n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12) >= 0.9) & (area > 1e-5)
        centre = (v[t[:, 0]] + v[t[:, 1]] + v[t[:, 2]]) / 3.0
        ci = np.clip(((centre[:, 0] - fine.x0) / fine.dot).astype(int), 0, fine.width - 1)
        cj = np.clip(((centre[:, 1] - fine.y0) / fine.dot).astype(int), 0, fine.height - 1)
        above = centre[:, 2] - h_fine[cj, ci]
        ok = up & (above >= spec.get('min_height_m', 0.05)) & (above <= spec.get('max_height_m', 1e9)) & has_fine[cj, ci]      # max_height_m (integrator, round 1): sills, lintels and ridges near a door are not treads
        if spec.get('near_entrances') and entrance_list:
            near = np.zeros(len(t), bool)
            for ex, ey, ez, _ in entrance_list:
                near |= np.hypot(centre[:, 0] - ex, centre[:, 1] - ey) <= spec.get('within_m', 0.9)
            ok &= near
        elif spec.get('near_entrances'):
            ok &= False
        if spec.get('max_extent_m'):          # a step tread is short: a long strip along a wall (a plinth or threshold course) is not a tread (integrator, round 1)
            xy = v[t][:, :, :2]
            extent = np.maximum(xy[:, :, 0].max(axis=1) - xy[:, :, 0].min(axis=1), xy[:, :, 1].max(axis=1) - xy[:, :, 1].min(axis=1))
            ok &= extent <= spec['max_extent_m']
        sel = np.nonzero(ok)[0]
        step_count = int(len(sel))
        fill_triangles(tread, fine, v[:, :2], t[sel], 1)
    out['step_top'] = tread.astype(np.float32)
    # the nosing: tread dots next to a non-tread dot that is not against a wall
    if tread.any():
        wall_d = cv2.resize(arrays['_d_solid_m'], (fine.width, fine.height), interpolation=cv2.INTER_LINEAR)
        edge = (cv2.dilate(tread, np.ones((3, 3), np.uint8)) - cv2.erode(tread, np.ones((3, 3), np.uint8))) > 0
        nosing = edge & (tread > 0) & (wall_d > 0.06)
        if nosing.any():
            dist = cv2.distanceTransform((~nosing).astype(np.uint8), cv2.DIST_L2, 5) * fine.dot
            out['step_edge'] = np.where(tread > 0, _clip01(dist / 0.25), 1.0).astype(np.float32)
        else:
            out['step_edge'] = np.ones(fine.shape(), np.float32)
    else:
        out['step_edge'] = np.ones(fine.shape(), np.float32)
    timer.mark(f'steps ({step_count} tread triangles)')
    # ---- outward sharp edges of the ground, kerb and step roles (convex, more than 35 degrees)
    edge_pic = np.zeros(fine.shape(), np.uint8)
    edge_roles = list(g['ground']['roles']) + list(spec.get('from', []))
    edge_dots = convex_edges(geo, edge_roles, fine, edge_pic)
    if edge_pic.any():
        dist = cv2.distanceTransform((1 - edge_pic).astype(np.uint8), cv2.DIST_L2, 5) * fine.dot
        out['edge_dist'] = _clip01(dist / 0.3)
    else:
        out['edge_dist'] = np.ones(fine.shape(), np.float32)
    out['edge_dist'][~has_fine & ~(tread > 0)] = 1.0
    timer.mark(f'sharp edges ({edge_dots} edges)')
    # ---- the boundary between two separate stones of one role
    gap = np.ones(fine.shape(), np.float32)
    pieces_found = {}
    for role in settings.expand_roles(g['ground']['roles']):
        data = geo.triangles([role])
        if data is None:
            continue
        v, t = data[0], data[1]
        n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
        nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
        labels, count = components(t)
        pieces_found[role] = count
        if count < 2:
            continue
        # per-piece footprint (up-facing faces); piece numbers modulo 250
        ids = np.zeros(fine.shape(), np.uint8)
        sel = np.nonzero(nz > 0.5)[0]
        for piece in range(1, count + 1):
            mine = sel[labels[sel] == piece]
            fill_triangles(ids, fine, v[:, :2], t[mine], (piece % 250) + 1)
        boundary = np.zeros(fine.shape(), np.uint8)
        for dy, dx in ((0, 2), (2, 0)):
            a = ids[dy:, dx:]
            b = ids[:ids.shape[0] - dy, :ids.shape[1] - dx]
            diff = (a != b) & (a > 0) & (b > 0)
            boundary[dy:, dx:][diff] = 1
        # the free ends of a row of stones: where a stone's footprint stops next to nothing but another piece would continue (gaps of one or two dots between stones)
        closed = cv2.morphologyEx((ids > 0).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        joins = (closed > 0) & (ids == 0)
        boundary |= joins.astype(np.uint8)
        if boundary.any():
            dist = cv2.distanceTransform((1 - boundary).astype(np.uint8), cv2.DIST_L2, 5) * fine.dot
            role_mask = ids > 0
            gap = np.where(role_mask | joins, np.minimum(gap, _clip01(dist / 0.3)), gap)
    out['piece_gap'] = gap.astype(np.float32)
    timer.mark(f'stone gaps (pieces per role: {pieces_found})')
    stats = dict(step_tread_triangles=step_count, pieces=pieces_found, edges=edge_dots)
    return fine, out, stats


def convex_edges(geo, roles, grid, canvas):
    """Draws (into canvas) the plan view of every convex, outward-pointing edge sharper than 35 degrees of the roles' meshes that has an up-facing face; returns how many edges."""
    import bmesh
    import cv2
    import bpy
    count = 0
    depsgraph = geo.depsgraph
    wanted = set(geo.settings.expand_roles(roles))
    for inst in depsgraph.object_instances:
        obj = inst.object
        if obj.type != 'MESH':
            continue
        host = inst.parent if (inst.is_instance and inst.parent is not None) else obj
        name = host.original.name
        if geo.role_map.primary.get(name) not in wanted:
            continue
        mesh = obj.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.transform(inst.matrix_world)
        bm.normal_update()
        for edge in bm.edges:
            if len(edge.link_faces) != 2:
                continue
            f1, f2 = edge.link_faces
            if f1.normal.dot(f2.normal) > math.cos(math.radians(35.0)):
                continue
            if max(f1.normal.z, f2.normal.z) < 0.5:
                continue
            # convex: the far vertex of face 2 lies below face 1's plane (and the other way round)
            p = edge.verts[0].co
            opposite = [v for v in f2.verts if v not in edge.verts]
            if not opposite or f1.normal.dot(opposite[0].co - p) >= -1e-6:
                continue
            a, b = edge.verts[0].co, edge.verts[1].co
            pa = (int(round((a.x - grid.x0) / grid.dot)), int(round((a.y - grid.y0) / grid.dot)))
            pb = (int(round((b.x - grid.x0) / grid.dot)), int(round((b.y - grid.y0) / grid.dot)))
            cv2.line(canvas, pa, pb, 1, 1)
            count += 1
        bm.free()
        obj.to_mesh_clear()
    return count
