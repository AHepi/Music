import bpy, json, sys
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import *
PL = ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007']
planks = Parts(PL)
pb, lab = planks.all_bvh()
cr = Parts(['G6 wood / bridge cramps'])
rows = []
for it in cr.items:
    c = (it['bmin'] + it['bmax']) / 2
    # sample 5 points over part bbox centre line for plank top beneath
    tops = []
    for fx in (0.1, 0.5, 0.9):
        for fy in (0.1, 0.5, 0.9):
            x = it['bmin'][0] + (it['bmax'][0] - it['bmin'][0]) * fx; y = it['bmin'][1] + (it['bmax'][1] - it['bmin'][1]) * fy
            h = pb.ray_cast(Vector((x, y, 1.0)), Vector((0, 0, -1)), 3.0)
            if h[0] is not None: tops.append(h[0].z)
    rows.append({'id': it['id'], 'nv': len(it['V']), 'bmin': np.round(it['bmin'], 3).tolist(), 'bmax': np.round(it['bmax'], 3).tolist(), 'plank_top_under_min_max': [round(min(tops), 3), round(max(tops), 3)] if tops else None})
json.dump(rows, open(sys.argv[-1], 'w'))
