# Runs the bus and scale tests on one scene (Blender side):  blender -b SCENE.blend --python harness/run_bus_tests.py -- SET SCENE OUT [tests] [camera]
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

import bpy  # noqa: E402

from apply import kit as kit_module  # noqa: E402
from harness import bus_tests, cameras, layers  # noqa: E402
from masks import bus as bus_module  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
set_id, scene_id, out = args[0], args[1], args[2]
tests = (args[3] if len(args) > 3 else 'ground,walls,dots,nodes').split(',')
os.makedirs(out, exist_ok=True)
results = {}
ORIGINAL_CAMERA = bpy.context.scene.camera


def fresh():
    bpy.context.scene.camera = ORIGINAL_CAMERA
    k = kit_module.Kit.load(set_id, scene_id=scene_id, strict=False)
    bus_module.attach(k)
    layers.register_templates(k)
    return k


for name in tests:
    t = time.time()
    try:
        k = fresh()
        if name == 'ground':
            results[name] = bus_tests.bus_ground(k, out)
        elif name == 'walls':
            results[name] = bus_tests.bus_walls(k, out)
        elif name == 'dots':
            cams, _ = cameras.make_all(k.settings, scene_id)
            entry = k.settings.scene(scene_id).get('default_camera', 'main')
            cam = cams.get(entry) or bpy.context.scene.camera
            results[name] = bus_tests.dot_table(k, out, cam, k.settings.get('plate')['size'][1])
        elif name == 'nodes':
            from masks import scale
            scale.build_scale_group()
            scale.build_mark_width_group()
            k.prepare()
            k.apply(layers=['template_a'])
            results[name] = bus_tests.no_forbidden_nodes()
    except Exception:
        results[name] = dict(passed=False, error=traceback.format_exc())
    results[name]['seconds'] = round(time.time() - t, 1)
    print('TEST', name, results[name].get('passed'), flush=True)
json.dump(dict(set=set_id, scene=scene_id, results=results), open(os.path.join(out, f'bus_tests_{scene_id}.json'), 'w'), indent=1, default=str)
print('BUS TESTS DONE', flush=True)
