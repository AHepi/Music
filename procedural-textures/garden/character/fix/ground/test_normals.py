"""GROUND builder: TEST LIGHT for the four normal maps (direction test 21). Runs in Blender (CPU Cycles, a few seconds per picture):
   blender -b --factory-startup --python test_normals.py -- OUT.json
For each map: a flat plane (default UVs, u = +X, v = +Y, the whole map once over the plane), the same Image (Non-Color) -> Normal Map (Tangent,
strength as in the real material) -> Principled chain, a low sun (30 degrees) from +X and then from +Y, camera straight down. The fine luminance
(picture minus its blurred copy) is correlated with the slope that faces the sun, taken from the HEIGHT picture the map was made from:
sun from +X: -d(height)/dx ; sun from +Y: -d(height)/dy. PASS needs a correlation of at least +0.25 for both suns."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/ground'
sys.path.insert(0, HERE)
import normal_tools as NT

MAPS = os.path.join(HERE, 'maps')
CASES = [('ground', 'ground_normal.png', 'ground_height.png', 1.0), ('moss', 'moss_normal.png', 'moss_height.png', 0.45),
         ('pebble', 'pebble_normal.png', 'pebble_height.png', 1.0), ('stone', 'stone_normal.png', 'stone_height.png', 1.0)]
SIZE = 256


def load_gray(path, size):
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.zeros(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1, :, 0]               # rows top to bottom
    bpy.data.images.remove(img)
    k = w // size
    return a.reshape(size, k, size, k).mean(axis=(1, 3))


def blur(a, s):
    n0, n1 = a.shape
    fy = np.fft.fftfreq(n0)[:, None]
    fx = np.fft.fftfreq(n1)[None, :]
    return np.fft.ifft2(np.fft.fft2(a) * np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))).real


def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def main():
    out_path = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'normal_test.json')
    res = {}
    res['direction_line'] = NT.check_direction(verbose=True)['line']
    for name, nfile, hfile, strength in CASES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 32
        sc.cycles.use_denoising = False
        sc.render.resolution_x = sc.render.resolution_y = SIZE
        sc.view_settings.view_transform = 'Standard'
        sc.world = bpy.data.worlds.new('W')
        sc.world.color = (0, 0, 0)
        bpy.ops.mesh.primitive_plane_add(size=2.0)
        plane = bpy.context.active_object
        mat = bpy.data.materials.new('m')
        mat.use_nodes = True
        bs = mat.node_tree.nodes['Principled BSDF']
        bs.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
        bs.inputs['Roughness'].default_value = 1.0
        plane.data.materials.append(mat)
        img = bpy.data.images.load(os.path.join(MAPS, nfile), check_existing=False)
        img.colorspace_settings.name = 'Non-Color'
        nt = mat.node_tree
        uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = plane.data.uv_layers[0].name
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Cubic'; tx.extension = 'REPEAT'
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'; nm.uv_map = plane.data.uv_layers[0].name; nm.inputs['Strength'].default_value = strength
        nt.links.new(uv.outputs['UV'], tx.inputs['Vector'])
        nt.links.new(tx.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
        cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 2.0
        cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
        cam.location = (0, 0, 5)
        sd = bpy.data.lights.new('S', 'SUN'); sd.energy = 4.0
        sun = bpy.data.objects.new('S', sd); sc.collection.objects.link(sun)
        H = load_gray(os.path.join(MAPS, hfile), SIZE)
        gy_row, gx = np.gradient(H, axis=0), np.gradient(H, axis=1)
        gy = -gy_row                                         # +y is up the picture
        r = {}
        for az_name, az in (('+X', 0.0), ('+Y', 90.0)):
            el = math.radians(30.0)
            d = Vector((-math.cos(math.radians(az)) * math.cos(el), -math.sin(math.radians(az)) * math.cos(el), -math.sin(el)))
            sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            p = os.path.join('/tmp', 'g6_nrm_%s_%s.png' % (name, az_name[1]))
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            a = bpy.data.images.load(p)
            px = np.array(a.pixels[:], dtype=np.float32).reshape(SIZE, SIZE, 4)[::-1, :, :3].mean(axis=2)   # rows top to bottom
            bpy.data.images.remove(a)
            os.remove(p)
            fine = px - blur(px, 4.0)
            slope = (-gx if az_name == '+X' else -gy)
            slope = slope - blur(slope, 4.0)
            r[az_name] = round(corr(fine, slope), 3)
        r['pass'] = bool(r['+X'] >= 0.25 and r['+Y'] >= 0.25)
        a = np.asarray(bpy.data.images.load(os.path.join(MAPS, nfile), check_existing=False).pixels[:], dtype=np.float32).reshape(-1, 4)
        r['mean_rgb'] = [round(float(a[:, i].mean()), 3) for i in range(3)]
        r['strength_in_material'] = strength
        res[name] = r
        print('NORMAL_MAP', name, r)
    json.dump(res, open(out_path, 'w'), indent=1)
    print('NORMAL_TEST_DONE', json.dumps(res))


main()
