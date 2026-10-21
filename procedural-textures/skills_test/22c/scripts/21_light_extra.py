# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22c, part 1b: follow-ups on the lighting skill's checks (street COPY only, nothing saved back):
#  (a) the nearest lit lamp that is really in the main camera's view (gas_lamp_1; gas_lamp_0 stands outside the 23-degree-wide frame) as the subject;
#  (b) does the skill's colour-pipeline audit (color_audit) catch a planted fault: a data picture (roughness) set to colour (sRGB), first on a plain material
#      and then inside the wetness layer's node group;
#  (c) is the per-lamp share of light_contributions meaningful here? Draws the street with every lamp off and the sky light off: how much of the colliery's
#      brightness is left (emission of lit windows, lamp glass, sky dome), which every "one lamp alone" picture carries as a constant.
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


def plain(x):
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    return x


# (a) lamp 1 as the subject, both states
LAMP = ['gas_lamp_1_post', 'gas_lamp_1_glass']
log['lamp1'] = {}
for state in ('today', 'wet'):
    if state == 'wet':
        aw.apply(wetness=0.0, puddles=0.0)
        aw.set_state(0.85, 0.5)
    res = BL.render(os.path.join(out, f'x_{state}'), exr=True, depth='32')
    mask = BL.mask_cryptomatte(res['exr'], LAMP)
    rep = BL.analyse(res['png'], mask, exr=res['exr'])
    log['lamp1'][state] = {'mask_area_pct': round(float(100 * (mask > 0.5).mean()), 3), 'subject': rep.get('subject'), 'focus': rep['focus'], 'thirds': rep.get('thirds'),
                           'squint_on_subject': rep['squint'].get('max_on_subject'), 'verdict': BL.verdict(rep)}
    if state == 'wet':
        BL.value_study(res['png'], os.path.join(out, 'values_wet_lamp1.png'), mask=mask)
        colliery = BL.mask_cryptomatte(res['exr'], ['headframe_lattice', 'winding_wheel_left', 'winding_wheel_right', 'engine_house_walls', 'engine_house_trim', 'engine_house_glass'])
        wet_exr = res['exr']

# (b) colour audit: planted faults, with the wetness layer on (state wet is on now)
images = {}
for m in bpy.data.materials:
    if m.node_tree and m.users:
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeTexImage' and n.image:
                images.setdefault(n.image.name, n.image.colorspace_settings.name)
log['image_colourspaces_in_wet_state'] = images
baseline_audit = BL.color_audit()
# fault 1: a data picture directly into a plain Principled socket
test = bpy.data.materials.new('trial_plain_fault')
test.use_nodes = True
img = bpy.data.images.new('trial_fake_rough', 8, 8)
img.colorspace_settings.name = 'sRGB'
tex = test.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = img
bsdf = next(n for n in test.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
test.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Roughness'])
holder = bpy.data.objects.new('trial_holder', bpy.data.meshes.new('trial_holder_mesh'))
holder.data.materials.append(test)
scene.collection.objects.link(holder)
fault1 = BL.color_audit()
# fault 2: the street's own roughness picture inside the wetness layer set to sRGB
target = [n for n in images if 'rough' in n.lower()]
changed = None
for name in target[:1]:
    bpy.data.images[name].colorspace_settings.name = 'sRGB'
    changed = name
fault2 = BL.color_audit()
log['color_audit'] = {'baseline_wet_state': baseline_audit, 'plain_fault_planted': fault1, 'wetness_layer_picture_set_to_sRGB': {'image': changed, 'audit': fault2}}
bpy.data.objects.remove(holder)

# (c) baseline emission: every lamp and sun off, world off
lights = [o for o in scene.objects if o.type == 'LIGHT']
for o in lights:
    o.hide_render = True
bg = scene.world.node_tree.nodes['Background']
saved = bg.inputs['Strength'].default_value
bg.inputs['Strength'].default_value = 0.0
base = BL.render(os.path.join(out, 'x_all_lights_off'), exr=True, depth='32')
for o in lights:
    o.hide_render = False
bg.inputs['Strength'].default_value = saved
full = BL.load_rgba(wet_exr)[..., :3]
off = BL.load_rgba(base['exr'])[..., :3]
m = colliery > 0.5
yf, yo = BL.luma(full)[m].mean(), BL.luma(off)[m].mean()
log['baseline_without_lights'] = {'colliery_mean_linear_all_lights_on': round(float(yf), 5), 'colliery_mean_linear_all_lights_off_and_world_off': round(float(yo), 5),
                                  'share_left_with_no_lamp_at_all': round(float(yo / yf), 3),
                                  'frame_mean_all_on': round(float(BL.luma(full).mean()), 5), 'frame_mean_all_off': round(float(BL.luma(off).mean()), 5)}
json.dump(plain(log), open(os.path.join(out, 'light_extra.json'), 'w'), indent=1)
print('DONE extra')
