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


# ------------------------------------------------------------------ materials (our own, with a small picture so the surface pass keeps them)
IMAGE_NAME = 'Cottages south variation'


def variation_image():
    """A small soft grey picture (values 0.45 to 1.0) that varies the colour and the roughness a little across every object. Colour space is set BEFORE the pixels are written."""
    size = 96
    img = bpy.data.images.get(IMAGE_NAME)
    if img is None or img.size[0] != size:
        if img is not None:
            bpy.data.images.remove(img)
        img = bpy.data.images.new(IMAGE_NAME, size, size, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rng = np.random.default_rng(5)
    f = np.fft.fft2(rng.normal(size=(size, size)))
    kx = np.fft.fftfreq(size)[:, None]
    ky = np.fft.fftfreq(size)[None, :]
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0
    field = np.real(np.fft.ifft2(f / (k ** 1.1)))
    field = (field - field.min()) / (field.max() - field.min())
    values = 0.45 + 0.55 * field
    pixels = np.ones((size, size, 4), dtype=np.float32)
    pixels[..., 0] = pixels[..., 1] = pixels[..., 2] = values
    img.pixels.foreach_set(pixels.ravel())
    img.update()
    try:
        img.pack()
    except RuntimeError:
        pass
    return img


def make_material(name, rough_low=0.7, rough_high=0.95, displace=None):
    """Colour = the mesh's Col layer times a gentle variation read from the small picture (object space, so no two objects match); roughness varies with the same picture."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    attr = tree.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'Col'
    attr.attribute_type = 'GEOMETRY'
    coord = tree.nodes.new('ShaderNodeTexCoord')
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (0.9, 0.9, 0.9)
    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.image = variation_image()
    tex.interpolation = 'Linear'
    tex.projection = 'BOX'
    tex.projection_blend = 0.3
    sep = tree.nodes.new('ShaderNodeSeparateColor')
    vary = tree.nodes.new('ShaderNodeMapRange')
    vary.inputs['From Min'].default_value = 0.45
    vary.inputs['From Max'].default_value = 1.0
    vary.inputs['To Min'].default_value = 0.9
    vary.inputs['To Max'].default_value = 1.1
    scale = tree.nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    rough = tree.nodes.new('ShaderNodeMapRange')
    rough.inputs['From Min'].default_value = 0.45
    rough.inputs['From Max'].default_value = 1.0
    rough.inputs['To Min'].default_value = rough_low
    rough.inputs['To Max'].default_value = rough_high
    L = tree.links.new
    L(coord.outputs['Object'], mapping.inputs['Vector'])
    L(mapping.outputs['Vector'], tex.inputs['Vector'])
    L(tex.outputs['Color'], sep.inputs['Color'])
    L(sep.outputs['Red'], vary.inputs['Value'])
    L(sep.outputs['Red'], rough.inputs['Value'])
    L(attr.outputs['Color'], scale.inputs[0])
    L(vary.outputs['Result'], scale.inputs['Scale'])
    L(scale.outputs['Vector'], bsdf.inputs['Base Color'])
    L(rough.outputs['Result'], bsdf.inputs['Roughness'])
    L(bsdf.outputs['BSDF'], out.inputs['Surface'])
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.25
    except KeyError:
        pass
    out.is_active_output = True
    if displace:
        # real displacement for the thatch (the role asks for it): the picture read at a finer tile, mid level 0.5, scale = the true depth in metres
        from place_kit.surfaces import displacement as disp
        map2 = tree.nodes.new('ShaderNodeMapping')
        map2.inputs['Scale'].default_value = (4.5, 4.5, 4.5)
        tex2 = tree.nodes.new('ShaderNodeTexImage')
        tex2.image = tex.image
        tex2.projection = 'BOX'
        tex2.projection_blend = 0.3
        sep2 = tree.nodes.new('ShaderNodeSeparateColor')
        L(coord.outputs['Object'], map2.inputs['Vector'])
        L(map2.outputs['Vector'], tex2.inputs['Vector'])
        L(tex2.outputs['Color'], sep2.inputs['Color'])
        disp.set_displacement(mat, sep2.outputs['Red'], displace, tree)
    mat['cs_made'] = 1
    return mat


# ------------------------------------------------------------------ the parts registry
class Parts:
    """The objects of the part, by key: each has an accumulator, a name, a role (its role is given as it is made) and a flag for seating on the ground."""

    def __init__(self):
        self.d = {}
        self.order = []

    def acc(self, key, name, role, smooth=False, seat=False):
        if key not in self.d:
            self.d[key] = dict(acc=Acc(smooth=smooth), name=name, role=role, seat=seat)
            self.order.append(key)
        return self.d[key]['acc']


def wbox(wall, u0, u1, w0, w1, z0, z1):
    """A box in a wall's own frame (u along, w across, z up) as ONE closed solid."""
    pts = [wall.P(u, w, z) for (u, w, z) in ((u0, w0, z0), (u1, w0, z0), (u1, w1, z0), (u0, w1, z0), (u0, w0, z1), (u1, w0, z1), (u1, w1, z1), (u0, w1, z1))]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array(pts, float), F


def post_solid(wall, u, w, a, b, z0, z1, lean=(0.0, 0.0), bow=(0.0, 0.0), twist=0.0, taper=1.0, topz=None):
    """A post or stud in a wall's frame: three rings (foot, middle, head), leaning by `lean` (metres of drift at the head), bowing by `bow` at the middle, turned by `twist` radians at the head
    and narrowing by `taper`. topz(world xy corners) may give each head corner its own height (a head cut to the slope of a rafter)."""
    rings = []
    for t in (0.0, 0.5, 1.0):
        z = z0 + (z1 - z0) * t
        cu = u + lean[0] * t + bow[0] * math.sin(math.pi * t)
        cw = w + lean[1] * t + bow[1] * math.sin(math.pi * t)
        s = 1.0 + (taper - 1.0) * t
        ang = twist * t
        ca, sa = math.cos(ang), math.sin(ang)
        corners = []
        for du, dw in ((a * s, -b * s), (a * s, b * s), (-a * s, b * s), (-a * s, -b * s)):
            corners.append((cu + ca * du - sa * dw, cw + sa * du + ca * dw))
        ring = np.array([wall.P(cu_, cw_, z) for cu_, cw_ in corners])
        if t == 1.0 and topz is not None:
            ring[:, 2] = [topz(p[0], p[1]) for p in ring]
        rings.append(ring)
    return loft(rings)


def stud_at(stud, z):
    """(centre u, centre w) of a stud at height z (its lean is a straight drift from foot to head)."""
    t = (z - stud['z0']) / (stud['z1'] - stud['z0'])
    return stud['u'] + stud['lean'][0] * t, stud['w'] + stud['lean'][1] * t


# ------------------------------------------------------------------ shared builders for both cottages
def ground_top(x0, x1, y0, y1):
    """The highest ground under a rectangle (read on a grid of 5 x 5 points) and the lowest."""
    hs = [pk.ground_height_at(x, y) for x in np.linspace(x0, x1, 5) for y in np.linspace(y0, y1, 5)]
    return max(hs), min(hs)


def stone_solid(cx, cy, L, Wd, rot, zb, zt, rng, chamfer=(0.05, 0.10)):
    """A rubble stone: four rings of a chamfered rectangle (bulging a little in the middle, jittered), flat on top at height zt so a sill can lie on it."""
    hx, hy = L / 2, Wd / 2
    c = rng.uniform(*chamfer)
    base = np.array([(hx, -hy + c), (hx, hy - c), (hx - c, hy), (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c), (-hx + c, -hy), (hx - c, -hy)])
    zs = [zb, zb + 0.30 * (zt - zb), zb + 0.72 * (zt - zb), zt]
    scales = [0.90, 1.03, 1.00, 0.95]
    rings = []
    for z, s in zip(zs, scales):
        pts = base * s + rng.uniform(-0.012, 0.012, size=base.shape)
        ring = np.c_[pts[:, 0] + cx, pts[:, 1] + cy, np.full(8, z)]
        rings.append(rot_z(ring, rot, (cx, cy)))
    return loft(rings)


def stone_colour(base, g, factor, moss=0.0):
    moss_c = hexl('#5E7040')

    def fn(V):
        c = shade(np.tile(base, (len(V), 1)), factor)
        low = smoothstep(g + 0.16, g - 0.02, V[:, 2]) * (0.22 + moss)
        return mixc(c, moss_c, low)
    return fn


def bar_solid(wall, u0, u1, wc, hwid, z0, z1, bow=0.003, taper=1.0, stations=3, twist=0.0):
    """A straight timber lying along a wall (u from u0 to u1) with a flat top and bottom (z0, z1), a slight bow in plan, centred across at wc with half width hwid."""
    rings = []
    for k in range(stations):
        t = k / (stations - 1)
        u = u0 + (u1 - u0) * t
        cw = wc + bow * math.sin(math.pi * t)
        h = hwid * (1.0 + (taper - 1.0) * t)
        rings.append(np.array([wall.P(u, cw - h, z0), wall.P(u, cw + h, z0), wall.P(u, cw + h, z1), wall.P(u, cw - h, z1)]))
    return loft(rings)


def oak(rng, base, spread=0.16):
    return shade(base, rng.uniform(1 - spread, 1 + spread * 0.7))


def daub_panel(wall, uL, uR, z0, z1, rng, noise, colours, chip=None, wf0=0.050, wb=-0.050, cell=0.11):
    """A daub panel between two studs, as ONE closed solid: a flat back (w = wb) and a front surface (w about wf0) with soft lumps, a recess at the borders, and, where `chip` says
    (u centre, z centre, u radius, z radius), a ragged chip where the render has fallen off and only the core is left. uL and uR are functions of z (the stud faces, pushed 1.5 cm
    into the studs); z1 may be a number or a function of u. Returns (V, F, colour array, chip mask of the front vertices)."""
    zmid = z0 + 0.5 * ((z1(0.5 * (uL(z0) + uR(z0))) if callable(z1) else z1) - z0)
    width = float(uR(zmid) - uL(zmid))
    top_mid = z1(0.5 * (uL(zmid) + uR(zmid))) if callable(z1) else z1
    nu = max(2, int(round(width / cell)))
    nz = max(2, int(round((top_mid - z0) / (cell * 1.2))))
    Fg = np.zeros((nu + 1, nz + 1, 3))
    Bg = np.zeros((nu + 1, nz + 1, 3))
    col_f = np.zeros((nu + 1, nz + 1, 4))
    mask = np.zeros((nu + 1, nz + 1))
    uLn, uRn = uL(zmid), uR(zmid)
    for j in range(nz + 1):
        tj = j / nz
        for i in range(nu + 1):
            si = i / nu
            un = uLn + si * (uRn - uLn)
            top = z1(un) if callable(z1) else z1
            z = z0 + tj * (top - z0)
            u = uL(z) + si * (uR(z) - uL(z))
            edge = min(si * width, (1 - si) * width, (z - z0), (top - z)) if (top - z0) > 0.0 else 0.0
            wf = wf0 + 0.007 * noise.value(u * 2.1, z * 2.1, 0.3) - 0.014 * (1 - smoothstep(0.0, 0.07, edge))
            if chip is not None:
                uc, zc, ru, rz = chip
                r = math.hypot((u - uc) / ru, (z - zc) / rz) * (1 + 0.28 * noise.value(u * 5.3, z * 5.3, 1.7))
                m = float(smoothstep(1.0, 0.72, r))
                mask[i, j] = m
                wf = wf * (1 - m) + (0.004 + 0.006 * noise.value(u * 7, z * 7, 2.2)) * m
            Fg[i, j] = wall.P(u, wf, z)
            Bg[i, j] = wall.P(u, wb, z)
    return Fg, Bg, mask


def lean_for(rng, scale, big=False):
    mag = (rng.uniform(0.010, 0.019) if big else rng.uniform(0.002, 0.010)) * scale
    ang = rng.uniform(0, 2 * math.pi)
    return (mag * math.cos(ang), mag * math.sin(ang))


def plank_leaf(wall, u0, u1, wback, thick, z0, z1, widths, rng, base, fresh, replaced, bow=0.004, ledges=(), ledge_thick=0.022, groove=0.010):
    """A plank leaf (door or shutter) as ONE closed solid: vertical planks of the given widths with a groove between them, a bow, and ledges on the back (z ranges relative to z0).
    replaced: plank numbers in a fresher colour. Returns (V, F, colours)."""
    n = len(widths)
    ws = np.array(widths, float)
    ws = ws / ws.sum() * (u1 - u0)
    edges = u0 + np.concatenate([[0.0], np.cumsum(ws)])
    wf = [wback + thick + rng.uniform(-0.002, 0.002) + (0.003 if k in replaced else 0.0) for k in range(n)]
    plank_col = []
    for k in range(n):
        c = fresh if k in replaced else base
        plank_col.append(shade(c, rng.uniform(0.86, 1.1)))
    # the profile loop: back left, back right, then the front from right to left
    prof, pcol = [], []
    back_col = shade(base, 0.8)
    prof.append((edges[0], 0.0, -1))
    prof.append((edges[-1], 0.0, -1))
    for k in range(n - 1, -1, -1):
        prof.append((edges[k + 1] - 0.004, wf[k] - wback, k))
        prof.append((edges[k] + 0.004, wf[k] - wback, k))
        if k > 0:
            prof.append((edges[k], min(wf[k], wf[k - 1]) - wback - groove, k))
    levels = [(0.0, 0.0)]
    for a, b in ledges:
        levels += [(a, 0.0), (a, ledge_thick), (b, ledge_thick), (b, 0.0)]
    levels.append((z1 - z0, 0.0))
    rings, cols = [], []
    for zrel, led in levels:
        t = zrel / (z1 - z0)
        shift = bow * math.sin(math.pi * t)
        pts = []
        for (u, w, k) in prof:
            w_here = wback + w + shift - (led if k == -1 else 0.0)
            pts.append(wall.P(u, w_here, z0 + zrel))
        rings.append(np.array(pts))
        cols.append(np.array([back_col if k == -1 else plank_col[k] for (_, _, k) in prof]))
    V, F = loft(rings)
    return V, F, np.vstack(cols)


def hinge_set(acc, wall, u_hinge, direction, wf_top, z_list, length, thick=0.012, pin_in=0.022, wback=0.0, col=None):
    """Iron hinges: for each height a strap lying on the front of the leaf (from the hinge edge `length` along `direction`) and a pintle block straddling the gap between the leaf edge and the post."""
    for z in z_list:
        strap = wbox(wall, min(u_hinge, u_hinge + direction * length), max(u_hinge, u_hinge + direction * length), wf_top, wf_top + thick - 0.001, z - 0.022, z + 0.022)
        acc.add(*strap, col=col)
        pa, pb = u_hinge - direction * 0.035, u_hinge + direction * 0.012
        pin = wbox(wall, min(pa, pb), max(pa, pb), wback, wf_top + thick + 0.003, z - 0.03, z + 0.03)
        acc.add(*pin, col=col)


# ------------------------------------------------------------------ cottage C
def build_C(parts, o):
    """Cottage C: timber frame with red-ochre daub, pale thatch at 50 degrees, a tall door in the north wall. Returns a dict of facts (sizes, counts) for the report."""
    rng = np.random.default_rng(o['seed'] + 101)
    noise = Noise(o['seed'] + 7)
    noise2 = Noise(o['seed'] + 8, scales=(1.3, 0.6, 0.3))
    X0, X1, Y0, Y1 = -29.7, -22.3, -12.8, -8.2
    hw = 0.07
    xw0, xw1, yw0, yw1 = X0 + hw, X1 - hw, Y0 + hw, Y1 - hw
    xm, yc = -26.0, -10.5
    LX, LY = xw1 - xw0, yw1 - yw0
    hp = yw1 - yc
    g, g_low = ground_top(X0 - 0.3, X1 + 0.3, Y0 - 0.3, Y1 + 0.3)
    ztf = g + 0.32
    zsb = ztf + 0.001
    zst = zsb + 0.15
    zpb = g + 2.06
    zpt = g + 2.2
    ZS = g + 2.2
    TAN, COS, SIN = math.tan(math.radians(50)), math.cos(math.radians(50)), math.sin(math.radians(50))
    WN = Wall((xw0, yw1), (1, 0), (0, 1), LX)
    WS = Wall((xw0, yw0), (1, 0), (0, -1), LX)
    WW = Wall((xw0, yw0), (0, 1), (-1, 0), LY)
    WE = Wall((xw1, yw0), (0, 1), (1, 0), LY)
    OAK = hexl('#33281F')
    DAUB = shade(tone3(hexl(o['daub_hex']), hexl('#8A4A3A'), hexl('#A5603E'), o['daub_tone']), o['daub_value'])
    MUD, CLAY = hexl('#5A3D2C'), hexl('#8C7050')
    WEATHER, FRESH = hexl('#5A4C40'), hexl('#8A6A45')
    IRON = hexl('#2A2826')
    STONE = hexl('#7C7A73')
    WATTLE = hexl('#5E4A33')
    facts = dict(g=g, g_low=g_low)

    # ---- footing: rubble stones, flat on top at one height, sunk into the pad, left out under the door
    foot = parts.acc('footC', 'Cottage C footing', 'stone.footing', seat=0.03)

    def fill(start, end):
        pos, out = start, []
        while end - pos > 0.05:
            L = rng.uniform(0.45, 0.85)
            if end - pos - L < 0.38:
                L = end - pos
            out.append((pos + L / 2, L - 0.02))
            pos += L
        return out
    door_u0, door_u1 = -26.5, -25.5
    runs = []
    for (a, b) in ((xw0 - 0.21, door_u0), (door_u1, xw1 + 0.21)):
        for c, L in fill(a, b):
            runs.append((c, yw1, L, 0.0))
    for c, L in fill(xw0 - 0.21, xw1 + 0.21):
        runs.append((c, yw0, L, 0.0))
    for c, L in fill(yw0 + 0.21 + 0.015, yw1 - 0.21 - 0.015):
        runs.append((xw0, c, L, math.pi / 2))
        runs.append((xw1, c, L, math.pi / 2))
    for (cx, cy, L, rot) in runs:
        if rot == 0.0:
            cx, cy = cx, cy + rng.uniform(-0.012, 0.012)
        else:
            cx, cy = cx + rng.uniform(-0.012, 0.012), cy
        width = rng.uniform(0.38, 0.46)
        zb = pk.ground_height_at(cx, cy) - 0.03
        V, F = stone_solid(cx, cy, L, width, rot, zb, ztf, rng)
        foot.add(V, F, col=stone_colour(STONE, g, rng.uniform(0.80, 1.12)))

    # ---- sill timbers (the north sill is cut at the door; the east and west sills lie between the north and south ones)
    sill = parts.acc('sillC', 'Cottage C sill', 'timber.beam')
    sill_cols = lambda: oak(rng, OAK)  # noqa: E731
    dl = -26.45 - xw0
    dr = -25.55 - xw0
    for wall, u0, u1 in ((WN, -0.075, dl), (WN, dr, LX + 0.075), (WS, -0.075, LX / 2 - 0.0075), (WS, LX / 2 + 0.0075, LX + 0.075), (WW, 0.078, LY - 0.078), (WE, 0.078, LY - 0.078)):
        hwid = 0.075 + rng.uniform(-0.004, 0.004)
        V, F = bar_solid(wall, u0, u1, 0.0, hwid, zsb, zst, bow=rng.uniform(-0.004, 0.004), taper=rng.uniform(0.97, 1.0))
        sill.add(V, F, col=sill_cols())

    # ---- the corner posts (four objects: the kit leans a post about its own foot, so each stands alone)
    corner_info = {}
    for tag, wall, u in (('NW', WN, 0.0), ('NE', WN, LX), ('SW', WS, 0.0), ('SE', WS, LX)):
        a = rng.uniform(0.072, 0.082)
        b = rng.uniform(0.072, 0.080)
        lean = lean_for(rng, o['lean'], big=True)
        acc = parts.acc('postC' + tag, 'Cottage C post ' + tag, 'timber.post')
        V, F = post_solid(wall, u, 0.0, a, b, zst + 0.001, zpb - 0.001, lean=lean, bow=(rng.uniform(-0.004, 0.004), rng.uniform(-0.004, 0.004)),
                          twist=rng.uniform(-0.03, 0.03), taper=rng.uniform(0.94, 0.99))
        acc.add(V, F, col=oak(rng, OAK))
        corner_info[tag] = dict(a=a, b=b, lw=lean[0] * wall.eu[:2] + lean[1] * wall.ew[:2])

    def corner_rec(tag, wall, u):
        ci = corner_info[tag]
        aa, bb = (ci['a'], ci['b']) if wall in (WN, WS) else (ci['b'], ci['a'])
        lean = (float(ci['lw'] @ wall.eu[:2]), float(ci['lw'] @ wall.ew[:2]))
        return dict(u=u, w=0.0, a=aa, b=bb, kind='corner', lean=lean, win=None, z0=zst + 0.001, z1=zpb - 0.001)

    # ---- the wall frames
    studs = parts.acc('studsC', 'Cottage C studs', 'timber.beam')
    rails = parts.acc('railsC', 'Cottage C rails', 'timber.beam')
    door_posts = parts.acc('doorpostsC', 'Cottage C door posts', 'timber.post')
    win_acc = {1: parts.acc('wpostsC1', 'Cottage C window posts 1', 'timber.post'), 2: parts.acc('wpostsC2', 'Cottage C window posts 2', 'timber.post'),
               3: parts.acc('wpostsC3', 'Cottage C loft window studs', 'timber.beam')}
    panel_specs = []
    window_info = {}

    def make_rec(u, kind, win=None, z0=zst + 0.001, z1=zpb - 0.001, topz=None, a=None, big=False):
        a_ = a if a is not None else (rng.uniform(0.052, 0.060) if kind == 'stud' else 0.055 if kind == 'jamb' else 0.052)
        b_ = rng.uniform(0.068, 0.074)
        lean = lean_for(rng, o['lean'] * (0.5 if kind in ('wpost', 'jamb') else 1.0), big=big)
        rec = dict(u=u, w=0.0, a=a_, b=b_, kind=kind, lean=lean, win=win, z0=z0, z1=z1, topz=topz)
        V, F = post_solid(WALLS_CUR[0], u, 0.0, a_, b_, z0, z1, lean=lean, bow=(0, 0), twist=0.0, taper=1.0, topz=topz)
        if kind == 'stud':
            studs.add(V, F, col=oak(rng, OAK))
        elif kind == 'jamb':
            door_posts.add(V, F, col=oak(rng, OAK))
        else:
            win_acc[win].add(V, F, col=oak(rng, OAK))
        return rec
    WALLS_CUR = [None]

    def frame_wall(wall, name, recs, rail_fn, ztop_fn=None, zbot=zst + 0.003, ztop_const=None, door=None):
        """recs: vertical records from one end to the other (the first and last are corner or edge records). rail_fn(bay_kind, left, right) gives the rail levels [(z0, z1, opening_after)]."""
        for i in range(len(recs) - 1):
            left, right = recs[i], recs[i + 1]
            kind = 'door' if (left['kind'] == 'jamb' and right['kind'] == 'jamb') else 'window' if (left.get('win') and left.get('win') == right.get('win')) else 'plain'
            if kind == 'door':
                zl0, zl1 = g + 1.985, zpb - 0.001
                zm = 0.5 * (zl0 + zl1)
                ul = stud_at(left, zm)[0] + left['a'] - 0.085
                ur = stud_at(right, zm)[0] - right['a'] + 0.085
                V, F = wbox(wall, ul, ur, -0.06, 0.06, zl0, zl1)
                rails.add(V, F, col=oak(rng, OAK))
                window_info.setdefault(name + 'door', dict(u0=stud_at(left, zm)[0] + left['a'], u1=stud_at(right, zm)[0] - right['a'], zlintel=zl0))
                continue
            levels = rail_fn(kind, left, right)
            pen = 0.075 if kind == 'window' else 0.043
            for (rz0, rz1, opening) in levels:
                zm = 0.5 * (rz0 + rz1)
                ul = stud_at(left, zm)[0] + left['a'] - pen
                ur = stud_at(right, zm)[0] - right['a'] + pen
                V, F = wbox(wall, ul, ur, -0.06, 0.06, rz0, rz1)
                rails.add(V, F, col=oak(rng, OAK))
            # panels are the spaces between the rails, except the opening of a window
            spans = []
            cur = zbot
            skip_next = False
            for (rz0, rz1, opening) in levels:
                if not skip_next:
                    spans.append((cur, rz0 - 0.003))
                cur = rz1 + 0.003
                skip_next = opening
            spans.append((cur, None))
            for (zb, zt_) in spans:
                top = zt_ if zt_ is not None else (ztop_fn if ztop_fn is not None else ztop_const)
                if not callable(top) and top - zb < 0.08:
                    continue
                panel_specs.append(dict(wall=wall, left=left, right=right, z0=zb, z1=top, name=name, kind=kind))

    # south, west and east walls: plain bays with one mid rail
    mid_rail = lambda kind, l, r: [(g + 1.25, g + 1.35, False)]  # noqa: E731

    def plain_recs(wall, length, bays, c0, c1, base_u):
        recs = [c0]
        us = [length * k / bays for k in range(1, bays)]
        for u in us:
            WALLS_CUR[0] = wall
            recs.append(make_rec(u + rng.uniform(-0.03, 0.03), 'stud'))
        recs.append(c1)
        return recs

    WALLS_CUR[0] = WS
    recs = plain_recs(WS, LX, 9, corner_rec('SW', WS, 0.0), corner_rec('SE', WS, LX), 0)
    frame_wall(WS, 'S', recs, mid_rail, ztop_const=zpb - 0.003)
    WALLS_CUR[0] = WW
    recs = plain_recs(WW, LY, 6, corner_rec('SW', WW, 0.0), corner_rec('NW', WW, LY), 0)
    frame_wall(WW, 'W', recs, mid_rail, ztop_const=zpb - 0.003)
    WALLS_CUR[0] = WE
    recs = plain_recs(WE, LY, 6, corner_rec('SE', WE, 0.0), corner_rec('NE', WE, LY), 0)
    frame_wall(WE, 'E', recs, mid_rail, ztop_const=zpb - 0.003)

    # north wall: two windows and the door
    WALLS_CUR[0] = WN
    win_x = {1: -28.2, 2: -23.8}
    xs_n = [(-29.05, 'stud', None), (win_x[1] - 0.277, 'wpost', 1), (win_x[1] + 0.277, 'wpost', 1), (-27.25, 'stud', None), (-26.505, 'jamb', None),
            (-25.495, 'jamb', None), (-24.85, 'stud', None), (win_x[2] - 0.277, 'wpost', 2), (win_x[2] + 0.277, 'wpost', 2), (-22.9, 'stud', None)]
    recs = [corner_rec('NW', WN, 0.0)]
    for x, kind, win in xs_n:
        jitter = rng.uniform(-0.02, 0.02) if kind == 'stud' else 0.0
        recs.append(make_rec(x - xw0 + jitter, kind, win=win))
    recs.append(corner_rec('NE', WN, LX))

    def north_rails(kind, l, r):
        if kind == 'window':
            return [(g + 0.90, g + 1.00, True), (g + 1.60, g + 1.70, False)]
        return [(g + 1.25, g + 1.35, False)]
    frame_wall(WN, 'N', recs, north_rails, ztop_const=zpb - 0.003)
    for w in (1, 2):
        window_info[w] = dict(u=win_x[w] - xw0, z0=g + 1.00, z1=g + 1.60, wall=WN)

    # ---- gable walls above the gable plates: studs, rails, panels up to the principal rafters
    def zin(x, y):
        h = abs(y - yc)
        return ZS + (hp - h) * TAN - 0.16 / COS - 0.002

    def gable(wall, name, rels, loft_window=False):
        top_u = lambda u: max(zin(0.0, yw0 + u) - 0.003, zpt + 0.03)  # noqa: E731
        WALLS_CUR[0] = wall
        edge_l = dict(u=(yc - 2.09) - yw0, w=0.0, a=0.0, b=0.0, kind='edge', lean=(0.0, 0.0), win=None, z0=zpt, z1=zpt + 1.0)
        edge_r = dict(u=(yc + 2.09) - yw0, w=0.0, a=0.0, b=0.0, kind='edge', lean=(0.0, 0.0), win=None, z0=zpt, z1=zpt + 1.0)
        recs_g = [edge_l]
        for rel, kind, win in rels:
            u = yc + rel - yw0
            topz = lambda x, y: zin(x, y)  # noqa: E731
            rec = make_rec(u + (rng.uniform(-0.02, 0.02) if kind == 'stud' else 0.0), kind, win=win, z0=zpt + 0.001, z1=zin(0, yc + rel), topz=topz)
            recs_g.append(rec)
        recs_g.append(edge_r)

        def gable_rails(kind, l, r):
            ztops = [min(top_u(stud_at(l, zpt)[0] + l['a']), top_u(stud_at(r, zpt)[0] - r['a']))]
            if kind == 'window':
                return [(g + 2.95, g + 3.05, True), (g + 3.55, g + 3.65, False)]
            if ztops[0] > g + 3.10:
                return [(g + 2.95, g + 3.05, False)]
            return []
        frame_wall(wall, name, recs_g, gable_rails, ztop_fn=top_u, zbot=zpt + 0.003)
        return recs_g

    gw_rels = [(-1.5, 'stud', None), (-0.9, 'stud', None), (-0.3, 'stud', None), (0.3, 'stud', None), (0.9, 'stud', None), (1.5, 'stud', None)]
    ge_rels = [(-1.65, 'stud', None), (-0.95, 'stud', None), (-0.277, 'wpost', 3), (0.277, 'wpost', 3), (0.95, 'stud', None), (1.65, 'stud', None)]
    gable(WW, 'GW', gw_rels)
    gable(WE, 'GE', ge_rels, loft_window=True)
    window_info[3] = dict(u=(yc - yw0), z0=g + 3.05, z1=g + 3.55, wall=WE)

    # ---- gable plates (flat, between the long plates) and the long wall plates (wedge seat cut to the roof slope)
    plate = parts.acc('plateC', 'Cottage C wall plate', 'timber.beam')
    for wall in (WW, WE):
        V, F = wbox(wall, 0.083, LY - 0.083, -0.07, 0.07, zpb, zpt)
        plate.add(V, F, col=oak(rng, OAK))

    SAG = [rng.uniform(0.026, 0.034) * o['sag'], rng.uniform(0.032, 0.040) * o['sag']]
    xt = [xw0, xm, xw1]

    def sag_fn(x):
        x = np.asarray(x, float)
        out = np.zeros_like(x)
        for k in range(2):
            m = (x >= xt[k]) & (x <= xt[k + 1])
            out[m] = SAG[k] * np.sin(np.pi * (x[m] - xt[k]) / (xt[k + 1] - xt[k]))
        return out

    def zU(x, h):
        return ZS + (hp - h) * TAN - sag_fn(x) * (1 - h / hp)

    def slope(x):
        return -TAN + sag_fn(x) / hp

    def nvec(x, s):
        m = float(slope(x))
        n = np.array([0.0, s * (-m), 1.0])
        return n / np.linalg.norm(n)

    for s in (1, -1):
        for (xa, xb) in ((X0, xm - 0.008), (xm + 0.008, X1)):
            rings = []
            for x in np.linspace(xa, xb, 7):
                hi, ho = hp - 0.08, hp + 0.08
                pts = [(yc + s * hi, zpb), (yc + s * ho, zpb), (yc + s * ho, float(zU(x, ho))), (yc + s * hi, float(zU(x, hi)))]
                rings.append(np.array([(x, p[0], p[1]) for p in pts]))
            V, F = loft(rings)
            plate.add(V, F, col=oak(rng, OAK))

    # ---- rafters: common rafters on the plate, the purlin and the ridge; principal rafters at the three truss lines
    rafters = parts.acc('raftersC', 'Cottage C rafters', 'timber.beam')
    principals = parts.acc('principalsC', 'Cottage C principal rafters', 'timber.beam')

    def roof_beam(x, s, ha, hb, width, d_lo, d_hi):
        n = nvec(x, s)
        ex = np.array([1.0, 0.0, 0.0])
        rings = []
        for h in (ha, hb):
            L = np.array([x, yc + s * h, float(zU(x, h))])
            rings.append(np.array([L - ex * width / 2 + n * d_lo, L + ex * width / 2 + n * d_lo, L + ex * width / 2 + n * d_hi, L - ex * width / 2 + n * d_hi]))
        return loft(rings)
    h_edge = hp + hw + 0.5
    rafter_x = []
    for k in range(2):
        for i in range(1, 6):
            rafter_x.append(xt[k] + (xt[k + 1] - xt[k]) * i / 6 + rng.uniform(-0.025, 0.025))
    for x in rafter_x:
        for s in (1, -1):
            V, F = roof_beam(x + rng.uniform(-0.01, 0.01), s, h_edge, 0.03, rng.uniform(0.082, 0.098), 0.0, 0.09)
            rafters.add(V, F, col=oak(rng, WEATHER, 0.12))
    for x in xt:
        for s in (1, -1):
            V, F = roof_beam(x, s, hp, 0.03, 0.14, -0.16, 0.004)
            principals.add(V, F, col=oak(rng, WEATHER, 0.1))

    # purlins: one on each slope, butted between the principal rafters (a bay each)
    purlins = parts.acc('purlinsC', 'Cottage C purlins', 'timber.beam')
    hpur = 1.15
    for s in (1, -1):
        for k in range(2):
            xa, xb = xt[k] + 0.02, xt[k + 1] - 0.02
            rings = []
            for x in np.linspace(xa, xb, 9):
                n = nvec(x, s)
                dh = 0.06 * math.cos(math.atan(abs(float(slope(x)))))
                o1 = np.array([x, yc + s * (hpur - dh), float(zU(x, hpur - dh))])
                o2 = np.array([x, yc + s * (hpur + dh), float(zU(x, hpur + dh))])
                rings.append(np.array([o1, o2, o2 - n * 0.12, o1 - n * 0.12]))
            V, F = loft(rings)
            purlins.add(V, F, col=oak(rng, WEATHER, 0.1))

    # collars at the three truss lines (between the principals, up near the ridge)
    collars = parts.acc('collarsC', 'Cottage C collars', 'timber.beam')
    hc = 0.85
    zc_mid = float(zU(0.0, hc)) - 0.078 / COS
    zc0, zc1 = zc_mid - 0.06, zc_mid + 0.06

    def h_range(z):
        return hp - (z + 0.16 / COS - ZS) / TAN, hp - (z - 0.004 / COS - ZS) / TAN
    lo_top = h_range(zc1)
    lo_bot = h_range(zc0)
    half = max(lo_top[0], lo_bot[0]) + 0.03
    facts['collar_embed'] = round(half - max(lo_top[0], lo_bot[0]), 3)
    for k_, x in enumerate(xt):
        V, F = box(x - 0.06, x + 0.06, yc - half, yc + half, zc0, zc1)
        collars.add(V, F, col=oak(rng, WEATHER, 0.1))
        # a king post stands on the collar and carries the ridge piece (one object each, so that the kit leans each about its own foot)
        kp = parts.acc('kingC%d' % (k_ + 1), 'Cottage C king post %d' % (k_ + 1), 'timber.post')
        zr_here = float(ZS + hp * TAN) - 0.09
        kw = 0.052 + 0.003 * k_
        V, F = box(x - kw - 0.002, x + kw + 0.002, yc - kw, yc + kw, zc1 + 0.001, zr_here - 0.001)
        kp.add(V, F, col=oak(rng, WEATHER, 0.1))

    # ---- door leaf, hinges, doorstep, lintel already built; the leaf rests on the doorstep
    step_top = g + 0.17
    dinfo = window_info['Ndoor']
    leaf_u0, leaf_u1 = dinfo['u0'] + 0.004, dinfo['u1'] - 0.004
    leaf_z0, leaf_z1 = step_top + 0.001, step_top + 0.001 + 1.8
    door = parts.acc('doorC', 'Cottage C door leaf', 'timber.door')
    widths = rng.uniform(0.11, 0.145, size=7)
    V, F, cols = plank_leaf(WN, leaf_u0, leaf_u1, 0.010, 0.045, leaf_z0, leaf_z1, widths, rng, WEATHER, FRESH, replaced={3}, bow=0.005,
                            ledges=((0.25, 0.38), (1.42, 1.55)))
    door.add(V, F, col=cols)
    hinges = parts.acc('hingesC', 'Cottage C hinges', 'iron.fitting')
    hinge_set(hinges, WN, leaf_u0, +1, 0.055, [leaf_z0 + 0.315, leaf_z0 + 1.485], 0.62, wback=0.010, col=shade(IRON, 1.0))
    # a latch bar and a ring (iron) on the door
    V, F = wbox(WN, leaf_u1 - 0.22, leaf_u1 - 0.04, 0.055, 0.067, leaf_z0 + 0.93, leaf_z0 + 0.96)
    hinges.add(V, F, col=IRON)
    V, F = wbox(WN, leaf_u1 - 0.065, leaf_u1 - 0.035, 0.055, 0.070, leaf_z0 + 0.90, leaf_z0 + 0.99)
    hinges.add(V, F, col=IRON)
    step = parts.acc('stepC', 'Cottage C doorstep', 'stone.step', seat=0.06)
    V, F = stone_solid(xm, -8.075, 1.12, 0.76, 0.0, g - 0.06, step_top, rng, chamfer=(0.09, 0.13))
    step.add(V, F, col=stone_colour(hexl('#8B8880'), g, 1.0, 0.0))

    # ---- floor.earth inside the footing
    floor = parts.acc('floorC', 'Cottage C earth floor', 'floor.earth', smooth=True, seat=0.08)
    xs = np.linspace(-29.40, -22.60, 35)
    ys = np.linspace(-12.52, -8.48, 21)
    XX, YY = np.meshgrid(xs, ys, indexing='ij')
    ZZ = g + 0.05 + 0.007 * noise.value(XX * 1.7, YY * 1.7, 0.5)
    T = np.stack([XX, YY, ZZ], axis=-1)
    Bb = np.array([[(x, ys[0], g - 0.08), (x, ys[-1], g - 0.08)] for x in xs])
    V, F, nt = grid_slab(T, Bb)
    earth = hexl('#4B3B2B')
    floor.add(V, F, col=lambda P: shade(np.tile(earth, (len(P), 1)), 1 + 0.12 * noise.value(P[:, 0] * 2, P[:, 1] * 2, 0.0)))

    # ---- daub panels (with chips), wattle in the chips
    wattle = parts.acc('wattleC', 'Cottage C wattle', 'timber.generic')
    panels = parts.acc('panelsC', 'Cottage C daub panels', 'wall.timber_frame', smooth=True)
    chip_wanted = {('N', 0), ('N', 3), ('E', 1), ('E', 4), ('S', 2), ('W', 3), ('GE', 2)}
    count_by_wall = {}
    chipped = 0
    for spec in panel_specs:
        wall, left, right, name = spec['wall'], spec['left'], spec['right'], spec['name']
        k = count_by_wall.get(name, 0)
        count_by_wall[name] = k + 1
        uL = lambda z, r=left: stud_at(r, z)[0] + r['a'] - 0.015  # noqa: E731
        uR = lambda z, r=right: stud_at(r, z)[0] - r['a'] + 0.015  # noqa: E731
        z1 = spec['z1']
        chip = None
        if (name, k) in chip_wanted:
            zt_mid = z1(0.5 * (uL(spec['z0']) + uR(spec['z0']))) if callable(z1) else z1
            zc = spec['z0'] + (zt_mid - spec['z0']) * rng.uniform(0.35, 0.6)
            width = uR(zc) - uL(zc)
            ru = min(width * 0.36, 0.26) * o['chip']
            rz = min((zt_mid - spec['z0']) * 0.32, 0.30) * o['chip']
            uc = uL(zc) + width * rng.uniform(0.40, 0.60)
            chip = (uc, zc, ru, rz)
            chipped += 1
        Fg, Bg, mask = daub_panel(wall, uL, uR, spec['z0'], z1, rng, noise2, None, chip=chip)
        V, F = slab_between(Fg, Bg)
        tint = rng.uniform(0.94, 1.06)
        nF = Fg.shape[0] * Fg.shape[1]
        col = np.zeros((len(V), 4))
        P = V
        macro = 1 + 0.07 * noise.value(P[:, 0] * 1.1, P[:, 1] * 1.1, P[:, 2] * 1.1)
        c = shade(np.tile(DAUB, (len(P), 1)), macro * tint)
        c = mixc(c, MUD, smoothstep(g + 1.05, g + 0.55, P[:, 2]) * 0.55)
        c = shade(c, 1 - 0.16 * smoothstep(zpb - 0.35, zpb, P[:, 2]))
        m_full = np.zeros(len(V))
        m_full[:nF] = mask.reshape(-1)
        c = mixc(c, CLAY, m_full)
        panels.add(V, F, col=c)
        if chip is not None:
            uc, zc, ru, rz = chip
            n = 3 if ru > 0.19 else 2
            zb0 = spec['z0'] - 0.0025
            zt0 = (z1(uc) if callable(z1) else z1) - 0.004
            su = [uc + (i - (n - 1) / 2) * 0.25 for i in range(n)]
            for u_ in su:
                V, F = wbox(wall, u_ - 0.025, u_ + 0.025, -0.015, 0.035, zb0, min(zt0, zb0 + 1.3))
                wattle.add(V, F, col=shade(WATTLE, rng.uniform(0.85, 1.12)))
            for i in range(n - 1):
                for zf in (0.30, 0.62):
                    zz = zb0 + (min(zt0, zb0 + 1.3) - zb0) * zf
                    V, F = wbox(wall, su[i] - 0.02, su[i + 1] + 0.02, -0.012, 0.040, zz - 0.025, zz + 0.025)
                    wattle.add(V, F, col=shade(WATTLE, rng.uniform(0.9, 1.15)))
    facts['chipped_panels'] = chipped
    facts['panels'] = len(panel_specs)

    # ---- windows: opening 0.45 x 0.6, shutter leaves (no glass), one ajar
    shutters = parts.acc('shuttersC', 'Cottage C shutters', 'timber.shutter')
    sh_hinges = parts.acc('shhingesC', 'Cottage C shutter hinges', 'iron.fitting')

    def shutter_pair(w, which, ajar_leaf=None):
        info = window_info[w]
        wall = info['wall']
        uc = info['u']
        zb, zt_ = info['z0'] - 0.005, info['z1'] + 0.015
        wf = 0.073
        leaves = [(uc - 0.255, uc - 0.004, 'L'), (uc + 0.004, uc + 0.255, 'R')] if which == 'pair' else [(uc - 0.255, uc + 0.255, 'R')]
        for (a, b, tag) in leaves:
            u_h = a if tag == 'L' else b
            d = +1 if u_h == a else -1
            widths = rng.uniform(0.9, 1.15, size=2 if which == 'pair' else 4)
            replaced = {int(rng.integers(0, len(widths)))} if rng.random() < 0.55 else set()
            V, F, cols = plank_leaf(wall, a, b, wf, 0.025, zb, zt_, widths, rng, hexl('#4F4337'), FRESH, replaced=replaced, bow=0.003)
            is_ajar = (ajar_leaf is not None and tag == ajar_leaf)
            pivot, ang = None, 0.0
            if is_ajar:
                pivot = wall.P(u_h, wf, 0.0)[:2]
                dv = wall.eu[:2] * d
                cross = dv[0] * wall.ew[1] - dv[1] * wall.ew[0]
                ang = math.radians(64) * (1 if cross > 0 else -1)
                V = rot_z(V, ang, pivot)
            shutters.add(V, F, col=cols)
            for zrel in (0.20, zt_ - zb - 0.20):
                zz = zb + zrel
                length = 0.2
                strap = wbox(wall, min(u_h, u_h + d * length), max(u_h, u_h + d * length), wf + 0.025, wf + 0.036, zz - 0.02, zz + 0.02)
                pin = wbox(wall, min(u_h - d * 0.035, u_h + d * 0.012), max(u_h - d * 0.035, u_h + d * 0.012), wf - 0.065, wf + 0.040, zz - 0.03, zz + 0.03)
                sV = rot_z(strap[0], ang, pivot) if is_ajar else strap[0]
                sh_hinges.add(sV, strap[1], col=IRON)
                sh_hinges.add(*pin, col=IRON)
    shutter_pair(1, 'pair')
    shutter_pair(2, 'pair', ajar_leaf=+1)
    shutter_pair(3, 'single')

    # ---- the thatch: two slabs resting on the rafters, and a rolled ridge cap
    thatch_col = tone3(hexl(o['thatch_hex']), hexl('#9C8A64'), hexl('#CBB07A'), o['thatch_tone'])
    cap_col = hexl('#8E7442')
    De = h_edge + 0.07
    xs_t = np.linspace(X0 - 0.30, X1 + 0.30, 81)
    Ds = np.linspace(0.0, De, 29)
    XXt, DDt = np.meshgrid(xs_t, Ds, indexing='ij')
    sg = sag_fn(XXt)
    mm = -TAN + sg / hp
    cosf = 1 / np.sqrt(1 + mm * mm)
    sinf = -mm * cosf

    def zT_of(x, D):
        sgx = sag_fn(x)
        m = -TAN + sgx / hp
        cf = 1 / np.sqrt(1 + m * m)
        sf = -m * cf
        hU = D - 0.09 * sf
        return ZS + (hp - hU) * TAN - sgx * (1 - hU / hp) + 0.09 * cf
    zT = zT_of(XXt, DDt)
    tv0 = 0.35 / cosf
    slabs = {}
    for s, key, nm in ((1, 'thatchN', 'Cottage C thatch north'), (-1, 'thatchS', 'Cottage C thatch south')):
        yw = yc + s * DDt
        damp = smoothstep(0.0, 0.45, DDt)
        lump = (0.10 * noise.value(XXt * 1.15, yw * 1.15, 0.0) + 0.045 * noise2.value(XXt * 2.3, yw * 2.3, 1.0)) * o['thatch_lump'] * damp
        course = 0.012 * np.sin(DDt * 2 * np.pi / 0.40)
        ee = np.minimum.reduce([De - DDt, XXt - xs_t[0], xs_t[-1] - XXt])
        roll = 0.07 * o['thatch_roll'] * np.exp(-((De - DDt - 0.30) / 0.15) ** 2)
        tv = tv0 * (1 + lump + roll) + course * damp
        tv = tv * (1 - 0.40 * smoothstep(0.17, 0.0, ee))
        Ptop = np.stack([XXt, yw, zT + tv], axis=-1)
        Bb = np.array([[(x, yc, float(zT_of(x, 0.0)) + 0.0005), (x, yc + s * De, float(zT_of(x, De)) + 0.0005)] for x in xs_t])
        V, F, nt = grid_slab(Ptop, Bb)
        col = np.zeros((len(V), 4))
        nTop = Ptop.shape[0] * Ptop.shape[1]
        P = V
        straw = shade(np.tile(thatch_col, (len(P), 1)), 1 + 0.10 * noise.value(P[:, 0] * 0.8, P[:, 1] * 0.8, 0.0) + 0.05 * np.sin(P[:, 1] * 2 * np.pi / 0.40 * 0.5))
        edge_dark = smoothstep(0.35, 0.0, np.minimum(De - np.abs(P[:, 1] - yc), 0.35))
        straw = mixc(straw, hexl('#7C6238'), edge_dark * 0.45)
        under = np.zeros(len(P))
        under[nTop:] = 1.0
        straw = mixc(straw, hexl('#3F3224'), under * 0.8)
        flags = np.zeros(len(F), bool)
        flags[:nt] = True
        parts.acc(key, nm, 'roof.thatch', smooth=True).add(V, F, col=straw, smooth=flags)

    # ridge piece (two lengths, one in each bay): flat underneath, its top cut to the slope of the thatch so that the thatch rests on it
    ridge = parts.acc('ridgeC', 'Cottage C ridge piece', 'timber.beam')
    for (xa, xb) in ((X0, xm - 0.008), (xm + 0.008, X1)):
        rings = []
        for x in np.linspace(xa, xb, 9):
            zr = float(zU(x, 0.0))
            rings.append(np.array([(x, yc - 0.085, zr - 0.09), (x, yc + 0.085, zr - 0.09), (x, yc + 0.085, float(zT_of(x, 0.085)) - 0.001), (x, yc, float(zT_of(x, 0.0)) - 0.001),
                                   (x, yc - 0.085, float(zT_of(x, 0.085)) - 0.001)]))
        V, F = loft(rings)
        ridge.add(V, F, col=oak(rng, WEATHER, 0.1))

    # ridge cap: a rolled ridge along the ridge line
    cap = parts.acc('thatchcapC', 'Cottage C thatch ridge cap', 'roof.thatch', smooth=True)
    rings = []
    for x in np.linspace(X0 - 0.30, X1 + 0.30, 33):
        z_a = float(zT_of(x, 0.0)) + float(0.35 / (1 / math.sqrt(1 + float(slope(x)) ** 2)))
        tanp = abs(float(slope(x)))
        bulge = 0.20 + 0.03 * float(noise.value(x * 1.3, 0.0, 0.5))
        Dp = [-0.46, -0.30, -0.15, 0.0, 0.15, 0.30, 0.46]
        low = [(yc + d_, z_a - abs(d_) * tanp - 0.06) for d_ in Dp]
        top = [(yc + d_, z_a - abs(d_) * tanp + bulge * (1 - (d_ / 0.52) ** 2) ** 0.8 * (1 + 0.1 * float(noise2.value(x * 3, d_ * 3, 0.0)))) for d_ in Dp[::-1]]
        rings.append(np.array([(x, p[0], p[1]) for p in low + top]))
    V, F = loft(rings)
    capc = np.tile(cap_col, (len(V), 1))
    capc = shade(capc, 1 + 0.08 * noise.value(V[:, 0] * 0.9, V[:, 1], 0.0))
    cap.add(V, F, col=capc)
    facts['zU_ridge_mid'] = float(zU(xm, 0.0))
    facts['sag_cm'] = [round(s_ * 100, 1) for s_ in SAG]
    facts['H_ridge_top'] = float(zU(xm, 0.0)) + 0.35 / COS + 0.2 - g
    return facts


# ------------------------------------------------------------------ cottage D
def outline_points(cx, cy, hx, hy, R, n_e, n_n, n_arc=8):
    """A rounded rectangle, counter-clockwise from the start of the east straight: sections east, north-east arc, north, north-west arc, west, south-west arc, south, south-east arc.
    Returns (points (N, 2), section starts [list of 8 indices], outward unit normals (N, 2))."""
    pts, nor, starts = [], [], []

    def straight(p0, p1, n, normal):
        for k in range(n):
            t = k / n
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
            nor.append(normal)

    def arc(c, a0, n):
        for k in range(n):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((c[0] + R * math.cos(a), c[1] + R * math.sin(a)))
            nor.append((math.cos(a), math.sin(a)))
    starts.append(len(pts)); straight((cx + hx, cy - hy + R), (cx + hx, cy + hy - R), n_e, (1.0, 0.0))
    starts.append(len(pts)); arc((cx + hx - R, cy + hy - R), 0, n_arc)
    starts.append(len(pts)); straight((cx + hx - R, cy + hy), (cx - hx + R, cy + hy), n_n, (0.0, 1.0))
    starts.append(len(pts)); arc((cx - hx + R, cy + hy - R), 90, n_arc)
    starts.append(len(pts)); straight((cx - hx, cy + hy - R), (cx - hx, cy - hy + R), n_e, (-1.0, 0.0))
    starts.append(len(pts)); arc((cx - hx + R, cy - hy + R), 180, n_arc)
    starts.append(len(pts)); straight((cx - hx + R, cy - hy), (cx + hx - R, cy - hy), n_n, (0.0, -1.0))
    starts.append(len(pts)); arc((cx + hx - R, cy - hy + R), 270, n_arc)
    return np.array(pts, float), starts, np.array(nor, float)


def cob_piece(Pout, Pin, Nrm, i0, i1, zbot, ztop_fn, noise, rows, bulge, lump, ring_total):
    """One piece of the cob wall ring (columns i0..i1 inclusive, counter-clockwise): outer face, inner face, top, bottom and two end caps, as ONE closed solid. ztop_fn(x, y) gives the
    top height of a column; the top row is exact (no lumps) so that a plate or a roof can lie on it; the walls bulge a little and are lumpy."""
    idx = [(i % ring_total) for i in range(i0, i1 + 1)]
    n = len(idx)
    O = np.zeros((n, rows + 1, 3))
    I = np.zeros((n, rows + 1, 3))
    for c, i in enumerate(idx):
        po, pi_, nn = Pout[i], Pin[i], Nrm[i]
        zt = max(ztop_fn(po[0], po[1]), zbot + 0.2)
        zt_in = max(ztop_fn(pi_[0], pi_[1]), zbot + 0.2)
        for j in range(rows + 1):
            t = j / rows
            w = (1 - smoothstep(0.80, 1.0, t)) * smoothstep(0.0, 0.06, t)
            for (P, zz, side, store) in ((po, zt, 1.0, O), (pi_, zt_in, -1.0, I)):
                z = zbot + t * (zz - zbot)
                d = (bulge * math.sin(math.pi * t) ** 0.8 + lump * float(noise.value(P[0] * 1.9, P[1] * 1.9, z * 1.9))) * w
                if side < 0:
                    d *= 0.55
                store[c, j] = (P[0] + side * nn[0] * d, P[1] + side * nn[1] * d, z)
    F = []
    for c in range(n - 1):
        for j in range(rows):
            F.append((tuple_idx(c, j, rows, n, 0), tuple_idx(c + 1, j, rows, n, 0), tuple_idx(c + 1, j + 1, rows, n, 0), tuple_idx(c, j + 1, rows, n, 0)))
            F.append((tuple_idx(c, j, rows, n, 1), tuple_idx(c, j + 1, rows, n, 1), tuple_idx(c + 1, j + 1, rows, n, 1), tuple_idx(c + 1, j, rows, n, 1)))
        F.append((tuple_idx(c, rows, rows, n, 0), tuple_idx(c + 1, rows, rows, n, 0), tuple_idx(c + 1, rows, rows, n, 1), tuple_idx(c, rows, rows, n, 1)))
        F.append((tuple_idx(c + 1, 0, rows, n, 0), tuple_idx(c, 0, rows, n, 0), tuple_idx(c, 0, rows, n, 1), tuple_idx(c + 1, 0, rows, n, 1)))
    for j in range(rows):
        F.append((tuple_idx(0, j, rows, n, 0), tuple_idx(0, j + 1, rows, n, 0), tuple_idx(0, j + 1, rows, n, 1), tuple_idx(0, j, rows, n, 1)))
        F.append((tuple_idx(n - 1, j, rows, n, 0), tuple_idx(n - 1, j, rows, n, 1), tuple_idx(n - 1, j + 1, rows, n, 1), tuple_idx(n - 1, j + 1, rows, n, 0)))
    V = np.vstack([O.reshape(-1, 3), I.reshape(-1, 3)])
    return V, F


def tuple_idx(c, j, rows, n, side):
    return side * n * (rows + 1) + c * (rows + 1) + j


def boolean_cut(V, F, cutters):
    """Cuts boxes (x0, x1, y0, y1, z0, z1) out of a closed solid with Blender's exact boolean, using temporary objects that are removed again. Returns (V, F)."""
    mesh = bpy.data.meshes.new('cs_tmp_cob')
    mesh.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    mesh.update()
    obj = bpy.data.objects.new('cs_tmp_cob', mesh)
    bpy.context.scene.collection.objects.link(obj)
    temps = [obj]
    meshes = [mesh]
    for k, c in enumerate(cutters):
        cV, cF = box(*c)
        cm = bpy.data.meshes.new(f'cs_tmp_cut{k}')
        cm.from_pydata([tuple(v) for v in cV], [], cF)
        cm.update()
        co = bpy.data.objects.new(f'cs_tmp_cut{k}', cm)
        bpy.context.scene.collection.objects.link(co)
        temps.append(co)
        meshes.append(cm)
        mod = obj.modifiers.new(f'cut{k}', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = co
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    m2 = bpy.data.meshes.new_from_object(ev)
    n = len(m2.vertices)
    flat = np.empty(n * 3)
    m2.vertices.foreach_get('co', flat)
    V2 = flat.reshape(-1, 3)
    F2 = [tuple(p.vertices) for p in m2.polygons]
    for t in temps:
        bpy.data.objects.remove(t, do_unlink=True)
    for m in meshes + [m2]:
        bpy.data.meshes.remove(m)
    return V2, F2


def build_D(parts, o):
    """Cottage D: the smallest, pale cob walls with rounded corners and no frame, silver shingles at 42 degrees, one low plank door in the north gable end."""
    rng = np.random.default_rng(o['seed'] + 202)
    noise = Noise(o['seed'] + 17)
    noise2 = Noise(o['seed'] + 18, scales=(1.1, 0.5, 0.25))
    X0, X1, Y0, Y1 = 2.15, 5.85, -10.2, -5.8
    cx, cy = 4.0, -8.0
    tw = 0.5
    xw0, xw1, yw0, yw1 = X0 + tw / 2, X1 - tw / 2, Y0 + tw / 2, Y1 - tw / 2
    hp = 1.6
    g, g_low = ground_top(X0 - 0.3, X1 + 0.3, Y0 - 0.3, Y1 + 0.3)
    zp = g + 0.30
    zc = g + 1.92
    zpb = zc + 0.001
    ZS = g + 2.04
    TAN, COS, SIN = math.tan(math.radians(42)), math.cos(math.radians(42)), math.sin(math.radians(42))
    WNd = Wall((xw0, yw1), (1, 0), (0, 1), xw1 - xw0)
    WEd = Wall((xw1, yw0), (0, 1), (1, 0), yw1 - yw0)
    COB = tone3(hexl(o['cob_hex']), hexl('#A39170'), hexl('#CFBF9C'), o['cob_tone'])
    SPL = hexl('#6E6050')
    WEATHER, FRESH = hexl('#6B5E4C'), hexl('#8A6A45')
    IRON = hexl('#2A2826')
    STONE = hexl('#7C7A73')
    facts = dict(g=g, g_low=g_low)

    # ---- plinth: rubble stones 0.5 wide, flat on top 0.3 m above the pad, none under the door
    foot = parts.acc('footD', 'Cottage D plinth', 'stone.footing', seat=0.03)

    def fill(start, end):
        pos, out = start, []
        while end - pos > 0.05:
            L = rng.uniform(0.45, 0.8)
            if end - pos - L < 0.36:
                L = end - pos
            out.append((pos + L / 2, L - 0.02))
            pos += L
        return out
    runs = []
    for (a, b) in ((xw0 - 0.25, 3.50), (4.50, xw1 + 0.25)):
        for c, L in fill(a, b):
            runs.append((c, yw1, L, 0.0))
    for c, L in fill(xw0 - 0.25, xw1 + 0.25):
        runs.append((c, yw0, L, 0.0))
    for c, L in fill(yw0 + 0.25 + 0.015, yw1 - 0.25 - 0.015):
        runs.append((xw0, c, L, math.pi / 2))
        runs.append((xw1, c, L, math.pi / 2))
    for (sx, sy, L, rot) in runs:
        sx, sy = (sx, sy + rng.uniform(-0.01, 0.01)) if rot == 0.0 else (sx + rng.uniform(-0.01, 0.01), sy)
        width = rng.uniform(0.445, 0.465)
        corner = (L > 0.5 and (abs(sx - xw0) < 0.45 or abs(sx - xw1) < 0.45) and rot == 0.0) 
        zb = pk.ground_height_at(sx, sy) - 0.03
        V, F = stone_solid(sx, sy, L, width, rot, zb, zp, rng, chamfer=(0.12, 0.2) if corner else (0.05, 0.10))
        foot.add(V, F, col=stone_colour(STONE, g, rng.uniform(0.82, 1.12)))

    # ---- the cob walls: four pieces (east, north gable, west, south gable) of a ring with rounded corners, cut for the door and the window
    def zU_plane(h, sag=0.0):
        return ZS + (hp - h) * TAN - sag * (1 - h / hp)

    def gable_top(x, y):
        h = abs(x - cx)
        hU = h - 0.07 * SIN
        return float(ZS + (hp - hU) * TAN + 0.07 * COS) - 0.001
    Pout, starts, Nrm = outline_points(cx, cy, 1.85, 2.2, 0.45, 22, 20)
    Pin, _, _ = outline_points(cx, cy, 1.35, 1.7, 0.06, 22, 20)
    N = len(Pout)
    s = starts + [N]
    flat_top = lambda x, y: zc  # noqa: E731
    gab_top = lambda x, y: max(zc, gable_top(x, y))  # noqa: E731
    pieces = [('E', s[0], s[1], flat_top), ('N', s[1], s[4], gab_top), ('W', s[4], s[5], flat_top), ('S', s[5], s[8], gab_top)]
    cob = parts.acc('cobD', 'Cottage D cob walls', 'wall.cob', smooth=True)
    cut_door = [(3.52, 4.48, yw1 - 0.60, yw1 + 0.45, zp - 0.4, g + 1.77), (3.32, 4.68, yw1 - 0.60, yw1 + 0.45, g + 1.77, g + 1.90)]
    cut_window = [(xw1 - 0.4, xw1 + 0.6, -8.25, -7.75, g + 1.05, g + 1.50), (xw1 - 0.4, xw1 + 0.6, -8.37, -7.63, g + 1.50, g + 1.62), (xw1 - 0.4, xw1 + 0.6, -8.37, -7.63, g + 0.93, g + 1.05)]
    for name, i0, i1, topfn in pieces:
        V, F = cob_piece(Pout, Pin, Nrm, i0, i1, zp + 0.0005, topfn, noise, 14, 0.03 * (0.6 + 0.4 * o['cob_lump']), 0.018 * o['cob_lump'], N)
        if name == 'N':
            V, F = boolean_cut(V, F, cut_door)
        elif name == 'E':
            V, F = boolean_cut(V, F, cut_window)
        P = V
        macro = 1 + 0.06 * noise.value(P[:, 0] * 1.2, P[:, 1] * 1.2, P[:, 2] * 1.2) + 0.03 * noise2.value(P[:, 0] * 3.1, P[:, 1] * 3.1, P[:, 2] * 3.1)
        c = shade(np.tile(COB, (len(P), 1)), macro * rng.uniform(0.97, 1.03))
        c = mixc(c, SPL, smoothstep(g + 0.85, g + 0.30, P[:, 2]) * 0.55)
        c = shade(c, 1 - 0.12 * smoothstep(zc - 0.4, zc, P[:, 2]) * (1 - smoothstep(zc, zc + 0.5, P[:, 2])))
        cob.add(V, F, col=c)
    facts['cob_tris'] = cob.tris

    # ---- the door frame, lintel, doorstep, leaf and hinges
    step_top = g + 0.15
    dposts = parts.acc('doorpostsD', 'Cottage D door posts', 'timber.post')
    for xs_, w_ in ((3.52, 0.08), (4.40, 0.08)):
        a = rng.uniform(0.0, 0.0)
        V, F = post_solid(WNd, (xs_ + w_ / 2) - xw0, 0.18, w_ / 2, 0.07, step_top + 0.001, g + 1.769, lean=lean_for(rng, o['lean'] * 0.5), twist=rng.uniform(-0.02, 0.02))
        dposts.add(V, F, col=oak(rng, WEATHER))
    beams = parts.acc('beamsD', 'Cottage D lintels and cill', 'timber.beam')
    V, F = box(3.325, 4.675, yw1 - 0.235, yw1 + 0.235, g + 1.771, g + 1.895)
    beams.add(V, F, col=oak(rng, WEATHER))
    V, F = box(xw1 - 0.245, xw1 + 0.245, -8.365, -7.635, g + 0.931, g + 1.05)
    beams.add(V, F, col=oak(rng, WEATHER))
    V, F = box(xw1 - 0.245, xw1 + 0.245, -8.365, -7.635, g + 1.501, g + 1.619)
    beams.add(V, F, col=oak(rng, WEATHER))
    step = parts.acc('stepD', 'Cottage D doorstep', 'stone.step', seat=0.06)
    V, F = stone_solid(4.0, -5.865, 1.15, 1.07, 0.0, g - 0.06, step_top, rng, chamfer=(0.09, 0.14))
    step.add(V, F, col=stone_colour(hexl('#8B8880'), g, 1.0, 0.0))
    door = parts.acc('doorD', 'Cottage D door leaf', 'timber.door')
    leaf_u0, leaf_u1 = 3.604 - xw0, 4.396 - xw0
    leaf_z0, leaf_z1 = step_top + 0.001, step_top + 0.001 + 1.6
    widths = rng.uniform(0.15, 0.22, size=5)
    V, F, cols = plank_leaf(WNd, leaf_u0, leaf_u1, 0.115, 0.040, leaf_z0, leaf_z1, widths, rng, WEATHER, FRESH, replaced={1}, bow=0.005, ledges=((0.22, 0.34), (1.18, 1.30)))
    door.add(V, F, col=cols)
    hinges = parts.acc('hingesD', 'Cottage D hinges', 'iron.fitting')
    hinge_set(hinges, WNd, leaf_u0, +1, 0.155, [leaf_z0 + 0.28, leaf_z0 + 1.24], 0.5, wback=0.115, col=IRON)
    V, F = wbox(WNd, leaf_u1 - 0.20, leaf_u1 - 0.04, 0.155, 0.166, leaf_z0 + 0.82, leaf_z0 + 0.85)
    hinges.add(V, F, col=IRON)

    # ---- the window in the east wall: two posts on the cill, a shutter leaf on the outside, ajar
    wposts = parts.acc('wpostsD', 'Cottage D window posts', 'timber.post')
    for (ya, yb) in ((-8.25, -8.20), (-7.80, -7.75)):
        u = 0.5 * (ya + yb) - yw0
        V, F = post_solid(WEd, u, 0.19, 0.025, 0.07, g + 1.051, g + 1.499, lean=lean_for(rng, o['lean'] * 0.3))
        wposts.add(V, F, col=oak(rng, WEATHER))
    shutters = parts.acc('shuttersD', 'Cottage D shutter', 'timber.shutter')
    sh_hinges = parts.acc('shhingesD', 'Cottage D shutter hinges', 'iron.fitting')
    u_a, u_b = -8.26 - yw0, -7.74 - yw0
    wf = 0.25 + 0.003
    zb, zt_ = g + 1.04, g + 1.52
    V, F, cols = plank_leaf(WEd, u_a, u_b, wf, 0.025, zb, zt_, rng.uniform(0.9, 1.15, size=3), rng, hexl('#5A4E40'), FRESH, replaced={2}, bow=0.003)
    pivot = WEd.P(u_a, wf, 0.0)[:2]
    dv = WEd.eu[:2]
    cross = dv[0] * WEd.ew[1] - dv[1] * WEd.ew[0]
    ang = math.radians(66) * (1 if cross > 0 else -1)
    shutters.add(rot_z(V, ang, pivot), F, col=cols)
    for zrel in (0.14, zt_ - zb - 0.14):
        zz = zb + zrel
        strap = wbox(WEd, u_a, u_a + 0.22, wf + 0.025, wf + 0.036, zz - 0.02, zz + 0.02)
        pin = wbox(WEd, u_a - 0.03, u_a + 0.012, wf - 0.004, wf + 0.040, zz - 0.03, zz + 0.03)
        sh_hinges.add(rot_z(strap[0], ang, pivot), strap[1], col=IRON)
        sh_hinges.add(*pin, col=IRON)

    # ---- floor.earth
    floor = parts.acc('floorD', 'Cottage D earth floor', 'floor.earth', smooth=True, seat=0.08)
    xs = np.linspace(2.66, 5.34, 15)
    ys = np.linspace(-9.69, -6.42, 18)
    XX, YY = np.meshgrid(xs, ys, indexing='ij')
    ZZ = g + 0.05 + 0.007 * noise.value(XX * 1.7, YY * 1.7, 0.5)
    T = np.stack([XX, YY, ZZ], axis=-1)
    Bb = np.array([[(x, ys[0], g - 0.08), (x, ys[-1], g - 0.08)] for x in xs])
    V, F, nt = grid_slab(T, Bb)
    earth = hexl('#4F3F2E')
    floor.add(V, F, col=lambda P: shade(np.tile(earth, (len(P), 1)), 1 + 0.12 * noise.value(P[:, 0] * 2, P[:, 1] * 2, 0.0)))

    # ---- the roof frame: wall plates on the cob, rafters on the plates and the purlins, ridge piece
    yA, yB = -9.7, -6.3
    SAGD = rng.uniform(0.018, 0.026) * o['sag']

    def sag_fn(y):
        y = np.asarray(y, float)
        out = np.zeros_like(y)
        m = (y >= yA) & (y <= yB)
        out[m] = SAGD * np.sin(np.pi * (y[m] - yA) / (yB - yA))
        return out

    def zU(y, h):
        return ZS + (hp - h) * TAN - sag_fn(y) * (1 - h / hp)

    def slope(y):
        return -TAN + sag_fn(y) / hp

    def nvec(y, s_):
        m = float(slope(y))
        n = np.array([s_ * (-m), 0.0, 1.0])
        return n / np.linalg.norm(n)
    plate = parts.acc('plateD', 'Cottage D wall plate', 'timber.beam')
    for s_ in (1, -1):
        rings = []
        for y in np.linspace(-9.69, -6.31, 6):
            hi, ho = hp - 0.10, hp + 0.10
            pts = [(cx + s_ * hi, zpb), (cx + s_ * ho, zpb), (cx + s_ * ho, float(zU(y, ho))), (cx + s_ * hi, float(zU(y, hi)))]
            rings.append(np.array([(p[0], y, p[1]) for p in pts]))
        V, F = loft(rings)
        plate.add(V, F, col=oak(rng, WEATHER))
    rafters = parts.acc('raftersD', 'Cottage D rafters', 'timber.beam')

    def roof_beam(y, s_, ha, hb, width, d_lo, d_hi):
        n = nvec(y, s_)
        ey = np.array([0.0, 1.0, 0.0])
        rings = []
        for h in (ha, hb):
            L = np.array([cx + s_ * h, y, float(zU(y, h))])
            rings.append(np.array([L - ey * width / 2 + n * d_lo, L + ey * width / 2 + n * d_lo, L + ey * width / 2 + n * d_hi, L - ey * width / 2 + n * d_hi]))
        return loft(rings)
    h_edge = hp + 0.25 + 0.30
    for k in range(6):
        y = -9.45 + k * 0.58 + rng.uniform(-0.02, 0.02)
        for s_ in (1, -1):
            V, F = roof_beam(y + rng.uniform(-0.008, 0.008), s_, h_edge, 0.03, rng.uniform(0.07, 0.085), 0.0, 0.07)
            rafters.add(V, F, col=oak(rng, WEATHER, 0.12))
    purlins = parts.acc('purlinD', 'Cottage D purlin', 'timber.beam')
    hpur = 0.85
    for s_ in (1, -1):
        rings = []
        for y in np.linspace(-10.05, -5.95, 11):
            n = nvec(y, s_)
            dh = 0.05 * math.cos(math.atan(abs(float(slope(y)))))
            o1 = np.array([cx + s_ * (hpur - dh), y, float(zU(y, hpur - dh))])
            o2 = np.array([cx + s_ * (hpur + dh), y, float(zU(y, hpur + dh))])
            rings.append(np.array([o1, o2, o2 - n * 0.10, o1 - n * 0.10]))
        V, F = loft(rings)
        purlins.add(V, F, col=oak(rng, WEATHER, 0.1))
    # ---- the shingles: two slabs of courses, each shingle a little different, a few slipped and a few missing
    De = h_edge + 0.07 * SIN
    ys_t = np.linspace(-10.35, -5.65, 68)
    n_rows = 64
    Ds = np.linspace(0.0, De, n_rows)
    YYt, DDt = np.meshgrid(ys_t, Ds, indexing='ij')
    sgt = sag_fn(YYt)
    mm = -TAN + sgt / hp
    cosf = 1 / np.sqrt(1 + mm * mm)
    sinf = -mm * cosf

    def zT_of(y, D):
        sgx = sag_fn(y)
        m = -TAN + sgx / hp
        cf = 1 / np.sqrt(1 + m * m)
        sf = -m * cf
        hU = D - 0.07 * sf
        return ZS + (hp - hU) * TAN - sgx * (1 - hU / hp) + 0.07 * cf
    zT = zT_of(YYt, DDt)
    # the ridge piece: flat underneath, its top cut to the slope of the shingle slabs (a few mm under them, and under the cob gable tops where its ends are sunk into them)
    ridge = parts.acc('ridgeD', 'Cottage D ridge piece', 'timber.beam')
    rings = []
    for y in np.linspace(-10.0, -6.0, 9):
        zr = float(zU(y, 0.0))
        rings.append(np.array([(cx - 0.08, y, zr - 0.08), (cx + 0.08, y, zr - 0.08), (cx + 0.08, y, float(zT_of(y, 0.08)) - 0.0035), (cx, y, float(zT_of(y, 0.0)) - 0.0035),
                               (cx - 0.08, y, float(zT_of(y, 0.08)) - 0.0035)]))
    V, F = loft(rings)
    ridge.add(V, F, col=oak(rng, WEATHER, 0.1))

    exposure = 0.141
    sl_total = De / COS
    sl = DDt / COS
    r_ = (sl_total - sl) / exposure
    kk = np.floor(r_).astype(int)
    fr = r_ - kk                                           # 0 at the butt (lower edge), up to 1 at the upper edge
    f_butt = 1 - fr
    n_courses = int(kk.max()) + 1
    n_cols = len(ys_t)
    tone = {}
    lift_off = {}
    tilt = {}
    state = {}
    block_of = np.zeros((n_courses, n_cols), int)
    joint = np.zeros((n_courses, n_cols), bool)
    for k in range(n_courses):
        pos = -int(rng.integers(0, 3)) - (k % 2)
        bid = 0
        c = 0
        starts_k = []
        while pos < n_cols + 3:
            w = int(rng.choice([2, 2, 2, 3]))
            starts_k.append(pos)
            for c in range(max(pos, 0), min(pos + w, n_cols)):
                block_of[k, c] = bid
            joint[k, max(min(pos, n_cols - 1), 0)] = True if pos >= 0 else joint[k, 0]
            tone[(k, bid)] = max(0.45, 1.0 + rng.uniform(-0.30, 0.12) * o['shingle_mix'])
            lift_off[(k, bid)] = rng.uniform(-0.004, 0.004)
            tilt[(k, bid)] = rng.uniform(-0.004, 0.004)
            state[(k, bid)] = 'ok'
            bid += 1
            pos += w
    keys = [kb for kb in tone if kb[0] > 2]
    for kb in rng.permutation(len(keys))[:6]:
        state[keys[int(kb)]] = 'missing'
    for kb in rng.permutation(len(keys))[:9]:
        if state[keys[int(kb)]] == 'ok':
            state[keys[int(kb)]] = 'slipped'
    SH = hexl(o['shingle_hex'])
    UNDER = hexl('#3E3730')
    slabs = {}
    for s_, key, nm in ((1, 'shingleE', 'Cottage D shingles east'), (-1, 'shingleW', 'Cottage D shingles west')):
        xw = cx + s_ * DDt
        lift = np.zeros_like(DDt)
        colr = np.zeros(DDt.shape + (4,))
        for i in range(n_cols):
            for j in range(n_rows):
                k = int(kk[i, j])
                f = float(f_butt[i, j])
                if DDt[i, j] < 0.34:                      # the two courses at the ridge are laid flat under the cap
                    lift[i, j] = 0.022
                    colr[i, j] = shade(SH, 0.9)
                    continue
                kb = (k, int(block_of[k, i]))
                st = state[kb]
                base = 0.010 + 0.012 * f + lift_off[kb] + tilt[kb] * ((i % 3) - 1) + 0.003 * float(noise2.value(ys_t[i] * 3, Ds[j] * 3, s_))
                tn = tone[kb]
                if st == 'missing':
                    base = -0.009
                    c = shade(UNDER, rng.uniform(0.9, 1.1))
                else:
                    if st == 'slipped':
                        base += 0.018 * f * f + 0.012
                        tn *= 0.85
                    c = shade(SH, tn)
                    warm = hexl('#B3A794') if (kb[0] + kb[1]) % 3 == 0 else hexl('#9DA29E')
                    c = mixc(c, shade(warm, tn), 0.35)
                    c = shade(c, 1 - 0.18 * smoothstep(0.30, 0.0, 1 - f_butt[i, j]) * 0)            # kept neutral
                    if fr[i, j] < 0.20:                         # the shadow under the butt of the course above
                        c = shade(c, 0.78 + 0.22 * fr[i, j] / 0.20)
                    if joint[k, i]:
                        c = shade(c, 0.78)
                    if s_ == -1 and Ds[j] > De - 0.7:
                        c = mixc(c, hexl('#7C8466'), 0.18)
                lift[i, j] = base
                colr[i, j] = c
        Ptop = np.stack([YYt * 0 + xw, YYt, zT + 0.016 + lift], axis=-1)
        Bb = np.array([[(cx, y, float(zT_of(y, 0.0)) + 0.0005), (cx + s_ * De, y, float(zT_of(y, De)) + 0.0005)] for y in ys_t])
        V, F, nt = grid_slab(Ptop, Bb)
        col = np.zeros((len(V), 4))
        col[:Ptop.shape[0] * Ptop.shape[1]] = colr.reshape(-1, 4)
        col[Ptop.shape[0] * Ptop.shape[1]:] = shade(UNDER, 0.8)
        flags = np.zeros(len(F), bool)
        flags[:nt] = True
        parts.acc(key, nm, 'roof.shingle', smooth=True).add(V, F, col=col, smooth=flags)
        slabs[key] = Ptop
    # the ridge boards: one inverted V of boards lying on the two slabs along the ridge
    cap = parts.acc('shinglecapD', 'Cottage D shingle ridge', 'roof.shingle')
    rings = []
    ytop = np.linspace(-10.35, -5.65, 13)
    for y in ytop:
        Dp = [-0.30, -0.15, 0.0, 0.15, 0.30]
        def ztop_at(D):
            return float(zT_of(y, abs(D))) + 0.016 + 0.022 + 0.001
        low = [(cx + d_, ztop_at(d_)) for d_ in Dp]
        jit = rng.uniform(-0.004, 0.004)
        top = [(cx + d_ + jit * (1 if d_ > 0 else -1), ztop_at(d_) + 0.034 + 0.004 * float(noise2.value(y * 3, d_ * 3, 1.0))) for d_ in Dp[::-1]]
        rings.append(np.array([(p[0], y, p[1]) for p in low + top]))
    V, F = loft(rings)
    cap.add(V, F, col=shade(np.tile(SH, (len(V), 1)), 0.82))
    facts['ridge_len'] = 4.0
    facts['ridge_height_above_ground'] = float(zU(-8.0, 0.0)) + 0.016 + 0.022 + 0.04 - g
    facts['sag_cm'] = round(SAGD * 100, 1)
    return facts


# ------------------------------------------------------------------ the stage
DEFAULTS = dict(seed=31, thatch_lump=1.3, thatch_roll=1.5, sag=1.0, chip=1.5, cob_lump=1.2, daub_tone=0.15, daub_value=1.08, thatch_tone=0.6, cob_tone=0.4, lean=1.0, daub_hex='#9C4F36',
                thatch_hex='#B8985A', cob_hex='#B9A683', shingle_hex='#A9A8A2', shingle_mix=1.2, cottages='CD')
ROUGHNESS = {'timber.beam': (0.72, 0.95), 'timber.post': (0.72, 0.95), 'timber.door': (0.7, 0.92), 'timber.shutter': (0.7, 0.92), 'timber.generic': (0.75, 0.95), 'stone.footing': (0.8, 0.97),
             'stone.step': (0.7, 0.92), 'floor.earth': (0.9, 1.0), 'iron.fitting': (0.45, 0.75), 'wall.timber_frame': (0.85, 0.98), 'wall.cob': (0.88, 1.0), 'roof.thatch': (0.9, 1.0),
             'roof.shingle': (0.7, 0.92)}


def apply(options=None):
    """Builds cottage C and cottage D on the frozen ground. Safe to run twice (it forgets what an earlier run made first). Returns a dict of facts."""
    o = dict(DEFAULTS)
    o.update(options or {})
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    parts = Parts()
    facts = {}
    if 'C' in o['cottages']:
        facts['C'] = build_C(parts, o)
    if 'D' in o['cottages'] and 'build_D' in globals():
        facts['D'] = build_D(parts, o)
    mats = {}
    made, tris = 0, 0
    for key in parts.order:
        d = parts.d[key]
        if d['acc'].empty():
            continue
        mesh = d['acc'].make(d['name'])
        role = d['role']
        if role not in mats:
            lo, hi = ROUGHNESS.get(role, (0.75, 0.95))
            mats[role] = make_material('Cottage S ' + role, lo, hi, displace=0.05 if role == 'roof.thatch' else None)
        mesh.materials.append(mats[role])
        obj = pk.new_part_object(OWNER, role, d['name'], mesh)
        if d['seat'] is not None and d['seat'] is not False:
            pk.seat_on_ground(obj, sink=float(d['seat']))
        made += 1
        tris += sum(len(p.vertices) - 2 for p in mesh.polygons)
    bpy.context.view_layer.update()
    facts['objects'] = made
    facts['triangles'] = tris
    print(f'cottages_south: {made} objects made, {tris} triangles, 0 changed, 0 deleted outside the part')
    return facts
