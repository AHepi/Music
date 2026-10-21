import sys, json, os, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy
from apply import kit as wk, layer_template, chain as chain_module
k = wk.Kit.load('pit_village_street')
print(k.validation)
print('ROLES', k.role_map.counts())
print('UNASSIGNED', len(k.role_map.unassigned), k.role_map.unassigned[:10])
print('ALSO', list(k.role_map.also.items())[:5])
n = k.prepare()
print('HOOKABLE', n, 'SKIPPED', k.skipped)
for key, slot in (('t_a', 'A'), ('t_b', 'B'), ('t_c', 'C')):
    k.register_layer(key, lambda key: layer_template.build_template(key), slot=slot, roles='all')
before = {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree}
res = k.apply(layers=['t_a', 't_b', 't_c'])
print({key: len(v) for key, v in res.items()})
print('VERIFY', k.verify()[:5])
print(k.report()['chains'].get('street_setts'))
k.remove()
after = {m.name: chain_module.graph_signature(m) for m in bpy.data.materials if m.node_tree}
diff = [m for m in before if before[m] != after.get(m)]
print('RESTORED_DIFF', diff)
