# POND BUILDER (22 October character round): shared helpers for stage_pond.py (water, plants, maple, pine).
# Plain words: small tools used by every step: making a mesh object from numpy arrays, UV maps, vertex colours, materials with a Normal Map node,
# finding the ground height, the bridge corridor, and removing what an earlier run made (so the stage can run twice with the same result).
# Everything here works in Blender 5.2.2 headless. numpy only (no PIL, no scipy).
import bpy
import math
import os
import json
import numpy as np
from mathutils import Vector

OWNER = 'pond'
COLL = 'G6 pond'
HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = os.path.join(HERE, 'maps')
SCANS = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/maps'
WATER_Z = -0.12
BRIDGE_NODES = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]
POND_BBOX = (-5.65, -1.25, 0.20, 3.10)         # x0, y0, x1, y1 of the water mesh (5.85 x 4.35 m); RippleUV runs over this box

# facts of the starting scene that must survive a second run (the curves are turned into meshes on the first run)
MAPLE_TRUNK_PTS = [(-6.7, 1.3, -0.05, 0.2), (-6.65, 1.2, 0.95, 0.165), (-6.15, 1.05, 1.85, 0.13), (-5.55, 1.2, 2.6, 0.095), (-5.0, 1.45, 3.25, 0.06)]
PINE_TRUNK_PTS = [(7.6, 4.6, -0.1, 0.24), (7.45, 4.65, 1.0, 0.198), (7.95, 4.55, 2.0, 0.155), (7.55, 4.7, 3.0, 0.112), (7.85, 4.6, 3.9, 0.07)]
PINE_LIMB_PTS = [
    [(7.7, 4.57, 1.15, 0.05), (8.15, 4.43, 1.38, 0.038), (8.6, 4.3, 1.5, 0.025)],
    [(7.5, 4.63, 1.95, 0.05), (7.05, 4.76, 2.18, 0.038), (6.6, 4.9, 2.3, 0.025)],
    [(7.71, 4.63, 2.65, 0.05), (8.2, 4.76, 2.88, 0.038), (8.7, 4.9, 3.0, 0.025)],
    [(7.53, 4.58, 3.15, 0.05), (7.22, 4.49, 3.38, 0.038), (6.9, 4.4, 3.5, 0.025)],
    [(7.63, 4.6, 3.75, 0.05), (7.76, 4.6, 3.98, 0.038), (7.9, 4.6, 4.1, 0.025)],
    [(8.6, 4.3, 1.57, 0.028), (8.72, 4.41, 1.76, 0.021), (8.77, 4.52, 1.88, 0.014)],
    [(8.7, 4.9, 3.07, 0.028), (8.82, 5.0, 3.26, 0.021), (8.86, 5.1, 3.38, 0.014)],
    [(7.9, 4.6, 4.17, 0.028), (7.88, 4.73, 4.36, 0.021), (7.78, 4.86, 4.48, 0.014)],
]
PINE_LIMB_NAMES = ['Pine limb', 'Pine limb.001', 'Pine limb.002', 'Pine limb.003', 'Pine limb.004', 'Pine limb.005', 'Pine limb.006', 'Pine limb.007']
MAPLE_BRANCH_NAMES = ['Maple branch'] + ['Maple branch.%03d' % i for i in range(1, 17)]
# the 16 lily pad centres of the starting scene (x, y, radius) and the two flowers (kept from the starting scene's props)
POND_STONES = ['Pond edge stone %d' % i for i in range(15)] + ['Rock %d' % i for i in range(5)]
LILY_CENTRES = [(-3.8583, 1.5196, 0.1663), (-3.1963, 2.6823, 0.1529), (-2.1099, 2.8402, 0.1571), (-0.4998, 2.0706, 0.1929), (-1.8696, -0.6845, 0.1875),
                (-2.5439, 2.0691, 0.1290), (-4.3603, 2.3440, 0.1885), (-3.2227, 1.8964, 0.1417), (-0.4597, 0.7555, 0.1303), (-4.0211, -0.8516, 0.1363),
                (-1.3795, 2.6835, 0.1697), (-3.2367, -0.8843, 0.1832), (-4.7020, -0.6011, 0.1325), (-1.3096, 1.8693, 0.1565), (-2.4413, -0.1641, 0.1296),
                (-5.1474, 2.1990, 0.1761)]


class Report:
    def __init__(self):
        self.created, self.changed, self.deleted, self.notes, self.numbers = [], [], [], [], {}

    def say(self, text):
        self.notes.append(text)
        print('[pond] ' + text, flush=True)


REP = Report()


def say(text):
    REP.say(text)


# ------------------------------------------------------------------------------------------------ collections, tags, removal
def collection():
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(c)
    elif c.name not in [x.name for x in bpy.context.scene.collection.children_recursive] and c not in list(bpy.context.scene.collection.children):
        try:
            bpy.context.scene.collection.children.link(c)
        except Exception:
            pass
    return c


def tag(ob, role, new=False):
    ob['garden_owner'] = OWNER
    ob['garden_role'] = role
    if new:
        ob['g6p_new'] = 1


def remove_object(ob):
    data = ob.data
    kind = ob.type
    bpy.data.objects.remove(ob, do_unlink=True)
    if data is not None and data.users == 0:
        try:
            if kind == 'MESH':
                bpy.data.meshes.remove(data)
            elif kind == 'CURVE':
                bpy.data.curves.remove(data)
        except Exception:
            pass


def remove_previous():
    """Remove everything an earlier run made (objects tagged g6p_new) and report how many."""
    gone = []
    for ob in list(bpy.data.objects):
        if ob.get('g6p_new'):
            gone.append(ob.name)
            remove_object(ob)
    return gone


# ------------------------------------------------------------------------------------------------ numpy -> mesh
def make_mesh(name, V, F, colors=None, uvs=None, smooth=False, materials=None, attrs=None, flat_colors=False):
    """V (n,3) float, F (m,3) int triangles. colors: (m*3,4) per corner or (n,4) per vertex. uvs: {layer name: (m*3,2) per corner}.
    attrs: {name: (n,) float point attribute}."""
    V = np.asarray(V, dtype=np.float32)
    F = np.asarray(F, dtype=np.int32).reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set('co', V.ravel())
    nl = len(F) * 3
    me.loops.add(nl)
    me.loops.foreach_set('vertex_index', F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set('loop_start', np.arange(0, nl, 3, dtype=np.int32))
    me.polygons.foreach_set('loop_total', np.full(len(F), 3, dtype=np.int32))
    me.update(calc_edges=True)
    if smooth:
        me.polygons.foreach_set('use_smooth', np.ones(len(F), dtype=bool))
    else:
        me.polygons.foreach_set('use_smooth', np.zeros(len(F), dtype=bool))
    if uvs:
        for lname, arr in uvs.items():
            lay = me.uv_layers.new(name=lname)
            lay.data.foreach_set('uv', np.asarray(arr, dtype=np.float32).reshape(-1, 2).ravel())
    if colors is not None:
        C = np.asarray(colors, dtype=np.float32)
        if len(C) == len(V):
            ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
            ca.data.foreach_set('color', C.reshape(-1, 4).ravel())
        else:
            ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
            ca.data.foreach_set('color', C.reshape(-1, 4).ravel())
    if attrs:
        for an, arr in attrs.items():
            a = me.attributes.new(an, 'FLOAT', 'POINT')
            a.data.foreach_set('value', np.asarray(arr, dtype=np.float32))
    for m in (materials or []):
        me.materials.append(m)
    me.update()
    return me


def face_colors_to_corners(fcol):
    """(m,4) per face -> (m*3,4) per corner."""
    return np.repeat(np.asarray(fcol, dtype=np.float32), 3, axis=0)


def new_object(name, me, role, cols=None, new=True):
    ob = bpy.data.objects.new(name, me)
    for c in (cols or [collection()]):
        c.objects.link(ob)
    tag(ob, role, new=new)
    return ob


def replace_mesh(ob, me):
    old = ob.data
    ob.data = me
    if old is not None and old.users == 0:
        try:
            bpy.data.meshes.remove(old)
        except Exception:
            pass


def merge(parts):
    """parts: list of (V, F, C) with optional C (n,4) per vertex or None. Returns V, F and per-vertex colour (or None)."""
    Vs, Fs, Cs, off = [], [], [], 0
    any_c = any(p[2] is not None for p in parts)
    for V, F, C in parts:
        Vs.append(np.asarray(V, dtype=np.float32))
        Fs.append(np.asarray(F, dtype=np.int32) + off)
        if any_c:
            Cs.append(np.asarray(C if C is not None else np.tile([0.5, 0.5, 0.5, 1.0], (len(V), 1)), dtype=np.float32))
        off += len(V)
    return np.concatenate(Vs), np.concatenate(Fs), (np.concatenate(Cs) if any_c else None)


def vcols_to_corners(C, F):
    """per vertex colours (n,4) -> per corner (m*3,4)."""
    return np.asarray(C, dtype=np.float32)[np.asarray(F).reshape(-1)]


# ------------------------------------------------------------------------------------------------ UV maps (per corner arrays)
def uv_planar(V, F, tile_m=3.0, origin=(0.0, 0.0)):
    P = np.asarray(V)[np.asarray(F).reshape(-1)]
    return np.stack([(P[:, 0] - origin[0]) / tile_m, (P[:, 1] - origin[1]) / tile_m], axis=1)


def uv_bbox(V, F, bbox=POND_BBOX):
    P = np.asarray(V)[np.asarray(F).reshape(-1)]
    x0, y0, x1, y1 = bbox
    return np.stack([(P[:, 0] - x0) / (x1 - x0), (P[:, 1] - y0) / (y1 - y0)], axis=1)


def uv_box(V, F, tile_m=1.0):
    """Box projection per triangle: the two axes that are not the face normal's strongest axis, divided by tile_m (1 UV unit = tile_m metres).
    Every triangle is turned so its UV winding is positive (no mirrored islands): faces that look the other way get u negated."""
    V = np.asarray(V, dtype=np.float32)
    F = np.asarray(F).reshape(-1, 3)
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(B - A, C - A)
    ax = np.argmax(np.abs(n), axis=1)
    P = V[F.reshape(-1)].reshape(-1, 3, 3)
    uv = np.zeros((len(F), 3, 2), dtype=np.float32)
    for k, (a, b) in enumerate(((1, 2), (0, 2), (0, 1))):          # x-dominant -> (y, z); y-dominant -> (x, z); z-dominant -> (x, y)
        m = ax == k
        if m.any():
            uv[m, :, 0] = P[m, :, a] / tile_m
            uv[m, :, 1] = P[m, :, b] / tile_m
    area = (uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1]) - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])
    neg = area < 0
    uv[neg, :, 0] *= -1.0
    return uv.reshape(-1, 2)


def add_uv_by_position(me, name, fn):
    """Add (or overwrite) UV layer `name` on an existing mesh with any polygons: fn(P (n,3) corner positions) -> (n,2)."""
    nloops = len(me.loops)
    vi = np.empty(nloops, dtype=np.int32)
    me.loops.foreach_get('vertex_index', vi)
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    P = co.reshape(-1, 3)[vi]
    lay = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    lay.data.foreach_set('uv', np.asarray(fn(P), dtype=np.float32).reshape(-1, 2).ravel())
    return lay


# ------------------------------------------------------------------------------------------------ ground height (ray cast on the ground mesh only)
class Ground:
    def __init__(self):
        from mathutils.bvhtree import BVHTree
        g = bpy.data.objects['Astra / Courtyard receiving ground']
        self.bvh = BVHTree.FromObject(g, bpy.context.evaluated_depsgraph_get())

    def z(self, x, y, default=0.0):
        r = self.bvh.ray_cast(Vector((float(x), float(y), 6.0)), Vector((0.0, 0.0, -1.0)))
        return r[0].z if r[0] is not None else default

    def zs(self, X, Y):
        return np.array([self.z(x, y) for x, y in zip(X, Y)], dtype=np.float32)


def dist_to_corridor(x, y):
    """Distance in metres from (x, y) to the bridge centre line (4 nodes, 3 arms)."""
    best = 1e9
    p = np.array([x, y], dtype=np.float64)
    for i in range(3):
        a = np.array(BRIDGE_NODES[i]); b = np.array(BRIDGE_NODES[i + 1])
        ab = b - a
        t = float(np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0.0, 1.0))
        best = min(best, float(np.hypot(*(p - (a + t * ab)))))
    return best


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def pond_radius(x, y):
    """About 1.0 on the pond's edge, below 1 in the water (the outline the first build used)."""
    cx, cy, A, B, rot = -3.0, 1.0, 3.3, 2.5, math.radians(10)
    dx, dy = x - cx, y - cy
    u = dx * math.cos(-rot) - dy * math.sin(-rot)
    v = dx * math.sin(-rot) + dy * math.cos(-rot)
    th = math.atan2(v / B, u / A)
    wob = 1 + 0.10 * math.sin(3 * th + 0.8) + 0.06 * math.sin(5 * th + 2.1) + 0.04 * math.sin(2 * th)
    return math.hypot(u / A, v / B) / wob


# ------------------------------------------------------------------------------------------------ materials
def fresh_material(name):
    """Get or create material `name` with an empty node tree (idempotent: always rebuilt from scratch)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt.nodes, nt.links


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def hex_lin(h, alpha=True):
    h = h.lstrip('#')
    rgb = np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
    lin = srgb_to_linear(rgb)
    return (float(lin[0]), float(lin[1]), float(lin[2]), 1.0) if alpha else tuple(float(v) for v in lin)


def principled(nodes, links, color=None, rough=0.7, out_loc=(600, 0), **inputs):
    b = nodes.new('ShaderNodeBsdfPrincipled')
    out = nodes.new('ShaderNodeOutputMaterial')
    b.inputs['Roughness'].default_value = rough
    if color is not None:
        b.inputs['Base Color'].default_value = color
    for k, v in inputs.items():
        k = k.replace('_', ' ')
        if k in b.inputs:
            b.inputs[k].default_value = v
    links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return b, out


def load_image(path, non_color=True):
    """Load an image file from disk as Non-Color. Colour space is set right after loading (before any pixel use)."""
    img = bpy.data.images.get(os.path.basename(path))
    if img is not None and bpy.path.abspath(img.filepath) != path:
        img = None
    if img is None:
        img = bpy.data.images.load(path, check_existing=False)
    if non_color and img.colorspace_settings.name != 'Non-Color':
        img.colorspace_settings.name = 'Non-Color'
    return img


def normal_map_chain(nodes, links, image_path, uv_name, strength, scale=(1.0, 1.0, 1.0), label='NM', loc=(-900, 0), interpolation='Cubic'):
    """UV Map -> Mapping -> Image Texture (Non-Color, repeat) -> Normal Map (Tangent, uv_map set). Returns the Normal Map node."""
    img = load_image(image_path)
    uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = uv_name; uv.name = uv.label = label + ' UV'
    mp = nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale; mp.name = mp.label = label + ' Mapping'
    tx = nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = interpolation; tx.extension = 'REPEAT'; tx.name = tx.label = label + ' Image'
    nm = nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'; nm.uv_map = uv_name; nm.inputs['Strength'].default_value = strength; nm.name = nm.label = label + ' Normal Map'
    links.new(uv.outputs['UV'], mp.inputs['Vector'])
    links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    links.new(tx.outputs['Color'], nm.inputs['Color'])
    for i, n in enumerate((uv, mp, tx, nm)):
        n.location = (loc[0] + i * 220, loc[1])
    return nm


def ramp_node(nodes, stops, interpolation='LINEAR'):
    r = nodes.new('ShaderNodeValToRGB')
    cr = r.color_ramp
    cr.interpolation = interpolation
    while len(cr.elements) > 2:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1]
    cr.elements[1].position = stops[1][0]; cr.elements[1].color = stops[1][1]
    for pos, col in stops[2:]:
        e = cr.elements.new(pos); e.color = col
    return r


# ------------------------------------------------------------------------------------------------ small geometry helpers
def rot_matrix(axis, ang):
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def yaw_matrix(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def icosphere(subdiv=2):
    """Unit icosphere vertices and triangles (subdiv 2 = 162 verts, 320 tris; subdiv 1 = 42 verts, 80 tris)."""
    t = (1.0 + 5 ** 0.5) / 2.0
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    V = [np.array(v, dtype=np.float64) / np.linalg.norm(v) for v in V]
    for _ in range(subdiv):
        cache = {}
        nF = []

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = (V[a] + V[b]) / 2
                V.append(m / np.linalg.norm(m))
                cache[k] = len(V) - 1
            return cache[k]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nF += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = nF
    return np.array(V, dtype=np.float32), np.array(F, dtype=np.int32)


def tube(path, radii, sides=8, cap_start=False, cap_end=True, twist=0.0, up_hint=(0, 0, 1.0)):
    """Sweep a circle along a 3D polyline. Returns V, F, and UV info: for every vertex (u in 0..1 around, s = arc length in metres).
    path (n,3), radii (n,). Parallel-transport frames, optional total twist (radians) over the length."""
    path = np.asarray(path, dtype=np.float64)
    radii = np.asarray(radii, dtype=np.float64)
    n = len(path)
    T = np.zeros_like(path)
    T[1:-1] = path[2:] - path[:-2]
    T[0] = path[1] - path[0]
    T[-1] = path[-1] - path[-2]
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    up = np.asarray(up_hint, dtype=np.float64)
    N0 = np.cross(T[0], np.cross(up, T[0]))
    if np.linalg.norm(N0) < 1e-6:
        N0 = np.cross(T[0], [1.0, 0, 0])
    N0 /= np.linalg.norm(N0)
    frames = [N0]
    for i in range(1, n):
        v = np.cross(T[i - 1], T[i])
        s = np.linalg.norm(v)
        if s < 1e-9:
            frames.append(frames[-1])
        else:
            ang = math.asin(min(1.0, s))
            frames.append(rot_matrix(v, ang) @ frames[-1])
    seg = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    V, S, U = [], [], []
    for i in range(n):
        N = frames[i]
        B = np.cross(T[i], N)
        tw = twist * (seg[i] / max(seg[-1], 1e-9))
        for k in range(sides + 1):                                    # sides+1: duplicate seam column for UVs
            a = tw + k * math.tau / sides
            V.append(path[i] + radii[i] * (math.cos(a) * N + math.sin(a) * B))
            S.append(seg[i]); U.append(k / sides)
    V = np.array(V, dtype=np.float32); S = np.array(S, dtype=np.float32); U = np.array(U, dtype=np.float32)
    F = []
    w = sides + 1
    for i in range(n - 1):
        for k in range(sides):
            a, b, c, d = i * w + k, i * w + k + 1, (i + 1) * w + k + 1, (i + 1) * w + k
            F += [(a, b, c), (a, c, d)]
    F = np.array(F, dtype=np.int32)
    extra_uv = None
    if cap_end:
        ce = len(V)
        V = np.vstack([V, path[-1][None, :].astype(np.float32)]); S = np.r_[S, seg[-1]]; U = np.r_[U, 0.5]
        last = (n - 1) * w
        F = np.vstack([F, [(ce, last + k + 1, last + k) for k in range(sides)]])
    if cap_start:
        cs = len(V)
        V = np.vstack([V, path[0][None, :].astype(np.float32)]); S = np.r_[S, 0.0]; U = np.r_[U, 0.5]
        F = np.vstack([F, [(cs, k, k + 1) for k in range(sides)]])
    return V, F.astype(np.int32), U, S


def catmull(points, per_seg=6, closed=False):
    """Catmull-Rom through control points (n,3) (or (n,4) with radius): returns (m, same dim) samples."""
    P = np.asarray(points, dtype=np.float64)
    if len(P) < 3:
        t = np.linspace(0, 1, per_seg * (len(P) - 1) + 1)[:, None]
        return P[0] * (1 - t) + P[-1] * t
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for t in np.linspace(0, 1, per_seg, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1])
    return np.array(out)


def lightgroup_like(ob, other_name):
    o = bpy.data.objects.get(other_name)
    if o is not None and hasattr(ob, 'lightgroup'):
        ob.lightgroup = o.lightgroup


def snapshot_names():
    return sorted(o.name for o in bpy.data.objects), sorted(m.name for m in bpy.data.materials)


def make_camera(name, loc, target, lens, sensor=36.0, clip_end=200.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_end = clip_end
    ob = bpy.data.objects.new(name, cd)
    collection().objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    tag(ob, 'camera', new=True)
    return ob


G6_CAMERAS = [
    ('G6 pond cam 1', (-1.0, -1.7, 0.34), (-3.4, 0.0, -0.12), 35),          # water low from the south-east bank (the east bank view is blocked by the bridge)
    ('G6 pond cam 2', (-2.8, 1.0, 5.5), (-2.8, 1.0, 0.0), 28),             # top view of the pond (straight down)
    ('G6 pond cam 3', (-3.0, 0.55, 0.55), (-3.75, 1.6, -0.1), 85),         # lily cluster close
    ('G6 pond cam 4', (-1.7, -1.15, 0.55), (-2.35, -0.3, -0.12), 50),      # ripple close
    ('G6 pond cam 5', (-3.0, -2.5, 0.8), (-5.5, 1.5, 3.0), 24),            # maple crown from the ground
    ('G6 pond cam 6', (4.5, 1.0, 1.4), (7.7, 4.6, 3.0), 35),               # pine crown
    ('G6 pond cam 7', (-3.7, -2.0, 0.55), (-3.4, -0.7, -0.2), 50),         # the south shelf: pebbles, flat stone, iris, rim
]
