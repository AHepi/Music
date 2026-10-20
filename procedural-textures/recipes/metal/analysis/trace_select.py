# What this does (plain words): the cost-aware "tracing" layer. It finds every candidate patch (a place where the reference palette colour differs from
# what the layout paints), measures what each patch would gain (how much closer to the reference the picture gets, counting dots near strong edges
# three times) against what it costs (bytes of description), and keeps the best gain-per-byte patches until a byte budget is used up. Analysis only:
# it reads the reference. The kept patches are the 'regions' layer of a description (steps in whole dots, painted largest first).
import json, os, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE)
import trace_regions as tr

def is_simple(poly):
    """True when no two non-neighbouring edges of the closed polygon cross or touch (so any triangulation tool can fill it)."""
    p=np.asarray(poly,float); n=len(p)
    if n<3: return False
    a=p; b=np.roll(p,-1,axis=0)
    def orient(u,v,w): return (v[...,0]-u[...,0])*(w[...,1]-u[...,1])-(v[...,1]-u[...,1])*(w[...,0]-u[...,0])
    i,j=np.triu_indices(n,k=2)
    keep=~((i==0)&(j==n-1)); i,j=i[keep],j[keep]
    o1=orient(a[i],b[i],a[j]); o2=orient(a[i],b[i],b[j]); o3=orient(a[j],b[j],a[i]); o4=orient(a[j],b[j],b[i])
    cross=(o1*o2<0)&(o3*o4<0)          # only proper crossings matter: a polygon that merely touches itself at a corner is filled correctly by the slab method
    return not bool(cross.any())

MAX_CORNERS=120      # an outline never has more corners than this (so no single list in a description is picture-sized); the smaller patches painted on top refine it

def simple_outline(contour, eps):
    """Simplify a pixel contour with approxPolyDP into a simple polygon (no crossing edges) of at most MAX_CORNERS corners: tighten if it crosses itself, loosen if it has too many corners."""
    for e in (eps, eps*0.7, 0.6, 0.0):
        ap=cv2.approxPolyDP(contour,e,True).reshape(-1,2) if e>0 else contour.reshape(-1,2)
        if len(ap)>=3 and is_simple(ap): break
    else:
        return None
    grow=eps
    while len(ap)>MAX_CORNERS and grow<30:
        grow*=1.5
        trial=cv2.approxPolyDP(contour,grow,True).reshape(-1,2)
        if len(trial)>=3 and is_simple(trial): ap=trial
    return ap if len(ap)<=MAX_CORNERS else None

def candidates(ref, canvas, palette, min_area=10, sigma=0.8, edge_weight=3.0):
    K=len(palette)
    pal_lab=cv2.cvtColor(np.array(palette,np.float32).reshape(1,-1,3)/255.0,cv2.COLOR_RGB2LAB).reshape(-1,3)
    ref_l=tr.smooth_labels(tr.nearest_labels(ref,pal_lab),K,sigma)
    can_l=tr.nearest_labels(canvas,pal_lab)
    ref_lab=cv2.cvtColor(ref.astype(np.float32)/255.0,cv2.COLOR_RGB2LAB)
    can_lab=cv2.cvtColor(canvas.astype(np.float32)/255.0,cv2.COLOR_RGB2LAB)
    grey=cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx=cv2.Sobel(grey,cv2.CV_32F,1,0); gy=cv2.Sobel(grey,cv2.CV_32F,0,1); mag=np.hypot(gx,gy)
    weight=1.0+edge_weight*np.clip(mag/ (np.percentile(mag,90)+1e-6),0,1)
    err_before=np.sqrt(((ref_lab-can_lab)**2).sum(-1))*weight
    out=[]
    for k in range(K):
        mask=((ref_l==k)&(can_l!=k)).astype(np.uint8)
        if mask.sum()<min_area: continue
        n,lab,st,cen=cv2.connectedComponentsWithStats(mask,connectivity=4)
        for i in range(1,n):
            a=st[i,cv2.CC_STAT_AREA]
            if a<min_area: continue
            x,y,w,h=st[i,0],st[i,1],st[i,2],st[i,3]
            sub=(lab[y:y+h,x:x+w]==i).astype(np.uint8)
            cs,hier=cv2.findContours(sub,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
            for ci,c in enumerate(cs):
                if hier[0][ci][3]!=-1 or cv2.contourArea(c)<min_area*0.5: continue
                eps=1.0 if a<150 else (1.6 if a<700 else 2.2)
                ap=simple_outline(c,eps)
                if ap is None: continue
                ap=ap+np.array([x,y])
                m=sub.astype(bool)
                eb=err_before[y:y+h,x:x+w][m].sum()
                ea=(np.sqrt(((ref_lab[y:y+h,x:x+w][m]-cv2.cvtColor(np.array(palette[k],np.float32).reshape(1,1,3)/255.0,cv2.COLOR_RGB2LAB).reshape(3))**2).sum(-1))*weight[y:y+h,x:x+w][m]).sum()
                steps=np.diff(np.vstack([ap,ap[:1]]),axis=0)[:-1]
                cost=len(json.dumps([k,int(ap[0,0]),int(ap[0,1])]+[int(v) for v in steps.ravel()],separators=(',',':')))+1
                out.append({'k':k,'area':float(cv2.contourArea(ap.astype(np.float32))),'ap':ap,'gain':float(eb-ea),'cost':cost,'steps':steps})
    return out

def select(cands, budget_bytes):
    ranked=sorted([c for c in cands if c['gain']>0],key=lambda c:-c['gain']/c['cost'])
    chosen=[]; used=0
    for c in ranked:
        if used+c['cost']>budget_bytes: continue
        chosen.append(c); used+=c['cost']
    chosen.sort(key=lambda c:-c['area'])
    regions=[[c['k'],int(c['ap'][0,0]),int(c['ap'][0,1])]+[int(v) for v in c['steps'].ravel()] for c in chosen]
    return regions,used


# ---------------------------------------------------------------------------------------------- seamless tracing
def heal_seam(ref, ramp=14):
    """The reference tile has a mild seam (the picture jumps across the wrap-around edge). Heal it: near every picture edge fade to the half-tile-shifted
    picture, whose own edge is the middle of the original (continuous). Only a strip `ramp` dots wide at each edge changes. Analysis only."""
    w=ref.shape[0]
    rolled=np.roll(np.roll(ref,w//2,0),w//2,1)
    d=np.minimum(np.arange(w),w-1-np.arange(w)).astype(np.float32)
    s=np.clip(d/ramp,0,1); s=s*s*(3-2*s)
    m=(s[:,None]*s[None,:])[...,None]
    return (ref*m+rolled*(1-m)).round().astype(np.uint8)

def candidates_wrapped(ref, canvas, palette, pad=40, **kw):
    """Trace on a picture padded by `pad` dots of wrap-around on every side; keep patches whose middle lies in the real tile (so a patch crossing the
    edge is one patch, drawn again on the other side by the generator's wrap copies). ref and canvas must both be periodic."""
    refp=np.pad(ref,((pad,pad),(pad,pad),(0,0)),mode='wrap'); canp=np.pad(canvas,((pad,pad),(pad,pad),(0,0)),mode='wrap')
    cands=candidates(refp,canp,palette,**kw)
    h=ref.shape[0]; out=[]
    for c in cands:
        cx,cy=c['ap'].mean(axis=0)
        if pad<=cx<pad+h and pad<=cy<pad+h:
            c=dict(c); c['ap']=c['ap']-pad; out.append(c)
    return out
