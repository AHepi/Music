import sys
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
import bpy
import apply_weathering as aw
w = aw.apply('japanese_courtyard', 'mossy_courtyard_rough', state='dry')
for n in ('Hall roof', 'CT / Ceramic pan prototype'):
    o = bpy.data.objects[n]
    print('PROPS', n, {k: round(o[k], 3) for k in o.keys() if k.startswith('wk_') and isinstance(o[k], (int, float))})
    print('ROLE', n, w.kit.role_map.primary.get(n))
m = bpy.data.materials['CT / Ceramic painterly surface']
print('CHAIN', w.kit.chains.get(m.name) and w.kit.chains[m.name].keys())
print('SKIPPED', {k: v for k, v in w.kit.skipped.items() if 'CT' in k or 'Timber' in k})
print('MATERIALS of roles', w.kit.role_map.material_roles.get('CT / Ceramic painterly surface'), w.kit.role_map.material_roles.get('CT / Timber painterly surface'))
print('TREE nodes', [n.name for n in m.node_tree.nodes][:40])
w.remove()
