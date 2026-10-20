# What this does (plain words): for each strap and brace in the reference, slides along its two long edges and records, at every step,
# the colours found at 1-dot distances across the edge (from 30 dots outside to 30 dots inside). The MIDDLE value (median) over the whole
# length gives the typical "edge profile": the shadow, the dark crease, the bright edge line, the strap face. Rust and chips come and go,
# so the median shows the steel underneath. Analysis only (it reads the reference). Writes edge_profiles.json.
import cv2, numpy as np, json, math
PROC='proc-work'
c=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1].astype(np.float32)
H,W=c.shape[:2]
P=80
cp=cv2.copyMakeBorder(c,P,P,P,P,cv2.BORDER_WRAP)
rivets=[r for r in json.load(open('rivets_found.json')) if r[2]>=0.68]
def profile(point, angle_deg, t_ranges, offsets=np.arange(-30,31), step=2.0, skip_rivets=True, min_samples=30):
    """Line through `point` with direction angle (image coordinates, y down). Offsets are measured along the normal n=(sin a, -cos a)."""
    a=math.radians(angle_deg); d=np.array([math.cos(a),math.sin(a)]); n=np.array([math.sin(a),-math.cos(a)])
    p0=np.array(point,float); out=[]
    for (ta,tb) in t_ranges:
        for t in np.arange(ta,tb,step):
            base=p0+d*t
            if skip_rivets and any((base[0]-rx)**2+(base[1]-ry)**2<36**2 or (abs(((base[0]-rx+W/2)%W)-W/2)<36 and abs(((base[1]-ry+H/2)%H)-H/2)<36) for rx,ry,_ in rivets): continue
            pts=base[None,:]+offsets[:,None]*n[None,:]
            out.append(pts)
    pts=np.array(out)  # (N, O, 2)
    mx=(pts[...,0]+P).astype(np.float32); my=(pts[...,1]+P).astype(np.float32)
    samp=cv2.remap(cp,mx,my,cv2.INTER_LINEAR)   # (N,O,3)
    # robust 'steel only' profile: at every offset keep the half of the samples that are least rusty (smallest red minus blue), then take their median colour
    out_med=np.zeros((samp.shape[1],3),np.float32)
    for k in range(samp.shape[1]):
        col=samp[:,k,:]; rust=col[:,0]-col[:,2]
        keep=col[rust<=np.median(rust)]
        out_med[k]=np.median(keep,axis=0)
    return out_med, samp.shape[0]
if __name__=='__main__':
    res={}
    def run(name,point,angle,t_ranges):
        m,n=profile(point,angle,t_ranges)
        res[name]={'offsets':list(range(-30,31)),'median_rgb':m.round(1).tolist(),'samples':n,'point':point,'angle':angle}
        g=m@np.array([.299,.587,.114])
        print(name.ljust(8),n,' '.join('%3d'%v for v in g[::2]))
    print('offset  '+'  '.join('%3d'%v for v in range(-30,31,2)))
    # normal n=(sin a, -cos a): angle 0 (direction +x) gives n=(0,-1) i.e. UP; offset>0 = up/outwards-left side
    # horizontal straps: crease lines
    run('H1_top',(0,526),0,[(200,650),(810,1240)])
    run('H1_bot',(0,626),0,[(200,650),(810,1240)])
    run('H2_top',(0,1181),0,[(190,650),(830,1180)])
    run('H2_bot',(0,90),0,[(950,1250)])
    # vertical straps (direction +y, angle 90 -> n=(1,0)): offset>0 = to the right
    run('V1_left',(41,0),90,[(100,500),(650,1170)])
    run('V1_right',(176,0),90,[(100,500),(650,1170)])
    run('V2_left',(662.5,0),90,[(70,440),(640,1170)])
    run('V2_right',(799.5,0),90,[(110,500),(640,1170)])
    # braces: direction (cos a, sin a); n=(sin a,-cos a) points up-right. d=-x sin a + y cos a = -(p.n)  -> crease line passes where p.n = -d
    for nm,ang,dd in (('B1',48.3,(-194.3,-92.3)),('B2',50.5,(-263.0,-164.0))):
        a=math.radians(ang); n=np.array([math.sin(a),-math.cos(a)]); d=np.array([math.cos(a),math.sin(a)])
        for tag,dv in zip(('ur','ll'),dd):
            pt=n*(-dv)    # a point with p.n = -dv
            ranges={'B1':[(380,700)],'B2':[(1050,1250),(900,1000)]}[nm]
            # t values (along direction) measured from the projection of the origin: t = p.d ; choose via sample points
            run(f'{nm}_{tag}',tuple(pt),ang,[(r[0]-(pt@d),r[1]-(pt@d)) for r in ranges])
    json.dump(res,open('edge_profiles.json','w'))
