import bpy
m = bpy.data.materials['CT / Stone painterly surface.008']
nt = m.node_tree
def val(s):
    d = getattr(s, 'default_value', None)
    if d is None: return None
    try: return tuple(round(x,3) for x in d)
    except TypeError: return round(d,3) if isinstance(d,float) else d
for n in nt.nodes:
    if n.bl_idname == 'ShaderNodeGroup' and n.name.startswith('WK'):
        print('NODE', n.name, n.node_tree.name)
        for i in n.inputs:
            print('    in', i.name, val(i), 'LINKED' if i.is_linked else '')
# the principled base colour source
b = nt.nodes['Principled BSDF']
for i in ('Base Color','Roughness'):
    s = b.inputs[i]
    print('BSDF', i, s.is_linked, [ (l.from_node.name, l.from_socket.name) for l in s.links])
