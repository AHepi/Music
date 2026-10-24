# What this does: a close look at a factory's cart doorway from the lane (scratch check, round 5): opens the doors,
# lights the doorway, adds a warm room light that reaches only the room and its machines, and draws it.
# Run: blender -b FACTORY.blend --python look_doorway.py -- OUT.png CAMERA_X CAMERA_Y FOV_DEGREES AIM_Z PREFIX
import bpy, math, sys, os
sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/inflation-chapter-2-newcomers/works')
import works_kit as kit
args = sys.argv[sys.argv.index('--') + 1:]
out, cx, cy, fov, aim, prefix = args[0], float(args[1]), float(args[2]), float(args[3]), float(args[4]), args[5]
scene = bpy.context.scene
kit.set_doorway(prefix, True)
for side in ('left', 'right'):
    leaf = bpy.data.objects.get(f'{prefix}-loading-door-{side}')
    if leaf is not None and prefix == 'no-1':
        leaf.rotation_mode = 'XYZ'
        leaf.rotation_euler.z = math.radians(100 if side == 'right' else -100)
cam = bpy.data.objects.new('look', bpy.data.cameras.new('look'))
scene.collection.objects.link(cam)
cam.data.sensor_fit = 'VERTICAL'
cam.data.angle_y = math.radians(fov)
cam.location = (cx, cy, 1.84)
cam.rotation_euler = (math.radians(90 + math.degrees(math.atan2(aim - 1.84, 8.0 - cy))), 0, 0)
scene.camera = cam
x = 2.9 if prefix == 'no-2' else -3.4
room = bpy.data.objects.new('room', bpy.data.lights.new('room', 'POINT'))
room.data.energy = 160; room.data.color = (1.0, 0.66, 0.36); room.data.use_shadow = False; room.data.shadow_soft_size = 0.8
room.location = (x, 10.2, 3.9)
scene.collection.objects.link(room)
front = bpy.data.objects.new('front', bpy.data.lights.new('front', 'POINT'))
front.data.energy = 300; front.data.color = (0.6, 0.7, 1.0); front.data.use_shadow = False
front.location = (cx, cy + 3, 4.0)
scene.collection.objects.link(front)
coll = bpy.data.collections.new('room-reach'); scene.collection.children.link(coll)
for o in bpy.data.objects:
    if o.name in (f'{prefix}-doorway-room', f'{prefix}-doorway-machines'):
        coll.objects.link(o)
room.light_linking.receiver_collection = coll
world = scene.world or bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.1, 0.13, 0.2, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x, scene.render.resolution_y = 720, 720
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
