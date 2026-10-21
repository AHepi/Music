# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22c, part 1c (street COPY only, nothing saved back). Two things the first follow-up got wrong or left open:
#  (b2) the colour audit, this time with the right picture: the street's own roughness picture (square_cobblestone_rough.jpg, inside the wetness layer) set
#       to colour (sRGB) on purpose. Does color_audit notice?
#  (c2) the per-lamp "share" of light_contributions with the constant glow of the emissive surfaces taken away (a picture with every lamp and the sky light
#       off), to see whether the skill's numbers can answer "which lamps light the colliery" at all.
import json
import os
import sys

import bpy
import numpy as np

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-lighting-rendering/scripts')
import bx_light as BL  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import apply_wetness_to_set as aw  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
scene.camera = aw.cameras()['main']
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 540, 960, 100
scene.eevee.taa_render_samples = 64
scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
scene.view_layers[0].use_pass_cryptomatte_object = True
log = {}
aw.apply(wetness=0.0, puddles=0.0)
aw.set_state(0.85, 0.5)

# (b2) planted fault inside the wetness layer
log['audit_before'] = BL.color_audit()
used_by = []
for m in bpy.data.materials:
    if m.node_tree and m.users:
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeTexImage' and n.image and n.image.name == 'square_cobblestone_rough.jpg':
                used_by.append((m.name, n.name, [l.to_node.bl_idname + ':' + l.to_socket.name for l in m.node_tree.links if l.from_node == n]))
log['rough_picture_used_by'] = used_by[:6]
bpy.data.images['square_cobblestone_rough.jpg'].colorspace_settings.name = 'sRGB'
bpy.data.images['square_cobblestone_normal_smooth_4.png'].colorspace_settings.name = 'sRGB'
log['audit_after_two_data_pictures_set_to_sRGB'] = BL.color_audit()
bpy.data.images['square_cobblestone_rough.jpg'].colorspace_settings.name = 'Non-Color'
bpy.data.images['square_cobblestone_normal_smooth_4.png'].colorspace_settings.name = 'Non-Color'

# (c2) per-lamp share on the colliery with the constant emissive glow taken away
COLL = ['headframe_lattice', 'winding_wheel_left', 'winding_wheel_right', 'engine_house_walls', 'engine_house_trim', 'engine_house_glass']
res = BL.render(os.path.join(out, 'y_wet'), exr=True, depth='32')
mask = BL.mask_cryptomatte(res['exr'], COLL)
lights = [o for o in scene.objects if o.type == 'LIGHT']
contrib = BL.light_contributions(lights, mask, os.path.join(out, 'solo'), pct=50)
for o in lights:
    o.hide_render = True
bg = scene.world.node_tree.nodes['Background']
saved = bg.inputs['Strength'].default_value
bg.inputs['Strength'].default_value = 0.0
scene.render.resolution_percentage = 50
base = BL.render(os.path.join(out, 'y_off'), exr=True, depth='32')
scene.render.resolution_percentage = 100
for o in lights:
    o.hide_render = False
bg.inputs['Strength'].default_value = saved
off = BL.luma(BL.load_rgba(base['exr'])[..., :3])
mb = mask > 0.5
yi = (np.arange(off.shape[0]) * mb.shape[0] / off.shape[0]).astype(int)
xi = (np.arange(off.shape[1]) * mb.shape[1] / off.shape[1]).astype(int)
baseline = float(off[mb[yi][:, xi]].mean())
log['baseline_mean_linear_no_lights'] = round(baseline, 5)
net = {k: max(v['mean'] - baseline, 0.0) for k, v in contrib.items()}
tot = sum(net.values()) or 1e-9
groups = {'gas_lamps': 0.0, 'cottage_window_lights': 0.0, 'engine_house_lights': 0.0, 'suns': 0.0, 'world': 0.0}
for k, v in net.items():
    key = 'gas_lamps' if k.startswith('gas_lamp') else 'cottage_window_lights' if 'window_light' in k else 'engine_house' if k.startswith('engine_house') else 'world' if k == 'World' else 'suns'
    groups[key if key != 'engine_house' else 'engine_house_lights'] += v / tot
log['group_share_skill_as_given'] = None
raw_tot = sum(v['mean'] for v in contrib.values()) or 1e-9
raw = {'gas_lamps': 0.0, 'cottage_window_lights': 0.0, 'engine_house_lights': 0.0, 'suns': 0.0, 'world': 0.0}
for k, v in contrib.items():
    key = 'gas_lamps' if k.startswith('gas_lamp') else 'cottage_window_lights' if 'window_light' in k else 'engine_house_lights' if k.startswith('engine_house') else 'world' if k == 'World' else 'suns'
    raw[key] += v['mean'] / raw_tot
log['group_share_skill_as_given'] = {k: round(x, 3) for k, x in raw.items()}
log['group_share_glow_taken_away'] = {k: round(x, 3) for k, x in groups.items()}
log['top_net_lights'] = sorted(((k, round(v / tot, 3)) for k, v in net.items()), key=lambda t: -t[1])[:6]
log['sum_of_net_vs_all_on'] = {'sum_of_net_means': round(sum(net.values()), 5), 'all_on_minus_baseline': round(float(BL.luma(BL.load_rgba(res['exr'])[..., :3])[mb].mean()) - baseline, 5)}
json.dump(log, open(os.path.join(out, 'light_extra2.json'), 'w'), indent=1)
print('DONE extra2')
