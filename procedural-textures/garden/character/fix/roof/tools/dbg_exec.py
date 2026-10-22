# code snippet run (exec) before each debug picture: rewires every G6 roof stone material's Base Color to a chosen point of the weathering-kit chain
# p['dbg'] in: scan, foot, dirt, cracks, growth, moss (end of kit), full (no change = marks as built)
import bpy
stage = p['dbg']
names = {'foot': 'WK foot', 'dirt': 'WK dirt', 'cracks': 'WK wallcracks', 'growth': 'WK wallgrowth', 'moss': 'WK groundmoss'}
n_ok = 0
for m in bpy.data.materials:
    if not m.name.startswith('G6 roof / ') or m.node_tree is None:
        continue
    nt = m.node_tree
    if nt.nodes.get('WK foot') is None or nt.nodes.get('WK groundmoss') is None:
        continue
    b = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
    if '_orig_col' not in m:
        m['_orig_col'] = 1
        # remember the full link source by node/socket name
        l = b.inputs['Base Color'].links[0]
        m['_orig_from'] = [l.from_node.name, l.from_socket.identifier]
    if stage == 'full':
        fn, fs = m['_orig_from']
        src = [s for s in nt.nodes[fn].outputs if s.identifier == fs][0]
    elif stage == 'scan':
        src = nt.nodes['WK foot'].inputs['Colour'].links[0].from_socket
    else:
        src = nt.nodes[names[stage]].outputs['Colour']
    nt.links.new(src, b.inputs['Base Color'])
    n_ok += 1
print('DBG', stage, 'materials rewired', n_ok, flush=True)
