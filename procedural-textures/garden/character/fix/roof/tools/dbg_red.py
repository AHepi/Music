import bpy
name = p['mat']
for m in bpy.data.materials:
    if m.node_tree is None: continue
    b = [n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
    if not b: continue
    b = b[0]
    if m.name == name:
        for l in list(b.inputs['Base Color'].links): m.node_tree.links.remove(l)
        b.inputs['Base Color'].default_value = (1, 0, 0, 1)
        for l in list(b.inputs['Emission Color'].links): m.node_tree.links.remove(l)
        b.inputs['Emission Color'].default_value = (1, 0, 0, 1)
        b.inputs['Emission Strength'].default_value = 3.0
        print('DBGRED set', name, flush=True)
