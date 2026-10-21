import sys, json, os, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy, numpy as np
from apply import kit as wk, layer_template
args = sys.argv[sys.argv.index('--')+1:]
out, W, H, S = args[0], int(args[1]), int(args[2]), int(args[3])
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
def draw(name):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
    scene.eevee.taa_render_samples = S
    scene.eevee.use_raytracing = True
    scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
    p = os.path.join(out, name + '.png'); scene.render.filepath = p
    t = time.time(); bpy.ops.render.render(write_still=True); sec = time.time() - t
    img = bpy.data.images.load(p); img.colorspace_settings.name = 'Non-Color'
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[..., :3]
    bpy.data.images.remove(img)
    return a, sec
base, t0 = draw('base')
k = wk.Kit.load('pit_village_street')
k.prepare()
for key, slot in (('t_a', 'A'), ('t_b', 'B'), ('t_c', 'C')):
    k.register_layer(key, lambda key: layer_template.build_template(key), slot=slot, roles='all')
k.apply(layers=['t_a', 't_b', 't_c'])
withk, t1 = draw('with_layers')
d = np.abs(withk - base)
res = dict(size=[W, H], samples=S, dots=int(d.shape[0]*d.shape[1]), max_diff=float(d.max()), mean_diff=float(d.mean()), dots_over_1_255=float((d.max(axis=2) > 1/255+1e-6).mean()),
           seconds_base=round(t0, 2), seconds_with=round(t1, 2), hooked=len(k.hookable()))
# demo > 0 changes things (the layers are really in the material)
k.set_dials('t_b', demo=1.0)
demo, t2 = draw('demo')
res['demo_mean_diff'] = float(np.abs(demo - base).mean())
k.remove()
after, t3 = draw('after_remove')
res['after_remove_max_diff'] = float(np.abs(after - base).max())
print('IDENTITY', json.dumps(res))
json.dump(res, open(os.path.join(out, 'identity.json'), 'w'), indent=1)
