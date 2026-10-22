# Runs on the RunPod worker (and locally with --device cpu): open the starting file, apply the life stage, draw pictures with Cycles.
# Use: blender -b --disable-autoexec START.blend -P render_preview.py -- LOOK OUTDIR SIZE_X SAMPLES VIEWS [steps]
#   VIEWS = comma list of names: hero, pond, maple, veranda, lantern, rocks
import bpy, sys, os, time, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
look, outdir, sx, samples, views = argv[0], argv[1], int(argv[2]), int(argv[3]), argv[4].split(',')
steps = argv[5].split(',') if len(argv) > 5 and argv[5] != 'all' else None
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)   # this folder holds stage_life.py, astra_loader.py and addon_copy
import stage_life
label = look
chain = look.endswith('+shapes')
look = look.split('+')[0]
t0 = time.time()
if chain:                                      # compatibility test: the other builder's shapes stage first (a copy kept next to this file)
    import stage_shapes_copy
    stage_shapes_copy.apply({'look': look})
rep = stage_life.apply({'look': look, 'steps': steps, 'addon': os.path.join(HERE, 'addon_copy')})
t_stage = time.time() - t0
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
dev = 'none'
for kind in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type != 'CPU']
        if gpus:
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            sc.cycles.device = 'GPU'
            dev = kind + ':' + ','.join(d.name for d in gpus)
            break
    except Exception as e:
        print('device try failed', kind, e)
print('CYCLES DEVICE', dev)
sc.cycles.samples = samples
sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_x = sx
sc.render.resolution_y = int(sx * 2 / 3)
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
VIEWS = {
    'hero': None,
    'pond': (-2.0, -2.6, 1.3, -3.6, 1.0, -0.15, 30),
    'maple': (-3.2, -1.8, 1.5, -5.2, 1.3, 3.0, 32),
    'veranda': (3.6, 5.3, 1.55, -2.5, 0.8, 0.55, 24),
    'lantern': (-1.5, -2.5, 1.4, 1.0, 1.1, 1.0, 40),
    'rocks': (-3.5, -0.8, 1.1, -3.8, 3.4, 0.2, 35),
}
os.makedirs(outdir, exist_ok=True)
main_cam = sc.camera
log = {'device': dev, 'stage_seconds': round(t_stage, 1), 'pictures': {}}
for v_full in views:
    v, _, eng = v_full.partition('@')
    spec = VIEWS[v]
    sc.render.engine = 'BLENDER_EEVEE' if eng == 'eevee' else 'CYCLES'
    if spec is None:
        sc.camera = main_cam
    else:
        x, y, z, tx, ty, tz, lens = spec
        cd = bpy.data.cameras.new('life_' + v); cd.lens = lens; cd.sensor_width = 36
        co = bpy.data.objects.new('life_' + v, cd); sc.collection.objects.link(co); co.location = (x, y, z)
        co.rotation_euler = (Vector((tx, ty, tz)) - co.location).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = co
    path = os.path.join(outdir, f'{label}_{v}{"_eevee" if eng == "eevee" else ""}.png')
    sc.render.filepath = path
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    log['pictures'][v_full] = round(time.time() - t1, 1)
    print('PICTURE', v_full, log['pictures'][v_full], 's')
json.dump(log, open(os.path.join(outdir, f'{label}_log.json'), 'w'))
print('TOTAL', round(time.time() - t0, 1))
