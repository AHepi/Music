import sys, json, os, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy, numpy as np
from apply import kit as wk, layer_template, chain as chain_module
from harness import legacy_stack
W, H, S = 90, 160, 2
out = 'bis_out'; os.makedirs(out, exist_ok=True)
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
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p); img.colorspace_settings.name = 'Non-Color'
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[..., :3]
    bpy.data.images.remove(img)
    return a
k = wk.Kit.load('pit_village_street')
k.prepare()
stack = legacy_stack.LegacyStack(k)
stack.apply(pieces=False)
stack.look('joints')
k.set_state(0.85, 0.5)
base = draw('base')
for key, slot in (('t_a', 'A'), ('t_b', 'B'), ('t_c', 'C')):
    k.register_layer(key, lambda key: layer_template.build_template(key), slot=slot, roles='all')
res = {}
for key in ('t_a',):
    k.apply(layers=[key])
    a = draw(key)
    res[key] = (float(np.abs(a - base).max()), float(np.abs(a - base).mean()))
    k.remove(key)
    k.registry[key].tree = None  # force rebuild of group next time (not needed)
    again = draw(key + '_removed')
    res[key + '_removed'] = float(np.abs(again - base).max())
print('BISECT', json.dumps(res))
