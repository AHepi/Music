import bpy
for name in ('Bamboo leaf colour',):
    m = bpy.data.materials[name]
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            print('EM', name, n.inputs['Emission Strength'].default_value, tuple(n.inputs['Emission Color'].default_value), bool(n.inputs['Emission Color'].links), bool(n.inputs['Emission Strength'].links))
    print([o.name for o in bpy.data.objects if any(s.material == m for s in o.material_slots)])
