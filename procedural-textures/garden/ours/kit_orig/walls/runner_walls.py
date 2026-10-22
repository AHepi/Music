# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The kit's picture runner (harness/runner.py, unchanged) plus EXTRA CAMERAS named in the job file, so a layer can be looked at face-on, from a doorstep, or with a flat
# (orthographic) camera that the set's own camera table does not have. Everything else (looks, views, states, files) is the kit runner's own.
#     blender -b --disable-autoexec SCENE.blend --python walls/runner_walls.py -- JOBS.json OUT_FOLDER
# The job file may carry  "extra_cameras": [{"name": "face_on", "location": [x, y, z], "look_at": [x, y, z], "fov_v": 50, "ortho_scale": 7.5 (optional: flat camera)}]
# and a job then says "camera": "face_on". The camera's plate dot is the job's plate_height (so marks are sized for the picture asked for).
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from harness import cameras, runner as kit_runner  # noqa: E402


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    spec = json.load(open(args[0]))
    out = args[1]
    t0 = time.time()
    runner = kit_runner.Runner(spec, out)
    for c in spec.get('extra_cameras', []):
        cam = cameras._make('wk_' + c['name'], c['location'], look_at=c.get('look_at'), quaternion_wxyz=c.get('quaternion_wxyz'), fov_vertical=c.get('fov_v', 40.0))
        if c.get('ortho_scale'):
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = c['ortho_scale']
        runner.cams[c['name']] = cam
    jobs = sorted(enumerate(spec['jobs']), key=lambda it: (kit_runner.LOOK_RANK.get(it[1].get('look', 'today'), 2), it[0]))
    for _, job in jobs:
        runner.draw_job(job)
    summary = dict(set=spec['set'], scene=runner.kit.scene_id, jobs=len(jobs), seconds_total=round(time.time() - t0, 1), registered=runner.registered,
                   register_errors=runner.register_errors, camera_notes=runner.cam_notes, kit_report=runner.kit.report() if runner.kit.prepared else {})
    json.dump(summary, open(os.path.join(out, 'run_summary.json'), 'w'), indent=1, default=str)
    print('ALL JOBS DONE', summary['seconds_total'], flush=True)


if __name__ == '__main__':
    main()
