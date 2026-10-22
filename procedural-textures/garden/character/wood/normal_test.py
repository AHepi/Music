"""normal_test.py - TEST LIGHT for every normal map of the wood builder (direction file section 7 item 6).
For each map: a flat plane with the FINAL material (and a plain-grey control with the same Normal Map node), default UVs (u = +X, v = +Y, in metres),
a low sun (30 degrees up) from +X and then from +Y, camera straight down. Correlation of the fine luminance (picture minus its blur) with
-dh/dx (sun from +X) and with the slope towards +Y (sun from +Y), h = the height picture the map was made from. Must be >= +0.25.
   blender -b --disable-autoexec START.blend --python normal_test.py -- OUTDIR"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import bpy
import wood_mats as wm
import normal_tools

out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'work')
os.makedirs(out, exist_ok=True)
maps = os.path.join(HERE, 'maps')
plank_m = wm.make_plank_materials(maps)
post_m = wm.make_post_material(maps)
stone_m = wm.make_stone_material(maps)

def box_blur(a, r):
    k = 2 * r + 1
    c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0)), mode='wrap'), axis=0)
    a = (c[k:] - c[:-k]) / k
    c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r)), mode='wrap'), axis=1)
    return (c[:, k:] - c[:, :-k]) / k

def resample(h, w_out, h_out):
    H, W = h.shape
    fy, fx = H // h_out, W // w_out
    return h[:fy * h_out, :fx * w_out].reshape(h_out, fy, w_out, fx).mean(axis=(1, 3))

def control_material(name, image_path, scale):
    m = bpy.data.materials.new(name)
    nb = wm.NB(m)
    uv = nb.n('ShaderNodeUVMap', uv_map='UVMap'); mp = nb.n('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale
    nb.link(uv, 'UV', mp, 'Vector')
    img = wm.image_node(nb, wm.load_image(image_path), (0, 0), (mp, 'Vector'))
    nm = nb.n('ShaderNodeNormalMap', space='TANGENT', uv_map='UVMap'); nm.inputs['Strength'].default_value = 1.0
    nb.link(img, 'Color', nm, 'Color')
    b = nb.n('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1); b.inputs['Roughness'].default_value = 1.0
    nb.nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    o = nb.n('ShaderNodeOutputMaterial'); nb.nt.links.new(b.outputs['BSDF'], o.inputs['Surface'])
    return m

specs = [
    ('plank_top', plank_m['top'], 'plank_top_normal.png', (1.0, 0.25), (1, 4, 1), '_h_plank_top.npy', (1024, 256)),
    ('end_grain', plank_m['end'], 'end_grain_normal.png', (0.25, 0.25), (4, 4, 1), '_h_end_grain.npy', (512, 512)),
    ('post_timber', post_m, 'post_timber_normal.png', (0.28, 0.56), (1 / 0.28, 1 / 0.56, 1), '_h_post_timber.npy', (256, 512)),
    ('footing_stone', stone_m, 'footing_stone_normal.png', (1.0, 1.0), (1, 1, 1), '_h_footing_stone.npy', (512, 512)),
]
sc = bpy.data.scenes.new('NT')
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 48
sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
world = bpy.data.worlds.new('NTW'); world.use_nodes = False; world.color = (0, 0, 0); sc.world = world
results = []
sun_d = bpy.data.lights.new('NTS', 'SUN'); sun_d.energy = 3.0
sun = bpy.data.objects.new('NTS', sun_d); sc.collection.objects.link(sun)
cam_d = bpy.data.cameras.new('NTC'); cam_d.type = 'ORTHO'
cam = bpy.data.objects.new('NTC', cam_d); sc.collection.objects.link(cam); sc.camera = cam
for name, mat, mapfile, tile, scale, hfile, res in specs:
    h = np.load(os.path.join(maps, hfile)).astype(np.float32)
    h = resample(h, res[0], res[1])
    ctl = control_material('NTctl ' + name, os.path.join(maps, mapfile), scale)
    for label, m in (('final', mat), ('control', ctl)):
        me = bpy.data.meshes.new('NTp'); w, hh = tile
        me.from_pydata([(0, 0, 0), (w, 0, 0), (w, hh, 0), (0, hh, 0)], [], [(0, 1, 2, 3)])
        uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.array([0, 0, w, 0, w, hh, 0, hh], np.float32))
        me.materials.append(m)
        ob = bpy.data.objects.new('NTp', me); sc.collection.objects.link(ob)
        cam.location = (w / 2, hh / 2, 3.0); cam_d.ortho_scale = max(w, hh)
        sc.render.resolution_x, sc.render.resolution_y = res
        corr = {}
        for sname, az in (('+X', 0.0), ('+Y', 90.0)):
            el = math.radians(30.0)
            from mathutils import Vector
            d = Vector((-math.cos(math.radians(az)) * math.cos(el), -math.sin(math.radians(az)) * math.cos(el), -math.sin(el)))
            sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            path = os.path.join(out, 'nt_%s_%s_%s.png' % (name, label, sname[1]))
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True, scene='NT')
            img = bpy.data.images.load(path)
            px = np.array(img.pixels[:], np.float32).reshape(res[1], res[0], 4)[::-1, :, :3]   # row 0 = top
            bpy.data.images.remove(img)
            lum = px.mean(axis=2)
            fine = lum - box_blur(lum, 6)
            dh_dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
            dh_drow = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
            target = -dh_dx if sname == '+X' else dh_drow
            c = float(np.corrcoef(fine.ravel(), target.ravel())[0, 1])
            corr[sname] = round(c, 3)
            # also: lit side of a ridge is the side facing the light (mean luminance where the slope faces the sun vs away)
            sel_up = target > np.percentile(target, 90)
            sel_dn = target < np.percentile(target, 10)
            corr[sname + '_lit_vs_away'] = [round(float(lum[sel_up].mean()), 4), round(float(lum[sel_dn].mean()), 4)]
        bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
        ok = corr['+X'] >= 0.25 and corr['+Y'] >= 0.25
        r = dict(map=name, material=label, corr_sun_from_plusX=corr['+X'], corr_sun_from_plusY=corr['+Y'], lit_vs_away_X=corr['+X_lit_vs_away'], lit_vs_away_Y=corr['+Y_lit_vs_away'], result='PASS' if ok else 'FAIL')
        results.append(r)
        print('NORMALMAP_TEST', json.dumps(r), flush=True)
json.dump(results, open(os.path.join(out, 'normal_test.json'), 'w'), indent=1)
