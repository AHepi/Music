"""wood_deck.py - step 4: the veranda deck (boards on joists with butt joints, nosing, heads), the lowered stone plinth strip, maple leaves.
Deck facts of the starting scene: top z 0.56, x -5.25 .. 5.65, boards across y 4.6 .. 6.4 run along x. Plinth front face y 4.7, hall floor behind at z 0.55.
"""
import math
import numpy as np
import bpy
from wood_geo import (build_plank, plank_top_z, peg_mesh, leaf_mesh, prism, rect_poly, box_uv_for_faces, MeshData, perp, unit)

DECK_X0, DECK_X1 = -5.25, 5.65   # first / last board end 5 cm beyond the first / last joist
DECK_Y_FRONT, DECK_Y_BACK = 4.665, 6.40
DECK_TOP = 0.56
PLINTH_FRONT_Z = 0.46
JOIST_X0, JOIST_DX, N_JOIST = -5.20, 0.60, 19
JOIST_TOP = 0.505
ROWS = 14


def _row_joints(rng, prev):
    """indices of the joists where a row has butt joints (strictly inside 0..18), not shared with the previous row."""
    for _ in range(400):
        j, seq = 0, []
        first = int(rng.choice([2, 3]))
        j = first
        seq.append(j)
        while True:
            left = (N_JOIST - 1) - j
            if left in (2, 3):
                break
            if left < 2:
                seq = None
                break
            step = int(rng.choice([2, 3, 4], p=[0.3, 0.4, 0.3]))
            if left - step in (1,) or left - step < 0:
                continue
            j += step
            seq.append(j)
        if seq is None:
            continue
        if prev is not None and set(seq) & set(prev):
            continue
        return seq
    return [3, 6, 10, 13]


def deck_layout(rng):
    # row widths: 14 rows between the nosing line and the back, gaps 4.5 to 8 mm
    gaps = rng.uniform(0.0055, 0.0095, ROWS - 1)
    w = rng.uniform(0.106, 0.138, ROWS)
    avail = (DECK_Y_BACK - DECK_Y_FRONT) - gaps.sum()
    w = w * (avail / w.sum())
    rows = []
    y = DECK_Y_FRONT
    prev = None
    for r in range(ROWS):
        joints = _row_joints(rng, prev)
        prev = joints
        # boards between consecutive joints
        edges = [-1] + joints + [N_JOIST]          # -1 and 19 stand for the run ends
        boards = []
        for a, b in zip(edges[:-1], edges[1:]):
            xa = DECK_X0 if a == -1 else JOIST_X0 + JOIST_DX * a + 0.002
            xb = DECK_X1 if b == N_JOIST else JOIST_X0 + JOIST_DX * b - 0.002
            boards.append((xa, xb))
        rows.append(dict(y0=y, w=float(w[r]), boards=boards, joints=joints))
        y += float(w[r]) + (float(gaps[r]) if r < ROWS - 1 else 0.0)
    return rows


def build_deck(ctx, seed, options, stage):
    rng = np.random.default_rng(seed + 100)
    coll, rep = ctx['coll'], ctx['rep']
    P3 = ctx['deck3']

    def damp_fn(x, y, z):
        v = 0.12
        v += 0.26 * math.exp(-((y - DECK_Y_FRONT) / 0.08) ** 2)              # outer edge seams
        v += 0.2 * math.exp(-((x - DECK_X0) / 0.35) ** 2) + 0.2 * math.exp(-((x - DECK_X1) / 0.35) ** 2)
        v += 0.12 * math.exp(-(((x - 2.2) / 1.0) ** 2 + ((y - 4.8) / 0.4) ** 2))
        return float(min(max(v, 0.0), 1.0))

    def wear_fn(x, y, z):
        band = 1.0 / (1.0 + math.exp(-(y - 5.55) / 0.12))                     # worn band in front of the shoji (back 0.85 m)
        steps = math.exp(-(((x - 2.2) / 0.95) ** 2 + ((y - 5.0) / 0.5) ** 2))
        return float(min(1.0, band + steps))

    objs = {n: MeshData() for n in ('Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002')}
    rows = deck_layout(rng)
    pegs = MeshData()
    n_boards = 0
    lens = []
    thick_all = []
    parts = []
    deck_specs = []
    pid = 0
    tone_row_bias = rng.uniform(0, 1, ROWS)
    for ri, row in enumerate(rows):
        yc = row['y0'] + row['w'] / 2
        for bi, (xa, xb) in enumerate(row['boards']):
            L = xb - xa
            T = float(rng.uniform(0.049, 0.060))
            # tones: mostly warm, a few silvered boards
            tone = float(rng.choice([rng.uniform(0.0, 0.35), rng.uniform(0.55, 0.95)], p=[0.3, 0.7]))
            nosing = ri == 0
            spec = dict(O=(xa, yc), ax=(1.0, 0.0), zb=DECK_TOP - T - 0.001, L=L, w=row['w'], T=T,
                        r=0.012 if nosing else float(rng.uniform(0.007, 0.011)), b=0.003,
                        bow=float(rng.uniform(0.0015, 0.0028)), cup=float(rng.choice([-1, 1]) * rng.uniform(0.0005, 0.002)),
                        twist_deg=float(rng.choice([-1, 1]) * rng.uniform(0.5, 1.1)), sweep=float(rng.uniform(-0.002, 0.002)),
                        dish=float(rng.uniform(0.0008, 0.0015)), dish_x=L / 2, n_top=4,
                        uvoff=(float(rng.uniform(0, 1)), float(rng.uniform(0, 0.25))),
                        attrs=dict(plank_id=float(rng.random()), plank_tone=tone), damp_fn=damp_fn, wear_fn=wear_fn)
            if rng.random() < 0.12:
                end = int(rng.integers(0, 2))
                spec['chip'] = dict(end=end, side=int(rng.choice([-1, 1])), cx=float(rng.uniform(0.03, 0.06)), cy=float(rng.uniform(0.03, 0.045)),
                                    depth=float(rng.uniform(0.014, 0.022)))
            if rng.random() < 0.18:
                end = int(rng.integers(0, 2))
                if spec.get('chip') is None or spec['chip']['end'] != end:
                    spec['check'] = dict(end=end, y=float(rng.choice([-0.026, 0.026])), length=float(rng.uniform(0.05, 0.12)),
                                         width=float(rng.uniform(0.002, 0.003)), depth=0.003)
            W, F, Mt, uv, at, V2 = build_plank(spec)
            deck_specs.append(dict(spec, row=ri, xa=xa, xb=xb))
            xc = 0.5 * (xa + xb)
            key = 'Astra / varied planks' if xc < -1.62 else ('Astra / varied planks.001' if xc < 2.02 else 'Astra / varied planks.002')
            objs[key].add_part(W, F, Mt, uv, at, pid)
            parts.append(dict(id=pid, kind='board', row=ri, xa=xa, xb=xb, L=L, w=row['w'], T=T, n=len(W), tone=tone))
            pid += 1
            n_boards += 1
            lens.append(L)
            thick_all.append(T)
            # heads: at the butt joint ends (one per board end, offset from the joist centre) and now and then over a middle joist
            def head(xh, yh):
                top = plank_top_z(spec, xh - xa, yh - yc)
                nail = rng.random() < 0.6
                if nail:
                    V, Fh = peg_mesh(np.array([xh, yh, top]), (0, 0, 1), r=0.0048, proud=0.0028, sink=0.0015, n=10)
                else:
                    V, Fh = peg_mesh(np.array([xh, yh, top]), (0, 0, 1), r=0.0068, proud=0.0058, sink=0.002, n=12)
                pegs.add_part(V, Fh, [1 if nail else 0] * len(Fh), [[(0.0, 0.0)] * len(f) for f in Fh], {}, pid)
            for jx_i in range(N_JOIST):
                jx = JOIST_X0 + JOIST_DX * jx_i
                if xa + 0.03 < jx < xb - 0.03:
                    at_end = (abs(jx - xa) < 0.12) or (abs(jx - xb) < 0.12)
                    if at_end and rng.random() < 0.85:
                        head(jx + (0.0), yc + float(rng.uniform(-0.012, 0.012)))
                    elif (not at_end) and rng.random() < 0.18:
                        head(jx, yc + float(rng.uniform(-0.012, 0.012)))
                elif abs(jx - xa) <= 0.03 or abs(jx - xb) <= 0.03:
                    pass
    # --- write the three deck runs
    for name, md in objs.items():
        o, created = stage.put_object(name, md, P3, 'timber.deck', coll)
        (rep['created'] if created else rep['changed']).append(name)
    # --- joists
    jm = MeshData()
    for ji in range(N_JOIST):
        jx = JOIST_X0 + JOIST_DX * ji
        poly = rect_poly(jx, 0.5 * (4.72 + 6.38), 0.0, 1.0, 0.5 * (6.38 - 4.72), 0.04)
        V, F = prism(poly, PLINTH_FRONT_Z, JOIST_TOP, ch=0.004, cb=0.0)
        uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
        jm.add_part(V, F, [0] * len(F), uv, {'damp': 0.5, 'plank_id': float(rng.random())}, 1000 + ji)
    o, created = stage.put_object('G6 wood / deck joists', jm, [ctx['mat_post']], 'timber.frame', coll)
    (rep['created'] if created else rep['changed']).append(o.name)
    # --- heads
    o, created = stage.put_object('G6 wood / deck pegs', pegs, [ctx['mat_peg'], ctx['mat_nail']], 'timber.deck', coll)
    (rep['created'] if created else rep['changed']).append(o.name)
    # --- plinth: front strip (y 4.7 .. 6.4) lowered to z 0.46, hall floor strip behind stays at 0.55
    pl = bpy.data.objects['Stone plinth']
    stage.original_mesh(pl)
    md = MeshData()
    for (y0, y1, ztop) in ((4.70, 6.40, PLINTH_FRONT_Z), (6.40, 10.30, 0.55)):
        poly = rect_poly(0.5 * (-5.26 + 5.66), 0.5 * (y0 + y1), 1.0, 0.0, 0.5 * (5.66 + 5.26), 0.5 * (y1 - y0))
        V, F = prism(poly, -0.04, ztop, ch=0.0, cb=0.0)
        uv = box_uv_for_faces(V, F, 1.0, (0.0, 0.0))
        md.add_part(V, F, [0] * len(F), uv, {}, 0)
    stage.write_mesh(pl.data, md, world_obj=pl, smooth=False)
    pl.data.materials.clear()
    pl.data.materials.append(bpy.data.materials['Plinth stone'])
    pl['garden_owner'] = 'wood'
    rep['changed'].append('Stone plinth')
    # --- leaves on the deck
    leaves = []
    lm = make_leaf_material()
    spots = [(-4.2, 5.2), (-2.6, 4.85), (-0.6, 5.55), (1.3, 5.0), (3.4, 5.35), (4.7, 5.0)]
    for i, (lx, ly) in enumerate(spots):
        lx += float(rng.uniform(-0.25, 0.25)); ly += float(rng.uniform(-0.1, 0.1))
        V, F = leaf_mesh((lx, ly, DECK_TOP + 0.003), float(rng.uniform(0, 6.28)), float(rng.uniform(0.04, 0.062)), curl=0.012, seed=i)
        md = MeshData()
        md.add_part(V, F, [0] * len(F), [[(0.0, 0.0)] * len(f) for f in F], {}, 0)
        o, created = stage.put_object('G6 wood / deck leaf %d' % (i + 1), md, [lm], 'leaf', coll)
        rep['created'].append(o.name)
    ctx['deck_parts'] = parts
    ctx['deck_specs'] = deck_specs
    ctx['deck_rows'] = rows
    rep['deck'] = dict(boards=n_boards, rows=ROWS, len_min=round(min(lens), 2), len_max=round(max(lens), 2),
                       thick_min=round(min(thick_all), 4), thick_max=round(max(thick_all), 4), vertices=sum(len(o.data.vertices) for o in
                       [bpy.data.objects[n] for n in objs]))
    # --- the lower step etc.
    return rep


def make_leaf_material(name='G6 wood / deck leaf'):
    import wood_mats as wm
    m = bpy.data.materials.new(name)
    nb = wm.NB(m)
    oi = nb.n('ShaderNodeObjectInfo', loc=(0, 0))
    ramp = nb.n('ShaderNodeValToRGB', loc=(250, 0))
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = wm.lin('#9a3a12')
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = wm.lin('#b86a1c')
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = wm.lin('#ad4a14')
    nb.link(oi, 'Random', ramp, 'Fac')
    bsdf = nb.n('ShaderNodeBsdfPrincipled', loc=(600, 0))
    bsdf.inputs['Roughness'].default_value = 0.7
    bsdf.inputs['Specular IOR Level'].default_value = 0.2
    nb.nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    out = nb.n('ShaderNodeOutputMaterial', loc=(900, 0))
    nb.nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    m['garden_owner'] = 'wood'
    return m
