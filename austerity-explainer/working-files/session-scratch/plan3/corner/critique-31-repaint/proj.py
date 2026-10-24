import math, numpy as np
RISE=math.tan(math.radians(4))
def pav(y): return y*RISE+0.13
YAW=math.radians(6.87)
END=np.array([3.10,17.85,pav(17.85)+1.81])
NC=np.array([3.45,22.75])
t=NC-END[:2]; t=t/np.linalg.norm(t)
START=END.copy(); START[:2]-=t*1.5
def proj(P,C,fov):
    d=np.array([-math.sin(YAW),math.cos(YAW),0]); r=np.array([math.cos(YAW),math.sin(YAW),0]); u=np.array([0,0,1])
    v=np.array(P)-C; xc,yc,zc=v@r,v@u,v@d
    th=math.tan(math.radians(fov/2)); tw=th*1080/1920
    return 0.5+0.5*xc/(zc*tw), 0.5-0.5*yc/(zc*th), zc
if __name__=='__main__':
    print('END',END.round(3),'START',START.round(3))
    print('notice centre', proj([3.454,22.808,2.754],END,60.4))
    print('lamp light', proj([3.72,23.25,5.043],END,60.4), 'facts 0.8644,0.1986')
    print('brazier', proj([2.78,22.0,2.93],END,60.4),'facts 0.5656,0.5533')
    # spot leak: from coals toward notice bottom edge
    coals=np.array([2.78,22.0,pav(22.0)+0.70+0.25])
    BL=0.46;BS=1.11
    nc=np.array([3.45,22.75,pav(22.75)+BL+0.59*BS]); tgt=nc-np.array([0,0,0.36*BS])
    dvec=tgt-coals; dvec/=np.linalg.norm(dvec)
    print('coals',coals.round(3),'target',tgt.round(3),'dir',dvec.round(3))
    tw=(4.15-coals[0])/dvec[0]; hit=coals+dvec*tw
    print('spot axis hits house front x=4.15 at',hit.round(3),'screen',proj(hit,END,60.4))
    for ang in (-10,10):
        a=math.radians(ang); R=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
        dd=R@dvec; tt=(4.15-coals[0])/dd[0]; h=coals+dd*tt; print(' cone edge',ang,h.round(2),proj(h,END,60.4))
    for ang in (-10,10):
        a=math.radians(ang); # vertical spread
        dd=dvec.copy(); dd[2]+=math.tan(a); dd/=np.linalg.norm(dd); tt=(4.15-coals[0])/dd[0]; h=coals+dd*tt; print(' cone v',ang,h.round(2),proj(h,END,60.4))
