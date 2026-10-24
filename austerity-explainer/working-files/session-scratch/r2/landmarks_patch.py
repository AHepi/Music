import numpy as np, json
from PIL import Image
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
h=np.asarray(Image.open(P+'reference/wood/height_as_uploaded.png').convert('L'),dtype=np.float64)/255
c=np.asarray(Image.open(P+'reference/wood/colour.png').convert('RGB'),dtype=np.float64)/255
F=np.concatenate([h[...,None]*1.0,c],-1)   # 1254x1254x4
T=1254
# landmarks: name, x, y, r (solid radius), kind
L=[('knot K2',350,378,85,'knot'),('knot K3',170,806,85,'knot'),('knot K4',832,893,72,'knot'),
   ('zigzag R2',742,325,55,'mark'),('hook R2',925,410,65,'mark'),('rust cloud R3',600,540,105,'mark'),('hole R3',1100,578,65,'mark'),
   ('notch R3',130,592,50,'mark'),('splinter R4',620,790,70,'mark'),('rust R4',1060,770,75,'mark'),('splinter R5',880,1050,75,'mark'),
   ('stains R5',460,1100,90,'mark'),('rubble R5',600,1195,50,'mark')]
gaps=[189,470,709,980,1254]
def row_of(y):
    for i in range(4):
        if gaps[i]<=y<gaps[i+1]: return i
yy,xx=np.mgrid[0:T,0:T]
def fft_corr(A,B):
    # cross-correlation: out[dy,dx]=sum A[y+dy,x+dx]*B[y,x] (B small padded) -- use full FFT
    return np.fft.irfft2(np.fft.rfft2(A)*np.conj(np.fft.rfft2(B)),s=A.shape)
res=[]
occupied=np.zeros((T,T),bool)
for name,x0,y0,r,k in L:
    occupied|= ((xx-x0)**2+(yy-y0)**2)<=(1.5*r)**2
for name,x0,y0,r,k in L:
    rin,rout=0.85*r,1.35*r
    d=np.sqrt((xx-x0)**2+(yy-y0)**2)
    ring=((d>=rin)&(d<=rout)).astype(np.float64)
    # restrict to bounding box for the template
    x1,x2,y1,y2=int(x0-rout)-1,int(x0+rout)+2,int(y0-rout)-1,int(y0+rout)+2
    B=np.zeros((T,T)); 
    ssd=np.zeros((T,T))
    # template placed with centre at (x0,y0); correlate: score(cx,cy)=sum ring(p-c0)*(F(p-c0+c)-F0(p-c0))^2 ; do by shifting template to origin
    tm=np.roll(np.roll(ring,-int(y0),axis=0),-int(x0),axis=1)   # ring centred at origin (wrap)
    for ch in range(4):
        Ft=np.roll(np.roll(F[...,ch]*ring,-int(y0),axis=0),-int(x0),axis=1)
        Fa=F[...,ch]
        # sum m*(Fa(c+q)-Ft(q))^2 = sum m Fa^2 (c+q) -2 sum Ft Fa(c+q) + sum Ft^2 / careful: Ft already multiplied by m
        t1=fft_corr(Fa*Fa,tm); t2=fft_corr(Fa,Ft); t3=(Ft*Ft/np.maximum(tm,1e-9)).sum()
        ssd+= t1-2*t2+ (Ft**2).sum()
    n=ring.sum()*4
    score=ssd/n   # mean squared diff, at index (cy,cx) = candidate centre (wrap-around valid only if away from edges)
    # candidate validity
    valid=np.ones((T,T),bool)
    valid[:int(rout)+4]=False; valid[-int(rout)-4:]=False; valid[:,:int(rout)+4]=False; valid[:,-int(rout)-4:]=False
    rowL=row_of(y0)
    rel=(y0-gaps[rowL])/(gaps[rowL+1]-gaps[rowL])
    for cand_row in range(4):
        lo=gaps[cand_row]+ (gaps[cand_row+1]-gaps[cand_row])*(rel-0.22)
        hi=gaps[cand_row]+ (gaps[cand_row+1]-gaps[cand_row])*(rel+0.22)
        pass
    ok=np.zeros((T,T),bool)
    for cr in range(4):
        a=gaps[cr]; b=gaps[cr+1]; hh=b-a
        lo=max(a+rout+6,a+hh*(rel-0.22)); hi=min(b-rout-6,a+hh*(rel+0.22))
        if hi>lo: ok[int(lo):int(hi)+1,:]=True
    valid&=ok
    # not near any landmark (dilated)
    from numpy.lib.stride_tricks import sliding_window_view
    # candidate disc must not touch occupied zone: use integral image
    I=np.pad(occupied.astype(np.float64),((1,0),(1,0))).cumsum(0).cumsum(1)
    rr=int(0.9*r)
    def boxsum(cy,cx):
        pass
    # approximate with a box of half-size rr
    y_lo=np.clip(yy-rr,0,T);y_hi=np.clip(yy+rr+1,0,T);x_lo=np.clip(xx-rr,0,T);x_hi=np.clip(xx+rr+1,0,T)
    occ=I[y_hi,x_hi]-I[y_lo,x_hi]-I[y_hi,x_lo]+I[y_lo,x_lo]
    valid&=occ==0
    # at least 200 dots away from the landmark itself
    valid&=((xx-x0)**2+(yy-y0)**2)>(2.2*r)**2
    # interior should be plain: height std small-ish and no very dark pixels
    sc=np.where(valid,score,1e9)
    idx=np.argsort(sc.ravel())[:2000]
    # choose best with a smooth interior: compute interior std for top 400 candidates
    best=None
    for i in idx[:400]:
        cy,cx=divmod(int(i),T)
        patch=F[cy-rr:cy+rr+1,cx-rr:cx+rr+1,0]
        std=patch.std(); dark=(patch<0.2).mean()
        if std>0.25 or dark>0.04: continue
        best=(cx,cy,float(sc.ravel()[i]),float(std)); break
    if best is None:
        i=idx[0]; cy,cx=divmod(int(i),T); best=(cx,cy,float(sc.ravel()[i]),-1)
    res.append({'name':name,'x':x0,'y':y0,'r':r,'kind':k,'dx':best[0]-x0,'dy':best[1]-y0,'cand':[best[0],best[1]],'ring_msd':round(best[2],5),'interior_std':round(best[3],3)})
    print(res[-1],flush=True)
json.dump(res,open('landmarks_patches.json','w'),indent=1)
# preview: apply all paint-outs (every landmark) to the colour map
out=c.copy(); hh_out=h.copy()
for e in res:
    x0,y0,r,dx,dy=e['x'],e['y'],e['r'],e['dx'],e['dy']
    d=np.sqrt((xx-x0)**2+(yy-y0)**2)
    t=np.clip((d-r)/(0.35*r),0,1); m=1-(t*t*(3-2*t))
    xs=np.clip(xx+dx,0,T-1); ys=np.clip(yy+dy,0,T-1)
    for ch in range(3): out[...,ch]=out[...,ch]*(1-m)+c[ys,xs,ch]*m
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save('source_painted_out.jpg',quality=90)
