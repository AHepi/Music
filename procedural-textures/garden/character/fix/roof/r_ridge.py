"""Ridge and eave details (step 3 of the roof brief). Plain words: the roof had a plain box for a ridge and bare tile ends at the eave.
New objects in 'G6 roof' (also linked into 'G4 rim receivers' and 'G4 roof receivers' so the rim and roof lights reach them):
 * a rolled ridge course (half-round cap tiles with a seam ring, a flat base course) and two rounded ridge-end caps with a disc relief,
 * 86 round eave-end discs (14 cm, 3 cm thick, ring relief) on the lowest course, one on every tile of the eave course."""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix
from r_common import *


def revolve(profile, n=28, close_center=True):
    """profile: [(radius, z), ...] from the centre outwards and back; returns verts, faces of a body of revolution around Z"""
    verts, faces = [], []
    rings = []
    for (r, z) in profile:
        if r < 1e-6:
            verts.append((0.0, 0.0, z))
            rings.append([len(verts) - 1] * n)
        else:
            ring = []
            for i in range(n):
                a = 2 * math.pi * i / n
                verts.append((r * math.cos(a), r * math.sin(a), z))
                ring.append(len(verts) - 1)
            rings.append(ring)
    for k in range(len(profile) - 1):
        for i in range(n):
            a, b = rings[k][i], rings[k][(i + 1) % n]
            c, d = rings[k + 1][(i + 1) % n], rings[k + 1][i]
            if a == b:
                faces.append((a, c, d)) if c != d else None
            elif c == d:
                faces.append((a, b, c))
            else:
                faces.append((a, b, c, d))
    return verts, faces


def disc_profile(r=0.07, th=0.03):
    """a round eave-end disc: back face at z = 0, rim, a shallow recessed field, a raised ring and a small boss (relief 3 to 6 mm)"""
    return [(0.0, 0.0), (r, 0.0), (r, th * 0.82), (r * 0.965, th), (r * 0.84, th), (r * 0.80, th - 0.006), (r * 0.66, th - 0.006),
            (r * 0.63, th + 0.002), (r * 0.52, th + 0.002), (r * 0.49, th - 0.006), (r * 0.22, th - 0.006), (r * 0.19, th + 0.003), (0.0, th + 0.003)]


def _flip(faces):
    return [tuple(reversed(f)) for f in faces]


def disc_mesh_data(r, th):
    v, f = revolve(disc_profile(r, th), 28)
    return v, _flip(f)


def build_eave_discs(M, plan, mat):
    """one disc at the lower end of every course-7 tile (both banks), positioned from the evaluated tile matrices"""
    allv, allf = [], []
    dripv = []                  # FIX ROUND: per-vertex drip stain (0..1) so the disc under a drip tongue is dark too
    count = 0
    from r_tiles import NB, NCRS
    dv, df = disc_mesh_data(0.07, 0.03)
    rx = Matrix.Rotation(math.radians(90), 4, 'X')       # disc axis (+Z) -> tile local -Y (down the slope, outward)
    for k in range(len(M)):
        if k % NCRS != NCRS - 1:
            continue
        if plan['variant'][k] in (3, 5):       # no disc on a broken-half or missing tile
            continue
        T = Matrix(M[k].tolist())
        loc = Matrix.Translation(Vector((0.0, -0.335, 0.138)))
        mw = T @ loc @ rx
        base = len(allv)
        dval = float(plan['drip'][k][2]) if plan['drip'][k][0] > 0 else 0.0
        for p in dv:
            allv.append(tuple(mw @ Vector(p)))
            dripv.append(dval)
        for f in df:
            allf.append(tuple(base + i for i in f))
        count += 1
    me = new_mesh('eave discs', allv, allf, smooth=True)
    a_ = me.attributes.new('g6_drip', 'FLOAT', 'POINT')
    a_.data.foreach_set('value', np.array(dripv, np.float32))
    # UV: planar polar-ish mapping per disc is not needed (small); give a box UV in metres so the tangent frame exists
    set_uv(me, 'UVMap', box_uv_fn(1.0))
    me.materials.append(mat)
    return me, count


def _arc_extrude(x0, x1, y0, zc, R, n=14, closed_ends=True, z_base=None):
    """half-round profile (a half pipe lying along X) from x0 to x1; returns verts, faces"""
    verts, faces = [], []
    prof = []
    zb = zc if z_base is None else z_base
    prof.append((y0 - R, zb))
    for i in range(n + 1):
        a = math.pi - math.pi * i / n
        prof.append((y0 + R * math.cos(a), zc + R * math.sin(a)))
    prof.append((y0 + R, zb))
    m = len(prof)
    for x in (x0, x1):
        for (y, z) in prof:
            verts.append((x, y, z))
    for i in range(m - 1):
        faces.append((i, i + 1, m + i + 1, m + i))
    # bottom face and end caps
    faces.append((m + m - 1, m, 0, m - 1)) if False else None
    faces.append(tuple(range(m - 1, -1, -1)))            # end cap at x0 (normal -x)
    faces.append(tuple(range(m, 2 * m)))                 # end cap at x1 (normal +x)
    faces.append((m - 1, 0, m, 2 * m - 1))               # flat underside
    return verts, faces


def _box(x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def build_ridge(mat, x_lo=-5.75, x_hi=6.15, y0=7.2, zc=4.665, R=0.19, rng=None):
    """a rolled ridge course: flat base band, half-round cap tiles 0.31 m long with a seam ring, and two rounded end caps with a disc relief"""
    rng = rng or np.random.default_rng(3)
    V, F = [], []

    def add(v, f):
        b = len(V)
        V.extend(v)
        F.extend([tuple(b + i for i in face) for face in f])
    # base band (one box with a slightly raised outer lip)
    add(*_box(x_lo - 0.05, x_hi + 0.05, y0 - 0.27, y0 + 0.27, zc - 0.07, zc - 0.005))
    n_seg = int(round((x_hi - x_lo) / 0.32))
    seg = (x_hi - x_lo) / n_seg
    for i in range(n_seg):
        xa = x_lo + i * seg + 0.006
        xb = x_lo + (i + 1) * seg - 0.006
        add(*_arc_extrude(xa, xb, y0, zc, R * rng.uniform(0.985, 1.015)))
        # seam ring: a slightly larger short half-pipe at the up-slope-left end of every segment
        add(*_arc_extrude(xa - 0.004, xa + 0.034, y0, zc, R + 0.014))
    # end caps: bigger rounded blocks, with a disc relief on the outer face
    for side in (-1, 1):
        xe = x_lo - 0.02 if side < 0 else x_hi + 0.02
        xa, xb = (xe - 0.22, xe) if side < 0 else (xe, xe + 0.22)
        add(*_arc_extrude(xa, xb, y0, zc - 0.02, R + 0.05, 16, z_base=zc - 0.07))
        dv, df = revolve(disc_profile(0.15, 0.03), 32)
        df = _flip(df)
        # disc axis +Z -> +/-X, centred on the cap's outer face
        rot = Matrix.Rotation(math.radians(90 * (1 if side > 0 else -1)), 4, 'Y')
        cen = Vector((xb if side > 0 else xa, y0, zc + 0.045))
        mw = Matrix.Translation(cen) @ rot
        b = len(V)
        for p in dv:
            V.append(tuple(mw @ Vector(p)))
        F.extend([tuple(b + i for i in f) for f in df])
    me = new_mesh('ridge course', V, F, smooth=False)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    set_uv(me, 'UVMap', box_uv_fn(1.0))
    me.materials.append(mat)
    return me, n_seg


def build_leaves(M, plan, mat, rng, count=8):
    """a few fallen maple leaves lying in the valleys between tile pans on the south slope (flat folded ellipses, 5 to 8 cm)"""
    from r_tiles import NB, NCRS
    cand = [k for k in range(NB, 2 * NB) if plan['vis_hero'][k] and 2 <= k % NCRS <= 6 and plan['variant'][k] == 0]
    rng.shuffle(cand)
    chosen = []
    for k in cand:
        p = M[k][:3, 3]
        if all(np.linalg.norm(p - M[c][:3, 3]) > 1.2 for c in chosen):
            chosen.append(k)
        if len(chosen) >= count:
            break
    V, F = [], []
    for k in chosen:
        T = Matrix(M[k].tolist())
        sx = rng.choice([-1, 1])
        ly = rng.uniform(-0.2, 0.1)
        base = Vector((sx * 0.148, ly, 0.105 + 0.014))
        yaw = rng.uniform(0, 2 * math.pi)
        size = rng.uniform(0.05, 0.08) * 1.45          # FIX ROUND: leaf litter 45 percent bigger so it reads
        # outline of a pointed leaf: 10 points, midrib folded 10 degrees
        pts = []
        n = 10
        for i in range(n):
            a = 2 * math.pi * i / n
            r_ = size * (0.55 + 0.45 * math.cos(a)) if True else size
            x = r_ * math.cos(a) * 0.6
            y = size * 0.9 * math.sin(a) * (1.0 if math.sin(a) > 0 else 0.7)
            pts.append((y, x))
        b = len(V)
        centre = Vector((0, 0, 0.004))
        V.append(tuple(T @ (base + Matrix.Rotation(yaw, 3, 'Z') @ centre)))
        for (px, py) in pts:
            fold = 0.004 + 0.18 * abs(py) * 0.35
            q = Matrix.Rotation(yaw, 3, 'Z') @ Vector((px, py, fold))
            V.append(tuple(T @ (base + q)))
        for i in range(n):
            F.append((b, b + 1 + i, b + 1 + (i + 1) % n))
    me = new_mesh('roof leaves', V, F, smooth=False)
    set_uv(me, 'UVMap', box_uv_fn(1.0))
    me.materials.append(mat)
    return me, chosen


def leaf_material():
    m = bpy.data.materials.new(PFX + 'roof leaf')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    oi = nnew(nt, 'ShaderNodeObjectInfo', 'G6 oi')
    geo = nnew(nt, 'ShaderNodeNewGeometry', 'G6 geo')
    sep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 sep')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    nz = nnew(nt, 'ShaderNodeTexNoise', 'G6 n', noise_dimensions='3D')
    nz.inputs['Scale'].default_value = 90.0
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    c = mix_rgb(nt, nz.outputs['Fac'], hex_lin('#7a4120'), hex_lin('#9a5a2a'))
    nt.links.new(mix_out(c), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    return m
