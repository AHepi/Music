import cv2, numpy as np, json
REF='/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg'
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/'
NOW=B+'final/composed-end-4.png'; OLD=B+'composed-end-2.png'; IDS=B+'final/facts/ids.png'
def load(p):
    im=cv2.imread(p)[:,:,::-1].astype(np.float32)/255.0
    return im
def luma(im): return 0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2]
def stats(im, m, label):
    px=im[m]; L=luma(im)[m]
    if len(px)==0: print(label,'EMPTY'); return
    r,g,b=px.mean(0)
    w=(px[:,0]-px[:,2]).mean()
    hsv=cv2.cvtColor((im*255).astype(np.uint8),cv2.COLOR_RGB2HSV)[m]
    print(f"{label:38s} n={len(px):6d} luma mean {L.mean():.3f} p10 {np.percentile(L,10):.3f} p90 {np.percentile(L,90):.3f} max {L.max():.3f} | RGB {r*255:5.0f}{g*255:5.0f}{b*255:5.0f} | R-B {w:+.3f} | sat {hsv[:,1].mean()/255:.2f} | clip>0.95 {(px.min(1)>0.95).mean()*100:4.1f}%")
    return dict(luma=float(L.mean()),rgb=[float(r),float(g),float(b)])
def box(im,x0,y0,x1,y1):
    h,w=im.shape[:2]; m=np.zeros((h,w),bool); m[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=True; return m
ids=cv2.imread(IDS)[:,:,::-1].astype(int)
def idm(c,tol=12): return (np.abs(ids-np.array(c)).max(2)<=tol)
now=load(NOW); ref=load(REF); old=load(OLD)
H,W=now.shape[:2]
print('frame mean luma: ref %.3f old %.3f now %.3f'%(luma(ref).mean(),luma(old).mean(),luma(now).mean()))
G=json.load(open(B+'final/facts/facts.json'))['groups']
M={k:idm(v['colour']) for k,v in G.items()}
for k,m in M.items(): print('mask',k,m.sum())
print('\n== NOW props (ids masks)')
for k in ['notice','board','drum','chair','lantern','pail','lamp post','handcart']:
    stats(now,M[k],'now '+k)

import sys; sys.path.insert(0,'.')
from regions import R
IM={'ref':ref,'old':old,'now':now}
print()
names=list(R['now'].keys())
for n in names:
    print('--',n)
    for k in ['ref','old','now']:
        im=IM[k]; stats(im, box(im,*R[k][n]), k)
