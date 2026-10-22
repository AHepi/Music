import sys, os, json
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/wood'
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import numpy as np
import wood_bridge as wb, wood_tests as wt
bed = lambda x, y: -0.44 if y < 1.9 else 0.08
L = wb.layout(7, bed_fn=bed, rocks=[])
out, parts = wb.build_meshes(L)
ctx = dict(bridge_layout=L, bridge_parts=parts, bridge_out=out)
r = wt.test9(ctx, bed)
print(json.dumps({k: v for k, v in r.items() if k != 'details'}, default=str))
print(json.dumps(r['details'], default=str)[:1500])
print('planks', sum(1 for p in L['planks'] if p['kind']=='arm'), 'offcuts', sum(1 for p in L['planks'] if p.get('offcut')))
