import bpy
t=bpy.data.node_groups.new('x','GeometryNodeTree')
m=t.nodes.new('ShaderNodeMix'); m.data_type='RGBA'
print(m.inputs['A'].type, m.inputs['A'].enabled, m.inputs['Factor'].type, m.outputs['Result'].type)
m2=t.nodes.new('ShaderNodeMix'); m2.data_type='VECTOR'
print(m2.inputs['A'].type)
c=t.nodes.new('FunctionNodeCompare'); c.data_type='INT'; print(c.inputs['A'].type, [ (s.name,s.type,s.enabled) for s in c.inputs])
mr=t.nodes.new('ShaderNodeMapRange'); print(mr.inputs['From Min'].type, mr.data_type)
