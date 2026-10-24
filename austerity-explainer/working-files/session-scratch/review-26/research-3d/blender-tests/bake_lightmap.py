# Bake a light-only map (sun, sky, shadows, bounce) into the model's own second UV layout (UVMap.001),
# the same layout its corner-shading picture already uses. A web page can then light the model for free.
import bpy, time, math, os, sys
argv = sys.argv[sys.argv.index('--')+1:]
size, samples, out = int(argv[0]), int(argv[1]), argv[2]
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath='/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models/factory-a.glb')
# ground so the building gets contact shadows and bounce light
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.02))
img = bpy.data.images.new('lightmap', size, size, alpha=False, float_buffer=True)
targets = []
for o in scene.objects:
    if o.type != 'MESH' or 'UVMap.001' not in o.data.uv_layers: continue
    o.data.uv_layers['UVMap'].active_render = True
    o.data.uv_layers.active = o.data.uv_layers['UVMap.001']
    for mat in o.data.materials:
        if mat is None or not mat.use_nodes: continue
        n = mat.node_tree.nodes.get('LM') or mat.node_tree.nodes.new('ShaderNodeTexImage'); n.name = 'LM'; n.image = img
        mat.node_tree.nodes.active = n
    targets.append(o)
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.color = (1.0, 0.65, 0.4); sun.angle = math.radians(4)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(65), 0, math.radians(-38))
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.25, 0.33, 0.45, 1); bg.inputs[1].default_value = 0.8
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples
scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
bake = scene.render.bake; bake.use_pass_direct = True; bake.use_pass_indirect = True; bake.use_pass_color = False
bpy.ops.object.select_all(action='DESELECT')
for o in targets: o.select_set(True)
bpy.context.view_layer.objects.active = targets[0]
t = time.time()
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, margin=4, use_clear=True)
dt = time.time() - t
# save as 8-bit PNG scaled into 0..1 (light can exceed 1; divide by 2 and multiply back in the page)
img.scale(size, size)
px = list(img.pixels)
for i in range(0, len(px), 4):
    px[i] = min(1.0, px[i] / 2.0); px[i+1] = min(1.0, px[i+1] / 2.0); px[i+2] = min(1.0, px[i+2] / 2.0)
out_img = bpy.data.images.new('lm8', size, size, alpha=False); out_img.pixels = px
out_img.filepath_raw = out; out_img.file_format = 'PNG'; out_img.save()
print('LIGHTMAP_RESULT objects', len(targets), 'size', size, 'samples', samples, 'bake_seconds', round(dt, 1))
