import bpy
m=bpy.data.materials.new('x'); m.use_nodes=True
n=m.node_tree.nodes.new('ShaderNodeHueSaturation')
for i,s in enumerate(n.inputs): print(i, s.name, s.identifier, s.type, getattr(s,'default_value',None))
print(n.inputs.find('Value'), n.inputs.find('Hue'))
