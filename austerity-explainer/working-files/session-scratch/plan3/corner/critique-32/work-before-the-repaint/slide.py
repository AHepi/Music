import math, numpy as np, sys
sys.path.insert(0,'.')
from proj import proj, CAMS
def solve(f, a, b, it=60):
    fa=f(a)
    for _ in range(it):
        m=(a+b)/2; fm=f(m)
        if (fa<0)==(fm<0): a,fa=m,fm
        else: b=m
    return (a+b)/2
def drum_right_edge(cam, z=2.0, c=(2.78,22.0), r=0.296):
    best=-1
    for t in np.linspace(0,2*math.pi,3600):
        p=(c[0]+r*math.cos(t), c[1]+r*math.sin(t), z)
        best=max(best, proj(p,cam)[0])
    return best
# post: left edge at y=22.833, z=2.0; find x so the end-frame x is 0.6694
y=22.833; z=2.0
x=solve(lambda X: proj((X,y,z),'end')[0]-0.6694, 2.9, 3.4)
print('post left edge world x', round(x,4))
for cam in ['end','start-film','plate']:
    W=CAMS[cam][2]
    de=drum_right_edge(cam); pe=proj((x,y,z),cam)[0]
    print(cam, 'drum right edge', round(de,4), 'post left edge', round(pe,4), 'overlap px', round((de-pe)*W,1))
# board top-left corner vs doorway right jamb. board corner: end frame (0.638,0.446). Find world by assuming depth of board front plane y~22.70 at the board's left end
# board's left end at dx=-0.495*1.11? estimate from screen: solve X at y=22.78 z=3.53 (board top) to give 0.638
yb=22.78; zb=3.50
xb=solve(lambda X: proj((X,yb,zb),'end')[0]-0.638, 2.5, 3.4)
print('board left top corner world x', round(xb,3))
# doorway right jamb: end (0.6426, 0.44); far: building front y=81.6, z?
yd=81.6
zd=solve(lambda Z: proj((0,yd,Z),'end')[1]-0.44, 0, 20)
xd=solve(lambda X: proj((X,yd,zd),'end')[0]-0.6426, -5, 5)
print('doorway jamb world', round(xd,3), round(zd,3))
for cam in ['end','start-film','plate']:
    W=CAMS[cam][2]
    a=proj((xb,yb,zb),cam); d=proj((xd,yd,zd),cam)
    print(cam, 'board corner x', round(a[0],4), 'y', round(a[1],4), ' doorway jamb x', round(d[0],4), ' gap px (board-jamb)', round((a[0]-d[0])*W,1))
# lamp glass right edge vs rusty pipe: lamp glass right edge end (0.842, 0.25). lamp head ~ y 25.5+? lamp at (3.72,25.5); glass right edge x ~ 3.72+0.2?
yl=25.5; zl=solve(lambda Z: proj((3.9,yl,Z),'end')[1]-0.25, 3, 7)
xl=solve(lambda X: proj((X,yl,zl),'end')[0]-0.842, 3.5, 4.2)
# pipe on house front x=4.15 (maybe 4.10 for pipe): find y that gives 0.847 at same height
xp=4.10
yp=solve(lambda Y: proj((xp,Y,zl),'end')[0]-0.847, 20, 60)
print('lamp glass edge world', round(xl,3), yl, round(zl,3), ' pipe y', round(yp,2))
for cam in ['end','start-film','plate']:
    W=CAMS[cam][2]
    a=proj((xl,yl,zl),cam); p=proj((xp,yp,zl),cam)
    print(cam, 'lamp glass right', round(a[0],4), 'pipe', round(p[0],4), 'gap px', round((p[0]-a[0])*W,1))
