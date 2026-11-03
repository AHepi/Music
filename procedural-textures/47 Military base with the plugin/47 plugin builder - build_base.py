"""Builds a military camp (a 1915-style army camp) as plain named shapes. Lay along Y. python3 build_base.py --out base.blend"""
import argparse, math, os, random, sys
import bpy
from mathutils import Vector

def box(name, c, s, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    o = bpy.context.object; o.name = name; o.scale = s; o.rotation_euler = rotation
    bpy.ops.object.transform_apply(scale=True); return o
def cyl(name, c, r, h, v=16, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=c)
    o = bpy.context.object; o.name = name; o.rotation_euler = rot; return o
def plane(name, c, s):
    bpy.ops.mesh.primitive_plane_add(size=1, location=c)
    o = bpy.context.object; o.name = name; o.scale = (s[0], s[1], 1)
    bpy.ops.object.transform_apply(scale=True); return o

def hut(rng, side, y0, length, tag, kinds):
    """a timber barrack hut: road-side wall slab, back wall, gables, two roof slabs, windows, door, stovepipe"""
    fx = side * 5.0          # face of the wall, towards the road
    depth = 6.0
    h = 2.7
    mid = y0 + length / 2
    cx = fx + side * depth / 2
    n = 'hut %s ' % tag
    box(n + 'wall timber', (fx + side*0.1, mid, h/2 + 0.3), (0.2, length, h))        # road side
    box(n + 'back wall timber', (fx + side*(depth-0.1), mid, h/2 + 0.3), (0.2, length, h))
    for gy in (y0 + 0.1, y0 + length - 0.1):
        box(n + 'gable wall timber', (cx, gy, h/2 + 0.9), (depth, 0.2, h + 1.2))
    box(n + 'plinth stone', (fx + side*0.1, mid, 0.15), (0.3, length + 0.2, 0.3))
    for p in (-1, 1):
        box(n + 'roof slate', (cx + p * depth/4 * 0.98, mid, h + 0.3 + 0.8), (depth/2 + 0.35, length + 0.5, 0.1),
            rotation=(0, p * math.radians(20), 0))
    box(n + 'ridge iron', (cx, mid, h + 0.3 + 1.28), (0.2, length + 0.5, 0.12))
    cols = int((length - 3) / 2.4)
    for i in range(cols):
        wy = y0 + 2.7 + i * 2.4 + 0.6
        k = rng.choice(kinds)
        box(n + 'window ' + k, (fx - side*0.0, wy, 1.7), (0.08, 1.1, 1.05))
        box(n + 'shutter wood', (fx - side*0.02, wy - 0.7, 1.7), (0.06, 0.3, 1.05))
        box(n + 'shutter wood', (fx - side*0.02, wy + 0.7, 1.7), (0.06, 0.3, 1.05))
    box(n + 'door wood', (fx - side*0.0, y0 + 1.2, 1.35), (0.1, 1.0, 2.1))
    box(n + 'door step', (fx - side*0.5, y0 + 1.2, 0.2), (0.9, 1.5, 0.12))
    cyl(n + 'stovepipe iron', (fx + side*2.0, mid + rng.uniform(-2, 2), h + 1.8), 0.1, 2.4)
    # a fire bucket and a water butt at the hut's end
    cyl(n + 'water butt wood', (fx - side*0.6, y0 + length - 0.8, 0.5), 0.45, 0.9, v=20)
    cyl(n + 'drain pipe iron', (fx - side*0.04, y0 + length - 0.8, 1.5), 0.05, 2.2)

def build(seed=7):
    rng = random.Random(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    plane('parade ground earth', (0, 40, 0), (70, 140))
    # wheel ruts and duckboard paths
    for x in (-1.8, 1.9):
        plane('rut puddle water %d' % int(x*10), (x, 22, 0.02), (0.5, 3.2))
    for x, y, l in ((-2.0, 6.5, 2.5), (2.2, 30, 3.5), (-1.5, 42, 2.0), (1.0, 55, 3.0)):
        plane('puddle water %d' % int(y*10), (x, y, 0.015), (1.4, l))
    for side in (-1, 1):
        plane('duckboard path planks %d' % side, (side*4.2, 42, 0.05), (1.0, 84))
    # huts
    ys = [6, 21, 36, 51, 66]
    for i, y in enumerate(ys):
        hut(rng, -1, y, 12, 'L%d' % i, ['dark', 'dark', 'dim', 'dark', 'lit'] if i in (1, 3) else ['dark', 'dark', 'dim', 'dark'])
    for i, y in enumerate([6, 21, 66]):
        hut(rng, 1, y, 12, 'R%d' % i, ['dark', 'lit', 'dim', 'dark'] if i != 1 else ['dark', 'dim', 'dark', 'lit'])
    # headquarters: a brick building on the right
    hy, hl = 36, 22
    fx = 6.0
    box('headquarters wall brick', (fx + 4.0, hy + hl/2, 4.0), (8.0, hl, 8.0))
    for p in (-1, 1):
        box('headquarters roof slate', (fx + 4.0 + p*2.2, hy + hl/2, 8.0 + 1.0), (4.8, hl + 0.8, 0.14), rotation=(0, p*math.radians(24), 0))
    for cy in (hy + 5, hy + hl - 5):
        box('headquarters chimney brick', (fx + 6.0, cy, 10.8), (1.2, 1.0, 2.6))
    box('headquarters chimney smoke', (fx + 6.0, hy + 5, 13.8), (2.0, 2.0, 4.0))
    for r, z in enumerate((2.0, 5.2)):
        for c in range(6):
            wy = hy + 2.0 + c * 3.6
            if r == 0 and c == 2: continue
            kind = 'lit' if (r, c) in ((1, 1), (0, 4)) else ('dim' if (r, c) == (1, 4) else 'dark')
            box('headquarters window surround stone', (fx - 0.04, wy, z), (0.08, 1.4, 2.0))
            box('headquarters window ' + kind, (fx - 0.08, wy, z), (0.06, 1.1, 1.7))
    dy = hy + 2.0 + 2 * 3.6
    box('headquarters door surround stone', (fx - 0.05, dy, 1.4), (0.1, 1.7, 2.8))
    box('headquarters door wood', (fx - 0.09, dy, 1.3), (0.06, 1.3, 2.5))
    box('headquarters door step', (fx - 0.6, dy, 0.1), (1.2, 2.2, 0.2))
    box('headquarters door step', (fx - 1.1, dy, 0.05), (1.0, 2.6, 0.1))
    # sandbag wall by the door and a flagpole
    for k in range(3):
        for j in range(8):
            box('sandbag earth', (fx - 2.0 - k*0.0 - (0.0), dy - 4.5 + j*0.55 + 0.0 + (0.27 if k == 1 else 0), 0.15 + k*0.28 - 0.0), (0.5, 0.52, 0.27), rotation=(0, 0, rng.uniform(-0.1, 0.1)))
    cyl('flagpole mast iron', (4.9, dy + 5, 5.0), 0.07, 10.0)
    box('pennant paper', (4.9, dy + 5.9, 9.3), (0.02, 1.7, 0.9))
    # the gate at the camera end
    for x in (-4.6, 4.6):
        cyl('gate post iron %d' % x, (x, 0, 1.4), 0.12, 2.8)
        box('gate post cap iron', (x, 0, 2.85), (0.3, 0.3, 0.1))
    box('barrier bar timber', (-4.6 + 2.2, 0, 1.0 + 1.9), (5.2, 0.1, 0.12), rotation=(0, math.radians(-38), 0))
    box('barrier counterweight iron', (-4.6 + 0.3, 0, 1.0), (0.4, 0.3, 0.3))
    for side in (-1, 1):
        for i in range(10):
            x = side * (5.4 + i * 1.4)
            cyl('fence post timber', (x, 0, 0.9), 0.06, 1.8, v=8)
        for z in (0.4, 0.9, 1.4):
            box('fence wire iron', (side * 12.5, 0, z), (14.0, 0.02, 0.02))
        cyl('barbed wire coil iron', (side * 11, 0.2, 0.35), 0.35, 12.0, v=10, rot=(0, math.radians(90), 0))
    # sentry box and its sandbags
    box('sentry box wall timber', (-6.8, 1.6, 1.2), (1.4, 1.4, 2.4))
    box('sentry box roof slate', (-6.8, 1.6, 2.55), (1.8, 1.8, 0.12), rotation=(math.radians(8), 0, 0))
    box('sentry box window dim', (-6.1, 1.6, 1.5), (0.06, 0.8, 0.7))
    box('sentry box door wood', (-6.1, 0.9, 1.0), (0.06, 0.6, 1.9))
    for k in range(2):
        for j in range(7):
            box('sandbag earth', (-4.3 - k*0.0, 1.6 + j*0.55 - 1.4 + (0.27 if k else 0), 0.15 + k*0.28), (0.52, 0.5, 0.27), rotation=(0, 0, rng.uniform(-0.12, 0.12)))
    # foreground clutter along the bottom edge: crates, barrels, boards
    for i, (x, y) in enumerate(((2.2, -6.2), (2.9, -5.5), (2.4, -5.4), (-2.6, -5.0), (-3.3, -4.4))):
        box('crate wood', (x, y, 0.3 + (0.6 if i == 2 else 0)), (0.7, 0.7, 0.6), rotation=(0, 0, rng.uniform(-0.4, 0.4)))
    for x, y in ((-3.6, -3.4),):
        cyl('barrel wood', (x, y, 0.45), 0.3, 0.9, v=18)
    box('ammunition box wood', (1.0, -4.6, 0.15), (0.8, 0.4, 0.3), rotation=(0, 0, 0.3))
    box('plank wood', (-1.6, -3.2, 0.04), (0.25, 3.0, 0.05), rotation=(0, 0, 0.05))
    box('plank wood', (-1.3, -3.2, 0.04), (0.25, 2.6, 0.05), rotation=(0, 0, 0.03))
    plane('centre duckboard path planks', (-0.7, 40, 0.05), (1.3, 84))
    for yy in range(-8, 80, 3):
        box('duckboard batten wood', (-0.7, yy + 0.5, 0.03), (1.5, 0.12, 0.05))
    for k in range(3):
        for j in range(5):
            box('sandbag earth', (3.3 + k*0.0, -3.4 + j*0.54 + (0.27 if k == 1 else 0), 0.15 + k*0.27), (0.5, 0.52, 0.27), rotation=(0, 0, rng.uniform(-0.15, 0.15)))
    for x, y, r in ((1.0, -2.0, 0.3), (-2.4, -1.6, 0.45)):
        cyl('barbed wire coil iron', (x, y, 0.35), 0.45, 0.7, v=12)
    box('rifle rack timber', (-3.9, 0.2, 0.5), (0.1, 1.8, 1.0))
    for z in (0.2, 0.55, 0.9):
        box('ammunition box wood', (-2.3, -3.0, 0.15 + (z-0.2)*0.45), (0.5, 0.3, 0.3), rotation=(0,0,0.2))
    # a brazier with a fire, centre-right
    cyl('brazier iron', (1.4, 13.0, 0.45), 0.38, 0.9, v=14)
    for dx, dy2 in ((-0.3, -0.3), (0.3, -0.3), (0.3, 0.3), (-0.3, 0.3)):
        cyl('brazier leg iron', (1.4 + dx, 13.0 + dy2, 0.2), 0.03, 0.4, v=6)
    box('brazier fire flame', (1.4, 13.0, 1.05), (0.4, 0.4, 0.35), rotation=(0, 0, 0.5))
    # a field gun on the left, a truck on the right-centre
    gy = 28.0
    for dx in (-0.95, 0.95):
        cyl('gun wheel iron', (-2.6 + dx, gy, 0.6), 0.6, 0.12, v=24, rot=(0, math.radians(90), 0))
    cyl('gun barrel iron', (-2.6, gy + 1.6, 1.1), 0.09, 3.4, v=12, rot=(math.radians(84), 0, 0))
    box('gun shield iron', (-2.6, gy + 0.2, 1.1), (1.5, 0.05, 0.9))
    box('gun trail timber', (-2.6, gy - 1.6, 0.4), (0.15, 3.0, 0.15), rotation=(math.radians(-6), 0, 0))
    ty = 44.0
    box('truck bed wood', (2.4, ty - 1.5, 1.35), (2.1, 3.4, 0.2))
    for s in (-1, 1):
        box('truck side board wood', (2.4 + s*1.0, ty - 1.5, 1.75), (0.08, 3.4, 0.6))
    box('truck back board wood', (2.4, ty - 3.2, 1.75), (2.1, 0.08, 0.6))
    box('truck cab iron', (2.4, ty + 0.9, 1.7), (2.0, 1.6, 1.8))
    box('truck bonnet iron', (2.4, ty + 2.2, 1.35), (1.8, 1.1, 1.0))
    box('truck windscreen window dark', (2.4, ty + 1.71, 2.1), (1.5, 0.05, 0.7))
    box('truck chassis iron', (2.4, ty, 0.85), (1.2, 7.0 - 1.0, 0.2))
    for wy in (ty - 2.3, ty + 1.5):
        for s in (-1, 1):
            cyl('truck wheel iron', (2.4 + s*1.0, wy, 0.55), 0.55, 0.3, v=24, rot=(0, math.radians(90), 0))
    # crates by the huts
    for y in (13.0, 30.0, 57.0):
        box('crate wood', (-5.0, y, 0.4), (0.8, 0.8, 0.8))
        box('crate wood', (-5.0, y + 0.8, 0.3), (0.7, 0.7, 0.6), rotation=(0, 0, 0.3))
    # lamps
    for side, y in ((-1, 3), (1, 17), (-1, 33), (1, 48), (-1, 62)):
        x = side * 4.6
        cyl('lamp post iron %d' % y, (x, y, 2.1), 0.07, 4.2)
        box('lamp glass %d' % y, (x, y, 4.45), (0.34, 0.34, 0.5))
        box('lamp cap iron %d' % y, (x, y, 4.78), (0.5, 0.5, 0.12))
    # water tower and the watch tower at the far end
    for dx, dy2 in ((-1.4, -1.4), (1.4, -1.4), (1.4, 1.4), (-1.4, 1.4)):
        cyl('water tower leg timber', (-7.5 + dx, 88 + dy2, 5.0), 0.18, 10.0, v=10)
    cyl('water tower tank iron', (-7.5, 88, 11.2), 2.2, 3.0, v=24)
    box('water tower roof iron', (-7.5, 88, 13.0), (4.8, 4.8, 0.2), rotation=(0, 0, 0.78))
    box('searchlight platform timber', (-7.5, 88, 9.8), (4.0, 4.0, 0.2))
    # end block across the camp, gap on the left so lines meet beside it
    box('end block wall brick', (6.0, 96, 4.0), (16.0, 6.0, 8.0))
    for p in (-1, 1):
        box('end block roof slate', (6.0 + p*4.2, 96, 8.9), (8.6, 6.4, 0.14), rotation=(0, p*math.radians(22), 0))
    for x in (0.5, 4.0, 7.5, 11.0):
        for z, r in ((2.2, 0), (5.4, 1)):
            kind = 'lit' if (x, r) in ((4.0, 1),) else ('dim' if (x, r) == (11.0, 0) else 'dark')
            box('end block window surround stone', (x, 92.96, z), (1.4, 0.08, 2.0))
            box('end block window ' + kind, (x, 92.92, z), (1.1, 0.06, 1.7))
    box('end block door wood', (7.5, 92.9, 1.3), (1.5, 0.1, 2.6))
    box('end block door step', (7.5, 92.3, 0.1), (2.4, 1.2, 0.2))
    # a mast
    cyl('radio mast iron', (-3.5, 90, 9), 0.08, 18.0, v=8)
    # camera
    cd = bpy.data.cameras.new('base camera'); cd.lens = 32; cd.sensor_width = 36
    cd.shift_y = -0.06
    cam = bpy.data.objects.new('base camera', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.4, -9.0, 1.65)
    cam.rotation_euler = (Vector((0.4, 60.0, 1.65)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    a = ap.parse_args(sys.argv[1:])
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
    print('saved', len(bpy.data.objects))
