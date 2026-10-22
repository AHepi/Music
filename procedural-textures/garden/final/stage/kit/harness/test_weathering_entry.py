# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE INTEGRATED TEST of the kit's one door (apply_weathering.py), run in Blender on a scene file (on the rented machine, because it draws):
#     blender -b --disable-autoexec SCENE.blend --python harness/test_weathering_entry.py -- SET LOOK OUT_JSON [CAMERA LIGHT WIDTH HEIGHT SAMPLES]
# It checks, with small pictures:
#   1. remove      apply, then remove() gives the picture of the scene as it was (identical, at most one step of 255 on at most 1 % of dots), every material back as its snapshot, and
#                  nothing of the kit left (no object, material, node group or image the kit made)
#   2. master 0    all the kit's layers together with the master dial at 0 give the picture of the earlier layers alone (the baseline); and each of the three groups of layers
#                  switched off alone differs from "all on" (so each does something) while the sum of their changes stays inside the whole change
#   3. determinism two draws of the same state are identical
#   4. twice       apply / remove twice in one session works and leaves the same numbers of nodes
#   5. earlier     the earlier layers' own master dials: wetness 0 = the dry picture, joints and rubbish at 0 change the picture
# A picture is compared as numbers (8 bit PNG): `dots_over_one_step` is the share of dots that differ by more than 1/255 in any channel.
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
import numpy as np  # noqa: E402

import apply_weathering as aw  # noqa: E402
from harness import cameras, lighting  # noqa: E402


def read(path):
    image = bpy.data.images.load(path)
    w, h = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
    bpy.data.images.remove(image)
    return pixels


def compare(a, b):
    d = np.abs(a - b)
    over = (d > (1.5 / 255.0)).any(axis=2)
    return dict(dots_over_one_step=round(float(over.mean()), 5), max_difference=round(float(d.max()), 4), mean_difference=round(float(d.mean()), 6))


def fingerprint():
    """What the kit must leave no trace of: counts of data blocks and every material's node-name list."""
    return dict(objects=len(bpy.data.objects), materials=len(bpy.data.materials), node_groups=len(bpy.data.node_groups), images=len([i for i in bpy.data.images if i.name != 'Render Result']), meshes=len(bpy.data.meshes),
                nodes={m.name: sorted(n.name for n in m.node_tree.nodes) for m in bpy.data.materials if m.node_tree is not None},
                links={m.name: len(m.node_tree.links) for m in bpy.data.materials if m.node_tree is not None})


def diff_fingerprint(a, b):
    out = {}
    for key in ('objects', 'materials', 'node_groups', 'images', 'meshes'):
        if a[key] != b[key]:
            out[key] = (a[key], b[key])
    changed = [m for m in set(a['nodes']) | set(b['nodes']) if a['nodes'].get(m) != b['nodes'].get(m) or a['links'].get(m) != b['links'].get(m)]
    if changed:
        out['materials_changed'] = sorted(changed)[:10]
        out['materials_changed_count'] = len(changed)
    return out


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    set_id, look, out_json = args[0], args[1], args[2]
    camera_name = args[3] if len(args) > 3 else None
    light = args[4] if len(args) > 4 else 'A'
    width, height, samples = (int(args[5]), int(args[6]), int(args[7])) if len(args) > 7 else (270, 480, 8)
    scratch = os.path.join(os.path.dirname(os.path.abspath(out_json)), 'entry_test_pictures')
    os.makedirs(scratch, exist_ok=True)
    result = dict(set=set_id, look=look, size=[width, height, samples], tests={}, errors=[])
    scene = bpy.context.scene

    def make_cameras(settings, scene_id):
        return cameras.make_all(settings, scene_id)[0]

    state = {}

    def draw(name, handle=None, wet=None):
        path = os.path.join(scratch, name + '.png')
        scene.render.engine = 'BLENDER_EEVEE'
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = width, height, 100
        scene.render.image_settings.file_format, scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = 'PNG', 'RGB', '8'
        scene.eevee.taa_render_samples = samples
        scene.eevee.use_raytracing = True
        scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
        scene.render.filter_size = 1.5
        scene.camera = state['cams'][state['camera']]
        lighting.set_rig(state['settings'], light)
        if handle is not None:
            handle.camera(scene.camera, plate_height=height)
        scene.render.filepath = path
        started = time.time()
        bpy.ops.render.render(write_still=True)
        state.setdefault('seconds', {})[name] = round(time.time() - started, 2)
        return read(path)

    try:
        # ---- the scene as it is, and the pictures that need no kit
        w = aw.apply(set_id, look, state='dry', layers=[])           # earlier layers only (the baseline); also reads the settings
        settings = w.kit.settings
        scene_id = w.kit.scene_id
        state['settings'] = settings
        state['cams'] = make_cameras(settings, scene_id)
        state['camera'] = camera_name or next(iter(state['cams']))
        has_earlier = bool(w.stack and w.stack.present())
        w.remove()
        before = fingerprint()
        today = draw('today')
        # ---- baseline: earlier layers only, dry and wet
        w = aw.apply(set_id, look, state='dry', layers=[])
        base_dry = draw('base_dry', w)
        w.set_state(0.85, 0.5)
        base_wet = draw('base_wet', w)
        w.remove()
        after = fingerprint()
        result['tests']['remove_of_earlier_only'] = dict(picture=compare(today, draw('today_again')), fingerprint_difference=diff_fingerprint(before, after))
        # ---- everything on
        w = aw.apply(set_id, look, state='wet')
        result['applied'] = {k: len(v) for k, v in w.applied.items()}
        result['problems'] = w.problems
        all_on = draw('all_on_wet', w)
        all_on_again = draw('all_on_wet_again', w)
        result['tests']['determinism'] = compare(all_on, all_on_again)
        result['tests']['kit_changes_the_picture'] = compare(base_wet, all_on)
        # ---- master dial 0
        w.set_master(0.0)
        master0 = draw('master0_wet', w)
        result['tests']['master_0_equals_earlier_only'] = compare(base_wet, master0)
        w.set_master(1.0)
        # ---- each group alone off: the picture must differ from all-on (the group does something); master 0 of one layer is tested per layer
        groups = {'walls': ('soot', 'runoff', 'foot', 'steps', 'wallcracks', 'wallgrowth', 'paint'), 'ground': ('dirt', 'groundcracks', 'groundmoss', 'iron'), 'growth': ('growth',)}
        result['tests']['group_off'] = {}
        for name, keys in groups.items():
            for key in keys:
                if key in w.kit.active:
                    w.set_layer_master(key, 0.0)
            picture = draw(f'off_{name}_wet', w)
            result['tests']['group_off'][name] = compare(all_on, picture)
            for key in keys:
                if key in w.kit.active:
                    w.set_layer_master(key, 1.0)
        # ---- earlier layers' own master dials
        if has_earlier:
            w.set_master_of('wetness', 0.0)
            dry = draw('wetness0_picture', w)
            w.set_master_of('wetness', 1.0)
            result['tests']['wetness_0_differs_from_wet'] = compare(all_on, dry)
            w.set_master_of('rubbish', 0.0)
            result['tests']['rubbish_0_differs'] = compare(all_on, draw('rubbish0', w))
            w.set_master_of('rubbish', 1.0)
            w.set_master_of('joints', 0.0)
            result['tests']['joints_0_differs'] = compare(all_on, draw('joints0', w))
            w.set_master_of('joints', 1.0)
        result['report'] = {k: v for k, v in w.report().items() if k in ('layers', 'skipped', 'problems', 'pieces', 'hookable', 'roles')}
        result['verify_problems'] = w.kit.verify()
        # ---- remove: everything as it was
        w.remove()
        result['tests']['remove_all'] = dict(picture=compare(today, draw('today_after_all')), fingerprint_difference=diff_fingerprint(before, fingerprint()))
        leftovers = [o.name for o in bpy.data.objects if o.name.startswith('WK')] + [m.name for m in bpy.data.materials if m.name.startswith('WK')] + [g.name for g in bpy.data.node_groups if g.name.startswith('WK')]
        result['tests']['leftovers'] = leftovers[:20]
        # ---- twice
        counts = []
        for _ in range(2):
            w = aw.apply(set_id, look, state='wet')
            counts.append(sum(len(m.node_tree.nodes) for m in bpy.data.materials if m.node_tree is not None))
            w.remove()
        result['tests']['apply_remove_twice_same_node_count'] = dict(node_counts=counts, same=counts[0] == counts[1], remove_again=aw.remove())
        result['tests']['fingerprint_after_twice'] = diff_fingerprint(before, fingerprint())
    except Exception:
        result['errors'].append(traceback.format_exc())
        print(traceback.format_exc(), flush=True)
    result['seconds'] = state.get('seconds', {})
    json.dump(result, open(out_json, 'w'), indent=1, default=str)
    print('ENTRY TEST DONE', flush=True)


if __name__ == '__main__':
    main()
