# What this does: draws one contact sheet of test plates: a 1 m cube per surface (top and two sides visible), built straight from the stage's material
# builders, lit by a neutral sun and sky so the colours can be judged. Runs on the RunPod worker:
#   blender -b --disable-autoexec --python render_plates.py -- OUT.png [W H samples]
import bpy, sys, os, math, time, json
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
W, H, SAMPLES = (int(args[1]), int(args[2]), int(args[3])) if len(args) >= 4 else (1800, 1100, 48)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stage_surfaces as ss
import surf_kit as K
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
opt = {'look': 'real', 'maps_dir': os.path.join(HERE, 'maps')}
PLATES = [  # (label, builder family, ctx, option overrides)
    ('ground', 'ground.earth', {}, {}), ('gravel', 'ground.gravel', {}, {}), ('rock', 'stone.rock', {'kind': 'rock'}, {}), ('pier', 'stone.pier', {'kind': 'pier'}, {}),
    ('step', 'stone.step', {'kind': 'step'}, {}), ('lantern', 'stone.lantern', {'kind': 'lantern'}, {}), ('plinth', 'stone.plinth', {}, {}),
    ('roof tile', 'roof.tile', {'part': 'roof.tile'}, {}), ('roof ridge', 'roof.ridge', {'part': 'roof.ridge'}, {}), ('wall cap', 'wall.cap', {}, {}),
    ('hall plaster', 'wall.hall', {}, {}), ('garden wall', 'wall.garden', {'z0': 0.0}, {}),
    ('hall post', 'timber.post', {'family': 'timber.post'}, {}), ('hall beam', 'timber.beam', {'family': 'timber.beam'}, {}),
    ('veranda plank', 'plank', {'run': 1, 'orig_rgb': (0.15, 0.1, 0.07)}, {}), ('bridge plank', 'plank', {'run': 4, 'orig_rgb': (0.15, 0.1, 0.07)}, {}),
    ('maple bark', 'bark.maple', {'family': 'bark.maple'}, {}), ('pine bark', 'bark.pine', {'family': 'bark.pine'}, {}),
    ('pebbles', 'pebbles', {'orig_rgb': (0.22, 0.2, 0.18)}, {}),
]
cols = 7
for i, (label, fam, ctx, over) in enumerate(PLATES):
    mat = bpy.data.materials.new('plate ' + label)
    o = dict(opt); o.update(over)
    ss.REAL_BUILDERS[fam](mat, o, dict({'family': fam}, **ctx))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=((i % cols) * 1.4, -(i // cols) * 1.4, 0.5))
    cube = bpy.context.active_object
    cube.name = 'plate ' + label
    cube.data.materials.append(mat)
cam = bpy.data.cameras.new('c'); cam.lens = 32
co = bpy.data.objects.new('c', cam); scene.collection.objects.link(co)
cx, cy = (cols - 1) * 0.7, -1.4
co.location = (cx, cy - 8.0, 7.0)
from mathutils import Vector
co.rotation_euler = (Vector((cx, cy, 0.3)) - Vector(co.location)).to_track_quat('-Z', 'Y').to_euler()
scene.camera = co
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 3.0; sun.angle = math.radians(2)
so = bpy.data.objects.new('s', sun); scene.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-35))
world = bpy.data.worlds.new('w'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.55, 0.62, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
scene.world = world
bpy.ops.mesh.primitive_plane_add(size=40, location=(cx, cy, 0))
fl = bpy.context.active_object
fm = bpy.data.materials.new('floor'); fm.diffuse_color = (0.35, 0.35, 0.35, 1); fm.use_nodes = True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1)
fl.data.materials.append(fm)
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
for d in prefs.devices: d.use = d.type == 'OPTIX'
scene.render.engine = 'CYCLES'; scene.cycles.device = 'GPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'AgX'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100
scene.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True)
print('PLATES DRAWN', round(time.time() - t, 1), 's')
from bpy_extras.object_utils import world_to_camera_view
lab = []
for ob in bpy.data.objects:
    if ob.name.startswith('plate '):
        v = world_to_camera_view(scene, co, ob.location + __import__('mathutils').Vector((0, 0, 0.6)))
        lab.append([ob.name[6:], round(v.x * W), round((1 - v.y) * H)])
json.dump(lab, open(out + '.labels.json', 'w'))
