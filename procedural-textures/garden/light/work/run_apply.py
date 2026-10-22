import bpy, sys, json, os
sys.dont_write_bytecode = True
HERE='proc-work/garden/light'
sys.path.insert(0, HERE)
import stage_light
a = sys.argv[sys.argv.index('--')+1:]
look = a[0]
opts = {'look': look}
if len(a) > 1: opts.update(json.loads(a[1]))
rep = stage_light.apply(opts)
print(json.dumps({k: v for k, v in rep.items() if k != 'log'}, indent=1)[:3000])
if len(a) > 2 and a[2] == 'evening':
    print(json.dumps(stage_light.apply_evening({'look': look}), indent=1)[:1500])
