import bpy
dg = bpy.context.evaluated_depsgraph_get()
roof = bpy.data.objects['Hall roof']
print('ROOF MODS', [(m.name, m.node_group.name if m.node_group else None, m.type) for m in roof.modifiers])
print('ROOF SLOTS', [s.material.name if s.material else None for s in roof.material_slots], 'in scene', roof.name in bpy.context.scene.objects)
seen = {}
for inst in dg.object_instances:
    p = inst.parent; o = inst.object
    if (p and p.name == 'Hall roof') or o.name == 'Hall roof' or 'CT / Ceramic' in o.name:
        mats = [s.material.name if s.material else None for s in o.material_slots]
        key = (o.name, p.name if p else None, inst.is_instance, tuple(mats), o.type, o.name in bpy.context.scene.objects)
        seen[key] = seen.get(key, 0) + 1
for k, v in seen.items(): print('INST', k, v)
def walk(tree, depth=0, seen_trees=None):
    seen_trees = seen_trees if seen_trees is not None else set()
    if tree.name in seen_trees: return
    seen_trees.add(tree.name)
    for n in tree.nodes:
        if n.bl_idname == 'GeometryNodeSetMaterial':
            mat = n.inputs['Material'].default_value
            linked = [l.from_node.name for l in n.inputs['Material'].links]
            print('  '*depth+'SETMAT', tree.name, n.name, mat.name if mat else None, linked)
        elif n.bl_idname == 'GeometryNodeObjectInfo':
            ob = n.inputs[0].default_value
            print('  '*depth+'OBJINFO', tree.name, n.name, ob.name if ob else None, [l.from_node.name for l in n.inputs[0].links])
        elif n.bl_idname == 'GeometryNodeCollectionInfo':
            print('  '*depth+'COLINFO', tree.name, n.name)
        elif n.bl_idname == 'GeometryNodeGroup' and n.node_tree:
            print('  '*depth+'GROUP', n.node_tree.name)
            walk(n.node_tree, depth+1, seen_trees)
        elif n.bl_idname == 'GeometryNodeInputMaterial':
            print('  '*depth+'INPUTMATERIAL', tree.name, n.name, n.material.name if n.material else None)
for m in roof.modifiers:
    if m.type == 'NODES' and m.node_group:
        walk(m.node_group)
        for k in m.keys():
            v = m[k]
            print('  MODINPUT', k, v if isinstance(v,(int,float,str)) else type(v).__name__, getattr(v,'name',''))
proto = bpy.data.objects.get('CT / Ceramic pan prototype')
print('PROTO', proto, proto.users_collection if proto else None, [c.name for c in proto.users_collection] if proto else None, proto.hide_render if proto else None)
print('SCENE OBJECTS with GN modifiers:', [(o.name,[m.node_group.name for m in o.modifiers if m.type=='NODES' and m.node_group]) for o in bpy.context.scene.objects if any(m.type=='NODES' for m in o.modifiers)])
