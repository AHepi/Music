# usage: blender -b courtyard.blend -P smoke_apply.py -- KITDIR OUT.json [SETFILE]
import sys, json, time
args = sys.argv[sys.argv.index('--')+1:]
kitdir, out = args[0], args[1]
setref = args[2] if len(args) > 2 else 'japanese_courtyard'
sys.path.insert(0, kitdir); sys.dont_write_bytecode = True
import bpy
import apply_weathering as aw
t = time.time()
w = aw.apply(setref, 'mossy_courtyard_rough', pieces=False, strict=False, earlier=False)
rep = w.report()
res = {'seconds': round(time.time()-t, 1), 'keys': sorted(rep.keys())}
k = w.kit
res['layers'] = {key: sorted(v['materials']) for key, v in k.active.items()}
roof_mats = [m for m in bpy.data.materials.keys() if m.startswith('CT / Ceramic') or m.startswith('CT / Timber')]
res['roof_material_chains'] = {m: (sorted(k.chains[m].stages.keys()) if m in k.chains and hasattr(k.chains[m], 'stages') and isinstance(k.chains[m].stages, dict) else [s.key for s in k.chains[m].stages] if m in k.chains else None) for m in roof_mats}
res['skipped'] = k.skipped
json.dump(res, open(out, 'w'), indent=1, sort_keys=True, default=str)
print('SMOKE', out, res['seconds'], 's', {key: len(v) for key, v in res['layers'].items()})
print('ROOF', json.dumps(res['roof_material_chains'], default=str))
