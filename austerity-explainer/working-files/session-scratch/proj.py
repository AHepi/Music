import numpy as np, sys
def proj(pos, tgt, fov, pt):
    pos,tgt,pt=map(np.array,(pos,tgt,pt)); f=tgt-pos; f/=np.linalg.norm(f)
    r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f)
    d=pt-pos; z=d@f; t=np.tan(np.radians(fov/2))
    y=(d@u)/z/t; x=(d@r)/z/(t*9/16)
    return round(540+540*x), round(960-960*y), round(z,2)
dial=[0.79,-0.11,-10.21]
# dial radius 0.62 -> px
def rad(fov,z): return round(0.62/(z*np.tan(np.radians(fov/2))*9/16)*540)
for name,pos,tgt,fov in [('wide',[0.15,-0.15,-0.6],[0.15,0.1,-30],36),('out',[0.15,-0.15,-0.6],[0.05,0.1,-30],36),('dial',[0.35,-0.05,-2.0],[1.95,0.95,-30],27)]+[eval(a) for a in sys.argv[1:]]:
    x,y,z=proj(pos,tgt,fov,dial); print(name,x,y,'r',rad(fov,z))
