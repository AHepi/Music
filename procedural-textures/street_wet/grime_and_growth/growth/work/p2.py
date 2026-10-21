import bpy
print([n for n in dir(bpy.types) if 'SeparateColor' in n or 'SeparateRGB' in n])
t=bpy.data.node_groups.new('x','GeometryNodeTree')
for idn in ('FunctionNodeSeparateColor','ShaderNodeSeparateColor','CompositorNodeSeparateColor'):
    try:
        n=t.nodes.new(idn); print(idn,'ok',[o.name for o in n.outputs])
    except Exception as e: print(idn,'fail')
