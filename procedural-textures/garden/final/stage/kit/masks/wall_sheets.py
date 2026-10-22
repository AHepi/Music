# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WALL SHEETS: one flat picture per wall mesh, made in the wall's OWN frame: u across the front, v up from the floor, 50 dots a metre (2 cm). Houses that share one mesh share
# one sheet. Everything a wall layer needs that depends on the wall's shape and its surroundings is in the sheet:
#   height (metres above the ground at the wall foot), sheltered (rain cannot reach), drip, drip_dist, drip_kind (run-off lines, from the ledge finder), corner, reveal
#   (distance to a wall corner or opening edge; how deep inside an opening), and at 8 cm: openness, shade, dampness, moss_site, algae_site, lichen_site.
# A trim object (sills, steps) reads the sheet of its own walls (the set's frames[].share_sheet_with), because it stands in the same frame.
# The shader uses a sheet only where the surface faces the frame (within 25 degrees); elsewhere frame_valid is 0 and the bus falls back to the ground plan (gable ends, roofs).
# Frames are described by the set file (geometry.frames with kind 'wall_front'): roles, sheet_per ('mesh' or 'object'), dots_per_m, share_sheet_with.
import math
import re

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import geom, ledges as ledge_module, shade as shade_module
from .geom import smoothstep

FRONT_COS = math.cos(math.radians(25.0))


class Sheet:
    def __init__(self, sheet_id, name):
        self.id = sheet_id
        self.name = name
        self.objects = []
        self.arrays = {}
        self.coarse = {}
        self.sources = []
        self.pipe_info = {}
        self.meta = {}


def _eval_local_mesh(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    mesh.calc_loop_triangles()
    co = np.empty(len(mesh.vertices) * 3, np.float64)
    mesh.vertices.foreach_get('co', co)
    tri = np.empty(len(mesh.loop_triangles) * 3, np.int64)
    mesh.loop_triangles.foreach_get('vertices', tri)
    verts, tris = co.reshape(-1, 3), tri.reshape(-1, 3)
    ev.to_mesh_clear()
    return verts, tris


def _same_frame(a, b, tol=1e-3):
    return np.abs(np.array(a.matrix_world) - np.array(b.matrix_world)).max() < tol


def find_frames(geo, settings, role_map):
    """Groups the wall objects into sheets. Returns (sheets [Sheet with .rep and .frame spec], frame_of_object {object name: sheet id})."""
    sheets, frame_of = [], {}
    shared = []
    for spec in settings.geometry.get('frames', []):
        if spec.get('kind') != 'wall_front':
            continue
        if 'share_sheet_with' in spec:
            shared.append(spec)
            continue
        groups = {}
        for name in role_map.objects_of(spec['roles']):
            obj = bpy.data.objects[name]
            key = obj.data.name if spec.get('sheet_per', 'mesh') == 'mesh' and obj.data is not None else name
            groups.setdefault(key, []).append(name)
        for key, names in sorted(groups.items()):
            sheet = Sheet(len(sheets) + 1, key)
            sheet.objects = sorted(names)
            sheet.spec = spec
            sheets.append(sheet)
            for n in names:
                frame_of[n] = sheet.id
    for spec in shared:
        pattern, use = spec['share_sheet_with']['object_regex'], spec['share_sheet_with']['use']
        for name in role_map.objects_of(spec['roles']):
            m = re.match(pattern, name)
            if not m:
                continue
            target = m.expand(use)
            if target in frame_of:
                frame_of[name] = frame_of[target]
    return sheets, frame_of


def _choose_front(nn, area, matrix, to_centre):
    """The old scoring of the four candidate fronts, unchanged: returns (best, fallback) as (weight, axis, sign, facing) or None."""
    best = None
    fallback = None
    length = float(np.linalg.norm(to_centre))
    for axis in (0, 1):
        for sign in (1.0, -1.0):
            direction = np.zeros(3)
            direction[axis] = sign
            world_dir = matrix[:3, :3] @ direction
            alignment = float(np.dot(world_dir, to_centre) / max(length, 1e-9))          # 1 = straight toward the ground
            facing = (nn[:, axis] * sign >= FRONT_COS) & (np.abs(nn[:, 2]) < 0.2)
            weight = float(area[facing].sum()) * max(alignment, 0.0)
            if alignment < 0.5:
                if fallback is None or weight > fallback[0]:
                    fallback = (weight, axis, sign, facing)
                continue
            if best is None or weight > best[0]:
                best = (weight, axis, sign, facing)
    return best, fallback


_DIRECTIONS = {'+x': (1.0, 0.0), '-x': (-1.0, 0.0), '+y': (0.0, 1.0), '-y': (0.0, -1.0)}


def forced_front(spec, object_name):
    """The explicit front a set file gives a wall: geometry.frames[].front = {"<object name regex>": "-y" | "+x" | ... | "toward:X,Y" | "-y@6.55"} (WORLD directions; "toward:X,Y" = the
    front faces that world point; a trailing "@N" = the wall plane sits at world coordinate N (metres) along that axis, for a mesh made of several boxes whose biggest plane is not
    the visible one). Returns {'dir': (dx, dy) or None, 'toward': (x, y) or None, 'plane': N or None}, or None when the set says nothing about this object."""
    for pattern, how in (spec.get('front') or {}).items():
        if not re.match(pattern, object_name):
            continue
        plane = None
        if isinstance(how, str) and '@' in how:
            how, text = how.split('@', 1)
            plane = float(text)
        if how in _DIRECTIONS:
            return {'dir': _DIRECTIONS[how], 'toward': None, 'plane': plane}
        if isinstance(how, str) and how.startswith('toward:'):
            x, y = (float(v) for v in how[7:].split(','))
            return {'dir': None, 'toward': (x, y), 'plane': plane}
        raise ValueError(f'geometry.frames front {how!r} for {pattern!r}: use "+x", "-x", "+y", "-y" or "toward:X,Y", optionally followed by "@N"')
    return None


def _front_of(verts, tris, matrix, toward_xy, forced=None, fallback_xy=None):
    """The front of a wall mesh: the horizontal local axis direction (+-x, +-y) that has the most near-vertical face area and points toward `centre_xy` (world). Returns
    (axis index 0/1, sign, plane coordinate, top z). toward_xy: the world (x, y) the front must point to (the nearest ground seen from the mesh's middle).
    forced: an explicit front from the set file (forced_front); it replaces the ground hint. fallback_xy: a world (x, y) (the set's first camera) tried only when the old rule found
    no front (earth running under the wall makes the nearest ground point straight below it, so the hint is undecided). Where the old rule finds a front, nothing changes."""
    n = np.cross(verts[tris[:, 1]] - verts[tris[:, 0]], verts[tris[:, 2]] - verts[tris[:, 0]])
    area = np.linalg.norm(n, axis=1) * 0.5
    nn = n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
    centre = (verts[tris[:, 0]] + verts[tris[:, 1]] + verts[tris[:, 2]]) / 3.0
    origin = matrix[:3, 3]
    middle = matrix[:3, :3] @ ((verts.min(axis=0) + verts.max(axis=0)) * 0.5) + origin
    to_centre = np.array([toward_xy[0] - middle[0], toward_xy[1] - middle[1], 0.0])
    plane_hint = None
    if forced is not None:
        plane_hint = forced['plane']
        if forced['dir'] is not None:
            to_centre = np.array([forced['dir'][0], forced['dir'][1], 0.0])
        elif forced['toward'] is not None:
            to_centre = np.array([forced['toward'][0] - middle[0], forced['toward'][1] - middle[1], 0.0])
    best, fallback = _choose_front(nn, area, matrix, to_centre)
    if best is None and fallback is not None and fallback[0] > 0:
        best = fallback
    if best is None and fallback_xy is not None and forced is None:           # the old rule found nothing: try again toward the fallback point
        to_centre = np.array([fallback_xy[0] - middle[0], fallback_xy[1] - middle[1], 0.0])
        best, fallback = _choose_front(nn, area, matrix, to_centre)
        if best is None and fallback is not None and fallback[0] > 0:
            best = fallback
    if best is None:
        raise RuntimeError('no wall face points toward the ground plan (give this wall a front in geometry.frames[].front)')
    _, axis, sign, facing = best
    coords = centre[facing, axis]
    w = area[facing]
    order = np.argsort(coords)
    cum = np.cumsum(w[order])
    plane = float(coords[order][np.searchsorted(cum, cum[-1] * 0.5)])
    # the main plane: the area-weighted mode of the coordinate (round to 2 cm) is more stable than the median when reveals are big
    rounded = np.round(coords / 0.02) * 0.02
    uniq, inv = np.unique(rounded, return_inverse=True)
    plane = float(uniq[np.argmax(np.bincount(inv.ravel(), weights=w))])
    if plane_hint is not None:                                                # the set says which plane is the visible one (a mesh of several boxes; world-aligned meshes only)
        scale = float(matrix[axis, axis])
        if abs(scale) > 1e-6 and abs(matrix[1 - axis, axis]) < 1e-6 and abs(matrix[2, axis]) < 1e-6:
            plane = float(uniq[np.argmin(np.abs(origin[axis] + scale * uniq - plane_hint))])
    on_plane = np.abs(verts[:, axis] - plane) < 0.03
    return axis, sign, plane, float(verts[on_plane, 2].max()) if on_plane.any() else float(verts[:, 2].max())


def build_sheet(sheet, geo, settings, role_map, gp, grid, timer):
    """Fills one Sheet: arrays at 2 cm (sheltered, drip, drip_dist, drip_kind, corner, reveal, height) and at 8 cm (openness, shade, dampness, moss_site, algae_site, lichen_site)."""
    import cv2
    depsgraph = geo.depsgraph
    rep = bpy.data.objects[sheet.objects[0]]
    matrix = np.array(rep.matrix_world)
    M = Matrix(rep.matrix_world)
    dpm = float(sheet.spec.get('dots_per_m', 50))
    verts, tris = _eval_local_mesh(rep, depsgraph)
    ground_tree = geo.tree(settings.geometry['ground']['roles'])
    middle_world = M @ Vector(((verts.min(axis=0) + verts.max(axis=0)) * 0.5).tolist())
    nearest = ground_tree.find_nearest(Vector((middle_world.x, middle_world.y, middle_world.z - 2.0)))
    cams = (settings.get('cameras') or [])
    fallback_xy = tuple(cams[0]['location'][:2]) if cams and cams[0].get('location') else None
    axis, sign, plane, top_z = _front_of(verts, tris, matrix, (nearest[0].x, nearest[0].y), forced=forced_front(sheet.spec, rep.name), fallback_xy=fallback_xy)
    u_axis_index = 1 - axis
    on_plane = np.abs(verts[:, axis] - plane) < 0.03
    # GARDEN FINAL PATCH 6 (integration step): the shapes stage battered the garden walls (their garden face leans back about 3.5 degrees, one flat plane). No vertex lies
    # within 3 cm of the mid-height plane then, and the sheet failed ('zero-size array'). In that case the extents come from the vertices of the front-facing triangles
    # within 25 cm of the plane, and the sheet dots are moved onto the real (leaning) face by a horizontal ray, so height, shelter and reveal are read at the true surface.
    lean = not on_plane.any()
    plane_tol = 0.03
    if lean:
        nrm = np.cross(verts[tris[:, 1]] - verts[tris[:, 0]], verts[tris[:, 2]] - verts[tris[:, 0]])
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1)[:, None], 1e-12)
        facing_tris = nrm[:, axis] * sign > math.cos(math.radians(12.0))
        on_plane = np.zeros(len(verts), bool)
        on_plane[np.unique(tris[facing_tris].ravel())] = True
        on_plane &= np.abs(verts[:, axis] - plane) < 0.25
        plane_tol = 0.25
        print('[reader] PATCH 6: leaning wall front for', rep.name, 'vertices used', int(on_plane.sum()), flush=True)
    u_lo, u_hi = float(verts[on_plane, u_axis_index].min()) - 0.05, float(verts[on_plane, u_axis_index].max()) + 0.05
    v_lo, v_hi = float(verts[on_plane, 2].min()) - 0.05, float(verts[on_plane, 2].max()) + 0.05
    nu, nv = int(math.ceil((u_hi - u_lo) * dpm)), int(math.ceil((v_hi - v_lo) * dpm))
    us = u_lo + (np.arange(nu) + 0.5) / dpm
    vs = v_lo + (np.arange(nv) + 0.5) / dpm
    sheet.meta = dict(object=rep.name, objects=sheet.objects, matrix_world=matrix.tolist(), front_axis=int(axis), front_sign=float(sign), plane=plane, u_axis=int(u_axis_index),
                      u_range=[u_lo, u_hi], v_range=[v_lo, v_hi], dots_per_m=dpm, size=[nu, nv], top_z=top_z)
    # local -> world for the whole sheet
    local = np.zeros((nv, nu, 3))
    local[..., u_axis_index] = us[None, :]
    local[..., axis] = plane
    local[..., 2] = vs[:, None]
    world = local @ matrix[:3, :3].T + matrix[:3, 3]
    n_local = np.zeros(3)
    n_local[axis] = sign
    n_world = Vector(matrix[:3, :3] @ n_local).normalized()
    if lean:                                                                   # PATCH 6: put every dot on the real face
        face_tree = geo.tree(sheet.spec['roles'])
        moved = 0
        for j in range(nv):
            for i in range(nu):
                hit = face_tree.ray_cast(Vector(world[j, i]) + n_world * 0.3, -n_world, 0.6)
                if hit[0] is not None:
                    world[j, i] = (hit[0].x, hit[0].y, hit[0].z)
                    moved += 1
        print('[reader] PATCH 6: dots moved onto the leaning face:', moved, 'of', nu * nv, flush=True)
    # ground height under every column (a ray from above through the column's x and y)
    col_ground = np.zeros(nu)
    for i in range(nu):
        hit = ground_tree.ray_cast(Vector((world[0, i, 0], world[0, i, 1], 80.0)), Vector((0, 0, -1)), 200.0)
        col_ground[i] = hit[0].z if hit[0] is not None else world[0, i, 2] - 0.0
    height = (world[..., 2] - col_ground[None, :]).astype(np.float32)
    # ---- sheltered: share of 24 rays within 35 degrees of straight up that meet something overhanging within reach
    all_roles = [r for r in settings.roles if r not in settings.geometry['ground']['roles']]
    solids = geo.tree(all_roles)
    reach = (settings.geometry.get('ledges') or {}).get('reach_m', 1.2)
    dirs = geom.cone_directions(24, 35.0)
    sheltered = np.zeros((nv, nu), np.float32)
    ray = solids.ray_cast
    for j in range(nv):
        for i in range(nu):
            origin = Vector(world[j, i]) + n_world * 0.03
            n = 0
            for d in dirs:
                hit = ray(origin, d, reach)
                if hit[0] is not None and abs(hit[1].z) > 0.3:
                    n += 1
            sheltered[j, i] = n / len(dirs)
    timer.mark(f'sheet {sheet.name}: sheltered ({nu}x{nv})')
    # ---- reveal: how deep behind the face the first wall surface is
    wall_tree = geo.tree(sheet.spec['roles'])
    reveal = np.zeros((nv, nu), np.float32)
    back = -n_world
    for j in range(nv):
        for i in range(nu):
            origin = Vector(world[j, i]) + n_world * 0.03
            hit = wall_tree.ray_cast(origin, back, 0.5)
            reveal[j, i] = 1.0 if hit[0] is None else min(1.0, max(0.0, (hit[3] - 0.03) / 0.3))
    timer.mark(f'sheet {sheet.name}: reveal')
    # ---- the ledge finder on the meshes that stand in this frame (same placement): walls, trim, pipes
    spec_l = settings.geometry.get('ledges') or {}
    members = []
    for name in role_map.objects_of(spec_l.get('sources_from_roles', [])):
        obj = bpy.data.objects[name]
        if _same_frame(obj, rep):
            members.append(obj)
    sources, pipe_info = [], {}
    for obj in members:
        v, t = _eval_local_mesh(obj, depsgraph)
        if role_map.primary.get(obj.name, '').startswith('iron'):
            s, info = ledge_module.find_pipe_sources(v, plane, sign, spec_l, top_z)
            sources += s
            pipe_info = info or pipe_info
        else:
            sources += ledge_module.find_ledges(v, t, plane, sign, spec_l, top_z, u_hi - u_lo)
    drip, drip_dist, drip_kind = ledge_module.drip_pictures(sources, us, vs, spec_l.get('drip_length_m', 1.2))
    timer.mark(f'sheet {sheet.name}: ledges ({len(sources)} sources)')
    # ---- corners and opening edges: convex edges of the wall mesh lying in (or just behind) the front plane
    canvas = np.zeros((nv, nu), np.uint8)
    import bmesh
    ev = rep.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        f1, f2 = edge.link_faces
        if f1.normal.dot(f2.normal) > math.cos(math.radians(35.0)):
            continue
        a, b = edge.verts[0].co, edge.verts[1].co
        fa, fb = sign * (a[axis] - plane), sign * (b[axis] - plane)
        if max(fa, fb) > plane_tol or min(fa, fb) < -0.3 - (plane_tol - 0.03):
            continue
        pa = (int(round((a[u_axis_index] - u_lo) * dpm)), int(round((a[2] - v_lo) * dpm)))
        pb = (int(round((b[u_axis_index] - u_lo) * dpm)), int(round((b[2] - v_lo) * dpm)))
        cv2.line(canvas, pa, pb, 1, 1)
    bm.free()
    ev.to_mesh_clear()
    if canvas.any():
        dist = cv2.distanceTransform((1 - canvas).astype(np.uint8), cv2.DIST_L2, 5) / dpm
        corner = np.clip(dist / 0.4, 0, 1).astype(np.float32)
    else:
        corner = np.ones((nv, nu), np.float32)
    timer.mark(f'sheet {sheet.name}: corners')
    sheet.arrays = dict(height=height, sheltered=sheltered, drip=drip, drip_dist=drip_dist, drip_kind=drip_kind, corner=corner, reveal=reveal)
    sheet.sources = sources
    sheet.pipe_info = pipe_info
    # ---- 8 cm pictures: openness, sun shade, shade, dampness, habitat
    stride = max(1, int(round(0.08 * dpm)))
    cu, cv_ = us[::stride], vs[::stride]
    cpts, cnorm = [], []
    for j in range(0, nv, stride):
        for i in range(0, nu, stride):
            cpts.append(Vector(world[j, i]))
            cnorm.append(n_world)
    shade_cfg = settings.get('shade') or {'mode': 'none'}
    wo, ws = shade_module.weights_of(shade_cfg)
    blocker = shade_module.blockers(geo, settings)
    extra = geo.extra_tree(shade_cfg.get('extra_blockers', {}).get('objects', [])) if shade_cfg.get('extra_blockers') else None
    extra_w = (shade_cfg.get('extra_blockers') or {}).get('block', 0.0)
    shape_c = (len(range(0, nv, stride)), len(range(0, nu, stride)))
    openness = np.full(shape_c, 0.5, np.float32)
    sun_shade = np.full(shape_c, 0.5, np.float32)
    if wo > 0:
        o = shade_module.openness_at(blocker, cpts, cnorm, int(shade_cfg.get('openness_rays', 48)), float(shade_cfg.get('ray_length_m', 40.0)), extra, extra_w)
        openness = o.reshape(shape_c)
        openness = shade_module.stretch(openness, None)
    if ws > 0:
        suns = shade_module.sun_positions(shade_cfg)
        e = shade_module.sun_exposure_at(blocker, cpts, cnorm, suns, 60.0, extra, extra_w)
        sun_shade = 1.0 - shade_module.stretch(e.reshape(shape_c), None)
    shade_c = np.clip(wo * (1 - openness) + ws * sun_shade, 0, 1).astype(np.float32) if (wo + ws) > 0 else np.full(shape_c, 0.5, np.float32)
    timer.mark(f'sheet {sheet.name}: shade (8 cm)')

    def down(a):
        return cv2.resize(a, (shape_c[1], shape_c[0]), interpolation=cv2.INTER_AREA)
    h_c, drip_c, shelter_c, kind_c = down(height), down(drip), down(sheltered), down(drip_kind)
    damp = settings.get('dampness') or {}
    w = damp.get('weights', {})
    foot_reach = damp.get('wall_foot_reach_m', 0.5)
    foot = np.clip(1.0 - np.maximum(h_c, 0.0) / foot_reach, 0, 1)
    water = np.zeros(shape_c, np.float32)
    if settings.geometry.get('water'):
        wd = np.interp(world[0, ::stride, 0], [grid.x0, grid.x1], [0, 1])
        xi = np.clip(((world[0, ::stride, 0] - grid.x0) / grid.dot).astype(int), 0, grid.width - 1)
        yi = np.clip(((world[0, ::stride, 1] - grid.y0) / grid.dot).astype(int), 0, grid.height - 1)
        water = np.broadcast_to(1.0 - gp['water_dist'][yi, xi], shape_c).astype(np.float32)
    low = np.full(shape_c, 0.3, np.float32)
    dampness = np.clip(w.get('wall_foot', 0) * foot + w.get('drip', 0) * drip_c + w.get('water', 0) * water + w.get('lowness', 0) * low + w.get('shelter', 0) * shelter_c
                       + w.get('shade', 0) * shade_c, 0, 1).astype(np.float32)
    hab = settings.get('habitat') or {}
    moss, algae, lichen = hab.get('moss', {}), hab.get('algae', {}), hab.get('lichen', {})
    edge = np.maximum(np.clip(1.0 - np.maximum(h_c, 0.0) / (2.0 * moss.get('edge_reach_m', 0.5)), 0, 1), 0.6 * drip_c * (1.0 - down(drip_dist)))
    moss_site = np.clip(moss.get('dampness', 0.45) * dampness + moss.get('shade', 0.30) * shade_c + moss.get('edge', 0.25) * edge, 0, 1).astype(np.float32)
    outlet = drip_c * ((np.abs(kind_c - 0.6) < 0.15) | (np.abs(kind_c - 0.8) < 0.15))
    algae_site = np.clip(algae.get('dampness', 0.5) * dampness + algae.get('shade', 0.2) * shade_c + algae.get('pipe_outlets', 0.3) * outlet, 0, 1).astype(np.float32)
    if lichen.get('enabled'):
        north = lichen.get('north_bias', 0.6)
        lichen_site = np.clip(north * shade_c + (1 - north) * (1 - dampness), 0, 1).astype(np.float32)
    else:
        lichen_site = np.zeros(shape_c, np.float32)
    sheet.coarse = dict(openness=openness, shade=shade_c, dampness=dampness, moss_site=moss_site, algae_site=algae_site, lichen_site=lichen_site)
    sheet.meta['coarse_stride'] = stride
    sheet.meta['sources'] = [s.as_dict() for s in sources]
    sheet.meta['pipe'] = pipe_info
    return sheet
