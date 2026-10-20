"""Plain note: our own test. Builds one Ucupaint stack, then makes the Colour and Roughness pictures TWO ways in the same
Blender session: (a) Ucupaint's own channel bake, (b) our 'photograph' route (straight-down camera over the plane, the channel
shown as plain emitted light, as lib/bake_harness.py does). Saves both so a separate script can measure how different they are."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; SIZE = int(sys.argv[sys.argv.index('--')+2])
os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
bpy.ops.wm.y_new_layer(name='Base', type='COLOR', solid_color=(0.55,0.25,0.12), uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Cloud', type='NOISE', uv_map='UVMap')
yp, grp = get_yp(mat)
for l in yp.layers:
    for i in (0,2): l.channels[i].enable = True
yp.layers['Cloud'].channels[2].socket_input_name = 'Factor'   # grey noise (not the colour noise) feeds the single-number Roughness channel
yp.layers['Cloud'].channels[0].intensity_value = 0.4
yp.layers['Cloud'].channels[0].blend_type = 'MULTIPLY'
print('group outputs:', [(s.name, s.socket_type if hasattr(s,'socket_type') else s.type) for s in grp.outputs])
# ---------------- (b) photograph first (before baking switches the group to baked pictures)
photo = bpy.data.scenes.new('photo'); photo.render.engine='CYCLES'
photo.cycles.device='CPU'; photo.cycles.samples=4; photo.cycles.use_adaptive_sampling=False; photo.cycles.use_denoising=False
photo.cycles.max_bounces=0; photo.cycles.pixel_filter_type='BOX'; photo.cycles.filter_width=1.0
photo.render.resolution_x=photo.render.resolution_y=SIZE; photo.render.resolution_percentage=100
photo.view_settings.look='None'; photo.view_settings.exposure=0; photo.view_settings.gamma=1
w = bpy.data.worlds.new('black'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1); photo.world=w
photo.collection.objects.link(obj)   # same plane object, same UVs, same material
cam_data = bpy.data.cameras.new('cam'); cam_data.type='ORTHO'; cam_data.ortho_scale=1.0
cam = bpy.data.objects.new('cam', cam_data); cam.location=(0,0,5); photo.collection.objects.link(cam); photo.camera=cam
def photograph(channel, path, raw):
    m = bpy.data.materials.new('photo_'+channel); m.use_nodes=True; t=m.node_tree; t.nodes.clear()
    g = t.nodes.new('ShaderNodeGroup'); g.node_tree = grp.node_tree
    em = t.nodes.new('ShaderNodeEmission'); out = t.nodes.new('ShaderNodeOutputMaterial')
    if channel=='Color': t.links.new(g.outputs['Color'], em.inputs['Color'])
    else:
        c = t.nodes.new('ShaderNodeCombineColor')
        for s in ('Red','Green','Blue'): t.links.new(g.outputs[channel], c.inputs[s])
        t.links.new(c.outputs['Color'], em.inputs['Color'])
    t.links.new(em.outputs['Emission'], out.inputs['Surface'])
    obj.data.materials[0] = m
    photo.view_settings.view_transform = 'Raw' if raw else 'Standard'
    photo.display_settings.display_device='sRGB'
    photo.render.image_settings.file_format='PNG'; photo.render.image_settings.color_mode='RGB'; photo.render.image_settings.color_depth='8'
    photo.render.filepath = path
    t0=time.time(); bpy.ops.render.render(write_still=True, scene=photo.name); return time.time()-t0
t_c = photograph('Color', os.path.join(OUT,'photo_colour.png'), False)
t_r = photograph('Roughness', os.path.join(OUT,'photo_roughness.png'), True)
obj.data.materials[0] = mat
print('photograph seconds: colour %.2f roughness %.2f' % (t_c, t_r))
# ---------------- (a) Ucupaint's own bake
ov = ui_override(); t=time.time()
with bpy.context.temp_override(**ov):
    bpy.ops.wm.y_bake_channels(width=SIZE, height=SIZE, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
print('Ucupaint bake seconds: %.2f' % (time.time()-t))
for im in bpy.data.images:
    if im.name in ('Ucupaint Material Color','Ucupaint Material Roughness'):
        im.filepath_raw = os.path.join(OUT, 'ucu_' + im.name.split()[-1].lower() + '.png'); im.file_format='PNG'; im.save()
