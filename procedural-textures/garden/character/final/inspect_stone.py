import bpy
m = bpy.data.materials['CT / Stone painterly surface.015']
def dump(nt, ind=0, depth=0):
    for n in nt.nodes:
        extra = ''
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree: extra = ' GROUP ' + n.node_tree.name
        if hasattr(n, 'image') and n.image: extra += ' IMG ' + n.image.name
        vals = []
        for i in n.inputs:
            if not i.is_linked and hasattr(i, 'default_value') and i.name in ('Scale','Strength','Distance','Detail','Roughness','Fac','Lacunarity','W','Distortion','Base Color','Mix','Factor'):
                try: vals.append('%s=%s' % (i.name, tuple(round(x, 3) for x in i.default_value) if hasattr(i.default_value, '__len__') else round(i.default_value, 3)))
                except Exception: pass
        print(' ' * ind + n.bl_idname.replace('ShaderNode', '') + ' ' + n.name + extra + ' ' + ' '.join(vals))
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree and depth < 1 and n.node_tree.name.startswith('CT'):
            dump(n.node_tree, ind + 4, depth + 1)
dump(m.node_tree)
print('LINKS', len(m.node_tree.links))
