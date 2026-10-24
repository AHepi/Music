import bpy
t=bpy.data.node_groups.new('x','GeometryNodeTree')
n=t.nodes.new('GeometryNodeMeshBoolean')
print([ (s.name, s.enabled, s.type) for s in n.inputs])
print([p.identifier for p in n.bl_rna.properties if p.identifier in ('solver','operation')], getattr(n,'solver',None), n.operation if hasattr(n,'operation') else None)
for p in n.bl_rna.properties:
    if p.identifier in ('solver','operation'): print(p.identifier, [e.identifier for e in p.enum_items])
