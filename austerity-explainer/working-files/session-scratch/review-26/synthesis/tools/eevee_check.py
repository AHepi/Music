# Independent check: can EEVEE draw a tall frame on this machine through a virtual screen, and how fast?
# Reads the project's models only (never writes to the project).
import bpy, sys, time, os, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
M = '/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
sc = bpy.context.scene
for n in ['town.glb', 'factory-a.glb']:
    bpy.ops.import_scene.gltf(filepath=os.path.join(M, n))
cd = bpy.data.cameras.new('c'); cd.lens = 30
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
cam.location = Vector((1.6, -10.5, 0.9)); tgt = Vector((0, 0, 2.2))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = cam
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 4.0; sun.color = (1.0, 0.62, 0.35)
so = bpy.data.objects.new('s', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(72), 0, math.radians(-38))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.2, 0.3, 0.42, 1)
r = sc.render; r.resolution_x, r.resolution_y = 1080, 1920; r.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 16; r.image_settings.file_format = 'JPEG'; r.filepath = out
times = []
for i in range(2):
    t = time.time(); bpy.ops.render.render(write_still=True); times.append(round(time.time() - t, 1))
import gpu
print('CHECK_RESULT seconds', times, '|', gpu.platform.renderer_get())
