import bpy, sys
exr = sys.argv[sys.argv.index('--')+1]
img = bpy.data.images.load(exr, check_existing=False)
print('type before touching', img.type)
_ = img.size[0]
print('type after size', img.type, img.size[:])
img.reload()
print('type after reload', img.type)
tree = bpy.data.node_groups.new('t','CompositorNodeTree')
feed = tree.nodes.new('CompositorNodeImage'); feed.image = img
print([ (o.name, o.enabled) for o in feed.outputs])
try: tree.update_tag()
except Exception as e: print('upd', e)
bpy.context.scene.compositing_node_group = tree
bpy.context.view_layer.update()
print([ (o.name, o.enabled) for o in feed.outputs][:14])
print('props', [p.identifier for p in feed.bl_rna.properties if p.identifier in ('layer','layer_name','view','frame_duration','use_auto_refresh')])
try:
    print('layer items', [(i.identifier,i.name) for i in feed.bl_rna.properties['layer'].enum_items])
except Exception as e: print('items err', e)
try:
    feed.layer = 'ViewLayer'
    bpy.context.view_layer.update()
    print('after layer=ViewLayer', [ (o.name, o.enabled) for o in feed.outputs][:20])
except Exception as e: print('set layer err', e)
