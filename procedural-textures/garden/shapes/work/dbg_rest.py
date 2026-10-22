import bpy, numpy as np
dg = bpy.context.evaluated_depsgraph_get()
for n in ('Rock 0', 'Rock 4', 'Stepping stone 1', 'Lantern base'):
    ob = bpy.data.objects[n]
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    n3 = len(me.vertices)
    co = np.empty(n3*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    att = me.attributes['CT_rest']; r = np.empty(n3*3, np.float32); att.data.foreach_get('vector', r); r = r.reshape(-1,3)
    print(n, 'pos min', co.min(0).round(2), 'max', co.max(0).round(2), '| rest min', r.min(0).round(2), 'max', r.max(0).round(2), 'domain', att.domain)
    ev.to_mesh_clear()
mat = bpy.data.materials['CT / Stone painterly surface.025']
for nd in mat.node_tree.nodes:
    if nd.bl_idname in ('ShaderNodeAttribute',): print('attr node', nd.attribute_name, nd.attribute_type)
