import bpy
for nm in ('CT / Stone painterly surface.008', 'CT / Stone painterly surface.009'):
    m = bpy.data.materials[nm]
    print('MAT', nm, 'users', m.users, [o.name for o in bpy.data.objects if o.type=='MESH' and nm in [s.material.name for s in o.material_slots if s.material]])
    for n in m.node_tree.nodes:
        extra = ''
        if n.bl_idname == 'ShaderNodeGroup':
            extra = n.node_tree.name
        if n.bl_idname == 'ShaderNodeRGB':
            extra = str(tuple(round(x,3) for x in n.outputs[0].default_value))
        if n.bl_idname == 'ShaderNodeValToRGB':
            extra = str([(round(e.position,2), tuple(round(c,2) for c in e.color)) for e in n.color_ramp.elements])
        if n.bl_idname in ('ShaderNodeMix',):
            extra = n.blend_type + ' ' + str([ (i.name, (tuple(round(x,2) for x in i.default_value) if hasattr(i.default_value,'__len__') else round(i.default_value,3))) for i in n.inputs if not i.is_linked and i.enabled][:4])
        print('  ', n.name, '|', n.bl_idname, '|', n.label, '|', extra)
    print('  LINKS', len(m.node_tree.links))
ng = bpy.data.node_groups
print([g.name for g in ng if 'tone' in g.name.lower() or 'CT' in g.name][:30])
