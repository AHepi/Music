import sys
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy
from apply import kit as wk, layer_template
from masks import bus, debug
k = wk.Kit.load('pit_village_street')
bus.attach(k)
k.prepare()
k.register_layer('t_a', lambda key: layer_template.build_template(key), slot='A', roles='all')
k.apply(layers=['t_a'])
undo = debug.show_mask(k, 'shade')
g = bpy.data.node_groups['WK MASKS street_setts']
for n in g.nodes:
    ins = [(i.name, (i.links[0].from_node.name, i.links[0].from_socket.name) if i.links else (round(i.default_value,4) if hasattr(i,'default_value') and not hasattr(i.default_value,'__len__') else '-')) for i in n.inputs if i.enabled]
    extra = n.image.name if n.bl_idname=='ShaderNodeTexImage' and n.image else ''
    print('NODE', n.name, n.bl_idname, extra, ins)
