import numpy as np, cv2, json
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
plate=load(P+'people-test-plate.jpg'); paint=load(P+'people-test-painting.png')
H,W=plate.shape[:2]
facts=json.load(open(F+'facts.json'))
ids=np.asarray(Image.open(F+'ids.png').convert('RGB')).astype(int)
def vis(n):
    m=(np.abs(ids-np.array(facts['groups'][n]['colour'])).sum(-1)<24).astype(np.uint8)
    return cv2.resize(m,(W,H),interpolation=cv2.INTER_NEAREST).astype(bool)
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
figs=[n for n in facts['groups'] if n.startswith('man') or n.startswith('walker')]
allm=np.zeros((H,W),bool)
for n in figs: allm|=vis(n)
def skin(a):
    hsv=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(int)
    h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
    return (h>=0)&(h<=25)&(s>=50)&(s<=180)&(v>=90)
sp,sq=skin(plate),skin(paint)
for n in figs:
    m=vis(n)
    if m.sum()<30: print(n,'hidden',m.sum()); continue
    m8=m.astype(np.uint8)
    inner=cv2.erode(m8,np.ones((7,7),np.uint8)).astype(bool)
    if inner.sum()<20: inner=m
    ring=cv2.dilate(m8,np.ones((61,61),np.uint8)).astype(bool)&~cv2.dilate(m8,np.ones((13,13),np.uint8)).astype(bool)&~allm
    ys,xs=np.nonzero(m); top=ys.min(); h=ys.max()-top+1
    head=m&(np.arange(H)[:,None]<top+0.15*h)
    headw=cv2.dilate(head.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
    out=[]
    for lab,a,s in [('plate',plate,sp),('paint',paint,sq)]:
        L=lum(a); out.append(f'{lab} ratio {L[inner].mean()/L[ring].mean():.2f} skin {int((s&headw).sum())}')
    print(f'{n:16s} h={h} | '+' | '.join(out))
