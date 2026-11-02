import sys, os, time, bpy
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
blend, out, w, h, samples = args[0], args[1], int(args[2]), int(args[3]), int(args[4])
bpy.ops.wm.open_mainfile(filepath=blend)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'
s.render.resolution_x = w; s.render.resolution_y = h; s.render.resolution_percentage = 100
s.cycles.samples = samples; s.cycles.use_denoising = True; s.cycles.denoiser = 'OPENIMAGEDENOISE'
try:
    s.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'; s.cycles.denoising_prefilter = 'ACCURATE'
except Exception as e: print('denoise opts', e)
s.cycles.max_bounces = 6; s.cycles.diffuse_bounces = 3; s.cycles.glossy_bounces = 3; s.cycles.transmission_bounces = 6
s.cycles.transparent_max_bounces = 16
s.cycles.volume_bounces = 1; s.cycles.volume_step_rate = 2.0; s.cycles.volume_max_steps = 64
s.cycles.sample_clamp_indirect = 8
s.view_settings.view_transform = 'AgX'; s.view_settings.exposure = float(os.environ.get('EXPO','-0.8'))
try: s.view_settings.look = os.environ.get('LOOK','AgX - High Contrast')
except Exception as e: print('look', e)
if os.environ.get('HAZEDENS'):
    for n in bpy.data.materials['haze'].node_tree.nodes:
        if n.type == 'VOLUME_SCATTER': n.inputs['Density'].default_value = float(os.environ['HAZEDENS'])
if os.environ.get('SKYSTR'):
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value = float(os.environ['SKYSTR'])
if os.environ.get('SKYAIR'):
    sk = s.world.node_tree.nodes['Sky Texture']; sk.air_density = float(os.environ['SKYAIR']); sk.aerosol_density = float(os.environ.get('SKYAER', '0.3'))
if os.environ.get('SUNSTR'):
    bpy.data.lights['sun'].energy = float(os.environ['SUNSTR'])
if os.environ.get('CAMLENS'):
    s.camera.data.lens = float(os.environ['CAMLENS'])
if os.environ.get('CAMPOS'):
    from mathutils import Vector
    cam = s.camera
    cam.location = Vector([float(v) for v in os.environ['CAMPOS'].split(',')])
    tgt = Vector([float(v) for v in os.environ['CAMLOOK'].split(',')])
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = float(os.environ.get('LENS', '35'))
ng = s.compositing_node_group
if ng is not None and ng.nodes.get('VigBlur') is not None:
    ng.nodes['VigBlur'].inputs['Size'].default_value = (w * 0.30, h * 0.30)
    if os.environ.get('NOCOMP'): s.compositing_node_group = None
s.render.image_settings.file_format = 'PNG'
s.render.filepath = os.path.abspath(out)
s.render.threads = 2
t = time.time(); bpy.ops.render.render(write_still=True)
print('RENDER_SECONDS', round(time.time() - t, 1))
