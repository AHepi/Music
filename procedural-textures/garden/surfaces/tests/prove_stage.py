# What this does: PROOF that the surfaces stage changes only what it owns. Opens the starting file, records everything, applies the stage in one look, records again,
# and lists every difference. Run:  blender -b --disable-autoexec START.blend --python prove_stage.py -- LOOK OUT.json [weather 0|1]
import bpy, sys, os, json, hashlib, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
args = sys.argv[sys.argv.index('--') + 1:]
look, out = args[0], args[1]
weather = (args[2] == '1') if len(args) > 2 else (look == 'real')

def r(v, n=4):
    try:
        return [round(float(x), n) for x in v]
    except TypeError:
        return round(float(v), n)

def tree_sig(tree, depth=0):
    if tree is None:
        return None
    nodes = []
    for n in tree.nodes:
        entry = [n.bl_idname, n.name]
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree:
            entry.append(n.node_tree.name)
        for i in n.inputs:
            if hasattr(i, 'default_value') and not i.is_linked:
                try:
                    entry.append((i.identifier, r(i.default_value)))
                except Exception:
                    pass
        nodes.append(entry)
    links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in tree.links)
    return hashlib.md5(json.dumps([sorted(nodes, key=lambda e: e[1]), links], default=str).encode()).hexdigest()

def mesh_sig(ob):
    d = ob.data
    if ob.type == 'MESH':
        co = np.empty(len(d.vertices) * 3, dtype=np.float32)
        d.vertices.foreach_get('co', co)
        return hashlib.md5(np.round(co, 5).tobytes()).hexdigest() + f':{len(d.vertices)}:{len(d.polygons)}'
    if ob.type == 'CURVE':
        pts = [tuple(round(c, 4) for c in p.co[:3]) for sp in d.splines for p in (sp.bezier_points if sp.type == 'BEZIER' else sp.points)]
        return hashlib.md5(json.dumps(pts).encode()).hexdigest()
    return ''

def snapshot():
    s = {'objects': {}, 'materials': {}, 'lights': {}, 'node_groups': sorted(g.name for g in bpy.data.node_groups), 'collections': sorted(c.name for c in bpy.data.collections)}
    for ob in bpy.data.objects:
        s['objects'][ob.name] = {
            'type': ob.type, 'loc': r(ob.location), 'rot': r(ob.rotation_euler), 'scale': r(ob.scale), 'parent': ob.parent.name if ob.parent else None,
            'mesh': mesh_sig(ob), 'mods': [(m.type, m.name, getattr(getattr(m, 'node_group', None), 'name', None)) for m in ob.modifiers],
            'slots': [m.name if m else None for m in ob.data.materials] if ob.type in ('MESH', 'CURVE') else None, 'hide': [ob.hide_render, ob.hide_viewport],
            'props': sorted(k for k in ob.keys() if not k.startswith('_')),
            'cols': sorted(c.name for c in ob.users_collection),
        }
        if ob.type == 'LIGHT':
            L = ob.data
            s['lights'][ob.name] = [L.type, r(L.energy), r(L.color), r(ob.rotation_euler), r(ob.location)] + ([r(L.size)] if hasattr(L, 'size') else [])
        if ob.type == 'CAMERA':
            s['lights'][ob.name] = ['CAM', r(ob.data.lens), r(ob.location), r(ob.rotation_euler)]
    for m in bpy.data.materials:
        s['materials'][m.name] = tree_sig(m.node_tree)
    sc = bpy.context.scene
    s['world'] = tree_sig(sc.world.node_tree) if sc.world else None
    s['render'] = [sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.view_settings.view_transform, sc.view_settings.look, r(sc.view_settings.exposure), sc.camera.name if sc.camera else None]
    return s

before = snapshot()
import stage_surfaces as ss
t = time.time()
rep = ss.apply({'look': look, 'weathering': weather, 'verbose': True})
secs = round(time.time() - t, 1)
after = snapshot()

res = {'look': look, 'weathering': weather, 'seconds': secs}
bo, ao = before['objects'], after['objects']
res['objects_added'] = sorted(set(ao) - set(bo))
res['objects_removed'] = sorted(set(bo) - set(ao))
common = sorted(set(bo) & set(ao))
res['objects_geometry_changed'] = [n for n in common if bo[n]['mesh'] != ao[n]['mesh']]
res['objects_transform_changed'] = [n for n in common if (bo[n]['loc'], bo[n]['rot'], bo[n]['scale'], bo[n]['parent']) != (ao[n]['loc'], ao[n]['rot'], ao[n]['scale'], ao[n]['parent'])]
res['objects_modifiers_changed'] = [n for n in common if bo[n]['mods'] != ao[n]['mods']]
res['objects_visibility_changed'] = [n for n in common if bo[n]['hide'] != ao[n]['hide']]
res['objects_collections_changed'] = [n for n in common if bo[n]['cols'] != ao[n]['cols']]
res['objects_props_changed'] = [n for n in common if bo[n]['props'] != ao[n]['props']]
res['objects_slot_changed'] = {n: [bo[n]['slots'], ao[n]['slots']] for n in common if bo[n]['slots'] != ao[n]['slots']}
res['lights_cameras_changed'] = [n for n in before['lights'] if before['lights'][n] != after['lights'].get(n)]
res['world_changed'] = before['world'] != after['world']
res['render_settings_changed'] = before['render'] != after['render']
bm, am = before['materials'], after['materials']
res['materials_created'] = sorted(set(am) - set(bm))
res['materials_deleted'] = sorted(set(bm) - set(am))
changed = sorted(n for n in set(bm) & set(am) if bm[n] != am[n])
res['materials_rebuilt_count'] = len(changed)
untouched_expected = [n for n in set(bm) & set(am) if bm[n] == am[n]]
res['materials_unchanged_count'] = len(untouched_expected)
# every changed material must be one the stage owns (tagged) or one the kit edited (real look with weathering: the kit works in the materials' node trees)
tag = {m.name: m.get('garden_owner') for m in bpy.data.materials}
res['materials_changed_not_tagged'] = [n for n in changed if tag.get(n) != 'surfaces']
res['materials_unchanged_names'] = sorted(untouched_expected)
res['node_groups_created'] = len(set(after['node_groups']) - set(before['node_groups']))
res['stage_report'] = {k: v for k, v in rep.items() if k in ('built', 'reassigned_slots', 'seconds')}
res['weathering'] = rep.get('weathering')
json.dump(res, open(out, 'w'), indent=1, default=str)
print('PROOF', look, 'added', len(res['objects_added']), 'removed', len(res['objects_removed']), 'geometry changed', len(res['objects_geometry_changed']), 'transforms changed',
      len(res['objects_transform_changed']), 'modifiers changed', len(res['objects_modifiers_changed']), 'lights/cameras changed', res['lights_cameras_changed'], 'world changed', res['world_changed'],
      'render settings changed', res['render_settings_changed'], '| materials rebuilt', len(changed), 'not tagged', len(res['materials_changed_not_tagged']), '| slots moved on', len(res['objects_slot_changed']), 'objects')
