import bpy
m = bpy.data.materials.new('x')
print('use_nodes', m.use_nodes, 'tree', m.node_tree, [n.name for n in m.node_tree.nodes] if m.node_tree else None)
