"""GROUND builder: flowers, twigs (step 1) and the vertex-colour material they share."""
import math
import numpy as np
import bpy
from mathutils import Vector
from g6_common import hex_lin, mesh_from_arrays, add_object, PFX, N, link
from g6_tufts import Mesh, add_blade, grad, TINTS

TINTS['petal_white'] = [(0.0, hex_lin('#cfcbb6')), (1.0, hex_lin('#ebe6d2'))]
TINTS['petal_yellow'] = [(0.0, hex_lin('#c79a1a')), (1.0, hex_lin('#e2b83a'))]
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


def add_flower(m, base, rng, white=True, az=0.0):
    H = rng.uniform(0.06, 0.11)
    tip, ax = add_blade(m, base, az, H, 0.0045, rng.uniform(4, 14), rng.uniform(6, 20), kind='stalk', prof=(1.0, 0.9, 0.8))
    R = rng.uniform(0.0075, 0.0105)
    petal = 'petal_white' if white else 'petal_yellow'
    c = np.array(tip)
    # head faces up with a slight tilt
    tilt = np.array([rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 1.0])
    tilt /= np.linalg.norm(tilt)
    u = np.cross(tilt, [0, 0, 1.0])
    if np.linalg.norm(u) < 1e-3:
        u = np.array([1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(tilt, u)
    verts, cols = [c + tilt * 0.001], [grad(petal, 0.1)]
    for k in range(15):
        a = 2 * math.pi * k / 15
        rr = R * (0.72, 1.0, 0.72)[k % 3]
        verts.append(c + (u * math.cos(a) + v * math.sin(a)) * rr)
        cols.append(grad(petal, 0.9))
    faces = [(0, 1 + k, 1 + (k + 1) % 15) for k in range(15)]
    m.add(verts, faces, cols)
    eye = [c + tilt * 0.0025]
    ecols = [grad('flower_eye', 0.8)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        eye.append(c + tilt * 0.0012 + (u * math.cos(a) + v * math.sin(a)) * R * 0.32)
        ecols.append(grad('flower_eye', 0.2))
    m.add(eye, [(0, 1 + k, 1 + (k + 1) % 6) for k in range(6)], ecols)


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
