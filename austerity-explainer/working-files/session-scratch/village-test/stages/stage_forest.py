"""stage_forest.py : the FOREST part of the forest village (owner 'forest', collection 'Place: forest').

What it makes (all seated on the frozen ground, nothing else is touched):
  * about 12 hero trees (one trunk object and one crown object each) at the clearing's rim, nearest the four view cameras;
  * tree clusters (one trunk object and one crown object holding 3 to 6 separate trees) all round out to 150 m, among them tight groups either side of both
    ends of the high road, which hide where the road goes;
  * undergrowth (bushes and ferns, joined into a few objects), 6 stumps, 4 fallen logs, 8 mossy boulders, a moss cushion at the north foot of every trunk.
Roles: trunks, stumps and logs tree.bark; crowns, bushes, ferns and moss plant.foliage; boulders stone.rock.
Rules it keeps (ownership.json contracts): no trunk within 14 m of a wall or inside the stable yard; inside the clearing only at its rim and 10 m from a road edge;
none on the south-east side of a building and no crown shadow on a road, wall, yard or the middle of the clearing; the view cameras' sightlines stay clear;
no tree, stump or log on a road (3 m from a road edge at least); no prop of any kind.
It is IDEMPOTENT (it forgets what it made, then makes it again from a fixed seed) and reads only the ground, the cameras and the sun (never changes them).
Options (all optional): seed, crown_lump (0.05 to 0.35), far_clusters (count), crown_scale, moss_scale, hero_count.
Needs Blender (bpy), numpy and the place kit (EXPLAINER_FILM_KIT names the kit folder when it is not already importable).
"""
import copy
import math
import os
import sys

import numpy as np

import bpy
import mathutils
from mathutils.kdtree import KDTree

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
if KIT and os.path.join(KIT, 'place-kit') not in sys.path:
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
import place_kit as pk  # noqa: E402
from place_kit import parts as pkp  # noqa: E402
from place_kit import settings_file as pk_settings  # noqa: E402
from place_kit.surfaces import materials as pk_materials  # noqa: E402

OWNER = 'forest'

# ------------------------------------------------------------------ facts from the plan files (place-settings.json, style-note.md section 8, brief)
HIGH_ROAD = [(-140, -34), (-110, -18), (-80, -6), (-45, -1.5), (-12, 0.5), (20, 2), (52, -2.5), (85, -10), (115, -19), (140, -33)]
LANE = [(20, 2), (20.5, 10), (22, 18), (24, 26), (24.3, 34.2)]
ROAD_HALF = {'high': 2.5, 'lane': 1.7}
CLEARING = (-50.0, -32.0, 60.0, 50.0)                      # x0, y0, x1, y1
REGION = (-150.0, -90.0, 150.0, 90.0)
# buildings (centre x, centre y, size x, size y); the log store of A reaches 3 m further west
BUILDINGS = [('A', -32.0, 10.0, 11.1, 4.8), ('A store', -39.0, 10.0, 3.0, 4.8), ('B', -6.0, 9.5, 6.4, 4.6), ('C', -26.0, -10.5, 7.4, 4.6), ('D', 4.0, -8.0, 3.7, 4.4),
             ('stable', 24.0, 39.0, 9.8, 6.0)]
YARD = (14.0, 24.0, 34.0, 36.0)
WALL_CLEAR = 14.8            # trunk to wall (the contract says 14 m)
CLEARING_ROAD_CLEAR = 10.5   # trunk to road edge inside the clearing (the contract says 10 m)
ROAD_EDGE_MIN = 3.2          # a trunk outside the clearing stands at least this far from a road's edge
SUN_DOWN = (-0.455, 0.455, -0.766)                         # the way the sun's light travels (read from the Sun lamp when there is one)
FALLBACK_CAMERAS = {
    'View wide': ((-50.15, -27.9, 14.0), (0.72, 0.667), 28.0, 70.0),
    'View road_eye': ((-62.0, -3.7, 1.25), (1.0, -0.1), 35.0, 100.0),
    'View stable_close': ((28.5, 25.5, 1.97), (-0.394, 0.919), 28.0, 30.0),
    'View cottage_close': ((-12.76, 3.03, 1.6), (-0.965, 0.262), 35.0, 40.0),
}
CORRIDOR_LENGTH = {'View wide': 70.0, 'View road_eye': 100.0, 'View stable_close': 30.0, 'View cottage_close': 40.0}
SIGHT_MARGIN = 6.0

# foliage tones: dark greens of the style note's #3F5A32 family, a bluer green for pines, one golden brown, and moss
TONES = {
    'dark': ['#34502b', '#2c4725', '#3d5a30'],
    'mid': ['#3f5a32', '#364f2c', '#4a6838'],
    'olive': ['#4a5e30', '#3f5429', '#566b36'],
    'pine': ['#2f4a35', '#274030', '#385540'],
    'golden': ['#8a6a2e', '#74561f', '#9a7a3a'],
    'moss': ['#5e8236', '#6c8f3d', '#7c9a44'],
}
TONE_NAMES = {'dark': 'Forest leaf dark green', 'mid': 'Forest leaf mid green', 'olive': 'Forest leaf olive green', 'pine': 'Forest leaf pine green', 'golden': 'Forest leaf golden brown',
              'moss': 'Forest moss green'}

_REJECTS = {}
_SINK = {'i': 0}


def next_sink():
    """Between 3 and 18 mm, in a golden-ratio order (neighbours never sink the same): how far a moss cushion or a bush lump's flat foot lies below the ground's top."""
    _SINK['i'] += 1
    return 0.003 + 0.015 * ((_SINK['i'] * 0.6180339887) % 1.0)


def _reject(reason):
    _REJECTS[reason] = _REJECTS.get(reason, 0) + 1
    return False


# ------------------------------------------------------------------ small mesh tools (numpy, bulk)
_ICO = {}


def ico(sub):
    """A unit icosphere (vertices, triangles), outward facing."""
    if sub in _ICO:
        return _ICO[sub]
    t = (1.0 + 5 ** 0.5) / 2.0
    v = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], dtype=float)
    v /= np.linalg.norm(v, axis=1)[:, None]
    f = np.array([(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
                  (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)], dtype=np.int64)
    for _ in range(sub):
        verts = [tuple(p) for p in v]
        cache = {}
        faces = []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                p = (np.array(verts[a]) + np.array(verts[b])) / 2.0
                p /= np.linalg.norm(p)
                verts.append(tuple(p))
                cache[key] = len(verts) - 1
            return cache[key]
        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        v, f = np.array(verts), np.array(faces, dtype=np.int64)
    _ICO[sub] = (v, f)
    return v, f


def orient(v, f):
    """Turns the triangles round when the closed piece has a negative volume (so every normal points out)."""
    tri = v[f]
    volume = np.einsum('ij,ij->i', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0
    return (v, f[:, [0, 2, 1]]) if volume < 0 else (v, f)


class Acc:
    """Collects pieces (vertices, triangles) into one mesh; a piece may carry a foliage tone (a material slot of the mesh)."""

    def __init__(self):
        self.v, self.f, self.n, self.pieces, self.tone = [], [], 0, 0, []

    def add(self, v, f, closed=True, tone=None, open_foot=False):
        """open_foot=True leaves out the flat triangles of the foot (they lie under the ground; two feet at the same height would be twin faces that flicker)."""
        v, f = np.asarray(v, dtype=float), np.asarray(f, dtype=np.int64)
        if closed:
            v, f = orient(v, f)
        if open_foot:
            low = v[:, 2].min()
            flat = np.all(v[f][:, :, 2] <= low + 1e-4, axis=1)
            f = f[~flat]
            used = np.unique(f)                       # leave out the points only the foot used
            remap = -np.ones(len(v), dtype=np.int64)
            remap[used] = np.arange(len(used))
            v, f = v[used], remap[f]
        self.v.append(v)
        self.f.append(f + self.n)
        self.tone.append(tone)
        self.n += len(v)
        self.pieces += 1

    def triangles(self):
        return int(sum(len(f) for f in self.f))

    def bounds(self):
        v = np.vstack(self.v)
        return v.min(axis=0), v.max(axis=0)

    def to_mesh(self, name, materials=None):
        mesh = bpy.data.meshes.new(name)
        if not self.v:
            return mesh
        v = np.vstack(self.v)
        f = np.vstack(self.f)
        mesh.from_pydata(v.tolist(), [], f.tolist())
        mesh.update()
        mesh.validate()
        tones = [t for t in dict.fromkeys(self.tone) if t is not None]
        if tones and materials:
            for t in tones:
                mesh.materials.append(materials[t])
            index = np.concatenate([np.full(len(fp), tones.index(t) if t in tones else 0, dtype=np.int32) for fp, t in zip(self.f, self.tone)])
            mesh.polygons.foreach_set('material_index', index)
            mesh.update()
        return mesh


def box_probes(low, high, inside=0.9):
    return pkp.box_footprint_points(low, high, inside)


def seat_shift(v, sink=0.0):
    """How far to lift a piece (vertices v, world xy already final) so its lowest point is the ground height the construction check reads under it (centre and four pulled-in corners),
    less `sink` (a few millimetres for a moss cushion or a bush lump, so its flat foot never lies in the same plane as another piece's foot)."""
    low, high = v.min(axis=0), v.max(axis=0)
    best = None
    for x, y in box_probes(low, high):
        found = pkp.ground_probe(x, y)
        if found is not None and (best is None or found[0] > best):
            best = found[0]
    if best is None:
        best = 0.0
    return best - float(low[2]) - sink


# ------------------------------------------------------------------ the world the trees stand in (ground, cameras, sun, buildings)
class World:
    def __init__(self):
        scene = bpy.context.scene
        # road surface points (from the frozen ground's own road meshes): the edge of a road is read from them
        pts, lane_pts = [], []
        for obj in scene.objects:
            if obj.type == 'MESH' and (obj.get('place_role') or '') == 'ground.dirt_road':
                mesh = obj.data
                n = len(mesh.vertices)
                co = np.empty(n * 3)
                mesh.vertices.foreach_get('co', co)
                co = co.reshape(n, 3)
                m = np.array(obj.matrix_world)
                w = co @ m[:3, :3].T + m[:3, 3]
                (lane_pts if 'lane' in obj.name else pts).append(w[:, :2])
        if not pts:                        # no road meshes in the scene: sample the polylines at the road's half width
            pts.append(polyline_samples(HIGH_ROAD, 0.5))
            lane_pts.append(polyline_samples(LANE, 0.5))
        allp = np.vstack(pts + lane_pts)
        step = max(1, len(allp) // 60000)
        allp = allp[::step]
        self.road_pts = allp
        self.road_kd = KDTree(len(allp))
        for i, p in enumerate(allp):
            self.road_kd.insert((float(p[0]), float(p[1]), 0.0), i)
        self.road_kd.balance()
        self.high_line = polyline_samples(HIGH_ROAD, 1.0)
        self.lane_line = polyline_samples(LANE, 1.0)
        # sun
        sun = next((o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN' and not o.hide_render), None)
        if sun is not None:
            d = sun.matrix_world.to_3x3() @ mathutils.Vector((0.0, 0.0, -1.0))
            d.normalize()
        else:
            d = mathutils.Vector(SUN_DOWN).normalized()
        self.shadow_k = (float(d.x / -d.z), float(d.y / -d.z))        # shadow offset on the ground per metre of height
        # cameras
        self.cameras = {}
        for name, (loc, fwd, lens, _length) in FALLBACK_CAMERAS.items():
            cam = scene.objects.get(name)
            sensor = 36.0
            if cam is not None and cam.type == 'CAMERA':
                m = cam.matrix_world
                loc = (float(m.translation.x), float(m.translation.y), float(m.translation.z))
                f3 = m.to_3x3() @ mathutils.Vector((0.0, 0.0, -1.0))
                fwd = (float(f3.x), float(f3.y))
                lens = float(cam.data.lens)
                sensor = float(cam.data.sensor_width)
            f = np.array(fwd, dtype=float)
            f /= max(np.linalg.norm(f), 1e-9)
            self.cameras[name] = {'loc': np.array(loc, dtype=float), 'fwd': f, 'hfov': 2.0 * math.atan(sensor / (2.0 * lens)), 'length': CORRIDOR_LENGTH[name]}
        # buildings: the plan's footprints, widened by the real objects of the other parts when they are in the scene
        self.rects = [(cx - sx / 2.0, cy - sy / 2.0, cx + sx / 2.0, cy + sy / 2.0) for _n, cx, cy, sx, sy in BUILDINGS]
        for obj in scene.objects:
            if obj.type == 'MESH' and (obj.name.startswith('Cottage ') or obj.name.startswith('Stable')) and obj.get('place_owner') in ('cottages_north', 'cottages_south', 'stable'):
                corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
                self.rects.append((min(c.x for c in corners), min(c.y for c in corners), max(c.x for c in corners), max(c.y for c in corners)))
        # the places that must stay in the sun: roads inside the clearing, walls (1.5 m round), the yard, the middle of the clearing
        prot = []
        x0, y0, x1, y1 = CLEARING
        inside = (allp[:, 0] > x0) & (allp[:, 0] < x1) & (allp[:, 1] > y0) & (allp[:, 1] < y1)
        rp = allp[inside]
        prot.append(rp[:: max(1, len(rp) // 6000)])
        for rx0, ry0, rx1, ry1 in self.rects:
            gx, gy = np.meshgrid(np.arange(rx0 - 1.5, rx1 + 1.6, 1.0), np.arange(ry0 - 1.5, ry1 + 1.6, 1.0))
            prot.append(np.stack([gx.ravel(), gy.ravel()], axis=1))
        gx, gy = np.meshgrid(np.arange(YARD[0] - 1, YARD[2] + 1.1, 1.5), np.arange(YARD[1] - 1, YARD[3] + 1.1, 1.5))
        prot.append(np.stack([gx.ravel(), gy.ravel()], axis=1))
        gx, gy = np.meshgrid(np.arange(x0 + 5, x1 - 4.9, 2.0), np.arange(y0 + 5, y1 - 4.9, 2.0))
        prot.append(np.stack([gx.ravel(), gy.ravel()], axis=1))
        prot = np.vstack(prot)
        self.prot_kd = KDTree(len(prot))
        for i, p in enumerate(prot):
            self.prot_kd.insert((float(p[0]), float(p[1]), 0.0), i)
        self.prot_kd.balance()

    # ---- distances
    def road_edge_distance(self, x, y):
        _co, _i, dist = self.road_kd.find((float(x), float(y), 0.0))
        return float(dist)

    def centre_distance(self, x, y):
        d1 = np.min(np.hypot(self.high_line[:, 0] - x, self.high_line[:, 1] - y))
        d2 = np.min(np.hypot(self.lane_line[:, 0] - x, self.lane_line[:, 1] - y))
        return float(min(d1, d2))

    def wall_distance(self, x, y):
        best = 1e9
        for rx0, ry0, rx1, ry1 in self.rects:
            dx = max(rx0 - x, 0.0, x - rx1)
            dy = max(ry0 - y, 0.0, y - ry1)
            best = min(best, math.hypot(dx, dy))
        return best

    def shaded_protected(self, x, y, spec):
        """True when any part of the tree's shadow falls on a protected place (a road inside the clearing, a wall, the yard, the middle of the clearing)."""
        kx, ky = self.shadow_k
        for cx, cy, cz, r in spec['shadow_discs']:
            sx = x + cx + kx * cz
            sy = y + cy + ky * cz
            if self.prot_kd.find_n((float(sx), float(sy), 0.0), 1)[0][2] < r:
                return True
        return False

    def in_clearing(self, x, y, shrink=0.0):
        x0, y0, x1, y1 = CLEARING
        return (x0 + shrink) <= x <= (x1 - shrink) and (y0 + shrink) <= y <= (y1 - shrink)

    def rim_depth(self, x, y):
        """How far inside the clearing's edge a point is (negative outside)."""
        x0, y0, x1, y1 = CLEARING
        return min(x - x0, x1 - x, y - y0, y1 - y)

    def sight_distance(self, x, y, name):
        cam = self.cameras[name]
        p = np.array([x, y]) - cam['loc'][:2]
        t = float(np.clip(p @ cam['fwd'], 0.0, cam['length']))
        return float(np.linalg.norm(p - cam['fwd'] * t))

    def in_frustum(self, x, y, name, near, margin_deg=12.0):
        cam = self.cameras[name]
        p = np.array([x, y]) - cam['loc'][:2]
        dist = float(np.linalg.norm(p))
        if dist > near:
            return False
        if dist < 1e-6:
            return True
        ang = math.acos(max(-1.0, min(1.0, float(p @ cam['fwd']) / dist)))
        return ang < cam['hfov'] / 2.0 + math.radians(margin_deg)

    def sees(self, x, y, far=140.0):
        """How many cameras have (x, y) inside their horizontal view within `far` metres."""
        return sum(1 for name in self.cameras if self.in_frustum(x, y, name, far, 0.0))


def polyline_samples(points, step):
    pts = np.array(points, dtype=float)
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for i in range(n):
            out.append(a + (b - a) * (i / n))
    out.append(pts[-1])
    return np.array(out)


def side_point(samples, index, side, offset):
    """The point `offset` metres from the road centre line at sample `index`, on side +1 (left of the way of travel) or -1."""
    i0, i1 = max(index - 1, 0), min(index + 1, len(samples) - 1)
    t = samples[i1] - samples[i0]
    t = t / max(np.linalg.norm(t), 1e-9)
    n = np.array([-t[1], t[0]])
    return samples[index] + n * side * offset


# ------------------------------------------------------------------ trees: the specs (sizes, crown lumps) and the meshes
def tree_spec(rng, kind, hero, opt, lean=None):
    """Random sizes for one tree. Lengths in metres, positions relative to the foot of the trunk. lean = (degrees, heading in radians) for a leaning tree."""
    lean_deg = rng.uniform(0.0, 2.2)
    lean_dir = rng.uniform(0, 2 * math.pi)
    if lean is not None:
        lean_deg, lean_dir = lean
    if kind == 'B':
        H = rng.uniform(15.6, 24.6)
        dia = 0.35 + (H - 14.0) / 10.0 * rng.uniform(0.25, 0.55) + rng.uniform(0.0, 0.1)
        dia = float(np.clip(dia, 0.38, 0.88))
        spec = {'kind': 'B', 'H': H, 'r_br': dia / 2.0, 'r_top': max(0.13, dia * 0.22), 'seg': 12 if hero else 10}
        Rt = H * rng.uniform(0.19, 0.24) * opt['crown_scale']
        zt = H - Rt                                         # centre of the top lump
        lumps = [(0.0, 0.0, zt, Rt * rng.uniform(0.95, 1.05), Rt * rng.uniform(0.95, 1.05), Rt * rng.uniform(0.85, 1.0))]
        count = int(rng.integers(3, 6))                     # 3 to 5 lumps
        base_angle = rng.uniform(0, 2 * math.pi)
        for k in range(count - 1):
            ang = base_angle + 2 * math.pi * (k + rng.uniform(-0.15, 0.15)) / (count - 1)
            R = Rt * rng.uniform(0.7, 1.0)
            d = R * rng.uniform(0.25, 0.5)                  # near enough to the trunk for the lump to be carried by it
            dz = -Rt * rng.uniform(0.4, 1.5)
            lumps.append((d * math.cos(ang), d * math.sin(ang), zt + dz, R * rng.uniform(0.95, 1.05), R * rng.uniform(0.95, 1.05), R * rng.uniform(0.8, 0.95)))
        spec['lumps'] = lumps
        spec['T'] = zt + 0.1 * Rt                           # trunk top: inside the top lump
        spec['crown_r'] = max(math.hypot(l[0], l[1]) + max(l[3], l[4]) for l in lumps)
        spec['top'] = max(l[2] + l[5] for l in lumps)
    else:
        H = rng.uniform(16.5, 30.0)
        dia = 0.3 + (H - 16.0) / 14.0 * rng.uniform(0.2, 0.32) + rng.uniform(0.0, 0.08)
        dia = float(np.clip(dia, 0.32, 0.68))
        spec = {'kind': 'P', 'H': H, 'r_br': dia / 2.0, 'r_top': 0.1, 'seg': 12 if hero else 10}
        n = int(rng.integers(4, 7))                          # 4 to 6 stacked cones in the top half
        z0 = H * rng.uniform(0.44, 0.52)
        top_h = H * rng.uniform(0.12, 0.16)
        step = (H - z0 - top_h) / (n - 1)
        Rb = H * rng.uniform(0.1, 0.14) * opt['crown_scale']
        cones = []
        for k in range(n):
            frac = k / (n - 1)
            R = Rb * (1.0 - 0.62 * frac) * rng.uniform(0.92, 1.08)
            h = max(step * 1.7, 2.0) if k < n - 1 else top_h
            if k == n - 1:
                R = Rb * 0.38 * rng.uniform(0.9, 1.1)
            cones.append((z0 + k * step, h, R, rng.uniform(0, 2 * math.pi)))
        spec['cones'] = cones
        spec['T'] = H - top_h * 0.45
        spec['crown_r'] = max(c[2] for c in cones)
        spec['top'] = cones[-1][0] + cones[-1][1]
    spec['lean'] = (math.tan(math.radians(lean_deg)) * math.cos(lean_dir), math.tan(math.radians(lean_deg)) * math.sin(lean_dir))
    spec['sway'] = rng.uniform(0.0, 0.35 if kind == 'B' else 0.2)
    spec['phase'] = rng.uniform(0, 2 * math.pi)
    spec['flare'] = rng.uniform(0.35, 0.6)
    spec['seed'] = int(rng.integers(1, 10 ** 9))
    spec['crown_r'] += math.hypot(*axis_xy(spec, spec['top']))
    spec['hero'] = hero
    spec['golden'] = False
    spec['tone'] = 'mid'
    # the tree's shadow, as discs (centre offset from the foot, height, radius): the trunk every 2.5 m, and the crown
    discs = []
    for z in np.arange(1.0, spec['T'] + 0.1, 2.5):
        ax = axis_xy(spec, z)
        discs.append((ax[0], ax[1], float(z), spec['r_br'] + 0.4))
    if kind == 'B':
        for cx, cy, cz, rx, ry, rz in spec['lumps']:
            ax = axis_xy(spec, min(cz, spec['T']))
            discs.append((cx + ax[0], cy + ax[1], cz, 1.3 * max(rx, ry) + 0.3))
    else:
        for z, h, R, _p in spec['cones']:
            ax = axis_xy(spec, min(z, spec['T']))
            for fr, rr in ((0.0, R), (0.5, R * 0.5), (0.9, R * 0.12)):
                discs.append((ax[0], ax[1], z + fr * h, 1.3 * rr + 0.3))
    spec['shadow_discs'] = discs
    return spec


def axis_xy(spec, z):
    """Where the trunk's middle is at height z (a slight lean and a slow sway), relative to the foot."""
    H = spec['H']
    s = spec['sway'] * math.sin(math.pi * 1.2 * z / H + spec['phase'])
    lx, ly = spec['lean']
    # the sway pushes sideways to the lean
    px, py = -ly, lx
    norm = math.hypot(px, py) or 1.0
    return (lx * z + px / norm * s, ly * z + py / norm * s)


def build_trunk(spec, x, y, rng, marks, ragged=False):
    """One tapered, faceted trunk with a root flare (flat foot at z=0). Returns vertices (world xy, z from 0) and triangles."""
    seg = spec['seg']
    T = spec['T']
    zs = [0.0, 0.3, 0.8, 1.6, 2.6]
    zs = [z for z in zs if z < T - 1.0]
    z = zs[-1] + rng.uniform(1.8, 2.6)
    while z < T - 1.2:
        zs.append(z)
        z += rng.uniform(1.8, 2.8)
    zs.append(T)
    zs = np.array(zs)
    nr = len(zs)
    theta = np.arange(seg) * 2 * math.pi / seg + rng.uniform(0, 0.4)
    taper = (zs / T) ** 0.85
    rad = spec['r_br'] + (spec['r_top'] - spec['r_br']) * taper
    flare = 1.0 + spec['flare'] * np.exp(-zs / 0.6)
    lobes = int(rng.integers(3, 5))
    phi = rng.uniform(0, 2 * math.pi)
    butt = (np.maximum(0.0, np.cos(lobes * (theta[None, :] - phi) / 1.0 * 1.0)) ** 2) * np.exp(-zs / 0.9)[:, None]
    R = (rad * flare)[:, None] * (1.0 + 0.4 * butt) * (1.0 + 0.05 * rng.uniform(-1, 1, (nr, seg)))
    # designed marks: a scar (a clean vertical groove), a hollow (a big dent) and a burr (a round bump), on a trunk that is allowed them
    if marks:
        j0 = int(rng.integers(0, seg))
        if nr > 5 and 'scar' in marks:
            k = 4 if nr > 6 else 3
            for kk in (k, k + 1):
                for jj in (j0, (j0 + 1) % seg):
                    R[kk, jj] *= 0.55
        if 'hollow' in marks:
            j1 = (j0 + seg // 2) % seg
            for kk in (2, 3):
                for jj in (j1 - 1, j1, (j1 + 1) % seg):
                    R[kk, jj % seg] *= 0.52
        if 'burr' in marks and nr > 7:
            j2 = (j0 + seg // 3) % seg
            for jj in (j2, (j2 + 1) % seg):
                R[5, jj] *= 1.38
    cx = np.array([axis_xy(spec, z)[0] for z in zs])
    cy = np.array([axis_xy(spec, z)[1] for z in zs])
    verts = np.zeros((nr, seg, 3))
    verts[:, :, 0] = cx[:, None] + R * np.cos(theta)[None, :]
    verts[:, :, 1] = cy[:, None] + R * np.sin(theta)[None, :]
    verts[:, :, 2] = zs[:, None]
    if ragged:                      # a broken top: the last ring is torn at uneven heights
        verts[-1, :, 2] += rng.uniform(-0.85, 0.5, seg)
    flat = verts.reshape(-1, 3)
    bottom_c = np.array([[cx[0], cy[0], zs[0]]])
    top_c = np.array([[cx[-1], cy[-1], float(verts[-1, :, 2].max()) + (0.05 if ragged else 0.15)]])
    V = np.vstack([flat, bottom_c, top_c])
    tris = []
    for i in range(nr - 1):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            c, d = (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j
            tris += [(a, b, c), (a, c, d)]
    bc, tc = nr * seg, nr * seg + 1
    for j in range(seg):
        a, b = j, (j + 1) % seg
        tris.append((bc, b, a))
        a, b = (nr - 1) * seg + j, (nr - 1) * seg + (j + 1) % seg
        tris.append((tc, a, b))
    V[:, 0] += x
    V[:, 1] += y
    return V, np.array(tris, dtype=np.int64)


def build_lump(cx, cy, cz, rx, ry, rz, rng, amp, sub, x, y):
    v, f = ico(sub)
    jitter = 1.0 + amp * rng.uniform(-1.0, 1.0, len(v))
    p = v * jitter[:, None]
    ang = rng.uniform(0, 2 * math.pi)
    ca, sa = math.cos(ang), math.sin(ang)
    px = p[:, 0] * rx
    py = p[:, 1] * ry
    pz = p[:, 2] * rz
    out = np.stack([px * ca - py * sa + cx + x, px * sa + py * ca + cy + y, pz + cz], axis=1)
    return out, f


def build_cone(x, y, ax, z, h, R, phase, seg, rng):
    """A cone (apex up, flat base) with a star-shaped base ring (alternating long and short points)."""
    ang = np.arange(seg) * 2 * math.pi / seg + phase
    rr = R * np.where(np.arange(seg) % 2 == 0, 1.0, 0.8) * (1.0 + 0.06 * rng.uniform(-1, 1, seg))
    ring = np.stack([ax[0] + rr * np.cos(ang) + x, ax[1] + rr * np.sin(ang) + y, np.full(seg, z)], axis=1)
    apex = np.array([[ax[0] + x + rng.uniform(-0.15, 0.15), ax[1] + y + rng.uniform(-0.15, 0.15), z + h]])
    base_c = np.array([[ax[0] + x, ax[1] + y, z]])
    V = np.vstack([ring, apex, base_c])
    tris = []
    for j in range(seg):
        a, b = j, (j + 1) % seg
        tris.append((a, b, seg))
        tris.append((seg + 1, b, a))
    return V, np.array(tris, dtype=np.int64)


def build_tree(spec, x, y, trunk_acc, crown_acc, rng, opt, sub):
    """Adds one tree to a trunk mesh and a crown mesh, seated on the ground (the crown is lifted with its trunk)."""
    marks = []
    if spec['hero']:
        marks = ['scar', 'hollow', 'burr']
    else:
        r = rng.random()
        if r < 0.25:
            marks = ['scar']
        elif r < 0.45:
            marks = ['hollow']
        elif r < 0.6:
            marks = ['burr']
    tv, tf = build_trunk(spec, x, y, rng, marks)
    dz = seat_shift(tv)
    tv[:, 2] += dz
    trunk_acc.add(tv, tf, open_foot=True)
    pieces = 0
    if spec['kind'] == 'B':
        for cx, cy, cz, rx, ry, rz in spec['lumps']:
            # lumps are placed round the trunk's own axis at their height (so a leaning tree carries its crown)
            lv, lf = build_lump(cx + (axis_xy(spec, cz)[0] if cz <= spec['T'] else axis_xy(spec, spec['T'])[0]), cy + (axis_xy(spec, cz)[1] if cz <= spec['T'] else axis_xy(spec, spec['T'])[1]), cz, rx, ry, rz,
                                rng, opt['crown_lump'], sub, x, y)
            lv[:, 2] += dz
            crown_acc.add(lv, lf, tone=spec['tone'])
            pieces += 1
    else:
        for z, h, R, phase in spec['cones']:
            ax = axis_xy(spec, min(z, spec['T']))
            cv, cf = build_cone(x, y, ax, z, h, R, phase, 12 if spec['hero'] else 10, rng)
            cv[:, 2] += dz
            crown_acc.add(cv, cf, tone='pine')
            pieces += 1
    spec['foot'] = (x, y, float(tv[:, 2].min()))
    return dz


# ------------------------------------------------------------------ checks for a place to stand
def tree_ok(world, spec, x, y, others, hero=False, min_gap=3.4, sight=True, why=True):
    x0, y0, x1, y1 = REGION
    if not (x0 + 3 <= x <= x1 - 3 and y0 + 3 <= y <= y1 - 3):
        return _reject('region')
    if world.wall_distance(x, y) < WALL_CLEAR:
        return _reject('wall 14 m')
    if YARD[0] - 4 <= x <= YARD[2] + 4 and YARD[1] - 4 <= y <= YARD[3] + 8:
        return _reject('yard')
    edge = world.road_edge_distance(x, y)
    inside = world.in_clearing(x, y)
    if inside:
        if world.rim_depth(x, y) > 9.0:
            return _reject('inside clearing, not rim')
        if edge < CLEARING_ROAD_CLEAR + spec['r_br']:
            return _reject('clearing road 10 m')
    else:
        if edge < ROAD_EDGE_MIN + spec['r_br']:
            return _reject('road edge')
    if world.centre_distance(x, y) < 5.0:
        return _reject('road centre')
    # south-east of a building: no tree there within 32 m (a shadow is at most 0.84 times the height long: about 25 m, and a crown is wide)
    for rx0, ry0, rx1, ry1 in world.rects:
        if x > rx1 - 0.5 and y < ry0 + 0.5 and math.hypot(x - rx1, y - ry0) < 32.0:
            return _reject('south-east of a building')
    if world.shaded_protected(x, y, spec):
        return _reject('shadow on road, wall, yard or clearing')
    if sight:
        for name, cam in world.cameras.items():
            margin = SIGHT_MARGIN + (spec['crown_r'] if name == 'View wide' else 0.0)
            if world.sight_distance(x, y, name) < margin:
                return _reject('sightline ' + name)
            if world.in_frustum(x, y, name, 22.0, 10.0):
                return _reject('near the camera ' + name)
            if np.linalg.norm(np.array([x, y]) - cam['loc'][:2]) < 12.0:
                return _reject('close to camera ' + name)
    for ox, oy, orad in others:
        if math.hypot(x - ox, y - oy) < min_gap + spec['r_br'] + orad:
            return _reject('too close to another trunk')
    return True


def low_ok(world, x, y, margin_edge=3.5, sight=3.5, wall=WALL_CLEAR - 3.0, others=(), gap=2.5, allow_clearing_rim=True):
    """A stump, log end, boulder or bush: not on or beside a road, not in the yard, away from walls, not in a sightline."""
    x0, y0, x1, y1 = REGION
    if not (x0 + 3 <= x <= x1 - 3 and y0 + 3 <= y <= y1 - 3):
        return False
    if world.wall_distance(x, y) < wall:
        return False
    if YARD[0] - 2 <= x <= YARD[2] + 2 and YARD[1] - 2 <= y <= YARD[3] + 4:
        return False
    if world.road_edge_distance(x, y) < margin_edge or world.centre_distance(x, y) < 4.5:
        return False
    if world.in_clearing(x, y):
        if not allow_clearing_rim or world.rim_depth(x, y) > 7.0 or world.road_edge_distance(x, y) < 9.0:
            return False
    for name in world.cameras:
        if world.sight_distance(x, y, name) < sight:
            return False
        if np.linalg.norm(np.array([x, y]) - world.cameras[name]['loc'][:2]) < 9.0:
            return False
    for ox, oy, orad in others:
        if math.hypot(x - ox, y - oy) < gap + orad:
            return False
    return True


# ------------------------------------------------------------------ the small things: moss cushions, stumps, logs, boulders, bushes, ferns
def cushion(rng, x, y, rx, ry, rz, acc, sub=1, amp=0.12):
    """A moss cushion: a squashed half-ball with its flat foot 0.8 to 1.6 cm into the ground's skin (never in the same plane as a trunk's or a log's foot)."""
    v, f = ico(sub)
    jitter = 1.0 + amp * rng.uniform(-1.0, 1.0, len(v))
    p = v * jitter[:, None]
    p[:, 2] = np.maximum(p[:, 2], 0.0)
    out = np.stack([p[:, 0] * rx + x, p[:, 1] * ry + y, p[:, 2] * rz], axis=1)
    dz = seat_shift(out, sink=next_sink())
    out[:, 2] += dz
    acc.add(out, f, tone='moss', open_foot=True)
    return dz


def rock_mesh(rng, x, y, sx, sy, sz, sub=2, amp=0.22):
    v, f = ico(sub)
    jitter = 1.0 + amp * rng.uniform(-1.0, 1.0, len(v))
    p = v * jitter[:, None]
    # chiselled: squash the lower half flat so it rests, chamfer the sharp top
    p[:, 2] = np.where(p[:, 2] < -0.25, -0.25 + (p[:, 2] + 0.25) * 0.02, p[:, 2])
    ang = rng.uniform(0, 2 * math.pi)
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = p[:, 0] * sx, p[:, 1] * sy
    out = np.stack([px * ca - py * sa + x, px * sa + py * ca + y, (p[:, 2] + 0.25) * sz], axis=1)
    out[:, 2] -= out[:, 2].min()
    dz = seat_shift(out)
    out[:, 2] += dz
    return out, f


def stump_mesh(rng, x, y, dia, height, seg=10):
    zs = np.array([0.0, 0.12, height * 0.55, height])
    theta = np.arange(seg) * 2 * math.pi / seg + rng.uniform(0, 1)
    R = np.array([dia / 2 * 1.35, dia / 2 * 1.08, dia / 2 * 1.0, dia / 2 * 0.93])[:, None] * (1.0 + 0.07 * rng.uniform(-1, 1, (4, seg)))
    zt = zs[:, None] + np.zeros((4, seg))
    zt[3] += rng.uniform(-0.07, 0.07, seg)              # the broken top is uneven
    verts = np.zeros((4, seg, 3))
    verts[:, :, 0] = x + R * np.cos(theta)[None, :]
    verts[:, :, 1] = y + R * np.sin(theta)[None, :]
    verts[:, :, 2] = zt
    flat = verts.reshape(-1, 3)
    V = np.vstack([flat, [[x, y, 0.0]], [[x, y, height + 0.02]]])
    tris = []
    for i in range(3):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            c, d = (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j
            tris += [(a, b, c), (a, c, d)]
    bc, tc = 4 * seg, 4 * seg + 1
    for j in range(seg):
        tris.append((bc, (j + 1) % seg, j))
        tris.append((tc, 3 * seg + j, 3 * seg + (j + 1) % seg))
    V[:, 2] -= V[:, 2].min()
    dz = seat_shift(V)
    V[:, 2] += dz
    return V, np.array(tris, dtype=np.int64)


def log_mesh(rng, x, y, length, dia, heading, seg=8):
    """A fallen log lying along `heading`, tapered, with a flat facet down so it rests; a broken, uneven end."""
    n = 5
    ts = np.linspace(-0.5, 0.5, n) * length
    theta = (np.arange(seg) + 0.5) * 2 * math.pi / seg           # a facet is flat down at theta = -90 degrees (index chosen by orient)
    rr = dia / 2.0 * (1.0 - 0.18 * (np.linspace(0, 1, n))) [:, None] * (1.0 + 0.06 * rng.uniform(-1, 1, (n, seg)))
    verts = np.zeros((n, seg, 3))
    verts[:, :, 0] = ts[:, None]
    verts[:, :, 1] = rr * np.cos(theta)[None, :]
    verts[:, :, 2] = rr * np.sin(theta)[None, :]
    verts[-1, :, 0] += rng.uniform(-0.15, 0.15, seg)             # the broken end
    verts[:, :, 1] += (0.06 * np.sin(ts / length * 3.0 + 1.0))[:, None]
    flat = verts.reshape(-1, 3)
    V = np.vstack([flat, [[ts[0] - 0.02, 0, 0]], [[ts[-1] + 0.05, 0, 0]]])
    tris = []
    for i in range(n - 1):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            c, d = (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j
            tris += [(a, b, c), (a, c, d)]
    c0, c1 = n * seg, n * seg + 1
    for j in range(seg):
        tris.append((c0, (j + 1) % seg, j))
        tris.append((c1, (n - 1) * seg + j, (n - 1) * seg + (j + 1) % seg))
    ca, sa = math.cos(heading), math.sin(heading)
    out = np.stack([V[:, 0] * ca - V[:, 1] * sa + x, V[:, 0] * sa + V[:, 1] * ca + y, V[:, 2]], axis=1)
    out[:, 2] -= out[:, 2].min()
    dz = seat_shift(out)
    out[:, 2] += dz
    return out, np.array(tris, dtype=np.int64)


def fern_mesh(rng, x, y, size):
    """A fern: 7 to 9 arching blades from one centre (one connected piece)."""
    blades = int(rng.integers(7, 10))
    V = [np.array([x, y, 0.0])]
    F = []
    for k in range(blades):
        ang = 2 * math.pi * (k + rng.uniform(-0.2, 0.2)) / blades
        L = size * rng.uniform(0.75, 1.1)
        w = size * rng.uniform(0.09, 0.14)
        d = np.array([math.cos(ang), math.sin(ang)])
        nrm = np.array([-d[1], d[0]])
        prev = None
        for s, (t, widthf) in enumerate(((0.0, 0.5), (0.35, 1.0), (0.7, 0.8), (1.0, 0.0))):
            dist = t * L
            h = 0.5 * size * math.sin(min(t * 1.3, 1.0) * math.pi * 0.62) + 0.03
            c = np.array([x, y]) + d * dist
            if widthf == 0.0:
                V.append(np.array([c[0], c[1], h]))
                idx = (len(V) - 1,)
            else:
                V.append(np.array([c[0] + nrm[0] * w * widthf, c[1] + nrm[1] * w * widthf, h]))
                V.append(np.array([c[0] - nrm[0] * w * widthf, c[1] - nrm[1] * w * widthf, h]))
                idx = (len(V) - 2, len(V) - 1)
            if prev is None:
                F.append((0, idx[0], idx[1]))
            elif len(idx) == 2:
                F += [(prev[0], prev[1], idx[1]), (prev[0], idx[1], idx[0])]
            else:
                F.append((prev[0], prev[1], idx[0]))
            prev = idx
    V = np.array(V)
    V[:, 2] -= V[:, 2].min()
    dz = seat_shift(V)
    V[:, 2] += dz
    return V, np.array(F, dtype=np.int64)


def bush_pieces(rng, x, y, size):
    """A bush: two or three overlapping squashed lumps with flat feet. Yields (vertices, triangles) for each lump."""
    out = []
    count = int(rng.integers(2, 4))
    for k in range(count):
        ang = rng.uniform(0, 2 * math.pi)
        d = size * rng.uniform(0.0, 0.45) if k else 0.0
        px, py = x + d * math.cos(ang), y + d * math.sin(ang)
        r = size * rng.uniform(0.6, 0.95)
        v, f = ico(1)
        jitter = 1.0 + 0.16 * rng.uniform(-1.0, 1.0, len(v))
        p = v * jitter[:, None]
        p[:, 2] = np.maximum(p[:, 2], -0.05)
        w = np.stack([p[:, 0] * r + px, p[:, 1] * r * rng.uniform(0.9, 1.1) + py, p[:, 2] * r * 0.85 * rng.uniform(0.9, 1.15)], axis=1)
        w[:, 2] -= w[:, 2].min()
        dz = seat_shift(w, sink=next_sink())
        w[:, 2] += dz
        out.append((w, f))
    return out


# ------------------------------------------------------------------ the stage
_STATE = {'world': None, 'materials': None}


def make_tone_materials(size=1024):
    """The foliage materials of this part (not named PK, so the surface pass keeps them: they carry their own normal map). Built the kit's own way from the foliage surface, with a dark
    green palette of the style note. Rebuilt from nothing on every run."""
    made = {}
    base = pk_settings.surface('foliage')
    for tone, colours in TONES.items():
        name = TONE_NAMES[tone]
        old = bpy.data.materials.get(name)
        if old is not None:
            bpy.data.materials.remove(old)
        spec = copy.deepcopy(base)
        spec['colour']['palette'] = {'value': colours, 'unit': 'sRGB hex colours', 'kind': 'judged', 'source': 'style-note.md section 3 (dark leaf #3F5A32 family, moss #5E8236 to #7C9A44)'}
        material = pk_materials.build_surface_material('plant.foliage', 'foliage', spec, size, False, quick=size <= 256)
        material.name = name
        material['forest_tone'] = tone
        made[tone] = material
    return made


def make_object(role, name, acc):
    mesh = acc.to_mesh(name, _STATE['materials'] if role == 'plant.foliage' else None)
    obj = pk.new_part_object(OWNER, role, name, mesh)
    # far scenery that is large casts no shadow (the audit's place: world rule: a large object more than 100 m from every view camera)
    world = _STATE['world']
    if world is not None and acc.v:
        lo, hi = acc.bounds()
        middle = (lo[:2] + hi[:2]) / 2.0
        size = float(max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
        nearest = min(float(np.linalg.norm(middle - cam['loc'][:2])) for cam in world.cameras.values())
        if nearest > 96.0 and size > 15.0:
            obj.visible_shadow = False
    return obj


def apply(options):
    options = dict(options or {})
    opt = {
        'seed': int(options.get('seed', 11)),
        'crown_lump': float(options.get('crown_lump', 0.22)),
        'far_clusters': int(options.get('far_clusters', 23)),
        'rim_clusters': int(options.get('rim_clusters', 15)),
        'crown_scale': float(options.get('crown_scale', 1.1)),
        'moss_scale': float(options.get('moss_scale', 1.2)),
        'hero_count': int(options.get('hero_count', 12)),
        'golden': int(options.get('golden', 2)),
        'sub': int(options.get('lump_detail', 2)),
        'lean_share': float(options.get('lean_share', 0.25)),
        'snags': int(options.get('snags', 3)),
        'w_dark': float(options.get('w_dark', 0.25)),
        'w_mid': float(options.get('w_mid', 0.40)),
        'w_olive': float(options.get('w_olive', 0.35)),
    }
    _REJECTS.clear()
    _SINK['i'] = 0
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    pkp.refresh_ground()
    rng = np.random.default_rng(opt['seed'])
    world = World()
    _STATE['world'] = world
    _STATE['materials'] = make_tone_materials()
    placed = []                      # (x, y, trunk radius) of every trunk
    trees = []                       # (spec, x, y, group)

    # ---------------------------------------------------------- 1. hero trees: at the clearing's rim, nearest the cameras
    x0, y0, x1, y1 = CLEARING
    candidates = []
    for _ in range(9000):
        # a point at the rim: along the clearing's outline, 8 m inside to 14 m outside
        edge = rng.integers(0, 4)
        t = rng.random()
        off = rng.uniform(-8.0, 15.0)
        if edge == 0:
            px, py = x0 + t * (x1 - x0), y0 - off
        elif edge == 1:
            px, py = x0 + t * (x1 - x0), y1 + off
        elif edge == 2:
            px, py = x0 - off, y0 + t * (y1 - y0)
        else:
            px, py = x1 + off, y0 + t * (y1 - y0)
        candidates.append((px, py))
    scored = []
    for px, py in candidates:
        s = world.sees(px, py, 150.0)
        scored.append((s + rng.uniform(0.0, 1.6), px, py))
    scored.sort(key=lambda r: -r[0])
    heroes = []
    kinds = ['B', 'P', 'B', 'B', 'P', 'B', 'P', 'B', 'B', 'P', 'B', 'P']
    for k in range(opt['hero_count']):
        kind = kinds[k % len(kinds)]
        spec = None
        for s, px, py in scored:
            if s < 1.0:
                break
            if any(math.hypot(px - h[1], py - h[2]) < 16.0 for h in heroes):
                continue
            spec = tree_spec(rng, kind, True, opt)
            if tree_ok(world, spec, px, py, placed, hero=True):
                heroes.append((spec, px, py))
                placed.append((px, py, spec['r_br']))
                break
            spec = None
        if spec is None:
            continue
    for k, (spec, px, py) in enumerate(heroes):
        trees.append((spec, px, py, f'hero {k + 1:02d}'))

    # ---------------------------------------------------------- 2. road-end groups: tight groups either side of both ends of the high road, 3 to 6 m from its edge
    line = world.high_line
    groups = []
    for end in ('west', 'east'):
        if end == 'west':
            idx = [i for i in range(len(line)) if line[i][0] < -53.0]
            idx = idx[::-1]                          # from the clearing outward
        else:
            idx = [i for i in range(len(line)) if line[i][0] > 61.0]
        if not idx:
            continue
        for side in (1, -1):
            ngroups = 3
            span = len(idx) - 1
            for g in range(ngroups):
                members = []
                for attempt in range(5):
                    s = idx[min(span, int(span * (g + 0.5 + rng.uniform(-0.2, 0.2)) / ngroups))]
                    members = []
                    want = int(rng.integers(4, 7))
                    tries = 0
                    while len(members) < want and tries < 80:
                        tries += 1
                        j = int(np.clip(s + rng.integers(-7, 8), 0, len(line) - 1))
                        off = ROAD_HALF['high'] + rng.uniform(3.0, 6.0)
                        p = side_point(line, j, side, off)
                        kind = 'B' if rng.random() < 0.6 else 'P'
                        spec = tree_spec(rng, kind, False, opt)
                        if tree_ok(world, spec, float(p[0]), float(p[1]), placed + [(m[1], m[2], m[0]['r_br']) for m in members], min_gap=3.0):
                            members.append((spec, float(p[0]), float(p[1])))
                    if len(members) >= 3:
                        break
                if len(members) >= 3:
                    for m in members:
                        placed.append((m[1], m[2], m[0]['r_br']))
                    groups.append((f'road {end} {"north" if side == 1 else "south"} {g + 1}', members))

    # ---------------------------------------------------------- 3a. rim clusters: a belt of groups round the clearing, 6 to 24 m outside its edge
    rim = []
    tries = 0
    while len(rim) < opt['rim_clusters'] and tries < 3000:
        tries += 1
        edge = int(rng.integers(0, 4))
        t = rng.random()
        off = rng.uniform(6.0, 24.0)
        if edge == 0:
            cx, cy = x0 + t * (x1 - x0), y0 - off
        elif edge == 1:
            cx, cy = x0 + t * (x1 - x0), y1 + off
        elif edge == 2:
            cx, cy = x0 - off, y0 + t * (y1 - y0)
        else:
            cx, cy = x1 + off, y0 + t * (y1 - y0)
        if any(math.hypot(cx - r[0], cy - r[1]) < 13.0 for r in rim):
            continue
        members = []
        want = int(rng.integers(4, 7))
        t2 = 0
        while len(members) < want and t2 < 60:
            t2 += 1
            ang = rng.uniform(0, 2 * math.pi)
            rad = rng.uniform(0.5, 7.5)
            px, py = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
            kind = 'B' if rng.random() < 0.6 else 'P'
            lean = None
            if rng.random() < opt['lean_share']:                      # a leaning tree at the rim, leaning away from the village
                lean = (rng.uniform(6.0, 13.0), math.atan2(py - 0.0, px - 5.0) + rng.uniform(-0.4, 0.4))
            spec = tree_spec(rng, kind, False, opt, lean=lean)
            if tree_ok(world, spec, px, py, placed + [(m[1], m[2], m[0]['r_br']) for m in members]):
                members.append((spec, px, py))
        if len(members) >= 3:
            for m in members:
                placed.append((m[1], m[2], m[0]['r_br']))
            rim.append((cx, cy, members))

    # ---------------------------------------------------------- 3b. tree clusters all round, out to the region's edge
    centres = [(t[1], t[2]) for t in trees]
    far = []
    tries = 0
    while len(far) < opt['far_clusters'] and tries < 4000:
        tries += 1
        cx = rng.uniform(REGION[0] + 6, REGION[2] - 6)
        cy = rng.uniform(REGION[1] + 6, REGION[3] - 6)
        # keep the middle of the forest at its density: nearer the village is denser
        d = math.hypot(cx - 5, cy - 9)
        if d < 30:
            continue
        if any(math.hypot(cx - px, cy - py) < 12.0 for px, py in [(f[0], f[1]) for f in far]):
            continue
        members = []
        want = int(rng.integers(4, 7))
        t2 = 0
        while len(members) < want and t2 < 60:
            t2 += 1
            ang = rng.uniform(0, 2 * math.pi)
            rad = rng.uniform(0.5, 8.0)
            px, py = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
            kind = 'B' if rng.random() < 0.6 else 'P'
            spec = tree_spec(rng, kind, False, opt)
            if tree_ok(world, spec, px, py, placed + [(m[1], m[2], m[0]['r_br']) for m in members]):
                members.append((spec, px, py))
        if len(members) >= 3:
            for m in members:
                placed.append((m[1], m[2], m[0]['r_br']))
            far.append((cx, cy, members))
    for gname, members in groups:
        pass
    # the cluster lists in one order
    clusters = [(gname, members) for gname, members in groups] + [(f'rim {i + 1:02d}', m[2]) for i, m in enumerate(rim)] + [(f'forest {i + 1:02d}', m[2]) for i, m in enumerate(far)]

    # a few golden-brown trees among the crowns (judged: one or two allowed)
    pool = [m for _g, members in clusters for m in members if m[0]['kind'] == 'B']
    for k in range(min(opt['golden'], len(pool))):
        pool[int(rng.integers(0, len(pool)))][0]['golden'] = True
    # tones: broadleaf crowns draw from three dark greens by the weights; the golden ones are golden brown; pines are their own green
    weights = np.array([opt['w_dark'], opt['w_mid'], opt['w_olive']], dtype=float)
    weights /= weights.sum()
    tone_rng = np.random.default_rng(opt['seed'] + 7)
    for spec, *_rest in [(t[0],) for t in trees] + [m for _g, members in clusters for m in members]:
        if spec['kind'] == 'B':
            spec['tone'] = 'golden' if spec['golden'] else ['dark', 'mid', 'olive'][int(tone_rng.choice(3, p=weights))]

    # ---------------------------------------------------------- build the meshes
    moss = Acc()
    tri_count = 0
    mossy_spots = []
    objects = []
    for spec, x, y, gname in trees:
        ta, ca = Acc(), Acc()
        build_tree(spec, x, y, ta, ca, np.random.default_rng(spec['seed']), opt, opt['sub'] + (1 if spec['hero'] and opt['sub'] < 3 else 0))
        objects.append(make_object('tree.bark', f'Tree {gname} trunk', ta))
        objects.append(make_object('plant.foliage', f'Tree {gname} crown', ca))
        mossy_spots.append((spec, x, y))
    for gname, members in clusters:
        ta, ca = Acc(), Acc()
        for spec, x, y in members:
            build_tree(spec, x, y, ta, ca, np.random.default_rng(spec['seed']), opt, opt['sub'])
            mossy_spots.append((spec, x, y))
        objects.append(make_object('tree.bark', f'Tree cluster {gname} trunks', ta))
        objects.append(make_object('plant.foliage', f'Tree cluster {gname} crowns', ca))

    # moss cushions: low on the north side of each trunk (a big soft shape each)
    for spec, x, y in mossy_spots:
        r = spec['r_br'] * (1.0 + spec['flare'])
        rr = np.random.default_rng(spec['seed'] + 5)
        n = rr.uniform(0.0, 0.5) - 0.25
        px, py = x + (r * 0.8) * math.sin(n), y + (r * 0.8) * math.cos(n)
        cushion(rr, px, py, r * rr.uniform(0.75, 1.0) * opt['moss_scale'], r * rr.uniform(0.5, 0.7) * opt['moss_scale'], rr.uniform(0.28, 0.42) * opt['moss_scale'], moss)

    # ---------------------------------------------------------- 4. undergrowth, stumps, logs, boulders
    small_rng = np.random.default_rng(opt['seed'] + 101)
    lows = [(p[0], p[1], p[2] + 0.3) for p in placed]
    # spots at the rim: a ring round the clearing, outside it, plus beside the road outside the clearing
    def rim_point(rr, inside_depth=-1.0, outside=12.0):
        edge = int(rr.integers(0, 4))
        t = rr.random()
        off = rr.uniform(inside_depth, outside)
        if edge == 0:
            return x0 + t * (x1 - x0), y0 - off
        if edge == 1:
            return x0 + t * (x1 - x0), y1 + off
        if edge == 2:
            return x0 - off, y0 + t * (y1 - y0)
        return x1 + off, y0 + t * (y1 - y0)

    stump_objs = []
    spots = []
    guard = 0
    while len(spots) < 6 and guard < 3000:
        guard += 1
        px, py = rim_point(small_rng, -3.0, 9.0)
        if low_ok(world, px, py, others=lows + [(s[0], s[1], 1.5) for s in spots], gap=4.0, margin_edge=8.0, sight=6.2, wall=WALL_CLEAR - 2.0):
            spots.append((px, py))
    for k, (px, py) in enumerate(spots):
        dia = small_rng.uniform(0.5, 0.9)
        height = small_rng.uniform(0.3, 0.6)
        v, f = stump_mesh(small_rng, px, py, dia, height)
        acc = Acc()
        acc.add(v, f)
        stump_objs.append(make_object('tree.bark', f'Stump {k + 1}', acc))
        cushion(small_rng, px, py + dia * 0.45, dia * 0.5 * opt['moss_scale'], dia * 0.3 * opt['moss_scale'], 0.22 * opt['moss_scale'], moss)
        lows.append((px, py, dia))
    snag_objs = []
    guard = 0
    while len(snag_objs) < opt['snags'] and guard < 3000:
        guard += 1
        px, py = rim_point(small_rng, -2.0, 10.0)
        spec = tree_spec(small_rng, 'B', False, opt)
        spec['T'] = float(small_rng.uniform(4.6, 7.6))            # a broken tree: the trunk stops at 5 to 7 m, no crown
        spec['H'] = spec['T']
        spec['r_top'] = spec['r_br'] * 0.72
        spec['lean'] = (0.02, 0.01)
        spec['sway'] = 0.1
        spec['shadow_discs'] = []
        spec['crown_r'] = 0.0
        if not tree_ok(world, spec, px, py, placed + [(l[0], l[1], l[2]) for l in lows], sight=True):
            continue
        tv, tf = build_trunk(spec, px, py, np.random.default_rng(spec['seed']), ['hollow'], ragged=True)
        tv[:, 2] += seat_shift(tv)
        acc = Acc()
        acc.add(tv, tf, open_foot=True)
        snag_objs.append(make_object('tree.bark', f'Tree snag {len(snag_objs) + 1} trunk', acc))
        r = spec['r_br'] * (1.0 + spec['flare'])
        cushion(small_rng, px, py + r * 0.8, r * 0.8 * opt['moss_scale'], r * 0.55 * opt['moss_scale'], 0.3 * opt['moss_scale'], moss)
        lows.append((px, py, spec['r_br'] + 0.3))
    log_objs = []
    lspots = []
    guard = 0
    while len(lspots) < 4 and guard < 4000:
        guard += 1
        px, py = rim_point(small_rng, -3.0, 12.0)
        length = small_rng.uniform(2.6, 4.6)
        hd = small_rng.uniform(0, math.pi)
        ends = [(px + math.cos(hd) * length / 2 * s, py + math.sin(hd) * length / 2 * s) for s in (-1, 0, 1)]
        if all(low_ok(world, ex, ey, others=lows + [(s[0], s[1], 2.0) for s in lspots], gap=3.0, margin_edge=7.0, sight=6.2, wall=WALL_CLEAR - 2.0) for ex, ey in ends):
            lspots.append((px, py, length, hd))
    for k, (px, py, length, hd) in enumerate(lspots):
        dia = small_rng.uniform(0.3, 0.6)
        v, f = log_mesh(small_rng, px, py, length, dia, hd)
        acc = Acc()
        acc.add(v, f)
        log_objs.append(make_object('tree.bark', f'Log fallen {k + 1}', acc))
        cx, cy = px + 0.3 * math.cos(hd), py + 0.3 * math.sin(hd)
        cushion(small_rng, cx, cy + dia * 0.4, 0.6 * opt['moss_scale'], dia * 0.45 * opt['moss_scale'], dia * 0.45 * opt['moss_scale'], moss)
        lows.append((px, py, length / 2))
    rock_objs = []
    rspots = []
    guard = 0
    while len(rspots) < 8 and guard < 5000:
        guard += 1
        if len(rspots) < 4:
            px, py = rim_point(small_rng, -3.0, 12.0)
            margin = 6.0
        else:   # beside the road outside the clearing
            j = int(small_rng.integers(0, len(line)))
            side = 1 if small_rng.random() < 0.5 else -1
            p = side_point(line, j, side, ROAD_HALF['high'] + small_rng.uniform(3.6, 6.5))
            px, py = float(p[0]), float(p[1])
            margin = 3.6
        if world.in_clearing(px, py) and len(rspots) >= 4:
            continue
        if low_ok(world, px, py, others=lows + [(s[0], s[1], 1.5) for s in rspots], gap=3.0, margin_edge=margin, sight=6.2, wall=WALL_CLEAR - 2.0):
            rspots.append((px, py))
    for k, (px, py) in enumerate(rspots):
        s = small_rng.uniform(0.7, 1.15)                    # the boulder's width in metres; its height is 0.4 to 0.9 m
        h = small_rng.uniform(0.4, 0.9)
        v, f = rock_mesh(small_rng, px, py, s * 0.5, s * 0.5 * small_rng.uniform(0.7, 1.0), h / 1.25)
        acc = Acc()
        acc.add(v, f)
        rock_objs.append(make_object('stone.rock', f'Rock boulder {k + 1}', acc))
        cushion(small_rng, px, py + s * 0.3, s * 0.3 * opt['moss_scale'], s * 0.2 * opt['moss_scale'], 0.14 * opt['moss_scale'], moss)
        lows.append((px, py, s))
    # bushes and ferns at the rim and beside the roads, outside the clearing, joined by region into a few objects
    anchors = [(t[1], t[2]) for t in trees] + [(m[1], m[2]) for _g, members in groups for m in members]
    bush_groups = {}
    count = 0
    guard = 0
    while count < 38 and guard < 6000:
        guard += 1
        ax_, ay_ = anchors[int(small_rng.integers(0, len(anchors)))]
        ang = small_rng.uniform(0, 2 * math.pi)
        rad = small_rng.uniform(2.0, 5.0)
        px, py = ax_ + rad * math.cos(ang), ay_ + rad * math.sin(ang)
        if world.in_clearing(px, py, shrink=-1.0):
            continue
        if not low_ok(world, px, py, others=lows, gap=1.6, margin_edge=3.4, sight=2.5, wall=WALL_CLEAR):
            continue
        key = (int(px // 75), int(py // 75))
        grp = bush_groups.setdefault(key, {'bush': Acc(), 'fern': Acc()})
        if small_rng.random() < 0.55:
            tone = ['dark', 'mid', 'olive'][int(small_rng.integers(0, 3))]
            for v, f in bush_pieces(small_rng, px, py, small_rng.uniform(0.55, 1.0)):
                grp['bush'].add(v, f, tone=tone, open_foot=True)
        else:
            v, f = fern_mesh(small_rng, px, py, small_rng.uniform(0.9, 1.3))
            grp['fern'].add(v, f, closed=False, tone='olive')
        lows.append((px, py, 0.8))
        count += 1
    plant_objs = []
    for key, grp in sorted(bush_groups.items()):
        if grp['bush'].pieces:
            plant_objs.append(make_object('plant.foliage', f'Bush group {key[0]}_{key[1]}', grp['bush']))
        if grp['fern'].pieces:
            plant_objs.append(make_object('plant.foliage', f'Fern group {key[0]}_{key[1]}', grp['fern']))
    moss_obj = make_object('plant.foliage', 'Forest moss cushions', moss)

    bpy.context.view_layer.update()
    tris = sum(len(o.data.polygons) for o in objects + snag_objs + stump_objs + log_objs + rock_objs + plant_objs + [moss_obj])
    n_trunks = sum(1 for spec, *_ in trees) + sum(len(m) for _g, m in clusters)
    info = {'objects': len(objects) + len(snag_objs) + len(stump_objs) + len(log_objs) + len(rock_objs) + len(plant_objs) + 1, 'trees': n_trunks, 'heroes': len(trees), 'clusters': len(clusters), 'triangles': tris,
            'snags': len(snag_objs), 'stumps': len(stump_objs), 'logs': len(log_objs), 'rocks': len(rock_objs), 'bush_and_fern_pieces': count, 'rejects': dict(_REJECTS)}
    print('forest stage:', info)
    apply.info = info
    return info
