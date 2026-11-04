"""Military camp at dusk. Run: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png"""
import sys, math, os, random
W, H, SAMPLES, OUT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
FOLDER = '/home/claude/build-51-military/kit'
sys.path.insert(0, FOLDER + '/store/tools')
import bpy, bmesh
import numpy as np
from mathutils import Vector, noise
import store, lay_walkway, puddle, lay_boards

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- ground ----------
def rut(x, cx, w):
    return math.exp(-((x - cx) / w) ** 2)
def ground_h(x, y):
    n = noise.noise(Vector((x * 0.35, y * 0.35, 1.3))) * 0.10 + noise.noise(Vector((x * 1.8, y * 1.8, 4.1))) * 0.025
    r = -0.08 * (rut(x, 2.4, 0.22) + rut(x, 3.7, 0.22)) * (1 if y > 0 else 1)
    r += -0.06 * (rut(x, -2.6, 0.2))
    # mounds near walkway edge
    return n + r

me = bpy.data.meshes.new('ground')
bm = bmesh.new()
nx, ny = 150, 260
xs = np.concatenate([np.linspace(-60, -12, 30), np.linspace(-12, 12, 90), np.linspace(12, 60, 30)])
ys = np.concatenate([np.linspace(-8, 10, 70), np.linspace(10, 40, 70), np.linspace(40, 140, 30)])
verts = [[bm.verts.new((x, y, ground_h(x, y))) for x in xs] for y in ys]
for j in range(len(ys) - 1):
    for i in range(len(xs) - 1):
        bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
bm.to_mesh(me); bm.free()
ground = bpy.data.objects.new('ground', me)
scene.collection.objects.link(ground)
for p in me.polygons: p.use_smooth = True

mud = store.material('SURFACE • mud_forest').copy()
mud.name = 'camp mud'
wn = mud.node_tree.nodes['Weather']
try: mud.node_tree.nodes['Picture size'].inputs['Scale'].default_value = float(os.environ.get('MSCALE','0.6'))
except Exception as e: print('scale', e)
for k, v in (('Wet', 0.6), ('Grime', 0.4), ('Bump', 0.6), ('Roughness', 0.7)):
    try: wn.inputs[k].default_value = v
    except Exception as e: print('dial', k, e)
wn.inputs['Color'].default_value = (0.5, 0.52, 0.62, 1)
store.use_material(ground, mud, ground=0.0)

# ---------- things ----------
parts = []
def part(name, loc, turn=0, seed=0, **kw):
    z = ground_h(loc[0], loc[1]) if len(loc) == 2 else loc[2]
    r = store.add_part(name, location=(loc[0], loc[1], z), turn=turn, seed=seed, **kw)
    parts.append(r); return r

# hut on left, door side facing the walkway
hut = part('timber_hut', (-6.4, 16), turn=90, seed=3, length=14, width=5.5, windows_per_side=4, lit_windows=True, door_open=False)
# bell tents on right
part('bell_tent', (7.4, 15.0), turn=-35, seed=2)
part('bell_tent', (9.5, 27), turn=-10, seed=5, door_open=False)
# the gun, hero, muzzle toward camera-left
part('field_gun', (2.9, 7.4), turn=-48, seed=2, elevation=6)
part('shell_box', (1.45, 6.4), turn=20, seed=1)
part('shell_box', (1.2, 7.3), turn=-15, seed=4, count=4)
# foreground left
part('sandbag_wall', (-1.75, 3.4), turn=86, seed=2, length=3.0, courses=4)
part('shell_box', (-0.8, 0.9), turn=30, seed=11, count=5)
part('crate', (-1.05, 1.9), turn=-14, seed=12)
part('sandbag_wall', (-2.2, 6.0), turn=20, seed=6, length=2.2, courses=3)
part('hurricane_lantern', (-1.05, 1.9, ground_h(-1.05, 1.9) + 0.38), seed=5)
part('barbed_wire_coil', (-1.6, 5.2), turn=88, seed=1, length=2.6)
part('barrel', (-4.4, 11.0), seed=1)
part('barrel', (-4.6, 12.2), seed=2, lying=True)
cr = part('crate', (1.9, 2.4), turn=12, seed=3)
part('crate', (2.7, 2.9), turn=-20, seed=5, size=(0.7, 0.4, 0.34))
part('crate', (2.65, 2.95, ground_h(2.7, 2.9) + 0.34), turn=15, seed=6, size=(0.6, 0.4, 0.3))
part('shell_box', (3.2, 4.5), turn=-30, seed=7, count=5)
part('sandbag_wall', (4.6, 10.0), turn=105, seed=9, length=3.2, courses=3)
lan = part('hurricane_lantern', (1.9, 2.4, ground_h(1.9, 2.4) + 0.38), seed=2)
part('barbed_wire_fence', (2.4, 17), turn=88, seed=2, length=14)
part('barbed_wire_fence', (-3.0, 30), turn=92, seed=3, length=12)
part('watch_tower', (3.5, 52), seed=1, height=9)
part('hurricane_lantern', (-4.3, 12.0, 0.55), seed=3)   # by hut step


# bucket left by the gunners beside the track
bm2 = bmesh.new()
bmesh.ops.create_cone(bm2, cap_ends=False, cap_tris=False, segments=20, radius1=0.11, radius2=0.15, depth=0.28)
bmesh.ops.translate(bm2, verts=bm2.verts, vec=(0, 0, 0.14))
bb = bmesh.ops.create_circle(bm2, cap_ends=True, radius=0.11, segments=20)
me2 = bpy.data.meshes.new('bucket'); bm2.to_mesh(me2); bm2.free()
bk = bpy.data.objects.new('bucket', me2); scene.collection.objects.link(bk)
bk.location = (-0.85, 2.3, ground_h(-0.85, 2.3)); [setattr(p, 'use_smooth', True) for p in me2.polygons]
gal = bpy.data.materials.new('galvanised'); gal.use_nodes = True
gp_ = gal.node_tree.nodes['Principled BSDF']; gp_.inputs['Base Color'].default_value = (0.16, 0.17, 0.18, 1); gp_.inputs['Metallic'].default_value = 0.9; gp_.inputs['Roughness'].default_value = 0.45
me2.materials.append(gal)
bpy.ops.mesh.primitive_torus_add(major_radius=0.14, minor_radius=0.006, location=(-0.85, 2.3, bk.location.z + 0.32)); hd = bpy.context.object
hd.rotation_euler = (math.radians(70), 0, 0); hd.data.materials.append(gal); hd.scale = (1, 1, 1)
part('barrel', (-1.9, 2.9), seed=4)

# walkway
line = [(0.5, -1.8, ground_h(0.5, -1.8)), (0.3, 0.5, ground_h(0.3, 0.5)), (0.0, 7, ground_h(0, 7)), (-0.6, 15, ground_h(-0.6, 15)), (-0.2, 25, ground_h(-0.2, 25)), (0.6, 38, ground_h(0.6, 38))]
lay_walkway.lay(line, width=0.95, ground=ground, wear=0.8, wet=0.7, mud_at_ends=0.8, missing=0.04, seed=4)


# telegraph poles with wires, along the left of the track
iron = bpy.data.materials.new('wire iron'); iron.use_nodes = True
pb = iron.node_tree.nodes['Principled BSDF']; pb.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1); pb.inputs['Metallic'].default_value = 0.8; pb.inputs['Roughness'].default_value = 0.5
bark = store.material('MADE • wet bark')
pole_pos = [(-1.9, 5.0), (-2.4, 13.0), (-2.5, 22.0), (-2.0, 33.0), (-1.4, 47.0)]
tops = []
for (px, py) in pole_pos:
    gz = ground_h(px, py); h = 6.8
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=h, vertices=10, location=(px, py, gz + h / 2 - 0.2))
    p = bpy.context.object; p.name = 'pole'; p.data.materials.append(bark)
    p.rotation_euler = (random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(px, py, gz + h - 0.5)); arm = bpy.context.object; arm.scale = (1.5, 0.08, 0.1); arm.name = 'crossarm'; arm.data.materials.append(bark)
    tops.append((px, py, gz + h - 0.5))
for dx in (-0.6, 0.0, 0.6):
    for a, b in zip(tops[:-1], tops[1:]):
        cu = bpy.data.curves.new('wire', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006; cu.bevel_resolution = 1
        sp = cu.splines.new('POLY'); n = 14; sp.points.add(n)
        for i in range(n + 1):
            t = i / n; x = a[0] + (b[0] - a[0]) * t + dx; y = a[1] + (b[1] - a[1]) * t
            z = a[2] + (b[2] - a[2]) * t - 0.9 * 4 * t * (1 - t) * (1 + (b[1] - a[1]) / 40)
            sp.points[i].co = (x, y, z, 1)
        ob = bpy.data.objects.new('wire', cu); scene.collection.objects.link(ob); cu.materials.append(iron)

lay_walkway.lay([(0.0, 12.2, ground_h(0.0, 12.2)), (-1.6, 12.8, ground_h(-1.6, 12.8)), (-3.2, 13.0, ground_h(-3.2, 13.0))], width=0.7, ground=ground, wear=0.8, wet=0.6, mud_at_ends=0.6, missing=0.0, seed=9, section_length=1.6)
WATER = store.material('MADE • puddle water').copy(); WATER.name = 'camp puddle water'
for n in WATER.node_tree.nodes:
    if n.type == 'MIX' and n.data_type == 'RGBA':
        n.inputs[6].default_value = (0.02, 0.032, 0.045, 1); n.inputs[7].default_value = (0.07, 0.06, 0.045, 1)

# mud banks heaped along the hut's foot (spade work: drains cut round it)
def mud_bank(p0, p1, width=0.55, height=0.22, seed=0):
    rnd = random.Random(seed); bmm = bmesh.new()
    n = int(math.dist(p0, p1) / 0.25); m = 5
    grid = []
    for i in range(n + 1):
        t = i / n; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
        dx, dy = (p1[0] - p0[0]), (p1[1] - p0[1]); L = math.hypot(dx, dy); nx_, ny_ = -dy / L, dx / L
        row = []
        for j in range(m + 1):
            u = j / m * 2 - 1
            h = height * (1 - u * u) ** 0.8 * (0.75 + 0.5 * noise.noise(Vector((x * 1.7, y * 1.7, seed))))
            px_, py_ = x + nx_ * u * width, y + ny_ * u * width
            row.append(bmm.verts.new((px_, py_, ground_h(px_, py_) + h - 0.03)))
        grid.append(row)
    for i in range(n):
        for j in range(m):
            bmm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    mm = bpy.data.meshes.new('mud bank'); bmm.to_mesh(mm); bmm.free()
    for p in mm.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('mud bank', mm); scene.collection.objects.link(ob)
    store.use_material(ob, mud, ground=0.0); return ob
mud_bank((-3.45, 9.2), (-3.45, 22.8), seed=1)
mud_bank((-8.9, 8.7), (-3.5, 8.7), seed=2)

# puddles in the ruts and the track
for loc, size, turn, seed in [((3.3, 3.4), (3.4, 0.7), 92, 1), ((2.7, 13), (6.0, 0.7), 92, 2), ((-1.5, 4.5), (6.0, 1.1), 88, 3),
                              ((1.3, 21), (4.0, 0.8), 88, 4), ((1.9, -0.6), (3.0, 1.0), 100, 7), ((-2.2, 10.2), (3.0, 0.8), 80, 8), ((4.2, 8.5), (3.0, 0.8), 85, 9)]:
    puddle.make((loc[0], loc[1], ground_h(*loc)), size=size, turn=turn, ground=ground, seed=seed, water_material=WATER)

store.prepare_for_render(scene)

# ---------- world, sun, haze ----------
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeNewGeometry'); vn = nt.nodes.new('ShaderNodeVectorMath'); vn.operation = 'NORMALIZE'; nt.links.new(tc.outputs['Position'], vn.inputs[0]); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.02; mr.inputs['From Max'].default_value = 0.75
ramp = nt.nodes.new('ShaderNodeValToRGB')
stops = [(0.0, (2.2, 0.8, 0.28)), (0.04, (1.4, 0.55, 0.24)), (0.09, (0.8, 0.38, 0.22)), (0.15, (0.5, 0.28, 0.22)), (0.24, (0.38, 0.25, 0.25)),
         (0.36, (0.22, 0.22, 0.29)), (0.55, (0.07, 0.12, 0.18)), (1.0, (0.012, 0.035, 0.06))]
cr = ramp.color_ramp
cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1] + (1,)
cr.elements[1].position = stops[-1][0]; cr.elements[1].color = stops[-1][1] + (1,)
for p, c in stops[1:-1]:
    e = cr.elements.new(p); e.color = c + (1,)
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 6; nz.inputs['Roughness'].default_value = 0.6
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 1.0, 4.5)
nr = nt.nodes.new('ShaderNodeValToRGB'); nr.color_ramp.elements[0].position = 0.38; nr.color_ramp.elements[0].color = (0.25, 0.25, 0.3, 1); nr.color_ramp.elements[1].position = 0.62; nr.color_ramp.elements[1].color = (1, 1, 1, 1)
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
nt.links.new(vn.outputs[0], mp.inputs[0]); nt.links.new(mp.outputs[0], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], nr.inputs[0])
nt.links.new(ramp.outputs[0], mx.inputs[6]); nt.links.new(nr.outputs[0], mx.inputs[7])
bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = float(os.environ.get('SKY', '1.0'))
out = nt.nodes.new('ShaderNodeOutputWorld')
vol = nt.nodes.new('ShaderNodeVolumeScatter'); vol.inputs['Density'].default_value = 0.006
vol.inputs['Color'].default_value = (0.75, 0.82, 0.9, 1)
nt.links.new(vn.outputs[0], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
nt.links.new(mr.outputs[0], ramp.inputs[0]); nt.links.new(mx.outputs[2], bg.inputs['Color'])
nt.links.new(bg.outputs[0], out.inputs['Surface'])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 300, 100)); box = bpy.context.object; box.scale = (1200, 700, 300); box.name = 'haze box'
hm = bpy.data.materials.new('haze'); hm.use_nodes = True; hn = hm.node_tree.nodes; hn.clear()
gc = hn.new('ShaderNodeNewGeometry'); gs = hn.new('ShaderNodeSeparateXYZ'); gm = hn.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'
gm.inputs[1].default_value = -0.1
gp = hn.new('ShaderNodeMath'); gp.operation = 'EXPONENT'
gd = hn.new('ShaderNodeMath'); gd.operation = 'MULTIPLY'; gd.inputs[1].default_value = float(os.environ.get('HAZE', '0.003'))
hm.node_tree.links.new(gc.outputs['Position'], gs.inputs[0]); hm.node_tree.links.new(gs.outputs['Z'], gm.inputs[0])
hm.node_tree.links.new(gm.outputs[0], gp.inputs[0]); hm.node_tree.links.new(gp.outputs[0], gd.inputs[0])
pv = hn.new('ShaderNodeVolumeScatter'); hm.node_tree.links.new(gd.outputs[0], pv.inputs['Density']); pv.inputs['Color'].default_value = (0.7, 0.8, 0.95, 1)
ho = hn.new('ShaderNodeOutputMaterial'); hm.node_tree.links.new(pv.outputs[0], ho.inputs['Volume'])
box.data.materials.append(hm); box.visible_shadow = False
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = float(os.environ.get('SUN', '5.0')); sun.color = (1.0, 0.7, 0.45); sun.angle = math.radians(3)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so)
so.rotation_euler = (math.radians(-84), 0, math.radians(20))
fl = bpy.data.lights.new('fill', 'SUN'); fl.energy = float(os.environ.get('FILL', '0.7')); fl.color = (0.55, 0.7, 1.0); fl.angle = math.radians(20)
fo = bpy.data.objects.new('fill', fl); scene.collection.objects.link(fo); fo.rotation_euler = (math.radians(40), 0, math.radians(-30))
for o in scene.objects:
    if o.type == 'LIGHT' and 'lantern' in o.name:
        o.data.energy = float(os.environ.get('LAN', '150'))
for nm, loc, en in (('tent glow', (7.0, 14.6, 0.9), 300), ('door spill', (-3.6, 13.0, 1.6), 250), ('gun glow', (1.2, 5.0, 1.3), 120)):
    pl = bpy.data.lights.new(nm, 'POINT'); pl.energy = en; pl.color = (1.0, 0.6, 0.3); pl.shadow_soft_size = 0.3
    po = bpy.data.objects.new(nm, pl); scene.collection.objects.link(po); po.location = loc

# ---------- camera ----------
cam = bpy.data.cameras.new('cam'); cam.lens = 26; cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 28
co = bpy.data.objects.new('cam', cam); scene.collection.objects.link(co); scene.camera = co
co.location = (0.5, -3.2, 1.6)
tgt = Vector((-0.2, 20, -0.2))
d = tgt - co.location
co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# ---------- render ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.cycles.max_bounces = 6; scene.cycles.volume_bounces = 1
scene.cycles.sample_clamp_indirect = 8
scene.render.resolution_x = W; scene.render.resolution_y = H; scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Filmic' if 'Filmic' in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items.keys() else 'AgX'
scene.view_settings.look = 'None'
scene.view_settings.exposure = float(os.environ.get('EXPO', '0.0'))
raw = OUT.replace('.png', '_raw.exr')
scene.render.image_settings.file_format = 'OPEN_EXR'; scene.render.image_settings.color_depth = '32'
scene.render.filepath = raw
bpy.ops.render.render(write_still=True)
import finish
finish.finish(raw, OUT, exposure=float(os.environ.get('EXPO2', '1.0')), bloom=1.0, soften=0.4)
print('done', OUT)
