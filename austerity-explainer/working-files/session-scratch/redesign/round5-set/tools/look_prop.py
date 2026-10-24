# What this does: draws one prop from the side and from the front (scratch look, round 5).
# Run: blender -b --python look_prop.py -- PROP.glb OUT.png
import bpy, math, sys
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=args[0])
scene = bpy.context.scene
for o in scene.objects:
    if o.type == 'MESH':
        print('part', o.name, [round(v, 3) for v in o.matrix_world.translation], [round(v,3) for v in o.dimensions])
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.5
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x, scene.render.resolution_y = 600, 600
for name, loc, rot in (('side', (5, 0, 0.9), (math.radians(90), 0, math.radians(90))), ('front', (0, -5, 0.9), (math.radians(90), 0, 0))):
    cam.location = loc; cam.rotation_euler = rot
    scene.render.filepath = args[1].replace('.png', f'-{name}.png')
    bpy.ops.render.render(write_still=True)
