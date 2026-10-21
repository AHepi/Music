import bpy
print(hasattr(bpy.types,'FunctionNodeIntegerMath'))
t=bpy.data.node_groups.new('x','GeometryNodeTree')
s=t.interface.new_socket('F',in_out='INPUT',socket_type='NodeSocketFloat')
print([p for p in dir(s) if 'struct' in p or 'field' in p.lower()])
c=t.interface.new_socket('C',in_out='INPUT',socket_type='NodeSocketCollection')
i=t.interface.new_socket('I',in_out='INPUT',socket_type='NodeSocketInt')
print('ok')
