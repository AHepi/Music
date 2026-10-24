"""What this does: the PROPS part of the forest village (owner props, collection "Place: props", every object named "Prop ..."): the scattered mediaeval props. A well with a windlass, a rope and a bucket;
five barrels; three crates and chests (one broken); four slumped sacks; three buckets; a parked two-wheeled cart with its shafts down on a block and a spare wheel leaning on the stable's west wall; a woodpile with end stakes,
a chopping block with an axe stuck in it, chips and bark, and a stool; a haystack and two bales; six woven wattle hurdles; a bench with two jugs, a jug by cottage B, two baskets; a handbarrow; a leaning ladder; fifteen
loose straw scraps on the floor of the empty stable (3 small clusters, none piled); two beehive skeps on a low bench behind cottage B and a broken wheel by the road verge. No sign, no lettering, no animal, no person.

Built from the ground up, every part carried: each log lies on the ground or on the logs under it, each stake is driven into the ground, the posts of the well stand in the ground, the crossbeam and the roller are tenoned
into both posts, the rope hangs from the roller to the bucket's bail, the bucket stands on the curb, the cart's axle sits in both hubs, its bearers lie on the axle, its floor boards on the bearers, the shafts rest on a block,
a ladder stands on its two feet, a hurdle's woven panel is held by its three stakes. Wherever a part stands on a slope it is sunk into the ground on the high side (the note "pk_seat_sink" says how far), so nothing floats on the low side.
Character is SHAPE: no two barrels, sacks, hurdles or crates alike (heights, widths, a stave missing, a lid dished, a slump to one side, ragged tops), chips and bark lying about the block, a fallen board by the broken crate.
Colour is written into each mesh as a colour layer (Col) and read by a material of our own that carries a small picture, so the surface pass keeps our colours and adds its maps and wear on top (mud splash is a designed
colour band at the foot of wheels, barrels and sacks).
It is IDEMPOTENT: apply(options) first forgets what an earlier run of this owner made (pk.forget_part), then builds again with the same seed. It changes nothing that is not ours.
A concrete example: apply({'seed': 7}) twice gives the same objects. Options (all optional): seed (7), sack_slump (how far the sacks slump, 1.0), hay_shape (how broad the haystack is: 0.6 steep cone, 1.5 broad dome, 1.0),
weave (how deep the wicker weave stands out, 1.0), weave_rows (how many woven rows a hurdle has, 12), mud (how far the mud splash climbs, 1.0).
Frames and units: metres; x east, y north, z up.
"""
import math
import os
import sys

import numpy as np

import bpy
import bmesh
from mathutils import Matrix

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
for _path in (os.path.join(KIT, 'place-kit') if KIT else '', '/home/user/Music/plugins/explainer-film/kit/place-kit'):
    if _path and os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
import place_kit as pk  # noqa: E402
from place_kit import names as pk_names  # noqa: E402
from place_kit import parts as pk_parts  # noqa: E402

OWNER = 'props'


# ------------------------------------------------------------------ colour
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexl(h):
    h = h.lstrip('#')
    return (_lin(int(h[0:2], 16) / 255.0), _lin(int(h[2:4], 16) / 255.0), _lin(int(h[4:6], 16) / 255.0), 1.0)


def mixc(a, b, t):
    t = float(min(max(t, 0.0), 1.0))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def vary(c, rng, amount):
    f = 1.0 + amount * (rng.random() * 2 - 1)
    g = 1.0 + amount * 0.4 * (rng.random() * 2 - 1)
    return (min(c[0] * f * g, 1.0), min(c[1] * f, 1.0), min(c[2] * f / g, 1.0), 1.0)


C_TIMBER = hexl('#5A4C40')
C_TIMBER_L = hexl('#6E5D49')
C_OAK = hexl('#4B3F33')
C_FRESH = hexl('#8A6A45')
C_CUT = hexl('#A88B5C')
C_SILVER = hexl('#7A736A')
C_BARK = hexl('#4A3B2E')
C_STONE = hexl('#7C7A73')
C_STONE_L = hexl('#8F8C82')
C_STONE_D = hexl('#6B6A64')
C_MOSS = hexl('#5E8236')
C_MOSS_D = hexl('#4F6B3A')
C_IRON = hexl('#2E2B29')
C_RUST = hexl('#8A4B2C')
C_STRAW = hexl('#9C7A3F')
C_HAY = hexl('#9A8043')
C_HAY_D = hexl('#745C2E')
C_LINEN = hexl('#A8946A')
C_LINEN_D = hexl('#8C7A55')
C_JUG = hexl('#8A5E3C')
C_JUG_D = hexl('#6E4A30')
C_WICKER = hexl('#8A6A45')
C_WICKER_D = hexl('#6F5435')
C_MUD = hexl('#4F3E2C')
C_PIT = hexl('#1F1B17')
C_TWINE = hexl('#5A4630')


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


# ------------------------------------------------------------------ transforms
def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def xf(V, R=None, t=(0.0, 0.0, 0.0)):
    V = np.asarray(V, float)
    if R is not None:
        V = V @ np.asarray(R).T
    return V + np.asarray(t, float)


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
        self.mud = None

    def add(self, V, F, col=(0.5, 0.5, 0.5, 1.0), closed=True):
        V = np.asarray(V, float)
        F = [tuple(int(i) for i in f) for f in F]
        if closed and F and _signed_volume(V, F) < 0:
            F = [tuple(reversed(f)) for f in F]
        if callable(col):
            cols = [col(k, f, V) for k, f in enumerate(F)]
        elif isinstance(col, list):
            cols = col
        else:
            cols = [col] * len(F)
        self.V.append(V)
        for f, c in zip(F, cols):
            self.F.append(tuple(i + self.n for i in f))
            self.C.append(c)
        self.n += len(V)

    def empty(self):
        return self.n == 0

    def stacked(self):
        return np.vstack(self.V)

    def make(self, name, smooth=False):
        mesh = bpy.data.meshes.new(name)
        V = np.vstack(self.V)
        mesh.from_pydata([tuple(v) for v in V], [], self.F)
        mesh.update()
        cols = list(self.C)
        if self.mud is not None:
            ground_z, height, amount, rng = self.mud
            for i, f in enumerate(self.F):
                zc = float(np.mean([V[j][2] for j in f]))
                t = 1.0 - (zc - ground_z) / max(height, 1e-6)
                if t > 0:
                    t = min(t, 1.0) * amount * (0.55 + 0.45 * rng.random())
                    cols[i] = mixc(cols[i], C_MUD, min(t, 0.85))
        attr = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        loop_cols = []
        for f, col in zip(self.F, cols):
            loop_cols.extend([col] * len(f))
        attr.data.foreach_set('color', np.asarray(loop_cols, float).ravel())
        if smooth:
            try:
                mesh.shade_smooth()
            except Exception:  # noqa: BLE001
                pass
        return mesh


# ------------------------------------------------------------------ primitives (each returns vertices and faces of ONE closed solid)
BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box(x0, x1, y0, y1, z0, z1):
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return np.array(V, float), list(BOX_FACES)


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


def lathe(profile, n=14, rfun=None, phase=0.0, loop=False):
    """A surface of revolution round the z axis. profile: [(radius, z)] from bottom to top; a radius of 0 is a pole (a flat cap) when loop is False. loop=True closes the profile on itself (a ring, a hoop).
    rfun(k, row, z) -> factor for the radius of vertex k of ring row. Returns vertices, faces and, for each face, (row, k) so that a caller can colour it."""
    V, rows = [], []
    for ri, (r, z) in enumerate(profile):
        if (not loop) and r < 1e-9:
            rows.append(('p', len(V)))
            V.append((0.0, 0.0, z))
        else:
            idx = []
            for k in range(n):
                a = phase + 2 * math.pi * k / n
                rr = r * (rfun(k, ri, z) if rfun else 1.0)
                idx.append(len(V))
                V.append((rr * math.cos(a), rr * math.sin(a), z))
            rows.append(('r', idx))
    F, M = [], []
    count = len(rows)
    pairs = [(i, i + 1) for i in range(count - 1)] + ([(count - 1, 0)] if loop else [])
    for i, j in pairs:
        a, b = rows[i], rows[j]
        for k in range(n):
            k2 = (k + 1) % n
            if a[0] == 'r' and b[0] == 'r':
                F.append((a[1][k], a[1][k2], b[1][k2], b[1][k]))
            elif a[0] == 'p':
                F.append((a[1], b[1][k2], b[1][k]))
            else:
                F.append((a[1][k], a[1][k2], b[1]))
            M.append((i, k))
    return np.array(V, float), F, M


def tube(P, r, sides=6, phase=0.0):
    """A solid tube of radius r (a number, or one per point) along the polyline P, closed with flat ends."""
    P = np.asarray(P, float)
    r = np.full(len(P), float(r)) if np.isscalar(r) else np.asarray(r, float)
    keep = [0] + [i for i in range(1, len(P)) if np.linalg.norm(P[i] - P[i - 1]) > 1e-6]
    P, r = P[keep], r[keep]
    n = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    T /= np.linalg.norm(T, axis=1)[:, None]
    up = np.array([0.0, 0.0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    N = np.cross(T[0], up)
    N /= np.linalg.norm(N)
    rings = []
    for i in range(n):
        N = N - np.dot(N, T[i]) * T[i]
        N /= np.linalg.norm(N)
        B = np.cross(T[i], N)
        rings.append([P[i] + r[i] * (math.cos(phase + 2 * math.pi * s / sides) * N + math.sin(phase + 2 * math.pi * s / sides) * B) for s in range(sides)])
    return loft_rings(rings)


def prism_poly(poly_xy, z0, z1):
    """A solid standing on the polygon poly_xy between heights z0 and z1."""
    P = np.asarray(poly_xy, float)
    n = len(P)
    V = np.vstack([np.column_stack([P, np.full(n, z0)]), np.column_stack([P, np.full(n, z1)])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def extrude_x(poly_yz, x0, x1):
    P = np.asarray(poly_yz, float)
    n = len(P)
    V = np.vstack([np.column_stack([np.full(n, x0), P[:, 0], P[:, 1]]), np.column_stack([np.full(n, x1), P[:, 0], P[:, 1]])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def extrude_y(poly_xz, y0, y1):
    P = np.asarray(poly_xz, float)
    n = len(P)
    V = np.vstack([np.column_stack([P[:, 0], np.full(n, y0), P[:, 1]]), np.column_stack([P[:, 0], np.full(n, y1), P[:, 1]])])
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return V, F


def union(parts):
    """The boolean union of closed solids [(V, F), ...] as ONE connected mesh (vertices, faces). Uses Blender's exact boolean on temporary objects."""
    temp_objects, temp_meshes = [], []

    def make(V, F, tag):
        m = bpy.data.meshes.new(tag)
        m.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
        m.update()
        bm = bmesh.new()
        bm.from_mesh(m)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(m)
        bm.free()
        o = bpy.data.objects.new(tag, m)
        bpy.context.scene.collection.objects.link(o)
        temp_objects.append(o)
        temp_meshes.append(m)
        return o
    base = make(parts[0][0], parts[0][1], 'prop_u0')
    for i, (V, F) in enumerate(parts[1:], 1):
        other = make(V, F, f'prop_u{i}')
        mod = base.modifiers.new('u', 'BOOLEAN')
        mod.operation = 'UNION'
        mod.solver = 'EXACT'
        mod.object = other
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        result = bpy.data.meshes.new_from_object(base.evaluated_get(deps), preserve_all_data_layers=False, depsgraph=deps)
        base.modifiers.remove(mod)
        old = base.data
        base.data = result
        temp_meshes.append(result)
        if old in temp_meshes:
            temp_meshes.remove(old)
        bpy.data.meshes.remove(old)
    me = base.data
    count = len(me.vertices)
    flat = np.empty(count * 3, dtype=np.float64)
    me.vertices.foreach_get('co', flat)
    V = flat.reshape(count, 3).copy()
    F = [tuple(p.vertices) for p in me.polygons]
    for o in temp_objects:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in temp_meshes:
        try:
            bpy.data.meshes.remove(m)
        except Exception:  # noqa: BLE001
            pass
    return V, F


# ------------------------------------------------------------------ materials (our own, with a small picture so the surface pass keeps them)
def tile_image():
    name = 'Prop tile'
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, 64, 64, alpha=False)
        img.colorspace_settings.name = 'Non-Color'                 # first, before the pixels (blender-5-traps.md, trap 1)
        rng = np.random.default_rng(17)
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


# ------------------------------------------------------------------ the ground and the keep-clear shapes
HIGH_ROAD = [(-140, -34), (-110, -18), (-80, -6), (-45, -1.5), (-12, 0.5), (20, 2), (52, -2.5), (85, -10), (115, -19), (140, -33)]
LANE = [(20, 2), (20.5, 10), (22, 18), (24, 26), (24.3, 34.2)]
DOOR_STEPS = {'A': (-32.66, 7.14, -31.34, 7.76), 'B': (-6.92, 6.68, -5.08, 7.70), 'C': (-26.58, -8.46, -25.42, -7.69), 'D': (3.41, -6.42, 4.59, -5.31)}
FOOTPRINTS = {'A': (-37.6, 7.55, -26.4, 12.45), 'A lean-to': (-40.4, 8.0, -37.55, 11.6), 'B': (-9.22, 7.19, -2.78, 11.82), 'B chimney': (-2.94, 8.96, -1.93, 10.03),
              'C': (-29.87, -12.98, -22.13, -8.03), 'D': (2.14, -10.21, 5.86, -5.79), 'stable': (19.09, 35.99, 28.91, 42.01)}
STABLE_DOORWAY = (21.4, 34.6, 26.6, 36.8)
FOOTFALL = [((-32, 7.4), (-32, 1.9)), ((-6, 7.1), (-6, 3.2)), ((-26, -8.0), (-26, -2.8)), ((4, -5.7), (4, -1.4)), ((-17.5, 3.2), (-17.5, 5.2))]
STABLE_YARD = (19.5, 24.0, 29.5, 36.0)
WELL_C = (-17.5, 6.0)


def seg_dist(p, a, b):
    p, a, b = np.asarray(p, float), np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = float(np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab)))


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[i + 1]) for i in range(len(poly) - 1))


def box_dist(x, y, b):
    dx = max(b[0] - x, 0.0, x - b[2])
    dy = max(b[1] - y, 0.0, y - b[3])
    return math.hypot(dx, dy)


def clear_problems(x, y, r, allow=()):
    """Reasons why a prop with a footprint of radius r at (x, y) may not stand there (the contracts with the ground, the cottages and the stable). An empty list means it is clear."""
    found = []
    if 'road' not in allow:
        if poly_dist((x, y), HIGH_ROAD) - r < 2.5 + 0.6:
            found.append('within 0.6 m of the high road bank or on it')
        if poly_dist((x, y), LANE) - r < 1.7 + 0.6:
            found.append('within 0.6 m of the lane bank or on it')
    for key, b in DOOR_STEPS.items():
        if box_dist(x, y, b) - r < 1.0:
            found.append(f'within 1.0 m of the doorstep of {key}')
        if b[0] - 0.6 - r < x < b[2] + 0.6 + r and b[1] - 0.6 - r < y < b[3] + 1.0 + r:
            found.append(f'in the door strip of {key}')
    for a, b in FOOTFALL:
        if seg_dist((x, y), a, b) - r < 0.5:
            found.append('on a footfall strip')
    if 'stable_yard' not in allow and box_dist(x, y, STABLE_YARD) - r <= 0.0:
        found.append('in the stable yard')
    if box_dist(x, y, STABLE_DOORWAY) - r <= 0.0:
        found.append('in the stable doorway')
    for key, b in FOOTPRINTS.items():
        if key in allow:
            continue
        if box_dist(x, y, b) - r < 0.0:
            found.append(f'inside the footprint of {key}')
    well_box = (WELL_C[0] - 0.65, WELL_C[1] - 0.65, WELL_C[0] + 0.65, WELL_C[1] + 0.65)
    if 'well' not in allow and box_dist(x, y, well_box) - r < 0.8:
        found.append('within 0.8 m of the well curb')
    try:
        if 'masks' not in allow and pk.is_keep_clear(x, y):
            found.append('the plan masks say keep clear')
    except Exception:  # noqa: BLE001
        pass
    return found


def ground5(V):
    """The ground height read where the construction check reads it: under the centre and the four corners (pulled in a tenth) of the box of V."""
    V = np.asarray(V, float)
    z, _ = pk_parts.ground_under_box(V.min(axis=0), V.max(axis=0))
    return float(z if z is not None else 0.0)


def seat_world(V_list, sink=0.012):
    """Shifts every array in V_list by one amount so that the lowest point of all of them is `sink` below the ground read under the whole group. Returns (shift, ground)."""
    V_all = np.vstack(V_list)
    g = ground5(V_all)
    shift = (g - sink) - float(V_all[:, 2].min())
    return shift, g


# ------------------------------------------------------------------ the objects of the part
class Maker:
    def __init__(self, mats, mud_amount):
        self.M, self.objects, self.mud_amount = mats, [], mud_amount

    def emit(self, acc, name, role, mat, sink=None, smooth=False, bevel=True, mud=None, mud_rng=None, rests_on_other=False):
        if acc.empty():
            return None
        if mud is not None and self.mud_amount > 0:
            acc.mud = (mud[0], mud[1], mud[2] * self.mud_amount, mud_rng or np.random.default_rng(3))
        full = f'Prop {name}'
        mesh = acc.make(full, smooth=smooth)
        mesh.materials.append(self.M[mat])
        obj = pk.new_part_object(OWNER, role, full, mesh)
        if not bevel:
            obj['pk_bevelled'] = 1
        if sink is not None and not rests_on_other:
            obj['_want_sink'] = sink if isinstance(sink, str) else float(sink)
        self.objects.append(obj)
        return obj


PROBLEMS = []


def check_spot(label, x, y, r, allow=()):
    for reason in clear_problems(x, y, r, allow):
        PROBLEMS.append(f'{label} at ({x:.2f}, {y:.2f}) r {r:.2f}: {reason}')


def mossy_stone_colour(kind, rng, normal, moss_top=0.35):
    base = vary(mixc(C_STONE, C_STONE_L, rng.random() * 0.6), rng, 0.08)
    if normal[2] > 0.6 and rng.random() < moss_top:
        return vary(mixc(C_MOSS_D, C_MOSS, rng.random()), rng, 0.08)
    if normal[2] < 0.3 and abs(normal[2]) < 0.2 and rng.random() < 0.10:
        return vary(C_MOSS_D, rng, 0.08)
    return base


# ------------------------------------------------------------------ the wheel (one connected solid: bore, hub, ten spokes, rim)
def wheel_mesh(R=0.545, spokes=10, hub_len=0.16, rim_w=0.075, rim_t=0.062, spoke_t=0.046, spoke_w=0.052, bore=0.034, rng=None, missing=(), rim_gap=None, K=4):
    """A cart wheel standing in the x-z plane with its axle along y, centre at the origin. Returns vertices and faces of ONE closed solid. `missing` lists the spokes that are broken off, rim_gap=(k0, k1) cuts the rim."""
    rng = rng or np.random.default_rng(1)
    M = spokes * K
    rim_in = R - rim_t
    hub_b = 0.15
    rings = [(bore, hub_len), (0.095, hub_len), (hub_b, spoke_t + 0.01), (rim_in, rim_w), (R, rim_w * 0.92)]
    ang = [[2 * math.pi * k / M for k in range(M)] for _ in rings]
    for s in range(spokes):
        centre = 2 * math.pi * (K * s + (K - 1) / 2.0) / M
        for ri in (2, 3):
            r = rings[ri][0]
            half = (spoke_w / 2.0) / r
            ang[ri][K * s + K // 2 - 1] = centre - half
            ang[ri][K * s + K // 2] = centre + half
    V = []
    index = {}
    for side in (1, -1):
        for ri, (r, T) in enumerate(rings):
            for k in range(M):
                rr = r * (1.0 + (0.012 * (rng.random() - 0.5) if ri == 4 else 0.0))
                a = ang[ri][k]
                index[(side, ri, k)] = len(V)
                V.append((rr * math.cos(a), side * T / 2.0 * (1.0 + 0.06 * (rng.random() - 0.5)), rr * math.sin(a)))
    faces = []
    for ri in (0, 1, 3):
        for k in range(M):
            if ri == 3 and rim_gap is not None and rim_gap[0] <= k < rim_gap[1]:
                continue
            k2 = (k + 1) % M
            faces.append((ri, k, ri, k2, ri + 1, k2, ri + 1, k))
    for s in range(spokes):
        if s in missing:
            continue
        k = K * s + K // 2 - 1
        k2 = k + 1
        faces.append((2, k, 2, k2, 3, k2, 3, k))
    front = []
    for (a0, k0, a1, k1, b1, k2, b2, k3) in faces:
        front.append(tuple(index[(1, r, k)] for r, k in ((a0, k0), (a1, k1), (b1, k2), (b2, k3))))
    back = []
    for (a0, k0, a1, k1, b1, k2, b2, k3) in faces:
        back.append(tuple(index[(-1, r, k)] for r, k in ((b2, k3), (b1, k2), (a1, k1), (a0, k0))))
    # walls on every boundary edge of the front sheet
    edge_count = {}
    face_of_edge = {}
    for fi, f in enumerate(front):
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            key = (min(a, b), max(a, b))
            edge_count[key] = edge_count.get(key, 0) + 1
            face_of_edge[key] = (fi, a, b)
    Va = np.array(V, float)
    count = len(V) // 2
    walls = []
    for key, c in edge_count.items():
        if c != 1:
            continue
        fi, a, b = face_of_edge[key]
        centre = Va[list(front[fi])].mean(axis=0)
        mid = (Va[a] + Va[b]) / 2.0
        outward = mid - centre
        outward[1] = 0.0
        quad = (a, b, b + count, a + count)
        n = np.cross(Va[quad[1]] - Va[quad[0]], Va[quad[3]] - Va[quad[0]])
        walls.append(quad if np.dot(n, outward) > 0 else tuple(reversed(quad)))
    return Va, front + back + walls


def tyre_mesh(R_inner, width=0.055, thick=0.013, n=40):
    """An iron tyre: a rectangular hoop round the z... axis y: returned with its axis along y, centre at the origin."""
    prof = [(R_inner, -width / 2), (R_inner + thick, -width / 2), (R_inner + thick, width / 2), (R_inner, width / 2)]
    V, F, _ = lathe(prof, n=n, loop=True)
    V = xf(V, Rx(math.pi / 2))                         # lathe axis z -> y
    return V, F


def apply(options=None):
    options = dict(options or {})
    seed = int(options.get('seed', 7))
    sack_slump = float(options.get('sack_slump', 1.0))
    hay_shape = float(options.get('hay_shape', 1.0))
    weave = float(options.get('weave', 1.0))
    weave_rows = int(options.get('weave_rows', 10))
    mud_amount = float(options.get('mud', 1.0))
    PROBLEMS.clear()
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    bpy.context.view_layer.update()
    pk_parts.refresh_ground()
    mats = dict(wood=make_material('PK prop. wood', 0.88), stone=make_material('PK prop. stone', 0.9), iron=make_material('PK prop. iron', 0.55), straw=make_material('PK prop. straw', 0.95),
                cloth=make_material('PK prop. cloth', 0.95), ceramic=make_material('PK prop. ceramic', 0.6), wicker=make_material('PK prop. wicker', 0.9))
    mk = Maker(mats, mud_amount)
    out = {}

    # ================================================================== 1. THE WELL (centre WELL_C)
    cx, cy = WELL_C
    rng = np.random.default_rng(seed * 100 + 1)
    # the base level: the highest ground under the curb ring and the two posts
    ring_pts = [(cx + 0.55 * math.cos(a), cy + 0.55 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
    post_x = (cx - 1.0, cx + 1.0)
    gz_post = [ground5(box(x - 0.08, x + 0.08, cy - 0.08, cy + 0.08, 0, 1)[0]) for x in post_x]
    zb = max([pk.ground_height_at(x, y) for x, y in ring_pts] + gz_post)
    # curb: 3 courses of chunky blocks, each course 0.3 m, bottoms sunk into the ground
    acc = Acc()
    blocks = []                                                      # (angle0, angle1, top) of the last course, for the bucket
    prev = []
    n_blocks = (9, 8, 9)
    r_in, r_out = 0.40, 0.65
    for course in range(3):
        nb = n_blocks[course]
        off = (0.5 if course == 1 else 0.0) * 2 * math.pi / nb + rng.random() * 0.1
        cur = []
        for b in range(nb):
            a0 = off + 2 * math.pi * b / nb + 0.012 * (rng.random() - 0.5)
            a1 = off + 2 * math.pi * (b + 1) / nb - 0.012 + 0.012 * (rng.random() - 0.5)
            am = (a0 + a1) / 2
            ri = r_in + 0.02 * (rng.random() - 0.5)
            ro = r_out + 0.03 * (rng.random() - 0.5) - (0.02 if course == 2 else 0.0)
            plan_bottom = [(ri * math.cos(a0), ri * math.sin(a0)), (ro * math.cos(a0), ro * math.sin(a0)), (ro * math.cos(am), ro * math.sin(am)), (ro * math.cos(a1), ro * math.sin(a1)),
                           (ri * math.cos(a1), ri * math.sin(a1)), (ri * math.cos(am), ri * math.sin(am))]
            plan_top = [(px * (1 + 0.03 * (rng.random() - 0.5)) + 0.01 * (rng.random() - 0.5), py * (1 + 0.03 * (rng.random() - 0.5)) + 0.01 * (rng.random() - 0.5)) for px, py in plan_bottom]
            top_z = zb + 0.30 * (course + 1) + 0.012 * (rng.random() - 0.5) * 2
            if course == 0:
                probe = np.array([[cx + p[0], cy + p[1], 0.0] for p in plan_bottom])
                g = ground5(probe)
                z0 = g - 0.04
            else:
                below = [t for (aa0, aa1, t) in prev if max(min(aa1, a1 + sh) - max(aa0, a0 + sh) for sh in (-2 * math.pi, 0.0, 2 * math.pi)) > 0.02]
                z0 = (max(below) if below else zb + 0.30 * course) - 0.006
            V = np.vstack([np.column_stack([np.array(plan_bottom) + [cx, cy], np.full(6, z0)]),
                           np.column_stack([np.array(plan_top) + [cx, cy], top_z + 0.012 * (np.random.default_rng(seed + b + 13 * course).random(6) - 0.5)])])
            Vb, Fb = V, [tuple(range(5, -1, -1)), tuple(range(6, 12))] + [(i, (i + 1) % 6, 6 + (i + 1) % 6, 6 + i) for i in range(6)]
            moss_t = 0.45 if course == 2 else 0.2
            acc.add(Vb, Fb, lambda k, f, V_, rr=rng, mt=moss_t: mossy_stone_colour('curb', rr, np.cross(V_[f[1]] - V_[f[0]], V_[f[-1]] - V_[f[0]]) / (np.linalg.norm(np.cross(V_[f[1]] - V_[f[0]], V_[f[-1]] - V_[f[0]])) + 1e-9), mt))
            cur.append((a0, a1, float(Vb[6:, 2].max())))
        prev = cur
        if course == 2:
            blocks = cur
    # the dark shaft inside the curb (no water: a dark floor of the pit, level with the ground)
    pit_z = pk.ground_height_at(cx, cy) + 0.03
    pv, pf, _ = lathe([(0.0, pit_z - 0.02), (0.41, pit_z - 0.02), (0.41, pit_z), (0.0, pit_z)], n=16)
    acc.add(pv + np.array([cx, cy, 0.0]), pf, C_PIT)
    curb = mk.emit(acc, 'well curb', 'stone.well', 'stone', sink=0.04, bevel=True)
    out['curb'] = curb
    curb_top = max(t for (_, _, t) in blocks)

    # posts, crossbeam, roller, crank, rope, bucket
    rng = np.random.default_rng(seed * 100 + 2)
    z_top = zb + 2.2
    post_objs = []
    for i, (px, gz) in enumerate(zip(post_x, gz_post)):
        acc = Acc()
        lean = ((rng.random() - 0.5) * 0.02, (rng.random() - 0.5) * 0.02)
        bottom = [(px - 0.08, cy - 0.08, gz - 0.06), (px + 0.08, cy - 0.08, gz - 0.06), (px + 0.08, cy + 0.08, gz - 0.06), (px - 0.08, cy + 0.08, gz - 0.06)]
        top = [(x + lean[0], y + lean[1], z_top) for x, y, _ in bottom]
        acc.add(np.array(bottom + top, float), list(BOX_FACES), vary(C_TIMBER, rng, 0.1))
        post_objs.append(mk.emit(acc, f'well post {"west" if i == 0 else "east"}', 'timber.post', 'wood', sink=0.06))
    acc = Acc()
    beam_z = z_top - 0.03                                  # the crossbeam lies on the post tops, sunk 3 cm into them (a tenon in each post head)
    V, F = box(post_x[0] - 0.08, post_x[1] + 0.08, cy - 0.075, cy + 0.075, beam_z, beam_z + 0.14)
    acc.add(V, F, vary(C_TIMBER_L, rng, 0.08))
    out['beam'] = mk.emit(acc, 'well crossbeam', 'timber.beam', 'wood')
    roller_z = zb + 1.70
    path = [(post_x[0] + 0.005, cy, roller_z), (post_x[1] + 0.30, cy, roller_z)]
    V, F = tube(path, 0.07, sides=8)
    acc = Acc()
    acc.add(V, F, vary(C_TIMBER, rng, 0.08))
    out['roller'] = mk.emit(acc, 'well roller', 'timber.beam', 'wood')
    # the crank: ONE iron piece, a stub driven 10 cm into the roller's east end, an arm and a grip
    ex = post_x[1] + 0.30
    acc = Acc()
    path = [(ex - 0.10, cy, roller_z), (ex + 0.06, cy, roller_z), (ex + 0.06, cy - 0.10, roller_z - 0.01), (ex + 0.06, cy - 0.27, roller_z - 0.04), (ex + 0.06, cy - 0.30, roller_z - 0.12),
            (ex + 0.06, cy - 0.30, roller_z - 0.30)]
    V, F = tube(path, [0.05, 0.05, 0.026, 0.026, 0.030, 0.036], sides=6)
    acc.add(V, F, mixc(C_IRON, C_RUST, 0.15))
    out['crank'] = mk.emit(acc, 'well crank', 'iron.fitting', 'iron', bevel=False)
    # the bucket stands on the curb at the east side, under the roller's unwound rope
    ba = 0.0
    bx, by = cx + 0.525 * math.cos(ba), cy + 0.525 * math.sin(ba)
    out['well_bucket_spot'] = (bx, by)
    rope_x = bx
    bucket_z0 = curb_top - 0.004

    # ================================================================== helper: a staved bucket
    def bucket_mesh(rng_b, h=0.30, r0=0.115, r1=0.155, wall=0.014, n=14):
        prof = [(0.0, 0.0), (r0, 0.0), (r0 + 0.004, 0.012), (r1, h), (r1 - wall, h), (r0 + 0.004 - wall, 0.03), (0.0, 0.03)]
        stave = [1.0 + 0.012 * (rng_b.random() - 0.5) for _ in range(n)]
        V, F, M_ = lathe(prof, n=n, rfun=lambda k, ri, z: stave[k] * (1.0 + 0.012 * math.sin(3 * k)))
        shade = [vary(mixc(C_TIMBER, C_TIMBER_L, rng_b.random()), rng_b, 0.1) for _ in range(n)]

        def colour(k, f, V_, M_=M_, shade=shade):
            row, kk = M_[k]
            if row >= 3:
                return mixc(shade[kk], C_OAK, 0.4)
            return shade[kk]
        return V, F, colour

    def bucket_iron(Vb, rng_b, h, r0, r1, bail_up=True, yaw=0.0, centre=(0, 0)):
        """Two hoops and a bail for a bucket (vertices of the hoops and the bail, in the same frame as the bucket mesh before it is moved)."""
        parts = []
        for zf in (0.07, 0.23):
            zz = zf * h / 0.30
            rr = r0 + (r1 - r0) * zz / h + 0.004
            prof = [(rr - 0.007, zz - 0.014), (rr + 0.006, zz - 0.014), (rr + 0.006, zz + 0.014), (rr - 0.007, zz + 0.014)]
            Vh, Fh, _ = lathe(prof, n=14, loop=True)
            parts.append((Vh, Fh))
        return parts

    def bail_mesh(h, r1, up=True, rng_b=None):
        top = h + (0.22 if up else 0.08)
        pts = [(-(r1 - 0.004), 0.0, h - 0.015), (-(r1 + 0.03), 0.0, h + 0.03)]
        for a_ in np.linspace(math.pi, 0.0, 11)[1:-1]:
            pts.append(((r1 + 0.03) * math.cos(a_), 0.0, h + 0.03 + (top - h - 0.03) * math.sin(a_)))
        pts += [((r1 + 0.03), 0.0, h + 0.03), ((r1 - 0.004), 0.0, h - 0.015)]
        return tube(np.array(pts, float), 0.0065, sides=5)

    iron_acc = Acc()                      # all the bands, hoops, bails and straps: ONE iron mesh, every loose piece touching the thing it holds

    def add_bucket(label, x, y, z0, rng_b, yaw, h=0.30, up_bail=False, on_ground=True, tip=None):
        r0 = 0.115 * (0.95 + 0.1 * rng_b.random())
        r1 = 0.155 * (0.95 + 0.1 * rng_b.random())
        Vb, Fb, colour = bucket_mesh(rng_b, h, r0, r1)
        acc_b = Acc()
        pieces = bucket_iron(Vb, rng_b, h, r0, r1)
        bailV, bailF = bail_mesh(h, r1, up=up_bail, rng_b=rng_b)
        R = Rz(yaw)
        Vw = xf(Vb, R, (x, y, 0.0))
        if on_ground:
            shift, g = seat_world([Vw], sink=0.01)
        else:
            shift, g = z0 - Vw[:, 2].min(), None
        Vw[:, 2] += shift
        acc_b.add(Vw, Fb, colour)
        for Vh, Fh in pieces:
            iron_acc.add(xf(Vh, R, (x, y, shift)), Fh, mixc(C_IRON, C_RUST, 0.10 * rng_b.random()))
        iron_acc.add(xf(bailV, R, (x, y, shift)), bailF, C_IRON)
        obj = mk.emit(acc_b, label, 'prop.wood', 'wood', sink=0.01, rests_on_other=not on_ground, mud=(g, 0.14, 0.8) if on_ground else None, mud_rng=rng_b)
        return obj, shift, Vw

    rng = np.random.default_rng(seed * 100 + 3)
    bucket_obj, bshift, bV = add_bucket('bucket well', bx, by, bucket_z0, rng, 0.4, up_bail=True, on_ground=False)
    out['bucket well'] = bucket_obj
    bail_top = float(bV[:, 2].min()) + 0.30 + 0.22
    # the rope: five turns on the roller (x from rope_x - 0.42 to rope_x), then down to the bail with a slack bow
    rng = np.random.default_rng(seed * 100 + 4)
    pts = []
    turns = 5
    x_start = rope_x - 0.42
    steps = turns * 10
    rr = 0.074
    for i in range(steps + 1):
        t = i / steps
        a_ = 2 * math.pi * turns * t - math.pi / 2
        pts.append((x_start + 0.42 * t, cy + rr * math.cos(a_), roller_z + rr * math.sin(a_)))
    last = np.array(pts[-1])
    end = np.array([rope_x, by, bail_top])
    D = last[2] - end[2]
    drop = [last + np.array([0.012, -0.02, -0.35 * D]), last + np.array([-0.008, 0.025, -0.70 * D]), end]
    path = np.array(pts + [tuple(p) for p in drop], float)
    V, F = tube(path, 0.0125, sides=5)
    acc = Acc()
    acc.add(V, F, lambda k, f, V_, rr_=rng: vary(mixc(C_LINEN_D, C_TIMBER_L, 0.3), rr_, 0.12))
    out['rope'] = mk.emit(acc, 'well rope', 'prop.rope', 'cloth', bevel=False)

    # ================================================================== 2. BARRELS
    def barrel_mesh(H, Rb, rng_b, open_top=False, n=14):
        r_end = Rb * 0.80
        zs = np.linspace(0.0, 1.0, 9)
        belly = [(r_end + (Rb - r_end) * math.sin(math.pi * t) ** 0.9, H * t) for t in zs]
        if open_top:
            prof = [(0.0, 0.0)] + [(r, z) for r, z in belly] + [(belly[-1][0] - 0.022, H), (belly[-1][0] - 0.022, 0.05), (0.0, 0.05)]
        else:
            prof = [(0.0, 0.0), (r_end * 0.94, 0.0)] + belly[:-1] + [(belly[-1][0], H), (belly[-1][0] * 0.90, H), (belly[-1][0] * 0.88, H - 0.035), (0.0, H - 0.035)]
        stave = [1.0 + 0.010 * (rng_b.random() - 0.5) for _ in range(n)]
        tone = [vary(mixc(C_TIMBER, C_TIMBER_L, rng_b.random()), rng_b, 0.1) for _ in range(n)]
        if rng_b.random() < 0.7:
            tone[int(rng_b.integers(0, n))] = vary(C_FRESH, rng_b, 0.05)                       # one replaced stave
        V, F, M_ = lathe(prof, n=n, rfun=lambda k, ri, z: stave[k])

        def colour(k, f, V_, M_=M_):
            row, kk = M_[k]
            if row <= 0:
                return C_OAK
            if row >= len(prof) - 3:
                return mixc(C_TIMBER_L, C_SILVER, 0.4)
            return tone[kk]

        def radius_at(z):
            return float(np.interp(z, [p[1] for p in belly], [p[0] for p in belly]))
        return V, F, colour, radius_at

    barrels = [('barrel 1', -35.55, 7.12, 0.78, 0.34, 0.2, False, 'stand'), ('barrel 2', -34.95, 6.30, 0.62, 0.285, 1.4, False, 'stand'),
               ('barrel 3', -10.70, 6.30, 0.88, 0.32, 0.0, False, 'lie'), ('barrel 4', 30.80, 40.50, 0.94, 0.38, 2.2, False, 'stand'), ('barrel 5', 30.55, 41.75, 0.74, 0.32, 0.7, True, 'stand')]
    for label, x, y, H, Rb, yaw, open_top, mode in barrels:
        rng_b = np.random.default_rng(seed * 100 + 10 + len(label) + int(10 * x) % 7)
        check_spot(label, x, y, Rb if mode == 'stand' else H / 2)
        V, F, colour, radius_at = barrel_mesh(H, Rb, rng_b, open_top)
        hoops_z = [0.10 * H, 0.30 * H, 0.70 * H, 0.90 * H] if not open_top else [0.08 * H, 0.30 * H, 0.72 * H, 0.93 * H]
        hoops = []
        for zh in hoops_z:
            rr = radius_at(zh)
            rrb = radius_at(max(zh - 0.017, 0.0))
            rrt = radius_at(min(zh + 0.017, H))
            prof = [(rrb - 0.004, zh - 0.017), (rrb + 0.010, zh - 0.017), (rrt + 0.010, zh + 0.017), (rrt - 0.004, zh + 0.017)]
            Vh, Fh, _ = lathe(prof, n=14, loop=True)
            hoops.append((Vh, Fh))
        if mode == 'stand':
            R = Rz(yaw)
            Vw = xf(V, R, (x, y, 0.0))
            hoopsW = [xf(h_[0], R, (x, y, 0.0)) for h_ in hoops]
            shift, g = seat_world([Vw], sink=0.012)
        else:
            R = Rz(yaw) @ Rx(math.pi / 2)
            Vw = xf(V - np.array([0, 0, H / 2]), R, (x, y, 0.0))
            hoopsW = [xf(h_[0] - np.array([0, 0, H / 2]), R, (x, y, 0.0)) for h_ in hoops]
            shift, g = seat_world([Vw], sink=0.012)
        Vw[:, 2] += shift
        acc = Acc()
        acc.add(Vw, F, colour)
        for hv, (_, Fh) in zip(hoopsW, hoops):
            hv = hv.copy()
            hv[:, 2] += shift
            iron_acc.add(hv, Fh, mixc(C_IRON, C_RUST, 0.04 + 0.12 * rng_b.random()))
        out[label] = mk.emit(acc, label, 'prop.barrel', 'wood', sink=0.012, bevel=False, mud=(g, 0.34, 0.8), mud_rng=rng_b)

    # ================================================================== 3. CRATES AND CHESTS
    def board_solid(x0, x1, y0, y1, z0, z1, rng_b, tone=None, tilt_end=0.0):
        V, F = box(x0, x1, y0, y1, z0, z1)
        return V, F, vary(tone if tone is not None else mixc(C_TIMBER, C_TIMBER_L, rng_b.random()), rng_b, 0.1)

    def crate(label, x, y, yaw, L, W, H, rng_b, broken=False):
        """An open crate: a base slab, two long sides and two ends of two boards each. `broken` takes the upper boards off one long side and cuts the lower one at a slant."""
        t = 0.028
        base_t = 0.035
        parts = []
        # local frame: length along x, width along y, base bottom at z = 0
        parts.append(board_solid(-L / 2, L / 2, -W / 2, W / 2, 0.0, base_t, rng_b, C_OAK))
        hb = (H - base_t) / 2.0
        for side in (-1, 1):
            ys = side * (W / 2 - t / 2)
            lo = board_solid(-L / 2, L / 2, ys - t / 2, ys + t / 2, base_t - 0.001, base_t + hb, rng_b)
            parts.append(lo)
            if not (broken and side == -1):
                parts.append(board_solid(-L / 2, L / 2, ys - t / 2, ys + t / 2, base_t + hb - 0.001 + 0.004, H, rng_b))
        for sx in (-1, 1):
            xs = sx * (L / 2 - t / 2)
            parts.append(board_solid(xs - t / 2, xs + t / 2, -W / 2 + t, W / 2 - t, base_t - 0.001, base_t + hb, rng_b))
            parts.append(board_solid(xs - t / 2, xs + t / 2, -W / 2 + t, W / 2 - t, base_t + hb - 0.001 + 0.004, H, rng_b))
        return parts

    def place_parts(parts, x, y, yaw, acc, sink=0.012, mud_h=0.2, rng_b=None, raise_by=0.0):
        R = Rz(yaw)
        Vs = [xf(p[0], R, (x, y, 0.0)) for p in parts]
        shift, g = seat_world(Vs, sink)
        for p, Vw in zip(parts, Vs):
            Vw[:, 2] += shift + raise_by
            acc.add(Vw, p[1], p[2])
        return shift, g

    rng_b = np.random.default_rng(seed * 100 + 31)
    check_spot('crate C', -21.45, -9.55, 0.45)
    acc = Acc()
    parts = crate('crate C', -21.45, -9.55, 0.12, 0.70, 0.48, 0.44, rng_b)
    shift, g = place_parts(parts, -21.45, -9.55, 0.12, acc)
    out['crate C'] = mk.emit(acc, 'crate C', 'prop.crate', 'wood', sink=0.012, mud=(g, 0.2, 0.7), mud_rng=rng_b)

    # the broken crate beside the well (north-east of the curb, outside the clear band round it): one side broken, a board fallen
    wx, wy = -15.55, 7.75
    check_spot('broken crate', wx, wy, 0.42)
    acc = Acc()
    parts = crate('crate broken', wx, wy, -0.35, 0.58, 0.42, 0.38, rng_b, broken=True)
    # a fallen board and a splinter lie beside it
    fall = [board_solid(-0.30, 0.30, -0.075, 0.075, 0.0, 0.026, rng_b, C_TIMBER_L)]
    Vfall = xf(fall[0][0], Rz(0.9), (wx + 0.15, wy - 0.78, 0.0))
    Rb_ = Rz(-0.35)
    Vs = [xf(p[0], Rb_, (wx, wy, 0.0)) for p in parts]
    shift, g = seat_world(Vs, 0.012)
    for p, Vw in zip(parts, Vs):
        Vw[:, 2] += shift
        acc.add(Vw, p[1], p[2])
    Vfall[:, 2] += ground5(Vfall) - 0.008 - Vfall[:, 2].min()
    acc.add(Vfall, fall[0][1], fall[0][2])
    V, F = prism_poly([(-0.14, -0.03), (0.16, -0.045), (0.10, 0.04), (-0.12, 0.03)], 0.0, 0.02)
    Vs2 = xf(V, Rz(2.2), (wx - 0.55, wy - 0.55, 0.0))
    Vs2[:, 2] += ground5(Vs2) - 0.008 - Vs2[:, 2].min()
    acc.add(Vs2, F, C_TIMBER_L)
    out['crate broken'] = mk.emit(acc, 'crate broken', 'prop.crate', 'wood', sink=0.008, mud=(g, 0.2, 0.7), mud_rng=rng_b)

    # the chest by cottage B's east wall (north of the chimney), with an arched lid and three iron straps
    chx, chy = -2.22, 11.0
    for dy_ in (-0.38, 0.0, 0.38):
        check_spot('chest B', chx, chy + dy_, 0.27)
    L_, W_, Hb = 0.86, 0.50, 0.42
    rng_b = np.random.default_rng(seed * 100 + 33)
    body = board_solid(-L_ / 2, L_ / 2, -W_ / 2, W_ / 2, 0.0, Hb, rng_b, mixc(C_OAK, C_TIMBER, 0.5))
    poly = [(-W_ / 2, Hb - 0.002)] + [(-W_ / 2 + W_ * (i / 8.0), Hb - 0.002 + 0.12 * math.sin(math.pi * i / 8.0)) for i in range(1, 8)] + [(W_ / 2, Hb - 0.002)]
    lid = extrude_x(poly, -L_ / 2 - 0.01, L_ / 2 + 0.01)
    R = Rz(math.pi / 2 + 0.15)                          # its long side along the wall (north-south)
    Vbody = xf(body[0], R, (chx, chy, 0.0))
    Vlid = xf(lid[0], R, (chx, chy, 0.0))
    shift, g = seat_world([Vbody, Vlid], 0.012)
    Vbody[:, 2] += shift
    Vlid[:, 2] += shift
    acc = Acc()
    acc.add(Vbody, body[1], body[2])
    acc.add(Vlid, lid[1], vary(mixc(C_TIMBER, C_TIMBER_L, 0.5), rng_b, 0.08))
    out['chest B'] = mk.emit(acc, 'chest B', 'prop.crate', 'wood', sink=0.012, mud=(g, 0.2, 0.7), mud_rng=rng_b)
    for xs in (-0.30, 0.0, 0.30):
        # an iron strap over the lid and down both ends: a thin arched band, sunk 1 cm into the wood
        path = [(xs, -W_ / 2 - 0.004, 0.04), (xs, -W_ / 2 - 0.004, Hb)] + [(xs, -W_ / 2 + W_ * (i / 8.0), Hb + 0.124 * math.sin(math.pi * i / 8.0) + 0.004) for i in range(1, 8)] + [(xs, W_ / 2 + 0.004, Hb), (xs, W_ / 2 + 0.004, 0.04)]
        Vs_, Fs_ = tube(np.array(path), 0.012, sides=4, phase=math.pi / 4)
        iron_acc.add(xf(Vs_, R, (chx, chy, shift)), Fs_, mixc(C_IRON, C_RUST, 0.3))

    # ================================================================== 4. SACKS
    def sack_mesh(H, W, rng_b, slump=1.0, n=14, lean=0.0):
        rows = 11
        zs = np.linspace(0.0, 1.0, rows)
        V, F = [], []
        ring_pts = []
        noise = Noise(int(rng_b.integers(1, 10000)), (0.9, 0.5, 0.3), 2)
        for ri, t in enumerate(zs):
            # width profile: flat foot, fat belly at a third, a neck gathered at the top, a little floppy lip
            w = W * (0.80 + 0.2 * min(t / 0.12, 1.0)) if t < 0.12 else W * (1.0 - 0.12 * ((t - 0.12) / 0.88) ** 1.5 - (0.62 * ((t - 0.62) / 0.38) ** 1.3 if t > 0.62 else 0.0))
            w = max(w, 0.045)
            if t > 0.96:
                w = max(w, 0.07 + 0.05 * (t - 0.96) / 0.04)
            z = H * t * (1.0 - 0.05 * slump * (t ** 2))
            off_x = slump * lean * H * t ** 2
            ring = []
            for k in range(n):
                a = 2 * math.pi * k / n
                bump = 1.0 + 0.10 * noise.value(math.cos(a) * 3 + t * 5, math.sin(a) * 3 - t * 3)
                sq = 1.0 + 0.14 * abs(math.sin(a))
                rx = w * bump
                ry = w * 0.78 * bump * sq
                ring.append((rx * math.cos(a) + off_x, ry * math.sin(a), z))
            ring_pts.append(ring)
        base = [(0.0, 0.0, 0.0)]
        Vv = [(0.0, 0.0, 0.0)]
        idx = []
        for ring in ring_pts:
            idx.append(len(Vv))
            Vv.extend(ring)
        top_c = len(Vv)
        Vv.append((float(np.mean([p[0] for p in ring_pts[-1]])), 0.0, ring_pts[-1][0][2] + 0.01))
        Ff = []
        for k in range(n):
            k2 = (k + 1) % n
            Ff.append((0, idx[0] + k2, idx[0] + k))
        for ri in range(rows - 1):
            for k in range(n):
                k2 = (k + 1) % n
                Ff.append((idx[ri] + k, idx[ri] + k2, idx[ri + 1] + k2, idx[ri + 1] + k))
        for k in range(n):
            k2 = (k + 1) % n
            Ff.append((idx[-1] + k, idx[-1] + k2, top_c))
        return np.array(Vv, float), Ff

    sacks = [('sack 1', -27.55, 7.15, 0.85, 0.30, 0.9, 0.10, math.pi / 2), ('sack 2', -26.95, 6.75, 0.62, 0.34, 0.4, -0.05, math.pi / 2 + 0.5), ('sack 3', 6.55, -7.15, 0.76, 0.31, 1.0, 0.12, math.pi),
             ('sack 4', 6.75, -8.25, 0.58, 0.33, 0.7, -0.08, math.pi - 0.4)]
    for label, x, y, H, W, slump_l, lean, yaw0 in sacks:
        rng_b = np.random.default_rng(seed * 100 + 40 + int(abs(x * 10)) % 13)
        check_spot(label, x, y, 0.38)
        V, F = sack_mesh(H, W, rng_b, slump_l * sack_slump, lean=lean)
        yaw = yaw0 + (rng_b.random() - 0.5) * 0.4
        Vw = xf(V, Rz(yaw), (x, y, 0.0))
        shift, g = seat_world([Vw], 0.012)
        Vw[:, 2] += shift
        acc = Acc()
        tone = vary(mixc(C_LINEN, C_LINEN_D, rng_b.random() * 0.6), rng_b, 0.06)
        acc.add(Vw, F, lambda k, f, V_, tone=tone, rr=rng_b, g=g: vary(mixc(tone, C_LINEN_D, 0.5 if np.mean([V_[i][2] for i in f]) - g < 0.05 else 0.0), rr, 0.05))
        out[label] = mk.emit(acc, label, 'prop.cloth', 'cloth', sink=0.012, smooth=True, bevel=False, mud=(g, 0.30, 0.8), mud_rng=rng_b)

    # ================================================================== 5. OTHER BUCKETS
    rng_b = np.random.default_rng(seed * 100 + 51)
    check_spot('bucket woodpile', -44.35, 8.55, 0.2)
    out['bucket woodpile'], _, _ = add_bucket('bucket woodpile', -44.35, 8.55, 0.0, rng_b, 1.1)
    rng_b = np.random.default_rng(seed * 100 + 52)
    check_spot('bucket B', -8.55, 6.55, 0.2)
    out['bucket B'], _, _ = add_bucket('bucket B', -8.55, 6.55, 0.0, rng_b, 2.4)

    # ================================================================== 6. THE TWO-WHEELED CART (parked, shafts down on a block) AND THE SPARE WHEEL
    cart_x, cart_y, cart_yaw = 12.5, -5.8, math.radians(10.0)
    check_spot('cart', cart_x + 1.0, cart_y, 2.4, allow=())
    rng_c = np.random.default_rng(seed * 100 + 61)
    Rw = 0.545
    tyre_t = 0.013
    zc = Rw + tyre_t
    wheel_y = 0.70
    wheels, tyres = [], []
    for side in (1, -1):
        Vw_, Fw_ = wheel_mesh(R=Rw, spokes=10, rng=np.random.default_rng(seed * 100 + 62 + (side > 0)))
        wheels.append((xf(Vw_, None, (0.0, side * wheel_y, zc)), Fw_))
        Vt_, Ft_ = tyre_mesh(Rw - 0.003, width=0.058, thick=tyre_t + 0.003)
        tyres.append((xf(Vt_, None, (0.0, side * wheel_y, zc)), Ft_))
    Vax, Fax = tube([(0.0, -wheel_y - 0.12, zc), (0.0, wheel_y + 0.12, zc)], 0.04, sides=8)
    # bearers that continue as shafts (one bar each), resting on the axle and, forward, on a block
    def bar_path(y, pts, w0, h0, w1, h1):
        rings = []
        for i, (x, zbot, ztop) in enumerate(pts):
            t = i / (len(pts) - 1)
            w = w0 + (w1 - w0) * t
            rings.append([(x, y - w / 2, zbot), (x, y + w / 2, zbot), (x, y + w / 2, ztop), (x, y - w / 2, ztop)])
        return loft_rings(rings)
    shafts = []
    for side in (1, -1):
        pts = [(-1.12, 0.595, 0.765), (1.12, 0.595, 0.765), (1.40, 0.545, 0.69), (1.80, 0.40, 0.52), (2.26, 0.235, 0.335), (2.58, 0.165, 0.245)]
        yv = side * 0.40 + 0.01 * (rng_c.random() - 0.5)
        shafts.append(bar_path(yv, pts, 0.085, 0.17, 0.065, 0.08))
    block = box(2.12, 2.40, -0.56, 0.56, 0.0, 0.26)
    # the bed: floor boards across the bearers, side boards, front and tail boards
    bed = []
    plank_w = 0.18
    n_pl = 12
    x_start = -1.10
    for i in range(n_pl):
        x0 = x_start + i * (plank_w + 0.004)
        tone = C_FRESH if i == 4 else mixc(C_TIMBER, C_TIMBER_L, rng_c.random())
        bed.append((box(x0, x0 + plank_w, -0.58 - 0.01 * rng_c.random(), 0.58 + 0.01 * rng_c.random(), 0.765 + 0.0, 0.800 + 0.003 * rng_c.random()), vary(tone, rng_c, 0.1)))
    x_end = x_start + n_pl * (plank_w + 0.004)
    for side in (1, -1):
        ys = side * 0.563
        bed.append((box(x_start, x_end - 0.004, ys - 0.015, ys + 0.015, 0.799, 0.935), vary(mixc(C_TIMBER, C_TIMBER_L, rng_c.random()), rng_c, 0.1)))
        bed.append((box(x_start + 0.02 * rng_c.random(), x_end - 0.004 - 0.03 * rng_c.random(), ys - 0.015, ys + 0.015, 0.934, 1.065), vary(mixc(C_TIMBER, C_SILVER, 0.3 * rng_c.random()), rng_c, 0.1)))
    bed.append((box(x_end - 0.034, x_end - 0.004, -0.55, 0.55, 0.799, 1.02), vary(C_TIMBER_L, rng_c, 0.08)))
    bed.append((box(x_start, x_start + 0.03, -0.55, 0.55, 0.799, 0.96), vary(C_TIMBER, rng_c, 0.08)))
    # seat everything as one group on the ground under the two tyres
    allV = [w[0] for w in wheels] + [t[0] for t in tyres] + [Vax] + [s[0] for s in shafts] + [block[0]] + [b[0][0] for b in bed]
    Rc = Rz(cart_yaw)
    shifts = [xf(v, Rc, (cart_x, cart_y, 0.0)) for v in allV]
    tyre_world = shifts[2:4]
    g_t = max(ground5(tw) for tw in tyre_world)
    low = min(tw[:, 2].min() for tw in tyre_world)
    shift = (g_t - 0.012) - low
    placed = [v.copy() for v in shifts]
    for v in placed:
        v[:, 2] += shift
    # the block: its base goes down to the ground under it (a little sunk), its top stays where the shafts need it (0.26 m over the tyres' contact level)
    bl = placed[7]
    gb = ground5(bl)
    bl[:4, 2] = gb - 0.03
    bl[4:8, 2] = (g_t - 0.012) + 0.26
    wheelL, wheelR = placed[0], placed[1]
    acc = Acc()
    acc.add(wheelL, wheels[0][1], lambda kf, f, V_: wheel_colour(V_, f, wheelL, rng_c, g_t))
    out['cart wheel left'] = mk.emit(acc, 'cart wheel left', 'prop.wheel', 'wood', sink=0.0, bevel=True, mud=(g_t, 0.45, 0.9), mud_rng=rng_c, rests_on_other=True)
    acc = Acc()
    acc.add(wheelR, wheels[1][1], lambda kf, f, V_: wheel_colour(V_, f, wheelR, rng_c, g_t))
    out['cart wheel right'] = mk.emit(acc, 'cart wheel right', 'prop.wheel', 'wood', sink=0.0, bevel=True, mud=(g_t, 0.45, 0.9), mud_rng=rng_c, rests_on_other=True)
    tyre_acc = Acc()
    for tv, (_, Ft) in zip(placed[2:4], tyres):
        tyre_acc.add(tv, Ft, mixc(C_IRON, C_RUST, 0.06 + 0.12 * rng_c.random()))
    cart_tyres = tyre_acc
    acc = Acc()
    acc.add(placed[4], Fax, vary(C_OAK, rng_c, 0.08))
    out['cart axle'] = mk.emit(acc, 'cart axle', 'prop.cart', 'wood', rests_on_other=True)
    acc = Acc()
    for sV, (_, sF) in zip(placed[5:7], shafts):
        acc.add(sV, sF, vary(mixc(C_TIMBER, C_TIMBER_L, 0.4), rng_c, 0.08))
    out['cart shafts'] = mk.emit(acc, 'cart shafts', 'prop.cart', 'wood', rests_on_other=True, bevel=True)
    acc = Acc()
    acc.add(bl, block[1], vary(C_BARK, rng_c, 0.1))
    out['cart block'] = mk.emit(acc, 'cart block', 'prop.wood', 'wood', sink=0.03, mud=(g_t, 0.2, 0.8), mud_rng=rng_c)
    acc = Acc()
    for bV_, (bv, col) in zip(placed[8:], bed):
        acc.add(bV_, bv[1], col)
    out['cart bed'] = mk.emit(acc, 'cart bed', 'prop.cart', 'wood', rests_on_other=True)

    # the spare wheel leaning on the stable's west wall (carried by the ground at its foot, its top a hand off the boards)
    sx, sy = 18.90, 38.5
    Vw_, Fw_ = wheel_mesh(R=0.52, spokes=10, rng=np.random.default_rng(seed * 100 + 66), missing=(), hub_len=0.15)
    Vt_, Ft_ = tyre_mesh(0.52 - 0.003, width=0.055, thick=0.016)
    lean = math.radians(11.0)
    Rl = Ry(lean) @ Rz(math.pi / 2)
    Vwl = xf(Vw_, Rl, (sx, sy, 0.0))
    Vtl = xf(Vt_, Rl, (sx, sy, 0.0))
    check_spot('spare wheel', sx, sy, 0.6, allow=('stable',))
    g_s = ground5(Vtl)
    sh = (g_s - 0.012) - Vtl[:, 2].min()
    Vwl[:, 2] += sh
    Vtl[:, 2] += sh
    acc = Acc()
    acc.add(Vwl, Fw_, lambda kf, f, V_: wheel_colour(V_, f, Vwl, rng_c, g_s, axis=0))
    out['spare wheel'] = mk.emit(acc, 'spare wheel', 'prop.wheel', 'wood', rests_on_other=True, mud=(g_s, 0.35, 0.9), mud_rng=rng_c)
    cart_tyres.add(Vtl, Ft_, mixc(C_IRON, C_RUST, 0.3))
    out['cart tyres'] = mk.emit(cart_tyres, 'cart tyres', 'iron.fitting', 'iron', sink=0.012, bevel=False)

    # ================================================================== 7. WOODPILE, CHOPPING BLOCK, AXE, CHIPS, STOOL
    rng_w = np.random.default_rng(seed * 100 + 71)
    pile_x, pile_y = -43.0, 10.5
    check_spot('woodpile', pile_x, pile_y, 1.2)
    logs = []
    rows = 7
    L_pile = 2.4
    per_row = 14
    prev_row = []
    log_acc = Acc()
    for rw in range(rows):
        cur = []
        n_here = per_row - (1 if rw % 2 else 0) - (rw // 3)
        span = L_pile - 0.16 * rw
        for j in range(n_here):
            u = (j + 0.5) / n_here
            y = pile_y - span / 2 + u * span + 0.04 * (rng_w.random() - 0.5)
            if rw % 2:
                y += 0.0
            r = 0.075 + 0.025 * rng_w.random()
            length = 0.58 + 0.12 * rng_w.random()
            x = pile_x + 0.04 * (rng_w.random() - 0.5)
            yaw = 0.10 * (rng_w.random() - 0.5)
            # the height of its centre: on the ground for the first row, else on the highest log below within reach
            if rw == 0:
                zc_ = None
            else:
                best = None
                for (yy, rr_, zz) in prev_row:
                    d = abs(yy - y)
                    if d < r + rr_:
                        h = zz + math.sqrt((r + rr_) ** 2 - d * d) - 0.012
                        best = h if best is None else max(best, h)
                zc_ = best
            sides = 8
            ring_ang = [2 * math.pi * i / sides + math.pi / sides for i in range(sides)]
            rings = [[(xs, r * math.cos(a) * (1 + 0.06 * (rng_w.random() - 0.5)), r * math.sin(a) * (1 + 0.06 * (rng_w.random() - 0.5))) for a in ring_ang] for xs in (-length / 2, length / 2)]
            V_, F_ = loft_rings(rings)
            V_ = np.asarray(V_)
            V_ = xf(V_, Rz(yaw), (x, y, 0.0))
            if zc_ is None:
                g = ground5(V_)
                V_[:, 2] += g - 0.010 - V_[:, 2].min()
                zc_ = float(V_[:, 2].mean())
            else:
                V_[:, 2] += zc_
            cur.append((y, r, float(V_[:, 2].mean())))
            tone = vary(mixc(C_BARK, C_TIMBER_L, rng_w.random() * 0.6), rng_w, 0.1)
            end_tone = vary(C_CUT, rng_w, 0.08) if rng_w.random() < 0.6 else vary(C_TIMBER_L, rng_w, 0.08)
            Vn = V_

            def lcol(k, f, V__, tone=tone, end_tone=end_tone, length=length, x=x):
                return end_tone if len(f) == sides else tone
            log_acc.add(Vn, F_, lcol)
        prev_row = cur
    g_pile = ground5(log_acc.stacked())
    out['woodpile logs'] = mk.emit(log_acc, 'woodpile logs', 'prop.wood', 'wood', sink=0.010, bevel=False, mud=(g_pile, 0.25, 0.7), mud_rng=rng_w)
    # end stakes: two pairs of leaning stakes driven into the ground at the ends
    stake_acc = Acc()
    for end in (-1, 1):
        for side in (-1, 1):
            sx_, sy_ = pile_x + side * 0.40, pile_y + end * (L_pile / 2 + 0.10)
            top_h = 1.35 + 0.1 * rng_w.random()
            lean_ = (-side * 0.04 * rng_w.random(), end * 0.05 * rng_w.random())
            pts = [(sx_, sy_, 0.0), (sx_ + lean_[0] * top_h, sy_ + lean_[1] * top_h, top_h)]
            probe = np.array([pts[0], pts[1]])
            g = ground5(np.array([[sx_ - 0.04, sy_ - 0.04, 0], [sx_ + 0.04, sy_ + 0.04, 1]]))
            P = np.array([(sx_, sy_, g - 0.15), (sx_ + lean_[0] * top_h, sy_ + lean_[1] * top_h, g + top_h)])
            V, F = tube(P, [0.045, 0.036], sides=6)
            stake_acc.add(V, F, vary(mixc(C_TIMBER, C_BARK, 0.4), rng_w, 0.1))
    out['woodpile stakes'] = mk.emit(stake_acc, 'woodpile stakes', 'prop.wood', 'wood', sink=0.15, bevel=False)

    # the chopping block with the axe stuck in it, chips and bark about, a stool beside it
    rng_k = np.random.default_rng(seed * 100 + 72)
    kx, ky = -41.4, 7.6
    check_spot('chopping block', kx, ky, 0.3, allow=())
    H_k = 0.45
    prof = [(0.0, 0.0), (0.26, 0.0), (0.275, 0.05), (0.265, 0.25), (0.245, 0.43), (0.235, H_k), (0.15, H_k - 0.03), (0.0, H_k - 0.045)]
    Vk, Fk, Mk = lathe(prof, n=12, rfun=lambda k, ri, z: 1.0 + 0.06 * math.sin(2.3 * k + 1.0) + 0.03 * math.sin(5.1 * k))
    Vk = xf(Vk, Rz(rng_k.random() * 3), (kx, ky, 0.0))
    shift, g_k = seat_world([Vk], 0.03)
    Vk[:, 2] += shift
    acc = Acc()
    acc.add(Vk, Fk, lambda k, f, V_, Mk=Mk, rr=rng_k: (C_CUT if Mk[k][0] >= 5 else (vary(mixc(C_BARK, C_TIMBER, rr.random()), rr, 0.1) if Mk[k][0] > 0 else C_OAK)))
    block_obj = mk.emit(acc, 'chopping block', 'prop.wood', 'wood', sink=0.03, bevel=False, mud=(g_k, 0.2, 0.7), mud_rng=rng_k)
    out['chopping block'] = block_obj
    top_z = float(Vk[:, 2].max())
    # the axe: a head with a long eye block, the blade biting 6 cm into the top, the haft leaning out (25 degrees)
    head_poly = [(-0.050, 0.065), (0.050, 0.065), (0.050, 0.010), (0.115, -0.085), (0.105, -0.115), (-0.105, -0.115), (-0.115, -0.085), (-0.050, 0.010)]
    # in (x, z): the eye block on top, the blade fanning out to the edge at the bottom
    Vh, Fh = extrude_y(head_poly, -0.028, 0.028)
    Vhaft, Fhaft = tube([(0.0, 0.0, 0.0), (0.0, 0.0, 0.80)], 0.025, sides=6)
    Vhaft[:, 0] *= 1.0
    tilt = math.radians(25.0)
    Rax = Rz(1.1) @ Ry(tilt)
    pos = (kx + 0.02, ky - 0.02, top_z + 0.115 - 0.065)
    Vh_w = xf(Vh, Rax, pos)
    Vhaft_w = xf(Vhaft + np.array([0.0, 0.0, -0.02]), Rax, pos)
    acc = Acc()
    acc.add(Vh_w, Fh, mixc(C_IRON, C_RUST, 0.25))
    out['axe head'] = mk.emit(acc, 'axe head', 'iron.fitting', 'iron', bevel=False)
    acc = Acc()
    acc.add(Vhaft_w, Fhaft, vary(C_FRESH, rng_k, 0.06))
    out['axe haft'] = mk.emit(acc, 'axe haft', 'prop.wood', 'wood', bevel=False, rests_on_other=True)
    # chips and bark: big flat wedges lying about the block
    chip_acc = Acc()
    for i in range(16):
        a = rng_k.random() * 2 * math.pi
        d = 0.42 + 0.75 * rng_k.random()
        px, py = kx + d * math.cos(a), ky + d * math.sin(a)
        if i % 3 == 0:
            L = 0.20 + 0.12 * rng_k.random()
            Wd = 0.07 + 0.05 * rng_k.random()
            poly = [(-L / 2, -Wd / 2), (L / 2, -Wd * 0.3), (L / 2 * 0.9, Wd / 2), (-L / 2 * 0.8, Wd * 0.4)]
            V, F = prism_poly(poly, 0.0, 0.022 + 0.01 * rng_k.random())
            col = vary(C_BARK, rng_k, 0.1)
        else:
            L = 0.09 + 0.09 * rng_k.random()
            Wd = 0.035 + 0.03 * rng_k.random()
            poly = [(-L / 2, -Wd / 2), (L / 2, -Wd * 0.2), (L * 0.2, Wd / 2), (-L / 2, Wd * 0.3)]
            V, F = prism_poly(poly, 0.0, 0.025 + 0.015 * rng_k.random())
            col = vary(C_CUT, rng_k, 0.1)
        V = xf(V, Rz(rng_k.random() * 6.28), (px, py, 0.0))
        if box_dist(px, py, (kx - 0.3, ky - 0.3, kx + 0.3, ky + 0.3)) < 0.05:
            continue
        V[:, 2] += ground5(V) - 0.008 - V[:, 2].min()
        chip_acc.add(V, F, col)
    out['chips and bark'] = mk.emit(chip_acc, 'chips and bark', 'prop.wood', 'wood', sink=0.008, bevel=False)
    # the stool: three round legs and a thick round seat resting on their flat tops
    rng_s = np.random.default_rng(seed * 100 + 73)
    stx, sty = -42.55, 6.35
    check_spot('stool', stx, sty, 0.25)
    leg_pos = [(stx + 0.12 * math.cos(a), sty + 0.12 * math.sin(a)) for a in (0.5, 0.5 + 2.094, 0.5 + 4.188)]
    legs_g = [ground5(np.array([[x - 0.035, y - 0.035, 0], [x + 0.035, y + 0.035, 1]])) for x, y in leg_pos]
    seat_bottom = max(legs_g) + 0.40
    acc = Acc()
    for (x, y), g in zip(leg_pos, legs_g):
        V, F = tube([(x, y, g - 0.012), (x, y, seat_bottom + 0.004)], 0.036, sides=8)
        acc.add(V, F, vary(C_TIMBER, rng_s, 0.1))
    Vs, Fs, Ms = lathe([(0.0, seat_bottom), (0.165, seat_bottom), (0.175, seat_bottom + 0.02), (0.17, seat_bottom + 0.055), (0.0, seat_bottom + 0.055)], n=12, rfun=lambda k, ri, z: 1.0 + 0.04 * math.sin(3.1 * k))
    acc.add(Vs + np.array([stx, sty, 0.0]), Fs, lambda k, f, V_, rr=rng_s: C_CUT if V_[f[0]][2] > seat_bottom + 0.05 else vary(C_TIMBER_L, rr, 0.08))
    out['stool'] = mk.emit(acc, 'stool', 'prop.furniture', 'wood', sink=0.012, mud=(max(legs_g), 0.15, 0.7), mud_rng=rng_s)

    # ================================================================== 8. HAYSTACK AND BALES
    rng_h = np.random.default_rng(seed * 100 + 81)
    hx, hy = -34.5, -14.5
    check_spot('haystack', hx, hy, 1.6)
    Hh = 2.62
    R0 = 1.5 * (0.85 + 0.15 * hay_shape)
    profile = [(1.0, 0.0), (1.02, 0.35), (1.04, 0.85), (0.93, 1.35), (0.74, 1.80), (0.50, 2.20), (0.27, 2.47), (0.10, 2.58)]
    pw = hay_shape
    # hay_shape 0.6 gives a steep cone (the upper rings are pulled in), 1.5 a broad dome (they are pushed out)
    prof = [(R0 * r * (1.0 + (pw - 1.0) * 0.28 * (z / Hh) ** 1.0), z) for (r, z) in profile]
    n_h = 20
    nz = Noise(seed + 5, (1.6, 0.8, 0.4), 3)
    ring_ground = [pk.ground_height_at(hx + prof[0][0] * math.cos(2 * math.pi * k / n_h), hy + prof[0][0] * math.sin(2 * math.pi * k / n_h)) for k in range(n_h)]
    gmax_h = max(ring_ground)

    def hay_r(k, ri, z):
        a = 2 * math.pi * k / n_h
        band = 1.0 + 0.035 * math.sin(7.0 * z + 1.3)                   # soft rolled bands up the stack
        return band * (1.0 + 0.07 * nz.value(math.cos(a) * 2.0 + z * 0.8, math.sin(a) * 2.0 - z * 0.5))
    Vh, Fh, Mh = lathe([(0.0, 0.0)] + prof + [(0.0, Hh + 0.02)], n=n_h, rfun=hay_r)
    Vh = Vh + np.array([hx, hy, 0.0])
    # the bottom ring follows the ground; the rows above keep their height over the highest ground
    Vh[:, 2] += gmax_h
    nb = 1 + n_h
    for k in range(n_h):
        i = 1 + k
        Vh[i, 2] = ring_ground[k] - 0.03
    Vh[0, 2] = min(ring_ground) - 0.03
    acc = Acc()
    acc.add(Vh, Fh, lambda k, f, V_, Mh=Mh, rr=rng_h: vary(mixc(C_HAY, C_HAY_D, 0.15 + 0.5 * rr.random() * (1.0 - min(1.0, (np.mean([V_[i][2] for i in f]) - gmax_h) / 1.6))), rr, 0.07))
    hay_obj = mk.emit(acc, 'haystack', 'prop.straw', 'straw', sink='auto', smooth=True, bevel=False, mud=(gmax_h, 0.5, 0.6), mud_rng=rng_h)
    out['haystack'] = hay_obj
    # the bales: two rounded blocks with twine bands; the second lies across the first
    rng_b2 = np.random.default_rng(seed * 100 + 82)
    bale_acc = Acc()
    bx0, by0 = -31.3, -9.9

    def bale(L, W, H, rng_x):
        rings = []
        for i, x in enumerate(np.linspace(-L / 2, L / 2, 7)):
            bulge = 1.0 + 0.05 * math.sin(math.pi * i / 6.0)
            w, h_ = W / 2 * bulge, H * bulge
            rr_ = [(x, -w, 0.0), (x, -w * 0.9, h_ * 0.9), (x, -w * 0.5, h_), (x, w * 0.5, h_), (x, w * 0.9, h_ * 0.9), (x, w, 0.0), (x, w * 0.5, 0.0), (x, -w * 0.5, 0.0)]
            rings.append([(a, b + 0.01 * (rng_x.random() - 0.5), c) for a, b, c in rr_])
        return loft_rings(rings)
    V1, F1 = bale(0.56, 0.40, 0.34, rng_b2)
    V1 = xf(V1, Rz(0.25), (bx0, by0, 0.0))
    shift, g_b = seat_world([V1], 0.012)
    V1[:, 2] += shift
    V2, F2 = bale(0.52, 0.38, 0.32, rng_b2)
    V2 = xf(V2, Rz(0.25 + 1.2), (bx0 + 0.04, by0 + 0.03, 0.0))
    V2[:, 2] += float(V1[:, 2].max()) - 0.012 - V2[:, 2].min()
    for Vb_, Fb_ in ((V1, F1), (V2, F2)):
        cx_ = float(Vb_[:, 0].mean())
        acc_col = lambda k, f, V_, rr=rng_b2: (C_TWINE if abs(math.atan2(0, 1) + (V_[f[0]][0] - cx_) * 0) < 0 else vary(mixc(C_HAY, C_HAY_D, rr.random() * 0.5), rr, 0.07))
        bale_acc.add(Vb_, Fb_, lambda k, f, V_, rr=rng_b2: vary(mixc(C_HAY, C_HAY_D, rr.random() * 0.5), rr, 0.07))
    out['hay bales'] = mk.emit(bale_acc, 'hay bales', 'prop.straw', 'straw', sink=0.012, smooth=False, bevel=False, mud=(g_b, 0.25, 0.7), mud_rng=rng_b2)

    # ================================================================== 9. WATTLE HURDLES (6)
    def hurdle(L, H, rng_x, rows_n, weave_k, missing_patch=False, ragged=0.05):
        """One woven panel: a solid slab whose two faces carry the weave (rows of withies that pass in front of a stake-width of panel and behind the next, alternating row by row, so the pattern reads as basketry),
        held by three stakes driven into the ground. Returns vertices, faces, one colour for each face and the stake positions."""
        nx, nz_ = 32, 30
        xs = np.linspace(-L / 2, L / 2, nx + 1)
        top_h = H + ragged * np.array([math.sin(3.1 * x + 0.6) * 0.6 + (rng_x.random() - 0.5) for x in xs])
        top_h[0] = H - ragged * (0.8 + rng_x.random())
        top_h[-1] = H - ragged * rng_x.random()
        stakes_x = (-L / 2 + 0.07, 0.0 + 0.04 * (rng_x.random() - 0.5), L / 2 - 0.07)
        seg = L / 4.0
        shift_x = rng_x.random() * seg
        light, dark = hexl('#9C7E52'), hexl('#6F5435')

        def over(x, row, side):
            sq = math.sin(2 * math.pi * (x + L / 2 + shift_x) / (2 * seg) + math.pi * row + (0.0 if side > 0 else math.pi))
            return 0.5 + 0.5 * math.tanh(2.6 * sq)

        def rel_at(x, z, side, hole):
            t = (z * rows_n / H) % 1.0
            row = int(z * rows_n / H)
            rope = math.sin(math.pi * min(max(t, 0.02), 0.98)) ** 0.6
            r = 0.0215 * weave_k * rope * (0.30 + 0.70 * over(x, row, side))
            return r * (0.15 if hole else 1.0)

        def hole_at(x, z):
            return missing_patch and 0.30 < (x / L + 0.5) < 0.52 and 0.40 < z / H < 0.70
        V = []
        for side in (1, -1):
            for i, x in enumerate(xs):
                for j in range(nz_ + 1):
                    z = top_h[i] * j / nz_
                    V.append((x, side * (0.020 + rel_at(x, z, side, hole_at(x, z))), z))
        V = np.array(V, float)
        per = (nx + 1) * (nz_ + 1)

        def vid(side, i, j):
            return (0 if side > 0 else per) + i * (nz_ + 1) + j

        def cell_col(i, j, side):
            xc = 0.5 * (xs[i] + xs[i + 1])
            zc = 0.5 * (top_h[i] * j / nz_ + top_h[i] * (j + 1) / nz_)
            row = int(zc * rows_n / H)
            t = (zc * rows_n / H) % 1.0
            o = over(xc, row, side)
            c = mixc(dark, light, o * (0.55 + 0.45 * math.sin(math.pi * t)))
            return vary(c, rng_x, 0.05)
        F, C = [], []
        for i in range(nx):
            for j in range(nz_):
                F.append((vid(1, i, j), vid(1, i, j + 1), vid(1, i + 1, j + 1), vid(1, i + 1, j)))
                C.append(cell_col(i, j, 1))
                F.append((vid(-1, i, j), vid(-1, i + 1, j), vid(-1, i + 1, j + 1), vid(-1, i, j + 1)))
                C.append(cell_col(i, j, -1))
        for i in range(nx):
            F.append((vid(1, i, 0), vid(1, i + 1, 0), vid(-1, i + 1, 0), vid(-1, i, 0)))
            F.append((vid(1, i, nz_), vid(-1, i, nz_), vid(-1, i + 1, nz_), vid(1, i + 1, nz_)))
            C += [dark, light]
        for j in range(nz_):
            F.append((vid(1, 0, j), vid(-1, 0, j), vid(-1, 0, j + 1), vid(1, 0, j + 1)))
            F.append((vid(1, nx, j), vid(1, nx, j + 1), vid(-1, nx, j + 1), vid(-1, nx, j)))
            C += [light, light]
        return V, F, C, stakes_x

    hurdle_specs = [('hurdle 1', -8.35, 13.55, 0.05, 1.8, 1.00, False), ('hurdle 2', -6.55, 13.70, 0.14, 1.8, 0.92, True), ('hurdle 3', -4.75, 13.80, -0.08, 1.8, 1.08, False),
                    ('hurdle 4', -3.10, 13.05, 1.25, 1.8, 0.96, False), ('hurdle 5', 7.85, -8.55, 1.50, 1.8, 1.04, False), ('hurdle 6', 7.30, -10.25, 2.15, 1.8, 0.90, True)]
    for label, x, y, yaw, L, H, broken in hurdle_specs:
        rng_x = np.random.default_rng(seed * 100 + 90 + len(label) + int(abs(x)) % 11)
        check_spot(label, x, y, 0.95)
        V, F, Cf, stakes_x = hurdle(L, H, rng_x, weave_rows + int(rng_x.integers(-1, 2)), weave, missing_patch=broken)
        lean_roll = (rng_x.random() - 0.5) * math.radians(5.0)
        Rh = Rz(yaw) @ Rx(lean_roll)
        ground_probe = [(x + (u * L / 2) * math.cos(yaw), y + (u * L / 2) * math.sin(yaw)) for u in (-1, 0, 1)]
        gg = [pk.ground_height_at(px, py) for px, py in ground_probe]
        Vw = xf(V, Rh, (x, y, 0.0))
        Vw[:, 2] += max(gg) + 0.05 - Vw[:, 2].min()                                        # the panel's lowest edge a hand above the highest ground, held by its stakes
        acc = Acc()
        acc.add(Vw, F, Cf)
        for sxp in stakes_x:
            P0 = xf(np.array([[sxp, 0.0, 0.0]]), Rh, (x, y, 0.0))[0]
            g0 = ground5(np.array([[P0[0] - 0.04, P0[1] - 0.04, 0], [P0[0] + 0.04, P0[1] + 0.04, 1]]))
            top = H + 0.12 + 0.08 * rng_x.random()
            local = np.array([[sxp, 0.0, -0.18], [sxp + 0.004, 0.0, 0.20], [sxp + 0.012 * (rng_x.random() - 0.5), 0.0, top]])
            V_s, F_s = tube(local, [0.032, 0.032, 0.022], sides=8, phase=0.0)
            V_s = xf(V_s, Rh, (x, y, 0.0))
            V_s[:, 2] += g0 - float(xf(np.array([[sxp, 0.0, 0.0]]), Rh, (x, y, 0.0))[0][2])
            acc.add(V_s, F_s, vary(mixc(C_TIMBER, C_WICKER_D, 0.5), rng_x, 0.1))
        out[label] = mk.emit(acc, label, 'prop.wicker', 'wicker', sink=0.18, bevel=False, smooth=False)

    # ================================================================== 10. BENCH, JUGS, BASKETS
    rng_j = np.random.default_rng(seed * 100 + 101)
    bnx, bny = -29.2, 7.36
    for dx_ in (-0.6, 0.0, 0.6):
        check_spot('bench A', bnx + dx_, bny, 0.15)
    yawb = 0.04
    leg_x = (bnx - 0.58, bnx + 0.58)
    legs_g = []
    for lx in leg_x:
        legs_g.append(ground5(np.array([[lx - 0.03, bny - 0.13, 0], [lx + 0.03, bny + 0.13, 1]])))
    seat_z0 = max(legs_g) + 0.405
    acc = Acc()
    def about(V_, yaw_, cx_, cy_):
        return xf(np.asarray(V_) - np.array([cx_, cy_, 0.0]), Rz(yaw_), (cx_, cy_, 0.0))
    for lx, g in zip(leg_x, legs_g):
        V, F = box(lx - 0.03, lx + 0.03, bny - 0.13, bny + 0.13, g - 0.012, seat_z0 + 0.004)
        acc.add(about(V, yawb, bnx, bny), F, vary(C_TIMBER, rng_j, 0.08))
    V, F = box(bnx - 0.75, bnx + 0.75, bny - 0.15, bny + 0.15, seat_z0, seat_z0 + 0.045)
    Vsit = about(V, yawb, bnx, bny)
    acc.add(Vsit, F, lambda k, f, V_, rr=rng_j: vary(C_TIMBER_L if V_[f[0]][2] > seat_z0 + 0.03 else C_TIMBER, rr, 0.08))
    out['bench'] = mk.emit(acc, 'bench', 'prop.furniture', 'wood', sink=0.012, mud=(max(legs_g), 0.18, 0.7), mud_rng=rng_j)
    seat_top = seat_z0 + 0.045

    def jug_parts(rng_x, h=0.22):
        prof = [(0.0, 0.0), (0.050, 0.0), (0.060, 0.012), (0.086, 0.08), (0.084, 0.125), (0.05, 0.18), (0.040, 0.20), (0.050, h), (0.040, h), (0.036, h - 0.012), (0.0, h - 0.016)]
        V, F, M_ = lathe(prof, n=14, rfun=lambda k, ri, z: 1.0 + 0.015 * math.sin(2 * k))
        handle = [(0.045, 0.0, h - 0.012), (0.085, 0.0, h + 0.015), (0.125, 0.0, h - 0.04), (0.128, 0.0, 0.14), (0.098, 0.0, 0.085)]
        Hv, Hf = tube(np.array(handle), 0.014, sides=6)
        Vu, Fu = union([(V, F), (Hv, Hf)])
        return Vu, Fu

    jug_spots = [('jug 1', bnx - 0.35, bny - 0.02, 0.1, 'bench'), ('jug 2', bnx + 0.25, bny + 0.03, 2.6, 'bench'), ('jug B', -3.6, 6.85, 1.2, 'ground')]
    for label, x, y, yaw, where in jug_spots:
        rng_x = np.random.default_rng(seed * 100 + 110 + len(label) + int(abs(x)) % 5)
        check_spot(label, x, y, 0.14, allow=('B',) if where == 'ground' and False else ())
        Vu, Fu = jug_parts(rng_x, 0.21 + 0.03 * rng_x.random())
        Vw = xf(Vu, Rz(yaw), (x, y, 0.0))
        if where == 'bench':
            Vw[:, 2] += seat_top - 0.004 - Vw[:, 2].min()
            g_j = None
        else:
            shift, g_j = seat_world([Vw], 0.008)
            Vw[:, 2] += shift
        acc = Acc()
        glaze = vary(mixc(C_JUG, C_JUG_D, rng_x.random()), rng_x, 0.06)
        acc.add(Vw, Fu, lambda k, f, V_, glaze=glaze, rr=rng_x: mixc(glaze, C_JUG_D, 0.5) if float(np.mean([V_[i][2] for i in f])) - float(Vw[:, 2].min()) < 0.03 else vary(glaze, rr, 0.03))
        out[label] = mk.emit(acc, label, 'prop.ceramic', 'ceramic', sink=0.008, smooth=True, bevel=False, rests_on_other=(where == 'bench'), mud=(g_j, 0.1, 0.5) if g_j is not None else None, mud_rng=rng_x)

    def basket_parts(rng_x, h=0.27, r0=0.17, r1=0.23):
        n = 16
        prof = [(0.0, 0.0), (r0, 0.0), (r0 + 0.01, 0.03), (r1 - 0.01, h * 0.7), (r1, h), (r1 - 0.025, h), (r0 - 0.012, 0.035), (0.0, 0.035)]
        weave_ = lambda k, ri, z: 1.0 + 0.045 * (1 if (k + ri) % 2 else -1) * (1 if 0 < ri < 5 else 0)
        V, F, M_ = lathe(prof, n=n, rfun=weave_)
        handle = [(-(r1 - 0.012), 0.0, h - 0.015)] + [(-(r1) * math.cos(a) * 1.0, 0.0, h + 0.03 + 0.27 * math.sin(a)) for a in np.linspace(0.15, math.pi - 0.15, 9)] + [((r1 - 0.012), 0.0, h - 0.015)]
        Hv, Hf = tube(np.array(handle), 0.014, sides=6)
        Vu, Fu = union([(V, F), (Hv, Hf)])
        return Vu, Fu

    for label, x, y, yaw in (('basket 1', -23.85, -7.45, 0.6), ('basket 2', -19.7, 6.5, 2.0)):
        rng_x = np.random.default_rng(seed * 100 + 120 + int(abs(x)) % 9)
        check_spot(label, x, y, 0.24)
        Vu, Fu = basket_parts(rng_x, 0.25 + 0.05 * rng_x.random())
        Vw = xf(Vu, Rz(yaw), (x, y, 0.0))
        shift, g_k2 = seat_world([Vw], 0.01)
        Vw[:, 2] += shift
        acc = Acc()
        acc.add(Vw, Fu, lambda k, f, V_, rr=rng_x: vary(mixc(C_WICKER, C_WICKER_D, 0.5 + 0.5 * math.sin(13 * float(np.mean([V_[i][2] for i in f])) + 3 * float(np.mean([V_[i][0] for i in f])))), rr, 0.06))
        out[label] = mk.emit(acc, label, 'prop.wicker', 'wicker', sink=0.01, smooth=False, bevel=False, mud=(g_k2, 0.12, 0.6), mud_rng=rng_x)

    # ================================================================== 11. HANDBARROW AND LADDER
    rng_hb = np.random.default_rng(seed * 100 + 131)
    hbx, hby, hbyaw = -12.0, -6.0, 0.55
    check_spot('handbarrow', hbx, hby, 1.1)
    acc = Acc()
    poles = []
    for side in (-1, 1):
        yv = side * 0.27
        rings = []
        for t_ in np.linspace(0, 1, 6):
            x = -0.95 + 1.9 * t_
            zb_ = 0.30 + (0.005 - 0.30) * t_
            zt_ = zb_ + 0.075
            w = 0.065 - 0.012 * t_
            rings.append([(x, yv - w / 2, zb_), (x, yv + w / 2, zb_), (x, yv + w / 2, zt_), (x, yv - w / 2, zt_)])
        poles.append(loft_rings(rings))
    Rhb = Rz(hbyaw)
    polesW = [xf(p[0], Rhb, (hbx, hby, 0.0)) for p in poles]
    # the front tips rest on the ground; the rear stands on two legs
    tip_g = ground5(np.vstack(polesW))
    shift = (tip_g - 0.01) - min(p[:, 2].min() for p in polesW)
    for p in polesW:
        p[:, 2] += shift
    ang_s = math.atan(0.295 / 1.9)
    slats = []
    for i in range(6):
        t_ = 0.22 + i * 0.105
        xc = -0.95 + 1.9 * t_
        zt_ = 0.30 + (0.005 - 0.30) * t_ + 0.075
        V, F = box(-0.075, 0.075, -0.40, 0.40, -0.002, 0.024)
        V = xf(V, Ry(ang_s), (xc, 0.0, zt_))
        slats.append((xf(V, Rhb, (hbx, hby, shift)), F))
    leg_list = []
    for side in (-1, 1):
        lx, ly = -0.78, side * 0.27
        V, F = box(lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, 0.0, 1.0)
        Vw = xf(V, Rhb, (hbx, hby, 0.0))
        g = ground5(np.array([[Vw[:, 0].min(), Vw[:, 1].min(), 0.0], [Vw[:, 0].max(), Vw[:, 1].max(), 1.0]]))
        zbot_pole = 0.30 + (0.005 - 0.30) * ((lx + 0.95) / 1.9)
        Vw[:4, 2] = g - 0.012
        Vw[4:, 2] = zbot_pole + shift + 0.006
        leg_list.append((Vw, F))
    for pv, (_, pf) in zip(polesW, poles):
        acc.add(pv, pf, vary(mixc(C_TIMBER, C_TIMBER_L, 0.4), rng_hb, 0.08))
    for sv, sf in slats:
        acc.add(sv, sf, vary(mixc(C_TIMBER, C_SILVER, 0.3 * rng_hb.random()), rng_hb, 0.1))
    for lv, lf in leg_list:
        acc.add(lv, lf, vary(C_OAK, rng_hb, 0.08))
    out['handbarrow'] = mk.emit(acc, 'handbarrow', 'prop.cart', 'wood', sink=0.012, mud=(tip_g, 0.25, 0.7), mud_rng=rng_hb)

    # the ladder leaning towards cottage D's south wall (its top a hand off the cob, carried by its feet)
    rng_l = np.random.default_rng(seed * 100 + 141)
    lx0, ly0 = 4.62, -11.17
    check_spot('ladder foot', lx0, ly0, 0.35)
    check_spot('ladder top', lx0, ly0 + 0.8, 0.12)
    LL = 2.6
    parts = []
    for side in (-1, 1):
        xr = side * 0.215
        V, F = box(xr - 0.035, xr + 0.035, -0.035, 0.035, 0.0, LL)
        # a little taper: the rail narrows towards the top
        V[4:, 0] = V[4:, 0] * 0.9 + (xr * 0.1)
        parts.append((V, F, vary(mixc(C_TIMBER, C_TIMBER_L, rng_l.random() * 0.6), rng_l, 0.08)))
    for i in range(8):
        z = 0.30 + i * 0.30 + 0.01 * (rng_l.random() - 0.5)
        V, F = box(-0.245 - 0.012 * rng_l.random(), 0.245 + 0.012 * rng_l.random(), -0.026, 0.026, z - 0.026, z + 0.026)
        parts.append((V, F, vary(C_FRESH if i == 5 else mixc(C_TIMBER, C_TIMBER_L, rng_l.random()), rng_l, 0.1)))
    lean_a = math.radians(19.0)
    Rld = Rz(0.0) @ Rx(-lean_a)                  # the top leans towards +y (the wall)
    Vsl = [xf(p[0], Rld, (lx0, ly0, 0.0)) for p in parts]
    shift, g_l = seat_world(Vsl, 0.014)
    acc = Acc()
    for Vl, p in zip(Vsl, parts):
        Vl[:, 2] += shift
        acc.add(Vl, p[1], p[2])
    out['ladder'] = mk.emit(acc, 'ladder', 'prop.wood', 'wood', sink=0.014, mud=(g_l, 0.35, 0.7), mud_rng=rng_l)
    ladder_top = (float(np.vstack(Vsl)[:, 1].max()), float(np.vstack(Vsl)[:, 2].max()))
    out['ladder_top'] = ladder_top

    # ================================================================== 12. LOOSE STRAW IN THE EMPTY STABLE (15 scraps, 3 clusters, flat on the floor, none piled)
    rng_t = np.random.default_rng(seed * 100 + 151)
    stable_probe = [pk.ground_height_at(19.1 + (28.9 - 19.1) * i / 8.0, 36.0 + 6.0 * j / 8.0) for i in range(9) for j in range(9)]
    floor_z = round(float(max(stable_probe)), 4) + 0.01              # the stable's beaten-earth floor: flush with the pad, a centimetre proud (the stable part's own number)
    floor_obj = bpy.data.objects.get('Stable earth floor')
    straw_acc = Acc()
    clusters = [(20.85, 39.95), (27.15, 40.2), (28.05, 37.15)]
    placed_scraps = []
    for cxs, cys in clusters:
        count = 0
        guard = 0
        while count < 5 and guard < 100:
            guard += 1
            px, py = cxs + (rng_t.random() - 0.5) * 0.9, cys + (rng_t.random() - 0.5) * 0.7
            if not (19.4 <= px <= 28.6 and 36.4 <= py <= 41.6):
                continue
            if any(math.hypot(px - qx, py - qy) < 0.16 for qx, qy in placed_scraps):
                continue
            if 21.4 <= px <= 26.6 and 34.6 <= py <= 36.8:
                continue
            L = 0.16 + 0.11 * rng_t.random()
            Wd = 0.012 + 0.01 * rng_t.random()
            bend = (rng_t.random() - 0.5) * 0.05
            poly = [(-L / 2, -Wd / 2), (-L / 4, -Wd / 2 + bend / 2), (0, -Wd / 2 + bend), (L / 4, -Wd / 2 + bend / 2), (L / 2, -Wd / 2 + bend * 0.2), (L / 2, Wd / 2 + bend * 0.2), (L / 4, Wd / 2 + bend / 2), (0, Wd / 2 + bend), (-L / 4, Wd / 2 + bend / 2), (-L / 2, Wd / 2)]
            V, F = prism_poly(poly, 0.0, 0.006 + 0.004 * rng_t.random())
            V = xf(V, Rz(rng_t.random() * math.pi), (px, py, 0.0))
            V[:, 2] += floor_z - 0.006
            straw_acc.add(V, F, vary(mixc(C_STRAW, C_HAY, rng_t.random()), rng_t, 0.1))
            placed_scraps.append((px, py))
            count += 1
    out['straw scraps'] = mk.emit(straw_acc, 'straw scraps', 'prop.straw', 'straw', sink=-0.006, bevel=False)
    out['straw_count'] = len(placed_scraps)

    # ================================================================== 13. IF TIME: two beehive skeps on a low bench behind cottage B, and a broken wheel by the road verge
    rng_q = np.random.default_rng(seed * 100 + 161)
    qx, qy = -6.2, 12.95
    check_spot('skep bench', qx, qy, 0.7)
    legs_g = [ground5(np.array([[qx + dx - 0.03, qy - 0.13, 0], [qx + dx + 0.03, qy + 0.13, 1]])) for dx in (-0.35, 0.35)]
    seat_z0 = max(legs_g) + 0.40
    acc = Acc()
    for dx, g in zip((-0.35, 0.35), legs_g):
        V, F = box(qx + dx - 0.03, qx + dx + 0.03, qy - 0.13, qy + 0.13, g - 0.012, seat_z0 + 0.004)
        acc.add(V, F, vary(C_TIMBER, rng_q, 0.08))
    V, F = box(qx - 0.50, qx + 0.50, qy - 0.16, qy + 0.16, seat_z0, seat_z0 + 0.04)
    acc.add(V, F, vary(C_TIMBER_L, rng_q, 0.08))
    out['low bench'] = mk.emit(acc, 'low bench', 'prop.furniture', 'wood', sink=0.012, mud=(max(legs_g), 0.15, 0.6), mud_rng=rng_q)
    bench_top = seat_z0 + 0.04
    for i, (dx, hh, rr0) in enumerate(((-0.22, 0.30, 0.20), (0.2, 0.27, 0.18))):
        prof = [(0.0, 0.0), (rr0, 0.0), (rr0 + 0.015, 0.03), (rr0 + 0.01, 0.10), (rr0 * 0.8, 0.18), (rr0 * 0.5, 0.25), (rr0 * 0.2, hh - 0.02), (0.0, hh)]
        V, F, M_ = lathe(prof, n=16, rfun=lambda k, ri, z: 1.0 + 0.05 * (1 if int(z * 28) % 2 else -1) * (1 if ri > 0 else 0))
        V = xf(V, Rz(rng_q.random() * 6), (qx + dx, qy, bench_top - 0.004))
        acc = Acc()
        acc.add(V, F, lambda k, f, V_, rr=rng_q: vary(mixc(C_STRAW, C_HAY_D, 0.35 + 0.4 * (int(float(np.mean([V_[i_][2] for i_ in f])) * 28) % 2)), rr, 0.05))
        out[f'skep {i + 1}'] = mk.emit(acc, f'skep {i + 1}', 'prop.wicker', 'wicker', rests_on_other=True, smooth=False, bevel=False)
    # the broken wheel: standing in the soft verge ground, a third of it sunk, tilted, three spokes gone and the rim broken
    rng_bw = np.random.default_rng(seed * 100 + 171)
    bwx, bwy = -2.2, -4.7
    check_spot('broken wheel', bwx, bwy, 0.6)
    Vw_, Fw_ = wheel_mesh(R=0.52, spokes=10, rng=rng_bw, missing=(3, 4, 5), rim_gap=(14, 26), hub_len=0.15)
    Vbw = xf(Vw_, Rz(0.6) @ Rx(math.radians(-14.0)), (bwx, bwy, 0.0))
    g_bw = ground5(Vbw)
    shift = (g_bw - 0.30) - Vbw[:, 2].min()
    Vbw[:, 2] += shift
    acc = Acc()
    acc.add(Vbw, Fw_, lambda kf, f, V_: wheel_colour(V_, f, Vbw, rng_bw, g_bw, axis=1))
    out['broken wheel'] = mk.emit(acc, 'broken wheel', 'prop.wheel', 'wood', sink=0.30, mud=(g_bw + 0.1, 0.5, 1.0), mud_rng=rng_bw)

    # ================================================================== the iron bands (one mesh for all of them)
    out['iron bands'] = mk.emit(iron_acc, 'iron bands', 'iron.fitting', 'iron', bevel=False)

    # ---------------------------------------------------------------- the seat notes (how far each object is sunk, and the ground it was seated on)
    bpy.context.view_layer.update()
    for obj in mk.objects:
        if obj is None:
            continue
        sink = obj.get('_want_sink')
        if '_want_sink' in obj.keys():
            del obj['_want_sink']
        if sink is None:
            continue
        g5 = pk_parts.ground_under(obj)
        if isinstance(sink, str):
            low = min(float(v_.co[2]) for v_ in obj.data.vertices) + obj.location.z
            sink = g5 - low
        obj[pk_names.SEAT_GROUND_Z] = float(g5)
        obj[pk_names.SEAT_SINK] = float(sink)
    for obj in mk.objects:
        if obj is not None:
            obj['props_part'] = True
    bpy.context.view_layer.update()
    total = len([o for o in mk.objects if o is not None])
    print(f'PROPS STAGE: objects created: {total}; changed: 0; deleted: 0 (apart from what an earlier run of this owner made); problems with keep-clear: {len(PROBLEMS)}')
    for line in PROBLEMS:
        print('KEEP-CLEAR PROBLEM:', line)
    return {'objects': [o.name for o in mk.objects if o is not None], 'problems': list(PROBLEMS), 'straw': out.get('straw_count'), 'ladder_top': out.get('ladder_top')}


def wheel_colour(V, f, Vall, rng, g, axis=1):
    """The colour of one face of a wheel: dark oak hub, lighter spokes, weathered rim (judged from the face's distance from the wheel's centre)."""
    c = np.mean([V[i] for i in f], axis=0)
    centre = Vall.mean(axis=0)
    d = c - centre
    d[axis] = 0.0
    r = float(np.linalg.norm(d))
    if r < 0.14:
        base = C_OAK
    elif r > 0.46:
        base = mixc(C_TIMBER, C_SILVER, 0.35)
    else:
        base = C_TIMBER_L
    return vary(base, rng, 0.07)


# ---- variation hook wrapper: the variations tool calls apply(variation); the stage's own apply takes the options
_STAGE_APPLY = apply


def apply(variation):
    """Runs inside Blender on a freshly opened copy of the built scene (never saved): rebuilds the props with the variation's numbers."""
    return _STAGE_APPLY(dict(variation.get('args') or {}))
