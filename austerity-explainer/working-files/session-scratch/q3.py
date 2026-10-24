import bpy
t=bpy.data.node_groups.new('x','GeometryNodeTree')
b=t.nodes.new('GeometryNodeMeshBevel')
for s in b.inputs: print(s.name, s.type, s.enabled, getattr(s,'default_value',None), getattr(s,'hide_value',None))
print(b.bl_rna.properties.keys())
for p in b.bl_rna.properties:
    if p.type=='ENUM': print(p.identifier,[e.identifier for e in p.enum_items], getattr(b,p.identifier))
