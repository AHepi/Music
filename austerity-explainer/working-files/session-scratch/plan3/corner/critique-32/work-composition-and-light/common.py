import cv2, numpy as np, json
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/'
REF='/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg'
V5=B+'final/composed-end-5.png'; V4=B+'final/composed-end-4.png'
IDS=B+'next/next26/ids.png'; FACTS=B+'next/next26/facts.json'
def load(p):
    return cv2.imread(p, cv2.IMREAD_COLOR)[:,:,::-1].astype(np.float32)/255.0
def luma(im): return 0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2]
def rb(im): return im[...,0]-im[...,2]
def sat(im):
    mx=im.max(2); mn=im.min(2); return np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
def boxm(shape,x0,y0,x1,y1):
    h,w=shape[:2]; m=np.zeros((h,w),bool); m[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=True; return m
G=json.load(open(FACTS))['groups']
ids=cv2.imread(IDS)[:,:,::-1].astype(int)
def idm(name,tol=10): return (np.abs(ids-np.array(G[name]['colour'])).max(2)<=tol)
def stats(im,m,label=''):
    px=im[m]
    if len(px)==0: return f'{label}: EMPTY'
    L=luma(im)[m]; S=sat(im)[m]; W=rb(im)[m]
    r,g,b=px.mean(0)*255
    return (f'{label:34s} n={len(px):6d} L {L.mean():.3f} (p10 {np.percentile(L,10):.3f} p90 {np.percentile(L,90):.3f} max {L.max():.3f} sd {L.std():.3f})'
            f' RGB {r:4.0f}{g:4.0f}{b:4.0f} R-B {W.mean():+.3f} sat {S.mean():.2f} chan>=0.995 {(px.max(1)>=0.995).mean()*100:4.1f}%')
