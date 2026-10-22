# Fresh-eyes direction test for every normal-map image in the combined scene (checker's own code).
# For each image: plane with UV 0..1, Image(Non-Color) -> Normal Map(Tangent, 'UVMap') -> Principled, low sun (30 deg) from +X and +Y, top orthographic camera.
# Correlate the fine detail of the lit picture with (red-0.5) under the +X sun and (green-0.5) under the +Y sun. A flipped-green control must fail.
import bpy, sys, json, math, os, numpy as np
BLEND = sys.argv[sys.argv.index('--') + 1]
OUT = sys.argv[sys.argv.index('--') + 2]
IMGS = [n for n in json.load(open(sys.argv[sys.argv.index('--') + 3]))]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(BLEND, link=False) as (src, dst):
    dst.images = [n for n in src.images if n in IMGS]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 6
sc.cycles.use_denoising = False
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Raw'
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'OPEN_EXR'
sc.render.image_settings.color_depth = '32'
w = bpy.data.worlds.new('w'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
sc.world = w
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
cam.location = (0, 0, 3); cam.rotation_euler = (0, 0, 0)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0
sun.data.angle = 0.0
me = bpy.data.meshes.new('plane')
me.from_pydata([(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new(name='UVMap')
for l, co in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
    uv.data[l.index].uv = co
ob = bpy.data.objects.new('plane', me); sc.collection.objects.link(ob)
mat = bpy.data.materials.new('m'); mat.use_nodes = True; ob.data.materials.append(mat)
nt = mat.node_tree

def build(img, mode, flip_g=False):
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'; tex.extension = 'EXTEND'
    img.colorspace_settings.name = 'Non-Color'
    if mode == 'lit':
        col = tex.outputs['Color']
        if flip_g:
            sep = nt.nodes.new('ShaderNodeSeparateColor'); comb = nt.nodes.new('ShaderNodeCombineColor')
            inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
            nt.links.new(tex.outputs['Color'], sep.inputs['Color'])
            nt.links.new(sep.outputs['Green'], inv.inputs[1])
            nt.links.new(sep.outputs['Red'], comb.inputs['Red']); nt.links.new(inv.outputs['Value'], comb.inputs['Green']); nt.links.new(sep.outputs['Blue'], comb.inputs['Blue'])
            col = comb.outputs['Color']
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'; nm.uv_map = 'UVMap'; nm.inputs['Strength'].default_value = 1.0
        pr = nt.nodes.new('ShaderNodeBsdfPrincipled'); pr.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1); pr.inputs['Roughness'].default_value = 1.0
        for nme in ('Specular IOR Level',):
            if nme in pr.inputs: pr.inputs[nme].default_value = 0.0
        nt.links.new(col, nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], pr.inputs['Normal'])
        nt.links.new(pr.outputs['BSDF'], out.inputs['Surface'])
    else:
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        comb = nt.nodes.new('ShaderNodeCombineColor')
        em = nt.nodes.new('ShaderNodeEmission')
        nt.links.new(tex.outputs['Color'], sep.inputs['Color'])
        ch = 'Red' if mode == 'R' else 'Green'
        for k in ('Red', 'Green', 'Blue'):
            nt.links.new(sep.outputs[ch], comb.inputs[k])
        nt.links.new(comb.outputs['Color'], em.inputs['Color'])
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])

def shoot(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path + '.exr' if not path.endswith('.exr') else path)
    n = im.size[0] * im.size[1] * 4
    px = np.empty(n, dtype=np.float32); im.pixels.foreach_get(px)
    a = px.reshape(im.size[1], im.size[0], 4)[::-1]  # row 0 = top
    bpy.data.images.remove(im)
    return a[..., :3].mean(axis=2)

def blur(a, s):
    k = int(s * 3) * 2 + 1
    x = np.arange(k) - k // 2
    g = np.exp(-x ** 2 / (2 * s * s)); g /= g.sum()
    b = np.apply_along_axis(lambda r: np.convolve(np.pad(r, k // 2, mode='edge'), g, mode='valid'), 1, a)
    b = np.apply_along_axis(lambda c: np.convolve(np.pad(c, k // 2, mode='edge'), g, mode='valid'), 0, b)
    return b

def corr(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = math.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0

def aim(sun_from):
    if sun_from == 'X': sun.rotation_euler = (0, math.radians(60), 0)
    else: sun.rotation_euler = (math.radians(-60), 0, 0)

res = {}
tmp = '/tmp/_nmdir_%d' % os.getpid()
os.makedirs(tmp, exist_ok=True)
for name in IMGS:
    img = bpy.data.images[name]
    W, H = img.size
    rr = max(W, H)
    scale = min(1.0, 1024 / rr)
    px_w, px_h = int(W * scale), int(H * scale)
    aspect = W / H
    ob.scale = (aspect, 1, 1)
    cam.data.ortho_scale = max(aspect, 1) * 1.0
    sc.render.resolution_x = px_w; sc.render.resolution_y = px_h; sc.render.resolution_percentage = 100
    if aspect < 1:
        cam.data.ortho_scale = 1.0 / 1.0 * 1.0
        cam.data.sensor_fit = 'VERTICAL'
    else:
        cam.data.sensor_fit = 'HORIZONTAL'
    if aspect < 1: ob.scale = (aspect, 1, 1)
    cam.data.ortho_scale = max(aspect, 1.0)
    cam.data.sensor_fit = 'AUTO'
    build(img, 'R'); R = shoot(tmp + '/r')
    build(img, 'G'); G = shoot(tmp + '/g')
    sig = max(2.0, px_w / 128)
    Rh = R - blur(R, sig * 2); Gh = G - blur(G, sig * 2)
    r = {'size': [W, H], 'render': [px_w, px_h]}
    build(img, 'lit'); aim('X'); LX = shoot(tmp + '/lx'); aim('Y'); LY = shoot(tmp + '/ly')
    LXh = LX - blur(LX, sig * 2); LYh = LY - blur(LY, sig * 2)
    r['corr_sunX_with_red'] = round(corr(LXh, Rh), 3)
    r['corr_sunY_with_green'] = round(corr(LYh, Gh), 3)
    r['corr_sunX_with_green_(should_be_~0)'] = round(corr(LXh, Gh), 3)
    r['corr_sunY_with_red_(should_be_~0)'] = round(corr(LYh, Rh), 3)
    build(img, 'lit', flip_g=True); aim('Y'); LYf = shoot(tmp + '/lyf'); LYfh = LYf - blur(LYf, sig * 2)
    r['control_green_flipped_corr_sunY_with_green'] = round(corr(LYfh, Gh), 3)
    r['lit_contrast_std_sunX'] = round(float(LXh.std()), 4)
    r['lit_mean_sunX'] = round(float(LX.mean()), 4)
    res[name] = r
    print(name, r, flush=True)
json.dump(res, open(OUT, 'w'), indent=1)
print('NM DIR DONE')
