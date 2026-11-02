import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Euler, Matrix

# ---------- node helpers ----------
class NB:
    """small helper to build shader node trees quickly"""
    def __init__(self, mat_or_tree, clear=True):
        self.t = mat_or_tree.node_tree if hasattr(mat_or_tree, 'node_tree') else mat_or_tree
        if clear:
            self.t.nodes.clear()
        self.x = 0
    def n(self, typ, loc=None, **kw):
        nd = self.t.nodes.new(typ)
        nd.location = loc or (self.x, 0)
        self.x += 0
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd
    def link(self, a, b):
        self.t.links.new(a, b)
    def set(self, node, name, val):
        node.inputs[name].default_value = val
    def val(self, v):
        nd = self.n('ShaderNodeValue'); nd.outputs[0].default_value = v; return nd.outputs[0]
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.n('ShaderNodeMath'); nd.operation = op; nd.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): nd.inputs[i].default_value = v
            else: self.link(v, nd.inputs[i])
        return nd.outputs[0]
    def mix(self, fac, a, b, typ='RGBA'):
        nd = self.n('ShaderNodeMix'); nd.data_type = typ
        ia, ib, o = (6, 7, 2) if typ == 'RGBA' else (2, 3, 0)
        for sock, v in ((nd.inputs[0], fac), (nd.inputs[ia], a), (nd.inputs[ib], b)):
            if v is None: continue
            if isinstance(v, (tuple, list, int, float)): sock.default_value = v
            else: self.link(v, sock)
        return nd.outputs[o]
    def ramp(self, fac, stops, interp='LINEAR'):
        nd = self.n('ShaderNodeValToRGB')
        nd.color_ramp.interpolation = interp
        cr = nd.color_ramp
        while len(cr.elements) < len(stops): cr.elements.new(1.0)
        for e, (p, c) in zip(cr.elements, stops):
            e.position = p; e.color = c if len(c) == 4 else (*c, 1)
        if isinstance(fac, (int, float)): nd.inputs[0].default_value = fac
        else: self.link(fac, nd.inputs[0])
        return nd
    def noise(self, vec=None, scale=5, detail=4, rough=0.5, distort=0.0, ntype='FBM'):
        nd = self.n('ShaderNodeTexNoise')
        try: nd.noise_type = ntype
        except Exception: pass
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Distortion'].default_value = distort
        if vec is not None: self.link(vec, nd.inputs['Vector'])
        return nd
    def mapping(self, vec, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        nd = self.n('ShaderNodeMapping')
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Location'].default_value = loc
        nd.inputs['Rotation'].default_value = rot
        self.link(vec, nd.inputs['Vector'])
        return nd.outputs[0]
    def coord(self, which='Object'):
        nd = self.n('ShaderNodeTexCoord'); return nd.outputs[which]
    def bump(self, height, strength=0.3, dist=0.1, normal=None):
        nd = self.n('ShaderNodeBump')
        nd.inputs['Strength'].default_value = strength
        nd.inputs['Distance'].default_value = dist
        self.link(height, nd.inputs['Height'])
        if normal is not None: self.link(normal, nd.inputs['Normal'])
        return nd.outputs[0]
    def sep(self, vec):
        nd = self.n('ShaderNodeSeparateXYZ'); self.link(vec, nd.inputs[0]); return nd.outputs
    def principled(self, base=(0.5, 0.5, 0.5, 1), rough=0.5, **kw):
        nd = self.n('ShaderNodeBsdfPrincipled')
        if isinstance(base, (tuple, list)): nd.inputs['Base Color'].default_value = base if len(base) == 4 else (*base, 1)
        else: self.link(base, nd.inputs['Base Color'])
        if isinstance(rough, (int, float)): nd.inputs['Roughness'].default_value = rough
        else: self.link(rough, nd.inputs['Roughness'])
        for k, v in kw.items():
            k = k.replace('_', ' ')
            if isinstance(v, (int, float, tuple, list)): nd.inputs[k].default_value = v
            else: self.link(v, nd.inputs[k])
        return nd
    def out(self, shader, vol=None):
        o = self.n('ShaderNodeOutputMaterial')
        self.link(shader, o.inputs['Surface'])
        return o

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m

def simple_mat(name, color, rough=0.5, metal=0.0, **kw):
    m = new_mat(name); nb = NB(m)
    p = nb.principled(color, rough, Metallic=metal, **kw)
    nb.out(p.outputs[0]); return m

def emission_mat(name, color, strength):
    m = new_mat(name); nb = NB(m)
    e = nb.n('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nb.out(e.outputs[0]); return m

# ---------- mesh helpers ----------
def mesh_obj(name, verts, faces, mat=None, coll=None, smooth=True, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = loc; ob.rotation_euler = rot; ob.scale = scale
    (coll or bpy.context.scene.collection).objects.link(ob)
    if mat is not None: me.materials.append(mat)
    return ob

def box(name, size, loc, mat, coll=None, rot=(0, 0, 0), parent=None, bevel=0.0):
    """size = full dimensions"""
    sx, sy, sz = size
    v = [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5), (-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]
    v = [(a * sx, b * sy, c * sz) for a, b, c in v]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, mat, coll, smooth=False, loc=loc, rot=rot)
    if bevel > 0:
        m = ob.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 2; m.limit_method = 'ANGLE'
    if parent: ob.parent = parent
    return ob

def cyl(name, r, h, loc, mat, coll=None, rot=(0, 0, 0), seg=24, r2=None, cap=True, parent=None, smooth=True):
    v = []; f = []
    r2 = r if r2 is None else r2
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r * math.cos(a), r * math.sin(a), -h / 2))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r2 * math.cos(a), r2 * math.sin(a), h / 2))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    if cap:
        v.append((0, 0, -h / 2)); v.append((0, 0, h / 2))
        for i in range(seg):
            j = (i + 1) % seg
            f.append((2 * seg, j, i)); f.append((2 * seg + 1, seg + i, seg + j))
    ob = mesh_obj(name, v, f, mat, coll, smooth=smooth, loc=loc, rot=rot)
    if parent: ob.parent = parent
    return ob

def sphere(name, r, loc, mat, coll=None, seg=16, ring=10, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.scale = scale
    (coll or bpy.context.scene.collection).objects.link(ob)
    if mat: me.materials.append(mat)
    return ob

def join(objs, name, coll=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    return ob

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def hash_noise2(x, y, seed=0):
    """cheap value noise on numpy arrays"""
    def h(ix, iy):
        n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        n = n ^ (n >> 16)
        return (n & 0xFFFF) / 65535.0
    x0 = np.floor(x).astype(np.int64); y0 = np.floor(y).astype(np.int64)
    fx = x - x0; fy = y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a = h(x0, y0); b = h(x0 + 1, y0); c = h(x0, y0 + 1); d = h(x0 + 1, y0 + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def fbm2(x, y, oct=4, seed=0):
    s = 0; a = 0.5; f = 1.0
    for i in range(oct):
        s += a * hash_noise2(x * f, y * f, seed + i * 17); a *= 0.5; f *= 2.03
    return s / (1 - 0.5 ** oct)
