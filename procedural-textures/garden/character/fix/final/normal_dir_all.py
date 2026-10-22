"""normal_dir_all.py - TEST LIGHT for EVERY normal map picture of the SAVED combined scene (direction file, section 7, item 6; acceptance test 21).
   blender -b --disable-autoexec garden_character_fix.blend -P normal_dir_all.py -- JOB.json
JOB.json = {"json": "/abs/out.json", "tmp": "/abs/tmpfolder"}
What it does: for each image that a Normal Map node reads (taken from the saved scene, the packed copy that really renders), a flat grey plane with default
UVs (u = +X, v = +Y), the Normal Map node (Tangent) reading that image at strength 1, camera straight down (ortho, image up = +Y), a low sun (30 degrees up)
from +X and then from +Y, Cycles (CPU, 32 samples, no denoise), float EXR. Correlation between the fine luminance (picture minus its blur) and the fine part
of the decoded normal: red channel for the sun from +X (a face tilted towards the sun is lit), green channel for the sun from +Y. Limit: at least +0.25 for
both. The same render with the green channel flipped must give a NEGATIVE value for +Y, so the test can fail (one control per picture)."""
import sys
import os
import json
import math
import numpy as np
import bpy
from mathutils import Vector

job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
os.makedirs(job['tmp'], exist_ok=True)


def box_blur(a, r):
    k = 2 * r + 1
    c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0)), mode='reflect'), axis=0)
    a = (c[k:] - c[:-k]) / k
    c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r)), mode='reflect'), axis=1)
    return (c[:, k:] - c[:, :-k]) / k


def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = math.sqrt(float((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / d) if d > 0 else 0.0


# images used by Normal Map nodes
used = {}
for m in bpy.data.materials:
    if m.node_tree is None:
        continue
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeNormalMap':
            for l in m.node_tree.links:
                if l.to_node == n and l.to_socket.identifier == 'Color' and l.from_node.bl_idname == 'ShaderNodeTexImage' and l.from_node.image is not None:
                    used.setdefault(l.from_node.image.name, []).append(m.name)
imgs = sorted(used)
if job.get('only'):
    imgs = [i for i in imgs if i in job['only']]
print('NORMAL_DIR images', len(imgs), flush=True)

sc = bpy.data.scenes.new('NT')
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 32
sc.cycles.use_denoising = False
sc.cycles.use_adaptive_sampling = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.media_type = 'IMAGE'
sc.render.image_settings.file_format = 'OPEN_EXR'
sc.render.image_settings.color_depth = '32'
sc.render.image_settings.color_mode = 'RGB'
sc.world = bpy.data.worlds.new('NTW')
sc.world.color = (0, 0, 0)
cam_d = bpy.data.cameras.new('NTC')
cam_d.type = 'ORTHO'
cam = bpy.data.objects.new('NTC', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = (0, 0, 5)
sun_d = bpy.data.lights.new('NTS', 'SUN')
sun_d.energy = 4.0
sun = bpy.data.objects.new('NTS', sun_d)
sc.collection.objects.link(sun)
mesh = bpy.data.meshes.new('NTP')
mesh.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
mesh.uv_layers.new(name='UVMap')
mesh.uv_layers[0].data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
plane = bpy.data.objects.new('NTP', mesh)
sc.collection.objects.link(plane)

results = {}
for name in imgs:
    im = bpy.data.images[name]
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[..., :3]          # rows from the BOTTOM (v = 0 first)
    f = max(1, int(max(w, h) // 1024))
    rw, rh = w // f, h // f
    plane.scale = (1.0, h / w, 1.0)
    cam_d.ortho_scale = 2.0 * max(1.0, h / w)   # larger side of the plane: width 2 (landscape) or 2 h/w (portrait)
    sc.render.resolution_x, sc.render.resolution_y = rw, rh
    # downsample the decoded normal by f (area average) so the two pictures align pixel by pixel
    nx = (a[..., 0] * 2 - 1)
    ny = (a[..., 1] * 2 - 1)
    nx = nx[:rh * f, :rw * f].reshape(rh, f, rw, f).mean(axis=(1, 3))
    ny = ny[:rh * f, :rw * f].reshape(rh, f, rw, f).mean(axis=(1, 3))
    res = {'size': [w, h], 'render': [rw, rh], 'materials': used[name][:6]}
    for flip in (False, True):
        mat = bpy.data.materials.new('NTM')
        mat.use_nodes = True
        nt = mat.node_tree
        bs = nt.nodes['Principled BSDF']
        bs.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
        bs.inputs['Roughness'].default_value = 1.0
        tx = nt.nodes.new('ShaderNodeTexImage')
        tx.image = im
        tx.interpolation = 'Linear'
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.space = 'TANGENT'
        nm.uv_map = 'UVMap'
        nm.inputs['Strength'].default_value = 1.0
        src = tx.outputs['Color']
        if flip:
            sep = nt.nodes.new('ShaderNodeSeparateColor')
            com = nt.nodes.new('ShaderNodeCombineColor')
            inv = nt.nodes.new('ShaderNodeMath')
            inv.operation = 'SUBTRACT'
            inv.inputs[0].default_value = 1.0
            nt.links.new(src, sep.inputs['Color'])
            nt.links.new(sep.outputs['Red'], com.inputs['Red'])
            nt.links.new(sep.outputs['Green'], inv.inputs[1])
            nt.links.new(inv.outputs['Value'], com.inputs['Green'])
            nt.links.new(sep.outputs['Blue'], com.inputs['Blue'])
            src = com.outputs['Color']
        nt.links.new(src, nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
        mesh.materials.clear()
        mesh.materials.append(mat)
        for az_name, az, ref in (('from+X', 0.0, nx), ('from+Y', 90.0, ny)):
            if flip and az_name == 'from+X':
                continue
            el = math.radians(float(job.get('el_deg', 30.0)))
            d = Vector((-math.cos(math.radians(az)) * math.cos(el), -math.sin(math.radians(az)) * math.cos(el), -math.sin(el)))
            sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            p = os.path.join(job['tmp'], 'nd.exr')
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True, scene='NT')
            im2 = bpy.data.images.load(p)
            im2.colorspace_settings.name = 'Non-Color'
            b = np.empty(rw * rh * 4, np.float32)
            im2.pixels.foreach_get(b)
            bpy.data.images.remove(im2)
            lum = b.reshape(rh, rw, 4)[..., :3].mean(axis=2)
            r = max(3, min(rw, rh) // 64)
            fine_l = lum - box_blur(lum, r)
            ref_f = ref - box_blur(ref, r)
            key = ('flipped_' if flip else '') + az_name
            res[key] = round(corr(fine_l, ref_f), 3)
        bpy.data.materials.remove(mat)
    res['pass'] = bool(res['from+X'] >= 0.25 and res['from+Y'] >= 0.25 and res['flipped_from+Y'] < 0.0)
    results[name] = res
    print('NORMAL_DIR', name, json.dumps(res), flush=True)
    try:
        os.remove(os.path.join(job['tmp'], 'nd.exr'))
    except Exception:
        pass
out = {'images': results, 'all_pass': all(v['pass'] for v in results.values()), 'failed': [k for k, v in results.items() if not v['pass']]}
json.dump(out, open(job['json'], 'w'), indent=1)
print('NORMAL_DIR_DONE all_pass', out['all_pass'], 'failed', out['failed'], flush=True)
