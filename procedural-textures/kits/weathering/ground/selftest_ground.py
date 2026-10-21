# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GROUND LAYERS' SELF-TESTS (Blender side; they run on the rented machine through run_script). It uses the foundation's own tests where they fit and adds the ones a real layer needs.
#     blender -b --disable-autoexec SCENE.blend --python ground/selftest_ground.py -- SET SCENE OUT_FOLDER [layers comma separated] [WIDTHxHEIGHT]
# For each ground layer in the set (a layer whose roles the set leaves empty is reported 'no roles' and skipped, as a set of gravel and earth does for cracks and iron):
#   dial_zero    the layer drawn on strong dial values (so it surely acts) differs from the plain picture, and at Amount 0 the picture is IDENTICAL to the plain one (16 bit)
#   isolation    a layer alone changes only the dots of its own roles (its Mask view, drawn in plain light, is zero outside them; the class picture says which dots are which role)
#   remove       taking the layer out (in any order, twice) leaves every material exactly as the snapshot says (graph signatures)
# and for the scene as a whole:
#   determinism  two draws of the same picture with all the layers in are identical
#   reuse_smoke  every ground layer goes in and out again without a crash on this set; materials restored exactly
# Pictures are small (default 270 x 480, 4 samples). The result is written to OUT_FOLDER/selftest_ground_<scene>.json.
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
from harness import cameras, layers as layer_module, render, selftests  # noqa: E402
from ground import ground_common as gc  # noqa: E402

# dial values that make every element of a layer act somewhere in view (the layers' own defaults are shy by design)
STRONG = {
    'dirt': dict(film=2.0, film_darkness=0.4, polish=1.0, water_marks=1.0, rust_halo=1.0, drum_ring=1.0, tar_patches=1.0, tar_splash=1.0, scrub_strip=1.0, tar_max_share=0.06),
    'groundcracks': dict(flag_fine_share=0.5, flag_broken_share=0.2, flag_tilt_share=0.3, corner_chip_share=0.5, kerb_chip_share=0.6, sett_disturbed_share=0.3, open_joint_share=0.4, missing_share=0.02),
    'groundmoss': dict(joint_share=0.3, patch_moss=1.0, algae_fan=1.0, liverwort=1.0, far_band=1.0),
    'iron': dict(rust_cover=0.8, collar_rust=1.0, base_ring=1.0, shoe_streak=1.0, drum_rust=1.0, heat_scale=1.0, soot_halo=1.0),
}


def fresh(set_id, scene_id, look=None):
    k = kit_module.Kit.load(set_id, scene_id=scene_id, strict=False, look=look)
    try:
        from masks import bus as bus_module
        bus_module.attach(k)
    except Exception:
        pass
    layer_module.register_templates(k)
    layer_module.register_builders(k)
    return k


def strong_overrides(layer, extra=None):
    values = dict(STRONG.get(layer, {}))
    values.update(extra or {})
    return {layer: values}


def dial_zero(k, out, camera, layer, size, samples=4):
    w, h = size
    k.prepare()
    render.draw(f'{out}/dz_base_{layer}.png', w, h, samples, camera)
    base = render.read(f'{out}/dz_base_{layer}.png')
    k.apply(layers=[layer], overrides=strong_overrides(layer))
    render.draw(f'{out}/dz_on_{layer}.png', w, h, samples, camera)
    on = render.read(f'{out}/dz_on_{layer}.png')
    k.set_dials(layer, amount=0.0)
    render.draw(f'{out}/dz_zero_{layer}.png', w, h, samples, camera)
    zero = render.read(f'{out}/dz_zero_{layer}.png')
    # the master dial at 0 too (every layer in at once is the integrator's test; here only this layer)
    k.set_dials(layer, amount=1.0)
    k.set_master(0.0)
    render.draw(f'{out}/dz_master_{layer}.png', w, h, samples, camera)
    master = render.read(f'{out}/dz_master_{layer}.png')
    k.set_master(1.0)
    acts, nothing, nothing_master = render.compare(base, on), render.compare(base, zero), render.compare(base, master)
    k.remove()
    for name in ('base', 'on', 'zero', 'master'):
        try:
            os.remove(f'{out}/dz_{name}_{layer}.png')
        except OSError:
            pass
    return dict(passed=selftests._same(nothing) and selftests._same(nothing_master) and acts['share_changed'] > 0.0, identical_16bit_at_amount_0=nothing['max_diff'] == 0.0,
                identical_16bit_master_0=nothing_master['max_diff'] == 0.0, acts_on_strong_values=acts, at_amount_0=nothing, at_master_0=nothing_master)


def isolation(k, out, camera, layer, size):
    roles = k.layer_role_names(layer)
    k.registry[layer].roles = roles                                                # a layer's own roles
    res = selftests.isolation(k, out, camera, layer, roles, size)
    return res


def remove_orders(k, keys):
    from apply import chain as chain_module
    k.prepare()
    before = {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree is not None}
    k.apply(layers=list(keys))
    problems = []
    for key in list(reversed(keys)) + [keys[0], keys[-1]]:                          # in another order, and twice
        k.remove(key)
        problems += k.verify()
    k.remove()
    after = {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree is not None}
    differ = [m for m in before if before[m] != after.get(m)]
    return dict(passed=not problems and not differ, wiring_problems=problems[:5], not_restored=differ[:5])


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    set_id, scene_id, out = args[0], args[1], args[2]
    wanted = args[3].split(',') if len(args) > 3 and not args[3].count('x') else list(gc.LAYER_KEYS)
    size = tuple(int(v) for v in args[-1].split('x')) if 'x' in args[-1] else (270, 480)
    os.makedirs(out, exist_ok=True)
    started = time.time()
    results = {}
    k0 = fresh(set_id, scene_id)
    cams, _ = cameras.make_all(k0.settings, scene_id)
    default = k0.settings.scene(scene_id).get('default_camera')
    camera = cams[default] if default in cams else bpy.context.scene.camera
    # a second, closer camera where the layer's elements are large (the set's own list of close views, else the default)
    close = [cams[c] for c in (k0.settings.get('test_set') or {}).get('close_views', []) if c in cams]
    where = {'dirt': close[3] if len(close) > 3 else camera, 'groundcracks': close[4] if len(close) > 4 else camera, 'groundmoss': close[3] if len(close) > 3 else camera,
             'iron': close[1] if len(close) > 1 else camera}
    present = []
    for layer in wanted:
        t = time.time()
        k = fresh(set_id, scene_id)
        if layer not in k.registry or not k.layer_role_names(layer):
            results[layer] = dict(passed=True, skipped='no roles in this set (nothing to test)')
            continue
        present.append(layer)
        cam = where.get(layer, camera)
        entry = {}
        for name, fn in (('dial_zero', lambda: dial_zero(k, out, cam, layer, size)), ('isolation', lambda: isolation(k, out, cam, layer, size))):
            try:
                entry[name] = fn()
            except Exception:
                entry[name] = dict(passed=False, error=traceback.format_exc())
            k.remove()
            k = fresh(set_id, scene_id)
        try:
            entry['remove'] = remove_orders(k, [layer])
        except Exception:
            entry['remove'] = dict(passed=False, error=traceback.format_exc())
        entry['passed'] = all(v.get('passed') for v in entry.values() if isinstance(v, dict))
        entry['seconds'] = round(time.time() - t, 1)
        results[layer] = entry
        print('SELFTEST', layer, entry['passed'], entry['seconds'], flush=True)
    k = fresh(set_id, scene_id)
    try:
        if present:
            k.prepare()
            k.apply(layers=present, overrides={p: STRONG.get(p, {}) for p in present})
            render.draw(f'{out}/det_1.png', size[0], size[1], 4, camera)
            a = render.read(f'{out}/det_1.png')
            render.draw(f'{out}/det_2.png', size[0], size[1], 4, camera)
            b = render.read(f'{out}/det_2.png')
            cmp = render.compare(a, b)
            results['determinism'] = dict(passed=selftests._same(cmp), identical_16bit=cmp['max_diff'] == 0.0, **cmp)
            k.remove()
            for f in ('det_1.png', 'det_2.png'):
                try:
                    os.remove(f'{out}/{f}')
                except OSError:
                    pass
        k = fresh(set_id, scene_id)
        results['reuse_smoke'] = selftests.reuse_smoke(k, [p for p in gc.LAYER_KEYS if p in k.registry])
    except Exception:
        results['reuse_smoke'] = dict(passed=False, error=traceback.format_exc())
    results['passed'] = all(v.get('passed', False) for v in results.values() if isinstance(v, dict))
    json.dump(dict(set=set_id, scene=scene_id, size=list(size), seconds=round(time.time() - started, 1), results=results), open(os.path.join(out, f'selftest_ground_{scene_id}.json'), 'w'), indent=1, default=str)
    print('SELFTEST DONE', results['passed'], round(time.time() - started, 1), flush=True)


main()
