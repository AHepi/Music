import sys, json, os, time
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy
from apply import kit as wk, layer_template, chain as chain_module, roles as R
k = wk.Kit.load('japanese_courtyard')
print(k.validation)
print('ROLES', k.role_map.counts())
print('UNASSIGNED', len(k.role_map.unassigned), k.role_map.unassigned)
print('TWO ROLES', R.two_roles_check(k.role_map))
print('meshes', sum(1 for o in bpy.context.scene.objects if o.type=='MESH'), 'assigned', len(k.role_map.primary))
n = k.prepare(policy=False)
print('HOOKABLE', n, 'SKIPPED', k.skipped, 'FORCED', k.forced)
for key, slot in (('t_a', 'A'), ('t_b', 'B'), ('t_c', 'C')):
    k.register_layer(key, lambda key: layer_template.build_template(key), slot=slot, roles='all')
before = {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree}
res = k.apply(layers=['t_a', 't_b', 't_c'])
print({key: len(v) for key, v in res.items()})
adapted = [n for n,(s,p,a,g) in k._snap.items() if a is not None]
plain = [n for n,(s,p,a,g) in k._snap.items() if a is None]
print('ADAPTED', len(adapted), 'PLAIN', len(plain))
print('VERIFY', k.verify()[:5])
k.remove()
after = {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree}
print('RESTORED_DIFF', [m for m in before if before[m] != after.get(m)])
