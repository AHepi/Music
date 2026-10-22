# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Draws the test set (or a part of it) of one look on the rented machine and brings the pictures back: write the job files, send what changed, one Blender run per scene file,
# bring back one tar of JPG, JSON and the PNG a measure needs. Every call also measures how long the whole run took (written next to the pictures as run_time.json).
#   python3 -I harness/run_testset.py SET_ID LOOK OUT_ROOT [--scenes id,id] [--parts t22,close,plates,masks] [--tag r1] [--layers a,b] [--today] [--maskviews]
# Pictures land in OUT_ROOT/<tag>/<scene id>/. The remote folder is cleared before every run (a stale picture can never come back), states start with 'today' (the runner draws the
# look 'today' jobs first; --today adds one small 'today' picture per scene so every run starts there).
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from harness import jobs as jobs_module, remote  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {}
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith('--'):
            nxt = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--') else True
            opts[a] = nxt
    set_id, look, out_root = args[0], args[1], args[2]
    for v in opts.values():
        if isinstance(v, str) and v in args:
            args.remove(v)
    settings = settings_module.load_set(set_id)
    scenes = opts['--scenes'].split(',') if '--scenes' in opts else [s['id'] for s in settings.scenes]
    parts = tuple(opts['--parts'].split(',')) if '--parts' in opts else ('t22', 'close', 'plates', 'masks')
    tag = opts.get('--tag', 'r1')
    layer_keys = tuple(opts['--layers'].split(',')) if '--layers' in opts else ()
    started = time.time()
    summary = {}
    for scene in settings.scenes:
        if scene['id'] not in scenes:
            continue
        extra = []
        if '--today' in opts:
            extra.append(dict(name=f'today_{scene["id"]}', camera=scene.get('default_camera'), light='A', state='wet', look='today', view='beauty', size=[540, 960, 16], group='today', scene=scene['id']))
        if '--maskviews' in opts:
            from harness import testset
            extra += testset.mask_view_jobs(settings, scene['id'])
        job_dir = os.path.join(out_root, tag, '_jobs')
        files = jobs_module.write(settings, [look], job_dir, parts=parts, scenes=[scene['id']], extra_jobs=extra, layer_keys=layer_keys)
        if not files:
            continue
        local_out = os.path.join(out_root, tag, scene['id'])
        remote_out = f'/workspace/wk_out/{set_id}_{look.replace(":", "_").replace(",", "+")}_{tag}_{scene["id"]}'
        t = time.time()
        result = remote.run_batch(scene['file'], list(files.values()), remote_out, local_out)
        result['wall_seconds'] = round(time.time() - t, 1)
        summary[scene['id']] = result
        print(scene['id'], result, flush=True)
    summary['total_seconds'] = round(time.time() - started, 1)
    os.makedirs(os.path.join(out_root, tag), exist_ok=True)
    json.dump(summary, open(os.path.join(out_root, tag, 'run_time.json'), 'w'), indent=1)
    print('DONE', summary['total_seconds'], flush=True)


if __name__ == '__main__':
    main()
