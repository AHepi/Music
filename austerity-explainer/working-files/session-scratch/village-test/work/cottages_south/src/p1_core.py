"""What this does: the COTTAGES_SOUTH part of the forest village (owner cottages_south): cottage C (south side of the high road, centre -26, -10.5: 7.4 x 4.6 m, black-brown timber frame
with RED-OCHRE daub panels, pale new straw thatch at 50 degrees, a tall door in the north wall) and cottage D (centre 4, -8: the smallest, 3.7 x 4.4 m, pale clay cob walls with rounded corners and
no frame showing, silver-grey shingle roof at 42 degrees, one low plank door in the north gable end), both seated on the frozen ground (the level pads the ground part built).
Everything is built from the ground up and every part is carried: a stone footing (or plinth), a sill on it, posts and studs on the sill, rails tenoned into the studs, daub panels in the frames,
a wall plate on the post tops, rafters resting on the plate (a wedge seat cut to the roof slope) and on a purlin, the purlin tenoned into the principal rafters (C) or into the cob gables (D),
a ridge piece laid in the rafter tops, a thick rolled thatch slab (C) or a courses-and-slipped-shingles slab (D) resting on the rafters, an earth floor, a door leaf on iron hinges, a flat stone doorstep,
small shuttered windows with no glass (one shutter ajar). Character is SHAPE: posts out of plumb and no two alike, ridges sagging 2 to 4 cm between the trusses, lumpy thatch with a rolled eave,
daub chipped away to show the wattle, a darker splash band at the foot, replaced boards in a fresher colour, slipped and missing shingles, uneven footing stones.
Colour is written into each mesh as a colour layer (Col) and read by a material of our own that carries a small picture (so the surface pass keeps our colours and adds its normal maps,
roughness and wear on top). The cottages build NO props (no barrel, bucket, bench, ladder, sack, jug, woodpile): the props part makes them.
It is IDEMPOTENT: apply(options) first forgets what an earlier run of this owner made (pk.forget_part), then builds again with the same seed. It changes nothing that is not ours.
A concrete example: apply({'seed': 31}) twice gives the same objects. Options (all optional): seed (31), thatch_lump (scale of the lumps in the thatch, 1.3), thatch_roll (eave roll scale, 1.5),
sag (ridge sag scale, 1.0 = 3 to 4 cm), chip (size of the daub chips, 1.5), cob_lump (lumpiness of the cob, 1.2), daub_hex (the red-ochre of C, default #9C4F36), daub_tone (-1 deeper brown-red to +1 lighter terracotta, 0.15), daub_value (brightness, 1.08), thatch_hex (default #B8985A), thatch_tone (-1 greyer to +1 paler, 0.6), cob_hex (default #B9A683), cob_tone (-1 darker to +1 paler clay, 0.4),
shingle_hex (default #A9A8A2), shingle_mix (how different the shingles are, 1.2), lean (scale of the lean of the posts, 1.0).
Frames and units: metres; x east, y north, z up. Heights in the code are measured from the pad (g) unless a name says absolute.
"""
import math
import os
import sys

import numpy as np

import bpy

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
for _path in (os.path.join(KIT, 'place-kit') if KIT else '', '/home/user/Music/plugins/explainer-film/kit/place-kit'):
    if _path and os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
import place_kit as pk  # noqa: E402

OWNER = 'cottages_south'


# ------------------------------------------------------------------ colour
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexl(h):
    h = h.lstrip('#')
    return np.array([_lin(int(h[0:2], 16) / 255.0), _lin(int(h[2:4], 16) / 255.0), _lin(int(h[4:6], 16) / 255.0), 1.0])


def mixc(a, b, t):
    t = np.asarray(t, float)
    if t.ndim:
        t = t[..., None]
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def tone3(base, dark, light, t):
    """A colour moved from `base` toward `dark` (t below 0) or toward `light` (t above 0), t from -1 to 1."""
    t = float(t)
    return mixc(base, dark, -t) if t < 0 else mixc(base, light, t)


def shade(c, f):
    f = np.asarray(f, float)
    if f.ndim:
        f = f[..., None]
    out = np.asarray(c, float) * f
    out[..., 3] = 1.0
    return out


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Noise:
    """Smooth repeatable noise: a few sine waves with random directions, scales and phases. value(x, y, z) is about -1..1."""

    def __init__(self, seed, scales=(1.9, 0.9, 0.45), count=3):
        rng = np.random.default_rng(seed)
        self.waves = []
        for k, s in enumerate(scales):
            for _ in range(count):
                v = rng.normal(size=3)
                v /= np.linalg.norm(v)
                self.waves.append((v * 2 * math.pi / s, rng.random() * 2 * math.pi, 1.0 / (1 + 0.6 * k)))
        self.norm = sum(w[2] for w in self.waves)

    def value(self, x, y, z=0.0):
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
        total = np.zeros(x.shape)
        for k, ph, amp in self.waves:
            total = total + amp * np.sin(k[0] * x + k[1] * y + k[2] * z + ph)
        return total / self.norm * 1.7


# ------------------------------------------------------------------ the mesh accumulator
def signed_volume(V, F):
    vol = 0.0
    for f in F:
        a = V[f[0]]
        for k in range(1, len(f) - 1):
            vol += float(np.dot(a, np.cross(V[f[k]], V[f[k + 1]])))
    return vol / 6.0


class Acc:
    """Collects closed solids (each with its own vertices, so each is one loose piece) and their colours (one colour, or a function of the points), then makes one mesh object."""

    def __init__(self, smooth=False):
        self.items = []
        self.smooth = smooth
        self.tris = 0

    def add(self, V, F, col=(0.5, 0.5, 0.5, 1.0), closed=True, smooth=None):
        V = np.asarray(V, float)
        F = [tuple(int(i) for i in f) for f in F]
        if closed and F and signed_volume(V, F) < 0:
            F = [tuple(reversed(f)) for f in F]
        self.items.append((V, F, col, self.smooth if smooth is None else smooth))
        self.tris += sum(len(f) - 2 for f in F)

    def empty(self):
        return not self.items

    def make(self, name):
        Vs, Fs, cols, flags, off = [], [], [], [], 0
        for V, F, col, smooth in self.items:
            Vs.append(V)
            if callable(col):
                vc = np.asarray(col(V), float)
            elif isinstance(col, np.ndarray) and col.ndim == 2:
                vc = col
            else:
                vc = np.tile(np.asarray(col, float), (len(V), 1))
            per_face = isinstance(smooth, (list, tuple, np.ndarray))
            for fi, f in enumerate(F):
                Fs.append(tuple(i + off for i in f))
                cols.append(vc[list(f)])
                flags.append(bool(smooth[fi]) if per_face else bool(smooth))
            off += len(V)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(v) for v in np.vstack(Vs)], [], Fs)
        mesh.update()
        attr = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        attr.data.foreach_set('color', np.concatenate(cols).ravel() if cols else np.zeros(0))
        mesh.polygons.foreach_set('use_smooth', flags)
        mesh.update()
        return mesh


# ------------------------------------------------------------------ primitives (each returns vertices and faces of ONE closed solid)
def box(x0, x1, y0, y1, z0, z1):
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array(V, float), F


def loft(rings):
    """A closed solid from rings of equal length (each ring a closed loop of 3D points, in the same turning direction). The first and last ring are capped."""
    rings = [np.asarray(r, float) for r in rings]
    M = len(rings[0])
    V = np.vstack(rings)
    F = []
    for k in range(len(rings) - 1):
        a, b = k * M, (k + 1) * M
        for i in range(M):
            j = (i + 1) % M
            F.append((a + i, a + j, b + j, b + i))
    F.append(tuple(range(M - 1, -1, -1)))
    last = (len(rings) - 1) * M
    F.append(tuple(range(last, last + M)))
    return V, F


def rot_z(P, angle, pivot):
    P = np.array(P, float)
    c, s = math.cos(angle), math.sin(angle)
    x, y = P[..., 0] - pivot[0], P[..., 1] - pivot[1]
    P[..., 0] = pivot[0] + c * x - s * y
    P[..., 1] = pivot[1] + s * x + c * y
    return P


def grid_slab(T, Bb):
    """A closed slab from a top grid T[i][j] (points; i along the length, j across) and a flat-ish bottom Bb[i][0..1] (points under the first and the last row, one pair for each i).
    Returns (V, F, number of top faces). The faces are written for the handedness i x j = up; Acc.add turns them round when the volume comes out negative."""
    T = np.asarray(T, float)
    Bb = np.asarray(Bb, float)
    nx, ny = T.shape[0] - 1, T.shape[1] - 1
    V = list(T.reshape(-1, 3))
    idx = lambda i, j: i * (ny + 1) + j  # noqa: E731
    F = []
    for i in range(nx):
        for j in range(ny):
            F.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)))
    top_faces = len(F)
    b = len(V)
    V += list(Bb.reshape(-1, 3))
    bi = lambda i, k: b + i * 2 + k  # noqa: E731
    for i in range(nx):
        F.append((idx(i + 1, 0), idx(i, 0), bi(i, 0), bi(i + 1, 0)))
        F.append((idx(i, ny), idx(i + 1, ny), bi(i + 1, 1), bi(i, 1)))
        F.append((bi(i + 1, 0), bi(i, 0), bi(i, 1), bi(i + 1, 1)))
    F.append(tuple([idx(nx, j) for j in range(ny, -1, -1)] + [bi(nx, 0), bi(nx, 1)]))
    F.append(tuple([idx(0, j) for j in range(0, ny + 1)] + [bi(0, 1), bi(0, 0)]))
    return np.array(V, float), F, top_faces


def slab_between(Fg, Bg):
    """A closed slab from a front grid Fg[i][j] and a back grid Bg[i][j] of the same shape (points). Returns (V, F)."""
    Fg, Bg = np.asarray(Fg, float), np.asarray(Bg, float)
    nx, ny = Fg.shape[0] - 1, Fg.shape[1] - 1
    V = list(Fg.reshape(-1, 3)) + list(Bg.reshape(-1, 3))
    f = lambda i, j: i * (ny + 1) + j  # noqa: E731
    k = (nx + 1) * (ny + 1)
    b = lambda i, j: k + i * (ny + 1) + j  # noqa: E731
    F = []
    for i in range(nx):
        for j in range(ny):
            F.append((f(i, j), f(i + 1, j), f(i + 1, j + 1), f(i, j + 1)))
            F.append((b(i, j), b(i, j + 1), b(i + 1, j + 1), b(i + 1, j)))
    for i in range(nx):
        F.append((f(i + 1, 0), f(i, 0), b(i, 0), b(i + 1, 0)))
        F.append((f(i, ny), f(i + 1, ny), b(i + 1, ny), b(i, ny)))
    for j in range(ny):
        F.append((f(0, j), f(0, j + 1), b(0, j + 1), b(0, j)))
        F.append((f(nx, j + 1), f(nx, j), b(nx, j), b(nx, j + 1)))
    return np.array(V, float), F


def rect_ring(c, ex, ey, hx, hy, twist=0.0):
    """Four corners of a rectangle with centre c (3D), axes ex and ey (unit vectors), half sizes hx and hy, turned by `twist` radians about their cross product. Turns counter-clockwise seen from ex x ey."""
    ex, ey = np.asarray(ex, float), np.asarray(ey, float)
    if twist:
        ct, st = math.cos(twist), math.sin(twist)
        ex, ey = ex * ct + ey * st, -ex * st + ey * ct
    c = np.asarray(c, float)
    return np.array([c + ex * hx - ey * hy, c + ex * hx + ey * hy, c - ex * hx + ey * hy, c - ex * hx - ey * hy])


class Wall:
    """A wall's own frame: u runs along the wall, w across it (outward), z up. P(u, w, z) is the world point."""

    def __init__(self, origin, eu, ew, length):
        self.o = np.array([origin[0], origin[1], 0.0], float)
        self.eu = np.array([eu[0], eu[1], 0.0], float)
        self.ew = np.array([ew[0], ew[1], 0.0], float)
        self.length = length

    def P(self, u, w, z):
        u, w, z = np.broadcast_arrays(np.asarray(u, float), np.asarray(w, float), np.asarray(z, float))
        return self.o + u[..., None] * self.eu + w[..., None] * self.ew + np.stack([np.zeros_like(z), np.zeros_like(z), z], axis=-1)

    def to_uw(self, x, y):
        d = np.array([x, y]) - self.o[:2]
        return float(d @ self.eu[:2]), float(d @ self.ew[:2])
