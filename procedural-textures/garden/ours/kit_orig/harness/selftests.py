# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE SELF-TESTS (Blender side). Each takes a loaded Kit and returns a small dict with 'passed' and the numbers; a builder calls them for its own layers.
#   hook_all(kit)                         the hook (with the adapter) takes a do-nothing layer in slots A, B and C on EVERY material that has a surface (policy off), the wiring
#                                         verifies, and kit.remove() gives back exactly the snapshot (graph signatures equal)
#   remove_orders(kit)                    layers taken off in other orders and twice leave the chain right (verify) and finally restore the original
#   do_nothing(kit, size, camera)         a picture with do-nothing layers in A, B, C equals the picture without (16 bit, exact)
#   dial_zero(kit, layer, ...)            at Amount 0 a layer changes nothing (exact picture; a layer with a visible 'demo' dial is switched on first to prove it would otherwise act)
#   isolation(kit, layer, role_names)     a layer alone changes only the dots of its roles (the class picture says which dots are which role)
#   determinism(kit, ...)                 two draws of the same picture are identical
#   reuse_smoke(kit, layers)              on any set: every layer goes in without a crash, and out again, restoring every material
#   lighting_matches_earlier(...)         the rigs A, C, E reproduce the earlier pictures within one step on 99 % of dots
# Pictures are drawn by harness.render (EEVEE, 16 bit).
import json
import random
import time

import bpy
import numpy as np

from apply import chain as chain_module, hook

from . import render


def _signatures(kit):
    return {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree is not None}


def _same(cmp):
    """The plan's line for 'nothing changed': identical, or at most one step of 255 on at most 1 % of dots (the EEVEE noise floor)."""
    return cmp['share_over_one_step'] <= 0.01


def hook_all(kit, keys=('template_a', 'template_b', 'template_c')):
    """Do-nothing layers in A, B and C on every material with a surface. Returns the counts. The kit must be freshly loaded (nothing applied)."""
    before = _signatures(kit)
    kit.prepare(policy=False)
    plain = [n for n, (s, p, a, g) in kit._snap.items() if a is None]
    adapted = [n for n, (s, p, a, g) in kit._snap.items() if a is not None]
    result = kit.apply(layers=list(keys))
    problems = kit.verify()
    wired = {k: len(v) for k, v in result.items()}
    kit.remove()
    after = _signatures(kit)
    differ = [m for m in before if before[m] != after.get(m)]
    return dict(passed=(not problems and not differ and all(c == len(kit_plain_adapted(plain, adapted)) for c in wired.values())),
                materials_total=len([m for m in bpy.data.materials if m.node_tree is not None]), hooked_plain=len(plain), hooked_adapted=len(adapted), layers_in=wired,
                skipped_no_surface=sorted(kit.skipped), forced_past_policy=sorted(kit.forced), wiring_problems=problems[:10], not_restored=differ[:10])


def kit_plain_adapted(plain, adapted):
    return list(plain) + list(adapted)


def remove_orders(kit, keys=('template_a', 'template_b', 'template_c'), seed=7):
    kit.prepare()
    before_all = _signatures(kit)
    kit.apply(layers=list(keys))
    rng = random.Random(seed)
    steps = []
    order = list(keys)
    rng.shuffle(order)
    order = order + [order[0], order[1]]                    # twice
    problems = []
    for key in order:
        kit.remove(key)
        steps.append(key)
        problems += kit.verify()
    # all gone: the chains equal the snapshot except for constant nodes the kit made (removed with kit.remove below)
    kit.remove()
    after = _signatures(kit)
    differ = [m for m in before_all if before_all[m] != after.get(m)]
    return dict(passed=not problems and not differ, order=steps, wiring_problems=problems[:10], not_restored=differ[:10])


def do_nothing(kit, out_dir, camera, size=(135, 240), samples=4, keys=('template_a', 'template_b', 'template_c'), light=None):
    w, h = size
    kit.prepare()
    a_path, b_path = f'{out_dir}/dn_base.png', f'{out_dir}/dn_layers.png'
    render.draw(a_path, w, h, samples, camera)
    base = render.read(a_path)
    kit.apply(layers=list(keys))
    render.draw(b_path, w, h, samples, camera)
    layers = render.read(b_path)
    cmp = render.compare(base, layers)
    kit.remove()
    return dict(passed=_same(cmp), identical_16bit=cmp['max_diff'] == 0.0, size=[w, h], samples=samples, **cmp)


def dial_zero(kit, out_dir, camera, layer='template_b', size=(135, 240), samples=4, demo_dial='demo'):
    w, h = size
    kit.prepare()
    base_path = f'{out_dir}/dz_base.png'
    render.draw(base_path, w, h, samples, camera)
    base = render.read(base_path)
    kit.apply(layers=[layer], overrides={layer: {demo_dial: 1.0}})
    render.draw(f'{out_dir}/dz_on.png', w, h, samples, camera)
    on = render.read(f'{out_dir}/dz_on.png')
    kit.set_dials(layer, amount=0.0)
    render.draw(f'{out_dir}/dz_zero.png', w, h, samples, camera)
    zero = render.read(f'{out_dir}/dz_zero.png')
    acts = render.compare(base, on)
    nothing = render.compare(base, zero)
    kit.remove()
    return dict(passed=_same(nothing) and acts['share_changed'] > 0.0, identical_16bit=nothing['max_diff'] == 0.0, acts_at_amount_1=acts, at_amount_0=nothing)


def isolation(kit, out_dir, camera, layer, role_names, size=(135, 240), samples=4):
    """A layer alone acts only on its roles: its own Mask view (plain light, raw) is zero outside the dots of its roles (the class picture says which dots are which role; a
    two-dot margin is allowed for smoothing at edges). Light bounced from a tinted surface would change its neighbours a little in a beauty picture, so the mask view is the test."""
    import cv2
    from . import class_pass
    from masks import debug
    w, h = size
    kit.prepare()
    kit.apply(layers=[layer], overrides={layer: {'demo': 1.0}})
    render.plain_light(True)
    undo = debug.show_layer(kit, layer)
    render.draw(f'{out_dir}/iso_mask.png', w, h, 1, camera, raytracing=False)
    undo()
    render.plain_light(False)
    mask = render.read(f'{out_dir}/iso_mask.png')[..., 0]
    kit.remove()
    kit.prepare()
    render.plain_light(True)
    bpy.context.view_layer.material_override = class_pass.make_material()
    render.draw(f'{out_dir}/iso_class.png', w, h, 1, camera, raytracing=False)
    bpy.context.view_layer.material_override = None
    render.plain_light(False)
    ids = np.round(render.read(f'{out_dir}/iso_class.png')[..., 0] * 64.0).astype(int)
    wanted = {list(kit.settings.roles).index(r) + 1 for r in kit.settings.expand_roles(role_names)}
    inside = np.isin(ids, list(wanted))
    grown = cv2.dilate(inside.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    acting = (mask > 0.01) & (ids > 0)                  # sky and glass (no role) stay lit by their own materials in a plain-light view
    outside = int((acting & ~grown).sum())
    by_id = {int(i): int(((ids == i) & acting & ~grown).sum()) for i in np.unique(ids[acting & ~grown])} if outside else {}
    names = list(kit.settings.roles)
    return dict(passed=outside == 0 and bool(acting.any()), dots_acting=int(acting.sum()), dots_acting_outside_roles=outside, roles=sorted(wanted),
                class_id_counts={int(i): int((ids == i).sum()) for i in np.unique(ids)}, mask_max=float(mask.max()),
                outside_by_role={(names[i - 1] if 0 < i <= len(names) else 'no role'): n for i, n in by_id.items()})


def determinism(kit, out_dir, camera, size=(135, 240), samples=4):
    w, h = size
    render.draw(f'{out_dir}/det_1.png', w, h, samples, camera)
    a = render.read(f'{out_dir}/det_1.png')
    render.draw(f'{out_dir}/det_2.png', w, h, samples, camera)
    b = render.read(f'{out_dir}/det_2.png')
    cmp = render.compare(a, b)
    return dict(passed=_same(cmp), identical_16bit=cmp['max_diff'] == 0.0, **cmp)


def reuse_smoke(kit, layers=None):
    """Every given (default: every registered) layer goes in and out without a crash on this set, and the materials come back exactly."""
    before = _signatures(kit)
    kit.prepare()
    errors = {}
    keys = layers or list(kit.registry)
    went_in = {}
    for key in keys:
        try:
            went_in[key] = len(kit.apply(layers=[key]).get(key, []))
        except Exception as error:                  # reported, never hidden
            errors[key] = repr(error)
    problems = kit.verify()
    kit.remove()
    after = _signatures(kit)
    differ = [m for m in before if before[m] != after.get(m)]
    return dict(passed=not errors and not problems and not differ, layers=went_in, errors=errors, wiring_problems=problems[:5], not_restored=differ[:5])


def lighting_matches_earlier(kit, out_dir, camera, size=(270, 480), samples=8, rigs=('A', 'C', 'D', 'E')):
    """The rigs written as data (harness.lighting) reproduce the earlier study's own rigs (the pinned b02 set_lighting): the same picture within one step of 255 on 99 % of dots.
    Each rig is drawn twice, once lit by the earlier function and once by the data rig, with everything put back in between."""
    from . import legacy_stack, lighting
    lv = legacy_stack.modules()['lv']
    w, h = size
    out = {}
    for rig in rigs:
        lighting.restore()
        lv.set_lighting(rig)
        render.draw(f'{out_dir}/lt_{rig}_earlier.png', w, h, samples, camera, raytracing=True)
        a = render.read(f'{out_dir}/lt_{rig}_earlier.png')
        lv.set_lighting('A')
        lighting.set_rig(kit.settings, rig)
        render.draw(f'{out_dir}/lt_{rig}_data.png', w, h, samples, camera, raytracing=True)
        b = render.read(f'{out_dir}/lt_{rig}_data.png')
        lighting.restore()
        cmp = render.compare(a, b)
        out[rig] = dict(passed=cmp['share_over_one_step'] <= 0.01, share_over_one_step=cmp['share_over_one_step'], max_diff=cmp['max_diff'])
    lv.set_lighting('A')
    return dict(passed=all(v['passed'] for v in out.values()), rigs=out, size=[w, h], samples=samples)
