# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE LEDGE FINDER: finds, from the real 3D shapes, every place where rain runs off a wall: window sills, lintels, string courses, eaves courses, step treads, the joints
# and feet of a downpipe, the ends of an eaves gutter. No typed numbers: an up-facing flat piece of the wall, trim or pipe meshes (normal within 25 degrees of straight up, at
# least min_width_m wide, at least min_area_m2 big, within in_front_m in front of or behind_m behind the wall face) is a LEDGE; a downpipe is found as the column where the
# pipe mesh is tall and thin. Everything is worked out in the wall mesh's own frame (across the front = u, up from the floor = z, out from the face = front axis).
# Also here: the ground-plan drip lines (the lower outer edge of every raised up-facing surface of the set's source roles, dropped to the ground) for the lines under eaves.
import math

import numpy as np

KIND_CODE = {'none': 0.0, 'ledge': 0.2, 'pipe_joint': 0.4, 'pipe_foot': 0.6, 'gutter_end': 0.8, 'eave': 0.8, 'cap': 1.0, 'canopy': 1.0, 'cap_overhang': 1.0, 'step': 0.2}


class Source:
    """One run-off source in a wall frame: where it is across the front (u0..u1), how high (z), how far out from the face (out), what kind."""

    def __init__(self, kind, z, u0, u1, out0, out1, area=0.0, name=''):
        self.kind, self.z, self.u0, self.u1, self.out0, self.out1, self.area, self.name = kind, float(z), float(u0), float(u1), float(out0), float(out1), float(area), name

    def as_dict(self):
        return dict(kind=self.kind, z=round(self.z, 3), u=[round(self.u0, 3), round(self.u1, 3)], out=[round(self.out0, 3), round(self.out1, 3)], width=round(self.u1 - self.u0, 3),
                    area=round(self.area, 3), name=self.name)


def weld_ids(verts, tol=1e-3):
    """An id per vertex such that vertices within tol share an id (so separate quads of one sill join up)."""
    key = np.round(verts / tol).astype(np.int64)
    _, inverse = np.unique(key, axis=0, return_inverse=True)
    return inverse.ravel()


def up_facing_components(verts, tris, up_cos=0.9, min_area=0.02):
    """Connected pieces (by welded vertices) of the up-facing triangles: returns [(triangle indices, area)] for pieces with area >= min_area."""
    n = np.cross(verts[tris[:, 1]] - verts[tris[:, 0]], verts[tris[:, 2]] - verts[tris[:, 0]])
    norm = np.linalg.norm(n, axis=1)
    nz = n[:, 2] / np.maximum(norm, 1e-12)
    sel = np.nonzero((nz >= up_cos) & (norm > 1e-9))[0]
    if len(sel) == 0:
        return []
    weld = weld_ids(verts)
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for k in sel:
        a, b, c = (int(weld[v]) for v in tris[k])
        ra = find(a)
        for v in (b, c):
            rv = find(v)
            if rv != ra:
                parent[rv] = ra
    groups = {}
    for k in sel:
        groups.setdefault(find(int(weld[tris[k][0]])), []).append(k)
    result = []
    for members in groups.values():
        members = np.array(members)
        area = float((norm[members] * 0.5).sum())
        if area >= min_area:
            result.append((members, area))
    return result


def find_ledges(local_verts, local_tris, plane, front_sign, settings_ledges, wall_top_z, sheet_width):
    """Ledges of one wall frame. local_verts/tris: the frame's meshes in the wall's own frame (x = out axis, y = across u axis, z up), with the front axis being x with sign front_sign
    (front_sign * (x - plane) = how far OUT from the wall face). Returns a list of Source (u = local y)."""
    spec = settings_ledges
    sources = []
    for members, area in up_facing_components(local_verts, local_tris, spec.get('up_normal_z_min', 0.9), spec.get('min_area_m2', 0.02)):
        pts = local_verts[local_tris[members].ravel()]
        u0, u1 = float(pts[:, 1].min()), float(pts[:, 1].max())
        out = front_sign * (pts[:, 0] - plane)
        out0, out1 = float(out.min()), float(out.max())
        z = float((pts[:, 2] * 1.0).mean())
        width = u1 - u0
        if width < spec.get('min_width_m', 0.25):
            continue
        if out1 < -spec.get('behind_m', 0.6) or out0 > spec.get('in_front_m', 0.8):
            continue
        kind = 'ledge'
        if z >= wall_top_z - 0.3 and width >= 0.8 * sheet_width:
            kind = 'eave'
        sources.append(Source(kind, z, u0, u1, out0, out1, area))
    sources.sort(key=lambda s: (s.z, s.u0))
    return sources


def find_pipe_sources(local_verts, plane, front_sign, spec, wall_top_z, floor_z=0.0):
    """Downpipe joints and feet, gutter ends, from one pipe mesh in the wall's frame: the pipe is the column (a 5 cm slice across u) where the mesh is tall; the gutter is the long
    thin run at the top. Returns (sources, info dict with the pipe's u, width, proud and z range)."""
    if len(local_verts) == 0:
        return [], {}
    u = local_verts[:, 1]
    z = local_verts[:, 2]
    out = front_sign * (local_verts[:, 0] - plane)
    bins = np.floor((u - u.min()) / 0.05).astype(int)
    span = {}
    for b, zz in zip(bins, z):
        lo, hi = span.get(b, (zz, zz))
        span[b] = (min(lo, zz), max(hi, zz))
    tall = [b for b, (lo, hi) in span.items() if hi - lo > 1.5]
    sources, info = [], {}
    spacing = spec.get('pipe_joint_spacing_m', 1.9)
    if tall:
        ub = [u.min() + (b + 0.5) * 0.05 for b in tall]
        u_pipe, width = float(np.mean(ub)), max(0.08, (max(ub) - min(ub)) + 0.05)
        sel = (np.abs(u - u_pipe) < width)
        zlo, zhi = float(z[sel].min()), float(z[sel].max())
        column = sel & (z < zhi - 1.0)
        proud = float(out[column].mean()) if column.any() else float(out[sel].mean())          # the pipe's axis: the mean of its ring of vertices
        info = dict(u=round(u_pipe, 3), width=round(width, 3), proud=round(proud, 3), z=[round(zlo, 3), round(zhi, 3)])
        k = 1
        while zlo + k * spacing < zhi - 0.3:
            sources.append(Source('pipe_joint', zlo + k * spacing, u_pipe - width / 2, u_pipe + width / 2, 0.0, proud, name='pipe joint'))
            k += 1
        sources.append(Source('pipe_foot', max(zlo, floor_z), u_pipe - width / 2, u_pipe + width / 2, 0.0, proud, name='pipe foot'))
    high = z > wall_top_z - 0.6
    if high.any():
        gutter_bins = [b for b, (lo, hi) in span.items() if lo > wall_top_z - 0.8 and hi - lo < 0.6]
        if gutter_bins:
            ends = [u.min() + (min(gutter_bins) + 0.5) * 0.05, u.min() + (max(gutter_bins) + 0.5) * 0.05]
            for e in ends:
                sources.append(Source('gutter_end', wall_top_z - 0.1, e - 0.08, e + 0.08, 0.0, 0.15, name='gutter end'))
    return sources, info


def drip_pictures(sources, u_axis, v_axis, drip_length, margin=0.15, max_reach=1.5):
    """drip, drip_dist, drip_kind on a (v rows, u cols) sheet from the sources. u_axis, v_axis: 1-D arrays of dot centres (metres)."""
    U, V = np.meshgrid(u_axis, v_axis)
    drip = np.zeros(U.shape, np.float32)
    dist = np.full(U.shape, max_reach, np.float32)
    kind = np.zeros(U.shape, np.float32)
    for s in sources:
        du = np.maximum(np.maximum(s.u0 - U, U - s.u1), 0.0)
        lateral = 1.0 - np.clip(du / margin, 0.0, 1.0) ** 2 * (3 - 2 * np.clip(du / margin, 0.0, 1.0))
        below = s.z - V
        length = drip_length if s.kind not in ('pipe_foot',) else 0.4
        inside = (below >= -0.02) & (below <= length)
        fade_in = np.clip((below + 0.02) / 0.04, 0.0, 1.0)
        value = (lateral * inside * fade_in).astype(np.float32)
        drip = np.maximum(drip, value)
        better = (value > 0.05) & (np.maximum(below, 0.0) < dist)
        dist = np.where(better, np.maximum(below, 0.0), dist)
        kind = np.where(better, KIND_CODE.get(s.kind, 0.2), kind)
    return drip, np.clip(dist / max_reach, 0.0, 1.0).astype(np.float32), kind.astype(np.float32)


def ground_drip(geo, settings, grid, arrays):
    """Ground-plan drip lines: the outer boundary of the footprint of every raised, up-facing surface of the source roles (not the side against a wall), dropped to the ground.
    Returns (drip, drip_dist) on the ground grid."""
    import cv2
    from .ground_plan import fill_triangles
    spec = settings.geometry.get('ledges') or {}
    roles = spec.get('sources_from_roles', [])
    canvas = np.zeros(grid.shape(), np.uint8)
    data = geo.triangles(roles) if roles else None
    if data is not None:
        v, t = data[0], data[1]
        n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
        nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
        centre = (v[t[:, 0]] + v[t[:, 1]] + v[t[:, 2]]) / 3.0
        ci = np.clip(((centre[:, 0] - grid.x0) / grid.dot).astype(int), 0, grid.width - 1)
        cj = np.clip(((centre[:, 1] - grid.y0) / grid.dot).astype(int), 0, grid.height - 1)
        above = centre[:, 2] - arrays['ground_height'][cj, ci]
        sel = np.nonzero((nz >= spec.get('up_normal_z_min', 0.9) * 0.9) & (above >= 0.25) & arrays['has_ground'][cj, ci])[0]
        fill_triangles(canvas, grid, v[:, :2], t[sel], 1)
    if not canvas.any():
        return np.zeros(grid.shape(), np.float32), np.ones(grid.shape(), np.float32)
    boundary = (canvas - cv2.erode(canvas, np.ones((3, 3), np.uint8))) > 0
    d_solid_m = arrays['_d_solid_m']
    boundary &= d_solid_m > 0.06
    if not boundary.any():
        return np.zeros(grid.shape(), np.float32), np.ones(grid.shape(), np.float32)
    dist = cv2.distanceTransform((~boundary).astype(np.uint8), cv2.DIST_L2, 5) * grid.dot
    drip = np.exp(-(dist / 0.12) ** 2).astype(np.float32)
    return drip, np.clip(dist / 1.5, 0, 1).astype(np.float32)
