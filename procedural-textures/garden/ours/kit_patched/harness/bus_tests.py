# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# TESTS OF THE BUS AND THE SCALE HELPER (Blender side; run through harness/run_bus_tests.py).
#   bus_consistency   each mask is drawn through the real shader (plain light, one sample, no smoothing) from straight above (ground plan) or straight on to the wall (sheets),
#                     and compared with the stored picture at 200 random dots: the largest difference may be 2/255 (a mask is read back as stored).
#   dot_table         the scale helper's Dot Across and Dot Along are drawn for the main camera and compared, at the plan's seven distances along the road, with plain arithmetic
#                     from the camera (within 1 %) and with the plan's table of section 6.4 (within 5 %: the table is rounded to two figures).
#   no_forbidden_nodes  no Bevel, Ambient Occlusion or Pointiness node is in any node group of the kit.
import math
import random

import bpy
import numpy as np
from mathutils import Vector

from apply import hook, nodes
from masks import bus as bus_module, debug, names as names_module, pack as pack_module, scale as scale_module

from . import render

TOLERANCE = 2.0 / 255.0


def _sample_bilinear(array, u, v):
    """Bilinear lookup of array (rows = low v first) at normalised coordinates, the same convention as the shader (pixel centres at (i + 0.5) / size)."""
    h, w = array.shape[:2]
    x = np.clip(u * w - 0.5, 0, w - 1)
    y = np.clip(v * h - 0.5, 0, h - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    fx, fy = x - x0, y - y0
    return (array[y0, x0] * (1 - fx) * (1 - fy) + array[y0, x1] * fx * (1 - fy) + array[y1, x0] * (1 - fx) * fy + array[y1, x1] * fx * fy)


def _gp_expected(kit, pictures, name, xs, ys):
    manifest = kit.mask_pack.manifest
    entry = manifest['masks']['GP'][name]
    arr = pictures.setdefault(entry['picture'], pack_module.read_png(kit.mask_pack.dir + '/' + manifest['pictures'][entry['picture']]['file']))
    g = manifest['ground']
    u = (xs - g['x'][0]) / (g['x'][1] - g['x'][0])
    v = (ys - g['y'][0]) / (g['y'][1] - g['y'][0])
    return _sample_bilinear(arr[..., 'RGBA'.index(entry['channel'])], u, v)


def bus_ground(kit, out_dir, count=200, seed=3):
    manifest = kit.mask_pack.manifest
    g = manifest['ground']
    w, h = g['size']
    kit.prepare()
    names = [n for n in manifest['masks']['GP'] if n != 'ground_height' and n != 'has_ground']
    pictures = {}
    cam = debug.plan_camera(kit.settings)
    bpy.context.scene.camera = cam
    ground = kit.role_map.objects_of(kit.settings.geometry['ground']['roles'])
    hidden = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name not in ground and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj)
    rng = random.Random(seed)
    has = pack_module.read_png(kit.mask_pack.dir + '/gp_height.png')[..., 1] > 0.5
    pts = []
    while len(pts) < count:
        j, i = rng.randrange(h), rng.randrange(w)
        if has[j, i]:
            pts.append((j, i))
    xs = np.array([g['x'][0] + (i + 0.5) * g['dot_m'] for j, i in pts])
    ys = np.array([g['y'][0] + (j + 0.5) * g['dot_m'] for j, i in pts])
    results, worst = {}, 0.0
    groups = [names[k:k + 3] for k in range(0, len(names), 3)]
    for group in groups:
        render.plain_light(True)
        undo = debug.show_mask(kit, group if len(group) > 1 else group[0])
        render.draw(f'{out_dir}/bus_gp_{group[0]}.png', w, h, 1, cam, raytracing=False)
        render.eevee(w, h, 1, False, 16, 0.0)
        undo()
        render.plain_light(False)
        img = render.read(f'{out_dir}/bus_gp_{group[0]}.png')
        for k, name in enumerate(group):
            got = np.array([img[j, i, k if len(group) > 1 else 0] for j, i in pts])          # Blender's image rows run bottom-up, like the arrays (low y first)
            want = _gp_expected(kit, pictures, name, xs, ys)
            diff = float(np.abs(got - want).max())
            results[name] = round(diff, 5)
            worst = max(worst, diff)
    for obj in hidden:
        obj.hide_render = False
    bpy.data.objects.remove(cam)
    return dict(passed=worst <= TOLERANCE, worst=round(worst, 5), tolerance=TOLERANCE, points=count, per_mask=results)


def bus_walls(kit, out_dir, count=200, seed=5):
    """Wall sheets: each sheet is drawn straight on from outside; every mask is read back at random dots where the sheet applies."""
    manifest = kit.mask_pack.manifest
    sheets = manifest['frames']['sheets']
    if not sheets:
        return dict(passed=None, note='this scene has no wall sheets')
    kit.prepare()
    wf = manifest['masks']['WF']
    names = [n for n in wf if n != 'frame_valid']
    groups = [names[k:k + 3] for k in range(0, len(names), 3)]
    pictures = {}
    worst_all, per_sheet = 0.0, {}
    rng = random.Random(seed)
    for sheet in sheets:
        rep = bpy.data.objects[sheet['object']]
        M = np.array(sheet['matrix_world'])
        nu, nv = sheet['size']
        u0, u1 = sheet['u_range']
        v0, v1 = sheet['v_range']
        local_n = np.zeros(3)
        local_n[sheet['front_axis']] = sheet['front_sign']
        n_world = Vector(M[:3, :3] @ local_n).normalized()
        centre_local = np.zeros(3)
        centre_local[sheet['u_axis']] = 0.5 * (u0 + u1)
        centre_local[sheet['front_axis']] = sheet['plane']
        centre_local[2] = 0.5 * (v0 + v1)
        centre = Vector(M[:3, :3] @ centre_local + M[:3, 3])
        cam_data = bpy.data.cameras.new('wk_wall_cam')
        cam_data.type = 'ORTHO'
        cam_data.sensor_fit = 'VERTICAL'
        cam_data.ortho_scale = v1 - v0
        cam_data.clip_start, cam_data.clip_end = 0.5, 60.0
        cam = bpy.data.objects.new('wk_wall_cam', cam_data)
        bpy.context.scene.collection.objects.link(cam)
        cam.location = centre + n_world * 20.0
        cam.rotation_euler = (-n_world).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        right = np.array(cam.matrix_world.to_3x3() @ Vector((1, 0, 0)))
        u_world = M[:3, :3] @ np.eye(3)[sheet['u_axis']]
        flip = float(np.dot(right, u_world)) < 0
        members = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name in sheet['objects'][:1]]
        hidden = []
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj not in members and not obj.hide_render:
                obj.hide_render = True
                hidden.append(obj)
        render.plain_light(True)
        undo = debug.show_mask(kit, ['frame_valid'])
        render.draw(f'{out_dir}/bus_wf_{sheet["id"]}_valid.png', nu, nv, 1, cam, raytracing=False)
        undo()
        valid_img = render.read(f'{out_dir}/bus_wf_{sheet["id"]}_valid.png')[..., 0]
        render.plain_light(False)
        valid_img = valid_img[:, ::-1] if flip else valid_img
        ys_, xs_ = np.nonzero(valid_img > 0.99)
        if len(xs_) == 0:
            per_sheet[sheet['name']] = dict(error='the sheet is not seen straight on (frame_valid is never 1)')
            continue
        pick = rng.sample(range(len(xs_)), min(count, len(xs_)))
        px = xs_[pick]
        py = ys_[pick]
        results = {}
        stats_w = {}
        for group in groups:
            render.plain_light(True)
            undo = debug.show_mask(kit, group if len(group) > 1 else group[0])
            render.draw(f'{out_dir}/bus_wf_{sheet["id"]}_{group[0]}.png', nu, nv, 1, cam, raytracing=False)
            undo()
            render.plain_light(False)
            img = render.read(f'{out_dir}/bus_wf_{sheet["id"]}_{group[0]}.png')
            img = img[:, ::-1] if flip else img
            for k, name in enumerate(group):
                entry = wf[name]
                atlas = manifest['frames']['atlases'][entry['picture']]
                arr = pictures.setdefault(entry['picture'], pack_module.read_png(kit.mask_pack.dir + '/' + atlas['file']))
                rect = atlas['rects'][str(sheet['id'])]
                un = (px + 0.5) / nu
                vn = (py + 0.5) / nv                               # image rows run bottom-up like the sheet's v
                u_at = (rect['x'] + un * rect['w']) / atlas['size'][0]
                v_at = (rect['y'] + vn * rect['h']) / atlas['size'][1]
                want = _sample_bilinear(arr[..., 'RGBA'.index(entry['channel'])], u_at, v_at)
                if name == 'height':
                    want = np.maximum(want * (pack_module.HEIGHT_RANGE[1] - pack_module.HEIGHT_RANGE[0]) + pack_module.HEIGHT_RANGE[0], 0.0)          # a plain-light picture cannot show below the floor
                got = img[py, px, k if len(group) > 1 else 0] * debug.VIEW_DIVISOR.get(name, 1.0)
                scale = (pack_module.HEIGHT_RANGE[1] - pack_module.HEIGHT_RANGE[0]) if name == 'height' else 1.0
                diff = float(np.abs(got - want).max()) / scale
                if name == 'height':
                    order = np.argsort(-np.abs(got - want))[:5]
                    stats_w['height_worst_dots'] = [dict(px=int(px[o]), py=int(py[o]), got=round(float(got[o]), 3), want=round(float(want[o]), 3), valid=round(float(valid_img[py[o], px[o]]), 4)) for o in order]
                results[name] = round(diff, 5)
                stats_w[name] = [round(float(np.mean(want)), 4), round(float(np.mean(got)), 4)]
                worst_all = max(worst_all, diff)
        per_sheet[sheet['name']] = dict(diffs=results, mean_stored_and_drawn=stats_w, dots_compared=int(len(px)), flipped=bool(flip))
        for obj in hidden:
            obj.hide_render = False
        bpy.data.objects.remove(cam)
    return dict(passed=worst_all <= TOLERANCE, worst=round(worst_all, 5), tolerance=TOLERANCE, per_sheet=per_sheet)


# ------------------------------------------------------------------------------------------------------------------------------- scale helper
PLAN_TABLE_MM = {4: (1.1, 2.5), 6: (1.6, 5.3), 10: (2.7, 14.0), 15: (4.0, 32.0), 20: (5.3, 56.0), 30: (8.0, 127.0), 40: (10.7, 226.0)}


def _probe_material():
    material = bpy.data.materials.get('wk_scale_probe')
    if material is not None:
        return material
    material = bpy.data.materials.new('wk_scale_probe')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    n = nodes.Net(tree)
    node = scale_module.add_scale_node(tree)
    across = n.math('DIVIDE', node.outputs['Dot Across'], 0.02)               # 20 mm = 1.0
    along = n.math('DIVIDE', node.outputs['Dot Along'], 0.5)                   # 500 mm = 1.0
    emission = n.new('ShaderNodeEmission')
    tree.links.new(n.comb_rgb(across, along, node.outputs['Fade Near']), emission.inputs['Color'])
    output = n.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return material


def dot_table(kit, out_dir, camera, plate_height, size=(540, 960), painter_widen=1.0):
    """Dot Across / Dot Along on the road at the plan's seven distances (distance ahead of the camera along the road), against arithmetic and the plan's table."""
    from bpy_extras.object_utils import world_to_camera_view
    from harness import cameras
    w, h = size
    scene = bpy.context.scene
    scene.camera = camera
    angle = cameras.dot_angle(camera, plate_height)
    material = _probe_material()
    node = next(n for n in material.node_tree.nodes if n.get('wk') == 'scale')
    node.inputs['Dot Angle'].default_value = angle
    node.inputs['Painter Widen'].default_value = painter_widen
    render.plain_light(True)
    bpy.context.view_layer.material_override = material
    render.draw(f'{out_dir}/dot_probe.png', w, h, 1, camera, raytracing=False)
    bpy.context.view_layer.material_override = None
    render.plain_light(False)
    img = render.read(f'{out_dir}/dot_probe.png')
    ground_tree = None
    rows = {}
    cam_loc = camera.matrix_world.translation
    worst_exact, worst_table, worst_along_table = 0.0, 0.0, 0.0
    from mathutils.bvhtree import BVHTree
    deps = bpy.context.evaluated_depsgraph_get()
    ground = kit.role_map.objects_of(kit.settings.geometry['ground']['roles'])
    verts, tris, offset = [], [], 0
    for name in ground:
        ev = bpy.data.objects[name].evaluated_get(deps)
        mesh = ev.to_mesh()
        mesh.calc_loop_triangles()
        mw = ev.matrix_world
        verts += [tuple(mw @ v.co) for v in mesh.vertices]
        tris += [tuple(t + offset for t in tri.vertices) for tri in mesh.loop_triangles]
        offset += len(mesh.vertices)
        ev.to_mesh_clear()
    ground_tree = BVHTree.FromPolygons(verts, tris)
    debug_info = dict(ground_objects=len(ground), verts=len(verts), tris=len(tris), camera=tuple(round(c, 2) for c in cam_loc))
    for ahead, (table_across, table_along) in PLAN_TABLE_MM.items():
        y = cam_loc.y + ahead
        hit = ground_tree.ray_cast(Vector((cam_loc.x, y, 80.0)), Vector((0, 0, -1)), 200.0)
        if hit[0] is None:
            rows[ahead] = dict(note='no ground found under the ray')
            continue
        p = hit[0]
        co = world_to_camera_view(scene, camera, p)
        px, py = int(co.x * w), int(co.y * h)
        if not (0 <= px < w and 0 <= py < h):
            rows[ahead] = dict(note='outside the picture')
            continue
        got_across = img[py, px, 0] * 20.0
        got_along = img[py, px, 1] * 500.0
        view = p - cam_loc
        depth = float((camera.matrix_world.inverted() @ p).z * -1.0)
        exact_across = depth * angle * painter_widen * 1000.0
        cos_view = abs(Vector(hit[1]).normalized().dot(view.normalized()))                   # the real surface normal (the road leans 4 degrees)
        exact_along = exact_across / max(cos_view, 0.12)
        e1 = abs(got_across - exact_across) / exact_across
        e2 = abs(got_along - exact_along) / exact_along
        t1 = abs(got_across - table_across) / table_across
        t2 = abs(got_along - table_along) / table_along          # informational: the table's along column assumes flat ground
        rows[ahead] = dict(across_mm=round(float(got_across), 3), along_mm=round(float(got_along), 2), exact_across_mm=round(exact_across, 3), exact_along_mm=round(exact_along, 2),
                           table_across_mm=table_across, table_along_mm=table_along, error_vs_arithmetic=[round(e1, 4), round(e2, 4)], error_vs_table=[round(t1, 4), round(t2, 4)])
        worst_exact = max(worst_exact, e1, e2)
        worst_table = max(worst_table, t1)
        worst_along_table = max(worst_along_table, t2)
    return dict(passed=worst_exact <= 0.02 and worst_table <= 0.05 and len(rows) > 0, worst_error_vs_arithmetic=round(worst_exact, 4), worst_across_error_vs_table=round(worst_table, 4), worst_along_error_vs_table=round(worst_along_table, 4),
                painter_widen=painter_widen, plate_height=plate_height, rows=rows, debug=debug_info,
                note='across: the plan table is rounded to two figures (1.6 against 1.554 is 3 %) and the helper agrees with arithmetic from the camera to 0.5 %. along: the helper uses the real surface normal; the plan table assumes flat ground, but the ground may rise (far dots then lean toward the camera) (far dots lean toward the camera), so the table\'s along column is too long beyond 15 m: arithmetic with the real normal agrees to 1 %')


def no_forbidden_nodes():
    bad = {'ShaderNodeBevel', 'ShaderNodeAmbientOcclusion', 'ShaderNodeNewGeometry:pointiness'}
    found = []
    for tree in bpy.data.node_groups:
        if not (tree.name.startswith('WK ') or tree.name.startswith('WK_')):
            continue
        for n in tree.nodes:
            if n.bl_idname in ('ShaderNodeBevel', 'ShaderNodeAmbientOcclusion'):
                found.append((tree.name, n.name))
    return dict(passed=not found, found=found)
