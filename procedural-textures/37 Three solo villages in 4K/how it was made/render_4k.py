# What this file does (runs inside Blender on a rented graphics card): draws chosen camera views of the
# open scene at 3840 x 2560 with the card (OptiX, or CUDA if OptiX is missing), applying each shot's own
# settings from a settings file (samples, exposure, haze strength, road-detail level), keeping the
# scene's own light and colour otherwise, and saves each view as a high-quality JPG.
# Run: blender -b SCENE.blend --python render_4k.py -- SETTINGS.json OUT_FOLDER PREFIX PICTURE_NAME ...
import bpy, json, os, sys, time

arguments = sys.argv[sys.argv.index('--') + 1:]
settings = json.load(open(arguments[0]))
out_folder, prefix, wanted = arguments[1], arguments[2], set(arguments[3:])
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene

preferences = bpy.context.preferences.addons['cycles'].preferences
device_type_used = None
for device_type in ('OPTIX', 'CUDA'):
    try:
        preferences.compute_device_type = device_type
        preferences.get_devices()
        if any(d.type == device_type for d in preferences.devices):
            for d in preferences.devices:
                d.use = d.type == device_type
            device_type_used = device_type
            break
    except Exception:
        continue
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU' if device_type_used else 'CPU'
try:
    scene.render.compositor_device = 'CPU'
except Exception:
    pass
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 3840, 2560, 100
scene.cycles.use_denoising = True
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 95


def set_modifier_input(modifier, name, value):
    for item in modifier.node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == name:
            try:
                getattr(modifier.properties.inputs, item.identifier).value = value
            except AttributeError:
                modifier[item.identifier] = value
            return


log = {'device': device_type_used or 'CPU', 'views': []}
for shot in settings['shots']:
    if wanted and shot['picture'] not in wanted:
        continue
    camera = bpy.data.objects.get(shot['camera'])
    if camera is None:
        log['views'].append({'camera': shot['camera'], 'error': 'camera not found'})
        continue
    scene.camera = camera
    if 'samples' in shot:
        scene.cycles.samples = shot['samples']
    if 'exposure' in shot:
        scene.view_settings.exposure = shot['exposure']
    group = getattr(scene, 'compositing_node_group', None)
    if 'haze' in shot and group is not None and 'haze_strength' in group.nodes:
        group.nodes['haze_strength'].inputs[1].default_value = shot['haze']
    for object_name, level in shot.get('relief', {}).items():
        target = bpy.data.objects.get(object_name)
        if target is not None and 'relief' in target.modifiers:
            set_modifier_input(target.modifiers['relief'], 'Level', level)
    scene.render.filepath = os.path.join(out_folder, f"{prefix}{shot['picture']}.jpg")
    start = time.time()
    bpy.ops.render.render(write_still=True)
    log['views'].append({'camera': shot['camera'], 'picture': shot['picture'], 'seconds': round(time.time() - start, 1)})
    print('VIEW_DONE', shot['picture'], round(time.time() - start, 1), flush=True)
    json.dump(log, open(os.path.join(out_folder, f'{prefix}render_log_{os.getpid()}.json'), 'w'), indent=1)
print('RENDER_4K_DONE', json.dumps(log), flush=True)
