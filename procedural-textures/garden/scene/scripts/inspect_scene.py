# What this does: opens a saved courtyard scene (read-only, nothing is saved) and writes a JSON + a short text report of:
#   objects (type, collection, evaluated vertex/face counts, modifiers, materials, size, shadow/render flags), materials (add-on vs script,
#   node counts, image textures), lights, world nodes, camera, render settings.
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup FILE.blend -P inspect_scene.py -- OUT.json
import bpy, sys, json, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
R = {'blender': bpy.app.version_string, 'file': bpy.data.filepath}

objs = []
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    d = {'name': ob.name, 'type': ob.type, 'collections': [c.name for c in ob.users_collection],
         'loc': [round(v, 3) for v in ob.location], 'rot_deg': [round(math.degrees(v), 1) for v in ob.rotation_euler],
         'scale': [round(v, 3) for v in ob.scale], 'parent': ob.parent.name if ob.parent else None,
         'hide_render': ob.hide_render, 'hide_viewport': ob.hide_viewport,
         'visible_shadow': getattr(ob, 'visible_shadow', True), 'dims': [round(v, 3) for v in ob.dimensions],
         'modifiers': [(m.name, m.type) for m in ob.modifiers]}
    if ob.type in ('MESH', 'CURVE'):
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
            d['verts'] = len(me.vertices); d['faces'] = len(me.polygons)
            d['uv_layers'] = [u.name for u in me.uv_layers]
            d['color_attrs'] = [c.name for c in me.color_attributes]
            d['smooth_faces'] = sum(1 for p in me.polygons if p.use_smooth)
            d['mats_eval'] = [m.name if m else None for m in me.materials]
            ev.to_mesh_clear()
        except Exception as e:
            d['mesh_err'] = str(e)
        d['mats'] = [s.material.name if s.material else None for s in ob.material_slots]
    if ob.type == 'CURVE':
        d['bevel_depth'] = ob.data.bevel_depth
    objs.append(d)
R['objects'] = objs

mats = []
for m in sorted(bpy.data.materials, key=lambda m: m.name):
    d = {'name': m.name, 'users': m.users, 'use_nodes': m.use_nodes}
    if m.node_tree:
        types = {}
        for n in m.node_tree.nodes: types[n.bl_idname.replace('ShaderNode', '')] = types.get(n.bl_idname.replace('ShaderNode', ''), 0) + 1
        d['nodes'] = len(m.node_tree.nodes); d['node_types'] = types
        d['images'] = [n.image.name for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image]
        b = m.node_tree.nodes.get('Principled BSDF')
        if b:
            bc = b.inputs['Base Color']
            d['base'] = [round(v, 3) for v in bc.default_value[:3]] if not bc.is_linked else 'linked'
            d['rough'] = round(b.inputs['Roughness'].default_value, 3) if not b.inputs['Roughness'].is_linked else 'linked'
            es = b.inputs['Emission Strength'].default_value
            d['emission'] = round(es, 3)
        d['has_displacement'] = any(n.bl_idname == 'ShaderNodeDisplacement' for n in m.node_tree.nodes)
    mats.append(d)
R['materials'] = mats
R['images'] = [(i.name, list(i.size)) for i in bpy.data.images]
R['node_groups'] = [(g.name, g.bl_idname, g.users) for g in bpy.data.node_groups]

lights = []
for ob in bpy.data.objects:
    if ob.type == 'LIGHT':
        L = ob.data
        d = {'name': ob.name, 'type': L.type, 'energy': L.energy, 'color': [round(v, 3) for v in L.color], 'loc': [round(v, 2) for v in ob.location],
             'hide_render': ob.hide_render}
        # direction light travels (-Z of object)
        dirv = ob.matrix_world.to_3x3() @ Vector((0, 0, -1)); d['travel_dir'] = [round(v, 3) for v in dirv.normalized()]
        if L.type == 'SUN':
            d['angle_deg'] = round(math.degrees(L.angle), 2)
            d['elevation_deg'] = round(math.degrees(math.asin(-dirv.normalized().z)), 2)
            d['travel_azimuth_deg'] = round(math.degrees(math.atan2(dirv.y, dirv.x)), 1)
        if L.type == 'AREA':
            d['shape'] = L.shape; d['size'] = [L.size, L.size_y]
        if L.type == 'POINT': d['radius'] = L.shadow_soft_size
        lights.append(d)
R['lights'] = lights

w = sc.world; wd = {'name': w.name if w else None}
if w and w.node_tree:
    wd['nodes'] = []
    for n in w.node_tree.nodes:
        e = {'type': n.bl_idname.replace('ShaderNode', ''), 'name': n.name}
        if n.bl_idname == 'ShaderNodeTexSky':
            e.update(sky_type=n.sky_type, sun_disc=n.sun_disc, sun_elevation_deg=round(math.degrees(n.sun_elevation), 2), sun_rotation_deg=round(math.degrees(n.sun_rotation), 1),
                     altitude=n.altitude, air=n.air_density, aerosol=n.aerosol_density, ozone=n.ozone_density)
        if n.bl_idname == 'ShaderNodeBackground':
            e['strength'] = n.inputs['Strength'].default_value
        wd['nodes'].append(e)
R['world'] = wd

cam = sc.camera
cd = cam.data
R['camera'] = {'name': cam.name, 'loc': [round(v, 3) for v in cam.location], 'rot_deg': [round(math.degrees(v), 2) for v in cam.rotation_euler], 'lens': cd.lens,
               'sensor': cd.sensor_width, 'fov_deg': round(math.degrees(cd.angle), 1), 'dof': cd.dof.use_dof, 'fstop': cd.dof.aperture_fstop,
               'focus_obj': cd.dof.focus_object.name if cd.dof.focus_object else None, 'clip': [cd.clip_start, cd.clip_end],
               'focus_loc': [round(v, 2) for v in cd.dof.focus_object.location] if cd.dof.focus_object else None}
r = sc.render; c = sc.cycles
R['render'] = {'engine': r.engine, 'res': [r.resolution_x, r.resolution_y, r.resolution_percentage], 'samples': c.samples, 'adaptive': c.use_adaptive_sampling,
               'adaptive_threshold': c.adaptive_threshold, 'denoise': c.use_denoising, 'denoiser': c.denoiser, 'device': c.device,
               'bounces': [c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.volume_bounces],
               'clamp_indirect': c.sample_clamp_indirect, 'clamp_direct': c.sample_clamp_direct, 'caustics': [c.caustics_reflective, c.caustics_refractive],
               'view_transform': sc.view_settings.view_transform, 'look': sc.view_settings.look, 'exposure': sc.view_settings.exposure, 'gamma': sc.view_settings.gamma,
               'file_format': r.image_settings.file_format, 'color_depth': r.image_settings.color_depth,
               'film_transparent': r.film_transparent, 'motion_blur': r.use_motion_blur, 'fps': r.fps, 'frame_range': [sc.frame_start, sc.frame_end]}
R['counts'] = {'objects': len(bpy.data.objects), 'meshes': len(bpy.data.meshes), 'materials': len(bpy.data.materials), 'collections': [(col.name, len(col.objects)) for col in bpy.data.collections]}
json.dump(R, open(out, 'w'), indent=1, default=str)
print('INSPECT_DONE', out, 'objects', len(objs))
