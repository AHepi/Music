import bpy
for name in ('left_row_a_cottage_04_glass_upper_1', 'right_row_a_cottage_04_glass_upper_0', 'left_row_a_cottage_02_glass_upper_1'):
    o = bpy.data.objects.get(name)
    print('PROBE', name, o and [(s.link, s.material.name if s.material else None) for s in o.material_slots], o and o.data.name, o and o.type)
m = bpy.data.materials.get('window_dim_glow_1')
print('PROBE dim', m and [(n.name, [(i.name, i.default_value) for i in n.inputs if i.name in ('Emission Strength', 'Strength')]) for n in m.node_tree.nodes])
m = bpy.data.materials.get('window_lit_glow_1')
print('PROBE lit', m and [(n.type, n.name) for n in m.node_tree.nodes])
