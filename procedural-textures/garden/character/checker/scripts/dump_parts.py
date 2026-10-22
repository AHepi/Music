import bpy, json, sys, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import *
names = ['Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002', 'Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007',
         'Bridge pier 0', 'Bridge pier 1', 'Bridge pier 2', 'Bridge pier 3', 'Bridge stringers', 'G6 wood / bridge bearers', 'G6 wood / bridge cramps', 'G6 wood / bridge footings', 'G6 wood / bridge pegs', 'G6 wood / bridge posts', 'G6 wood / deck joists', 'G6 wood / deck pegs', 'Stone plinth']
rows = []
for nm in names:
    P = Parts([nm])
    for it in P.items:
        rows.append({'obj': nm, 'idx': it['idx'], 'nv': len(it['V']), 'bmin': [round(float(x), 4) for x in it['bmin']], 'bmax': [round(float(x), 4) for x in it['bmax']]})
json.dump(rows, open(sys.argv[-1], 'w'))
print('PARTS', len(rows))
