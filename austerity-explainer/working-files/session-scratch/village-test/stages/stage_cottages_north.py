"""What this does: the COTTAGES_NORTH part of the forest village (owner cottages_north): cottage A (long, dark oak frame, cream limewash panels, golden thatch, a log-store lean-to on its west end)
and cottage B (small, heavy, grey rubble stone, old mossy thatch, the only stone chimney), both on the north side of the high road, both seated on the frozen ground (the level pads the ground part built).
Everything is built from the ground up and every part is carried: stone footing, sill, posts, studs, wall plate, wall panels (or stone walls), rafters resting on the plates and let into a purlin,
a ridge piece laid on the rafter tops, a thick rolled thatch slab resting on the rafters, an earth floor, a door on iron hinges, a flat stone doorstep, small shuttered windows (no glass).
Character is SHAPE: posts out of plumb and no two alike, a sagging ridge, lumpy thatch with a rolled eave, plaster chipped to the wattle, a darker splash band at the foot, replaced boards in a fresher
colour, stones of uneven size standing out of the wall. Colour is written into each mesh as a colour layer (Col) and read by a material of our own that carries a small picture, so the surface pass keeps
our colours and adds its normal maps, roughness and wear on top.
It is IDEMPOTENT: apply(options) first forgets what an earlier run of this owner made (pk.forget_part), then builds again with the same seed. It changes nothing that is not ours.
A concrete example: apply({'seed': 17}) twice gives the same objects. Options: seed (default 17), sag_cm (ridge sag scale, 1.0 = 3 cm on A and 3.5 cm on B), thatch_roll (eave roll scale, default 1.3), thatch_lump (scale of the lumps in the thatch, default 1.25),
chip_amount (size of the plaster chips, default 1.35) and chip_count (how many panels of A are chipped, default 1.0 = five: three on the south wall, two on the north).
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
        loop_cols = []
        for f, col in zip(self.F, self.C):
            if isinstance(col[0], (tuple, list, np.ndarray)):          # one colour for each corner of the face (smooth gradients)
                loop_cols.extend(col)
            else:
                loop_cols.extend([col] * len(f))
        attr.data.foreach_set('color', np.asarray(loop_cols, float).ravel())
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
    vert_cols = colour_fn(U, Vv, fr) if colour_fn is not None else None          # one colour for each front vertex: blends smoothly across the faces
    for j in range(nv):
        for i in range(nu):
            if not keep[i, j]:
                continue
            F.append((fi(i, j), fi(i + 1, j), fi(i + 1, j + 1), fi(i, j + 1)))
            C.append([tuple(vert_cols[j, i]), tuple(vert_cols[j, i + 1]), tuple(vert_cols[j + 1, i + 1]), tuple(vert_cols[j + 1, i])] if vert_cols is not None else (0.5, 0.5, 0.5, 1.0))
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


def height_image():
    """A small soft height picture around 0.5 (mid level) for the real displacement of thatch and rubble."""
    name = 'Cottages north height'
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, 64, 64, alpha=False)
        img.colorspace_settings.name = 'Non-Color'
        rng = np.random.default_rng(9)
        a = np.kron(rng.random((8, 8)), np.ones((8, 8)))
        b = np.kron(rng.random((16, 16)), np.ones((4, 4)))
        v = 0.5 + 0.12 * (a - 0.5) + 0.06 * (b - 0.5)
        pix = np.stack([v, v, v, np.ones_like(v)], axis=-1)
        img.pixels.foreach_set(pix.ravel().astype(np.float32))
        img.pack()
        img.use_fake_user = True
    return img


def make_material(name, roughness=0.85, displace=None):
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
    out.is_active_output = True
    if displace:                                                   # real displacement (thatch and rubble need it): the kit's own node and method, our own height picture
        from place_kit.surfaces import displacement as kit_displacement
        himg = nt.nodes.new('ShaderNodeTexImage')
        himg.image = height_image()
        himg.interpolation = 'Cubic'
        nt.links.new(mapping.outputs['Vector'], himg.inputs['Vector'])
        kit_displacement.set_displacement(mat, himg.outputs['Color'], float(displace), nt)
    else:
        mat.displacement_method = 'BUMP'
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
        mud = smoothstep(0.55, 0.0, V)[..., None] * 0.35                                      # mud splashed up from the road along the foot of the wall
        col = col * (1 - mud) + np.array((0.24, 0.19, 0.13, 1.0)) * mud
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
        top = self.band * (1.0 + 0.35 * np.sin(U * 6.5 + 1.3) + 0.2 * np.sin(U * 13 + 0.4))
        s = smoothstep(top + 0.05, top - 0.05, V)[..., None]
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
        wedge = 0.012 * (0.2 + 0.8 * cf)                       # V grows down the slope: the lower edge of a course stands out
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
        mo = (np.clip(mo, 0, 0.5) * 0.45)[..., None]
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
        h, zb, zt = d_u, z_c - 0.045, z_c + 0.045
        zt_t = zt - 0.05                                                  # the tenons that go into the rafters are lower than the beam, so nothing 'stops short' under a rafter
        w = 0.09 + 0.02 * rng.random()
        poly = [(c.yc - h - 0.05, zb), (c.yc + h + 0.05, zb), (c.yc + h + 0.05, zt_t), (c.yc + h, zt_t), (c.yc + h, zt), (c.yc - h, zt), (c.yc - h, zt_t), (c.yc - h - 0.05, zt_t)]
        V, F = extrude_x(poly, x - w / 2, x + w / 2)
        out['collars'].add(V, F, vary(timber, rng, 0.1))
    # the purlins: a rectangle turned to lie along the slope, its top face 4.5 cm up inside the rafters' underside
    pen, ph, pw = 0.02, 0.14, 0.12
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
    xs = list(np.arange(c.tx0, c.tx1 - 1e-6, 0.2)) + [c.tx1]
    xs = sorted(set(list(np.round(xs, 4)) + [c.tx0 + 0.035, c.tx0 + 0.08, c.tx1 - 0.035, c.tx1 - 0.08]))
    xs = np.array(xs)
    n_u, n_a, n_t = 5, 9, 24
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
    vcols = []
    for m in range(M):
        vcols.append(colour_fn(kd, np.full(N, xs[m]), dp, sd, R[m, :, 2]))
    flat = []
    for m in range(M - 1):
        for k in range(N):
            k2 = (k + 1) % N
            flat.append([tuple(vcols[m][k]), tuple(vcols[m][k2]), tuple(vcols[m + 1][k2]), tuple(vcols[m + 1][k])])
    end_col = tuple(colour_fn(np.array([4]), np.array([xs[0]]), np.array([1.0]), np.array([1]), np.array([0.0]))[0])
    flat.append(end_col)
    flat.append(tuple(colour_fn(np.array([4]), np.array([xs[-1]]), np.array([1.0]), np.array([1]), np.array([0.0]))[0]))
    return V, F, flat


# ------------------------------------------------------------------ small helpers for both cottages
BEVEL_WIDTH = {'timber': 0.008, 'stone': 0.010, 'iron': 0.004, 'wall': 0.008, 'floor': 0.006, 'roof': 0.008}


def add_edge_rounding(obj, role):
    """Edges a hand could touch are rounded. A small boxy object gets its own cheap Bevel modifier (one segment, only on sharp edges); the kit then leaves it alone (it adds no second bevel). A large relief object (a
    rubble wall, a panel, the thatch, the shingles) is rounded in its own shape (pillowed stones, a rolled eave): it is marked pk_bevelled so the kit adds no bevel to millions of relief faces."""
    faces = len(obj.data.polygons)
    if faces > 1500:
        obj['pk_bevelled'] = 1
        return
    klass = role.split('.')[0]
    size = min(obj.dimensions) or 0.05
    width = min(BEVEL_WIDTH.get(klass, 0.008), max(size / 4.0, 0.001))
    mod = obj.modifiers.new('Cottage bevel', 'BEVEL')
    mod.width = width
    mod.segments = 1
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(40.0)


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
        add_edge_rounding(obj, role)
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
            if gap > limit and not (m[2] == 'door' and fixed[k + 1][2] == 'door'):
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


# ------------------------------------------------------------------ COTTAGE A
def _footing_acc(strips, rng, x_lo, x_hi, y_lo, y_hi, height, colours, outer):
    """Rough rubble strips: flat top and bottom, the outer long edge pushed out by a different amount every half metre; the strips butt (they never overlap)."""
    acc = Acc()
    for (xa, xb), (ya, yb), axis in strips:
        if axis == 'x_long':
            n = max(1, int((xb - xa) / 0.5))
            if outer == 'south':
                poly = [(xa, ya)] + [(xa + (xb - xa) * j / n, ya - 0.03 * rng.random()) for j in range(1, n)] + [(xb, ya), (xb, yb), (xa, yb)]
            else:
                poly = [(xa, ya), (xb, ya), (xb, yb)] + [(xb - (xb - xa) * j / n, yb + 0.03 * rng.random()) for j in range(1, n)] + [(xa, yb)]
        else:
            n = max(1, int((yb - ya) / 0.5))
            if outer == 'west':
                poly = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)] + [(xa - 0.03 * rng.random(), yb - (yb - ya) * j / n) for j in range(1, n)]
            else:
                poly = [(xa, ya), (xb, ya)] + [(xb + 0.03 * rng.random(), ya + (yb - ya) * j / n) for j in range(1, n)] + [(xb, yb), (xa, yb)]
        V, F = extrude_z(poly, 0.0, height)
        acc.add(V, F, vary(colours[int(rng.integers(0, len(colours)))], rng, 0.08))
    return acc


def _wall_panels(B, rng, wall, mem, wins, x0, x1, y0, y1, SILL_TOP, PL_BOT, base, chips_n, chip_scale, mats, splash_band=0.24):
    """The studs and the cream panels of one wall. mem: sorted members (centre, half width, kind). Returns (studs, panels, frames) accumulators."""
    OAK = mats['OAK']
    studs, panels = Acc(), Acc()
    for ctr, hw_, kind in mem:
        if kind not in ('stud', 'win'):
            continue
        lean = ((rng.random() - 0.5) * 0.01, (rng.random() - 0.5) * 0.01)
        if wall in ('south', 'north'):
            yy = y0 + 0.07 if wall == 'south' else y1 - 0.07
            V, F = lofted_post(ctr, yy, SILL_TOP, PL_BOT, 0.07, 0.12, lean=lean, twist=(rng.random() - 0.5) * 0.05, taper=0.96 + 0.04 * rng.random())
        else:
            xx = x0 + 0.07 if wall == 'west' else x1 - 0.07
            V, F = lofted_post(xx, ctr, SILL_TOP, PL_BOT, 0.12, 0.07, lean=lean, twist=(rng.random() - 0.5) * 0.05, taper=0.96 + 0.04 * rng.random())
        studs.add(V, F, vary(OAK, rng, 0.2))
    pan = []
    for (a, ha, ka), (b, hb, kb) in zip(mem[:-1], mem[1:]):
        if ka == 'door' and kb == 'door':
            continue
        lo, hi = a + ha + 0.003, b - hb - 0.003
        if hi - lo < 0.05:
            continue
        is_window = (ka == 'win' and kb == 'win') and any(abs((a + b) / 2 - wx) < 0.01 for wx in wins)
        for z0_, z1_ in ([(SILL_TOP, 0.90), (1.61, PL_BOT - 0.01)] if is_window else [(SILL_TOP, PL_BOT - 0.01)]):
            pan.append((lo, hi, z0_, z1_, is_window))
    eligible = [i for i, p in enumerate(pan) if (p[1] - p[0]) > 0.55 and not p[4]]
    chosen = set(rng.choice(eligible, size=min(chips_n, len(eligible)), replace=False).tolist()) if eligible and chips_n else set()
    for i, (lo, hi, z0_, z1_, is_window) in enumerate(pan):
        W, Hh = hi - lo, z1_ - z0_
        chips = 1 if i in chosen else 0
        field = PlasterField(int(rng.integers(1, 10 ** 6)), W, Hh, vary(base, rng, 0.04), mats['splash'], mats['hi'], mats['lo'], mats['rim'], chips=chips, chip_scale=chip_scale,
                             band=splash_band if z0_ == SILL_TOP else 0.0)
        step = 0.035 if chips else 0.3
        us, vs = subdivide_lines([0, W], step), subdivide_lines([0, Hh], step)
        if wall == 'south':
            orig, e_u, e_n = (lo, y0 + 0.12, z0_), (1, 0, 0), (0, -1, 0)
        elif wall == 'north':
            orig, e_u, e_n = (hi, y1 - 0.12, z0_), (-1, 0, 0), (0, 1, 0)
        elif wall == 'west':
            orig, e_u, e_n = (x0 + 0.12, hi, z0_), (0, -1, 0), (-1, 0, 0)
        else:
            orig, e_u, e_n = (x1 - 0.12, lo, z0_), (0, 1, 0), (1, 0, 0)
        V, F, C = relief_slab(orig, e_u, e_n, us, vs, 0.10, field.relief, None, colour_fn=field.colour, back_colour=mats['back'], edge_colour=mats['edge'])
        panels.add(V, F, C)
    return studs, panels


def build_cottage_A(opts):
    seed = int(opts.get('seed', 17))
    rng = np.random.default_rng(seed * 7 + 1)
    chip_scale = float(opts.get('chip_amount', 1.35))
    x0, x1, y0, y1 = -37.55, -26.45, 7.6, 12.4
    yc = 10.0
    g = ground_level(-40.1, x1, y0 - 0.5, y1)
    B = Builder('A', g)
    OAK, CREAM = hexl('#3E3128'), hexl('#CDBE9A')
    mats = dict(OAK=OAK, splash=hexl('#8C7B5C'), hi=hexl('#8A6A45'), lo=hexl('#4F3E2C'), rim=hexl('#E2D6B4'), back=hexl('#B5A583'), edge=hexl('#D8CBA6'))
    M = dict(oak=make_material('Cottage A oak frame', 0.8), lime=make_material('Cottage A limewash', 0.9), thatch=make_material('Cottage A thatch', 0.95, displace=0.05),
             stone=make_material('Cottage A footing stone', 0.85), boards=make_material('Cottage A boards', 0.8), iron=make_material('Cottage A iron', 0.6),
             earth=make_material('Cottage A earth', 0.95), shingle=make_material('Cottage A shingles', 0.85), shutter=make_material('Cottage A shutter wood', 0.8))
    IRON = hexl('#2E2E30')
    xt = [x0 + 0.07, x0 + 3.70, x0 + 7.40, x1 - 0.07]
    FOOT_H, SILL_TOP, PL_BOT, PL_TOP = 0.28, 0.40, 1.88, 2.0
    DOOR_X, DOOR_POSTS = -32.0, (-32.55, -31.45)
    c = Cot(x0=x0, x1=x1, y0=y0, y1=y1, Zp=PL_TOP, d_b=2.4, bw=0.14, r_d=0.10, xt=xt, sag_max=0.03 * float(opts.get('sag_cm', 1.0)), collar_z=4.0, collar_x=[xt[1], xt[2]], d_p=1.25,
            px0=x0 + 0.03, px1=x1 - 0.03, rx0=x0 + 0.05, rx1=x1 - 0.05, tx0=x0 - 0.25, tx1=x1 + 0.25, t_n=0.30, overhang=0.45, rafter_x=[])
    for k in range(3):
        a, b = xt[k], xt[k + 1]
        n = int(round((b - a) / 0.73))
        for j in range(n):
            c.rafter_x.append((a + (b - a) * j / n, j == 0))
    c.rafter_x.append((xt[-1], True))
    stone_cols = [hexl('#7C7A73'), hexl('#6F6D66'), hexl('#85827A'), hexl('#6A6962')]

    # ---- footing: rubble strips that butt (no overlap), the doorway left open
    acc = Acc()
    parts = [(_footing_acc([((x0 - 0.02, -32.70), (y0 - 0.02, y0 + 0.40), 'x_long'), ((-31.30, x1 + 0.02), (y0 - 0.02, y0 + 0.40), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'south')),
             (_footing_acc([((x0 - 0.02, x1 + 0.02), (y1 - 0.40, y1 + 0.02), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'north')),
             (_footing_acc([((x0 - 0.02, x0 + 0.40), (y0 + 0.40, y1 - 0.40), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'west')),
             (_footing_acc([((x1 - 0.40, x1 + 0.02), (y0 + 0.40, y1 - 0.40), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'east'))]
    for p in parts:
        merge_acc(acc, p)
    foot = B.emit(acc, 'footing', 'stone.footing', M['stone'])
    shift = pk.seat_on_ground(foot)
    B.g += shift                                                                   # everything else of this cottage is built from the footing's own seat

    # ---- sill timbers on the footing (flat tops and bottoms; bowed a little in plan)
    acc = Acc()
    sills = [(x0, xt[1] - 0.005, y0 + 0.08), (xt[1] + 0.005, -32.62, y0 + 0.08), (-31.38, xt[2] - 0.005, y0 + 0.08), (xt[2] + 0.005, x1, y0 + 0.08),
             (x0, xt[1] - 0.005, y1 - 0.08), (xt[1] + 0.005, xt[2] - 0.005, y1 - 0.08), (xt[2] + 0.005, x1, y1 - 0.08)]
    for xa, xb, yy in sills:
        V, F = bowed_bar_x(xa, xb, yy, 0.16, FOOT_H, SILL_TOP, (rng.random() - 0.5) * 0.014, ybow_phase=rng.random())
        acc.add(V, F, vary(OAK, rng, 0.15))
    for xx in (x0 + 0.08, x1 - 0.08):
        V, F = extrude_y([(xx - 0.08, FOOT_H), (xx + 0.08, FOOT_H), (xx + 0.08, SILL_TOP), (xx - 0.08, SILL_TOP)], y0 + 0.16, y1 - 0.16)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'sill timbers', 'timber.beam', M['oak'])

    # ---- posts: each its own object (so each leans differently); truss posts stand on the sill, the door posts on the ground
    corner = {(0, 0): 'south west corner', (0, 1): 'north west corner', (3, 0): 'south east corner', (3, 1): 'north east corner'}
    posts = []
    for k, x in enumerate(xt):
        for side, yy in ((0, y0 + 0.07), (1, y1 - 0.07)):
            posts.append((corner.get((k, side), f'truss {k + 1} {"south" if side == 0 else "north"}'), x, yy, SILL_TOP, 0.14, 0.14))
    for xdp in DOOR_POSTS:
        posts.append((f'door post {"west" if xdp < DOOR_X else "east"}', xdp, y0 + 0.07, 0.0, 0.12, 0.14))
    for nm, x, yy, zb, sx, sy in posts:
        acc = Acc()
        lean = ((rng.random() - 0.5) * 0.024, (rng.random() - 0.5) * 0.024)
        V, F = lofted_post(x, yy, zb, PL_BOT, sx, sy, lean=lean, twist=(rng.random() - 0.5) * 0.08, taper=0.92 + 0.07 * rng.random())
        acc.add(V, F, vary(OAK, rng, 0.2))
        o = B.emit(acc, f'post {nm}', 'timber.post', M['oak'])
        if zb == 0.0:
            pk.seat_on_ground(o)

    # ---- the four walls: studs, cream panels, window sills and heads
    south = [(xt[k], 0.07, 'post') for k in range(4)] + [(DOOR_POSTS[0], 0.06, 'door'), (DOOR_POSTS[1], 0.06, 'door')] + [(wx + s * 0.26, 0.035, 'win') for wx in (-35.0, -29.0) for s in (-1, 1)]
    north = [(xt[k], 0.07, 'post') for k in range(4)] + [(-32.0 + s * 0.26, 0.035, 'win') for s in (-1, 1)]
    end = [(y0 + 0.07, 0.07, 'post'), (y1 - 0.07, 0.07, 'post')]
    cc = float(opts.get('chip_count', 1.0))
    spec = {'south': (members_along(south), [-35.0, -29.0], int(round(3 * cc))), 'north': (members_along(north), [-32.0], int(round(2 * cc))), 'west': (members_along(end), [], 0), 'east': (members_along(end), [], 0)}
    for wall in ('south', 'north', 'west', 'east'):
        mem, wins, chips_n = spec[wall]
        studs, panels = _wall_panels(B, rng, wall, mem, wins, x0, x1, y0, y1, SILL_TOP, PL_BOT, CREAM, chips_n, chip_scale, mats)
        frames = Acc()
        for wx in wins:
            yy0 = y0 + 0.02 if wall == 'south' else y1 - 0.12
            for z0_, z1_ in ((0.90, 0.96), (1.55, 1.61)):
                V, F = box(wx - 0.275, wx + 0.275, yy0, yy0 + 0.10, z0_, z1_)
                frames.add(V, F, vary(OAK, rng, 0.15))
        B.emit(studs, f'{wall} wall studs', 'timber.beam', M['oak'])
        B.emit(panels, f'{wall} wall panels', 'wall.timber_frame', M['lime'])
        if not frames.empty():
            B.emit(frames, f'{wall} window sills and heads', 'timber.beam', M['oak'])

    # ---- wall plates: three sections on each long wall, one across each end
    acc = Acc()
    for xa, xb in ((x0, xt[1] - 0.005), (xt[1] + 0.005, xt[2] - 0.005), (xt[2] + 0.005, x1)):
        for yy in (y0 + 0.08, y1 - 0.08):
            V, F = bowed_bar_x(xa, xb, yy, 0.16, PL_BOT, PL_TOP, (rng.random() - 0.5) * 0.016, ybow_phase=rng.random())
            acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'wall plates', 'timber.beam', M['oak'])
    acc = Acc()
    for xx in (x0 + 0.08, x1 - 0.08):
        V, F = extrude_y([(xx - 0.08, PL_BOT), (xx + 0.08, PL_BOT), (xx + 0.08, PL_TOP), (xx - 0.08, PL_TOP)], y0 + 0.16, y1 - 0.16)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'end wall plates', 'timber.beam', M['oak'])

    # ---- gable ends: five gable studs and six panels over each end plate, up to the underside of the end rafters
    gable_y = [yc + k * 0.8 for k in (-2, -1, 0, 1, 2)]
    for wall, xx in (('west', x0 + 0.07), ('east', x1 - 0.07)):
        gs, gp = Acc(), Acc()
        for yy in gable_y:
            V, F = lofted_post(xx, yy, PL_TOP, c.U(abs(yy - yc)), 0.12, 0.07, lean=(0, (rng.random() - 0.5) * 0.006), top_z_fn=lambda x, y: (c.U(abs(y - yc)) if abs(y - yc) > 0.06 else float(c.ridge_z(x))) - 0.003)
            gs.add(V, F, vary(OAK, rng, 0.2))
        edges = [y0 + 0.16] + sum([[y - 0.038, y + 0.038] for y in gable_y], []) + [y1 - 0.16]
        for a, b in zip(edges[0::2], edges[1::2]):
            W = b - a
            field = PlasterField(int(rng.integers(1, 10 ** 6)), W, 3.0, vary(CREAM, rng, 0.04), mats['splash'], mats['hi'], mats['lo'], mats['rim'], chips=0, band=0.0)
            us, vs = subdivide_lines([0, W], 0.25), subdivide_lines([PL_TOP, PL_TOP + 1.0], 0.3)
            if wall == 'west':
                orig, e_u, e_n = (x0 + 0.12, b, 0.0), (0, -1, 0), (-1, 0, 0)
                yco = (lambda u, b=b: b - u)
            else:
                orig, e_u, e_n = (x1 - 0.12, a, 0.0), (0, 1, 0), (1, 0, 0)
                yco = (lambda u, a=a: a + u)
            V, F, C = relief_slab(orig, e_u, e_n, us, vs, 0.10, lambda U, V, f=field: f.relief(U, V - PL_TOP), None, colour_fn=lambda U, V, R, f=field: f.colour(U, V - PL_TOP, R),
                                  back_colour=mats['back'], edge_colour=mats['edge'], top_fn=lambda u, yco=yco: c.U(abs(yco(u) - yc)) - 0.006)
            gp.add(V, F, C)
        B.emit(gs, f'{wall} gable studs', 'timber.beam', M['oak'])
        B.emit(gp, f'{wall} gable panels', 'wall.timber_frame', M['lime'])
    return B, c, dict(rng=rng, M=M, OAK=OAK, IRON=IRON, x0=x0, x1=x1, y0=y0, y1=y1, yc=yc, xt=xt, DOOR_X=DOOR_X, DOOR_POSTS=DOOR_POSTS, FOOT_H=FOOT_H, PL_TOP=PL_TOP, PL_BOT=PL_BOT,
                      SILL_TOP=SILL_TOP, opts=opts, seed=seed, mats=mats)


def make_door(B, rng, mat, hinge_mat, iron_col, wall_y_front, x_left, width, height, thick, z_bottom, direction, fresh, tone, hinge_side='left', hinge_z=(0.35, 1.42), name_prefix='door'):
    """A door leaf (one piece: boards of unequal width with grooves, two battens on the back, one board a fresher replacement) and its two iron strap hinges. direction -1: the door faces south
    (outward is -y), +1: faces north. Returns (leaf acc, hinge acc)."""
    widths = [0.16 + 0.04 * rng.random() for _ in range(5)]
    field = BoardField(int(rng.integers(1, 10 ** 6)), width, height, widths, tone, fresh, fresh_index=int(rng.integers(1, 4)), batten_rows=[(0.28, 0.37), (height - 0.40, height - 0.31)])
    us, vs = subdivide_lines([0, width], 0.034), subdivide_lines([0, height], 0.22)
    if direction < 0:
        orig, e_u, e_n = (x_left, wall_y_front + thick, z_bottom), (1, 0, 0), (0, -1, 0)
    else:
        orig, e_u, e_n = (x_left + width, wall_y_front - thick, z_bottom), (-1, 0, 0), (0, 1, 0)
    V, F, C = relief_slab(orig, e_u, e_n, us, vs, thick, field.relief, field.back, colour_fn=field.colour, back_colour=shade(tone, 0.8), edge_colour=shade(tone, 0.7))
    leaf = Acc()
    leaf.add(V, F, C)
    hinges = Acc()
    for zc in hinge_z:
        length = 0.52 + 0.06 * rng.random()
        if direction < 0:
            xa, xb = (x_left - 0.01, x_left + length) if hinge_side == 'left' else (x_left + width - length, x_left + width + 0.01)
            ya, yb = wall_y_front - 0.011, wall_y_front + 0.002
        else:
            xa, xb = (x_left + width - length, x_left + width + 0.01) if hinge_side == 'left' else (x_left - 0.01, x_left + length)
            ya, yb = wall_y_front - 0.002, wall_y_front + 0.011
        zl = z_bottom + zc
        V, F = box(xa, xb, ya, yb, zl, zl + 0.07)
        hinges.add(V, F, vary(iron_col, rng, 0.2))
    # a latch: a short iron bar and a plate on the free edge, at hand height
    zl = z_bottom + 0.92
    if direction < 0:
        xa, xb = (x_left + width - 0.30, x_left + width - 0.07) if hinge_side == 'left' else (x_left + 0.07, x_left + 0.30)
        ya, yb = wall_y_front - 0.010, wall_y_front + 0.002
    else:
        xa, xb = (x_left + 0.07, x_left + 0.30) if hinge_side == 'left' else (x_left + width - 0.30, x_left + width - 0.07)
        ya, yb = wall_y_front - 0.002, wall_y_front + 0.010
    V, F = box(xa, xb, ya, yb, zl, zl + 0.025)
    hinges.add(V, F, vary(iron_col, rng, 0.2))
    V, F = box(xb - 0.07, xb + 0.012, ya - 0.004 if direction < 0 else ya, yb + (0.004 if direction > 0 else 0.0), zl - 0.02, zl + 0.045)
    hinges.add(V, F, vary(iron_col, rng, 0.2))
    return leaf, hinges


FACING_ANGLE = {'S': 0.0, 'E': 90.0, 'N': 180.0, 'W': 270.0}


def place_xy(V, facing, origin):
    """Moves a piece built at the origin facing south (outward is -y, the wall's outer plane is y = 0) to a wall that faces `facing` at `origin` (x, y)."""
    V = rot_z(V, math.radians(FACING_ANGLE[facing]), (0.0, 0.0))
    V[:, 0] += origin[0]
    V[:, 1] += origin[1]
    return V


def make_shutters(rng, iron_col, ajar, z0, z1, leaf_w, tone, fresh, facing, origin, plane=0.0):
    """Two shutter leaves of a window (no glass): each a board slab with a batten on the back and two strap hinges; the east leaf can stand ajar. Built facing south at x = 0 with the stud
    faces on the plane y = `plane`, then placed on the wall. Returns (leaves, hinges) accumulators."""
    leaves, hinges = Acc(), Acc()
    thick = 0.028
    for side in (-1, 1):                                       # -1: the west leaf (hinged at the west jamb), +1: the east leaf
        xa = -leaf_w if side < 0 else 0.0
        field = BoardField(int(rng.integers(1, 10 ** 6)), leaf_w, z1 - z0, [0.5 + 0.2 * rng.random(), 0.5 + 0.2 * rng.random()], tone, fresh, fresh_index=(int(rng.integers(0, 2)) if rng.random() < 0.3 else None),
                           batten_rows=[((z1 - z0) * 0.55, (z1 - z0) * 0.55 + 0.07)])
        us, vs = subdivide_lines([0, leaf_w], 0.05), subdivide_lines([0, z1 - z0], 0.2)
        yb = plane - 0.004                                       # back plane of the leaf, 4 mm off the stud faces
        V, F, C = relief_slab((xa, yb, z0), (1, 0, 0), (0, -1, 0), us, vs, thick, field.relief, field.back, colour_fn=field.colour, back_colour=shade(tone, 0.8), edge_colour=shade(tone, 0.7))
        hv = []
        for zc in (z0 + 0.12, z1 - 0.18):
            xs0, xs1 = (xa - 0.012, xa + 0.17) if side < 0 else (xa + leaf_w - 0.17, xa + leaf_w + 0.012)
            hv.append(box(xs0, xs1, yb - thick - 0.004, yb - thick + 0.002, zc, zc + 0.03))
        if ajar and side > 0:
            pivot = (xa + leaf_w, yb)
            ang = math.radians(72.0)
            V = rot_z(V, ang, pivot)
            hv = [(rot_z(hh[0], ang, pivot), hh[1]) for hh in hv]
        leaves.add(place_xy(V, facing, origin), F, C)
        for hh in hv:
            hinges.add(place_xy(hh[0], facing, origin), hh[1], vary(iron_col, rng, 0.2))
    return leaves, hinges


def merge_acc(dst, src):
    dst.V.extend(src.V)
    dst.F.extend([tuple(i + dst.n for i in f) for f in src.F])
    dst.C.extend(src.C)
    dst.n += src.n


def complete_cottage_A(B, c, ctx):
    rng, M, OAK, IRON = ctx['rng'], ctx['M'], ctx['OAK'], ctx['IRON']
    x0, x1, y0, y1, yc = ctx['x0'], ctx['x1'], ctx['y0'], ctx['y1'], ctx['yc']
    xt, DOOR_X, DOOR_POSTS = ctx['xt'], ctx['DOOR_X'], ctx['DOOR_POSTS']
    SILL_TOP, PL_BOT, PL_TOP, FOOT_H = ctx['SILL_TOP'], ctx['PL_BOT'], ctx['PL_TOP'], ctx['FOOT_H']
    opts = ctx['opts']

    # ---- earth floor inside the footing (top 5 cm above the ground), with a tongue out to the threshold
    acc = Acc()
    ex0, ex1, ey0, ey1 = x0 + 0.40, x1 - 0.40, y0 + 0.40, y1 - 0.40
    poly = [(ex0, ey0), (-32.487, ey0), (-32.487, y0 + 0.16), (-31.513, y0 + 0.16), (-31.513, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]
    V, F = extrude_z(poly, 0.0, 0.05)
    # a little unevenness in the top: 3 mm lumps on the interior vertices (the top ring only)
    n = len(poly)
    for i in range(n):
        V[n + i, 2] += 0.003 * (rng.random() - 0.5)
    acc.add(V, F, vary(hexl('#695842'), rng, 0.06))
    floor = B.emit(acc, 'earth floor', 'floor.earth', M['earth'])
    pk.seat_on_ground(floor)

    # ---- the doorstep: a flat stone, 14 cm high, between the door posts and a wider apron in front
    acc = Acc()
    ya = y0 - 0.45
    poly = [(-32.66, ya), (-31.34, ya), (-31.34, y0), (-31.513, y0), (-31.513, y0 + 0.16), (-32.487, y0 + 0.16), (-32.487, y0), (-32.66, y0)]
    # roughen only the outer corners
    poly[0] = (poly[0][0] + 0.02 * rng.random(), poly[0][1] - 0.02 * rng.random())
    poly[1] = (poly[1][0] - 0.02 * rng.random(), poly[1][1] - 0.02 * rng.random())
    V, F = extrude_z(poly, 0.0, 0.14)
    acc.add(V, F, vary(hexl('#8A867C'), rng, 0.06))
    step = B.emit(acc, 'doorstep', 'stone.step', M['stone'])
    pk.seat_on_ground(step)
    step_top = 0.14

    # ---- the door and its hinges
    leaf, hinges = make_door(B, rng, M['boards'], M['iron'], IRON, y0 + 0.05, DOOR_X - 0.425, 0.85, 1.70, 0.05, step_top + 0.004, -1, hexl('#8A6A45'), hexl('#6B5239'))
    B.emit(leaf, 'door leaf', 'timber.door', M['boards'])
    B.emit(hinges, 'door hinges', 'iron.fitting', M['iron'])

    # ---- the shuttered windows (two leaves each; one leaf of the second south window stands ajar)
    shut_tone, fresh = hexl('#5C4A36'), hexl('#8A6A45')
    allh = Acc()
    for k, (wx, wall, ajar) in enumerate(((-35.0, 'south', False), (-29.0, 'south', True), (-32.0, 'north', False))):
        facing = 'S' if wall == 'south' else 'N'
        origin = (wx, y0 + 0.01) if wall == 'south' else (wx, y1 - 0.01)
        leaves, hinges = make_shutters(rng, IRON, ajar, 0.95, 1.57, 0.255, shut_tone, fresh, facing, origin)
        B.emit(leaves, f'shutters {wall} window {k + 1}', 'timber.shutter', M['shutter'])
        merge_acc(allh, hinges)
    B.emit(allh, 'shutter hinges', 'iron.fitting', M['iron'])

    # ---- the roof frame: rafters, collars, purlins, ridge piece
    frame = build_roof_frame(c, rng, OAK, None)
    B.emit(frame['rafters'], 'rafters', 'timber.beam', M['oak'])
    B.emit(frame['collars'], 'collar beams', 'timber.beam', M['oak'])
    B.emit(frame['purlin_s'], 'purlin south', 'timber.beam', M['oak'])
    B.emit(frame['purlin_n'], 'purlin north', 'timber.beam', M['oak'])
    B.emit(frame['ridge'], 'ridge piece', 'timber.beam', M['oak'])
    # ---- the thatch: golden, thick, rolled at the eave, a darker ridge cap
    colour = thatch_colour_fn(int(ctx['seed']) + 21, hexl('#9C7A3F'), hexl('#B08C4A'), hexl('#7A5E30'), hexl('#6F8A3A'), hexl('#4F3F22'), hexl('#3E3222'), hexl('#C2A265'))
    V, F, C = build_thatch(c, rng, colour, roll=float(opts.get('thatch_roll', 1.3)), amp=0.028 * float(opts.get('thatch_lump', 1.25)), seed=ctx['seed'] + 3)
    acc = Acc()
    acc.add(V, F, C)
    B.emit(acc, 'thatch', 'roof.thatch', M['thatch'], smooth=True)

    build_lean_to(B, c, ctx)


def build_lean_to(B, c, ctx):
    """The log store on the west end: three posts on the ground carrying a plate, five rafters from the plate to a ledger let into the gable studs, a purlin, a shingle roof at 32 degrees, boards on
    the north side. Open to the south and to the west; EMPTY (the props part stacks the woodpile outside)."""
    rng, M, OAK, IRON = ctx['rng'], ctx['M'], ctx['OAK'], ctx['IRON']
    x0, y_s, y_n = ctx['x0'], 8.1, 11.5
    th = math.radians(33.0)
    tn, cs = math.tan(th), math.cos(th)
    z_p = 1.22                                              # top of the front plate
    d_b, d_a, r_d = 2.5, 2.36, 0.09
    rv = r_d / cs
    x_ref = x0                                              # d = distance west of the gable's outer plane

    def Ul(d):
        return z_p + tn * (d_b - d)

    def Tl(d):
        return Ul(d) + rv

    def xd(d):
        return x_ref - d
    # posts (on the ground), each its own object
    for k, yy in enumerate((y_s + 0.07, (y_s + y_n) / 2, y_n - 0.07)):
        acc = Acc()
        V, F = lofted_post(xd(2.43), yy, 0.0, z_p - 0.12, 0.14, 0.14, lean=((rng.random() - 0.5) * 0.03, (rng.random() - 0.5) * 0.03), twist=(rng.random() - 0.5) * 0.1, taper=0.9 + 0.08 * rng.random())
        acc.add(V, F, vary(OAK, rng, 0.2))
        o = B.emit(acc, f'lean-to post {("south", "middle", "north")[k]}', 'timber.post', M['oak'])
        pk.seat_on_ground(o)
    # plate (two sections, each between two posts)
    acc = Acc()
    mid = (y_s + y_n) / 2
    for ya, yb in ((y_s, mid - 0.005), (mid + 0.005, y_n)):
        poly = [(xd(d_b), z_p - 0.12), (xd(d_a - 0.02), z_p - 0.12), (xd(d_a - 0.02), z_p), (xd(d_b), z_p)]
        V, F = extrude_y(poly, ya, yb)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'lean-to plate', 'timber.beam', M['oak'])
    # ledger let into the gable studs, its top cut to the rafters' underside
    acc = Acc()
    poly = [(xd(0.075), Ul(0.075) - 0.14), (xd(-0.06), Ul(-0.06) - 0.14), (xd(-0.06), Ul(-0.06)), (xd(0.075), Ul(0.075))]
    V, F = extrude_y(poly, y_s, y_n)
    acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'lean-to ledger', 'timber.beam', M['oak'])
    # rafters
    acc = Acc()
    ys = [8.25, 9.0, 9.8, 10.6, 11.35]
    for yy in ys:
        w = 0.065 + 0.02 * rng.random()
        d_max = d_b + 0.22 + 0.1 * rng.random()
        poly = [(xd(0.0), Ul(0.0)), (xd(0.0), Tl(0.0)), (xd(d_max), Tl(d_max)), (xd(d_max), Ul(d_max)), (xd(d_b), z_p), (xd(d_a), z_p), (xd(d_a), Ul(d_a))]
        V, F = extrude_y(poly, yy - w / 2, yy + w / 2)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'lean-to rafters', 'timber.beam', M['oak'])
    # purlin let into the rafters 4.5 cm
    acc = Acc()
    pen, ph, pw = 0.02, 0.12, 0.10
    s_vec, n_vec = np.array([cs, -tn * cs]), np.array([tn * cs, cs])        # along the slope (outward and down), normal to it
    dpu = 1.35
    base = np.array([dpu, Ul(dpu)])
    pts = []
    for a, b in ((-pw / 2, -(ph - pen)), (pw / 2, -(ph - pen)), (pw / 2, pen), (-pw / 2, pen)):
        p = base + a * s_vec + b * n_vec
        pts.append((xd(p[0]), p[1]))
    V, F = extrude_y(pts, y_s + 0.05, y_n - 0.05)
    acc.add(V, F, vary(OAK, rng, 0.12))
    B.emit(acc, 'lean-to purlin', 'timber.beam', M['oak'])
    # shingle roof: a slab lying on the rafter tops (its back on the plane through the tops)
    W, L = (y_n - y_s) + 0.2, (d_b + 0.3) / cs
    field = ShingleField(int(ctx['seed']) + 77, W, L, [hexl('#6B5D4A'), hexl('#7A6B55'), hexl('#5F5547'), hexl('#85785F')], hexl('#2E261C'), hexl('#6F8A3A'))
    us, vs = subdivide_lines([0, W], 0.09), subdivide_lines([0, L], 0.09)
    e_n = np.array([-math.sin(th), 0.0, cs])
    e_u = np.array([0.0, 1.0, 0.0])
    e_v = np.cross(e_n, e_u)
    orig = np.array([xd(0.0), y_s - 0.1, Tl(0.0)])
    V, F, C = relief_slab(orig, e_u, e_n, us, vs, 0.045, field.relief, None, colour_fn=field.colour, back_colour=hexl('#3A2F22'), edge_colour=hexl('#4B3E2F'), e_v=e_v)
    acc = Acc()
    acc.add(V, F, C)
    B.emit(acc, 'lean-to shingle roof', 'roof.shingle', M['shingle'])
    # boards on the north side: upright boards on the ground, their tops cut to the underside of the roof slab
    acc = Acc()
    x_a, x_b = xd(d_b + 0.0), xd(0.02)
    xs = [x_a]
    while xs[-1] < x_b - 0.05:
        xs.append(xs[-1] + 0.15 + 0.03 * rng.random() + 0.004)
    xs[-1] = min(xs[-1], x_b)
    yb = y_n - 0.07 + 0.0
    fresh_i = int(rng.integers(2, len(xs) - 2))
    cols = []
    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1] - 0.004
        wdt = xb - xa
        top = lambda x, y: Tl(max(x_ref - x, 0.0)) - 0.003 - 0.0  # noqa: E731
        V, F = lofted_post((xa + xb) / 2, yb, 0.0, 1.0, wdt, 0.03, lean=(0, 0), twist=0.0, taper=1.0, top_z_fn=top)
        acc.add(V, F, vary(hexl('#6B5239') if i != fresh_i else hexl('#8A6A45'), rng, 0.15))
    B.emit(acc, 'lean-to boards', 'timber.plank', M['boards'])


# ------------------------------------------------------------------ COTTAGE B
def window_lining(rng, wood, centre_across, z0, z1, width_open, facing, origin, depth=0.20, proud=0.045):
    """A timber lining for a small window in a stone wall (no glass): a sill, two jambs and a head. Built facing south with the window centre at x = 0, the nominal outer plane at y = 0 and the
    frame standing `proud` outside it (so the shutters lie on flat faces), then placed on the wall. Returns an accumulator."""
    acc = Acc()
    wo = width_open / 2
    t = 0.05
    for (xa, xb, za, zb) in ((-wo - t, wo + t, z0, z0 + t), (-wo - t, -wo, z0 + t, z1 - t), (wo, wo + t, z0 + t, z1 - t), (-wo - t, wo + t, z1 - t, z1)):
        V, F = box(xa, xb, -proud, depth, za, zb)
        acc.add(place_xy(V, facing, origin), F, vary(wood, rng, 0.15))
    return acc


def build_chimney(rng, x_c, y_c, top, base_w=(1.04, 0.84), shaft=(0.90, 0.70), colour=None):
    """The stone chimney stack: a splayed base, a shaft of courses that each jut a little differently, a corbelled cap with a flue hollow. One closed piece from the ground to `top`."""
    courses = []
    z = 0.0
    courses.append((0.0, 0.34, base_w, x_c + 0.15))                 # the splayed base stands clear of the footing (no twin faces), the shaft is let 6 cm into the gable above it
    z = 0.34
    k = 0
    while z < top - 0.45:
        h = 0.26 + 0.18 * rng.random()
        h = min(h, top - 0.45 - z)
        taper = 1.0 - 0.07 * (z / top)
        courses.append((z, z + h, (shaft[0] * taper, shaft[1] * taper), x_c))
        z += h
    courses.append((z, top - 0.12, (shaft[0] * 0.93, shaft[1] * 0.93), x_c))
    courses.append((top - 0.12, top, (shaft[0] + 0.12, shaft[1] + 0.12), x_c))
    rings = []
    for (za, zb, (sy, sx), cxx) in courses:
        ring_a = ring_stone_course(cxx, y_c, za, zb, sx, sy, rng, jut=0.025)
        ring_b = [(px + (rng.random() - 0.5) * 0.008, py + (rng.random() - 0.5) * 0.008) for px, py in ring_a]
        rings.append([(px, py, za) for px, py in ring_a])
        rings.append([(px, py, zb) for px, py in ring_b])
    # the flue: an inner rim at the top and a hollow going down
    fx, fy = 0.30, 0.40
    rings.append([(x_c - fx / 2, y_c - fy / 2, top), (x_c + fx / 2, y_c - fy / 2, top), (x_c + fx / 2, y_c + fy / 2, top), (x_c - fx / 2, y_c + fy / 2, top)])
    rings.append([(x_c - fx / 2, y_c - fy / 2, top - 0.3), (x_c + fx / 2, y_c - fy / 2, top - 0.3), (x_c + fx / 2, y_c + fy / 2, top - 0.3), (x_c - fx / 2, y_c + fy / 2, top - 0.3)])
    V, F = loft_rings(rings)
    cols = []
    n_q = 4
    for m in range(len(rings) - 1):
        for k_ in range(n_q):
            base = vary(colour, rng, 0.07) if (m % 2 == 0) else colour
            cols.append(shade(base, 0.82) if m >= len(rings) - 3 else base)
    cols.append(colour)
    cols.append(shade(colour, 0.5))
    return V, F, cols


def build_cottage_B(opts):
    seed = int(opts.get('seed', 17))
    rng = np.random.default_rng(seed * 11 + 5)
    x0, x1, y0, y1 = -9.2, -2.8, 7.2, 11.8
    yc = 9.5
    g = ground_level(x0 - 0.2, -1.9, y0 - 0.6, y1 + 0.2)
    B = Builder('B', g)
    TIM, STONE_PAL = hexl('#5A4C40'), [hexl('#7C7A73'), hexl('#6E6C66'), hexl('#8A8880'), hexl('#5F5E58'), hexl('#74726B')]
    MOSS = hexl('#5F7A3A')
    M = dict(timber=make_material('Cottage B timber', 0.8), wall=make_material('Cottage B rubble', 0.9, displace=0.04), thatch=make_material('Cottage B thatch', 0.95, displace=0.05), footing=make_material('Cottage B footing stone', 0.85),
             boards=make_material('Cottage B boards', 0.8), iron=make_material('Cottage B iron', 0.6), earth=make_material('Cottage B earth', 0.95), shutter=make_material('Cottage B shutter wood', 0.8),
             chimney=make_material('Cottage B chimney stone', 0.9))
    IRON = hexl('#2E2E30')
    FOOT_H, WALL_TOP, WALL_T = 0.30, 2.10, 0.50
    PLATE_H = 0.12
    xt = [x0 + 0.62, -6.0, x1 - 0.62]
    c = Cot(x0=x0, x1=x1, y0=y0, y1=y1, Zp=WALL_TOP + PLATE_H, d_b=2.15, bw=0.14, r_d=0.10, xt=xt, sag_max=0.035 * float(opts.get('sag_cm', 1.0)), collar_z=4.05, collar_x=[xt[1]], d_p=1.15,
            px0=x0 + 0.52, px1=x1 - 0.52, rx0=x0 + 0.55, rx1=x1 - 0.55, tx0=x0, tx1=x1, t_n=0.35, overhang=0.40, rafter_x=[])
    for k in range(2):
        a, b = xt[k], xt[k + 1]
        n = int(round((b - a) / 0.8))
        for j in range(n):
            c.rafter_x.append((a + (b - a) * j / n, j == 0))
    c.rafter_x.append((xt[-1], True))

    # ---- footing: rubble strips under the walls (0.48 wide), the doorway left open
    acc = Acc()
    gap_lo, gap_hi = -6.62, -5.38
    fw = 0.48
    inset = (WALL_T - fw) / 2
    parts = [_footing_acc([((x0 + inset, gap_lo), (y0 + inset, y0 + inset + fw), 'x_long'), ((gap_hi, x1 - inset), (y0 + inset, y0 + inset + fw), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'south'),
             _footing_acc([((x0 + inset, x1 - inset), (y1 - inset - fw, y1 - inset), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'north'),
             _footing_acc([((x0 + inset, x0 + inset + fw), (y0 + inset + fw, y1 - inset - fw), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'west'),
             _footing_acc([((x1 - inset - fw, x1 - inset), (y0 + inset + fw, y1 - inset - fw), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'east')]
    for p in parts:
        merge_acc(acc, p)
    foot = B.emit(acc, 'footing', 'stone.footing', M['footing'])
    B.g += pk.seat_on_ground(foot)

    # ---- the rubble walls: big uneven blocks standing out of the face; the south wall has the doorway (with a rebate for the lintel) and a small window
    wall_specs = [
        ('south', (x0, y0 + WALL_T, FOOT_H), (1, 0, 0), (0, -1, 0), x1 - x0, [], [(2.65, 3.75, 0.0, 1.54), (2.35, 4.05, 1.54, 1.70), (0.95, 1.45, 0.70, 1.30)]),
        ('north', (x1, y1 - WALL_T, FOOT_H), (-1, 0, 0), (0, 1, 0), x1 - x0, [], []),
        ('west', (x0 + WALL_T, y1 - WALL_T, FOOT_H), (0, -1, 0), (-1, 0, 0), (y1 - y0) - 2 * WALL_T, [], []),
        ('east', (x1 - WALL_T, y0 + WALL_T, FOOT_H), (0, 1, 0), (1, 0, 0), (y1 - y0) - 2 * WALL_T, [], []),
    ]
    H = WALL_TOP - FOOT_H
    for name, orig, e_u, e_n, W, _unused, holes in wall_specs:
        if name == 'east':
            holes = [(2.8, 3.3, 0.70, 1.30)]
        sf = StoneField(int(rng.integers(1, 10 ** 6)), W, H, STONE_PAL, MOSS, big=1.0, amp=0.032)
        inner = StoneField(int(rng.integers(1, 10 ** 6)), W, H, STONE_PAL, MOSS, big=1.1, amp=0.012, moss_amount=0.0)
        must_u = [0.0, W] + [h for hh in holes for h in (hh[0], hh[1])]
        must_v = [0.0, H] + [h for hh in holes for h in (hh[2], hh[3])]
        us, vs = subdivide_lines(must_u, 0.07), subdivide_lines(must_v, 0.07)
        V, F, C = relief_slab(orig, e_u, e_n, us, vs, WALL_T, sf.relief, lambda U, V_, f=inner: 0.5 * f.relief(U, V_) + 0.01, holes=holes, colour_fn=sf.colour, back_colour=hexl('#6E6C66'), edge_colour=hexl('#5F5E58'))
        acc = Acc()
        acc.add(V, F, C)
        B.emit(acc, f'{name} wall', 'wall.stone', M['wall'], smooth=True)
    # ---- the two gables above the eaves: stone up to the underside of the thatch (a sloping top)
    for name, xo, e_u, e_n, y_start in (('west', x0, (0, 1, 0), (-1, 0, 0), y0), ('east', x1 - WALL_T, (0, 1, 0), (1, 0, 0), y0)):
        W = y1 - y0
        sf = StoneField(int(rng.integers(1, 10 ** 6)), W, 3.4, STONE_PAL, MOSS, big=1.0, amp=0.032)
        us = subdivide_lines([0.0, W], 0.08)
        vs = subdivide_lines([WALL_TOP, WALL_TOP + 3.0], 0.07)
        if name == 'west':
            orig, e_u_, e_n_ = (x0 + WALL_T, y1, 0.0), (0, -1, 0), (-1, 0, 0)
            yco = (lambda u: y1 - u)
        else:
            orig, e_u_, e_n_ = (x1 - WALL_T, y0, 0.0), (0, 1, 0), (1, 0, 0)
            yco = (lambda u: y0 + u)
        V, F, C = relief_slab(orig, e_u_, e_n_, us, vs, WALL_T, lambda U, V_, f=sf: f.relief(U, V_ - FOOT_H), lambda U, V_: 0.006 + 0.0 * U, colour_fn=lambda U, V_, R, f=sf: f.colour(U, V_ - FOOT_H, R),
                              back_colour=hexl('#6E6C66'), edge_colour=hexl('#5F5E58'), top_fn=lambda u: c.T(abs(yco(u) - yc)) - 0.003)
        acc = Acc()
        acc.add(V, F, C)
        B.emit(acc, f'{name} gable', 'wall.stone', M['wall'], smooth=True)
    # ---- quoin stones at the four corners: stacked blocks, long and short faces turn about
    acc = Acc()
    corners = [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]
    for cx, cy, sx, sy in corners:
        z = FOOT_H
        flip = int(rng.integers(0, 2))
        row = 0
        while z < WALL_TOP - 0.05:
            h = 0.25 + 0.09 * rng.random()
            h = min(h, WALL_TOP - z)
            if WALL_TOP - (z + h) < 0.18:
                h = WALL_TOP - z
            L, S = 0.44 + 0.2 * rng.random(), 0.30 + 0.06 * rng.random()
            along_x = ((row + flip) % 2 == 0)
            ax, ay = (L, S) if along_x else (S, L)
            xa, xb = (cx - 0.06, cx - 0.06 + ax) if sx > 0 else (cx + 0.06 - ax, cx + 0.06)          # 6 cm proud: past the highest stone of the wall face, so no faces share a plane
            ya, yb = (cy - 0.06, cy - 0.06 + ay) if sy > 0 else (cy + 0.06 - ay, cy + 0.06)
            V, F = stone_blob((xa + xb) / 2, (ya + yb) / 2, z, z + h, xb - xa, yb - ya, rng, wobble=0.05)
            acc.add(V, F, vary(hexl('#8E8B82'), rng, 0.08))
            z += h
            row += 1
    B.emit(acc, 'quoin stones', 'wall.stone', M['wall'])
    return B, c, dict(rng=rng, M=M, TIM=TIM, IRON=IRON, x0=x0, x1=x1, y0=y0, y1=y1, yc=yc, xt=xt, FOOT_H=FOOT_H, WALL_TOP=WALL_TOP, WALL_T=WALL_T, PLATE_H=PLATE_H, opts=opts, seed=seed, MOSS=MOSS)


def complete_cottage_B(B, c, ctx):
    rng, M, TIM, IRON = ctx['rng'], ctx['M'], ctx['TIM'], ctx['IRON']
    x0, x1, y0, y1, yc = ctx['x0'], ctx['x1'], ctx['y0'], ctx['y1'], ctx['yc']
    FOOT_H, WALL_TOP, WALL_T, PLATE_H = ctx['FOOT_H'], ctx['WALL_TOP'], ctx['WALL_T'], ctx['PLATE_H']
    opts = ctx['opts']
    DX = -6.0
    # ---- earth floor inside the walls
    acc = Acc()
    V, F = extrude_z([(x0 + WALL_T, y0 + WALL_T), (x1 - WALL_T, y0 + WALL_T), (x1 - WALL_T, y1 - WALL_T), (x0 + WALL_T, y1 - WALL_T)], 0.0, 0.05)
    for i in range(4):
        V[4 + i, 2] += 0.003 * (rng.random() - 0.5)
    acc.add(V, F, vary(hexl('#5E4E3A'), rng, 0.06))
    floor = B.emit(acc, 'earth floor', 'floor.earth', M['earth'])
    pk.seat_on_ground(floor)
    # ---- doorstep: an apron of flat stone in front, a neck through the doorway
    acc = Acc()
    ya = y0 - 0.5
    poly = [(DX - 0.92, ya), (DX + 0.92, ya), (DX + 0.92, y0), (DX + 0.432, y0), (DX + 0.432, y0 + WALL_T), (DX - 0.432, y0 + WALL_T), (DX - 0.432, y0), (DX - 0.92, y0)]
    poly[0] = (poly[0][0] + 0.03 * rng.random(), poly[0][1] - 0.02 * rng.random())
    poly[1] = (poly[1][0] - 0.03 * rng.random(), poly[1][1] - 0.02 * rng.random())
    V, F = extrude_z(poly, 0.0, 0.16)
    acc.add(V, F, vary(hexl('#8A867C'), rng, 0.06))
    step = B.emit(acc, 'doorstep', 'stone.step', M['footing'])
    pk.seat_on_ground(step)
    # ---- jamb posts (on the ground), lintel (resting on the rebate), door and hinges
    for sgn in (-1, 1):
        acc = Acc()
        xc = DX + sgn * 0.4925
        V, F = lofted_post(xc, y0 + 0.225, 0.0, 1.84, 0.115, 0.15, lean=((rng.random() - 0.5) * 0.012, 0.0), twist=(rng.random() - 0.5) * 0.04, taper=0.96)
        acc.add(V, F, vary(TIM, rng, 0.18))
        o = B.emit(acc, f'door post {"west" if sgn < 0 else "east"}', 'timber.post', M['timber'])
        pk.seat_on_ground(o)
    acc = Acc()
    V, F = box(DX - 0.85, DX + 0.85, y0 + 0.02, y0 + WALL_T - 0.02, 1.84, 2.00)
    acc.add(V, F, vary(TIM, rng, 0.12))
    B.emit(acc, 'lintel', 'timber.beam', M['timber'])
    leaf, hinges = make_door(B, rng, M['boards'], M['iron'], IRON, y0 + 0.20, DX - 0.425, 0.85, 1.65, 0.05, 0.16 + 0.004, -1, hexl('#7C6040'), hexl('#5E4B38'), hinge_z=(0.30, 1.30))
    B.emit(leaf, 'door leaf', 'timber.door', M['boards'])
    B.emit(hinges, 'door hinges', 'iron.fitting', M['iron'])
    # ---- the two small shuttered windows (0.4 x 0.5 clear), lined with timber so the shutters lie on flat faces
    shut_tone, fresh = hexl('#4F4236'), hexl('#7C6040')
    allh = Acc()
    for name, facing, origin, ajar in (('south', 'S', (-8.0, y0), True), ('east', 'E', (x1, 10.75), False)):
        lining = window_lining(rng, TIM, 0.0, 1.0, 1.6, 0.40, facing, origin)
        B.emit(lining, f'{name} window sill, jambs and head', 'timber.beam', M['timber'])
        leaves, hinges = make_shutters(rng, IRON, ajar, 1.02, 1.58, 0.215, shut_tone, fresh, facing, origin, plane=-0.045)
        B.emit(leaves, f'shutters {name} window', 'timber.shutter', M['shutter'])
        merge_acc(allh, hinges)
    B.emit(allh, 'shutter hinges', 'iron.fitting', M['iron'])
    # ---- wall plates on the stone tops (two sections each), the roof frame, the thatch
    acc = Acc()
    for xa, xb in ((x0 + WALL_T, -6.005), (-5.995, x1 - WALL_T)):
        for dd in (-1, 1):
            yy = yc + dd * 2.05
            V, F = bowed_bar_x(xa, xb, yy, 0.20, WALL_TOP, WALL_TOP + PLATE_H, (rng.random() - 0.5) * 0.014, ybow_phase=rng.random())
            acc.add(V, F, vary(TIM, rng, 0.15))
    B.emit(acc, 'wall plates', 'timber.beam', M['timber'])
    frame = build_roof_frame(c, rng, TIM, None)
    B.emit(frame['rafters'], 'rafters', 'timber.beam', M['timber'])
    B.emit(frame['collars'], 'collar beam', 'timber.beam', M['timber'])
    B.emit(frame['purlin_s'], 'purlin south', 'timber.beam', M['timber'])
    B.emit(frame['purlin_n'], 'purlin north', 'timber.beam', M['timber'])
    B.emit(frame['ridge'], 'ridge piece', 'timber.beam', M['timber'])
    colour = thatch_colour_fn(int(ctx['seed']) + 31, hexl('#6A6B50'), hexl('#5C5F45'), hexl('#46483A'), hexl('#62793A'), hexl('#3A402C'), hexl('#2F2A20'), hexl('#8D8A68'), moss_amount=0.8, north_moss=0.5)
    V, F, C = build_thatch(c, rng, colour, roll=float(opts.get('thatch_roll', 1.3)), amp=0.034 * float(opts.get('thatch_lump', 1.25)), seed=ctx['seed'] + 5)
    acc = Acc()
    acc.add(V, F, C)
    B.emit(acc, 'thatch', 'roof.thatch', M['thatch'], smooth=True)
    # ---- the chimney: from the ground, through the east gable, 1.2 m above the ridge
    ridge_top = float(c.T(0.0) + c.t_n / COS + 0.11)
    V, F, cols = build_chimney(rng, x1 + 0.29, yc, ridge_top + 1.2, colour=hexl('#76736B'))
    acc = Acc()
    acc.add(V, F, cols)
    chim = B.emit(acc, 'chimney', 'stone.chimney', M['chimney'])
    pk.seat_on_ground(chim)


# ------------------------------------------------------------------ the stage
def apply(options=None):
    """Makes cottage A and cottage B (see the note at the top). Idempotent: forgets what an earlier run of this owner made, then builds again with the same seed."""
    options = dict(options or {})
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    bpy.context.view_layer.update()
    made = {}
    for tag, build, complete in (('A', build_cottage_A, complete_cottage_A), ('B', build_cottage_B, complete_cottage_B)):
        B, c, ctx = build(options)
        complete(B, c, ctx)
        made[tag] = [o.name for o in B.objects]
    bpy.context.view_layer.update()
    total = sum(len(v) for v in made.values())
    print(f'COTTAGES_NORTH STAGE: objects created: {total} (A {len(made["A"])}, B {len(made["B"])}); changed: 0; deleted: 0 (apart from what an earlier run of this owner made)')
    return made
