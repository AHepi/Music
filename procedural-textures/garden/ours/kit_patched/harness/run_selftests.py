# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Runs the foundation's self-tests on one scene file (Blender side) and writes <out>/selftests_<scene>.json:
#     blender -b --disable-autoexec SCENE.blend --python harness/run_selftests.py -- SET SCENE OUT_FOLDER [tests comma separated] [WIDTHxHEIGHT]
# tests: hook, remove, nothing, legacy_nothing, dial_zero, isolation, determinism, reuse, lighting
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
from harness import cameras, layers, legacy_stack, lighting, selftests  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
set_id, scene_id, out = args[0], args[1], args[2]
tests = (args[3] if len(args) > 3 else 'hook,remove,nothing,dial_zero,isolation,determinism,reuse').split(',')
size = tuple(int(v) for v in args[4].split('x')) if len(args) > 4 else (135, 240)
os.makedirs(out, exist_ok=True)


def fresh():
    k = kit_module.Kit.load(set_id, scene_id=scene_id, strict=False)
    layers.register_templates(k)
    return k


results = {}
t0 = time.time()
k0 = fresh()
cams, _ = cameras.make_all(k0.settings, scene_id)
camera = cams[k0.settings.scenes[0].get('default_camera', 'main')] if k0.settings.scenes[0].get('default_camera') in cams else bpy.context.scene.camera
if k0.settings.scene(scene_id).get('default_camera') in cams:
    camera = cams[k0.settings.scene(scene_id)['default_camera']]
for name in tests:
    t = time.time()
    try:
        k = fresh()
        if name == 'hook':
            results[name] = selftests.hook_all(k)
        elif name == 'remove':
            results[name] = selftests.remove_orders(k)
        elif name == 'nothing':
            results[name] = selftests.do_nothing(k, out, camera, size)
        elif name == 'legacy_nothing':
            stack = legacy_stack.LegacyStack(k)
            k.prepare()
            stack.apply(pieces=True)
            stack.look('rubbish')
            k.set_state(0.85, 0.5)
            results[name] = selftests.do_nothing(k, out, camera, size)
        elif name == 'dial_zero':
            results[name] = selftests.dial_zero(k, out, camera, 'template_b', size)
        elif name == 'isolation':
            roles = k.settings.expand_roles(['wall'])[:1] or list(k.settings.roles)[:1]
            k.register_layer('template_iso', lambda key: __import__('apply.layer_template', fromlist=['x']).build_template(key), slot='A', roles=roles)
            results[name] = selftests.isolation(k, out, camera, 'template_iso', roles, size)
        elif name == 'determinism':
            results[name] = selftests.determinism(k, out, camera, size)
        elif name == 'reuse':
            results[name] = selftests.reuse_smoke(k)
        elif name == 'lighting':
            results[name] = selftests.lighting_matches_earlier(k, out, camera, (270, 480))
    except Exception:
        results[name] = dict(passed=False, error=traceback.format_exc())
    results[name]['seconds'] = round(time.time() - t, 1)
    print('TEST', name, results[name].get('passed'), results[name]['seconds'], flush=True)
json.dump(dict(set=set_id, scene=scene_id, size=list(size), seconds=round(time.time() - t0, 1), results=results), open(os.path.join(out, f'selftests_{scene_id}.json'), 'w'), indent=1, default=str)
print('SELFTESTS DONE', round(time.time() - t0, 1), flush=True)
