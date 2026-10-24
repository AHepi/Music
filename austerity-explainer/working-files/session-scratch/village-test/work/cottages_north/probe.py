import sys, json
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, place_kit as pk
out={}
def grid(x0,x1,y0,y1,n=7):
    r=[]
    for j in range(n):
        y=y0+(y1-y0)*j/(n-1)
        r.append([round(pk.ground_height_at(x0+(x1-x0)*i/(n-1),y),3) for i in range(n)])
    return r
out['A']=grid(-41.5,-25,6.1,13.9)
out['B']=grid(-10.7,-1.3,5.7,13.3)
out['names']=[ (o.name,o.get('place_role')) for o in bpy.data.objects][:60]
print('PROBE',json.dumps(out))
for k in ('A','B'):
    import numpy as np
    a=np.array(out[k]); print(k, a.min(), a.max())
    for row in out[k]: print(row)
