import sys; sys.path.insert(0,'scripts')
from common import *
import json
res={}
for name,(p,q) in PAIRS.items():
    A=lum(load_rgb(p)); B=lum(load_rgb(q))
    # gradient magnitude after light blur, normalised: compares outlines not brightness
    def edge(x):
        g=gauss(x,1.2); gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1)
        m=np.sqrt(gx*gx+gy*gy); return m/(gauss(m,40)+1e-3)
    EA=edge(A); EB=edge(B)
    tiles=[]; 
    T=384
    for y in range(0,H-T+1,T):
        for x in range(0,W-T+1,T):
            a=EA[y:y+T,x:x+T]; b=EB[y:y+T,x:x+T]
            win=cv2.createHanningWindow((T,T),cv2.CV_32F)
            (dx,dy),resp=cv2.phaseCorrelate(a.astype(np.float32),b.astype(np.float32),win)
            tiles.append((y,x,round(dx,2),round(dy,2),round(resp,3)))
    good=[t for t in tiles if t[4]>0.05]
    dxs=np.array([t[2] for t in good]); dys=np.array([t[3] for t in good])
    res[name]={'tiles_used':len(good),'of':len(tiles),'dx_median':float(np.median(dxs)),'dy_median':float(np.median(dys)),
               'dx_p10_p90':[float(np.percentile(dxs,10)),float(np.percentile(dxs,90))],'dy_p10_p90':[float(np.percentile(dys,10)),float(np.percentile(dys,90))],
               'abs_shift_p90':float(np.percentile(np.hypot(dxs,dys),90))}
    print(name,res[name])
json.dump(res,open(NUM+'/a1_registration.json','w'),indent=1)
