# Dump cameras, render settings and object layout of the open scene to JSON (read-only).
import bpy, json, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
d = {}
d['scene'] = sc.name
d['scenes'] = [s.name for s in bpy.data.scenes]
d['active_camera'] = sc.camera.name if sc.camera else None
r = sc.render
cy = sc.cycles
d['render'] = dict(engine=r.engine, res=(r.resolution_x, r.resolution_y, r.resolution_percentage),
    samples=cy.samples, adaptive=cy.use_adaptive_sampling, adaptive_threshold=cy.adaptive_threshold,
    adaptive_min=cy.adaptive_min_samples, denoise=cy.use_denoising, denoiser=str(cy.denoiser),
    denoise_passes=str(cy.denoising_input_passes), prefilter=str(cy.denoising_prefilter), device=cy.device,
    max_bounces=cy.max_bounces, diffuse_bounces=cy.diffuse_bounces, glossy_bounces=cy.glossy_bounces,
    transmission_bounces=cy.transmission_bounces, volume_bounces=cy.volume_bounces, transparent_max=cy.transparent_max_bounces,
    clamp_direct=cy.sample_clamp_direct, clamp_indirect=cy.sample_clamp_indirect, caustics=(cy.caustics_reflective, cy.caustics_refractive),
    blur_glossy=cy.blur_glossy, light_tree=getattr(cy, 'use_light_tree', None), film_transparent=r.film_transparent,
    filter_width=getattr(cy, 'filter_width', None), use_compositing=r.use_compositing, use_sequencer=r.use_sequencer,
    persistent=r.use_persistent_data, file_format=r.image_settings.file_format, quality=r.image_settings.quality,
    motion_blur=r.use_motion_blur, fps=r.fps, frame=sc.frame_current)
vs = sc.view_settings
d['colour'] = dict(display=sc.display_settings.display_device, view=vs.view_transform, look=vs.look,
    exposure=vs.exposure, gamma=vs.gamma, curves=vs.use_curve_mapping,
    sequencer=sc.sequencer_colorspace_settings.name)
try:
    d['colour']['working_space'] = bpy.data.colorspace.working_space
except Exception as e:
    d['colour']['working_space'] = str(e)
ng = getattr(sc, 'compositing_node_group', None)
d['compositor'] = None
if ng is not None:
    d['compositor'] = dict(name=ng.name, nodes=[(n.name, n.bl_idname) for n in ng.nodes])
    if 'haze_strength' in ng.nodes:
        d['compositor']['haze_strength'] = ng.nodes['haze_strength'].inputs[1].default_value
w = sc.world
d['world'] = dict(name=w.name if w else None, mist=(w.mist_settings.start, w.mist_settings.depth) if w else None)
cams = {}
for ob in bpy.data.objects:
    if ob.type == 'CAMERA':
        c = ob.data
        cams[ob.name] = dict(data=c.name, loc=list(ob.location), rot=list(ob.rotation_euler), rot_mode=ob.rotation_mode,
            scale=list(ob.scale), parent=ob.parent.name if ob.parent else None, lens=c.lens, sensor=c.sensor_width, sensor_h=c.sensor_height, fit=c.sensor_fit,
            clip=(c.clip_start, c.clip_end), shift=(c.shift_x, c.shift_y), type=c.type,
            dof=dict(use=c.dof.use_dof, dist=c.dof.focus_distance, f=c.dof.aperture_fstop, obj=c.dof.focus_object.name if c.dof.focus_object else None,
                     blades=c.dof.aperture_blades, rot=c.dof.aperture_rotation, ratio=c.dof.aperture_ratio),
            collections=[col.name for col in ob.users_collection], hide_render=ob.hide_render,
            anim=bool(ob.animation_data and ob.animation_data.action), data_anim=bool(c.animation_data and c.animation_data.action),
            markers=[m.name for m in sc.timeline_markers if m.camera == ob])
d['cameras'] = cams
def col_tree(col, depth=0):
    return dict(name=col.name, n_obj=len(col.objects), children=[col_tree(c, depth+1) for c in col.children])
d['collections'] = col_tree(sc.collection)
objs = []
for ob in sc.objects:
    if ob.type in ('MESH', 'EMPTY', 'CURVE', 'LIGHT') and not ob.hide_render:
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box] if ob.type == 'MESH' else [ob.matrix_world.translation]
        mn = [min(v[i] for v in bb) for i in range(3)]
        mx = [max(v[i] for v in bb) for i in range(3)]
        objs.append(dict(n=ob.name, t=ob.type, c=[round((mn[i]+mx[i])/2, 2) for i in range(3)], s=[round(mx[i]-mn[i], 2) for i in range(3)],
            col=ob.users_collection[0].name if ob.users_collection else '', mods=[m.type for m in ob.modifiers][:4],
            inst=ob.instance_type if ob.type == 'EMPTY' else ''))
d['objects'] = objs
d['n_objects_scene'] = len(sc.objects)
json.dump(d, open(out, 'w'), indent=1)
print('INSPECT_DONE', len(objs))
