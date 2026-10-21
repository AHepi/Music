# Inspects a blend file for things that behave differently in EEVEE and Cycles. Draws nothing, saves nothing.
import bpy, sys
sc = bpy.context.scene
print('FILE', bpy.data.filepath)
print('ENGINE', sc.render.engine, 'res', sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage)
vs = sc.view_settings
print('VIEW', vs.view_transform, vs.look, vs.exposure, vs.gamma, 'display', sc.display_settings.display_device, 'seq', sc.sequencer_colorspace_settings.name)
print('FILM transparent', sc.render.film_transparent, 'dither', sc.render.dither_intensity, 'filter', sc.render.filter_size)
e = sc.eevee
for k in ('taa_render_samples','use_raytracing','ray_tracing_method','shadow_ray_count','shadow_step_count','use_shadows','use_volumetric_shadows','volumetric_tile_size','light_threshold','shadow_pool_size','shadow_resolution_scale','use_fast_gi','fast_gi_method','gtao_distance','use_gtao','use_bloom','use_ssr','use_motion_blur','clamp_surface_direct','clamp_surface_indirect','use_overscan','fast_gi_ray_count','fast_gi_step_count'):
    if hasattr(e, k): print('EEVEE', k, getattr(e, k))
if hasattr(e,'ray_tracing_options'):
    o = e.ray_tracing_options
    print('EEVEE rt options', {a:getattr(o,a) for a in dir(o) if not a.startswith('_') and a not in ('bl_rna','rna_type')})
c = sc.cycles
for k in ('samples','use_adaptive_sampling','adaptive_threshold','adaptive_min_samples','use_denoising','denoiser','denoising_input_passes','max_bounces','diffuse_bounces','glossy_bounces','transmission_bounces','volume_bounces','transparent_max_bounces','sample_clamp_direct','sample_clamp_indirect','caustics_reflective','caustics_refractive','device','use_light_tree','light_sampling_threshold','film_exposure','blur_glossy','use_fast_gi','pixel_filter_type','filter_width','time_limit','tile_size'):
    if hasattr(c, k): print('CYCLES', k, getattr(c, k))
print('WORLD', sc.world.name if sc.world else None)
if sc.world and sc.world.node_tree:
    for n in sc.world.node_tree.nodes:
        extra = ''
        if n.type == 'BACKGROUND':
            extra = (tuple(n.inputs['Color'].default_value), n.inputs['Strength'].default_value)
        if n.type == 'TEX_SKY':
            extra = dict(sky_type=n.sky_type, sun_elevation=n.sun_elevation, sun_rotation=n.sun_rotation, sun_disc=n.sun_disc, air=n.air_density, dust=n.dust_density) if hasattr(n,'sky_type') else ''
        print('  WORLD NODE', n.type, n.name, extra)
    wl = sc.world
    for a in ('use_sun_shadow','sun_threshold','sun_angle','probe_resolution','light_settings'):
        if hasattr(wl, a): print('  world attr', a, getattr(wl,a))
print('LIGHTS')
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        d = o.data
        print('  ', o.name, d.type, 'E', round(d.energy,2), 'col', tuple(round(x,3) for x in d.color), 'hide_render', o.hide_render, 'shadow', getattr(d,'use_shadow',None), 'soft', getattr(d,'shadow_soft_size',None), 'angle', getattr(d,'angle',None), 'size', getattr(d,'size',None), 'spot', getattr(d,'spot_size',None), 'loc', tuple(round(x,2) for x in o.location), 'diffuse', getattr(d,'diffuse_factor',None), 'spec', getattr(d,'specular_factor',None), 'vol', getattr(d,'volume_factor',None), 'use_nodes', getattr(d,'use_nodes',None))
print('MATERIALS')
for m in bpy.data.materials:
    info = []
    if hasattr(m, 'surface_render_method'): info.append(('method', m.surface_render_method))
    if hasattr(m, 'blend_method'): info.append(('blend', m.blend_method))
    if hasattr(m, 'use_backface_culling'): info.append(('cull', m.use_backface_culling))
    types = {}
    if m.use_nodes and m.node_tree:
        for n in m.node_tree.nodes:
            types[n.type] = types.get(n.type, 0) + 1
    emis = []
    if m.use_nodes and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == 'EMISSION':
                emis.append(('EMISSION', n.inputs['Strength'].default_value))
            if n.type == 'BSDF_PRINCIPLED':
                es = n.inputs['Emission Strength'].default_value
                al = n.inputs['Alpha'].default_value
                tr = n.inputs['Transmission Weight'].default_value
                if es > 0 or al < 1 or tr > 0:
                    emis.append(('PRINCIPLED emis', es, 'alpha', al, 'transmission', tr))
    print('  ', m.name, 'users', m.users, info, emis)
print('OBJECT COUNTS')
from collections import Counter
cnt = Counter(o.type for o in bpy.data.objects)
print(dict(cnt))
print('PROBES / VOLUMES / SPECIAL')
for o in bpy.data.objects:
    if o.type in ('LIGHT_PROBE','VOLUME') or (o.type=='MESH' and (o.display_type!='TEXTURED' or o.hide_render or not o.visible_shadow or not o.visible_camera or not o.visible_glossy or not o.visible_diffuse or not o.visible_transmission or not o.visible_volume_scatter)):
        print('  ', o.name, o.type, 'display', o.display_type, 'hide_render', o.hide_render, 'vis cam/diff/gloss/trans/shadow', o.visible_camera, o.visible_diffuse, o.visible_glossy, o.visible_transmission, o.visible_shadow)
print('MODIFIERS')
for o in bpy.data.objects:
    for md in o.modifiers:
        print('  ', o.name, md.type, md.name)
print('CAMERA', sc.camera.name if sc.camera else None, sc.camera.data.lens if sc.camera else None, sc.camera.data.sensor_width if sc.camera else None, sc.camera.data.sensor_fit if sc.camera else None, sc.camera.data.angle_y if sc.camera else None, sc.camera.data.dof.use_dof if sc.camera else None, 'clip', sc.camera.data.clip_start, sc.camera.data.clip_end)
print('VIEWLAYER', [ (vl.name, vl.use_pass_combined) for vl in sc.view_layers])
