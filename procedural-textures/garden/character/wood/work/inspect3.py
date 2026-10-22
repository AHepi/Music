import bpy
def dump(mname, links=True):
    m = bpy.data.materials[mname]
    print("=== MAT", mname, "users", m.users, "blend", m.blend_method if hasattr(m,'blend_method') else '')
    nt = m.node_tree
    for n in nt.nodes:
        extra = ""
        if n.bl_idname == 'ShaderNodeGroup': extra = " GROUP=" + n.node_tree.name
        if n.bl_idname == 'ShaderNodeTexImage': extra = " IMG=" + (n.image.name if n.image else "None")
        if n.bl_idname == 'ShaderNodeBump': extra = " strength=%s" % n.inputs['Strength'].default_value
        if n.bl_idname == 'ShaderNodeAttribute': extra = " ATTR=" + n.attribute_name
        print("  node", n.name, n.bl_idname, extra)
    if links:
        for l in nt.links:
            print("  link", l.from_node.name, l.from_socket.name, "->", l.to_node.name, l.to_socket.name)
dump("CT / Stone painterly surface.039")
dump("Plinth stone")
dump("Dark timber")
dump("Beam timber", False)
for g in bpy.data.node_groups:
    if g.name.startswith("GARDEN scan"):
        imgs = [n.image.filepath for n in g.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image]
        print("GROUP", g.name, imgs[:4], [i.name for i in g.interface.items_tree][:12])
print([i.name for i in bpy.data.images][:50])
