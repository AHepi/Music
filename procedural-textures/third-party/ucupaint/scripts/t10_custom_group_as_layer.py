"""Plain note: our own test. Asks: can one of OUR recipe node groups (the seamless noise from lib/recipe_tools.py) act as the picture-maker
of a Ucupaint layer? Ucupaint has no button for this, so we try the hack of swapping the noise node inside the layer's own node group,
then changing layer settings (which makes Ucupaint reconnect everything) and baking."""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, 'proc-work/lib')
import bpy, numpy as np
from ucu_common import *
import recipe_tools as rt
OUT = sys.argv[sys.argv.index('--')+1]; os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene()
bpy.context.scene.render.engine='CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
common = importlib.import_module(MOD + '.common')
bpy.ops.wm.y_new_layer(name='Cloud', type='NOISE', uv_map='UVMap')
yp, grp = get_yp(mat); layer = yp.layers[0]
ltree = [n for n in grp.node_tree.nodes if n.type=='GROUP' and n.node_tree.name.startswith('.yP Layer')][0].node_tree
print('layer tree', ltree.name, 'source node name stored in layer:', layer.source)
src = ltree.nodes[layer.source]
print('noise node inputs:', [i.name for i in src.inputs], '| outputs:', [o.name for o in src.outputs])
print('links into noise node:', [(l.from_node.name, l.from_socket.name, l.to_socket.name) for l in ltree.links if l.to_node == src])
print('links out of noise node:', [(l.from_socket.name, l.to_node.name, l.to_socket.name) for l in ltree.links if l.from_node == src])
# our seamless noise group, wrapped so its outputs are called 'Factor' and 'Color' like Blender's noise node
inner = rt.tileable_noise_group()
wrap = bpy.data.node_groups.new('OurNoiseAsSource', 'ShaderNodeTree')
wrap.interface.new_socket('Vector', in_out='INPUT', socket_type='NodeSocketVector')
wrap.interface.new_socket('Factor', in_out='OUTPUT', socket_type='NodeSocketFloat')
wrap.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor')
gi = wrap.nodes.new('NodeGroupInput'); go = wrap.nodes.new('NodeGroupOutput'); gn = wrap.nodes.new('ShaderNodeGroup'); gn.node_tree = inner
gn.inputs['Scale'].default_value = 5.0; gn.inputs['Detail'].default_value = 5.0
wrap.links.new(gi.outputs['Vector'], gn.inputs['Vector']); wrap.links.new(gn.outputs['Fac'], go.inputs['Factor']); wrap.links.new(gn.outputs['Color'], go.inputs['Color'])
# swap
in_links = [(l.from_socket, l.to_socket.name) for l in ltree.links if l.to_node == src]
out_links = [(l.from_socket.name, l.to_node, l.to_socket) for l in ltree.links if l.from_node == src]
name = src.name; loc = src.location.copy(); ltree.nodes.remove(src)
new = ltree.nodes.new('ShaderNodeGroup'); new.node_tree = wrap; new.name = name; new.label = name; new.location = loc
for from_sock, to_name in in_links:
    if to_name == 'Vector': ltree.links.new(from_sock, new.inputs['Vector'])
for from_name, to_node, to_sock in out_links:
    ltree.links.new(new.outputs[from_name if from_name in new.outputs else 'Color'], to_sock)
print('swapped. layer.source still points to', layer.source, '->', ltree.nodes.get(layer.source))
def bake(tag, size=256):
    ov = ui_override()
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.y_bake_channels(width=size, height=size, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
    im = bpy.data.images['Ucupaint Material Color']; im.filepath_raw = os.path.join(OUT, tag+'.png'); im.file_format='PNG'; im.save()
    with bpy.context.temp_override(**ov): bpy.ops.wm.y_delete_baked_channel_images()
    for i in list(bpy.data.images):
        if i.name.startswith('Ucupaint Material'): bpy.data.images.remove(i)
bake('after_swap')
# now force Ucupaint to rebuild/reconnect the layer by changing settings
layer.channels[0].blend_type = 'ADD'; layer.channels[0].blend_type = 'MIX'; layer.enable = False; layer.enable = True
layer.scale = (1,1,1)
print('after settings changes, source node type:', ltree.nodes.get(layer.source).bl_idname if ltree.nodes.get(layer.source) else None)
bake('after_reconnect')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'custom_group_layer.blend'), copy=True)
