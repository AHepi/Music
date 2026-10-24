# Scratch: block out the two works as plain boxes in the test Works lane and draw the plan's three lane
# views small, to see which layout lets the chimneys show over the mills.
import bpy, math, sys, os
from mathutils import Euler
args = sys.argv[sys.argv.index('--') + 1:]
variant, out = args[0], args[1]
WALL_Y = 22.0
def box(name, x0, x1, y0, y1, z0, z1, colour):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    o.scale = (x1 - x0, y1 - y0, z1 - z0); o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    o.color = (*colour, 1)
    return o
def cyl(name, x, y, r0, r1, h, colour, sides=24):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=r0, radius2=r1, depth=h, location=(x, y, h / 2))
    o = bpy.context.active_object; o.name = name; o.color = (*colour, 1)
red, buff, wall, tank = (0.45, 0.12, 0.08), (0.75, 0.7, 0.55), (0.3, 0.3, 0.3), (0.1, 0.1, 0.4)
box('works wall', -40, 40, WALL_Y, WALL_Y + 0.5, 0, 4, wall)
box('dividing wall', -0.3, 0.3, WALL_Y, WALL_Y + 8, 0, 6, wall)
if variant == 'A':
    mills = [(-6.4, -26.4, 11, 2.6), (6.4, 28.4, 11, 3.6)]
elif variant == 'D':
    mills = [(-0.8, -22.8, 11, 2.6), (0.8, 24.8, 11, 3.6)]
else:
    mills = [(-0.8, -22.8, 7.6, 2.4), (0.8, 24.8, 7.6, 3.2)]
for i, (a, b, eaves, roof) in enumerate(mills):
    colour = red if i == 0 else buff
    x0, x1 = min(a, b), max(a, b)
    box(f'mill {i}', x0, x1, WALL_Y + 8, WALL_Y + 30, 0, eaves, colour)
    # roof profile: teeth (No. 1) or two gables (No. 2) as thin boxes
    if i == 0:
        bay = (x1 - x0) / 4
        for k in range(4):
            for s in range(6):
                f = (s + 0.5) / 6
                box(f'tooth {k} {s}', x0 + k * bay + s * bay / 6, x0 + k * bay + (s + 1) * bay / 6, WALL_Y + 8, WALL_Y + 30, eaves, eaves + roof * f, colour)
    else:
        span = (x1 - x0) / 2
        for k in range(2):
            for s in range(8):
                f = 1 - abs((s + 0.5) / 8 - 0.5) * 2
                box(f'gable {k} {s}', x0 + k * span + s * span / 8, x0 + k * span + (s + 1) * span / 8, WALL_Y + 8, WALL_Y + 30, eaves, eaves + roof * f, colour)
            box(f'lantern {k}', x0 + k * span + span / 2 - 1, x0 + k * span + span / 2 + 1, WALL_Y + 10, WALL_Y + 28, eaves + roof, eaves + roof + 1.2, colour)
cyl('chimney 1', -5.3, WALL_Y + 35, 1.4, 0.9, 25, red)
for x, y, h in ((5.3, 35, 23), (8.6, 39, 21)):
    box(f'chimney 2 {x}', x - 0.9, x + 0.9, WALL_Y + y - 0.9, WALL_Y + y + 0.9, 0, h, buff)
box('tank', 1.6, 5.6, WALL_Y + 18, WALL_Y + 21, 11, 14, tank)
for x in (1.8, 5.4):
    for y in (18.2, 20.8):
        box('leg', x - 0.15, x + 0.15, WALL_Y + y - 0.15, WALL_Y + y + 0.15, 0, 11, tank)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'OBJECT'
scene.display.shading.show_shadows = False
scene.render.resolution_x, scene.render.resolution_y = 270, 480
for name, (x, y, z) in {'W3': (0, WALL_Y - 30, 4.6), 'W1': (-5.0, WALL_Y - 13, 1.7), 'W2': (5.0, WALL_Y - 13, 1.7)}.items():
    data = bpy.data.cameras.new(name); data.sensor_fit = 'VERTICAL'; data.angle_y = math.radians(60.4); data.clip_end = 3000
    cam = bpy.data.objects.new(name, data); scene.collection.objects.link(cam)
    cam.location = (x, y, z); cam.rotation_euler = Euler((math.radians(90), 0, 0))
    scene.camera = cam
    scene.render.filepath = os.path.join(out, f'{variant}-{name}.png')
    bpy.ops.render.render(write_still=True)
