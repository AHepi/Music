"""GROUND builder, step 6 (small): the dark hedge blobs ('Life / shrubs', 'Fix / far hedge') stay dark rounded blobs with no leaf texture; each blob gets one of
three slightly different greens (a vertex colour per blob multiplies the material's colour by 0.90 to 1.08)."""
import numpy as np
import bpy
from g6_common import N, link, unlink_input
import g6_moss

TONES = [(0.90, 0.98, 0.95), (1.0, 1.0, 1.0), (1.07, 1.05, 0.92)]


def step6(ctx):
    rep = ctx['rep']
    rr = np.random.default_rng(ctx['o']['seed'] + 61)
    n_blobs = 0
    for name in ('Life / shrubs', 'Fix / far hedge'):
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        me = ob.data
        n = len(me.vertices)
        parent = list(range(n))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        for e in me.edges:
            a, b = find(e.vertices[0]), find(e.vertices[1])
            if a != b:
                parent[a] = b
        roots = np.array([find(i) for i in range(n)])
        cols = np.ones((n, 4), dtype=np.float32)
        for r in np.unique(roots):
            t = TONES[int(rr.integers(0, 3))]
            j = rr.uniform(0.97, 1.03)
            cols[roots == r, :3] = [t[0] * j, t[1] * j, t[2] * j]
            n_blobs += 1
        if me.color_attributes.get('Col') is None:
            ob['gnd_col_added'] = 1
        g6_moss.set_corner_colour_from_vertex(me, cols)
    mat = bpy.data.materials.get('Life / shrub')
    if mat is not None:
        nt = mat.node_tree
        bsdf = nt.nodes['Principled BSDF']
        src = [l for l in nt.links if l.to_node == bsdf and l.to_socket.name == 'Base Color']
        if src:
            from_sock = src[0].from_socket
            unlink_input(mat, 'Principled BSDF', 'Base Color')
            vc = N(nt, 'ShaderNodeVertexColor', 'hedge tone', (-300, 200))
            vc.layer_name = 'Col'
            mx = N(nt, 'ShaderNodeMix', 'hedge tone mul', (-100, 200))
            mx.data_type = 'RGBA'
            mx.blend_type = 'MULTIPLY'
            mx.inputs[0].default_value = 1.0
            link(nt, from_sock, mx, 6)
            link(nt, vc, 'Color', mx, 7)
            link(nt, next(o for o in mx.outputs if o.enabled), bsdf, 'Base Color')
    rep['hedge'] = dict(blobs=n_blobs, tones=3)
