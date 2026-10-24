import bpy
out = {}
for m in bpy.data.materials:
    if m.node_tree is None: continue
    b = m.node_tree.nodes.get('Principled BSDF')
    out[m.name] = {'base': [round(c, 3) for c in b.inputs['Base Color'].default_value], 'linked': b.inputs['Base Color'].is_linked,
                   'nodes': [n.bl_idname for n in m.node_tree.nodes]}
o = bpy.data.objects.get('crates-sacking')
out['sack_attrs'] = list(o.data.attributes.keys()) if o else None
out['colattr'] = {ob.name: list(ob.data.color_attributes.keys()) for ob in bpy.data.objects if ob.type == 'MESH'}
result = out
