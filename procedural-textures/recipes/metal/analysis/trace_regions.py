# What this does (plain words): the "tracing" layer. It compares the reference with the picture the layout alone paints, finds every patch of the
# reference whose palette colour is not what the layout paints there (rust, chips, stains, scratches), and writes each patch as a closed outline
# (a start point and small steps), painted largest first. Analysis only (it reads the reference). The patches it finds are the L-class 'tracing'
# layer: honest "tracing the picture", not a procedural description. The smaller the smallest patch kept (min_area) and the finer the outline
# (epsilon), the closer the picture and the bigger the file.
# Use as a module:  trace(reference_rgb, canvas_rgb, palette_rgb, min_area, epsilon) -> list of patches
import cv2, numpy as np, json

def nearest_labels(rgb, palette_lab):
    lab=cv2.cvtColor(rgb.astype(np.float32)/255.0,cv2.COLOR_RGB2LAB)
    flat=lab.reshape(-1,3); out=np.zeros(len(flat),np.int32)
    for i in range(0,len(flat),300000):
        d=((flat[i:i+300000,None,:]-palette_lab[None,:,:])**2).sum(-1); out[i:i+300000]=d.argmin(1)
    return out.reshape(rgb.shape[:2])

def smooth_labels(labels,K,sigma):
    if sigma<=0: return labels
    best=np.full(labels.shape,-1.0,np.float32); out=np.zeros(labels.shape,np.int32)
    for k in range(K):
        ind=cv2.GaussianBlur((labels==k).astype(np.float32),(0,0),sigma)
        better=ind>best; best[better]=ind[better]; out[better]=k
    return out

def trace(reference_rgb, canvas_rgb, palette_rgb, min_area=40, epsilon=1.0, sigma=0.8, wrap_pad=0):
    K=len(palette_rgb)
    palette_lab=cv2.cvtColor(np.array(palette_rgb,np.float32).reshape(1,-1,3)/255.0,cv2.COLOR_RGB2LAB).reshape(-1,3)
    ref_l=smooth_labels(nearest_labels(reference_rgb,palette_lab),K,sigma)
    can_l=nearest_labels(canvas_rgb,palette_lab)
    patches=[]; stats={'components':0}
    h,w=ref_l.shape
    for k in range(K):
        mask=((ref_l==k)&(can_l!=k)).astype(np.uint8)
        if mask.sum()<min_area: continue
        n,lab,st,cen=cv2.connectedComponentsWithStats(mask,connectivity=4)
        keep=[i for i in range(1,n) if st[i,cv2.CC_STAT_AREA]>=min_area]
        for i in keep:
            m=(lab==i).astype(np.uint8)
            cs,hier=cv2.findContours(m,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
            for ci,c in enumerate(cs):
                if hier[0][ci][3]!=-1: continue   # holes are handled by the other regions painted after (smaller)
                if cv2.contourArea(c)<min_area*0.5: continue
                ap=cv2.approxPolyDP(c,epsilon,True).reshape(-1,2)
                if len(ap)<3: continue
                patches.append((k,float(cv2.contourArea(ap.astype(np.float32))),ap))
    patches.sort(key=lambda p:-p[1])
    return patches

def encode(patches):
    """-> list of ['r', colour, x0, y0, dx1, dy1, ...] with steps in half dots (integers), start point in dots."""
    out=[]
    for k,area,ap in patches:
        pts=ap.astype(int)
        steps=(np.diff(np.vstack([pts,pts[:1]]),axis=0)*2)[:-0 or None]
        steps=np.diff(np.vstack([pts,pts[:1]]),axis=0)[:-1]*2     # closing step is implied
        out.append(['r',int(k),int(pts[0,0]),int(pts[0,1])]+[int(v) for v in steps.ravel()])
    return out
