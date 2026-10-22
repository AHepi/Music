import sys, json, time
args = sys.argv[sys.argv.index('--')+1:]
kitdir = args[0]
sys.path.insert(0, kitdir); sys.dont_write_bytecode = True
import bpy
import apply_weathering as aw
t = time.time()
w = aw.apply('japanese_courtyard', 'mossy_courtyard_rough', pieces=False, strict=False, earlier=False)
k = w.kit
print('APPLY seconds', round(time.time()-t,1), {key: len(v['materials']) for key, v in k.active.items()})
for name in ('Hall plaster', 'Back wall, left', 'Right wall behind hall', 'Rock 0', 'Stepping stone 0', 'Hall posts', 'Hall roof', 'Lantern cap'):
    o = bpy.data.objects.get(name)
    print('PROPS', name, k.role_map.primary.get(name), {kk: round(o[kk], 3) for kk in sorted(o.keys()) if kk.startswith('wk_wallgrowth_') or kk.startswith('wk_foot_') or kk in ('wk_frame_id', 'wk_role_id')})
print('FRAMES', json.dumps(k.mask_pack.manifest['frames']['frame_of_object']) if k.mask_pack else None)
print('ROOF', {m: [s for s in (k.chains[m].stages if m in k.chains else [])] if False else (sorted(k.chains[m].stages.keys()) if m in k.chains and isinstance(k.chains[m].stages, dict) else 'chain') for m in ('CT / Ceramic painterly surface', 'CT / Timber painterly surface')})
