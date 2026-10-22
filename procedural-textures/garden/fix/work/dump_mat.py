import bpy, sys
names = sys.argv[sys.argv.index('--')+1:]
def val(s):
    if not hasattr(s,'default_value'): return ''
    v = s.default_value
    try:
        return tuple(round(x,4) for x in v)
    except TypeError:
        return round(float(v),4) if isinstance(v,(int,float)) else str(v)
for nm in names:
    m = bpy.data.materials.get(nm)
    print('=== MATERIAL', nm, 'exists', bool(m))
    if not m: continue
    for n in m.node_tree.nodes:
        print(' NODE', n.name, n.bl_idname, getattr(n,'label',''), 'loc', tuple(round(x) for x in n.location))
        for s in n.inputs:
            if s.is_linked:
                l = s.links[0]
                print('    in', s.name, '<-', l.from_node.name, l.from_socket.name)
            elif hasattr(s,'default_value') and not s.hide:
                print('    in', s.name, '=', val(s))
