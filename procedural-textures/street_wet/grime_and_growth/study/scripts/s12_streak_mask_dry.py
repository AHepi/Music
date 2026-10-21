# What this does (plain words): STUDY ONLY, saves only two small pictures in the out folder. Puts the wetness layer on in memory with Wetness 0 (bone dry), then shows its "Streak Mask"
# (the rain-run-off lines under the window sills and eaves, which the layer got from the street builder's own window numbers) as plain light on the walls, and measures how much of the
# wall is covered. If the mask is not zero on a dry street, the new grime and stain layers can read it as "where run-off from the sills and eaves goes" without any wetness.
import os, sys, math
import bpy
import numpy as np
base = 'proc-work/street_wet/'
sys.path.insert(0, base + 'tools')
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw
import wetness_layer as wl
out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
aw.apply(wetness=0.0, puddles=0.0)
for name, (node, spec) in aw.APPLIED.items():
    if spec.get('wall'):
        wl.show_mask(bpy.data.materials[name], node, 'Streak Mask')
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 270, 480
scene.eevee.taa_render_samples = 1
scene.view_settings.view_transform, scene.view_settings.look = 'Raw', 'None'
scene.view_settings.exposure, scene.view_settings.gamma = 0.0, 1.0
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
scene.camera = cams['wall_lamp']
scene.render.filepath = os.path.join(out, 'streak_mask_dry_wall_lamp.png')
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(scene.render.filepath)
a = np.array(img.pixels[:]).reshape(-1, 4)[:, 0]
print('STREAK dry: share of picture dots with streak mask over 0.3:', round(float((a > 0.3).mean()), 3), 'over 0.6:', round(float((a > 0.6).mean()), 3), 'max', round(float(a.max()), 3))
scene.camera = cams['main']
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.render.filepath = os.path.join(out, 'streak_mask_dry_main.png')
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(scene.render.filepath)
a = np.array(img.pixels[:]).reshape(-1, 4)[:, 0]
print('STREAK dry main: share over 0.3:', round(float((a > 0.3).mean()), 3), 'max', round(float(a.max()), 3))
