import bpy, json, sys, hashlib
import numpy as np
def h(*a):
    m = hashlib.sha1()
    for x in a: m.update(repr(x).encode())
    return m.hexdigest()[:12]
def sockval(s):
    v = getattr(s, 'default_value', None)
    if v is None: return None
    if isinstance(v, str): return v[:40]
    try: return tuple(round(float(x), 4) for x in v)
    except TypeError:
        try: return round(float(v), 4)
        except Exception: return str(getattr(v, 'name', v))
def tree_fp(nt):
    items = []
    for n in sorted(nt.nodes, key=lambda n: n.name):
        ins = []
        for s in n.inputs:
            if not s.is_linked: ins.append((s.identifier, sockval(s)))
        extra = []
        for a in ('image', 'node_tree', 'object', 'attribute_name', 'operation', 'blend_type', 'data_type', 'interpolation', 'space', 'uv_map'):
            if hasattr(n, a):
                v = getattr(n, a)
                extra.append((a, getattr(v, 'name', v) if not isinstance(v, (int, float, str, bool, type(None))) else v))
        items.append((n.name, n.bl_idname, tuple(ins), tuple(extra), tuple(round(float(x), 3) for x in n.location)))
    links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in nt.links)
    return {'nodes': len(nt.nodes), 'links': len(nt.links), 'hash': h(items, links)}
def modfp(m):
    try:
        return h([(k, str(m[k])[:60]) for k in sorted(m.keys())])
    except Exception:
        return h(m.type, m.name)
def snapshot():
    S = {'objects': {}, 'materials': {}, 'groups': {}, 'collections': {}, 'scene': {}}
    for ob in bpy.data.objects:
        d = {'type': ob.type, 'mw': h([round(x, 4) for r in ob.matrix_world for x in r]), 'hide_render': ob.hide_render, 'hide_viewport': ob.hide_viewport,
             'colls': sorted(c.name for c in ob.users_collection), 'parent': ob.parent.name if ob.parent else None,
             'mats': [s.material.name if s.material else None for s in ob.material_slots],
             'mods': [(m.type, m.node_group.name if getattr(m, 'node_group', None) else None, modfp(m)) for m in ob.modifiers],
             'props': {k: str(ob[k])[:40] for k in ob.keys() if k.startswith('garden') or k.startswith('wk_')}}
        if ob.type == 'MESH':
            me = ob.data
            n = len(me.vertices)
            co = np.empty(n * 3); me.vertices.foreach_get('co', co)
            d['nv'] = n; d['np'] = len(me.polygons); d['cohash'] = h(np.round(co, 4).tobytes())
            d['uv'] = [u.name for u in me.uv_layers]
        elif ob.type == 'LIGHT':
            L = ob.data
            d['light'] = (L.type, round(L.energy, 3), tuple(round(x, 3) for x in L.color), getattr(L, 'shadow_soft_size', None))
            try: d['linking'] = (ob.light_linking.receiver_collection.name if ob.light_linking.receiver_collection else None, ob.light_linking.blocker_collection.name if ob.light_linking.blocker_collection else None)
            except Exception: pass
        elif ob.type == 'CAMERA':
            d['cam'] = (round(ob.data.lens, 3), ob.data.type)
        elif ob.type in ('CURVE',):
            d['curve'] = (len(ob.data.splines), sum(len(s.points) + len(s.bezier_points) for s in ob.data.splines))
        S['objects'][ob.name] = d
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree: S['materials'][m.name] = tree_fp(m.node_tree)
        else: S['materials'][m.name] = {'nodes': 0, 'hash': h(tuple(m.diffuse_color))}
    for g in bpy.data.node_groups:
        S['groups'][g.name] = tree_fp(g)
    for c in bpy.data.collections:
        S['collections'][c.name] = {'objs': sorted(o.name for o in c.objects), 'children': sorted(x.name for x in c.children)}
    sc = bpy.context.scene
    r = sc.render
    S['scene'] = {'engine': r.engine, 'res': (r.resolution_x, r.resolution_y, r.resolution_percentage), 'cycles_samples': sc.cycles.samples if hasattr(sc, 'cycles') else None,
                  'view': (sc.view_settings.view_transform, sc.view_settings.look, round(sc.view_settings.exposure, 3), round(sc.view_settings.gamma, 3)), 'camera': sc.camera.name if sc.camera else None, 'frame': sc.frame_current,
                  'world': tree_fp(sc.world.node_tree) if sc.world and sc.world.node_tree else None, 'compositor': tree_fp(sc.compositing_node_group) if getattr(sc, 'compositing_node_group', None) else None,
                  'light_groups': sorted(lg.name for lg in bpy.context.view_layer.lightgroups) if hasattr(bpy.context.view_layer, 'lightgroups') else None,
                  'denoise': (sc.cycles.use_denoising, sc.cycles.denoiser) if hasattr(sc, 'cycles') else None, 'seed': sc.cycles.seed if hasattr(sc, 'cycles') else None}
    return S
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/'
bpy.ops.wm.open_mainfile(filepath=G + 'direction/start/garden_real_fixed.blend')
A = snapshot()
bpy.ops.wm.open_mainfile(filepath=G + 'final/garden_character.blend')
B = snapshot()
R = {}
for kind in ('objects', 'materials', 'groups', 'collections'):
    a, b = A[kind], B[kind]
    R[kind] = {'removed': sorted(set(a) - set(b)), 'added': sorted(set(b) - set(a)), 'changed': sorted(n for n in a if n in b and a[n] != b[n])}
R['changed_detail'] = {}
for n in R['objects']['changed']:
    a, b = A['objects'][n], B['objects'][n]
    R['changed_detail'][n] = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
R['scene_changed'] = [k for k in A['scene'] if A['scene'][k] != B['scene'][k]]
R['scene_detail'] = {k: [A['scene'][k], B['scene'][k]] for k in R['scene_changed']}
json.dump(R, open(sys.argv[-1], 'w'), indent=1, default=str)
print('FP', {k: {x: len(y) for x, y in v.items()} for k, v in R.items() if isinstance(v, dict) and k in ('objects', 'materials', 'groups', 'collections')}, R['scene_changed'])
