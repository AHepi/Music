"""What this does: the COTTAGES_NORTH part of the forest village (owner cottages_north): cottage A (long, dark oak frame, cream limewash panels, golden thatch, a log-store lean-to on its west end)
and cottage B (small, heavy, grey rubble stone, old mossy thatch, the only stone chimney), both on the north side of the high road, both seated on the frozen ground (the level pads the ground part built).
Everything is built from the ground up and every part is carried: stone footing, sill, posts, studs, wall plate, wall panels (or stone walls), rafters resting on the plates and let into a purlin,
a ridge piece laid on the rafter tops, a thick rolled thatch slab resting on the rafters, an earth floor, a door on iron hinges, a flat stone doorstep, small shuttered windows (no glass).
Character is SHAPE: posts out of plumb and no two alike, a sagging ridge, lumpy thatch with a rolled eave, plaster chipped to the wattle, a darker splash band at the foot, replaced boards in a fresher
colour, stones of uneven size standing out of the wall. Colour is written into each mesh as a colour layer (Col) and read by a material of our own that carries a small picture, so the surface pass keeps
our colours and adds its normal maps, roughness and wear on top.
It is IDEMPOTENT: apply(options) first forgets what an earlier run of this owner made (pk.forget_part), then builds again with the same seed. It changes nothing that is not ours.
A concrete example: apply({'seed': 17}) twice gives the same objects. Options: seed (default 17), sag_cm (ridge sag scale, default 1.0), thatch_roll (eave roll scale, default 1.0), chip_amount (scale of the
plaster chips, default 1.0).
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

OWNER = 'cottages_north'
THETA = math.radians(50.0)
TAN, COS, SIN = math.tan(THETA), math.cos(THETA), math.sin(THETA)


# ------------------------------------------------------------------ colour
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexl(h):
    h = h.lstrip('#')
    return (_lin(int(h[0:2], 16) / 255.0), _lin(int(h[2:4], 16) / 255.0), _lin(int(h[4:6], 16) / 255.0), 1.0)


def mixc(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def shade(c, f):
    return (min(c[0] * f, 1.0), min(c[1] * f, 1.0), min(c[2] * f, 1.0), 1.0)


def vary(c, rng, amount):
    f = 1.0 + amount * (rng.random() * 2 - 1)
    g = 1.0 + amount * 0.4 * (rng.random() * 2 - 1)
    return (min(c[0] * f * g, 1.0), min(c[1] * f, 1.0), min(c[2] * f / g, 1.0), 1.0)


# ------------------------------------------------------------------ smooth noise (plain numpy, repeatable)
class Noise:
    """A few sine waves with random directions and phases: smooth, repeatable, cheap. value(x, y) is about -1..1."""

    def __init__(self, seed, scales=(2.0, 0.9, 0.45), count=3):
        rng = np.random.default_rng(seed)
        self.waves = []
        for s in scales:
            for _ in range(count):
                a = rng.random() * 2 * math.pi
                self.waves.append((math.cos(a) * 2 * math.pi / s, math.sin(a) * 2 * math.pi / s, rng.random() * 2 * math.pi, 1.0 / (1 + 0.5 * scales.index(s))))
        self.norm = sum(w[3] for w in self.waves)

    def value(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        total = 0.0
        for kx, ky, ph, amp in self.waves:
            total = total + amp * np.sin(kx * x + ky * y + ph)
        return total / self.norm * 1.6


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ the mesh accumulator
def _signed_volume(V, F):
    vol = 0.0
    for f in F:
        a = V[f[0]]
        for k in range(1, len(f) - 1):
            vol += np.dot(a, np.cross(V[f[k]], V[f[k + 1]]))
    return vol / 6.0


class Acc:
    """Collects closed solids (each with its own vertices, so each is one loose piece) and their face colours, then makes one mesh object."""

    def __init__(self):
        self.V, self.F, self.C, self.n = [], [], [], 0

    def add(self, V, F, col=(0.5, 0.5, 0.5, 1.0), closed=True):
        V = np.asarray(V, float)
        F = [tuple(int(i) for i in f) for f in F]
        if closed and F and _signed_volume(V, F) < 0:
            F = [tuple(reversed(f)) for f in F]
        cols = col if isinstance(col, list) else [col] * len(F)
        self.V.append(V)
        for f, c in zip(F, cols):
            self.F.append(tuple(i + self.n for i in f))
            self.C.append(c)
        self.n += len(V)

    def empty(self):
        return self.n == 0

    def make(self, name, smooth=False):
        mesh = bpy.data.meshes.new(name)
        V = np.vstack(self.V)
        mesh.from_pydata([tuple(v) for v in V], [], self.F)
        mesh.update()
        attr = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        starts = np.empty(len(mesh.polygons), dtype=np.int64)
        totals = np.empty(len(mesh.polygons), dtype=np.int64)
        mesh.polygons.foreach_get('loop_start', starts)
        mesh.polygons.foreach_get('loop_total', totals)
        face_of_loop = np.repeat(np.arange(len(mesh.polygons)), totals)
        colours = np.asarray(self.C, float)[face_of_loop]
        attr.data.foreach_set('color', colours.ravel())
        if smooth:
            try:
                mesh.shade_smooth()
            except Exception:  # noqa: BLE001 - flat shading is an acceptable fallback
                pass
        return mesh


# ------------------------------------------------------------------ primitives (each returns vertices and faces of ONE closed solid)
def rot_z(V, angle, pivot):
    V = np.array(V, float)
    c, s = math.cos(angle), math.sin(angle)
    x, y = V[:, 0] - pivot[0], V[:, 1] - pivot[1]
    V[:, 0] = pivot[0] + c * x - s * y
    V[:, 1] = pivot[1] + s * x + c * y
    return V


def box(x0, x1, y0, y1, z0, z1):
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array(V, float), F


def lofted_post(cx, cy, z0, z1, sx, sy, lean=(0.0, 0.0), twist=0.0, taper=1.0, top_z_fn=None):
    """A square post or stud: the bottom is a horizontal rectangle at z0, the top a horizontal rectangle at z1 moved by `lean` (metres) and scaled by `taper`: out of plumb, with level ends so it
    sits flat on a sill and carries a plate flat. top_z_fn(x, y) may cut the top on a slope instead."""
    def ring(cxx, cyy, z, kx, ky):
        pts = [(-kx, -ky), (kx, -ky), (kx, ky), (-kx, ky)]
        c, s = math.cos(twist), math.sin(twist)
        return [(cxx + c * px - s * py, cyy + s * px + c * py, z) for px, py in pts]
    bottom = ring(cx, cy, z0, sx / 2, sy / 2)
    top = ring(cx + lean[0], cy + lean[1], z1, sx / 2 * taper, sy / 2 * taper)
    if top_z_fn is not None:
        top = [(x, y, float(top_z_fn(x, y))) for x, y, _ in top]
    V = bottom + top
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array(V, float), F


def extrude_x(poly_yz, x0, x1):
    """A prism: a polygon in (y, z) pushed along x from x0 to x1 (any simple polygon; the winding is put right by Acc.add)."""
    P = np.asarray(poly_yz, float)
    n = len(P)
    V = np.vstack([np.column_stack([np.full(n, x0), P[:, 0], P[:, 1]]), np.column_stack([np.full(n, x1), P[:, 0], P[:, 1]])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def extrude_y(poly_xz, y0, y1):
    """A prism: a polygon in (x, z) pushed along y from y0 to y1."""
    P = np.asarray(poly_xz, float)
    n = len(P)
    V = np.vstack([np.column_stack([P[:, 0], np.full(n, y0), P[:, 1]]), np.column_stack([P[:, 0], np.full(n, y1), P[:, 1]])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def extrude_z(poly_xy, z0, z1):
    """A prism: a polygon in (x, y) pushed up from z0 to z1."""
    P = np.asarray(poly_xy, float)
    n = len(P)
    V = np.vstack([np.column_stack([P[:, 0], P[:, 1], np.full(n, z0)]), np.column_stack([P[:, 0], P[:, 1], np.full(n, z1)])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def loft_rings(rings, cap_colour=None):
    """A closed solid from rings (M, N, 3): quads between neighbouring rings, an n-gon at each end. Returns vertices, faces (quad faces are row-major: face index = m * N + k for the quad between ring m and
    m + 1 at ring point k), so a caller can colour them."""
    R = np.asarray(rings, float)
    M, N, _ = R.shape
    V = R.reshape(-1, 3)
    F = []
    for m in range(M - 1):
        for k in range(N):
            k2 = (k + 1) % N
            F.append((m * N + k, m * N + k2, (m + 1) * N + k2, (m + 1) * N + k))
    F.append(tuple(range(N - 1, -1, -1)))
    F.append(tuple((M - 1) * N + k for k in range(N)))
    return V, F


def bowed_bar_x(x0, x1, yc, w, z0, z1, bow, segments=8, ybow_phase=0.0):
    """A bar along x with flat top and bottom whose plan line bows sideways by up to `bow` metres (so it is not ruler straight)."""
    xs = np.linspace(x0, x1, segments + 1)
    rings = []
    for x in xs:
        t = (x - x0) / max(x1 - x0, 1e-6)
        off = bow * math.sin(math.pi * t + ybow_phase)
        rings.append([(x, yc + off - w / 2, z0), (x, yc + off + w / 2, z0), (x, yc + off + w / 2, z1), (x, yc + off - w / 2, z1)])
    return loft_rings(rings)


def stone_blob(cx, cy, z0, z1, sx, sy, rng, wobble=0.12):
    """A rough stone: a box with its upper corners pulled in a little differently, flat bottom and flat top (so a stone above it can rest)."""
    pts = []
    for z, kt in ((z0, 1.0), (z1, 1.0)):
        for ox, oy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            j = 1 - wobble * rng.random()
            pts.append((cx + ox * sx / 2 * j, cy + oy * sy / 2 * j, z))
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array(pts, float), F


# ------------------------------------------------------------------ the relief slab: a wall, panel, door or shutter whose faces are height fields
def subdivide_lines(must, step):
    """Grid lines that include every coordinate in `must` and are about `step` apart in between."""
    must = sorted(set(round(float(m), 6) for m in must))
    out = [must[0]]
    for a, b in zip(must[:-1], must[1:]):
        n = max(1, int(round((b - a) / step)))
        out.extend(a + (b - a) * np.arange(1, n + 1) / n)
    return np.array(out, float)


def relief_slab(origin, e_u, e_n, us, vs, thick, front_fn, back_fn=None, holes=(), colour_fn=None, back_colour=None, edge_colour=None, top_fn=None, e_v=None):
    """A closed slab whose front face (outward along e_n) and back face are height fields over a grid.
    origin: where u=0, v=0, w=0 is; e_u: unit vector along the width; e_n: unit outward normal; the up direction is z (e_v = e_n x e_u... chosen so that e_u x e_v = e_n).
    us, vs: grid lines along the width and along z (v measured from origin z). thick: body thickness (w from 0 to thick) before relief.
    front_fn(U, V) -> relief (metres, added to thick on the front face); back_fn(U, V) -> relief (subtracted from 0: the back face moves toward -e_n by it) or None.
    holes: rectangles (u0, u1, v0, v1) with edges on grid lines: no material there (a doorway, a window opening), with reveal faces on the sides.
    colour_fn(Uc, Vc, Rc) -> (n, 4) colours of the front cells; edge_colour for the reveal and edge faces.
    top_fn(u) -> top v for each column (a sloped top, as in a gable): the rows then are fractions of the column height (no holes allowed).
    Returns vertices, faces, colours."""
    e_u = np.asarray(e_u, float)
    e_n = np.asarray(e_n, float)
    if e_v is None:
        e_v = np.cross(e_n, e_u)
        assert e_v[2] > 0.99, 'e_u and e_n must make e_v point up (e_n x e_u = up) unless e_v is given'
    else:
        e_v = np.asarray(e_v, float)
    nu, nv = len(us) - 1, len(vs) - 1
    U, Vv = np.meshgrid(us, vs)                       # (nv+1, nu+1)
    if top_fn is not None:
        tops = np.array([top_fn(u) for u in us])
        frac = (vs - vs[0]) / (vs[-1] - vs[0])
        Vv = vs[0] + np.outer(frac, tops - vs[0])
    fr = front_fn(U, Vv)
    br = back_fn(U, Vv) if back_fn is not None else np.zeros_like(U)
    o = np.asarray(origin, float)
    Pf = o + U[..., None] * e_u + Vv[..., None] * e_v + (thick + fr)[..., None] * e_n
    Pb = o + U[..., None] * e_u + Vv[..., None] * e_v + (-br)[..., None] * e_n
    n_grid = (nu + 1) * (nv + 1)
    V = np.vstack([Pf.reshape(-1, 3), Pb.reshape(-1, 3)])

    def fi(i, j):
        return j * (nu + 1) + i

    def bi(i, j):
        return n_grid + j * (nu + 1) + i
    keep = np.ones((nu, nv), bool)
    for (u0, u1, v0, v1) in holes:
        for i in range(nu):
            if us[i] >= u0 - 1e-6 and us[i + 1] <= u1 + 1e-6:
                for j in range(nv):
                    if vs[j] >= v0 - 1e-6 and vs[j + 1] <= v1 + 1e-6:
                        keep[i, j] = False
    F, C = [], []
    Uc = (U[:-1, :-1] + U[1:, 1:]) / 2
    Vc = (Vv[:-1, :-1] + Vv[1:, 1:]) / 2
    Rc = (fr[:-1, :-1] + fr[1:, 1:]) / 2
    cell_cols = colour_fn(Uc, Vc, Rc) if colour_fn is not None else None
    for j in range(nv):
        for i in range(nu):
            if not keep[i, j]:
                continue
            F.append((fi(i, j), fi(i + 1, j), fi(i + 1, j + 1), fi(i, j + 1)))
            C.append(tuple(cell_cols[j, i]) if cell_cols is not None else (0.5, 0.5, 0.5, 1.0))
            F.append((bi(i, j), bi(i, j + 1), bi(i + 1, j + 1), bi(i + 1, j)))
            C.append(back_colour or (0.4, 0.4, 0.4, 1.0))
    ec = edge_colour or (0.35, 0.33, 0.30, 1.0)

    def kept(i, j):
        return 0 <= i < nu and 0 <= j < nv and keep[i, j]
    for j in range(nv):
        for i in range(nu):
            if not keep[i, j]:
                continue
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if kept(i + di, j + dj):
                    continue
                if di == -1:
                    a, b = (i, j), (i, j + 1)
                elif di == 1:
                    a, b = (i + 1, j + 1), (i + 1, j)
                elif dj == -1:
                    a, b = (i + 1, j), (i, j)
                else:
                    a, b = (i, j + 1), (i + 1, j + 1)
                F.append((fi(*a), fi(*b), bi(*b), bi(*a)))
                C.append(ec)
    return V, F, C


# ------------------------------------------------------------------ materials (our own, with a small picture so the surface pass keeps them)
def tile_image():
    name = 'Cottages north tile'
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, 64, 64, alpha=False)
        img.colorspace_settings.name = 'Non-Color'                 # first, before the pixels (blender-5-traps.md, trap 1)
        rng = np.random.default_rng(5)
        a = rng.random((8, 8))
        big = np.kron(a, np.ones((8, 8)))
        small = rng.random((64, 64))
        v = 0.90 + 0.07 * big + 0.03 * small
        pix = np.stack([v, v, v, np.ones_like(v)], axis=-1)
        img.pixels.foreach_set(pix.ravel().astype(np.float32))
        img.pack()
        img.use_fake_user = True
    return img


def make_material(name, roughness=0.85):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = roughness
    colour = nt.nodes.new('ShaderNodeVertexColor')
    colour.layer_name = 'Col'
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (1.3, 1.3, 1.3)
    image = nt.nodes.new('ShaderNodeTexImage')
    image.image = tile_image()
    image.interpolation = 'Cubic'
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    nt.links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], image.inputs['Vector'])
    nt.links.new(colour.outputs['Color'], mix.inputs[6])
    nt.links.new(image.outputs['Color'], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    mat['place_owner'] = OWNER
    return mat


# ------------------------------------------------------------------ height fields and colours for the relief slabs
class StoneField:
    """Rubble: courses of uneven height, blocks of uneven width, each block standing out of the wall by its own small amount, soft valleys between them (a few centimetres across, not a ruler line),
    a lighter mortar tone in the valleys, moss low in the damp corners. u runs along the wall (0..W), v up from the wall's foot."""

    def __init__(self, seed, W, H, palette, moss, big=1.0, amp=0.032, mortar=None, moss_amount=1.0, noise_seed=0):
        rng = np.random.default_rng(seed)
        self.palette, self.moss, self.amp, self.moss_amount = palette, moss, amp, moss_amount
        self.mortar = mortar or (0.50, 0.49, 0.45, 1.0)
        self.rows = [-rng.random() * 0.18]
        while self.rows[-1] < H + 0.05:
            self.rows.append(self.rows[-1] + (0.20 + 0.18 * rng.random()) * big)
        self.rows = np.array(self.rows)
        keys, starts, ends, base, tone = [], [], [], [], []
        for r in range(len(self.rows) - 1):
            u = -0.05 - rng.random() * 0.45
            while u < W + 0.05:
                w = (0.30 + 0.45 * rng.random()) * big
                keys.append(r * 1000.0 + (u + 5.0))
                starts.append(u)
                ends.append(u + w)
                base.append(rng.random() * amp)
                tone.append(rng.integers(0, len(palette)))
                u += w
        self.keys, self.starts, self.ends = np.array(keys), np.array(starts), np.array(ends)
        self.base, self.tone = np.array(base), np.array(tone)
        self.shade = 0.88 + 0.24 * rng.random(len(keys))
        self.noise = Noise(seed + 101 + noise_seed, (1.6, 0.7, 0.3))

    def _lookup(self, U, V):
        r = np.clip(np.searchsorted(self.rows, V, 'right') - 1, 0, len(self.rows) - 2)
        idx = np.clip(np.searchsorted(self.keys, r * 1000.0 + (U + 5.0), 'right') - 1, 0, len(self.keys) - 1)
        d = np.minimum.reduce([U - self.starts[idx], self.ends[idx] - U, V - self.rows[r], self.rows[r + 1] - V])
        return idx, d

    def relief(self, U, V):
        idx, d = self._lookup(U, V)
        d = np.maximum(d, 0.0)
        shape = smoothstep(0.0, 0.07, d)
        return -0.022 + (self.base[idx] + 0.022) * smoothstep(0.0, 0.035, d) + 0.016 * shape * self.noise.value(U * 1.3, V * 1.3)

    def colour(self, U, V, R):
        idx, d = self._lookup(U, V)
        out = np.empty(U.shape + (4,))
        pal = np.array(self.palette)
        base = pal[self.tone[idx]] * self.shade[idx][..., None]
        mort = np.array(self.mortar)
        t = smoothstep(0.05, 0.0, d)[..., None]
        col = base * (1 - 0.7 * t) + mort * 0.7 * t
        low = smoothstep(0.75, 0.0, V) * np.clip(0.5 + 0.9 * self.noise.value(U * 2.2 + 3, V * 1.1), 0, 1) * self.moss_amount
        low = np.clip(low, 0, 0.85)[..., None]
        col = col * (1 - low) + np.array(self.moss) * low
        col[..., 3] = 1.0
        return np.clip(col, 0, 1)


def blob_mask(U, V, cx, cy, rx, ry, rng_phase, rough=0.22):
    """A soft irregular blob (a plaster chip): 1 inside, 0 outside, with a ragged edge."""
    dx, dy = (U - cx) / rx, (V - cy) / ry
    ang = np.arctan2(dy, dx)
    edge = 1.0 + rough * np.sin(3 * ang + rng_phase[0]) + 0.5 * rough * np.sin(5 * ang + rng_phase[1])
    r = np.sqrt(dx * dx + dy * dy) / edge
    return smoothstep(1.0, 0.82, r)


class PlasterField:
    """A limewash panel: soft lumps, a few big chips down to the wattle (horizontal hazel rods woven over upright stakes), a darker splash band at the foot with a ragged top."""

    def __init__(self, seed, W, H, base, splash, wattle_hi, wattle_lo, rim, chips=0, chip_scale=1.0, band=0.24):
        rng = np.random.default_rng(seed)
        self.W, self.H, self.base, self.splash = W, H, base, splash
        self.hi, self.lo, self.rim = wattle_hi, wattle_lo, rim
        self.noise = Noise(seed + 7, (1.1, 0.5, 0.25))
        self.band = band * (0.8 + 0.4 * rng.random())
        self.chips = []
        for k in range(chips):
            rx = min(W * (0.28 + 0.12 * rng.random()), 0.34) * chip_scale
            ry = (0.22 + 0.20 * rng.random()) * chip_scale
            cx = rx + 0.04 + (W - 2 * rx - 0.08) * rng.random() if W - 2 * rx - 0.08 > 0 else W / 2
            cy = ry + 0.05 + (H - 2 * ry - 0.1) * (0.15 + 0.8 * rng.random())
            self.chips.append((cx, cy, rx, ry, (rng.random() * 6, rng.random() * 6)))
        self.tone = 0.94 + 0.1 * rng.random()
        self.rod_phase = rng.random() * 6

    def mask(self, U, V):
        m = np.zeros_like(U, dtype=float)
        for cx, cy, rx, ry, ph in self.chips:
            m = np.maximum(m, blob_mask(U, V, cx, cy, rx, ry, ph))
        return m

    def relief(self, U, V):
        m = self.mask(U, V)
        lumps = 0.005 * self.noise.value(U * 3.1, V * 3.1) + 0.003 * np.sin(U * 17 + V * 5)
        rods = 0.011 * (0.5 + 0.5 * np.cos(2 * np.pi * V / 0.062 + self.rod_phase))
        stakes = 0.014 * smoothstep(0.55, 0.9, np.cos(2 * np.pi * U / 0.21))
        return lumps * (1 - m) + m * (-0.040 + rods + stakes)

    def colour(self, U, V, R):
        m = self.mask(U, V)
        base = np.array(self.base) * self.tone
        n = 0.5 + 0.5 * self.noise.value(U * 2.0, V * 2.0)
        col = base * (0.93 + 0.12 * n[..., None])
        top = self.band * (1.0 + 0.5 * np.sin(U * 11 + 1.3) + 0.4 * np.sin(U * 27 + 0.4))
        s = smoothstep(top + 0.03, top - 0.03, V)[..., None]
        col = col * (1 - s) + np.array(self.splash) * s
        rim = (smoothstep(0.02, 0.45, m) * smoothstep(0.9, 0.55, m))[..., None]
        col = col * (1 - 0.8 * rim) + np.array(self.rim) * 0.8 * rim
        rods = 0.5 + 0.5 * np.cos(2 * np.pi * V / 0.062 + self.rod_phase)
        stakes = smoothstep(0.55, 0.9, np.cos(2 * np.pi * U / 0.21))
        wat = np.array(self.lo) * (1 - rods[..., None]) + np.array(self.hi) * rods[..., None]
        wat = wat * (1 - 0.5 * stakes[..., None]) + np.array(self.lo) * 0.5 * stakes[..., None] * 1.2
        w = smoothstep(0.5, 0.75, m)[..., None]
        col = col * (1 - w) + wat * w
        col[..., 3] = 1.0
        return np.clip(col, 0, 1)


class BoardField:
    """Vertical boards of unequal width with a groove between them, a slight cup across each, an optional set of horizontal battens on the back; one board can be a fresher replacement."""

    def __init__(self, seed, W, H, widths, colour, fresh, fresh_index=None, grain=0.1, batten_rows=(), silver=None):
        rng = np.random.default_rng(seed)
        s = sum(widths)
        self.edges = np.concatenate([[0.0], np.cumsum(np.array(widths) * W / s)])
        self.W, self.H = W, H
        self.col = [vary(colour, rng, 0.14) for _ in widths]
        if fresh_index is not None:
            self.col[fresh_index] = vary(fresh, rng, 0.05)
        self.cup = (rng.random(len(widths)) - 0.5) * 0.008
        self.batten_rows = batten_rows
        self.grain = grain
        self.silver = silver
        self.noise = Noise(seed + 3, (0.9, 0.35, 0.15))

    def _board(self, U):
        return np.clip(np.searchsorted(self.edges, U, 'right') - 1, 0, len(self.edges) - 2)

    def relief(self, U, V):
        b = self._board(U)
        du = np.minimum(U - self.edges[b], self.edges[b + 1] - U)
        c = (self.edges[b] + self.edges[b + 1]) / 2
        hw = (self.edges[b + 1] - self.edges[b]) / 2
        cup = self.cup[b] * (1 - ((U - c) / hw) ** 2)
        return cup - 0.011 * smoothstep(0.012, 0.0, du) + 0.002 * self.noise.value(U * 5, V * 5)

    def back(self, U, V):
        r = np.zeros_like(U)
        for (v0, v1) in self.batten_rows:
            r = np.maximum(r, 0.022 * smoothstep(v0 - 0.01, v0 + 0.01, V) * smoothstep(v1 + 0.01, v1 - 0.01, V))
        return r

    def colour(self, U, V, R):
        b = self._board(U)
        col = np.array(self.col)[b]
        n = 0.5 + 0.5 * self.noise.value(U * 3, V * 3)
        col = col * (0.88 + 0.2 * n[..., None])
        du = np.minimum(U - self.edges[b], self.edges[b + 1] - U)
        g = smoothstep(0.014, 0.0, du)[..., None]
        col = col * (1 - 0.5 * g)
        if self.silver is not None:
            low = smoothstep(0.0, 0.5, V)[..., None] * 0.0
            col = col * (1 - low)
        col[..., 3] = 1.0
        return np.clip(col, 0, 1)


class ShingleField:
    """Wooden shingles in courses: each course stands a little out at its lower edge, each shingle has its own tone, a few are slipped or missing (a dark gap showing the boards)."""

    def __init__(self, seed, W, L, tones, dark, moss, course=0.15, miss=0.03):
        rng = np.random.default_rng(seed)
        self.course = course
        self.nc = int(math.ceil(L / course)) + 2
        self.edges = []
        for c in range(self.nc):
            u = -rng.random() * 0.14
            row = [u]
            while u < W + 0.14:
                u += 0.10 + 0.07 * rng.random()
                row.append(u)
            self.edges.append(np.array(row))
        self.tone = [rng.integers(0, len(tones), len(e)) for e in self.edges]
        self.shade = [0.85 + 0.3 * rng.random(len(e)) for e in self.edges]
        self.missing = [rng.random(len(e)) < miss for e in self.edges]
        self.slip = [(rng.random(len(e)) - 0.5) * 0.05 for e in self.edges]
        self.tones, self.dark, self.moss = tones, dark, moss
        self.noise = Noise(seed + 9, (1.5, 0.6, 0.25))

    def _cell(self, U, V):
        c = np.clip((V / self.course).astype(int), 0, self.nc - 1)
        cf = V / self.course - np.floor(V / self.course)
        idx = np.zeros(U.shape, int)
        for k in np.unique(c):
            sel = c == k
            idx[sel] = np.clip(np.searchsorted(self.edges[k], U[sel], 'right') - 1, 0, len(self.edges[k]) - 1)
        return c, cf, idx

    def relief(self, U, V):
        c, cf, idx = self._cell(U, V)
        slip = np.zeros(U.shape)
        miss = np.zeros(U.shape, bool)
        for k in np.unique(c):
            sel = c == k
            slip[sel] = self.slip[k][idx[sel]]
            miss[sel] = self.missing[k][idx[sel]]
        wedge = 0.026 * (0.2 + 0.8 * cf)                       # V grows down the slope: the lower edge of a course stands out
        wedge = wedge + slip
        return np.where(miss, -0.004, wedge) + 0.004 * self.noise.value(U * 4, V * 4)

    def colour(self, U, V, R):
        c, cf, idx = self._cell(U, V)
        out = np.zeros(U.shape + (4,))
        tones = np.array(self.tones)
        for k in np.unique(c):
            sel = c == k
            t = self.tone[k][idx[sel]]
            out[sel] = tones[t] * self.shade[k][idx[sel]][..., None]
            m = self.missing[k][idx[sel]]
            if m.any():
                tmp = out[sel]
                tmp[m] = np.array(self.dark)
                out[sel] = tmp
        shadow = smoothstep(0.0, 0.25, cf)[..., None]
        out = out * (0.85 + 0.15 * shadow)
        mo = np.clip(0.4 + self.noise.value(U * 1.2, V * 1.2), 0, 1) * smoothstep(1.0, 3.0, V)
        mo = (np.clip(mo, 0, 0.5) * 0.7)[..., None]
        out = out * (1 - mo) + np.array(self.moss) * mo
        out[..., 3] = 1.0
        return np.clip(out, 0, 1)


# ------------------------------------------------------------------ the roof: geometry shared by A and B
class Cot:
    """The numbers of one cottage's roof and walls. d is the distance from the ridge line (positive toward either eave); the rafters' underside line U(d) passes through the outer corner of their seat on
    the wall plate; T(d) is the top of the rafters (the plane the thatch rests on)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.yc = (self.y0 + self.y1) / 2
        self.hw = (self.y1 - self.y0) / 2
        self.d_a = self.d_b - self.bw
        self.rv = self.r_d / COS
        self.z_rb0 = self.Zp + TAN * (self.d_b - 0.02)          # bottom of the ridge piece with no sag

    def U(self, d):
        return self.Zp + TAN * (self.d_b - d)

    def T(self, d):
        return self.U(d) + self.rv

    def sag(self, x):
        x = np.asarray(x, float)
        s = np.zeros_like(x)
        for a, b in zip(self.xt[:-1], self.xt[1:]):
            m = (x >= a) & (x <= b)
            s[m] = np.sin(np.pi * (x[m] - a) / (b - a)) ** 2
        return s * self.sag_max

    def ridge_z(self, x):
        return self.z_rb0 - self.sag(x)


def rafter_polygon(c, z_cut, d_max):
    """The side view of a common rafter in (d, z): a horizontal cut at the ridge, the top line, a plumb tail end, the underside line with a birdsmouth over the wall plate."""
    d_cb = c.d_b - (z_cut - c.Zp) / TAN
    d_ct = d_cb + c.rv / TAN
    return [(d_cb, z_cut), (d_ct, z_cut), (d_max, c.T(d_max)), (d_max, c.U(d_max)), (c.d_b, c.Zp), (c.d_a, c.Zp), (c.d_a, c.U(c.d_a))], d_cb


def build_roof_frame(c, rng, timber, count_rafters_info):
    """Rafters (a south and a north one at every position), collars, purlins (let into the rafters), the ridge piece (laid on the rafter tops). Returns a dict of Acc objects."""
    out = {'rafters': Acc(), 'collars': Acc(), 'purlin_s': Acc(), 'purlin_n': Acc(), 'ridge': Acc()}
    for x, principal in c.rafter_x:
        z_cut = float(c.ridge_z(x))
        for side in (-1, 1):
            w = (0.105 + 0.015 * rng.random()) if principal else (0.065 + 0.025 * rng.random())
            d_max = c.hw + 0.17 + 0.14 * rng.random()
            poly, _ = rafter_polygon(c, z_cut, d_max)
            P = [(c.yc + side * d, z) for d, z in poly]
            V, F = extrude_x(P, x - w / 2, x + w / 2)
            yaw = math.radians((rng.random() - 0.5) * 0.9)
            V = rot_z(V, yaw, (x, c.yc + side * (c.d_a + c.d_b) / 2))
            out['rafters'].add(V, F, vary(timber, rng, 0.12))
    for x in c.collar_x:
        z_c = c.collar_z
        d_u = c.d_b - (z_c - c.Zp) / TAN
        half = d_u + 0.05
        w = 0.09 + 0.02 * rng.random()
        poly = [(c.yc - half, z_c - 0.045), (c.yc + half, z_c - 0.045), (c.yc + half, z_c + 0.045), (c.yc - half, z_c + 0.045)]
        V, F = extrude_x(poly, x - w / 2, x + w / 2)
        out['collars'].add(V, F, vary(timber, rng, 0.1))
    # the purlins: a rectangle turned to lie along the slope, its top face 4.5 cm up inside the rafters' underside
    pen, ph, pw = 0.045, 0.14, 0.12
    s_vec, n_vec = np.array([COS, -SIN]), np.array([SIN, COS])
    base = np.array([c.d_p, c.U(c.d_p)])
    corners = [(-pw / 2, -(ph - pen)), (pw / 2, -(ph - pen)), (pw / 2, pen), (-pw / 2, pen)]
    pts = [base + a * s_vec + b * n_vec for a, b in corners]
    cuts = [c.px0] + list(c.xt[1:-1]) + [c.px1]
    for name, side in (('purlin_s', -1), ('purlin_n', 1)):
        for a, b in zip(cuts[:-1], cuts[1:]):
            P = [(c.yc + side * float(p[0]), float(p[1])) for p in pts]
            V, F = extrude_x(P, a + 0.005, b - 0.005)
            out[name].add(V, F, vary(timber, rng, 0.1))
    # the ridge piece: a bar that sags between the trusses (bottom follows the cut tops of the rafters)
    wr, hr = 0.24, 0.14
    rcuts = [c.rx0] + list(c.xt[1:-1]) + [c.rx1]
    for a, b in zip(rcuts[:-1], rcuts[1:]):
        xs = np.linspace(a + 0.005, b - 0.005, max(3, int((b - a) / 0.2) + 1))
        zb = c.ridge_z(xs)
        rings = [[(x, c.yc - wr / 2, z), (x, c.yc + wr / 2, z), (x, c.yc + wr / 2, z + hr), (x, c.yc - wr / 2, z + hr)] for x, z in zip(xs, zb)]
        V, F = loft_rings(rings)
        out['ridge'].add(V, F, vary(timber, rng, 0.08))
    return out


def build_thatch(c, rng, colour_fn, roll=1.0, amp=0.03, seed=3):
    """The thatch: one closed slab, a thick shaggy sheet lying on the rafter tops (flat underside), a top surface with soft lumps, a rolled eave bead, a rounded hump (the ridge cap) that sags with the ridge,
    and rounded verges at both ends. colour_fn(kind, x, d, side, extra) -> (n, 4) colours of the faces."""
    noise = Noise(seed, (2.2, 0.9, 0.4))
    noise2 = Noise(seed + 50, (1.4, 0.6, 0.3))
    t_v = c.t_n / COS
    d_tip = c.hw + c.overhang
    a_arc = 0.15 * roll
    d_c = d_tip - a_arc
    xs = list(np.arange(c.tx0, c.tx1 - 1e-6, 0.14)) + [c.tx1]
    xs = sorted(set(list(np.round(xs, 4)) + [c.tx0 + 0.035, c.tx0 + 0.08, c.tx1 - 0.035, c.tx1 - 0.08]))
    xs = np.array(xs)
    n_u, n_a, n_t = 7, 9, 34
    ds_u = np.linspace(d_c, 0.0, n_u)
    ds_t = np.linspace(d_c, 0.0, n_t + 1)
    phis = np.linspace(-np.pi / 2, np.pi / 2, n_a)
    rings, kinds, dpos, sides = [], [], [], []
    for mi, x in enumerate(xs):
        endf = float(smoothstep(0.0, 0.12, min(x - c.tx0, c.tx1 - x)))
        thick_f = 0.25 + 0.75 * endf
        sag = float(c.sag(np.array([x]))[0])
        pts, kd, dp, sd = [], [], [], []

        def add(side, d, z, kind):
            pts.append((c.yc + side * d, z))
            kd.append(kind)
            dp.append(d)
            sd.append(side)
        for d in ds_u:                                                      # south underside, eave to ridge
            add(-1, d, c.T(d), 0)
        for d in ds_u[-2::-1]:                                              # north underside, ridge to eave
            add(1, d, c.T(d), 0)

        def arc(side, reverse):
            seq = phis[1:] if not reverse else phis[:0:-1]
            droop = 0.018 * roll * (0.5 + 0.5 * noise2.value(x * 1.7, side * 3.0))
            aa = a_arc * (0.85 + 0.3 * (0.5 + 0.5 * noise2.value(x * 2.3, side * 7.0)))
            for ph in seq:
                tv = t_v * thick_f
                zc = c.T(d_c) + tv / 2
                dd = d_c + aa * np.cos(ph)
                zz = zc + tv / 2 * np.sin(ph) - droop * (1 - np.sin(ph)) / 2
                add(side, dd, zz, 1)

        arc(1, False)
        top = []
        for k, d in enumerate(ds_t):
            if k == 0:
                continue                                                    # the arc's last point is the top at d_c
            top.append(d)
        for d in top:                                                       # north top, eave to ridge
            sd_ = 1
            nz = amp * (noise.value(x * 1.0 + 3.1, d * 1.0 + 1.1) + 0.5 * noise2.value(x * 3.1, d * 3.1 + 5))
            nz = nz * (0.25 + 0.75 * endf)
            hump = 0.11 * math.exp(-(d / 0.33) ** 2)
            z = c.T(d) + t_v * thick_f + nz * COS + hump - sag * math.exp(-(d / 1.0) ** 2) * 0.9
            dd = d + nz * SIN
            add(sd_, dd if d > 0 else 0.0, z, 3 if d < 0.42 else 2)
        for d in top[-2::-1]:                                               # south top, ridge to eave (the ridge point is shared)
            sd_ = -1
            nz = amp * (noise.value(x * 1.0 + 9.7, d * 1.0 + 4.1) + 0.5 * noise2.value(x * 3.1 + 2, d * 3.1 + 9))
            nz = nz * (0.25 + 0.75 * endf)
            hump = 0.11 * math.exp(-(d / 0.33) ** 2)
            z = c.T(d) + t_v * thick_f + nz * COS + hump - sag * math.exp(-(d / 1.0) ** 2) * 0.9
            dd = d + nz * SIN
            add(sd_, dd, z, 3 if d < 0.42 else 2)
        arc(-1, True)
        rings.append([(x, y, z) for y, z in pts])
        kinds.append(kd)
        dpos.append(dp)
        sides.append(sd)
    R = np.array(rings)
    M, N, _ = R.shape
    V, F = loft_rings(R)
    kd, dp, sd = np.array(kinds[0]), np.array(dpos[0]), np.array(sides[0])
    cols = []
    for m in range(M - 1):
        xm = (xs[m] + xs[m + 1]) / 2
        kk = np.arange(N)
        k2 = (kk + 1) % N
        kind = np.maximum(kd[kk], kd[k2])
        dmid = (dp[kk] + dp[k2]) / 2
        smid = sd[kk]
        z_mid = (R[m, kk, 2] + R[m + 1, k2, 2]) / 4 + (R[m, k2, 2] + R[m + 1, kk, 2]) / 4
        cols.append(colour_fn(kind, np.full(N, xm), dmid, smid, z_mid))
    flat = []
    for m in range(M - 1):
        flat.extend(tuple(row) for row in cols[m])
    flat.append(colour_fn(np.array([4]), np.array([xs[0]]), np.array([1.0]), np.array([1]), np.array([0.0]))[0].tolist())
    flat.append(colour_fn(np.array([4]), np.array([xs[-1]]), np.array([1.0]), np.array([1]), np.array([0.0]))[0].tolist())
    return V, F, [tuple(f) for f in flat]


# ------------------------------------------------------------------ small helpers for both cottages
class Builder:
    """Makes the objects of one cottage: every object gets its owner and role as it is made, a material, and (later) a seat on the ground."""

    def __init__(self, tag, g):
        self.tag, self.g, self.objects = tag, g, []

    def emit(self, acc, name, role, mat, smooth=False):
        if acc.empty():
            return None
        full = f'Cottage {self.tag} {name}'
        mesh = acc.make(full, smooth=smooth)
        mesh.transform(__import__('mathutils').Matrix.Translation((0.0, 0.0, self.g)))
        mesh.update()
        mesh.materials.append(mat)
        obj = pk.new_part_object(OWNER, role, full, mesh)
        self.objects.append(obj)
        return obj


def members_along(fixed, limit=0.9):
    """fixed: sorted list of (centre, half width, kind). Between neighbours whose centre-to-centre gap is over `limit`, equal studs are added so that no gap is over `limit`. Returns the full sorted list
    with the added ones marked kind 'stud'."""
    out = []
    fixed = sorted(fixed, key=lambda m: m[0])
    for k, m in enumerate(fixed):
        out.append(m)
        if k + 1 < len(fixed):
            a, b = m[0], fixed[k + 1][0]
            gap = b - a
            if gap > limit:
                n = int(math.ceil(gap / limit))
                for j in range(1, n):
                    out.append((a + gap * j / n, 0.035, 'stud'))
    return out


def jitter_poly_edges(pts, rng, amount, only_long=True, step=0.45):
    """Adds points along each long edge of a footprint polygon, pushed outward by a random amount (rubble, not a ruler line)."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % n], float)
        out.append(tuple(a))
        L = np.linalg.norm(b - a)
        if L > 1.0 and only_long:
            k = int(L / step)
            d = (b - a) / L
            nrm = np.array([d[1], -d[0]])
            for j in range(1, k):
                t = j / k
                out.append(tuple(a + (b - a) * t + nrm * amount * (rng.random() - 0.3)))
    return out


def ring_stone_course(cx, cy, z0, z1, sx, sy, rng, jut=0.03):
    """A loft of a rectangle that varies a little from course to course: a chimney's courses. Returns the 4 corners (x, y) of the ring."""
    j = lambda: jut * (rng.random() - 0.3)  # noqa: E731
    return [(cx - sx / 2 - j(), cy - sy / 2 - j()), (cx + sx / 2 + j(), cy - sy / 2 - j()), (cx + sx / 2 + j(), cy + sy / 2 + j()), (cx - sx / 2 - j(), cy + sy / 2 + j())]


def ground_level(x0, x1, y0, y1):
    return max(pk.ground_height_at(x, y) for x in np.linspace(x0, x1, 9) for y in np.linspace(y0, y1, 6))


# ------------------------------------------------------------------ the colour of thatch (faces of the thatch slab)
def thatch_colour_fn(seed, base_a, base_b, patch, moss, cap, under, end, moss_amount=0.0, north_moss=0.0):
    noise = Noise(seed, (1.8, 0.7, 0.3))
    noise2 = Noise(seed + 11, (1.2, 0.5, 0.22))

    def fn(kind, x, d, side, z):
        kind = np.asarray(kind)
        x, d, side = np.asarray(x, float), np.asarray(d, float), np.asarray(side, float)
        n = 0.5 + 0.5 * noise.value(x * 0.9 + side * 3.0, d * 1.4 + 5 * side)
        n2 = 0.5 + 0.5 * noise2.value(x * 2.3 + side, d * 2.7 + 1.0)
        base = np.array(base_a) * (1 - n[:, None]) + np.array(base_b) * n[:, None]
        pm = smoothstep(0.62, 0.8, n2)[:, None] * 0.55
        base = base * (1 - pm) + np.array(patch) * pm
        if moss_amount > 0:
            lowness = smoothstep(0.0, 2.2, d)                      # more moss lower on the slope (larger d is nearer the eave)
            shade = 1.0 + north_moss * (side > 0)
            mm = np.clip(smoothstep(0.45, 0.75, n2) * lowness * moss_amount * shade, 0, 0.85)[:, None]
            base = base * (1 - mm) + np.array(moss) * mm
        out = base.copy()
        arc = (kind == 1)
        out[arc] = base[arc] * 0.82
        cp = (kind == 3)
        t = (smoothstep(0.42, 0.2, d[cp]) * 0.85)[:, None]
        out[cp] = base[cp] * (1 - t) + np.array(cap) * t
        out[kind == 0] = np.array(under)
        out[kind == 4] = np.array(end)
        out[..., 3] = 1.0
        return np.clip(out, 0, 1)
    return fn


