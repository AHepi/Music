import bpy, sys
names = sys.argv[sys.argv.index('--')+1:]
def dump(m):
    nt = m.node_tree
    print('=== MATERIAL', m.name, 'blend', m.surface_render_method)
    for n in nt.nodes:
        extra = ''
        if n.bl_idname == 'ShaderNodeValToRGB':
            extra = str([(round(e.position,3), tuple(round(c,3) for c in e.color)) for e in n.color_ramp.elements])
        if n.bl_idname == 'ShaderNodeAttribute':
            extra = n.attribute_name + ' ' + n.attribute_type
        ins = []
        for i in n.inputs:
            if i.is_linked: ins.append('%s<-%s.%s' % (i.name, [l.from_node.name for l in i.links][0], [l.from_socket.name for l in i.links][0]))
            elif hasattr(i, 'default_value'):
                try:
                    v = i.default_value
                    v = tuple(round(x,3) for x in v) if hasattr(v, '__len__') else round(v,3)
                    ins.append('%s=%s' % (i.name, v))
                except Exception: pass
        print(' ', n.name, '|', n.bl_idname, '|', extra, '|', '; '.join(ins)[:600])
for nme in names:
    m = bpy.data.materials.get(nme)
    if m: dump(m)
    else: print('no material', nme)
g = bpy.data.node_groups.get('Life / maple leaf instancer')
print('=== GROUP', g.name if g else None)
if g:
    for n in g.nodes:
        print(' ', n.name, n.bl_idname)
ob = bpy.data.objects['Maple leaves']
print('leaves obj', ob.lightgroup, [m.name for m in ob.modifiers], ob.data.attributes.keys())
