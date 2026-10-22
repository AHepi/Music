import bpy
def dump(mname):
    m = bpy.data.materials[mname]
    print("=== MAT", mname, "users", m.users)
    nt = m.node_tree
    for n in nt.nodes:
        extra = ""
        if n.bl_idname == 'ShaderNodeGroup': extra = " GROUP=" + n.node_tree.name
        if n.bl_idname == 'ShaderNodeTexImage': extra = " IMG=" + (n.image.name if n.image else "None")
        if n.bl_idname == 'ShaderNodeBump': extra = " strength=%s" % n.inputs['Strength'].default_value
        print("  node", n.name, n.bl_idname, extra)
    for l in nt.links:
        print("  link", l.from_node.name, l.from_socket.name, "->", l.to_node.name, l.to_socket.name)
for n in ["Astra / planks tone 3","Astra / planks tone 3.003","GARDEN timber.post","Dark timber","Beam timber","Plinth stone","CT / Stone painterly surface.039"]:
    dump(n)
print("node groups:", [g.name for g in bpy.data.node_groups if 'GARDEN' in g.name or 'WK' in g.name][:60])
for c in bpy.data.collections:
    print("COLL", c.name, len(c.objects), [ch.name for ch in c.children][:5])
