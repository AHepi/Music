import bpy, sys, json
out = {}
want = ['cottage_brick', 'cottage_stone', 'dressed_stone', 'dark_dressed_stone', 'colliery_brick', 'plaster_dark', 'roof_slate', 'paint_', 'cast_iron']
for m in bpy.data.materials:
    if m.node_tree is None or m.users == 0: continue
    if not any(m.name.startswith(w) for w in want): continue
    nt = m.node_tree
    info = dict(users=m.users, nodes=len(nt.nodes), types=[n.bl_idname.replace('ShaderNode','') + (':' + n.node_tree.name if n.bl_idname == 'ShaderNodeGroup' and n.node_tree else '') for n in nt.nodes])
    p = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    if p:
        p = p[0]
        info['principled'] = {i.name: (list(i.default_value) if hasattr(i.default_value, '__len__') else i.default_value) for i in p.inputs if hasattr(i, 'default_value') and i.name in ('Base Color','Roughness','Metallic','Specular IOR Level','Coat Weight','Coat Roughness')}
        info['links'] = {i.name: (i.links[0].from_node.name + ':' + i.links[0].from_socket.name) for i in p.inputs if i.links}
    out[m.name] = info
objs = {}
for o in bpy.data.objects:
    for w in ('left_row_a_cottage_01', 'right_row_a_cottage_03', 'right_row_a_cottage_04'):
        if o.name.startswith(w):
            objs[o.name] = dict(type=o.type, loc=list(o.location), rot=list(o.rotation_euler), dims=list(o.dimensions), mats=[s.material.name if s.material else None for s in o.material_slots], faces=len(o.data.polygons) if o.type == 'MESH' else 0)
print('PROBE', json.dumps(dict(materials=out, objects=objs), indent=1))
