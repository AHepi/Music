import bpy
for name in ('CT / Ceramic painterly surface',):
    m = bpy.data.materials[name]
    t = m.node_tree
    g = next(n for n in t.nodes if n.type=='GROUP').node_tree
    p = next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED')
    print('INNER_PRINCIPLED_INPUTS')
    for i in p.inputs:
        v = getattr(i,'default_value',None)
        try: v = tuple(v)
        except Exception: pass
        print('  ', i.name, bool(i.links), v)
    out = next(n for n in g.nodes if n.type=='GROUP_OUTPUT')
    for i in out.inputs:
        print('  OUT', i.name, [ (l.from_node.name, l.from_socket.name) for l in i.links])
    print([ (n.type, n.name) for n in t.nodes])
    print('props', {k: str(v) for k,v in m.items()})
