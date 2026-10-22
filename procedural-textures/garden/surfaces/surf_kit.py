# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The small toolbox that stage_surfaces.py builds its materials with (Blender 5.2, shader nodes only, no geometry is touched):
#   * load_scan(key)            loads the three 1k pictures of a Poly Haven surface (colour = sRGB, roughness and height = Non-Color) once
#   * scan_group(...)           one shared node group per surface: it reads a picture three ways ("planar" from above with a second look at another size and
#                               angle so no tile repeats, or "triplanar" = box projection from all three directions) and gives back Color, Roughness, Height.
#                               Nothing in the scene has UV coordinates, so everything is projected from world position.
#   * Builder                   a tiny helper that adds nodes and wires them inside one material
# Colour rule used everywhere ("normalise"): colour_out = target_mean * (scan / scan_mean) ^ contrast, so the scene (not the photographer's sky) decides the
# overall colour and brightness, and the scan only brings the small-scale variation. contrast < 1 quietens it.
import bpy
import math
import os
import json

SCAN_STATS = {}
_BUILT = set()   # scan groups already (re)built in this session: building one again would cut the wires of every material that already uses it
# which way the boards/grain run in the picture itself (u = along the picture's width, v = up the picture)
SCAN_BOARD = {'weathered_planks': 'v', 'wood_planks_grey': 'v'}


def maps_dir(options=None):
    here = os.path.dirname(os.path.abspath(__file__))
    return (options or {}).get('maps_dir') or os.path.join(here, 'maps')


def scan_stats(options=None):
    global SCAN_STATS
    if not SCAN_STATS:
        with open(os.path.join(maps_dir(options), 'scan_stats.json')) as f:
            SCAN_STATS = json.load(f)
    return SCAN_STATS


_IMAGES = {}


def load_scan(key, options=None, which=('diff', 'rough', 'disp')):
    """{'diff': image, 'rough': image, 'disp': image} for a scan id such as 'rock_boulder_dry'."""
    out = {}
    for w in which:
        name = f'{key}_{w}_1k.jpg'
        path = os.path.join(maps_dir(options), name)
        img = bpy.data.images.get(name)
        if img is None or (img.filepath and not os.path.exists(bpy.path.abspath(img.filepath)) and not img.packed_file):
            img = bpy.data.images.load(path, check_existing=True)
            img.name = name
        if img.source == 'FILE' and not img.packed_file and (not os.path.exists(bpy.path.abspath(img.filepath))):
            img.filepath = path
            img.reload()
        img.colorspace_settings.name = 'sRGB' if w == 'diff' else 'Non-Color'
        img['garden_owner'] = 'surfaces'
        out[w] = img
    return out


# ------------------------------------------------------------------------------------------------------------------------------ node helpers
def _in(node, ident):
    """A socket of ShaderNodeMix by identifier (the float, vector and colour versions share one name: 'A', 'B', 'Factor', 'Result')."""
    for sock in list(node.inputs) + list(node.outputs):
        if sock.identifier == ident:
            return sock
    raise KeyError(ident)


class Builder:
    """Adds nodes to a node tree and wires them. n(...) makes a node, l(a, b) links, c(...) shortcuts for constants."""

    def __init__(self, tree, x=0, y=0):
        self.t = tree
        self.x, self.y = x, y
        self.col = 0

    def n(self, idname, label=None, loc=None, **props):
        node = self.t.nodes.new(idname)
        if label:
            node.label = label
        node.location = loc if loc is not None else (self.x, self.y)
        for k, v in props.items():
            setattr(node, k, v)
        self.y -= 180
        return node

    def newcol(self, step=260):
        self.x += step
        self.y = 0

    def l(self, a, b):
        self.t.links.new(a, b)

    # ---- value helpers: every helper returns an OUTPUT socket
    def val(self, v, label=None):
        node = self.n('ShaderNodeValue', label)
        node.outputs[0].default_value = v
        return node.outputs[0]

    def rgb(self, c, label=None):
        node = self.n('ShaderNodeRGB', label)
        node.outputs[0].default_value = (c[0], c[1], c[2], 1.0)
        return node.outputs[0]

    def vec(self, v, label=None):
        node = self.n('ShaderNodeCombineXYZ', label)
        for i in range(3):
            node.inputs[i].default_value = v[i]
        return node.outputs[0]

    def put(self, sock, v):
        """Feed an input socket with a socket (link) or a plain number/tuple."""
        if hasattr(v, 'node'):
            self.l(v, sock)
        else:
            try:
                sock.default_value = v
            except TypeError:
                sock.default_value = tuple(v) + ((1.0,) if len(sock.default_value) == 4 and len(v) == 3 else ())

    def math(self, op, a, b=None, c=None, clamp=False, label=None):
        node = self.n('ShaderNodeMath', label, operation=op, use_clamp=clamp)
        self.put(node.inputs[0], a)
        if b is not None:
            self.put(node.inputs[1], b)
        if c is not None:
            self.put(node.inputs[2], c)
        return node.outputs[0]

    def vmath(self, op, a, b=None, c=None, label=None, scale=None):
        node = self.n('ShaderNodeVectorMath', label, operation=op)
        self.put(node.inputs[0], a)
        if b is not None:
            self.put(node.inputs[1], b)
        if c is not None:
            self.put(node.inputs[2], c)
        if scale is not None:
            self.put(node.inputs[3], scale)
        return node.outputs[0] if op not in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else node.outputs['Value']

    def sep(self, v):
        node = self.n('ShaderNodeSeparateXYZ')
        self.l(v, node.inputs[0])
        return node.outputs[0], node.outputs[1], node.outputs[2]

    def comb(self, x, y, z):
        node = self.n('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            self.put(node.inputs[i], v)
        return node.outputs[0]

    def mixc(self, fac, a, b, blend='MIX', label=None):
        """Colour mix: result = a*(1-fac) + b*fac for MIX."""
        node = self.n('ShaderNodeMix', label, data_type='RGBA', blend_type=blend)
        self.put(_in(node, 'Factor_Float'), fac)
        self.put(_in(node, 'A_Color'), a if hasattr(a, 'node') else (a[0], a[1], a[2], 1.0))
        self.put(_in(node, 'B_Color'), b if hasattr(b, 'node') else (b[0], b[1], b[2], 1.0))
        return _in(node, 'Result_Color')

    def mixf(self, fac, a, b, label=None):
        node = self.n('ShaderNodeMix', label, data_type='FLOAT')
        self.put(_in(node, 'Factor_Float'), fac)
        self.put(_in(node, 'A_Float'), a)
        self.put(_in(node, 'B_Float'), b)
        return _in(node, 'Result_Float')

    def ramp(self, fac, stops, interp='LINEAR', label=None):
        node = self.n('ShaderNodeValToRGB', label)
        node.color_ramp.interpolation = interp
        els = node.color_ramp.elements
        while len(els) > 2:
            els.remove(els[-1])
        for i, (pos, col) in enumerate(stops):
            if i >= len(els):
                els.new(pos)
            els[i].position = pos
            els[i].color = (col[0], col[1], col[2], 1.0) if len(col) == 3 else col
        self.put(node.inputs[0], fac)
        return node.outputs[0]

    def maprange(self, v, a0, a1, b0, b1, clamp=True, label=None):
        node = self.n('ShaderNodeMapRange', label, clamp=clamp)
        self.put(node.inputs[0], v)
        self.put(node.inputs[1], a0)
        self.put(node.inputs[2], a1)
        self.put(node.inputs[3], b0)
        self.put(node.inputs[4], b1)
        return node.outputs[0]

    def noise(self, vec, scale, detail=3.0, rough=0.5, label=None, distortion=0.0):
        node = self.n('ShaderNodeTexNoise', label, noise_dimensions='3D')
        self.put(node.inputs['Vector'], vec)
        self.put(node.inputs['Scale'], scale)
        self.put(node.inputs['Detail'], detail)
        self.put(node.inputs['Roughness'], rough)
        if distortion:
            self.put(node.inputs['Distortion'], distortion)
        return node.outputs[0]

    def hsv(self, color, hue=0.5, sat=1.0, value=1.0, fac=1.0, label=None):
        node = self.n('ShaderNodeHueSaturation', label)
        self.put(node.inputs['Hue'], hue)
        self.put(node.inputs['Saturation'], sat)
        self.put(node.inputs['Value'], value)
        self.put(node.inputs['Fac'], fac)
        self.put(node.inputs['Color'], color)
        return node.outputs[0]

    def group(self, tree, label=None):
        node = self.n('ShaderNodeGroup', label)
        node.node_tree = tree
        return node

    def smooth(self, v, a, b):
        """smoothstep(a, b, v) from a map range with the smooth-step type."""
        node = self.n('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='SMOOTHSTEP', clamp=True)
        self.put(node.inputs[0], v)
        self.put(node.inputs[1], a)
        self.put(node.inputs[2], b)
        return node.outputs[0]

    def lum(self, color):
        node = self.n('ShaderNodeRGBToBW')
        self.l(color, node.inputs[0])
        return node.outputs[0]


def clear_tree(tree):
    for node in list(tree.nodes):
        tree.nodes.remove(node)


def new_group(name, inputs, outputs):
    """(Re)builds an empty shader node group with the given interface. inputs: [(name, socket_type, default)], outputs: [(name, socket_type)]."""
    ng = bpy.data.node_groups.get(name)
    if ng is None:
        ng = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    clear_tree(ng)
    ng.interface.clear()
    for nm, st, default in inputs:
        s = ng.interface.new_socket(name=nm, in_out='INPUT', socket_type=st)
        if default is not None:
            try:
                s.default_value = default
            except Exception:
                pass
    for nm, st in outputs:
        ng.interface.new_socket(name=nm, in_out='OUTPUT', socket_type=st)
    ng['garden_owner'] = 'surfaces'
    ng.use_fake_user = False
    gin = ng.nodes.new('NodeGroupInput')
    gin.location = (-900, 0)
    gout = ng.nodes.new('NodeGroupOutput')
    gout.location = (1400, 0)
    return ng, gin, gout


# ------------------------------------------------------------------------------------------------------------------------------ scan groups
def scan_group(key, mode, grain=None, antitile=False, options=None, which=('diff', 'rough', 'disp')):
    """Shared node group 'GARDEN scan <key> <mode...>'. mode 'planar' (from above, optional anti-tiling) or 'tri' (box projection by the surface normal).
    grain (tri only): the world axis ('x', 'y' or 'z') the picture's boards / wood grain should run along (None = leave the picture as it lies)."""
    name = f'GARDEN scan {key} {mode}{"-" + grain if grain else ""}{"+AT" if antitile else ""}'
    if name in _BUILT and name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    _BUILT.add(name)
    imgs = load_scan(key, options, which)
    ng, gin, gout = new_group(name,
                              [('Position', 'NodeSocketVector', (0, 0, 0)), ('Normal', 'NodeSocketVector', (0, 0, 1)), ('Scale', 'NodeSocketFloat', 2.0),
                               ('Offset', 'NodeSocketVector', (0, 0, 0)), ('Rotation', 'NodeSocketFloat', 0.0), ('Sharpness', 'NodeSocketFloat', 5.0)],
                              [('Color', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
    b = Builder(ng, -700, 200)
    P = b.vmath('ADD', gin.outputs['Position'], gin.outputs['Offset'], label='position + offset')
    inv = b.math('DIVIDE', 1.0, gin.outputs['Scale'], label='1 / metres per repeat')

    def sample(uvw, rot=None, shift=(0.0, 0.0), size_mult=1.0):
        """Three image looks at one coordinate; returns (colour, roughness, height) output sockets."""
        scl = b.math('MULTIPLY', inv, 1.0 / size_mult) if size_mult != 1.0 else inv
        v = b.vmath('SCALE', uvw, scale=scl)
        if rot is not None or shift != (0.0, 0.0):
            mp = b.n('ShaderNodeMapping', vector_type='POINT')
            b.l(v, mp.inputs['Vector'])
            if shift != (0.0, 0.0):
                mp.inputs['Location'].default_value = (shift[0], shift[1], 0.0)
            if rot is not None:
                b.l(b.comb(0.0, 0.0, rot), mp.inputs['Rotation'])
            v = mp.outputs[0]
        res = []
        for w in ('diff', 'rough', 'disp'):
            if w not in imgs:
                res.append(None)
                continue
            tx = b.n('ShaderNodeTexImage', f'{w}', image=imgs[w], interpolation='Linear', extension='REPEAT', projection='FLAT')
            b.l(v, tx.inputs['Vector'])
            res.append(tx.outputs['Color'])
        return res

    if mode == 'planar':
        px, py, pz = b.sep(P)
        uvw = b.comb(px, py, 0.0)
        c1, r1, h1 = sample(uvw, rot=gin.outputs['Rotation'])
        if not antitile:
            out = (c1, r1, h1)
        else:
            rot2 = b.math('ADD', gin.outputs['Rotation'], 0.93)
            c2, r2, h2 = sample(uvw, rot=rot2, shift=(0.37, 0.61), size_mult=1.7)
            ns = b.noise(b.vmath('SCALE', P, scale=0.23), 1.0, detail=2.0, rough=0.5)
            fac = b.smooth(ns, 0.38, 0.62)
            out = (b.mixc(fac, c1, c2), b.mixf(fac, r1, r2), b.mixf(fac, h1, h2))
    else:
        # box projection: weights from the normal, one picture look per axis
        nrm = b.vmath('ABSOLUTE', gin.outputs['Normal'])
        sh = b.comb(gin.outputs['Sharpness'], gin.outputs['Sharpness'], gin.outputs['Sharpness'])
        nw = b.vmath('POWER', nrm, sh)
        wx, wy, wz = b.sep(nw)
        tot = b.math('ADD', b.math('ADD', wx, wy), wz)
        tot = b.math('MAXIMUM', tot, 0.0001)
        wx, wy, wz = [b.math('DIVIDE', w, tot) for w in (wx, wy, wz)]
        px, py, pz = b.sep(P)
        g = grain
        axes = {'x': px, 'y': py, 'z': pz}

        def plane(n):
            """(u, v) world components for the faces whose normal runs along axis n; the picture's board direction (SCAN_BOARD) is put along the wanted grain axis."""
            first, second = {'x': ('y', 'z'), 'y': ('x', 'z'), 'z': ('x', 'y')}[n]
            if g is None or g == n:
                return axes[first], axes[second]
            other = second if g == first else first
            if SCAN_BOARD.get(key, 'u') == 'u':
                return axes[g], axes[other]
            return axes[other], axes[g]
        uvx, uvy, uvz = plane('x'), plane('y'), plane('z')
        samples = []
        for (u, v_), w in ((uvx, wx), (uvy, wy), (uvz, wz)):
            c, r, h = sample(b.comb(u, v_, 0.0))
            samples.append((c, r, h, w))
        col = None
        rough = None
        hgt = None
        for c, r, h, w in samples:
            cw = b.vmath('SCALE', c, scale=w)
            rw = b.math('MULTIPLY', r, w)
            hw = b.math('MULTIPLY', h, w)
            col = cw if col is None else b.vmath('ADD', col, cw)
            rough = rw if rough is None else b.math('ADD', rough, rw)
            hgt = hw if hgt is None else b.math('ADD', hgt, hw)
        out = (col, rough, hgt)
    b.l(out[0], gout.inputs['Color'])
    b.l(out[1], gout.inputs['Roughness'])
    b.l(out[2], gout.inputs['Height'])
    return ng


def seed_hash(text, mod=1000):
    h = 2166136261
    for ch in text:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return (h % mod) / float(mod)


def fresh_material_tree(mat):
    mat.use_nodes = True
    clear_tree(mat.node_tree)
    return mat.node_tree


class Surface:
    """One material being built: geometry inputs, object random, a Principled box, a Bump node and the output. Subclass-free: call methods in order."""

    def __init__(self, mat, name_for_seed=None):
        self.mat = mat
        self.tree = fresh_material_tree(mat)
        self.b = Builder(self.tree, -1400, 300)
        self.seed = seed_hash(name_for_seed or mat.name)
        b = self.b
        geo = b.n('ShaderNodeNewGeometry', 'Geometry')
        self.pos = geo.outputs['Position']
        self.nrm = geo.outputs['Normal']
        info = b.n('ShaderNodeObjectInfo', 'Object')
        self.rand = info.outputs['Random']
        # per-object offset (metres) so two stones/boards never show the same part of a picture
        self.offset = b.vec((0, 0, 0))
        off = b.comb(b.math('MULTIPLY', b.math('ADD', self.rand, self.seed), 41.0),
                     b.math('MULTIPLY', b.math('ADD', self.rand, self.seed * 1.7), 29.0),
                     b.math('MULTIPLY', b.math('ADD', self.rand, self.seed * 2.3), 17.0))
        self.offset = off

    def scan(self, key, mode='tri', grain=None, scale=2.0, antitile=False, rotation=0.0, options=None, offset_mult=1.0, sharp=5.0, pos=None):
        b = self.b
        ng = scan_group(key, mode, grain, antitile, options)
        node = b.group(ng, f'scan {key}')
        b.l(pos if pos is not None else self.pos, node.inputs['Position'])
        b.l(self.nrm, node.inputs['Normal'])
        node.inputs['Scale'].default_value = scale
        node.inputs['Rotation'].default_value = rotation
        node.inputs['Sharpness'].default_value = sharp
        if offset_mult == 1.0:
            b.l(self.offset, node.inputs['Offset'])
        else:
            b.l(b.vmath('SCALE', self.offset, scale=offset_mult), node.inputs['Offset'])
        return node.outputs['Color'], node.outputs['Roughness'], node.outputs['Height']

    def normalise(self, color, key, target, contrast=0.8, options=None):
        """target * (scan / scan_mean) ^ contrast (all linear). target is a colour tuple or a socket."""
        b = self.b
        mean = scan_stats(options)[key]['mean_lin']
        rel = b.vmath('DIVIDE', color, tuple(mean))
        powd = b.vmath('POWER', rel, (contrast, contrast, contrast))
        return b.vmath('MULTIPLY', powd, target)

    def vary(self, color, amount):
        """Per-object brightness variation of +-amount (0.15 = +-15 percent) from the object's random value."""
        b = self.b
        f = b.math('ADD', b.math('MULTIPLY', b.math('SUBTRACT', self.rand, 0.5), 2.0 * amount), 1.0)
        return b.vmath('SCALE', color, scale=f)

    def finish(self, color, rough, height=None, bump=(0.3, 0.02), spec=0.5, extra_normal=None, rough_remap=None, metallic=0.0):
        """Principled + Bump + output. rough_remap = (scan_lo, scan_hi, out_lo, out_hi)."""
        b = self.b
        b.newcol(300)
        b.y = 300
        if rough_remap is not None and hasattr(rough, 'node'):
            rough = b.maprange(rough, *rough_remap)
        pr = b.n('ShaderNodeBsdfPrincipled', 'Principled BSDF')
        b.put(pr.inputs['Base Color'], color)
        b.put(pr.inputs['Roughness'], rough)
        pr.inputs['Specular IOR Level'].default_value = spec
        pr.inputs['Metallic'].default_value = metallic
        if height is not None and bump and bump[0] > 0:
            bp = b.n('ShaderNodeBump', 'Bump')
            bp.inputs['Strength'].default_value = bump[0]
            bp.inputs['Distance'].default_value = bump[1]
            b.l(height, bp.inputs['Height'])
            b.l(bp.outputs['Normal'], pr.inputs['Normal'])
        out = b.n('ShaderNodeOutputMaterial', 'Material Output')
        b.l(pr.outputs['BSDF'], out.inputs['Surface'])
        return pr
