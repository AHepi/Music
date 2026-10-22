"""GROUND builder: flowers, twigs (step 1) and the vertex-colour material they share."""
import math
import numpy as np
import bpy
from mathutils import Vector
from g6_common import hex_lin, mesh_from_arrays, add_object, PFX, N, link
from g6_tufts import Mesh, add_blade, add_stalk, grad, TINTS

TINTS['petal_white'] = [(0.0, hex_lin('#d8d2b4')), (1.0, hex_lin('#f4eedc'))]
TINTS['petal_yellow'] = [(0.0, hex_lin('#cf9e16')), (1.0, hex_lin('#ecc23e'))]
TINTS['straw_lit'] = [(0.0, hex_lin('#50452a')), (1.0, hex_lin('#7a6c3c'))]
TINTS['leaf_dry'] = [(0.0, hex_lin('#33261a')), (1.0, hex_lin('#52402a'))]
TINTS['flower_eye'] = [(0.0, hex_lin('#9a6414')), (1.0, hex_lin('#b87a1c'))]
TINTS['twig'] = [(0.0, hex_lin('#4a3624')), (1.0, hex_lin('#5e4a36'))]


def vcol_material(name, rough=0.7, spec=0.25):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    ca = nt.nodes.new('ShaderNodeVertexColor')
    ca.layer_name = 'Col'
    nt.links.new(ca.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = spec
    return mat


def tuft_material(name):
    """vertex colour -> Principled, with a little translucency so blades glow when the low sun is behind them (as the old tuft material did)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.bl_idname not in ('ShaderNodeOutputMaterial',):
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    ca = nt.nodes.new('ShaderNodeVertexColor')
    ca.layer_name = 'Col'
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Roughness'].default_value = 0.58
    bs.inputs['Specular IOR Level'].default_value = 0.3
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    mx.inputs['Fac'].default_value = 0.10
    nt.links.new(ca.outputs['Color'], bs.inputs['Base Color'])
    nt.links.new(ca.outputs['Color'], tr.inputs['Color'])
    nt.links.new(bs.outputs['BSDF'], mx.inputs[1])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return mat


def add_flower(m, base, rng, white=True, az=0.0, R=None):
    """FIX ROUND: a big, simple five petal flower (head 5 to 6.5 cm across): stalk 7 to 13 cm, five round petals cupped a little, a small yellow eye.
    White flowers have a warm cream rim and a faint yellow throat; yellow ones are buttercup yellow."""
    H = rng.uniform(0.08, 0.14)
    tip, ax = add_stalk(m, base, az, H, 0.0045, rng.uniform(4, 14), rng.uniform(6, 20), kind='stalk', r1=0.8)
    R = R or rng.uniform(0.032, 0.040)
    petal = 'petal_white' if white else 'petal_yellow'
    c = np.array(tip)
    tilt = np.array([rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 1.0])
    tilt /= np.linalg.norm(tilt)
    u = np.cross(tilt, [0, 0, 1.0])
    if np.linalg.norm(u) < 1e-3:
        u = np.array([1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(tilt, u)
    a0 = rng.uniform(0, 6.28)
    arc = (-0.56, -0.30, 0.0, 0.30, 0.56)
    rad = (0.60, 0.97, 1.0, 0.97, 0.60)
    verts, cols = [c + tilt * 0.003], [grad('flower_eye', 0.9)]
    ring = []
    for k in range(5):
        for j in range(5):
            ang = a0 + 2 * math.pi * k / 5 + arc[j]
            rr = R * rad[j]
            ring.append(len(verts))
            cup = 0.0045 * (rr / R)
            verts.append(c + (u * math.cos(ang) + v * math.sin(ang)) * rr + tilt * cup)
            cols.append(grad(petal, 0.95 - (0.12 if j in (0, 4) else 0.0), 1.0 if k % 2 == 0 else 0.93))
    faces = [(0, ring[i], ring[(i + 1) % 25]) for i in range(25)]
    m.add(verts, faces, cols)
    eye = [c + tilt * 0.0052]
    ecols = [grad('flower_eye', 0.9)]
    for k in range(7):
        a = 2 * math.pi * k / 7
        eye.append(c + tilt * 0.0036 + (u * math.cos(a) + v * math.sin(a)) * R * 0.30)
        ecols.append(grad('flower_eye', 0.3))
    m.add(eye, [(0, 1 + k, 1 + (k + 1) % 7) for k in range(7)], ecols)


def add_straw(m, centre, az, length, rng, gz_fn, width=0.008):
    """FIX ROUND litter: a flat dry grass blade lying on the ground (3 rings, pale straw colour), slightly bent."""
    d = np.array([math.cos(az), math.sin(az)])
    nrm = np.array([-d[1], d[0]])
    bend = rng.uniform(-0.12, 0.12) * length
    pts = []
    for t in (-0.5, -0.17, 0.17, 0.5):
        p = np.array(centre[:2]) + d * t * length + nrm * bend * (1 - (2 * t) ** 2)
        pts.append(p)
    verts, cols = [], []
    for i, p in enumerate(pts):
        w = width * (0.55, 1.0, 1.0, 0.45)[i] * 0.5
        z = gz_fn(p[0], p[1]) + 0.004
        verts += [(p[0] - nrm[0] * w, p[1] - nrm[1] * w, gz_fn(p[0] - nrm[0] * w, p[1] - nrm[1] * w) + 0.004),
                  (p[0] + nrm[0] * w, p[1] + nrm[1] * w, gz_fn(p[0] + nrm[0] * w, p[1] + nrm[1] * w) + 0.004)]
        cols += [grad('straw_lit', 0.3 + 0.2 * i / 3, rng.uniform(0.9, 1.1))] * 2
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(3)]
    m.add(verts, faces, cols)


def add_dry_leaf(m, centre, az, R, rng, gz_fn):
    """FIX ROUND litter: a small flat brown leaf (7 vertex oval with a pointed tip), lying on the ground."""
    c = np.array(centre[:2])
    d = np.array([math.cos(az), math.sin(az)])
    nrm = np.array([-d[1], d[0]])
    outline = [(1.0, 0.0), (0.55, 0.42), (-0.1, 0.5), (-0.75, 0.25), (-1.0, 0.0), (-0.75, -0.25), (-0.1, -0.5), (0.55, -0.42)]
    verts = [(c[0], c[1], gz_fn(c[0], c[1]) + 0.005)]
    cols = [grad('leaf_dry', 0.2, rng.uniform(0.85, 1.1))]
    for (a, b) in outline:
        p = c + d * a * R + nrm * b * R
        verts.append((p[0], p[1], gz_fn(p[0], p[1]) + 0.004))
        cols.append(grad('leaf_dry', 0.8, rng.uniform(0.9, 1.1)))
    m.add(verts, [(0, 1 + k, 1 + (k + 1) % 8) for k in range(8)], cols)


def add_tube(m, pts, r0, r1, kind='twig', bright=1.0):
    n = len(pts)
    pts = [np.array(p, dtype=float) for p in pts]
    verts, cols = [], []
    for i, p in enumerate(pts):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        tmp = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(d, tmp)
        u /= np.linalg.norm(u)
        v = np.cross(d, u)
        r = r0 + (r1 - r0) * i / (n - 1)
        for k in range(4):
            a = math.pi / 2 * k + math.pi / 4
            verts.append(p + (u * math.cos(a) + v * math.sin(a)) * r)
            cols.append(grad(kind, i / (n - 1), bright))
    tipv = pts[-1] + (pts[-1] - pts[-2]) / np.linalg.norm(pts[-1] - pts[-2]) * 0.006
    verts.append(tipv)
    cols.append(grad(kind, 1.0, bright))
    faces = []
    for i in range(n - 1):
        for k in range(4):
            a0, a1 = i * 4 + k, i * 4 + (k + 1) % 4
            faces.append((a0, a1, a1 + 4, a0 + 4))
    for k in range(4):
        faces.append(((n - 1) * 4 + k, (n - 1) * 4 + (k + 1) % 4, len(verts) - 1))
    m.add(verts, faces, cols)


def add_twig(m, centre, az, length, rng, gz_fn):
    """a lying twig with a fork: one main branch (4 points) and one or two side twigs. gz_fn(x, y) gives the ground height."""
    d = np.array([math.cos(az), math.sin(az)])
    nrm = np.array([-d[1], d[0]])
    pts = []
    for i in range(4):
        t = (i / 3 - 0.5) * length
        off = nrm * rng.uniform(-0.02, 0.02) * (1 if i not in (0, 3) else 0.3)
        p = np.array(centre[:2]) + d * t + off
        pts.append([p[0], p[1], gz_fn(p[0], p[1]) + 0.007 + (0.012 if i == 3 else 0.0) + (0.0 if i else 0.002)])
    r = rng.uniform(0.0042, 0.0068)
    add_tube(m, pts, r, r * 0.45, bright=rng.uniform(0.9, 1.1))
    for _ in range(rng.integers(1, 3)):
        i0 = int(rng.integers(1, 3))
        a2 = az + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
        d2 = np.array([math.cos(a2), math.sin(a2)])
        base = np.array(pts[i0])
        bl = length * rng.uniform(0.22, 0.38)
        side = []
        for j in range(3):
            p = base[:2] + d2 * bl * j / 2
            side.append([p[0], p[1], gz_fn(p[0], p[1]) + 0.007 + 0.008 * j])
        add_tube(m, side, r * 0.7, r * 0.3, bright=rng.uniform(0.9, 1.1))
