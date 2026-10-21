import sys, json
KIT='proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy
from apply import kit as km, dials
from harness import layers
out = sys.argv[sys.argv.index('--')+1]
k = km.Kit.load('pit_village_street', scene_id='street', strict=False)
layers.register_builders(k)
look = json.load(open(KIT+'/presets/sooty_1926.json'))
court = json.load(open(KIT+'/presets/mossy_courtyard_kept.json'))
res = {}
for key, t in dials.TABLE.layers.items():
    if key in ('template_a','template_b','template_c'): continue
    res[key] = dict(meta={m:v for m,v in t.meta.items() if isinstance(v,(str,int,float,list))}, rows=[dict(r, street=look['layers'].get(key,{}).get(r['name']), courtyard=court['layers'].get(key,{}).get(r['name'])) for r in t.rows.values()], slot=k.registry[key].slot if key in k.registry else None)
json.dump(res, open(out,'w'), indent=1, default=str)
print('DIALS', {k:len(v['rows']) for k,v in res.items()})
