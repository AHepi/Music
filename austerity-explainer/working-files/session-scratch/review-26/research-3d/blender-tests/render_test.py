# Render-time test: imports the project's own Blender models (read only) and renders one tall frame.
# Usage: blender -b --factory-startup --python render_test.py -- ENGINE SAMPLES OUT [extra flags]
import bpy, sys, time, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
engine, samples, out = argv[0], int(argv[1]), argv[2]
flags = set(argv[3:])
MODELS = '/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models'
t0 = time.time()
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
for name in ['town.glb', 'factory-a.glb', 'factory-b.glb', 'props.glb']:
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, name))
objs = [o for o in scene.objects if o.type == 'MESH']
tris = 0
for o in objs:
    me = o.data
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
mins = Vector((1e9,)*3); maxs = Vector((-1e9,)*3)
fa = [o for o in objs if 'factory' in o.name.lower() or 'works' in o.name.lower()]
for o in (fa or objs):
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mins = Vector(map(min, mins, w)); maxs = Vector(map(max, maxs, w))
print('MODEL_INFO objects', len(objs), 'triangles', tris, 'bbox', tuple(round(v,2) for v in mins), tuple(round(v,2) for v in maxs), 'focus objs', len(fa))
center = (mins + maxs) / 2
size = (maxs - mins).length
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 28
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam)
cam.location = center + Vector((size*0.15, -size*0.55, size*0.05))
direction = center - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; sun.color = (1.0, 0.75, 0.5); sun.angle = math.radians(3)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so)
so.rotation_euler = (math.radians(70), 0, math.radians(-40))
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.25, 0.35, 0.45, 1); bg.inputs[1].default_value = 0.6
if 'fog' in flags:
    world.node_tree.nodes.new('ShaderNodeVolumePrincipled')
    vol = world.node_tree.nodes.new('ShaderNodeVolumeScatter'); vol.inputs['Density'].default_value = 0.02
    world.node_tree.links.new(vol.outputs[0], world.node_tree.nodes['World Output'].inputs['Volume'])
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.image_settings.file_format = 'JPEG'
r.filepath = out
if engine == 'CYCLES':
    r.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    try: scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception as e: print('denoiser', e)
    scene.cycles.max_bounces = 4
    r.threads_mode = 'FIXED'; r.threads = 4
elif engine == 'EEVEE':
    r.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = samples
    if 'raytrace' in flags:
        scene.eevee.use_raytracing = True
    if 'shadows_off' in flags:
        scene.eevee.use_shadows = False
elif engine == 'WORKBENCH':
    r.engine = 'BLENDER_WORKBENCH'
    scene.display.render_aa = '8'
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'TEXTURE'
if 'freestyle' in flags:
    r.use_freestyle = True
    r.line_thickness_mode = 'ABSOLUTE'; r.line_thickness = 1.5
if 'kuwahara' in flags:
    # compositor painterly filter (Blender 4.0+ Kuwahara node)
    try:
        tree = bpy.data.node_groups.new('comp', 'CompositorNodeTree')
        scene.compositing_node_group = tree
        rl = tree.nodes.new('CompositorNodeRLayers')
        kw = tree.nodes.new('CompositorNodeKuwahara')
        outn = tree.nodes.new('NodeGroupOutput')
        tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        print('KUWAHARA inputs', [i.name for i in kw.inputs], [p.identifier for p in kw.bl_rna.properties][-12:])
        tree.links.new(rl.outputs['Image'], kw.inputs['Image'])
        tree.links.new(kw.outputs['Image'], outn.inputs[0])
    except Exception as e:
        print('KUWAHARA setup failed (5.x API):', repr(e))
        try:
            scene.use_nodes = True
            tree = scene.node_tree
            rl = tree.nodes['Render Layers']; comp = tree.nodes['Composite']
            kw = tree.nodes.new('CompositorNodeKuwahara')
            tree.links.new(rl.outputs['Image'], kw.inputs['Image'])
            tree.links.new(kw.outputs['Image'], comp.inputs['Image'])
        except Exception as e2:
            print('KUWAHARA old API failed:', repr(e2))
t1 = time.time()
print('SETUP_SECONDS', round(t1-t0,1))
bpy.ops.render.render(write_still=True)
t2 = time.time()
print('RENDER_SECONDS', engine, samples, sorted(flags), round(t2-t1,1))
try:
    import gpu
    print('GPU', gpu.platform.vendor_get(), '|', gpu.platform.renderer_get(), '|', gpu.platform.version_get())
except Exception as e:
    print('GPU info n/a', repr(e)[:120])
