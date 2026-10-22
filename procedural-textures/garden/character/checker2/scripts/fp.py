# Fingerprint of a whole scene (objects, meshes, materials, node groups, collections, lights, light links, world, render settings) -> JSON.
# checker's own code. blender -b FILE --python fp.py -- OUT.json
import bpy, sys, json, hashlib, numpy as np
OUT = sys.argv[-1]

def h(s): return hashlib.md5(s.encode()).hexdigest()[:12]

def val(v):
    try:
        if hasattr(v, '__len__') and not isinstance(v, str):
            return [round(float(x), 4) for x in v]
        if isinstance(v, float): return round(v, 4)
        if hasattr(v, 'name'): return 'ID:' + v.name
        return v if isinstance(v, (int, str, bool)) or v is None else str(v)
    except Exception:
        return str(v)

def tree_fp(nt):
    parts = []
    for n in sorted(nt.nodes, key=lambda n: n.name):
        d = [n.bl_idname, n.name]
        for i in n.inputs:
            if not i.is_linked and hasattr(i, 'default_value'):
                d.append((i.identifier, val(i.default_value)))
        for pn in ('operation', 'blend_type', 'data_type', 'space', 'uv_map', 'interpolation', 'extension', 'noise_dimensions', 'distribution', 'subsurface_method'):
            if hasattr(n, pn):
                d.append((pn, val(getattr(n, pn))))
        if n.bl_idname == 'ShaderNodeTexImage' and n.image: d.append(('img', n.image.name))
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree: d.append(('grp', n.node_tree.name))
        if n.bl_idname == 'ShaderNodeValToRGB':
            d.append(('ramp', [(round(e.position, 3), [round(x, 3) for x in e.color]) for e in n.color_ramp.elements]))
        parts.append(repr(d))
    links = sorted('%s:%s>%s:%s' % (l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in nt.links)
    return {'nodes': len(nt.nodes), 'links': len(nt.links), 'hash': h('|'.join(parts) + '#' + '|'.join(links))}

R = {}
objs = {}
for ob in bpy.data.objects:
    d = {'type': ob.type, 'owner': ob.get('garden_owner'), 'role': ob.get('garden_role'), 'colls': sorted(c.name for c in ob.users_collection), 'parent': ob.parent.name if ob.parent else None,
         'mw': h(repr(np.round(np.array(ob.matrix_world), 4).tolist())), 'hide_render': ob.hide_render, 'hide_viewport': ob.hide_viewport,
         'mods': sorted((m.type, m.name, m.node_group.name if getattr(m, 'node_group', None) else None) for m in ob.modifiers),
         'mats': [s.material.name if s.material else None for s in ob.material_slots], 'lightgroup': ob.lightgroup, 'visible': [ob.visible_camera, ob.visible_diffuse, ob.visible_glossy, ob.visible_shadow]}
    try:
        ll = ob.light_linking
        d['ll'] = [ll.receiver_collection.name if ll.receiver_collection else None, ll.blocker_collection.name if ll.blocker_collection else None]
    except Exception:
        d['ll'] = None
    if ob.type == 'MESH':
        me = ob.data
        n = len(me.vertices)
        co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
        w = (np.arange(n) % 7 + 1)[:, None]
        d['nv'] = n; d['nf'] = len(me.polygons); d['pos'] = h(repr(np.round((co * w).sum(axis=0), 4).tolist()) + repr(np.round(np.abs(co).sum(), 3)))
        d['uv'] = [u.name for u in me.uv_layers]
        d['mesh'] = me.name
        d['attrs'] = sorted(a.name for a in me.attributes if not a.name.startswith('.'))
    elif ob.type == 'CURVE':
        d['splines'] = len(ob.data.splines)
    elif ob.type == 'LIGHT':
        L = ob.data
        d['light'] = [L.type, round(L.energy, 3), [round(x, 3) for x in L.color], round(getattr(L, 'size', 0), 3)]
    elif ob.type == 'CAMERA':
        d['cam'] = [round(ob.data.lens, 2), round(ob.data.sensor_width, 2)]
    objs[ob.name] = d
R['objects'] = objs
mats = {}
for m in bpy.data.materials:
    d = {'users': m.users, 'use_nodes': m.use_nodes}
    if m.node_tree:
        d.update(tree_fp(m.node_tree))
    mats[m.name] = d
R['materials'] = mats
ngs = {}
for g in bpy.data.node_groups:
    ngs[g.name] = {'type': g.bl_idname, **tree_fp(g)}
R['node_groups'] = ngs
R['collections'] = {c.name: {'objects': sorted(o.name for o in c.objects), 'children': sorted(x.name for x in c.children), 'hide_render': c.hide_render} for c in bpy.data.collections}
R['images'] = sorted(i.name for i in bpy.data.images)
sc = bpy.context.scene
R['scene'] = {'engine': sc.render.engine, 'res': [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage], 'samples': sc.cycles.samples, 'view': [sc.view_settings.view_transform, sc.view_settings.look, round(sc.view_settings.exposure, 3)],
              'camera': sc.camera.name if sc.camera else None, 'frame': sc.frame_current, 'world': sc.world.name if sc.world else None, 'lightgroups': [lg.name for lg in sc.view_layers[0].lightgroups], 'use_nodes_compositing': getattr(sc, 'use_nodes', None)}
if sc.world and sc.world.node_tree: R['scene']['world_fp'] = tree_fp(sc.world.node_tree)
try:
    ct = sc.compositing_node_group
    if ct: R['scene']['compositor_fp'] = tree_fp(ct)
except Exception as e:
    R['scene']['compositor_err'] = str(e)
R['n'] = {'objects': len(bpy.data.objects), 'materials': len(bpy.data.materials), 'node_groups': len(bpy.data.node_groups), 'images': len(bpy.data.images), 'meshes': len(bpy.data.meshes), 'collections': len(bpy.data.collections)}
json.dump(R, open(OUT, 'w'), default=str)
print('FP DONE', R['n'])
