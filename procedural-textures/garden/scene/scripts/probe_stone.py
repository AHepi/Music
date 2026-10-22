import bpy, sys
for name in ('Rock 0', 'Rock 1', 'Hall roof', 'Lantern post'):
    ob = bpy.data.objects[name]
    print('=====', name, 'dims', [round(v, 2) for v in ob.dimensions], 'mats', [s.material.name if s.material else None for s in ob.material_slots])
    for m in ob.modifiers:
        print(' MOD', m.name, m.type, 'show_render', m.show_render)
        if m.type == 'NODES':
            ng = m.node_group
            print('   group', ng.name, 'nodes', len(ng.nodes))
            vals = {}
            try:
                for it in ng.interface.items_tree:
                    if it.item_type == 'SOCKET' and it.in_out == 'INPUT':
                        v = getattr(m.properties.inputs, it.identifier).value if hasattr(m, 'properties') else m.get(it.identifier)
                        try: v = tuple(v)
                        except Exception: pass
                        vals[it.name] = v
            except Exception as e:
                vals['err'] = str(e)
            print('   inputs', vals)
            print('   node kinds', sorted({n.bl_idname for n in ng.nodes})[:40])
        if m.type == 'BEVEL':
            print('   bevel width', m.width, 'segments', m.segments, 'limit', m.limit_method, 'angle', m.angle_limit)
dg = bpy.context.evaluated_depsgraph_get()
roof = bpy.data.objects['Hall roof']
cnt = 0; tris = 0; kinds = {}
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.original == roof:
        cnt += 1
        me = inst.object.data
        kinds[me.name if me else None] = kinds.get(me.name if me else None, 0) + 1
        tris += len(me.polygons) if me else 0
print('ROOF instances', cnt, 'polys of instance meshes', tris, 'distinct', len(kinds))
for k, v in list(kinds.items())[:10]: print('   ', k, v)
