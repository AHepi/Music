"""Shared helpers for the village build: noise, mesh builder, node-material builder, async jobs.
Everything is procedural; nothing is read from outside this folder."""
import bpy, bmesh, math, os, sys, time, threading, traceback, random
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion, kdtree

BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control'
SCRIPTS = BASE + '/scripts'
PREV = BASE + '/previews'
PICS = BASE + '/pictures'
BLEND = BASE + '/village.blend'

# ------------------------------------------------------------------ math helpers
def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def euler_mat(rx=0.0, ry=0.0, rz=0.0):
    return rotz(rz) @ roty(ry) @ rotx(rx)

def basis_from_dir(d, up=(0.0, 0.0, 1.0)):
    """Matrix whose local +Z axis points along d (columns = x, y, z)."""
    z = np.asarray(d, float)
    z = z / (np.linalg.norm(z) + 1e-12)
    up = np.asarray(up, float)
    if abs(np.dot(z, up)) > 0.98:
        up = np.array([1.0, 0.0, 0.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x) + 1e-12
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=1)

# ------------------------------------------------------------------ noise (numpy, vectorised)
_GRADS = np.array([[1, 1], [-1, 1], [1, -1], [-1, -1], [1, 0], [-1, 0], [0, 1], [0, -1]], dtype=np.float64)
_perm_cache = {}

def _perm(seed):
    if seed not in _perm_cache:
        rng = np.random.RandomState(seed & 0x7fffffff)
        p = rng.permutation(256).astype(np.int64)
        _perm_cache[seed] = np.concatenate([p, p])
    return _perm_cache[seed]

def perlin2(x, y, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    p = _perm(seed)
    x0 = np.floor(x)
    y0 = np.floor(y)
    xi = x0.astype(np.int64) & 255
    yi = y0.astype(np.int64) & 255
    xf = x - x0
    yf = y - y0
    u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
    v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
    aa = p[p[xi] + yi]
    ab = p[p[xi] + yi + 1]
    ba = p[p[xi + 1] + yi]
    bb = p[p[xi + 1] + yi + 1]

    def g(h, dx, dy):
        gr = _GRADS[h & 7]
        return gr[..., 0] * dx + gr[..., 1] * dy

    x1 = g(aa, xf, yf) * (1 - u) + g(ba, xf - 1, yf) * u
    x2 = g(ab, xf, yf - 1) * (1 - u) + g(bb, xf - 1, yf - 1) * u
    return (x1 * (1 - v) + x2 * v) * 1.41

def fbm2(x, y, octaves=5, lac=2.0, gain=0.5, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    tot = np.zeros(np.broadcast(x, y).shape)
    amp = 1.0
    f = 1.0
    norm = 0.0
    for o in range(octaves):
        tot = tot + amp * perlin2(x * f + 17.3 * o, y * f - 9.1 * o, seed + o * 7)
        norm += amp
        amp *= gain
        f *= lac
    return tot / norm

def noise3(p, seed=0):
    """Value noise in 3D; p is (N,3). Returns (N,) in [-1,1]."""
    p = np.asarray(p, dtype=np.float64)
    perm = _perm(seed)
    vals = np.random.RandomState((seed + 11) & 0x7fffffff).rand(256) * 2 - 1
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    x0, y0, z0 = np.floor(x), np.floor(y), np.floor(z)
    xi, yi, zi = x0.astype(np.int64) & 255, y0.astype(np.int64) & 255, z0.astype(np.int64) & 255
    xf, yf, zf = x - x0, y - y0, z - z0
    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    w = zf * zf * (3 - 2 * zf)

    def h(ix, iy, iz):
        return vals[perm[perm[perm[ix & 255] + (iy & 255)] + (iz & 255)]]

    c000 = h(xi, yi, zi); c100 = h(xi + 1, yi, zi)
    c010 = h(xi, yi + 1, zi); c110 = h(xi + 1, yi + 1, zi)
    c001 = h(xi, yi, zi + 1); c101 = h(xi + 1, yi, zi + 1)
    c011 = h(xi, yi + 1, zi + 1); c111 = h(xi + 1, yi + 1, zi + 1)
    x00 = c000 * (1 - u) + c100 * u
    x10 = c010 * (1 - u) + c110 * u
    x01 = c001 * (1 - u) + c101 * u
    x11 = c011 * (1 - u) + c111 * u
    y0_ = x00 * (1 - v) + x10 * v
    y1_ = x01 * (1 - v) + x11 * v
    return y0_ * (1 - w) + y1_ * w

def fbm3(p, octaves=4, lac=2.0, gain=0.5, seed=0):
    p = np.asarray(p, dtype=np.float64)
    tot = np.zeros(len(p))
    amp = 1.0
    f = 1.0
    norm = 0.0
    for o in range(octaves):
        tot += amp * noise3(p * f + 31.7 * o, seed + 5 * o)
        norm += amp
        amp *= gain
        f *= lac
    return tot / norm

# ------------------------------------------------------------------ mesh builder
class MB:
    """Accumulates vertices, triangles and quads (with per-loop UVs and material indices) as numpy arrays."""

    def __init__(self):
        self.V = []
        self.nv = 0
        self.Q = []; self.QUV = []; self.QM = []; self.QS = []
        self.T = []; self.TUV = []; self.TM = []; self.TS = []
        self.A = {}          # name -> list of arrays aligned with V
        self.rng = np.random.RandomState(1)

    # ---- vertices
    def verts(self, P, **attrs):
        P = np.asarray(P, dtype=np.float64).reshape(-1, 3)
        n = len(P)
        base = self.nv
        names = set(self.A.keys()) | set(attrs.keys())
        for nm in names:
            if nm not in self.A:
                self.A[nm] = [np.zeros(self.nv)] if self.nv else []
            val = attrs.get(nm, 0.0)
            val = np.broadcast_to(np.asarray(val, dtype=np.float64), (n,)).copy()
            self.A[nm].append(val)
        self.V.append(P)
        self.nv += n
        return base

    # ---- faces
    def quads(self, idx, uv=None, mat=0, smooth=True):
        idx = np.asarray(idx, dtype=np.int64).reshape(-1, 4)
        n = len(idx)
        if uv is None:
            uv = np.zeros((n, 4, 2))
        uv = np.asarray(uv, dtype=np.float64).reshape(n, 4, 2)
        self.Q.append(idx); self.QUV.append(uv)
        self.QM.append(np.broadcast_to(np.asarray(mat, dtype=np.int64), (n,)).copy())
        self.QS.append(np.broadcast_to(np.asarray(smooth, dtype=bool), (n,)).copy())

    def tris(self, idx, uv=None, mat=0, smooth=True):
        idx = np.asarray(idx, dtype=np.int64).reshape(-1, 3)
        n = len(idx)
        if uv is None:
            uv = np.zeros((n, 3, 2))
        uv = np.asarray(uv, dtype=np.float64).reshape(n, 3, 2)
        self.T.append(idx); self.TUV.append(uv)
        self.TM.append(np.broadcast_to(np.asarray(mat, dtype=np.int64), (n,)).copy())
        self.TS.append(np.broadcast_to(np.asarray(smooth, dtype=bool), (n,)).copy())

    def quads_hard(self, P4, uv4=None, mat=0, smooth=False, **attrs):
        P4 = np.asarray(P4, dtype=np.float64).reshape(-1, 4, 3)
        n = len(P4)
        a2 = {k: np.repeat(np.broadcast_to(np.asarray(v, float), (n,)), 4) for k, v in attrs.items()}
        base = self.verts(P4.reshape(-1, 3), **a2)
        idx = base + np.arange(n * 4).reshape(n, 4)
        self.quads(idx, uv4, mat, smooth)

    def tris_hard(self, P3, uv3=None, mat=0, smooth=False, **attrs):
        P3 = np.asarray(P3, dtype=np.float64).reshape(-1, 3, 3)
        n = len(P3)
        a2 = {k: np.repeat(np.broadcast_to(np.asarray(v, float), (n,)), 3) for k, v in attrs.items()}
        base = self.verts(P3.reshape(-1, 3), **a2)
        idx = base + np.arange(n * 3).reshape(n, 3)
        self.tris(idx, uv3, mat, smooth)

    # ---- transforms of what was added since a mark
    def mark(self):
        return (len(self.V), len(self.Q), len(self.T))

    def xform_since(self, mark, R=None, t=(0, 0, 0), s=1.0):
        R = np.eye(3) if R is None else np.asarray(R, float)
        t = np.asarray(t, float)
        for i in range(mark[0], len(self.V)):
            self.V[i] = (self.V[i] * s) @ R.T + t

    # ---- primitives
    def box(self, c, size, R=None, mat=0, uvoff=None, uvscale=1.0, smooth=False, grain=None, bevel=0.0):
        sx, sy, sz = size
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        corners = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], dtype=np.float64) * np.array([hx, hy, hz])
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5)]
        axes = [(0, 1), (0, 1), (0, 2), (0, 2), (1, 2), (1, 2)]
        if grain is None:
            grain = int(np.argmax([sx, sy, sz]))
        if uvoff is None:
            uvoff = self.rng.rand(2) * 20.0
        P4 = np.zeros((6, 4, 3))
        UV = np.zeros((6, 4, 2))
        for fi, (f, (a, b)) in enumerate(zip(faces, axes)):
            P4[fi] = corners[list(f)]
            ca = P4[fi][:, a]
            cb = P4[fi][:, b]
            if grain == b:
                u_, v_ = cb, ca
            else:
                u_, v_ = ca, cb
            UV[fi, :, 0] = u_ * uvscale + uvoff[0]
            UV[fi, :, 1] = v_ * uvscale + uvoff[1]
        if R is not None:
            P4 = P4 @ np.asarray(R, float).T
        P4 = P4 + np.asarray(c, float)
        self.quads_hard(P4, UV, mat, smooth)

    def tube(self, pts, radii, sides=8, mat=0, cap0=False, cap1=False, smooth=True, uvscale=1.0, uvoff=(0.0, 0.0), swap_uv=False, **attrs):
        pts = np.asarray(pts, dtype=np.float64)
        n = len(pts)
        radii = np.broadcast_to(np.asarray(radii, dtype=np.float64), (n,)).copy()
        T = np.zeros_like(pts)
        if n > 2:
            T[1:-1] = pts[2:] - pts[:-2]
        T[0] = pts[1] - pts[0]
        T[-1] = pts[-1] - pts[-2]
        T /= (np.linalg.norm(T, axis=1, keepdims=True) + 1e-12)
        ref = np.array([0.0, 0.0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        N = np.zeros_like(pts)
        n0 = np.cross(T[0], ref)
        N[0] = n0 / (np.linalg.norm(n0) + 1e-12)
        for i in range(1, n):
            v = N[i - 1] - T[i] * np.dot(N[i - 1], T[i])
            nn = np.linalg.norm(v)
            if nn < 1e-9:
                v = np.cross(T[i], ref); nn = np.linalg.norm(v) + 1e-12
            N[i] = v / nn
        B = np.cross(T, N)
        ang = np.arange(sides) * (2 * math.pi / sides)
        ring = np.cos(ang)[None, :, None] * N[:, None, :] + np.sin(ang)[None, :, None] * B[:, None, :]
        P = pts[:, None, :] + ring * radii[:, None, None]
        a2 = {k: np.repeat(np.broadcast_to(np.asarray(v, float), (n,)), sides) for k, v in attrs.items()}
        base = self.verts(P.reshape(-1, 3), **a2)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        Vc = np.concatenate([[0.0], np.cumsum(seg)])
        i = np.arange(n - 1)[:, None]
        j = np.arange(sides)[None, :]
        ia = base + i * sides + j
        ib = base + i * sides + (j + 1) % sides
        ic = base + (i + 1) * sides + (j + 1) % sides
        idd = base + (i + 1) * sides + j
        idx = np.stack([ia, ib, ic, idd], axis=-1).reshape(-1, 4)
        circ = 2 * math.pi * radii
        ua = (j / sides) * circ[:-1, None]
        ub = ((j + 1) / sides) * circ[:-1, None]
        uc = ((j + 1) / sides) * circ[1:, None]
        ud = (j / sides) * circ[1:, None]
        va = np.broadcast_to(Vc[:-1, None], (n - 1, sides))
        vc = np.broadcast_to(Vc[1:, None], (n - 1, sides))
        UV = np.stack([np.stack([ua, va], -1), np.stack([ub, va], -1), np.stack([uc, vc], -1), np.stack([ud, vc], -1)], axis=2)
        UV = UV.reshape(-1, 4, 2) * uvscale + np.asarray(uvoff)
        if swap_uv:
            UV = UV[:, :, ::-1].copy()
        self.quads(idx, UV, mat, smooth)
        if cap0:
            cb = self.verts(pts[0][None, :], **{k: v for k, v in attrs.items() if np.isscalar(v)})
            ring0 = base + np.arange(sides)
            tri = np.stack([np.full(sides, cb), ring0, np.roll(ring0, -1)], axis=1)
            tri = tri[:, [0, 2, 1]]
            self.tris(tri, None, mat, smooth)
        if cap1:
            cb = self.verts(pts[-1][None, :], **{k: v for k, v in attrs.items() if np.isscalar(v)})
            ring1 = base + (n - 1) * sides + np.arange(sides)
            tri = np.stack([np.full(sides, cb), ring1, np.roll(ring1, -1)], axis=1)
            self.tris(tri, None, mat, smooth)
        return base

    def lathe(self, profile, sides=16, mat=0, smooth=True, uvscale=1.0, cap_bottom=False, cap_top=False, wobble=None, swap_uv=False):
        """Surface of revolution about +Z. profile: list of (r, z). wobble: optional function(theta_array, z)->radius scale."""
        prof = np.asarray(profile, dtype=np.float64)
        n = len(prof)
        ang = np.arange(sides) * (2 * math.pi / sides)
        r = np.maximum(prof[:, 0], 1e-4)
        rr = np.broadcast_to(r[:, None], (n, sides)).copy()
        if wobble is not None:
            rr = rr * wobble(ang[None, :], prof[:, 1][:, None])
        P = np.zeros((n, sides, 3))
        P[:, :, 0] = rr * np.cos(ang)[None, :]
        P[:, :, 1] = rr * np.sin(ang)[None, :]
        P[:, :, 2] = prof[:, 1][:, None]
        base = self.verts(P.reshape(-1, 3))
        seg = np.linalg.norm(np.diff(prof, axis=0), axis=1)
        Vc = np.concatenate([[0.0], np.cumsum(seg)])
        i = np.arange(n - 1)[:, None]
        j = np.arange(sides)[None, :]
        ia = base + i * sides + j
        ib = base + i * sides + (j + 1) % sides
        ic = base + (i + 1) * sides + (j + 1) % sides
        idd = base + (i + 1) * sides + j
        idx = np.stack([ia, ib, ic, idd], axis=-1).reshape(-1, 4)
        # winding: profile goes bottom->top with increasing angle CCW; normals outward for increasing z
        idx = idx[:, [0, 3, 2, 1]]
        circ = 2 * math.pi * r
        ua = (j / sides) * circ[:-1, None]
        ub = ((j + 1) / sides) * circ[:-1, None]
        uc = ((j + 1) / sides) * circ[1:, None]
        ud = (j / sides) * circ[1:, None]
        va = np.broadcast_to(Vc[:-1, None], (n - 1, sides))
        vc = np.broadcast_to(Vc[1:, None], (n - 1, sides))
        UV = np.stack([np.stack([ua, va], -1), np.stack([ub, va], -1), np.stack([uc, vc], -1), np.stack([ud, vc], -1)], axis=2)
        UV = UV.reshape(-1, 4, 2)[:, [0, 3, 2, 1]] * uvscale
        if swap_uv:
            UV = UV[:, :, ::-1].copy()
        self.quads(idx, UV, mat, smooth)
        if cap_bottom:
            cb = self.verts(np.array([[0.0, 0.0, prof[0, 1]]]))
            ring0 = base + np.arange(sides)
            tri = np.stack([np.full(sides, cb), ring0, np.roll(ring0, -1)], axis=1)
            self.tris(tri, None, mat, False)
        if cap_top:
            cb = self.verts(np.array([[0.0, 0.0, prof[-1, 1]]]))
            ring1 = base + (n - 1) * sides + np.arange(sides)
            tri = np.stack([np.full(sides, cb), np.roll(ring1, -1), ring1], axis=1)
            self.tris(tri, None, mat, False)
        return base

    def grid(self, P, uv=None, mat=0, smooth=True, flip=False, wrap_u=False, wrap_v=False, **attrs):
        """P: (nu, nv, 3). Quads between neighbours (i along first axis, j along second)."""
        P = np.asarray(P, dtype=np.float64)
        nu, nv = P.shape[:2]
        a2 = {k: np.asarray(v, float).reshape(-1) for k, v in attrs.items()}
        base = self.verts(P.reshape(-1, 3), **a2)
        ni = nu if wrap_u else nu - 1
        nj = nv if wrap_v else nv - 1
        i = np.arange(ni)[:, None]
        j = np.arange(nj)[None, :]
        i1 = (i + 1) % nu
        j1 = (j + 1) % nv
        ia = base + i * nv + j
        ib = base + i1 * nv + j
        ic = base + i1 * nv + j1
        idd = base + i * nv + j1
        idx = np.stack([np.broadcast_to(ia, (ni, nj)), np.broadcast_to(ib, (ni, nj)), np.broadcast_to(ic, (ni, nj)), np.broadcast_to(idd, (ni, nj))], axis=-1).reshape(-1, 4)
        if flip:
            idx = idx[:, [0, 3, 2, 1]]
        if uv is not None:
            uv = np.asarray(uv, dtype=np.float64)
            uva = uv[:-1, :-1] if not (wrap_u or wrap_v) else None
            if uva is not None:
                UV = np.stack([uv[:-1, :-1], uv[1:, :-1], uv[1:, 1:], uv[:-1, 1:]], axis=2).reshape(-1, 4, 2)
                if flip:
                    UV = UV[:, [0, 3, 2, 1]]
            else:
                UV = None
        else:
            UV = None
        self.quads(idx, UV, mat, smooth)
        return base

    def polygon_fan(self, pts, mat=0, flip=False, uv=None, smooth=False):
        pts = np.asarray(pts, float)
        c = pts.mean(axis=0)
        base = self.verts(np.vstack([c[None, :], pts]))
        n = len(pts)
        i = np.arange(n)
        tri = np.stack([np.full(n, base), base + 1 + i, base + 1 + (i + 1) % n], axis=1)
        if flip:
            tri = tri[:, [0, 2, 1]]
        self.tris(tri, None, mat, smooth)

    def extend(self, other, R=None, t=(0, 0, 0), s=1.0, mat_map=None):
        """Append another builder (optionally transformed)."""
        R = np.eye(3) if R is None else np.asarray(R, float)
        t = np.asarray(t, float)
        base = self.nv
        P = np.concatenate(other.V) if other.V else np.zeros((0, 3))
        P = (P * s) @ R.T + t
        names = set(self.A.keys()) | set(other.A.keys())
        n = len(P)
        for nm in names:
            if nm not in self.A:
                self.A[nm] = [np.zeros(self.nv)] if self.nv else []
            if nm in other.A:
                self.A[nm].append(np.concatenate(other.A[nm]))
            else:
                self.A[nm].append(np.zeros(n))
        self.V.append(P)
        self.nv += n
        for src, dst, k in ((other.Q, self.Q, 4), (other.T, self.T, 3)):
            for arr in src:
                dst.append(arr + base)
        self.QUV += other.QUV; self.TUV += other.TUV
        for m_src, m_dst in ((other.QM, self.QM), (other.TM, self.TM)):
            for m in m_src:
                m_dst.append(np.array([mat_map.get(int(x), int(x)) for x in m]) if mat_map else m.copy())
        self.QS += other.QS; self.TS += other.TS

    def add_instances(self, tmpl, pos, yaw, scale, jitter=None, rng=None):
        """Replicate template builder `tmpl` at many positions (yaw about Z, uniform scale). Vectorised."""
        V = np.concatenate(tmpl.V)
        nv = len(V)
        pos = np.asarray(pos, float).reshape(-1, 3)
        n = len(pos)
        yaw = np.broadcast_to(np.asarray(yaw, float), (n,))
        scale = np.broadcast_to(np.asarray(scale, float), (n,))
        c, s = np.cos(yaw), np.sin(yaw)
        X = V[None, :, 0] * scale[:, None]; Y = V[None, :, 1] * scale[:, None]; Z = V[None, :, 2] * scale[:, None]
        P = np.stack([c[:, None] * X - s[:, None] * Y + pos[:, 0:1], s[:, None] * X + c[:, None] * Y + pos[:, 1:2], Z + pos[:, 2:3]], axis=-1).reshape(-1, 3)
        attrs = {}
        for nm, lst in tmpl.A.items():
            arr = np.concatenate(lst)
            big = np.tile(arr, n)
            if jitter and nm in jitter:
                r = (rng or np.random).rand(n)
                big = (big.reshape(n, nv) + r[:, None] * jitter[nm]).reshape(-1) % 1.0
            attrs[nm] = big
        base = self.verts(P, **attrs)
        offs = (base + np.arange(n) * nv)[:, None, None]
        for lst_i, lst_uv, lst_m, lst_s, k, dst in ((tmpl.Q, tmpl.QUV, tmpl.QM, tmpl.QS, 4, 'q'), (tmpl.T, tmpl.TUV, tmpl.TM, tmpl.TS, 3, 't')):
            if not lst_i:
                continue
            F = np.concatenate(lst_i)
            UV = np.concatenate(lst_uv)
            M = np.concatenate(lst_m)
            S = np.concatenate(lst_s)
            idx = (offs + F[None]).reshape(-1, k)
            uvt = np.tile(UV, (n, 1, 1))
            if dst == 'q':
                self.quads(idx, uvt, np.tile(M, n), np.tile(S, n))
            else:
                self.tris(idx, uvt, np.tile(M, n), np.tile(S, n))

    # ---- build
    def build(self, name, mats=(), mesh=None):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), dtype=np.int64)
        T = np.concatenate(self.T) if self.T else np.zeros((0, 3), dtype=np.int64)
        QUV = np.concatenate(self.QUV) if self.QUV else np.zeros((0, 4, 2))
        TUV = np.concatenate(self.TUV) if self.TUV else np.zeros((0, 3, 2))
        QM = np.concatenate(self.QM) if self.QM else np.zeros(0, dtype=np.int64)
        TM = np.concatenate(self.TM) if self.TM else np.zeros(0, dtype=np.int64)
        QS = np.concatenate(self.QS) if self.QS else np.zeros(0, dtype=bool)
        TS = np.concatenate(self.TS) if self.TS else np.zeros(0, dtype=bool)
        nq, nt = len(Q), len(T)
        me = mesh if mesh is not None else bpy.data.meshes.new(name)
        me.vertices.add(len(V))
        me.vertices.foreach_set('co', V.astype(np.float32).ravel())
        loop_v = np.concatenate([Q.ravel(), T.ravel()]).astype(np.int32)
        me.loops.add(len(loop_v))
        me.loops.foreach_set('vertex_index', loop_v)
        me.polygons.add(nq + nt)
        starts = np.concatenate([np.arange(nq) * 4, nq * 4 + np.arange(nt) * 3]).astype(np.int32)
        me.polygons.foreach_set('loop_start', starts)
        me.polygons.foreach_set('loop_total', np.concatenate([np.full(nq, 4), np.full(nt, 3)]).astype(np.int32))
        me.update(calc_edges=True)
        uv = me.uv_layers.new(name='UVMap')
        uvall = np.concatenate([QUV.reshape(-1, 2), TUV.reshape(-1, 2)]).astype(np.float32)
        uv.data.foreach_set('uv', uvall.ravel())
        me.polygons.foreach_set('material_index', np.concatenate([QM, TM]).astype(np.int32))
        me.polygons.foreach_set('use_smooth', np.concatenate([QS, TS]).astype(bool))
        for nm, lst in self.A.items():
            arr = np.concatenate(lst).astype(np.float32)
            at = me.attributes.new(name=nm, type='FLOAT', domain='POINT')
            at.data.foreach_set('value', arr)
        for m in mats:
            me.materials.append(m)
        me.update()
        return me

# ------------------------------------------------------------------ scene helpers
def get_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def add_obj(name, mesh, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, mesh)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    return ob

def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for ma in list(bpy.data.materials):
        bpy.data.materials.remove(ma)
    for im in list(bpy.data.images):
        bpy.data.images.remove(im)

# ------------------------------------------------------------------ material builder (node DSL)
class MatB:
    def __init__(self, name, replace=True):
        old = bpy.data.materials.get(name)
        if old is not None and replace:
            self.m = old          # keep the datablock so meshes that use it keep their slots
        else:
            self.m = bpy.data.materials.new(name)
        self.m.use_nodes = True
        self.nt = self.m.node_tree
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self.nodes.clear()
        self.out = self.nodes.new('ShaderNodeOutputMaterial')
        self._tc = None

    # -- plumbing
    def _set(self, sock, val):
        if val is None:
            return
        if isinstance(val, bpy.types.NodeSocket):
            self.links.new(val, sock)
        elif hasattr(val, 'outputs'):
            self.links.new(val.outputs[0], sock)
        else:
            if sock.type == 'RGBA':
                if len(val) == 3:
                    val = (val[0], val[1], val[2], 1.0)
            elif sock.type == 'VECTOR' and np.isscalar(val):
                val = (val, val, val)
            sock.default_value = val

    def node(self, idname, **props):
        n = self.nodes.new(idname)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def tc(self):
        if self._tc is None:
            self._tc = self.nodes.new('ShaderNodeTexCoord')
        return self._tc

    def uv(self):
        return self.tc().outputs['UV']

    def objc(self):
        return self.tc().outputs['Object']

    def gen(self):
        return self.tc().outputs['Generated']

    def attr(self, name, out='Fac'):
        n = self.nodes.new('ShaderNodeAttribute')
        n.attribute_name = name
        n.attribute_type = 'GEOMETRY'
        return n.outputs[out]

    def position(self):
        n = self.nodes.new('ShaderNodeNewGeometry')
        return n.outputs['Position']

    def geometry(self, out):
        n = self.nodes.new('ShaderNodeNewGeometry')
        return n.outputs[out]

    def obj_random(self):
        n = self.nodes.new('ShaderNodeObjectInfo')
        return n.outputs['Random']

    def mapping(self, vec, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), vtype='POINT'):
        n = self.nodes.new('ShaderNodeMapping')
        n.vector_type = vtype
        self._set(n.inputs['Vector'], vec)
        self._set(n.inputs['Location'], loc)
        self._set(n.inputs['Rotation'], rot)
        self._set(n.inputs['Scale'], scale)
        return n.outputs['Vector']

    def noise(self, vec=None, scale=5.0, detail=2.0, rough=0.5, distortion=0.0, lac=2.0, w=None, dims='3D', out='Factor', ntype='FBM', normalize=True):
        n = self.nodes.new('ShaderNodeTexNoise')
        n.noise_dimensions = dims
        n.noise_type = ntype
        n.normalize = normalize
        self._set(n.inputs['Scale'], scale)
        self._set(n.inputs['Detail'], detail)
        self._set(n.inputs['Roughness'], rough)
        self._set(n.inputs['Distortion'], distortion)
        self._set(n.inputs['Lacunarity'], lac)
        if w is not None:
            self._set(n.inputs['W'], w)
        if vec is not None:
            self._set(n.inputs['Vector'], vec)
        return n.outputs[out]

    def voronoi(self, vec=None, scale=5.0, feature='F1', rand=1.0, out='Distance', dims='3D', smooth=None, w=None, detail=0.0, rough=0.5, ret_node=False):
        n = self.nodes.new('ShaderNodeTexVoronoi')
        n.voronoi_dimensions = dims
        n.feature = feature
        self._set(n.inputs['Scale'], scale)
        self._set(n.inputs['Randomness'], rand)
        if detail:
            self._set(n.inputs['Detail'], detail)
            self._set(n.inputs['Roughness'], rough)
        if smooth is not None:
            self._set(n.inputs['Smoothness'], smooth)
        if w is not None:
            self._set(n.inputs['W'], w)
        if vec is not None:
            self._set(n.inputs['Vector'], vec)
        if ret_node:
            return n
        return n.outputs[out]

    def sepcol(self, col):
        n = self.nodes.new('ShaderNodeSeparateColor')
        n.mode = 'RGB'
        self._set(n.inputs[0], col)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def wave(self, vec=None, scale=5.0, distortion=0.0, detail=0.0, dscale=1.0, drough=0.5, wtype='BANDS', direction='X', profile='SIN', phase=0.0, out='Factor'):
        n = self.nodes.new('ShaderNodeTexWave')
        n.wave_type = wtype
        n.bands_direction = direction
        n.wave_profile = profile
        self._set(n.inputs['Scale'], scale)
        self._set(n.inputs['Distortion'], distortion)
        self._set(n.inputs['Detail'], detail)
        self._set(n.inputs['Detail Scale'], dscale)
        self._set(n.inputs['Detail Roughness'], drough)
        self._set(n.inputs['Phase Offset'], phase)
        if vec is not None:
            self._set(n.inputs['Vector'], vec)
        return n.outputs[out]

    def brick(self, vec=None, scale=5.0, mortar_size=0.02, bias=0.0, bw=0.5, rh=0.25, offset=0.5, c1=(0.5, 0.5, 0.5), c2=(0.4, 0.4, 0.4), mortar=(0.1, 0.1, 0.1), smooth=0.1, out='Color'):
        n = self.nodes.new('ShaderNodeTexBrick')
        n.offset = offset
        self._set(n.inputs['Scale'], scale)
        self._set(n.inputs['Mortar Size'], mortar_size)
        self._set(n.inputs['Mortar Smooth'], smooth)
        self._set(n.inputs['Bias'], bias)
        self._set(n.inputs['Brick Width'], bw)
        self._set(n.inputs['Row Height'], rh)
        self._set(n.inputs['Color1'], c1)
        self._set(n.inputs['Color2'], c2)
        self._set(n.inputs['Mortar'], mortar)
        if vec is not None:
            self._set(n.inputs['Vector'], vec)
        return n.outputs[out]

    def ramp(self, fac, stops, interp='LINEAR', out='Color'):
        n = self.nodes.new('ShaderNodeValToRGB')
        cr = n.color_ramp
        cr.interpolation = interp
        els = cr.elements
        while len(els) > 1:
            els.remove(els[len(els) - 1])
        els[0].position = stops[0][0]
        for p, c in stops[1:]:
            els.new(p)
        for i, (p, c) in enumerate(stops):
            c = tuple(c) if len(c) == 4 else (c[0], c[1], c[2], 1.0)
            els[i].color = c
        self._set(n.inputs['Factor'], fac)
        return n.outputs[out]

    def mixc(self, fac, a, b, blend='MIX', clamp=True):
        n = self.nodes.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = blend
        n.clamp_factor = clamp
        self._set(n.inputs[0], fac)
        self._set(n.inputs[6], a)
        self._set(n.inputs[7], b)
        return n.outputs[2]

    def mixf(self, fac, a, b, clamp=True):
        n = self.nodes.new('ShaderNodeMix')
        n.data_type = 'FLOAT'
        n.clamp_factor = clamp
        self._set(n.inputs[0], fac)
        self._set(n.inputs[2], a)
        self._set(n.inputs[3], b)
        return n.outputs[0]

    def mixv(self, fac, a, b, clamp=True):
        n = self.nodes.new('ShaderNodeMix')
        n.data_type = 'VECTOR'
        n.clamp_factor = clamp
        self._set(n.inputs[0], fac)
        self._set(n.inputs[4], a)
        self._set(n.inputs[5], b)
        return n.outputs[1]

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.nodes.new('ShaderNodeMath')
        n.operation = op
        n.use_clamp = clamp
        self._set(n.inputs[0], a)
        if b is not None:
            self._set(n.inputs[1], b)
        if c is not None:
            self._set(n.inputs[2], c)
        return n.outputs[0]

    def vmath(self, op, a, b=None, c=None, out='Vector'):
        n = self.nodes.new('ShaderNodeVectorMath')
        n.operation = op
        self._set(n.inputs[0], a)
        if b is not None:
            self._set(n.inputs[1], b)
        if c is not None:
            self._set(n.inputs[2], c)
        return n.outputs[out]

    def maprange(self, v, fmin=0.0, fmax=1.0, tmin=0.0, tmax=1.0, clamp=True, interp='LINEAR'):
        n = self.nodes.new('ShaderNodeMapRange')
        n.data_type = 'FLOAT'
        n.clamp = clamp
        n.interpolation_type = interp
        self._set(n.inputs['Value'], v)
        self._set(n.inputs[1], fmin)
        self._set(n.inputs[2], fmax)
        self._set(n.inputs[3], tmin)
        self._set(n.inputs[4], tmax)
        return n.outputs[0]

    def sepxyz(self, vec):
        n = self.nodes.new('ShaderNodeSeparateXYZ')
        self._set(n.inputs['Vector'], vec)
        return n.outputs['X'], n.outputs['Y'], n.outputs['Z']

    def combxyz(self, x=0.0, y=0.0, z=0.0):
        n = self.nodes.new('ShaderNodeCombineXYZ')
        self._set(n.inputs['X'], x); self._set(n.inputs['Y'], y); self._set(n.inputs['Z'], z)
        return n.outputs['Vector']

    def hsv(self, color, hue=0.5, sat=1.0, val=1.0, fac=1.0):
        n = self.nodes.new('ShaderNodeHueSaturation')
        self._set(n.inputs['Hue'], hue); self._set(n.inputs['Saturation'], sat)
        self._set(n.inputs['Value'], val); self._set(n.inputs['Factor'], fac)
        self._set(n.inputs['Color'], color)
        return n.outputs['Color']

    def bump(self, height, strength=1.0, dist=0.1, normal=None, invert=False):
        n = self.nodes.new('ShaderNodeBump')
        n.invert = invert
        self._set(n.inputs['Strength'], strength)
        self._set(n.inputs['Distance'], dist)
        self._set(n.inputs['Height'], height)
        if normal is not None:
            self._set(n.inputs['Normal'], normal)
        return n.outputs['Normal']

    def bevel(self, radius=0.01, samples=4):
        n = self.nodes.new('ShaderNodeBevel')
        n.samples = samples
        self._set(n.inputs['Radius'], radius)
        return n.outputs['Normal']

    def principled(self, base=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, normal=None, spec=None, alpha=None,
                   sss=None, sss_radius=None, sss_scale=None, coat=None, coat_rough=None, emit=None, emit_strength=None,
                   transmission=None, ior=None, sheen=None, sheen_rough=None, spec_tint=None):
        n = self.nodes.new('ShaderNodeBsdfPrincipled')
        self._set(n.inputs['Base Color'], base)
        self._set(n.inputs['Roughness'], rough)
        self._set(n.inputs['Metallic'], metal)
        if normal is not None:
            self._set(n.inputs['Normal'], normal)
        if spec is not None:
            self._set(n.inputs['Specular IOR Level'], spec)
        if spec_tint is not None:
            self._set(n.inputs['Specular Tint'], spec_tint)
        if alpha is not None:
            self._set(n.inputs['Alpha'], alpha)
        if sss is not None:
            self._set(n.inputs['Subsurface Weight'], sss)
        if sss_radius is not None:
            self._set(n.inputs['Subsurface Radius'], sss_radius)
        if sss_scale is not None:
            self._set(n.inputs['Subsurface Scale'], sss_scale)
        if coat is not None:
            self._set(n.inputs['Coat Weight'], coat)
        if coat_rough is not None:
            self._set(n.inputs['Coat Roughness'], coat_rough)
        if emit is not None:
            self._set(n.inputs['Emission Color'], emit)
        if emit_strength is not None:
            self._set(n.inputs['Emission Strength'], emit_strength)
        if transmission is not None:
            self._set(n.inputs['Transmission Weight'], transmission)
        if ior is not None:
            self._set(n.inputs['IOR'], ior)
        if sheen is not None:
            self._set(n.inputs['Sheen Weight'], sheen)
        if sheen_rough is not None:
            self._set(n.inputs['Sheen Roughness'], sheen_rough)
        return n

    def mixsh(self, fac, a, b):
        n = self.nodes.new('ShaderNodeMixShader')
        self._set(n.inputs[0], fac)
        self.links.new(a, n.inputs[1])
        self.links.new(b, n.inputs[2])
        return n.outputs[0]

    def translucent(self, color):
        n = self.nodes.new('ShaderNodeBsdfTranslucent')
        self._set(n.inputs['Color'], color)
        return n.outputs[0]

    def transparent(self):
        n = self.nodes.new('ShaderNodeBsdfTransparent')
        return n.outputs[0]

    def finish(self, bsdf, disp=None):
        sock = bsdf.outputs[0] if hasattr(bsdf, 'outputs') else bsdf
        self.links.new(sock, self.out.inputs['Surface'])
        if disp is not None:
            self.links.new(disp, self.out.inputs['Displacement'])
        # tidy: lay out nodes in a grid so the file is readable if opened
        try:
            for i, nd in enumerate(self.nodes):
                nd.location = ((i % 8) * 260, -(i // 8) * 260)
        except Exception:
            pass
        return self.m

# ------------------------------------------------------------------ async jobs and preview rendering
def _ns():
    return bpy.app.driver_namespace

def run_async(name, fn, *args, **kw):
    """Run fn in a thread so long jobs survive the 60 s tool limit. Poll with job_status(name)."""
    J = {'name': name, 'done': False, 'err': None, 't0': time.time(), 'log': []}
    _ns()['job_' + name] = J

    def work():
        try:
            J['result'] = fn(*args, **kw)
        except Exception:
            J['err'] = traceback.format_exc()
        J['done'] = True
        J['t1'] = time.time()

    th = threading.Thread(target=work, daemon=True)
    th.start()
    return J

def job_status(name):
    J = _ns().get('job_' + name)
    if J is None:
        return {'missing': True}
    out = {'done': J['done'], 'err': J['err'], 'elapsed': round(J.get('t1', time.time()) - J['t0'], 1), 'log': J['log'][-12:]}
    if J['done'] and 'result' in J:
        try:
            import json
            json.dumps(J['result'])
            out['result'] = J['result']
        except Exception:
            out['result'] = str(J['result'])[:500]
    return out

def render_job(name, path, w=600, h=400, samples=24, cam=None, noisethr=0.03, denoise=True, hide_colls=(), fmt='JPEG', quality=92):
    sc = bpy.context.scene
    if cam is not None:
        sc.camera = bpy.data.objects[cam] if isinstance(cam, str) else cam
    r = sc.render
    r.resolution_x = w
    r.resolution_y = h
    r.resolution_percentage = 100
    r.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = noisethr
    sc.cycles.use_denoising = denoise
    r.image_settings.file_format = fmt
    if fmt == 'JPEG':
        r.image_settings.quality = quality
    r.filepath = path
    saved = {}

    def work():
        for cn in hide_colls:
            c = bpy.data.collections.get(cn)
            if c is not None:
                saved[cn] = c.hide_render
                c.hide_render = True
        try:
            bpy.ops.render.render(write_still=True)
        finally:
            for cn, v in saved.items():
                bpy.data.collections[cn].hide_render = v
        return {'path': path}

    return run_async(name, work)


def render_many(name, shots, fmt='JPEG', quality=92, hide_colls=()):
    """shots: list of dicts(cam, path, w, h, samples, [exposure])"""
    sc = bpy.context.scene

    def work():
        saved = {}
        for cn in hide_colls:
            c = bpy.data.collections.get(cn)
            if c is not None:
                saved[cn] = c.hide_render
                c.hide_render = True
        out = []
        try:
            for sh in shots:
                J = _ns()['job_' + name]
                J['log'].append('start ' + sh['path'].split('/')[-1])
                t0 = time.time()
                sc.camera = bpy.data.objects[sh['cam']]
                if 'haze' in sh:
                    import scene_setup
                    scene_setup.set_haze(sh['haze'])
                if 'look' in sh:
                    sc.view_settings.look = sh['look']
                r = sc.render
                r.engine = 'CYCLES'
                r.resolution_x, r.resolution_y, r.resolution_percentage = sh['w'], sh['h'], 100
                sc.cycles.device = 'CPU'
                sc.cycles.samples = sh['samples']
                sc.cycles.use_denoising = sh.get('denoise', True)
                sc.cycles.adaptive_threshold = sh.get('thr', 0.03)
                if 'exposure' in sh:
                    sc.view_settings.exposure = sh['exposure']
                r.image_settings.file_format = fmt
                if fmt == 'JPEG':
                    r.image_settings.quality = quality
                r.filepath = sh['path']
                bpy.ops.render.render(write_still=True)
                J['log'].append('done %s %.0fs' % (sh['path'].split('/')[-1], time.time() - t0))
                out.append(sh['path'])
        finally:
            for cn, v in saved.items():
                bpy.data.collections[cn].hide_render = v
        return out

    return run_async(name, work)
