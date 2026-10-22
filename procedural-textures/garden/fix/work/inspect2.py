import bpy, sys
import numpy as np
for nm in ['Life / tufts','Life / moss at feet and damp edges','Life / pebble fringe']:
    ob = bpy.data.objects[nm]
    me = ob.data
    n=len(me.vertices)
    print('==',nm,n)
    for a in me.attributes:
        if a.domain=='POINT' and a.data_type in ('FLOAT','FLOAT_VECTOR','INT') and not a.name.startswith('.'):
            if a.data_type=='FLOAT':
                arr=np.zeros(n,dtype=np.float32); a.data.foreach_get('value',arr); print(' ',a.name, arr[:6].round(3), arr.min().round(3), arr.max().round(3))
            elif a.data_type=='FLOAT_VECTOR':
                arr=np.zeros(n*3,dtype=np.float32); a.data.foreach_get('vector',arr); arr=arr.reshape(-1,3); print(' ',a.name, arr[:3].round(3).tolist(), arr.min(0).round(3), arr.max(0).round(3))
    for m in ob.modifiers:
        ng=m.node_group
        print('  mod', m.name, ng.name if ng else None)
        for it in ng.interface.items_tree:
            if it.item_type=='SOCKET' and it.in_out=='INPUT':
                try:
                    v=m[it.identifier]
                    try: v=tuple(v)
                    except Exception: pass
                except Exception as e: v='?'
                print('     input', it.name, it.identifier, v)
