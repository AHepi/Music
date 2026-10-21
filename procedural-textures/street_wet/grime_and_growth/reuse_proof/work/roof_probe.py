import bpy
dg = bpy.context.evaluated_depsgraph_get()
roof = bpy.data.objects['Hall roof']
print('ROOF MODS', [(m.name, m.node_group.name if m.node_group else None) for m in roof.modifiers])
seen = {}
for inst in dg.object_instances:
    p = inst.parent
    o = inst.object
    if (p and p.name == 'Hall roof') or o.name == 'Hall roof' or 'CT / Ceramic' in o.name:
        mats = [s.material.name if s.material else None for s in o.material_slots]
        key = (o.name, p.name if p else None, inst.is_instance, tuple(mats), o.type)
        seen[key] = seen.get(key, 0) + 1
for k, v in seen.items():
    print('INST', k, v)
ev = roof.evaluated_get(dg)
try:
    me = ev.to_mesh()
    print('EVAL MESH faces', len(me.polygons), 'mats', [m.name if m else None for m in me.materials])
    ev.to_mesh_clear()
except Exception as e:
    print('to_mesh failed', e)
for m in roof.modifiers:
    if m.type == 'NODES' and m.node_group:
        for n in m.node_group.nodes:
            if n.bl_idname in ('GeometryNodeSetMaterial',):
                print('SETMAT', n.name, n.inputs['Material'].default_value.name if n.inputs['Material'].default_value else None, [l.from_node.name for l in n.inputs['Material'].links])
            if n.bl_idname == 'GeometryNodeObjectInfo':
                print('OBJINFO', n.name, n.inputs[0].default_value.name if n.inputs[0].default_value else None)
print('PROPS roof', {k: roof[k] for k in roof.keys() if k.startswith('wk_')})
proto = bpy.data.objects['CT / Ceramic pan prototype']
print('PROPS proto', {k: proto[k] for k in proto.keys() if k.startswith('wk_')})
