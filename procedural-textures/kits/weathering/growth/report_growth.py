# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE PLANT REPORT (Blender code): writes pieces.json, the position, kind and size of every plant of a picture, for the zone test (P6), the litter-proximity test, the count budget
# and the cover numbers (P4). One file per camera.
#     blender -b --disable-autoexec SCENE.blend --python growth/report_growth.py -- SET_ID SCENE_ID OUT_FOLDER [CAMERA,CAMERA ...] [LOOK]
# Cameras default to the plate cameras of the set's test set that belong to this scene (camera 'from the file' = the scene's own camera). Each file, pieces_<camera>.json:
#   {camera, count, pieces: [{x, y, z, kind ('weed_<species>' or 'moss_cushion'), species, size_m (width of the plant as drawn), scale, distance (to the camera)}], kinds (the kind table:
#    index -> species), fire_points (xy of the set's fire role objects, for the fire-radius test), calibration (the gains and the target counts), stats (the window the counts were made in)}
# The earlier litter layer's pieces (if the set has one) are written to rubbish_<camera>.json beside it. The runner (runner_growth.py) writes the same files for any picture of a job list.
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import kit as kit_module  # noqa: E402
from harness import cameras, legacy_stack  # noqa: E402
from masks import bus as bus_module  # noqa: E402
from growth import apply_growth, runner_growth  # noqa: E402


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    set_id, scene_id, out = args[0], args[1], args[2]
    names = args[3].split(',') if len(args) > 3 and args[3] else None
    look = args[4] if len(args) > 4 else None
    os.makedirs(out, exist_ok=True)
    kit = kit_module.Kit.load(set_id, scene_id=scene_id, look=look, strict=False)
    bus_module.attach(kit)
    cams, notes = cameras.make_all(kit.settings, scene_id)
    apply_growth.register(kit)
    kit.prepare()
    if kit.settings.legacy():
        stack = legacy_stack.LegacyStack(kit)
        stack.apply(pieces=True)
    kit.apply(layers=['growth'])
    system = kit.growth
    ts = kit.settings.get('test_set') or {}
    if names is None:
        names = [c for c, light, state in ts.get('plates', []) if ts.get('scene_of', {}).get(c, scene_id) == scene_id] or list(cams)[:1]
    written = {}
    for name in names:
        cam = cams[name]
        rows = system.table(cam)
        fire = []
        role = (system.section.get('zones_for_report') or {}).get('fire_role')
        if role:
            for obj_name in kit.role_map.objects_of([role]):
                o = bpy.data.objects[obj_name]
                fire.append([round(o.matrix_world.translation.x, 3), round(o.matrix_world.translation.y, 3)])
        json.dump(dict(camera=name, count=len(rows), pieces=rows, kinds=[s['name'] for s in system.kind_specs], fire_points=fire,
                       calibration={k: v for k, v in system.calibration.items() if k != 'notes'}, stats=system.stats), open(os.path.join(out, f'pieces_{name}.json'), 'w'))
        json.dump(runner_growth.rubbish_table(), open(os.path.join(out, f'rubbish_{name}.json'), 'w'))
        written[name] = len(rows)
    print('REPORT DONE', written, flush=True)


if __name__ == '__main__':
    main()
