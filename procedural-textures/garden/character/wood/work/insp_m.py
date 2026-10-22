import bpy
def dump(m, depth=0):
    nt = m.node_tree
    print("MAT", m.name, "users", m.users, "nodes", len(nt.nodes), "links", len(nt.links), "blend", getattr(m,'surface_render_method',None))
    for n in nt.nodes:
        extra = ""
        if n.bl_idname == 'ShaderNodeGroup': extra = " group=" + (n.node_tree.name if n.node_tree else "None")
        if n.bl_idname == 'ShaderNodeTexImage': extra = " img=" + (n.image.name if n.image else "None")
        if n.bl_idname == 'ShaderNodeBump': extra = " strength=%.2f dist=%.2f" % (n.inputs['Strength'].default_value, n.inputs['Distance'].default_value)
        print("   N", n.name, n.bl_idname.replace('ShaderNode',''), extra)
    for l in nt.links:
        print("   L", l.from_node.name, ":", l.from_socket.name, "->", l.to_node.name, ":", l.to_socket.name)
    for n in nt.nodes:
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            print("   BSDF", n.name, {i.name: (tuple(round(x,3) for x in i.default_value) if hasattr(i.default_value,'__len__') else round(i.default_value,3)) for i in n.inputs if i.name in ('Base Color','Roughness','Metallic','Specular IOR Level','Coat Weight','Sheen Weight') })
for name in ["Astra / planks tone 0", "Astra / planks tone 3", "Dark timber", "Beam timber", "GARDEN timber.post", "Plinth stone", "CT / Stone painterly surface.039", "CT / Stone painterly surface.008"]:
    dump(bpy.data.materials[name])
# group list
print("GROUPS", [(g.name, g.users) for g in bpy.data.node_groups if 'GARDEN' in g.name or 'WK' in g.name][:60])
print("IMAGES", [(i.name, i.size[:], i.colorspace_settings.name, i.filepath[-40:]) for i in bpy.data.images][:80])
