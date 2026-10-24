# Bake test: work out the full lighting (sun, sky, shadows, bounce light) of the project's brick works ONCE,
# into one texture, so a web renderer only has to paste the texture (no lighting maths per frame).
import bpy, time, math, os, sys
argv = sys.argv[sys.argv.index('--')+1:]
size, samples, out = int(argv[0]), int(argv[1]), argv[2]
MODELS = '/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, 'factory-a.glb'))
meshes = [o for o in scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
me = obj.data
orig = me.uv_layers.active
orig.active_render = True
bake_uv = me.uv_layers.new(name='bake')
me.uv_layers.active = bake_uv
t0 = time.time()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=0.002)
bpy.ops.object.mode_set(mode='OBJECT')
t_uv = time.time() - t0
img = bpy.data.images.new('baked', size, size, alpha=False)
for mat in me.materials:
    if mat is None or not mat.use_nodes: continue
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img
    mat.node_tree.nodes.active = n
# light: warm low sun + cool sky
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.color = (1.0, 0.65, 0.4); sun.angle = math.radians(4)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(65), 0, math.radians(-38))
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.25, 0.33, 0.45, 1); bg.inputs[1].default_value = 0.8
tris = sum(len(p.vertices) - 2 for p in me.polygons)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples
scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
t1 = time.time()
bpy.ops.object.bake(type='COMBINED', margin=4, use_clear=True)
t_bake = time.time() - t1
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
print('BAKE_RESULT size', size, 'samples', samples, 'triangles', tris, 'uv_seconds', round(t_uv, 1), 'bake_seconds', round(t_bake, 1))
