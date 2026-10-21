# Trial 22b: lists the control sockets of the two node groups that add_wear builds (to check whether they have a seed). Reads only.
import bpy
for g in bpy.data.node_groups:
    if g.name.startswith('BX'):
        print('GROUP', g.name, [s.name for s in g.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'], '->', [s.name for s in g.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT'])
