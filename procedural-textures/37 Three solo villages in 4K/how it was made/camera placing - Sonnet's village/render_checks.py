import bpy, sys, json, math, time, os
sys.path.insert(0, os.path.dirname(__file__))
import camlib
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
spec_path, names, mode, samples, outdir, pct = argv[0], argv[1].split(','), argv[2], int(argv[3]), argv[4], int(argv[5])
specs = {s['name']: s for s in json.load(open(spec_path))}
sc = bpy.context.scene
coll = bpy.data.collections['Cameras']
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1200, 800, pct
r.image_settings.file_format = 'JPEG'; r.image_settings.quality = 88
if mode == 'wb':
    r.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = False
else:
    r.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    r.use_persistent_data = True
dg = bpy.context.evaluated_depsgraph_get()
for nm in names:
    sp = specs[nm]
    ob, loc, tgt = camlib.make_camera(sp, coll)
    dg.update()
    # safety: inside-object test and nearest hits over the frame
    inside = []
    for dv in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
        res, p, n, i, o, m = sc.ray_cast(dg, loc, Vector(dv))
        if res and n.dot(Vector(dv)) > 0 and (p - loc).length < 3:
            inside.append((o.name, round((p - loc).length, 2)))
    cam = ob.data
    fr = [ob.matrix_world @ v for v in cam.view_frame(scene=sc)]
    near = []
    for a in range(7):
        for b in range(5):
            u, v = (a + 0.5) / 7, (b + 0.5) / 5
            # frame corners order: tr, br, bl, tl
            top = fr[3].lerp(fr[0], u); bot = fr[2].lerp(fr[1], u)
            pt = bot.lerp(top, v)
            dvec = (pt - loc).normalized()
            res, p, n, i, o, m = sc.ray_cast(dg, loc, dvec)
            if res:
                near.append(((p - loc).length, o.name, round(u, 2), round(v, 2)))
    near.sort()
    gz = camlib.ground(loc.x, loc.y)
    from bpy_extras.object_utils import world_to_camera_view
    proj = []
    for b in bpy.data.collections['Buildings'].objects:
        pts = [world_to_camera_view(sc, ob, b.matrix_world @ Vector(c)) for c in b.bound_box]
        if all(p.z > 0 for p in pts):
            xs = [p.x for p in pts]; ys = [p.y for p in pts]
            if max(xs) > 0 and min(xs) < 1 and max(ys) > 0 and min(ys) < 1:
                proj.append('%s x%.2f..%.2f y%.2f..%.2f' % (b.name, min(xs), max(xs), min(ys), max(ys)))
    print('PROJ', nm, proj)
    sc.camera = ob
    r.filepath = os.path.join(outdir, '%s_%s.jpg' % (nm, mode))
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    d = tgt - loc
    pitch = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
    yaw = math.degrees(math.atan2(d.y, d.x))
    print('CHECK %s loc=(%.2f,%.2f,%.2f) agl=%.2f tgt=(%.2f,%.2f,%.2f) dist=%.1f pitch=%.1f yaw=%.1f lens=%s render=%.0fs inside=%s near=%s' % (
        nm, loc.x, loc.y, loc.z, loc.z - gz, tgt.x, tgt.y, tgt.z, d.length, pitch, yaw, sp.get('lens'), time.time() - t0, inside,
        [(round(a, 2), b, c, e) for a, b, c, e in near[:4]]))
    sys.stdout.flush()
