import bpy
ob = bpy.data.objects['Maple leaves']
m = ob.modifiers[0]
I = m.properties.inputs
for k in ('Socket_0','Socket_2'):
    g = I[k]
    print(k, g.to_dict() if hasattr(g,'to_dict') else g)
print([ (i.name, i.identifier, getattr(i,'default_value',None)) for i in m.node_group.interface.items_tree if i.item_type=='SOCKET' and i.in_out=='INPUT'])
g = I['Socket_2']
print('keys', list(g.keys()))
