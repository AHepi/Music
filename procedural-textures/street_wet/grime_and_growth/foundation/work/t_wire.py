import sys
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy
from apply import kit as wk, layer_template
from harness import legacy_stack
k = wk.Kit.load('pit_village_street')
k.prepare()
stack = legacy_stack.LegacyStack(k); stack.apply(pieces=False)
def dump(mat, node_names):
    t = bpy.data.materials[mat].node_tree
    for nn in node_names:
        n = t.nodes[nn]
        print('  NODE', nn)
        for i in n.inputs:
            if i.links:
                l = i.links[0]; print('     in', i.name, '<-', l.from_node.name, l.from_socket.name)
    p = next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED')
    for i in p.inputs:
        if i.links: print('  PLUG', i.name, '<-', i.links[0].from_node.name, i.links[0].from_socket.name)
print('BEFORE'); dump('street_setts', ['WETNESS'])
k.register_layer('t_a', lambda key: layer_template.build_template(key), slot='A', roles='all')
k.apply(layers=['t_a'])
print('AFTER'); dump('street_setts', ['WETNESS', 'WK t_a'])
ch = k.chains['street_setts']
st = ch.stage('wetness'); print('OWN', st.own, 'TAKES', st.takes)
