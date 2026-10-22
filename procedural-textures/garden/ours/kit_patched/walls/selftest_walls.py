# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE SELF-TEST of the walls layers (Blender side). It calls the foundation's own tests for every walls layer that has a role in the set, on one scene, and writes selftest_walls.json:
#     blender -b --disable-autoexec SCENE.blend --python walls/selftest_walls.py -- SET_ID_OR_FILE SCENE_ID OUT_FOLDER CONFIG.json
# CONFIG.json: {"layers": ["soot"] (optional: only these),"size": [w, h], "layer_sizes": {"<layer>": [w, h]}, "samples": 4, "camera": "<default camera name>", "layer_cameras": {"<layer>": "<camera name>"}, "look": "<look name or file, optional>",
#               "stack": true|false (put the set's earlier layers on first, as the real pictures have them)}
# Per layer: dial_zero (at Amount 0 the picture is identical; the picture at Amount 1 does change: the foundation's test), isolation (the layer alone changes only the dots of its
# roles), plus the layer's node count and the forbidden-node check. Then for all layers together: reuse_smoke (every layer goes in and out without a crash, materials restored
# exactly), master dial 0 (set_master(0) with every layer in: the same picture as no layer), determinism (two draws identical). A layer the set gives no role is reported as 'no role'.
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

import bpy  # noqa: E402

from apply import kit as kit_module  # noqa: E402
from harness import cameras, legacy_stack, render, selftests  # noqa: E402
from masks import bus as bus_module  # noqa: E402
from walls import apply_walls, walls_common  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
set_ref, scene_id, out = args[0], args[1], args[2]
config = json.load(open(args[3])) if len(args) > 3 else {}
size = tuple(config.get('size', (135, 240)))
samples = config.get('samples', 4)
os.makedirs(out, exist_ok=True)


def fresh(with_stack=None):
    with_stack = config.get('stack', False) if with_stack is None else with_stack
    k = kit_module.Kit.load(set_ref, scene_id=scene_id, look=config.get('look'), strict=False)
    bus_module.attach(k)
    apply_walls.register(k)
    if with_stack:
        k.prepare()
        stack = legacy_stack.LegacyStack(k)
        if stack.present():
            stack.apply(pieces=False)
            stack.look('rubbish')
            k.set_state(0.85, 0.5)
            return k, stack
    return k, None


k0, stack0 = fresh()
cams, _ = cameras.make_all(k0.settings, scene_id)


def release(k, stack):
    """Everything off again (the kit's own remove, then the earlier layers' module state), so the next test starts from the scene as it was."""
    try:
        k.remove()
    finally:
        if stack is not None:
            stack.reset()


release(k0, stack0)
default_camera = cams.get(config.get('camera')) or cams.get(k0.settings.scene(scene_id).get('default_camera')) or bpy.context.scene.camera
results, t0 = {}, time.time()
keys = [k for k in apply_walls.keys() if not config.get('layers') or k in config['layers']]
for key in keys:
    t = time.time()
    entry = {}
    k = stack = None
    try:
        k, stack = fresh()
        roles = k.settings.layer_roles(key)
        if not roles:
            entry = dict(passed=True, note='no role in this set: the layer goes into no material')
        else:
            camera = cams.get(config.get('layer_cameras', {}).get(key)) or default_camera
            lsize = tuple(config.get('layer_sizes', {}).get(key, size))
            dz = selftests.dial_zero(k, out, camera, key, lsize, samples)
            entry['dial_zero'] = dict(identical_16bit=dz['identical_16bit'], passed_zero=dz['at_amount_0']['share_over_one_step'] <= 0.01, acts_at_amount_1_share_changed=dz['acts_at_amount_1']['share_changed'],
                                      acts_max_diff=dz['acts_at_amount_1']['max_diff'], at_amount_0=dz['at_amount_0'])
            release(k, stack)
            k, stack = fresh()
            iso = selftests.isolation(k, out, camera, key, roles, lsize, samples)
            entry['isolation'] = iso
            if not iso.get('dots_acting'):
                entry['note'] = 'the layer drew nothing in this view, so isolation could not be proven (no dot changed outside its roles either)'
            release(k, stack)
            k, stack = fresh()
            k.prepare()
            k.apply(layers=[key])
            tree = k.registry[key].tree
            entry['nodes'], entry['noise_nodes'] = walls_common.count_nodes(tree)
            entry['forbidden_nodes'] = walls_common.forbidden_nodes(tree)
            entry['passed'] = bool(entry['dial_zero']['passed_zero'] and iso.get('passed') and not entry['forbidden_nodes'])
    except Exception:
        entry = dict(passed=False, error=traceback.format_exc())
    finally:
        if k is not None:
            try:
                release(k, stack)
            except Exception:
                entry['release_error'] = traceback.format_exc()
    entry['seconds'] = round(time.time() - t, 1)
    results[key] = entry
    print('LAYER', key, entry.get('passed'), entry['seconds'], flush=True)

for name in ('reuse', 'master_zero', 'determinism'):
    t = time.time()
    k = stack = None
    try:
        if name == 'reuse':
            k, stack = fresh(False)                                            # the foundation's reuse test compares the materials before and after, so no earlier layers on
            res = selftests.reuse_smoke(k, layers=keys)
        elif name == 'master_zero':
            k, stack = fresh()
            k.prepare()
            render.draw(f'{out}/mz_base.png', size[0], size[1], samples, default_camera)
            base = render.read(f'{out}/mz_base.png')
            k.apply(layers=keys)
            k.set_master(0.0)
            render.draw(f'{out}/mz_zero.png', size[0], size[1], samples, default_camera)
            zero = render.read(f'{out}/mz_zero.png')
            cmp = render.compare(base, zero)
            res = dict(passed=cmp['share_over_one_step'] <= 0.01, identical_16bit=cmp['max_diff'] == 0.0, **cmp)
        else:
            k, stack = fresh()
            k.prepare()
            k.apply(layers=keys)
            res = selftests.determinism(k, out, default_camera, size, samples)
    except Exception:
        res = dict(passed=False, error=traceback.format_exc())
    finally:
        if k is not None:
            try:
                release(k, stack)
            except Exception:
                pass
    res['seconds'] = round(time.time() - t, 1)
    results[name] = res
    print('TEST', name, res.get('passed'), res['seconds'], flush=True)

summary = dict(set=set_ref, scene=scene_id, size=list(size), samples=samples, seconds=round(time.time() - t0, 1), layers=keys, all_passed=all(v.get('passed') for v in results.values()), results=results)
json.dump(summary, open(os.path.join(out, 'selftest_walls.json'), 'w'), indent=1, default=str)
print('SELFTEST DONE', summary['all_passed'], flush=True)
