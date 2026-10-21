import bpy
t=bpy.data.node_groups.new('x','GeometryNodeTree')
for idn in ('FunctionNodeRotateVector','GeometryNodeRotateVector','ShaderNodeVectorRotate'):
    try:
        n=t.nodes.new(idn); print(idn,'ok',[i.name for i in n.inputs],[o.name for o in n.outputs])
    except Exception as e: print(idn,'fail')
n=t.nodes.new('GeometryNodeObjectInfo'); print([o.name+':'+o.type for o in n.outputs])
