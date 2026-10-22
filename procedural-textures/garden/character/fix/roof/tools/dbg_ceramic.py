import bpy
v = p['v']
m = bpy.data.materials['G6 roof / ceramic']
nt = m.node_tree
b = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
if '_orig_from' not in m:
    l = b.inputs['Base Color'].links[0]
    m['_orig_from'] = [l.from_node.name, l.from_socket.identifier]
if v == 'full':
    fn, fs = m['_orig_from']
    src = [s for s in nt.nodes[fn].outputs if s.identifier == fs][0]
elif v == 'soot':
    src = nt.nodes['WK soot'].outputs['Colour']
elif v == 'growth':
    src = nt.nodes['WK wallgrowth'].outputs['Colour']
elif v == 'tone':
    # colour after the tile tone step, before moss/lichen/drip: find the first Vector Math SCALE fed by WK wallgrowth tinted
    src = nt.nodes['WK wallgrowth'].outputs['Colour']
nt.links.new(src, b.inputs['Base Color'])
print('DBGCER', v, flush=True)
