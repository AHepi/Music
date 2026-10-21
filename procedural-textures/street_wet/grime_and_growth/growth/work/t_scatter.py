import sys, time, bpy, json
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import kit as kit_module
from masks import bus as bus_module
from growth import apply_growth
t0=time.time()
k=kit_module.Kit.load('pit_village_street', scene_id='street', strict=False)
bus_module.attach(k)
print('kit loaded', round(time.time()-t0,2))
print(apply_growth.register(k))
k.prepare()
t1=time.time()
res=k.apply(layers=['growth'])
print('applied', res, round(time.time()-t1,2))
gs=k.growth
print('timings', gs.timings, 'stats', gs.stats)
print('calibration', json.dumps({a:b for a,b in gs.calibration.items()}, default=str)[:1500])
t2=time.time()
rows=gs.table()
print('table', len(rows), round(time.time()-t2,2))
from collections import Counter
print(Counter(r['species'] for r in rows))
import numpy as np
if rows:
    ys=np.array([r['y'] for r in rows]); xs=np.array([r['x'] for r in rows])
    print('y range', ys.min(), ys.max(), 'x range', xs.min(), xs.max())
    print(rows[:3])
mats,kind,extra=__import__('growth.scatter',fromlist=['x']).evaluated_instances(gs.host)
print(mats[0])
