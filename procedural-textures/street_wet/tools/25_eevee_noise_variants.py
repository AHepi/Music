# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2, run 3. Run 1 and 2 showed that the white speckle ("grit") the checker saw on the wet road in EEVEE is NOT made by the stones' fine relief picture (smoothing it, or
# flattening the relief completely, left the speckle as bad: 0.026 on the road's left third against 0.0025 dry). It shows only when the WHOLE picture is drawn (a part-picture
# "border" render has none), only where the surface is glossy but not a mirror, and only in EEVEE's ray tracing (the part of EEVEE that finds reflections). So this run changes
# EEVEE's own settings, one at a time, for the same wet main-camera picture (540 x 960, 16 samples unless said):
#   trace_full      ray tracing at full size instead of half size ("resolution_scale" 1 instead of 2)
#   trace_best      full size, best screen-trace quality, and rays allowed for rougher surfaces
#   rough_half      the road's and pavement's wet roughness 0.5 instead of 0.3 / 0.35 (the checker's suggestion: rougher than the ray tracer's limit of 0.5? borderline)
#   samples_48      48 samples instead of 16 (what the film's plates use)
#   clamp           brightness limit on indirect light (clamp_surface_indirect 1.0, glossy clamp 1.0): stops single very bright samples
#   shadows_1024    a bigger shadow memory
#   (run 4, which part of the road MATERIAL makes the speckle: each of these takes ONE picture out of the road's and the pavement's wet material)
#   no_height       no relief height picture (it decides which dots are 'dry tops')
#   no_rough_pic    no roughness picture (a plain 0.9)
#   no_normal       no relief (normal) picture at all
#   no_colour_pic   no colour picture (a plain grey)
#   rt_off          ray tracing off
#   no_fast_gi      EEVEE's cheap bounce light ('fast GI') off
#   no_shadows      shadows off   (RESULT of run 4: this one cured the speckle: it is shadow noise, from the soft shadows of the lamp and window lights)
#   (run 5, ways to calm the shadow noise)
#   shadow_rays4    shadow_ray_count 4 and shadow_step_count 16 (the most EEVEE allows: smoother soft shadows)
#   shadow_rays4_48 the same with 48 samples
#   shadow_scale2   shadow_resolution_scale 2 (finer shadow maps)
#   small_lights    every window light's radius 0.5 m -> 0.1 m (a change to the SET's lights, not to materials)
# Writes OUT_FOLDER/main_<variant>.png and seconds.txt. Measure with: python3 -I tools/22b_numbers.py OUT_FOLDER wet_base trace_full ...  (name the first one wet_base: copy of work/r22/main_wet.png)
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/25_eevee_noise_variants.py -- OUT_FOLDER [variant ...]
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out_folder = args[0]
wanted = args[1:] or ['trace_full', 'trace_best', 'rough_half', 'samples_48', 'clamp', 'shadows_1024']
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
aw.cameras()
aw.apply(wetness=0.85, puddles=0.5)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = 16
scene.eevee.use_raytracing = True
rt = scene.eevee.ray_tracing_options
defaults = dict(resolution_scale=rt.resolution_scale, quality=rt.screen_trace_quality, max_rough=rt.trace_max_roughness, clamp=scene.eevee.clamp_surface_indirect,
                glossy=scene.eevee.gi_glossy_clamp, pool=scene.eevee.shadow_pool_size, samples=16, ray_count=scene.eevee.shadow_ray_count,
                step_count=scene.eevee.shadow_step_count, res_scale=scene.eevee.shadow_resolution_scale,
                window_radius=next((l.shadow_soft_size for l in bpy.data.lights if 'window_light' in l.name), 0.5))


GROUP_LINKS = {}
for _name in ('street_setts', 'pavement_flags'):
    _node = aw.APPLIED[_name][0]
    GROUP_LINKS[_name] = {socket: _node.inputs[socket].links[0].from_socket for socket in ('Height', 'Roughness', 'Normal', 'Wet Normal', 'Colour') if _node.inputs[socket].is_linked}


def cut(socket_name, value=None):
    for name in GROUP_LINKS:
        node = aw.APPLIED[name][0]
        for link in list(node.inputs[socket_name].links):
            node.id_data  # noqa: B018
            bpy.data.materials[name].node_tree.links.remove(link)
        if value is not None:
            node.inputs[socket_name].default_value = value


def reset():
    for name, links in GROUP_LINKS.items():
        node = aw.APPLIED[name][0]
        for socket_name, source in links.items():
            if not node.inputs[socket_name].is_linked:
                bpy.data.materials[name].node_tree.links.new(source, node.inputs[socket_name])
    scene.eevee.use_raytracing, scene.eevee.use_fast_gi, scene.eevee.use_shadows = True, True, True
    scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count, scene.eevee.shadow_resolution_scale = defaults['ray_count'], defaults['step_count'], defaults['res_scale']
    for light in bpy.data.lights:
        if 'window_light' in light.name:
            light.shadow_soft_size = defaults['window_radius']
    rt.resolution_scale, rt.screen_trace_quality, rt.trace_max_roughness = defaults['resolution_scale'], defaults['quality'], defaults['max_rough']
    scene.eevee.clamp_surface_indirect, scene.eevee.gi_glossy_clamp = defaults['clamp'], defaults['glossy']
    scene.eevee.shadow_pool_size, scene.eevee.taa_render_samples = defaults['pool'], defaults['samples']
    for name, wet_roughness in (('street_setts', 0.3), ('pavement_flags', 0.35)):
        aw.APPLIED[name][0].inputs['Wet Roughness'].default_value = wet_roughness


seconds = {}
for variant in wanted:
    reset()
    if variant == 'trace_full':
        rt.resolution_scale = '1'
    elif variant == 'trace_best':
        rt.resolution_scale = '1'
        rt.screen_trace_quality = 1.0
        rt.trace_max_roughness = 0.8
    elif variant == 'rough_half':
        for name in ('street_setts', 'pavement_flags'):
            aw.APPLIED[name][0].inputs['Wet Roughness'].default_value = 0.5
    elif variant == 'samples_48':
        scene.eevee.taa_render_samples = 48
    elif variant == 'clamp':
        scene.eevee.clamp_surface_indirect = 1.0
        scene.eevee.gi_glossy_clamp = 1.0
    elif variant == 'shadows_1024':
        scene.eevee.shadow_pool_size = '1024'
    elif variant == 'no_height':
        cut('Height', 0.5)
    elif variant == 'no_rough_pic':
        cut('Roughness', 0.9)
    elif variant == 'no_normal':
        cut('Normal', (0.0, 0.0, 1.0))
        cut('Wet Normal', (0.0, 0.0, 1.0))
    elif variant == 'no_colour_pic':
        cut('Colour', (0.2, 0.2, 0.2, 1.0))
    elif variant == 'rt_off':
        scene.eevee.use_raytracing = False
    elif variant == 'no_fast_gi':
        scene.eevee.use_fast_gi = False
    elif variant == 'no_shadows':
        scene.eevee.use_shadows = False
    elif variant in ('shadow_rays4', 'shadow_rays4_48'):
        scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
        if variant.endswith('48'):
            scene.eevee.taa_render_samples = 48
    elif variant == 'shadow_scale2':
        scene.eevee.shadow_resolution_scale = 2.0
    elif variant == 'small_lights':
        for light in bpy.data.lights:
            if 'window_light' in light.name:
                light.shadow_soft_size = 0.1
    scene.render.filepath = os.path.join(out_folder, f'main_{variant}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds[variant] = round(time.time() - started, 1)
    print('DRAWN', variant, seconds[variant], 's', flush=True)
open(os.path.join(out_folder, 'seconds.txt'), 'w').write(str(seconds) + '\n')
