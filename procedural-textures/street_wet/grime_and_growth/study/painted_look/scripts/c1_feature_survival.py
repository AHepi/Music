"""Which small features of a plate come back in the painting?  (the central measurement of the painted-look study)

For every plate and its painting (painting lined up locally):
  dark features:  depth_k(p) = closing(picture, k x k disc)(p) - picture(p)   = how much darker p is than the surroundings, for features narrower than k pixels
  bright features: height_k(p) = picture(p) - opening(picture, k x k disc)(p)
A feature of 'width class' (k_prev..k) at a pixel has the contrast  c = depth_k - depth_kprev.  Only the strongest pixel of each feature is kept
(local maximum in a 5 x 5 window).  The painting 'has' the feature when, within 2 pixels of the same place, its own contrast of the same width class and sign
is at least half of the plate's AND at least 0.015 (0.015 of picture brightness = roughly what the film's grain hides).
Chance level: the same test with the painting moved 30 to 80 pixels away (that is how often a painted brush mark happens to be there anyway).
Sizes are plate pixels at 1536 x 2730.  Brightness is the picture's stored brightness 0..1 (Rec.709 weights), the way the earlier tests measured it."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json, itertools
KS=[3,5,7,9,13,17,25,33,49]        # disc sizes; a feature of width w is 'class k' if k_prev <= w < k
CLASS_NAMES={3:'1-2 px',5:'3-4 px',7:'5-6 px',9:'7-8 px',13:'9-12 px',17:'13-16 px',25:'17-24 px',33:'25-32 px',49:'33-48 px'}
DEPTH_BINS=[0.015,0.03,0.06,0.12,0.24,1.0]
def disc(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k))
def granulo(A,dark=True):
    out={}
    for k in KS:
        if dark: out[k]=cv2.morphologyEx(A,cv2.MORPH_CLOSE,disc(k))-A
        else: out[k]=A-cv2.morphologyEx(A,cv2.MORPH_OPEN,disc(k))
    cls={}; prev=np.zeros_like(A)
    for k in KS:
        cls[k]=np.maximum(out[k]-prev,0); prev=out[k]
    return cls
def local_max(c,size=5):
    m=cv2.dilate(c,np.ones((size,size),np.uint8))
    return (c>=m)&(c>0)
def nbr_max(c,r=2):
    return cv2.dilate(c,np.ones((2*r+1,2*r+1),np.uint8))
def shifted(img,dx,dy):
    return np.roll(np.roll(img,dy,0),dx,1)
def run(name, regions, paint_scale_note=""):
    p,q=PAIRS[name]
    A=lum(load_rgb(p)); B=lum(load_rgb(WORK+f"/{name}_painting_registered.png"))
    res={}
    for dark in (True,False):
        ca=granulo(A,dark); cb=granulo(B,dark)
        for k in KS:
            pk=local_max(ca[k])
            vals=ca[k]
            near=nbr_max(cb[k],2)
            # chance: painting moved away (4 different displacements, average)
            chances=[]
            for dx,dy in [(41,-33),(-57,29),(33,71),(-39,-62)]:
                chances.append(nbr_max(shifted(cb[k],dx,dy),2))
            for rn,rm in regions.items():
                for lo,hi in zip(DEPTH_BINS[:-1],DEPTH_BINS[1:]):
                    sel=pk&rm&(vals>=lo)&(vals<hi)
                    n=int(sel.sum())
                    if n<40: continue
                    a=vals[sel]
                    ok=(near[sel]>=np.maximum(0.5*a,0.015))
                    okc=np.mean([ (ch[sel]>=np.maximum(0.5*a,0.015)).mean() for ch in chances])
                    res.setdefault(rn,[]).append({'dark':dark,'k':k,'class':CLASS_NAMES[k],'depth_lo':lo,'depth_hi':hi,'n':n,
                        'survive':float(ok.mean()),'chance':float(okc),'net':float((ok.mean()-okc)/max(1e-6,1-okc)),
                        'ratio_median':float(np.median(near[sel]/a))})
    return res
if __name__=='__main__':
    allres={}
    for name in PAIRS:
        if name.startswith('lockout'):
            M=lockout_masks()
            ground=erode(M['road']|M['pavement']|M['kerb']|M['gutter'],7)
            walls=erode(M['walls']|M['roofs']|M['colliery'],7)
            regions={'all':np.ones((H,W),bool),'ground (road, pavement, kerb, gutter)':ground,'walls, roofs, colliery':walls,'sky':erode(M['sky'],9)}
        else:
            yy=np.arange(H)[:,None]*np.ones((1,W))
            regions={'all':np.ones((H,W),bool),'lower half (ground)':yy>=H*0.5,'upper half':yy<H*0.5}
        allres[name]=run(name,regions)
        print(name,"done",flush=True)
    json.dump(allres,open(NUM+'/c1_feature_survival.json','w'),indent=1)
