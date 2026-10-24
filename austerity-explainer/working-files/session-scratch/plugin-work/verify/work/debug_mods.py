import bpy
for n in ['Coping near west stone 1','Prop crate','Gate near heel strap 1','Step 3','Wall far panel 1','Gate near board 1','Prop bollard 1']:
    o=bpy.data.objects[n]
    print('OBJ', n, o.get('place_role'), [ (m.name,m.type) for m in o.modifiers], 'verts', len(o.data.vertices), 'mats', [m.name if m else None for m in o.data.materials], 'pk_bevelled', o.get('pk_bevelled'))
