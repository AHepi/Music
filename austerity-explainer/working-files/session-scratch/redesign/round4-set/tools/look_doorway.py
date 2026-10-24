# What this does: a close look at a factory's cart doorway and gable windows from the lane (scratch check).
# Run: blender -b FACTORY.blend --python look_doorway.py -- OUT.png CAMERA_X CAMERA_Y FOV_DEGREES AIM_Z
import bpy, math, sys
args = sys.argv[sys.argv.index('--') + 1:]
out, cx, cy, fov, aim = args[0], float(args[1]), float(args[2]), float(args[3]), float(args[4])
scene = bpy.context.scene
cam = bpy.data.objects.new('look', bpy.data.cameras.new('look'))
scene.collection.objects.link(cam)
cam.data.sensor_fit = 'VERTICAL'
cam.data.angle_y = math.radians(fov)
cam.location = (cx, cy, 1.84)
cam.rotation_euler = (math.radians(90 + math.degrees(math.atan2(aim - 1.84, 8.0 - cy))), 0, 0)
scene.camera = cam
for name, loc, energy in (('room', (cx * 0 + (2.9 if cx > 0 else -3.4), 11.0, 4.0), 150.0), ('front', (cx, cy + 3, 4.0), 400.0)):
    light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'POINT'))
    light.data.energy = energy; light.data.color = (1.0, 0.7, 0.4); light.data.use_shadow = False
    light.location = loc
    scene.collection.objects.link(light)
world = scene.world or bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.1, 0.13, 0.2, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x, scene.render.resolution_y = 720, 720
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
