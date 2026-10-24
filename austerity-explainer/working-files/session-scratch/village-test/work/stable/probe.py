import sys, json
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, place_kit as pk, numpy as np
print('OBJS',[(o.name,o.get('place_role'),o.type) for o in bpy.data.objects])
def grid(x0,x1,y0,y1,n=9):
    a=np.zeros((n,n))
    for j in range(n):
        y=y0+(y1-y0)*j/(n-1)
        for i in range(n):
            a[j,i]=pk.ground_height_at(x0+(x1-x0)*i/(n-1),y)
    return a
a=grid(17.6,30.4,34.5,43.5,9)
print('PAD grid x17.6..30.4 y34.5..43.5 (rows y)');
for r in a: print(np.round(r,3))
print('building', a[2:-1,1:-1].min(), a[2:-1,1:-1].max())
b=grid(12,38,22,36,9)
print('YARD'); 
for r in b: print(np.round(r,3))
for n in ['View wide','View road_eye','View stable_close','View cottage_close']:
    c=bpy.data.objects[n]; print(n, tuple(round(v,2) for v in c.location), tuple(round(v,3) for v in c.rotation_euler), c.data.lens, c.data.clip_end)
for o in bpy.data.objects:
    if o.type=='LIGHT': print('LIGHT',o.name,o.data.type,tuple(round(v,2) for v in o.location),tuple(round(v,3) for v in o.rotation_euler),o.data.energy)
print('COLL',[c.name for c in bpy.data.collections])
print('mats',[m.name for m in bpy.data.materials][:40])
