# What this does: draws small preview pictures of the garden (hero view and a few close views) with Cycles on the graphics card, after the surfaces stage
# has been applied in a chosen look. Run by Blender on the RunPod worker (or locally, slowly):
#   blender -b --disable-autoexec START.blend --python render_preview.py -- LOOK OUTDIR [--weather 0|1] [--w 960 --h 640 --samples 48] [--views hero,lantern,posts,roof,ground]
# LOOK is real, painted or orig (orig = the starting file untouched, for the "before" picture).
import bpy, sys, os, time, math, json
args = sys.argv[sys.argv.index('--') + 1:]
look, outdir = args[0], args[1]
def opt(name, default):
    return args[args.index(name) + 1] if name in args else default
W, H, SAMPLES = int(opt('--w', 960)), int(opt('--h', 640)), int(opt('--samples', 48))
WEATHER = opt('--weather', '0') == '1'
TAG = opt('--tag', '')
ADDON = opt('--addon', '')
VIEWS = opt('--views', 'hero,lantern,posts,roof,ground').split(',')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.makedirs(outdir, exist_ok=True)
t0 = time.time()
log = {'look': look, 'weather': WEATHER}
if look != 'orig':
    import stage_surfaces as ss
    rep = ss.apply({'look': look, 'weathering': WEATHER, 'verbose': True, 'addon_dir': ADDON or None})
    print('PIGMENT', rep.get('pigment'))
    log['stage_seconds'] = rep['seconds']
log['stage_done_at'] = round(time.time() - t0, 1)
scene = bpy.context.scene
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
log['devices'] = [(d.name, d.type, d.use) for d in prefs.devices]
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPTIX'
except Exception:
    pass
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100
scene.render.image_settings.file_format = 'PNG'
hero = scene.camera or bpy.data.objects.get('Camera') or bpy.data.objects.get('photo')

def make_cam(name, loc, target, fov_v):
    cam = bpy.data.cameras.new(name)
    cam.sensor_fit = 'VERTICAL'
    cam.angle_y = math.radians(fov_v)
    ob = bpy.data.objects.new(name, cam)
    scene.collection.objects.link(ob)
    ob.location = loc
    from mathutils import Vector
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob
cams = {'hero': hero,
        'lantern': make_cam('prev_lantern', (2.6, -1.0, 1.15), (-1.5, 2.6, 0.7), 40.0),
        'posts': make_cam('prev_posts', (3.9, 1.3, 1.25), (0.3, 5.0, 1.1), 42.0),
        'roof': make_cam('prev_roof', (-2.4, -0.2, 2.5), (0.4, 5.0, 3.6), 40.0),
        'ground': make_cam('prev_ground', (-6.0, -4.5, 1.6), (-5.0, 1.0, 0.0), 38.0),
        'gravel': make_cam('prev_gravel', (0.5, -6.5, 1.4), (5.0, -1.0, 0.0), 35.0),
        'rocks': make_cam('prev_rocks', (-5.5, -1.0, 1.0), (-3.5, 3.7, 0.7), 40.0),
        'bridge': make_cam('prev_bridge', (-0.5, -3.0, 1.6), (-2.5, 0.8, 0.2), 40.0)}
_w = bpy.data.objects.get('Right wall behind hall')
if _w is not None:
    _c = [(_w.matrix_world @ __import__('mathutils').Vector(v)) for v in _w.bound_box]
    _cx = sum(v.x for v in _c) / 8; _cy = sum(v.y for v in _c) / 8; _minx = min(v.x for v in _c)
    cams['wall'] = make_cam('prev_wall', (_minx - 5.0, _cy - 1.0, 1.5), (_cx, _cy, 1.2), 40.0)
for v in VIEWS:
    scene.camera = cams[v]
    if WEATHER and look == 'real':
        import weathering_stage
        weathering_stage.camera_for_picture(cams[v], H)
    scene.render.filepath = os.path.join(outdir, f'{look}{TAG}_{v}.png')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    log[f'draw_{v}_s'] = round(time.time() - t, 1)
    print('DRAWN', v, log[f'draw_{v}_s'], 's', flush=True)
if '--dialtest' in args and WEATHER and look == 'real':
    # render the first view several times with different wallgrowth / groundmoss dials set on top (to see which dial makes which mark)
    import weathering_stage
    w = weathering_stage._HANDLE['w']
    v0 = VIEWS[0]
    scene.camera = cams[v0]
    weathering_stage.camera_for_picture(cams[v0], H)
    variants = json.loads(args[args.index('--dialtest') + 1])
    for name, spec in variants.items():
        for layer, dials in spec.items():
            w.set_dials(layer, **dials)
        scene.render.filepath = os.path.join(outdir, f'dial_{name}_{v0}.png')
        bpy.ops.render.render(write_still=True)
        print('DIALTEST', name, flush=True)
if '--sweep' in args and WEATHER and look == 'real':
    # one picture per kit layer with that layer switched off (to see what each layer does), on the first view
    import weathering_stage
    w = weathering_stage._HANDLE['w']
    v0 = VIEWS[0]
    scene.camera = cams[v0]
    weathering_stage.camera_for_picture(cams[v0], H)
    for layer in weathering_stage.LAYERS:
        w.layer_off(layer)
        scene.render.filepath = os.path.join(outdir, f'sweep_off_{layer}_{v0}.png')
        bpy.ops.render.render(write_still=True)
        w.layer_on(layer)
        print('SWEPT', layer, flush=True)
    for layer in weathering_stage.LAYERS:
        w.layer_off(layer)
    scene.render.filepath = os.path.join(outdir, f'sweep_off_ALL_{v0}.png')
    bpy.ops.render.render(write_still=True)
log['total_s'] = round(time.time() - t0, 1)
json.dump(log, open(os.path.join(outdir, f'{look}{TAG}_log.json'), 'w'), indent=1)
print('LOG', json.dumps(log))
