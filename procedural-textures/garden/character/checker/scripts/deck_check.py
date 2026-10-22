import bpy, json, sys, time
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import *
from mathutils import Vector
R = {}
deck = Parts(['Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002'])
joists = Parts(['G6 wood / deck joists'])
plinth = Parts(['Stone plinth'])
R['n_boards'] = len(deck.items); R['n_joists'] = len(joists.items)
R['plinth_parts'] = [(np.round(p['bmin'], 3).tolist(), np.round(p['bmax'], 3).tolist()) for p in plinth.items]
R['joist_z'] = [(round(float(j['bmin'][2]), 3), round(float(j['bmax'][2]), 3)) for j in joists.items][:4]
tops = np.array([d['bmax'][2] for d in deck.items]); bots = np.array([d['bmin'][2] for d in deck.items])
R['deck_top_z_min_max'] = [round(float(tops.min()), 4), round(float(tops.max()), 4)]
R['board_z_extent_mm_min_max'] = [round(float((tops - bots).min() * 1000), 1), round(float((tops - bots).max() * 1000), 1)]
# rows by y centre
yc = np.array([(d['bmin'][1] + d['bmax'][1]) / 2 for d in deck.items]); xs = np.array([[d['bmin'][0], d['bmax'][0]] for d in deck.items])
order = np.argsort(yc); rows = []; cur = [order[0]]
for i in order[1:]:
    if yc[i] - yc[cur[-1]] > 0.06: rows.append(cur); cur = [i]
    else: cur.append(i)
rows.append(cur)
R['rows'] = len(rows)
lens = np.array([d['bmax'][0] - d['bmin'][0] for d in deck.items])
R['board_len_m_min_max'] = [round(float(lens.min()), 2), round(float(lens.max()), 2)]
# butt joints x positions per row (board ends)
joints = []
for r in rows:
    ends = sorted(xs[r][:, 1])[:-1]
    joints.append(ends)
near = []
for a, b in zip(rows[:-1], rows[1:]):
    ea = sorted(xs[a][:, 1])[:-1]; eb = sorted(xs[b][:, 1])[:-1]
    for x in ea:
        for y in eb: near.append(abs(x - y))
R['min_distance_between_neighbouring_row_joints_m'] = round(float(min(near)), 3) if near else None
# boards rest on joists
lb, lab = joists.all_bvh()
bad = []; counts = []
for it in deck.items:
    k = it['id']; xs_ = np.arange(it['bmin'][0] + 0.01, it['bmax'][0], 0.03); ys_ = np.arange(it['bmin'][1] + 0.01, it['bmax'][1], 0.01)
    cnt = {}; 
    for x in xs_:
        for y in ys_:
            h = deck.bvh(k).ray_cast(Vector((x, y, it['bmin'][2] - 0.05)), Vector((0, 0, 1)), 1.0)
            if h[0] is None: continue
            hh = lb.ray_cast(Vector((x, y, h[0].z + 0.02)), Vector((0, 0, -1)), 1.0)
            if hh[0] is not None and h[0].z - hh[0].z < 0.008: cnt[int(lab[hh[2]])] = cnt.get(int(lab[hh[2]]), 0) + 1
    good = [l for l, c in cnt.items() if c >= 3]
    counts.append(len(good))
    if len(good) < 2: bad.append({'board': k, 'obj': it['obj'], 'x': [round(float(it['bmin'][0]), 2), round(float(it['bmax'][0]), 2)], 'supports': len(good)})
R['boards_on_fewer_than_2_joists'] = {'n': len(bad), 'examples': bad[:8], 'min_max_supports': [min(counts), max(counts)]}
# joists rest on plinth
pb, plab = plinth.all_bvh()
jb = []
for it in joists.items:
    k = it['id']; xs_ = np.linspace(it['bmin'][0] + 0.01, it['bmax'][0] - 0.01, 12); ys_ = np.linspace(it['bmin'][1] + 0.01, it['bmax'][1] - 0.01, 6); gaps = []
    for x in xs_:
        for y in ys_:
            h = joists.bvh(k).ray_cast(Vector((x, y, it['bmin'][2] - 0.05)), Vector((0, 0, 1)), 1.0)
            if h[0] is None: continue
            hh = pb.ray_cast(Vector((x, y, h[0].z + 0.02)), Vector((0, 0, -1)), 2.0)
            gaps.append(None if hh[0] is None else round(float(h[0].z - hh[0].z) * 1000, 1))
    g = [x for x in gaps if x is not None]
    jb.append({'joist': k, 'n': len(gaps), 'no_support_under': len(gaps) - len(g), 'gap_mm_min_max': [min(g), max(g)] if g else None})
R['joists_on_plinth'] = jb
# gap between board underside and the plinth front strip (stand clear?) : board bottom z vs plinth strips top
R['front_strip_top'] = round(float(plinth.items[0]['bmax'][2]), 3); R['hall_strip_top'] = round(float(plinth.items[1]['bmax'][2]), 3)
R['deck_bottom_z_min'] = round(float(bots.min()), 4)
json.dump(R, open(sys.argv[-1], 'w'), indent=1, default=str)
print('DECK done')
