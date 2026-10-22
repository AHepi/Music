import bpy
names=[n for n in dir(bpy.types) if n.startswith('CompositorNode')]
print(len(names)); print(sorted(names))
sc=bpy.context.scene
t=bpy.data.node_groups.get('GARDEN finish')
print('finish group', t, [ (n.name, n.bl_idname) for n in t.nodes] if t else None)
print('scene comp group', sc.compositing_node_group.name if sc.compositing_node_group else None)
if sc.compositing_node_group:
    for n in sc.compositing_node_group.nodes: print('  scene node', n.name, n.bl_idname)
