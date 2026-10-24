import sys, time, bpy, json
import numpy as np
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import kit as kit_module
from masks import bus as bus_module
from growth import apply_growth, local_masks, pieces, scatter
k=kit_module.Kit.load('pit_village_street', scene_id='street', strict=False)
bus_module.attach(k)
apply_growth.register(k)
k.prepare()
gs=k.growth
t=time.time()
lib=pieces.Library(); lib.build(['grass','moss_string']); print('lib build',round(time.time()-t,2))
masks=local_masks.read_masks(k.mask_pack, apply_growth.MASK_NAMES)
for n,a in masks.items(): print(n, a.shape, round(float(a.min()),3), round(float(a.max()),3), round(float(a.mean()),3))
z,has,role=local_masks.read_ground(k.mask_pack)
print('ground', z.shape, has.sum(), np.unique(role))
