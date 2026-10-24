# Check renders of candidate camera views. Never saves the .blend.
# Run: blender -b SCENE.blend --python check_views.py -- SPEC.json OUT_DIR PREFIX ENGINE(wb|cy) RES_X RES_Y [SAMPLES]
# SPEC: list of dicts:
#   name, eye [x,y], eye_h (metres above ground) or eye_z (absolute), tgt [x,y], tgt_h or tgt_z, lens,
#   optional dof [focus_dist, fstop] or dof "tgt" (focus at the target point) + fstop, ortho_scale, exposure, haze
#   or 'matrix' (4x4 list) + lens + dof to place exactly; or 'existing': name of a camera already in the scene.
import bpy, json, os, sys, math, time
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
spec_path, out_dir, prefix, engine, rx, ry = a[0], a[1], a[2], a[3], int(a[4]), int(a[5])
samples = int(a[6]) if len(a) > 6 else 16
os.makedirs(out_dir, exist_ok=True)
spec = json.load(open(spec_path))
sc = bpy.context.scene

_trees = []
def ground_trees():
    if _trees:
        return _trees
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith(("terrain", "road_", "yard_")):
            continue
        me = ob.data
        nv = len(me.vertices)
        co = np.zeros(nv * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        nl = len(me.loops)
        lv = np.zeros(nl, dtype=np.int64)
        me.loops.foreach_get("vertex_index", lv)
        tot = np.zeros(len(me.polygons), dtype=np.int64)
        me.polygons.foreach_get("loop_total", tot)
        st = np.zeros(len(me.polygons), dtype=np.int64)
        me.polygons.foreach_get("loop_start", st)
        polys = [lv[s:s + n].tolist() for s, n in zip(st, tot)]
        _trees.append((ob.name, BVHTree.FromPolygons(co.tolist(), polys)))
    return _trees

def ground_z(x, y):
    best, bn = None, None
    for nm, t in ground_trees():
        hit = t.ray_cast(Vector((x, y, 500.0)), Vector((0, 0, -1)))
        if hit[0] is not None and (best is None or hit[0].z > best):
            best, bn = hit[0].z, nm
    return best, bn

col = bpy.data.collections.get("Cameras") or sc.collection
report = []
made = []
for s in spec:
    if 'existing' in s:
        cam = bpy.data.objects[s['existing']]
        made.append((s.get('name', cam.name), cam, s))
        report.append(dict(name=s.get('name', cam.name), existing=cam.name))
        continue
    cd = bpy.data.cameras.new("chk_" + s['name'])
    cam = bpy.data.objects.new("chk_" + s['name'], cd)
    col.objects.link(cam)
    cd.sensor_width = 36.0
    cd.clip_start = 0.05
    cd.clip_end = 1500.0
    cd.lens = s.get('lens', 26.0)
    cam.rotation_mode = 'QUATERNION'
    if 'matrix' in s:
        cam.matrix_world = Matrix(s['matrix'])
        eye = cam.matrix_world.translation.copy()
        gz, gn = ground_z(eye.x, eye.y)
        tgt = None
    else:
        ex, ey = s['eye']
        gz, gn = ground_z(ex, ey)
        ez = s['eye_z'] if 'eye_z' in s else gz + s['eye_h']
        tx, ty = s['tgt']
        tgz, _ = ground_z(tx, ty)
        tz = s['tgt_z'] if 'tgt_z' in s else tgz + s.get('tgt_h', 1.5)
        eye = Vector((ex, ey, ez))
        tgt = Vector((tx, ty, tz))
        cam.location = eye
        cam.rotation_quaternion = (tgt - eye).to_track_quat('-Z', 'Y')
    if s.get('ortho_scale'):
        cd.type = 'ORTHO'
        cd.ortho_scale = s['ortho_scale']
    cd.shift_x = s.get('shift_x', 0.0)
    cd.shift_y = s.get('shift_y', 0.0)
    dof = s.get('dof')
    if dof:
        cd.dof.use_dof = True
        if dof == 'tgt':
            cd.dof.focus_distance = (tgt - eye).length
            cd.dof.aperture_fstop = s.get('fstop', 4.0)
        else:
            cd.dof.focus_distance, cd.dof.aperture_fstop = dof
    else:
        cd.dof.use_dof = False
    bpy.context.view_layer.update()
    # clearance: distance from the lens to the nearest surface in 26 directions (real meshes only)
    deps = bpy.context.evaluated_depsgraph_get()
    near = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                d = Vector((dx, dy, dz)).normalized()
                hit, loc, nrm, idx, ob, mt = sc.ray_cast(deps, cam.matrix_world.translation, d, distance=3.0)
                if hit:
                    near.append(((loc - cam.matrix_world.translation).length, ob.name))
    near.sort()
    # what the centre ray hits
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    hit, loc, nrm, idx, ob, mt = sc.ray_cast(deps, cam.matrix_world.translation, fwd, distance=2000.0)
    eul = cam.matrix_world.to_euler('XYZ')
    report.append(dict(name=s['name'], loc=[round(v, 3) for v in cam.matrix_world.translation], ground=round(gz, 3) if gz is not None else None,
                       ground_obj=gn, h_above_ground=round(cam.matrix_world.translation.z - gz, 3) if gz is not None else None,
                       tilt_deg=round(math.degrees(eul.x) - 90, 2), roll_deg=round(math.degrees(eul.y), 3), heading_deg=round(math.degrees(eul.z), 2),
                       lens=cd.lens, dof=[cd.dof.use_dof, round(cd.dof.focus_distance, 2), cd.dof.aperture_fstop],
                       centre_hit=[ob.name if hit else None, round((loc - cam.matrix_world.translation).length, 2) if hit else None],
                       nearest=[(round(dd, 2), nn) for dd, nn in near[:4]],
                       matrix=[list(r) for r in cam.matrix_world]))
    made.append((s['name'], cam, s))

# temporary render settings (never saved)
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = rx, ry, 100
r.use_border = False
r.image_settings.file_format = 'JPEG'
r.image_settings.quality = 90
haze = None
ng = getattr(sc, 'compositing_node_group', None)
if ng is not None and 'haze_strength' in ng.nodes:
    haze = ng.nodes['haze_strength']
if engine == 'wb':
    r.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_shadows = True
    sh.show_cavity = False
    sc.display.light_direction = (0.4, -0.5, 0.75)
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    r.use_compositing = False
else:
    r.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    r.compositor_device = 'CPU'   # the saved scene uses the GPU compositor, which needs EGL (absent here)
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    r.use_persistent_data = True
base_exposure = sc.view_settings.exposure
for name, cam, s in made:
    sc.camera = cam
    if engine != 'wb':
        sc.view_settings.exposure = s.get('exposure', base_exposure)
        if haze is not None and 'haze' in s:
            haze.inputs[1].default_value = s['haze']
    r.filepath = os.path.join(out_dir, prefix + name + '.jpg')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('CHECK_DONE', name, round(time.time() - t, 1), flush=True)
json.dump(report, open(os.path.join(out_dir, prefix + 'report.json'), 'w'), indent=1)
print('ALL_CHECKS_DONE', flush=True)
