from proj import *
import math
FS,FE=64.4,60.4
def ray_hit(C,N,plane):
    # plane: ('x',val) or ('ground',) or ('board',) -> background point along ray C->N beyond N
    d=np.array(N)-C
    if plane[0]=='x':
        t=(plane[1]-C[0])/d[0]
    elif plane[0]=='y':
        t=(plane[1]-C[1])/d[1]
    elif plane[0]=='ground':
        # z = y*RISE+0.13 (pavement); solve C+t d
        t=(C[2]-(C[1]*RISE+0.13))/((d[1]*RISE)-d[2])
    elif plane[0]=='boardplane':
        # plane through board centre with normal toward end camera (horizontal)
        n=np.array([END[0]-3.45,END[1]-22.75,0]); n/=np.linalg.norm(n)
        P0=np.array([3.45,22.75,0]); t=((P0-C)@n)/(d@n)
    return C+t*d
W,H=1080,1920
def report(name,N,plane):
    B=ray_hit(START,N,plane)
    n0=proj(N,START,FS); b0=proj(B,START,FS)
    n1=proj(N,END,FE); b1=proj(B,END,FE)
    du=(n1[0]-b1[0])*W; dv=(n1[1]-b1[1])*H
    print(f'{name:38s} edge at end ({n1[0]:.3f},{n1[1]:.3f}) z={n1[2]:.2f}; bg {B.round(2)} z={b1[2]:.2f}; edge moves vs bg by {du:+.0f}px across, {dv:+.0f}px down (end frame)')
def side(cx,cy,r,z,sign):
    # silhouette point of a vertical cylinder at height z on the left(-1)/right(+1) side as seen from START
    C=START[:2]; v=np.array([cx,cy])-C; dist=np.linalg.norm(v); v/=dist
    perp=np.array([v[1],-v[0]])  # right-hand perpendicular
    a=math.asin(r/dist)
    p=np.array([cx,cy])+perp*sign*r*math.cos(a) - v*r*math.sin(a)
    return [p[0],p[1],z]
print('FOE end frame:', proj([3.45,22.75,END[2]],END,FE)[:2])
# drum: centre 2.78,22.0 radius ~0.39 top 2.524
report('drum right edge, mid height', side(2.78,22.0,0.39,2.1,+1),('boardplane',))
report('drum right edge, rim', side(2.78,22.0,0.39,2.5,+1),('boardplane',))
report('drum left edge, mid (outer side)', side(2.78,22.0,0.39,2.1,-1),('ground',))
report('drum rim top (front), vs ground', [2.78,22.0-0.39,2.524],('boardplane',))
# chair back top: chair at 3.27,21.75 top 2.664; back is at +y side, rotated -40; approx back top centre
import math
ang=math.radians(-40); back=np.array([3.27,21.75])+np.array([-math.sin(ang),math.cos(ang)])*0.25
report('chair back top rail', [back[0],back[1],2.664],('boardplane',))
report('chair back top rail, right end', [back[0]+0.15,back[1]+0.12,2.64],('boardplane',))
report('chair seat front edge (vs pavement)', [3.20,21.45,2.13],('ground',))
report('lantern top (vs board)', [3.275,21.57,2.504],('boardplane',))
report('pail top far rim (vs pavement)', [3.28,21.35,1.915],('ground',))
report('board left edge mid (vs house x=4.15? no: vs far pavement)', [2.96,22.80,2.8],('y',30.0))
report('board left post foot (vs pavement)', [3.13,22.78,1.9],('ground',))
report('board right post (vs wall 4.15)', [3.77,22.72,2.2],('x',4.15))
report('board bottom edge centre (vs lamp base / wall)', [3.45,22.75,2.18],('x',4.15))
report('lamp post shaft (vs wall)', [3.72,23.25,4.0],('x',4.15))
report('lamp post shaft low (vs wall)', [3.72,23.25,2.0],('x',4.15))
