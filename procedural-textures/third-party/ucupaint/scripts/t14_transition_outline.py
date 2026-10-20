"""Plain note: our own test. Ucupaint can draw a coloured 'transition ramp' (an outline) and a 'transition bump' (a raised edge) where a
layer's mask goes from on to off. Our references have dark painted outlines and chunky edges, so we test it: a layer of orange patches
(voronoi mask) with a dark ramp at the mask edge, plus bump; bake colour and height headless."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene()
bpy.context.scene.render.engine='CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
bpy.ops.wm.y_new_layer(name='Ground', type='COLOR', solid_color=(0.25,0.12,0.06), uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Patches', type='COLOR', solid_color=(0.85,0.45,0.15), uv_map='UVMap')
bpy.ops.wm.y_new_layer_mask(name='PatchMask', type='VORONOI', texcoord_type='UV', uv_name='UVMap', blend_type='MULTIPLY')
yp, grp = get_yp(mat); L = yp.layers[0]
ch = L.channels[0]; ch.enable = True
print('transition ramp props before:', ch.enable_transition_ramp, ch.show_transition_ramp)
ch.show_transition_ramp = True; ch.enable_transition_ramp = True
nt = [n for n in grp.node_tree.nodes if n.type=='GROUP' and n.node_tree.name==('.yP Layer Patches')][0].node_tree
ramps = [n for n in nt.nodes if n.type=='VALTORGB']
print('colour-ramp nodes in layer tree:', [n.name for n in ramps])
for n in ramps:
    cr = n.color_ramp
    print('  ramp', n.name, 'elements', [(round(e.position,2), tuple(round(c,2) for c in e.color)) for e in cr.elements])
# make the ramp a dark outline: dark at one end, transparent-ish (alpha 0) at other
for n in ramps:
    cr = n.color_ramp
    cr.elements[0].color = (0.02,0.01,0.005,1.0); cr.elements[-1].color = (0.0,0.0,0.0,0.0)
ch3 = L.channels[3]; ch3.enable = True; ch3.normal_map_type = 'BUMP_MAP'
ch3.show_transition_bump = True; ch3.enable_transition_bump = True
print('bump props: value', ch3.transition_bump_value, 'distance', ch3.transition_bump_distance)
ov = ui_override(); t=time.time()
with bpy.context.temp_override(**ov):
    bpy.ops.wm.y_bake_channels(width=512, height=512, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
print('bake %.2fs' % (time.time()-t))
for im in bpy.data.images:
    if im.name.startswith('Ucupaint Material'):
        im.filepath_raw=os.path.join(OUT, im.name.replace(' ','_')+'.png'); im.file_format='PNG'; im.save(); print('saved', im.name)
