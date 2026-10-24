# Read-only state dump for before/after comparison: cameras (exact), render and colour settings, datablock counts,
# object transforms. Run: blender -b FILE.blend --python dump_state.py -- OUT.json
import bpy, json, sys, hashlib
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
d = {'file': bpy.data.filepath, 'scene_camera': sc.camera.name if sc.camera else None, 'frame': sc.frame_current}
cams = {}
for ob in bpy.data.objects:
    if ob.type != 'CAMERA':
        continue
    c = ob.data
    cams[ob.name] = dict(data=c.name, matrix=[list(r) for r in ob.matrix_world], rot_mode=ob.rotation_mode,
                         quat=list(ob.rotation_quaternion), euler=list(ob.rotation_euler), loc=list(ob.location),
                         lens=c.lens, sensor=[c.sensor_width, c.sensor_height, c.sensor_fit], type=c.type,
                         ortho=c.ortho_scale, clip=[c.clip_start, c.clip_end], shift=[c.shift_x, c.shift_y],
                         dof=[c.dof.use_dof, c.dof.focus_distance, c.dof.aperture_fstop, c.dof.focus_object.name if c.dof.focus_object else None],
                         collections=[x.name for x in ob.users_collection], hide_render=ob.hide_render)
d['cameras'] = cams
r, cy, vs = sc.render, sc.cycles, sc.view_settings
d['render'] = dict(engine=r.engine, res=[r.resolution_x, r.resolution_y, r.resolution_percentage], samples=cy.samples,
                   adaptive=[cy.use_adaptive_sampling, cy.adaptive_threshold, cy.adaptive_min_samples],
                   denoise=[cy.use_denoising, str(cy.denoiser), str(cy.denoising_input_passes), str(cy.denoising_prefilter)],
                   device=cy.device, bounces=[cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces,
                                              cy.volume_bounces, cy.transparent_max_bounces],
                   clamp=[cy.sample_clamp_direct, cy.sample_clamp_indirect], filter_width=cy.filter_width,
                   compositing=r.use_compositing, compositor_device=getattr(r, 'compositor_device', None),
                   persistent=r.use_persistent_data, fmt=[r.image_settings.file_format, r.image_settings.quality],
                   film_transparent=r.film_transparent, light_tree=cy.use_light_tree)
d['colour'] = dict(display=sc.display_settings.display_device, view=vs.view_transform, look=vs.look, exposure=vs.exposure,
                   gamma=vs.gamma, curves=vs.use_curve_mapping, sequencer=sc.sequencer_colorspace_settings.name)
ng = getattr(sc, 'compositing_node_group', None)
d['compositor'] = None if ng is None else dict(name=ng.name, haze=ng.nodes['haze_strength'].inputs[1].default_value if 'haze_strength' in ng.nodes else None)
d['world'] = sc.world.name if sc.world else None
d['counts'] = {k: len(getattr(bpy.data, k)) for k in ('objects', 'cameras', 'meshes', 'materials', 'node_groups', 'images',
                                                      'collections', 'lights', 'worlds', 'curves', 'textures', 'actions')}
h = hashlib.sha1()
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type == 'CAMERA':
        continue
    h.update(ob.name.encode())
    h.update(repr([round(v, 6) for row in ob.matrix_world for v in row]).encode())
    h.update(repr((ob.hide_render, ob.hide_viewport, len(ob.modifiers))).encode())
d['non_camera_objects_hash'] = h.hexdigest()
d['n_scene_objects'] = len(sc.objects)
json.dump(d, open(out, 'w'), indent=1)
print('DUMP_DONE', out)
