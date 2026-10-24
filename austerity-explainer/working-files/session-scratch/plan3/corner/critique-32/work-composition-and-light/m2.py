from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
nm=idm('notice'); ch=idm('chair')|idm('lantern')
ys,xs=np.where(nm); print('notice mask box', xs.min()/1080, ys.min()/1920, xs.max()/1080, ys.max()/1920)
def bands(im, mask, n=6, label=''):
    ys,xs=np.where(mask); y0,y1=ys.min(),ys.max()
    L=luma(im); W=rb(im)
    out=[]
    for i in range(n):
        a=y0+(y1-y0)*i/n; b=y0+(y1-y0)*(i+1)/n
        m=mask.copy(); m[:int(a)]=False; m[int(b):]=False
        l=L[m]; thr=np.percentile(l,40)
        paper=m & (L>=thr) & (L> 0.6*np.percentile(l,90))
        out.append((L[paper].mean(), W[paper].mean(), paper.sum()))
    print(label, ' | '.join(f'{a:.3f}/{b:+.3f}' for a,b,c in out))
    return out
paper5=nm & ~ch
bands(v4,paper5,6,'v4 notice bands (top->bottom) L/R-B:')
bands(v5,paper5,6,'v5 notice bands (top->bottom) L/R-B:')
# reference notice: hand box, then threshold the paper
H,W_=ref.shape[:2]
rm=boxm(ref.shape,0.752,0.462,0.905,0.655)
# exclude the reference chair (white chair top rail over notice bottom right ~0.86-0.97, 0.60-0.66)
rm &= ~boxm(ref.shape,0.86,0.59,0.98,0.70)
bands(ref,rm,6,'ref notice bands (top->bottom) L/R-B:')
# left-right across the notice in v5
L=luma(v5)
ys,xs=np.where(paper5)
for i in range(4):
    a=xs.min()+(xs.max()-xs.min())*i/4; b=xs.min()+(xs.max()-xs.min())*(i+1)/4
    m=paper5.copy(); m[:,:int(a)]=False; m[:,int(b):]=False
    l=L[m]; p=m&(L>=np.percentile(l,40))
    print('v5 notice column %d: L %.3f R-B %+.3f'%(i,L[p].mean(),rb(v5)[p].mean()))
