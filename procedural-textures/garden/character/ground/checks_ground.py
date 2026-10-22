"""GROUND builder: the checks (direction tests 17, 20, 22, 23 and the triangle counts) with numbers.
Run:  blender -b --disable-autoexec --python checks_ground.py -- START.blend OUT.json [save_dir]
It (1) opens the starting scene and records a snapshot of everything, (2) applies the stage, (3) applies it again (idempotence), (4) measures.
Test 21 (the test light) is test_normals.py; its numbers are merged into the report by hand."""
import bpy, sys, os, json, math, hashlib, time
import numpy as np
from mathutils import Vector
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/ground'
sys.path.insert(0, HERE)
import g6_common as C

argv = sys.argv[sys.argv.index('--') + 1:]
START = argv[0]
OUT = argv[1]
SAVE_DIR = argv[2] if len(argv) > 2 else None


def evaluated_tris(dg):
    """triangle count per top-level object name, counting instances (what the renderer draws)."""
    tot = {}
    cache = {}
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type != 'MESH':
            continue
        key = ob.data.name if inst.is_instance else ob.name
        if inst.is_instance:
            par = inst.parent.name if inst.parent else ob.name
            if key not in cache:
                me = ob.data
                me.calc_loop_triangles()
                cache[key] = len(me.loop_triangles)
            tot[par] = tot.get(par, 0) + cache[key]
        else:
            if ob.hide_render:
                continue
            eo = ob.evaluated_get(dg)
            me = eo.to_mesh()
            me.calc_loop_triangles()
            tot[ob.name] = tot.get(ob.name, 0) + len(me.loop_triangles)
            eo.to_mesh_clear()
    return tot


def instance_verts(dg, parent_name):
    n = 0
    cnt = 0
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.name == parent_name:
            n += len(inst.object.data.vertices)
            cnt += 1
    return n, cnt


def realize_count(name):
    """exact (vertices, triangles) of what an object draws, instances included: a temporary Realize Instances modifier."""
    ob = bpy.data.objects[name]
    ng = bpy.data.node_groups.new('TMP realize', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput'); r = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(gi.outputs[0], r.inputs[0]); ng.links.new(r.outputs[0], go.inputs[0])
    m = ob.modifiers.new('TMP realize', 'NODES'); m.node_group = ng
    dg = bpy.context.evaluated_depsgraph_get(); eo = ob.evaluated_get(dg); me = eo.to_mesh(); me.calc_loop_triangles()
    res = (len(me.vertices), len(me.loop_triangles)); eo.to_mesh_clear()
    ob.modifiers.remove(m); bpy.data.node_groups.remove(ng)
    return res


def snapshot():
    snap = {'objects': {}, 'materials': {}, 'collections': {}, 'lightlink': {}}
    for ob in bpy.data.objects:
        d = {'type': ob.type, 'colls': sorted(c.name for c in ob.users_collection), 'hide_render': ob.hide_render,
             'loc': [round(v, 4) for v in ob.location], 'props': sorted(k for k in ob.keys())}
        if ob.type == 'MESH':
            me = ob.data
            n = len(me.vertices)
            co = np.zeros(n * 3, dtype=np.float32)
            me.vertices.foreach_get('co', co)
            d['verts'] = n
            d['poshash'] = hashlib.md5(np.round(co, 4).tobytes()).hexdigest()
            d['mods'] = [(m.type, m.name, (m.node_group.name if m.type == 'NODES' and m.node_group else None)) for m in ob.modifiers]
            d['mats'] = [s.material.name if s.material else None for s in ob.material_slots]
            d['uvs'] = [u.name for u in me.uv_layers]
        if ob.type == 'LIGHT':
            d['light_linking'] = (ob.light_linking.receiver_collection.name if ob.light_linking.receiver_collection else None,
                                  ob.light_linking.blocker_collection.name if ob.light_linking.blocker_collection else None)
        d['lightgroup'] = ob.lightgroup
        snap['objects'][ob.name] = d
    for m in bpy.data.materials:
        if m.node_tree:
            snap['materials'][m.name] = (len(m.node_tree.nodes), len(m.node_tree.links))
    for c in bpy.data.collections:
        snap['collections'][c.name] = sorted(o.name for o in c.objects)
    return snap


def owned_object(name, ob_props):
    return name in set(C.object_names_owned()) or name.startswith(C.PFX) or ob_props.get('g6_made')


def main():
    res = {}
    bpy.ops.wm.open_mainfile(filepath=START)
    import stage_ground
    dg = bpy.context.evaluated_depsgraph_get()
    before = snapshot()
    tris_before = evaluated_tris(dg)
    tc_before = instance_verts(dg, 'Life / tufts')[1]
    tv_before, tt_before = realize_count('Life / tufts')
    res['tuft_today'] = {'instances': tc_before, 'vertices': tv_before, 'triangles': tt_before}
    res['triangles_before'] = {k: tris_before.get(k) for k in ['Life / tufts', 'Life / moss at feet and damp edges', 'Life / pebble fringe', 'Astra / moss grouped bodies',
                                                               'Astra / pebbles grouped bodies', 'Fallen leaves', 'Gravel kerb', 'Raked gravel court']}
    res['triangles_before_total'] = int(sum(v for v in tris_before.values() if v))
    inv_before = C.inventory()
    t0 = time.time()
    rep1 = stage_ground.apply({'cameras': True, 'verbose': False})
    res['apply_seconds'] = round(time.time() - t0, 1)
    after1 = snapshot()
    if SAVE_DIR:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SAVE_DIR, 'test_a.blend'), copy=True)
    dg = bpy.context.evaluated_depsgraph_get()
    tris_after = evaluated_tris(dg)
    rep2 = stage_ground.apply({'cameras': True, 'verbose': False})
    after2 = snapshot()
    if SAVE_DIR:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SAVE_DIR, 'test_b.blend'), copy=True)
        sa, sb = os.path.getsize(os.path.join(SAVE_DIR, 'test_a.blend')), os.path.getsize(os.path.join(SAVE_DIR, 'test_b.blend'))
        res['saved_file_sizes'] = {'first_apply': sa, 'second_apply': sb, 'difference_percent': round(abs(sa - sb) / sa * 100, 3)}
    dg = bpy.context.evaluated_depsgraph_get()
    tris_after2 = evaluated_tris(dg)
    res['triangles_after'] = {k: tris_after.get(k) for k in res['triangles_before']}
    res['triangles_after_total'] = int(sum(v for v in tris_after.values() if v))
    res['triangles_added'] = res['triangles_after_total'] - res['triangles_before_total']
    res['triangles_after_second_run_total'] = int(sum(v for v in tris_after2.values() if v))
    res['apply_report_first'] = rep1

    # ------------------------------------------------ test 23: ownership and idempotence
    changed_foreign = []
    for name, d in before['objects'].items():
        a = after1['objects'].get(name)
        if a is None:
            changed_foreign.append((name, 'DELETED'))
            continue
        if name in set(C.object_names_owned()):
            continue
        for k in ('verts', 'poshash', 'mods', 'mats', 'colls', 'hide_render', 'loc', 'light_linking', 'lightgroup'):
            if d.get(k) != a.get(k):
                changed_foreign.append((name, k))
    foreign_mats = []
    owned_mats = set(C.OWNED_MATERIAL_NAMES)
    for name, v in before['materials'].items():
        if name in owned_mats:
            continue
        if after1['materials'].get(name) != v:
            foreign_mats.append(name)
    new_objs = sorted(set(after1['objects']) - set(before['objects']))
    bad_tags = [n for n in new_objs if not (bpy.data.objects[n].get('garden_owner') == 'ground' and bpy.data.objects[n].get('garden_role'))]
    not_in_coll = [n for n in new_objs if bpy.data.objects[n].users_collection[0].name != 'G6 ground']
    res['test23'] = {
        'owned_object_names_before_that_changed': sorted(n for n in C.object_names_owned() if n in before['objects'] and before['objects'][n] != after1['objects'].get(n))[:60],
        'foreign_objects_changed': changed_foreign, 'foreign_materials_changed': foreign_mats,
        'objects_renamed_or_deleted': [n for n in before['objects'] if n not in after1['objects']],
        'new_objects': len(new_objs), 'new_objects_without_owner_or_role': bad_tags, 'new_objects_not_in_G6_ground': not_in_coll,
        'second_run_object_count_equal': len(after2['objects']) == len(after1['objects']),
        'second_run_objects_identical': {n: after2['objects'][n] == after1['objects'][n] for n in after1['objects'] if after2['objects'].get(n) != after1['objects'][n]},
        'second_run_material_counts_equal': after2['materials'] == after1['materials'],
        'objects_first': len(after1['objects']), 'objects_second': len(after2['objects']),
        'total_triangles_first': res['triangles_after_total'], 'total_triangles_second': res['triangles_after_second_run_total']}
    # names before / after (proof the stage touches only what it owns)
    inv_after = C.inventory()
    res['names'] = {'objects_added': sorted(set(inv_after['objects']) - set(inv_before['objects'])), 'objects_removed': sorted(set(inv_before['objects']) - set(inv_after['objects'])),
                    'materials_added': sorted(set(inv_after['materials']) - set(inv_before['materials'])),
                    'materials_removed': sorted(set(inv_before['materials']) - set(inv_after['materials'])),
                    'node_groups_added': sorted(set(inv_after['node_groups']) - set(inv_before['node_groups']))}

    # ------------------------------------------------ test 17: tufts
    dg = bpy.context.evaluated_depsgraph_get()
    tv, tt_now = realize_count('Life / tufts')
    tuft_objs = [o for o in bpy.data.objects if o.get('g6_tuft_key')]
    shape_hash = set()
    for o in tuft_objs:
        co = np.zeros(len(o.data.vertices) * 3, dtype=np.float32)
        o.data.vertices.foreach_get('co', co)
        shape_hash.add(hashlib.md5(np.round(co, 3).tobytes()).hexdigest())
    # per-instance sources and scales from the point cloud
    tp = bpy.data.objects['Life / tufts'].data
    n = len(tp.vertices)
    pk = np.zeros(n, dtype=np.int32)
    tp.attributes['g6_pick'].data.foreach_get('value', pk)
    sc = np.zeros(n, dtype=np.float32)
    tp.attributes['g6_scale'].data.foreach_get('value', sc)
    srcs = sorted(tuft_objs, key=lambda o: o.name)
    seed_share = float(np.mean([srcs[p]['g6_tuft_key'].startswith('seed_') for p in pk]))
    tints = sorted(set(o['g6_tuft_tint'] for o in tuft_objs))
    heights = np.array([srcs[p]['g6_height_m'] for p in pk]) * sc
    kerb_t = bpy.data.objects.get('G6 ground / kerb tufts')
    flowers = bpy.data.objects.get('G6 ground / flowers')
    twigs = bpy.data.objects.get('G6 ground / twigs')
    res['test17'] = {
        'tuft_meshes_different': len(shape_hash), 'tuft_recipes_by_key': len(set(o['g6_tuft_key'] for o in tuft_objs)), 'tuft_sources': len(tuft_objs),
        'scale_min': float(sc.min()), 'scale_max': float(sc.max()), 'scale_ratio': float(sc.max() / sc.min()),
        'tints': tints, 'seed_head_share': round(seed_share, 3), 'tufts_placed': int(n),
        'tuft_vertices_today': tv_before, 'tuft_vertices_now': tv, 'ratio_vertices': round(tv / tv_before, 2),
        'tuft_triangles_today': res['tuft_today']['triangles'], 'tuft_triangles_now': tt_now,
        'ratio_triangles': round(tt_now / res['tuft_today']['triangles'], 2),
        'height_p5_p95_m': [round(float(np.percentile(heights, 5)), 3), round(float(np.percentile(heights, 95)), 3)],
        'kerb_tufts': len(kerb_t.data.vertices) if kerb_t else 0, 'flowers': flowers['g6_flower_count'] if flowers else 0, 'twigs': twigs['g6_twig_count'] if twigs else 0,
        'soil_lip_object': 'G6 ground / kerb soil lip' in bpy.data.objects, 'moss_collars': rep2.get('moss_collars'), 'leaves': rep2.get('leaves')}
    # blade width at the base of every tuft source (smallest ring-0 width of a blade)
    minw = 1e9
    for o in tuft_objs:
        if o['g6_tuft_key'] in ('clover',):
            continue
        co = np.zeros(len(o.data.vertices) * 3, dtype=np.float32)
        o.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        # verts come in blade order: ring 0 pairs are the lowest pair of each blade -> take the pair spacing of all vertices with z < 0.0
        low = co[co[:, 2] < 0.001]
        if len(low) >= 2:
            for i in range(0, len(low) - 1, 2):
                minw = min(minw, float(np.linalg.norm(low[i] - low[i + 1])))
    res['test17']['min_blade_base_width_mm'] = round(minw * 1000, 1) if minw < 1e8 else None

    # flower coverage in the picture (share of pixels)
    def view_share(cam_name, pts_r):
        cam = bpy.data.objects[cam_name]
        sc_ = bpy.context.scene
        from bpy_extras.object_utils import world_to_camera_view
        w, h = 2400, 1600
        f_px = cam.data.lens / cam.data.sensor_width * w
        area = 0.0
        for p, r in pts_r:
            c = world_to_camera_view(sc_, cam, Vector(p))
            if 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0:
                rp = f_px * r / c.z
                area += math.pi * rp * rp
        return area / (w * h)
    if flowers:
        me = flowers.data
        # flower heads: the 16-vertex discs are the faces with 15 triangles; use every vertex group of the head: approximate by lowest radius 1 cm per flower
        # (count) x pi (0.01)^2
        centres = []
        co = np.zeros(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        # each flower = stem (7 verts) + head (16) + eye (7) = 30 vertices
        per = 30
        for i in range(0, len(co) - per + 1, per):
            centres.append((tuple(co[i + 7]), 0.0095))
        res['test17']['flower_screen_share_percent'] = {c: round(100 * view_share(c, centres), 4) for c in ('photo', 'veranda')}
    # worn path coverage in the pictures (rays from the cameras onto the ground)
    from g6_world import World
    world = World(os.path.join(HERE, 'maps'), verbose=False)

    def path_cover(cam_name, u0, u1, v0, v1):
        cam = bpy.data.objects[cam_name]
        w, h = 2400, 1600
        hit = tot = 0
        for u in np.linspace(u0, u1, 28):
            for v in np.linspace(v0, v1, 20):
                px = (u - 0.5) * cam.data.sensor_width
                py = -(v - 0.5) * cam.data.sensor_width * h / w
                d = cam.matrix_world.to_3x3() @ Vector((px, py, -cam.data.lens)).normalized()
                r = world.gbvh.ray_cast(cam.matrix_world.translation, d)
                if r[0] is None:
                    continue
                tot += 1
                if world.mask_at(r[0].x, r[0].y) > 0.5:
                    hit += 1
        return round(hit / max(tot, 1), 3)
    res['test17']['bare_path_share_hero_lower_right'] = path_cover('photo', 0.55, 1.0, 0.72, 1.0)
    res['test17']['bare_path_share_veranda_foreground'] = path_cover('veranda', 0.0, 0.5, 0.72, 1.0)
    # leaves within 1 cm of the surface
    lv = bpy.data.objects['Fallen leaves']
    me = lv.data
    nv = len(me.vertices)
    co = np.zeros(nv * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    per = 13        # centre + 14 outline (7 lobes) ... the leaf has 1 + 14 + 1 vertices
    per = 16
    dmax = 0.0
    n_leaf = nv // per
    off_ground = 0
    for i in range(n_leaf):
        c = co[i * per]
        z, _ = world.surface(float(c[0]), float(c[1]))
        if z is None:
            off_ground += 1
            continue
        dmax = max(dmax, abs(float(c[2]) - z))
        if not world.free(float(c[0]), float(c[1]), 0.0, zmin=-0.01, gravel_ok=True):
            off_ground += 1
    res['test17']['leaves'] = {'count': n_leaf, 'max_centre_distance_to_surface_m': round(dmax, 4), 'not_on_free_ground_above_water': off_ground,
                               'max_vertex_rise_m': round(float(max(co[i * per + j][2] - world.surface(float(co[i * per][0]), float(co[i * per][1]))[0] for i in range(n_leaf) for j in range(per))), 4)}

    # ------------------------------------------------ test 20: normal maps wired right, 22: UV hygiene
    changed_mats = ['Moss and earth', 'Astra / moss tone 0', 'Astra / moss tone 1', 'Astra / moss tone 2', 'Astra / moss tone 3', 'Astra / pebbles tone 0',
                    'Astra / pebbles tone 1', 'Astra / pebbles tone 2', 'Astra / pebbles tone 3', 'G6 ground / stone.rock'] + \
        ['CT / Stone painterly surface'] + ['CT / Stone painterly surface.%03d' % i for i in list(range(1, 8)) + [30, 31, 32]]
    users = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for s in ob.material_slots:
            if s.material:
                users.setdefault(s.material.name, []).append(ob)
    # sources instanced by the scatter groups carry the materials too
    t20 = {}
    for mn in changed_mats:
        m = bpy.data.materials[mn]
        nt = m.node_tree
        nms = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeNormalMap']
        r = {'normal_map_nodes': len(nms), 'ok': False}
        for nm in nms:
            lk = [l for l in nt.links if l.to_node == nm and l.to_socket.name == 'Color']
            img = None
            if lk and lk[0].from_node.bl_idname == 'ShaderNodeTexImage':
                img = lk[0].from_node.image
            # does the Normal reach the Principled?
            reach = False
            frontier = [nm]
            seen = set()
            while frontier:
                cur = frontier.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                if cur.bl_idname == 'ShaderNodeBsdfPrincipled':
                    reach = True
                for l in nt.links:
                    if l.from_node == cur and l.to_socket.name in ('Normal', 'Wet Normal') or (l.from_node == cur and l.to_node.bl_idname == 'ShaderNodeGroup'):
                        frontier.append(l.to_node)
            uvs_ok = all(nm.uv_map in [u.name for u in ob.data.uv_layers] for ob in users.get(mn, [])) if users.get(mn) else None
            if img is not None:
                px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4) if img.size[0] * img.size[1] < 5_000_000 else None
                stats = None if px is None else [round(float(px[:, i].mean()), 3) for i in range(3)]
                r.update({'image': img.name, 'size': list(img.size), 'colorspace': img.colorspace_settings.name, 'space': nm.space, 'uv_map': nm.uv_map,
                          'uv_layer_on_every_user': uvs_ok, 'users': len(users.get(mn, [])), 'reaches_principled': reach, 'mean_rgb': stats,
                          'strength': round(nm.inputs['Strength'].default_value, 2)})
                r['ok'] = bool(img.colorspace_settings.name == 'Non-Color' and nm.space == 'TANGENT' and min(img.size) >= 1024 and reach and (stats is None or (stats[2] >= 0.85 and abs(stats[0] - 0.5) <= 0.03 and abs(stats[1] - 0.5) <= 0.03)))
        bumps = [(n.name, round(n.inputs['Strength'].default_value, 3), any(l.from_node.bl_idname == 'ShaderNodeNormalMap' and l.to_node == n and l.to_socket.name == 'Normal' for l in nt.links))
                 for n in nt.nodes if n.bl_idname == 'ShaderNodeBump']
        r['bumps'] = bumps
        r['bump_rule_ok'] = all(s <= 0.3 or fed for _, s, fed in bumps)
        t20[mn] = r
    res['test20'] = t20
    # UV hygiene: mirrored faces on objects whose UV layer 'UVMap' I wrote
    t22 = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.data.uv_layers.get('UVMap') or not (ob.name in set(C.object_names_owned()) or C.is_mine(ob)):
            continue
        me = ob.data
        uv = np.zeros(len(me.loops) * 2, dtype=np.float32)
        me.uv_layers['UVMap'].data.foreach_get('uv', uv)
        uv = uv.reshape(-1, 2)
        ls = np.zeros(len(me.polygons), dtype=np.int32)
        me.polygons.foreach_get('loop_start', ls)
        lt = np.zeros(len(me.polygons), dtype=np.int32)
        me.polygons.foreach_get('loop_total', lt)
        ok = lt >= 3
        a, b, c = uv[ls[ok]], uv[ls[ok] + 1], uv[ls[ok] + 2]
        cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
        t22[ob.name] = {'faces': int(ok.sum()), 'mirrored_faces': int((cr < -1e-9).sum()), 'uv_min': [round(float(uv[:, 0].min()), 2), round(float(uv[:, 1].min()), 2)],
                        'uv_max': [round(float(uv[:, 0].max()), 2), round(float(uv[:, 1].max()), 2)]}
    res['test22'] = t22
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print('CHECKS_DONE', OUT)


main()
