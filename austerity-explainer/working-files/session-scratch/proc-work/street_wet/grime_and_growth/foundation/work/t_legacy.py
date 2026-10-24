import sys, json, os, time
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy, numpy as np
from apply import kit as wk, layer_template, chain as chain_module
from harness import legacy_stack
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
k = wk.Kit.load('pit_village_street')
k.prepare()
today, _ = draw('today')
stack = legacy_stack.LegacyStack(k)
stack.apply(pieces=True)
stack.look('rubbish')
k.set_state(0.85, 0.5)
print('STAGES', {n: c.keys() for n, c in k.chains.items() if c.stages and n in ('street_setts','pavement_flags','cottage_brick','cottage_brick_door_left','cast_iron')})
print('VERIFY0', k.verify())
base, t1 = draw('base')
print('BASE drawn', round(t1,1), 'pieces', stack.piece_count())
for key, slot in (('t_a', 'A'), ('t_b', 'B'), ('t_c', 'C')):
    k.register_layer(key, lambda key: layer_template.build_template(key), slot=slot, roles='all')
k.apply(layers=['t_a', 't_b', 't_c'])
print('CHAINS', {n: c.keys() for n, c in k.chains.items() if c.stages and n in ('street_setts','pavement_flags','cottage_brick','cottage_brick_door_left','cast_iron')})
print('VERIFY1', k.verify())
withk, t2 = draw('with_layers')
d = np.abs(withk - base)
res = dict(size=[W,H], max_diff=float(d.max()), mean_diff=float(d.mean()), dots_over_1_255=float((d.max(axis=2) > 1/255+1e-6).mean()), base_vs_today_mean=float(np.abs(base-today).mean()))
# remove layers in odd order and twice
for key in ('t_b', 't_a', 't_b', 't_c', 't_a'):
    k.remove(key)
print('VERIFY2', k.verify())
again, t3 = draw('after_layers_removed')
res['after_removal_max_diff'] = float(np.abs(again - base).max())
k.remove()
final, t4 = draw('after_remove_all')
res['after_remove_all_vs_today_max_diff'] = float(np.abs(final - today).max())
print('LEGACY_IDENTITY', json.dumps(res))
json.dump(res, open(os.path.join(out, 'legacy_identity.json'), 'w'), indent=1)
