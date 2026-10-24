import sys, time, bpy, json, cProfile, pstats
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
from apply import dials
vals=dials.resolve('growth', k.look, k.settings, None, strict=False)
gs.values=vals
pr=cProfile.Profile(); pr.enable()
gs.build()
pr.disable()
pstats.Stats(pr).sort_stats('cumulative').print_stats(12)
e=gs.engine
print('dials', {n: e.get_dial(n) for n in ('amount','distance','g_bg','weeds_amount')})
gs._push()
e.set_dials(g_bg=50.0,g_gut=50.0,g_wall=50.0,g_moss=50.0,g_toad=50.0, amount=1.0,weeds_amount=1.0,cushions_amount=1.0, cam_override_on=1.0, cam_x=0, cam_y=3, cam_z=1.9)
t=time.time()
mats,kind,extra=scatter.evaluated_instances(gs.host)
print('eval', len(kind), round(time.time()-t,2))
print([o.name for o in gs.targets])
for st in ('points_0','kept_0','points_8','kept_8','joined'):
    print(st, e.probe(gs.host, st))
import numpy as np
for f in ('gate','heap_w','fade_d','W','WS','GS','K','F','C','H','HG','dist','likes_0','prob_0'):
    a=e.probe_field(gs.host,f)
    print(f, 'min',round(float(a.min()),3),'max',round(float(a.max()),3),'mean',round(float(a.mean()),3), 'nz', int((a>0).sum()))
img=bpy.data.images.get('WKG sites')
print('sites image', img.size[:], img.generated_type if hasattr(img,'generated_type') else '', img.is_float, img.source, img.has_data)
buf=np.empty(img.size[0]*img.size[1]*4,np.float32); img.pixels.foreach_get(buf)
print('readback', buf.reshape(-1,4).max(axis=0), buf.reshape(-1,4).mean(axis=0))
