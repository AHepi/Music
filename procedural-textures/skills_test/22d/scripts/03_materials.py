# What this does: lists which node types each street material uses (picture files vs procedural), and the displacement settings of the road. Changes nothing.
import bpy
for m in bpy.data.materials:
    if not m.node_tree: continue
    types = sorted({n.bl_idname.replace('ShaderNode', '') for n in m.node_tree.nodes})
    imgs = [n.image.name for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    users = sum(1 for o in bpy.data.objects if o.type=='MESH' and m.name in [s.material.name for s in o.material_slots if s.material])
    disp = [n for n in m.node_tree.nodes if n.type == 'DISPLACEMENT']
    print('MAT', m.name, 'objs', users, 'images', len(imgs), 'nodes', len(m.node_tree.nodes), 'disp', len(disp), 'method', getattr(m, 'displacement_method', None), types if len(types) < 14 else str(len(types)) + ' types')
