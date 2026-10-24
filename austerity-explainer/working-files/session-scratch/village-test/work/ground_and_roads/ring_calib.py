# measures the mean display colour of each hill ring as the four cameras see it (each ring drawn alone), in sRGB 0..255 and in linear
import sys, bpy, numpy as np, os, json
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/ground_and_roads'
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 6; scene.cycles.use_denoising = False
scene.render.resolution_x = 600; scene.render.resolution_y = 400
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('Backdrop'): o.hide_render = True
rings = ['Backdrop near ring', 'Backdrop middle ring', 'Backdrop far ring']
res = {}
def srgb_to_lin(v):
    v = np.asarray(v, float)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
for ring in rings:
    for o in rings: bpy.data.objects[o].hide_render = (o != ring)
    acc = []
    for cam in ('View wide', 'View road_eye', 'View stable_close', 'View cottage_close'):
        scene.camera = bpy.data.objects[cam]
        p = f'{base}/rc_tmp.png'
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(p); w, h = img.size
        px = np.array(img.pixels[:]).reshape(h, w, 4)
        bpy.data.images.remove(img)
        m = px[..., 3] > 0.98
        if m.sum():
            acc.append((px[..., :3][m].mean(0), int(m.sum())))
    tot = sum(n for _, n in acc)
    mean_display = sum(c * n for c, n in acc) / tot          # these are display-encoded (sRGB) floats
    res[ring] = {'display_255': (mean_display * 255).round(1).tolist(), 'linear': srgb_to_lin(mean_display).round(4).tolist(), 'pixels': tot}
print('RINGCAL', json.dumps(res), flush=True)
os.remove(f'{base}/rc_tmp.png')
