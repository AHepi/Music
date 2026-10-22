"""Lantern details (step 6): clean dark cracks on the post and gallery, a chipped cap corner. Plain words: cracks are single tapering
dark ribbons lying 3 mm off the stone (found by ray casting sideways onto the part), the chip is one slanted cut across a corner."""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from r_common import *
import r_stones


def crack_on_face(bvh, face_dir, centre_xy, z0, length, rng, lateral0=0.0, width=0.007, name='lantern crack', drift=0.35):
    """walk down a vertical face. face_dir = (1,0)/(-1,0)/(0,1)/(0,-1) = the side of the part the crack is on"""
    fx, fy = face_dir
    lx, ly = -fy, fx                       # lateral direction on that face
    cx, cy = centre_xy
    pts, nrms = [], []
    u, z = lateral0, z0
    ang = rng.uniform(-0.4, 0.4)
    for i in range(int(length / 0.03)):
        o = Vector((cx + fx * 1.2 + lx * u, cy + fy * 1.2 + ly * u, z))
        loc, nrm, idx, dist = bvh.ray_cast(o, Vector((-fx, -fy, 0)), 3.0)
        if loc is None:
            break
        pts.append(loc)
        nrms.append(nrm)
        ang += rng.uniform(-0.55, 0.55)
        ang = max(-1.0, min(1.0, ang))
        u += math.sin(ang) * 0.03 * (1 + drift)
        z -= math.cos(ang) * 0.03
    if len(pts) < 5:
        return None
    return r_stones.ribbon_mesh(name, pts, nrms, width, lift=0.0025)


def chip_corner(obj, sx, sy, reach=0.06, tilt=0.4):
    """cut a corner of the part (local coordinates of its mesh): plane through a point 'reach' inside the lowest corner (sx, sy)"""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    co = np.array([v.co[:] for v in bm.verts])
    xm = co[:, 0].max() if sx > 0 else co[:, 0].min()
    ym = co[:, 1].max() if sy > 0 else co[:, 1].min()
    # the lowest vertices near that corner
    near = co[(np.abs(co[:, 0] - xm) < 0.12) & (np.abs(co[:, 1] - ym) < 0.12)]
    zc = near[:, 2].min() if len(near) else co[:, 2].min()
    corner = Vector((xm, ym, zc))
    n = Vector((sx, sy, tilt)).normalized()
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=corner - n * reach, plane_no=n, clear_outer=True)
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=24)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return corner
