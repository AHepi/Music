"""Building parts: beams, framed walls, stone walls, thatch and shingle roofs, doors, windows."""
import bpy
import numpy as np
import math
from collections import defaultdict
from mathutils import Vector, Matrix, Euler
import common as C


# ----------------------------------------------------------------------------
# Parts container
# ----------------------------------------------------------------------------
class Parts:
    def __init__(self, seed=0):
        self.mb = defaultdict(C.MeshBuilder)
        self.rng = np.random.RandomState(seed)

    def add(self, key, verts, faces, uvs=None, rnd=None, attrs=None):
        if rnd is None:
            rnd = self.rng.uniform()
        self.mb[key].add(verts, faces, uvs, rnd=rnd, attrs=attrs)

    def box(self, key, center, size, rot=None, rnd=None, jitter=0.0):
        if jitter > 0:
            r = self.rng.normal(0, jitter, 3)
            rot = (Euler(rot) if isinstance(rot, (tuple, list)) else rot)
            R = (rot.to_matrix() if isinstance(rot, Euler) else (rot if rot is not None else Matrix.Identity(3)))
            R = Euler(r).to_matrix() @ R
            rot = R
        v, f, uv = C.box(center, size, rot)
        self.add(key, v, f, uv, rnd)

    def beam(self, key, a, b, w, h, up=(0, 0, 1), extend=0.0, rnd=None, jitter=0.0):
        a = Vector(a)
        b = Vector(b)
        x = (b - a)
        L = x.length
        x.normalize()
        u = Vector(up)
        z = (u - x * x.dot(u))
        if z.length < 1e-6:
            z = x.orthogonal()
        z.normalize()
        y = z.cross(x)
        R = Matrix((x, y, z)).transposed()
        if jitter > 0:
            R = Euler(self.rng.normal(0, jitter, 3)).to_matrix() @ R
        c = (a + b) * 0.5
        v, f, uv = C.box(c, (L + 2 * extend, w, h), R)
        self.add(key, v, f, uv, rnd)

    def cyl(self, key, a, b, r0, r1=None, sides=10, caps=True, rnd=None):
        v, f, uv = C.cylinder(a, b, r0, r1, sides=sides, caps=caps)
        self.add(key, v, f, uv, rnd)

    def log(self, key, a, b, r, sides=9, split=0, rnd=None, flip=False):
        """Firewood piece: round (split=0), half (1) or quarter (2) log with end-grain caps (face attr 'cap')."""
        a = Vector(a)
        b = Vector(b)
        ax = b - a
        M = C.frame_from(ax)
        yv, zv = M.col[1], M.col[2]
        if split == 0:
            angs = [2 * math.pi * k / sides for k in range(sides)]
            prof = [(math.cos(t) * r, math.sin(t) * r) for t in angs]
        elif split == 1:
            angs = [math.pi * k / (sides - 1) for k in range(sides)]
            prof = [(math.cos(t) * r, math.sin(t) * r - r * 0.35) for t in angs]
        else:
            angs = [0.5 * math.pi * k / (sides - 2) for k in range(sides - 1)]
            prof = [(0.0 - r * 0.4, 0.0 - r * 0.4)] + [(math.cos(t) * r * 1.2 - r * 0.4, math.sin(t) * r * 1.2 - r * 0.4) for t in angs]
        if flip:
            prof = [(p[0], -p[1]) for p in prof][::-1]
        n = len(prof)
        jit = self.rng.normal(0, r * 0.06, (n, 2))
        prof = [(p[0] + j[0], p[1] + j[1]) for p, j in zip(prof, jit)]
        v0 = [tuple(a + yv * px + zv * py) for px, py in prof]
        v1 = [tuple(b + yv * px + zv * py) for px, py in prof]
        L = ax.length
        rnd = self.rng.uniform() if rnd is None else rnd
        verts = np.array(v0 + v1)
        faces = []
        uvs = []
        per = 0.0
        for k in range(n):
            k2 = (k + 1) % n
            faces.append([k, k2, n + k2, n + k])
            seg = math.dist(prof[k], prof[k2])
            uvs.append([(per, 0), (per + seg, 0), (per + seg, L), (per, L)])
            per += seg
        self.mb[key].add(verts, faces, uvs, rnd=rnd, attrs={"cap": 0.0})
        cap_uv = [(px / r, py / r) for px, py in prof]
        self.mb[key].add(np.array(v0[::-1]), [list(range(n))], [cap_uv[::-1]], rnd=rnd, attrs={"cap": 1.0})
        self.mb[key].add(np.array(v1), [list(range(n))], [cap_uv], rnd=rnd, attrs={"cap": 1.0})

    def tube(self, key, pts, radii, sides=6, caps=True, rnd=None):
        v, f, uv = C.tube(pts, radii, sides=sides, caps=caps)
        self.add(key, v, f, uv, rnd)

    def deform(self, keys, fn):
        """Apply fn(verts (n,3)) -> verts to all accumulated geometry of the given keys."""
        for k in keys:
            mb = self.mb.get(k)
            if mb is None:
                continue
            mb.verts = [fn(np.asarray(v, dtype=float).copy()) for v in mb.verts]

    def build(self, name, col, mats, loc=(0, 0, 0), rot_z=0.0, bevel=None, subsurf=None, parent=None):
        bevel = bevel or {}
        subsurf = subsurf or {}
        obs = []
        for key, mb in self.mb.items():
            if mb.empty():
                continue
            me = mb.build(f"{name}_{key}", materials=[mats[key]], smooth=key in ("thatch", "thatch_ridge", "stone", "straw", "rope", "iron_round", "clay", "burlap", "pebble"))
            ob = bpy.data.objects.new(f"{name}_{key}", me)
            col.objects.link(ob)
            ob.location = loc
            ob.rotation_euler = (0, 0, math.radians(rot_z))
            if parent is not None:
                ob.parent = parent
            if key in bevel:
                md = ob.modifiers.new("bevel", 'BEVEL')
                md.width = bevel[key]
                md.segments = 2
                md.limit_method = 'ANGLE'
                md.angle_limit = math.radians(40)
                md.harden_normals = False
            if key in subsurf:
                md = ob.modifiers.new("subsurf", 'SUBSURF')
                md.levels = 1
                md.render_levels = subsurf[key]
            if key not in ("thatch", "thatch_ridge", "stone", "straw", "rope", "clay", "burlap", "pebble"):
                # flat shading for hard pieces, smoothed bevel edges
                me.shade_flat()
            obs.append(ob)
        return obs


# ----------------------------------------------------------------------------
# Wall frame helpers (local building coordinates; walls are 2D lines with an outward normal)
# ----------------------------------------------------------------------------
class Wall:
    def __init__(self, p0, p1, out):
        self.p0 = Vector((p0[0], p0[1], 0))
        self.p1 = Vector((p1[0], p1[1], 0))
        self.u = (self.p1 - self.p0)
        self.L = self.u.length
        self.u.normalize()
        self.n = Vector((out[0], out[1], 0)).normalized()

    def pt(self, s, z, d=0.0):
        return self.p0 + self.u * s + self.n * d + Vector((0, 0, z))

    def rot(self):
        # local x along wall, y along outward normal, z up
        return Matrix((self.u, self.n, Vector((0, 0, 1)))).transposed()

    def board(self, parts, key, s0, s1, z0, za, zb, d0, d1, rnd=None):
        """Board in the wall plane whose top edge slopes from za (at s0) to zb (at s1)."""
        corners = [(s0, z0, d0), (s1, z0, d0), (s1, z0, d1), (s0, z0, d1), (s0, za, d0), (s1, zb, d0), (s1, zb, d1), (s0, za, d1)]
        v = np.array([tuple(self.pt(cs, cz, cd)) for cs, cz, cd in corners])
        f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        H = max(za, zb) - z0
        W = s1 - s0
        uv = [[(0, 0)] * 4, [(0, 0)] * 4, [(0, 0), (0, W), (H, W), (H, 0)], [(0, 0)] * 4, [(0, 0), (0, W), (H, W), (H, 0)], [(0, 0)] * 4]
        parts.add(key, v, f, uv, rnd=rnd)

    def box(self, parts, key, s0, s1, z0, z1, d0, d1, rnd=None, jitter=0.0):
        c = self.pt((s0 + s1) / 2, (z0 + z1) / 2, (d0 + d1) / 2)
        parts.box(key, c, (abs(s1 - s0), abs(d1 - d0), abs(z1 - z0)), self.rot(), rnd=rnd, jitter=jitter)


def framed_wall(parts, wall, z_base, z_top, posts, bays, t=0.2, inset=0.035, infill=0.1, braces=(), rng=None,
                plate_ext=(0.1, 0.1), rail_h=0.16, skip_end_posts=False):
    """Timber-framed wall with daub infill.

    posts: list of s positions (centres). bays: list (one per gap between posts) of dicts:
       {'rails': [z...]} or {'door': (z0, z1)} or {'window': (z0, z1)}.
    """
    rng = rng or parts.rng
    th = t
    # sole plate and wall plate
    wall.box(parts, "timber", -plate_ext[0], wall.L + plate_ext[1], z_base, z_base + 0.2, -th / 2, th / 2, jitter=0.003)
    wall.box(parts, "timber", -plate_ext[0], wall.L + plate_ext[1], z_top - 0.22, z_top, -th / 2 - 0.01, th / 2 + 0.01, jitter=0.003)
    zb = z_base + 0.2
    zt = z_top - 0.22
    for pi_, s in enumerate(posts):
        if skip_end_posts and pi_ in (0, len(posts) - 1):
            continue
        wall.box(parts, "timber", s - th / 2, s + th / 2, zb, zt, -th / 2, th / 2, jitter=0.004)
    d_out = th / 2 - inset
    d_in = d_out - infill
    for i, bay in enumerate(bays):
        sa = posts[i] + th / 2
        sb = posts[i + 1] - th / 2
        levels = [zb]
        open_cells = []
        if 'door' in bay:
            z0, z1 = bay['door']
            levels += [z1, z1 + rail_h]
            open_cells.append((zb, z1))
            wall.box(parts, "timber", sa, sb, z1, z1 + rail_h, -th / 2, th / 2, jitter=0.003)
        elif 'window' in bay:
            z0, z1 = bay['window']
            levels += [z0 - rail_h, z0, z1, z1 + rail_h]
            open_cells.append((z0, z1))
            wall.box(parts, "timber", sa - 0.02, sb + 0.02, z0 - rail_h, z0, -th / 2 - 0.015, th / 2, jitter=0.003)
            wall.box(parts, "timber", sa, sb, z1, z1 + rail_h, -th / 2, th / 2, jitter=0.003)
        else:
            for rz in bay.get('rails', []):
                levels += [rz - rail_h / 2, rz + rail_h / 2]
                wall.box(parts, "timber", sa, sb, rz - rail_h / 2, rz + rail_h / 2, -th / 2, th / 2, jitter=0.004)
        levels.append(zt)
        levels = sorted(levels)
        # infill cells = gaps between consecutive levels that are not timber or open
        timber_spans = []
        if 'door' in bay:
            timber_spans.append((bay['door'][1], bay['door'][1] + rail_h))
        if 'window' in bay:
            z0, z1 = bay['window']
            timber_spans += [(z0 - rail_h, z0), (z1, z1 + rail_h)]
        for rz in bay.get('rails', []) if ('door' not in bay and 'window' not in bay) else []:
            timber_spans.append((rz - rail_h / 2, rz + rail_h / 2))
        for k in range(len(levels) - 1):
            a, b = levels[k], levels[k + 1]
            if b - a < 0.02:
                continue
            mid = (a + b) / 2
            if any(x0 - 1e-6 <= mid <= x1 + 1e-6 for x0, x1 in timber_spans):
                continue
            if any(x0 - 1e-6 <= mid <= x1 + 1e-6 for x0, x1 in open_cells):
                continue
            wall.box(parts, "daub", sa - 0.01, sb + 0.01, a - 0.01, b + 0.01, d_in, d_out)
    for (s0, z0, s1, z1) in braces:
        a = wall.pt(s0, z0, 0.0)
        b = wall.pt(s1, z1, 0.0)
        parts.beam("timber", a, b, th * 0.85, th * 0.8, up=wall.n.cross(b - a).normalized() if False else Vector((0, 0, 1)), jitter=0.0)


def fix_brace_orientation(parts):
    pass


def stone_wall(parts, wall, z0, z1, thick, openings=(), rng=None, course=(0.15, 0.3), slen=(0.22, 0.55), gap=0.03,
               ext=(0.0, 0.0), alt_ext=None, depth=0.2, key="stone", core=True, lib=None):
    """Fieldstone wall along `wall` (centre line), outer face at +thick/2 along the normal.
    openings: list of (s0, s1, za, zb). ext: extension beyond the ends (for corners).
    alt_ext: (ext_even, ext_odd) pairs per end to interlock corners on alternate courses."""
    rng = rng or parts.rng
    lib = lib or stone_lib()
    if core:
        wall.box(parts, "mortar", -ext[0] + 0.02, wall.L + ext[1] - 0.02, z0, z1 - 0.005, -thick / 2 + 0.03, thick / 2 - 0.035)
    z = z0
    ci = 0
    R = wall.rot()
    while z < z1 - 0.06:
        h = rng.uniform(*course)
        if z + h > z1 - 0.08:
            h = z1 - z
        if alt_ext is not None:
            e0 = alt_ext[0][ci % 2]
            e1 = alt_ext[1][ci % 2]
        else:
            e0, e1 = ext
        s = -e0
        first = True
        while s < wall.L + e1 - 0.05:
            l = rng.uniform(*slen)
            if first and ci % 2 == 1:
                l *= 0.6
            first = False
            if s + l > wall.L + e1 - 0.12:
                l = wall.L + e1 - s
            sc = s + l / 2
            zc = z + h / 2
            skip = False
            for (a, b, za, zb) in openings:
                if (sc > a - 0.02 and sc < b + 0.02) and (zc > za - 0.02 and zc < zb + 0.02):
                    skip = True
                    break
                # clip stones straddling the opening edge
                if (s < b and s + l > a) and (zc > za and zc < zb):
                    if sc < (a + b) / 2:
                        l = max(a - s, 0.0)
                    else:
                        ns = b
                        l = max(s + l - b, 0.0)
                        s = ns
                    sc = s + l / 2
            if not skip and l > 0.06:
                v, f = lib[rng.randint(len(lib))]
                prot = rng.uniform(-0.012, 0.022)
                hh = h * rng.uniform(0.72, 1.0)
                zc2 = z + hh / 2 + rng.uniform(0.0, h - hh)
                sz = np.array([(l - gap) / 2 * rng.uniform(0.88, 1.0), depth / 2, (hh - gap) / 2])
                vv = v * sz
                Rr = np.array(Euler((rng.normal(0, 0.03), rng.normal(0, 0.05), rng.normal(0, 0.06))).to_matrix())
                vv = vv @ Rr.T
                # to wall coordinates: x along u, y along n, z up
                cen = wall.pt(sc, zc2, thick / 2 - depth / 2 + prot)
                M = np.array(R)
                vv = vv @ M.T + np.array(cen)
                parts.add(key, vv, f, None, rnd=rng.uniform())
            s += l
        z += h
        ci += 1


_STONE_LIB = None


def stone_lib(n=12):
    global _STONE_LIB
    if _STONE_LIB is not None:
        return _STONE_LIB
    rng = np.random.RandomState(77)
    lib = []
    base_v, base_f = C.subdivided_cube(4)
    for i in range(n):
        v = base_v.copy()
        # round the box (partial spherify) and add lumps
        nrm = v / np.linalg.norm(v, axis=1, keepdims=True)
        rr = 0.4 + 0.25 * rng.uniform()
        v = v * (1 - rr) + nrm * np.linalg.norm(v, axis=1, keepdims=True) * rr * 0.72
        seed = rng.randint(1000)
        n1 = C.fbm(v[:, 0] * 1.3 + v[:, 2] * 0.7, v[:, 1] * 1.3 + v[:, 2] * 1.1, 3, seed)
        n2 = C.fbm(v[:, 0] * 3.1 - v[:, 2] * 1.7, v[:, 1] * 2.9 + v[:, 2] * 2.3, 2, seed + 5)
        v = v * (1 + 0.13 * n1[:, None] + 0.04 * n2[:, None])
        # a flatter outer face (dressed side) on +y
        v[:, 1] = np.where(v[:, 1] > 0.55, 0.55 + (v[:, 1] - 0.55) * 0.35, v[:, 1])
        v = v / np.abs(v).max(axis=0)
        lib.append((v, base_f))
    _STONE_LIB = lib
    return lib


# ----------------------------------------------------------------------------
# Roofs
# ----------------------------------------------------------------------------
def thatch_gabled(parts, L, D, z_wp, pitch_deg, oe=0.55, og=0.35, t=0.36, rng=None, nx=None, key="thatch"):
    """Gabled thatch slab over a building of outer length L (x) and depth D (y)."""
    rng = rng or parts.rng
    th = math.radians(pitch_deg)
    tn = math.tan(th)
    Lh = L / 2 + og
    Dh = D / 2 + oe
    tv = t / math.cos(th)
    # sample positions with support loops near the edges
    def axis(h, n, edge=0.13):
        core = np.linspace(-h + edge, h - edge, n)
        return np.concatenate([[-h], core, [h]])
    nx = nx or int(L * 6) + 8
    xs = axis(Lh, nx)
    ys = axis(Dh, int(D * 6) + 10)
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    rr = 0.35
    sA, sB = rng.randint(1000), rng.randint(1000)

    def surf_full(Xv, Yv):
        ayv = np.sqrt(np.asarray(Yv) ** 2 + rr ** 2) - rr
        zuv = z_wp + (D / 2 - ayv) * tn
        lumpv = 0.035 * C.fbm(np.asarray(Xv) / 1.3, np.asarray(Yv) / 1.3, 3, sA) + 0.012 * C.fbm(np.asarray(Xv) / 0.3, np.asarray(Yv) / 0.4, 2, sB)
        sagv = -0.06 * (1 - (np.asarray(Xv) / Lh) ** 2) * (1 - (np.abs(Yv) / Dh))
        return zuv + tv + lumpv + sagv
    ay = np.sqrt(Y ** 2 + rr ** 2) - rr      # rounded ridge
    zu = z_wp + (D / 2 - ay) * tn
    ztop = surf_full(X, Y)
    # eave: thick cut face; bottom rim slightly inboard
    zbot = zu - 0.02
    nX, nY = X.shape
    top = np.stack([X, Y, ztop], -1).reshape(-1, 3)
    # the bottom rim is pulled in under the eave so the cut face slopes down and inward
    inward = 0.2 * np.clip((np.abs(Y) - D / 2) / max(oe, 1e-3), 0, 1) ** 0.7 + 0.02
    inward_x = 0.1 * np.clip((np.abs(X) - (Lh - og)) / max(og, 1e-3), 0, 1)
    bot = np.stack([X - np.sign(X) * inward_x, Y - np.sign(Y) * inward, zbot], -1).reshape(-1, 3)
    verts = np.concatenate([top, bot])
    off = nX * nY
    idx = np.arange(off).reshape(nX, nY)
    faces = []
    uvs = []
    attrs_eave = []
    slope_v = lambda yv: (Dh - abs(yv)) / math.cos(th)
    for i in range(nX - 1):
        for j in range(nY - 1):
            a, b, c, d = idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]
            faces.append([a, b, c, d])
            uvs.append([(xs[i], slope_v(ys[j])), (xs[i + 1], slope_v(ys[j])), (xs[i + 1], slope_v(ys[j + 1])), (xs[i], slope_v(ys[j + 1]))])
            attrs_eave.append(0.0)
            faces.append([d + off, c + off, b + off, a + off])
            uvs.append([(xs[i], 0.0)] * 4)
            attrs_eave.append(0.0)
    # rims: boundary loop
    loop = [idx[i, 0] for i in range(nX)] + [idx[nX - 1, j] for j in range(1, nY)] + [idx[i, nY - 1] for i in range(nX - 2, -1, -1)] + [idx[0, j] for j in range(nY - 2, 0, -1)]
    for k in range(len(loop)):
        a = loop[k]
        b = loop[(k + 1) % len(loop)]
        faces.append([b, a, a + off, b + off])
        pa, pb = top[a], top[b]
        uvs.append([(pb[0] * 3 + pb[1] * 3, 0.0), (pa[0] * 3 + pa[1] * 3, 0.0), (pa[0] * 3 + pa[1] * 3, 0.3), (pb[0] * 3 + pb[1] * 3, 0.3)])
        # eave faces get the straw-ends look; verges too (they show cut ends)
        attrs_eave.append(1.0)
    mb = parts.mb[key]
    base = mb.nv
    mb.verts.append(verts)
    for fi, f in enumerate(faces):
        mb.faces.append([base + q for q in f])
        mb.uvs.append(uvs[fi])
        mb.mat.append(0)
        mb.frnd.append(0.5)
        mb.fattr.setdefault("eave", [0.0] * (len(mb.faces) - 1))
        mb.fattr["eave"].append(attrs_eave[fi])
    mb.nv += len(verts)
    # pad other attrs
    for k in mb.fattr:
        while len(mb.fattr[k]) < len(mb.faces):
            mb.fattr[k].append(0.0)
    ridge_z = z_wp + (D / 2) * tn + tv
    return dict(ridge_z=ridge_z, Lh=Lh, Dh=Dh, tn=tn, tv=tv, z_wp=z_wp, D=D, rr=rr, surface=lambda x, y: float(surf_full(x, y)))


def thatch_ridge(parts, info, rng=None, key="thatch_ridge", w0=0.5, scallop=0.55, liggers=True):
    """Block-cut ridge with scalloped lower edge, hazel liggers and cross spars."""
    rng = rng or parts.rng
    Lh = info["Lh"] - 0.12
    surf = info["surface"]
    nxs = int(Lh * 2 / 0.05) + 1
    xs = np.linspace(-Lh, Lh, nxs)
    nys = 15
    vs = np.linspace(-1, 1, nys)
    verts = []
    thick = 0.11
    for x in xs:
        ph = (x / scallop) % 1.0
        sc = 1.0 - abs(ph - 0.5) * 2      # triangle wave 0..1
        w = w0 + 0.16 * sc
        for v in vs:
            y = v * w
            z = surf(x, y) + thick * (1 - 0.25 * abs(v)) - 0.01
            verts.append((x, y, z))
    for x in xs:
        ph = (x / scallop) % 1.0
        sc = 1.0 - abs(ph - 0.5) * 2
        w = w0 + 0.16 * sc
        for v in vs:
            y = v * w
            z = surf(x, y) - 0.08
            verts.append((x, y, z))
    verts = np.array(verts)
    off = nxs * nys
    idx = np.arange(off).reshape(nxs, nys)
    faces, uvs, eav = [], [], []
    for i in range(nxs - 1):
        for j in range(nys - 1):
            a, b, c, d = idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]
            faces.append([a, b, c, d])
            uvs.append([(xs[i], vs[j]), (xs[i + 1], vs[j]), (xs[i + 1], vs[j + 1]), (xs[i], vs[j + 1])])
            eav.append(0.0)
    loop = [idx[i, 0] for i in range(nxs)] + [idx[nxs - 1, j] for j in range(1, nys)] + [idx[i, nys - 1] for i in range(nxs - 2, -1, -1)] + [idx[0, j] for j in range(nys - 2, 0, -1)]
    for k in range(len(loop)):
        a = loop[k]
        b = loop[(k + 1) % len(loop)]
        faces.append([b, a, a + off, b + off])
        uvs.append([(0, 0)] * 4)
        eav.append(1.0)
    mb = parts.mb[key]
    base = mb.nv
    mb.verts.append(verts)
    for fi, f in enumerate(faces):
        mb.faces.append([base + q for q in f])
        mb.uvs.append(uvs[fi])
        mb.mat.append(0)
        mb.frnd.append(0.3)
        mb.fattr.setdefault("eave", [0.0] * (len(mb.faces) - 1))
        mb.fattr["eave"].append(eav[fi])
    mb.nv += len(verts)
    for k in mb.fattr:
        while len(mb.fattr[k]) < len(mb.faces):
            mb.fattr[k].append(0.0)
    if liggers:
        for side in (-1, 1):
            for yy in (0.2, 0.45):
                pts = []
                for x in np.linspace(-Lh + 0.05, Lh - 0.05, 30):
                    y = side * yy
                    pts.append((x, y, surf(x, y) + thick * (1 - 0.25 * yy / w0) + 0.004))
                parts.tube("hazel", pts, [0.013] * len(pts), sides=6)
            # cross spars between the two liggers
            n = int((2 * Lh - 0.2) / 0.32)
            for k in range(n):
                x0 = -Lh + 0.15 + k * 0.32
                for dx in (0.16, -0.16):
                    xa, xb = x0, x0 + dx
                    ya, yb = side * 0.2, side * 0.45
                    pa = (xa, ya, surf(xa, ya) + thick * (1 - 0.25 * 0.2 / w0) + 0.008)
                    pb = (xb, yb, surf(xb, yb) + thick * (1 - 0.25 * 0.45 / w0) + 0.008)
                    parts.tube("hazel", [pa, pb], [0.008, 0.008], sides=5)


def thatch_hipped(parts, L, D, z_eave, pitch_deg, oe=0.55, t=0.38, p=4.0, rng=None, key="thatch", nring=None, nper=120):
    """Hipped thatch with rounded hips from superellipse contour rings.
    L, D: outer wall dimensions; z_eave: underside height at the wall line."""
    rng = rng or parts.rng
    th = math.radians(pitch_deg)
    tn = math.tan(th)
    Lh = L / 2 + oe
    Dh = D / 2 + oe
    tv = t / math.cos(th)
    z0 = z_eave - oe * tn     # underside height at the outer eave line
    dmax = Dh - 0.04
    nring = nring or int(dmax / 0.07) + 4
    ds = np.concatenate([[0.0, 0.03], np.linspace(0.08, dmax, nring)])
    angs = np.linspace(0, 2 * np.pi, nper, endpoint=False)
    ca, sa = np.cos(angs), np.sin(angs)
    seedn = rng.randint(1000)

    def ring(d, dz=0.0, shrink=0.0):
        a = Lh - d - shrink
        b = Dh - d - shrink
        x = a * np.sign(ca) * np.abs(ca) ** (2 / p)
        y = b * np.sign(sa) * np.abs(sa) ** (2 / p)
        z = z0 + d * tn + dz
        return np.stack([x, y, np.full_like(x, z)], 1)
    top_rings = []
    for k, d in enumerate(ds):
        r = ring(d, tv)
        r[:, 2] += 0.03 * C.fbm(r[:, 0] / 1.2, r[:, 1] / 1.2, 3, seedn) + 0.01 * C.fbm(r[:, 0] / 0.3, r[:, 1] / 0.3, 2, seedn + 1)
        if k == 0:
            r[:, 2] -= 0.05   # rounded eave lip
        top_rings.append(r)
    bot = [ring(0.0, -0.0, shrink=0.2), ring(0.6, 0.0), ring(1.2, 0.0)]
    rings = top_rings + bot
    verts = np.concatenate(rings)
    nt = len(top_rings)
    faces, uvs, eav = [], [], []
    perim = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([top_rings[0], top_rings[0][:1]]), axis=0), axis=1))])[:-1]
    for k in range(nt - 1):
        for j in range(nper):
            j2 = (j + 1) % nper
            a = k * nper + j
            b = k * nper + j2
            c = (k + 1) * nper + j2
            d = (k + 1) * nper + j
            faces.append([a, b, c, d])
            v0 = ds[k] / math.cos(th)
            v1 = ds[k + 1] / math.cos(th)
            u0 = perim[j]
            u1 = perim[j2] if j2 else perim[-1] + 0.1
            uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
            eav.append(0.0)
    # cap the top: connect the last ring across (thin ellipse) with a fan to its centre
    last = (nt - 1) * nper
    cen = top_rings[-1].mean(0) + np.array([0, 0, 0.02])
    ci = len(verts)
    verts = np.vstack([verts, cen])
    for j in range(nper):
        j2 = (j + 1) % nper
        faces.append([last + j, last + j2, ci])
        uvs.append([(0, 9), (0.1, 9), (0.05, 9.1)])
        eav.append(0.0)
    # eave rim: top ring 0 to bottom ring 0
    b0 = nt * nper
    for j in range(nper):
        j2 = (j + 1) % nper
        faces.append([b0 + j, b0 + j2, j2, j])
        uvs.append([(perim[j], 0), (perim[j], 0), (perim[j], 0.3), (perim[j], 0.3)])
        eav.append(1.0)
    # underside band
    for k in range(2):
        for j in range(nper):
            j2 = (j + 1) % nper
            a = b0 + k * nper + j
            b = b0 + k * nper + j2
            c = b0 + (k + 1) * nper + j2
            d = b0 + (k + 1) * nper + j
            faces.append([d, c, b, a])
            uvs.append([(0, 0)] * 4)
            eav.append(0.0)
    mb = parts.mb[key]
    base = mb.nv
    mb.verts.append(verts)
    for fi, f in enumerate(faces):
        mb.faces.append([base + q for q in f])
        mb.uvs.append(uvs[fi])
        mb.mat.append(0)
        mb.frnd.append(0.5)
        mb.fattr.setdefault("eave", [0.0] * (len(mb.faces) - 1))
        mb.fattr["eave"].append(eav[fi])
    mb.nv += len(verts)
    for k in mb.fattr:
        while len(mb.fattr[k]) < len(mb.faces):
            mb.fattr[k].append(0.0)
    return dict(ridge_z=z0 + dmax * tn + tv, ridge_half=Lh - Dh, tn=tn, z0=z0, tv=tv, Lh=Lh, Dh=Dh, p=p, top0=top_rings[0])


def thatch_fringe_hipped(st, info, rng, per_m=60):
    """Straw ends along the cut eave of a hipped thatch."""
    ring = info["top0"]
    n = len(ring)
    cen = ring.mean(0)
    perim = np.sum(np.linalg.norm(np.diff(np.vstack([ring, ring[:1]]), axis=0), axis=1))
    count = int(perim * per_m)
    th = math.atan(info["tn"])
    for k in range(count):
        j = rng.randint(n)
        a = ring[j]
        b = ring[(j + 1) % n]
        t = rng.uniform()
        top = a + (b - a) * t
        out = top[:2] - cen[:2]
        out = out / (np.linalg.norm(out) + 1e-9)
        f = rng.uniform(0.05, 0.95)
        p = np.array([top[0] - out[0] * f * 0.2, top[1] - out[1] * f * 0.2, top[2] - f * (top[2] - info["z0"]) - 0.02])
        d = np.array([out[0] * math.cos(th) * 0.8, out[1] * math.cos(th) * 0.8, -math.sin(th) - 0.4]) + rng.normal(0, 0.3, 3)
        st.add(p - np.array([out[0], out[1], 0]) * 0.03, d, rng.uniform(0.02, 0.09), rng.uniform(0.004, 0.008), straw_colour(rng, 0.7), bend=np.array([0, 0, -0.3]))


def shingle_plane(parts, x0, x1, eave_y, ridge_y, z_eave, z_ridge, rng=None, key="shingle", expo=0.14, slen=0.42, th=0.013,
                  wrange=(0.1, 0.24), missing=0.01, batten_key=None, x_clip=None):
    """Shingles over a rectangular roof plane from the eave line (y=eave_y) up to the ridge line (y=ridge_y)."""
    rng = rng or parts.rng
    A = Vector((0, eave_y, z_eave))
    B = Vector((0, ridge_y, z_ridge))
    up = (B - A)
    Ls = up.length
    up.normalize()
    xdir = Vector((1, 0, 0))
    nrm = xdir.cross(up) if up.y < 0 else up.cross(xdir)
    if nrm.z < 0:
        nrm = -nrm
    nrm.normalize()
    k = 0
    s = -0.04
    while s < Ls - 0.05:
        x = x0 - rng.uniform(0, 0.1)
        while x < x1:
            w = rng.uniform(*wrange)
            xe = min(x + w, x1 + 0.02)
            if rng.uniform() > missing:
                lift = th * 2.0
                l = min(slen, Ls - s + 0.06)
                jit_s = rng.uniform(-0.01, 0.01)
                ww = xe - x - rng.uniform(0.004, 0.014)
                curl = rng.uniform(0, 0.012) if rng.uniform() < 0.12 else 0.0
                rot = rng.normal(0, 0.012)
                cxm = (x + xe) / 2
                # 8 corners: butt (s), top (s+l); butt raised by lift
                pts = []
                for (sv, lv) in ((0.0, lift), (l, 0.0)):
                    for side in (-0.5, 0.5):
                        xx = cxm + side * ww + rot * sv
                        base = A + up * (s + jit_s + sv) + xdir * (xx) + nrm * (lv + (curl if side > 0 and sv == 0 else 0.0))
                        pts.append(base)
                # bottom 4 then top 4 (offset by thickness)
                vb = [pts[0], pts[1], pts[3], pts[2]]
                vt = [p + nrm * th for p in vb]
                verts = np.array([tuple(p) for p in vb + vt])
                faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
                uvs = [[(0, 0), (0, l), (ww, l), (ww, 0)], [(0, 0), (ww, 0), (ww, l), (0, l)]] + [[(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01)]] * 4
                # grain runs along the slope -> make U along the slope for the top faces
                uvs[1] = [(0, 0), (0, ww), (l, ww), (l, 0)]
                parts.add(key, verts, faces, uvs, rnd=rng.uniform())
            x = xe
        if batten_key:
            # batten under this course (visible from inside)
            p0 = A + up * (s + slen * 0.75) + xdir * x0 - nrm * 0.03
            p1 = A + up * (s + slen * 0.75) + xdir * x1 - nrm * 0.03
            parts.beam(batten_key, p0, p1, 0.05, 0.025, up=nrm)
        s += expo
        k += 1
    return nrm


# ----------------------------------------------------------------------------
# Doors, windows, shutters, chimneys
# ----------------------------------------------------------------------------
def plank_door(parts, wall, s0, s1, z0, z1, d, open_deg=0.0, hinge_left=True, key="plank_dark", rng=None):
    """Plank door hung in the opening [s0,s1]x[z0,z1] of `wall`, outer face at depth d. Rotates inward."""
    rng = rng or parts.rng
    W = s1 - s0
    H = z1 - z0
    n = max(int(round(W / 0.16)), 4)
    pw = W / n
    hs = s0 if hinge_left else s1
    ang = math.radians(open_deg) * (1 if hinge_left else -1)
    hinge = wall.pt(hs, 0, d)
    R = wall.rot()

    def place(local):
        # local: (along wall from hinge, along normal, z) -> rotate about vertical hinge axis (opening inward)
        x, y, z = local
        ca, sa = math.cos(ang), math.sin(ang)
        xr = x * ca + y * sa
        yr = -x * sa + y * ca
        return hinge + wall.u * xr + wall.n * yr + Vector((0, 0, z))
    sign = 1 if hinge_left else -1
    for i in range(n):
        a = i * pw + 0.003
        b = (i + 1) * pw - 0.003
        corners = []
        for (xx, yy, zz) in [(a, -0.035, z0), (b, -0.035, z0), (b, 0.0, z0), (a, 0.0, z0), (a, -0.035, z1 - rng.uniform(0, 0.01)), (b, -0.035, z1), (b, 0.0, z1), (a, 0.0, z1)]:
            corners.append(place((sign * xx, yy, zz)))
        v = np.array([tuple(c) for c in corners])
        f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        uv = [[(0, 0), (H, 0), (H, pw), (0, pw)], [(0, 0), (0, pw), (H, pw), (H, 0)]] + [[(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01)]] * 4
        parts.add(key, v, f, uv, rnd=rng.uniform())
    # battens on the inside and strap hinges outside
    for zz in (z0 + 0.25, z1 - 0.3):
        c0 = place((sign * 0.03, -0.06, zz))
        c1 = place((sign * (W - 0.03), -0.06, zz))
        parts.beam(key, c0, c1, 0.03, 0.12)
        h0 = place((sign * -0.02, 0.008, zz))
        h1 = place((sign * W * 0.75, 0.008, zz))
        parts.beam("iron", h0, h1, 0.008, 0.045)
    # latch ring
    lp = place((sign * (W - 0.12), 0.02, z0 + 1.0))
    parts.cyl("iron", lp, lp + wall.n * 0.02, 0.025, sides=8)


def window_open(parts, wall, s0, s1, z0, z1, d_out, depth, bars=2, shutters=True, open_deg=110.0, rng=None):
    """Window opening with a small frame, mullion bars and open plank shutters."""
    rng = rng or parts.rng
    # frame lining
    wall.box(parts, "timber", s0, s0 + 0.05, z0, z1, d_out - depth, d_out - 0.02)
    wall.box(parts, "timber", s1 - 0.05, s1, z0, z1, d_out - depth, d_out - 0.02)
    for i in range(bars):
        s = s0 + (s1 - s0) * (i + 1) / (bars + 1)
        wall.box(parts, "timber", s - 0.02, s + 0.02, z0, z1, d_out - 0.09, d_out - 0.05)
    # dark backing (the room beyond)
    wall.box(parts, "interior", s0 - 0.05, s1 + 0.05, z0 - 0.05, z1 + 0.05, d_out - depth - 0.6, d_out - depth - 0.55)
    if shutters:
        W = (s1 - s0) / 2
        ang = math.radians(open_deg)
        for side, hs in ((-1, s0), (1, s1)):
            hinge = wall.pt(hs, 0, d_out + 0.012)
            dir_close = wall.u * (-side)
            sdir = dir_close * math.cos(ang) + wall.n * math.sin(ang)
            tdir = wall.n * math.cos(ang) - dir_close * math.sin(ang)
            n = 3
            H = z1 - z0
            for k in range(n):
                a = k * W / n + 0.003
                b = (k + 1) * W / n - 0.003
                corners = []
                for (xx, yy, zz) in [(a, 0, z0 + 0.01), (b, 0, z0 + 0.01), (b, 0.028, z0 + 0.01), (a, 0.028, z0 + 0.01),
                                     (a, 0, z1 - 0.01), (b, 0, z1 - 0.01), (b, 0.028, z1 - 0.01), (a, 0.028, z1 - 0.01)]:
                    corners.append(hinge + sdir * xx + tdir * yy + Vector((0, 0, zz)))
                v = np.array([tuple(c) for c in corners])
                f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
                uv = [[(0, 0), (H, 0), (H, 0.1), (0, 0.1)], [(0, 0), (0, 0.1), (H, 0.1), (H, 0)]] + [[(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01)]] * 4
                parts.add("plank_dark", v, f, uv, rnd=rng.uniform())
            # two battens across each shutter and hinge straps
            for zz in (z0 + 0.12, z1 - 0.12):
                p0 = hinge + sdir * 0.0 + tdir * 0.03 + Vector((0, 0, zz))
                p1 = hinge + sdir * (W - 0.02) + tdir * 0.03 + Vector((0, 0, zz))
                parts.beam("iron", p0, p1, 0.006, 0.035, up=Vector((0, 0, 1)))


def chimney(parts, base_xy, z_bottom, z_top, w=0.75, d=0.6, rng=None):
    """Rubble-stone chimney stack with a slate-ish cap."""
    rng = rng or parts.rng
    cx, cy = base_xy
    wall = Wall((cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (0, -1))
    walls = [
        Wall((cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (0, -1)),
        Wall((cx + w / 2, cy - d / 2), (cx + w / 2, cy + d / 2), (1, 0)),
        Wall((cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2), (0, 1)),
        Wall((cx - w / 2, cy + d / 2), (cx - w / 2, cy - d / 2), (-1, 0)),
    ]
    # core
    parts.box("mortar", (cx, cy, (z_bottom + z_top) / 2), (w - 0.06, d - 0.06, z_top - z_bottom))
    for i, wl in enumerate(walls):
        stone_wall(parts, wl, z_bottom, z_top, 0.12, rng=rng, course=(0.12, 0.2), slen=(0.15, 0.3),
                   alt_ext=((0.06, -0.06), (0.06, -0.06)) if i % 2 == 0 else ((-0.06, 0.06), (-0.06, 0.06)), depth=0.12, core=False)
    # cap stones and flue
    parts.box("stone", (cx, cy, z_top + 0.04), (w + 0.1, d + 0.1, 0.08))
    parts.box("interior", (cx, cy, z_top + 0.05), (w - 0.3, d - 0.3, 0.06))


# ----------------------------------------------------------------------------
# Straw strands (fuzzy thatch edges, hay)
# ----------------------------------------------------------------------------
class Strands:
    def __init__(self):
        self.v = []
        self.f = []
        self.c = []

    def add(self, p, d, length, width, col, bend=None, segs=2):
        """A thin straw strip from p along direction d (bending toward `bend` vector)."""
        p = np.asarray(p, float)
        d = np.asarray(d, float)
        d = d / (np.linalg.norm(d) + 1e-9)
        side = np.cross(d, [0, 0, 1.0])
        if np.linalg.norm(side) < 1e-4:
            side = np.array([1.0, 0, 0])
        side /= np.linalg.norm(side)
        # random roll of the strip
        b0 = len(self.v)
        pos = p.copy()
        for i in range(segs + 1):
            t = i / segs
            w = width * (1 - 0.5 * t)
            self.v.append(tuple(pos + side * w / 2))
            self.v.append(tuple(pos - side * w / 2))
            self.c.append(col)
            self.c.append(col)
            step = d + (np.asarray(bend) * t if bend is not None else 0)
            step = step / (np.linalg.norm(step) + 1e-9)
            pos = pos + step * (length / segs)
        for i in range(segs):
            a = b0 + 2 * i
            self.f.append([a, a + 1, a + 3, a + 2])

    def build(self, name, col, mat, parent=None):
        if not self.v:
            return None
        cols = np.array([tuple(c) + (1.0,) for c in self.c])
        me = C.mesh_from_arrays(name, np.array(self.v), self.f, point_attrs={"col": cols}, materials=[mat])
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        if parent is not None:
            ob.parent = parent
        return ob


def straw_colour(rng, aged=0.6):
    from plants import lin
    fresh = lin((0.62, 0.52, 0.30))
    old = lin((0.36, 0.33, 0.27))
    t = np.clip(aged + rng.normal(0, 0.2), 0, 1)
    return tuple(fresh * (1 - t) + old * t) if False else tuple((fresh * (1 - t) + old * t) * rng.uniform(0.7, 1.2))


def thatch_fringe_gabled(st, info, rng, density=900):
    """Straw ends sticking out of the cut eaves and verges of a gabled thatch."""
    Lh, Dh, tn, tv = info["Lh"], info["Dh"], info["tn"], info["tv"]
    surf = info["surface"]
    th = math.atan(tn)
    # eaves (long sides)
    n_e = int(2 * Lh * density / 6)
    for side in (-1, 1):
        for k in range(n_e):
            x = rng.uniform(-Lh + 0.05, Lh - 0.05)
            f = rng.uniform(0.05, 0.95)
            # a point on the sloped cut face between the top edge and the pulled-in bottom edge
            y = side * (Dh - 0.03 - f * 0.2)
            ztop = surf(x, side * (Dh - 0.02))
            z = ztop - f * (ztop - (info["z_wp"] + (info["D"] / 2 - Dh) * tn - 0.02))
            down = np.array([0, side * math.cos(th) * 0.8, -math.sin(th) - 0.4])
            d = down + rng.normal(0, 0.3, 3)
            L_ = rng.uniform(0.02, 0.09)
            st.add((x, y - side * 0.03, z), d, L_, rng.uniform(0.004, 0.008), straw_colour(rng, 0.7), bend=np.array([0, 0, -0.3]))
    # verges (gable ends)
    n_v = int(2 * Dh * density / 4)
    for side in (-1, 1):
        for k in range(n_v):
            y = rng.uniform(-Dh + 0.05, Dh - 0.05)
            x = side * (Lh - rng.uniform(0.0, 0.05))
            ztop = surf(x, y) - 0.02
            z = ztop - rng.uniform(0.02, tv * 0.9)
            d = np.array([side * 1.0, 0, -0.2]) + rng.normal(0, 0.3, 3)
            st.add((x - side * 0.05, y, z), d, rng.uniform(0.04, 0.16), rng.uniform(0.004, 0.009), straw_colour(rng), bend=np.array([0, 0, -0.4]))
    # loose strands lying on the surface
    n_s = int(4 * Lh * Dh * 12)
    for k in range(n_s):
        x = rng.uniform(-Lh + 0.1, Lh - 0.1)
        y = rng.uniform(-Dh + 0.1, Dh - 0.1)
        z = surf(x, y) - 0.005
        side = 1 if y > 0 else -1
        down = np.array([0, side * math.cos(th), -math.sin(th)])
        d = down + rng.normal(0, 0.35, 3)
        d[2] = -abs(d[2]) * 0.3 - math.sin(th) * 0.8
        st.add((x, y, z), d, rng.uniform(0.08, 0.25), rng.uniform(0.003, 0.005), straw_colour(rng, 0.75), bend=None, segs=1)
