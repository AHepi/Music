import bpy
for g in bpy.data.node_groups:
    if not g.name.startswith('WK '): continue
    attrs = []
    def walk(nt, depth=0):
        for n in nt.nodes:
            if n.bl_idname == 'ShaderNodeAttribute':
                attrs.append((n.attribute_type, n.attribute_name))
            if n.bl_idname == 'ShaderNodeGroup' and n.node_tree is not None and depth < 4:
                walk(n.node_tree, depth+1)
    walk(g)
    print('GROUP', g.name, 'nodes', len(g.nodes))
    print('   ATTRS', sorted(set(a for a in attrs)))
