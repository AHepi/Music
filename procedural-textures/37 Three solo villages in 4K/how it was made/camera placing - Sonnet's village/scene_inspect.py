import bpy, json, math
from mathutils import Vector
sc = bpy.context.scene
r = sc.render
out = {}
out['scenes'] = [s.name for s in bpy.data.scenes]
out['engine'] = r.engine
out['res'] = (r.resolution_x, r.resolution_y, r.resolution_percentage)
try:
    cy = sc.cycles
    out['cycles'] = dict(samples=cy.samples, adaptive=cy.use_adaptive_sampling, thr=cy.adaptive_threshold, denoise=cy.use_denoising, denoiser=getattr(cy,'denoiser',None), device=cy.device, bounces=cy.max_bounces, preview=cy.preview_samples, time_limit=getattr(cy,'time_limit',None))
except Exception as e:
    out['cycles'] = str(e)
vs = sc.view_settings
out['color'] = dict(display=sc.display_settings.display_device, view=vs.view_transform, look=vs.look, exposure=vs.exposure, gamma=vs.gamma, seq=sc.sequencer_colorspace_settings.name, curves=vs.use_curve_mapping)
out['film'] = dict(transparent=r.film_transparent, filter=getattr(sc.cycles,'filter_width',None))
out['camera'] = sc.camera.name if sc.camera else None
cams = []
for o in bpy.data.objects:
    if o.type == 'CAMERA':
        d = o.data
        cams.append(dict(name=o.name, loc=[round(v,3) for v in o.location], rot=[round(math.degrees(v),2) for v in o.rotation_euler], rotmode=o.rotation_mode, lens=d.lens, sensor=d.sensor_width, fit=d.sensor_fit, dof=d.dof.use_dof, fstop=d.dof.aperture_fstop, focus_obj=d.dof.focus_object.name if d.dof.focus_object else None, focus_dist=d.dof.focus_distance, clip=(d.clip_start,d.clip_end), shift=(d.shift_x,d.shift_y), parent=o.parent.name if o.parent else None, colls=[c.name for c in o.users_collection], data=d.name, constraints=[c.type for c in o.constraints], anim=bool(o.animation_data and o.animation_data.action)))
out['cams'] = cams
out['markers'] = [(m.name, m.frame, m.camera.name if m.camera else None) for m in sc.timeline_markers]
def walk(c, depth=0, acc=None):
    acc.append(('  '*depth) + c.name + ' objs=%d' % len(c.objects))
    for ch in c.children:
        walk(ch, depth+1, acc)
    return acc
out['colls'] = walk(sc.collection, 0, [])
objs = {}
for name in ('Buildings','Props','Fences','Terrain'):
    c = bpy.data.collections.get(name)
    if c:
        lst = []
        for o in c.objects:
            bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
            mn = [round(min(v[i] for v in bb),2) for i in range(3)]; mx = [round(max(v[i] for v in bb),2) for i in range(3)]
            lst.append((o.name, o.type, [round(v,2) for v in o.location], round(math.degrees(o.rotation_euler.z),1), mn, mx))
        objs[name] = lst
out['objs'] = objs
out['nobj'] = len(bpy.data.objects)
out['lights'] = [(o.name, o.data.type, round(o.data.energy,2)) for o in bpy.data.objects if o.type=='LIGHT']
out['world'] = sc.world.name if sc.world else None
out['frame'] = (sc.frame_start, sc.frame_end, sc.frame_current)
out['filepath_out'] = r.filepath
out['image_settings'] = (r.image_settings.file_format, r.image_settings.color_depth)
print('JSON>>' + json.dumps(out))
