import sys, time, bpy
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import kit as kit_module
from masks import bus as bus_module
from harness import layers, legacy_stack
k=kit_module.Kit.load('pit_village_street', scene_id='street', strict=False); bus_module.attach(k)
found,errors=layers.register_builders(k)
print('registered', found, 'errors', {a:b[-300:] for a,b in errors.items()})
k.prepare()
stack=legacy_stack.LegacyStack(k); stack.apply(pieces=True)
keys=[x for x in k.registry]
t=time.time()
try:
    res=k.apply(layers=keys)
    print('applied all', {a:len(b) for a,b in res.items()}, round(time.time()-t,1))
    print('growth plants', len(k.growth.table()))
    k.set_master(0.0); print('master 0 plants', len(k.growth.table()))
    k.set_master(1.0)
    k.remove(); print('removed; leftovers', [o.name for o in bpy.data.objects if o.name.startswith('WKG')])
except Exception as e:
    import traceback; traceback.print_exc()
