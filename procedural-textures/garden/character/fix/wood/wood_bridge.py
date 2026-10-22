"""wood_bridge.py - layout and meshes of the rebuilt zigzag bridge (pure numpy, world metres).
Stack from the bottom: footing stones on the pond bed -> square posts in pairs -> bearers (cross beams) between the post pair ->
two stringers (rails) per arm (a third, short one under the last metre before each turn) -> planks across -> pegs, iron cramps.
At each turn the two arms meet on a MITRE line through the node; a diagonal breaker board lies on it; arm planks are cut to the mitre.
"""
import math
import numpy as np
from wood_geo import (unit, perp, prism, octagon, rect_poly, convex_hull, build_plank, plank_top_z, peg_mesh, leaf_mesh,
                      box_uv_for_faces, fix_winding, MeshData, rot2)

NODES = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]     # N3 west bank, N2, N1, N0 east bank
RAIL_U = 0.42            # stringer centre line, metres either side of the arm axis
RAIL_W, Z_R0, Z_R1 = 0.08, 0.04, 0.16
BEAR_L, BEAR_W, BEAR_H = 1.14, 0.12, 0.10
POST = 0.14
POST_OFF = 0.62
MITRE_CLEAR = 0.093       # offset of the cut line from the mitre centre line (breaker half width 0.08 + gap)
BANK_OVER = 0.275         # deck runs this far past the bank node on the ground
DECK_REF = 0.22
SILL_TOP = 0.10
FOOT_TOP = -0.098         # footing stone tops: 2 cm above the water (water z -0.12)


def make_arms():
    arms = []
    P = [np.array(n, float) for n in NODES]
    for k in range(3):
        A, B = P[k], P[k + 1]
        d = unit(B - A)
        arms.append(dict(k=k, A=A, B=B, d=d, n=perp(d), L=float(np.linalg.norm(B - A))))
    mit = {}
    for node in (1, 2):
        din, dout = arms[node - 1]['d'], arms[node]['d']
        b = unit(din + dout)
        mit[node] = dict(P=P[node], b=b, m=perp(b), half_turn=math.acos(float(np.clip(np.dot(din, b), -1, 1))))
    arms[0].update(start='bank', end='mitre', node_end=1)
    arms[1].update(start='mitre', end='mitre', node_start=1, node_end=2)
    arms[2].update(start='mitre', end='bank', node_start=2)
    return arms, mit


def _constraint_interval(arm, mit, s, c=MITRE_CLEAR):
    """valid u-interval (lo, hi) of the arm's ribbon at axis position s (clipped by the mitre half-planes)."""
    lo, hi = -9.0, 9.0
    n, d, A = arm['n'], arm['d'], arm['A']
    if arm['start'] == 'mitre':
        M = mit[arm['node_start']]
        k0 = float(np.dot(A - M['P'], M['b'])) + s * float(np.dot(d, M['b']))
        k1 = float(np.dot(n, M['b']))             # need k0 + u*k1 >= c
        lim = (c - k0) / k1
        lo, hi = (max(lo, lim), hi) if k1 > 0 else (lo, min(hi, lim))
    if arm['end'] == 'mitre':
        M = mit[arm['node_end']]
        k0 = float(np.dot(A - M['P'], M['b'])) + s * float(np.dot(d, M['b']))
        k1 = float(np.dot(n, M['b']))             # need k0 + u*k1 <= -c
        lim = (-c - k0) / k1
        lo, hi = (lo, min(hi, lim)) if k1 > 0 else (max(lo, lim), hi)
    return lo, hi


def route_dist_fn():
    P = [np.array(n, float) for n in NODES]
    segs = [(P[i], P[i + 1]) for i in range(3)]

    def f(x, y):
        p = np.array([x, y])
        best = 9.0
        for a, b in segs:
            ab = b - a
            t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
            best = min(best, float(np.linalg.norm(p - (a + t * ab))))
        return best
    return f


def layout(seed=7, bed_fn=None, rocks=None):
    rng = np.random.default_rng(seed)
    arms, mit = make_arms()
    bed_fn = bed_fn or (lambda x, y: -0.44)
    planks = []          # dicts: spec + meta
    pid = 0
    thick = 0.057
    for arm in arms:
        d, n, A, L = arm['d'], arm['n'], arm['A'], arm['L']

        def holds_centre(sv):
            lo, hi = _constraint_interval(arm, mit, sv)
            return lo <= -0.025 and hi >= 0.025
        if arm['start'] == 'bank':
            s_lo = -BANK_OVER
        else:
            sv = 0.0
            while not holds_centre(sv):
                sv += 0.001
            s_lo = sv
        if arm['end'] == 'bank':
            s_hi = L + BANK_OVER
        else:
            sv = L
            while not holds_centre(sv):
                sv -= 0.001
            s_hi = sv
        span = s_hi - s_lo
        for attempt in range(300):
            nn = int(round(span / 0.1385)) + int(rng.integers(-1, 2))
            w = rng.uniform(0.095, 0.158, nn)
            gaps = rng.uniform(0.0075, 0.014, nn - 1)
            k = (span - gaps.sum()) / w.sum()
            w = w * k
            if w.min() >= 0.09 and w.max() <= 0.17:
                break
        s = s_lo
        count = 0
        for i in range(nn):
            ovl, ovr = float(rng.uniform(0.088, 0.12)), float(rng.uniform(0.088, 0.12))
            Hl, Hr = RAIL_U + ovl, RAIL_U + ovr
            wi = float(w[i])
            sc = s + wi / 2
            iv = [_constraint_interval(arm, mit, s), _constraint_interval(arm, mit, s + wi)]
            (lon, hin), (lof, hif) = iv
            x0n, x1n = Hl - min(Hl, hin), Hl - max(-Hr, lon)
            x0f, x1f = Hl - min(Hl, hif), Hl - max(-Hr, lof)
            Lp = Hl + Hr
            thick = float(np.clip(thick + rng.normal(0, 0.0035), 0.047, 0.062))
            replaced = rng.random() < 0.085
            planks.append(dict(arm=arm['k'], id=pid, s=s, w=wi, sc=sc, Hl=Hl, Hr=Hr, L=Lp, clip=(x0n, x0f, x1n, x1f),
                               T=thick + (0.004 if replaced else 0.0), replaced=replaced, kind='arm'))
            pid += 1
            count += 1
            s += wi + (float(gaps[i]) if i < nn - 1 else 0.0)
        # FIX ROUND (wood): offcut planks that close the OUTER corner of each mitre. The main run above stops where the centre line meets the mitre line;
        # on the outer side the ribbon goes on for about 0.3 m more, so two short, obliquely cut planks follow on that side (like a real mitred deck).
        for end in ('end', 'start'):
            if arm[end] != 'mitre':
                continue
            s_cur = s_hi if end == 'end' else s_lo
            for _k in range(5):
                wi = float(rng.uniform(0.105, 0.15))
                gp = float(rng.uniform(0.0075, 0.012))
                s_new = s_cur + gp if end == 'end' else s_cur - gp - wi
                ovl, ovr = float(rng.uniform(0.088, 0.12)), float(rng.uniform(0.088, 0.12))
                Hl, Hr = RAIL_U + ovl, RAIL_U + ovr
                (lon, hin), (lof, hif) = _constraint_interval(arm, mit, s_new), _constraint_interval(arm, mit, s_new + wi)
                x0n, x1n = Hl - min(Hl, hin), Hl - max(-Hr, lon)
                x0f, x1f = Hl - min(Hl, hif), Hl - max(-Hr, lof)
                ln, lf = x1n - x0n, x1f - x0f
                if min(ln, lf) < 0.05:
                    break
                thick = float(np.clip(thick + rng.normal(0, 0.0035), 0.047, 0.062))
                planks.append(dict(arm=arm['k'], id=pid, s=s_new, w=wi, sc=s_new + wi / 2, Hl=Hl, Hr=Hr, L=Hl + Hr, clip=(x0n, x0f, x1n, x1f),
                                   T=thick, replaced=False, kind='arm', offcut=True))
                pid += 1
                count += 1
                s_cur = s_new + wi if end == 'end' else s_new
        arm['n_planks'] = count
        arm['s_lo'], arm['s_hi'] = s_lo, s_hi
    # breaker boards on the mitres
    for node, M in mit.items():
        planks.append(dict(arm=-1, id=pid, node=node, w=0.16, L=round(max(1.20, 1.05 / math.cos(M['half_turn']) + 0.04), 3), T=0.062, replaced=False, kind='breaker', M=M))
        pid += 1
    # ---------------- planks to specs (warps, wear marks)
    route = route_dist_fn()
    rock_pts = rocks or []
    # posts first (needed for the damp function)
    sup = supports(arms, mit, bed_fn)
    post_xy = np.array([p['xy'] for p in sup['posts']])

    def damp_fn(x, y, z):
        dpost = float(np.min(np.hypot(post_xy[:, 0] - x, post_xy[:, 1] - y)))
        v = 0.10 + 0.50 * max(0.0, 1 - dpost / 0.62)
        dr = route(x, y)
        v += 0.16 * max(0.0, (dr - 0.33) / 0.2)                 # the outer edge of the deck stays a little damper
        for rx, ry, rr in rock_pts:
            v += 0.35 * max(0.0, 1 - (math.hypot(x - rx, y - ry) - rr) / 0.9)
        v *= 1.0 - 0.6 * math.exp(-(dr / 0.2) ** 2)             # less on the walking line
        return float(np.clip(v, 0.0, 1.0))

    def wear_fn(x, y, z):
        return float(math.exp(-(route(x, y) / 0.2) ** 2))

    for p in planks:
        r = rng
        replaced = p['replaced']
        if p['kind'] == 'breaker':
            M = p['M']
            ax = M['m']
            O = M['P'] - ax * p['L'] / 2 + (-M['b']) * 0.0
            # Y axis = perp(ax) = -b ; centre the breaker on the mitre line: shift O by +b*0 (Y in [-w/2, w/2])
            p.update(O=O, ax=ax, ay=perp(ax), Hl=p['L'] / 2, Hr=p['L'] / 2, clip=None, dish_x=p['L'] / 2)
        else:
            arm = arms[p['arm']]
            O = arm['A'] + arm['d'] * p['sc'] + arm['n'] * p['Hl']
            yaw = math.radians(float(r.uniform(-0.1, 0.1)))
            ax = rot2(-arm['n'], yaw)
            p.update(O=O, ax=ax, ay=perp(ax), dish_x=p['Hl'])
        T = p['T']
        p['spec'] = dict(
            O=p['O'], ax=p['ax'], zb=Z_R1, L=p['L'], w=p['w'], T=T,
            r=float(r.uniform(0.006, 0.012)) if not replaced else 0.006, b=0.003,
            bow=float(r.uniform(0.002, 0.006)) if not replaced else 0.0005,
            cup=float(r.choice([-1, 1]) * r.uniform(0.001, 0.004)) if not replaced else 0.0,
            twist_deg=float(r.choice([-1, 1]) * r.uniform(0.35, 1.5)) if not replaced else 0.0,
            sweep=float(r.uniform(-0.002, 0.002)),
            dish=float(r.uniform(0.001, 0.002)) if not replaced else 0.0, dish_x=p['dish_x'],
            clip=p['clip'], n_top=5, uvoff=(float(r.uniform(0, 2.0)), float(r.uniform(0, 0.5))),
            attrs=dict(plank_id=float(r.random()), plank_tone=1.0 if replaced else float(r.uniform(0.0, 0.3))),
            damp_fn=damp_fn, wear_fn=wear_fn)
        sp = p['spec']
        # marks
        full_ends = p['kind'] == 'arm'
        if full_ends and r.random() < 0.11 and not replaced:
            end = int(r.integers(0, 2)); side = int(r.choice([-1, 1]))
            sp['chip'] = dict(end=end, side=side, cx=float(r.uniform(0.032, 0.06)), cy=float(r.uniform(0.03, 0.05)), depth=float(r.uniform(0.016, 0.026)))
        if r.random() < 0.19 and not replaced:
            end = int(r.integers(0, 2))
            if sp.get('chip') is None or sp['chip']['end'] != end:
                yc = float(r.choice([-0.4, -0.14, 0.14, 0.4]) * p['w'] * 0.5 * 2 / 2 * 1.0) * 0.8
                sp['check'] = dict(end=end, y=yc, length=float(r.uniform(0.05, 0.12)), width=float(r.uniform(0.002, 0.003)), depth=0.003)
        if p['kind'] == 'arm' and not replaced and p['w'] < 0.12:
            pass
    return dict(arms=arms, mit=mit, planks=planks, sup=sup, rng=rng, bed_fn=bed_fn, damp_fn=damp_fn, wear_fn=wear_fn, route=route)


# ---------------------------------------------------------------- supports: bearers, posts, rails
def _rail_end_s(arm, mit, u, end):
    """axis position s where the rail line at lateral offset u meets the mitre centre line (or the bank end)."""
    d, n, A, L = arm['d'], arm['n'], arm['A'], arm['L']
    if end == 'start':
        if arm['start'] == 'bank':
            return 0.0
        M = mit[arm['node_start']]
        k0 = float(np.dot(A - M['P'], M['b'])); k1 = float(np.dot(n, M['b'])); kd = float(np.dot(d, M['b']))
        return -(k0 + u * k1) / kd
    if arm['end'] == 'bank':
        return L
    M = mit[arm['node_end']]
    k0 = float(np.dot(A - M['P'], M['b'])); k1 = float(np.dot(n, M['b'])); kd = float(np.dot(d, M['b']))
    return -(k0 + u * k1) / kd


def supports(arms, mit, bed_fn=None, max_span=1.38):
    bed_fn = bed_fn or (lambda x, y: -0.44)
    bearers, posts, rails = [], [], []
    for arm in arms:
        d, n, A, L = arm['d'], arm['n'], arm['A'], arm['L']
        ends = {}
        for u in (+RAIL_U, -RAIL_U):
            ends[u] = (_rail_end_s(arm, mit, u, 'start'), _rail_end_s(arm, mit, u, 'end'))
        s_lo = 0.5 * sum(e[0] for e in ends.values())
        s_hi = 0.5 * sum(e[1] for e in ends.values())
        n_int = 0
        while True:
            pos = [s_lo + (s_hi - s_lo) * (i + 1) / (n_int + 1) for i in range(n_int)]
            # keep every post of a pair off dry land: move a line along the arm until both posts stand at z <= -0.05
            for pi_, sv in enumerate(pos):
                for off in (0.0, -0.1, 0.1, -0.2, 0.2, -0.3, 0.3, -0.4, 0.4, -0.5, 0.5, -0.6, 0.6):
                    c = A + d * (sv + off)
                    if max(bed_fn(*(c + n * 0.62)), bed_fn(*(c - n * 0.62))) <= -0.05:
                        pos[pi_] = sv + off
                        break
            pos = sorted(pos)
            ok = True
            for u, (a, b) in ends.items():
                pts = [a] + pos + [b]
                if max(np.diff(pts)) > max_span:
                    ok = False
            if ok:
                break
            n_int += 1
        arm['interior_s'] = pos
        arm['rail_ends'] = ends
        for s in pos:
            c = A + d * s
            bearers.append(dict(c=c, ax=n, kind='mid', arm=arm['k'], s=s))
    for node, M in mit.items():
        bearers.append(dict(c=M['P'], ax=M['m'], kind='node', node=node))
    # posts: a pair at every bearer; the 2 banks have posts on the sills
    pl = []
    for b in bearers:
        for sgn in (+1, -1):
            xy = b['c'] + b['ax'] * sgn * POST_OFF
            pl.append(dict(xy=xy, kind='bollard' if b['kind'] == 'node' else 'mid', bearer=b, side=sgn))
    for arm, (end_pt, tag) in ((arms[0], (arms[0]['A'], 'bank0')), (arms[2], (arms[2]['B'], 'bank3'))):
        for sgn in (+1, -1):
            xy = end_pt + arm['n'] * sgn * POST_OFF
            pl.append(dict(xy=xy, kind='bank', bearer=None, side=sgn, tag=tag, arm=arm['k']))
    return dict(bearers=bearers, posts=pl)


# ---------------------------------------------------------------- meshes
def mesh_from_prism(V, F, mat, tile=1.0, part=0, attrs=None, uvoff=(0.0, 0.0)):
    uv = box_uv_for_faces(V, F, tile, uvoff)
    return V, F, [mat] * len(F), uv


def build_meshes(L, rng=None, opts=None):
    """Returns a dict of MeshData objects and a parts registry (for tests)."""
    opts = opts or {}
    rng = rng or L['rng']
    arms, mit, planks, sup, bed = L['arms'], L['mit'], L['planks'], L['sup'], L['bed_fn']
    out = {k: MeshData() for k in ('planks_arm0', 'planks_arm1', 'planks_arm2', 'planks_n1', 'planks_n2', 'stringers',
                                    'bearers', 'posts', 'footings', 'sill0', 'sill3', 'footing_n1', 'footing_n2', 'pegs', 'cramps', 'leaves')}
    parts = []
    pid = 0

    def reg(kind, V, **kw):
        nonlocal pid
        V = np.asarray(V)
        parts.append(dict(id=pid, kind=kind, bmin=V.min(0).tolist(), bmax=V.max(0).tolist(), **kw))
        pid += 1
        return pid - 1

    # ---- planks
    plank_meshes = {}
    for p in planks:
        W, F, Mt, uv, at, V2 = build_plank(p['spec'])
        key = 'planks_arm%d' % p['arm'] if p['kind'] == 'arm' else ('planks_n%d' % p['node'])
        if p['kind'] == 'arm' and p['clip'] is not None:
            x0n, x0f, x1n, x1f = p['clip']
            if min(x0n, x0f) > 0.02 or max(x1n, x1f) < p['L'] - 0.02:
                node = None
        i = reg('plank' if p['kind'] == 'arm' else 'breaker', W, plank=p['id'], arm=p['arm'], T=p['T'], w=p['w'], L=p['L'],
                replaced=p['replaced'], n=len(W))
        out[key].add_part(W, F, Mt, uv, at, i)
        p['obj'] = key
        p['part'] = i
    # ---- bearers + posts (+footings)
    foot_polys = []
    post_info = []
    for b in sup['bearers']:
        c, ax = b['c'], b['ax']
        poly = rect_poly(c[0], c[1], ax[0], ax[1], BEAR_L / 2, BEAR_W / 2)
        V, F = prism(poly, Z_R0 - BEAR_H, Z_R0, ch=0.006)
        uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
        i = reg('bearer', V, kind2=b['kind'])
        out['bearers'].add_part(V, F, [0] * len(F), uv, {'damp': 0.3, 'plank_id': float(rng.random())}, i)
    for p in sup['posts']:
        xy = p['xy']
        bank = p['kind'] == 'bank'
        bz = bed(xy[0], xy[1])
        if bank:
            z0 = SILL_TOP
        else:
            if bz > -0.12:                       # shore: a flat stone buried to its top face
                ftop, fbot = bz + 0.012, bz - 0.09
            else:
                ftop = FOOT_TOP + float(rng.uniform(-0.012, 0.010))        # FIX ROUND: the stone top stands just out of the water, so it reads
                ftop = max(ftop, bz + 0.105)
                fbot = bz - 0.005
            rad = float(rng.uniform(0.20, 0.265))
            ang = float(rng.uniform(0, math.pi))
            pts = []
            for k in range(9):
                a = 2 * math.pi * k / 9 + float(rng.uniform(-0.15, 0.15))
                rr = rad * float(rng.uniform(0.9, 1.05))
                pts.append((xy[0] + rr * 1.05 * math.cos(a + ang), xy[1] + rr * 0.9 * math.sin(a + ang)))
            hull = convex_hull(pts)
            V, F = prism(hull, fbot, ftop, ch=0.022 if ftop - fbot > 0.11 else 0.015, cb=0.008)
            uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
            fid = reg('footing', V, thick=ftop - fbot, w=rad * 2)
            p['footing'] = fid
            p['ftop'] = ftop
            tgt = 'footing_n1' if (p['kind'] == 'bollard' and p['bearer'].get('node') == 2 and p['side'] > 0) else \
                  ('footing_n2' if (p['kind'] == 'bollard' and p['bearer'].get('node') == 1 and p['side'] > 0) else 'footings')
            # node indices: mitre node 1 is N2 (landing between arm0/arm1), node 2 is N1 -> piers: 'Bridge pier 2' at N2, 'Bridge pier 1' at N1
            out[tgt].add_part(V, F, [0] * len(F), uv, {'damp': 1.0}, fid)
            z0 = ftop
        if p['kind'] == 'bollard':
            ztop = 0.345 + float(rng.uniform(-0.03, 0.03))
        elif p['kind'] == 'bank':
            ztop = 0.335 + float(rng.uniform(-0.025, 0.025))
        else:
            ztop = DECK_REF - float(rng.uniform(0.03, 0.05))
        tilt = math.radians(float(rng.uniform(0.0, 0.8)))
        ta = float(rng.uniform(0, 2 * math.pi))
        shear = (math.tan(tilt) * math.cos(ta), math.tan(tilt) * math.sin(ta))
        poly = octagon(xy[0], xy[1], POST / 2, 0.015, yaw=float(rng.uniform(-0.04, 0.04)))
        V, F = prism(poly, z0, ztop, ch=0.006, cb=0.003, shear=shear)
        uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
        i = reg('post', V, kind2=p['kind'], base=z0, top=ztop)
        p['part'] = i
        p['z0'], p['ztop'], p['shear'] = z0, ztop, shear
        out['posts'].add_part(V, F, [0] * len(F), uv, {'damp': 1.0, 'plank_id': float(rng.random())}, i)
    # ---- sills (bank piers)
    for tag, arm, endpt, key in (('sill0', arms[0], arms[0]['A'], 'sill0'), ('sill3', arms[2], arms[2]['B'], 'sill3')):
        d, n = arm['d'], arm['n']
        poly = rect_poly(endpt[0] + d[0] * (0.0 if tag == 'sill0' else 0.0), endpt[1], n[0], n[1], 0.72, 0.25)
        # rotate: long axis along n, depth along d
        poly = rect_poly(endpt[0], endpt[1], n[0], n[1], 0.72, 0.25)
        ground = bed(endpt[0], endpt[1])
        V, F = prism(poly, min(ground, 0.0) - 0.25, SILL_TOP, ch=0.025, cb=0.01)
        uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
        i = reg('sill', V, tag=tag)
        out[key].add_part(V, F, [0] * len(F), uv, {'damp': 0.8}, i)
        arm[tag] = i
    # ---- rails (stringers): two per arm, ends cut to the mitre, bird's-mouth (6 cm thick) where they rest on a bank sill
    mit = L['mit']
    for arm in arms:
        d, n, A, L_ = arm['d'], arm['n'], arm['A'], arm['L']
        for u in (+RAIL_U, -RAIL_U):
            def s_at(uu, end):
                return _rail_end_s(arm, mit, uu, end)
            a_left, a_right = (s_at(u + RAIL_W / 2, 'start'), s_at(u - RAIL_W / 2, 'start'))
            b_left, b_right = (s_at(u + RAIL_W / 2, 'end'), s_at(u - RAIL_W / 2, 'end'))
            if arm['start'] == 'bank':
                a_left = a_right = -0.20
            if arm['end'] == 'bank':
                b_left = b_right = L_ + 0.20

            def quad(sa_r, sb_r, sa_l, sb_l):
                return np.array([A + d * sa_r + n * (u - RAIL_W / 2), A + d * sb_r + n * (u - RAIL_W / 2),
                                 A + d * sb_l + n * (u + RAIL_W / 2), A + d * sa_l + n * (u + RAIL_W / 2)])
            segs = []
            if arm['start'] == 'bank':
                segs.append((quad(a_right, 0.26, a_left, 0.26), SILL_TOP, 'stub'))
                segs.append((quad(0.26, b_right, 0.26, b_left), Z_R0, 'main'))
            elif arm['end'] == 'bank':
                segs.append((quad(a_right, L_ - 0.26, a_left, L_ - 0.26), Z_R0, 'main'))
                segs.append((quad(L_ - 0.26, b_right, L_ - 0.26, b_left), SILL_TOP, 'stub'))
            else:
                segs.append((quad(a_right, b_right, a_left, b_left), Z_R0, 'main'))
            for poly, z0, tag in segs:
                V, F = prism(poly, z0, Z_R1, ch=0.005, cb=0.005)
                uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
                i = reg('rail' if tag != 'stub' else 'rail_stub', V, arm=arm['k'], u=u, tag=tag)
                out['stringers'].add_part(V, F, [0] * len(F), uv, {'damp': 0.4}, i)
        # ---- third (centre) stringers under the last stretch before each mitre
        for end in ('start', 'end'):
            if arm[end] != 'mitre':
                continue
            if end == 'end':
                s_mit = _rail_end_s(arm, mit, 0.0, 'end')
                ints = [s for s in arm['interior_s'] if s < s_mit - 0.15]
                s_from = (ints[-1] - 0.15) if ints else s_mit - 1.1
                s_from = max(s_from, s_mit - 1.25)
                s_to = s_mit
            else:
                s_mit = _rail_end_s(arm, mit, 0.0, 'start')
                ints = [s for s in arm['interior_s'] if s > s_mit + 0.15]
                s_to = (ints[0] + 0.15) if ints else s_mit + 1.1
                s_to = min(s_to, s_mit + 1.25)
                s_from = s_mit
            u0, u1 = -RAIL_W / 2, RAIL_W / 2
            poly = np.array([A + d * s_from + n * u0, A + d * s_to + n * u0, A + d * s_to + n * u1, A + d * s_from + n * u1])
            # mitre cut at the node end: each long edge ends where it meets the mitre line
            for uu_i, uu in ((0, u0), (1, u1)):
                sm = _rail_end_s(arm, mit, uu, end)
                if end == 'end':
                    poly[1 + uu_i] = A + d * sm + n * uu
                else:
                    poly[(0, 3)[uu_i]] = A + d * sm + n * uu
            V, F = prism(poly, Z_R0, Z_R1, ch=0.005, cb=0.005)
            uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
            i = reg('rail', V, arm=arm['k'], u=0.0, tag='centre')
            out['stringers'].add_part(V, F, [0] * len(F), uv, {'damp': 0.4}, i)
    # ---- FIX ROUND: one short corner rail beside each breaker board, on each arm side, along the mitre line under the offcut planks
    for node, M in mit.items():
        for arm, sgn in ((arms[node - 1], -1.0), (arms[node], +1.0)):
            n_ = arm['n']
            c0 = float(np.dot(n_, sgn * M['b'])) * 0.165
            c1 = float(np.dot(n_, M['m']))
            ta, tb = sorted(((-0.47 - c0) / c1, (0.47 - c0) / c1))
            ta, tb = max(ta, -0.62), min(tb, 0.62)
            a0 = M['P'] + M['m'] * ta + sgn * M['b'] * 0.165
            a1 = M['P'] + M['m'] * tb + sgn * M['b'] * 0.165
            ax_ = unit(a1 - a0)
            nx_ = perp(ax_)
            hw = 0.045
            poly = np.array([a0 + nx_ * hw, a1 + nx_ * hw, a1 - nx_ * hw, a0 - nx_ * hw])
            V, F = prism(poly, Z_R0, Z_R1, ch=0.005, cb=0.005)
            uv = box_uv_for_faces(V, F, 1.0, (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))))
            i = reg('rail_stub', V, arm=arm['k'], u=0.0, tag='corner')
            out['stringers'].add_part(V, F, [0] * len(F), uv, {'damp': 0.4}, i)
    # ---- plank pegs (one per plank end over an outer stringer, about 15 percent skipped) and nail heads on replaced planks
    for p in planks:
        if p['kind'] != 'arm':
            continue
        sp = p['spec']
        x0n, x0f, x1n, x1f = p['clip']
        for sgn in (+1, -1):
            if rng.random() < 0.30 and not p['replaced']:
                continue
            Xp = p['Hl'] - sgn * RAIL_U
            Yp = float(rng.uniform(-0.012, 0.012)) * (p['w'] / 0.13)
            lo = max(x0n, x0f) + 0.035
            hi = min(x1n, x1f) - 0.035
            if not (lo < Xp < hi):
                continue
            z = plank_top_z(sp, Xp, Yp)
            pos = _w(sp, Xp, Yp)
            if p['replaced']:
                V, F = peg_mesh(np.array([pos[0], pos[1], z]), (0, 0, 1), r=0.0068, proud=0.0045, sink=0.002, n=10)
                kind = 'nail'
            else:
                # FIX ROUND: pegs 50 percent bigger so that they read at normal size
                V, F = peg_mesh(np.array([pos[0], pos[1], z]), (0, 0, 1), r=0.0105, proud=0.0105, sink=0.002, n=12)
                kind = 'peg'
            i = reg(kind, V, plank=p['id'], top=z)
            uv = [[(0.0, 0.0)] * len(f) for f in F]
            out['pegs'].add_part(V, F, [1 if p['replaced'] else 0] * len(F), uv, {'plank_tone': 1.0 if p['replaced'] else 0.0}, i)
    # ---- pegs through the posts into the bearer ends (two per joint, on the outer face of the post)
    for p in sup['posts']:
        b = p['bearer']
        if b is None:
            continue
        outv = np.array([b['ax'][0] * p['side'], b['ax'][1] * p['side'], 0.0])
        for dz in (+0.022, -0.022):
            zc = Z_R0 - BEAR_H / 2 + dz
            base_xy = p['xy'] + outv[:2] * (POST / 2) + np.array([p['shear'][0], p['shear'][1]]) * (zc - p['z0'])
            V, F = peg_mesh(np.array([base_xy[0], base_xy[1], zc]), outv, r=0.0105, proud=0.009, sink=0.002, n=12)
            i = reg('peg', V, post=p['part'])
            out['pegs'].add_part(V, F, [0] * len(F), [[(0.0, 0.0)] * len(f) for f in F], {'plank_tone': 0.0}, i)
    # ---- iron cramps across the joints beside each breaker board (4 per turn) and two at the bank ends
    cr = 0
    for p in planks:
        if p['kind'] != 'breaker':
            continue
        M = p['M']
        for sgn_b in (+1, -1):                      # which side of the breaker (toward arm in / arm out)
            for tt in (-0.32, +0.32):               # along the breaker
                centre = M['P'] + M['m'] * tt + M['b'] * sgn_b * (0.08 + 0.0065)
                # strap long axis = b direction (across the gap)
                zA = _top_at(planks, p, centre)
                zs = [z for z in (zA,) if z is not None]
                # find the neighbour plank top under the centre of the strap on the other side
                other = centre + M['b'] * sgn_b * 0.045
                zB = _top_over(planks, other)
                zl = min([z for z in (zA, zB) if z is not None] or [0.22])
                poly = rect_poly(centre[0], centre[1], M['b'][0] * sgn_b, M['b'][1] * sgn_b, 0.06, 0.015)
                V, F = prism(poly, zl - 0.0015, zl + 0.0045, ch=0.0012, cb=0.0)
                i = reg('cramp', V, node=p['node'])
                out['cramps'].add_part(V, F, [0] * len(F), [[(0.0, 0.0)] * len(f) for f in F], {}, i)
                for e in (-0.036, +0.036):
                    hp = centre + M['b'] * sgn_b * e
                    V, F = peg_mesh(np.array([hp[0], hp[1], zl + 0.0045]), (0, 0, 1), r=0.0042, proud=0.0028, sink=0.0006, n=6)
                    i = reg('nailhead', V)
                    out['cramps'].add_part(V, F, [0] * len(F), [[(0.0, 0.0)] * len(f) for f in F], {}, i)
                cr += 1
    L['n_cramps'] = cr
    return out, parts


def _w(sp, X, Y):
    ax = unit(sp['ax']); ay = perp(ax); O = np.array(sp['O'], float)
    return O + X * ax + Y * ay


def _local(sp, xy):
    ax = unit(sp['ax']); ay = perp(ax); O = np.array(sp['O'], float)
    q = np.asarray(xy) - O
    return float(np.dot(q, ax)), float(np.dot(q, ay))


def _top_over(planks, xy):
    """top height of whichever plank covers the point (None when none)."""
    for p in planks:
        sp = p['spec']
        X, Y = _local(sp, xy)
        if -sp['w'] / 2 <= Y <= sp['w'] / 2:
            x0n, x0f, x1n, x1f = p['clip'] if p.get('clip') is not None else (0.0, 0.0, p['L'], p['L'])
            if max(x0n, x0f) + 0.01 < X < min(x1n, x1f) - 0.01:
                return plank_top_z(sp, X, Y)
    return None


def _top_at(planks, p, xy):
    sp = p['spec']
    X, Y = _local(sp, xy)
    return plank_top_z(sp, min(max(X, 0.02), sp['L'] - 0.02), max(-sp['w'] / 2, min(sp['w'] / 2, Y)))
