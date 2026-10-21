import bpy
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    if o.name.endswith('_walls') and 'cottage' in o.name:
        m=o.matrix_world
        print('OBJ', o.name, [round(v,2) for v in m.translation], [round(v,2) for v in o.dimensions], o.material_slots[0].material.name if o.material_slots else None)
