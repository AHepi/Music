import bpy
m = bpy.data.materials['CT / Stone painterly surface.009']
nt = m.node_tree
g = nt.nodes['Group']
print('GROUP', g.node_tree.name, [o.name for o in g.outputs])
for o in g.outputs:
    for l in o.links:
        print('  ', o.name, '->', l.to_node.name, l.to_socket.name)
for n in nt.nodes:
    if n.name.startswith('WK ') and n.bl_idname == 'ShaderNodeGroup':
        c = n.inputs['Colour']
        print(n.name, 'Colour from', [(l.from_node.name, l.from_socket.name) for l in c.links])
        for o in n.outputs:
            if o.name.startswith('Colour') or o.name == 'Colour':
                print('   out', o.name, '->', [(l.to_node.name, l.to_socket.name) for l in o.links])
b = nt.nodes['Principled BSDF']
print('BSDF base color from', [(l.from_node.name, l.from_socket.name) for l in b.inputs['Base Color'].links])
