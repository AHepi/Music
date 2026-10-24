import sys, json
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np, place_kit as pk
def grid(x0,x1,y0,y1,nx,ny):
    xs=np.linspace(x0,x1,nx); ys=np.linspace(y0,y1,ny)
    return np.array([[pk.ground_height_at(x,y) for x in xs] for y in ys])
for name,(x0,x1,y0,y1) in {'C':(-29.7,-22.3,-12.8,-8.2),'Cpad':(-31.2,-20.8,-14.3,-6.7),'D':(2.15,5.85,-10.2,-5.8),'Dpad':(0.65,7.35,-11.7,-4.3)}.items():
    g=grid(x0,x1,y0,y1,15,11)
    print(name,'min',g.min().round(3),'max',g.max().round(3),'mean',g.mean().round(3))
    if name in('C','D'):
        for r in g[::2]: print(' '.join('%6.2f'%v for v in r[::2]))
print([ (o.name,o.get('place_role'),o.get('place_owner')) for o in bpy.data.objects])
print('keepclear', pk.is_keep_clear(-26,-8.0), pk.is_keep_clear(4,-5.5))
for o in bpy.data.objects:
    if o.type=='CAMERA': print(o.name, tuple(round(v,1) for v in o.location), o.rotation_euler[:], o.data.lens)
