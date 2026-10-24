# Integrator: draws one look of the kit's test set for ONE scene on the rented machine with the growth runner (the kit's runner plus the growth layer's views and plant lists).
#   python3 -I run_round.py LOOK OUT_ROOT TAG SCENE [--layers a,b] [--parts t22,close,plates,masks] [--pieces] [--today]
import json, os, sys, time
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import jobs as jobs_module, remote

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = {}
for i, a in enumerate(sys.argv[1:], 1):
    if a.startswith('--'):
        nxt = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--') else True
        opts[a] = nxt
look, out_root, tag, scene_id = args[:4]
for v in opts.values():
    if isinstance(v, str) and v in args[4:]:
        args.remove(v)
settings = settings_module.load_set('pit_village_street')
scene = next(s for s in settings.scenes if s['id'] == scene_id)
parts = tuple(opts['--parts'].split(',')) if '--parts' in opts else ('t22', 'close', 'plates', 'masks')
layers = tuple(opts['--layers'].split(',')) if '--layers' in opts else ()
extra = []
if '--today' in opts:
    extra.append(dict(name=f'today_{scene_id}', camera=scene.get('default_camera'), light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene=scene_id))
job_dir = os.path.join(out_root, tag, '_jobs')
files = jobs_module.write(settings, [look], job_dir, parts=parts, scenes=[scene_id], extra_jobs=extra, layer_keys=layers)
if '--pieces' in opts:        # the plant lists of the plate cameras (for the zone measure)
    for path in files.values():
        spec = json.load(open(path))
        for j in spec['jobs']:
            if j.get('group') == 'plate' and 'behind' not in j['name']:
                j['pieces_json'] = True
        json.dump(spec, open(path, 'w'), indent=1)
local_out = os.path.join(out_root, tag, scene_id)
remote_out = f'/workspace/wk_out/int_{look.replace(":", "_")}_{tag}_{scene_id}'
t = time.time()
result = remote.run_batch(scene['file'], list(files.values()), remote_out, local_out, runner_script=os.path.join(KIT, 'growth', 'runner_growth.py'))
result['wall_seconds'] = round(time.time() - t, 1)
print(scene_id, result, flush=True)
json.dump(result, open(os.path.join(out_root, tag, f'run_time_{scene_id}.json'), 'w'))
