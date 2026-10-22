# Proves what the life stage touched: fingerprint every object, material, node group, light, camera, world and render setting before and after.
# Run: blender -b --disable-autoexec START.blend -P test_integrity.py -- LOOK OUT.json [steps]
import bpy, sys, json, hashlib, re, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
look, out = argv[0], argv[1]
steps = argv[2].split(',') if len(argv) > 2 and argv[2] != 'all' else None
HERE = 'proc-work/garden/life'
sys.path.insert(0, HERE)
import stage_life

def h(a):
    return hashlib.sha1(np.ascontiguousarray(np.round(np.asarray(a, dtype=np.float64), 5)).tobytes()).hexdigest()[:12]

def val(v):
    try:
        return [round(float(x), 5) for x in v]
    except TypeError:
        try:
            return round(float(v), 5)
        except Exception:
            return str(v)

def ob_fp(ob, dg):
    d = {'type': ob.type, 'loc': val(ob.location), 'rot': val(ob.rotation_euler), 'scale': val(ob.scale), 'parent': ob.parent.name if ob.parent else None,
         'hide_render': ob.hide_render, 'mods': [(m.name, m.type, m.node_group.name if getattr(m, 'node_group', None) else None) for m in ob.modifiers],
         'mats': [s.material.name if s.material else None for s in ob.material_slots], 'cols': [c.name for c in ob.users_collection]}
    if ob.type == 'MESH':
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        V = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', V)
        sm = np.zeros(len(me.polygons), dtype=bool); me.polygons.foreach_get('use_smooth', sm)
        mi = np.zeros(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('material_index', mi)
        d['geo'] = [len(me.vertices), len(me.polygons), h(V), int(sm.sum()), h(mi)]
        ev.to_mesh_clear()
    elif ob.type == 'CURVE':
        d['geo'] = [h([[p.co.x, p.co.y, p.co.z, p.radius] for sp in ob.data.splines for p in sp.points]), ob.data.bevel_depth]
    elif ob.type == 'LIGHT':
        L = ob.data; d['geo'] = [L.type, round(L.energy, 4), val(L.color)]
    elif ob.type == 'CAMERA':
        d['geo'] = [ob.data.lens]
    return d

def mat_fp(m):
    if not m.node_tree:
        return {'diffuse': val(m.diffuse_color)}
    nodes = []
    for n in m.node_tree.nodes:
        ins = []
        for s in n.inputs:
            if hasattr(s, 'default_value') and not s.is_linked:
                ins.append(val(s.default_value) if not isinstance(s.default_value, str) and getattr(s.default_value, '__class__', None).__name__ != 'bpy_prop_array' else val(s.default_value))
        nodes.append((n.bl_idname, n.name, ins))
    links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in m.node_tree.links)
    return {'nodes': h([ord(c) for c in json.dumps(nodes, default=str)]), 'links': h([ord(c) for c in json.dumps(links)]),
            'n': len(nodes), 'settings': [getattr(m, 'use_backface_culling', None), getattr(m, 'blend_method', None), getattr(m, 'surface_render_method', None)]}

def ng_fp(g):
    nodes = [(n.bl_idname, n.name, [val(s.default_value) for s in n.inputs if hasattr(s, 'default_value') and not s.is_linked and not isinstance(s.default_value, (str, bpy.types.bpy_struct))]) for n in g.nodes]
    return {'n': len(g.nodes), 'links': len(g.links), 'h': h([ord(c) for c in json.dumps(nodes, default=str)])}

def snapshot():
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    S = {'objects': {o.name: ob_fp(o, dg) for o in bpy.data.objects}, 'materials': {m.name: mat_fp(m) for m in bpy.data.materials},
         'node_groups': {g.name: ng_fp(g) for g in bpy.data.node_groups}}
    w = sc.world
    S['world'] = mat_fp(w) if w and w.node_tree else {}
    r = sc.render; c = sc.cycles
    S['render'] = [r.engine, r.resolution_x, r.resolution_y, c.samples, c.device, sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure,
                   sc.camera.name if sc.camera else None, sc.frame_current]
    return S

before = snapshot()
rep = stage_life.apply({'look': look, 'steps': steps})
bpy.context.view_layer.update()
after = snapshot()
res = {'look': look}
for kind in ('objects', 'materials', 'node_groups'):
    b, a = before[kind], after[kind]
    res[kind] = {'added': sorted(set(a) - set(b)), 'removed': sorted(set(b) - set(a)), 'changed': sorted(k for k in b if k in a and b[k] != a[k])}
res['names'] = {'objects_before': sorted(before['objects']), 'objects_after': sorted(after['objects']), 'materials_before': sorted(before['materials']), 'materials_after': sorted(after['materials'])}
res['world_changed'] = before['world'] != after['world']
res['render_settings_changed'] = before['render'] != after['render']
# who may change: the objects and materials this stage owns
OWN_OBJ = re.compile(r'^(Maple (leaves|inner mass|trunk|branch.*)|Pine (pads|trunk|limb.*)|Fallen leaves|Lily pads|Lotus blossoms|Pond water|Bamboo (stalks|leaves|fence)|Astra / (Courtyard receiving ground|pebbles grouped bodies|moss grouped bodies)|Life / .*)$')
OWN_MAT = re.compile(r'^(Maple leaves|Maple inner mass|Pine needles|Pond water|Fallen leaves|Lily pad|Lotus blossom|Bamboo (stalk|leaf colour)|Astra / moss tone \d|Life / .*)$')
res['violations'] = {
    'objects_changed_not_owned': [n for n in res['objects']['changed'] + res['objects']['removed'] if not OWN_OBJ.match(n)],
    'materials_changed_not_owned': [n for n in res['materials']['changed'] + res['materials']['removed'] if not OWN_MAT.match(n)],
    'node_groups_changed_not_owned': [n for n in res['node_groups']['changed'] + res['node_groups']['removed'] if not n.startswith('Life / ')],
    'objects_added_not_tagged': [n for n in res['objects']['added'] if bpy.data.objects[n].get('garden_owner') != 'life'],
    'objects_added_without_role': [n for n in res['objects']['added'] if not bpy.data.objects[n].get('garden_role')],
    'objects_added_outside_G2_life_collection_or_bank': [n for n in res['objects']['added'] if not any(c.name.startswith('G2 life') or c.name.startswith('Life / ') for c in bpy.data.objects[n].users_collection) and bpy.data.objects[n].users_collection],
    'lost_material_slots': [n for n in before['objects'] if n in after['objects'] and before['objects'][n]['mats'] and not any(after['objects'][n]['mats'])],
}
res['report_numbers'] = rep['numbers']
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(res, open(out, 'w'), indent=1, default=str)
print('INTEGRITY', json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in res['violations'].items()}))
print('CHANGED OBJECTS', res['objects']['changed'])
print('REMOVED OBJECTS', res['objects']['removed'], 'ADDED', len(res['objects']['added']))
print('CHANGED MATERIALS', res['materials']['changed'], 'ADDED', res['materials']['added'])
print('NODE GROUPS', res['node_groups'])
print('world changed', res['world_changed'], 'render changed', res['render_settings_changed'])
