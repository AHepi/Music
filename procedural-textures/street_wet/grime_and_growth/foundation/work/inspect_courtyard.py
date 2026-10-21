import bpy, json, sys, collections
out = {}
mats = bpy.data.materials
kinds = collections.Counter()
groups = collections.Counter()
detail = {}
for m in mats:
    if not m.use_nodes or not m.node_tree: kinds['nonodes'] += 1; continue
    t = m.node_tree
    output = next((n for n in t.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    surf = output.inputs['Surface'].links[0].from_node if output and output.inputs['Surface'].links else None
    k = surf.type if surf else 'NONE'
    if k == 'GROUP':
        k += ':' + surf.node_tree.name
        groups[surf.node_tree.name] += 1
    kinds[k] += 1
    if k.startswith('GROUP') and len(detail) < 3:
        g = surf.node_tree
        detail[m.name] = dict(group=g.name, inputs=[(s.name, s.socket_type) for s in g.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT'][:40],
                              outputs=[(s.name, s.socket_type) for s in g.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='OUTPUT'],
                              inner=[(n.type, n.name) for n in g.nodes if n.type in ('BSDF_PRINCIPLED','GROUP','GROUP_OUTPUT')],
                              node_inputs=[(i.name, bool(i.links), getattr(i,'default_value',None) if not hasattr(getattr(i,'default_value',None),'__len__') else tuple(i.default_value)) for i in surf.inputs][:30],
                              props={k: str(v) for k,v in m.items()})
print('KINDS', dict(kinds))
print('GROUPS', dict(groups))
print('DETAIL', json.dumps(detail, indent=1, default=str)[:6000])
# custom props on materials / objects
cp = collections.Counter()
for m in mats:
    for k in m.keys(): cp['mat:'+k+'='+str(m[k])[:20]] += 1
for o in bpy.data.objects:
    for k in o.keys():
        if not k.startswith('_'): cp['obj:'+k+'='+str(o[k])[:20]] += 1
print('CUSTOMPROPS', dict(cp))
print('OBJS', collections.Counter(o.type for o in bpy.data.objects))
print('SCENE', bpy.context.scene.render.engine, bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y, bpy.context.scene.camera.name if bpy.context.scene.camera else None)
