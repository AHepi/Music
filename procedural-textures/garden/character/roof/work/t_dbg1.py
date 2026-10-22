import sys, json
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import stage_roof, bpy, numpy as np
rep=stage_roof.apply({'steps':[0,1,2],'map_sizes':{'glaze':128,'plaster':128,'stone':128,'moss':128}})
dg=bpy.context.evaluated_depsgraph_get()
from collections import Counter
c=Counter(); ex=[]
k=-1
for inst in dg.object_instances:
    if not (inst.is_instance and inst.parent and inst.parent.name=='Hall roof'): continue
    k+=1
    o=inst.object
    try:
        d=o.data
        key=(type(d).__name__, d.name if d else None, len(d.vertices) if hasattr(d,'vertices') else None)
    except Exception as e:
        key=('ERR',str(e)[:60])
    c[key]+=1
    if k in (428,452,458,502,589,0): ex.append((k,key))
print(c); print(ex)
print(rep['tile_plan'])
