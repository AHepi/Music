# Checker script: independent fingerprint of everything in a .blend (objects, materials, lights, cameras, world, render settings).
# Run: blender -b --disable-autoexec FILE.blend --python fingerprint.py -- OUT.json
import bpy, sys, json, hashlib

out_path = sys.argv[sys.argv.index('--') + 1]


def h(s):
    return hashlib.sha1(str(s).encode()).hexdigest()[:12]


def r(x, n=4):
    try:
        return round(float(x), n)
    except Exception:
        return str(x)


def val(v):
    try:
        if hasattr(v, '__len__') and not isinstance(v, str):
            return [r(a) if isinstance(a, float) else (a if isinstance(a, (int, bool)) else str(a)) for a in v]
    except Exception:
        pass
    if isinstance(v, float):
        return r(v)
    if isinstance(v, (int, bool, str)):
        return v
    return getattr(v, 'name', str(type(v)))


def tree_sig(nt, depth=0):
    if nt is None:
        return None
    nodes = []
    for n in nt.nodes:
        ins = []
        for s in n.inputs:
            if hasattr(s, 'default_value') and not s.is_linked:
                try:
                    ins.append((s.identifier, val(s.default_value)))
                except Exception:
                    pass
        extra = []
        for a in ('operation', 'blend_type', 'data_type', 'noise_type', 'interpolation', 'projection', 'distribution', 'subsurface_method'):
            if hasattr(n, a):
                extra.append((a, str(getattr(n, a))))
        if hasattr(n, 'node_tree') and n.node_tree is not None:
            extra.append(('group', n.node_tree.name))
        if getattr(n, 'image', None) is not None:
            extra.append(('image', n.image.name))
        nodes.append((n.name, n.bl_idname, tuple(ins), tuple(extra), tuple(r(c) for c in n.location)))
    links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in nt.links)
    return h((sorted(nodes), links))


def mod_sig(m):
    d = [m.name, m.type]
    if m.type == 'NODES':
        d.append(m.node_group.name if m.node_group else None)
        if m.node_group:
            for it in m.node_group.interface.items_tree:
                if getattr(it, 'item_type', '') == 'SOCKET' and it.in_out == 'INPUT':
                    try:
                        v = m[it.identifier]
                        d.append((it.identifier, val(v) if not hasattr(v, 'name') else v.name))
                    except Exception:
                        pass
    else:
        for p in m.bl_rna.properties:
            if p.identifier in ('rna_type', 'name', 'type'):
                continue
            try:
                d.append((p.identifier, val(getattr(m, p.identifier))))
            except Exception:
                pass
    return h(d)


R = {'objects': {}, 'materials': {}, 'node_groups': {}, 'lights': {}, 'cameras': {}, 'world': {}, 'render': {}, 'counts': {}}
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    e = {'type': o.type, 'parent': o.parent.name if o.parent else None,
         'loc': [r(a) for a in o.location], 'rot': [r(a) for a in o.rotation_euler], 'scl': [r(a) for a in o.scale],
         'hide_render': o.hide_render, 'hide_viewport': o.hide_viewport,
         'collections': sorted(c.name for c in o.users_collection),
         'slots': [s.material.name if s.material else None for s in o.material_slots],
         'mods': [mod_sig(m) for m in o.modifiers],
         'mod_names': [m.name for m in o.modifiers],
         'owner': o.get('garden_owner'), 'role': o.get('garden_role')}
    if o.type == 'MESH':
        me = o.data
        co = [tuple(round(c, 4) for c in v.co) for v in me.vertices]
        e['geom'] = h(co)
        e['nverts'] = len(co); e['npolys'] = len(me.polygons)
        e['smooth'] = h([p.use_smooth for p in me.polygons])
        e['mesh_name'] = me.name
    elif o.type == 'CURVE':
        cu = o.data
        pts = []
        for s in cu.splines:
            for p in s.points:
                pts.append(tuple(round(c, 4) for c in p.co))
            for p in s.bezier_points:
                pts.append(tuple(round(c, 4) for c in p.co))
        e['geom'] = h(pts); e['nverts'] = len(pts)
        e['bevel'] = [r(cu.bevel_depth), cu.bevel_resolution, r(cu.extrude)]
    elif o.type == 'LIGHT':
        l = o.data
        e['geom'] = None
    R['objects'][o.name] = e
for m in bpy.data.materials:
    R['materials'][m.name] = {'sig': tree_sig(m.node_tree), 'users': m.users,
                              'blend': getattr(m, 'blend_method', None), 'owner': m.get('garden_owner')}
for g in bpy.data.node_groups:
    R['node_groups'][g.name] = {'sig': tree_sig(g), 'type': g.bl_idname}
for l in bpy.data.lights:
    R['lights'][l.name] = {'type': l.type, 'energy': r(l.energy), 'color': [r(c) for c in l.color], 'size': r(getattr(l, 'size', getattr(l, 'shadow_soft_size', 0))),
                           'angle': r(getattr(l, 'angle', 0)), 'shape': getattr(l, 'shape', None),
                           'lg': getattr(l, 'lightgroup', None) if hasattr(l, 'lightgroup') else None}
for c in bpy.data.cameras:
    R['cameras'][c.name] = {'lens': r(c.lens), 'sensor': r(c.sensor_width), 'shift': [r(c.shift_x), r(c.shift_y)], 'clip': [r(c.clip_start), r(c.clip_end)],
                            'dof': c.dof.use_dof, 'fstop': r(c.dof.aperture_fstop), 'focus': c.dof.focus_object.name if c.dof.focus_object else None, 'dist': r(c.dof.focus_distance)}
for w in bpy.data.worlds:
    R['world'][w.name] = {'sig': tree_sig(w.node_tree), 'color': [r(x) for x in w.color]}
sc = bpy.context.scene
rs = sc.render
R['render'] = {'engine': rs.engine, 'res': [rs.resolution_x, rs.resolution_y, rs.resolution_percentage], 'film_transparent': rs.film_transparent,
               'view_transform': sc.view_settings.view_transform, 'look': sc.view_settings.look, 'exposure': r(sc.view_settings.exposure), 'gamma': r(sc.view_settings.gamma),
               'display_device': sc.display_settings.display_device, 'camera': sc.camera.name if sc.camera else None,
               'frame': [sc.frame_start, sc.frame_end, sc.frame_current],
               'cycles': {k: val(getattr(sc.cycles, k)) for k in ('samples', 'use_adaptive_sampling', 'adaptive_threshold', 'use_denoising', 'denoiser', 'max_bounces', 'diffuse_bounces',
                                                                  'glossy_bounces', 'transmission_bounces', 'transparent_max_bounces', 'caustics_reflective', 'caustics_refractive', 'device',
                                                                  'sample_clamp_direct', 'sample_clamp_indirect', 'film_exposure', 'use_light_tree') if hasattr(sc.cycles, k)},
               'eevee_taa': getattr(sc.eevee, 'taa_render_samples', None),
               'lightgroups': [lg.name for lg in bpy.context.view_layer.lightgroups],
               'compositor': bool(sc.compositing_node_group) if hasattr(sc, 'compositing_node_group') else bool(sc.use_nodes),
               'seed': sc.cycles.seed}
R['counts'] = {'objects': len(bpy.data.objects), 'materials': len(bpy.data.materials), 'node_groups': len(bpy.data.node_groups), 'images': len(bpy.data.images),
               'collections': len(bpy.data.collections), 'meshes': len(bpy.data.meshes)}
json.dump(R, open(out_path, 'w'))
print('FP_DONE', R['counts'])
