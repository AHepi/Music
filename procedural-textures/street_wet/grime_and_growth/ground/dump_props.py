import sys, os, json
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
import bpy
from harness import runner as R
scene_id=sys.argv[sys.argv.index('--')+2] if len(sys.argv)>sys.argv.index('--')+2 else 'street'
out=sys.argv[sys.argv.index('--')+1]
r=R.Runner(dict(set='pit_village_street', scene=scene_id, pack=True, feature_dirs=[], jobs=[]), out)
r.set_look('kit:dirt,groundcracks,groundmoss,iron')
res={}
for m in bpy.data.materials:
    t=m.node_tree
    if t is None: continue
    items=[]
    for node in t.nodes:
        if node.type=='GROUP' and node.get('wk') in ('dirt','groundcracks','groundmoss','iron'):
            items.append((node['wk'], node.node_tree.name, len(node.node_tree.nodes)))
    if items: res[m.name]=items
for k,v in res.items(): print('MAT',k,v)
json.dump(res, open(out+'/variants.json','w'), indent=1)
