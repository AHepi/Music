# What this is: my own near-copy (twin) search for the look check, round 2. Not part of the project.
import sys, json
import numpy as np
from PIL import Image
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/wood_from_displacement'
def lum(p):
    a=np.array(Image.open(p).convert('RGB')).astype(np.float64)
    return 0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
def search(I, pieces, ph, pw, seed=0, label=''):
    H,Wd=I.shape
    N=int(2**np.ceil(np.log2(max(H,Wd)+pw)))  # pad
    N=max(N,2560)
    Ic=I-I.mean()
    P=np.zeros((N,N)); P[:H,:Wd]=Ic
    FI=np.fft.rfft2(P)
    # local sums
    c1=np.cumsum(np.cumsum(Ic,0),1); c2=np.cumsum(np.cumsum(Ic**2,0),1)
    def box(c):
        c=np.pad(c,((1,0),(1,0)))
        return c[ph:,pw:]-c[:-ph,pw:]-c[ph:,:-pw]+c[:-ph,:-pw]
    S1=box(c1); S2=box(c2); n=ph*pw
    var=np.maximum(S2-S1**2/n,1e-6)
    den_img=np.sqrt(var)  # shape (H-ph+1, W-pw+1)
    res=[]
    for (y,x) in pieces:
        T=Ic[y:y+ph,x:x+pw]
        best=-1; bestinfo=None
        for o in range(4):
            Tt=[T,T[:,::-1],T[::-1,:],T[::-1,::-1]][o]
            Tz=Tt-Tt.mean()
            tn=np.sqrt((Tz**2).sum())
            if tn<1e-6: continue
            PT=np.zeros((N,N)); PT[:ph,:pw]=Tz
            corr=np.fft.irfft2(FI*np.conj(np.fft.rfft2(PT)),s=(N,N))
            c=corr[:H-ph+1,:Wd-pw+1]/(den_img*tn)
            # exclude the piece itself (overlap > 25%)
            yy0=max(0,int(y-0.75*ph)); yy1=min(c.shape[0],int(y+0.75*ph)+1)
            xx0=max(0,int(x-0.75*pw)); xx1=min(c.shape[1],int(x+0.75*pw)+1)
            c=c.copy(); c[yy0:yy1,xx0:xx1]=-1
            k=np.argmax(c); by,bx=divmod(k,c.shape[1])
            if c[by,bx]>best: best=float(c[by,bx]); bestinfo=(int(by),int(bx),o)
        res.append(dict(y=int(y),x=int(x),ncc=best,match=bestinfo))
    return res
if __name__=='__main__':
    which=sys.argv[1]; ph=int(sys.argv[2]); pw=int(sys.argv[3]); npieces=int(sys.argv[4]); out=sys.argv[5]
    I=lum(which)
    rng=np.random.default_rng(12345)
    H,Wd=I.shape
    pieces=[(int(rng.integers(0,H-ph)),int(rng.integers(0,Wd-pw))) for _ in range(npieces)]
    r=search(I,pieces,ph,pw)
    v=np.array([q['ncc'] for q in r])
    summ=dict(file=which,ph=ph,pw=pw,n=npieces,mean=float(v.mean()),median=float(np.median(v)),p90=float(np.percentile(v,90)),max=float(v.max()),
              share_over_0_6=float((v>0.6).mean()),share_over_0_7=float((v>0.7).mean()),share_over_0_8=float((v>0.8).mean()))
    print(json.dumps(summ))
    json.dump(dict(summary=summ,pieces=r),open(out,'w'))
