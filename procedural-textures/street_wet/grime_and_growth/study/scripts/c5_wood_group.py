# What this does (plain words): STUDY ONLY, saves nothing. Prints the add-on's "FOUNDRY / Wood" shader group: its inputs, outputs and the box that makes the final surface.
# Run: blender -b --disable-autoexec FILE --python c5_wood_group.py -- OUT.txt
import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
L = []
g = bpy.data.node_groups.get('FOUNDRY / Wood')
for it in g.interface.items_tree:
    if it.item_type == 'SOCKET':
        L.append(f'{it.in_out:6s} {it.socket_type:22s} {it.name}  default={getattr(it, "default_value", None) if not hasattr(getattr(it, "default_value", None), "__len__") else list(it.default_value)}')
for n in g.nodes:
    if n.bl_idname in ('NodeGroupOutput', 'ShaderNodeBsdfPrincipled'):
        for i in n.inputs:
            if i.is_linked: L.append(f'{n.name}: "{i.name}" <- {i.links[0].from_node.name}.{i.links[0].from_socket.name}')
L.append('nodes: %d' % len(g.nodes))
L.append('users of FOUNDRY / Wood: %d; Wet Stone users: %d' % (g.users, bpy.data.node_groups['FOUNDRY / Wet Stone'].users))
open(out, 'w').write('\n'.join(L))
