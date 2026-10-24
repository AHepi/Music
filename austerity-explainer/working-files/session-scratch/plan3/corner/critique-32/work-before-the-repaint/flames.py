import math, numpy as np, sys
sys.path.insert(0,'.')
from proj import proj, CAMS, fwd
c=np.array([2.78,22.0]); rim=2.524; r=0.296
for cam in ['end','plate']:
    pts=[proj((c[0]+r*math.cos(t), c[1]+r*math.sin(t), rim),cam) for t in np.linspace(0,2*math.pi,720)]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    print(cam,'rim ellipse x %.3f-%.3f y %.4f-%.4f'%(min(xs),max(xs),min(ys),max(ys)), 'height px', round((max(ys)-min(ys))*CAMS[cam][3],1))
    # sight line over near rim
    cpos=CAMS[cam][0]
    dh=math.hypot(*(c-cpos[:2]))
    drop=(cpos[2]-rim)/(dh-r)
    print('   sight line z at centre %.3f, at far inner wall (r=0.26) %.3f'%(rim-drop*r, rim-drop*(r+0.26)))
    # where does a ray just over the far rim (0.15 m above it) land on the ground beyond?
    far=np.array([c[0], c[1]+r, rim+0.15])
    d=far-cpos
    for s in np.linspace(1,6,2001):
        p=cpos+d*s
        ground=p[1]*math.tan(math.radians(4))+0.13   # pavement height
        if p[2]<=ground:
            print('   a point 15 cm over the far rim is painted onto the ground at y %.2f x %.2f (%.1f m behind the drum)'%(p[1],p[0],p[1]-c[1])); break
