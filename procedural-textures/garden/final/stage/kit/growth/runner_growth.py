# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The kit's picture runner (harness/runner.py, unchanged) plus what the growth layer needs to be looked at and counted:
#     blender -b --disable-autoexec SCENE.blend --python growth/runner_growth.py -- JOBS.json OUT_FOLDER
#   * EXTRA CAMERAS named in the job file ("extra_cameras": [{"name", "location", "look_at", "fov_v"}]) so a plant can be looked at from just above and beside it;
#   * the checking view `layer:growth` (every plant plain white light, everything else black) through the runner's own `layer:<key>` view;
#   * a job may say "pieces_json": true: the plants of that picture's camera are written to pieces_<name>.json (position, kind, size of every plant) next to the picture, and
#     the earlier rubbish layer's pieces to rubbish_<name>.json (for the proximity test), and "fire_points" are not needed (the measure reads the set's fire role itself);
#   * a job may say "hide_growth": true to draw the same picture with the growth layer's host hidden.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

import bpy  # noqa: E402

from harness import cameras, runner as kit_runner  # noqa: E402
from masks import debug  # noqa: E402
from growth import apply_growth  # noqa: E402


def install_views():
    original = debug.show_layer

    def show_layer(kit, key):
        if key == apply_growth.LAYER_KEY:
            return apply_growth.show_layer(kit)
        return original(kit, key)
    debug.show_layer = show_layer


def rubbish_table():
    """The earlier rubbish layer's 3D pieces as [{x, y, z, kind}] (world positions of the instances of its host)."""
    host = bpy.data.objects.get('rubbish_scatter')
    if host is None:
        return []
    import numpy as np
    from growth import scatter
    mats, kind, extra = scatter.evaluated_instances(host)
    return [dict(x=round(float(m[3, 0]), 4), y=round(float(m[3, 1]), 4), z=round(float(m[3, 2]), 4), kind='rubbish') for m in mats]


class GrowthRunner(kit_runner.Runner):
    def draw_job(self, job):
        name = job['name']
        host = getattr(self.kit, 'growth', None)
        draw = super().draw_job
        if job.get('hide_growth') and host is not None and host.host is not None:
            host.visible(False)
        draw(job)
        if job.get('pieces_json') and host is not None and host.attached:
            cam = self.cams.get(job.get('camera')) if job.get('camera') else self.scene.camera
            rows = host.table(cam)
            fire = []
            role = (host.section.get('zones_for_report') or {}).get('fire_role')
            if role:
                for obj_name in self.kit.role_map.objects_of([role]):
                    obj = bpy.data.objects[obj_name]
                    fire.append([round(obj.matrix_world.translation.x, 3), round(obj.matrix_world.translation.y, 3)])
            json.dump(dict(camera=job.get('camera'), count=len(rows), pieces=rows, fire_points=fire, kinds=[s['name'] for s in host.kind_specs], calibration={k: v for k, v in host.calibration.items() if k != 'notes'},
                           stats=host.stats), open(os.path.join(self.out, f'pieces_{name}.json'), 'w'))
            json.dump(rubbish_table(), open(os.path.join(self.out, f'rubbish_{name}.json'), 'w'))


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    spec = json.load(open(args[0]))
    out = args[1]
    t0 = time.time()
    install_views()
    runner = GrowthRunner(spec, out)
    for c in spec.get('extra_cameras', []):
        cam = cameras._make('wk_' + c['name'], c['location'], look_at=c.get('look_at'), quaternion_wxyz=c.get('quaternion_wxyz'), fov_vertical=c.get('fov_v', 40.0))
        runner.cams[c['name']] = cam
    jobs = sorted(enumerate(spec['jobs']), key=lambda it: (kit_runner.LOOK_RANK.get(it[1].get('look', 'today'), 2), it[0]))
    for _, job in jobs:
        runner.draw_job(job)
    summary = dict(set=spec['set'], scene=runner.kit.scene_id, jobs=len(jobs), seconds_total=round(time.time() - t0, 1), registered=runner.registered, register_errors=runner.register_errors)
    gs = getattr(runner.kit, 'growth', None)
    if gs is not None:
        summary['growth'] = dict(timings=gs.timings, notes=gs.notes, stats=gs.stats, calibration={k: v for k, v in gs.calibration.items()}, section=gs.section)
    json.dump(summary, open(os.path.join(out, 'run_summary.json'), 'w'), indent=1, default=str)
    print('ALL JOBS DONE', summary['seconds_total'], flush=True)


if __name__ == '__main__':
    main()
