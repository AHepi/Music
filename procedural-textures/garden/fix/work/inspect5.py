import bpy, numpy as np, sys
ob = bpy.data.objects['Maple leaves']
me = ob.data
n = len(me.vertices)
print('verts', n, 'faces', len(me.polygons), 'attrs', [(a.name,a.domain,a.data_type) for a in me.attributes if not a.name.startswith('.')])
for a in me.attributes:
    if a.name.startswith('.') or a.domain!='POINT': continue
    if a.data_type=='FLOAT':
        arr=np.zeros(n,dtype=np.float32); a.data.foreach_get('value',arr); print(' ',a.name, 'min/mean/max', arr.min().round(3), arr.mean().round(3), arr.max().round(3))
    elif a.data_type=='FLOAT_VECTOR':
        arr=np.zeros(n*3,dtype=np.float32); a.data.foreach_get('vector',arr); arr=arr.reshape(-1,3); print(' ',a.name, 'min', arr.min(0).round(3), 'mean', arr.mean(0).round(3), 'max', arr.max(0).round(3))
    elif a.data_type=='INT':
        arr=np.zeros(n,dtype=np.int32); a.data.foreach_get('value',arr); print(' ',a.name, 'min/max', arr.min(), arr.max(), np.bincount(arr)[:8])
    elif a.data_type in ('FLOAT_COLOR','BYTE_COLOR'):
        arr=np.zeros(n*4,dtype=np.float32); a.data.foreach_get('color',arr); arr=arr.reshape(-1,4); print(' ',a.name, 'mean', arr.mean(0).round(3))
m = ob.modifiers[0]
ng = m.node_group
print('GN', ng.name, 'nodes', len(ng.nodes))
for it in ng.interface.items_tree:
    if it.item_type=='SOCKET' and it.in_out=='INPUT':
        try: v=m[it.identifier]
        except Exception: v='?'
        print('  in', it.name, it.identifier, it.socket_type, v)
for nd in ng.nodes:
    print('  node', nd.name, nd.bl_idname, getattr(nd,'label',''))
for nm in ['Maple leaf source 0','Maple leaf source 4','Maple inner mass']:
    o=bpy.data.objects[nm]; co=np.array([v.co[:] for v in o.data.vertices]); print(nm, 'bbox', co.min(0).round(3), co.max(0).round(3), 'faces', len(o.data.polygons), 'smooth', sum(p.use_smooth for p in o.data.polygons))
