"""Soft pale and dark patches (stains) on the corner pavement flags: plate contrast vs painting contrast of the same shape."""
import sys; sys.path.insert(0,'scripts')
import c7_specific_match as C
from common import *
p,q=PAIRS['corner_dry']
A=lum(load_rgb(p)); B=lum(load_rgb(WORK+"/corner_dry_painting_registered.png"))
yy,xx=np.mgrid[0:H,0:W]
flags=(xx>=880)&(xx<=1500)&(yy>=2120)&(yy<=2700)&~((xx<1220)&(yy<2250))
for dark in (False,True):
    Ab=gauss(A,1.5)
    f=(cv2.morphologyEx(Ab,cv2.MORPH_CLOSE,C.disc(61))-Ab) if dark else (Ab-cv2.morphologyEx(Ab,cv2.MORPH_OPEN,C.disc(61)))
    m=((f>0.02)&flags).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,C.disc(9))
    n,lab,stats,cent=cv2.connectedComponentsWithStats(m,connectivity=8)
    rows=[]
    for i in range(1,n):
        x,y,w,h,area=stats[i]
        if area<400 or area>40000: continue
        pad=30; x0,y0,x1,y1=max(0,x-pad),max(0,y-pad),min(W,x+w+pad),min(H,y+h+pad)
        comp=lab[y0:y1,x0:x1]==i
        cu=comp.astype(np.uint8)
        ring=(cv2.dilate(cu,C.disc(41))>0)&~(cv2.dilate(cu,C.disc(9))>0)
        sa=C.signal(A[y0:y1,x0:x1],comp,ring,dark); sb=C.signal(B[y0:y1,x0:x1],comp,ring,dark)
        dt=cv2.distanceTransform(np.pad(cu,1),cv2.DIST_L2,3)
        rows.append((2*dt.max(),sa,sb))
    R=np.array(rows)
    print("dark" if dark else "pale","patches on the flags:",len(R))
    if len(R):
        for lo,hi in [(0,0.02),(0.02,0.04),(0.04,0.08),(0.08,1)]:
            s=(R[:,1]>=lo)&(R[:,1]<hi)
            if s.sum()>=4: print("   plate contrast %.2f-%.2f: n=%3d  width median %.0f px  painting contrast median %.3f  ratio painted/plate median %.2f"%(lo,hi,s.sum(),np.median(R[s,0]),np.median(R[s,2]),np.median(R[s,2]/R[s,1])))
