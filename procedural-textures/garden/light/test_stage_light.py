# What this does (plain words): proves stage_light on its own. Opens the starting file (read-only: it never saves), takes a "fingerprint" of every object
# and material, applies the stage with a look, fingerprints again, and lists exactly what was created, changed and deleted. Anything that changed and is NOT
# on the list of things this stage owns is reported as "UNEXPECTED". Also runs the stage twice (safe to repeat?) and the evening variant on top.
# Run: blender -b --disable-autoexec courtyard_final.blend -P test_stage_light.py -- real|painted OUT.json [evening]
import hashlib
import json
import math
import os
import sys

import bpy

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stage_light

OWNED_OBJECT_PREFIX = ('Hills, ', 'Dark plain', 'Camera', 'photo', 'veranda', 'Cool sky fill', 'Golden hour sun', 'Hall glow', 'Lantern light', 'Rim light', 'Roof lift')
OWNED_MATERIALS = ('Hills, ', 'Far hill', 'Lantern flame', 'Shoji paper glow', 'Open room, dim', 'Dark plain ground')


def r(v, n=4):
    return round(float(v), n)


def mat_fp(m):
    h = hashlib.sha1()
    if m.node_tree:
        for n in sorted(m.node_tree.nodes, key=lambda n: n.name):
            h.update(n.bl_idname.encode())
            for i in n.inputs:
                if hasattr(i, 'default_value') and not i.is_linked:
                    try:
                        h.update(repr(tuple(round(x, 4) for x in i.default_value)).encode())
                    except TypeError:
                        h.update(repr(round(i.default_value, 4) if isinstance(i.default_value, float) else i.default_value).encode())
        h.update(repr(sorted((l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name) for l in m.node_tree.links)).encode())
    h.update(repr(tuple(round(x, 4) for x in m.diffuse_color)).encode())
    return h.hexdigest()[:12]


def obj_fp(o):
    d = dict(type=o.type, loc=[r(v) for v in o.location], rot=[r(v) for v in o.rotation_euler], scale=[r(v) for v in o.scale],
             parent=o.parent.name if o.parent else None, hide_render=o.hide_render, hide_viewport=o.hide_viewport,
             vis=[getattr(o, a, None) for a in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_shadow')],
             mats=[s.material.name if s.material else None for s in o.material_slots],
             collections=sorted(c.name for c in o.users_collection), mods=[(m.name, m.type) for m in o.modifiers], lightgroup=getattr(o, 'lightgroup', ''))
    if o.type == 'MESH':
        me = o.data
        d.update(nv=len(me.vertices), nf=len(me.polygons), vsum=r(sum(v.co.x + 2 * v.co.y + 3 * v.co.z for v in me.vertices), 3),
                 smooth=sum(1 for p in me.polygons if p.use_smooth))
    elif o.type == 'CURVE':
        d.update(splines=len(o.data.splines), bevel=r(o.data.bevel_depth))
    elif o.type == 'LIGHT':
        d.update(energy=r(o.data.energy), color=[r(v) for v in o.data.color], ltype=o.data.type)
    return d


def fingerprint():
    sc = bpy.context.scene
    return dict(objects={o.name: obj_fp(o) for o in bpy.data.objects}, materials={m.name: mat_fp(m) for m in bpy.data.materials},
                collections=sorted(c.name for c in bpy.data.collections), camera=sc.camera.name if sc.camera else None,
                render=[sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.view_settings.view_transform, sc.view_settings.look,
                        r(sc.view_settings.exposure), sc.cycles.caustics_reflective, sc.cycles.caustics_refractive],
                world=sc.world.name if sc.world else None)


def diff(a, b):
    out = dict(objects_created=sorted(set(b['objects']) - set(a['objects'])), objects_deleted=sorted(set(a['objects']) - set(b['objects'])),
               objects_changed={}, materials_created=sorted(set(b['materials']) - set(a['materials'])), materials_changed=[],
               materials_deleted=sorted(set(a['materials']) - set(b['materials'])), unexpected=[])
    for n in sorted(set(a['objects']) & set(b['objects'])):
        fa, fb = a['objects'][n], b['objects'][n]
        keys = [k for k in fa if fa[k] != fb.get(k)]
        # being listed in the hidden rim-receivers collection is allowed (it is not part of the scene)
        if 'collections' in keys:
            la = [c for c in fa['collections']]
            lb = [c for c in fb['collections'] if c not in ('G4 rim receivers', 'G4 roof receivers')]
            if la == lb:
                keys.remove('collections')
        if keys:
            out['objects_changed'][n] = keys
            if not n.startswith(OWNED_OBJECT_PREFIX) and keys != ['lightgroup']:
                out['unexpected'].append(f'object {n}: {keys}')
            elif not n.startswith(OWNED_OBJECT_PREFIX):
                pass     # light group name on an emitter (screens, glows) belongs to this stage
    for n in sorted(set(a['materials']) & set(b['materials'])):
        if a['materials'][n] != b['materials'][n]:
            out['materials_changed'].append(n)
            if not n.startswith(OWNED_MATERIALS):
                out['unexpected'].append(f'material {n}')
    if a['collections'] != b['collections']:
        out['collections_added'] = sorted(set(b['collections']) - set(a['collections']))
        out['collections_removed'] = sorted(set(a['collections']) - set(b['collections']))
    out['render_before'], out['render_after'] = a['render'], b['render']
    out['camera_before'], out['camera_after'] = a['camera'], b['camera']
    return out


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    look, outp = argv[0], argv[1]
    do_evening = len(argv) > 2 and argv[2] == 'evening'
    before = fingerprint()
    rep1 = stage_light.apply({'look': look})
    after1 = fingerprint()
    d1 = diff(before, after1)
    # run again: nothing new may be created and nothing may change in other objects
    rep2 = stage_light.apply({'look': look})
    after2 = fingerprint()
    d2 = diff(after1, after2)
    cam_before = before['objects']['Camera']
    cam_after = after2['objects']['photo']
    cam_same = all(cam_before[k] == cam_after[k] for k in ('loc', 'rot', 'scale', 'parent'))
    cd0 = None
    result = dict(look=look, hero_camera_same_place_and_rotation=cam_same, first_run=d1, second_run_vs_first=dict(objects_created=d2['objects_created'], objects_deleted=d2['objects_deleted'],
                  unexpected=d2['unexpected'], objects_changed=d2['objects_changed'], materials_changed=d2['materials_changed']),
                  names_the_kit_relies_on_still_there=all(n in after2['objects'] for n in ('photo', 'Golden hour sun', 'Lantern window glow', 'Hall posts')),
                  lantern_window_glow_kept=('Lantern window glow' in after2['objects'] and after2['objects']['Lantern window glow']['mats'] == ['Lantern flame']),
                  no_object_lost_materials=[n for n, o in after2['objects'].items() if o['type'] == 'MESH' and n in before['objects'] and
                                            any(m is None for m in o['mats']) and not any(m is None for m in before['objects'][n]['mats'])])
    cam = bpy.data.objects['photo']
    result['photo_lens_mm'] = cam.data.lens
    result['photo_dof'] = [cam.data.dof.use_dof, cam.data.dof.focus_object.name if cam.data.dof.focus_object else None, cam.data.dof.aperture_fstop]
    sun = bpy.data.objects['Golden hour sun']
    result['sun_rotation_euler_unchanged'] = ([r(v) for v in sun.rotation_euler] == before['objects']['Golden hour sun']['rot'])
    veranda = bpy.data.objects['veranda']
    result['veranda'] = dict(loc=[r(v, 3) for v in veranda.location], lens=veranda.data.lens)
    result['light_groups'] = [g.name for g in bpy.context.scene.view_layers[0].lightgroups]
    if do_evening:
        before_e = fingerprint()
        stage_light.apply_evening({'look': look})
        after_e = fingerprint()
        result['evening_on_top'] = diff(before_e, after_e)
    json.dump(result, open(outp, 'w'), indent=1, default=str)
    print('TEST_STAGE_LIGHT', look, 'created', len(d1['objects_created']), 'deleted', d1['objects_deleted'], 'changed', len(d1['objects_changed']),
          'materials changed', len(d1['materials_changed']), 'UNEXPECTED', d1['unexpected'], '| second run:', result['second_run_vs_first']['objects_created'],
          result['second_run_vs_first']['unexpected'])


main()
