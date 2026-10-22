"""TEST LIGHT for the roof builder's four normal maps (direction test 21).
   blender -b --factory-startup --python test_normals.py -- OUT.json [render_px]
Plain words: prints the NORMAL_DIRECTION line of normal_tools (a bump must be lit on the side that faces the sun), then for each of my
four maps (tile glaze, plaster, stone, moss pillows) lights a flat plane that carries the map (Normal Map node, Tangent, the same
strength as in the garden materials) with a low sun (30 degrees) from +X and from +Y, and measures the correlation between the picture's
brightness and the slope the map is meant to show (-d height / dx for the sun from +X; -d height / dy for +Y, top of the picture = +V).
A flipped copy of every map is drawn too, to show that the test can fail. Pass = correlation >= +0.25 for both suns."""
import sys, os, json, math, tempfile
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof'
sys.path.insert(0, HERE)
import bpy, numpy as np
from mathutils import Vector
import normal_tools, r_maps

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
PX = int(argv[1]) if len(argv) > 1 else 384
res = {}
res['direction_line'] = normal_tools.check_direction()['line']
print(res['direction_line'])

MAPS = [('glaze', lambda: r_maps.glaze_height(1024, 11), 0.065, 0.55), ('plaster', lambda: r_maps.plaster_height(2048, 21), 0.045, 1.0),
        ('stone', lambda: r_maps.stone_height(1024, 31), 0.11, 0.8), ('moss', lambda: r_maps.moss_height(1024, 41), 0.28, 0.5)]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.render.resolution_x = sc.render.resolution_y = PX
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W')
sc.world.color = (0, 0, 0)
bpy.ops.mesh.primitive_plane_add(size=2.0)
plane = bpy.context.active_object
cd = bpy.data.cameras.new('C')
cd.type = 'ORTHO'
cd.ortho_scale = 2.0
cam = bpy.data.objects.new('C', cd)
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = (0, 0, 5)
sd = bpy.data.lights.new('S', 'SUN')
sd.energy = 4.0
sun = bpy.data.objects.new('S', sd)
sc.collection.objects.link(sun)
tmp = tempfile.mkdtemp(prefix='nt_')


def blockmean(a, n):
    f = a.shape[0] // n
    return a[:f * n, :f * n].reshape(n, f, n, f).mean(axis=(1, 3))


def render(img, strength, az):
    m = bpy.data.materials.new('m')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
    b.inputs['Roughness'].default_value = 1.0
    plane.data.materials.clear()
    plane.data.materials.append(m)
    if not plane.data.uv_layers:
        plane.data.uv_layers.new(name='UVMap')
    nm = normal_tools.add_normal_map_nodes(m, img, 'UVMap', strength)
    el = math.radians(30)
    d = Vector((-math.cos(math.radians(az)) * math.cos(el), -math.sin(math.radians(az)) * math.cos(el), -math.sin(el)))
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    p = os.path.join(tmp, 'r.png')
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    a = bpy.data.images.load(p)
    px = np.array(a.pixels[:], np.float32).reshape(PX, PX, 4)[..., :3].mean(axis=2)[::-1]      # rows top first
    bpy.data.images.remove(a)
    bpy.data.materials.remove(m)
    return px


rows = []
for name, hfn, target, strength in MAPS:
    h = hfn()
    n, s_used = r_maps.to_normal(h, target)
    hs = blockmean(h, PX) if h.shape[0] % PX == 0 else None
    if hs is None:
        idx = (np.arange(PX) * h.shape[0] / PX).astype(int)
        hs = h[idx][:, idx]
    hs = r_maps.blur(hs, 0.6)
    gx = -np.gradient(hs, axis=1)         # slope facing +X
    gy = np.gradient(hs, axis=0)          # slope facing +Y (rows go down)
    row = {'map': name, 'strength_in_material': strength, 'mean_slope_target': target}
    for flip in (False, True):
        nn = n.copy()
        if flip:
            nn[..., 1] *= -1
        img = normal_tools.make_normal_image('t_%s_%s' % (name, 'flip' if flip else 'ok'), nn)
        lx = render(img, strength, 0.0)
        ly = render(img, strength, 90.0)
        cx = float(np.corrcoef((lx - lx.mean()).ravel(), gx.ravel())[0, 1])
        cy = float(np.corrcoef((ly - ly.mean()).ravel(), gy.ravel())[0, 1])
        row['flipped' if flip else 'ok'] = {'corr_sun_from_+X': round(cx, 3), 'corr_sun_from_+Y': round(cy, 3)}
        bpy.data.images.remove(img)
    row['PASS'] = row['ok']['corr_sun_from_+X'] >= 0.25 and row['ok']['corr_sun_from_+Y'] >= 0.25
    row['flipped_Y_fails'] = row['flipped']['corr_sun_from_+Y'] < 0.25
    rows.append(row)
    print('NMAP', json.dumps(row))
res['maps'] = rows
res['all_pass'] = all(r['PASS'] for r in rows)
json.dump(res, open(out, 'w'), indent=1)
print('NORMAL_TESTS_DONE', res['direction_line'][:40], 'all_pass', res['all_pass'])
