"""What this does: the STABLE part of the forest village (owner stable): the EMPTY stable (9.8 x 6.0 m, centre (24, 39), long side facing south onto the yard), its yard fittings (an empty hollowed-log
trough on two stone blocks, a bare hitching rail) and the pieces of its own work that lie about (one fallen shingle, broken, below its gap in the roof). Nothing else: no horse, no hay, no cart, no person, no sign.

Built from the ground up, every part carried: a stone dwarf wall (stone.footing) under all walls with a gap at the doorway where a sill stone (stone.step) lies; timber posts on the wall, girts tenoned into the
posts, wall plates on the post tops, a lintel over the doorway, ties across the building resting on the plates and on posts at the stall-front line, near-black UPRIGHT boards on the outside standing on the
wall; three empty box stalls against the north wall (partitions on the truss lines, boards below and open rails above, an empty manger on two short posts, an empty hay rack and an iron tie ring in each);
a beaten earth floor flush with the ground; a doorway 2.4 m wide with a lintel and two door leaves on iron hinges standing open (one against the outside wall, one half open and sagging); two slatted vents
in the gables; a roof of 40 degrees: queen posts on the ties, a purlin on each slope, common rafters with a birdsmouth on the plates, a ridge piece, courses of shingles with a few slipped, missing and mossy ones.
Character is SHAPE: boards of different widths and heights with a few fresher replacements and two gaps, posts a little out of plumb, a ridge that sags between the trusses, a door leaf that sags on its hinges.
Colour is written into each mesh as a colour layer (Col) and read by a material of our own that carries a small picture, so the surface pass keeps our colours and adds its maps and wear on top.
It is IDEMPOTENT: apply(options) first forgets what an earlier run of this owner made (pk.forget_part), then builds again with the same seed. It changes nothing that is not ours.
A concrete example: apply({'seed': 5}) twice gives the same objects. Options (all optional): seed (5), sag_deg (door leaf sag in degrees, 2.4), fresh (how fresh the replaced boards look, 1.2), moss (moss on the shingles,
1.2), gaps (scale of slipped and missing shingles and of board gaps, 1.5), open_deg (how far the half-open leaf stands open, 52). The defaults are the picks of one batch of ten variations (judged by eye from the sheet).
Frames and units: metres; x east, y north, z up. Heights in the code are measured from the pad (G) unless a name says absolute.
"""
import math
import os
import sys

import numpy as np

import bpy
from mathutils import Matrix

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
for _path in (os.path.join(KIT, 'place-kit') if KIT else '', '/home/user/Music/plugins/explainer-film/kit/place-kit'):
    if _path and os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
import place_kit as pk  # noqa: E402
from place_kit import names as pk_names  # noqa: E402
from place_kit import parts as pk_parts  # noqa: E402

OWNER = 'stable'
X0, X1, Y0, Y1 = 19.1, 28.9, 36.0, 42.0          # outer footprint
YC = 39.0                                          # ridge line
THETA = math.radians(40.0)
TAN, COS, SIN = math.tan(THETA), math.cos(THETA), math.sin(THETA)
FT = 0.40            # top of the dwarf wall above the pad
FLOOR_TOP = 0.01     # top of the earth floor above the pad (flush with the ground, 1 cm proud so it never z-fights the ground)
PL0, PL1 = 2.32, 2.44    # wall plate: bottom and top
TIE0, TIE1 = 2.44, 2.60  # ties lie on the plates
BT = 0.03            # thickness of the cladding boards
D_B, BW, R_D, D_MAX = 3.0, 0.23, 0.09, 3.40   # roof: distance of the plate's outer edge from the ridge, seat width, rafter depth, tail of the rafters
D_A = D_B - BW
RV = R_D / COS
TRUSS_X = (19.23, 22.4, 25.6, 28.77)
STALL_C = (20.85, 24.0, 27.15)
DOOR_X0, DOOR_X1 = 22.8, 25.2


# ------------------------------------------------------------------ colour
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexl(h):
    h = h.lstrip('#')
    return (_lin(int(h[0:2], 16) / 255.0), _lin(int(h[2:4], 16) / 255.0), _lin(int(h[4:6], 16) / 255.0), 1.0)


def mixc(a, b, t):
    t = float(min(max(t, 0.0), 1.0))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def shade(c, f):
    return (min(c[0] * f, 1.0), min(c[1] * f, 1.0), min(c[2] * f, 1.0), 1.0)


def vary(c, rng, amount):
    f = 1.0 + amount * (rng.random() * 2 - 1)
    g = 1.0 + amount * 0.4 * (rng.random() * 2 - 1)
    return (min(c[0] * f * g, 1.0), min(c[1] * f, 1.0), min(c[2] * f / g, 1.0), 1.0)


C_BOARD = hexl('#33281F')      # near-black stable boards
C_SILVER = hexl('#7A736A')     # silvered board edges
C_FRESH = hexl('#8A6A45')      # a replaced board
C_TIMBER = hexl('#5A4C40')     # weathered timber
C_OAK = hexl('#4B3F33')        # old oak frame inside
C_STONE = hexl('#7C7A73')
C_SILL = hexl('#8F8C82')
C_EARTH = hexl('#6B5538')
C_SHINGLE = hexl('#5C544A')
C_SHINGLE_D = hexl('#463F37')
C_SHINGLE_S = hexl('#7A766C')
C_MOSS = hexl('#5E8236')
C_MOSS_D = hexl('#4F6B3A')
C_IRON = hexl('#2E2B29')
C_RUST = hexl('#8A4B2C')
C_DOOR = hexl('#473A2E')


# ------------------------------------------------------------------ smooth noise (plain numpy, repeatable)
class Noise:
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


# ------------------------------------------------------------------ the mesh accumulator
def _signed_volume(V, F):
    vol = 0.0
    for f in F:
        a = V[f[0]]
        for k in range(1, len(f) - 1):
            vol += np.dot(a, np.cross(V[f[k]], V[f[k + 1]]))
    return vol / 6.0


class Acc:
    """Collects closed solids (each with its own vertices, so each is one loose piece) and their face colours, then makes one mesh."""

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
            loop_cols.extend([col] * len(f))
        attr.data.foreach_set('color', np.asarray(loop_cols, float).ravel())
        if smooth:
            try:
                mesh.shade_smooth()
            except Exception:  # noqa: BLE001
                pass
        return mesh


# ------------------------------------------------------------------ primitives (each returns vertices and faces of ONE closed solid)
BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]   # bottom, top, y0, x1, y1, x0


def box(x0, x1, y0, y1, z0, z1):
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return np.array(V, float), list(BOX_FACES)


def lofted_post(cx, cy, z0, z1, sx, sy, lean=(0.0, 0.0), taper=1.0, top_z_fn=None):
    """A square post: level bottom at z0, top at z1 moved by `lean` (out of plumb); top_z_fn(x, y) cuts the top on a slope."""
    def ring(cxx, cyy, z, kx, ky):
        return [(cxx - kx, cyy - ky, z), (cxx + kx, cyy - ky, z), (cxx + kx, cyy + ky, z), (cxx - kx, cyy + ky, z)]
    bottom = ring(cx, cy, z0, sx / 2, sy / 2)
    top = ring(cx + lean[0], cy + lean[1], z1, sx / 2 * taper, sy / 2 * taper)
    if top_z_fn is not None:
        top = [(x, y, float(top_z_fn(x, y))) for x, y, _ in top]
    return np.array(bottom + top, float), list(BOX_FACES)


def extrude_x(poly_yz, x0, x1):
    P = np.asarray(poly_yz, float)
    n = len(P)
    V = np.vstack([np.column_stack([np.full(n, x0), P[:, 0], P[:, 1]]), np.column_stack([np.full(n, x1), P[:, 0], P[:, 1]])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def loft_rings(rings):
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


def bowed_bar_x(x0, x1, yc, w, z0, z1, bow, segments=8, phase=0.0):
    xs = np.linspace(x0, x1, segments + 1)
    rings = []
    for x in xs:
        t = (x - x0) / max(x1 - x0, 1e-6)
        off = bow * math.sin(math.pi * t + phase)
        rings.append([(x, yc + off - w / 2, z0), (x, yc + off + w / 2, z0), (x, yc + off + w / 2, z1), (x, yc + off - w / 2, z1)])
    return loft_rings(rings)


def bowed_bar_y(y0, y1, xc, w, z0, z1, bow, segments=8, phase=0.0):
    ys = np.linspace(y0, y1, segments + 1)
    rings = []
    for y in ys:
        t = (y - y0) / max(y1 - y0, 1e-6)
        off = bow * math.sin(math.pi * t + phase)
        rings.append([(xc + off - w / 2, y, z0), (xc + off + w / 2, y, z0), (xc + off + w / 2, y, z1), (xc + off - w / 2, y, z1)])
    V, F = loft_rings(rings)
    return V, F


def stone_blob(cx, cy, z0, z1, sx, sy, rng, wobble=0.06):
    """A rough stone: a box with its plan corners pulled in a little differently; flat bottom and flat top (so a post, a board or a log can rest on it)."""
    pts = []
    corner_pull = [1 - wobble * rng.random() for _ in range(4)]
    for z in (z0, z1):
        for k, (ox, oy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            pts.append((cx + ox * sx / 2 * corner_pull[k], cy + oy * sy / 2 * corner_pull[k], z))
    return np.array(pts, float), list(BOX_FACES)


def rot_z_about(V, angle, pivot):
    V = np.array(V, float)
    c, s = math.cos(angle), math.sin(angle)
    x, y = V[:, 0] - pivot[0], V[:, 1] - pivot[1]
    V[:, 0] = pivot[0] + c * x - s * y
    V[:, 1] = pivot[1] + s * x + c * y
    return V


def torus(cx, cy, cz, R, r, plane='xz', nu=14, nv=7):
    """A ring (iron) lying in the xz plane (plane='xz') or the yz plane; closed."""
    V, F = [], []
    for i in range(nu):
        a = 2 * math.pi * i / nu
        for j in range(nv):
            b = 2 * math.pi * j / nv
            rad = R + r * math.cos(b)
            u, w = rad * math.cos(a), rad * math.sin(a)
            h = r * math.sin(b)
            if plane == 'xz':
                V.append((cx + u, cy + h, cz + w))
            else:
                V.append((cx + h, cy + u, cz + w))
    for i in range(nu):
        for j in range(nv):
            i2, j2 = (i + 1) % nu, (j + 1) % nv
            F.append((i * nv + j, i2 * nv + j, i2 * nv + j2, i * nv + j2))
    return np.array(V, float), F


# ------------------------------------------------------------------ materials (our own, with a small picture so the surface pass keeps them)
def tile_image():
    name = 'Stable tile'
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, 64, 64, alpha=False)
        img.colorspace_settings.name = 'Non-Color'                 # first, before the pixels (blender-5-traps.md, trap 1)
        rng = np.random.default_rng(7)
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
    out.is_active_output = True
    mat.displacement_method = 'BUMP'
    mat['place_owner'] = OWNER
    return mat


BEVEL_WIDTH = {'timber': 0.008, 'stone': 0.010, 'iron': 0.004, 'wall': 0.008, 'floor': 0.006, 'roof': 0.008}


def add_edge_rounding(obj, role):
    """Edges a hand could touch are rounded: a small boxy object gets its own cheap Bevel modifier; a big relief object (the shingle roof) is marked pk_bevelled so the kit adds no bevel to it."""
    faces = len(obj.data.polygons)
    if faces > 4000:
        obj['pk_bevelled'] = 1
        return
    klass = role.split('.')[0]
    size = min(obj.dimensions) or 0.05
    width = min(BEVEL_WIDTH.get(klass, 0.008), max(size / 4.0, 0.001))
    mod = obj.modifiers.new('Stable bevel', 'BEVEL')
    mod.width = width
    mod.segments = 1
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(40.0)


class Builder:
    """Makes the objects of the stable: every object gets its owner and role as it is made, a material and (for what stands on the ground) a note of how far it is sunk."""

    def __init__(self, G, mats):
        self.G, self.M, self.objects = G, mats, []

    def emit(self, acc, name, role, mat, sink=None, absolute=False, smooth=False, bevel=True):
        if acc.empty():
            return None
        full = f'Stable {name}'
        mesh = acc.make(full, smooth=smooth)
        if not absolute:
            mesh.transform(Matrix.Translation((0.0, 0.0, self.G)))
            mesh.update()
        mesh.materials.append(self.M[mat] if isinstance(mat, str) else mat)
        obj = pk.new_part_object(OWNER, role, full, mesh)
        self.objects.append(obj)
        if sink is not None:
            obj[pk_names.SEAT_GROUND_Z] = float(self.G if not absolute else sink[1])
            obj[pk_names.SEAT_SINK] = float(sink[0] if absolute else sink)
        if bevel:
            add_edge_rounding(obj, role)
        else:
            obj['pk_bevelled'] = 1
        return obj


# ------------------------------------------------------------------ the roof's numbers
def U(d):
    """underside of the rafters at distance d from the ridge line (the line passes through the outer corner of the rafters' seat on the plate)"""
    return PL1 + TAN * (D_B - d)


def Tt(d):
    return U(d) + RV


def sag_at(x, sag_max=0.03):
    x = np.atleast_1d(np.asarray(x, float))
    s = np.zeros_like(x)
    for a, b in zip(TRUSS_X[:-1], TRUSS_X[1:]):
        m = (x >= a) & (x <= b)
        s[m] = np.sin(np.pi * (x[m] - a) / (b - a)) ** 2
    return s * sag_max


Z_RB0 = PL1 + TAN * (D_B - 0.02)
RAFTER_X = (18.85, 19.72, 20.55, 21.38, 22.10, 22.75, 23.55, 24.40, 25.15, 26.05, 26.85, 27.65, 28.35, 29.15)


def ridge_z(x):
    return Z_RB0 - sag_at(x)


# ------------------------------------------------------------------ the shingles: courses that lie on the rafters' top plane
def slab_from_quads(quads, colours, thick, to3d):
    """A closed slab from non-overlapping quads (corners (x, s), counter-clockwise seen from the outer face) with one colour each. Neighbouring quads share vertices. to3d(x, s, n) gives a world point
    for a position on the plane and a distance n out of it. Returns (vertices, faces, face colours)."""
    index, V = {}, []

    def vid(x, s, layer):
        key = (round(x, 6), round(s, 6), layer)
        i = index.get(key)
        if i is None:
            i = len(V)
            index[key] = i
            V.append(to3d(x, s, 0.0 if layer == 0 else thick))
        return i
    F, C, edges = [], [], {}
    for q, col in zip(quads, colours):
        top = tuple(vid(x, s, 1) for x, s in q)
        bot = tuple(vid(x, s, 0) for x, s in reversed(q))
        F.append(top)
        C.append(col)
        F.append(bot)
        C.append(col)
        for k in range(4):
            a, b = q[k], q[(k + 1) % 4]
            ka, kb = (round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6))
            key = (ka, kb) if ka < kb else (kb, ka)
            edges.setdefault(key, []).append((a, b, col))
    for key, lst in edges.items():
        if len(lst) == 1:
            a, b, col = lst[0]
            F.append((vid(a[0], a[1], 0), vid(b[0], b[1], 0), vid(b[0], b[1], 1), vid(a[0], a[1], 1)))
            C.append(shade(col, 0.8))
    return np.array(V, float), F, C


def build_shingles(side, rng, moss_amount, gap_scale, missing, slipped, fresh_tabs, noise):
    """One slope's courses: each course is one connected slab lying on the rafters' top, its lower part cut into tabs (different widths, a slot between), colours per tab."""
    D_TOP = 0.16
    pitch = 0.24
    L = pitch - 0.004
    x_s, x_e = 18.72, 29.28
    s_max = (D_MAX - D_TOP) / COS
    n_courses = int(math.ceil((s_max + 0.03) / pitch))
    acc = Acc()
    tab_count = 0
    lost = []
    shaded = side > 0                                                  # the north slope is the shaded one
    base_col = C_SHINGLE if shaded else mixc(C_SHINGLE, C_SHINGLE_S, 0.35)
    for k in range(n_courses):
        s_c = -0.03 + k * pitch
        s_top = min(s_c + L, s_max)
        if s_top - s_c < 0.06:
            continue
        thick = 0.020 + 0.008 * rng.random() + (0.003 if k % 2 else 0.0)
        slot_up = min(0.034, (s_top - s_c) * 0.3)                      # the band along the top of the course that holds the tabs together
        s_b0 = s_top - slot_up

        def to3d(x, s, n, thick=thick):
            d = D_MAX - s * COS + SIN * n
            return (x, YC + side * d, Tt(D_MAX) + s * SIN + COS * n)
        quads, cols = [], []
        x = x_s
        row_tab = 0
        while x < x_e - 0.04:
            w = 0.20 + 0.12 * rng.random()
            xr = min(x + w, x_e)
            if x_e - xr < 0.10:
                xr = x_e
            nxt = xr + 0.006 + 0.003 * rng.random() * gap_scale

            def hit(lst, k=k, x=x, xr=xr):
                return any(kk == k and x <= xt < xr for kk, xt in lst)
            low = s_c + (0.004 + 0.012 * rng.random())
            skip = hit(missing)
            if hit(slipped):
                low = s_c + 0.035 + 0.02 * gap_scale
            tone = base_col
            q_m = float(np.clip(0.5 + 0.5 * noise.value((x + xr) / 2, side * 0.8 + s_c * 0.5), 0, 1))
            if shaded:
                moss_cover = moss_amount * (0.78 - 0.18 * min(k, 12) / 12.0) * (0.55 + 0.45 * q_m)
                moss_pick = rng.random() < (0.48 * moss_amount * (0.6 + 0.4 * q_m))
            else:
                moss_cover = moss_amount * 0.12 * (0.4 + q_m)
                moss_pick = rng.random() < 0.10 * moss_amount
            if rng.random() < 0.28:
                tone = mixc(tone, C_SHINGLE_D, 0.5 + 0.4 * rng.random())
            elif rng.random() < 0.22:
                tone = mixc(tone, C_SHINGLE_S, 0.45)
            is_fresh = hit(fresh_tabs)
            if is_fresh:
                tone = mixc(C_FRESH, C_SHINGLE_S, 0.35)
            tone = vary(tone, rng, 0.09)
            if skip:
                lost.append((k, (x + xr) / 2.0))
            if moss_pick and not is_fresh:
                tone = mixc(tone, C_MOSS if rng.random() < 0.6 else C_MOSS_D, 0.35 + 0.35 * moss_cover)
            band_tone = shade(tone, 0.85)
            # the tab (unless it is missing) and the band above it; the slot after it is a band only
            if not skip:
                quads.append([(x, low), (xr, low), (xr, s_b0), (x, s_b0)])
                cols.append(tone)
            else:
                pass
            quads.append([(x, s_b0), (xr, s_b0), (xr, s_top), (x, s_top)])
            cols.append(band_tone)
            if nxt < x_e - 1e-6 and xr < x_e:
                quads.append([(xr, s_b0), (nxt, s_b0), (nxt, s_top), (xr, s_top)])
                cols.append(band_tone)
            x = nxt if xr < x_e else x_e
            row_tab += 1
            tab_count += 1
        V, F, C = slab_from_quads(quads, cols, thick, to3d)
        acc.add(V, F, C, closed=True)
    return acc, tab_count, lost


# ------------------------------------------------------------------ the stage
def apply(options=None):
    options = dict(options or {})
    seed = int(options.get('seed', 5))
    sag_deg = float(options.get('sag_deg', 2.4))
    fresh_amount = float(options.get('fresh', 1.2))
    moss_amount = float(options.get('moss', 1.2))
    gap_scale = float(options.get('gaps', 1.5))
    open_deg = float(options.get('open_deg', 52.0))
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    bpy.context.view_layer.update()
    pk_parts.refresh_ground()
    rng = np.random.default_rng(seed)
    noise = Noise(seed + 2, (2.2, 0.9, 0.4))
    # the pad: the highest ground under the building (the contract says it is level within 0.25 m; it is level to a few millimetres)
    probes = [pk.ground_height_at(X0 + (X1 - X0) * i / 8.0, Y0 + (Y1 - Y0) * j / 8.0) for i in range(9) for j in range(9)]
    G = round(float(max(probes)), 4)
    M = dict(board=make_material('Stable boards', 0.85), timber=make_material('Stable timber', 0.8), stone=make_material('Stable stone', 0.88), sill=make_material('Stable sill stone', 0.8),
             earth=make_material('Stable earth floor', 0.96), shingle=make_material('Stable shingles', 0.85), iron=make_material('Stable iron', 0.6), door=make_material('Stable door wood', 0.82),
             trough=make_material('Stable trough wood', 0.9))
    B = Builder(G, M)
    out = {}

    # ---------------------------------------------------------------- 1. the dwarf wall (stone.footing), the sill stone, the floor
    def stones_along(axis, a0, a1, c0, c1):
        """Loose stones in a row: along `axis` from a0 to a1, across from c0 to c1 (width about 0.44), all with the same flat top at FT."""
        acc = Acc()
        a = a0
        while a < a1 - 0.05:
            length = 0.55 + 0.55 * rng.random()
            b = min(a + length, a1)
            if a1 - b < 0.45:
                b = a1
            gap = 0.012 if b < a1 else 0.0
            cx_a = (a + b - gap) / 2.0
            sx_a = (b - a) - gap
            across0 = c0 - 0.012 * rng.random()
            across1 = c1 + 0.012 * rng.random()
            cc = (across0 + across1) / 2.0
            sc = across1 - across0
            if axis == 'x':
                V, F = stone_blob(cx_a, cc, -0.03, FT, sx_a, sc, rng)
            else:
                V, F = stone_blob(cc, cx_a, -0.03, FT, sc, sx_a, rng)
            acc.add(V, F, vary(C_STONE, rng, 0.14))
            a = b
        return acc
    wl = 0.44
    out['footing sw'] = B.emit(stones_along('x', X0, DOOR_X0, Y0, Y0 + wl), 'footing south west', 'stone.footing', 'stone', sink=0.03)
    out['footing se'] = B.emit(stones_along('x', DOOR_X1, X1, Y0, Y0 + wl), 'footing south east', 'stone.footing', 'stone', sink=0.03)
    out['footing n'] = B.emit(stones_along('x', X0, X1, Y1 - wl, Y1), 'footing north', 'stone.footing', 'stone', sink=0.03)
    out['footing w'] = B.emit(stones_along('y', Y0 + wl, Y1 - wl, X0, X0 + wl), 'footing west', 'stone.footing', 'stone', sink=0.03)
    out['footing e'] = B.emit(stones_along('y', Y0 + wl, Y1 - wl, X1 - wl, X1), 'footing east', 'stone.footing', 'stone', sink=0.03)
    acc = Acc()
    mid = (DOOR_X0 + DOOR_X1) / 2.0
    for a, b in ((DOOR_X0, mid - 0.006), (mid + 0.006, DOOR_X1)):
        V, F = stone_blob((a + b) / 2, Y0 + wl / 2 + 0.005, -0.06, 0.11, b - a, wl - 0.01, rng, wobble=0.03)
        acc.add(V, F, vary(C_SILL, rng, 0.10))
    out['sill'] = B.emit(acc, 'sill stones', 'stone.step', 'sill', sink=0.06)
    acc = Acc()
    V, F = box(X0 + wl, X1 - wl, Y0 + wl, Y1 - wl, -0.12, FLOOR_TOP)
    acc.add(V, F, [C_EARTH] * 6)
    out['floor'] = B.emit(acc, 'earth floor', 'floor.earth', 'earth', sink=0.12)

    # ---------------------------------------------------------------- 2. posts of the walls (timber.post), standing on the dwarf wall
    def lean():
        return ((rng.random() - 0.5) * 0.014, (rng.random() - 0.5) * 0.014)
    post_oak = C_OAK

    # every post is its own object: the surface pass leans a post or a fence about the foot of its object, which would tip a long object holding many posts off its plates
    def post(name, cx, cy, sx, sy, z0, z1, **kw):
        acc = Acc()
        V, F = lofted_post(cx, cy, z0, z1, sx, sy, lean=lean(), **kw)
        acc.add(V, F, vary(post_oak, rng, 0.12))
        return B.emit(acc, name, 'timber.post', 'timber')

    ys, yn = 36.13, 41.87
    posts_made = []
    for k, cx in enumerate((19.23, 19.95, 21.75, 22.4, 25.6, 26.25, 28.05, 28.77)):
        posts_made.append(post(f'post south wall {k + 1}', cx, ys, 0.2, 0.2, FT, PL0))
    for k, cx in enumerate((22.65, 25.35)):                                      # jambs of the doorway: wider, flush with the boards
        posts_made.append(post(f'door jamb post {k + 1}', cx, 36.10, 0.3, 0.2, FT, PL0))
    for k, cx in enumerate((19.23, 19.95, 21.75, 22.4, 23.1, 24.9, 25.6, 26.25, 28.05, 28.77)):
        posts_made.append(post(f'post north wall {k + 1}', cx, yn, 0.2, 0.2, FT, PL0))
    for k, cy in enumerate((38.7, 40.25)):
        posts_made.append(post(f'post west gable {k + 1}', 19.23, cy, 0.2, 0.2, FT, PL1))      # the stall-front line post and a stud, up to the tie
        posts_made.append(post(f'post east gable {k + 1}', 28.77, cy, 0.2, 0.2, FT, PL1))
    for cx in (22.4, 25.6):
        for k, cy in enumerate((38.7, 40.25)):
            posts_made.append(post(f'post stall front {int(cx)} {k + 1}', cx, cy, 0.2, 0.2, FLOOR_TOP, PL1))   # on the floor, up to the tie (they are also the ends of the stall partitions)
    out['posts'] = posts_made

    # ---------------------------------------------------------------- 3. wall plates, lintel, ties (the studs between the truss posts keep every free stretch of a plate short)
    # wall plates: sit on the post tops (z PL0 to PL1), y 0.23 wide (the rafters' seat), butting at the posts
    acc = Acc()
    for x_a, x_b in ((X0 + 0.03, 22.75), (25.25, X1 - 0.03)):
        V, F = bowed_bar_x(x_a, x_b, Y0 + BW / 2, BW, PL0, PL1, 0.006, phase=rng.random() * 3)
        acc.add(V, F, vary(C_TIMBER, rng, 0.1))
    out['plate s'] = B.emit(acc, 'wall plate south', 'timber.beam', 'timber')
    acc = Acc()
    for x_a, x_b in ((X0 + 0.03, 22.4), (22.4, 25.6), (25.6, X1 - 0.03)):
        V, F = bowed_bar_x(x_a, x_b, Y1 - BW / 2, BW, PL0, PL1, 0.006, phase=rng.random() * 3)
        acc.add(V, F, vary(C_TIMBER, rng, 0.1))
    out['plate n'] = B.emit(acc, 'wall plate north', 'timber.beam', 'timber')
    acc = Acc()
    V, F = box(22.75, 25.25, Y0, Y0 + BW, PL0, PL1)
    acc.add(V, F, vary(C_OAK, rng, 0.08))
    out['lintel'] = B.emit(acc, 'lintel', 'timber.beam', 'timber')
    # ties across the building: on the plates at both ends and on the posts at the stall-front line
    acc = Acc()
    for xc in TRUSS_X:
        V, F = bowed_bar_y(Y0 + 0.05, Y1 - 0.05, xc, 0.20, TIE0, TIE1, 0.008, phase=rng.random() * 3)
        acc.add(V, F, vary(C_TIMBER, rng, 0.1))
    out['ties'] = B.emit(acc, 'ties', 'timber.beam', 'timber')

    # ---------------------------------------------------------------- 4. the cladding: near-black upright boards (timber.plank), one object for each wall
    replaced = {'south': (5,), 'south2': (4,), 'north': (14,), 'west': (11,), 'east': (9,)}
    gaps_at = {'south': (8,), 'north': (17,), 'west': (), 'east': (13,)}

    def board(acc, axis, a0, a1, t0, t1, z0, z1, fresh=False, tone_amt=0.0):
        """One upright board between a0 and a1 along the wall and t0..t1 across it (the thickness), a little out of plumb at the top."""
        lx, ly = (rng.random() - 0.5) * 0.008, (rng.random() - 0.5) * 0.008
        if axis == 'x':
            V, F = lofted_post((a0 + a1) / 2, (t0 + t1) / 2, z0, z1, a1 - a0, t1 - t0, lean=(lx, 0.0))
        else:
            V, F = lofted_post((t0 + t1) / 2, (a0 + a1) / 2, z0, z1, t1 - t0, a1 - a0, lean=(0.0, ly))
        base = mixc(C_BOARD, C_TIMBER, 0.12 * rng.random())
        face = vary(base, rng, 0.14)
        if fresh:
            face = vary(mixc(base, C_FRESH, min(1.0, 0.75 * fresh_amount)), rng, 0.08)
        edge = vary(mixc(face, C_SILVER, 0.6 if not fresh else 0.25), rng, 0.08)
        top = shade(face, 0.8)
        # faces: bottom, top, y0, x1, y1, x0 ; the outer face is y0 (south wall, axis x) or x0 (west gable, axis y); mirrored on the other side
        acc.add(V, F, [shade(face, 0.6), top, face, edge, face, edge] if axis == 'x' else [shade(face, 0.6), top, edge, face, edge, face])

    def wall_boards(axis, a_start, a_end, t0, t1, z_bottom, z_top_fn, key, holes=(), acc=None):
        """Boards side by side from a_start to a_end; z_top_fn(a0, a1) gives the top; holes: (a0, a1, z0, z1) openings to cut."""
        acc = acc if acc is not None else Acc()
        a = a_start
        i = 0
        while a < a_end - 0.02:
            w = 0.15 + 0.15 * rng.random()
            b = min(a + w, a_end)
            if a_end - b < 0.14:
                b = a_end
            gap = 0.0
            if i in gaps_at.get(key, ()):
                gap = 0.026 * gap_scale
            elif b < a_end:
                gap = 0.0015 + 0.002 * rng.random()
            a1 = b - gap
            z_top = z_top_fn(a, a1) - 0.012 * rng.random()
            fresh = i in replaced.get(key, ())
            pieces = [(z_bottom, z_top)]
            for h0, h1, hz0, hz1 in holes:
                if a1 > h0 and a < h1:
                    new = []
                    for z_a, z_b in pieces:
                        if z_b <= hz0 or z_a >= hz1:
                            new.append((z_a, z_b))
                        else:
                            if z_a < hz0:
                                new.append((z_a, hz0))
                            if z_b > hz1:
                                new.append((hz1, z_b))
                    pieces = new
            for z_a, z_b in pieces:
                if z_b - z_a > 0.05:
                    board(acc, axis, a, a1, t0, t1, z_a, z_b, fresh=fresh)
            a = b
            i += 1
        return acc

    plate_bottom = PL0
    # the south wall: two stretches either side of the doorway, outer face at y = Y0 (both go into one object)
    acc_south = Acc()
    wall_boards('x', X0 + BT, 22.5, Y0, Y0 + BT, FT, lambda a, b: plate_bottom, 'south', acc=acc_south)
    wall_boards('x', 25.5, X1 - BT, Y0, Y0 + BT, FT, lambda a, b: plate_bottom, 'south2', acc=acc_south)
    out['clad s'] = B.emit(acc_south, 'cladding south wall', 'timber.plank', 'board')
    acc = wall_boards('x', X0 + BT, X1 - BT, Y1 - BT, Y1, FT, lambda a, b: plate_bottom, 'north')
    out['clad n'] = B.emit(acc, 'cladding north wall', 'timber.plank', 'board')

    def gable_top(a, b):
        d = max(abs(a - YC), abs(b - YC))
        return U(d) - 0.015
    vent_y0, vent_y1, vent_z0, vent_z1 = 38.72, 39.28, 3.70, 4.13
    acc = wall_boards('y', Y0, Y1, X0, X0 + BT, FT, gable_top, 'west', holes=[(vent_y0, vent_y1, vent_z0, vent_z1)])
    out['clad w'] = B.emit(acc, 'cladding west gable', 'timber.plank', 'board')
    acc = wall_boards('y', Y0, Y1, X1 - BT, X1, FT, gable_top, 'east', holes=[(vent_y0, vent_y1, vent_z0, vent_z1)])
    out['clad e'] = B.emit(acc, 'cladding east gable', 'timber.plank', 'board')

    # ---------------------------------------------------------------- 5. vents high in the gables: a frame resting on the boards below, the boards above rest on it; slats between the side bars
    for tag, xa in (('west', X0), ('east', X1 - BT)):
        acc = Acc()
        x_lo, x_hi = xa - 0.012, xa + BT + 0.012
        bar = 0.06
        V, F = box(x_lo, x_hi, vent_y0, vent_y1, vent_z0, vent_z0 + bar)
        acc.add(V, F, vary(C_TIMBER, rng, 0.1))
        for yy0 in (vent_y0, vent_y1 - bar):
            V, F = box(x_lo, x_hi, yy0, yy0 + bar, vent_z0 + bar, vent_z1 - bar)
            acc.add(V, F, vary(C_TIMBER, rng, 0.1))
        V, F = box(x_lo, x_hi, vent_y0, vent_y1, vent_z1 - bar, vent_z1)
        acc.add(V, F, vary(C_TIMBER, rng, 0.1))
        out['vent ' + tag] = B.emit(acc, f'vent frame {tag} gable', 'timber.generic', 'timber')
        acc = Acc()
        zc0, zc1 = vent_z0 + bar, vent_z1 - bar
        n_slats = 4
        for i in range(n_slats):
            zc = zc0 + (zc1 - zc0) * (i + 0.5) / n_slats
            tilt = math.radians(28.0)
            hw, ht = 0.034, 0.011
            pts = []
            for dz, dx in ((-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht)):
                pts.append((dx * math.cos(tilt) - dz * math.sin(tilt), dx * math.sin(tilt) + dz * math.cos(tilt)))
            rect = [(x_lo + (x_hi - x_lo) / 2 + p[0], zc + p[1]) for p in pts]
            V = []
            for yy in (vent_y0 + bar, vent_y1 - bar):
                for (px, pz) in rect:
                    V.append((px, yy, pz))
            F = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            acc.add(np.array(V, float), F, vary(C_TIMBER, rng, 0.1))
        out['slats ' + tag] = B.emit(acc, f'vent slats {tag} gable', 'timber.fence', 'timber', bevel=False)

    # ---------------------------------------------------------------- 6. the roof frame: queen posts on the ties, purlins, rafters on the plates, the ridge piece
    PEN, PH, PW = 0.03, 0.14, 0.12
    D_P = 1.55
    d0b = D_P - (PH - PEN) * SIN
    z0b = U(D_P) - (PH - PEN) * COS
    queens = []
    for k, xc in enumerate(TRUSS_X):
        for side, tag in ((-1, 'south'), (1, 'north')):
            cy = YC + side * d0b

            def top_fn(x, y, side=side):
                d = (y - YC) * side
                return z0b + 0.02 - (d - d0b) * TAN                 # the top is cut on the purlin's underside plane and sits 2 cm into it, so the surface pass's small lean never lifts it away
            acc = Acc()
            V, F = lofted_post(xc, cy, TIE1, z0b, 0.14, 0.09, lean=(0.0, 0.0), top_z_fn=top_fn)
            acc.add(V, F, vary(C_OAK, rng, 0.1))
            queens.append(B.emit(acc, f'queen post {tag} {k + 1}', 'timber.post', 'timber'))
    out['queen'] = queens
    s_vec, n_vec = np.array([COS, -SIN]), np.array([SIN, COS])
    base = np.array([D_P, U(D_P)])
    corners = [(-PW / 2, -(PH - PEN)), (PW / 2, -(PH - PEN)), (PW / 2, PEN), (-PW / 2, PEN)]
    pts = [base + a * s_vec + b * n_vec for a, b in corners]
    cuts = [18.75, 22.4, 25.6, 29.25]
    for side, tag in ((-1, 'south'), (1, 'north')):
        acc = Acc()
        for a, b in zip(cuts[:-1], cuts[1:]):
            P = [(YC + side * float(p[0]), float(p[1])) for p in pts]
            V, F = extrude_x(P, a + 0.005, b - 0.005)
            acc.add(V, F, vary(C_OAK, rng, 0.1))
        out['purlin ' + tag] = B.emit(acc, f'purlin {tag} slope', 'timber.beam', 'timber')
    for side, tag in ((-1, 'south'), (1, 'north')):
        acc = Acc()
        for x in RAFTER_X:
            z_cut = float(ridge_z(x)[0])
            d_cb = D_B - (z_cut - PL1) / TAN
            d_ct = d_cb + RV / TAN
            d_max = D_MAX + (rng.random() - 0.5) * 0.04
            w = 0.07 + 0.02 * rng.random()
            poly = [(d_cb, z_cut), (d_ct, z_cut), (d_max, Tt(d_max)), (d_max, U(d_max)), (D_B, PL1), (D_A, PL1), (D_A, U(D_A))]
            P = [(YC + side * d, z) for d, z in poly]
            V, F = extrude_x(P, x - w / 2, x + w / 2)
            V = rot_z_about(V, math.radians((rng.random() - 0.5) * 0.5), (x, YC + side * (D_A + D_B) / 2))
            acc.add(V, F, vary(C_TIMBER, rng, 0.12))
        out['rafters ' + tag] = B.emit(acc, f'rafters {tag} slope', 'timber.beam', 'timber')
    acc = Acc()
    rcuts = [18.75, 22.4, 25.6, 29.25]
    wr, hr = 0.24, 0.14
    for a, b in zip(rcuts[:-1], rcuts[1:]):
        xs = sorted(set([a + 0.005, b - 0.005] + [x for x in RAFTER_X if a + 0.005 < x < b - 0.005] + list(np.linspace(a + 0.005, b - 0.005, 9))))
        rings = []
        for x in xs:
            zb = float(ridge_z(x)[0])
            rings.append([(x, YC - wr / 2, zb), (x, YC + wr / 2, zb), (x, YC + wr / 2, zb + hr), (x, YC - wr / 2, zb + hr)])
        V, F = loft_rings(rings)
        acc.add(V, F, vary(C_OAK, rng, 0.08))
    out['ridge'] = B.emit(acc, 'ridge piece', 'timber.beam', 'timber')

    # ---------------------------------------------------------------- 7. the shingles (roof.shingle): courses on the rafters, with slipped, missing and mossy ones; the missing one on the yard side is the fallen one
    missing_s = [(4, 27.6)]
    slipped_s = [(2, 20.4), (9, 25.0), (14, 23.2)]
    fresh_s = [(6, 21.7)]
    missing_n = [(7, 23.3), (12, 21.0)]
    slipped_n = [(3, 26.4), (5, 19.8), (11, 27.9)]
    fresh_n = [(10, 24.5)]
    for side, tag, mi, sl, fr in ((-1, 'south', missing_s, slipped_s, fresh_s), (1, 'north', missing_n, slipped_n, fresh_n)):
        acc, n_tabs, lost = build_shingles(side, rng, moss_amount, gap_scale, mi, sl, fr, noise)
        if side < 0:
            lost_south = lost
        out['shingles ' + tag] = B.emit(acc, f'shingles {tag} slope', 'roof.shingle', 'shingle', bevel=False)
        out['tabs ' + tag] = n_tabs

    # ---------------------------------------------------------------- 8. the door: two leaves (timber.door) on iron hinges (iron.fitting), standing open
    def leaf_grid(rng_l):
        """The leaf in its own frame as ONE closed height-field slab: u along the leaf from the hinge axis (0 to 1.2), v across it (the outer face at v < 0), w up from the leaf's bottom. The front is cut by a V-groove at every
        joint between boards, the back carries three ledges (raised bands with sloped edges); the top edge is uneven from board to board. Returns (vertex grid front, vertex grid back, face colours) in local coordinates."""
        widths, total = [], 0.0
        while total < 1.2 - 1e-6:
            w = 0.16 + 0.07 * rng_l.random()
            if 1.2 - (total + w) < 0.15:
                w = 1.2 - total
            widths.append(w)
            total += w
        us, vf = [0.0], [-0.0225]
        u = 0.0
        for idx, w in enumerate(widths):
            if idx > 0:
                us += [u - 0.004, u, u + 0.004]
                vf += [-0.0225, -0.0125, -0.0225]
            u += w
        us.append(1.2)
        vf.append(-0.0225)
        ws, vb = [0.0], [0.0225]
        for zc in (0.40, 1.15, 1.95):
            ws += [zc - 0.07 - 0.008, zc - 0.07, zc + 0.07, zc + 0.07 + 0.008]
            vb += [0.0225, 0.0525, 0.0525, 0.0225]
        ws.append(2.30)
        vb.append(0.0225)
        tops = [2.30 - 0.014 * rng_l.random() for _ in us]
        nu, nw = len(us), len(ws)
        Fv = np.zeros((nu, nw, 3))
        Bv = np.zeros((nu, nw, 3))
        for i in range(nu):
            for j in range(nw):
                w_ = ws[j] if j < nw - 1 else tops[i]
                Fv[i, j] = (us[i], vf[i], w_)
                Bv[i, j] = (us[i], vb[j], w_)
        tone = [vary(C_DOOR, rng_l, 0.16) for _ in widths]
        return Fv, Bv, tone, widths, ws, vb

    def leaf_to_world(pts, hinge, psi, u0, sag_rad, w_pivot, w_base):
        """Points (u, v, w) of the leaf frame in the world: sag (a turn about the leaf's v axis through the lower hinge; the free edge drops), then the swing about the hinge axis, then the move to the hinge."""
        out_pts = []
        cs, ss = math.cos(sag_rad), -math.sin(sag_rad)
        cp, sp = math.cos(psi), math.sin(psi)
        for u, v, w in pts:
            wr_ = w + w_base - w_pivot
            u2 = u * cs - wr_ * ss
            w2 = u * ss + wr_ * cs + w_pivot
            px, py = u2 * u0, v                                             # closed leaf: u runs along (+1, 0) or (-1, 0), v along (0, +1)
            qx, qy = cp * px - sp * py, sp * px + cp * py
            out_pts.append((hinge[0] + qx, hinge[1] + qy, w2))
        return np.array(out_pts, float)

    LEAF_BOTTOM = 0.06
    hinge_y = 35.93
    hz_lo, hz_hi = LEAF_BOTTOM + 0.44, LEAF_BOTTOM + 1.89
    leaf_specs = (('west', 22.78, 1.0, -math.pi, 0.0), ('east', 25.22, -1.0, math.radians(open_deg), math.radians(sag_deg)))
    for tag, hx, u0, psi, sag_rad in leaf_specs:
        rng_l = np.random.default_rng(seed + (11 if tag == 'west' else 12))
        Fv, Bv, tone, widths_l, ws, vb = leaf_grid(rng_l)
        cum_w = np.cumsum(widths_l)[:-1]
        nu, nw = Fv.shape[0], Fv.shape[1]

        def W(P):
            return leaf_to_world(P.reshape(-1, 3), (hx, hinge_y), psi, u0, sag_rad, hz_lo, LEAF_BOTTOM)
        Vw = np.vstack([W(Fv), W(Bv)])                                  # front vertices first, then back vertices
        fi = lambda i, j: i * nw + j                                    # noqa: E731
        bi = lambda i, j: nu * nw + i * nw + j                          # noqa: E731
        F, C = [], []
        edge_col = mixc(C_DOOR, C_SILVER, 0.45)
        for i in range(nu - 1):
            b_idx = int(np.searchsorted(cum_w, (Fv[i, 0, 0] + Fv[i + 1, 0, 0]) / 2))
            for j in range(nw - 1):
                F.append((fi(i, j), fi(i + 1, j), fi(i + 1, j + 1), fi(i, j + 1)))
                C.append(tone[b_idx])
                F.append((bi(i, j), bi(i, j + 1), bi(i + 1, j + 1), bi(i + 1, j)))
                ledge = vb[j] > 0.03 and vb[j + 1] > 0.03
                C.append(shade(C_TIMBER, 0.95) if ledge else shade(tone[b_idx], 0.8))
        for j in range(nw - 1):
            F.append((fi(0, j), fi(0, j + 1), bi(0, j + 1), bi(0, j)))
            C.append(edge_col)
            F.append((fi(nu - 1, j), bi(nu - 1, j), bi(nu - 1, j + 1), fi(nu - 1, j + 1)))
            C.append(edge_col)
        for i in range(nu - 1):
            F.append((fi(i, 0), bi(i, 0), bi(i + 1, 0), fi(i + 1, 0)))
            C.append(shade(edge_col, 0.7))
            F.append((fi(i, nw - 1), fi(i + 1, nw - 1), bi(i + 1, nw - 1), bi(i, nw - 1)))
            C.append(edge_col)
        accl = Acc()
        accl.add(Vw, F, C)
        # the hinge straps (long iron straps on the outer face, flush with it) and the pintles driven 8 cm into the jamb
        acch = Acc()
        for zc in (0.44, 1.89):
            (ua, ub), (va, vb_), (wa, wb) = (0.0, 1.05), (-0.0305, -0.0225), (zc - 0.05, zc + 0.05)
            pts = []
            for w_ in (wa, wb):
                for v_, u_ in ((va, ua), (vb_, ua), (vb_, ub), (va, ub)):
                    pts.append((u_, v_, w_))
            acch.add(leaf_to_world(np.array(pts), (hx, hinge_y), psi, u0, sag_rad, hz_lo, LEAF_BOTTOM), list(BOX_FACES), vary(C_IRON, rng_l, 0.1))
        for hz in (hz_lo, hz_hi):
            V, F2 = box(hx - 0.06, hx + 0.06, hinge_y - 0.035, hinge_y + 0.15, hz - 0.07, hz + 0.07)
            acch.add(V, F2, C_RUST if rng_l.random() < 0.3 else C_IRON)
        out['leaf ' + tag] = B.emit(accl, f'{tag} door leaf', 'timber.door', 'door')
        out['hinges ' + tag] = B.emit(acch, f'{tag} door hinges', 'iron.fitting', 'iron')

    # ---------------------------------------------------------------- 9. three empty box stalls: partitions (boards + open rails), manger on two short posts, hay rack, tie ring
    # the partitions are made in two halves each (front and back of the mid post): the surface pass leans a fence about the foot of its object, so a short object keeps its small lean small; the boards are sunk
    # 2 cm into the floor and the rails go 8 cm into the posts, so that lean never lifts a board or pulls a rail out
    for pi, px in enumerate((22.4, 25.6)):
        for half, (y_a, y_b, p_a, p_b) in enumerate(((38.8, 40.15, 38.7, 40.25), (40.35, 41.77, 40.25, 41.87))):
            acc_b, acc_r = Acc(), Acc()
            y = y_a
            while y < y_b - 0.01:
                w = 0.135 + 0.03 * rng.random()
                if y_b - (y + w) < 0.13:
                    w = y_b - y
                y1 = y + w - 0.004
                V, F = lofted_post(px, (y + y1) / 2, FLOOR_TOP - 0.012, 1.38 + 0.04 * rng.random(), 0.035, y1 - y, lean=((rng.random() - 0.5) * 0.006, 0.0))
                acc_b.add(V, F, vary(C_TIMBER, rng, 0.13))
                y += w
            for z0, z1 in ((1.42, 1.49), (1.78, 1.86), (2.12, 2.20)):
                V, F = box(px - 0.025, px + 0.025, p_a + 0.02, p_b - 0.02, z0, z1)
                acc_r.add(V, F, vary(C_TIMBER, rng, 0.1))
            out[f'part boards {pi}{half}'] = B.emit(acc_b, f'stall partition {pi + 1} boards {("front", "back")[half]}', 'timber.fence', 'timber')
            out[f'part rails {pi}{half}'] = B.emit(acc_r, f'stall partition {pi + 1} rails {("front", "back")[half]}', 'timber.fence', 'timber')
    for si, c in enumerate(STALL_C):
        # the manger: an empty open box, 1.0 x 0.4 m, rim at 1.1 m, on two short posts
        zb, zt, wall = 0.80, 1.10, 0.045
        x0, x1, y0, y1 = c - 0.5, c + 0.5, 41.37, 41.77
        V, F = [], []
        ob = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        ib = [(x0 + wall, y0 + wall), (x1 - wall, y0 + wall), (x1 - wall, y1 - wall), (x0 + wall, y1 - wall)]
        for (x, y) in ob:
            V.append((x, y, zb))
        for (x, y) in ob:
            V.append((x, y, zt))
        for (x, y) in ib:
            V.append((x, y, zt))
        for (x, y) in ib:
            V.append((x, y, zb + wall))
        F = [(0, 3, 2, 1)]
        for k in range(4):
            k2 = (k + 1) % 4
            F.append((k, k2, 4 + k2, 4 + k))                       # outer walls
            F.append((4 + k, 4 + k2, 8 + k2, 8 + k))               # the rim
            F.append((8 + k, 8 + k2, 12 + k2, 12 + k))             # inner walls
        F.append((12, 13, 14, 15))                                 # inner bottom
        acc = Acc()
        acc.add(np.array(V, float), F, [vary(C_TIMBER, rng, 0.1)] * len(F), closed=True)
        out[f'manger {si}'] = B.emit(acc, f'stall {si + 1} manger', 'timber.generic', 'trough')
        for k, dx in enumerate((-0.35, 0.35)):
            acc_p = Acc()
            V, F = lofted_post(c + dx, 41.57, FLOOR_TOP, zb + 0.01, 0.10, 0.10, lean=(0.0, 0.0))        # 1 cm into the manger's floor
            acc_p.add(V, F, vary(C_OAK, rng, 0.1))
            B.emit(acc_p, f'manger post {si + 1} {k + 1}', 'timber.post', 'timber')
        # the hay rack: three rails in the wall plane between the two studs that flank the stall's manger, each tenoned 8 cm into both studs, the lowest at 1.5 m
        acc = Acc()
        for z0 in (1.50, 1.78, 2.06):
            V, F = box(c - 0.90 + 0.02, c + 0.90 - 0.02, 41.82, 41.88, z0, z0 + 0.07)
            acc.add(V, F, vary(C_TIMBER, rng, 0.1))
        out[f'rack {si}'] = B.emit(acc, f'stall {si + 1} hay rack', 'timber.fence', 'timber')
        # the tie ring: an iron plate on the wall boards and a ring hanging from it
        acc = Acc()
        rx = c + 0.65
        V, F = box(rx - 0.05, rx + 0.05, 41.93, 41.97, 1.46, 1.58)
        acc.add(V, F, C_IRON)
        V, F = torus(rx, 41.945, 1.46 - 0.06 + 0.004, 0.048, 0.012, plane='xz')
        acc.add(V, F, mixc(C_IRON, C_RUST, 0.25))
        out[f'ring {si}'] = B.emit(acc, f'stall {si + 1} tie ring', 'iron.fitting', 'iron', bevel=False)

    # ---------------------------------------------------------------- 10. the yard fittings, seated on the yard: the empty trough (a hollowed log) on two stone blocks, the bare hitching rail
    pk_parts.refresh_ground()

    def ground_max(cx, cy, sx, sy):
        lo, hi = (cx - sx / 2, cy - sy / 2, 0.0), (cx + sx / 2, cy + sy / 2, 0.0)
        z, _ = pk_parts.ground_under_box(lo, hi)
        return float(z if z is not None else pk.ground_height_at(cx, cy))
    tx, ty = 31.2, 34.2
    bx = (tx - 0.55, tx + 0.55)
    gz = [ground_max(x, ty, 0.34, 0.40) for x in bx]
    ztop = max(gz) + 0.22
    acc = Acc()
    for x, g in zip(bx, gz):
        V, F = stone_blob(x, ty, g - 0.04, ztop, 0.34, 0.40, rng, wobble=0.08)
        acc.add(V, F, vary(C_STONE, rng, 0.12))
    obj = B.emit(acc, 'trough stone blocks', 'stone.footing', 'stone', sink=(0.04, max(gz)), absolute=True)
    out['trough blocks'] = obj
    # the hollowed log: an outer lofted solid minus a pocket (a boolean), lying along x with a flat underside on the blocks
    prof_out = [(-0.11, 0.0), (-0.20, 0.04), (-0.26, 0.12), (-0.285, 0.22), (-0.28, 0.31), (-0.27, 0.38)]
    prof_out = prof_out + [(-x, z) for x, z in reversed(prof_out)]
    rings = []
    for xs_ in np.linspace(-0.9, 0.9, 7):
        t = (xs_ + 0.9) / 1.8
        k = 1.0 + 0.04 * math.sin(3.1 * t + 0.7)
        rings.append([(xs_, ty + p[0] * k, ztop + p[1]) for p in prof_out])
    V, F = loft_rings(rings)
    mo = bpy.data.meshes.new('trough outer tmp')
    mo.from_pydata([tuple(v) for v in V], [], F)
    mo.update()
    prof_in = [(-0.17, 0.52), (-0.17, 0.30), (-0.15, 0.20), (-0.09, 0.14), (0.09, 0.14), (0.15, 0.20), (0.17, 0.30), (0.17, 0.52)]
    rings = []
    for xs_ in np.linspace(-0.76, 0.76, 5):
        rings.append([(xs_, ty + p[0], ztop + p[1]) for p in prof_in])
    V, F = loft_rings(rings)
    mi_ = bpy.data.meshes.new('trough pocket tmp')
    mi_.from_pydata([tuple(v) for v in V], [], F)
    mi_.update()
    for m_ in (mo, mi_):                                         # make the normals point out, for a clean boolean
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(m_)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(m_)
        bm.free()
    ob_o = bpy.data.objects.new('trough outer tmp', mo)
    ob_i = bpy.data.objects.new('trough pocket tmp', mi_)
    col = pk.begin_part(OWNER)
    col.objects.link(ob_o)
    col.objects.link(ob_i)
    ob_o.matrix_world = Matrix.Translation((tx, 0.0, 0.0))
    ob_i.matrix_world = Matrix.Translation((tx, 0.0, 0.0))
    bpy.context.view_layer.update()
    mod = ob_o.modifiers.new('cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = ob_i
    mod.solver = 'EXACT'
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    mesh_log = bpy.data.meshes.new_from_object(ob_o.evaluated_get(deps), preserve_all_data_layers=False, depsgraph=deps)
    bpy.data.objects.remove(ob_o, do_unlink=True)
    bpy.data.objects.remove(ob_i, do_unlink=True)
    bpy.data.meshes.remove(mo)
    bpy.data.meshes.remove(mi_)
    mesh_log.name = 'Stable trough'
    mesh_log.transform(Matrix.Translation((tx, 0.0, 0.0)))
    mesh_log.update()
    attr = mesh_log.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    log_cols = []
    for poly in mesh_log.polygons:
        up = poly.normal.z
        c = vary(C_TIMBER if up < 0.5 else mixc(C_TIMBER, C_SILVER, 0.25), rng, 0.08)
        log_cols.extend([c] * poly.loop_total)
    attr.data.foreach_set('color', np.asarray(log_cols, float).ravel())
    mesh_log.materials.clear()
    mesh_log.materials.append(M['trough'])
    obj = pk.new_part_object(OWNER, 'timber.generic', 'Stable trough', mesh_log)
    add_edge_rounding(obj, 'timber.generic')
    B.objects.append(obj)
    out['trough'] = obj
    # the bare hitching rail: two posts set into the ground and a rail tenoned into both
    hx = (16.6, 18.8)
    hy = 33.0
    gzp = [ground_max(x, hy, 0.16, 0.16) for x in hx]
    ztop_p = max(gzp) + 1.30
    hitch = []
    for k, (x, g) in enumerate(zip(hx, gzp)):
        acc = Acc()
        V, F = lofted_post(x, hy, g - 0.10, ztop_p, 0.16, 0.16, lean=((rng.random() - 0.5) * 0.02, (rng.random() - 0.5) * 0.02))
        acc.add(V, F, vary(C_TIMBER, rng, 0.1))
        hitch.append(B.emit(acc, f'hitching post {k + 1}', 'timber.post', 'timber', sink=(0.10, g), absolute=True))
    out['hitch posts'] = hitch
    zr = max(gzp) + 1.10
    acc = Acc()
    V, F = bowed_bar_x(hx[0], hx[1], hy, 0.09, zr - 0.045, zr + 0.045, 0.006, segments=6)      # tenoned 8 cm into each post (to the post's centre)
    acc.add(V, F, vary(C_TIMBER, rng, 0.1))
    out['hitch rail'] = B.emit(acc, 'hitching rail', 'timber.fence', 'timber', absolute=True)

    # ---------------------------------------------------------------- 11. the fallen shingle: three big pieces on the yard below the gap on the south slope (course 4, tab 23)
    fx, fy = (lost_south[0][1] if lost_south else 27.55), 35.05
    acc = Acc()
    piece_defs = [((0.0, 0.0), (0.17, 0.19), 0.35), ((0.20, -0.09), (0.11, 0.14), -0.9), ((-0.16, 0.13), (0.075, 0.15), 1.4)]
    for (ox, oy), (w, h), ang in piece_defs:
        cx, cy = fx + ox, fy + oy
        gz_p = ground_max(cx, cy, 0.25, 0.25)
        thick = 0.024
        z0p = gz_p - 0.012
        hw, hh = w / 2, h / 2
        corners = [(-hw, -hh * (0.9 + 0.2 * rng.random())), (hw, -hh), (hw * 0.95, hh * (0.8 + 0.3 * rng.random())), (-hw * 0.7, hh)]
        V = []
        for z in (z0p, z0p + thick):
            for (px, py) in corners:
                V.append((cx + px * math.cos(ang) - py * math.sin(ang), cy + px * math.sin(ang) + py * math.cos(ang), z))
        acc.add(np.array(V, float), list(BOX_FACES), vary(mixc(C_SHINGLE, C_SHINGLE_S, 0.3), rng, 0.1))
    out['fallen'] = B.emit(acc, 'fallen shingle pieces', 'roof.shingle', 'shingle', absolute=True, bevel=False)
    for o in B.objects:
        o['stable_part'] = True
    bpy.context.view_layer.update()
    total = len(B.objects)
    print(f'STABLE STAGE: objects created: {total}; changed: 0; deleted: 0 (apart from what an earlier run of this owner made); pad height G={G}')
    return {'objects': [o.name for o in B.objects], 'G': G}
