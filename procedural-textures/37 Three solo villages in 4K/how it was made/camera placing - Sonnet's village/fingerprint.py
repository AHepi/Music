import bpy, sys, json, math
out_path = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene; r = sc.render; cy = sc.cycles; vs = sc.view_settings
fp = {}
fp['render'] = dict(engine=r.engine, res=[r.resolution_x, r.resolution_y, r.resolution_percentage], samples=cy.samples, adaptive=cy.use_adaptive_sampling,
    thr=round(cy.adaptive_threshold, 6), denoise=cy.use_denoising, denoiser=cy.denoiser, device=cy.device, max_bounces=cy.max_bounces,
    diffuse=cy.diffuse_bounces, glossy=cy.glossy_bounces, transmission=cy.transmission_bounces, volume=cy.volume_bounces, transparent=cy.transparent_max_bounces,
    caustics=[cy.caustics_reflective, cy.caustics_refractive], clamp=[cy.sample_clamp_direct, cy.sample_clamp_indirect], persistent=r.use_persistent_data,
    film_transparent=r.film_transparent, filter=cy.filter_width, fmt=[r.image_settings.file_format, r.image_settings.color_depth, r.image_settings.quality],
    filepath=r.filepath, view=vs.view_transform, look=vs.look, exposure=round(vs.exposure, 5), gamma=vs.gamma, display=sc.display_settings.display_device,
    curves=vs.use_curve_mapping, camera=sc.camera.name if sc.camera else None, world=sc.world.name, frames=[sc.frame_start, sc.frame_end, sc.frame_current],
    motion_blur=r.use_motion_blur, light_tree=getattr(cy, 'use_light_tree', None), seed=cy.seed)
objs = {}
for o in bpy.data.objects:
    m = [round(v, 4) for row in o.matrix_world for v in row]
    d = dict(t=o.type, data=o.data.name if o.data else None, m=m, colls=sorted(c.name for c in o.users_collection), hide_r=o.hide_render, hide_v=o.hide_viewport, mods=[x.name for x in o.modifiers])
    if o.type == 'CAMERA':
        cd = o.data
        d['cam'] = dict(lens=cd.lens, sensor=cd.sensor_width, fit=cd.sensor_fit, clip=[cd.clip_start, cd.clip_end], shift=[cd.shift_x, cd.shift_y], dof=cd.dof.use_dof, fstop=cd.dof.aperture_fstop, fd=round(cd.dof.focus_distance, 4), type=cd.type)
    if o.type == 'LIGHT':
        d['light'] = [o.data.type, o.data.energy, list(o.data.color)]
    objs[o.name] = d
fp['objects'] = objs
fp['counts'] = {k: len(getattr(bpy.data, k)) for k in ('objects', 'meshes', 'materials', 'node_groups', 'images', 'cameras', 'lights', 'collections', 'worlds', 'textures', 'curves')}
fp['mesh_sizes'] = {me.name: [len(me.vertices), len(me.polygons)] for me in bpy.data.meshes}
fp['materials'] = sorted(m.name for m in bpy.data.materials)
w = sc.world
fp['world_nodes'] = sorted((n.name, n.bl_idname) for n in w.node_tree.nodes) if w.node_tree else []
json.dump(fp, open(out_path, 'w'), sort_keys=True)
print('FP OK', fp['counts'])
