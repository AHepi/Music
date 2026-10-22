"""Shared helpers of the roof builder (22 October). Runs inside Blender 5.2 Python (numpy yes, PIL no).
Plain words: small tools used by every step of stage_roof.py: naming, tagging, collections, material copies, node helpers, UV writers."""
import bpy
import bmesh
import math
import os
import sys
import numpy as np
from mathutils import Vector, Matrix

OWNER = 'roof'
PFX = 'G6 roof / '
COLL = 'G6 roof'
HERE = os.path.dirname(os.path.abspath(__file__))
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'


def log(*a):
    print('[roof]', *a, flush=True)


def collection():
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(c)
    return c


def link_to(obj, *names):
    for n in names:
        c = bpy.data.collections.get(n)
        if c is not None and obj.name not in c.objects:
            c.objects.link(obj)


def tag(obj, role):
    obj['garden_owner'] = OWNER
    obj['garden_role'] = role
    obj['g6_made'] = 1


def new_object(name, mesh, role, receivers=False, linked=True, hide_render=False):
    """New object in collection 'G6 roof' (garden_owner=roof, garden_role=role). receivers=True also links it into
    'G4 rim receivers' and 'G4 roof receivers' (roof parts only)."""
    o = bpy.data.objects.new(PFX + name, mesh)
    tag(o, role)
    if linked:
        collection().objects.link(o)
        if receivers:
            link_to(o, 'G4 rim receivers', 'G4 roof receivers')
    o.hide_render = hide_render
    return o


def copy_wk_props(src, dst):
    """The weathering kit reads wk_* custom properties of the object; copy them so a new part weathers like its neighbour."""
    for k in src.keys():
        if k.startswith('wk_'):
            dst[k] = src[k]


def mat_copy(src_name, new_name):
    src = bpy.data.materials[src_name]
    m = src.copy()
    m.name = PFX + new_name
    return m


def new_mesh(name, verts, faces, uv=None, smooth=False):
    me = bpy.data.meshes.new(PFX + name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return me


def set_uv(me, uv_name, fn):
    """fn(co: Vector, normal: Vector) -> (u, v), evaluated per face corner (normal = face normal).
    A face whose UV winding came out mirrored is turned around (its u mirrored about its own middle) when only a few faces are affected."""
    layer = me.uv_layers.get(uv_name) or me.uv_layers.new(name=uv_name)
    neg = []
    for p in me.polygons:
        n = p.normal
        pts = []
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv = fn(co, n)
            layer.data[li].uv = uv
            pts.append(uv)
        a = 0.0
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            a += x0 * y1 - x1 * y0
        if a < -1e-12:
            neg.append(p)
    if neg and len(neg) < 0.2 * len(me.polygons):
        for p in neg:
            us = [layer.data[li].uv[0] for li in p.loop_indices]
            m = (min(us) + max(us)) * 0.5
            for li in p.loop_indices:
                u, v = layer.data[li].uv
                layer.data[li].uv = (2 * m - u, v)
    return layer


def box_uv_fn(tile_m, off=(0.0, 0.0), per_axis_offset=None, world=None, inside_out=False):
    """Box projection: coordinates not along the face's dominant axis, divided by tile_m (1 UV unit = tile_m metres).
    Every face gets the same winding seen from outside (u mirrored on the faces that would otherwise be mirrored), so no island is flipped."""
    def fn(co, n):
        if world is not None:
            co = world @ co
        ax = max(range(3), key=lambda i: abs(n[i]))
        if ax == 2:
            u, v = co.x, co.y
            flip = n[2] < 0
        elif ax == 1:
            u, v = co.x, co.z
            flip = n[1] > 0
        else:
            u, v = co.y, co.z
            flip = n[0] < 0
        if flip != inside_out:
            u = -u
        ox, oy = off
        if per_axis_offset is not None:
            s = 0 if n[ax] > 0 else 1
            ox += per_axis_offset[ax][s][0]
            oy += per_axis_offset[ax][s][1]
        return (u / tile_m + ox, v / tile_m + oy)
    return fn


# ------------------------------------------------------------------ node helpers
def sock(sockets, name, enabled_only=True):
    first = None
    for s in sockets:
        if s.name == name:
            if first is None:
                first = s
            if s.enabled and not getattr(s, 'hide', False):
                return s
    return first


def sid(sockets, ident):
    for s in sockets:
        if s.identifier == ident:
            return s
    raise KeyError(ident)


def nnew(nt, idname, name=None, loc=None, **props):
    n = nt.nodes.new(idname)
    for k, v in props.items():
        setattr(n, k, v)
    if name:
        n.name = name
        n.label = name
    if loc is not None:
        n.location = loc
    return n


def link(nt, a, b):
    nt.links.new(a, b)


def val(nt, v, name=None):
    n = nt.nodes.new('ShaderNodeValue')
    n.outputs[0].default_value = v
    if name:
        n.name = n.label = name
    return n


def math_node(nt, op, a=None, b=None, c=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = float(x)
        else:
            nt.links.new(x, n.inputs[i])
    return n


def vmath(nt, op, a=None, b=None, c=None):
    n = nt.nodes.new('ShaderNodeVectorMath')
    n.operation = op
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (tuple, list)):
            n.inputs[i].default_value = tuple(x)
        else:
            nt.links.new(x, n.inputs[i])
    return n


def mix_rgb(nt, fac, a, b, blend='MIX'):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    n.clamp_factor = True
    if isinstance(fac, (int, float)):
        sid(n.inputs, 'Factor_Float').default_value = float(fac)
    else:
        nt.links.new(fac, sid(n.inputs, 'Factor_Float'))
    for key, x in (('A_Color', a), ('B_Color', b)):
        s = sid(n.inputs, key)
        if x is None:
            continue
        if isinstance(x, (tuple, list)):
            s.default_value = tuple(x) if len(x) == 4 else tuple(x) + (1.0,)
        else:
            nt.links.new(x, s)
    return n


def signed_volume(me):
    """positive when the faces are wound outwards (normals point out), negative for an inside-out mesh"""
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    tri = np.empty(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get('vertices', tri)
    tri = tri.reshape(-1, 3)
    a, b, c_ = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    return float(np.einsum('ij,ij->i', a, np.cross(b, c_)).sum() / 6.0)


def srgb_to_lin(c):
    out = []
    for v in c[:3]:
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def hex_lin(h, a=1.0):
    h = h.lstrip('#')
    c = tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return srgb_to_lin(c) + (a,)


def mix_out(n):
    return n.outputs['Result'] if False else [o for o in n.outputs if o.name == 'Result' and o.enabled][0]


def smoothstep_node(nt, x, lo, hi):
    """smoothstep(lo, hi, x) with float lo/hi, built from Map Range (smoothstep) so it stays inside Blender."""
    n = nt.nodes.new('ShaderNodeMapRange')
    n.data_type = 'FLOAT'
    n.interpolation_type = 'SMOOTHSTEP'
    n.clamp = True
    n.inputs['From Min'].default_value = lo
    n.inputs['From Max'].default_value = hi
    n.inputs['To Min'].default_value = 0.0
    n.inputs['To Max'].default_value = 1.0
    if isinstance(x, (int, float)):
        n.inputs['Value'].default_value = x
    else:
        nt.links.new(x, n.inputs['Value'])
    return n


# ------------------------------------------------------------------ images
def make_image(name, rgba_rows_top_first, colorspace='Non-Color', alpha=False):
    """Make a generated image from a (h, w, 3 or 4) array in 0..1, row 0 = TOP. Colour space first, pixels second (Blender 5.2.2 gotcha)."""
    a = np.asarray(rgba_rows_top_first, dtype=np.float32)
    h, w = a.shape[:2]
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones((h, w, 1), np.float32)], axis=2)
    old = bpy.data.images.get(PFX + name)
    if old is not None:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(PFX + name, w, h, alpha=alpha, float_buffer=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(a[::-1].ravel())
    img.update()
    img.pack()
    return img


def save_png(img, path):
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()


def load_gray(path):
    """Read an image file as numpy rows-top-first (h, w) raw values (Non-Color)."""
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[::-1]
    bpy.data.images.remove(img)
    return px[..., :3].mean(axis=2), px[..., :3]
