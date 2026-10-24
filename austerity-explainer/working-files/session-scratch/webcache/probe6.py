import bpy
print('bake item socket types:', [i.identifier for i in bpy.types.NodeGeometryBakeItem.bl_rna.properties['socket_type'].enum_items])
t=bpy.data.node_groups.new('g','GeometryNodeTree')
n=t.nodes.new('GeometryNodeBake')
print('Bake node inputs', [(s.name,s.type) for s in n.inputs], 'outputs',[(s.name,s.type) for s in n.outputs])
print('Bake node props', [p.identifier for p in n.bl_rna.properties if p.identifier in ('bake_items','active_index','bake_target','bake_mode','data_blocks')])
print('NodesModifierBake props', [p.identifier for p in bpy.types.NodesModifierBake.bl_rna.properties])
print('gn nodes with Image:', [x for x in dir(bpy.types) if x.startswith('GeometryNode') and 'Image' in x])
print('gn nodes with Bake/Capture:', [x for x in dir(bpy.types) if x.startswith('GeometryNode') and ('Bake' in x or 'Capture' in x)])
