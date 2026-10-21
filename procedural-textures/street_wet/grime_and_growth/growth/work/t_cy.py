import sys, bpy, numpy as np
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import kit as kit_module
from masks import bus as bus_module
from growth import apply_growth, local_masks
k=kit_module.Kit.load('japanese_courtyard', scene_id='courtyard', strict=False); bus_module.attach(k); apply_growth.register(k); k.prepare()
k.apply(layers=['growth']); gs=k.growth
rows=gs.table()
low=[r for r in rows if r['z']<-0.1]
print(len(rows), 'below -0.1:', len(low))
m=gs.arrays['masks']; g=gs.arrays['grid']
for r in low[:5]:
    ix=int((r['x']-g['x'][0])/g['dot_m']); iy=int((r['y']-g['y'][0])/g['dot_m'])
    print(r['x'],r['y'],r['z'], r['species'], 'above_water', m['above_water'][iy,ix], 'ground z', gs.arrays['ground_z'][iy,ix], 'moss_site', m['moss_site'][iy,ix])
print('above_water stats', m['above_water'].min(), m['above_water'].max(), (m['above_water']<0.03).mean())
import collections
print(collections.Counter(o.name for o in gs.targets))
