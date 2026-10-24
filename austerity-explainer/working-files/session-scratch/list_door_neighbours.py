# What this does: lists the objects and materials around cottage 03's door in the street copy, and where each material's pictures come from (read only).
import bpy, mathutils
door = bpy.data.objects['right_row_a_cottage_03_door']
centre = door.matrix_world.translation
near = sorted((o for o in bpy.data.objects if o.type == 'MESH' and (o.matrix_world.translation - centre).length < 3.0),
              key=lambda o: (o.matrix_world.translation - centre).length)
seen = set()
for o in near[:14]:
    mats = [s.material.name for s in o.material_slots if s.material]
    print(f"{o.name:45s} {round((o.matrix_world.translation - centre).length, 2):5} m  {mats}")
    for m in mats:
        if m in seen: continue
        seen.add(m)
        mat = bpy.data.materials[m]
        imgs = sorted({n.image.filepath for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image} if mat.node_tree else set())
        print('     material', m, '| pictures:', [i.split('/')[-1] for i in imgs][:6] or 'none (made by nodes)')
