import numpy as np, json
from PIL import Image
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
h=np.asarray(Image.open(P+'reference/wood/height_as_uploaded.png').convert('L'),dtype=np.float64)/255
c=np.asarray(Image.open(P+'reference/wood/colour.png').convert('RGB'),dtype=np.float64)/255
F=np.concatenate([h[...,None],c],-1)
T=1254
L=[('knot K2',350,378,88,'knot'),('knot K3',170,806,85,'knot'),('knot K4',832,893,72,'knot'),
   ('zigzag R2',742,325,55,'mark'),('hook R2',925,410,65,'mark'),('rust cloud R3',600,540,100,'mark'),('hole R3',1100,578,65,'mark'),
   ('notch R3',130,592,50,'mark'),('splinter R4',620,790,70,'mark'),('splinter R5',880,1050,75,'mark'),
   ('stains R5',460,1100,85,'mark'),('rubble R5',600,1195,50,'mark')]
gaps=[189,470,709,980,1254]
def row_of(y):
    for i in range(4):
        if gaps[i]<=y<gaps[i+1]: return i
yy,xx=np.mgrid[0:T,0:T]
def corr(A,B): return np.fft.irfft2(np.fft.rfft2(A)*np.conj(np.fft.rfft2(B)),s=A.shape)
occupied=np.zeros((T,T),bool)
for name,x0,y0,r,k in L: occupied|=((xx-x0)**2+(yy-y0)**2)<=(1.2*r)**2
# local interior std map (box 2*rr) for plainness: computed per landmark
res=[]
for name,x0,y0,r,k in L:
    d=np.sqrt((xx-x0)**2+(yy-y0)**2)
    ring=((d>=r-8)&(d<=r+8)).astype(np.float64)
    tm=np.roll(np.roll(ring,-int(y0),0),-int(x0),1)
    ssd=np.zeros((T,T))
    for ch in range(4):
        Ft=np.roll(np.roll(F[...,ch]*ring,-int(y0),0),-int(x0),1)
        Fa=F[...,ch]
        ssd+=corr(Fa*Fa,tm)-2*corr(Fa,Ft)+(Ft**2).sum()
    score=ssd/(ring.sum()*4)
    I=np.pad(occupied.astype(np.float64),((1,0),(1,0))).cumsum(0).cumsum(1)
    rr=int(r)
    rowL=row_of(y0); rel=(y0-gaps[rowL])/(gaps[rowL+1]-gaps[rowL])
    ok=np.zeros((T,T),bool)
    for cr in range(4):
        a=gaps[cr]; b=gaps[cr+1]; hh=b-a
        lo=max(a+r+10,a+hh*(rel-0.3)); hi=min(b-r-10,a+hh*(rel+0.3))
        if hi>lo: ok[int(lo):int(hi)+1,:]=True
    valid=ok.copy()
    valid[:,:rr+8]=False; valid[:,-rr-8:]=False
    y_lo=np.clip(yy-rr,0,T);y_hi=np.clip(yy+rr+1,0,T);x_lo=np.clip(xx-rr,0,T);x_hi=np.clip(xx+rr+1,0,T)
    occ=I[y_hi,x_hi]-I[y_lo,x_hi]-I[y_hi,x_lo]+I[y_lo,x_lo]
    valid&=occ==0
    valid&=((xx-x0)**2+(yy-y0)**2)>(2.3*r)**2
    sc=np.where(valid,score,1e9)
    idx=np.argsort(sc.ravel())[:3000]
    best=None;tries=0
    for i in idx:
        cy,cx=divmod(int(i),T)
        patch=F[cy-rr:cy+rr+1,cx-rr:cx+rr+1,0]
        dist=np.sqrt((np.mgrid[-rr:rr+1,-rr:rr+1]**2).sum(0))
        inside=patch[dist<=rr]
        # reject candidates that are themselves distinctive: lots of very dark or very bright pixels
        if (inside<0.12).mean()>0.05 or inside.std()>0.30: continue
        best=(cx,cy,float(sc.ravel()[i]),float(inside.std())); break
    occupied|=((xx-best[0])**2+(yy-best[1])**2)<=(1.3*r)**2
    res.append({'name':name,'kind':k,'x':x0,'y':y0,'r':r,'dx':best[0]-x0,'dy':best[1]-y0,'candidate':[best[0],best[1]],'ring_msd':round(best[2],5),'std':round(best[3],3)})
    print(res[-1],flush=True)
json.dump(res,open('landmarks_patches3.json','w'),indent=1)
# preview with a hard ragged edge
rng=np.random.default_rng(1)
def smooth_noise(scale):
    a=rng.random((T//scale+3,T//scale+3))
    im=Image.fromarray((a*255).astype(np.uint8)).resize((T,T),Image.BICUBIC)
    return np.asarray(im,dtype=np.float64)/255
nz=smooth_noise(20)
out=c.copy()
for e in res:
    x0,y0,r,dx,dy=e['x'],e['y'],e['r'],e['dx'],e['dy']
    d=np.sqrt((xx-x0)**2+(yy-y0)**2)+(nz-0.5)*0.35*r
    m=np.clip((r-d)/3.0+0.5,0,1)
    xs=np.clip(xx+dx,0,T-1); ys=np.clip(yy+dy,0,T-1)
    for ch in range(3): out[...,ch]=out[...,ch]*(1-m)+c[ys,xs,ch]*m
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save('source_painted_out3.jpg',quality=90)
