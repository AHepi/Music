"""GROUND builder, shared helpers (22 October character round).
Everything the stage creates carries  garden_owner = 'ground', garden_role, g6_made = 1  and lives in collection 'G6 ground'.
Things the stage CHANGES on objects/materials the ground builder owns are recorded so that cleanup() can put them back first (idempotence).
"""
import bpy
import bmesh
import json
import math
import numpy as np
from mathutils import Vector, Matrix, Euler

OWNER = 'ground'
COLL = 'G6 ground'
PFX = 'G6 ground / '


# ------------------------------------------------------------------ colour
def srgb_to_lin(c):
    c = float(c)
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h, mul=1.0):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_lin(r) * mul, srgb_to_lin(g) * mul, srgb_to_lin(b) * mul)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ collections / objects
def get_collection():
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(c)
    return c


def is_mine(ob):
    """made by this stage (and not by another builder that might use a similar label)."""
    return ob.get('g6_made') == 1 and ob.get('garden_owner') == OWNER and ob.name.startswith(('G6 ground', PFX))


def tag(obj, role):
    obj['garden_owner'] = OWNER
    obj['garden_role'] = role
    obj['g6_made'] = 1


def add_object(name, mesh, role, mats=(), hide_render=False, hide_viewport=False):
    obj = bpy.data.objects.new(name, mesh)
    get_collection().objects.link(obj)
    for m in mats:
        mesh.materials.append(m)
    tag(obj, role)
    obj.hide_render = hide_render
    obj.hide_viewport = hide_viewport
    return obj


def mesh_from_arrays(name, verts, faces, cols=None, uv=None, smooth=False, col_name='Col'):
    """verts Nx3, faces list of tuples, cols Nx4 (per vertex, linear) or None, uv Nx2 per vertex or None."""
    me = bpy.data.meshes.new(name)
    verts = np.asarray(verts, dtype=np.float32)
    me.from_pydata(verts.tolist(), [], [tuple(int(i) for i in f) for f in faces])
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if cols is not None:
        cols = np.asarray(cols, dtype=np.float32)
        if cols.shape[1] == 3:
            cols = np.concatenate([cols, np.ones((len(cols), 1), np.float32)], axis=1)
        ca = me.color_attributes.new(col_name, 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', cols.ravel())
        me.color_attributes.active_color = ca
        me.color_attributes.render_color_index = 0
    if uv is not None:
        add_uv_per_vertex(me, 'UVMap', uv)
    me.update()
    return me


def add_uv_per_vertex(me, name, uv):
    layer = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    uv = np.asarray(uv, dtype=np.float32)
    loops = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get('vertex_index', loops)
    layer.data.foreach_set('uv', uv[loops].ravel())


def box_uv(me, name, tile, matrix=None, offset=(0.0, 0.0)):
    """Per-face box UV: the face's dominant normal axis is dropped, the two other (object or matrix-transformed) coordinates / tile
    are the UV. 1 UV unit = `tile` metres. Works for any mesh (sources, stones, kerb)."""
    n = len(me.vertices)
    co = np.zeros(n * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    if matrix is not None:
        m = np.array(matrix.to_3x3(), dtype=np.float32)
        t = np.array(matrix.translation, dtype=np.float32)
        co = co @ m.T + t
    layer = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    nl = len(me.loops)
    vi = np.zeros(nl, dtype=np.int32)
    me.loops.foreach_get('vertex_index', vi)
    pn = np.zeros(len(me.polygons) * 3, dtype=np.float32)
    me.polygons.foreach_get('normal', pn)
    pn = np.abs(pn.reshape(-1, 3))
    dom = pn.argmax(axis=1)                                   # 0 x, 1 y, 2 z
    ls = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get('loop_start', ls)
    lt = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get('loop_total', lt)
    face_of_loop = np.repeat(np.arange(len(me.polygons)), lt)
    d = dom[face_of_loop]
    p = co[vi]
    u = np.where(d == 0, p[:, 1], p[:, 0])
    v = np.where(d == 2, p[:, 1], p[:, 2])
    uv = np.stack([u / tile + offset[0], v / tile + offset[1]], axis=1)
    # no mirrored islands: where a face's UV runs the wrong way round (opposite faces of a box), flip its u
    ok = lt >= 3
    i0, i1, i2 = ls[ok], ls[ok] + 1, ls[ok] + 2
    cr = (uv[i1, 0] - uv[i0, 0]) * (uv[i2, 1] - uv[i0, 1]) - (uv[i1, 1] - uv[i0, 1]) * (uv[i2, 0] - uv[i0, 0])
    flip_face = np.zeros(len(me.polygons), dtype=bool)
    flip_face[np.where(ok)[0]] = cr < 0
    # winding of the polygon seen from its normal: the cross above is in UV space, so compare with the sign of the face normal axis
    pn_signed = np.zeros(len(me.polygons) * 3, dtype=np.float32)
    me.polygons.foreach_get('normal', pn_signed)
    pn_signed = pn_signed.reshape(-1, 3)
    axis_sign = np.take_along_axis(pn_signed, dom[:, None], axis=1)[:, 0]
    # for a +axis face the UV (a, b) already turns counter-clockwise only for some axes; use the computed area sign as the truth
    fl = flip_face[face_of_loop]
    uv[fl, 0] = -uv[fl, 0] + 2 * offset[0]
    layer.data.foreach_set('uv', uv.astype(np.float32).ravel())
    return layer


def planar_uv(me, name, tile_xy, offset=(0.0, 0.0), matrix=None):
    """top-down (x, y) UV: u = x / tile_x + off, v = y / tile_y + off."""
    n = len(me.vertices)
    co = np.zeros(n * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    if matrix is not None:
        co = co @ np.array(matrix.to_3x3(), dtype=np.float32).T + np.array(matrix.translation, dtype=np.float32)
    layer = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    vi = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get('vertex_index', vi)
    p = co[vi]
    uv = np.stack([p[:, 0] / tile_xy[0] + offset[0], p[:, 1] / tile_xy[1] + offset[1]], axis=1)
    layer.data.foreach_set('uv', uv.astype(np.float32).ravel())
    return layer


# ------------------------------------------------------------------ restoring changes on owned (existing) things
def _rec(mat):
    try:
        return json.loads(mat.get('gnd_rec', '{"links": [], "vals": []}'))
    except Exception:
        return {"links": [], "vals": []}


def _save(mat, d):
    mat['gnd_rec'] = json.dumps(d)


def unlink_input(mat, node_name, sock_ident_or_name):
    """remove links into one input socket, remembering them so cleanup can put them back."""
    nt = mat.node_tree
    d = _rec(mat)
    for l in list(nt.links):
        if l.to_node.name == node_name and (l.to_socket.identifier == sock_ident_or_name or l.to_socket.name == sock_ident_or_name):
            d['links'].append([l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier])
            nt.links.remove(l)
    _save(mat, d)


def set_default(mat, node_name, sock_name, value):
    """set an input default on an ORIGINAL node, remembering the old value."""
    nt = mat.node_tree
    node = nt.nodes[node_name]
    sock = node.inputs[sock_name]
    d = _rec(mat)
    key = [node_name, sock.identifier]
    if not any(v[0] == key[0] and v[1] == key[1] for v in d['vals']):
        old = sock.default_value
        try:
            old = list(old)
        except TypeError:
            pass
        d['vals'].append([node_name, sock.identifier, old])
        _save(mat, d)
    sock.default_value = value


def restore_material(mat):
    if mat is None or mat.node_tree is None:
        return
    nt = mat.node_tree
    for n in [n for n in nt.nodes if n.name.startswith('G6 ')]:
        nt.nodes.remove(n)
    d = _rec(mat)
    for fn, fid, tn, tid in d['links']:
        a, b = nt.nodes.get(fn), nt.nodes.get(tn)
        if a is None or b is None:
            continue
        so = next((s for s in a.outputs if s.identifier == fid), None)
        si = next((s for s in b.inputs if s.identifier == tid), None)
        if so is None or si is None:
            continue
        if not any(l.from_socket == so and l.to_socket == si for l in nt.links):
            nt.links.new(so, si)
    for nn, sid, old in d['vals']:
        n = nt.nodes.get(nn)
        if n is None:
            continue
        s = next((s for s in n.inputs if s.identifier == sid), None)
        if s is not None:
            try:
                s.default_value = old
            except Exception:
                pass
    if 'gnd_rec' in mat:
        del mat['gnd_rec']


# ------------------------------------------------------------------ node helpers (shader)
def N(nt, idname, name, loc=(0, 0), label=None, **props):
    n = nt.nodes.new(idname)
    n.name = 'G6 ' + name
    n.label = label or name
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n


def link(nt, *args):
    """link(nt, node, out_name_or_index, node2, in_name_or_index)  or  link(nt, out_socket, node2, in_name_or_index)"""
    if len(args) == 4:
        a, asock, b, bsock = args
        so = a.outputs[asock] if isinstance(asock, (str, int)) else asock
    else:
        so, b, bsock = args
    si = b.inputs[bsock] if isinstance(bsock, (str, int)) else bsock
    nt.links.new(so, si)


def load_image(path, name, non_color=True):
    img = bpy.data.images.get(name)
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.load(path, check_existing=False)
    img.name = name
    if non_color:
        img.colorspace_settings.name = 'Non-Color'      # a loaded FILE image: safe (pixels are read afterwards)
    img.alpha_mode = 'NONE' if non_color else img.alpha_mode
    return img


def normal_chain(nt, img_node_name, image, uv_map, strength, scale, loc=(0, 0), mapping_rot=None):
    """UV Map -> Mapping -> Image (Non-Color, Cubic, Repeat) -> Normal Map (Tangent). Returns (normal_map_node, mapping_node)."""
    uv = N(nt, 'ShaderNodeUVMap', img_node_name + ' UV', (loc[0], loc[1]))
    uv.uv_map = uv_map
    mp = N(nt, 'ShaderNodeMapping', img_node_name + ' Mapping', (loc[0] + 180, loc[1]))
    mp.inputs['Scale'].default_value = scale
    tx = N(nt, 'ShaderNodeTexImage', img_node_name + ' Image', (loc[0] + 380, loc[1]))
    tx.image = image
    tx.interpolation = 'Cubic'
    tx.extension = 'REPEAT'
    nm = N(nt, 'ShaderNodeNormalMap', img_node_name + ' Normal Map', (loc[0] + 700, loc[1]))
    nm.space = 'TANGENT'
    nm.uv_map = uv_map
    nm.inputs['Strength'].default_value = strength
    link(nt, uv, 'UV', mp, 'Vector')
    link(nt, mp, 'Vector', tx, 'Vector')
    link(nt, tx, 'Color', nm, 'Color')
    return nm, mp


# ------------------------------------------------------------------ cleanup of an earlier run
def swap_mesh(obj, new_mesh):
    """give an existing object a new mesh; the old one is kept (renamed, fake user) so cleanup can restore it."""
    if 'gnd_orig_mesh' not in obj:
        old = obj.data
        obj['gnd_orig_mesh'] = old.name
        old.name = PFX + 'orig ' + old.name
        old.use_fake_user = True
    new_mesh.name = new_mesh.name if new_mesh.name.startswith(PFX) else new_mesh.name
    mats = [s.material for s in obj.material_slots]
    obj.data = new_mesh
    if not new_mesh.materials:
        for m in mats:
            new_mesh.materials.append(m)


def restore_object_mesh(obj):
    on = obj.get('gnd_orig_mesh')
    if on is None:
        return
    old = bpy.data.meshes.get(PFX + 'orig ' + on)
    if old is not None:
        cur = obj.data
        mats = [s.material for s in obj.material_slots]
        obj.data = old
        old.name = on
        old.use_fake_user = False
        if cur.users == 0 and cur != old:
            bpy.data.meshes.remove(cur)
    del obj['gnd_orig_mesh']


MY_IMAGES = ('G6 path_mask', 'G6 ground_normal', 'G6 moss_normal', 'G6 stone_normal', 'G6 pebble_normal')
OWNED_MATERIAL_NAMES = ['Moss and earth', 'Raked gravel', 'Astra / moss tone 0', 'Astra / moss tone 1', 'Astra / moss tone 2', 'Astra / moss tone 3',
                        'Astra / pebbles tone 0', 'Astra / pebbles tone 1', 'Astra / pebbles tone 2', 'Astra / pebbles tone 3', 'Life / tuft',
                        'Life / shrub', 'Fallen leaves'] + \
    ['CT / Stone painterly surface'] + ['CT / Stone painterly surface.%03d' % i for i in list(range(1, 8)) + [30, 31, 32]]


def object_names_owned():
    names = ['Astra / Courtyard receiving ground', 'Courtyard ground source', 'Astra / moss grouped bodies', 'Astra / pebbles grouped bodies',
             'Life / moss at feet and damp edges', 'Life / pebble fringe', 'Life / tufts', 'Life / shrubs', 'Fix / far hedge', 'Fallen leaves',
             'Raked gravel court', 'Gravel kerb']
    names += ['Life / moss sources %d' % i for i in range(6)] + ['Life / pebble sources %d' % i for i in range(6)] + ['Life / tuft sources %d' % i for i in range(4)]
    names += ['Gravel rock %d' % i for i in range(3)] + ['Stepping stone %d' % i for i in range(8)]
    return names


def cleanup():
    """remove everything an earlier run made and restore what it changed. Safe to call on a scene that never had a run."""
    # 1. restore changed owned objects (meshes, modifiers, material slots)
    for ob in list(bpy.data.objects):
        if ob.get('gnd_orig_mesh') is not None:
            restore_object_mesh(ob)
        og = ob.get('gnd_orig_group')
        if og is not None:
            for m in ob.modifiers:
                if m.type == 'NODES' and m.node_group is not None and m.node_group.name.startswith(PFX):
                    m.node_group = bpy.data.node_groups.get(og)
            del ob['gnd_orig_group']
        om = ob.get('gnd_orig_mats')
        if om is not None:
            try:
                names = json.loads(om)
                for i, nm in enumerate(names):
                    if i < len(ob.material_slots):
                        ob.material_slots[i].material = bpy.data.materials.get(nm)
            except Exception:
                pass
            del ob['gnd_orig_mats']
        if ob.get('gnd_col_added') and ob.type == 'MESH':
            ca = ob.data.color_attributes.get('Col')
            if ca is not None:
                ob.data.color_attributes.remove(ca)
        ua = ob.get('gnd_uv_added')
        if ua is not None and ob.type == 'MESH':
            try:
                for nm in json.loads(ua):
                    lay = ob.data.uv_layers.get(nm)
                    if lay is not None:
                        ob.data.uv_layers.remove(lay)
            except Exception:
                pass
        if not is_mine(ob):
            for key in ('gnd_orig_mesh', 'gnd_orig_group', 'gnd_orig_mats', 'gnd_uv_added', 'gnd_col_added'):
                if key in ob:
                    try:
                        del ob[key]
                    except Exception:
                        pass
    # 2. remove my own objects
    for ob in [o for o in bpy.data.objects if is_mine(o)]:
        me = ob.data if ob.type == 'MESH' else None
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    # 3. restore materials that were edited in place (only the ones this builder owns, so another builder's nodes named 'G6 ...' are never touched)
    owned = set(OWNED_MATERIAL_NAMES)
    for m in list(bpy.data.materials):
        if m.name.startswith(PFX):
            continue
        if m.get('gnd_rec') is not None or (m.name in owned and m.node_tree and any(n.name.startswith('G6 ') for n in m.node_tree.nodes)):
            restore_material(m)
    # 4. drop my datablocks
    for m in [m for m in bpy.data.materials if m.name.startswith(PFX)]:
        bpy.data.materials.remove(m)
    for g in [g for g in bpy.data.node_groups if g.name.startswith(PFX)]:
        bpy.data.node_groups.remove(g)
    for i in [i for i in bpy.data.images if i.name in MY_IMAGES]:
        bpy.data.images.remove(i)
    for me in [me for me in bpy.data.meshes if me.name.startswith(PFX) and not me.name.startswith(PFX + 'orig ') and me.users == 0]:
        bpy.data.meshes.remove(me)
    for cam in [c for c in bpy.data.cameras if c.name.startswith('G6 ground cam')]:
        if cam.users == 0:
            bpy.data.cameras.remove(cam)
    for ld in [l for l in bpy.data.lights if l.name.startswith(PFX)]:
        if ld.users == 0:
            bpy.data.lights.remove(ld)
    c = bpy.data.collections.get(COLL)
    if c is not None:
        for ch in list(c.children):
            bpy.data.collections.remove(ch)
        bpy.data.collections.remove(c)


def track_uv(obj, name):
    """call BEFORE adding a UV layer to an existing object: remembers that the layer is ours so cleanup can remove it."""
    if obj.data.uv_layers.get(name) is None:
        d = json.loads(obj.get('gnd_uv_added', '[]'))
        if name not in d:
            d.append(name)
        obj['gnd_uv_added'] = json.dumps(d)


def inventory():
    return {'objects': sorted(o.name for o in bpy.data.objects), 'materials': sorted(m.name for m in bpy.data.materials),
            'node_groups': sorted(g.name for g in bpy.data.node_groups)}


def tri_count(obj, dg=None):
    dg = dg or bpy.context.evaluated_depsgraph_get()
    eo = obj.evaluated_get(dg)
    me = eo.to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    eo.to_mesh_clear()
    return n
