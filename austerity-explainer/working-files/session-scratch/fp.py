import sys, math
sys.path.insert(0,'/home/user/work/paper-pop-up-film-kit/paper-film/tools')
from frame_check import project
cam=tuple(map(float,sys.argv[1].split(",")));tgt=tuple(map(float,sys.argv[2].split(",")));fov=float(sys.argv[3])
def run(hx,hz,rot,px,pz,w=1.0,d=0.95):
    bay=min(0.4,0.42*d); gw=0.775*w/1.0; fr=d/2+bay+0.55; bk=-d/2
    pts={}
    for nm,(lx,lz) in {'gBL':(-gw,bk),'gBR':(gw,bk),'gFL':(-gw,fr),'gFR':(gw,fr)}.items():
        x=lx*math.cos(rot)+lz*math.sin(rot); z=-lx*math.sin(rot)+lz*math.cos(rot)
        pts[nm]=(hx+x,0.012,hz+z)
    pts['roof']=(hx,0.75,hz); pts['postTop']=(px,1.25,pz); pts['postBot']=(px,0,pz); pts['board']=(2.85,1.05,-2.65); pts['boardL']=(2.5,1.05,-2.65)
    print(f'house {hx},{hz} rot {rot} post {px},{pz}')
    for k,p in pts.items():
        X,Y,d=project(cam,tgt,fov,p); print(f'  {k:8s} ({p[0]:.2f},{p[2]:.2f}) -> {X:.0f},{Y:.0f}')
for a in sys.argv[4:]:
    run(*[float(v) for v in a.split(',')])
