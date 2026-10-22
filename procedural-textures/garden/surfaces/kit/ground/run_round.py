# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# DRAWS ONE ROUND OF THE GROUND LAYERS' TEST PICTURES on the rented machine and brings them back (plain Python here; the drawing is the kit's own runner there).
#     python3 -I ground/run_round.py SET_ID LOOK OUT_ROOT TAG [--scenes a,b] [--parts t22,plates,masks,close] [--no-elements] [--layers dirt,groundcracks,groundmoss,iron]
# For each scene file of the set it writes one job list and draws it in one run:
#   * the test set of the kit (harness/testset.py): the 22 lighting pictures, the plates, the helper pictures (class, depth, the layers' own whole Mask pictures for the joint
#     measure and the zones measure), and optionally the close views;
#   * for every plate camera and every named part of every ground layer, that part's own Mask picture at plate size (part_<layer>_<part>_<camera>.png), the pictures the
#     readability measure (P3) and the share measures use. A part is shown through the layer's show_part dial, nothing else changes.
# Pictures land in OUT_ROOT/TAG/<scene id>/ (PNG kept where a measure needs exact numbers). Disk is tight: the PNGs are deleted by measure_ground.py --clean when measured.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from harness import jobs as jobs_module, remote, testset  # noqa: E402
from ground import ground_names as gc  # noqa: E402

LAYERS = ('dirt', 'groundcracks', 'groundmoss', 'iron')


def part_jobs(settings, scene_id, look, layers):
    ts = settings.get('test_set') or {}
    plate = settings.get('plate') or {}
    out = []
    for camera, w, h in testset._plate_list(ts, scene_id, settings):
        light = next((l for c, l, s in ts.get('plates', []) if c == camera), 'A')
        for layer in layers:
            for part, number in gc.PART_NUMBERS[layer].items():
                out.append(dict(name=f'part_{layer}_{part}_{camera}', camera=camera, light=light, state='wet', look=look, view=f'layer:{layer}', size=[w, h, 1], group='part',
                                plate_height=h, scene=scene_id, dials={layer: {'show_part': number}}))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {}
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith('--'):
            nxt = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--') else True
            opts[a] = nxt
    for v in opts.values():
        if isinstance(v, str) and v in args:
            args.remove(v)
    set_id, look, out_root, tag = args[:4]
    settings = settings_module.load_set(set_id)
    scenes = opts['--scenes'].split(',') if '--scenes' in opts else [s['id'] for s in settings.scenes]
    parts = tuple(opts['--parts'].split(',')) if '--parts' in opts else ('t22', 'plates', 'masks')
    layers = tuple(opts['--layers'].split(',')) if '--layers' in opts else LAYERS
    started = time.time()
    summary = {}
    for scene in settings.scenes:
        if scene['id'] not in scenes:
            continue
        extra = [] if '--no-elements' in opts else part_jobs(settings, scene['id'], look, layers)
        job_dir = os.path.join(out_root, tag, '_jobs')
        files = jobs_module.write(settings, [look], job_dir, parts=parts, scenes=[scene['id']], extra_jobs=extra, layer_keys=layers)
        if not files:
            continue
        local_out = os.path.join(out_root, tag, scene['id'])
        remote_out = f'/workspace/wk_out/ground_{set_id}_{tag}_{scene["id"]}'
        t = time.time()
        result = remote.run_batch(scene['file'], list(files.values()), remote_out, local_out)
        result['wall_seconds'] = round(time.time() - t, 1)
        summary[scene['id']] = result
        print(scene['id'], result, flush=True)
    summary['total_seconds'] = round(time.time() - started, 1)
    json.dump(summary, open(os.path.join(out_root, tag, 'run_time.json'), 'w'), indent=1)
    print('DONE', summary['total_seconds'], flush=True)


if __name__ == '__main__':
    main()
