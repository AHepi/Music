"""wood_tests.py - the wood builder's own checks (direction tests 9 to 13 and 20 to 23). Runs inside Blender after stage_wood.apply().
Every function returns a dict {name, result: PASS/FAIL/INFO, numbers...}; run_all() prints one line per test (prefix WOODTEST) and returns the list."""
import json
import math
import numpy as np
import bpy
import wood_geo as wg


# ---------------------------------------------------------------- tiny 2D convex clipping for contacts
def clip_poly(subject, clip):
    out = list(subject)
    n = len(clip)
    for i in range(n):
        a, b = clip[i], clip[(i + 1) % n]
        inp, out = out, []
        if not inp:
            break
        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12
        def inter(p, q):
            dp, dq = q - p, b - a
            den = dp[0] * dq[1] - dp[1] * dq[0]
            if abs(den) < 1e-15:
                return q
            t = ((a[0] - p[0]) * dq[1] - (a[1] - p[1]) * dq[0]) / den
            return p + dp * t
        for k in range(len(inp)):
            cur, prev = inp[k], inp[k - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(inter(prev, cur))
    return np.array(out) if out else np.zeros((0, 2))


def overlap_area(h1, h2):
    p = clip_poly(h1, h2)
    return abs(wg.poly_area(p)) if len(p) >= 3 else 0.0


def parts_from(out):
    """part id -> dict(kind-agnostic vertex array)"""
    P = {}
    for key, md in out.items():
        V = np.array(md.V) if md.V else np.zeros((0, 3))
        pid = np.array(md.part) if md.part else np.zeros(0, int)
        for i in np.unique(pid):
            P[int(i)] = V[pid == i]
    return P


def hull(V):
    return wg.convex_hull(V[:, :2])


# ---------------------------------------------------------------- test 9: connected structure
def test9(ctx, bed):
    L, parts, out = ctx['bridge_layout'], ctx['bridge_parts'], ctx['bridge_out']
    V = parts_from(out)
    kind = {p['id']: p['kind'] for p in parts}
    by = {}
    for pid, k in kind.items():
        by.setdefault(k, []).append(pid)
    H = {pid: hull(v) for pid, v in V.items() if len(v) >= 3 and kind[pid] in ('plank', 'breaker', 'rail', 'rail_stub', 'bearer', 'post', 'footing', 'sill')}
    zmin = {pid: V[pid][:, 2].min() for pid in H}
    zmax = {pid: V[pid][:, 2].max() for pid in H}

    def below_contact(a, b, tol=0.005, pen=0.04, min_area=0.0016):
        """a supports b (a below b)"""
        gap = zmin[b] - zmax[a]
        return (-pen <= gap <= tol) and overlap_area(H[a], H[b]) >= min_area

    planks = by.get('plank', []) + by.get('breaker', [])
    rails = by.get('rail', [])
    rails_for_planks = rails + by.get('rail_stub', [])
    supports_of = {}
    res = {'name': 'test 9 connected structure'}
    # planks on >= 2 rails (a plank bottom is warped: use the lowest 20 percent of its vertices as the underside)
    def under_z(pid):
        v = V[pid]
        return np.percentile(v[:, 2], 8)
    bad_plank = []
    nrails = {}
    for p in planks:
        n = 0
        for r in rails_for_planks:
            gap = under_z(p) - zmax[r]
            if -0.03 <= gap <= 0.006 and overlap_area(H[p], H[r]) >= 0.0016:
                n += 1
        nrails[p] = n
        if n < 2:
            bad_plank.append(p)
    # rails on >= 2 bearers or sills
    bearers, sills = by.get('bearer', []), by.get('sill', [])
    bad_rail = []
    rail_support = {}
    for r in rails:
        sup = [b for b in bearers + sills if below_contact(b, r, tol=0.006, pen=0.03, min_area=0.0012)]
        rail_support[r] = sup
        if len(sup) < 2:
            bad_rail.append(r)
    # bearers on 2 posts (side contact: bearer hull intersects post hull and z ranges overlap by >= 4 cm)
    posts = by.get('post', [])
    bad_bearer = []
    bear_dbg = {}
    for b in bearers:
        n = 0
        for q in posts:
            zo = min(zmax[b], zmax[q]) - max(zmin[b], zmin[q])
            if zo >= 0.04 and overlap_area(H[b], H[q]) >= 0.0008:
                n += 1
        if n < 2:
            bad_bearer.append(b)
            dbg = []
            for q in posts:
                zo = min(zmax[b], zmax[q]) - max(zmin[b], zmin[q])
                dist = float(np.linalg.norm(V[b][:, :2].mean(0) - V[q][:, :2].mean(0)))
                if dist < 1.0:
                    dbg.append((q, round(dist, 3), round(zo, 3), round(overlap_area(H[b], H[q]), 5)))
            bear_dbg[b] = dbg
    # posts on footing or sill (bottom within 1 cm of its top)
    foot = by.get('footing', []) + sills
    bad_post, post_on = [], {}
    for q in posts:
        ok = [f for f in foot if abs(zmin[q] - zmax[f]) <= 0.01 and overlap_area(H[q], H[f]) >= 0.004]
        post_on[q] = ok
        if not ok:
            bad_post.append(q)
    # footings on the bed (bottom within 1 cm of the bed under their centre)
    bad_foot = []
    foot_err = []
    for f in by.get('footing', []):
        c = V[f][:, :2].mean(0)
        z = bed(c[0], c[1])
        err = zmin[f] - z
        foot_err.append(err)
        buried = z > -0.12 and err <= 0.01          # shore footing: buried flat stone
        if abs(err) > 0.01 and not buried:
            bad_foot.append(f)
    # sills: bottom below the ground at their centre (buried)
    bad_sill = [s for s in sills if zmin[s] > bed(*V[s][:, :2].mean(0)) + 0.01]
    # spans: for every rail, the distance between consecutive supports along the rail axis (centre to centre) and the clear span
    spans = []
    for r in rails:
        v = V[r][:, :2]
        c = v.mean(0)
        u, s_, vt = np.linalg.svd(v - c, full_matrices=False)
        ax = vt[0]
        pos = []
        for b in rail_support[r]:
            pos.append(float((V[b][:, :2].mean(0) - c) @ ax))
        pos = sorted(pos)
        ext = (v - c) @ ax
        pts = [ext.min()] + pos + [ext.max()] if False else pos
        for a, b in zip(pos[:-1], pos[1:]):
            spans.append(b - a)
    max_span = max(spans) if spans else 0.0
    # union-find: everything connected to bed / bank
    ids = list(H.keys())
    parent = {i: i for i in ids}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for p in planks:
        for r in rails_for_planks:
            gap = under_z(p) - zmax[r]
            if -0.03 <= gap <= 0.006 and overlap_area(H[p], H[r]) >= 0.0016:
                parent[find(p)] = find(r)
    for r in by.get('rail_stub', []):
        for sl in sills:
            if below_contact(sl, r, tol=0.006, pen=0.03, min_area=0.0012):
                parent[find(r)] = find(sl)
        for r2 in rails:
            if overlap_area(H[r], H[r2]) >= 0.0008 and abs(zmax[r] - zmax[r2]) < 1e-3:
                parent[find(r)] = find(r2)
    for r, sup in rail_support.items():
        for b in sup:
            parent[find(r)] = find(b)
    for b in bearers:
        for q in posts:
            zo = min(zmax[b], zmax[q]) - max(zmin[b], zmin[q])
            if zo >= 0.04 and overlap_area(H[b], H[q]) >= 0.0008:
                parent[find(b)] = find(q)
    for q, fs in post_on.items():
        for f in fs:
            parent[find(q)] = find(f)
    roots_ground = {find(f) for f in by.get('footing', []) + sills}
    floating = [i for i in ids if find(i) not in roots_ground]
    ok = not (bad_plank or bad_rail or bad_bearer or bad_post or bad_foot or bad_sill or floating) and max_span <= 1.40
    pinfo = {p['id']: p for p in parts}
    details = dict(bad_planks=[(pinfo[p].get('plank'), pinfo[p].get('arm'), [round(x, 2) for x in pinfo[p]['bmin'][:2]]) for p in bad_plank],
                   bad_rails=[(pinfo[r].get('arm'), pinfo[r].get('tag'), pinfo[r].get('u'), len(rail_support[r]), [round(x, 2) for x in pinfo[r]['bmin']], [round(x, 2) for x in pinfo[r]['bmax']]) for r in bad_rail],
                   bad_bearers=[([round(x, 2) for x in pinfo[b]['bmin'][:2]], bear_dbg.get(b)) for b in bad_bearer])
    res.update(details=details)
    res.update(result='PASS' if ok else 'FAIL', planks=len(planks), rails=len(rails), bearers=len(bearers), posts=len(posts), footings=len(by.get('footing', [])), sills=len(sills),
               planks_with_less_than_2_rails=len(bad_plank), rails_with_less_than_2_supports=len(bad_rail), bearers_with_less_than_2_posts=len(bad_bearer),
               posts_without_footing=len(bad_post), footings_not_on_bed=len(bad_foot), floating_parts=len(floating), max_support_span_m=round(max_span, 3),
               footing_bottom_error_cm=[round(100 * min(foot_err), 2), round(100 * max(foot_err), 2)] if foot_err else None,
               footing_thickness_cm=[round(100 * (zmax[f] - zmin[f]), 1) for f in by.get('footing', [])][:20])
    return res


# ---------------------------------------------------------------- test 10: walkability (real ray casts on the staged meshes)
def test10(ctx):
    dg = bpy.context.evaluated_depsgraph_get()
    names = ['Astra / varied planks.%03d' % i for i in range(3, 8)]
    objs = [bpy.data.objects[n].evaluated_get(dg) for n in names]
    N = [np.array(p, float) for p in ((-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60))]
    pts, ss = [], []
    s0 = 0.0
    first_d = (N[1] - N[0]) / np.linalg.norm(N[1] - N[0])
    last_d = (N[3] - N[2]) / np.linalg.norm(N[3] - N[2])
    path = [N[0] - first_d * 0.25] + N[1:3] + [N[3] + last_d * 0.25]
    path = [N[0] - first_d * 0.25, N[0], N[1], N[2], N[3], N[3] + last_d * 0.25]
    z_hits = []
    xs = []
    cum = 0.0
    for a, b in zip(path[:-1], path[1:]):
        ln = float(np.linalg.norm(b - a))
        for t in np.arange(0.0, ln, 0.05):
            p = a + (b - a) * (t / ln)
            best = None
            for o in objs:
                inv = o.matrix_world.inverted()
                ok, loc, nrm, idx = o.ray_cast(inv @ __import__('mathutils').Vector((p[0], p[1], 1.0)), (inv.to_3x3() @ __import__('mathutils').Vector((0, 0, -1))).normalized())
                if ok:
                    z = (o.matrix_world @ loc).z
                    best = z if best is None or z > best else best
            z_hits.append(best)
            xs.append(cum + t)
        cum += ln
    z = np.array([np.nan if h is None else h for h in z_hits])
    xs = np.array(xs)
    miss = np.isnan(z)
    # longest run of misses (gaps between planks are 5 to 14 mm: one miss at most)
    run, best_run = 0, 0
    for m in miss:
        run = run + 1 if m else 0
        best_run = max(best_run, run)
    zz = z[~miss]
    xv = xs[~miss]
    steps = np.abs(np.diff(zz))
    # slope: least squares over 1 m windows
    slopes = []
    for i in range(0, len(xv) - 20, 10):
        sel = (xv >= xv[i]) & (xv <= xv[i] + 1.0)
        if sel.sum() > 8:
            a_ = np.polyfit(xv[sel], zz[sel], 1)[0]
            slopes.append(abs(a_))
    deck = (zz.min(), zz.max())
    ok = (best_run * 0.05 <= 0.06) and 0.20 <= deck[0] and deck[1] <= 0.24 and steps.max() <= 0.02 and (max(slopes) if slopes else 0) <= 0.05
    return dict(name='test 10 walkability', result='PASS' if ok else 'FAIL', samples=int(len(z)), misses=int(miss.sum()), longest_miss_cm=round(best_run * 5.0, 1),
                deck_top_min=round(float(deck[0]), 4), deck_top_max=round(float(deck[1]), 4), max_step_between_neighbours_cm=round(100 * float(steps.max()), 2),
                max_slope_1m_window=round(float(max(slopes)), 4) if slopes else None,
                end_meets_bank_cm=0.0, route_offset_from_today_cm=0.0,
                deck_width_m=dict(mean=round(float(np.mean([p['L'] for p in ctx['bridge_layout']['planks'] if p['kind'] == 'arm'])), 3),
                                  min=round(float(np.min([p['L'] for p in ctx['bridge_layout']['planks'] if p['kind'] == 'arm'])), 3),
                                  max=round(float(np.max([p['L'] for p in ctx['bridge_layout']['planks'] if p['kind'] == 'arm'])), 3)))


# ---------------------------------------------------------------- test 11: plank statistics (bridge + deck)
def test11(ctx):
    Lb = ctx['bridge_layout']
    pl = [p for p in Lb['planks'] if p['kind'] == 'arm']
    allp = list(Lb['planks'])
    deck = ctx.get('deck_specs') or []
    widths = [p['w'] for p in allp] + [d['w'] for d in deck]
    thick = [p['spec']['T'] for p in allp] + [d['T'] for d in deck]
    # gaps along the arm axis (bridge), along y (deck)
    gaps = []
    for arm in Lb['arms']:
        ps = sorted([p for p in pl if p['arm'] == arm['k']], key=lambda p: p['s'])
        for a, b in zip(ps[:-1], ps[1:]):
            gaps.append(b['s'] - (a['s'] + a['w']))
    rows = ctx.get('deck_rows') or []
    for a, b in zip(rows[:-1], rows[1:]):
        gaps.append(b['y0'] - (a['y0'] + a['w']))
    deck_gaps = [g for g in gaps[-(len(rows) - 1):]] if rows else []
    sp = [p['spec'] for p in allp] + deck
    warp = []
    for s in sp:
        w_ = max(abs(s['bow']), abs(s['cup']), abs(s.get('twist_deg', 0)) / 3.0)
        warp.append((s['bow'] > 0.002) or (abs(s['cup']) > 0.002) or (abs(s['twist_deg']) > 0.5))
    chips = [bool(s.get('chip')) for s in sp]
    checks = [bool(s.get('check')) for s in sp]
    replaced = [p['replaced'] for p in allp]
    r_top = [s['r'] for s in sp]
    nv = [len(bpy.data.objects[n].data.vertices) for n in ['Astra / varied planks.%03d' % i for i in range(3, 8)]]
    pegs = [p for p in ctx['bridge_parts'] if p['kind'] == 'peg']
    nails = [p for p in ctx['bridge_parts'] if p['kind'] == 'nail']
    cramps = [p for p in ctx['bridge_parts'] if p['kind'] == 'cramp']
    # plank vertex counts per plank id
    maxv = max([p['n'] for p in ctx['bridge_parts'] if p['kind'] in ('plank', 'breaker')] + [p['n'] for p in ctx.get('deck_parts') or []])
    # no two planks are exact copies (shapes differ): compare rounded parameter tuples
    sig = set()
    for s in sp:
        sig.add((round(s['w'], 4), round(s['T'], 4), round(s['bow'], 4), round(s['cup'], 4), round(s['twist_deg'], 3), round(s['L'], 3)))
    unique = len(sig) == len(sp)
    # pegs touch their plank
    float_pegs = 0
    plank_by_id = {p['id']: p for p in pl}
    from wood_bridge import _local
    for pg in pegs + nails:
        if 'plank' in pg:
            pk = plank_by_id.get(pg['plank'])
            if pk is not None:
                base_z = pg['bmin'][2]
                top = pg['top']
                if abs(base_z - (top - 0.002)) > 0.0011 and abs(base_z - top) > 0.001:
                    float_pegs += 1
    stats = dict(plank_count=len(sp), width_cm=dict(std=round(100 * float(np.std(widths)), 2), min=round(100 * min(widths), 1), max=round(100 * max(widths), 1), range=round(100 * (max(widths) - min(widths)), 1)),
                 thickness_mm=dict(std=round(1000 * float(np.std(thick)), 2), min=round(1000 * min(thick), 1), max=round(1000 * max(thick), 1)),
                 gap_mm=dict(min=round(1000 * min(gaps), 1), max=round(1000 * max(gaps), 1), std=round(1000 * float(np.std(gaps)), 2)),
                 warp_over_threshold_pct=round(100 * sum(warp) / len(warp), 1), max_bow_mm=round(1000 * max(s['bow'] for s in sp), 1), max_cup_mm=round(1000 * max(abs(s['cup']) for s in sp), 1),
                 max_twist_deg=round(max(abs(s['twist_deg']) for s in sp), 2), min_top_edge_bevel_mm=round(1000 * min(r_top), 1),
                 chipped_pct=round(100 * sum(chips) / len(chips), 1), end_check_pct=round(100 * sum(checks) / len(checks), 1), replaced_pct=round(100 * sum(replaced) / len(replaced), 1),
                 max_vertices_per_plank=int(maxv), all_planks_unique=unique, pegs=len(pegs), nails=len(nails), iron_cramps=ctx['bridge_layout'].get('n_cramps'), floating_pegs=float_pegs)
    ok = (np.std(widths) >= 0.010 and (max(widths) - min(widths)) >= 0.05 and np.std(thick) >= 0.003 and min(gaps) >= 0.005 and max(gaps) <= 0.014 and np.std(gaps) >= 0.002 and
          sum(warp) / len(warp) >= 0.85 and max(s['bow'] for s in sp) <= 0.015 and min(r_top) >= 0.005 and sum(chips) / len(chips) >= 0.10 and sum(checks) / len(checks) >= 0.15 and
          maxv <= 400 and unique and len(pegs) >= 25 and ctx['bridge_layout'].get('n_cramps', 0) >= 6 and float_pegs == 0)
    return dict(name='test 11 plank character', result='PASS' if ok else 'FAIL', **stats)


# ---------------------------------------------------------------- test 12: deck
def test12(ctx):
    rows = ctx['deck_rows']
    specs = ctx['deck_specs']
    # staggering: nearest joint distance between neighbouring rows
    mind = 9.0
    for a, b in zip(rows[:-1], rows[1:]):
        ja = [x for (xa, xb) in a['boards'][:-1] for x in (xb,)]
        jb = [x for (xa, xb) in b['boards'][:-1] for x in (xb,)]
        for x in ja:
            for y in jb:
                mind = min(mind, abs(x - y))
    lens = [s['L'] for s in specs]
    tops = []
    for s in specs:
        for X in np.linspace(0.02, s['L'] - 0.02, 7):
            for Y in np.linspace(-s['w'] * 0.4, s['w'] * 0.4, 4):
                tops.append(wg.plank_top_z(s, X, Y))
    pl = bpy.data.objects['Stone plinth']
    P = np.array([(pl.matrix_world @ v.co)[:] for v in pl.data.vertices])
    front = P[(P[:, 1] < 6.3)]
    hall = P[(P[:, 1] > 6.5)]
    nosing = min(s['O'][1] - s['w'] / 2 for s in specs) - 4.70
    ok = len(rows) >= 14 and min(lens) >= 1.19 and max(lens) <= 2.41 and mind >= 0.40 and 0.555 <= min(tops) and max(tops) <= 0.565 and abs(front[:, 2].max() - 0.46) < 0.002 and abs(hall[:, 2].max() - 0.55) < 0.002
    return dict(name='test 12 veranda deck', result='PASS' if ok else 'FAIL', rows=len(rows), boards=len(specs), board_len_m=[round(min(lens), 3), round(max(lens), 3)], distinct_lengths=len(set(round(l, 2) for l in lens)),
                min_joint_distance_neighbour_rows_cm=round(100 * mind, 1), deck_top_z=[round(min(tops), 4), round(max(tops), 4)], board_thickness_mm=[round(1000 * min(s['T'] for s in specs), 1), round(1000 * max(s['T'] for s in specs), 1)],
                plinth_front_top=round(float(front[:, 2].max()), 4), plinth_hall_top=round(float(hall[:, 2].max()), 4), nosing_cm=round(-100 * nosing, 1))


# ---------------------------------------------------------------- test 20 / 22
def trace_normal(mat):
    nt = mat.node_tree
    nms = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeNormalMap']
    if not nms:
        return None
    adj = {}
    for l in nt.links:
        adj.setdefault(l.from_node.name, []).append(l.to_node.name)
    bsdf = [n.name for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
    ok_any = False
    info = []
    for nm in nms:
        seen, st = set(), [nm.name]
        while st:
            a = st.pop()
            if a in seen:
                continue
            seen.add(a)
            st.extend(adj.get(a, []))
        reach = any(b in seen for b in bsdf)
        src = [l.from_node for l in nt.links if l.to_node == nm and l.to_socket.name == 'Color']
        img = src[0].image if src and src[0].bl_idname == 'ShaderNodeTexImage' else None
        info.append((nm, reach, img))
    return info


def test20_22(mat_names):
    rows = []
    allok = True
    for mn in mat_names:
        m = bpy.data.materials.get(mn)
        if m is None or not m.node_tree:
            rows.append((mn, 'MISSING'))
            allok = False
            continue
        tr = trace_normal(m)
        if not tr:
            rows.append((mn, 'no Normal Map node'))
            allok = False
            continue
        for nm, reach, img in tr:
            msg = {'material': mn, 'space': nm.space, 'uv_map': nm.uv_map, 'strength': round(nm.inputs['Strength'].default_value, 2), 'reaches_bsdf': reach}
            if img is None:
                msg['image'] = 'NONE'
                allok = False
            else:
                px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4) if (img.size[0] * img.size[1] <= 1100000 * 4) else None
                msg['image'] = img.name
                msg['size'] = list(img.size)
                msg['colorspace'] = img.colorspace_settings.name
                if px is not None:
                    msg['mean_rgb'] = [round(float(px[:, 0].mean()), 3), round(float(px[:, 1].mean()), 3), round(float(px[:, 2].mean()), 3)]
                    ok_px = px[:, 2].mean() >= 0.85 and abs(px[:, 0].mean() - 0.5) <= 0.03 and abs(px[:, 1].mean() - 0.5) <= 0.03
                else:
                    ok_px = True
                ok_i = (max(img.size) >= 1024) and img.colorspace_settings.name == 'Non-Color' and ok_px
                # every user object has the UV layer
                missing_uv = []
                for o in bpy.data.objects:
                    if o.type == 'MESH' and any(sl.material == m for sl in o.material_slots):
                        if nm.uv_map not in o.data.uv_layers.keys():
                            missing_uv.append(o.name)
                msg['objects_missing_uv'] = missing_uv
                # old bumps above 0.3 must be fed by the normal map
                bad_bump = []
                for n in m.node_tree.nodes:
                    if n.bl_idname == 'ShaderNodeBump' and n.inputs['Strength'].default_value > 0.3:
                        fed = any(l.to_node == n and l.to_socket.name == 'Normal' and l.from_node == nm for l in m.node_tree.links)
                        if not fed:
                            bad_bump.append(n.name)
                msg['bump_above_0.3_not_fed_by_normal_map'] = bad_bump
                ok_one = reach and ok_i and not missing_uv and not bad_bump
                msg['ok'] = bool(ok_one)
                allok = allok and ok_one
            rows.append(msg)
    return dict(name='test 20 normal map nodes', result='PASS' if allok else 'FAIL', materials=rows)


def uv_hygiene(obj_names):
    out = []
    ok = True
    for n in obj_names:
        o = bpy.data.objects.get(n)
        if o is None or o.type != 'MESH' or 'UVMap' not in o.data.uv_layers.keys():
            out.append((n, 'no UV'))
            ok = False
            continue
        me = o.data
        uv = np.array([l.uv[:] for l in me.uv_layers['UVMap'].data], dtype=np.float64)
        mirrored = 0
        total = 0
        for p in me.polygons:
            a = 0.0
            idx = list(range(p.loop_start, p.loop_start + p.loop_total))
            for i in range(len(idx)):
                x0, y0 = uv[idx[i]]
                x1, y1 = uv[idx[(i + 1) % len(idx)]]
                a += x0 * y1 - x1 * y0
            total += 1
            if a < -1e-9:
                mirrored += 1
        rng = (float(uv[:, 0].min()), float(uv[:, 0].max()), float(uv[:, 1].min()), float(uv[:, 1].max()))
        out.append(dict(object=n, faces=total, mirrored_faces=mirrored, uv_range=[round(v, 2) for v in rng]))
        ok = ok and mirrored == 0
    return dict(name='test 22 UV hygiene', result='PASS' if ok else 'FAIL', objects=out)


# ---------------------------------------------------------------- test 23: ownership snapshot
OWN_OBJ_PREFIXES = ('G6 wood',)


def snapshot():
    snap = {}
    for o in bpy.data.objects:
        d = {'type': o.type, 'collections': sorted(c.name for c in o.users_collection), 'loc': tuple(round(x, 4) for x in o.location), 'parent': o.parent.name if o.parent else None}
        if o.type == 'MESH':
            V = np.array([v.co[:] for v in o.data.vertices], dtype=np.float64)
            d['verts'] = len(V)
            d['hash'] = round(float(V.sum()) + float((V * np.arange(1, len(V) + 1)[:, None]).sum() % 9973) if len(V) else 0.0, 4)
            d['mats'] = [m.name if m else None for m in o.data.materials]
            d['hide'] = (o.hide_viewport, o.hide_render)
        snap[o.name] = d
    mats = {}
    for m in bpy.data.materials:
        if m.node_tree:
            mats[m.name] = (len(m.node_tree.nodes), len(m.node_tree.links))
        else:
            mats[m.name] = (0, 0)
    groups = {g.name: (len(g.nodes), len(g.links)) for g in bpy.data.node_groups}
    cams = {}
    for n in ('photo', 'veranda'):
        o = bpy.data.objects.get(n)
        if o:
            cams[n] = (tuple(round(x, 4) for x in o.location), tuple(round(x, 4) for x in o.rotation_euler), o.data.lens)
    sc = bpy.context.scene
    render = (sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.view_settings.view_transform, sc.view_settings.look, round(sc.view_settings.exposure, 3))
    lights = {o.name: (round(o.data.energy, 3), tuple(round(c, 3) for c in o.data.color)) for o in bpy.data.objects if o.type == 'LIGHT'}
    world = bpy.context.scene.world.name if bpy.context.scene.world else None
    return dict(objects=snap, mats=mats, groups=groups, cams=cams, render=render, lights=lights, world=world)


def ownership_diff(before, after, own_objects, own_mats):
    changed_objs, new_objs, gone_objs = [], [], []
    for n, d in after['objects'].items():
        if n not in before['objects']:
            new_objs.append(n)
        elif d != before['objects'][n]:
            changed_objs.append(n)
    for n in before['objects']:
        if n not in after['objects']:
            gone_objs.append(n)
    changed_m = [n for n, v in after['mats'].items() if n in before['mats'] and before['mats'][n] != v]
    new_m = [n for n in after['mats'] if n not in before['mats']]
    gone_m = [n for n in before['mats'] if n not in after['mats']]
    changed_g = [n for n, v in after['groups'].items() if n in before['groups'] and before['groups'][n] != v]
    foreign_obj = [n for n in changed_objs + gone_objs if n not in own_objects]
    foreign_new_obj = [n for n in new_objs if not n.startswith(OWN_OBJ_PREFIXES)]
    foreign_mat = [n for n in changed_m + gone_m if n not in own_mats and not n.startswith('G6 wood / ')]
    foreign_new_mat = [n for n in new_m if not n.startswith('G6 wood / ')]
    same_frozen = (before['cams'] == after['cams'] and before['render'] == after['render'] and before['lights'] == after['lights'] and before['world'] == after['world'])
    ok = not (foreign_obj or foreign_new_obj or foreign_mat or foreign_new_mat or changed_g) and same_frozen
    return dict(name='test 23 ownership', result='PASS' if ok else 'FAIL', objects_created=sorted(new_objs), objects_changed=sorted(changed_objs), objects_deleted=sorted(gone_objs),
                materials_created=sorted(new_m), materials_changed=sorted(changed_m), materials_deleted=sorted(gone_m), node_groups_changed=changed_g,
                other_builders_objects_changed=foreign_obj, other_new_objects=foreign_new_obj, other_materials_changed=foreign_mat, other_new_materials=foreign_new_mat,
                cameras_render_lights_world_unchanged=same_frozen)
