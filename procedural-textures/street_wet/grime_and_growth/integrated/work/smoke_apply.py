# local smoke test of apply_weathering (build only, nothing drawn): python blender -b FILE --python smoke_apply.py -- SET LOOK OUT_JSON
import sys, time, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0, KIT)
args = sys.argv[sys.argv.index('--')+1:]
set_id, look, out = args[0], args[1], args[2]
import bpy, apply_weathering as aw
t=time.time()
w = aw.apply(set_id, look, state='wet')
t1=time.time()-t
rep = w.report()
print('APPLY SECONDS', round(t1,1))
print('PROBLEMS', json.dumps(rep['problems'], indent=1)[:3000])
print('layers', {k:(v['on'],v['materials']) for k,v in rep['layers'].items()})
print('verify', w.kit.verify()[:5])
print('pieces', rep['pieces'])
t=time.time(); w.remove(); print('REMOVE SECONDS', round(time.time()-t,1))
left=[o.name for o in bpy.data.objects if o.name.startswith('WKG')]
print('left WKG objects', left[:5])
json.dump(dict(apply_seconds=t1, report={k:v for k,v in rep.items() if k!='log'}, log=rep['log']), open(out,'w'), indent=1, default=str)
