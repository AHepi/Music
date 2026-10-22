import bpy
for ng in bpy.data.node_groups:
    if 'WALL' in ng.name.upper() and 'GROWTH' in ng.name.upper():
        print('GROUP', ng.name, len(ng.nodes))
        ins=[it.name for it in ng.interface.items_tree if it.item_type=='SOCKET' and it.in_out=='INPUT']
        print('  inputs', len(ins), [i for i in ins if 'ich' in i.lower() or 'dial' in i.lower()][:20])
        break
# find a material with lantern
m = bpy.data.materials['CT / Stone painterly surface.034']
print('MAT', m.name, len(m.node_tree.nodes))
for n in m.node_tree.nodes:
    if n.bl_idname=='ShaderNodeGroup':
        g = n.node_tree.name if n.node_tree else None
        print('  groupnode', n.name, g)
        for s in n.inputs:
            if 'ichen' in s.name or 'dots' in s.name.lower():
                print('     ', s.name, s.is_linked, getattr(s,'default_value',None))
# how many materials include a wall growth group node
cnt=0
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.bl_idname=='ShaderNodeGroup' and n.node_tree and 'WALL GROWTH' in n.node_tree.name.upper():
                cnt+=1
print('materials with wall growth group', cnt)
