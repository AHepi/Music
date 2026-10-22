import bpy, sys
names = sys.argv[sys.argv.index('--')+1:]
def dump(nt, ind=0, seen=None):
    for n in nt.nodes:
        extra = ''
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree: extra = ' GROUP=' + n.node_tree.name
        vals = []
        for i in n.inputs:
            if not i.is_linked and hasattr(i,'default_value'):
                try:
                    v = i.default_value
                    if hasattr(v,'__len__'): v = tuple(round(x,3) for x in v)
                    elif isinstance(v,float): v = round(v,3)
                    vals.append('%s=%s'%(i.name,v))
                except Exception: pass
        print(' '*ind, n.name, '|', n.bl_idname, extra, '|', ' '.join(vals)[:260])
    for l in nt.links:
        print(' '*ind, 'LINK', l.from_node.name, l.from_socket.name, '->', l.to_node.name, l.to_socket.name)
for o in bpy.data.objects:
    if o.name in ('Rock 0','Rock 1','Rock 3','Lantern cap','Lantern post','Back wall, right','Pond edge stone 3'):
        print('OBJ', o.name, [m.name for m in o.data.materials] if o.type=='MESH' else '', [ (k,o[k]) for k in o.keys() if k.startswith('wk_')])
for nm in names:
    m = bpy.data.materials[nm]
    print('=== MATERIAL', nm)
    dump(m.node_tree)
