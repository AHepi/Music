"""Shared helpers for the forest village build: noise, mesh building, node building."""
import bpy
import bmesh
import numpy as np
import math
from mathutils import Vector, Matrix, Euler, Quaternion

WORK = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control-opus"

# ----------------------------------------------------------------------------
# Noise (numpy, vectorised)
# ----------------------------------------------------------------------------
class Perlin2:
    def __init__(self, seed=0):
        rng = np.random.RandomState(seed)
        perm = rng.permutation(256)
        self.p = np.concatenate([perm, perm]).astype(np.int64)
        ang = rng.uniform(0, 2 * np.pi, 256)
        self.g = np.stack([np.cos(ang), np.sin(ang)], 1)

    def __call__(self, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        xi0 = np.floor(x).astype(np.int64)
        yi0 = np.floor(y).astype(np.int64)
        xf = x - xi0
        yf = y - yi0
        xi = xi0 & 255
        yi = yi0 & 255
        p = self.p
        g = self.g

        def grad(ix, iy, dx, dy):
            h = p[p[ix] + iy] & 255
            return g[h, 0] * dx + g[h, 1] * dy

        n00 = grad(xi, yi, xf, yf)
        n10 = grad(xi + 1, yi, xf - 1, yf)
        n01 = grad(xi, yi + 1, xf, yf - 1)
        n11 = grad(xi + 1, yi + 1, xf - 1, yf - 1)
        u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
        v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
        a = n00 + u * (n10 - n00)
        b = n01 + u * (n11 - n01)
        return (a + v * (b - a)) * 1.4142


_NOISES = {}


def perlin(x, y, seed=0):
    n = _NOISES.get(seed)
    if n is None:
        n = Perlin2(seed)
        _NOISES[seed] = n
    return n(x, y)


def fbm(x, y, octaves=4, seed=0, lac=2.0, gain=0.5):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    total = np.zeros(np.broadcast(x, y).shape)
    amp = 1.0
    freq = 1.0
    norm = 0.0
    for o in range(octaves):
        total = total + amp * perlin(x * freq + 17.13 * o, y * freq - 9.71 * o, seed + o * 31)
        norm += amp
        amp *= gain
        freq *= lac
    return total / norm


def noise1(s, seed=0, octaves=2):
    """1D noise along a parameter."""
    return fbm(s, 0.37 + seed * 3.17, octaves=octaves, seed=seed)


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------
# Collections and objects
# ----------------------------------------------------------------------------
def get_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def clear_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        return
    for ob in list(col.all_objects):
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is not None and getattr(data, "users", 1) == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
    for child in list(col.children):
        clear_collection(child.name)
        bpy.data.collections.remove(child)


def link(ob, col):
    col.objects.link(ob)
    return ob


def new_object(name, data, col, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    col.objects.link(ob)
    return ob


def mesh_from_arrays(name, verts, faces, loop_uv=None, face_attrs=None, point_attrs=None,
                     mat_index=None, smooth=False, materials=None, corner_attrs=None):
    """Create a mesh from numpy arrays.

    verts: (N,3) float array.
    faces: either a (M,k) int array or a list of index lists.
    loop_uv: (L,2) array matching the flattened loop order.
    face_attrs / point_attrs: dict name -> array (float) or (n,4) colour.
    """
    verts = np.asarray(verts, dtype=np.float32).reshape(-1, 3)
    if isinstance(faces, np.ndarray):
        faces = faces.astype(np.int32)
        nf, k = faces.shape
        loops = faces.ravel()
        totals = np.full(nf, k, dtype=np.int32)
    else:
        totals = np.array([len(f) for f in faces], dtype=np.int32)
        loops = np.fromiter((i for f in faces for i in f), dtype=np.int32, count=int(totals.sum()))
        nf = len(faces)
    starts = np.zeros(nf, dtype=np.int32)
    if nf:
        starts[1:] = np.cumsum(totals)[:-1]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(len(loops))
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    if loop_uv is not None:
        uv = me.uv_layers.new(name="UVMap")
        uv.data.foreach_set("uv", np.asarray(loop_uv, dtype=np.float32).ravel())
    if face_attrs:
        for an, arr in face_attrs.items():
            arr = np.asarray(arr, dtype=np.float32)
            if arr.ndim == 2:
                a = me.attributes.new(an, 'FLOAT_COLOR', 'FACE')
                a.data.foreach_set("color", arr.ravel())
            else:
                a = me.attributes.new(an, 'FLOAT', 'FACE')
                a.data.foreach_set("value", arr)
    if point_attrs:
        for an, arr in point_attrs.items():
            arr = np.asarray(arr, dtype=np.float32)
            if arr.ndim == 2:
                a = me.attributes.new(an, 'FLOAT_COLOR', 'POINT')
                a.data.foreach_set("color", arr.ravel())
            else:
                a = me.attributes.new(an, 'FLOAT', 'POINT')
                a.data.foreach_set("value", arr)
    if corner_attrs:
        for an, arr in corner_attrs.items():
            arr = np.asarray(arr, dtype=np.float32)
            if arr.ndim == 2:
                a = me.attributes.new(an, 'FLOAT_COLOR', 'CORNER')
                a.data.foreach_set("color", arr.ravel())
            else:
                a = me.attributes.new(an, 'FLOAT', 'CORNER')
                a.data.foreach_set("value", arr)
    if materials:
        for m in materials:
            me.materials.append(m)
    if mat_index is not None:
        me.polygons.foreach_set("material_index", np.asarray(mat_index, dtype=np.int32))
    if smooth:
        me.shade_smooth()
    me.validate(clean_customdata=False)
    return me


# ----------------------------------------------------------------------------
# MeshBuilder: accumulate many parts into one mesh
# ----------------------------------------------------------------------------
class MeshBuilder:
    def __init__(self):
        self.verts = []      # list of (n,3) arrays
        self.faces = []      # list of index lists (global)
        self.uvs = []        # per-loop uv lists (aligned to faces)
        self.mat = []        # per face material index
        self.frnd = []       # per face random value (one per part)
        self.fattr = {}      # extra per-face attrs name -> list
        self.nv = 0

    def add(self, verts, faces, uvs=None, mat=0, rnd=None, attrs=None):
        """verts: (n,3) array; faces: list of local index lists; uvs: list of per-face lists of (u,v)."""
        verts = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        base = self.nv
        self.verts.append(verts)
        if rnd is None:
            rnd = np.random.random()
        for fi, f in enumerate(faces):
            self.faces.append([base + i for i in f])
            if uvs is not None:
                self.uvs.append(uvs[fi])
            else:
                self.uvs.append([(0.0, 0.0)] * len(f))
            self.mat.append(mat)
            self.frnd.append(rnd)
            if attrs:
                for k, v in attrs.items():
                    if k not in self.fattr:
                        self.fattr[k] = [0.0] * (len(self.faces) - 1)
            for k in self.fattr:
                self.fattr[k].append(attrs.get(k, 0.0) if attrs else 0.0)
        self.nv += len(verts)
        return base

    def empty(self):
        return self.nv == 0

    def build(self, name, materials=None, smooth=False):
        verts = np.concatenate(self.verts, 0) if self.verts else np.zeros((0, 3))
        loop_uv = np.array([uv for f in self.uvs for uv in f], dtype=np.float32)
        fa = {"rnd": np.array(self.frnd)}
        for k, v in self.fattr.items():
            fa[k] = np.array(v)
        me = mesh_from_arrays(name, verts, self.faces, loop_uv=loop_uv, face_attrs=fa,
                              mat_index=np.array(self.mat), smooth=smooth, materials=materials)
        return me


# ----------------------------------------------------------------------------
# Primitive generators (return verts, faces, uvs)
# ----------------------------------------------------------------------------
def frame_from(axis_x, axis_y=None):
    """Return a 3x3 matrix (columns = local x,y,z) given a local x axis (and optional y hint)."""
    x = Vector(axis_x).normalized()
    if axis_y is None:
        up = Vector((0, 0, 1)) if abs(x.z) < 0.95 else Vector((0, 1, 0))
        y = up.cross(x).normalized()
    else:
        y = Vector(axis_y)
        y = (y - x * x.dot(y)).normalized()
    z = x.cross(y).normalized()
    return Matrix((x, y, z)).transposed()


def box(center, size, rot=None, uv_scale=1.0):
    """Oriented box. size=(sx,sy,sz) along local axes. rot: 3x3 Matrix or Euler.
    UVs: each face gets planar UVs in metres with u along the longest local axis present on that face."""
    sx, sy, sz = [s * 0.5 for s in size]
    if rot is None:
        R = Matrix.Identity(3)
    elif isinstance(rot, Euler):
        R = rot.to_matrix()
    elif isinstance(rot, Matrix):
        R = rot.to_3x3()
    else:
        R = Euler(rot).to_matrix()
    c = Vector(center)
    lv = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
          (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    verts = np.array([tuple(c + R @ Vector(v)) for v in lv])
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    # uv: local coords
    L = np.array(lv)
    longest = int(np.argmax(size))
    uvs = []
    for f in faces:
        pts = L[f]
        # face normal axis = the axis constant over the face
        const = [i for i in range(3) if np.allclose(pts[:, i], pts[0, i])][0]
        axes = [i for i in range(3) if i != const]
        if longest in axes:
            ua = longest
            va = [a for a in axes if a != longest][0]
        else:
            ua, va = axes
        uvs.append([(p[ua] * uv_scale, p[va] * uv_scale) for p in pts])
    return verts, faces, uvs


def cylinder(p0, p1, r0, r1=None, sides=8, caps=True, uv_scale=1.0, twist=0.0):
    """Cylinder between two points. UV u = around (metres), v = along (metres)."""
    if r1 is None:
        r1 = r0
    p0 = Vector(p0)
    p1 = Vector(p1)
    axis = p1 - p0
    L = axis.length
    M = frame_from(axis)
    yv = M.col[1]
    zv = M.col[2]
    verts = []
    for ring, (p, r) in enumerate(((p0, r0), (p1, r1))):
        for i in range(sides):
            a = 2 * math.pi * i / sides + twist
            verts.append(tuple(p + (yv * math.cos(a) + zv * math.sin(a)) * r))
    faces = []
    uvs = []
    circ = 2 * math.pi * (r0 + r1) * 0.5
    for i in range(sides):
        j = (i + 1) % sides
        faces.append([i, j, sides + j, sides + i])
        u0 = circ * i / sides
        u1 = circ * (i + 1) / sides
        uvs.append([(u0 * uv_scale, 0), (u1 * uv_scale, 0), (u1 * uv_scale, L * uv_scale), (u0 * uv_scale, L * uv_scale)])
    if caps:
        faces.append(list(range(sides - 1, -1, -1)))
        uvs.append([(verts[k][0] * uv_scale, verts[k][1] * uv_scale) for k in range(sides - 1, -1, -1)])
        faces.append(list(range(sides, 2 * sides)))
        uvs.append([(verts[k][0] * uv_scale, verts[k][1] * uv_scale) for k in range(sides, 2 * sides)])
    return np.array(verts), faces, uvs


def tube(points, radii, sides=6, caps=False, uv_scale=1.0, closed_ring=True, up_hint=None, radius_noise=None):
    """Tube along a polyline with per-point radius, parallel-transport frames.
    UV: u around (metres), v along (metres)."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i - 1])
        if t.length < 1e-9:
            t = Vector((0, 0, 1))
        tangents.append(t.normalized())
    # initial normal
    t0 = tangents[0]
    hint = Vector(up_hint) if up_hint is not None else (Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0)))
    nrm = (hint - t0 * t0.dot(hint)).normalized()
    frames = []
    for i in range(n):
        t = tangents[i]
        if i > 0:
            # parallel transport
            prev_t = tangents[i - 1]
            axis = prev_t.cross(t)
            if axis.length > 1e-8:
                ang = prev_t.angle(t)
                q = Quaternion(axis.normalized(), ang)
                nrm = q @ nrm
            nrm = (nrm - t * t.dot(nrm)).normalized()
        b = t.cross(nrm).normalized()
        frames.append((nrm.copy(), b))
    verts = []
    vacc = [0.0]
    for i in range(1, n):
        vacc.append(vacc[-1] + (pts[i] - pts[i - 1]).length)
    for i in range(n):
        nr, bi = frames[i]
        r = radii[i]
        for k in range(sides):
            a = 2 * math.pi * k / sides
            rr = r
            if radius_noise is not None:
                rr = r * radius_noise(i, k)
            verts.append(tuple(pts[i] + (nr * math.cos(a) + bi * math.sin(a)) * rr))
    faces = []
    uvs = []
    for i in range(n - 1):
        circ = 2 * math.pi * (radii[i] + radii[i + 1]) * 0.5
        for k in range(sides):
            k2 = (k + 1) % sides
            a = i * sides + k
            b = i * sides + k2
            c = (i + 1) * sides + k2
            d = (i + 1) * sides + k
            faces.append([a, b, c, d])
            u0 = circ * k / sides * uv_scale
            u1 = circ * (k + 1) / sides * uv_scale
            uvs.append([(u0, vacc[i] * uv_scale), (u1, vacc[i] * uv_scale), (u1, vacc[i + 1] * uv_scale), (u0, vacc[i + 1] * uv_scale)])
    if caps:
        faces.append(list(range(sides - 1, -1, -1)))
        uvs.append([(0, 0)] * sides)
        last = (n - 1) * sides
        faces.append([last + k for k in range(sides)])
        uvs.append([(0, 0)] * sides)
    return np.array(verts), faces, uvs


def transform_verts(verts, loc=(0, 0, 0), rot=None, scale=None):
    v = np.asarray(verts, dtype=np.float64)
    if scale is not None:
        v = v * np.asarray(scale)
    if rot is not None:
        if isinstance(rot, (Euler, tuple, list)):
            R = np.array(Euler(rot).to_matrix())
        else:
            R = np.array(rot)
        v = v @ R.T
    return v + np.asarray(loc)


def subdivided_cube(n=3):
    """Unit cube [-1,1]^3 surface grid with n subdivisions per edge. Returns verts, quads (shared verts)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=n - 1, use_grid_fill=True)
    verts = np.array([v.co[:] for v in bm.verts])
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


# ----------------------------------------------------------------------------
# Shader node building helpers
# ----------------------------------------------------------------------------
class NB:
    """Tiny node-tree builder."""

    def __init__(self, tree, clear=True):
        self.t = tree
        self.nodes = tree.nodes
        self.links = tree.links
        if clear:
            for n in list(self.nodes):
                self.nodes.remove(n)
        self.x = 0

    def node(self, kind, inputs=None, **props):
        n = self.nodes.new(kind)
        n.location = (self.x, 0)
        self.x += 30
        for k, v in props.items():
            setattr(n, k, v)
        if inputs:
            for k, v in inputs.items():
                self.set(n, k, v)
        return n

    def sock_in(self, node, key):
        if isinstance(key, int):
            return node.inputs[key]
        alias = {'Fac': 'Factor', 'Factor': 'Fac'}
        cands = [s for s in node.inputs if s.name == key or s.identifier == key]
        if not cands and key in alias:
            cands = [s for s in node.inputs if s.name == alias[key] or s.identifier == alias[key]]
        for s in cands:
            if s.enabled:
                return s
        if cands:
            return cands[0]
        raise KeyError(f"{node.bl_idname} has no input {key}: {[s.name for s in node.inputs]}")

    def set(self, node, key, val):
        s = self.sock_in(node, key)
        if isinstance(val, bpy.types.NodeSocket):
            self.links.new(val, s)
        elif isinstance(val, bpy.types.Node):
            self.links.new(self.out(val), s)
        else:
            if isinstance(val, (tuple, list)):
                if s.type == 'RGBA' and len(val) == 3:
                    val = tuple(val) + (1.0,)
                s.default_value = val
            else:
                if s.type in ('RGBA',):
                    s.default_value = (val, val, val, 1.0)
                elif s.type in ('VECTOR',):
                    s.default_value = (val, val, val)
                else:
                    s.default_value = val

    def out(self, node, key=None):
        if isinstance(node, bpy.types.NodeSocket):
            return node
        if key is None:
            for s in node.outputs:
                if s.enabled:
                    return s
            return node.outputs[0]
        if isinstance(key, int):
            return node.outputs[key]
        alias = {'Fac': 'Factor', 'Factor': 'Fac'}
        cands = [s for s in node.outputs if s.name == key]
        if not cands and key in alias:
            cands = [s for s in node.outputs if s.name == alias[key]]
        for s in cands:
            if s.enabled:
                return s
        if cands:
            return cands[0]
        raise KeyError(f"{node.bl_idname} has no output {key}: {[s.name for s in node.outputs]}")

    # ---- common nodes ----
    def texcoord(self, which='Object'):
        n = self.node('ShaderNodeTexCoord')
        return self.out(n, which)

    def attr(self, name, which='Fac', kind='GEOMETRY'):
        n = self.node('ShaderNodeAttribute', attribute_name=name, attribute_type=kind)
        return self.out(n, which)

    def objinfo(self, which='Random'):
        n = self.node('ShaderNodeObjectInfo')
        return self.out(n, which)

    def geometry(self, which='Position'):
        n = self.node('ShaderNodeNewGeometry')
        return self.out(n, which)

    def noise(self, vec=None, scale=5.0, detail=4.0, rough=0.5, distortion=0.0, dims='3D', w=0.0, which='Fac', lac=2.0, ntype='FBM'):
        n = self.node('ShaderNodeTexNoise', noise_dimensions=dims)
        try:
            n.noise_type = ntype
        except Exception:
            pass
        if vec is not None:
            self.set(n, 'Vector', vec)
        self.set(n, 'Scale', scale)
        self.set(n, 'Detail', detail)
        self.set(n, 'Roughness', rough)
        self.set(n, 'Distortion', distortion)
        self.set(n, 'Lacunarity', lac)
        if dims in ('1D', '4D'):
            self.set(n, 'W', w)
        return self.out(n, which)

    def voronoi(self, vec=None, scale=5.0, feature='F1', which='Distance', rand=1.0, dims='3D', metric='EUCLIDEAN', detail=0.0, smooth=1.0):
        n = self.node('ShaderNodeTexVoronoi', voronoi_dimensions=dims, feature=feature, distance=metric)
        if vec is not None:
            self.set(n, 'Vector', vec)
        self.set(n, 'Scale', scale)
        self.set(n, 'Randomness', rand)
        try:
            self.set(n, 'Detail', detail)
        except Exception:
            pass
        if feature == 'SMOOTH_F1':
            self.set(n, 'Smoothness', smooth)
        return self.out(n, which)

    def wave(self, vec=None, scale=5.0, distortion=0.0, detail=2.0, dscale=1.0, droughness=0.5, wtype='BANDS', direction='X', profile='SIN', which='Fac', phase=0.0):
        n = self.node('ShaderNodeTexWave', wave_type=wtype, wave_profile=profile)
        if wtype == 'BANDS':
            n.bands_direction = direction
        else:
            n.rings_direction = direction
        if vec is not None:
            self.set(n, 'Vector', vec)
        self.set(n, 'Scale', scale)
        self.set(n, 'Distortion', distortion)
        self.set(n, 'Detail', detail)
        self.set(n, 'Detail Scale', dscale)
        self.set(n, 'Detail Roughness', droughness)
        self.set(n, 'Phase Offset', phase)
        return self.out(n, which)

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.set(n, 0, a)
        if b is not None:
            self.set(n, 1, b)
        if c is not None:
            self.set(n, 2, c)
        return self.out(n)

    def vmath(self, op, a, b=None, c=None, which=None):
        n = self.node('ShaderNodeVectorMath', operation=op)
        self.set(n, 0, a)
        if b is not None:
            self.set(n, 1, b)
        if c is not None:
            self.set(n, 2, c)
        if which:
            return self.out(n, which)
        if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE'):
            return self.out(n, 'Value')
        return self.out(n, 'Vector')

    def mapping(self, vec, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        n = self.node('ShaderNodeMapping', vector_type='POINT')
        self.set(n, 'Vector', vec)
        self.set(n, 'Location', loc)
        self.set(n, 'Rotation', rot)
        self.set(n, 'Scale', scale)
        return self.out(n)

    def maprange(self, v, a0, a1, b0=0.0, b1=1.0, clamp=True, interp='LINEAR'):
        n = self.node('ShaderNodeMapRange', clamp=clamp, interpolation_type=interp)
        self.set(n, 'Value', v)
        self.set(n, 'From Min', a0)
        self.set(n, 'From Max', a1)
        self.set(n, 'To Min', b0)
        self.set(n, 'To Max', b1)
        return self.out(n)

    def ramp(self, fac, stops, interp='LINEAR'):
        n = self.node('ShaderNodeValToRGB')
        cr = n.color_ramp
        cr.interpolation = interp
        # stops: list of (pos, (r,g,b[,a]))
        while len(cr.elements) > len(stops):
            cr.elements.remove(cr.elements[-1])
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for el, (pos, col) in zip(cr.elements, stops):
            el.position = pos
            if isinstance(col, (int, float)):
                col = (col, col, col, 1.0)
            if len(col) == 3:
                col = tuple(col) + (1.0,)
            el.color = col
        self.set(n, 'Fac', fac)
        return self.out(n, 'Color')

    def mix(self, fac, a, b, blend='MIX', dtype='RGBA', clamp_result=False):
        n = self.node('ShaderNodeMix', data_type=dtype, blend_type=blend, clamp_result=clamp_result)
        self.set(n, 'Factor', fac)
        self.set(n, 'A', a)
        self.set(n, 'B', b)
        return self.out(n, 'Result')

    def hsv(self, col, h=0.5, s=1.0, v=1.0, fac=1.0):
        n = self.node('ShaderNodeHueSaturation')
        self.set(n, 'Hue', h)
        self.set(n, 'Saturation', s)
        self.set(n, 'Value', v)
        self.set(n, 'Fac', fac)
        self.set(n, 'Color', col)
        return self.out(n)

    def bump(self, height, strength=1.0, distance=0.1, normal=None):
        n = self.node('ShaderNodeBump')
        self.set(n, 'Height', height)
        self.set(n, 'Strength', strength)
        self.set(n, 'Distance', distance)
        if normal is not None:
            self.set(n, 'Normal', normal)
        return self.out(n)

    def sep(self, vec):
        n = self.node('ShaderNodeSeparateXYZ')
        self.set(n, 0, vec)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def comb(self, x=0.0, y=0.0, z=0.0):
        n = self.node('ShaderNodeCombineXYZ')
        self.set(n, 0, x)
        self.set(n, 1, y)
        self.set(n, 2, z)
        return self.out(n)

    def principled(self, **inputs):
        n = self.node('ShaderNodeBsdfPrincipled')
        for k, v in inputs.items():
            self.set(n, k.replace('_', ' '), v)
        return n

    def output(self, shader, displacement=None, volume=None):
        n = self.node('ShaderNodeOutputMaterial')
        self.links.new(self.out(shader) if isinstance(shader, bpy.types.Node) else shader, n.inputs['Surface'])
        if displacement is not None:
            self.links.new(displacement, n.inputs['Displacement'])
        if volume is not None:
            self.links.new(self.out(volume) if isinstance(volume, bpy.types.Node) else volume, n.inputs['Volume'])
        return n


def new_material(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def lerp(a, b, t):
    return a + (b - a) * t


def set_mod_input(mod, name, value):
    """Set a geometry-nodes modifier input by interface socket name (Blender 5.x API, with fallback)."""
    ident = None
    for item in mod.node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and (item.name == name or item.identifier == name):
            ident = item.identifier
            break
    if ident is None:
        raise KeyError(name)
    try:
        getattr(mod.properties.inputs, ident).value = value
    except AttributeError:
        mod[ident] = value
